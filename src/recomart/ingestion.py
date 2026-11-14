"""Ingestion of two kinds of data into the raw lake:

  1. File drops (CSV) - clickstream, transactions, ratings - batch AND near-real-time
     micro-batches, picked up from the landing zone. Idempotent: a file whose MD5 was already
     ingested is skipped, so re-runs never duplicate data.
  2. REST APIs - product catalog (paginated) and external popularity/sentiment scores.

Every network call and file copy goes through `with_retry` (exponential backoff), every outcome is
logged to logs/ingestion.log and recorded in logs/audit.jsonl + the lake manifest.

    python -m recomart.ingestion                 # one ingestion run
    python -m recomart.ingestion --every 60      # periodic: poll every 60 minutes
"""
from __future__ import annotations

import argparse
import json
import time
import uuid
from datetime import datetime, timezone
from pathlib import Path

import pandas as pd
import requests

from .config import LANDING, STATE_DIR, cfg
from .logging_utils import audit, get_logger
from .storage import LakeStorage, md5_file, partition_key, storage_root

log = get_logger("ingestion", "ingestion.log")
STATE = STATE_DIR / "ingestion_state.json"
DTYPE = {"clickstream": "events", "transactions": "orders", "ratings": "reviews", "users": "profiles"}


class IngestionError(RuntimeError):
    pass


def with_retry(fn, what: str, retries: int | None = None, backoff: float | None = None):
    ic = cfg()["ingestion"]
    retries = ic["max_retries"] if retries is None else retries
    backoff = ic["backoff_seconds"] if backoff is None else backoff
    for attempt in range(1, retries + 2):
        try:
            return fn()
        except Exception as e:                        # noqa: BLE001 - we log and re-raise below
            if attempt > retries:
                log.error(f"{what}: FAILED after {attempt} attempts - {type(e).__name__}: {e}")
                audit("ingest_failed", what=what, attempts=attempt, error=str(e)[:200])
                raise IngestionError(f"{what} failed: {e}") from e
            wait = backoff * 2 ** (attempt - 1)
            log.warning(f"{what}: attempt {attempt} failed ({type(e).__name__}: {str(e)[:80]}); retrying in {wait:.1f}s")
            time.sleep(wait)


def _load_state() -> dict:
    return json.loads(STATE.read_text()) if STATE.exists() else {"files": {}}


def _save_state(s: dict):
    STATE.parent.mkdir(parents=True, exist_ok=True)
    STATE.write_text(json.dumps(s, indent=1))


def _date_from_name(name: str) -> str:
    digits = name.split("_")[1][:8]
    return f"{digits[:4]}-{digits[4:6]}-{digits[6:8]}"


def ingest_files(source: str, run_id: str, storage: LakeStorage, state: dict) -> dict:
    sc = cfg()["sources"][source]
    land = LANDING.parent.parent / sc["landing_dir"]
    files = sorted(land.glob(sc["pattern"]))
    done = skipped = failed = rows = 0
    for f in files:
        digest = md5_file(f)
        key = partition_key(source, DTYPE[source], _date_from_name(f.name), f.name)
        if state["files"].get(f"{source}/{f.name}") == digest and (storage_root() / key).exists():
            skipped += 1                                  # idempotent: same content already in the lake
            continue
        try:
            n = with_retry(lambda: sum(1 for _ in open(f, encoding="utf-8")) - 1, f"count {f.name}")
            with_retry(lambda: storage.put_file(f, key), f"store {f.name}")
            storage.record({"run_id": run_id, "source": source, "type": DTYPE[source], "key": key,
                            "md5": digest, "rows": n, "bytes": f.stat().st_size, "status": "ok"})
            state["files"][f"{source}/{f.name}"] = digest
            done += 1; rows += n
        except IngestionError:
            failed += 1
    log.info(f"{source}: {done} new file(s), {rows:,} rows ingested, {skipped} already ingested, {failed} failed")
    audit("ingest_files", run_id=run_id, source=source, new_files=done, rows=rows, skipped=skipped, failed=failed)
    return {"source": source, "new_files": done, "rows": rows, "skipped": skipped, "failed": failed}


def _get_json(url: str, params: dict | None = None) -> dict:
    r = requests.get(url, params=params, timeout=cfg()["ingestion"]["timeout_seconds"])
    r.raise_for_status()
    return r.json()


def ingest_api(source: str, run_id: str, storage: LakeStorage) -> dict:
    sc = cfg()["sources"][source]
    url = sc["base_url"] + sc["endpoint"]
    now = datetime.now(timezone.utc)
    if source == "catalog_api":
        items, page, pages = [], 1, 1
        while page <= pages:
            body = with_retry(lambda: _get_json(url, {"page": page, "size": sc["page_size"]}),
                              f"GET {sc['endpoint']} page {page}")
            items += body["items"]; pages = body["total_pages"]; page += 1
        dtype, payload = "products", {"fetched_at": now.isoformat(), "items": items}
    else:
        body = with_retry(lambda: _get_json(url), f"GET {sc['endpoint']}")
        dtype, payload = "scores", {"fetched_at": now.isoformat(), "as_of": body["as_of"], "items": body["items"]}
    data = json.dumps(payload).encode()
    key = partition_key(source, dtype, now.strftime("%Y-%m-%d"), f"{dtype}_{now:%H%M%S}.json")
    path = with_retry(lambda: storage.put_bytes(data, key), f"store {key}")
    storage.record({"run_id": run_id, "source": source, "type": dtype, "key": key, "md5": md5_file(path),
                    "rows": len(payload["items"]), "bytes": len(data), "status": "ok"})
    log.info(f"{source}: {len(payload['items'])} records fetched from {sc['endpoint']} -> {key}")
    audit("ingest_api", run_id=run_id, source=source, rows=len(payload["items"]), key=key)
    return {"source": source, "rows": len(payload["items"]), "key": key}


def run_ingestion(start_api: bool = True) -> dict:
    run_id = uuid.uuid4().hex[:10]
    log.info(f"=== ingestion run {run_id} started ===")
    storage, state = LakeStorage(), _load_state()
    if start_api:
        from .mock_api import serve_in_background
        serve_in_background()
    results = [ingest_files(s, run_id, storage, state) for s in ("clickstream", "transactions", "ratings", "users")]
    _save_state(state)
    for s in ("catalog_api", "popularity_api"):
        results.append(ingest_api(s, run_id, storage))
    log.info(f"=== ingestion run {run_id} finished ===")
    return {"run_id": run_id, "results": results}


def latest_api_snapshot(source: str, dtype: str) -> pd.DataFrame:
    files = LakeStorage.list_partition(source, dtype)
    if not files:
        raise FileNotFoundError(f"No {source} snapshot in the lake")
    return pd.DataFrame(json.loads(Path(files[-1]).read_text())["items"])


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--every", type=float, default=0, help="poll interval in minutes (0 = run once)")
    a = ap.parse_args()
    while True:
        print(json.dumps(run_ingestion(), indent=2))
        if not a.every:
            break
        time.sleep(a.every * 60)

"""Dataset versioning metadata and lineage (complements DVC).

Every stage registers its outputs: content hash, version number (bumped only when content
changes), the inputs it was built from, the transformation applied, data source and ingest dates.

  data/lineage/datasets.json   catalogue of datasets and all their versions
  data/lineage/lineage.jsonl   one record per stage run (inputs -> transformation -> outputs)
"""
from __future__ import annotations

import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

from .config import LINEAGE_DIR, ROOT

CATALOG = LINEAGE_DIR / "datasets.json"
LOG = LINEAGE_DIR / "lineage.jsonl"


def content_hash(path: Path) -> str:
    """MD5 of a file, or of all files under a directory (stable order, relative paths included)."""
    path = Path(path)
    h = hashlib.md5()
    files = [path] if path.is_file() else sorted(p for p in path.rglob("*") if p.is_file() and not p.name.endswith(".part"))
    for f in files:
        if f.name in ("_manifest.jsonl",):
            continue
        h.update(str(f.relative_to(path if path.is_dir() else path.parent)).encode())
        with open(f, "rb") as fh:
            for chunk in iter(lambda: fh.read(1 << 20), b""):
                h.update(chunk)
    return h.hexdigest()


def _load() -> dict:
    return json.loads(CATALOG.read_text()) if CATALOG.exists() else {}


def register(stage: str, outputs: dict[str, Path], inputs: dict[str, Path] | None = None,
             transformation: str = "", run_id: str = "", meta: dict | None = None) -> dict:
    LINEAGE_DIR.mkdir(parents=True, exist_ok=True)
    cat = _load()
    now = datetime.now(timezone.utc).isoformat(timespec="seconds")
    in_refs = {}
    for name, p in (inputs or {}).items():
        versions = cat.get(name, {}).get("versions", [])
        in_refs[name] = {"version": versions[-1]["version"] if versions else None,
                         "md5": versions[-1]["md5"] if versions else content_hash(p)}
    out_refs = {}
    for name, p in outputs.items():
        md5 = content_hash(p)
        entry = cat.setdefault(name, {"path": str(Path(p).relative_to(ROOT)), "versions": []})
        if not entry["versions"] or entry["versions"][-1]["md5"] != md5:
            entry["versions"].append({"version": len(entry["versions"]) + 1, "md5": md5, "created": now,
                                      "stage": stage, "run_id": run_id, "transformation": transformation,
                                      "inputs": in_refs, **(meta or {})})
        out_refs[name] = {"version": entry["versions"][-1]["version"], "md5": md5}
    CATALOG.write_text(json.dumps(cat, indent=1))
    rec = {"ts": now, "stage": stage, "run_id": run_id, "inputs": in_refs, "outputs": out_refs,
           "transformation": transformation, **(meta or {})}
    with open(LOG, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec) + "\n")
    return out_refs


def catalog() -> dict:
    return _load()


def history(limit: int = 200) -> list[dict]:
    if not LOG.exists():
        return []
    return [json.loads(x) for x in LOG.read_text().splitlines()[-limit:] if x.strip()]

"""Stage runner: ingestion -> validation -> preparation -> EDA -> transformation -> feature store ->
training. Each stage is timed, logged, recorded in logs/runs.jsonl and registered in the lineage
catalogue. The same stage functions are wrapped as Prefect tasks in flows/recomart_flow.py and
as DVC stages in dvc.yaml.

    python -m recomart.pipeline                  # whole pipeline
    python -m recomart.pipeline --stage validate # one stage
"""
from __future__ import annotations

import argparse
import json
import time
import traceback
import uuid
from datetime import datetime, timezone

from . import dq_report, eda, feature_store, generate, ingestion, lineage, preparation, train, transform, validation
from .config import (FEATURE_STORE, FIGURES, LANDING, LOG_DIR, PROCESSED, QUARANTINE, RAW, REPORTS, WAREHOUSE_DB,
                     ensure_dirs)
from .logging_utils import audit, get_logger

log = get_logger("pipeline")
RUNS = LOG_DIR / "runs.jsonl"


class ValidationGateError(RuntimeError):
    pass


def _record(run_id, stage, status, seconds, info=None, error=None):
    RUNS.parent.mkdir(parents=True, exist_ok=True)
    rec = {"run_id": run_id, "stage": stage, "status": status, "seconds": round(seconds, 2),
           "finished_at": datetime.now(timezone.utc).isoformat(timespec="seconds"), "info": info, "error": error}
    with open(RUNS, "a", encoding="utf-8") as f:
        f.write(json.dumps(rec, default=str) + "\n")


# ------------------------------------------------------------------ stages
def stage_sources(run_id=""):
    """Upstream systems (simulation). Only needed once, or to create fresh source data."""
    if not any(LANDING.glob("clickstream/*.csv")):
        return generate.generate_all()
    return {"skipped": "landing zone already populated"}


def stage_ingest(run_id=""):
    out = ingestion.run_ingestion()
    lineage.register("ingest", {"raw_lake": RAW}, {"landing_zone": LANDING}, "copy landing files + REST snapshots "
                     "into partitioned raw lake (source/type/date)", run_id,
                     {"sources": ["clickstream", "transactions", "ratings", "users", "catalog_api", "popularity_api"]})
    return out


def stage_validate(run_id=""):
    res = validation.run_validation()
    pdf = dq_report.build_pdf(res)
    lineage.register("validate", {"dq_report": REPORTS / "dq"}, {"raw_lake": RAW}, "pandera schema + custom checks", run_id)
    if any(d["status"] == "FAIL" for d in res["datasets"]):
        raise ValidationGateError("Data-quality gate failed - see reports/dq/data_quality_report.pdf")
    return {"quality_score": res["quality_score"], "report": pdf}


def stage_prepare(run_id=""):
    s = preparation.prepare()
    lineage.register("prepare", {"processed": PROCESSED, "quarantine": QUARANTINE}, {"raw_lake": RAW},
                     "dedupe, quarantine invalid rows, impute, encode categoricals, normalise numerics", run_id)
    return s


def stage_eda(run_id=""):
    s = eda.run_eda()
    lineage.register("eda", {"eda_figures": FIGURES}, {"processed": PROCESSED}, "EDA plots + summary", run_id)
    return {k: v for k, v in s.items() if k != "figures"}


def stage_transform(run_id=""):
    s = transform.run_transform()
    lineage.register("transform", {"warehouse": WAREHOUSE_DB}, {"processed": PROCESSED},
                     "load star schema; SQL feature tables (sql/*.sql); TF-IDF content similarity", run_id,
                     {"as_of": s["as_of"]})
    return s


def stage_features(run_id=""):
    s = feature_store.run_materialize()
    lineage.register("features", {"feature_store": FEATURE_STORE}, {"warehouse": WAREHOUSE_DB},
                     "weekly point-in-time snapshots; versions user_activity/v1, item_stats/v1+v2, item_cooccurrence/v1",
                     run_id)
    return s


def stage_train(run_id=""):
    s = train.train_and_evaluate()
    lineage.register("train", {"model_metrics": REPORTS / "model_metrics.json"},
                     {"processed": PROCESSED, "feature_store": FEATURE_STORE},
                     f"popularity/svd/content/hybrid; champion={s['best']}", run_id,
                     {"champion_version": s.get("champion", {}).get("version")})
    return {"best": s["best"], "champion": s.get("champion"),
            "metrics": {r["model"]: r[f"ndcg_at_{s['k']}"] for r in s["results"]}}


STAGES = {"sources": stage_sources, "ingest": stage_ingest, "validate": stage_validate, "prepare": stage_prepare,
          "eda": stage_eda, "transform": stage_transform, "features": stage_features, "train": stage_train}
ORDER = list(STAGES)


def run_stage(name: str, run_id: str | None = None):
    ensure_dirs()
    run_id = run_id or uuid.uuid4().hex[:10]
    t0 = time.time()
    log.info(f"[{run_id}] stage {name} started")
    try:
        info = STAGES[name](run_id)
        _record(run_id, name, "success", time.time() - t0, info)
        log.info(f"[{run_id}] stage {name} succeeded in {time.time() - t0:.1f}s")
        return info
    except Exception as e:
        _record(run_id, name, "failed", time.time() - t0, error=f"{type(e).__name__}: {e}")
        log.error(f"[{run_id}] stage {name} FAILED: {e}\n{traceback.format_exc(limit=3)}")
        audit("stage_failed", run_id=run_id, stage=name, error=str(e)[:300])
        raise


def run_all(stages: list[str] | None = None) -> dict:
    run_id = uuid.uuid4().hex[:10]
    log.info(f"===== pipeline run {run_id} =====")
    out = {}
    for s in stages or ORDER:
        out[s] = run_stage(s, run_id)
    audit("pipeline_success", run_id=run_id)
    return {"run_id": run_id, "stages": out}


def read_runs(limit: int = 400) -> list[dict]:
    if not RUNS.exists():
        return []
    return [json.loads(x) for x in RUNS.read_text().splitlines()[-limit:] if x.strip()]


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("--stage", choices=ORDER + ["all"], default="all")
    a = ap.parse_args()
    res = run_all() if a.stage == "all" else run_stage(a.stage)
    print(json.dumps(res, indent=1, default=str))

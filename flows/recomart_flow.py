"""Prefect orchestration of the RecoMart pipeline (DAG):

    ingest -> validate -> prepare -> eda
                                  -> transform -> features -> train

Each node is a Prefect task with its own retries, timeout and logging; a failure stops all
downstream tasks and fires an alert hook (logs/alerts.log). Run it:

    python flows/recomart_flow.py                 # one run (Prefect starts a temporary API)
    prefect server start                           # UI at http://127.0.0.1:4200
    python flows/serve.py                          # scheduled deployment (every 60 min)
"""
from __future__ import annotations

import os
import sys
from datetime import datetime, timezone
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
os.environ.setdefault("PREFECT_SERVER_ANALYTICS_ENABLED", "false")

from prefect import flow, get_run_logger, task  # noqa: E402

from recomart.config import LOG_DIR  # noqa: E402
from recomart.pipeline import run_stage  # noqa: E402


def _alert(flow_or_task, run, state):
    LOG_DIR.mkdir(parents=True, exist_ok=True)
    with open(LOG_DIR / "alerts.log", "a", encoding="utf-8") as f:
        f.write(f"{datetime.now(timezone.utc).isoformat(timespec='seconds')} | ALERT | {run.name} -> {state.type.value}: "
                f"{state.message}\n")


def _stage_task(name: str, retries: int = 0, retry_delay: int = 10, timeout: int = 900):
    @task(name=name, retries=retries, retry_delay_seconds=retry_delay, timeout_seconds=timeout,
          on_failure=[_alert], log_prints=True)
    def _t(run_id: str):
        logger = get_run_logger()
        logger.info(f"stage {name} started")
        info = run_stage(name, run_id)
        logger.info(f"stage {name} finished: {str(info)[:300]}")
        return info
    return _t


ingest = _stage_task("ingest", retries=2, retry_delay=15)
validate = _stage_task("validate")
prepare = _stage_task("prepare", retries=1)
eda = _stage_task("eda")
transform = _stage_task("transform", retries=1)
features = _stage_task("features", retries=1)
train = _stage_task("train")


@flow(name="recomart-data-pipeline", log_prints=True, on_failure=[_alert])
def recomart_pipeline(with_sources: bool = True):
    logger = get_run_logger()
    run_id = datetime.now(timezone.utc).strftime("pf%Y%m%d%H%M%S")
    if with_sources:
        run_stage("sources", run_id)
    i = ingest(run_id)
    v = validate(run_id, wait_for=[i])
    p = prepare(run_id, wait_for=[v])
    e = eda.submit(run_id, wait_for=[p])               # EDA runs in parallel with the transform branch
    t = transform(run_id, wait_for=[p])
    f = features(run_id, wait_for=[t])
    m = train(run_id, wait_for=[f])
    e.result()
    logger.info(f"pipeline {run_id} complete - champion: {m.get('champion')}")
    return {"run_id": run_id, "champion": m.get("champion"), "ndcg": m.get("metrics")}


if __name__ == "__main__":
    print(recomart_pipeline())

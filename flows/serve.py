"""Scheduled deployment: runs the pipeline periodically (interval from configs/pipeline.yaml).

    prefect server start          # terminal 1 (UI: http://127.0.0.1:4200)
    python flows/serve.py         # terminal 2 - keeps serving the scheduled deployment
"""
import sys
from datetime import timedelta
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "src"))
sys.path.insert(0, str(Path(__file__).resolve().parent))

from recomart.config import cfg  # noqa: E402
from recomart_flow import recomart_pipeline  # noqa: E402

if __name__ == "__main__":
    recomart_pipeline.serve(name="recomart-scheduled",
                            interval=timedelta(minutes=cfg()["ingestion"]["schedule_minutes"]),
                            tags=["recomart", "dmml"])

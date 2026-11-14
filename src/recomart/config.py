"""Paths and configuration shared by every pipeline stage."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path

import yaml

ROOT = Path(__file__).resolve().parents[2]
CONFIG_DIR = ROOT / "configs"
DATA = ROOT / "data"
LANDING = DATA / "landing"
LAKE = DATA / "lake"
RAW = LAKE / "raw"
QUARANTINE = LAKE / "quarantine"
PROCESSED = DATA / "processed"
WAREHOUSE_DB = DATA / "warehouse" / "recomart.db"
FEATURE_STORE = DATA / "feature_store"
LINEAGE_DIR = DATA / "lineage"
STATE_DIR = DATA / "state"
LOG_DIR = ROOT / "logs"
REPORTS = ROOT / "reports"
FIGURES = REPORTS / "figures"
SQL_DIR = ROOT / "sql"
MLFLOW_DB = ROOT / "mlflow.db"
MLFLOW_ARTIFACTS = ROOT / "mlartifacts"

EXPERIMENT = "recomart-recommender"
REGISTERED_MODEL = "recomart-recommender"
CHAMPION = "champion"

TEAM = [
    {"member": "Member 1", "name": "Rohesen Rajkamal Maurya", "id": "2025NS04108",
     "part": "Ingestion, Raw Storage & Data Versioning"},
    {"member": "Member 2", "name": "Akriti Adarsh", "id": "2025NS04070",
     "part": "Validation, Data Quality & Preparation (EDA)"},
    {"member": "Member 3", "name": "Chelsa Sam", "id": "2025NS04086",
     "part": "Feature Engineering, Warehouse & Feature Store"},
    {"member": "Member 4", "name": "Amogh J Putanikar", "id": "2025NS04023",
     "part": "Model Training, MLflow, Orchestration & Serving"},
]


@lru_cache(maxsize=1)
def cfg() -> dict:
    return yaml.safe_load((CONFIG_DIR / "pipeline.yaml").read_text())


def ensure_dirs() -> None:
    for d in (LANDING, RAW, QUARANTINE, PROCESSED, WAREHOUSE_DB.parent, FEATURE_STORE, LINEAGE_DIR,
              STATE_DIR, LOG_DIR, REPORTS, FIGURES):
        d.mkdir(parents=True, exist_ok=True)

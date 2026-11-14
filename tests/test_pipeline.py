"""Run after the pipeline has been executed once:  python -m recomart.pipeline && pytest -q"""
import json
import logging

import numpy as np
import pandas as pd
import pytest

from recomart import evaluate as ev
from recomart import feature_store, lineage
from recomart.config import PROCESSED, RAW, REPORTS
from recomart.ingestion import IngestionError, with_retry
from recomart.storage import LakeStorage, partition_key


# ---------------- ingestion & storage
@pytest.fixture
def quiet_ingestion_log():
    """Keep the deliberate test failures out of the real ingestion log shown in the app."""
    lg = logging.getLogger("recomart.ingestion")
    lg.disabled = True
    yield
    lg.disabled = False


def test_partition_key_layout_and_safety():
    assert partition_key("clickstream", "events", "2026-08-01", "a.csv") == \
        "source=clickstream/type=events/date=2026-08-01/a.csv"
    with pytest.raises(ValueError):
        partition_key("../etc", "events", "2026-08-01", "a.csv")


def test_retry_succeeds_after_transient_failures(quiet_ingestion_log):
    calls = {"n": 0}

    def flaky():
        calls["n"] += 1
        if calls["n"] < 3:
            raise ConnectionError("transient")
        return "ok"
    assert with_retry(flaky, "flaky", retries=4, backoff=0) == "ok" and calls["n"] == 3


def test_retry_gives_up_and_raises(quiet_ingestion_log):
    with pytest.raises(IngestionError):
        with_retry(lambda: 1 / 0, "always fails", retries=2, backoff=0)


def test_lake_is_partitioned_and_manifested():
    sources = {p.name for p in RAW.glob("source=*")}
    assert {"source=clickstream", "source=transactions", "source=ratings", "source=users",
            "source=catalog_api", "source=popularity_api"} <= sources
    assert all(e["md5"] and e["rows"] >= 0 for e in LakeStorage.manifest())


# ---------------- validation & preparation
def test_dq_report_detects_injected_issues():
    dq = json.loads((REPORTS / "dq" / "dq_results.json").read_text())
    by = {d["dataset"]: d for d in dq["datasets"]}
    assert by["events"]["schema_drift"], "renamed column (userId) must be detected"
    assert by["events"]["duplicate_rows"] > 0
    assert any(c["kind"] == "referential" and c["failures"] > 0 for c in by["events"]["checks"])
    assert any("rating" in c["check"] and c["failures"] > 0 for c in by["reviews"]["checks"])
    assert (REPORTS / "dq" / "data_quality_report.pdf").stat().st_size > 10_000


def test_prepared_data_is_clean():
    r = pd.read_parquet(PROCESSED / "ratings.parquet")
    assert r["rating"].between(1, 5).all()
    e = pd.read_parquet(PROCESSED / "events.parquet")
    assert e["event_ts"].notna().all() and not e.duplicated(["event_ts", "user_id", "product_id", "event_type"]).any()
    p = pd.read_parquet(PROCESSED / "products.parquet")
    assert (p["price"] > 0).all() and p["price_minmax"].between(0, 1).all()


# ---------------- feature store & lineage
def test_feature_store_versions_and_point_in_time():
    reg = feature_store.load_registry()
    last = reg["views"]["item_stats"]["snapshots"][-1]["as_of"]
    v1 = feature_store.get_training_features("item_stats", last, "v1")
    v2 = feature_store.get_training_features("item_stats", last, "v2")
    assert "trend_score" in v2 and "trend_score" not in v1
    snaps = [s["as_of"] for s in reg["views"]["user_activity"]["snapshots"] if s["version"] == "v1"]
    ent = pd.DataFrame({"user_id": ["U20001"], "ts": [snaps[2]]})
    row = feature_store.get_historical_features("user_activity", ent, "ts")
    assert str(row["as_of"].iloc[0]) < snaps[2]          # strictly before the event -> no leakage


def test_lineage_records_versions():
    cat = lineage.catalog()
    assert {"raw_lake", "processed", "warehouse", "feature_store"} <= set(cat)
    assert all(v["versions"][-1]["md5"] for v in cat.values())


# ---------------- models & metrics
def test_ranking_metrics():
    rec, rel = ["a", "b", "c", "d"], {"b", "x"}
    assert ev.precision_at_k(rec, rel, 4) == 0.25
    assert ev.recall_at_k(rec, rel, 4) == 0.5
    assert abs(ev.ndcg_at_k(rec, rel, 4) - (1 / np.log2(3)) / (1 + 1 / np.log2(3))) < 1e-9


def test_hybrid_beats_popularity_baseline():
    m = json.loads((REPORTS / "model_metrics.json").read_text())
    nd = {r["model"]: r["ndcg_at_10"] for r in m["results"]}
    assert nd["hybrid"] > nd["popularity"]


def test_api_recommendations():
    from fastapi.testclient import TestClient
    from serving.api import app
    c = TestClient(app)
    r = c.get("/recommend/U20001?k=5")
    assert r.status_code == 200 and len(r.json()["items"]) == 5
    assert c.get("/recommend/not-a-user").status_code == 422
    assert c.get("/recommend/U99999?k=3").json()["cold_start"] is True

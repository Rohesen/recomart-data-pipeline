"""Inference: recommendations for a user from the @champion model, enriched with product
details, online features and a human-readable reason, plus lineage for auditability."""
from __future__ import annotations

import time
from functools import lru_cache

import pandas as pd
from mlflow.tracking import MlflowClient

from . import feature_store
from .config import CHAMPION, PROCESSED, REGISTERED_MODEL
from .train import load_champion, setup_mlflow


@lru_cache(maxsize=4)
def _model(version: str):
    return load_champion()


@lru_cache(maxsize=1)
def products() -> pd.DataFrame:
    return pd.read_parquet(PROCESSED / "products.parquet").set_index("product_id")


def champion_info() -> dict:
    setup_mlflow()
    mv = MlflowClient().get_model_version_by_alias(REGISTERED_MODEL, CHAMPION)
    return {"model_name": REGISTERED_MODEL, "version": mv.version, "alias": CHAMPION, "run_id": mv.run_id,
            "family": mv.tags.get("model"), "ndcg_at_10": mv.tags.get("ndcg_at_10"), "data_md5": mv.tags.get("data_md5")}


def _reason(model, user_id: str, pid: str) -> str:
    try:
        uix = model.uidx[user_id]
        hist = model.R[uix].toarray().ravel()
        if getattr(model, "C", None) is not None:
            j = model.iidx[pid]
            contrib = model.C[:, j].toarray().ravel() * hist
            if contrib.max() > 0:
                src = model.items[contrib.argmax()]
                return f"Often bought together with {products().loc[src, 'title']}"
        cat = products().loc[pid, "category"]
        mine = products().reindex(model.items[hist > 0])["category"].value_counts()
        if len(mine) and cat == mine.index[0]:
            return f"Matches your interest in {cat}"
    except Exception:
        pass
    return "Popular with similar shoppers"


def recommend(user_id: str, k: int = 10) -> dict:
    t0 = time.perf_counter()
    info = champion_info()
    model = _model(str(info["version"]))
    cold = user_id not in model.uidx
    recs = model.recommend([user_id], k)[user_id]
    p = products()
    items = []
    feats = feature_store.get_online_features("item_stats", [pid for pid, _ in recs], "v1").set_index("product_id")
    for rank, (pid, score) in enumerate(recs, 1):
        row = p.loc[pid]
        items.append({"rank": rank, "product_id": pid, "title": row["title"], "category": row["category"],
                      "brand": row["brand"], "price": float(row["price"]), "score": round(score, 4),
                      "avg_rating": None if pd.isna(feats.loc[pid, "avg_rating"]) else float(feats.loc[pid, "avg_rating"]),
                      "buyers": int(feats.loc[pid, "total_buyers"]),
                      "reason": "Trending on RecoMart (new user)" if cold else _reason(model, user_id, pid)})
    return {"user_id": user_id, "cold_start": cold, "k": k, "items": items, "model": info,
            "latency_ms": round((time.perf_counter() - t0) * 1000, 1)}


def similar_items(product_id: str, k: int = 10) -> list[dict]:
    from .transform import connect
    con = connect()
    rows = con.execute("SELECT similar_product_id, cosine_similarity FROM feat_item_content_similarity "
                       "WHERE product_id = ? ORDER BY rank LIMIT ?", (product_id, k)).fetchall()
    con.close()
    p = products()
    return [{"product_id": r[0], "title": p.loc[r[0], "title"], "similarity": r[1]} for r in rows]

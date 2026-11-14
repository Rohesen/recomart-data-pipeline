"""Load prepared data into the SQLite warehouse and compute feature tables with SQL.

    python -m recomart.transform              # loads warehouse + features as of the latest date
"""
from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone

import numpy as np
import pandas as pd
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from .config import PROCESSED, SQL_DIR, WAREHOUSE_DB, cfg
from .logging_utils import audit, get_logger

log = get_logger("transform")


def connect() -> sqlite3.Connection:
    WAREHOUSE_DB.parent.mkdir(parents=True, exist_ok=True)
    con = sqlite3.connect(WAREHOUSE_DB)
    con.execute("PRAGMA foreign_keys = ON")
    return con


def _sql(name: str) -> str:
    return (SQL_DIR / name).read_text()


def _ts(df, cols):
    for c in cols:
        if c in df:
            df[c] = pd.to_datetime(df[c]).dt.strftime("%Y-%m-%d %H:%M:%S")
    return df


def load_warehouse() -> dict:
    con = connect()
    for t in ("feat_item_content_similarity", "feat_item_cooccurrence", "feat_item", "feat_user",
              "fact_ratings", "fact_orders", "fact_events", "dim_products", "dim_users"):
        con.execute(f"DROP TABLE IF EXISTS {t}")
    con.executescript(_sql("schema.sql"))
    P = lambda n: pd.read_parquet(PROCESSED / f"{n}.parquet")  # noqa: E731
    users = P("users")[["user_id", "signup_date", "age_band", "gender", "city_tier", "preferred_device",
                        "age_band_ord", "city_tier_ord"]]
    prods = P("products")[["product_id", "title", "category", "sub_category", "brand", "price", "price_minmax",
                           "log_price_z", "popularity_score", "sentiment_score", "social_mentions", "launch_date"]]
    ev = P("events")[["event_ts", "user_id", "product_id", "event_type", "weight", "session_id", "device", "channel"]]
    od = P("orders")[["order_id", "user_id", "product_id", "quantity", "unit_price", "discount_pct", "payment_mode",
                      "order_ts", "revenue"]]
    rt = P("ratings")[["user_id", "product_id", "rating", "rated_ts"]]
    counts = {}
    for name, df, tscols in (("dim_users", users, ["signup_date"]), ("dim_products", prods, ["launch_date"]),
                             ("fact_events", ev, ["event_ts"]), ("fact_orders", od, ["order_ts"]),
                             ("fact_ratings", rt, ["rated_ts"])):
        df = _ts(df.copy(), tscols)
        df.to_sql(name, con, if_exists="append", index=False, chunksize=5000)
        counts[name] = len(df)
    con.commit(); con.close()
    log.info(f"warehouse loaded: {counts}")
    return counts


def compute_features(as_of: str, con: sqlite3.Connection | None = None) -> dict[str, pd.DataFrame]:
    """Run the feature SQL for one point in time (only data strictly before `as_of`)."""
    own = con is None
    con = con or connect()
    p = {"as_of": as_of, "top_n": cfg()["features"]["cooccurrence_top_n"]}
    out = {"user_activity": pd.read_sql(_sql("features_user.sql"), con, params=p),
           "item_stats": pd.read_sql(_sql("features_item.sql"), con, params=p),
           "item_cooccurrence": pd.read_sql(_sql("features_cooccurrence.sql"), con, params=p)}
    if own:
        con.close()
    return out


def content_similarity(top_n: int = 20) -> pd.DataFrame:
    prods = pd.read_parquet(PROCESSED / "products.parquet")
    text = (prods["title"] + " " + prods["category"] + " " + prods["sub_category"] + " " + prods["brand"]).str.lower()
    X = TfidfVectorizer(ngram_range=(1, 2), min_df=1).fit_transform(text)
    S = cosine_similarity(X); np.fill_diagonal(S, -1)
    idx = np.argsort(-S, axis=1)[:, :top_n]
    rows = [(prods.product_id.iat[i], prods.product_id.iat[j], round(float(S[i, j]), 4), r + 1)
            for i in range(len(prods)) for r, j in enumerate(idx[i])]
    return pd.DataFrame(rows, columns=["product_id", "similar_product_id", "cosine_similarity", "rank"])


def run_transform(as_of: str | None = None) -> dict:
    counts = load_warehouse()
    con = connect()
    if as_of is None:
        mx = con.execute("SELECT MAX(event_ts) FROM fact_events").fetchone()[0]
        as_of = (pd.Timestamp(mx).normalize() + pd.Timedelta(days=1)).strftime("%Y-%m-%d %H:%M:%S")
    feats = compute_features(as_of, con)
    for view, table in (("user_activity", "feat_user"), ("item_stats", "feat_item"),
                        ("item_cooccurrence", "feat_item_cooccurrence")):
        feats[view].to_sql(table, con, if_exists="append", index=False)
        counts[table] = len(feats[view])
    sim = content_similarity()
    sim.to_sql("feat_item_content_similarity", con, if_exists="append", index=False)
    counts["feat_item_content_similarity"] = len(sim)
    con.execute("INSERT INTO etl_runs VALUES (?,?,?,?,?)",
                (datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S"), "transform",
                 datetime.now(timezone.utc).isoformat(timespec="seconds"), sum(counts.values()), "ok"))
    con.commit(); con.close()
    log.info(f"features as of {as_of}: {json.dumps({k: v for k, v in counts.items() if k.startswith('feat')})}")
    audit("transform", as_of=as_of, **counts)
    return {"as_of": as_of, "tables": counts}


if __name__ == "__main__":
    print(json.dumps(run_transform(), indent=1))

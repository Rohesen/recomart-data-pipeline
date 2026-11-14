"""A small, file-based feature store with a metadata registry (Feast-style concepts).

  registry      data/feature_store/registry.yaml - feature names, entity, dtype, source table,
                transformation, owner, version and every materialised snapshot (with MD5)
  offline store data/feature_store/offline/<view>/<version>/as_of=YYYY-MM-DD.parquet
                (full history of snapshots -> point-in-time-correct training sets)
  online store  data/feature_store/online.db  (latest snapshot per view+version -> inference)

Versioned retrieval: every feature view has a version. `item_stats` exists as v1 (SQL features)
and v2 (adds a derived `trend_score`); training and inference request a view *and* a version, so
a model trained on v1 keeps getting v1 features even after v2 is published.

    python -m recomart.feature_store materialize
    python -m recomart.feature_store demo
"""
from __future__ import annotations

import argparse
import hashlib
import json
import sqlite3
from datetime import datetime, timezone

import pandas as pd
import yaml

from .config import FEATURE_STORE, ROOT, cfg
from .logging_utils import audit, get_logger
from .transform import compute_features, connect

log = get_logger("feature_store")
REGISTRY = FEATURE_STORE / "registry.yaml"
OFFLINE = FEATURE_STORE / "offline"
ONLINE_DB = FEATURE_STORE / "online.db"

FEATURE_VIEWS = {
    "user_activity": {
        "entity": "user_id", "versions": ["v1"], "owner": "Member 3", "ttl_days": 7,
        "source": "warehouse.fact_events, fact_ratings, fact_orders", "transformation": "sql/features_user.sql",
        "description": "Recency, frequency and conversion behaviour of each user",
        "features": {
            "events_7d": ("int", "Events by the user in the 7 days before as_of"),
            "events_30d": ("int", "Events by the user in the 30 days before as_of (activity frequency)"),
            "purchases_30d": ("int", "Purchases in the last 30 days"),
            "total_purchases": ("int", "All purchases before as_of"),
            "distinct_items": ("int", "Distinct products interacted with"),
            "conversion_rate": ("float", "Purchases / views"),
            "avg_rating_given": ("float", "Average rating the user gives (null if none)"),
            "avg_order_value": ("float", "Average order revenue (INR)"),
            "days_since_last_event": ("float", "Recency in days"),
            "fav_category": ("str", "Category with the highest weighted interaction"),
        }},
    "item_stats": {
        "entity": "product_id", "versions": ["v1", "v2"], "owner": "Member 3", "ttl_days": 7,
        "source": "warehouse.fact_events, fact_ratings, dim_products", "transformation": "sql/features_item.sql",
        "description": "Popularity, conversion and rating statistics of each product",
        "features": {
            "views_30d": ("int", "Views in the last 30 days"),
            "purchases_30d": ("int", "Purchases in the last 30 days"),
            "total_buyers": ("int", "Distinct buyers before as_of"),
            "conversion_rate": ("float", "Purchases / views"),
            "avg_rating": ("float", "Average rating (null if unrated)"),
            "n_ratings": ("int", "Number of ratings"),
            "bayes_rating": ("float", "Bayesian-smoothed rating (m = 5)"),
            "popularity_score": ("float", "External popularity score 0-100 (popularity API)"),
            "sentiment_score": ("float", "External sentiment -1..1 (popularity API)"),
            "price_minmax": ("float", "Min-max normalised price"),
        },
        "v2_features": {"trend_score": ("float", "v2 only: 0.6 * purchases_30d pct-rank + 0.4 * sentiment rescaled to 0-1")}},
    "item_cooccurrence": {
        "entity": "product_id", "versions": ["v1"], "owner": "Member 3", "ttl_days": 7,
        "source": "warehouse.fact_events", "transformation": "sql/features_cooccurrence.sql",
        "description": "Top related products bought/carted by the same users (co-occurrence + lift)",
        "features": {"related_product_id": ("str", "Related product"), "co_users": ("int", "Users with both items"),
                     "lift": ("float", "Co-occurrence lift"), "rank": ("int", "Rank among related items")}},
}


def _apply_version(view: str, version: str, df: pd.DataFrame) -> pd.DataFrame:
    if view == "item_stats" and version == "v2":
        df = df.copy()
        df["trend_score"] = (0.6 * df["purchases_30d"].rank(pct=True) + 0.4 * (df["sentiment_score"] + 1) / 2).round(4)
    return df


def _md5_df(df: pd.DataFrame) -> str:
    return hashlib.md5(pd.util.hash_pandas_object(df, index=False).values.tobytes()).hexdigest()


def load_registry() -> dict:
    if REGISTRY.exists():
        return yaml.safe_load(REGISTRY.read_text())
    return {"project": "recomart", "views": {}}


def _save_registry(reg: dict):
    FEATURE_STORE.mkdir(parents=True, exist_ok=True)
    REGISTRY.write_text(yaml.safe_dump(reg, sort_keys=False))


def init_registry() -> dict:
    reg = load_registry()
    for name, fv in FEATURE_VIEWS.items():
        cur = reg["views"].get(name, {})
        feats = {k: {"dtype": t, "description": d, "since": "v1"} for k, (t, d) in fv["features"].items()}
        for k, (t, d) in fv.get("v2_features", {}).items():
            feats[k] = {"dtype": t, "description": d, "since": "v2"}
        reg["views"][name] = {"entity": fv["entity"], "versions": fv["versions"], "owner": fv["owner"],
                              "ttl_days": fv["ttl_days"], "source": fv["source"],
                              "transformation": fv["transformation"], "description": fv["description"],
                              "features": feats, "snapshots": cur.get("snapshots", [])}
    _save_registry(reg)
    return reg


def materialize(as_of_dates: list[str], views: list[str] | None = None) -> dict:
    reg = init_registry()
    con = connect()
    written = 0
    for as_of in as_of_dates:
        feats = compute_features(as_of, con)
        for view in views or FEATURE_VIEWS:
            for version in FEATURE_VIEWS[view]["versions"]:
                df = _apply_version(view, version, feats[view])
                path = OFFLINE / view / version / f"as_of={as_of[:10]}.parquet"
                path.parent.mkdir(parents=True, exist_ok=True)
                df.to_parquet(path, index=False)
                snaps = [s for s in reg["views"][view]["snapshots"] if not (s["version"] == version and s["as_of"] == as_of)]
                snaps.append({"version": version, "as_of": as_of, "rows": len(df), "md5": _md5_df(df),
                              "path": str(path.relative_to(ROOT)),
                              "created": datetime.now(timezone.utc).isoformat(timespec="seconds")})
                reg["views"][view]["snapshots"] = sorted(snaps, key=lambda s: (s["version"], s["as_of"]))
                written += 1
    con.close()
    _save_registry(reg)
    publish_online(reg)
    write_docs(reg)
    log.info(f"materialised {written} snapshots for {len(as_of_dates)} as_of dates")
    audit("feature_materialize", snapshots=written, as_of=as_of_dates[-1])
    return {"snapshots": written, "latest_as_of": as_of_dates[-1]}


def publish_online(reg: dict | None = None):
    reg = reg or load_registry()
    con = sqlite3.connect(ONLINE_DB)
    for view, meta in reg["views"].items():
        for version in meta["versions"]:
            snaps = [s for s in meta["snapshots"] if s["version"] == version]
            if snaps:
                pd.read_parquet(ROOT / snaps[-1]["path"]).to_sql(f"{view}__{version}", con, if_exists="replace", index=False)
    con.commit(); con.close()


# ---------------------------------------------------------------- retrieval API
def get_training_features(view: str, as_of: str, version: str = "v1") -> pd.DataFrame:
    """Latest snapshot with snapshot.as_of <= as_of (never a future snapshot)."""
    snaps = [s for s in load_registry()["views"][view]["snapshots"] if s["version"] == version and s["as_of"] <= as_of]
    if not snaps:
        raise LookupError(f"No {view}/{version} snapshot at or before {as_of}")
    return pd.read_parquet(ROOT / snaps[-1]["path"])


def get_historical_features(view: str, entity_df: pd.DataFrame, ts_col: str, version: str = "v1") -> pd.DataFrame:
    """Point-in-time join: each entity row gets the newest snapshot taken before its timestamp."""
    meta = load_registry()["views"][view]
    key = meta["entity"]
    hist = pd.concat([pd.read_parquet(ROOT / s["path"]) for s in meta["snapshots"] if s["version"] == version])
    hist["as_of"] = pd.to_datetime(hist["as_of"])
    left = entity_df.copy(); left[ts_col] = pd.to_datetime(left[ts_col])
    left["_row"] = range(len(left))
    out = pd.merge_asof(left.sort_values(ts_col), hist.sort_values("as_of"), left_on=ts_col, right_on="as_of",
                        by=key, direction="backward", allow_exact_matches=False)
    return out.sort_values("_row").drop(columns="_row").reset_index(drop=True)


def get_online_features(view: str, keys: list[str], version: str = "v1") -> pd.DataFrame:
    if view not in FEATURE_VIEWS or version not in FEATURE_VIEWS[view]["versions"]:
        raise ValueError(f"Unknown feature view/version {view}/{version}")
    con = sqlite3.connect(ONLINE_DB)
    entity = FEATURE_VIEWS[view]["entity"]
    marks = ",".join("?" * len(keys))
    df = pd.read_sql(f'SELECT * FROM "{view}__{version}" WHERE {entity} IN ({marks})', con, params=list(keys))
    con.close()
    return df


def write_docs(reg: dict | None = None):
    reg = reg or load_registry()
    lines = ["# Feature metadata (generated from data/feature_store/registry.yaml)", ""]
    for view, m in reg["views"].items():
        lines += [f"## {view}", "", f"- **Entity:** `{m['entity']}`  ", f"- **Versions:** {', '.join(m['versions'])}  ",
                  f"- **Source:** {m['source']}  ", f"- **Transformation:** `{m['transformation']}`  ",
                  f"- **Owner:** {m['owner']} · **TTL:** {m['ttl_days']} days  ", f"- {m['description']}", "",
                  "| Feature | Type | Since | Description |", "|---|---|---|---|"]
        lines += [f"| `{k}` | {v['dtype']} | {v['since']} | {v['description']} |" for k, v in m["features"].items()]
        lines += ["", f"Snapshots materialised: {len(m['snapshots'])}", ""]
    (ROOT / "docs" / "FEATURES.md").write_text("\n".join(lines))


def snapshot_dates(min_date: str, max_date: str, every_days: int = 7) -> list[str]:
    start = pd.Timestamp(min_date).normalize() + pd.Timedelta(days=14)
    end = pd.Timestamp(max_date).normalize() + pd.Timedelta(days=1)
    dates = list(pd.date_range(start, end, freq=f"{every_days}D"))
    if dates[-1] != end:
        dates.append(end)
    return [d.strftime("%Y-%m-%d %H:%M:%S") for d in dates]


def run_materialize(extra_dates: list[str] | None = None) -> dict:
    con = connect()
    mn, mx = con.execute("SELECT MIN(event_ts), MAX(event_ts) FROM fact_events").fetchone()
    con.close()
    dates = sorted(set(snapshot_dates(mn, mx) + (extra_dates or [])))
    return materialize(dates)


if __name__ == "__main__":
    ap = argparse.ArgumentParser()
    ap.add_argument("cmd", choices=["materialize", "demo"])
    a = ap.parse_args()
    if a.cmd == "materialize":
        print(json.dumps(run_materialize(), indent=1))
    else:
        reg = load_registry()
        last = reg["views"]["item_stats"]["snapshots"][-1]["as_of"]
        print("v1:", get_training_features("item_stats", last, "v1").columns.tolist())
        print("v2:", get_training_features("item_stats", last, "v2").columns.tolist())
        print(get_online_features("user_activity", ["U20001", "U20002"]).to_string())

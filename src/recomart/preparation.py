"""Cleaning and preprocessing: raw lake -> data/processed (Parquet), rejected rows -> quarantine.

  * harmonise schema drift, parse timestamps, drop exact duplicates
  * quarantine invalid rows (bad timestamp, unknown product/user, rating outside 1-5, quantity < 1)
  * impute missing categorical values; fix invalid prices with the category median
  * encode categorical attributes (one-hot category/gender, ordinal age band/city tier, label brand)
  * normalise numeric variables (min-max price, log-price z-score, recency of timestamps)
  * build the implicit-feedback interaction table (event weights) used by the models

    python -m recomart.preparation
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .config import PROCESSED, QUARANTINE, cfg
from .logging_utils import audit, get_logger
from .raw_reader import read_dataset

log = get_logger("preparation")


def _quarantine(df: pd.DataFrame, mask: pd.Series, name: str, reason: str, store: dict) -> pd.DataFrame:
    bad = df[mask]
    if len(bad):
        store.setdefault(name, []).append(bad.assign(_reason=reason))
    return df[~mask]


def prepare() -> dict:
    PROCESSED.mkdir(parents=True, exist_ok=True); QUARANTINE.mkdir(parents=True, exist_ok=True)
    q, summary = {}, {}

    # ---------------- products (+ external popularity)
    prod = read_dataset("products").drop(columns="_source_file")
    raw_n = len(prod)
    prod["price"] = pd.to_numeric(prod["price"], errors="coerce")
    bad_price = prod["price"].isna() | (prod["price"] <= 0)
    prod.loc[bad_price, "price"] = np.nan
    prod["price"] = prod["price"].fillna(prod.groupby("category")["price"].transform("median"))
    prod["brand"] = prod["brand"].fillna("Unknown")
    prod = prod.drop_duplicates("product_id", keep="last")
    pop = read_dataset("scores").drop(columns="_source_file")
    for c in ("popularity_score", "sentiment_score", "social_mentions"):
        pop[c] = pd.to_numeric(pop[c], errors="coerce")
    prod = prod.merge(pop, on="product_id", how="left")
    prod["popularity_score"] = prod["popularity_score"].fillna(prod["popularity_score"].median())
    prod["sentiment_score"] = prod["sentiment_score"].fillna(0)
    # encoding + normalisation
    prod["price_minmax"] = (prod["price"] - prod["price"].min()) / (prod["price"].max() - prod["price"].min())
    lp = np.log1p(prod["price"]); prod["log_price_z"] = (lp - lp.mean()) / lp.std()
    prod["brand_code"] = prod["brand"].astype("category").cat.codes
    prod = pd.concat([prod, pd.get_dummies(prod["category"], prefix="cat", dtype=int)], axis=1)
    prod["launch_date"] = pd.to_datetime(prod["launch_date"], errors="coerce")
    summary["products"] = {"raw": raw_n, "clean": len(prod), "prices_fixed": int(bad_price.sum())}
    products = set(prod["product_id"])

    # ---------------- users
    users = read_dataset("profiles").drop(columns="_source_file").drop_duplicates("user_id", keep="last")
    users["age_band_ord"] = users["age_band"].map({"18-24": 0, "25-34": 1, "35-44": 2, "45-54": 3, "55+": 4})
    users["city_tier_ord"] = users["city_tier"].map({"tier1": 1, "tier2": 2, "tier3": 3})
    users = pd.concat([users, pd.get_dummies(users["gender"], prefix="gender", dtype=int)], axis=1)
    users["signup_date"] = pd.to_datetime(users["signup_date"], errors="coerce")
    summary["users"] = {"raw": len(users), "clean": len(users)}
    known_users = set(users["user_id"])

    # ---------------- events (clickstream)
    ev = read_dataset("events")
    raw_n = len(ev)
    ev = ev.drop_duplicates(subset=[c for c in ev.columns if c != "_source_file"])
    ev["event_ts"] = pd.to_datetime(ev["event_ts"], errors="coerce", format="mixed")
    ev = _quarantine(ev, ev["event_ts"].isna(), "events", "invalid_timestamp", q)
    ev = _quarantine(ev, ~ev["product_id"].isin(products), "events", "unknown_product", q)
    ev = _quarantine(ev, ~ev["user_id"].isin(known_users), "events", "unknown_user", q)
    ev["device"] = ev["device"].fillna("unknown"); ev["session_id"] = ev["session_id"].fillna("unknown")
    w = cfg()["training"]["event_weights"]
    ev["weight"] = ev["event_type"].map(w)
    t0 = ev["event_ts"].min()
    ev["days_since_start"] = (ev["event_ts"] - t0).dt.total_seconds() / 86400
    ev["recency_norm"] = ev["days_since_start"] / ev["days_since_start"].max()
    ev["hour"] = ev["event_ts"].dt.hour
    summary["events"] = {"raw": raw_n, "clean": len(ev), "duplicates_removed": raw_n - len(ev) - sum(len(x) for x in q.get("events", []))}

    # ---------------- orders
    od = read_dataset("orders")
    raw_n = len(od)
    od = od.drop_duplicates(subset=[c for c in od.columns if c != "_source_file"])
    for c in ("quantity", "unit_price", "discount_pct"):
        od[c] = pd.to_numeric(od[c], errors="coerce")
    od["order_ts"] = pd.to_datetime(od["order_ts"], errors="coerce", format="mixed")
    od = _quarantine(od, od["quantity"].isna() | (od["quantity"] < 1), "orders", "invalid_quantity", q)
    od = _quarantine(od, ~od["product_id"].isin(products), "orders", "unknown_product", q)
    od = od.drop_duplicates("order_id", keep="last")
    od["revenue"] = od["quantity"] * od["unit_price"]
    summary["orders"] = {"raw": raw_n, "clean": len(od)}

    # ---------------- ratings
    rt = read_dataset("reviews")
    raw_n = len(rt)
    rt["rating"] = pd.to_numeric(rt["rating"], errors="coerce")
    rt["rated_ts"] = pd.to_datetime(rt["rated_ts"], errors="coerce", format="mixed")
    v = cfg()["validation"]
    rt = _quarantine(rt, ~rt["rating"].between(v["rating_min"], v["rating_max"]), "ratings", "rating_out_of_range", q)
    rt = rt.sort_values("rated_ts").drop_duplicates(["user_id", "product_id"], keep="last")
    rt["rating"] = rt["rating"].astype(int)
    summary["ratings"] = {"raw": raw_n, "clean": len(rt)}

    # ---------------- implicit interactions: one row per user-item with summed event weights
    inter = (ev.groupby(["user_id", "product_id"])
             .agg(strength=("weight", "sum"), n_events=("event_type", "size"),
                  purchased=("event_type", lambda s: int((s == "purchase").any())),
                  last_ts=("event_ts", "max")).reset_index())

    # ---------------- write
    for name, df in {"events": ev, "orders": od, "ratings": rt, "products": prod, "users": users,
                     "interactions": inter}.items():
        df.drop(columns=[c for c in df.columns if c == "_source_file"]).to_parquet(PROCESSED / f"{name}.parquet", index=False)
    qsum = {}
    for name, parts in q.items():
        qdf = pd.concat(parts)
        qdf.astype(str).to_csv(QUARANTINE / f"{name}_quarantine.csv", index=False)
        qsum[name] = qdf["_reason"].value_counts().to_dict()
    n_u, n_i = inter["user_id"].nunique(), inter["product_id"].nunique()
    summary["interactions"] = {"pairs": len(inter), "users": n_u, "items": n_i,
                               "sparsity_pct": round(100 * (1 - len(inter) / (n_u * n_i)), 2)}
    summary["quarantine"] = qsum
    (PROCESSED / "_prep_summary.json").write_text(json.dumps(summary, indent=1))
    log.info(f"prepared: {json.dumps({k: v.get('clean', v.get('pairs')) for k, v in summary.items() if k != 'quarantine'})}")
    log.info(f"quarantined: {qsum}")
    audit("preparation", **{k: v.get("clean") for k, v in summary.items() if isinstance(v, dict) and "clean" in v})
    return summary


if __name__ == "__main__":
    print(json.dumps(prepare(), indent=1, default=str))

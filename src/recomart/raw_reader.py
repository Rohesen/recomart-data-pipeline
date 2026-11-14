"""Read raw-lake partitions back into DataFrames (shared by validation and preparation)."""
from __future__ import annotations

import json
from pathlib import Path

import pandas as pd

from .storage import LakeStorage

# Known upstream column renames (schema drift) -> canonical names
ALIASES = {"userId": "user_id", "productId": "product_id", "eventType": "event_type"}
EXPECTED = {
    "events": ["event_ts", "user_id", "product_id", "event_type", "session_id", "device", "channel"],
    "orders": ["order_id", "user_id", "product_id", "quantity", "unit_price", "discount_pct", "payment_mode", "order_ts"],
    "reviews": ["user_id", "product_id", "rating", "rated_ts"],
    "profiles": ["user_id", "signup_date", "age_band", "gender", "city_tier", "preferred_device"],
    "products": ["product_id", "title", "category", "sub_category", "brand", "price", "launch_date", "in_stock"],
    "scores": ["product_id", "popularity_score", "sentiment_score", "social_mentions"],
}
SOURCES = {"events": "clickstream", "orders": "transactions", "reviews": "ratings", "profiles": "users",
           "products": "catalog_api", "scores": "popularity_api"}


def read_files(dtype: str) -> list[tuple[Path, pd.DataFrame]]:
    files = LakeStorage.list_partition(SOURCES[dtype], dtype)
    out = []
    for f in files:
        if f.suffix == ".json":
            out.append((f, pd.DataFrame(json.loads(f.read_text())["items"])))
        else:
            out.append((f, pd.read_csv(f, dtype=str, keep_default_na=True)))
    return out


def read_dataset(dtype: str, harmonize: bool = True, latest_only: bool | None = None) -> pd.DataFrame:
    parts = read_files(dtype)
    if latest_only is None:
        latest_only = dtype in ("products", "scores", "profiles")     # snapshots: newest wins
    if latest_only:
        parts = parts[-1:]
    frames = []
    for f, df in parts:
        if harmonize:
            df = df.rename(columns=ALIASES)
        frames.append(df.assign(_source_file=f.name))
    return pd.concat(frames, ignore_index=True) if frames else pd.DataFrame(columns=EXPECTED[dtype])

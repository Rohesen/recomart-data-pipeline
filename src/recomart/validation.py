"""Automated data-quality validation of the raw lake (pandera schemas + custom checks).

Checks per dataset: schema (missing / unexpected columns per file), completeness (missing values),
uniqueness (duplicate rows / keys), validity (ranges, allowed values, ID and timestamp formats)
and referential integrity (events must reference known products and users).

    python -m recomart.validation      # writes reports/dq/dq_results.json (+ PDF via dq_report)
"""
from __future__ import annotations

import json
from datetime import datetime, timezone

import pandas as pd

try:                                   # pandera >= 0.20
    import pandera.pandas as pa
except ImportError:                    # older pandera (Python 3.9 lab image)
    import pandera as pa

from .config import REPORTS, cfg
from .logging_utils import audit, get_logger
from .raw_reader import EXPECTED, read_dataset, read_files

log = get_logger("validation")
DQ_DIR = REPORTS / "dq"

UID, PID = r"^U\d{5}$", r"^P\d{5}$"
EVENTS = ["view", "wishlist", "add_to_cart", "purchase"]
CATS = ["Electronics", "Fashion", "Home", "Beauty", "Sports", "Books", "Grocery", "Toys"]


def _num(s):
    return pd.to_numeric(s, errors="coerce")


def _ts_ok(s):
    return pd.to_datetime(s, errors="coerce", format="mixed").notna()


def schemas() -> dict:
    v = cfg()["validation"]
    C = pa.Check
    return {
        "events": pa.DataFrameSchema({
            "event_ts": pa.Column(str, [C(_ts_ok, element_wise=False, error="timestamp format")], nullable=False),
            "user_id": pa.Column(str, C.str_matches(UID), nullable=False),
            "product_id": pa.Column(str, C.str_matches(PID), nullable=False),
            "event_type": pa.Column(str, C.isin(EVENTS), nullable=False),
            "session_id": pa.Column(str, nullable=False),
            "device": pa.Column(str, C.isin(["android", "ios", "web"]), nullable=False),
            "channel": pa.Column(str, C.isin(["web", "app"]), nullable=False),
        }, strict=False, coerce=False),
        "orders": pa.DataFrameSchema({
            "order_id": pa.Column(str, C.str_matches(r"^O\d+$"), nullable=False),
            "user_id": pa.Column(str, C.str_matches(UID), nullable=False),
            "product_id": pa.Column(str, C.str_matches(PID), nullable=False),
            "quantity": pa.Column(str, C(lambda s: _num(s) >= 1, element_wise=False, error="quantity >= 1")),
            "unit_price": pa.Column(str, C(lambda s: _num(s) > 0, element_wise=False, error="unit_price > 0")),
            "discount_pct": pa.Column(str, C(lambda s: _num(s).between(0, 90), element_wise=False, error="discount 0-90")),
            "payment_mode": pa.Column(str, C.isin(["UPI", "card", "COD", "netbanking"])),
            "order_ts": pa.Column(str, C(_ts_ok, element_wise=False, error="timestamp format")),
        }, strict=False),
        "reviews": pa.DataFrameSchema({
            "user_id": pa.Column(str, C.str_matches(UID), nullable=False),
            "product_id": pa.Column(str, C.str_matches(PID), nullable=False),
            "rating": pa.Column(str, C(lambda s: _num(s).between(v["rating_min"], v["rating_max"]), element_wise=False,
                                       error=f"rating {v['rating_min']}-{v['rating_max']}"), nullable=False),
            "rated_ts": pa.Column(str, C(_ts_ok, element_wise=False, error="timestamp format")),
        }, strict=False),
        "profiles": pa.DataFrameSchema({
            "user_id": pa.Column(str, C.str_matches(UID), nullable=False, unique=True),
            "age_band": pa.Column(str, C.isin(["18-24", "25-34", "35-44", "45-54", "55+"])),
            "gender": pa.Column(str, C.isin(["F", "M", "Other"])),
            "city_tier": pa.Column(str, C.isin(["tier1", "tier2", "tier3"])),
        }, strict=False),
        "products": pa.DataFrameSchema({
            "product_id": pa.Column(str, C.str_matches(PID), nullable=False, unique=True),
            "title": pa.Column(str, nullable=False),
            "category": pa.Column(str, C.isin(CATS)),
            "brand": pa.Column(str, nullable=False),
            "price": pa.Column(float, C.gt(0), nullable=False),
        }, strict=False, coerce=True),
        "scores": pa.DataFrameSchema({
            "product_id": pa.Column(str, C.str_matches(PID), unique=True),
            "popularity_score": pa.Column(float, C.in_range(0, 100)),
            "sentiment_score": pa.Column(float, C.in_range(-1, 1)),
        }, strict=False, coerce=True),
    }


def _schema_drift(dtype: str) -> list[dict]:
    drift = []
    for f, df in read_files(dtype):
        missing = sorted(set(EXPECTED[dtype]) - set(df.columns))
        extra = sorted(set(df.columns) - set(EXPECTED[dtype]))
        if missing or extra:
            drift.append({"file": f.name, "missing_columns": missing, "unexpected_columns": extra})
    return drift


def validate_dataset(dtype: str, ref: dict) -> dict:
    v = cfg()["validation"]
    df = read_dataset(dtype)
    data = df.drop(columns=["_source_file"])
    n = len(data)
    missing = (data.isna().mean() * 100).round(3).to_dict()
    dup_rows = int(data.duplicated().sum())
    checks = []

    def add(name, column, failures, kind, threshold_pct=0.0):
        pct = round(100 * failures / max(n, 1), 3)
        checks.append({"check": name, "column": column, "kind": kind, "failures": int(failures), "pct": pct,
                       "status": "PASS" if pct <= threshold_pct else ("WARN" if pct <= 5 else "FAIL")})

    drift = _schema_drift(dtype)
    checks.append({"check": "schema matches contract", "column": "*", "kind": "schema",
                   "failures": len(drift), "pct": 0.0, "status": "PASS" if not drift else "WARN"})
    for col, pct in missing.items():
        if pct > 0:
            add("not null", col, round(pct * n / 100), "completeness", v["max_missing_pct"])
    add("no duplicate rows", "*", dup_rows, "uniqueness", v["max_duplicate_pct"])

    try:
        schemas()[dtype].validate(data, lazy=True)
    except pa.errors.SchemaErrors as e:
        fc = e.failure_cases
        fc = fc[fc["check"].astype(str) != "not_nullable"]            # nulls are reported above
        for (col, chk), grp in fc.groupby(["column", "check"], dropna=False):
            kind = "uniqueness" if "unique" in str(chk) or "field_uniqueness" in str(chk) else "validity"
            add(str(chk), str(col), len(grp), kind, 0.0 if kind == "uniqueness" else 0.5)

    if dtype in ("events", "orders", "reviews"):
        orphan_p = int((~data["product_id"].isin(ref["products"])).sum())
        orphan_u = int((~data["user_id"].isin(ref["users"]) & data["user_id"].notna()).sum())
        add("product exists in catalog", "product_id", orphan_p, "referential", 0.5)
        add("user exists in CRM", "user_id", orphan_u, "referential", 0.5)

    status = "FAIL" if any(c["status"] == "FAIL" for c in checks) else (
        "WARN" if any(c["status"] == "WARN" for c in checks) else "PASS")
    return {"dataset": dtype, "rows": n, "columns": len(data.columns), "files": int(df["_source_file"].nunique()),
            "missing_pct": missing, "duplicate_rows": dup_rows, "duplicate_pct": round(100 * dup_rows / max(n, 1), 3),
            "schema_drift": drift, "checks": checks, "status": status,
            "checks_passed": sum(c["status"] == "PASS" for c in checks), "checks_total": len(checks)}


def run_validation() -> dict:
    DQ_DIR.mkdir(parents=True, exist_ok=True)
    ref = {"products": set(read_dataset("products")["product_id"].dropna()),
           "users": set(read_dataset("profiles")["user_id"].dropna())}
    results = [validate_dataset(d, ref) for d in ("events", "orders", "reviews", "profiles", "products", "scores")]
    total = sum(r["checks_total"] for r in results); passed = sum(r["checks_passed"] for r in results)
    out = {"generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
           "quality_score": round(100 * passed / max(total, 1), 1), "checks_passed": passed, "checks_total": total,
           "datasets": results}
    (DQ_DIR / "dq_results.json").write_text(json.dumps(out, indent=1, default=str))
    for r in results:
        lvl = log.warning if r["status"] != "PASS" else log.info
        lvl(f"{r['dataset']}: {r['rows']:,} rows, {r['checks_passed']}/{r['checks_total']} checks passed -> {r['status']}")
    audit("validation", quality_score=out["quality_score"], checks=f"{passed}/{total}")
    return out


if __name__ == "__main__":
    o = run_validation()
    print(json.dumps({"quality_score": o["quality_score"],
                      "datasets": {d["dataset"]: d["status"] for d in o["datasets"]}}, indent=1))

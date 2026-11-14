"""Simulates RecoMart's source systems (seeded, so every run is reproducible).

Produces what the real platform would expose to the data team:
  * data/landing/clickstream/clickstream_YYYYMMDD.csv     web + app event logs (daily drops)
  * data/landing/transactions/transactions_YYYYMMDD.csv   order system extracts
  * data/landing/ratings/ratings_YYYYMMDD.csv             product reviews
  * data/sources/catalog.json, popularity.json            behind the catalog REST API (mock_api.py)

Behaviour is driven by a latent-preference model (category affinity + latent taste + item
popularity), so recommendation models have real signal to learn. Realistic data-quality issues
are injected on purpose so the validation stage has something to catch.
"""
from __future__ import annotations

import json
from datetime import datetime, timedelta

import numpy as np
import pandas as pd

from .config import DATA, LANDING, cfg

CATEGORIES = {
    "Electronics": (["Mobiles", "Audio", "Laptops", "Accessories"], ["Noventa", "Kyron", "Zentek", "Aurix"], (999, 69999)),
    "Fashion": (["Men", "Women", "Footwear", "Watches"], ["Urbanloom", "Vastra", "Strider", "Kalaa"], (299, 4999)),
    "Home": (["Kitchen", "Decor", "Furniture", "Storage"], ["Gharsa", "Nestwell", "Oakline", "Bartan"], (199, 24999)),
    "Beauty": (["Skincare", "Haircare", "Makeup", "Fragrance"], ["Glowveda", "Rasa", "Lumiere", "Tvacha"], (149, 2999)),
    "Sports": (["Fitness", "Cricket", "Cycling", "Yoga"], ["Kheltek", "Stamina", "Pacer", "Asana"], (249, 19999)),
    "Books": (["Fiction", "Technology", "Self-help", "Exam Prep"], ["Penline", "Kitaab", "Folio", "Varnam"], (99, 1499)),
    "Grocery": (["Staples", "Snacks", "Beverages", "Organic"], ["Annapurna", "Kisan", "Chai Co", "Sattva"], (49, 1999)),
    "Toys": (["Learning", "Outdoor", "Puzzles", "Dolls"], ["Khilona", "Funbox", "Brainy", "Pari"], (149, 4999)),
}
ADJ = ["Classic", "Pro", "Lite", "Max", "Eco", "Smart", "Premium", "Essential", "Ultra", "Plus"]
CITIES = {"tier1": 0.45, "tier2": 0.35, "tier3": 0.20}
SRC_DIR = DATA / "sources"


def _rng(offset=0):
    return np.random.default_rng(cfg()["seed"] + offset)


def make_catalog(n_products: int):
    rng = _rng(1)
    cats = list(CATEGORIES)
    rows = []
    for i in range(n_products):
        cat = cats[i % len(cats)] if i < len(cats) * 4 else rng.choice(cats)
        subs, brands, (lo, hi) = CATEGORIES[cat]
        sub, brand = rng.choice(subs), rng.choice(brands)
        price = float(np.round(np.exp(rng.uniform(np.log(lo), np.log(hi))), -0))
        rows.append({
            "product_id": f"P{10001 + i}",
            "title": f"{brand} {rng.choice(ADJ)} {sub[:-1] if sub.endswith('s') else sub}",
            "category": cat, "sub_category": sub, "brand": brand, "price": price,
            "launch_date": str((pd.Timestamp("2025-01-01") + pd.Timedelta(days=int(rng.integers(0, 560)))).date()),
            "in_stock": bool(rng.random() > 0.05),
        })
    cat_df = pd.DataFrame(rows)
    # injected catalog issues: negative price, missing brand
    cat_df.loc[cat_df.sample(2, random_state=3).index, "price"] = -1.0
    cat_df.loc[cat_df.sample(3, random_state=4).index, "brand"] = None
    return cat_df


def simulate(write: bool = True) -> dict:
    c = cfg()["simulation"]
    rng = _rng(2)
    n_u, n_p, days = c["n_users"], c["n_products"], c["days"]
    start = pd.Timestamp(c["start_date"])
    catalog = make_catalog(n_p)
    cats = list(CATEGORIES)
    cat_idx = catalog["category"].map({k: i for i, k in enumerate(cats)}).values

    # ---- users
    users = pd.DataFrame({
        "user_id": [f"U{20001 + i}" for i in range(n_u)],
        "signup_date": [str((start - pd.Timedelta(days=int(d))).date()) for d in rng.integers(0, 700, n_u)],
        "age_band": rng.choice(["18-24", "25-34", "35-44", "45-54", "55+"], n_u, p=[.24, .36, .22, .12, .06]),
        "gender": rng.choice(["F", "M", "Other"], n_u, p=[.47, .5, .03]),
        "city_tier": rng.choice(list(CITIES), n_u, p=list(CITIES.values())),
        "preferred_device": rng.choice(["android", "ios", "web"], n_u, p=[.55, .2, .25]),
    })

    # ---- latent preference model
    pref = rng.dirichlet(np.full(len(cats), 0.45), n_u)              # category affinity (peaked)
    d = 8
    U = rng.normal(0, 1, (n_u, d)); V = rng.normal(0, 1, (n_p, d))
    pop = rng.lognormal(0, 1.25, n_p)                                  # intrinsic popularity (long tail)
    activity = rng.lognormal(0, 0.8, n_u); activity /= activity.mean()
    score = np.log(pref[:, cat_idx] + 1e-3) + 0.55 * (U @ V.T) / np.sqrt(d) + 1.0 * np.log(pop)[None, :]
    score[:, catalog["price"].values < 0] -= 5

    events, orders, ratings = [], [], []
    oid = 500001
    for day in range(days):
        date = start + pd.Timedelta(days=day)
        weekend = date.dayofweek >= 5
        p_active = np.clip(0.07 * activity * (1.25 if weekend else 1.0), 0, 0.9)
        active = np.where(rng.random(n_u) < p_active)[0]
        for u in active:
            for _ in range(1 + rng.poisson(0.4)):
                sid = f"S{rng.integers(1e8, 1e9)}"
                t = date + pd.Timedelta(minutes=int(rng.normal(20 * 60, 4 * 60)) % (24 * 60))
                device = users.at[u, "preferred_device"] if rng.random() < .8 else rng.choice(["android", "ios", "web"])
                cat = rng.choice(len(cats), p=pref[u])
                mask = cat_idx == cat if rng.random() < .8 else np.ones(n_p, bool)
                s = score[u] * mask + (~mask) * -1e9
                prob = np.exp(s - s.max()); prob /= prob.sum()
                n_views = 2 + rng.poisson(3)
                items = rng.choice(n_p, size=min(n_views, mask.sum()), replace=False, p=prob)
                for it in items:
                    t += pd.Timedelta(seconds=int(rng.integers(15, 240)))
                    aff = score[u, it] - score[u].mean()
                    events.append((t, users.at[u, "user_id"], catalog.at[it, "product_id"], "view", sid, device))
                    if rng.random() < 0.05 + 0.04 * max(aff, 0):
                        events.append((t + pd.Timedelta(seconds=20), users.at[u, "user_id"], catalog.at[it, "product_id"],
                                       "wishlist", sid, device))
                    if rng.random() < 0.10 + 0.06 * max(aff, 0):
                        t += pd.Timedelta(seconds=40)
                        events.append((t, users.at[u, "user_id"], catalog.at[it, "product_id"], "add_to_cart", sid, device))
                        if rng.random() < 0.45:
                            t += pd.Timedelta(seconds=90)
                            events.append((t, users.at[u, "user_id"], catalog.at[it, "product_id"], "purchase", sid, device))
                            price = abs(catalog.at[it, "price"]); disc = float(rng.choice([0, 0, 5, 10, 15, 20]))
                            qty = int(1 + rng.poisson(0.2))
                            orders.append((f"O{oid}", users.at[u, "user_id"], catalog.at[it, "product_id"], qty,
                                           round(price * (1 - disc / 100), 2), disc,
                                           rng.choice(["UPI", "card", "COD", "netbanking"], p=[.55, .2, .15, .1]), t))
                            oid += 1
                            if rng.random() < 0.35:
                                z = (score[u, it] - score[u].mean()) / score[u].std()
                                r = int(np.clip(np.round(2.7 + 0.55 * z + rng.normal(0, 0.95)), 1, 5))
                                ratings.append((users.at[u, "user_id"], catalog.at[it, "product_id"], r,
                                                t + pd.Timedelta(days=int(rng.integers(1, 6)))))

    ev = pd.DataFrame(events, columns=["event_ts", "user_id", "product_id", "event_type", "session_id", "device"])
    ev["channel"] = np.where(ev["device"] == "web", "web", "app")
    tx = pd.DataFrame(orders, columns=["order_id", "user_id", "product_id", "quantity", "unit_price",
                                       "discount_pct", "payment_mode", "order_ts"])
    rt = pd.DataFrame(ratings, columns=["user_id", "product_id", "rating", "rated_ts"])
    rt = rt[rt["rated_ts"] < start + pd.Timedelta(days=days)]

    # ---- external popularity / sentiment feed (noisy view of the latent popularity)
    popularity = pd.DataFrame({
        "product_id": catalog["product_id"],
        "popularity_score": np.round(100 * (np.log(pop) - np.log(pop).min()) / np.ptp(np.log(pop)) + rng.normal(0, 4, n_p), 1).clip(0, 100),
        "sentiment_score": np.round(np.tanh(rng.normal(0.3, 0.5, n_p)), 3),
        "social_mentions": rng.poisson(pop * 40),
    })

    if write:
        _write_sources(catalog, popularity)
        _write_landing(ev, tx, rt, start, days, rng)
    return {"users": users, "catalog": catalog, "events": ev, "orders": tx, "ratings": rt, "popularity": popularity}


def _write_sources(catalog, popularity):
    SRC_DIR.mkdir(parents=True, exist_ok=True)
    (SRC_DIR / "catalog.json").write_text(catalog.to_json(orient="records", indent=0))
    (SRC_DIR / "popularity.json").write_text(popularity.to_json(orient="records", indent=0))


def _inject(df: pd.DataFrame, rng, dup=0.0, null_cols=None, orphan_col=None):
    if dup:
        df = pd.concat([df, df.sample(frac=dup, random_state=int(rng.integers(1e6)))])
    for col, frac in (null_cols or {}).items():
        idx = df.sample(frac=frac, random_state=int(rng.integers(1e6))).index
        df.loc[idx, col] = None
    if orphan_col:
        idx = df.sample(frac=0.002, random_state=int(rng.integers(1e6))).index
        df.loc[idx, orphan_col] = "P99999"
    return df


def _write_landing(ev, tx, rt, start, days, rng):
    for sub in ("clickstream", "transactions", "ratings"):
        (LANDING / sub).mkdir(parents=True, exist_ok=True)
    for day in range(days):
        d0 = start + pd.Timedelta(days=day); d1 = d0 + pd.Timedelta(days=1); tag = d0.strftime("%Y%m%d")
        e = ev[(ev.event_ts >= d0) & (ev.event_ts < d1)].copy().reset_index(drop=True)
        e = _inject(e, rng, dup=0.015, null_cols={"device": 0.01, "session_id": 0.003}, orphan_col="product_id")
        e["event_ts"] = e["event_ts"].astype(str)
        bad = e.sample(frac=0.001, random_state=day).index
        e.loc[bad, "event_ts"] = "not-a-date"
        if day == 37:                                   # upstream schema drift: app release renamed a column
            e = e.rename(columns={"user_id": "userId"})
        e.to_csv(LANDING / "clickstream" / f"clickstream_{tag}.csv", index=False)

        t = tx[(tx.order_ts >= d0) & (tx.order_ts < d1)].copy().reset_index(drop=True)
        if len(t):
            idx = t.sample(frac=0.01, random_state=day).index
            t.loc[idx, "quantity"] = -1
            t = _inject(t, rng, dup=0.01)
            t.to_csv(LANDING / "transactions" / f"transactions_{tag}.csv", index=False)

        r = rt[(rt.rated_ts >= d0) & (rt.rated_ts < d1)].copy().reset_index(drop=True)
        if len(r):
            idx = r.sample(frac=0.02, random_state=day + 7).index
            r.loc[idx, "rating"] = rng.choice([0, 6, 7], len(idx))
            r = _inject(r, rng, null_cols={"rating": 0.005})
            r.to_csv(LANDING / "ratings" / f"ratings_{tag}.csv", index=False)


def write_users(users: pd.DataFrame):
    """CRM export of user profiles (daily full snapshot)."""
    (LANDING / "users").mkdir(parents=True, exist_ok=True)
    end = pd.Timestamp(cfg()["simulation"]["start_date"]) + pd.Timedelta(days=cfg()["simulation"]["days"] - 1)
    users.to_csv(LANDING / "users" / f"users_{end:%Y%m%d}.csv", index=False)


def simulate_stream(n_batches: int | None = None) -> list[str]:
    """Near-real-time: drop small micro-batch files into the landing zone (as a Kafka consumer
    or app gateway would), to be picked up by the next ingestion poll."""
    n_batches = n_batches or cfg()["simulation"]["stream_batches"]
    daily = sorted(f for f in (LANDING / "clickstream").glob("clickstream_*.csv") if "_mb" not in f.name)
    ev = pd.read_csv(daily[-1]).dropna().sample(60 * n_batches, random_state=int(datetime.now().timestamp()) % 9999,
                                                replace=True).reset_index(drop=True)
    ev = ev.rename(columns={"userId": "user_id"})
    # micro-batches belong to the last simulated day ("today" in the simulation's timeline)
    c = cfg()["simulation"]
    today = pd.Timestamp(c["start_date"]) + pd.Timedelta(days=c["days"] - 1)
    wall = datetime.now()
    out = []
    for b in range(n_batches):
        part = ev.iloc[b * 60:(b + 1) * 60].copy()
        base = today + pd.Timedelta(hours=wall.hour, minutes=wall.minute, seconds=wall.second)
        part["event_ts"] = [str(base + pd.Timedelta(seconds=i)) for i in range(len(part))]
        name = f"clickstream_{today:%Y%m%d}_{wall:%H%M%S}_mb{b + 1}.csv"
        part.to_csv(LANDING / "clickstream" / name, index=False)
        out.append(name)
    return out


def generate_all() -> dict:
    data = simulate(write=True)
    write_users(data["users"])
    return {k: len(v) for k, v in data.items()}


if __name__ == "__main__":
    print(json.dumps(generate_all(), indent=2))

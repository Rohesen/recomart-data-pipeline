"""Exploratory data analysis on the prepared data: distributions, popularity long tail, sparsity.

    python -m recomart.eda          # writes reports/figures/*.png and reports/eda_summary.json
"""
from __future__ import annotations

import json

import numpy as np
import pandas as pd

from .config import FIGURES, PROCESSED, REPORTS
from .plotting import GREY, INK, OCHRE, OLIVE, RUST, plt, style


def load():
    return {n: pd.read_parquet(PROCESSED / f"{n}.parquet")
            for n in ("events", "orders", "ratings", "products", "users", "interactions")}


def gini(x):
    x = np.sort(np.asarray(x, float)); n = len(x)
    return float((2 * np.arange(1, n + 1) - n - 1).dot(x) / (n * x.sum()))


def run_eda(show: bool = False) -> dict:
    style(); FIGURES.mkdir(parents=True, exist_ok=True)
    d = load(); ev, inter, prod, rt = d["events"], d["interactions"], d["products"], d["ratings"]
    figs = {}

    def save(fig, name):
        fig.savefig(FIGURES / f"{name}.png"); figs[name] = f"reports/figures/{name}.png"
        if not show:
            plt.close(fig)

    # 1 event funnel
    fig, ax = plt.subplots(figsize=(6, 3.4))
    order = ["view", "wishlist", "add_to_cart", "purchase"]
    cnt = ev["event_type"].value_counts().reindex(order)
    ax.bar(order, cnt.values, color=[GREY, OCHRE, OLIVE, RUST])
    for i, v in enumerate(cnt.values):
        ax.text(i, v, f"{v:,}", ha="center", va="bottom", fontsize=8)
    ax.set_title("Interaction distribution by event type (funnel)"); ax.set_ylabel("events")
    save(fig, "01_event_funnel")

    # 2 interactions per user (long tail)
    per_user = inter.groupby("user_id")["n_events"].sum()
    fig, ax = plt.subplots(figsize=(6, 3.4))
    ax.hist(per_user, bins=50, color=INK); ax.set_yscale("log")
    ax.set_title("Interactions per user"); ax.set_xlabel("events per user"); ax.set_ylabel("users (log)")
    save(fig, "02_interactions_per_user")

    # 3 item popularity long tail + Lorenz
    item_cnt = inter.groupby("product_id")["n_events"].sum().sort_values(ascending=False)
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.4))
    axs[0].plot(np.arange(1, len(item_cnt) + 1), item_cnt.values, color=RUST)
    axs[0].set_yscale("log"); axs[0].set_title("Item popularity (long tail)")
    axs[0].set_xlabel("item rank"); axs[0].set_ylabel("events (log)")
    cum = np.cumsum(np.sort(item_cnt.values)) / item_cnt.sum()
    axs[1].plot(np.linspace(0, 1, len(cum)), cum, color=INK, label="Lorenz curve")
    axs[1].plot([0, 1], [0, 1], "--", color=GREY, label="equality")
    g = gini(item_cnt.values)
    axs[1].set_title(f"Concentration of interactions (Gini = {g:.2f})"); axs[1].legend(fontsize=8)
    axs[1].set_xlabel("share of items"); axs[1].set_ylabel("share of interactions")
    save(fig, "03_item_popularity")

    # 4 sparsity heatmap (most active users x most popular items)
    top_u = per_user.sort_values(ascending=False).index[:60]; top_i = item_cnt.index[:60]
    m = (inter[inter.user_id.isin(top_u) & inter.product_id.isin(top_i)]
         .pivot_table(index="user_id", columns="product_id", values="strength", aggfunc="sum")
         .reindex(index=top_u, columns=top_i))
    fig, ax = plt.subplots(figsize=(6.5, 5))
    im = ax.imshow(np.log1p(m.fillna(0).values), cmap="Greys", aspect="auto")
    ax.set_title("User-item matrix (top 60 x top 60, log strength)")
    ax.set_xlabel("items (by popularity)"); ax.set_ylabel("users (by activity)")
    ax.set_xticks([]); ax.set_yticks([]); fig.colorbar(im, ax=ax, fraction=0.04)
    save(fig, "04_sparsity_heatmap")

    # 5 ratings
    fig, ax = plt.subplots(figsize=(6, 3.4))
    rc = rt["rating"].value_counts().sort_index()
    ax.bar(rc.index.astype(str), rc.values, color=OCHRE)
    ax.set_title(f"Rating distribution (mean {rt['rating'].mean():.2f})"); ax.set_xlabel("rating"); ax.set_ylabel("reviews")
    save(fig, "05_rating_distribution")

    # 6 category x event heatmap (conversion by category)
    ce = ev.merge(prod[["product_id", "category"]], on="product_id").pivot_table(
        index="category", columns="event_type", values="user_id", aggfunc="count").reindex(columns=order)
    conv = (ce["purchase"] / ce["view"] * 100).round(1)
    fig, ax = plt.subplots(figsize=(6.5, 4))
    im = ax.imshow(np.log10(ce.values), cmap="Greys", aspect="auto")
    ax.set_xticks(range(len(order))); ax.set_xticklabels(order); ax.set_yticks(range(len(ce)))
    ax.set_yticklabels([f"{c}  ({conv[c]}% conv.)" for c in ce.index])
    for i in range(ce.shape[0]):
        for j in range(ce.shape[1]):
            v = ce.values[i, j]
            ax.text(j, i, f"{int(v):,}", ha="center", va="center", fontsize=7,
                    color="white" if np.log10(v) > np.log10(ce.values).mean() else INK)
    ax.set_title("Events by category (view-to-purchase conversion)"); ax.grid(False)
    save(fig, "06_category_event_heatmap")

    # 7 daily activity
    daily = ev.set_index("event_ts").resample("D")["user_id"].count()
    fig, ax = plt.subplots(figsize=(9, 3))
    ax.plot(daily.index, daily.values, color=INK, lw=1.2)
    ax.set_title("Daily events (weekly seasonality)"); ax.set_ylabel("events")
    save(fig, "07_daily_activity")

    # 8 price normalisation
    fig, axs = plt.subplots(1, 2, figsize=(9, 3.2))
    axs[0].hist(prod["price"], bins=40, color=GREY); axs[0].set_title("Price (raw, INR)")
    axs[1].hist(prod["log_price_z"], bins=40, color=OLIVE); axs[1].set_title("Price after log + z-score")
    save(fig, "08_price_normalisation")

    n_u, n_i = inter.user_id.nunique(), inter.product_id.nunique()
    summary = {
        "events": int(len(ev)), "users_active": int(n_u), "items_interacted": int(n_i),
        "user_item_pairs": int(len(inter)), "sparsity_pct": round(100 * (1 - len(inter) / (n_u * n_i)), 2),
        "purchase_pairs_sparsity_pct": round(100 * (1 - inter["purchased"].sum() / (n_u * n_i)), 2),
        "item_popularity_gini": round(g, 3), "top10pct_items_share": round(
            float(item_cnt.iloc[: max(1, len(item_cnt) // 10)].sum() / item_cnt.sum()), 3),
        "median_events_per_user": float(per_user.median()), "mean_rating": round(float(rt["rating"].mean()), 2),
        "view_to_purchase_pct": round(100 * cnt["purchase"] / cnt["view"], 2), "figures": figs,
    }
    (REPORTS / "eda_summary.json").write_text(json.dumps(summary, indent=1))
    return summary


if __name__ == "__main__":
    print(json.dumps(run_eda(), indent=1))

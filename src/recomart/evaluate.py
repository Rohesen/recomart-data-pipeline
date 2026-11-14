"""Ranking metrics for top-K recommendation (binary relevance).

  Precision@K = |rec_K ∩ relevant| / K
  Recall@K    = |rec_K ∩ relevant| / |relevant|
  NDCG@K      = DCG@K / IDCG@K, DCG = Σ rel_i / log2(i + 1)   (position-aware)
  HitRate@K   = share of users with at least one relevant item in the top K
  MAP@K       = mean of average precision at K
  Coverage    = share of the catalogue that appears in anyone's top K
"""
from __future__ import annotations

import numpy as np


def precision_at_k(rec, rel, k):
    return len(set(rec[:k]) & rel) / k


def recall_at_k(rec, rel, k):
    return len(set(rec[:k]) & rel) / len(rel) if rel else 0.0


def ndcg_at_k(rec, rel, k):
    dcg = sum(1 / np.log2(i + 2) for i, p in enumerate(rec[:k]) if p in rel)
    idcg = sum(1 / np.log2(i + 2) for i in range(min(len(rel), k)))
    return dcg / idcg if idcg else 0.0


def ap_at_k(rec, rel, k):
    hits, s = 0, 0.0
    for i, p in enumerate(rec[:k]):
        if p in rel:
            hits += 1; s += hits / (i + 1)
    return s / min(len(rel), k) if rel else 0.0


def evaluate(recs: dict[str, list[str]], truth: dict[str, set], k: int, n_catalog: int) -> dict:
    users = [u for u in truth if u in recs and truth[u]]
    m = {f"precision_at_{k}": np.mean([precision_at_k(recs[u], truth[u], k) for u in users]),
         f"recall_at_{k}": np.mean([recall_at_k(recs[u], truth[u], k) for u in users]),
         f"ndcg_at_{k}": np.mean([ndcg_at_k(recs[u], truth[u], k) for u in users]),
         f"hit_rate_at_{k}": np.mean([len(set(recs[u][:k]) & truth[u]) > 0 for u in users]),
         f"map_at_{k}": np.mean([ap_at_k(recs[u], truth[u], k) for u in users]),
         "catalog_coverage": len({p for u in users for p in recs[u][:k]}) / n_catalog,
         "eval_users": len(users)}
    return {key: round(float(v), 4) for key, v in m.items()}

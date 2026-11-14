"""Recommendation models. All share one interface: fit(train_interactions) and scores(user_ids).

  PopularityRecommender  - baseline: most-engaged items in the training window
  SVDRecommender         - collaborative filtering, matrix factorisation (truncated SVD) of the
                           user x item implicit-feedback matrix, log(1 + weighted events)
  ContentRecommender     - content-based: TF-IDF of title/category/sub-category/brand; a user's
                           profile is the strength-weighted mean of the items they engaged with
  HybridRecommender      - weighted blend of SVD, item co-occurrence (from the feature store) and
                           content scores, each min-max normalised per user
"""
from __future__ import annotations

import numpy as np
import pandas as pd
from scipy.sparse import csr_matrix
from sklearn.decomposition import TruncatedSVD
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.preprocessing import normalize


class BaseRecommender:
    name = "base"

    def fit(self, inter: pd.DataFrame, products: pd.DataFrame, **kw):
        self.users = np.array(sorted(inter["user_id"].unique()))
        self.items = np.array(sorted(products["product_id"].unique()))
        self.uidx = {u: i for i, u in enumerate(self.users)}
        self.iidx = {p: i for i, p in enumerate(self.items)}
        rows = inter["user_id"].map(self.uidx).values
        cols = inter["product_id"].map(self.iidx).values
        self.R = csr_matrix((np.log1p(inter["strength"].values), (rows, cols)), shape=(len(self.users), len(self.items)))
        self.popularity = np.asarray(self.R.sum(axis=0)).ravel()
        self._fit(inter, products, **kw)
        return self

    def _fit(self, inter, products, **kw):
        pass

    def _scores(self, uix: np.ndarray) -> np.ndarray:
        raise NotImplementedError

    def recommend(self, user_ids, k: int = 10, exclude_seen: bool = True) -> dict[str, list[tuple[str, float]]]:
        known = [u for u in user_ids if u in self.uidx]
        out = {u: self.cold_start(k) for u in user_ids if u not in self.uidx}
        if known:
            uix = np.array([self.uidx[u] for u in known])
            S = self._scores(uix).astype(float)
            if exclude_seen:
                seen = self.R[uix].toarray() > 0
                S[seen] = -np.inf
            top = np.argpartition(-S, kth=min(k, S.shape[1] - 1), axis=1)[:, :k]
            for r, u in enumerate(known):
                idx = top[r][np.argsort(-S[r, top[r]])]
                out[u] = [(self.items[i], float(S[r, i])) for i in idx]
        return out

    def cold_start(self, k: int):
        idx = np.argsort(-self.popularity)[:k]
        return [(self.items[i], float(self.popularity[i])) for i in idx]

    def params(self) -> dict:
        return {}


class PopularityRecommender(BaseRecommender):
    name = "popularity"

    def _scores(self, uix):
        return np.tile(self.popularity, (len(uix), 1))


class SVDRecommender(BaseRecommender):
    name = "svd"

    def __init__(self, n_factors: int = 48, seed: int = 42):
        self.n_factors, self.seed = n_factors, seed

    def _fit(self, inter, products, **kw):
        k = min(self.n_factors, min(self.R.shape) - 1)
        svd = TruncatedSVD(n_components=k, random_state=self.seed)
        self.P = svd.fit_transform(self.R)            # user factors  (U * Sigma)
        self.Q = svd.components_.T                    # item factors  (V)
        self.explained_variance = float(svd.explained_variance_ratio_.sum())

    def _scores(self, uix):
        return self.P[uix] @ self.Q.T

    def params(self):
        return {"n_factors": self.n_factors}


class ContentRecommender(BaseRecommender):
    name = "content"

    def _fit(self, inter, products, **kw):
        prods = products.set_index("product_id").reindex(self.items)
        text = (prods["title"].fillna("") + " " + prods["category"].fillna("") + " " +
                prods["sub_category"].fillna("") + " " + prods["brand"].fillna("")).str.lower()
        self.X = normalize(TfidfVectorizer(ngram_range=(1, 2)).fit_transform(text))
        self.profiles = normalize(self.R @ self.X)

    def _scores(self, uix):
        return (self.profiles[uix] @ self.X.T).toarray()


class HybridRecommender(BaseRecommender):
    name = "hybrid"

    def __init__(self, n_factors: int = 48, alpha: float = 0.7, seed: int = 42):
        self.n_factors, self.alpha, self.seed = n_factors, alpha, seed

    def _fit(self, inter, products, cooccurrence: pd.DataFrame | None = None, **kw):
        self.svd = SVDRecommender(self.n_factors, self.seed).fit(inter, products)
        self.content = ContentRecommender().fit(inter, products)
        self.C = None
        if cooccurrence is not None and len(cooccurrence):
            co = cooccurrence[cooccurrence.product_id.isin(self.iidx) & cooccurrence.related_product_id.isin(self.iidx)]
            self.C = csr_matrix((np.log1p(co["co_users"].values),
                                 (co["product_id"].map(self.iidx).values, co["related_product_id"].map(self.iidx).values)),
                                shape=(len(self.items), len(self.items)))

    @staticmethod
    def _mm(S):
        lo, hi = S.min(axis=1, keepdims=True), S.max(axis=1, keepdims=True)
        return (S - lo) / np.where(hi - lo == 0, 1, hi - lo)

    def _scores(self, uix):
        s = self.alpha * self._mm(self.svd._scores(uix))
        rest = 1 - self.alpha
        if self.C is not None:
            s += rest * 0.6 * self._mm((self.R[uix] @ self.C).toarray())
            s += rest * 0.4 * self._mm(self.content._scores(uix))
        else:
            s += rest * self._mm(self.content._scores(uix))
        return s

    def params(self):
        return {"n_factors": self.n_factors, "alpha": self.alpha, "blend": "svd*alpha + (1-alpha)*(0.6 cooc + 0.4 content)"}


MODELS = {"popularity": PopularityRecommender, "svd": SVDRecommender, "content": ContentRecommender,
          "hybrid": HybridRecommender}


def build(name: str, **params) -> BaseRecommender:
    return MODELS[name](**params)

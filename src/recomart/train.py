"""Model training, evaluation and MLflow tracking / registry.

Protocol (time-based, no leakage):
  * cutoff = last event date - test_days; models only see events before the cutoff
  * relevant items for a user = products they added to cart or bought after the cutoff and had
    NOT interacted with before (we evaluate discovery of new items)
  * co-occurrence features come from the feature store snapshot taken at the cutoff
Then the best model (by NDCG@K) is refit on ALL data and registered as `@champion`.

    python -m recomart.train
"""
from __future__ import annotations

import json
import os
import pickle
import time
import warnings

os.environ.setdefault("MLFLOW_DISABLE_TELEMETRY", "true")
os.environ.setdefault("DO_NOT_TRACK", "true")

import mlflow  # noqa: E402
import mlflow.pyfunc  # noqa: E402
import pandas as pd  # noqa: E402
from mlflow.tracking import MlflowClient  # noqa: E402

from . import feature_store, lineage  # noqa: E402
from .config import (CHAMPION, EXPERIMENT, MLFLOW_ARTIFACTS, MLFLOW_DB, PROCESSED, REGISTERED_MODEL,  # noqa: E402
                     REPORTS, cfg)
from .evaluate import evaluate  # noqa: E402
from .logging_utils import audit, get_logger  # noqa: E402
from .models import build  # noqa: E402

warnings.filterwarnings("ignore")
log = get_logger("train")


def setup_mlflow() -> str:
    mlflow.set_tracking_uri(f"sqlite:///{MLFLOW_DB}")
    if mlflow.get_experiment_by_name(EXPERIMENT) is None:
        MLFLOW_ARTIFACTS.mkdir(parents=True, exist_ok=True)
        mlflow.create_experiment(EXPERIMENT, artifact_location=MLFLOW_ARTIFACTS.as_uri())
    mlflow.set_experiment(EXPERIMENT)
    return mlflow.get_tracking_uri()


class RecommenderPyfunc(mlflow.pyfunc.PythonModel):
    """MLflow wrapper: input DataFrame [user_id, k] -> recommendations."""

    def __init__(self, model):
        self.model = model

    def predict(self, context, model_input, params=None):
        k = int(model_input["k"].iloc[0]) if "k" in model_input else 10
        recs = self.model.recommend(list(model_input["user_id"]), k)
        return pd.DataFrame([{"user_id": u, "rank": r + 1, "product_id": p, "score": s}
                             for u, lst in recs.items() for r, (p, s) in enumerate(lst)])


def _interactions(ev: pd.DataFrame) -> pd.DataFrame:
    return ev.groupby(["user_id", "product_id"]).agg(strength=("weight", "sum")).reset_index()


def split(ev: pd.DataFrame, test_days: int, min_train: int):
    cutoff = ev["event_ts"].max().normalize() - pd.Timedelta(days=test_days - 1)
    tr, te = ev[ev.event_ts < cutoff], ev[ev.event_ts >= cutoff]
    inter = _interactions(tr)
    counts = inter.groupby("user_id").size()
    eligible = set(counts[counts >= min_train].index)
    seen = inter.groupby("user_id")["product_id"].apply(set).to_dict()
    pos = te[te.event_type.isin(["add_to_cart", "purchase"]) & te.user_id.isin(eligible)]
    truth = {}
    for u, items in pos.groupby("user_id")["product_id"]:
        new = set(items) - seen.get(u, set())
        if new:
            truth[u] = new
    return cutoff, inter, truth


def _log_model(model_obj, example_users):
    py = RecommenderPyfunc(model_obj)
    ex = pd.DataFrame({"user_id": example_users[:2], "k": [10, 10]})
    try:
        return mlflow.pyfunc.log_model(name="model", python_model=py, input_example=ex)
    except TypeError:
        return mlflow.pyfunc.log_model(artifact_path="model", python_model=py, input_example=ex)


def train_and_evaluate(model_names=None, register: bool = True) -> dict:
    setup_mlflow()
    tc = cfg()["training"]; k = tc["k"]
    ev = pd.read_parquet(PROCESSED / "events.parquet")
    products = pd.read_parquet(PROCESSED / "products.parquet")
    data_md5 = lineage.content_hash(PROCESSED / "events.parquet")
    cutoff, inter_tr, truth = split(ev, tc["test_days"], tc["min_train_interactions"])
    cut_s = cutoff.strftime("%Y-%m-%d %H:%M:%S")
    feature_store.materialize([cut_s], views=["item_cooccurrence"])
    co_cut = feature_store.get_training_features("item_cooccurrence", cut_s, "v1")
    log.info(f"split at {cutoff.date()}: {len(inter_tr):,} train pairs, {len(truth)} evaluation users")

    results = []
    for name in model_names or list(tc["models"]):
        params = dict(tc["models"][name])
        t0 = time.time()
        model = build(name, **params).fit(inter_tr, products, cooccurrence=co_cut)
        fit_s = time.time() - t0
        recs = model.recommend(list(truth), k)
        metrics = evaluate({u: [p for p, _ in v] for u, v in recs.items()}, truth, k, len(products))
        metrics["train_seconds"] = round(fit_s, 2)
        with mlflow.start_run(run_name=f"{name} | eval") as run:
            mlflow.log_params({"model": name, **{f"hp_{a}": b for a, b in model.params().items()},
                               "k": k, "split": f"time-based, last {tc['test_days']} days", "cutoff": str(cutoff.date()),
                               "train_pairs": len(inter_tr), "data_md5": data_md5,
                               "feature_view": "item_cooccurrence/v1@cutoff"})
            mlflow.log_metrics(metrics)
            mlflow.set_tags({"stage": "evaluation", "model_family": name})
            if hasattr(model, "explained_variance"):
                mlflow.log_metric("svd_explained_variance", round(model.explained_variance, 4))
        results.append({"model": name, "run_id": run.info.run_id, **metrics})
        log.info(f"{name}: NDCG@{k}={metrics[f'ndcg_at_{k}']:.4f} P@{k}={metrics[f'precision_at_{k}']:.4f} "
                 f"R@{k}={metrics[f'recall_at_{k}']:.4f}")

    best = max(results, key=lambda r: r[f"ndcg_at_{k}"])
    out = {"cutoff": str(cutoff.date()), "k": k, "eval_users": len(truth), "results": results, "best": best["model"]}
    if register:
        out["champion"] = refit_and_register(best, ev, products, data_md5)
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "model_metrics.json").write_text(json.dumps(out, indent=1))
    audit("train", best=best["model"], ndcg=best[f"ndcg_at_{k}"])
    return out


def refit_and_register(best: dict, ev: pd.DataFrame, products: pd.DataFrame, data_md5: str) -> dict:
    """Refit the winning model on all data (latest feature snapshot) and register it."""
    tc = cfg()["training"]; k = tc["k"]
    inter = _interactions(ev)
    latest = feature_store.load_registry()["views"]["item_cooccurrence"]["snapshots"][-1]["as_of"]
    co = feature_store.get_training_features("item_cooccurrence", latest, "v1")
    model = build(best["model"], **tc["models"][best["model"]]).fit(inter, products, cooccurrence=co)
    with mlflow.start_run(run_name=f"{best['model']} | production refit") as run:
        mlflow.log_params({"model": best["model"], **{f"hp_{a}": b for a, b in model.params().items()},
                           "trained_on": "all data", "data_md5": data_md5, "eval_run_id": best["run_id"],
                           "feature_view": f"item_cooccurrence/v1@{latest}"})
        mlflow.log_metrics({key: v for key, v in best.items() if isinstance(v, float)})
        mlflow.set_tags({"stage": "production", "model_family": best["model"]})
        info = _log_model(model, list(inter["user_id"].unique()))
    client = MlflowClient()
    mv = mlflow.register_model(info.model_uri, REGISTERED_MODEL)
    for tk, tv in {"model": best["model"], f"ndcg_at_{k}": str(best[f"ndcg_at_{k}"]), "data_md5": data_md5,
                   "eval_run_id": best["run_id"]}.items():
        client.set_model_version_tag(REGISTERED_MODEL, mv.version, tk, tv)
    client.set_registered_model_alias(REGISTERED_MODEL, CHAMPION, mv.version)
    log.info(f"registered {REGISTERED_MODEL} v{mv.version} ({best['model']}) as @{CHAMPION}")
    return {"version": mv.version, "run_id": run.info.run_id, "model": best["model"]}


def runs_dataframe() -> pd.DataFrame:
    setup_mlflow()
    return mlflow.search_runs(experiment_names=[EXPERIMENT], order_by=["start_time DESC"])


def registry_versions() -> pd.DataFrame:
    setup_mlflow()
    client = MlflowClient()
    try:
        champ = client.get_model_version_by_alias(REGISTERED_MODEL, CHAMPION).version
    except Exception:
        champ = None
    rows = [{"version": int(m.version), "alias": CHAMPION if m.version == champ else "", "model": m.tags.get("model"),
             f"ndcg_at_{cfg()['training']['k']}": m.tags.get(f"ndcg_at_{cfg()['training']['k']}"), "run_id": m.run_id,
             "created": pd.to_datetime(m.creation_timestamp, unit="ms").strftime("%Y-%m-%d %H:%M")}
            for m in client.search_model_versions(f"name='{REGISTERED_MODEL}'")]
    return pd.DataFrame(rows).sort_values("version", ascending=False) if rows else pd.DataFrame()


def load_champion():
    setup_mlflow()
    m = mlflow.pyfunc.load_model(f"models:/{REGISTERED_MODEL}@{CHAMPION}")
    return m.unwrap_python_model().model


if __name__ == "__main__":
    print(json.dumps(train_and_evaluate(), indent=1, default=str))

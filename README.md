# RecoMart: End-to-End Data Management Pipeline for a Recommendation System

**DSE ZG529 · Data Management for Machine Learning · BITS Pilani WILP · Experiential Learning Assignment (EC1)**

RecoMart is an e-commerce start-up that wants a data-driven recommendation engine. This repository implements the complete data management pipeline behind it: ingestion of batch and near-real-time data, a partitioned raw data lake, automated validation with a data quality report, preparation and EDA, SQL feature engineering in a warehouse, a versioned feature store, data versioning and lineage, model training with MLflow, Prefect orchestration and a recommendation API.

- **Live demo:** https://recomart-data-pipeline.streamlit.app
- **Team:** Rohesen Rajkamal Maurya (2025NS04108) · Akriti Adarsh (2025NS04070) · Chelsa Sam (2025NS04086) · Amogh J Putanikar (2025NS04023)

## Pipeline

```
 clickstream CSV ─┐
 transactions CSV ┤                                   ┌─> EDA (figures, notebook)
 ratings CSV ─────┼─> ingest ─> raw lake ─> validate ─> prepare ─┤
 users CSV ───────┤   retry,    source/    pandera,    clean,     └─> transform ─> feature store ─> train ─> API
 catalog API ─────┤   logging   type/date  DQ report   encode,        SQL           versioned       MLflow   FastAPI
 popularity API ──┘                                    quarantine     warehouse     v1/v2           @champion
```

Orchestrated as a Prefect flow (`flows/recomart_flow.py`) and reproducible as a DVC pipeline (`dvc.yaml`).

## Assignment tasks → where they are

| Task | Implementation | Evidence |
|---|---|---|
| Problem formulation | `README.md`, report, app "Overview" | Business problem, sources, outputs, metrics |
| Data collection & ingestion | `src/recomart/ingestion.py`, `mock_api.py` | `logs/ingestion.log`, `logs/audit.jsonl` |
| Raw data storage | `src/recomart/storage.py`, `configs/storage.yaml` | `data/lake/raw/source=*/type=*/date=*`, `docs/STORAGE.md` |
| Profiling & validation | `src/recomart/validation.py` (pandera), `dq_report.py` | `reports/dq/data_quality_report.pdf` |
| Data preparation & EDA | `src/recomart/preparation.py`, `eda.py`, `notebooks/01_data_preparation_and_eda.ipynb` | `reports/figures/*.png`, `data/processed/*.parquet` |
| Feature engineering & transformation | `sql/schema.sql`, `sql/features_*.sql`, `src/recomart/transform.py` | `data/warehouse/recomart.db` |
| Feature store | `src/recomart/feature_store.py` | `data/feature_store/registry.yaml`, `docs/FEATURES.md` |
| Data versioning & lineage | `dvc.yaml`, `dvc.lock`, `src/recomart/lineage.py` | `data/lineage/datasets.json`, `docs/VERSIONING.md` |
| Model training & evaluation | `src/recomart/models.py`, `evaluate.py`, `train.py` | MLflow runs, `reports/model_metrics.json` |
| Pipeline orchestration | `flows/recomart_flow.py`, `flows/serve.py` | Prefect UI, `logs/runs.jsonl`, `logs/alerts.log` |
| Serving | `serving/api.py`, `src/recomart/recommend.py` | `GET /recommend/{user_id}` |

## Results (time-based holdout, last 14 days, K = 10)

| Model | Precision@10 | Recall@10 | NDCG@10 | HitRate@10 | Coverage |
|---|---|---|---|---|---|
| Popularity (baseline) | 0.036 | 0.147 | 0.090 | 0.302 | 0.06 |
| SVD matrix factorisation | 0.038 | 0.139 | 0.096 | 0.309 | 0.45 |
| Content-based (TF-IDF) | 0.012 | 0.050 | 0.032 | 0.110 | 0.86 |
| **Hybrid (SVD + co-occurrence + content)** | **0.049** | **0.193** | **0.127** | **0.385** | 0.52 |

The hybrid model is registered in MLflow as `recomart-recommender@champion`.

## Run it

```bash
pip install -r requirements-dev.txt && pip install -e .

python -m recomart.pipeline            # whole pipeline (or: python flows/recomart_flow.py)
pytest -q                              # 11 tests
streamlit run app.py                   # interactive walkthrough
uvicorn serving.api:app --port 8000    # API docs at http://127.0.0.1:8000/docs
mlflow ui --backend-store-uri sqlite:///mlflow.db
prefect server start                   # Prefect UI at http://127.0.0.1:4200
python flows/serve.py                  # scheduled deployment (every 60 minutes)
dvc repro                              # rebuild only what changed
```

Individual stages: `python -m recomart.pipeline --stage ingest|validate|prepare|eda|transform|features|train`.

## Data

The source systems are simulated (`src/recomart/generate.py`) with a fixed seed: 1,500 users, 600 products in 8 categories, about 115,000 clickstream events over 90 days, 9,600 orders and 3,000 ratings. Behaviour follows a latent-preference model, so the recommenders have real signal to learn. Data-quality issues are injected on purpose (duplicates, missing values, an upstream column rename, invalid timestamps, out-of-range ratings, negative quantities and prices, unknown product IDs) so validation and preparation can be demonstrated.

## Repository layout

```
configs/            pipeline.yaml (all parameters), storage.yaml (local / S3)
src/recomart/       generate, mock_api, ingestion, storage, validation, dq_report, preparation, eda,
                    transform, feature_store, lineage, models, evaluate, train, recommend, pipeline
sql/                schema.sql + feature transformations
flows/              Prefect flow and scheduled deployment
serving/            FastAPI recommendation service
notebooks/          data preparation and EDA notebook (executed)
tests/              pytest suite
docs/               STORAGE.md, VERSIONING.md, FEATURES.md, VIDEO_SCRIPT.md
app.py              Streamlit walkthrough of every stage
dvc.yaml            DVC pipeline definition
```

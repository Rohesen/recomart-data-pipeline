# Data versioning and lineage

Two complementary mechanisms are used.

## 1. DVC: versioned data and a reproducible pipeline

`dvc.yaml` declares every stage with its command, dependencies, parameters and outputs:

```
ingest -> validate -> prepare -> eda
                              -> transform -> features -> train
```

`dvc repro` re-runs only the stages whose inputs changed. After a run, `dvc.lock` records the MD5 hash of every input and output. Committing `dvc.lock` to Git is what creates a **dataset version**: the Git history of `dvc.lock` is the history of the data.

```bash
dvc init                                         # once per repository
dvc repro                                        # build / rebuild
dvc dag                                          # show the stage graph
git add dvc.lock dvc.yaml && git commit -m "data: ingestion 2026-11-14"
dvc remote add -d storage gdrive://<folder-id>   # or s3://bucket/path, or a shared folder
dvc push                                         # upload the data; Git only keeps hashes
git checkout <commit> -- dvc.lock && dvc checkout   # restore any earlier dataset version
dvc diff HEAD~1                                  # what changed between two versions
```

Raw data (`data/lake/raw`), processed data (`data/processed`), the warehouse and the feature store are all DVC outputs, so both **raw and transformed** data are versioned.

## 2. Lineage catalogue: metadata for every version

`src/recomart/lineage.py` records, for every stage run:

| Field | Example |
|---|---|
| dataset | `processed` |
| version | 3 (bumped only when the content hash changes) |
| md5 | content hash of all files in the dataset |
| stage / run_id | `prepare` / `pf20261114163300` |
| inputs | `raw_lake` v2 (md5 …) |
| transformation | dedupe, quarantine invalid rows, impute, encode categoricals, normalise numerics |
| sources / ingest date | clickstream, transactions, ratings, users, catalog_api, popularity_api |

Files: `data/lineage/datasets.json` (catalogue of datasets and all their versions) and `data/lineage/lineage.jsonl` (one record per stage run). The Streamlit app draws the resulting lineage graph.

Models close the loop: every MLflow run logs the MD5 of the training data and the feature-store snapshot it used, so any recommendation can be traced back to the exact data version.

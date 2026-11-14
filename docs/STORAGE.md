# Raw data storage

## Layout

All ingested data lands unchanged in the raw zone of the data lake, partitioned by **source**, **type** and **date**:

```
data/lake/
├── raw/
│   ├── _manifest.jsonl                       one line per stored object (audit + lineage)
│   ├── source=clickstream/type=events/date=2026-08-01/clickstream_20260801.csv
│   ├── source=transactions/type=orders/date=2026-08-01/transactions_20260801.csv
│   ├── source=ratings/type=reviews/date=2026-08-02/ratings_20260802.csv
│   ├── source=users/type=profiles/date=2026-10-29/users_20261029.csv
│   ├── source=catalog_api/type=products/date=<ingest date>/products_HHMMSS.json
│   └── source=popularity_api/type=scores/date=<ingest date>/scores_HHMMSS.json
└── quarantine/                               rows rejected by preparation, with a reason code
    ├── events_quarantine.csv
    ├── orders_quarantine.csv
    └── ratings_quarantine.csv
```

- **File sources** are partitioned by the business date in the file name; near-real-time micro-batches (`*_mbN.csv`) land in the partition of the day they belong to.
- **API sources** are snapshots partitioned by ingestion date; the newest snapshot is used downstream, older ones are kept for audit and reproducibility.
- The raw zone is **append-only and immutable**: files are written atomically (`.part` file, then rename) and never edited. Cleaning happens downstream in `data/processed/`.

## Manifest

Every stored object gets a manifest record:

```json
{"stored_at": "2026-11-14T16:33:05+00:00", "run_id": "3f2a91c0d1", "source": "clickstream", "type": "events",
 "key": "source=clickstream/type=events/date=2026-08-01/clickstream_20260801.csv",
 "md5": "6c1f…", "rows": 1342, "bytes": 98234, "status": "ok"}
```

Ingestion is **idempotent**: a landing file whose MD5 is already recorded (and present in the lake) is skipped, so re-runs never duplicate data.

## Backends and upload

`configs/storage.yaml` selects the backend. `local` writes under `data/lake/`; `s3` writes the same keys to `s3://<bucket>/<prefix>/raw/...` using the standard AWS credential chain (no secrets in the repository).

```bash
python -m recomart.storage tree      # print the lake layout
python -m recomart.storage upload    # push the local lake to the configured backend
```

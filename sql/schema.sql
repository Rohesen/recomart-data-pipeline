-- RecoMart analytical warehouse (SQLite; portable to PostgreSQL with minor type changes)
-- Star schema: two dimensions, three facts, plus feature tables produced by sql/features_*.sql

PRAGMA foreign_keys = ON;

CREATE TABLE IF NOT EXISTS dim_users (
    user_id           TEXT PRIMARY KEY,
    signup_date       TEXT,
    age_band          TEXT,
    gender            TEXT,
    city_tier         TEXT,
    preferred_device  TEXT,
    age_band_ord      INTEGER,
    city_tier_ord     INTEGER
);

CREATE TABLE IF NOT EXISTS dim_products (
    product_id        TEXT PRIMARY KEY,
    title             TEXT NOT NULL,
    category          TEXT NOT NULL,
    sub_category      TEXT,
    brand             TEXT,
    price             REAL CHECK (price > 0),
    price_minmax      REAL,
    log_price_z       REAL,
    popularity_score  REAL,
    sentiment_score   REAL,
    social_mentions   INTEGER,
    launch_date       TEXT
);

CREATE TABLE IF NOT EXISTS fact_events (
    event_id    INTEGER PRIMARY KEY AUTOINCREMENT,
    event_ts    TEXT NOT NULL,
    user_id     TEXT NOT NULL REFERENCES dim_users(user_id),
    product_id  TEXT NOT NULL REFERENCES dim_products(product_id),
    event_type  TEXT NOT NULL CHECK (event_type IN ('view','wishlist','add_to_cart','purchase')),
    weight      REAL NOT NULL,
    session_id  TEXT,
    device      TEXT,
    channel     TEXT
);

CREATE TABLE IF NOT EXISTS fact_orders (
    order_id      TEXT PRIMARY KEY,
    user_id       TEXT NOT NULL REFERENCES dim_users(user_id),
    product_id    TEXT NOT NULL REFERENCES dim_products(product_id),
    quantity      INTEGER CHECK (quantity >= 1),
    unit_price    REAL,
    discount_pct  REAL,
    payment_mode  TEXT,
    order_ts      TEXT NOT NULL,
    revenue       REAL
);

CREATE TABLE IF NOT EXISTS fact_ratings (
    user_id     TEXT NOT NULL REFERENCES dim_users(user_id),
    product_id  TEXT NOT NULL REFERENCES dim_products(product_id),
    rating      INTEGER NOT NULL CHECK (rating BETWEEN 1 AND 5),
    rated_ts    TEXT NOT NULL,
    PRIMARY KEY (user_id, product_id)
);

-- ---------------- feature tables (one row per entity per as_of snapshot)
CREATE TABLE IF NOT EXISTS feat_user (
    user_id               TEXT NOT NULL,
    as_of                 TEXT NOT NULL,
    events_7d             INTEGER,
    events_30d            INTEGER,
    purchases_30d         INTEGER,
    total_purchases       INTEGER,
    distinct_items        INTEGER,
    conversion_rate       REAL,
    avg_rating_given      REAL,
    avg_order_value       REAL,
    days_since_last_event REAL,
    fav_category          TEXT,
    PRIMARY KEY (user_id, as_of)
);

CREATE TABLE IF NOT EXISTS feat_item (
    product_id        TEXT NOT NULL,
    as_of             TEXT NOT NULL,
    views_30d         INTEGER,
    purchases_30d     INTEGER,
    total_buyers      INTEGER,
    conversion_rate   REAL,
    avg_rating        REAL,
    n_ratings         INTEGER,
    bayes_rating      REAL,
    popularity_score  REAL,
    sentiment_score   REAL,
    price_minmax      REAL,
    PRIMARY KEY (product_id, as_of)
);

CREATE TABLE IF NOT EXISTS feat_item_cooccurrence (
    product_id          TEXT NOT NULL,
    related_product_id  TEXT NOT NULL,
    as_of               TEXT NOT NULL,
    co_users            INTEGER NOT NULL,
    lift                REAL,
    rank                INTEGER,
    PRIMARY KEY (product_id, related_product_id, as_of)
);

CREATE TABLE IF NOT EXISTS feat_item_content_similarity (
    product_id          TEXT NOT NULL,
    similar_product_id  TEXT NOT NULL,
    cosine_similarity   REAL NOT NULL,
    rank                INTEGER,
    PRIMARY KEY (product_id, similar_product_id)
);

CREATE TABLE IF NOT EXISTS etl_runs (
    run_id      TEXT,
    stage       TEXT,
    finished_at TEXT,
    rows        INTEGER,
    status      TEXT
);

CREATE INDEX IF NOT EXISTS ix_events_user_ts    ON fact_events(user_id, event_ts);
CREATE INDEX IF NOT EXISTS ix_events_product_ts ON fact_events(product_id, event_ts);
CREATE INDEX IF NOT EXISTS ix_events_type       ON fact_events(event_type);
CREATE INDEX IF NOT EXISTS ix_orders_user       ON fact_orders(user_id, order_ts);

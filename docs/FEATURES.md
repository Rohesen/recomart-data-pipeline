# Feature metadata (generated from data/feature_store/registry.yaml)

## user_activity

- **Entity:** `user_id`  
- **Versions:** v1  
- **Source:** warehouse.fact_events, fact_ratings, fact_orders  
- **Transformation:** `sql/features_user.sql`  
- **Owner:** Member 3 · **TTL:** 7 days  
- Recency, frequency and conversion behaviour of each user

| Feature | Type | Since | Description |
|---|---|---|---|
| `events_7d` | int | v1 | Events by the user in the 7 days before as_of |
| `events_30d` | int | v1 | Events by the user in the 30 days before as_of (activity frequency) |
| `purchases_30d` | int | v1 | Purchases in the last 30 days |
| `total_purchases` | int | v1 | All purchases before as_of |
| `distinct_items` | int | v1 | Distinct products interacted with |
| `conversion_rate` | float | v1 | Purchases / views |
| `avg_rating_given` | float | v1 | Average rating the user gives (null if none) |
| `avg_order_value` | float | v1 | Average order revenue (INR) |
| `days_since_last_event` | float | v1 | Recency in days |
| `fav_category` | str | v1 | Category with the highest weighted interaction |

Snapshots materialised: 12

## item_stats

- **Entity:** `product_id`  
- **Versions:** v1, v2  
- **Source:** warehouse.fact_events, fact_ratings, dim_products  
- **Transformation:** `sql/features_item.sql`  
- **Owner:** Member 3 · **TTL:** 7 days  
- Popularity, conversion and rating statistics of each product

| Feature | Type | Since | Description |
|---|---|---|---|
| `views_30d` | int | v1 | Views in the last 30 days |
| `purchases_30d` | int | v1 | Purchases in the last 30 days |
| `total_buyers` | int | v1 | Distinct buyers before as_of |
| `conversion_rate` | float | v1 | Purchases / views |
| `avg_rating` | float | v1 | Average rating (null if unrated) |
| `n_ratings` | int | v1 | Number of ratings |
| `bayes_rating` | float | v1 | Bayesian-smoothed rating (m = 5) |
| `popularity_score` | float | v1 | External popularity score 0-100 (popularity API) |
| `sentiment_score` | float | v1 | External sentiment -1..1 (popularity API) |
| `price_minmax` | float | v1 | Min-max normalised price |
| `trend_score` | float | v2 | v2 only: 0.6 * purchases_30d pct-rank + 0.4 * sentiment rescaled to 0-1 |

Snapshots materialised: 24

## item_cooccurrence

- **Entity:** `product_id`  
- **Versions:** v1  
- **Source:** warehouse.fact_events  
- **Transformation:** `sql/features_cooccurrence.sql`  
- **Owner:** Member 3 · **TTL:** 7 days  
- Top related products bought/carted by the same users (co-occurrence + lift)

| Feature | Type | Since | Description |
|---|---|---|---|
| `related_product_id` | str | v1 | Related product |
| `co_users` | int | v1 | Users with both items |
| `lift` | float | v1 | Co-occurrence lift |
| `rank` | int | v1 | Rank among related items |

Snapshots materialised: 13

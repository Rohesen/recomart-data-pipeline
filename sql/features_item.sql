-- Item features as of :as_of. bayes_rating shrinks the average rating towards the global mean
-- (m = 5 pseudo-ratings) so items with very few reviews are not over-ranked.
WITH ev AS (
    SELECT * FROM fact_events WHERE event_ts < :as_of
),
agg AS (
    SELECT product_id,
           SUM(CASE WHEN event_type = 'view'     AND event_ts >= datetime(:as_of, '-30 days') THEN 1 ELSE 0 END) AS views_30d,
           SUM(CASE WHEN event_type = 'purchase' AND event_ts >= datetime(:as_of, '-30 days') THEN 1 ELSE 0 END) AS purchases_30d,
           COUNT(DISTINCT CASE WHEN event_type = 'purchase' THEN user_id END)                                    AS total_buyers,
           1.0 * SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END)
               / NULLIF(SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END), 0)                                 AS conversion_rate
    FROM ev GROUP BY product_id
),
rat AS (
    SELECT product_id, AVG(rating) AS avg_rating, COUNT(*) AS n_ratings
    FROM fact_ratings WHERE rated_ts < :as_of GROUP BY product_id
),
g AS (
    SELECT COALESCE(AVG(rating), 3.0) AS mu FROM fact_ratings WHERE rated_ts < :as_of
)
SELECT p.product_id, :as_of AS as_of,
       COALESCE(a.views_30d, 0)       AS views_30d,
       COALESCE(a.purchases_30d, 0)   AS purchases_30d,
       COALESCE(a.total_buyers, 0)    AS total_buyers,
       ROUND(COALESCE(a.conversion_rate, 0), 4) AS conversion_rate,
       ROUND(r.avg_rating, 3)         AS avg_rating,
       COALESCE(r.n_ratings, 0)       AS n_ratings,
       ROUND((COALESCE(r.avg_rating, 0) * COALESCE(r.n_ratings, 0) + 5 * g.mu) / (COALESCE(r.n_ratings, 0) + 5), 3) AS bayes_rating,
       p.popularity_score, p.sentiment_score, ROUND(p.price_minmax, 4) AS price_minmax
FROM dim_products p
CROSS JOIN g
LEFT JOIN agg a USING (product_id)
LEFT JOIN rat r USING (product_id);

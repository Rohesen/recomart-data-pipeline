-- User features as of :as_of (only events strictly before :as_of -> no leakage)
WITH ev AS (
    SELECT * FROM fact_events WHERE event_ts < :as_of
),
agg AS (
    SELECT user_id,
           SUM(CASE WHEN event_ts >= datetime(:as_of, '-7 days')  THEN 1 ELSE 0 END)                          AS events_7d,
           SUM(CASE WHEN event_ts >= datetime(:as_of, '-30 days') THEN 1 ELSE 0 END)                          AS events_30d,
           SUM(CASE WHEN event_type = 'purchase' AND event_ts >= datetime(:as_of, '-30 days') THEN 1 ELSE 0 END) AS purchases_30d,
           SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END)                                            AS total_purchases,
           COUNT(DISTINCT product_id)                                                                          AS distinct_items,
           1.0 * SUM(CASE WHEN event_type = 'purchase' THEN 1 ELSE 0 END)
               / NULLIF(SUM(CASE WHEN event_type = 'view' THEN 1 ELSE 0 END), 0)                               AS conversion_rate,
           julianday(:as_of) - julianday(MAX(event_ts))                                                        AS days_since_last_event
    FROM ev GROUP BY user_id
),
fav AS (
    SELECT user_id, category AS fav_category FROM (
        SELECT e.user_id, p.category, SUM(e.weight) AS w,
               ROW_NUMBER() OVER (PARTITION BY e.user_id ORDER BY SUM(e.weight) DESC) AS rn
        FROM ev e JOIN dim_products p USING (product_id)
        GROUP BY e.user_id, p.category)
    WHERE rn = 1
),
rat AS (
    SELECT user_id, AVG(rating) AS avg_rating_given FROM fact_ratings WHERE rated_ts < :as_of GROUP BY user_id
),
ord AS (
    SELECT user_id, AVG(revenue) AS avg_order_value FROM fact_orders WHERE order_ts < :as_of GROUP BY user_id
)
SELECT a.user_id, :as_of AS as_of, a.events_7d, a.events_30d, a.purchases_30d, a.total_purchases, a.distinct_items,
       ROUND(COALESCE(a.conversion_rate, 0), 4) AS conversion_rate,
       ROUND(r.avg_rating_given, 3)             AS avg_rating_given,
       ROUND(o.avg_order_value, 2)              AS avg_order_value,
       ROUND(a.days_since_last_event, 2)        AS days_since_last_event,
       f.fav_category
FROM agg a
LEFT JOIN fav f USING (user_id)
LEFT JOIN rat r USING (user_id)
LEFT JOIN ord o USING (user_id);

-- Item-item co-occurrence: how many users added/bought both items before :as_of,
-- with lift = P(A and B) / (P(A) * P(B)). Keeps the top :top_n related items per product.
WITH strong AS (
    SELECT DISTINCT user_id, product_id
    FROM fact_events
    WHERE event_type IN ('add_to_cart', 'purchase') AND event_ts < :as_of
),
n_users AS (SELECT COUNT(DISTINCT user_id) AS n FROM strong),
item_users AS (SELECT product_id, COUNT(*) AS cnt FROM strong GROUP BY product_id),
pairs AS (
    SELECT a.product_id, b.product_id AS related_product_id, COUNT(*) AS co_users
    FROM strong a JOIN strong b ON a.user_id = b.user_id AND a.product_id <> b.product_id
    GROUP BY a.product_id, b.product_id
    HAVING COUNT(*) >= 2
),
scored AS (
    SELECT p.product_id, p.related_product_id, p.co_users,
           ROUND(1.0 * p.co_users * n.n / (ia.cnt * ib.cnt), 3) AS lift
    FROM pairs p
    JOIN item_users ia ON ia.product_id = p.product_id
    JOIN item_users ib ON ib.product_id = p.related_product_id
    CROSS JOIN n_users n
),
ranked AS (
    SELECT *, ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY co_users DESC, lift DESC) AS rank FROM scored
)
SELECT product_id, related_product_id, :as_of AS as_of, co_users, lift, rank
FROM ranked WHERE rank <= :top_n;

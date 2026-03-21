-- =========================
-- GOLD VIEW
-- CUSTOMER SEGMENTATION
-- =========================

CREATE OR REPLACE VIEW gold.customer_segmentation AS
SELECT
    customer_id,
    nb_transactions,
    total_spent,
    avg_item_price,

    CASE
        WHEN total_spent < 100 THEN 'Occasional'
        WHEN total_spent < 300 THEN 'Regular'
        ELSE 'VIP'
    END AS customer_segment

FROM gold.customer_value;
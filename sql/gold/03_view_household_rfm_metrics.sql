-- =========================
-- GOLD VIEW
-- RFM METRICS PAR HOUSEHOLD
-- =========================

CREATE OR REPLACE VIEW gold.household_rfm_metrics AS
SELECT
    c.household_id,
    MAX(t.transaction_timestamp)::date AS last_purchase_date,
    CURRENT_DATE - MAX(t.transaction_timestamp)::date AS recency_days,
    COUNT(DISTINCT t.transaction_id) AS frequency,
    ROUND(SUM(ti.quantity * ti.unit_price), 2) AS monetary
FROM datamarket.customers c
JOIN datamarket.loyalty_cards lc
    ON c.customer_id = lc.customer_id
JOIN datamarket.transactions t
    ON lc.card_id = t.card_id
JOIN datamarket.transaction_items ti
    ON t.transaction_id = ti.transaction_id
GROUP BY c.household_id;
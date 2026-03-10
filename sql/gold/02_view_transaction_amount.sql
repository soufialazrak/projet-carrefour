-- =========================
-- GOLD VIEW
-- MONTANT PAR TRANSACTION
-- =========================

CREATE OR REPLACE VIEW gold.transaction_amount AS
SELECT
    t.transaction_id,
    lc.customer_id,
    c.foyer_id,
    t.transaction_timestamp,
    SUM(ti.quantity * ti.unit_price) AS transaction_amount
FROM datamarket.transactions t
JOIN datamarket.loyalty_cards lc
    ON t.card_id = lc.card_id
JOIN datamarket.customers c
    ON lc.customer_id = c.customer_id
JOIN datamarket.transaction_items ti
    ON t.transaction_id = ti.transaction_id
GROUP BY
    t.transaction_id,
    lc.customer_id,
    c.foyer_id,
    t.transaction_timestamp;
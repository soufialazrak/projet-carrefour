-- =========================
-- GOLD VIEW
-- CUSTOMER VALUE
-- =========================
-- Cette vue calcule la valeur d'un client :
-- nombre de transactions, montant total dépensé
-- et prix moyen des articles achetés.


CREATE OR REPLACE VIEW gold.customer_value AS
SELECT
    c.customer_id,

    COUNT(DISTINCT t.transaction_id) AS nb_transactions,

    ROUND(SUM(ti.quantity * ti.unit_price), 2) AS total_spent,

    ROUND(AVG(ti.quantity * ti.unit_price), 2) AS avg_item_price

FROM datamarket.customers c

LEFT JOIN datamarket.loyalty_cards lc
    ON c.customer_id = lc.customer_id

LEFT JOIN datamarket.transactions t
    ON lc.card_id = t.card_id

LEFT JOIN datamarket.transaction_items ti
    ON t.transaction_id = ti.transaction_id

GROUP BY c.customer_id;
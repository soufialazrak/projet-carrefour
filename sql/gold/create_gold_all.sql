-- =========================
-- CREATE GOLD SCHEMA
-- =========================

CREATE SCHEMA IF NOT EXISTS gold;

COMMENT ON SCHEMA gold IS
'Couche Gold : vues analytiques et segmentation marketing construites à partir de la couche Silver.';


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


-- =========================
-- GOLD VIEW
-- RFM METRICS PAR FOYER
-- =========================

CREATE OR REPLACE VIEW gold.foyer_rfm_metrics AS
SELECT
    c.foyer_id,

    MAX(t.transaction_timestamp)::date AS last_purchase_date,

    CURRENT_DATE - MAX(t.transaction_timestamp)::date
        AS recency_days,

    COUNT(DISTINCT t.transaction_id)
        AS frequency,

    ROUND(SUM(ti.quantity * ti.unit_price), 2)
        AS monetary

FROM datamarket.customers c

JOIN datamarket.loyalty_cards lc
    ON c.customer_id = lc.customer_id

JOIN datamarket.transactions t
    ON lc.card_id = t.card_id

JOIN datamarket.transaction_items ti
    ON t.transaction_id = ti.transaction_id

GROUP BY c.foyer_id;


-- =========================
-- GOLD VIEW
-- RFM SEGMENTATION
-- =========================
CREATE OR REPLACE VIEW gold.foyer_rfm_segments AS
SELECT
    foyer_id,
    last_purchase_date,
    recency_days,
    frequency,
    monetary,

    -- SEGMENT RECENCE
    CASE
        WHEN recency_days <= 90 THEN 'actif'
        WHEN recency_days <= 240 THEN 'recent'
        ELSE 'inactif'
    END AS recency_segment,

    -- SEGMENT FREQUENCE
    CASE
        WHEN frequency = 1 THEN 'faible'
        WHEN frequency = 2 THEN 'moyen'
        WHEN frequency = 3 THEN 'eleve'
        ELSE 'tres frequent'
    END AS frequency_segment,

    -- SEGMENT MONETAIRE
    CASE
        WHEN monetary < 50 THEN 'tres petit panier'
        WHEN monetary < 100 THEN 'petit panier'
        WHEN monetary < 180 THEN 'gros panier'
        ELSE 'tres grand panier'
    END AS monetary_segment,

    -- MACRO SEGMENT
    CASE
        WHEN frequency = 1 THEN '1 achat'
        WHEN frequency = 2 THEN '2 achats'
        WHEN frequency BETWEEN 3 AND 4 THEN '3 à 4 achats'
        ELSE '5 achats et plus'
    END AS frequency_segment

FROM gold.foyer_rfm_metrics;

-- =========================
-- GOLD VIEW
-- CUSTOMER VALUE
-- =========================

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
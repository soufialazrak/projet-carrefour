-- =========================
-- GOLD VIEW
-- RFM SEGMENTATION PAR HOUSEHOLD
-- =========================

CREATE OR REPLACE VIEW gold.household_rfm_segments AS
SELECT
    household_id,
    last_purchase_date,
    recency_days,
    frequency,
    monetary,

    CASE
        WHEN recency_days <= 90 THEN 'tres actif'
        WHEN recency_days <= 180 THEN 'actif modere'
        WHEN recency_days <= 365 THEN 'a risque'
        ELSE 'inactif'
    END AS recency_segment,

    CASE
        WHEN frequency = 1 THEN 'faible'
        WHEN frequency BETWEEN 2 AND 3 THEN 'moyenne'
        ELSE 'elevee'
    END AS frequency_segment,

    CASE
        WHEN monetary < 100 THEN 'petit panier'
        WHEN monetary < 250 THEN 'panier moyen'
        WHEN monetary < 500 THEN 'grand panier'
        ELSE 'tres grand panier'
    END AS monetary_segment,

    CASE
        WHEN recency_days <= 90 AND frequency >= 4 AND monetary >= 500 THEN 'Premium'
        WHEN recency_days <= 180 AND frequency >= 2 AND monetary >= 250 THEN 'Fideles'
        WHEN recency_days <= 90 AND monetary >= 250 THEN 'Fort potentiel'
        WHEN recency_days > 365 AND frequency >= 2 THEN 'A reactiver'
        WHEN recency_days > 365 AND frequency = 1 THEN 'Perdus'
        ELSE 'Standard'
    END AS macro_segment

FROM gold.household_rfm_metrics;
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
        WHEN frequency >= 3 AND monetary >= 180 THEN 'Or'
        WHEN frequency >= 2 AND monetary >= 80 AND monetary < 180 THEN 'Argent'
        WHEN frequency = 1 AND monetary >= 40 AND monetary < 180 THEN 'Bronze'
        WHEN frequency >= 2 AND monetary < 100 THEN 'fideles faible panier'
        WHEN frequency = 1 AND monetary >= 180 THEN 'gros panier occasionnel'
        ELSE 'A analyser'
    END AS macro_segment

FROM gold.foyer_rfm_metrics;
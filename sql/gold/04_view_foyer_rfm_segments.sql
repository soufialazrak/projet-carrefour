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

-- RECENCY SEGMENT
CASE
    WHEN recency_days <= 30 THEN 'actif'
    WHEN recency_days <= 90 THEN 'recent'
    ELSE 'inactif'
END AS recency_segment,

-- FREQUENCY SEGMENT
CASE
    WHEN frequency BETWEEN 1 AND 3 THEN 'faible'
    WHEN frequency BETWEEN 4 AND 6 THEN 'moyen'
    WHEN frequency BETWEEN 7 AND 10 THEN 'eleve'
    ELSE 'tres frequent'
END AS frequency_segment,

-- MONETARY SEGMENT
CASE
    WHEN monetary <= 50 THEN 'tres petit panier'
    WHEN monetary <= 100 THEN 'petit panier'
    WHEN monetary <= 180 THEN 'gros panier'
    ELSE 'tres grand panier'
END AS monetary_segment,

-- MACRO SEGMENT
CASE
    WHEN frequency > 10 AND monetary > 180 THEN 'Or'
    WHEN frequency BETWEEN 4 AND 10 AND monetary > 100 AND monetary <= 180 THEN 'Argent'
    WHEN frequency BETWEEN 1 AND 3 AND monetary <= 100 THEN 'Bronze'
    ELSE 'A analyser'
END AS macro_segment

FROM gold.foyer_rfm_metrics;
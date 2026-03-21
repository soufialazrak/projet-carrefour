-- =========================
-- GOLD LAYER - FULL BUILD
-- =========================

-- 1. Création du schéma GOLD
\echo 'Creating GOLD schema...'
\i /sql/gold/01_create_gold_schema.sql

-- 2. Vue transaction amount
\echo 'Creating view: transaction_amount...'
\i /sql/gold/02_view_transaction_amount.sql

-- 3. Vue RFM metrics
\echo 'Creating view: household_rfm_metrics...'
\i /sql/gold/03_view_household_rfm_metrics.sql

-- 4. Vue RFM segmentation
\echo 'Creating view: household_rfm_segments...'
\i /sql/gold/04_view_household_rfm_segments.sql

-- 5. Vue customer value
\echo 'Creating view: customer_value...'
\i /sql/gold/05_view_customer_value.sql

-- 6. Vue customer segmentation
\echo 'Creating view: customer_segmentation...'
\i /sql/gold/06_view_customer_segmentation.sql

\echo 'GOLD layer created successfully.'
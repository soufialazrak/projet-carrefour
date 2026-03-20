-- =========================
-- UPSERT - SILVER LAYER
-- =========================

SET search_path TO datamarket;

-- =====================================================
-- 1) PRODUCT CATEGORIES
-- =====================================================
\echo 'Loading product_categories into staging...'

DROP TABLE IF EXISTS staging_product_categories;
CREATE TEMP TABLE staging_product_categories (
  category_id   INT,
  category_name VARCHAR(255)
);

\copy staging_product_categories(category_id, category_name)
FROM '/data/csv/product_categories.csv'
WITH (FORMAT csv, HEADER true);

\echo 'Upserting product_categories...'

INSERT INTO datamarket.product_categories (
  category_id,
  category_name
)
SELECT
  category_id,
  category_name
FROM staging_product_categories
ON CONFLICT (category_id) DO UPDATE
SET category_name = EXCLUDED.category_name;

-- =====================================================
-- 2) PRODUCTS
-- =====================================================
\echo 'Loading products into staging...'

DROP TABLE IF EXISTS staging_products;
CREATE TEMP TABLE staging_products (
  product_id         VARCHAR(64),
  category_id        INT,
  product_weight_g   NUMERIC,
  product_length_cm  NUMERIC,
  product_height_cm  NUMERIC,
  product_width_cm   NUMERIC
);

\copy staging_products(
  product_id,
  category_id,
  product_weight_g,
  product_length_cm,
  product_height_cm,
  product_width_cm
)
FROM '/data/csv/products.csv'
WITH (FORMAT csv, HEADER true);

\echo 'Upserting products...'

INSERT INTO datamarket.products (
  product_id,
  category_id,
  product_weight_g,
  product_length_cm,
  product_height_cm,
  product_width_cm
)
SELECT
  product_id,
  category_id,
  product_weight_g,
  product_length_cm,
  product_height_cm,
  product_width_cm
FROM staging_products
ON CONFLICT (product_id) DO UPDATE
SET
  category_id = EXCLUDED.category_id,
  product_weight_g = EXCLUDED.product_weight_g,
  product_length_cm = EXCLUDED.product_length_cm,
  product_height_cm = EXCLUDED.product_height_cm,
  product_width_cm = EXCLUDED.product_width_cm;

-- =====================================================
-- 3) HOUSEHOLDS
-- =====================================================
\echo 'Loading households into staging...'

DROP TABLE IF EXISTS staging_households;
CREATE TEMP TABLE staging_households (
  household_id          VARCHAR(64),
  household_created_at  TIMESTAMP
);

\copy staging_households(
  household_id,
  household_created_at
)
FROM '/data/csv/households.csv'
WITH (FORMAT csv, HEADER true);

\echo 'Upserting households...'

INSERT INTO datamarket.households (
  household_id,
  household_created_at
)
SELECT
  household_id,
  household_created_at
FROM staging_households
ON CONFLICT (household_id) DO UPDATE
SET household_created_at = EXCLUDED.household_created_at;

-- =====================================================
-- 4) CUSTOMERS
-- =====================================================
\echo 'Loading customers into staging...'

DROP TABLE IF EXISTS staging_customers;
CREATE TEMP TABLE staging_customers (
  customer_id      VARCHAR(64),
  household_id     VARCHAR(64),
  first_name       VARCHAR(100),
  last_name        VARCHAR(100),
  birth_year       INT,
  email            VARCHAR(255),
  customer_city    VARCHAR(255),
  postal_code      VARCHAR(20),
  region           VARCHAR(100)
);

\copy staging_customers(
  customer_id,
  household_id,
  first_name,
  last_name,
  birth_year,
  email,
  customer_city,
  postal_code,
  region
)
FROM '/data/csv/customers.csv'
WITH (FORMAT csv, HEADER true);

\echo 'Upserting customers...'

INSERT INTO datamarket.customers (
  customer_id,
  household_id,
  first_name,
  last_name,
  birth_year,
  email,
  customer_city,
  postal_code,
  region
)
SELECT
  customer_id,
  household_id,
  first_name,
  last_name,
  birth_year,
  email,
  customer_city,
  postal_code,
  region
FROM staging_customers
ON CONFLICT (customer_id) DO UPDATE
SET
  household_id = EXCLUDED.household_id,
  first_name = EXCLUDED.first_name,
  last_name = EXCLUDED.last_name,
  birth_year = EXCLUDED.birth_year,
  email = EXCLUDED.email,
  customer_city = EXCLUDED.customer_city,
  postal_code = EXCLUDED.postal_code,
  region = EXCLUDED.region;

-- =====================================================
-- 5) LOYALTY CARDS
-- =====================================================
\echo 'Loading loyalty_cards into staging...'

DROP TABLE IF EXISTS staging_loyalty_cards;
CREATE TEMP TABLE staging_loyalty_cards (
  card_id        VARCHAR(64),
  customer_id    VARCHAR(64),
  card_status    VARCHAR(20),
  issued_at      TIMESTAMP,
  last_used_at   TIMESTAMP
);

\copy staging_loyalty_cards(
  card_id,
  customer_id,
  card_status,
  issued_at,
  last_used_at
)
FROM '/data/csv/loyalty_cards.csv'
WITH (FORMAT csv, HEADER true);

\echo 'Upserting loyalty_cards...'

INSERT INTO datamarket.loyalty_cards (
  card_id,
  customer_id,
  card_status,
  issued_at,
  last_used_at
)
SELECT
  card_id,
  customer_id,
  card_status,
  issued_at,
  last_used_at
FROM staging_loyalty_cards
ON CONFLICT (card_id) DO UPDATE
SET
  customer_id = EXCLUDED.customer_id,
  card_status = EXCLUDED.card_status,
  issued_at = EXCLUDED.issued_at,
  last_used_at = EXCLUDED.last_used_at;

-- =====================================================
-- 6) TRANSACTIONS
-- =====================================================
\echo 'Loading transactions into staging...'

DROP TABLE IF EXISTS staging_transactions;
CREATE TEMP TABLE staging_transactions (
  transaction_id         VARCHAR(64),
  card_id                VARCHAR(64),
  transaction_status     VARCHAR(50),
  channel                VARCHAR(20),
  payment_types_used     VARCHAR(50),
  transaction_timestamp  TIMESTAMP
);

\copy staging_transactions(
  transaction_id,
  card_id,
  transaction_status,
  channel,
  payment_types_used,
  transaction_timestamp
)
FROM '/data/csv/transactions.csv'
WITH (FORMAT csv, HEADER true);

\echo 'Upserting transactions...'

INSERT INTO datamarket.transactions (
  transaction_id,
  card_id,
  transaction_status,
  channel,
  payment_types_used,
  transaction_timestamp
)
SELECT
  transaction_id,
  card_id,
  transaction_status,
  channel,
  payment_types_used,
  transaction_timestamp
FROM staging_transactions
ON CONFLICT (transaction_id) DO UPDATE
SET
  card_id = EXCLUDED.card_id,
  transaction_status = EXCLUDED.transaction_status,
  channel = EXCLUDED.channel,
  payment_types_used = EXCLUDED.payment_types_used,
  transaction_timestamp = EXCLUDED.transaction_timestamp;

-- =====================================================
-- 7) TRANSACTION ITEMS
-- =====================================================
\echo 'Loading transaction_items into staging...'

DROP TABLE IF EXISTS staging_transaction_items;
CREATE TEMP TABLE staging_transaction_items (
  transaction_id       VARCHAR(64),
  transaction_item_id  INT,
  product_id           VARCHAR(64),
  quantity             INT,
  unit_price           NUMERIC(10,2)
);

\copy staging_transaction_items(
  transaction_id,
  transaction_item_id,
  product_id,
  quantity,
  unit_price
)
FROM '/data/csv/transaction_items.csv'
WITH (FORMAT csv, HEADER true);

\echo 'Upserting transaction_items...'

INSERT INTO datamarket.transaction_items (
  transaction_id,
  transaction_item_id,
  product_id,
  quantity,
  unit_price
)
SELECT
  transaction_id,
  transaction_item_id,
  product_id,
  quantity,
  unit_price
FROM staging_transaction_items
ON CONFLICT (transaction_id, transaction_item_id) DO UPDATE
SET
  product_id = EXCLUDED.product_id,
  quantity = EXCLUDED.quantity,
  unit_price = EXCLUDED.unit_price;

\echo 'Monthly UPSERT completed successfully.'
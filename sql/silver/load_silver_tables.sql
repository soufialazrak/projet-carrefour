-- =========================
-- FIRST LOAD - SILVER LAYER
-- =========================

SET search_path TO datamarket;

-- Nettoyage complet (ordre important à cause des dépendances)
TRUNCATE TABLE transaction_items CASCADE;
TRUNCATE TABLE transactions CASCADE;
TRUNCATE TABLE loyalty_cards CASCADE;
TRUNCATE TABLE customers CASCADE;
TRUNCATE TABLE households CASCADE;
TRUNCATE TABLE products CASCADE;
TRUNCATE TABLE product_categories CASCADE;

-- =========================
-- LOAD PRODUCT CATEGORIES
-- =========================
\echo 'Loading product_categories...'
\copy datamarket.product_categories(category_id, category_name) FROM '/data/csv/product_categories.csv' WITH (FORMAT csv, HEADER true);

-- =========================
-- LOAD PRODUCTS
-- =========================
\echo 'Loading products...'
\copy datamarket.products(product_id, category_id, product_weight_g, product_length_cm, product_height_cm, product_width_cm) FROM '/data/csv/products.csv' WITH (FORMAT csv, HEADER true);

-- =========================
-- LOAD HOUSEHOLDS
-- =========================
\echo 'Loading households...'
\copy datamarket.households(household_id, household_created_at) FROM '/data/csv/households.csv' WITH (FORMAT csv, HEADER true);

-- =========================
-- LOAD CUSTOMERS
-- =========================
\echo 'Loading customers...'
\copy datamarket.customers(customer_id, household_id, first_name_encrypted, last_name_encrypted, birth_year, email_encrypted, email_hash, customer_city, postal_code, region) FROM '/data/csv/customers.csv' WITH (FORMAT csv, HEADER true);

-- =========================
-- LOAD LOYALTY CARDS
-- =========================
\echo 'Loading loyalty_cards...'
\copy datamarket.loyalty_cards(card_id, customer_id, card_status, issued_at, last_used_at) FROM '/data/csv/loyalty_cards.csv' WITH (FORMAT csv, HEADER true);

-- =========================
-- LOAD TRANSACTIONS
-- =========================
\echo 'Loading transactions...'
\copy datamarket.transactions(transaction_id, card_id, transaction_status, channel, payment_types_used, transaction_timestamp) FROM '/data/csv/transactions.csv' WITH (FORMAT csv, HEADER true);

-- =========================
-- LOAD TRANSACTION ITEMS
-- =========================
\echo 'Loading transaction_items...'
\copy datamarket.transaction_items(transaction_id, transaction_item_id, product_id, quantity, unit_price) FROM '/data/csv/transaction_items.csv' WITH (FORMAT csv, HEADER true);

\echo 'Initial silver load completed successfully.'


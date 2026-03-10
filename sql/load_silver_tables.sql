-- =========================
-- LOAD DATA - SILVER LAYER
-- =========================

\echo 'Loading product_categories...'
\copy datamarket.product_categories(category_id, category_name) FROM '/data/csv/product_categories.csv' WITH (FORMAT csv, HEADER true);

\echo 'Loading products...'
\copy datamarket.products(product_id, category_id, product_weight_g, product_length_cm, product_height_cm, product_width_cm) FROM '/data/csv/products.csv' WITH (FORMAT csv, HEADER true);

\echo 'Loading foyers...'
\copy datamarket.foyers(foyer_id, foyer_created_at, foyer_status) FROM '/data/csv/foyers.csv' WITH (FORMAT csv, HEADER true);

\echo 'Loading customers...'
\copy datamarket.customers(customer_id, foyer_id, customer_city, customer_state) FROM '/data/csv/customers.csv' WITH (FORMAT csv, HEADER true);

\echo 'Loading loyalty_cards...'
\copy datamarket.loyalty_cards(card_id, customer_id, card_status, issued_at) FROM '/data/csv/loyalty_cards.csv' WITH (FORMAT csv, HEADER true);

\echo 'Loading transactions...'
\copy datamarket.transactions(channel, transaction_timestamp, transaction_id, transaction_status, card_id, payment_types_used) FROM '/data/csv/transactions.csv' WITH (FORMAT csv, HEADER true);

\echo 'Loading transaction_items...'
\copy datamarket.transaction_items(quantity, transaction_id, transaction_item_id, product_id, unit_price) FROM '/data/csv/transaction_items.csv' WITH (FORMAT csv, HEADER true);

\echo 'All tables loaded successfully.'
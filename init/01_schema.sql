CREATE SCHEMA IF NOT EXISTS datamarket;
SET search_path TO datamarket;

-- =========================
-- PRODUCT CATEGORIES
-- =========================
CREATE TABLE IF NOT EXISTS product_categories (
  category_id   SERIAL PRIMARY KEY,
  category_name VARCHAR(255) UNIQUE NOT NULL
);

-- =========================
-- PRODUCTS (Bronze - complet)
-- =========================
CREATE TABLE IF NOT EXISTS products (
  product_id                  VARCHAR(64) PRIMARY KEY,
  category_id                 INT NOT NULL REFERENCES product_categories(category_id),

  -- Champs dataset (Bronze)
  product_name_lenght         NUMERIC,
  product_description_lenght  NUMERIC,
  product_photos_qty          NUMERIC,
  product_weight_g            NUMERIC,
  product_length_cm           NUMERIC,
  product_height_cm           NUMERIC,
  product_width_cm            NUMERIC
);

-- =========================
-- CUSTOMERS (foyer via master_customer_id)
-- =========================
CREATE TABLE IF NOT EXISTS customers (
  customer_id        VARCHAR(64) PRIMARY KEY,
  master_customer_id VARCHAR(64) NOT NULL,
  customer_city      VARCHAR(255),
  customer_state     VARCHAR(50),

  CONSTRAINT fk_customers_master
    FOREIGN KEY (master_customer_id) REFERENCES customers(customer_id)
);

CREATE INDEX IF NOT EXISTS idx_customers_master_customer_id
  ON customers(master_customer_id);

-- =========================
-- LOYALTY CARDS
-- =========================
CREATE TABLE IF NOT EXISTS loyalty_cards (
  card_id     VARCHAR(64) PRIMARY KEY,
  customer_id VARCHAR(64) NOT NULL REFERENCES customers(customer_id),
  card_status VARCHAR(20) NOT NULL CHECK (card_status IN ('active', 'inactive')),
  issued_at   TIMESTAMP
);

-- 1 seule carte active par client
CREATE UNIQUE INDEX IF NOT EXISTS ux_one_active_card_per_customer
  ON loyalty_cards(customer_id)
  WHERE card_status = 'active';

-- =========================
-- TRANSACTIONS
-- =========================
CREATE TABLE IF NOT EXISTS transactions (
  transaction_id        VARCHAR(64) PRIMARY KEY,
  card_id               VARCHAR(64) NOT NULL REFERENCES loyalty_cards(card_id),
  transaction_status    VARCHAR(50),
  channel               VARCHAR(20) CHECK (channel IN ('store', 'online')),
  payment_type          VARCHAR(20) CHECK (payment_type IN ('card', 'cash')),
  transaction_timestamp TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_card_id
  ON transactions(card_id);

CREATE INDEX IF NOT EXISTS idx_transactions_timestamp
  ON transactions(transaction_timestamp);

-- =========================
-- TRANSACTION ITEMS
-- =========================
CREATE TABLE IF NOT EXISTS transaction_items (
  transaction_id      VARCHAR(64) NOT NULL REFERENCES transactions(transaction_id),
  transaction_item_id INT NOT NULL,
  product_id          VARCHAR(64) NOT NULL REFERENCES products(product_id),
  quantity            INT NOT NULL CHECK (quantity > 0),
  price               NUMERIC(10,2) NOT NULL CHECK (price >= 0),

  CONSTRAINT pk_transaction_items
    PRIMARY KEY (transaction_id, transaction_item_id)
);

CREATE INDEX IF NOT EXISTS idx_transaction_items_product_id
  ON transaction_items(product_id);
CREATE SCHEMA IF NOT EXISTS datamarket;
SET search_path TO datamarket;

-- =========================
-- FOYERS
-- =========================
CREATE TABLE IF NOT EXISTS foyers (
  foyer_id          VARCHAR(64) PRIMARY KEY,
  foyer_created_at  TIMESTAMP NOT NULL,
  foyer_status      VARCHAR(20) NOT NULL CHECK (foyer_status IN ('active', 'inactive'))
);

-- =========================
-- CUSTOMERS
-- =========================
CREATE TABLE IF NOT EXISTS customers (
  customer_id     VARCHAR(64) PRIMARY KEY,
  foyer_id        VARCHAR(64) NOT NULL REFERENCES foyers(foyer_id),
  customer_city   VARCHAR(255),
  customer_state  VARCHAR(50)
);

CREATE INDEX IF NOT EXISTS idx_customers_foyer_id
  ON customers(foyer_id);

-- =========================
-- LOYALTY CARDS
-- =========================
CREATE TABLE IF NOT EXISTS loyalty_cards (
  card_id      VARCHAR(64) PRIMARY KEY,
  customer_id  VARCHAR(64) NOT NULL UNIQUE REFERENCES customers(customer_id),
  card_status  VARCHAR(20) NOT NULL CHECK (card_status IN ('active', 'inactive')),
  issued_at    TIMESTAMP
);

-- =========================
-- PRODUCT CATEGORIES
-- =========================
CREATE TABLE IF NOT EXISTS product_categories (
  category_id   INT PRIMARY KEY,
  category_name VARCHAR(255) UNIQUE NOT NULL
);

-- =========================
-- PRODUCTS
-- =========================
CREATE TABLE IF NOT EXISTS products (
  product_id         VARCHAR(64) PRIMARY KEY,
  category_id INT NOT NULL REFERENCES product_categories(category_id),
  product_weight_g   NUMERIC,
  product_length_cm  NUMERIC,
  product_height_cm  NUMERIC,
  product_width_cm   NUMERIC
);

-- =========================
-- TRANSACTIONS
-- =========================
CREATE TABLE IF NOT EXISTS transactions (
  transaction_id         VARCHAR(64) PRIMARY KEY,
  card_id                VARCHAR(64) NOT NULL REFERENCES loyalty_cards(card_id),
  transaction_status     VARCHAR(50),
  channel                VARCHAR(20) CHECK (channel IN ('store', 'online')),
  payment_types_used     VARCHAR(50),
  transaction_timestamp  TIMESTAMP NOT NULL
);

CREATE INDEX IF NOT EXISTS idx_transactions_card_id
  ON transactions(card_id);

CREATE INDEX IF NOT EXISTS idx_transactions_timestamp
  ON transactions(transaction_timestamp);

-- =========================
-- TRANSACTION ITEMS
-- =========================
CREATE TABLE IF NOT EXISTS transaction_items (
  transaction_id       VARCHAR(64) NOT NULL REFERENCES transactions(transaction_id),
  transaction_item_id  INT NOT NULL,
  product_id           VARCHAR(64) NOT NULL REFERENCES products(product_id),
  quantity             INT NOT NULL CHECK (quantity > 0),
  unit_price           NUMERIC(10,2) NOT NULL CHECK (unit_price >= 0),

  CONSTRAINT pk_transaction_items
    PRIMARY KEY (transaction_id, transaction_item_id)
);

CREATE INDEX IF NOT EXISTS idx_transaction_items_product_id
  ON transaction_items(product_id);
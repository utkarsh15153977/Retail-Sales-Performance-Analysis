-- ==============================================================================
-- Portfolio Project: Retail Sales Performance Analysis
-- Script: 02_create_tables.sql
-- Purpose: Create transactional, staging, and dimensional Star Schema tables.
-- Dialect: PostgreSQL 12+
-- Author: Senior Data Analyst & SQL Developer
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. Staging Layer: staging.superstore_raw
-- Permissive data types allow ELT ingestion without failing on dirty source rows.
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS staging.superstore_raw CASCADE;

CREATE TABLE staging.superstore_raw (
    raw_row_id         TEXT,
    order_id           TEXT,
    order_date         TEXT,
    ship_date          TEXT,
    ship_mode          TEXT,
    customer_id        TEXT,
    customer_name      TEXT,
    segment            TEXT,
    country            TEXT,
    city               TEXT,
    state              TEXT,
    postal_code        TEXT,
    region             TEXT,
    product_id         TEXT,
    category           TEXT,
    sub_category       TEXT,
    product_name       TEXT,
    sales              TEXT,
    quantity           TEXT,
    discount           TEXT,
    profit             TEXT,
    ingestion_timestamp TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

COMMENT ON TABLE staging.superstore_raw IS 'Unvalidated staging table for landing raw CSV text data.';

-- ------------------------------------------------------------------------------
-- 2. Core Transactional Model: core.retail_sales
-- The primary analytical table containing all 21 standard business dimensions & measures.
-- Strict typing, primary key, check constraints, and safe NULL handling.
-- ------------------------------------------------------------------------------
DROP TABLE IF EXISTS core.retail_sales CASCADE;

CREATE TABLE core.retail_sales (
    row_id             INT NOT NULL,
    order_id           VARCHAR(25) NOT NULL,
    order_date         DATE NOT NULL,
    ship_date          DATE NOT NULL,
    ship_mode          VARCHAR(25) NOT NULL,
    customer_id        VARCHAR(20) NOT NULL,
    customer_name      VARCHAR(100) NOT NULL,
    segment            VARCHAR(50) NOT NULL,
    country            VARCHAR(50) NOT NULL DEFAULT 'United States',
    city               VARCHAR(50) NOT NULL,
    state              VARCHAR(50) NOT NULL,
    postal_code        VARCHAR(20) NULL,      -- Handled safely: nullable for missing geographic zones
    region             VARCHAR(20) NOT NULL,
    product_id         VARCHAR(30) NOT NULL,
    category           VARCHAR(50) NOT NULL,
    sub_category       VARCHAR(50) NOT NULL,
    product_name       VARCHAR(255) NOT NULL,
    sales              NUMERIC(12, 4) NOT NULL,
    quantity           INT NOT NULL,
    discount           NUMERIC(5, 4) NOT NULL,
    profit             NUMERIC(12, 4) NOT NULL,
    
    -- Generated analytical metric (Stored for zero-cost downstream filtering)
    profit_margin      NUMERIC(7, 4) GENERATED ALWAYS AS (
                           CASE 
                               WHEN sales > 0 THEN ROUND((profit / sales)::NUMERIC, 4)
                               ELSE 0.0000 
                           END
                       ) STORED,
    
    -- Metadata tracking
    created_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,

    -- Table Constraints
    CONSTRAINT pk_retail_sales PRIMARY KEY (row_id),
    CONSTRAINT chk_sales_non_negative CHECK (sales >= 0.0),
    CONSTRAINT chk_quantity_positive CHECK (quantity > 0),
    CONSTRAINT chk_discount_range CHECK (discount >= 0.0 AND discount <= 1.0),
    CONSTRAINT chk_ship_after_order CHECK (ship_date >= order_date)
);

-- Documentation on Core Table and Fields
COMMENT ON TABLE core.retail_sales IS 'Cleansed, typed retail transaction records from the Sample Superstore dataset.';
COMMENT ON COLUMN core.retail_sales.row_id IS 'Unique surrogate row identifier from source CSV (Primary Key).';
COMMENT ON COLUMN core.retail_sales.order_id IS 'Business identifier for customer transaction order.';
COMMENT ON COLUMN core.retail_sales.order_date IS 'Calendar date when the order was placed by customer.';
COMMENT ON COLUMN core.retail_sales.ship_date IS 'Calendar date when the merchandise was shipped.';
COMMENT ON COLUMN core.retail_sales.postal_code IS 'Postal ZIP code, standardized to 5 characters with preserved leading zeros.';
COMMENT ON COLUMN core.retail_sales.sales IS 'Gross invoice sales amount in USD.';
COMMENT ON COLUMN core.retail_sales.discount IS 'Promotional discount rate as a decimal percentage (0.00 to 0.80).';
COMMENT ON COLUMN core.retail_sales.profit IS 'Net monetary gain or loss in USD (can be negative due to heavy discounts/returns).';
COMMENT ON COLUMN core.retail_sales.profit_margin IS 'Computed net profit margin (profit / sales).';

-- ------------------------------------------------------------------------------
-- 3. Core Transaction Table Performance Indexes
-- Designed specifically to optimize common analytical filtering and grouping paths.
-- ------------------------------------------------------------------------------
CREATE INDEX idx_retail_sales_order_id ON core.retail_sales (order_id);
CREATE INDEX idx_retail_sales_order_date ON core.retail_sales (order_date);
CREATE INDEX idx_retail_sales_customer_id ON core.retail_sales (customer_id);
CREATE INDEX idx_retail_sales_product_id ON core.retail_sales (product_id);
CREATE INDEX idx_retail_sales_category_subcat ON core.retail_sales (category, sub_category);
CREATE INDEX idx_retail_sales_region_state ON core.retail_sales (region, state);
CREATE INDEX idx_retail_sales_date_region ON core.retail_sales (order_date, region);
CREATE INDEX idx_retail_sales_segment ON core.retail_sales (segment);

-- ------------------------------------------------------------------------------
-- 4. Enterprise Star Schema Dimensional Model (Optional / Senior Showcase)
-- Demonstrates Kimball dimensional modeling principles for Data Warehouse architecture.
-- ------------------------------------------------------------------------------

-- Dimension: Customers
DROP TABLE IF EXISTS core.dim_customers CASCADE;
CREATE TABLE core.dim_customers (
    customer_id        VARCHAR(20) PRIMARY KEY,
    customer_name      VARCHAR(100) NOT NULL,
    segment            VARCHAR(50) NOT NULL,
    first_order_date   DATE,
    total_orders       INT DEFAULT 0,
    created_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE core.dim_customers IS 'Customer dimension capturing demographics and historical lifetime order count.';

-- Dimension: Products
DROP TABLE IF EXISTS core.dim_products CASCADE;
CREATE TABLE core.dim_products (
    product_id         VARCHAR(30) PRIMARY KEY,
    product_name       VARCHAR(255) NOT NULL,
    category           VARCHAR(50) NOT NULL,
    sub_category       VARCHAR(50) NOT NULL,
    created_at         TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);
COMMENT ON TABLE core.dim_products IS 'Product catalog dimension with category hierarchies.';

-- Dimension: Geography
DROP TABLE IF EXISTS core.dim_geography CASCADE;
CREATE TABLE core.dim_geography (
    geography_id       SERIAL PRIMARY KEY,
    country            VARCHAR(50) NOT NULL,
    region             VARCHAR(20) NOT NULL,
    state              VARCHAR(50) NOT NULL,
    city               VARCHAR(50) NOT NULL,
    postal_code        VARCHAR(20) NULL,
    CONSTRAINT uq_geography UNIQUE (country, region, state, city, postal_code)
);
COMMENT ON TABLE core.dim_geography IS 'Geographic dimension normalizing locations across regions, states, and cities.';

-- Dimension: Date
DROP TABLE IF EXISTS core.dim_date CASCADE;
CREATE TABLE core.dim_date (
    date_key           INT PRIMARY KEY, -- Formatted as YYYYMMDD
    full_date          DATE UNIQUE NOT NULL,
    year               INT NOT NULL,
    quarter            INT NOT NULL,
    month              INT NOT NULL,
    month_name         VARCHAR(20) NOT NULL,
    day                INT NOT NULL,
    day_of_week        INT NOT NULL,
    day_name           VARCHAR(20) NOT NULL,
    is_weekend         BOOLEAN NOT NULL
);
COMMENT ON TABLE core.dim_date IS 'Standard enterprise date dimension facilitating time-series analytics.';

-- Fact: Sales Transactions
DROP TABLE IF EXISTS core.fact_sales CASCADE;
CREATE TABLE core.fact_sales (
    fact_id            SERIAL PRIMARY KEY,
    row_id             INT NOT NULL,
    order_id           VARCHAR(25) NOT NULL,
    order_date_key     INT NOT NULL REFERENCES core.dim_date (date_key),
    ship_date_key      INT NOT NULL REFERENCES core.dim_date (date_key),
    customer_id        VARCHAR(20) NOT NULL REFERENCES core.dim_customers (customer_id),
    product_id         VARCHAR(30) NOT NULL REFERENCES core.dim_products (product_id),
    geography_id       INT NOT NULL REFERENCES core.dim_geography (geography_id),
    ship_mode          VARCHAR(25) NOT NULL,
    sales              NUMERIC(12, 4) NOT NULL,
    quantity           INT NOT NULL,
    discount           NUMERIC(5, 4) NOT NULL,
    profit             NUMERIC(12, 4) NOT NULL,
    CONSTRAINT chk_fact_sales_positive CHECK (sales >= 0.0),
    CONSTRAINT chk_fact_quantity_positive CHECK (quantity > 0)
);
COMMENT ON TABLE core.fact_sales IS 'Central sales fact table linking measures to business dimensions.';

CREATE INDEX idx_fact_sales_order_date ON core.fact_sales (order_date_key);
CREATE INDEX idx_fact_sales_customer ON core.fact_sales (customer_id);
CREATE INDEX idx_fact_sales_product ON core.fact_sales (product_id);
CREATE INDEX idx_fact_sales_geography ON core.fact_sales (geography_id);

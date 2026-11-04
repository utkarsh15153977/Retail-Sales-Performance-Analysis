-- ==============================================================================
-- Portfolio Project: Retail Sales Performance Analysis
-- Script: 04_data_cleaning.sql
-- Purpose: Data transformation, postal code standardization, non-destructive
--          deduplication views, and Star Schema population.
-- Dialect: PostgreSQL 12+
-- Author: Senior Data Analyst & SQL Developer
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- 1. In-Place Postal Code Standardization
-- Cleanse leading-zero truncation without data loss (e.g. '5408' -> '05408').
-- ------------------------------------------------------------------------------
UPDATE core.retail_sales
SET postal_code = LPAD(TRIM(postal_code), 5, '0')
WHERE postal_code IS NOT NULL 
  AND LENGTH(TRIM(postal_code)) < 5 
  AND TRIM(postal_code) ~ '^[0-9]+$';

-- Standardize any whitespace across string dimensions
UPDATE core.retail_sales
SET 
    customer_name = TRIM(customer_name),
    city          = TRIM(city),
    state         = TRIM(state),
    product_name  = TRIM(product_name);

-- ------------------------------------------------------------------------------
-- 2. Audit View: Duplicate Line Items & Provenance
-- Non-destructive handling: In retail ERP/POS systems, identical items in an
-- order can indicate split shipments or separate physical packages.
-- We never silently delete records; we flag them transparently for financial audit.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW core.v_duplicate_line_items AS
WITH ranked_transactions AS (
    SELECT 
        row_id,
        order_id,
        order_date,
        customer_id,
        customer_name,
        product_id,
        product_name,
        sales,
        quantity,
        discount,
        profit,
        ROW_NUMBER() OVER (
            PARTITION BY order_id, product_id, sales, quantity, discount, profit 
            ORDER BY row_id
        ) AS duplicate_rank,
        COUNT(*) OVER (
            PARTITION BY order_id, product_id, sales, quantity, discount, profit
        ) AS total_matches
    FROM core.retail_sales
)
SELECT 
    row_id,
    order_id,
    order_date,
    customer_name,
    product_name,
    sales,
    quantity,
    discount,
    profit,
    duplicate_rank,
    total_matches,
    CASE 
        WHEN duplicate_rank > 1 THEN 'Potential Duplicate Line Item - Retained for Provenance'
        ELSE 'Canonical Primary Record'
    END AS audit_status
FROM ranked_transactions
WHERE total_matches > 1;

COMMENT ON VIEW core.v_duplicate_line_items IS 'Audit log of multi-item matching entries preserved for complete reconciliation.';

-- ------------------------------------------------------------------------------
-- 3. Production Cleansed View: core.v_clean_retail_sales
-- Provides downstream business analysts with a pristine view:
-- Includes calculated metrics, delivery lag in days, and standardized fields.
-- ------------------------------------------------------------------------------
CREATE OR REPLACE VIEW core.v_clean_retail_sales AS
SELECT 
    row_id,
    order_id,
    order_date,
    ship_date,
    (ship_date - order_date) AS delivery_days,
    ship_mode,
    customer_id,
    customer_name,
    segment,
    country,
    city,
    state,
    postal_code,
    region,
    product_id,
    category,
    sub_category,
    product_name,
    sales,
    quantity,
    discount,
    profit,
    profit_margin,
    ROUND((sales / NULLIF(quantity, 0))::NUMERIC, 2) AS unit_price,
    ROUND(((sales - profit) / NULLIF(quantity, 0))::NUMERIC, 2) AS estimated_unit_cost,
    CASE 
        WHEN profit > 0 THEN 'Profitable'
        WHEN profit = 0 THEN 'Break-even'
        ELSE 'Loss-making'
    END AS profitability_tier,
    CASE 
        WHEN discount = 0.00 THEN 'No Discount (0%)'
        WHEN discount <= 0.20 THEN 'Low Discount (1-20%)'
        WHEN discount <= 0.50 THEN 'Moderate Discount (21-50%)'
        ELSE 'Deep Discount (>50%)'
    END AS discount_tier
FROM core.retail_sales;

COMMENT ON VIEW core.v_clean_retail_sales IS 'Production analytical view with standardized metrics, unit economics, and discount tiers.';

-- ------------------------------------------------------------------------------
-- 4. Star Schema Dimensional Population
-- ------------------------------------------------------------------------------

-- Populate dim_date: Calendar dimension spanning 2014 through 2018
INSERT INTO core.dim_date (
    date_key,
    full_date,
    year,
    quarter,
    month,
    month_name,
    day,
    day_of_week,
    day_name,
    is_weekend
)
SELECT 
    TO_CHAR(d, 'YYYYMMDD')::INT AS date_key,
    d::DATE AS full_date,
    EXTRACT(YEAR FROM d)::INT AS year,
    EXTRACT(QUARTER FROM d)::INT AS quarter,
    EXTRACT(MONTH FROM d)::INT AS month,
    TO_CHAR(d, 'FMMonth') AS month_name,
    EXTRACT(DAY FROM d)::INT AS day,
    EXTRACT(ISODOW FROM d)::INT AS day_of_week,
    TO_CHAR(d, 'FMDay') AS day_name,
    CASE WHEN EXTRACT(ISODOW FROM d) IN (6, 7) THEN TRUE ELSE FALSE END AS is_weekend
FROM GENERATE_SERIES('2014-01-01'::DATE, '2018-01-31'::DATE, '1 day'::INTERVAL) AS d
ON CONFLICT (date_key) DO NOTHING;

-- Populate dim_customers
INSERT INTO core.dim_customers (customer_id, customer_name, segment, first_order_date, total_orders)
SELECT 
    customer_id,
    MAX(customer_name) AS customer_name,
    MAX(segment) AS segment,
    MIN(order_date) AS first_order_date,
    COUNT(DISTINCT order_id) AS total_orders
FROM core.retail_sales
GROUP BY customer_id
ON CONFLICT (customer_id) DO UPDATE 
SET 
    customer_name    = EXCLUDED.customer_name,
    segment          = EXCLUDED.segment,
    first_order_date = EXCLUDED.first_order_date,
    total_orders     = EXCLUDED.total_orders;

-- Populate dim_products
-- Note: A product_id may occasionally have slightly modified descriptive strings over time.
-- We take the most recent product_name associated with each product_id.
WITH ranked_products AS (
    SELECT 
        product_id,
        product_name,
        category,
        sub_category,
        ROW_NUMBER() OVER (PARTITION BY product_id ORDER BY order_date DESC, row_id DESC) AS rn
    FROM core.retail_sales
)
INSERT INTO core.dim_products (product_id, product_name, category, sub_category)
SELECT 
    product_id,
    product_name,
    category,
    sub_category
FROM ranked_products
WHERE rn = 1
ON CONFLICT (product_id) DO UPDATE 
SET 
    product_name = EXCLUDED.product_name,
    category     = EXCLUDED.category,
    sub_category = EXCLUDED.sub_category;

-- Populate dim_geography
INSERT INTO core.dim_geography (country, region, state, city, postal_code)
SELECT DISTINCT 
    country,
    region,
    state,
    city,
    postal_code
FROM core.retail_sales
ON CONFLICT (country, region, state, city, postal_code) DO NOTHING;

-- Populate fact_sales
INSERT INTO core.fact_sales (
    row_id,
    order_id,
    order_date_key,
    ship_date_key,
    customer_id,
    product_id,
    geography_id,
    ship_mode,
    sales,
    quantity,
    discount,
    profit
)
SELECT 
    s.row_id,
    s.order_id,
    TO_CHAR(s.order_date, 'YYYYMMDD')::INT AS order_date_key,
    TO_CHAR(s.ship_date, 'YYYYMMDD')::INT  AS ship_date_key,
    s.customer_id,
    s.product_id,
    g.geography_id,
    s.ship_mode,
    s.sales,
    s.quantity,
    s.discount,
    s.profit
FROM core.retail_sales s
JOIN core.dim_geography g
  ON s.country = g.country
 AND s.region  = g.region
 AND s.state   = g.state
 AND s.city    = g.city
 AND (s.postal_code = g.postal_code OR (s.postal_code IS NULL AND g.postal_code IS NULL))
ON CONFLICT DO NOTHING;

-- ==============================================================================
-- Portfolio Project: Retail Sales Performance Analysis
-- Script: 03_data_validation.sql
-- Purpose: Rigorous Data Quality Audit & Integrity Verification Queries.
-- Dialect: PostgreSQL 12+
-- Author: Senior Data Analyst & SQL Developer
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Audit Query 1: Total Record Count
-- Expectation: Exactly 9,994 transaction rows loaded from Sample Superstore.
-- ------------------------------------------------------------------------------
SELECT 
    'Record Count Verification' AS audit_check,
    COUNT(*) AS total_records,
    CASE 
        WHEN COUNT(*) = 9994 THEN 'PASSED: Exact row count matches source'
        ELSE 'FAILED: Discrepancy detected against 9,994 baseline'
    END AS audit_status
FROM core.retail_sales;

-- ------------------------------------------------------------------------------
-- Audit Query 2: Duplicate Row ID Check (Primary Key Integrity)
-- Expectation: 0 duplicates. Every row_id must be globally unique.
-- ------------------------------------------------------------------------------
SELECT 
    row_id,
    COUNT(*) AS duplicate_count
FROM core.retail_sales
GROUP BY row_id
HAVING COUNT(*) > 1;

-- ------------------------------------------------------------------------------
-- Audit Query 3: Duplicate Order ID + Product ID Combinations
-- Business Context: In retail systems, repeated product entries in the same order
-- can indicate either separate carton line items or accidental double scans.
-- ------------------------------------------------------------------------------
WITH duplicate_order_products AS (
    SELECT 
        order_id,
        product_id,
        COUNT(*) AS occurrence_count,
        SUM(sales) AS total_sales,
        SUM(quantity) AS total_quantity
    FROM core.retail_sales
    GROUP BY order_id, product_id
    HAVING COUNT(*) > 1
)
SELECT 
    order_id,
    product_id,
    occurrence_count,
    total_sales,
    total_quantity,
    'Flagged for line-item review (Non-fatal in retail transactional systems)' AS audit_notes
FROM duplicate_order_products
ORDER BY occurrence_count DESC, order_id;

-- ------------------------------------------------------------------------------
-- Audit Query 4: Comprehensive NULL Value Audit across All 21 Columns
-- Expectation: 0 NULLs across mandatory fields; nullable only where permissible.
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) AS total_rows,
    COUNT(*) - COUNT(row_id)        AS null_row_id,
    COUNT(*) - COUNT(order_id)      AS null_order_id,
    COUNT(*) - COUNT(order_date)    AS null_order_date,
    COUNT(*) - COUNT(ship_date)     AS null_ship_date,
    COUNT(*) - COUNT(ship_mode)     AS null_ship_mode,
    COUNT(*) - COUNT(customer_id)   AS null_customer_id,
    COUNT(*) - COUNT(customer_name) AS null_customer_name,
    COUNT(*) - COUNT(segment)       AS null_segment,
    COUNT(*) - COUNT(country)       AS null_country,
    COUNT(*) - COUNT(city)          AS null_city,
    COUNT(*) - COUNT(state)         AS null_state,
    COUNT(*) - COUNT(postal_code)   AS null_postal_code,
    COUNT(*) - COUNT(region)        AS null_region,
    COUNT(*) - COUNT(product_id)    AS null_product_id,
    COUNT(*) - COUNT(category)      AS null_category,
    COUNT(*) - COUNT(sub_category)  AS null_sub_category,
    COUNT(*) - COUNT(product_name)  AS null_product_name,
    COUNT(*) - COUNT(sales)         AS null_sales,
    COUNT(*) - COUNT(quantity)      AS null_quantity,
    COUNT(*) - COUNT(discount)      AS null_discount,
    COUNT(*) - COUNT(profit)        AS null_profit
FROM core.retail_sales;

-- ------------------------------------------------------------------------------
-- Audit Query 5: Invalid Temporal Sequences (Ship Date < Order Date)
-- Business Context: Merchandise cannot ship prior to purchase timestamp.
-- ------------------------------------------------------------------------------
SELECT 
    row_id,
    order_id,
    order_date,
    ship_date,
    (ship_date - order_date) AS fulfillment_days,
    CASE 
        WHEN ship_date < order_date THEN 'FAILED: Anachronistic shipment'
        ELSE 'PASSED'
    END AS temporal_status
FROM core.retail_sales
WHERE ship_date < order_date;

-- ------------------------------------------------------------------------------
-- Audit Query 6: Negative or Zero Sales and Quantity Checks
-- Business Context: In this transaction model, returns are reflected via negative
-- profit rather than negative invoice sales. Sales and quantity must be positive.
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) FILTER (WHERE sales <= 0) AS invalid_sales_count,
    COUNT(*) FILTER (WHERE quantity <= 0) AS invalid_quantity_count,
    MIN(sales) AS min_sales_value,
    MAX(sales) AS max_sales_value,
    MIN(quantity) AS min_quantity_value,
    MAX(quantity) AS max_quantity_value
FROM core.retail_sales;

-- ------------------------------------------------------------------------------
-- Audit Query 7: Discount Range & Distribution Verification
-- Business Context: Discount rate must lie between 0.00 (0%) and 1.00 (100%).
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(*) FILTER (WHERE discount < 0.0 OR discount > 1.0) AS invalid_discounts,
    MIN(discount) AS min_discount,
    MAX(discount) AS max_discount,
    ROUND(AVG(discount), 4) AS avg_discount,
    COUNT(*) FILTER (WHERE discount = 0.0) AS zero_discount_transactions,
    COUNT(*) FILTER (WHERE discount > 0.0 AND discount <= 0.20) AS moderate_discount_transactions,
    COUNT(*) FILTER (WHERE discount > 0.20 AND discount <= 0.50) AS high_discount_transactions,
    COUNT(*) FILTER (WHERE discount > 0.50) AS extreme_discount_transactions
FROM core.retail_sales;

-- ------------------------------------------------------------------------------
-- Audit Query 8: Profit Distribution & Outlier Identification
-- Analyzes dispersion: Min, Max, Avg, Percentiles, and Loss-Making proportions.
-- ------------------------------------------------------------------------------
SELECT 
    ROUND(MIN(profit), 2) AS min_profit,
    ROUND(MAX(profit), 2) AS max_profit,
    ROUND(AVG(profit), 2) AS avg_profit,
    ROUND(STDDEV(profit), 2) AS stddev_profit,
    ROUND(PERCENTILE_CONT(0.25) WITHIN GROUP (ORDER BY profit)::NUMERIC, 2) AS p25_profit,
    ROUND(PERCENTILE_CONT(0.50) WITHIN GROUP (ORDER BY profit)::NUMERIC, 2) AS median_profit,
    ROUND(PERCENTILE_CONT(0.75) WITHIN GROUP (ORDER BY profit)::NUMERIC, 2) AS p75_profit,
    COUNT(*) FILTER (WHERE profit < 0) AS loss_making_orders_count,
    ROUND((COUNT(*) FILTER (WHERE profit < 0)::NUMERIC / COUNT(*) * 100), 2) AS loss_making_order_pct
FROM core.retail_sales;

-- ------------------------------------------------------------------------------
-- Audit Query 9: Date Range & Span Coverage
-- Business Context: Confirms full 4-year calendar span (2014-01-03 to 2017-12-30).
-- ------------------------------------------------------------------------------
SELECT 
    MIN(order_date) AS earliest_order_date,
    MAX(order_date) AS latest_order_date,
    (MAX(order_date) - MIN(order_date)) AS calendar_span_days,
    COUNT(DISTINCT EXTRACT(YEAR FROM order_date)) AS distinct_operating_years
FROM core.retail_sales;

-- ------------------------------------------------------------------------------
-- Audit Query 10: High-Level Cardinality & Entity Counts
-- Verifies core business entity counts against known benchmark values.
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(DISTINCT customer_id)   AS unique_customers,
    COUNT(DISTINCT order_id)      AS unique_orders,
    COUNT(DISTINCT product_id)    AS unique_products,
    COUNT(DISTINCT product_name)  AS unique_product_names,
    COUNT(DISTINCT city)          AS unique_cities,
    COUNT(DISTINCT state)         AS unique_states,
    COUNT(DISTINCT region)        AS unique_regions
FROM core.retail_sales;

-- ------------------------------------------------------------------------------
-- Audit Query 11: Postal Code Formatting & Anomaly Detection
-- Detects unformatted zip codes (e.g., Vermont 05408 dropping leading zeros).
-- ------------------------------------------------------------------------------
SELECT 
    state,
    city,
    postal_code,
    LENGTH(postal_code) AS zip_length,
    COUNT(*) AS row_count
FROM core.retail_sales
WHERE LENGTH(postal_code) <> 5 OR postal_code IS NULL
GROUP BY state, city, postal_code, LENGTH(postal_code)
ORDER BY row_count DESC;

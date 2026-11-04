-- ==============================================================================
-- Portfolio Project: Retail Sales Performance Analysis
-- Script: 05_analysis_queries.sql
-- Purpose: Core analytical queries covering KPIs, trends, geography, products,
--          customer segments, and shipping logistics.
-- Dialect: PostgreSQL 12+
-- Author: Senior Data Analyst & SQL Developer
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Query 1: Executive KPI Scorecard
-- Purpose: High-level financial health check. Baseline for dashboards and quarterly reviews.
-- Key Metrics: Gross Sales, Net Profit, Blended Margin, AOV, Order & Customer counts.
-- ------------------------------------------------------------------------------
SELECT 
    COUNT(DISTINCT order_id)                                           AS total_orders,
    COUNT(DISTINCT customer_id)                                        AS total_customers,
    SUM(quantity)                                                      AS total_units_sold,
    ROUND(SUM(sales), 2)                                               AS total_sales_usd,
    ROUND(SUM(profit), 2)                                              AS total_profit_usd,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0) * 100)::NUMERIC, 2)     AS overall_profit_margin_pct,
    ROUND((SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0))::NUMERIC, 2) AS average_order_value_aov,
    ROUND((SUM(profit) / NULLIF(COUNT(DISTINCT order_id), 0))::NUMERIC, 2) AS profit_per_order,
    ROUND((SUM(quantity)::NUMERIC / NULLIF(COUNT(DISTINCT order_id), 0)), 2) AS avg_items_per_order
FROM core.retail_sales;

-- ------------------------------------------------------------------------------
-- Query 2: Monthly & Yearly Sales & Profit Growth Trends (MoM & YoY)
-- Technique: Common Table Expressions (CTE) + Window Functions LAG() and SUM() OVER().
-- Business Insight: Identifies seasonality (Q4 holiday spikes in Nov/Dec) and annual growth trajectory.
-- ------------------------------------------------------------------------------
WITH monthly_metrics AS (
    SELECT 
        DATE_TRUNC('month', order_date)::DATE AS order_month,
        EXTRACT(YEAR FROM order_date)::INT    AS order_year,
        EXTRACT(MONTH FROM order_date)::INT   AS month_num,
        TO_CHAR(order_date, 'Mon')            AS month_abbrev,
        ROUND(SUM(sales), 2)                  AS monthly_sales,
        ROUND(SUM(profit), 2)                 AS monthly_profit,
        COUNT(DISTINCT order_id)              AS order_count
    FROM core.retail_sales
    GROUP BY 1, 2, 3, 4
),
growth_calculations AS (
    SELECT 
        order_month,
        order_year,
        month_num,
        month_abbrev,
        monthly_sales,
        monthly_profit,
        ROUND((monthly_profit / NULLIF(monthly_sales, 0) * 100)::NUMERIC, 2) AS monthly_margin_pct,
        order_count,
        -- Prior month revenue for MoM calculation
        LAG(monthly_sales, 1) OVER (ORDER BY order_month) AS prev_month_sales,
        -- Prior year same month revenue for YoY calculation
        LAG(monthly_sales, 12) OVER (ORDER BY order_month) AS prev_year_same_month_sales,
        -- Running cumulative sales by calendar year
        SUM(monthly_sales) OVER (PARTITION BY order_year ORDER BY order_month) AS ytd_sales
    FROM monthly_metrics
)
SELECT 
    order_month,
    order_year,
    month_abbrev,
    monthly_sales,
    monthly_profit,
    monthly_margin_pct,
    order_count,
    ROUND(((monthly_sales - prev_month_sales) / NULLIF(prev_month_sales, 0) * 100)::NUMERIC, 2) AS mom_sales_growth_pct,
    ROUND(((monthly_sales - prev_year_same_month_sales) / NULLIF(prev_year_same_month_sales, 0) * 100)::NUMERIC, 2) AS yoy_sales_growth_pct,
    ytd_sales
FROM growth_calculations
ORDER BY order_month;

-- ------------------------------------------------------------------------------
-- Query 3: Regional & State Performance Analysis
-- Technique: Aggregations, Window Functions, and Conditional CASE Filtering.
-- Business Insight: Identifies highly profitable regions (West, East) vs bleeders
-- (Central and South margins dragged down by heavy discounting).
-- ------------------------------------------------------------------------------
-- Part A: Regional Performance Summary
SELECT 
    region,
    COUNT(DISTINCT order_id)                                         AS total_orders,
    COUNT(DISTINCT customer_id)                                      AS unique_customers,
    ROUND(SUM(sales), 2)                                             AS total_sales,
    ROUND((SUM(sales) / SUM(SUM(sales)) OVER () * 100)::NUMERIC, 2)  AS sales_share_pct,
    ROUND(SUM(profit), 2)                                            AS total_profit,
    ROUND((SUM(profit) / SUM(SUM(profit)) OVER () * 100)::NUMERIC, 2) AS profit_share_pct,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0) * 100)::NUMERIC, 2)   AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2)                                    AS avg_discount_pct
FROM core.retail_sales
GROUP BY region
ORDER BY total_profit DESC;

-- Part B: Top 5 and Bottom 5 States by Total Profit
WITH state_summary AS (
    SELECT 
        state,
        region,
        ROUND(SUM(sales), 2) AS total_sales,
        ROUND(SUM(profit), 2) AS total_profit,
        ROUND((SUM(profit) / NULLIF(SUM(sales), 0) * 100)::NUMERIC, 2) AS margin_pct,
        ROUND(AVG(discount) * 100, 2) AS avg_discount_pct,
        DENSE_RANK() OVER (ORDER BY SUM(profit) DESC) AS rank_most_profitable,
        DENSE_RANK() OVER (ORDER BY SUM(profit) ASC)  AS rank_least_profitable
    FROM core.retail_sales
    GROUP BY state, region
)
SELECT 
    state,
    region,
    total_sales,
    total_profit,
    margin_pct,
    avg_discount_pct,
    CASE 
        WHEN rank_most_profitable <= 5 THEN 'Top 5 Most Profitable'
        WHEN rank_least_profitable <= 5 THEN 'Bottom 5 Loss-Making'
    END AS state_performance_cohort
FROM state_summary
WHERE rank_most_profitable <= 5 OR rank_least_profitable <= 5
ORDER BY total_profit DESC;

-- ------------------------------------------------------------------------------
-- Query 4: Product Category & Sub-Category Performance
-- Technique: Multi-level aggregation with window ranking.
-- Business Insight: Technology yields highest absolute profit, while Furniture
-- suffers from severe margin degradation due to Tables and Bookcases.
-- ------------------------------------------------------------------------------
SELECT 
    category,
    sub_category,
    COUNT(DISTINCT product_id)                                       AS distinct_products,
    SUM(quantity)                                                    AS units_sold,
    ROUND(SUM(sales), 2)                                             AS total_sales,
    ROUND((SUM(sales) / SUM(SUM(sales)) OVER () * 100)::NUMERIC, 2)  AS pct_of_total_sales,
    ROUND(SUM(profit), 2)                                            AS total_profit,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0) * 100)::NUMERIC, 2)   AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2)                                    AS avg_discount_pct,
    DENSE_RANK() OVER (
        PARTITION BY category 
        ORDER BY SUM(profit) DESC
    ) AS profit_rank_within_category
FROM core.retail_sales
GROUP BY category, sub_category
ORDER BY category, total_profit DESC;

-- ------------------------------------------------------------------------------
-- Query 5: Customer Segment Economics
-- Business Insight: Analyzes whether Consumer, Corporate, or Home Office
-- yields higher unit economics, order sizes, and discounting sensitivity.
-- ------------------------------------------------------------------------------
SELECT 
    segment,
    COUNT(DISTINCT customer_id)                                      AS unique_customers,
    COUNT(DISTINCT order_id)                                         AS total_orders,
    ROUND(COUNT(DISTINCT order_id)::NUMERIC / COUNT(DISTINCT customer_id), 2) AS orders_per_customer,
    ROUND(SUM(sales), 2)                                             AS total_sales,
    ROUND((SUM(sales) / SUM(SUM(sales)) OVER () * 100)::NUMERIC, 2)  AS sales_contribution_pct,
    ROUND(SUM(profit), 2)                                            AS total_profit,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0) * 100)::NUMERIC, 2)   AS profit_margin_pct,
    ROUND((SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0))::NUMERIC, 2) AS aov_per_segment,
    ROUND(AVG(discount) * 100, 2)                                    AS avg_discount_pct
FROM core.retail_sales
GROUP BY segment
ORDER BY total_sales DESC;

-- ------------------------------------------------------------------------------
-- Query 6: Shipping Logistics & Fulfillment Efficiency
-- Business Insight: Evaluates shipping turnaround times across fulfillment tiers.
-- ------------------------------------------------------------------------------
SELECT 
    ship_mode,
    COUNT(DISTINCT order_id)                                         AS total_orders,
    SUM(quantity)                                                    AS total_units,
    ROUND(SUM(sales), 2)                                             AS total_sales,
    ROUND(AVG(ship_date - order_date), 2)                            AS avg_fulfillment_days,
    MIN(ship_date - order_date)                                      AS min_fulfillment_days,
    MAX(ship_date - order_date)                                      AS max_fulfillment_days,
    ROUND((COUNT(DISTINCT order_id)::NUMERIC / SUM(COUNT(DISTINCT order_id)) OVER () * 100), 2) AS shipment_share_pct
FROM core.retail_sales
GROUP BY ship_mode
ORDER BY avg_fulfillment_days ASC;

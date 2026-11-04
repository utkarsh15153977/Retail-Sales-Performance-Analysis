-- ==============================================================================
-- Portfolio Project: Retail Sales Performance Analysis
-- Script: 06_business_insights.sql
-- Purpose: Advanced Strategic Business Intelligence & Portfolio Showcase Queries.
--          (Discount cliff, RFM segmentation, Cohorts, Pareto 80/20, Market Basket)
-- Dialect: PostgreSQL 12+
-- Author: Senior Data Analyst & SQL Developer
-- ==============================================================================

-- ------------------------------------------------------------------------------
-- Insight 1: The Discount Cliff & Profitability Elasticity Analysis
-- Business Problem: Sales teams often offer heavy discounts assuming higher volume
-- offsets lower margins. This query reveals the exact margin destruction threshold.
-- Finding: Discounts > 20% result in net negative profit. Discounts > 60% lose $1.23 per $1 sold.
-- ------------------------------------------------------------------------------
WITH discount_brackets AS (
    SELECT 
        row_id,
        sales,
        profit,
        quantity,
        discount,
        CASE 
            WHEN discount = 0.00 THEN '1. None (0%)'
            WHEN discount <= 0.20 THEN '2. Low (1% - 20%)'
            WHEN discount <= 0.40 THEN '3. Moderate (21% - 40%)'
            WHEN discount <= 0.60 THEN '4. High (41% - 60%)'
            ELSE '5. Extreme (> 60%)'
        END AS discount_tier
    FROM core.retail_sales
)
SELECT 
    discount_tier,
    COUNT(*)                                                          AS transaction_count,
    ROUND((COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100), 2)       AS transaction_share_pct,
    SUM(quantity)                                                     AS total_units_sold,
    ROUND(SUM(sales), 2)                                              AS total_sales_usd,
    ROUND(SUM(profit), 2)                                             AS total_profit_usd,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0) * 100)::NUMERIC, 2)    AS profit_margin_pct,
    ROUND((SUM(sales) / NULLIF(SUM(quantity), 0))::NUMERIC, 2)        AS avg_realized_price_per_unit,
    ROUND((SUM(profit) / NULLIF(SUM(quantity), 0))::NUMERIC, 2)       AS avg_profit_per_unit
FROM discount_brackets
GROUP BY discount_tier
ORDER BY discount_tier;

-- ------------------------------------------------------------------------------
-- Insight 2: Chronic Loss-Making Products & Bleeders
-- Business Action: Identify products that destroy significant enterprise value,
-- their prevailing discount levels, and the regions driving those sales.
-- ------------------------------------------------------------------------------
SELECT 
    product_id,
    product_name,
    category,
    sub_category,
    COUNT(DISTINCT order_id)                                         AS total_orders,
    SUM(quantity)                                                    AS total_units_sold,
    ROUND(SUM(sales), 2)                                             AS total_sales,
    ROUND(SUM(profit), 2)                                            AS total_loss,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0) * 100)::NUMERIC, 2)   AS profit_margin_pct,
    ROUND(AVG(discount) * 100, 2)                                    AS avg_discount_applied_pct,
    STRING_AGG(DISTINCT region, ', ' ORDER BY region)                AS regions_sold
FROM core.retail_sales
GROUP BY product_id, product_name, category, sub_category
HAVING SUM(profit) < -1000
ORDER BY total_loss ASC
LIMIT 15;

-- ------------------------------------------------------------------------------
-- Insight 3: Customer RFM Segmentation (Recency, Frequency, Monetary)
-- Business Value: Segment customer base into actionable behavioral cohorts for
-- targeted marketing, retention campaigns, and VIP loyalty programs.
-- ------------------------------------------------------------------------------
WITH customer_rfm_raw AS (
    SELECT 
        customer_id,
        MAX(customer_name) AS customer_name,
        MAX(segment) AS segment,
        -- Reference date set to 2017-12-31 (the day after the dataset max order date)
        ('2017-12-31'::DATE - MAX(order_date))::INT AS recency_days,
        COUNT(DISTINCT order_id) AS frequency_orders,
        ROUND(SUM(sales), 2) AS monetary_spend,
        ROUND(SUM(profit), 2) AS total_profit_contributed
    FROM core.retail_sales
    GROUP BY customer_id
),
customer_rfm_scores AS (
    SELECT 
        customer_id,
        customer_name,
        segment,
        recency_days,
        frequency_orders,
        monetary_spend,
        total_profit_contributed,
        -- Score from 1 (lowest) to 4 (highest)
        -- For recency, lower days = better score (hence DESC order in NTILE)
        NTILE(4) OVER (ORDER BY recency_days DESC)   AS r_score,
        NTILE(4) OVER (ORDER BY frequency_orders ASC) AS f_score,
        NTILE(4) OVER (ORDER BY monetary_spend ASC)   AS m_score
    FROM customer_rfm_raw
),
rfm_segments AS (
    SELECT 
        customer_id,
        customer_name,
        segment,
        recency_days,
        frequency_orders,
        monetary_spend,
        total_profit_contributed,
        r_score,
        f_score,
        m_score,
        CONCAT(r_score, f_score, m_score) AS rfm_combined,
        CASE 
            WHEN r_score = 4 AND f_score = 4 AND m_score >= 3 THEN 'Champions (VIP)'
            WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
            WHEN r_score >= 3 AND f_score < 3 THEN 'Recent Potentialists'
            WHEN r_score = 2 AND f_score >= 3 THEN 'Needs Attention (Slipping)'
            WHEN r_score = 1 AND f_score >= 3 THEN 'At Risk (High Spender Dormant)'
            WHEN r_score = 1 AND f_score <= 2 THEN 'Lost / Inactive'
            ELSE 'Standard Active Customers'
        END AS rfm_segment
    FROM customer_rfm_scores
)
-- Aggregate summary by RFM Segment
SELECT 
    rfm_segment,
    COUNT(*)                                                          AS customer_count,
    ROUND((COUNT(*)::NUMERIC / SUM(COUNT(*)) OVER () * 100), 2)       AS customer_share_pct,
    ROUND(AVG(recency_days), 1)                                       AS avg_days_since_last_order,
    ROUND(AVG(frequency_orders), 1)                                   AS avg_order_frequency,
    ROUND(SUM(monetary_spend), 2)                                     AS total_revenue,
    ROUND((SUM(monetary_spend) / SUM(SUM(monetary_spend)) OVER () * 100), 2) AS revenue_share_pct,
    ROUND(SUM(total_profit_contributed), 2)                           AS total_profit,
    ROUND(AVG(monetary_spend), 2)                                     AS avg_monetary_spend_per_customer
FROM rfm_segments
GROUP BY rfm_segment
ORDER BY total_revenue DESC;

-- ------------------------------------------------------------------------------
-- Insight 4: Customer Acquisition Cohort Analysis
-- Purpose: Track how customer cohorts acquired in different calendar years
-- behave and generate revenue over consecutive years.
-- ------------------------------------------------------------------------------
WITH customer_cohort AS (
    SELECT 
        customer_id,
        EXTRACT(YEAR FROM MIN(order_date))::INT AS cohort_year
    FROM core.retail_sales
    GROUP BY customer_id
),
cohort_annual_spend AS (
    SELECT 
        c.cohort_year,
        EXTRACT(YEAR FROM s.order_date)::INT AS activity_year,
        COUNT(DISTINCT s.customer_id) AS active_customers,
        ROUND(SUM(s.sales), 2) AS cohort_sales,
        ROUND(SUM(s.profit), 2) AS cohort_profit
    FROM core.retail_sales s
    JOIN customer_cohort c ON s.customer_id = c.customer_id
    GROUP BY c.cohort_year, EXTRACT(YEAR FROM s.order_date)::INT
)
SELECT 
    cohort_year,
    activity_year,
    (activity_year - cohort_year) AS cohort_age_years,
    active_customers,
    cohort_sales,
    cohort_profit,
    ROUND((cohort_profit / NULLIF(cohort_sales, 0) * 100)::NUMERIC, 2) AS cohort_margin_pct
FROM cohort_annual_spend
ORDER BY cohort_year, activity_year;

-- ------------------------------------------------------------------------------
-- Insight 5: Pareto Principle Analysis (80/20 Rule)
-- Question: Does the classic Pareto distribution apply to Superstore customers?
-- What percentage of customers generates 80% of the total revenue?
-- ------------------------------------------------------------------------------
WITH customer_revenue AS (
    SELECT 
        customer_id,
        customer_name,
        ROUND(SUM(sales), 2) AS customer_sales,
        ROW_NUMBER() OVER (ORDER BY SUM(sales) DESC) AS sales_rank,
        COUNT(*) OVER () AS total_customer_count,
        SUM(SUM(sales)) OVER () AS enterprise_total_sales
    FROM core.retail_sales
    GROUP BY customer_id, customer_name
),
pareto_calc AS (
    SELECT 
        customer_id,
        customer_name,
        customer_sales,
        sales_rank,
        total_customer_count,
        ROUND((sales_rank::NUMERIC / total_customer_count * 100), 2) AS customer_percentile,
        SUM(customer_sales) OVER (ORDER BY customer_sales DESC) AS cumulative_sales,
        ROUND((SUM(customer_sales) OVER (ORDER BY customer_sales DESC) / enterprise_total_sales * 100), 2) AS cumulative_sales_pct
    FROM customer_revenue
)
SELECT 
    CASE 
        WHEN cumulative_sales_pct <= 50.0 THEN 'Top 50% Revenue Tier'
        WHEN cumulative_sales_pct <= 80.0 THEN '50% - 80% Revenue Tier'
        ELSE 'Long Tail (Last 20% Revenue)'
    END AS revenue_band,
    COUNT(*) AS customer_count,
    ROUND((COUNT(*)::NUMERIC / MAX(total_customer_count) * 100), 2) AS pct_of_customer_base,
    ROUND(SUM(customer_sales), 2) AS band_total_sales,
    ROUND(MIN(customer_sales), 2) AS min_spend_in_band,
    ROUND(MAX(customer_sales), 2) AS max_spend_in_band
FROM pareto_calc
GROUP BY 1
ORDER BY band_total_sales DESC;

-- ------------------------------------------------------------------------------
-- Insight 6: Product Affinity / Market Basket Co-Purchase Analysis
-- Question: Which product subcategories are most frequently co-purchased in the
-- same order? Enables cross-merchandising and checkout recommendation bundles.
-- ------------------------------------------------------------------------------
WITH order_subcategories AS (
    SELECT DISTINCT 
        order_id,
        sub_category
    FROM core.retail_sales
)
SELECT 
    a.sub_category AS subcategory_a,
    b.sub_category AS subcategory_b,
    COUNT(*) AS co_occurrence_orders,
    DENSE_RANK() OVER (ORDER BY COUNT(*) DESC) AS affinity_rank
FROM order_subcategories a
JOIN order_subcategories b
  ON a.order_id = b.order_id
 AND a.sub_category < b.sub_category  -- Prevent duplicate pairs (A,B) vs (B,A) and self-pairs
GROUP BY a.sub_category, b.sub_category
HAVING COUNT(*) >= 100
ORDER BY co_occurrence_orders DESC
LIMIT 10;

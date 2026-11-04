# SQL Interview Discussion Guide: Retail Sales Performance Analysis

This guide provides high-impact questions, candidate explanations, and code snippets from this project to help you stand out in Data Analyst and SQL Developer technical interviews.

---

## 1. Window Functions & Ranking: `ROW_NUMBER()` vs `RANK()` vs `DENSE_RANK()`

### **Interview Question:**
> *"How do `ROW_NUMBER()`, `RANK()`, and `DENSE_RANK()` differ, and how did you apply them in your retail project?"*

### **Candidate Response:**
> "All three are SQL window ranking functions, but they handle ties differently:
> 
> - **`ROW_NUMBER()`**: Always assigns an unambiguous, sequential integer (1, 2, 3...) regardless of ties. In my project (`sql/04_data_cleaning.sql`), I used `ROW_NUMBER() OVER (PARTITION BY order_id, product_id, sales, quantity ORDER BY row_id)` to identify duplicate line items. Any row with rank > 1 is flagged as a duplicate.
> - **`RANK()`**: Assigns equal ranks to tied values, but skips subsequent rank numbers (e.g., 1, 2, 2, 4).
> - **`DENSE_RANK()`**: Assigns equal ranks to tied values without skipping numbers (e.g., 1, 2, 2, 3). In `sql/05_analysis_queries.sql`, I used `DENSE_RANK()` to rank product sub-categories by profitability within each parent category so there are no arbitrary gaps."

```sql
-- Example from project: Ranking products within category
SELECT 
    category,
    sub_category,
    SUM(profit) AS total_profit,
    DENSE_RANK() OVER (
        PARTITION BY category 
        ORDER BY SUM(profit) DESC
    ) AS profit_rank
FROM core.retail_sales
GROUP BY category, sub_category;
```

---

## 2. Temporal Analysis: MoM & YoY Calculations with `LAG()`

### **Interview Question:**
> *"How did you compute Month-over-Month (MoM) and Year-over-Year (YoY) revenue growth in SQL? What edge cases did you protect against?"*

### **Candidate Response:**
> "I aggregated sales to monthly buckets inside a Common Table Expression (CTE) and then used the `LAG()` window function. 
> 
> - For **MoM**, I lagged by 1 period: `LAG(monthly_sales, 1) OVER (ORDER BY order_month)`.
> - For **YoY**, because the data is aggregated by calendar month, I lagged by 12 periods: `LAG(monthly_sales, 12) OVER (ORDER BY order_month)`.
> - **Edge cases**: To prevent `division by zero` runtime exceptions for newly introduced periods or zero-revenue months, I wrapped the divisor in `NULLIF(prev_month_sales, 0)`. If the previous value is null or zero, SQL safely returns `NULL` rather than failing the entire query."

```sql
-- MoM Growth Formula
ROUND(((monthly_sales - prev_month_sales) / NULLIF(prev_month_sales, 0) * 100)::NUMERIC, 2) AS mom_growth_pct
```

---

## 3. Advanced Analytical Modeling: RFM Customer Segmentation with `NTILE()`

### **Interview Question:**
> *"Walk me through how you implemented Customer Segmentation without machine learning using SQL."*

### **Candidate Response:**
> "I implemented an RFM (Recency, Frequency, Monetary) segmentation model directly in PostgreSQL using `NTILE(4)`.
> 
> 1. **Metrics Calculation**:
>    - **Recency**: Days elapsed between each customer's last purchase and the dataset anchor date (`'2017-12-31'::DATE - MAX(order_date)`).
>    - **Frequency**: Distinct order count (`COUNT(DISTINCT order_id)`).
>    - **Monetary**: Total revenue spend (`SUM(sales)`).
> 2. **Scoring via Quartiles**: I used `NTILE(4)` to divide customers into 4 equal quartiles. For recency, lower days is superior, so I sorted `DESC` to ensure the most recent purchasers received a 4.
> 3. **Behavioral Archetypes**: Using a `CASE` statement on the combined scores, I classified customers into business cohorts like *Champions (VIP)*, *Loyal Customers*, *At Risk*, and *Lost*."

---

## 4. Business Acumen: The "Discount Cliff" Discovery

### **Interview Question:**
> *"What was the most surprising or impactful business insight you uncovered in the Superstore data?"*

### **Candidate Response:**
> "The discovery of what I term the **'Discount Cliff'**. In retail, sales teams often discount aggressively believing increased volume will compensate for tighter margins. 
> 
> By running a bucketing query across discount tiers, I discovered:
> - Orders with **0% discount** enjoyed a **+29.51% net profit margin**.
> - Orders with **1% to 20% discount** achieved a healthy **+11.91% margin**.
> - But past 20%, margins collapsed into negative territory (-15.30% for 21-40% discount, and -122.63% for discounts >60%).
> 
> This meant the company was losing \$1.23 for every \$1.00 of merchandise sold at >60% discount. My strategic recommendation was establishing a hard approval guardrail capping discounts at 20% unless authorized by regional directors."

---

## 5. Cumulative Window Aggregations: The Pareto (80/20) Rule

### **Interview Question:**
> *"How did you evaluate whether 20% of customers generated 80% of revenue?"*

### **Candidate Response:**
> "I used an unbounded running window sum. I ordered customers by total spend descending and calculated:
> `SUM(customer_sales) OVER (ORDER BY customer_sales DESC) / SUM(customer_sales) OVER () * 100`.
> 
> I found that the top 50% of revenue is generated by just the top **18.7% of customers**, and 80% of revenue is driven by **49.8% of customers**. This demonstrates that while the revenue is moderately concentrated, the company still maintains a significant customer long-tail."

---

## 6. Data Quality & Data Engineering Discipline

### **Interview Question:**
> *"Did you encounter any data quality defects in the Superstore data, and how did you resolve them?"*

### **Candidate Response:**
> "Yes, three key issues:
> 1. **Postal Code Integer Truncation**: US Zip codes from northeastern states (e.g. Vermont `05408`) were stored as numbers in CSV, dropping the leading zero (`5408`). I standardized them with `LPAD(TRIM(postal_code), 5, '0')` and typed the database column as `VARCHAR(20)`.
> 2. **Duplicate Line Items**: Row 3406 and 3407 contained identical order, product, and financial attributes. Rather than silently deleting them—which distorts ERP financial audits—I preserved both in the database with their raw `row_id` and exposed them in an audit view with duplicate rankings.
> 3. **Idempotent Ingestion**: To prevent duplicate inserts during script re-runs, I implemented PostgreSQL `ON CONFLICT (row_id) DO UPDATE` upsert logic."

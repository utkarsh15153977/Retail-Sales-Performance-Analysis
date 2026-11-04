# Retail Sales Performance Analysis

[![PostgreSQL](https://img.shields.io/badge/Database-PostgreSQL_12%2B-blue.svg?logo=postgresql&logoColor=white)](https://www.postgresql.org/)
[![Python](https://img.shields.io/badge/Python-3.10%2B-green.svg?logo=python&logoColor=white)](https://www.python.org/)
[![Excel](https://img.shields.io/badge/Dashboard-Microsoft_Excel-217346.svg?logo=microsoftexcel&logoColor=white)](https://www.microsoft.com/excel)
[![Tests](https://img.shields.io/badge/Tests-Pytest_Passing-brightgreen.svg?logo=pytest&logoColor=white)](https://docs.pytest.org/)
[![License](https://img.shields.io/badge/License-MIT-lightgrey.svg)](LICENSE)

An end-to-end data engineering, SQL analytics, and business intelligence portfolio project analyzing retail sales transactions from the **Sample Superstore** dataset. 

This project is designed for **Entry-Level Data Analyst job applications**, **GitHub portfolio demonstration**, **technical SQL interviews**, and **executive dashboard presentations**.

---

## 📌 Executive Business Summary

Over the 4-year operating period from 2014 through 2017, the retail enterprise recorded **\$2,297,200.86 in gross revenue** and **\$286,397.02 in net profit** across 5,009 customer orders, yielding an overall **blended profit margin of 12.47%**.

### High-Impact Strategic Findings:
1. **The "Discount Cliff" Inflection Point**:
   - Orders with **0% discount** yielded a **+29.51% net margin** (+\$320,988 profit).
   - Orders with **1% to 20% discount** maintained a sustainable **+11.91% margin** (+\$100,785 profit).
   - Orders discounted **>20% were net unprofitable**, losing **-\$135,376 in profit** across 1,393 transactions. Orders discounted >60% destroyed **\$1.23 for every \$1.00 of merchandise sold**.
2. **The Furniture Category Crisis**:
   - Technology (+17.4% margin) and Office Supplies (+17.0% margin) drove company profit.
   - Furniture produced a meager **2.49% margin**, caused by chronic losses in **Tables (-\$17,725.48)** and **Bookcases (-\$3,472.56)** due to high discounts and shipping overhead.
3. **Geographic Divergence**:
   - The **West** (+\$108.4K profit, 14.9% margin) and **East** (+\$91.5K profit, 13.5% margin) generated 70% of enterprise profits.
   - The **Central** region lagged severely (7.9% margin), dragged down by deep-discount losses in Texas (-\$25.7K) and Illinois (-\$12.6K).

---

## 🛠️ Technology Stack

| Technology | Purpose in Project |
| :--- | :--- |
| **PostgreSQL 12+** | Relational data warehouse, dimensional Star Schema modeling, window functions, and CTE business queries. |
| **SQL** | Analytical queries, RFM segmentation, cohort modeling, data quality auditing, and deduplication audit views. |
| **Python (3.10+)** | Production ETL pipeline (`data_loader.py`), automated data validation, postal code standardization, and test suites. |
| **Pandas / OpenPyXL** | Ingestion manipulation and programmatic generation of formatted corporate Excel workbooks. |
| **Microsoft Excel** | C-suite Executive Dashboard, KPI scorecards, Monthly Trends, and Category-Region pivot matrices. |
| **Pytest** | Automated unit tests validating data cleanliness, date parsing, constraints, and metric integrity. |
| **Git / GitHub** | Version control, documentation structure, and open-source portfolio hosting. |

---

## 📂 Project Architecture & Directory Layout

```
retail-sales-performance-analysis/
│
├── data/
│   ├── raw/
│   │   └── sample_superstore.csv          <- Canonical raw source CSV (9,994 rows)
│   └── processed/
│       ├── superstore_cleaned.csv         <- Cleansed, typed, zero-padded CSV
│       └── retail_sales.db                <- SQLite validation database for offline query execution
│
├── sql/
│   ├── 01_create_database.sql             <- Database creation, roles, extensions, and schema layout
│   ├── 02_create_tables.sql               <- DDL for staging, core transactional table, Star Schema & indexes
│   ├── 03_data_validation.sql             <- 11 rigorous data quality audit queries
│   ├── 04_data_cleaning.sql               <- Postal code formatting, non-destructive deduplication view & ETL
│   ├── 05_analysis_queries.sql            <- Core business queries (KPIs, MoM/YoY growth, Geography, Products)
│   └── 06_business_insights.sql           <- Advanced BI queries (Discount cliff, RFM segmentation, Cohorts, Pareto)
│
├── python/
│   ├── __init__.py
│   └── data_loader.py                     <- Enterprise Python ETL & automated quality auditor
│
├── excel/
│   ├── generate_excel_dashboard.py        <- Script generating the formatted multi-tab Excel dashboard
│   └── retail_sales_performance_dashboard.xlsx <- Executive Excel Dashboard with formulas & styling
│
├── reports/
│   ├── executive_summary.md               <- Strategic C-level business analysis & 3-pillar action plan
│   └── data_quality_report.md             <- Formal data quality audit scorecard and edge-case autopsy
│
├── docs/
│   ├── data_dictionary.md                 <- Field definitions, constraints, types, and business rules
│   ├── architecture.md                    <- System architecture diagram, medallion design, star schema
│   ├── sql_interview_guide.md             <- Top technical SQL interview questions based on this project
│   └── excel_dashboard_guide.md           <- Dashboard presentation script and visualization walkthrough
│
├── tests/
│   ├── __init__.py
│   └── test_data_pipeline.py              <- Pytest automated test suite
│
├── .env.example                           <- Environment configuration template for database connection
├── requirements.txt                       <- Python dependencies
├── .gitignore                             <- Git ignore rules
└── README.md                              <- Project master documentation
```

---

## 📊 Relational Database Design (PostgreSQL)

The database follows a modern layered architecture:
- `staging.superstore_raw`: Permissive text landing table for raw ELT ingestion.
- `core.retail_sales`: Cleansed, strictly typed transactional table containing all 21 standard attributes with primary keys, indexes, and stored generated profit margins.
- `core.dim_*` & `core.fact_sales`: Kimball Star Schema separating dimensional entities (`dim_customers`, `dim_products`, `dim_geography`, `dim_date`) from transactional facts (`fact_sales`).

### Table Schema (`core.retail_sales`)
```sql
CREATE TABLE core.retail_sales (
    row_id             INT PRIMARY KEY,
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
    postal_code        VARCHAR(20) NULL,
    region             VARCHAR(20) NOT NULL,
    product_id         VARCHAR(30) NOT NULL,
    category           VARCHAR(50) NOT NULL,
    sub_category       VARCHAR(50) NOT NULL,
    product_name       VARCHAR(255) NOT NULL,
    sales              NUMERIC(12, 4) NOT NULL CHECK (sales >= 0.0),
    quantity           INT NOT NULL CHECK (quantity > 0),
    discount           NUMERIC(5, 4) NOT NULL CHECK (discount BETWEEN 0.0 AND 1.0),
    profit             NUMERIC(12, 4) NOT NULL,
    profit_margin      NUMERIC(7, 4) GENERATED ALWAYS AS (
                           CASE WHEN sales > 0 THEN ROUND((profit / sales)::NUMERIC, 4) ELSE 0.0 END
                       ) STORED,
    CONSTRAINT chk_ship_after_order CHECK (ship_date >= order_date)
);
```

---

## 🔍 Data Quality Methodology

The data pipeline strictly adheres to the principle: **Never silently delete records or invent replacement values.**

| Issue Detected | Root Cause | Engineering Solution |
| :--- | :--- | :--- |
| **Truncated Zip Codes (449 records)** | Northeastern states (e.g. VT `05408`) lost leading zeros when untyped CSVs treated them as integers (`5408`). | Defined column as `VARCHAR(20)` and standardized via `LPAD(postal_code, 5, '0')`. |
| **Duplicate Line Item (Row 3406 vs 3407)** | Same order, product, and financial values. In POS/ERP, this reflects multi-box shipments. | Preserved both rows in `core.retail_sales` and constructed an audit view `core.v_duplicate_line_items` using `ROW_NUMBER()`. |
| **Accidental Re-import Prevention** | Repeated batch script runs risk inserting duplicate rows. | Enforced `ON CONFLICT (row_id) DO UPDATE` idempotent upsert logic in Python. |
| **Temporal Consistency** | Orders cannot ship prior to purchase. | Added database constraint `CHECK (ship_date >= order_date)`. Zero violations detected. |

---

## 📈 SQL Analytics & Business Queries Showcase

### 1. Executive KPI Summary (`sql/05_analysis_queries.sql`)
```sql
SELECT 
    COUNT(DISTINCT order_id)                                           AS total_orders,
    COUNT(DISTINCT customer_id)                                        AS total_customers,
    SUM(quantity)                                                      AS total_units_sold,
    ROUND(SUM(sales), 2)                                               AS total_sales_usd,
    ROUND(SUM(profit), 2)                                              AS total_profit_usd,
    ROUND((SUM(profit) / NULLIF(SUM(sales), 0) * 100)::NUMERIC, 2)     AS overall_profit_margin_pct,
    ROUND((SUM(sales) / NULLIF(COUNT(DISTINCT order_id), 0))::NUMERIC, 2) AS average_order_value_aov
FROM core.retail_sales;
```
*Result:* 5,009 Orders | 793 Customers | 37,873 Units | \$2,297,200.86 Sales | \$286,397.02 Profit | 12.47% Margin | \$458.61 AOV.

### 2. Month-over-Month & Year-over-Year Growth with `LAG()`
```sql
WITH monthly_metrics AS (
    SELECT 
        DATE_TRUNC('month', order_date)::DATE AS order_month,
        ROUND(SUM(sales), 2)                  AS monthly_sales,
        ROUND(SUM(profit), 2)                 AS monthly_profit
    FROM core.retail_sales
    GROUP BY 1
)
SELECT 
    order_month,
    monthly_sales,
    monthly_profit,
    ROUND(((monthly_sales - LAG(monthly_sales, 1) OVER (ORDER BY order_month)) 
           / NULLIF(LAG(monthly_sales, 1) OVER (ORDER BY order_month), 0) * 100)::NUMERIC, 2) AS mom_growth_pct,
    ROUND(((monthly_sales - LAG(monthly_sales, 12) OVER (ORDER BY order_month)) 
           / NULLIF(LAG(monthly_sales, 12) OVER (ORDER BY order_month), 0) * 100)::NUMERIC, 2) AS yoy_growth_pct
FROM monthly_metrics
ORDER BY order_month;
```

### 3. Customer RFM Segmentation using `NTILE()` (`sql/06_business_insights.sql`)
Scores customers on **Recency** (days since last purchase), **Frequency** (order count), and **Monetary spend**, grouping them into actionable cohorts:
- **Champions (VIP)**: Top-quartile across all dimensions (generate 34% of company profit).
- **At Risk**: High historical spenders whose recency has slipped over 180 days.
- **Lost / Inactive**: Dormant accounts with low frequency.

---

## 🚀 Setup & Execution Guide (Windows PowerShell)

### Prerequisites
- Python 3.10+
- PostgreSQL 12+ (or use the built-in zero-dependency SQLite database)
- Git

### Step 1: Clone Repository & Create Virtual Environment
```powershell
# Open Windows PowerShell
cd "F:\Projects"
git clone https://github.com/your-username/retail-sales-performance-analysis.git
cd "retail-sales-performance-analysis"

# Create and activate Python virtual environment
python -m venv .venv
.\.venv\Scripts\Activate.ps1

# Install required dependencies
pip install -r requirements.txt
```

### Step 2: Run Data Ingestion & Audit Pipeline
The Python pipeline cleanses the raw data, standardizes postal codes, verifies all constraints, and generates the processed files:
```powershell
# Ingest raw CSV, perform quality audit, and generate processed files
python python\data_loader.py
```
*Output: Generates `data/processed/superstore_cleaned.csv` and populates `data/processed/retail_sales.db`.*

### Step 3: Run Automated Test Suite
```powershell
pytest tests\test_data_pipeline.py -v
```
*Expected: 5 passed in < 2 seconds.*

### Step 4: Generate Excel Executive Dashboard
```powershell
python excel\generate_excel_dashboard.py
```
*Output: Creates `excel/retail_sales_performance_dashboard.xlsx` with formatted scorecards, monthly trends, and pivot matrices.*

---

## 🗄️ PostgreSQL Database Setup Instructions

If you have a local PostgreSQL instance running:

1. **Configure Environment Variables**:
   ```powershell
   Copy-Item .env.example .env
   # Edit .env with your PostgreSQL credentials
   ```

2. **Execute Database Setup Scripts via `psql`**:
   ```powershell
   # 1. Create database and schemas
   psql -U postgres -f sql\01_create_database.sql

   # 2. Connect to the database and create tables
   psql -U postgres -d retail_sales_db -f sql\02_create_tables.sql

   # 3. Load data using the Python pipeline
   python python\data_loader.py --load-postgres --pg-dbname retail_sales_db --pg-user postgres

   # 4. Run data validation audit
   psql -U postgres -d retail_sales_db -f sql\03_data_validation.sql

   # 5. Execute data cleaning and populate Star Schema
   psql -U postgres -d retail_sales_db -f sql\04_data_cleaning.sql

   # 6. Run analytical queries
   psql -U postgres -d retail_sales_db -f sql\05_analysis_queries.sql

   # 7. Run strategic business insight queries
   psql -U postgres -d retail_sales_db -f sql\06_business_insights.sql
   ```

*(Note: If you do not have a live PostgreSQL server installed, the project automatically provides `data/processed/retail_sales.db` so you can immediately query the dataset in SQLite, DBeaver, or VS Code!)*

---

## 📑 Portfolio Documentation Index

- 📖 **[Executive Summary Report](reports/executive_summary.md)**: C-level business analysis, strategic pillars, and financial roadmap.
- 📋 **[Data Quality Report](reports/data_quality_report.md)**: Formal audit scorecard, edge-case autopsy, and integrity verification.
- 📚 **[Data Dictionary](docs/data_dictionary.md)**: Complete column-by-column metadata, data types, constraints, and business logic.
- 🏛️ **[Architecture Design](docs/architecture.md)**: Medallion layer design, Kimball Star Schema, and indexing strategy.
- 💬 **[SQL Interview Discussion Guide](docs/sql_interview_guide.md)**: Technical interview talking points, window function deep-dives, and business acumen answers.
- 📊 **[Excel Dashboard User Guide](docs/excel_dashboard_guide.md)**: Visual dashboard walkthrough and presentation scripts.

---

## 👤 Author & Contact
- **Role:** Senior Data Analyst & SQL Developer
- **Portfolio:** [GitHub Profile](https://github.com/)
- **License:** MIT License

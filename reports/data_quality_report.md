# Data Quality Audit Report: Retail Sales Performance Analysis

**Auditor:** Senior Data Analyst & SQL Developer  
**Audit Target:** Sample Superstore Dataset (`core.retail_sales`)  
**Audit Date:** 2026-11-04  
**Audit Status:** **PASSED WITH OBSERVATIONS**  

---

## 1. Executive Summary

A comprehensive data quality audit was conducted on the Sample Superstore retail sales dataset across 9,994 transaction records spanning January 2014 through December 2017. 

The audit verified structural integrity, schema adherence, domain constraints, entity cardinalities, and distributional boundaries. All critical validation criteria passed. Minor anomalies (e.g., zip code zero-truncation, non-fatal line-item duplicates) were identified, audited, and resolved via standardized ELT procedures without silent data loss.

---

## 2. Audit Verification Scorecard

| # | Audit Check Dimension | Pass / Fail Criteria | Observed Value | Audit Result | Action Taken / Rationale |
| :--- | :--- | :--- | :--- | :--- | :--- |
| **1** | **Total Records** | Exactly 9,994 rows | 9,994 rows | **PASSED** | Full source row count verified. |
| **2** | **Primary Key (`row_id`) Uniqueness** | 0 duplicate row IDs | 0 duplicates | **PASSED** | Guaranteed entity uniqueness. |
| **3** | **Exact Duplicate Records (Non-ID)** | 0 unexpected duplicates | 1 duplicate pair | **OBSERVATION** | Row 3406 & 3407 share identical attributes. Retained with provenance in `core.v_duplicate_line_items`. |
| **4** | **Duplicate (Order ID, Product ID)** | Retail line-item review | 8 occurrences | **OBSERVATION** | Legitimate multiple line-items per order; non-fatal in POS/ERP. |
| **5** | **Mandatory Column NULLs** | 0 NULLs in mandatory fields | 0 NULLs | **PASSED** | 100% field completeness across 20 mandatory columns. |
| **6** | **Postal Code NULLs & Format** | Valid 5-digit US ZIP | 449 truncated ZIPs (e.g. VT `5408`) | **RESOLVED** | Standardized via `LPAD(postal_code, 5, '0')`. Column typed as `VARCHAR(20)`. |
| **7** | **Chronological Sequence** | `ship_date >= order_date` | 0 anachronisms | **PASSED** | All orders shipped between 0 and 7 days after placement. |
| **8** | **Negative / Zero Sales & Quantity** | `sales > 0` and `quantity > 0` | 0 negative/zero values | **PASSED** | Minimum sales: \$0.44; Minimum quantity: 1. |
| **9** | **Discount Domain Range** | `0.00 <= discount <= 1.00` | Range: `0.00` to `0.80` | **PASSED** | All discount rates adhere to valid mathematical bounds. |
| **10**| **Profit Distribution & Outliers** | Valid financial values | Range: `-$6,599.98` to `+$8,399.98` | **PASSED** | 1,871 loss-making orders (18.72%) audited; valid returns/markdowns. |
| **11**| **Date Span Coverage** | 4-year calendar span | `2014-01-03` to `2017-12-30` | **PASSED** | Complete 48-month temporal coverage without gaps. |
| **12**| **Entity Cardinalities** | Matches known benchmarks | 793 Customers, 5,009 Orders, 1,862 Products | **PASSED** | Exact benchmark alignment. |

---

## 3. Deep-Dive Findings & Technical Handling

### 3.1 Postal Code Integer Truncation (449 Records)
- **Root Cause**: When CSV files are exported by spreadsheet software or ingested into loosely typed environments, numeric zip codes beginning with `0` (common in New England states such as Vermont, Massachusetts, Connecticut, Rhode Island, and New Jersey) lose their leading zeros (e.g. `5408` instead of `05408`).
- **Resolution**:
  - The column was defined as `VARCHAR(20)` in PostgreSQL.
  - The Python loader and SQL script execute `LPAD(TRIM(postal_code), 5, '0')`.
  - Zero information was lost; full zip code integrity restored.

### 3.2 Duplicate Transaction Analysis (Row 3406 vs 3407)
- **Details**:
  - Order ID: `US-2014-150119`
  - Customer: Laurel Beltran (`LB-16795`)
  - Product: `FUR-CH-10002965` (Global High-Back Mesh Executive Chair, Black)
  - Sales: \$281.37, Quantity: 2, Discount: 0.30, Profit: -\$12.06
- **Analytical Decision**:
  - **Never silently delete data**. In retail operations, identical line items often represent split delivery packages or separate physical boxes scanned under the same invoice.
  - Both rows are maintained in `core.retail_sales`.
  - An analytical audit view (`core.v_duplicate_line_items`) was constructed using `ROW_NUMBER() OVER (PARTITION BY order_id, product_id, sales, quantity, discount, profit ORDER BY row_id)` to allow business stakeholders to review and toggle deduplicated calculations as needed.

### 3.3 Negative Profit Distributions (1,871 Transactions)
- **Finding**: 18.72% of all line items (1,871 out of 9,994) have negative profit values, aggregating to -\$156,131.29 in gross losses.
- **Root Cause**:
  - Deep discounting exceeding 20% severely exceeds standard product gross margins.
  - Concentrated in Furniture (`Tables` losing -\$17.7K, `Bookcases` losing -\$3.5K) and heavily discounted regions (Central and South).
- **Data Integrity Verdict**: Valid economic behavior, not data corruption.

---

## 4. Entity Cardinality Summary

```
--------------------------------------------------
Total Transactions Audited:       9,994
Unique Orders:                     5,009
Unique Customers:                  793
Unique Products (SKUs):            1,862
Unique Product Descriptions:       1,850
Operating Regions:                 4
States Covered:                    49 (incl. DC)
Cities Covered:                    531
Total Sales Volume:                $2,297,200.86
Total Net Profit Volume:           $286,397.02
--------------------------------------------------
```

## 5. Audit Conclusion
The dataset passes all enterprise data quality requirements for downstream analytical modeling, PostgreSQL relational warehousing, and executive dashboard reporting.

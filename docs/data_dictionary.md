# Data Dictionary: Retail Sales Performance Analysis

## Overview
This data dictionary documents the schema, field descriptions, source formats, target PostgreSQL types, constraints, and business handling rules for the **Sample Superstore** dataset.

---

## 1. Table: `core.retail_sales`

| Column Name | PostgreSQL Data Type | Source Format | Nullable | Primary Key | Constraints / Rules | Description & Business Context |
| :--- | :--- | :--- | :--- | :--- | :--- | :--- |
| `row_id` | `INTEGER` | Integer (1..9994) | **No** | **Yes** | `> 0` | Unique surrogate identifier for each transaction line item. |
| `order_id` | `VARCHAR(25)` | String (`CA-2016-152156`) | **No** | No | Format: `[CC]-[YYYY]-[ID]` | Business order identifier. An order can have multiple product lines. |
| `order_date` | `DATE` | String (`MM/DD/YYYY`) | **No** | No | `2014-01-03` to `2017-12-30` | Calendar date on which customer placed the purchase order. |
| `ship_date` | `DATE` | String (`MM/DD/YYYY`) | **No** | No | `ship_date >= order_date` | Calendar date on which merchandise departed fulfillment facility. |
| `ship_mode` | `VARCHAR(25)` | String (`Standard Class`) | **No** | No | Standard Class, Second Class, First Class, Same Day | Shipping class chosen at order placement. |
| `customer_id` | `VARCHAR(20)` | String (`CG-12520`) | **No** | No | Format: `[Initials]-[5 digits]` | Unique natural identifier for individual customer accounts. |
| `customer_name` | `VARCHAR(100)` | String (`Claire Gute`) | **No** | No | Standardized, trimmed | Full legal name of customer. |
| `segment` | `VARCHAR(50)` | String (`Consumer`) | **No** | No | Consumer, Corporate, Home Office | Customer account classification category. |
| `country` | `VARCHAR(50)` | String (`United States`) | **No** | No | Default: `'United States'` | Sovereign nation of shipping destination. |
| `city` | `VARCHAR(50)` | String (`Henderson`) | **No** | No | Standardized, trimmed | Municipal jurisdiction of shipping destination. |
| `state` | `VARCHAR(50)` | String (`Kentucky`) | **No** | No | 49 contiguous US States + DC | US state or administrative territory. |
| `postal_code` | `VARCHAR(20)` | String / Int (`42420`, `5408`) | **Yes** | No | Formatted to 5-digit string | US ZIP code. Left-padded with zeros (e.g., VT `05408`). |
| `region` | `VARCHAR(20)` | String (`South`) | **No** | No | Central, East, South, West | Geographic sales territory division. |
| `product_id` | `VARCHAR(30)` | String (`FUR-BO-10001798`) | **No** | No | Format: `[CAT]-[SUB]-[8 digits]` | Unique SKU/product catalog identifier. |
| `category` | `VARCHAR(50)` | String (`Furniture`) | **No** | No | Furniture, Office Supplies, Technology | Top-level merchandise grouping. |
| `sub_category` | `VARCHAR(50)` | String (`Bookcases`) | **No** | No | 17 discrete sub-categories | Granular departmental classification. |
| `product_name` | `VARCHAR(255)` | String (`Bush Somerset...`) | **No** | No | Standardized, trimmed | Commercial product title and model description. |
| `sales` | `NUMERIC(12, 4)` | Float (`261.96`) | **No** | No | `CHECK (sales >= 0.0)` | Total invoice sales amount charged to customer in USD. |
| `quantity` | `INTEGER` | Integer (`2`) | **No** | No | `CHECK (quantity > 0)` | Number of discrete physical units sold. |
| `discount` | `NUMERIC(5, 4)` | Float (`0.0`, `0.2`) | **No** | No | `CHECK (discount BETWEEN 0.0 AND 1.0)` | Promotional discount percentage expressed as a decimal. |
| `profit` | `NUMERIC(12, 4)` | Float (`41.9136`, `-12.0588`) | **No** | No | Unbounded (positive or negative) | Net profit/loss in USD after accounting for cost and discount. |
| `profit_margin` | `NUMERIC(7, 4)` | Generated Column | **No** | No | Generated `profit / sales` | Stored computed profit margin. |
| `created_at` | `TIMESTAMPTZ` | Timestamp | **No** | No | Default: `CURRENT_TIMESTAMP` | Audit timestamp of ETL database insertion. |

---

## 2. Business Logic & Special Handling Rules

### 2.1 Postal Code Zero-Padding
- **Issue**: Source CSV loads zip codes as integer numbers in Excel/Python if untyped. Northeastern states (Maine, Massachusetts, Rhode Island, Vermont, New Jersey) have zip codes beginning with `0` (e.g. `05408` in Burlington, Vermont).
- **Rule**: Postal codes must always be treated as `VARCHAR(20)`. The ETL pipeline applies `LPAD(postal_code, 5, '0')` to preserve valid postal identity without data loss.

### 2.2 Preserving Duplicate Line Items
- **Issue**: Row 3406 and 3407 share identical `Order ID` (`US-2014-150119`), customer, product, quantity, discount, and profit.
- **Rule**: Never silently delete records. In commercial ERPs, identical lines indicate distinct packages or multiple shipments. Both rows are preserved in `core.retail_sales` and exposed in `core.v_duplicate_line_items` for financial transparency.

### 2.3 The Discount Cliff
- Discounts ranging from `0.00` to `0.20` maintain healthy profitability (+11.9% to +29.5% margin).
- Discounts greater than `0.20` result in acute margin destruction across all categories. Discarding or capping discount rates is prohibited; values are captured faithfully.

# Excel Dashboard User & Presentation Guide

## 1. Overview
The companion Excel workbook (`excel/retail_sales_performance_dashboard.xlsx`) provides an executive-ready dashboard built on top of the cleansed Sample Superstore dataset. It is structured for C-suite executive briefings, business stakeholders, and technical interviews.

---

## 2. Workbook Structure

The workbook contains four purpose-built worksheets:

```
retail_sales_performance_dashboard.xlsx
├── 1. Executive_Dashboard      (KPI scorecards, category summaries, regional cuts, discount cliff)
├── 2. Monthly_Trend            (48-month revenue, profit, margin trajectory, and growth)
├── 3. Category_Region_Matrix   (Cross-tabulated sales and profit matrices)
└── 4. Raw_Cleaned_Data         (Pristine 9,994 transactional rows with active AutoFilter)
```

---

## 3. Worksheet Walkthrough & Design Decisions

### Tab 1: `Executive_Dashboard`
- **Corporate Visual Palette**: Formatted with high-contrast executive navy (`#1B365D`), subtle slate card backgrounds (`#EAEFF5`), and alert fills (`#FADBD8`) for loss-making items.
- **Top Metric Scorecards (Row 5 to 7)**:
  - **Total Revenue**: \$2,297,200.86
  - **Total Net Profit**: \$286,397.02
  - **Overall Margin**: 12.47%
  - **Total Orders**: 5,009
  - **Active Customers**: 793
  - **Average Order Value (AOV)**: \$458.61
- **Category & Sub-Category Table**: Real-time formulas for units, sales, profit, and net margin with conditional alert highlights for negative profit drivers (Tables, Bookcases, Supplies).
- **Regional Performance Summary**: Total Sales, Profit, and Profit Margin across the 4 operating territories (West, East, Central, South).
- **Discount Impact Table**: Categorizes orders into 5 distinct discount bands to highlight the steep margin cliff past 20%.

### Tab 2: `Monthly_Trend`
- Comprehensive chronological breakdown of all 48 operating months (Jan 2014 – Dec 2017).
- Enables visual tracking of Q4 holiday spikes (November and December sales surge) and annual growth.

### Tab 3: `Category_Region_Matrix`
- Two mirrored matrices providing instantaneous comparison:
  1. Gross Sales by Category across the 4 Regions.
  2. Net Profit by Category across the 4 Regions.
- Instantly demonstrates that Central region Furniture runs at an acute net loss (-\$2,871).

### Tab 4: `Raw_Cleaned_Data`
- Filter-ready transaction database with frozen headers and strict accounting number formatting.

---

## 4. How to Present This Dashboard in an Interview

1. **Start with the Executive Scorecard**:
   > *"As an executive stakeholder, looking at the top-line figures, our business generated \$2.3M in sales with an overall 12.5% profit margin across 5,009 orders. However, looking deeper reveals stark operational contrasts."*
2. **Highlight the Profitability Breakdown**:
   > *"While Technology and Office Supplies maintain healthy margins (~17%), Furniture produces a meager 2.5% margin. Digging into the sub-category table, Tables alone lost \$17.7K and Bookcases lost \$3.5K."*
3. **Walk Through the Regional Matrix**:
   > *"Our West and East territories generate 83% of total company profits. Central and South underperform heavily, driven by high discount rates in states like Texas and Ohio."*
4. **Deliver the Strategic Punchline (The Discount Cliff)**:
   > *"In the Discount Impact table, any transaction with over 20% discount produces negative returns. Discontinuing discounts above 20% immediately protects ~\$135,000 in bottom-line profit."*

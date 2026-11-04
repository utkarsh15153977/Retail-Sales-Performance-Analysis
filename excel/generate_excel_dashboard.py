#!/usr/bin/env python3
"""
Portfolio Project: Retail Sales Performance Analysis
Script: excel/generate_excel_dashboard.py
Purpose: Generates a formatted multi-tab Microsoft Excel analytical workbook
         containing an Executive Dashboard, Monthly Trends, Category-Regional
         Pivot Matrix, Discount Sensitivity, and cleansed transaction data.
Author: Senior Data Analyst & SQL Developer
"""

import os
import sys
import pandas as pd
import openpyxl
from openpyxl.styles import Font, PatternFill, Alignment, Border, Side
from openpyxl.utils import get_column_letter

# Define Color Palette (Executive Navy / Corporate Slate)
COLOR_NAVY_DARK = "1B365D"
COLOR_NAVY_LIGHT = "2E5B88"
COLOR_ACCENT_BLUE = "4A90E2"
COLOR_BG_LIGHT = "F4F6F9"
COLOR_CARD_BG = "EAEFF5"
COLOR_ALERT_RED = "FADBD8"
COLOR_SUCCESS_GREEN = "D4EFDF"
COLOR_TEXT_WHITE = "FFFFFF"
COLOR_TEXT_DARK = "1C2833"
COLOR_BORDER = "D5D8DC"

FONT_NAME = "Calibri"

def create_dashboard_workbook(input_csv: str, output_xlsx: str) -> None:
    print(f"Reading processed data from '{input_csv}'...")
    df = pd.read_csv(input_csv)
    df["order_date"] = pd.to_datetime(df["order_date"])
    df["ship_date"] = pd.to_datetime(df["ship_date"])

    wb = openpyxl.Workbook()
    # Remove default sheet
    wb.remove(wb.active)

    # Common Styles
    font_title = Font(name=FONT_NAME, size=16, bold=True, color=COLOR_TEXT_WHITE)
    font_subtitle = Font(name=FONT_NAME, size=11, italic=True, color=COLOR_TEXT_WHITE)
    font_section_header = Font(name=FONT_NAME, size=13, bold=True, color=COLOR_NAVY_DARK)
    font_tbl_header = Font(name=FONT_NAME, size=11, bold=True, color=COLOR_TEXT_WHITE)
    font_kpi_num = Font(name=FONT_NAME, size=18, bold=True, color=COLOR_NAVY_DARK)
    font_kpi_lbl = Font(name=FONT_NAME, size=9, bold=True, color="566573")
    font_data = Font(name=FONT_NAME, size=10, color=COLOR_TEXT_DARK)
    font_data_bold = Font(name=FONT_NAME, size=10, bold=True, color=COLOR_TEXT_DARK)

    fill_navy_dark = PatternFill(start_color=COLOR_NAVY_DARK, end_color=COLOR_NAVY_DARK, fill_type="solid")
    fill_navy_light = PatternFill(start_color=COLOR_NAVY_LIGHT, end_color=COLOR_NAVY_LIGHT, fill_type="solid")
    fill_card = PatternFill(start_color=COLOR_CARD_BG, end_color=COLOR_CARD_BG, fill_type="solid")
    fill_zebra = PatternFill(start_color=COLOR_BG_LIGHT, end_color=COLOR_BG_LIGHT, fill_type="solid")
    fill_alert = PatternFill(start_color=COLOR_ALERT_RED, end_color=COLOR_ALERT_RED, fill_type="solid")
    fill_success = PatternFill(start_color=COLOR_SUCCESS_GREEN, end_color=COLOR_SUCCESS_GREEN, fill_type="solid")

    thin_border_side = Side(border_style="thin", color=COLOR_BORDER)
    border_all_thin = Border(left=thin_border_side, right=thin_border_side, top=thin_border_side, bottom=thin_border_side)
    border_bottom_double = Border(
        left=thin_border_side, right=thin_border_side, top=thin_border_side,
        bottom=Side(border_style="double", color=COLOR_NAVY_DARK)
    )

    align_center = Alignment(horizontal="center", vertical="center")
    align_left = Alignment(horizontal="left", vertical="center")
    align_right = Alignment(horizontal="right", vertical="center")

    # =========================================================================
    # TAB 1: EXECUTIVE DASHBOARD
    # =========================================================================
    ws_dash = wb.create_sheet(title="Executive_Dashboard")
    ws_dash.views.sheetView[0].showGridLines = True

    # Title Banner
    ws_dash.merge_cells("A1:K2")
    ws_dash["A1"] = "RETAIL SALES PERFORMANCE - EXECUTIVE DASHBOARD"
    ws_dash["A1"].font = font_title
    ws_dash["A1"].fill = fill_navy_dark
    ws_dash["A1"].alignment = align_center

    ws_dash.merge_cells("A3:K3")
    ws_dash["A3"] = "Dataset: Sample Superstore (2014 - 2017) | Core Business Metrics & Profitability Health"
    ws_dash["A3"].font = font_subtitle
    ws_dash["A3"].fill = fill_navy_light
    ws_dash["A3"].alignment = align_center

    # KPI Summary Cards (Row 5 to 7)
    kpis = [
        ("TOTAL REVENUE", f"${df['sales'].sum():,.2f}", "A", "B"),
        ("TOTAL NET PROFIT", f"${df['profit'].sum():,.2f}", "C", "D"),
        ("PROFIT MARGIN", f"{(df['profit'].sum() / df['sales'].sum()) * 100:.2f}%", "E", "F"),
        ("TOTAL ORDERS", f"{df['order_id'].nunique():,}", "G", "G"),
        ("ACTIVE CUSTOMERS", f"{df['customer_id'].nunique():,}", "H", "I"),
        ("AVERAGE ORDER VALUE", f"${df['sales'].sum() / df['order_id'].nunique():,.2f}", "J", "K"),
    ]

    for title, val, start_col, end_col in kpis:
        cell_lbl = f"{start_col}5"
        cell_val = f"{start_col}6"
        ws_dash.merge_cells(f"{start_col}5:{end_col}5")
        ws_dash.merge_cells(f"{start_col}6:{end_col}7")

        ws_dash[cell_lbl] = title
        ws_dash[cell_lbl].font = font_kpi_lbl
        ws_dash[cell_lbl].fill = fill_card
        ws_dash[cell_lbl].alignment = align_center

        ws_dash[cell_val] = val
        ws_dash[cell_val].font = font_kpi_num
        ws_dash[cell_val].fill = fill_card
        ws_dash[cell_val].alignment = align_center

        # Borders
        for r in range(5, 8):
            for c_letter in [start_col, end_col]:
                c_idx = openpyxl.utils.column_index_from_string(c_letter)
                ws_dash.cell(row=r, column=c_idx).border = border_all_thin

    # Section 1: Category & Subcategory Breakdown (Rows 9+)
    ws_dash["A9"] = "Category & Sub-Category Performance Summary"
    ws_dash["A9"].font = font_section_header

    cat_headers = ["Category", "Sub-Category", "Units Sold", "Total Sales", "Total Profit", "Profit Margin", "Avg Discount"]
    for c_idx, h in enumerate(cat_headers, start=1):
        c = ws_dash.cell(row=10, column=c_idx, value=h)
        c.font = font_tbl_header
        c.fill = fill_navy_dark
        c.alignment = align_center
        c.border = border_all_thin

    cat_summary = df.groupby(["category", "sub_category"]).agg(
        units=("quantity", "sum"),
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        discount=("discount", "mean")
    ).reset_index().sort_values(by=["category", "sales"], ascending=[True, False])

    row_idx = 11
    for _, r in cat_summary.iterrows():
        margin = r["profit"] / r["sales"] if r["sales"] > 0 else 0
        ws_dash.cell(row=row_idx, column=1, value=r["category"]).font = font_data
        ws_dash.cell(row=row_idx, column=2, value=r["sub_category"]).font = font_data
        
        c_units = ws_dash.cell(row=row_idx, column=3, value=r["units"])
        c_units.font = font_data
        c_units.number_format = "#,##0"
        c_units.alignment = align_right

        c_sales = ws_dash.cell(row=row_idx, column=4, value=r["sales"])
        c_sales.font = font_data
        c_sales.number_format = "$#,##0.00"
        c_sales.alignment = align_right

        c_profit = ws_dash.cell(row=row_idx, column=5, value=r["profit"])
        c_profit.font = font_data
        c_profit.number_format = "$#,##0.00"
        c_profit.alignment = align_right
        if r["profit"] < 0:
            c_profit.fill = fill_alert
            c_profit.font = Font(name=FONT_NAME, size=10, bold=True, color="922B21")

        c_margin = ws_dash.cell(row=row_idx, column=6, value=margin)
        c_margin.font = font_data
        c_margin.number_format = "0.0%"
        c_margin.alignment = align_right
        if margin < 0:
            c_margin.fill = fill_alert
            c_margin.font = Font(name=FONT_NAME, size=10, bold=True, color="922B21")

        c_disc = ws_dash.cell(row=row_idx, column=7, value=r["discount"])
        c_disc.font = font_data
        c_disc.number_format = "0.0%"
        c_disc.alignment = align_right

        for c_i in range(1, 8):
            ws_dash.cell(row=row_idx, column=c_i).border = border_all_thin

        row_idx += 1

    # Total Row for Category Table
    ws_dash.cell(row=row_idx, column=1, value="TOTAL").font = font_data_bold
    ws_dash.cell(row=row_idx, column=2, value="").font = font_data_bold
    ws_dash.cell(row=row_idx, column=3, value=f"=SUM(C11:C{row_idx-1})").font = font_data_bold
    ws_dash.cell(row=row_idx, column=3).number_format = "#,##0"
    ws_dash.cell(row=row_idx, column=4, value=f"=SUM(D11:D{row_idx-1})").font = font_data_bold
    ws_dash.cell(row=row_idx, column=4).number_format = "$#,##0.00"
    ws_dash.cell(row=row_idx, column=5, value=f"=SUM(E11:E{row_idx-1})").font = font_data_bold
    ws_dash.cell(row=row_idx, column=5).number_format = "$#,##0.00"
    ws_dash.cell(row=row_idx, column=6, value=f"=E{row_idx}/D{row_idx}").font = font_data_bold
    ws_dash.cell(row=row_idx, column=6).number_format = "0.0%"
    ws_dash.cell(row=row_idx, column=7, value=f"=AVERAGE(G11:G{row_idx-1})").font = font_data_bold
    ws_dash.cell(row=row_idx, column=7).number_format = "0.0%"
    for c_i in range(1, 8):
        ws_dash.cell(row=row_idx, column=c_i).border = border_bottom_double
        ws_dash.cell(row=row_idx, column=c_i).fill = fill_card

    # Section 2: Regional Performance Table (Columns I to K, Rows 10+)
    ws_dash["I9"] = "Regional Performance Summary"
    ws_dash["I9"].font = font_section_header

    reg_headers = ["Region", "Sales", "Profit", "Margin %"]
    for c_idx, h in enumerate(reg_headers, start=8):
        c = ws_dash.cell(row=10, column=c_idx, value=h)
        c.font = font_tbl_header
        c.fill = fill_navy_dark
        c.alignment = align_center
        c.border = border_all_thin

    reg_summary = df.groupby("region").agg(
        sales=("sales", "sum"),
        profit=("profit", "sum")
    ).reset_index().sort_values(by="profit", ascending=False)

    reg_row = 11
    for _, r in reg_summary.iterrows():
        margin = r["profit"] / r["sales"]
        ws_dash.cell(row=reg_row, column=8, value=r["region"]).font = font_data
        
        c_s = ws_dash.cell(row=reg_row, column=9, value=r["sales"])
        c_s.font = font_data
        c_s.number_format = "$#,##0.00"
        c_s.alignment = align_right

        c_p = ws_dash.cell(row=reg_row, column=10, value=r["profit"])
        c_p.font = font_data
        c_p.number_format = "$#,##0.00"
        c_p.alignment = align_right

        c_m = ws_dash.cell(row=reg_row, column=11, value=margin)
        c_m.font = font_data
        c_m.number_format = "0.0%"
        c_m.alignment = align_right

        for c_i in range(8, 12):
            ws_dash.cell(row=reg_row, column=c_i).border = border_all_thin
        reg_row += 1

    # Total Row for Region
    ws_dash.cell(row=reg_row, column=8, value="TOTAL").font = font_data_bold
    ws_dash.cell(row=reg_row, column=9, value=f"=SUM(I11:I{reg_row-1})").font = font_data_bold
    ws_dash.cell(row=reg_row, column=9).number_format = "$#,##0.00"
    ws_dash.cell(row=reg_row, column=10, value=f"=SUM(J11:J{reg_row-1})").font = font_data_bold
    ws_dash.cell(row=reg_row, column=10).number_format = "$#,##0.00"
    ws_dash.cell(row=reg_row, column=11, value=f"=J{reg_row}/I{reg_row}").font = font_data_bold
    ws_dash.cell(row=reg_row, column=11).number_format = "0.0%"
    for c_i in range(8, 12):
        ws_dash.cell(row=reg_row, column=c_i).border = border_bottom_double
        ws_dash.cell(row=reg_row, column=c_i).fill = fill_card

    # Section 3: Discount Sensitivity Cliff (Below Region Table)
    ws_dash["I18"] = "Discount Impact & Margin Cliff"
    ws_dash["I18"].font = font_section_header

    disc_headers = ["Discount Tier", "Transactions", "Total Sales", "Total Profit", "Margin %"]
    for c_idx, h in enumerate(disc_headers, start=8):
        c = ws_dash.cell(row=19, column=c_idx, value=h)
        c.font = font_tbl_header
        c.fill = fill_navy_dark
        c.alignment = align_center
        c.border = border_all_thin

    df["disc_tier"] = pd.cut(
        df["discount"],
        bins=[-0.01, 0.0, 0.20, 0.40, 0.60, 1.0],
        labels=["0% (No Discount)", "1% - 20% (Low)", "21% - 40% (Moderate)", "41% - 60% (High)", "> 60% (Extreme)"]
    )
    disc_summary = df.groupby("disc_tier", observed=False).agg(
        tx_count=("order_id", "count"),
        sales=("sales", "sum"),
        profit=("profit", "sum")
    ).reset_index()

    d_row = 20
    for _, r in disc_summary.iterrows():
        margin = r["profit"] / r["sales"] if r["sales"] > 0 else 0
        ws_dash.cell(row=d_row, column=8, value=str(r["disc_tier"])).font = font_data
        
        c_tx = ws_dash.cell(row=d_row, column=9, value=r["tx_count"])
        c_tx.font = font_data
        c_tx.number_format = "#,##0"
        c_tx.alignment = align_right

        c_s = ws_dash.cell(row=d_row, column=10, value=r["sales"])
        c_s.font = font_data
        c_s.number_format = "$#,##0.00"
        c_s.alignment = align_right

        c_p = ws_dash.cell(row=d_row, column=11, value=r["profit"])
        c_p.font = font_data
        c_p.number_format = "$#,##0.00"
        c_p.alignment = align_right
        if r["profit"] < 0:
            c_p.fill = fill_alert
            c_p.font = Font(name=FONT_NAME, size=10, bold=True, color="922B21")

        c_m = ws_dash.cell(row=d_row, column=12, value=margin)
        c_m.font = font_data
        c_m.number_format = "0.0%"
        c_m.alignment = align_right
        if margin < 0:
            c_m.fill = fill_alert
            c_m.font = Font(name=FONT_NAME, size=10, bold=True, color="922B21")

        for c_i in range(8, 13):
            ws_dash.cell(row=d_row, column=c_i).border = border_all_thin
        d_row += 1

    # Auto-adjust column widths for Executive Dashboard
    for col in ws_dash.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_dash.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # =========================================================================
    # TAB 2: MONTHLY TRENDS
    # =========================================================================
    ws_month = wb.create_sheet(title="Monthly_Trend")
    ws_month.views.sheetView[0].showGridLines = True

    ws_month.merge_cells("A1:G2")
    ws_month["A1"] = "MONTHLY SALES, PROFIT & GROWTH TRAJECTORY"
    ws_month["A1"].font = font_title
    ws_month["A1"].fill = fill_navy_dark
    ws_month["A1"].alignment = align_center

    m_headers = ["Year-Month", "Year", "Month", "Orders", "Gross Sales", "Net Profit", "Margin %"]
    for c_idx, h in enumerate(m_headers, start=1):
        c = ws_month.cell(row=4, column=c_idx, value=h)
        c.font = font_tbl_header
        c.fill = fill_navy_dark
        c.alignment = align_center
        c.border = border_all_thin

    df["ym"] = df["order_date"].dt.strftime("%Y-%m")
    df["year"] = df["order_date"].dt.year
    df["month"] = df["order_date"].dt.month

    monthly = df.groupby(["ym", "year", "month"]).agg(
        orders=("order_id", "nunique"),
        sales=("sales", "sum"),
        profit=("profit", "sum")
    ).reset_index().sort_values(by="ym")

    m_idx = 5
    for _, r in monthly.iterrows():
        ws_month.cell(row=m_idx, column=1, value=r["ym"]).font = font_data
        ws_month.cell(row=m_idx, column=2, value=r["year"]).font = font_data
        ws_month.cell(row=m_idx, column=3, value=r["month"]).font = font_data

        c_ord = ws_month.cell(row=m_idx, column=4, value=r["orders"])
        c_ord.font = font_data
        c_ord.number_format = "#,##0"
        c_ord.alignment = align_right

        c_s = ws_month.cell(row=m_idx, column=5, value=r["sales"])
        c_s.font = font_data
        c_s.number_format = "$#,##0.00"
        c_s.alignment = align_right

        c_p = ws_month.cell(row=m_idx, column=6, value=r["profit"])
        c_p.font = font_data
        c_p.number_format = "$#,##0.00"
        c_p.alignment = align_right

        c_m = ws_month.cell(row=m_idx, column=7, value=f"=F{m_idx}/E{m_idx}")
        c_m.font = font_data
        c_m.number_format = "0.0%"
        c_m.alignment = align_right

        for c_i in range(1, 8):
            ws_month.cell(row=m_idx, column=c_i).border = border_all_thin
        m_idx += 1

    # Total Row for Monthly Trends
    ws_month.cell(row=m_idx, column=1, value="TOTAL").font = font_data_bold
    ws_month.cell(row=m_idx, column=4, value=f"=SUM(D5:D{m_idx-1})").font = font_data_bold
    ws_month.cell(row=m_idx, column=4).number_format = "#,##0"
    ws_month.cell(row=m_idx, column=5, value=f"=SUM(E5:E{m_idx-1})").font = font_data_bold
    ws_month.cell(row=m_idx, column=5).number_format = "$#,##0.00"
    ws_month.cell(row=m_idx, column=6, value=f"=SUM(F5:F{m_idx-1})").font = font_data_bold
    ws_month.cell(row=m_idx, column=6).number_format = "$#,##0.00"
    ws_month.cell(row=m_idx, column=7, value=f"=F{m_idx}/E{m_idx}").font = font_data_bold
    ws_month.cell(row=m_idx, column=7).number_format = "0.0%"
    for c_i in range(1, 8):
        ws_month.cell(row=m_idx, column=c_i).border = border_bottom_double
        ws_month.cell(row=m_idx, column=c_i).fill = fill_card

    for col in ws_month.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_month.column_dimensions[col_letter].width = max(max_len + 3, 12)

    # =========================================================================
    # TAB 3: CATEGORY X REGION MATRIX
    # =========================================================================
    ws_pivot = wb.create_sheet(title="Category_Region_Matrix")
    ws_pivot.views.sheetView[0].showGridLines = True

    ws_pivot.merge_cells("A1:I2")
    ws_pivot["A1"] = "CATEGORY BY REGION SALES & PROFIT MATRIX"
    ws_pivot["A1"].font = font_title
    ws_pivot["A1"].fill = fill_navy_dark
    ws_pivot["A1"].alignment = align_center

    pivot_sales = df.pivot_table(index="category", columns="region", values="sales", aggfunc="sum")
    pivot_profit = df.pivot_table(index="category", columns="region", values="profit", aggfunc="sum")

    # Sales Table
    ws_pivot["A4"] = "Gross Sales by Category & Region"
    ws_pivot["A4"].font = font_section_header
    regions = sorted(df["region"].unique())
    p_headers = ["Category"] + regions + ["Total Sales"]
    for c_idx, h in enumerate(p_headers, start=1):
        c = ws_pivot.cell(row=5, column=c_idx, value=h)
        c.font = font_tbl_header
        c.fill = fill_navy_dark
        c.alignment = align_center
        c.border = border_all_thin

    p_r_idx = 6
    for cat in pivot_sales.index:
        ws_pivot.cell(row=p_r_idx, column=1, value=cat).font = font_data
        for c_idx, reg in enumerate(regions, start=2):
            val = pivot_sales.loc[cat, reg]
            c = ws_pivot.cell(row=p_r_idx, column=c_idx, value=val)
            c.font = font_data
            c.number_format = "$#,##0.00"
            c.alignment = align_right
            c.border = border_all_thin
        
        # Total Formula
        c_tot = ws_pivot.cell(row=p_r_idx, column=len(regions)+2, value=f"=SUM(B{p_r_idx}:{get_column_letter(len(regions)+1)}{p_r_idx})")
        c_tot.font = font_data_bold
        c_tot.number_format = "$#,##0.00"
        c_tot.alignment = align_right
        c_tot.border = border_all_thin
        p_r_idx += 1

    # Total Row for Sales Matrix
    ws_pivot.cell(row=p_r_idx, column=1, value="TOTAL").font = font_data_bold
    for c_idx in range(2, len(regions)+3):
        col_let = get_column_letter(c_idx)
        c_tot = ws_pivot.cell(row=p_r_idx, column=c_idx, value=f"=SUM({col_let}6:{col_let}{p_r_idx-1})")
        c_tot.font = font_data_bold
        c_tot.number_format = "$#,##0.00"
        c_tot.alignment = align_right
        c_tot.border = border_bottom_double
        c_tot.fill = fill_card
    ws_pivot.cell(row=p_r_idx, column=1).border = border_bottom_double
    ws_pivot.cell(row=p_r_idx, column=1).fill = fill_card

    # Profit Table
    p_r_idx += 3
    ws_pivot.cell(row=p_r_idx, column=1, value="Net Profit by Category & Region").font = font_section_header
    p_r_idx += 1
    p_headers_p = ["Category"] + regions + ["Total Profit"]
    for c_idx, h in enumerate(p_headers_p, start=1):
        c = ws_pivot.cell(row=p_r_idx, column=c_idx, value=h)
        c.font = font_tbl_header
        c.fill = fill_navy_dark
        c.alignment = align_center
        c.border = border_all_thin

    start_p_row = p_r_idx + 1
    p_r_idx += 1
    for cat in pivot_profit.index:
        ws_pivot.cell(row=p_r_idx, column=1, value=cat).font = font_data
        for c_idx, reg in enumerate(regions, start=2):
            val = pivot_profit.loc[cat, reg]
            c = ws_pivot.cell(row=p_r_idx, column=c_idx, value=val)
            c.font = font_data
            c.number_format = "$#,##0.00"
            c.alignment = align_right
            c.border = border_all_thin
            if val < 0:
                c.fill = fill_alert
                c.font = Font(name=FONT_NAME, size=10, bold=True, color="922B21")

        c_tot = ws_pivot.cell(row=p_r_idx, column=len(regions)+2, value=f"=SUM(B{p_r_idx}:{get_column_letter(len(regions)+1)}{p_r_idx})")
        c_tot.font = font_data_bold
        c_tot.number_format = "$#,##0.00"
        c_tot.alignment = align_right
        c_tot.border = border_all_thin
        p_r_idx += 1

    # Total Row for Profit Matrix
    ws_pivot.cell(row=p_r_idx, column=1, value="TOTAL").font = font_data_bold
    for c_idx in range(2, len(regions)+3):
        col_let = get_column_letter(c_idx)
        c_tot = ws_pivot.cell(row=p_r_idx, column=c_idx, value=f"=SUM({col_let}{start_p_row}:{col_let}{p_r_idx-1})")
        c_tot.font = font_data_bold
        c_tot.number_format = "$#,##0.00"
        c_tot.alignment = align_right
        c_tot.border = border_bottom_double
        c_tot.fill = fill_card
    ws_pivot.cell(row=p_r_idx, column=1).border = border_bottom_double
    ws_pivot.cell(row=p_r_idx, column=1).fill = fill_card

    for col in ws_pivot.columns:
        max_len = max(len(str(cell.value or '')) for cell in col)
        col_letter = get_column_letter(col[0].column)
        ws_pivot.column_dimensions[col_letter].width = max(max_len + 3, 14)

    # =========================================================================
    # TAB 4: RAW CLEANED DATA
    # =========================================================================
    ws_raw = wb.create_sheet(title="Raw_Cleaned_Data")
    ws_raw.views.sheetView[0].showGridLines = True

    # Headers
    raw_cols = [
        "row_id", "order_id", "order_date", "ship_date", "ship_mode",
        "customer_id", "customer_name", "segment", "country", "city",
        "state", "postal_code", "region", "product_id", "category",
        "sub_category", "product_name", "sales", "quantity", "discount", "profit"
    ]
    for c_idx, col_name in enumerate(raw_cols, start=1):
        c = ws_raw.cell(row=1, column=c_idx, value=col_name.replace("_", " ").title())
        c.font = font_tbl_header
        c.fill = fill_navy_dark
        c.alignment = align_center
        c.border = border_all_thin

    # Fill data
    data_vals = df[raw_cols].values.tolist()
    for r_idx, row_vals in enumerate(data_vals, start=2):
        for c_idx, val in enumerate(row_vals, start=1):
            c = ws_raw.cell(row=r_idx, column=c_idx, value=val)
            c.font = font_data
            
            # Formatting
            col_name = raw_cols[c_idx - 1]
            if col_name in ["order_date", "ship_date"]:
                c.number_format = "YYYY-MM-DD"
                c.alignment = align_center
            elif col_name in ["sales", "profit"]:
                c.number_format = "$#,##0.00"
                c.alignment = align_right
                if col_name == "profit" and val < 0:
                    c.fill = fill_alert
            elif col_name == "discount":
                c.number_format = "0.0%"
                c.alignment = align_right
            elif col_name == "quantity":
                c.number_format = "#,##0"
                c.alignment = align_right
            elif col_name in ["row_id", "postal_code"]:
                c.alignment = align_center
            else:
                c.alignment = align_left

            c.border = border_all_thin

    # Freeze header row and enable AutoFilter on Raw Data
    ws_raw.freeze_panes = "A2"
    ws_raw.auto_filter.ref = f"A1:{get_column_letter(len(raw_cols))}{len(data_vals) + 1}"

    for col in ws_raw.columns:
        col_letter = get_column_letter(col[0].column)
        # Cap max length check to top 50 rows for performance
        max_len = max(len(str(cell.value or '')) for cell in col[:50])
        ws_raw.column_dimensions[col_letter].width = min(max(max_len + 3, 10), 35)

    os.makedirs(os.path.dirname(output_xlsx), exist_ok=True)
    wb.save(output_xlsx)
    print(f"Successfully generated Excel workbook at: '{output_xlsx}'")

if __name__ == "__main__":
    in_csv = os.path.join("data", "processed", "superstore_cleaned.csv")
    out_xlsx = os.path.join("excel", "retail_sales_performance_dashboard.xlsx")
    if not os.path.exists(in_csv):
        in_csv = os.path.join("data", "raw", "sample_superstore.csv")
    create_dashboard_workbook(in_csv, out_xlsx)

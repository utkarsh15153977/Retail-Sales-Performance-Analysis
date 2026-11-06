#!/usr/bin/env python3
"""
Render Excel Dashboard Visual Assets for GitHub README
Generates high-resolution presentation screenshots of the Excel dashboard
and analytical charts into the assets/ folder.
"""

import os
import matplotlib.pyplot as plt
import matplotlib.patches as patches
import pandas as pd
import numpy as np

# Styling constants
COLOR_NAVY_DARK = "#1B365D"
COLOR_NAVY_LIGHT = "#2E5B88"
COLOR_ACCENT_BLUE = "#4A90E2"
COLOR_BG = "#F8F9FA"
COLOR_CARD_BG = "#FFFFFF"
COLOR_CARD_BORDER = "#D5D8DC"
COLOR_TEXT_DARK = "#1C2833"
COLOR_TEXT_MUTED = "#566573"
COLOR_ALERT_RED = "#D9534F"
COLOR_SUCCESS_GREEN = "#2E7D32"

plt.rcParams["font.family"] = "sans-serif"
plt.rcParams["font.sans-serif"] = ["Segoe UI", "DejaVu Sans", "Calibri", "Arial"]

def generate_executive_dashboard_screenshot(df: pd.DataFrame, output_path: str):
    """Renders the Executive Dashboard layout matching the Excel sheet."""
    fig = plt.figure(figsize=(16, 11), facecolor="#F0F4F8", dpi=200)
    
    # 1. Header Banner
    ax_head = fig.add_axes([0.04, 0.90, 0.92, 0.08])
    ax_head.axis("off")
    rect_head = patches.FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02,rounding_size=0.03", 
                                       facecolor=COLOR_NAVY_DARK, edgecolor="none", transform=ax_head.transAxes)
    ax_head.add_patch(rect_head)
    ax_head.text(0.5, 0.65, "RETAIL SALES PERFORMANCE - EXECUTIVE DASHBOARD", 
                 color="white", fontsize=18, fontweight="bold", ha="center", va="center", transform=ax_head.transAxes)
    ax_head.text(0.5, 0.25, "Dataset: Sample Superstore (2014 - 2017) | Core Business Metrics, Category Mix & Regional Margins", 
                 color="#D5D8DC", fontsize=11, ha="center", va="center", transform=ax_head.transAxes)

    # 2. KPI Scorecards (Row of 6 cards)
    total_sales = df["sales"].sum()
    total_profit = df["profit"].sum()
    margin_pct = (total_profit / total_sales) * 100
    total_orders = df["order_id"].nunique()
    total_customers = df["customer_id"].nunique()
    aov = total_sales / total_orders

    kpis = [
        ("TOTAL REVENUE", f"${total_sales:,.2f}", "#1B365D", "5,009 Orders"),
        ("TOTAL NET PROFIT", f"${total_profit:,.2f}", "#2E7D32", f"{margin_pct:.2f}% Blended Margin"),
        ("BLENDED MARGIN", f"{margin_pct:.2f}%", "#2E5B88", "Target: 15.0%"),
        ("DISTINCT ORDERS", f"{total_orders:,}", "#1B365D", "37,873 Units Sold"),
        ("ACTIVE CUSTOMERS", f"{total_customers:,}", "#1B365D", "6.3 Orders / Customer"),
        ("AVERAGE ORDER VALUE", f"${aov:,.2f}", "#1B365D", "$57.18 Profit / Order"),
    ]

    card_width = 0.138
    card_gap = 0.018
    start_x = 0.04
    card_y = 0.77
    card_height = 0.105

    for i, (title, val, val_color, sub) in enumerate(kpis):
        x = start_x + i * (card_width + card_gap)
        ax_card = fig.add_axes([x, card_y, card_width, card_height])
        ax_card.axis("off")
        box = patches.FancyBboxPatch((0, 0), 1, 1, boxstyle="round,pad=0.02,rounding_size=0.08", 
                                     facecolor="white", edgecolor="#D5D8DC", linewidth=1.2, transform=ax_card.transAxes)
        ax_card.add_patch(box)
        ax_card.text(0.5, 0.80, title, color="#566573", fontsize=8.5, fontweight="bold", ha="center", va="center", transform=ax_card.transAxes)
        ax_card.text(0.5, 0.48, val, color=val_color, fontsize=14, fontweight="bold", ha="center", va="center", transform=ax_card.transAxes)
        ax_card.text(0.5, 0.18, sub, color="#7F8C8D", fontsize=7.5, ha="center", va="center", transform=ax_card.transAxes)

    # 3. Left Panel: Category & Sub-Category Table
    ax_table = fig.add_axes([0.04, 0.05, 0.50, 0.68])
    ax_table.axis("off")
    ax_table.text(0.0, 0.98, "Category & Sub-Category Performance Summary", fontsize=12.5, fontweight="bold", color=COLOR_NAVY_DARK)

    cat_summary = df.groupby(["category", "sub_category"]).agg(
        units=("quantity", "sum"),
        sales=("sales", "sum"),
        profit=("profit", "sum"),
        discount=("discount", "mean")
    ).reset_index().sort_values(by=["category", "sales"], ascending=[True, False])

    table_data = []
    cell_colors = []
    headers = ["Category", "Sub-Category", "Units", "Total Sales", "Net Profit", "Margin %", "Avg Disc"]

    for _, r in cat_summary.iterrows():
        margin = (r["profit"] / r["sales"]) * 100 if r["sales"] > 0 else 0
        row_vals = [
            r["category"],
            r["sub_category"],
            f"{r['units']:,}",
            f"${r['sales']:,.0f}",
            f"${r['profit']:,.0f}",
            f"{margin:.1f}%",
            f"{r['discount']*100:.1f}%"
        ]
        table_data.append(row_vals)
        
        # Color formatting
        is_loss = r["profit"] < 0
        r_color = ["#FADBD8" if is_loss and col_idx in [4, 5] else ("#F8F9FA" if _ % 2 == 0 else "white") for col_idx in range(7)]
        cell_colors.append(r_color)

    # Add Total row
    tot_margin = (total_profit / total_sales) * 100
    table_data.append(["TOTAL", "", f"{df['quantity'].sum():,}", f"${total_sales:,.0f}", f"${total_profit:,.0f}", f"{tot_margin:.1f}%", f"{df['discount'].mean()*100:.1f}%"])
    cell_colors.append(["#EAEFF5"] * 7)

    tbl = ax_table.table(cellText=table_data, colLabels=headers, cellColours=cell_colors,
                         colColours=[COLOR_NAVY_DARK]*7, loc="center", cellLoc="right")
    tbl.auto_set_font_size(False)
    tbl.set_fontsize(8.5)
    tbl.scale(1.0, 1.42)

    # Left-align category and sub-category
    for row_idx in range(len(table_data) + 1):
        for col_idx in [0, 1]:
            tbl[(row_idx, col_idx)].get_text().set_horizontalalignment("left")
        # Header text style
        if row_idx == 0:
            for c_i in range(7):
                tbl[(0, c_i)].get_text().set_color("white")
                tbl[(0, c_i)].get_text().set_fontweight("bold")
                tbl[(0, c_i)].get_text().set_horizontalalignment("center")
        elif row_idx == len(table_data):
            for c_i in range(7):
                tbl[(row_idx, c_i)].get_text().set_fontweight("bold")

    # 4. Right Top Panel: Regional Performance Summary Table
    ax_reg = fig.add_axes([0.57, 0.42, 0.39, 0.31])
    ax_reg.axis("off")
    ax_reg.text(0.0, 0.98, "Regional Performance Summary", fontsize=12, fontweight="bold", color=COLOR_NAVY_DARK)

    reg_summary = df.groupby("region").agg(
        orders=("order_id", "nunique"),
        sales=("sales", "sum"),
        profit=("profit", "sum")
    ).reset_index().sort_values(by="profit", ascending=False)

    reg_headers = ["Region", "Orders", "Total Sales", "Net Profit", "Margin %", "Profit Share"]
    reg_rows = []
    reg_colors = []
    for _, r in reg_summary.iterrows():
        m = (r["profit"] / r["sales"]) * 100
        p_share = (r["profit"] / total_profit) * 100
        reg_rows.append([
            r["region"],
            f"{r['orders']:,}",
            f"${r['sales']:,.0f}",
            f"${r['profit']:,.0f}",
            f"{m:.1f}%",
            f"{p_share:.1f}%"
        ])
        reg_colors.append(["white"] * 6)

    reg_rows.append(["TOTAL", f"{total_orders:,}", f"${total_sales:,.0f}", f"${total_profit:,.0f}", f"{tot_margin:.1f}%", "100.0%"])
    reg_colors.append(["#EAEFF5"] * 6)

    tbl_reg = ax_reg.table(cellText=reg_rows, colLabels=reg_headers, cellColours=reg_colors,
                           colColours=[COLOR_NAVY_DARK]*6, loc="center", cellLoc="right")
    tbl_reg.auto_set_font_size(False)
    tbl_reg.set_fontsize(8.5)
    tbl_reg.scale(1.0, 1.5)
    for r_i in range(len(reg_rows) + 1):
        tbl_reg[(r_i, 0)].get_text().set_horizontalalignment("left")
        if r_i == 0:
            for c_i in range(6):
                tbl_reg[(0, c_i)].get_text().set_color("white")
                tbl_reg[(0, c_i)].get_text().set_fontweight("bold")
                tbl_reg[(0, c_i)].get_text().set_horizontalalignment("center")
        elif r_i == len(reg_rows):
            for c_i in range(6):
                tbl_reg[(r_i, c_i)].get_text().set_fontweight("bold")

    # 5. Right Bottom Panel: The Discount Cliff Table
    ax_disc = fig.add_axes([0.57, 0.05, 0.39, 0.31])
    ax_disc.axis("off")
    ax_disc.text(0.0, 0.98, "Discount Impact & Margin Cliff (Value Destruction)", fontsize=12, fontweight="bold", color=COLOR_NAVY_DARK)

    df["disc_tier"] = pd.cut(
        df["discount"],
        bins=[-0.01, 0.0, 0.20, 0.40, 0.60, 1.0],
        labels=["0% (None)", "1-20% (Low)", "21-40% (Moderate)", "41-60% (High)", ">60% (Extreme)"]
    )
    disc_summary = df.groupby("disc_tier", observed=False).agg(
        records=("row_id", "count"),
        sales=("sales", "sum"),
        profit=("profit", "sum")
    ).reset_index()

    disc_headers = ["Discount Tier", "Line Items", "Total Sales", "Net Profit", "Margin %", "Verdict"]
    disc_rows = []
    disc_colors = []
    for _, r in disc_summary.iterrows():
        m = (r["profit"] / r["sales"]) * 100 if r["sales"] > 0 else 0
        verdict = "Highly Profitable" if m > 20 else ("Sustainable" if m > 0 else ("Capital Burn" if m > -50 else "Catastrophic"))
        disc_rows.append([
            str(r["disc_tier"]),
            f"{r['records']:,}",
            f"${r['sales']:,.0f}",
            f"${r['profit']:,.0f}",
            f"{m:.1f}%",
            verdict
        ])
        is_loss = r["profit"] < 0
        disc_colors.append(["#FADBD8" if is_loss and c in [3, 4, 5] else "white" for c in range(6)])

    tbl_disc = ax_disc.table(cellText=disc_rows, colLabels=disc_headers, cellColours=disc_colors,
                             colColours=[COLOR_NAVY_DARK]*6, loc="center", cellLoc="right")
    tbl_disc.auto_set_font_size(False)
    tbl_disc.set_fontsize(8.5)
    tbl_disc.scale(1.0, 1.5)
    for r_i in range(len(disc_rows) + 1):
        tbl_disc[(r_i, 0)].get_text().set_horizontalalignment("left")
        tbl_disc[(r_i, 5)].get_text().set_horizontalalignment("center")
        if r_i == 0:
            for c_i in range(6):
                tbl_disc[(0, c_i)].get_text().set_color("white")
                tbl_disc[(0, c_i)].get_text().set_fontweight("bold")
                tbl_disc[(0, c_i)].get_text().set_horizontalalignment("center")

    os.makedirs(os.path.dirname(output_path), exist_ok=True)
    fig.savefig(output_path, bbox_inches="tight", facecolor=fig.get_facecolor(), edgecolor="none")
    plt.close(fig)
    print(f"Generated Executive Dashboard screenshot: {output_path}")


def generate_discount_cliff_chart(df: pd.DataFrame, output_path: str):
    """Renders the executive Discount Cliff analytical chart."""
    fig, ax1 = plt.subplots(figsize=(11, 6), facecolor="white", dpi=200)

    df_copy = df.copy()
    df_copy["disc_tier"] = pd.cut(
        df_copy["discount"],
        bins=[-0.01, 0.0, 0.20, 0.40, 0.60, 1.0],
        labels=["0% (None)", "1-20% (Low)", "21-40% (Moderate)", "41-60% (High)", ">60% (Extreme)"]
    )
    summary = df_copy.groupby("disc_tier", observed=False).agg(
        sales=("sales", "sum"),
        profit=("profit", "sum")
    ).reset_index()
    summary["margin_pct"] = (summary["profit"] / summary["sales"]) * 100

    tiers = summary["disc_tier"].astype(str)
    sales = summary["sales"] / 1000  # in Thousands
    margins = summary["margin_pct"]

    x = np.arange(len(tiers))
    width = 0.45

    # Bar chart for Sales Volume
    bars = ax1.bar(x, sales, width, color=COLOR_NAVY_LIGHT, alpha=0.85, label="Sales Volume ($K)")
    ax1.set_ylabel("Sales Revenue ($K)", color=COLOR_NAVY_DARK, fontsize=11, fontweight="bold")
    ax1.tick_params(axis="y", labelcolor=COLOR_NAVY_DARK)
    ax1.set_xticks(x)
    ax1.set_xticklabels(tiers, fontsize=10, fontweight="bold")
    ax1.set_ylim(0, 1300)

    # Line chart for Profit Margin %
    ax2 = ax1.twinx()
    line_color = "#D9534F"
    line = ax2.plot(x, margins, color=line_color, marker="o", linewidth=3.0, markersize=8, label="Net Profit Margin %")
    ax2.set_ylabel("Net Profit Margin (%)", color=line_color, fontsize=11, fontweight="bold")
    ax2.tick_params(axis="y", labelcolor=line_color)
    ax2.axhline(0, color="gray", linestyle="--", linewidth=1.2, alpha=0.7)
    ax2.set_ylim(-140, 45)

    # Annotate margin values
    for i, m in enumerate(margins):
        txt_color = COLOR_SUCCESS_GREEN if m > 0 else COLOR_ALERT_RED
        offset_y = 6 if m > 0 else -14
        ax2.annotate(f"{m:+.1f}%", (x[i], m), textcoords="offset points", xytext=(0, offset_y),
                     ha="center", fontsize=10, fontweight="bold", color=txt_color,
                     bbox=dict(boxstyle="round,pad=0.2", facecolor="white", edgecolor=txt_color, alpha=0.9))

    # Annotate sales bar values
    for b, s in zip(bars, sales):
        ax1.annotate(f"${s:,.0f}K", (b.get_x() + b.get_width()/2, b.get_height() + 15),
                     ha="center", fontsize=9, fontweight="bold", color=COLOR_NAVY_DARK)

    # Add Profitability Cliff threshold line
    ax1.axvline(1.5, color="#D9534F", linestyle=":", linewidth=2)
    ax1.text(1.55, 1100, "PROFITABILITY CLIFF\n(Discounts > 20% destroy profit)", 
             color="#D9534F", fontsize=10, fontweight="bold", bbox=dict(boxstyle="round,pad=0.3", facecolor="#FDEDEC", edgecolor="#D9534F"))

    plt.title("The Superstore 'Discount Cliff': Volume vs Profit Margin Elasticity", fontsize=14, fontweight="bold", color=COLOR_NAVY_DARK, pad=18)
    fig.tight_layout()

    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated Discount Cliff chart: {output_path}")


def generate_monthly_trend_chart(df: pd.DataFrame, output_path: str):
    """Renders the 48-month revenue and profit growth trend."""
    df_copy = df.copy()
    df_copy["ym"] = pd.to_datetime(df_copy["order_date"]).dt.to_period("M")
    monthly = df_copy.groupby("ym").agg(
        sales=("sales", "sum"),
        profit=("profit", "sum")
    ).reset_index()
    monthly["ym_str"] = monthly["ym"].astype(str)

    fig, ax = plt.subplots(figsize=(13, 5.5), facecolor="white", dpi=200)

    x = np.arange(len(monthly))
    ax.fill_between(x, monthly["sales"], color=COLOR_NAVY_LIGHT, alpha=0.25)
    ax.plot(x, monthly["sales"], color=COLOR_NAVY_DARK, linewidth=2.2, label="Monthly Revenue ($)")
    
    # Plot profit with positive/negative fill
    ax.plot(x, monthly["profit"], color=COLOR_SUCCESS_GREEN, linewidth=2.0, marker="o", markersize=4, label="Net Profit ($)")
    ax.axhline(0, color="gray", linestyle="--", linewidth=0.9)

    ax.set_ylabel("USD ($)", fontsize=11, fontweight="bold", color=COLOR_NAVY_DARK)
    ax.set_title("48-Month Sales & Profit Trajectory (2014 – 2017) with Q4 Holiday Spikes", fontsize=13, fontweight="bold", color=COLOR_NAVY_DARK, pad=12)

    # Highlight November/December spikes
    q4_indices = [i for i, ym in enumerate(monthly["ym"]) if ym.month in [11, 12]]
    for idx in q4_indices:
        ax.axvspan(idx - 0.4, idx + 0.4, color="#FEF9E7", alpha=0.6)

    # X-ticks every 3 months
    tick_step = 3
    ax.set_xticks(x[::tick_step])
    ax.set_xticklabels(monthly["ym_str"].iloc[::tick_step], rotation=45, ha="right", fontsize=9)
    ax.legend(loc="upper left", frameon=True)
    ax.grid(axis="y", linestyle=":", alpha=0.6)

    fig.tight_layout()
    fig.savefig(output_path, bbox_inches="tight")
    plt.close(fig)
    print(f"Generated Monthly Trend chart: {output_path}")


def main():
    cleaned_csv = os.path.join("data", "processed", "superstore_cleaned.csv")
    if not os.path.exists(cleaned_csv):
        cleaned_csv = os.path.join("data", "raw", "sample_superstore.csv")

    df = pd.read_csv(cleaned_csv)
    assets_dir = os.path.join("assets")
    os.makedirs(assets_dir, exist_ok=True)

    generate_executive_dashboard_screenshot(df, os.path.join(assets_dir, "excel_executive_dashboard.png"))
    generate_discount_cliff_chart(df, os.path.join(assets_dir, "discount_cliff_analysis.png"))
    generate_monthly_trend_chart(df, os.path.join(assets_dir, "monthly_sales_profit_trend.png"))
    print("All visual screenshot assets generated successfully.")


if __name__ == "__main__":
    main()

"""
Automated Test Suite: Retail Sales Performance Analysis
Tests data validation, pipeline cleansing logic, and analytical calculations.
"""

import os
import sys
import sqlite3
import pandas as pd
import pytest

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from python.data_loader import SuperstoreDataLoader, REQUIRED_CANONICAL_COLUMNS


@pytest.fixture
def sample_raw_data():
    """Generates a small in-memory DataFrame with known edge cases for unit testing."""
    return pd.DataFrame([
        {
            "Row ID": 1,
            "Order ID": "CA-2016-152156",
            "Order Date": "11/8/2016",
            "Ship Date": "11/11/2016",
            "Ship Mode": "Second Class",
            "Customer ID": "CG-12520",
            "Customer Name": "Claire Gute ",
            "Segment": "Consumer",
            "Country": "United States",
            "City": "Burlington",
            "State": "Vermont",
            "Postal Code": 5408,  # Truncated zip code
            "Region": "East",
            "Product ID": "FUR-BO-10001798",
            "Category": "Furniture",
            "Sub-Category": "Bookcases",
            "Product Name": "Bush Somerset Bookcase",
            "Sales": 261.96,
            "Quantity": 2,
            "Discount": 0.0,
            "Profit": 41.9136,
        },
        {
            "Row ID": 2,
            "Order ID": "CA-2016-152156",
            "Order Date": "11/8/2016",
            "Ship Date": "11/11/2016",
            "Ship Mode": "Second Class",
            "Customer ID": "CG-12520",
            "Customer Name": "Claire Gute",
            "Segment": "Consumer",
            "Country": "United States",
            "City": "Burlington",
            "State": "Vermont",
            "Postal Code": "05408",
            "Region": "East",
            "Product ID": "FUR-CH-10000454",
            "Category": "Furniture",
            "Sub-Category": "Chairs",
            "Product Name": "Hon Chair",
            "Sales": 731.94,
            "Quantity": 3,
            "Discount": 0.20,
            "Profit": 219.582,
        }
    ])


def test_column_normalization(sample_raw_data):
    """Verifies that diverse header strings are normalized into canonical snake_case."""
    loader = SuperstoreDataLoader(input_path="dummy.csv")
    normalized_df = loader.normalize_column_names(sample_raw_data)
    for col in REQUIRED_CANONICAL_COLUMNS:
        assert col in normalized_df.columns, f"Missing expected canonical column: {col}"


def test_postal_code_standardization(sample_raw_data):
    """Verifies that integer truncated zip codes (e.g. 5408) are left-padded to '05408'."""
    loader = SuperstoreDataLoader(input_path="dummy.csv")
    norm_df = loader.normalize_column_names(sample_raw_data)
    clean_df = loader.perform_data_cleansing_and_audit(norm_df)
    assert clean_df.loc[0, "postal_code"] == "05408"
    assert clean_df.loc[1, "postal_code"] == "05408"


def test_date_conversion(sample_raw_data):
    """Verifies that dates are converted to standard ISO YYYY-MM-DD strings."""
    loader = SuperstoreDataLoader(input_path="dummy.csv")
    norm_df = loader.normalize_column_names(sample_raw_data)
    clean_df = loader.perform_data_cleansing_and_audit(norm_df)
    assert clean_df.loc[0, "order_date"] == "2016-11-08"
    assert clean_df.loc[0, "ship_date"] == "2016-11-11"
    assert loader.audit.invalid_dates_count == 0
    assert loader.audit.anachronistic_ship_dates == 0


def test_processed_dataset_integrity():
    """Validates the full processed CSV dataset against known enterprise benchmarks."""
    processed_path = os.path.join("data", "processed", "superstore_cleaned.csv")
    assert os.path.exists(processed_path), f"Processed CSV not found at {processed_path}"

    df = pd.read_csv(processed_path)
    assert len(df) == 9994, f"Expected 9,994 rows, found {len(df)}"
    assert len(df.columns) == 21, f"Expected 21 columns, found {len(df.columns)}"

    # Check totals
    total_sales = round(float(df["sales"].sum()), 2)
    total_profit = round(float(df["profit"].sum()), 2)
    assert total_sales == 2297200.86, f"Expected sales $2,297,200.86, got {total_sales}"
    assert total_profit == 286397.02, f"Expected profit $286,397.02, got {total_profit}"

    # Check bounds
    assert (df["sales"] >= 0).all(), "Negative sales found in processed data"
    assert (df["quantity"] > 0).all(), "Zero or negative quantity found in processed data"
    assert ((df["discount"] >= 0.0) & (df["discount"] <= 1.0)).all(), "Invalid discount rates found"


def test_sqlite_database_queries():
    """Executes verification queries on the generated SQLite database."""
    db_path = os.path.join("data", "processed", "retail_sales.db")
    assert os.path.exists(db_path), f"SQLite database not found at {db_path}"

    conn = sqlite3.connect(db_path)
    try:
        cur = conn.cursor()
        
        # Test 1: Row count
        count = cur.execute("SELECT COUNT(*) FROM retail_sales;").fetchone()[0]
        assert count == 9994

        # Test 2: Distinct orders & customers
        orders = cur.execute("SELECT COUNT(DISTINCT order_id) FROM retail_sales;").fetchone()[0]
        customers = cur.execute("SELECT COUNT(DISTINCT customer_id) FROM retail_sales;").fetchone()[0]
        assert orders == 5009
        assert customers == 793

        # Test 3: Profit margin check
        margin = cur.execute("SELECT ROUND((SUM(profit)/SUM(sales))*100, 2) FROM retail_sales;").fetchone()[0]
        assert margin == 12.47

    finally:
        conn.close()

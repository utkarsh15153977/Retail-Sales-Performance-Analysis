#!/usr/bin/env python3
"""
Portfolio Project: Retail Sales Performance Analysis
Script: python/data_loader.py
Purpose: Production-grade ingestion, validation, cleansing, and loading pipeline
         for Sample Superstore retail sales data into PostgreSQL / SQLite.
Author: Senior Data Analyst & SQL Developer
"""

import argparse
import logging
import os
import re
import sys
import time
from dataclasses import dataclass, field
from datetime import datetime
from typing import Any, Dict, List, Optional, Tuple

import pandas as pd

# Attempt optional database driver imports
try:
    import psycopg2
    from psycopg2 import extras
    PSYCOPG2_AVAILABLE = True
except ImportError:
    PSYCOPG2_AVAILABLE = False

try:
    import sqlite3
    SQLITE_AVAILABLE = True
except ImportError:
    SQLITE_AVAILABLE = False

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s",
    handlers=[
        logging.StreamHandler(sys.stdout),
    ],
)
logger = logging.getLogger("retail_data_loader")

# Canonical column definitions
EXPECTED_COLUMNS_MAP = {
    "row id": "row_id",
    "order id": "order_id",
    "order date": "order_date",
    "ship date": "ship_date",
    "ship mode": "ship_mode",
    "customer id": "customer_id",
    "customer name": "customer_name",
    "segment": "segment",
    "country": "country",
    "city": "city",
    "state": "state",
    "postal code": "postal_code",
    "region": "region",
    "product id": "product_id",
    "category": "category",
    "sub-category": "sub_category",
    "sub category": "sub_category",
    "product name": "product_name",
    "sales": "sales",
    "quantity": "quantity",
    "discount": "discount",
    "profit": "profit",
}

REQUIRED_CANONICAL_COLUMNS = [
    "row_id", "order_id", "order_date", "ship_date", "ship_mode",
    "customer_id", "customer_name", "segment", "country", "city",
    "state", "postal_code", "region", "product_id", "category",
    "sub_category", "product_name", "sales", "quantity", "discount", "profit"
]


@dataclass
class AuditReport:
    """Stores metrics and audit findings during the data ingestion pipeline."""
    total_raw_rows: int = 0
    valid_rows_count: int = 0
    flagged_rows_count: int = 0
    duplicate_row_ids: int = 0
    exact_duplicate_rows: int = 0
    duplicate_order_product_pairs: int = 0
    invalid_dates_count: int = 0
    negative_sales_count: int = 0
    invalid_quantity_count: int = 0
    invalid_discount_count: int = 0
    anachronistic_ship_dates: int = 0
    standardized_postal_codes_count: int = 0
    min_order_date: Optional[str] = None
    max_order_date: Optional[str] = None
    total_sales_volume: float = 0.0
    total_profit_volume: float = 0.0
    execution_time_seconds: float = 0.0
    loaded_into_database: bool = False
    database_type: Optional[str] = None
    records_loaded: int = 0


class SuperstoreDataLoader:
    """Enterprise ETL class for retail sales transaction data."""

    def __init__(self, input_path: str, output_cleaned_path: Optional[str] = None):
        self.input_path = input_path
        self.output_cleaned_path = output_cleaned_path
        self.raw_df: Optional[pd.DataFrame] = None
        self.clean_df: Optional[pd.DataFrame] = None
        self.audit = AuditReport()

    def read_csv_with_fallback_encodings(self) -> pd.DataFrame:
        """Reads CSV file trying standard encodings (utf-8, latin1, cp1252)."""
        encodings_to_try = ["utf-8", "latin1", "cp1252", "iso-8859-1"]
        for enc in encodings_to_try:
            try:
                logger.info(f"Attempting to read '{self.input_path}' with encoding '{enc}'...")
                df = pd.read_csv(self.input_path, encoding=enc)
                logger.info(f"Successfully loaded {len(df):,} records using '{enc}' encoding.")
                return df
            except UnicodeDecodeError:
                continue
            except Exception as e:
                logger.error(f"Failed to read CSV with {enc}: {e}")
                raise

        raise ValueError(f"Unable to decode file '{self.input_path}' using supported encodings.")

    def normalize_column_names(self, df: pd.DataFrame) -> pd.DataFrame:
        """Maps diverse header conventions into standard snake_case canonical names."""
        normalized_cols = {}
        for col in df.columns:
            clean_name = col.strip().lower()
            if clean_name in EXPECTED_COLUMNS_MAP:
                normalized_cols[col] = EXPECTED_COLUMNS_MAP[clean_name]
            else:
                # Fallback: replace spaces and hyphens with underscores
                normalized_cols[col] = re.sub(r"[ -]+", "_", clean_name)

        df = df.rename(columns=normalized_cols)
        
        # Verify required columns exist
        missing_cols = [c for c in REQUIRED_CANONICAL_COLUMNS if c not in df.columns]
        if missing_cols:
            raise KeyError(f"Input file is missing mandatory columns: {missing_cols}")

        return df

    def perform_data_cleansing_and_audit(self, df: pd.DataFrame) -> pd.DataFrame:
        """Executes validations, format conversions, and integrity checks."""
        start_time = time.time()
        self.audit.total_raw_rows = len(df)

        # 1. Audit Primary Key and Row Duplicates
        self.audit.duplicate_row_ids = int(df["row_id"].duplicated().sum())
        
        # Check exact duplicates across all columns except row_id
        non_id_cols = [c for c in df.columns if c != "row_id"]
        exact_dups = df.duplicated(subset=non_id_cols, keep=False)
        self.audit.exact_duplicate_rows = int(df.duplicated(subset=non_id_cols).sum())
        if self.audit.exact_duplicate_rows > 0:
            logger.warning(
                f"Detected {self.audit.exact_duplicate_rows} exact duplicate transaction lines "
                f"(e.g. matching Order ID, Customer, and Product). Preserved for financial audit."
            )

        # Check duplicate (order_id, product_id)
        order_prod_dups = df.duplicated(subset=["order_id", "product_id"]).sum()
        self.audit.duplicate_order_product_pairs = int(order_prod_dups)

        # 2. String Cleansing: Trim whitespace
        string_columns = [
            "order_id", "ship_mode", "customer_id", "customer_name", "segment",
            "country", "city", "state", "region", "product_id", "category",
            "sub_category", "product_name"
        ]
        for col in string_columns:
            if col in df.columns:
                df[col] = df[col].astype(str).str.strip()

        # 3. Postal Code Standardization
        # Postal codes must be strings to preserve leading zeroes (e.g. Vermont '05408')
        def clean_postal_code(val: Any) -> Optional[str]:
            if pd.isna(val) or str(val).strip().lower() in ["nan", "none", "", "null"]:
                return None
            val_str = str(val).split(".")[0].strip()
            if val_str.isdigit():
                return val_str.zfill(5)
            return val_str

        raw_postals = df["postal_code"].copy()
        df["postal_code"] = df["postal_code"].apply(clean_postal_code)
        
        # Count standardized leading zeroes
        changed_count = sum(
            1 for orig, cleaned in zip(raw_postals, df["postal_code"]) 
            if cleaned is not None and len(str(orig).split(".")[0].strip()) < 5
        )
        self.audit.standardized_postal_codes_count = changed_count

        # 4. Safe Date Parsing & Temporal Validation
        try:
            df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")
            df["ship_date"] = pd.to_datetime(df["ship_date"], errors="coerce")
        except Exception as e:
            logger.error(f"Date conversion error: {e}")
            raise

        self.audit.invalid_dates_count = int(df["order_date"].isna().sum() + df["ship_date"].isna().sum())
        if self.audit.invalid_dates_count > 0:
            logger.error(f"Found {self.audit.invalid_dates_count} unparseable dates!")

        # Check chronological consistency (ship_date >= order_date)
        anachronistic = df["ship_date"] < df["order_date"]
        self.audit.anachronistic_ship_dates = int(anachronistic.sum())
        if self.audit.anachronistic_ship_dates > 0:
            logger.warning(f"Found {self.audit.anachronistic_ship_dates} records where ship_date < order_date.")

        # 5. Measure Casting & Boundary Checks
        df["sales"] = pd.to_numeric(df["sales"], errors="coerce")
        df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype(int)
        df["discount"] = pd.to_numeric(df["discount"], errors="coerce")
        df["profit"] = pd.to_numeric(df["profit"], errors="coerce")

        self.audit.negative_sales_count = int((df["sales"] < 0).sum())
        self.audit.invalid_quantity_count = int((df["quantity"] <= 0).sum())
        self.audit.invalid_discount_count = int(((df["discount"] < 0.0) | (df["discount"] > 1.0)).sum())

        # Calculate high-level summary metrics
        self.audit.min_order_date = df["order_date"].min().strftime("%Y-%m-%d")
        self.audit.max_order_date = df["order_date"].max().strftime("%Y-%m-%d")
        self.audit.total_sales_volume = round(float(df["sales"].sum()), 2)
        self.audit.total_profit_volume = round(float(df["profit"].sum()), 2)

        # Convert dates to ISO-8601 strings for SQL and CSV export
        df["order_date"] = df["order_date"].dt.strftime("%Y-%m-%d")
        df["ship_date"] = df["ship_date"].dt.strftime("%Y-%m-%d")

        # Determine valid vs flagged count
        # In this dataset, records are verified without silent deletions
        self.audit.valid_rows_count = len(df)
        self.audit.execution_time_seconds = round(time.time() - start_time, 3)

        return df

    def export_processed_csv(self, df: pd.DataFrame, path: str) -> None:
        """Saves cleansed data to CSV with UTF-8 encoding."""
        os.makedirs(os.path.dirname(path), exist_ok=True)
        df.to_csv(path, index=False, encoding="utf-8")
        logger.info(f"Cleaned dataset written to '{path}' ({len(df):,} records).")

    def load_to_sqlite(self, df: pd.DataFrame, db_path: str) -> None:
        """Loads data into a local SQLite database for verification and offline query execution."""
        os.makedirs(os.path.dirname(db_path), exist_ok=True)
        conn = sqlite3.connect(db_path)
        try:
            logger.info(f"Populating local SQLite database at '{db_path}'...")
            # Create table if not exists with clean schema
            df.to_sql("retail_sales", conn, if_exists="replace", index=False)
            
            # Create indexes for fast query performance
            cur = conn.cursor()
            cur.execute("CREATE INDEX IF NOT EXISTS idx_order_id ON retail_sales (order_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_order_date ON retail_sales (order_date);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_customer_id ON retail_sales (customer_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_product_id ON retail_sales (product_id);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_category ON retail_sales (category, sub_category);")
            cur.execute("CREATE INDEX IF NOT EXISTS idx_region ON retail_sales (region, state);")
            conn.commit()
            
            count = cur.execute("SELECT COUNT(*) FROM retail_sales;").fetchone()[0]
            logger.info(f"Successfully loaded {count:,} records into SQLite 'retail_sales' table.")
            self.audit.database_type = "SQLite"
            self.audit.records_loaded = count
            self.audit.loaded_into_database = True
        finally:
            conn.close()

    def load_to_postgresql(
        self,
        df: pd.DataFrame,
        host: str = "localhost",
        port: int = 5432,
        dbname: str = "retail_sales_db",
        user: str = "postgres",
        password: Optional[str] = None,
        db_url: Optional[str] = None,
        batch_size: int = 1000
    ) -> None:
        """
        Loads records into PostgreSQL core.retail_sales using idempotent upsert
        (ON CONFLICT (row_id) DO UPDATE) to prevent duplicate insertion.
        """
        if not PSYCOPG2_AVAILABLE:
            raise ImportError("psycopg2 is required for PostgreSQL ingestion. Install via pip install psycopg2-binary.")

        logger.info("Connecting to PostgreSQL...")
        if db_url:
            conn = psycopg2.connect(db_url)
        else:
            conn = psycopg2.connect(
                host=host,
                port=port,
                dbname=dbname,
                user=user,
                password=password
            )

        try:
            conn.autocommit = False
            cur = conn.cursor()

            # Ensure schema and table exist
            cur.execute("CREATE SCHEMA IF NOT EXISTS core;")
            
            # Prepare records tuple
            cols = [
                "row_id", "order_id", "order_date", "ship_date", "ship_mode",
                "customer_id", "customer_name", "segment", "country", "city",
                "state", "postal_code", "region", "product_id", "category",
                "sub_category", "product_name", "sales", "quantity", "discount", "profit"
            ]
            records = [tuple(x) for x in df[cols].to_numpy()]

            upsert_query = f"""
                INSERT INTO core.retail_sales ({', '.join(cols)})
                VALUES %s
                ON CONFLICT (row_id) DO UPDATE SET
                    order_id = EXCLUDED.order_id,
                    order_date = EXCLUDED.order_date,
                    ship_date = EXCLUDED.ship_date,
                    ship_mode = EXCLUDED.ship_mode,
                    customer_id = EXCLUDED.customer_id,
                    customer_name = EXCLUDED.customer_name,
                    segment = EXCLUDED.segment,
                    country = EXCLUDED.country,
                    city = EXCLUDED.city,
                    state = EXCLUDED.state,
                    postal_code = EXCLUDED.postal_code,
                    region = EXCLUDED.region,
                    product_id = EXCLUDED.product_id,
                    category = EXCLUDED.category,
                    sub_category = EXCLUDED.sub_category,
                    product_name = EXCLUDED.product_name,
                    sales = EXCLUDED.sales,
                    quantity = EXCLUDED.quantity,
                    discount = EXCLUDED.discount,
                    profit = EXCLUDED.profit;
            """

            logger.info(f"Executing batch upsert of {len(records):,} records (batch size: {batch_size})...")
            extras.execute_values(cur, upsert_query, records, page_size=batch_size)
            conn.commit()

            cur.execute("SELECT COUNT(*) FROM core.retail_sales;")
            total_in_db = cur.fetchone()[0]
            logger.info(f"PostgreSQL upsert complete. Total rows in core.retail_sales: {total_in_db:,}")

            self.audit.database_type = "PostgreSQL"
            self.audit.records_loaded = total_in_db
            self.audit.loaded_into_database = True

        except Exception as e:
            conn.rollback()
            logger.error(f"PostgreSQL load failed, rolled back: {e}")
            raise
        finally:
            conn.close()

    def print_audit_summary(self) -> None:
        """Prints a structured summary of the data quality audit to stdout."""
        a = self.audit
        print("\n" + "=" * 70)
        print("          RETAIL SALES PIPELINE INGESTION & AUDIT REPORT          ")
        print("=" * 70)
        print(f"Total Raw Records Read:             {a.total_raw_rows:,}")
        print(f"Cleaned Valid Records:              {a.valid_rows_count:,}")
        print(f"Execution Processing Time:          {a.execution_time_seconds:.3f} seconds")
        print("-" * 70)
        print("INTEGRITY & DATA QUALITY AUDIT:")
        print(f"  - Duplicate Row IDs:              {a.duplicate_row_ids}")
        print(f"  - Exact Duplicate Rows (non-id):   {a.exact_duplicate_rows} (preserved with provenance)")
        print(f"  - Duplicate (Order, Product) Pairs:{a.duplicate_order_product_pairs}")
        print(f"  - Invalid / Unparseable Dates:    {a.invalid_dates_count}")
        print(f"  - Anachronistic (Ship < Order):   {a.anachronistic_ship_dates}")
        print(f"  - Negative Sales Count:           {a.negative_sales_count}")
        print(f"  - Non-positive Quantity Count:    {a.invalid_quantity_count}")
        print(f"  - Invalid Discount Range (<0 or >1):{a.invalid_discount_count}")
        print(f"  - Postal Codes Standardized:      {a.standardized_postal_codes_count} (e.g. VT 5408 -> 05408)")
        print("-" * 70)
        print("BUSINESS MEASURE TOTALS:")
        print(f"  - Order Date Span:                {a.min_order_date} to {a.max_order_date}")
        print(f"  - Total Gross Sales:              ${a.total_sales_volume:,.2f}")
        print(f"  - Total Net Profit:               ${a.total_profit_volume:,.2f}")
        print(f"  - Overall Profit Margin:          {(a.total_profit_volume / a.total_sales_volume * 100):.2f}%")
        print("-" * 70)
        if a.loaded_into_database:
            print(f"DATABASE LOAD STATUS:               SUCCESS ({a.database_type})")
            print(f"  - Total Records In Database:      {a.records_loaded:,}")
        else:
            print("DATABASE LOAD STATUS:               SKIPPED / DRY-RUN")
        print("=" * 70 + "\n")


def parse_arguments() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Sample Superstore Data Loader & Quality Auditor")
    parser.add_argument(
        "--input",
        type=str,
        default=os.path.join("data", "raw", "sample_superstore.csv"),
        help="Path to input raw CSV file (default: data/raw/sample_superstore.csv)"
    )
    parser.add_argument(
        "--output-cleaned",
        type=str,
        default=os.path.join("data", "processed", "superstore_cleaned.csv"),
        help="Path to output processed CSV file (default: data/processed/superstore_cleaned.csv)"
    )
    parser.add_argument(
        "--sqlite-path",
        type=str,
        default=os.path.join("data", "processed", "retail_sales.db"),
        help="Path to SQLite verification database (default: data/processed/retail_sales.db)"
    )
    parser.add_argument(
        "--load-postgres",
        action="store_true",
        help="Flag to trigger PostgreSQL ingestion"
    )
    parser.add_argument(
        "--db-url",
        type=str,
        default=os.getenv("DATABASE_URL"),
        help="PostgreSQL connection string URL (or env DATABASE_URL)"
    )
    parser.add_argument("--pg-host", type=str, default=os.getenv("PGHOST", "localhost"))
    parser.add_argument("--pg-port", type=int, default=int(os.getenv("PGPORT", "5432")))
    parser.add_argument("--pg-dbname", type=str, default=os.getenv("PGDATABASE", "retail_sales_db"))
    parser.add_argument("--pg-user", type=str, default=os.getenv("PGUSER", "postgres"))
    parser.add_argument("--pg-password", type=str, default=os.getenv("PGPASSWORD", None))
    parser.add_argument("--batch-size", type=int, default=1000)
    parser.add_argument(
        "--dry-run",
        action="store_true",
        help="Perform validation, audit, and clean CSV export without database writes"
    )
    return parser.parse_args()


def main() -> None:
    args = parse_arguments()

    if not os.path.exists(args.input):
        logger.error(f"Input file not found: {args.input}")
        logger.info("Please download the Sample Superstore CSV into data/raw/ or specify --input.")
        sys.exit(1)

    loader = SuperstoreDataLoader(
        input_path=args.input,
        output_cleaned_path=args.output_cleaned
    )

    # 1. Ingest
    raw_df = loader.read_csv_with_fallback_encodings()

    # 2. Normalize columns
    normalized_df = loader.normalize_column_names(raw_df)

    # 3. Clean and audit
    clean_df = loader.perform_data_cleansing_and_audit(normalized_df)

    # 4. Export cleaned CSV
    if args.output_cleaned:
        loader.export_processed_csv(clean_df, args.output_cleaned)

    # 5. Populate SQLite for local zero-dependency verification
    if not args.dry_run and args.sqlite_path:
        loader.load_to_sqlite(clean_df, args.sqlite_path)

    # 6. Populate PostgreSQL if requested
    if args.load_postgres and not args.dry_run:
        loader.load_to_postgresql(
            df=clean_df,
            host=args.pg_host,
            port=args.pg_port,
            dbname=args.pg_dbname,
            user=args.pg_user,
            password=args.pg_password,
            db_url=args.db_url,
            batch_size=args.batch_size
        )

    # 7. Print summary
    loader.print_audit_summary()


if __name__ == "__main__":
    main()

"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 7
 Topic : Mini ETL Project — pandas + psycopg2 + PostgreSQL
 Date  : 2026-07-19
=============================================================

 Pipeline:
   extract()  → read raw CSV (200 rows)
   validate() → split valid (127) / invalid (73)
   transform()→ clean text, parse dates, compute total_price, add loaded_at
   load_sales_clean()    → bulk insert valid rows → sales_clean
   load_sales_rejected() → bulk insert invalid rows → sales_rejected
   aggregate queries     → revenue by category, region, top 5 customers
   result dict           → pipeline summary

 Connection details (local PostgreSQL 17):
   host     = localhost
   port     = 5432
   dbname   = postgres
   user     = postgres
   password = root
=============================================================
"""

import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from datetime import datetime

DB = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "postgres",
    "user":     "postgres",
    "password": "root",
}

filepath = "day7/sales.csv"

def log(step, message, rows=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_info = f"{rows}" if rows is not None else ""
    print(f"[{ts}] [{step}] {message}{row_info}")


# ══════════════════════════════════════════════════════════
#  TABLE DEFINITIONS
# ══════════════════════════════════════════════════════════

def sales_clean_definition():
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales_clean (
            order_id         INTEGER PRIMARY KEY,
            customer         VARCHAR(100),
            region           VARCHAR(100),
            product_category VARCHAR(100),
            product_name     VARCHAR(100),
            quantity         INTEGER,
            unit_price       NUMERIC(10,2),
            order_date       DATE,
            total_price      NUMERIC(10,2),
            loaded_at        TIMESTAMP
        )
    """)
    conn.commit()
    log("DEFINE", "Table 'sales_clean' defined")
    cur.close()
    conn.close()

def sales_reject_definition():
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS sales_rejected (
            order_id         INTEGER PRIMARY KEY,
            customer         VARCHAR(100),
            region           VARCHAR(100),
            product_category VARCHAR(100),
            product_name     VARCHAR(100),
            quantity         INTEGER,
            unit_price       NUMERIC(10,2),
            order_date       DATE
        )
    """)
    conn.commit()
    log("DEFINE", "Table 'sales_rejected' defined")
    cur.close()
    conn.close()


# ══════════════════════════════════════════════════════════
#  EXTRACT
# ══════════════════════════════════════════════════════════

def extract(filepath):
    df = pd.read_csv(filepath)
    log("EXTRACT", "Read sales data from csv | Rows extracted: ", len(df))
    return df


# ══════════════════════════════════════════════════════════
#  VALIDATE
# ══════════════════════════════════════════════════════════

def validate(df):
    mask_valid = (
        df["customer"].notna() &
        df["quantity"].notna() & (df["quantity"] > 0) &
        df["unit_price"].notna() & (df["unit_price"] > 0)
    )
    df_valid   = df[mask_valid].copy()
    df_invalid = df[~mask_valid].copy()
    df_invalid["reject_reason"] = "null or invalid sales data (customer/quantity/unit_price)"
    log("VALIDATE", "Validated sales data | Valid Rows: ", len(df_valid))
    log("VALIDATE", "Found invalid sales data | Invalid Rows: ", len(df_invalid))
    return df_valid, df_invalid


# ══════════════════════════════════════════════════════════
#  TRANSFORM
# ══════════════════════════════════════════════════════════

def transform(df):
    df_transformed = df.copy()
    df_transformed["customer"]         = df_transformed["customer"].str.strip().str.lower()
    df_transformed["region"]           = df_transformed["region"].str.strip().str.lower()
    df_transformed["product_category"] = df_transformed["product_category"].str.strip().str.lower()
    df_transformed["product_name"]     = df_transformed["product_name"].str.strip().str.lower()
    df_transformed["order_date"]       = pd.to_datetime(df_transformed["order_date"], errors="coerce")
    df_transformed["total_price"]      = df_transformed["quantity"] * df_transformed["unit_price"]
    df_transformed["loaded_at"]        = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log("TRANSFORM", "Transformed sales data | Rows transformed: ", len(df_transformed))
    return df_transformed


# ══════════════════════════════════════════════════════════
#  LOAD — VALID ROWS
# ══════════════════════════════════════════════════════════

def load_sales_clean(df):
    sales_clean_definition()
    cols = [
        "order_id", "customer", "region", "product_category", "product_name",
        "quantity", "unit_price", "order_date", "total_price", "loaded_at"
    ]
    sales_tuple = [tuple(row) for row in df[cols].itertuples(index=False)]
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()
    execute_values(
        cur,
        "INSERT INTO sales_clean (order_id, customer, region, product_category, product_name, quantity, unit_price, order_date, total_price, loaded_at) VALUES %s ON CONFLICT (order_id) DO NOTHING",
        sales_tuple
    )
    conn.commit()
    log("INSERT", "Validated data loaded into 'sales_clean' table  |  Rows Inserted: ", len(df))
    cur.close()
    conn.close()


# ══════════════════════════════════════════════════════════
#  LOAD — INVALID ROWS
# ══════════════════════════════════════════════════════════

def load_sales_rejected(df):
    sales_reject_definition()
    cols = [
        "order_id", "customer", "region", "product_category", "product_name",
        "quantity", "unit_price", "order_date"
    ]
    # astype(object) keeps None as Python None through itertuples (float64 converts it back to NaN)
    df_clean    = df[cols].astype(object).where(pd.notna(df[cols]), other=None)
    sales_tuple = [tuple(row) for row in df_clean.itertuples(index=False)]
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()
    execute_values(
        cur,
        "INSERT INTO sales_rejected (order_id, customer, region, product_category, product_name, quantity, unit_price, order_date) VALUES %s ON CONFLICT (order_id) DO NOTHING",
        sales_tuple
    )
    conn.commit()
    log("INSERT", "Rejected data loaded into 'sales_rejected' table  |  Rows Inserted: ", len(df_clean))
    cur.close()
    conn.close()


# ══════════════════════════════════════════════════════════
#  REPORTING QUERIES
# ══════════════════════════════════════════════════════════

def aggregate_sales_by_product():
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()
    log("AGGREGATE", "Aggregated sales by product_category")
    cur.execute("""
        SELECT product_category, COUNT(*) AS orders,
               SUM(total_price) AS total_revenue,
               ROUND(AVG(total_price), 2) AS avg_order_value
        FROM sales_clean
        GROUP BY product_category
        ORDER BY total_revenue DESC
    """)
    for row in cur.fetchall():
        print(row)
    cur.close()
    conn.close()

def aggregate_sales_by_region():
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()
    log("AGGREGATE", "Aggregated sales by region")
    cur.execute("""
        SELECT region, COUNT(*) AS orders, SUM(total_price) AS total_revenue
        FROM sales_clean
        GROUP BY region
        ORDER BY total_revenue DESC
    """)
    for row in cur.fetchall():
        print(row)
    cur.close()
    conn.close()

def aggregate_sales_by_top_5_cust():
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()
    log("AGGREGATE", "Aggregated sales by Top 5 Customers")
    cur.execute("""
        SELECT customer, COUNT(*) AS orders, SUM(total_price) AS total_spend
        FROM sales_clean
        GROUP BY customer
        ORDER BY total_spend DESC
        LIMIT 5
    """)
    for row in cur.fetchall():
        print(row)
    cur.close()
    conn.close()


# ══════════════════════════════════════════════════════════
#  MAIN PIPELINE
# ══════════════════════════════════════════════════════════

def main_pipeline_run():
    raw_data = extract(filepath)

    valid_sales, invalid_sales = validate(raw_data)

    transformed_sales = transform(valid_sales)

    load_sales_clean(transformed_sales)
    load_sales_rejected(invalid_sales)

    aggregate_sales_by_product()
    aggregate_sales_by_region()
    aggregate_sales_by_top_5_cust()

    return {
        "status":         "success",
        "rows_extracted":  len(raw_data),
        "rows_valid":      len(valid_sales),
        "rows_rejected":   len(invalid_sales),
        "rows_loaded":     len(transformed_sales),
        "errors":          [],
    }

print(main_pipeline_run())


# ══════════════════════════════════════════════════════════
#  OUTPUT (VERIFIED — 2026-07-19)
# ══════════════════════════════════════════════════════════
"""
[2026-07-19 04:34:32] [EXTRACT]   Read sales data from csv | Rows extracted: 200
[2026-07-19 04:34:32] [VALIDATE]  Validated sales data | Valid Rows: 127
[2026-07-19 04:34:32] [VALIDATE]  Found invalid sales data | Invalid Rows: 73
[2026-07-19 04:34:32] [TRANSFORM] Transformed sales data | Rows transformed: 127
[2026-07-19 04:34:32] [DEFINE]    Table 'sales_clean' defined
[2026-07-19 04:34:32] [INSERT]    Validated data loaded into 'sales_clean' table  |  Rows Inserted: 127
[2026-07-19 04:34:32] [DEFINE]    Table 'sales_rejected' defined
[2026-07-19 04:34:32] [INSERT]    Rejected data loaded into 'sales_rejected' table  |  Rows Inserted: 73
[2026-07-19 04:34:32] [AGGREGATE] Aggregated sales by product_category
('sports', 37, Decimal('53162.45'), Decimal('1436.82'))
('electronics', 36, Decimal('44327.24'), Decimal('1231.31'))
('clothing', 32, Decimal('36290.68'), Decimal('1134.08'))
('home', 22, Decimal('19510.98'), Decimal('886.86'))
[2026-07-19 04:34:32] [AGGREGATE] Aggregated sales by region
('South', 36, Decimal('53240.20'))
('North', 33, Decimal('37914.27'))
('West', 33, Decimal('34858.78'))
('East', 25, Decimal('27278.10'))
[2026-07-19 04:34:32] [AGGREGATE] Aggregated sales by Top 5 Customers
('frank', 19, Decimal('20256.24'))
('isla', 17, Decimal('19448.22'))
('eve', 12, Decimal('18269.40'))
('charlie', 13, Decimal('16420.47'))
('bob', 12, Decimal('16406.65'))
{'status': 'success', 'rows_extracted': 200, 'rows_valid': 127, 'rows_rejected': 73, 'rows_loaded': 127, 'errors': []}
"""


# ══════════════════════════════════════════════════════════
#  EVALUATION
# ══════════════════════════════════════════════════════════
"""
SCORE: 8/10

BUGS FOUND & FIXED DURING DEVELOPMENT:

BUG 1 — database "sales" does not exist
  ❌ dbname="sales"
  ✅ dbname="postgres"

BUG 2 — cursor has no attribute execute_values
  ❌ cur.execute_values(...)
  ✅ execute_values(cur, ...)   — standalone function from psycopg2.extras

BUG 3 — invalid input syntax for numeric
  ❌ df.itertuples() without explicit column order → date inserted into numeric column
  ✅ df[cols].itertuples() with ordered cols list matching INSERT column list exactly

BUG 4 — NumericValueOutOfRange: integer out of range
  ❌ pandas NaN (float) passed to PostgreSQL INTEGER column → psycopg2 crash
  ✅ df[cols].astype(object).where(pd.notna(df[cols]), other=None)
     astype(object) is essential — without it, itertuples converts None back to NaN

BUG 5 — typo "regoin" in transform()
  ❌ df_transformed["regoin"] — wrote to a phantom column, region column untransformed
  ✅ df_transformed["region"]

BUG 6 — missing ON CONFLICT on sales_rejected
  ❌ second pipeline run crashes with duplicate key violation on order_id
  ✅ ON CONFLICT (order_id) DO NOTHING added

BUG 7 — connection leak in aggregate functions
  ❌ conn/cur opened but cur.close() / conn.close() never called
  ✅ teardown added to all three aggregate functions
"""

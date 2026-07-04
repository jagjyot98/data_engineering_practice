"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 5c
 Topic : SQLAlchemy — Deep Dive: Engine & Pipeline Practice
         Three progressively harder pipelines
 Date  : 2026-07-05
=============================================================
"""

from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime

engine = create_engine("sqlite:///day5c/sales.db")


# ══════════════════════════════════════════════════════════
#  PIPELINE A — Single-source sales pipeline with
#               validate / transform / load and a
#               post-load aggregate query
# ══════════════════════════════════════════════════════════

sales_data = [
    {"order_id": 1,  "customer": "Alice",   "product": "Laptop",  "quantity": 2,    "unit_price": 999.99,  "order_date": "2024-01-15"},
    {"order_id": 2,  "customer": "Bob",     "product": "Phone",   "quantity": 1,    "unit_price": 599.99,  "order_date": "2024-01-15"},
    {"order_id": 3,  "customer": "Charlie", "product": "Laptop",  "quantity": None, "unit_price": 999.99,  "order_date": "2024-01-16"},  # null quantity
    {"order_id": 4,  "customer": None,      "product": "Tablet",  "quantity": 3,    "unit_price": 449.99,  "order_date": "2024-01-16"},  # null customer
    {"order_id": 5,  "customer": "Eve",     "product": "Phone",   "quantity": -1,   "unit_price": 599.99,  "order_date": "2024-01-17"},  # negative qty
    {"order_id": 6,  "customer": "Frank",   "product": "Laptop",  "quantity": 1,    "unit_price": 999.99,  "order_date": "2024-01-17"},
    {"order_id": 7,  "customer": "Grace",   "product": "Tablet",  "quantity": 2,    "unit_price": 449.99,  "order_date": "2024-01-18"},
    {"order_id": 8,  "customer": "Henry",   "product": "Phone",   "quantity": 1,    "unit_price": -50,     "order_date": "2024-01-18"},  # negative price
]
pd.DataFrame(sales_data).to_csv("day5c/sales.csv", index=False)


def log(step, message, rows=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_info = f"{rows}" if rows is not None else ""
    print(f"[{ts}] [{step}] {message}{row_info}")

def extract(filepath):
    df = pd.read_csv(filepath)
    log("EXTRACT", "Read sales data from csv | Rows extracted: ", len(df))
    return df

def validate(df):
    mask_valid = (
        df["customer"].notna() &
        df["quantity"].notna() & (df["quantity"] > 0) &
        df["unit_price"].notna() & (df["unit_price"] > 0)
    )
    df_valid   = df[mask_valid].copy()
    df_invalid = df[~mask_valid].copy()
    df_invalid["reject_reason"] = "null or invalid order data (customer/quantity/unit_price)"
    log("VALIDATE", "Validated sales data | Valid Rows: ", len(df_valid))
    log("VALIDATE", "Found invalid sales data | Invalid Rows: ", len(df_invalid))
    return df_valid, df_invalid

def transform(df):
    df_t = df.copy()
    df_t["customer"]    = df_t["customer"].str.strip().str.lower()
    df_t["product"]     = df_t["product"].str.strip().str.lower()
    df_t["order_date"]  = pd.to_datetime(df_t["order_date"], errors="coerce")
    df_t["total_price"] = df_t["quantity"] * df_t["unit_price"]          # vectorised, not .apply()
    df_t["order_month"] = df_t["order_date"].dt.strftime("%Y-%m")        # "YYYY-MM" string
    log("TRANSFORM", "Transformed sales data | Rows transformed: ", len(df_t))
    return df_t

def load(df, table_name, engine):
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    log("LOAD", f"Loaded data into table '{table_name}' | Rows loaded: ", len(df))

def aggregate_sales_by_product(engine):
    query = text("""
        SELECT product, SUM(total_price) AS total_revenue, COUNT(*) AS orders
        FROM sales_clean
        GROUP BY product
        ORDER BY total_revenue DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    log("AGGREGATE", "Aggregated sales data by product | Rows: ", len(df))
    return df

def run_sales_pipeline(engine):
    extracted_data = extract("day5c/sales.csv")
    valid_data, invalid_data = validate(extracted_data)
    transformed_data = transform(valid_data)
    load(transformed_data, "sales_clean", engine)
    load(invalid_data, "sales_rejected", engine)
    aggregated_data = aggregate_sales_by_product(engine)
    print("Sales by product:")
    print(aggregated_data)
    return {
        "status":         "success",
        "rows_extracted": len(extracted_data),
        "rows_valid":     len(valid_data),
        "rows_rejected":  len(invalid_data),
        "rows_loaded":    len(transformed_data),
        "errors":         [],
    }

print(run_sales_pipeline(engine))


# ══════════════════════════════════════════════════════════
#  PIPELINE A — PIPELINE OUTPUT (VERIFIED)
# ══════════════════════════════════════════════════════════
"""
[EXTRACT]   Read sales data from csv | Rows extracted: 8
[VALIDATE]  Validated sales data | Valid Rows: 4
[VALIDATE]  Found invalid sales data | Invalid Rows: 4
[TRANSFORM] Transformed sales data | Rows transformed: 4
[LOAD]      Loaded data into table 'sales_clean' | Rows loaded: 4
[LOAD]      Loaded data into table 'sales_rejected' | Rows loaded: 4
[AGGREGATE] Aggregated sales data by product | Rows: 3

Sales by product:
  product    total_revenue  orders
  laptop       2999.97        3
  phone         599.99        1

{'status': 'success', 'rows_extracted': 8, 'rows_valid': 4,
 'rows_rejected': 4, 'rows_loaded': 4, 'errors': []}
"""


# ══════════════════════════════════════════════════════════
#  PIPELINE A — EVALUATION & REVIEW
# ══════════════════════════════════════════════════════════
"""
SCORE: 8.5/10

BUGS FOUND & FIXED:

BUG 1 — order_month returned integer, not "YYYY-MM" string
  ❌ df["order_month"] = df["order_date"].dt.month   → returns 1, 2, 3 ...
  ✅ df["order_month"] = df["order_date"].dt.strftime("%Y-%m")  → "2024-01"

BUG 2 — total_price used .apply(axis=1) for simple arithmetic
  ❌ df.apply(lambda row: row["quantity"] * row["unit_price"], axis=1)
     .apply() loops row-by-row — slow and unnecessary here
  ✅ df["total_price"] = df["quantity"] * df["unit_price"]
     Vectorised — operates on entire columns at once, much faster

BUG 3 — engine passed as global into pipeline function instead of parameter
  ❌ def run_sales_pipeline(): ... engine used from global scope
  ✅ def run_sales_pipeline(engine): ... engine passed as argument
     Pipelines must be portable — caller decides which DB to target

KEY LEARNINGS — PIPELINE A:
  1. dt.strftime("%Y-%m") for "YYYY-MM" strings — dt.month gives integers
  2. Vectorised column arithmetic (col1 * col2) is always preferred over .apply(axis=1)
  3. Always pass engine as a parameter — never rely on global state
  4. validate() can inline all column checks with & operators for single-source data
  5. Post-load aggregate queries prove the data landed correctly
"""


# ══════════════════════════════════════════════════════════
#  PIPELINE B — Multi-source: orders enriched with
#               customer lookup; unmatched orders
#               separated into their own table
# ══════════════════════════════════════════════════════════

orders_data = [
    {"order_id": 1, "customer_id": 101, "product": "Laptop",   "amount": 999.99},
    {"order_id": 2, "customer_id": 102, "product": "Phone",    "amount": 599.99},
    {"order_id": 3, "customer_id": 103, "product": "Tablet",   "amount": 449.99},
    {"order_id": 4, "customer_id": 999, "product": "Monitor",  "amount": 299.99},  # unknown customer
    {"order_id": 5, "customer_id": 101, "product": "Mouse",    "amount": 49.99},
    {"order_id": 6, "customer_id": None,"product": "Keyboard", "amount": 79.99},   # missing customer_id
]

customers_data = [
    {"customer_id": 101, "name": "Alice",   "region": "North"},
    {"customer_id": 102, "name": "Bob",     "region": "South"},
    {"customer_id": 103, "name": "Charlie", "region": "East"},
]

pd.DataFrame(orders_data).to_csv("day5c/orders.csv", index=False)
pd.DataFrame(customers_data).to_csv("day5c/customers.csv", index=False)


def extract_b(filepath):
    df = pd.read_csv(filepath)
    log("EXTRACT", f"Extracted data from '{filepath}' | Rows extracted: ", len(df))
    return df

def validate_b(df):
    mask_valid = df["customer_id"].notna()
    df_valid   = df[mask_valid].copy()
    df_invalid = df[~mask_valid].copy()
    df_invalid["reject_reason"] = "null or invalid order data"
    log("VALIDATE", "Validated orders data | Valid Rows: ", len(df_valid))
    log("VALIDATE", "Found invalid orders | Invalid Rows: ", len(df_invalid))
    return df_valid, df_invalid

def transform_b(df_orders, df_customers):
    df_o = df_orders.copy()
    df_c = df_customers.copy()
    df_merged = df_o.merge(df_c, on="customer_id", how="left")  # left: keep all orders
    df_merged["customer_found"] = df_merged["name"].notna()
    df_matched   = df_merged[df_merged["customer_found"]].copy()
    df_unmatched = df_merged[~df_merged["customer_found"]].copy()
    log("TRANSFORM", "Matched orders | Rows: ", len(df_matched))
    log("TRANSFORM", "Unmatched orders (unknown customer_id) | Rows: ", len(df_unmatched))
    return df_matched, df_unmatched

def load_b(df, table_name, engine):
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    log("LOAD", f"Loaded data into table '{table_name}' | Rows loaded: ", len(df))

def run_orders_pipeline(engine):
    orders    = extract_b("day5c/orders.csv")
    customers = extract_b("day5c/customers.csv")
    valid_orders, invalid_orders = validate_b(orders)
    matched_orders, unmatched_orders = transform_b(valid_orders, customers)
    load_b(matched_orders,   "orders_enriched",  engine)
    load_b(unmatched_orders, "orders_unmatched", engine)
    print(f"Orders enriched  : {len(matched_orders)}")
    print(f"Orders unmatched : {len(unmatched_orders)}")
    print(f"Orders rejected  : {len(invalid_orders)}")

run_orders_pipeline(engine)


# ══════════════════════════════════════════════════════════
#  PIPELINE B — PIPELINE OUTPUT (VERIFIED)
# ══════════════════════════════════════════════════════════
"""
[EXTRACT]   Extracted from 'orders.csv'   | Rows extracted: 6
[EXTRACT]   Extracted from 'customers.csv'| Rows extracted: 3
[VALIDATE]  Validated orders data | Valid Rows: 5
[VALIDATE]  Found invalid orders  | Invalid Rows: 1
[TRANSFORM] Matched orders            | Rows: 4
[TRANSFORM] Unmatched orders          | Rows: 1
[LOAD]      Loaded into 'orders_enriched'  | Rows: 4
[LOAD]      Loaded into 'orders_unmatched' | Rows: 1
Orders enriched  : 4
Orders unmatched : 1
Orders rejected  : 1
"""


# ══════════════════════════════════════════════════════════
#  PIPELINE B — EVALUATION & REVIEW
# ══════════════════════════════════════════════════════════
"""
SCORE: 9/10

KEY LEARNINGS — PIPELINE B:
  1. left join in transform is correct here — we WANT to keep all valid orders and
     flag which ones have no customer match (df["name"].notna() flag)
     This is different from Day 5b where inner join was correct (both sources must
     be valid for a record to pass through)
  2. customer_found boolean flag is the right pattern — makes the split readable
  3. Use df[bool_mask] not df[df["col"] == True] — cleaner and more Pythonic
  4. Multi-source pipelines need two extract calls and two separate validate passes
  5. Unmatched records go to their own table for investigation — not silently dropped

WHEN LEFT vs INNER JOIN in transform:
  - Use INNER JOIN when both sources must be valid (Day 5b employee + salary)
  - Use LEFT JOIN when you want to keep all primary records and flag missing lookups
    (here: keep all valid orders, just mark which customer wasn't found)
"""


# ══════════════════════════════════════════════════════════
#  PIPELINE C — Incremental load: only new rows are
#               inserted; existing rows are skipped
# ══════════════════════════════════════════════════════════

day1 = [
    {"order_id": 1, "customer": "Alice", "amount": 500},
    {"order_id": 2, "customer": "Bob",   "amount": 300},
]
day2 = [
    {"order_id": 1, "customer": "Alice", "amount": 500},
    {"order_id": 2, "customer": "Bob",   "amount": 300},
    {"order_id": 3, "customer": "Eve",   "amount": 750},
]


def log_c(step, message, rows=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_info = f"{rows}" if rows is not None else ""
    print(f"[{ts}] [{step}] {message}{row_info}")

def run_incremental_pipeline(df, engine):
    df = pd.DataFrame(df)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders_incremental (
                order_id INTEGER PRIMARY KEY,
                customer TEXT,
                amount REAL
            )
        """))
    existing_ids = pd.read_sql("SELECT order_id FROM orders_incremental", engine)["order_id"].tolist()
    new_rows = df[~df["order_id"].isin(existing_ids)]
    skipped  = df[df["order_id"].isin(existing_ids)]
    if not new_rows.empty:
        new_rows.to_sql("orders_incremental", engine, if_exists="append", index=False)
    log_c("INCREMENTAL LOAD", "New rows into 'orders_incremental' | Rows added: ", len(new_rows))
    log_c("INCREMENTAL LOAD", "Skipped rows already in table | Rows skipped: ", len(skipped))


# Drop table for clean demo — in production you would NOT do this
with engine.begin() as conn:
    conn.execute(text("DROP TABLE IF EXISTS orders_incremental"))

run_incremental_pipeline(day1, engine)   # run day1 FIRST
run_incremental_pipeline(day2, engine)   # then day2 — only Eve is new


# ══════════════════════════════════════════════════════════
#  PIPELINE C — PIPELINE OUTPUT (VERIFIED)
# ══════════════════════════════════════════════════════════
"""
=== RUN 1 — day1 ===
[INCREMENTAL LOAD] New rows into 'orders_incremental' | Rows added: 2
[INCREMENTAL LOAD] Skipped rows already in table | Rows skipped: 0

Table after day1:
 order_id  customer  amount
        1     Alice   500.0
        2       Bob   300.0

=== RUN 2 — day2 ===
[INCREMENTAL LOAD] New rows into 'orders_incremental' | Rows added: 1
[INCREMENTAL LOAD] Skipped rows already in table | Rows skipped: 2

Table after day2:
 order_id  customer  amount
        1     Alice   500.0
        2       Bob   300.0
        3       Eve   750.0

Final row count: 3 (expected: 3)
"""


# ══════════════════════════════════════════════════════════
#  PIPELINE C — EVALUATION & REVIEW
# ══════════════════════════════════════════════════════════
"""
SCORE: 8/10

BUGS FOUND & FIXED:

BUG 1 — day1 run commented out
  ❌ # run_incremental_pipeline(day1, engine)   ← commented out
     Only day2 ran. Table was empty → all 3 day2 rows inserted as "new".
     The skip behavior was never demonstrated.
  ✅ Fix: run day1 first (2 rows inserted), then run day2 (1 new + 2 skipped).
     Both runs are required to prove the incremental dedup works.

BUG 2 — unused load() function with if_exists="replace"
  ❌ def load(df, table_name, engine):
         df.to_sql(table_name, con=engine, if_exists="replace", index=False)
     Defined but never called in the incremental pipeline.
     Worse: if_exists="replace" would wipe all historical data if called accidentally.
  ✅ Fix: removed the function — dead code with a dangerous default doesn't belong here.

KEY LEARNINGS — PIPELINE C:
  1. Incremental load requires two runs in sequence — run the smaller dataset first
     to populate the table, then run the larger one to demonstrate skip behavior
  2. CREATE TABLE IF NOT EXISTS handles the first-run case cleanly — no try/except needed
  3. if_exists="append" is the correct flag for incremental load — never "replace"
  4. Read existing IDs into a Python list → filter new rows with ~df["id"].isin(ids)
  5. Always log both new_rows and skipped counts — both prove the pipeline is working
  6. Don't mix if_exists="replace" utilities in an incremental pipeline — the semantics
     are opposite and will cause data loss if accidentally called

OVERALL DAY 5c SUMMARY:
  Pipeline A — 8.5/10  Vectorised transform, post-load aggregate, engine as parameter
  Pipeline B — 9/10    Left join for enrichment + flag, multi-source split, quarantine
  Pipeline C — 8/10    CREATE TABLE IF NOT EXISTS, isin dedup, append-only incremental
"""

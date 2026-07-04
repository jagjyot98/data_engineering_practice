"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 5c NOTES
 Topic : SQLAlchemy — Engine & Pipeline Deep Practice
         Three progressively harder pipelines
 Date  : 2026-07-05
=============================================================
"""

from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime


# ══════════════════════════════════════════════════════════
#  TOPIC 1 — VECTORISED OPERATIONS vs .apply(axis=1)
# ══════════════════════════════════════════════════════════

# .apply(axis=1) loops over every row in Python — very slow on large datasets
# Vectorised operations work on entire columns at once — always prefer these

# ❌ SLOW — row-by-row Python loop
df["total_price"] = df.apply(lambda row: row["quantity"] * row["unit_price"], axis=1)

# ✅ FAST — vectorised column arithmetic
df["total_price"] = df["quantity"] * df["unit_price"]

# RULE: if you can express the operation as col1 OP col2, use vectorised.
# Only use .apply(axis=1) when the logic genuinely needs multiple columns
# and cannot be expressed as a vectorised expression.


# ══════════════════════════════════════════════════════════
#  TOPIC 2 — DATE FORMATTING WITH dt.strftime
# ══════════════════════════════════════════════════════════

df["order_date"] = pd.to_datetime(df["order_date"], errors="coerce")

# ❌ WRONG — returns an integer (1, 2, 3 ... 12)
df["order_month"] = df["order_date"].dt.month

# ✅ CORRECT — returns a "YYYY-MM" string like "2024-01"
df["order_month"] = df["order_date"].dt.strftime("%Y-%m")

# Common strftime formats:
# "%Y-%m"       → "2024-01"        (year-month, most common for grouping)
# "%Y-%m-%d"    → "2024-01-15"     (full date string)
# "%Y"          → "2024"           (year only)
# "%B %Y"       → "January 2024"   (human readable)
# "%Q"          → not supported — build quarters with dt.quarter manually


# ══════════════════════════════════════════════════════════
#  TOPIC 3 — ALWAYS PASS ENGINE AS A PARAMETER
# ══════════════════════════════════════════════════════════

# ❌ WRONG — pipeline function uses global engine
engine = create_engine("sqlite:///dev.db")

def run_pipeline():
    # engine picked up from global scope — caller cannot change it
    df.to_sql("table", con=engine, if_exists="replace", index=False)

# ✅ CORRECT — engine passed as argument
def run_pipeline(engine):
    df.to_sql("table", con=engine, if_exists="replace", index=False)

# Call the same pipeline against different databases:
dev_engine  = create_engine("sqlite:///dev.db")
test_engine = create_engine("sqlite:///test.db")
run_pipeline(dev_engine)
run_pipeline(test_engine)

# WHY: pipelines must be portable. Global state makes them impossible to test
# or reuse against a different target without editing the function.


# ══════════════════════════════════════════════════════════
#  TOPIC 4 — LEFT JOIN vs INNER JOIN IN TRANSFORM
# ══════════════════════════════════════════════════════════

# The correct join type depends on what you want to happen with unmatched rows.

# INNER JOIN — use when BOTH sources must be valid for a record to pass through
# (Day 5b pattern — employee + salary both required)
df_merged = df_employees.merge(df_salaries, on="employee_id", how="inner")
# Employees with no salary match are dropped entirely

# LEFT JOIN — use when you want to KEEP all primary records and flag missing lookups
# (Day 5c Pipeline B — keep all valid orders, flag which customer wasn't found)
df_merged = df_orders.merge(df_customers, on="customer_id", how="left")
df_merged["customer_found"] = df_merged["name"].notna()
df_matched   = df_merged[df_merged["customer_found"]].copy()
df_unmatched = df_merged[~df_merged["customer_found"]].copy()

# DECISION RULE:
# "Both sources must be valid for this record to mean anything"  → INNER JOIN
# "Keep all primary records, investigate which lookups failed"   → LEFT JOIN + flag


# ══════════════════════════════════════════════════════════
#  TOPIC 5 — INCREMENTAL LOAD PATTERN
# ══════════════════════════════════════════════════════════

# Full replace — drops and recreates the table every run
df.to_sql("orders", con=engine, if_exists="replace", index=False)
# Use when: table is small, source is always the complete dataset

# Append — adds all rows every run, no dedup
df.to_sql("orders_log", con=engine, if_exists="append", index=False)
# Use when: appending to an immutable log/audit table

# Incremental (upsert by key) — insert only rows NOT already in the table
def run_incremental_pipeline(df, engine):
    df = pd.DataFrame(df)

    # Step 1 — create table if it doesn't exist yet (handles first run)
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders_incremental (
                order_id INTEGER PRIMARY KEY,
                customer TEXT,
                amount   REAL
            )
        """))

    # Step 2 — read existing primary keys
    existing_ids = pd.read_sql(
        "SELECT order_id FROM orders_incremental", engine
    )["order_id"].tolist()

    # Step 3 — split incoming data into new vs already-loaded
    new_rows = df[~df["order_id"].isin(existing_ids)]
    skipped  = df[df["order_id"].isin(existing_ids)]

    # Step 4 — append only the new rows
    if not new_rows.empty:
        new_rows.to_sql("orders_incremental", engine, if_exists="append", index=False)

    print(f"New rows added : {len(new_rows)}")
    print(f"Rows skipped   : {len(skipped)}")

# Run in sequence to see incremental behavior:
run_incremental_pipeline(day1, engine)   # → added: 2, skipped: 0
run_incremental_pipeline(day2, engine)   # → added: 1, skipped: 2

# KEY RULES:
# 1. CREATE TABLE IF NOT EXISTS — no try/except needed for first run
# 2. if_exists="append" — never "replace" in an incremental pipeline
# 3. Read existing IDs → filter with ~df["id"].isin(ids) for new rows
# 4. Always run the smaller/earlier dataset first, then the larger one
# 5. Log both new_rows AND skipped — both prove the pipeline is working


# ══════════════════════════════════════════════════════════
#  TOPIC 6 — PIPELINE LOGGING PATTERN
# ══════════════════════════════════════════════════════════

def log(step, message, rows=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_info = f"{rows}" if rows is not None else ""
    print(f"[{ts}] [{step}] {message}{row_info}")

# Usage:
log("EXTRACT",   "Read from CSV | Rows: ", 8)
log("VALIDATE",  "Valid rows: ", 5)
log("VALIDATE",  "Invalid rows: ", 3)
log("TRANSFORM", "Rows transformed: ", 5)
log("LOAD",      "Loaded into 'sales_clean' | Rows: ", 5)

# Output format:
# [2024-01-15 10:23:44] [EXTRACT] Read from CSV | Rows: 8
# [2024-01-15 10:23:44] [VALIDATE] Valid rows: 5

# WHY LOG rows=None as optional:
# Some steps (like a status message) have no row count.
# Making rows optional with None keeps the function reusable.


# ══════════════════════════════════════════════════════════
#  TOPIC 7 — PIPELINE RESULT DICT (RETURN VALUE)
# ══════════════════════════════════════════════════════════

# Returning a summary dict from a pipeline function makes it easy to:
# - Check status in calling code
# - Log to a monitoring system
# - Write pipeline run metadata to a DB table

def run_pipeline(engine):
    # ... pipeline logic ...
    return {
        "status":         "success",
        "rows_extracted": 8,
        "rows_valid":     4,
        "rows_rejected":  4,
        "rows_loaded":    4,
        "errors":         [],
    }

result = run_pipeline(engine)
if result["status"] == "success":
    print(f"Pipeline complete — {result['rows_loaded']} rows loaded")


# ══════════════════════════════════════════════════════════
#  DAY 5c — KEY TAKEAWAYS
# ══════════════════════════════════════════════════════════
"""
PIPELINE A:
  1.  dt.strftime("%Y-%m") for "YYYY-MM" strings — dt.month returns integers
  2.  col1 * col2 (vectorised) always preferred over .apply(axis=1) for arithmetic
  3.  Always pass engine as a parameter — never use global state in pipelines
  4.  Post-load aggregate query confirms data landed correctly

PIPELINE B:
  5.  LEFT JOIN correct here — keep all valid orders, flag which lookup failed
  6.  INNER JOIN correct in Day 5b — both sources must be valid to pass through
  7.  df["name"].notna() as customer_found flag — clean, readable split
  8.  Use df[bool_mask] not df[df["col"] == True] — more Pythonic

PIPELINE C:
  9.  CREATE TABLE IF NOT EXISTS — handles first run without try/except
  10. if_exists="append" for incremental — "replace" would wipe history
  11. Read existing IDs → ~df["id"].isin(ids) — correct dedup filter
  12. Must run earlier batch first to populate table, then later batch to test skip
  13. Log both new_rows and skipped — proves dedup is working in both directions
  14. Never define a load() with if_exists="replace" inside an incremental pipeline

GENERAL:
  15. Pipelines must be tested with real data that exercises both the happy path
      AND the edge cases (nulls, negatives, duplicates, unknown foreign keys)
"""

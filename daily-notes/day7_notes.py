"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 7 NOTES
 Topic : Mini ETL Project — pandas + psycopg2 + PostgreSQL
 Date  : 2026-07-19
=============================================================
"""


# ══════════════════════════════════════════════════════════
#  WHAT IS AN ETL PIPELINE?
# ══════════════════════════════════════════════════════════
"""
ETL = Extract → Transform → Load

A structured pipeline that moves raw data from a source,
cleans and reshapes it, and loads it into a destination.

  CSV file → extract() → validate() → transform() → load() → PostgreSQL

Day 7 pipeline architecture:

  raw_data              = extract(filepath)
  valid, invalid        = validate(raw_data)
  transformed           = transform(valid)
  load_sales_clean(transformed)      # 127 rows → sales_clean
  load_sales_rejected(invalid)       # 73 rows  → sales_rejected
  aggregate queries → result dict

Two destination tables — a real-world pattern:
  sales_clean    → valid, transformed rows ready for analysis
  sales_rejected → invalid rows quarantined for audit/investigation
"""


# ══════════════════════════════════════════════════════════
#  STAGE 1 — EXTRACT
# ══════════════════════════════════════════════════════════
"""
def extract(filepath):
    df = pd.read_csv(filepath)
    return df

Reads raw CSV into a DataFrame.
No filtering, no assumptions — extract is always raw.
"""


# ══════════════════════════════════════════════════════════
#  STAGE 2 — VALIDATE
# ══════════════════════════════════════════════════════════
"""
mask_valid = (
    df["customer"].notna() &
    df["quantity"].notna() & (df["quantity"] > 0) &
    df["unit_price"].notna() & (df["unit_price"] > 0)
)
df_valid   = df[mask_valid].copy()
df_invalid = df[~mask_valid].copy()

Boolean mask splits the DataFrame into two:
  valid rows   → pass ALL conditions
  invalid rows → fail at least one condition

~mask  → bitwise NOT, flips True/False to get the rejected set
.copy() → prevents SettingWithCopyWarning when modifying either slice later
"""


# ══════════════════════════════════════════════════════════
#  STAGE 3 — TRANSFORM (valid rows only)
# ══════════════════════════════════════════════════════════
"""
df_transformed["customer"] = df_transformed["customer"].str.strip().str.lower()
df_transformed["order_date"] = pd.to_datetime(df_transformed["order_date"], errors="coerce")
df_transformed["total_price"] = df_transformed["quantity"] * df_transformed["unit_price"]
df_transformed["loaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")

Key transforms:
  .str.strip().str.lower()          → normalise text (trim whitespace, consistent casing)
  pd.to_datetime(..., errors="coerce") → parse dates; malformed dates become NaT, not a crash
  total_price                       → derived column computed from existing columns
  loaded_at                         → audit timestamp added in Python before load
"""


# ══════════════════════════════════════════════════════════
#  STAGE 4 — LOAD (execute_values)
# ══════════════════════════════════════════════════════════
"""
from psycopg2.extras import execute_values

cols = ["order_id", "customer", ..., "loaded_at"]
sales_tuple = [tuple(row) for row in df[cols].itertuples(index=False)]

execute_values(
    cur,
    "INSERT INTO sales_clean (...) VALUES %s ON CONFLICT (order_id) DO NOTHING",
    sales_tuple
)

execute_values — standalone function from psycopg2.extras (NOT a cursor method).
  Builds one large INSERT ... VALUES (row1), (row2), ... statement.
  Much faster than executemany for large datasets.

Column order matters — df[cols] must list columns in the EXACT same order
as the INSERT column list. One mismatch puts a date into a numeric column → crash.

ON CONFLICT (order_id) DO NOTHING — idempotent re-runs.
  If the pipeline runs twice, duplicate order_ids are silently skipped
  instead of raising a unique-violation error.
"""


# ══════════════════════════════════════════════════════════
#  NaN → None CONVERSION (critical)
# ══════════════════════════════════════════════════════════
"""
df_clean = df[cols].astype(object).where(pd.notna(df[cols]), other=None)

WHY this is needed:
  pandas stores missing values in numeric columns as float('nan')
  itertuples() reads from the underlying numpy float64 array —
  even after df.where(..., None), numpy converts None back to NaN
  PostgreSQL INTEGER/NUMERIC columns reject float nan → NumericValueOutOfRange

THE FIX — two steps:
  1. .astype(object)              → converts numpy float64 to Python object dtype,
                                    so None stays None through itertuples
  2. .where(pd.notna(...), None)  → replaces every NaN with Python None

  None → psycopg2 sends NULL → PostgreSQL stores NULL ✓
"""


# ══════════════════════════════════════════════════════════
#  TABLE DEFINITION MUST COME BEFORE INSERT
# ══════════════════════════════════════════════════════════
"""
psycopg2 sends raw SQL — no ORM, no auto-create.
If the table doesn't exist when execute_values runs → "relation does not exist"

Pattern:
  CREATE TABLE IF NOT EXISTS sales_clean (...)   # runs first, safe on re-run
  # then INSERT
"""


# ══════════════════════════════════════════════════════════
#  REPORTING QUERIES
# ══════════════════════════════════════════════════════════
"""
-- Revenue by product category
SELECT product_category, COUNT(*) AS orders,
       SUM(total_price) AS total_revenue,
       ROUND(AVG(total_price), 2) AS avg_order_value
FROM sales_clean
GROUP BY product_category
ORDER BY total_revenue DESC;

-- Revenue by region
SELECT region, COUNT(*) AS orders, SUM(total_price) AS total_revenue
FROM sales_clean
GROUP BY region
ORDER BY total_revenue DESC;

-- Top 5 customers by spend
SELECT customer, COUNT(*) AS orders, SUM(total_price) AS total_spend
FROM sales_clean
GROUP BY customer
ORDER BY total_spend DESC
LIMIT 5;
"""


# ══════════════════════════════════════════════════════════
#  PIPELINE RESULT DICT
# ══════════════════════════════════════════════════════════
"""
result = {
    "status":         "success",
    "rows_extracted":  200,
    "rows_valid":      127,
    "rows_rejected":   73,
    "rows_loaded":     127,
    "errors":          [],
}

A structured summary returned at the end of the pipeline.
Useful for orchestration tools, logging systems, or alerting.
"""


# ══════════════════════════════════════════════════════════
#  BUGS CAUGHT IN THIS SESSION
# ══════════════════════════════════════════════════════════
"""
BUG 1 — database "sales" does not exist
  ❌ dbname="sales" — no such database
  ✅ dbname="postgres"

BUG 2 — cursor has no attribute execute_values
  ❌ cur.execute_values(...)
  ✅ execute_values(cur, ...)   — standalone function, not a cursor method

BUG 3 — invalid input syntax for numeric
  ❌ df.itertuples() without specifying column order → date went into numeric column
  ✅ df[cols].itertuples() with explicit ordered cols list matching INSERT

BUG 4 — NumericValueOutOfRange: integer out of range
  ❌ pandas NaN passed to PostgreSQL INTEGER column
  ✅ df[cols].astype(object).where(pd.notna(df[cols]), other=None)

BUG 5 — typo "regoin" in transform()
  ❌ df_transformed["regoin"] = ...  → wrote to a phantom column, region untransformed
  ✅ df_transformed["region"] = ...

BUG 6 — missing ON CONFLICT on sales_rejected
  ❌ second pipeline run crashes with duplicate key on order_id
  ✅ ON CONFLICT (order_id) DO NOTHING added

BUG 7 — connection leak in aggregate functions
  ❌ conn/cur opened but never closed
  ✅ cur.close() and conn.close() added to all three aggregate functions
"""

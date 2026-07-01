"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 5b NOTES
 Topic : SQLAlchemy Deep Dive — Pipelines & Engines
 Date  : 2026-06-11
=============================================================
"""

from sqlalchemy import create_engine, text
import pandas as pd


# ══════════════════════════════════════════════════════════
#  TOPIC 1 — ENGINE CREATION & CONNECTION POOLING
# ══════════════════════════════════════════════════════════

# Basic engine — SQLite for local dev
engine = create_engine("sqlite:///day5b/company.db")

# Production engine — PostgreSQL with pool configuration
engine = create_engine(
    "postgresql://user:password@localhost:5432/company",
    pool_size=5,         # keep 5 connections permanently open
    max_overflow=10,     # allow 10 extra connections under high load
    pool_timeout=30,     # wait max 30s for a free connection before error
    pool_pre_ping=True,  # test each connection before use (handles dropped connections)
)

# Debug mode — prints every SQL statement to console (turn off in production)
engine = create_engine("sqlite:///day5b/company.db", echo=True)

# WHY POOLING MATTERS:
# Opening a DB connection takes ~100ms. A pipeline processing 10,000 files
# would be very slow opening a new connection per file.
# The pool keeps connections alive and reuses them — same 5 connections
# serve thousands of pipeline operations.


# ══════════════════════════════════════════════════════════
#  TOPIC 2 — ENGINE vs CONNECTION vs BEGIN
# ══════════════════════════════════════════════════════════

# ENGINE — the factory. Created ONCE, lives for the life of your application.
engine = create_engine("sqlite:///day5b/company.db")

# CONNECTION — for SELECT queries (no commit needed)
with engine.connect() as conn:
    result = conn.execute(text("SELECT * FROM employees"))
    df = pd.DataFrame(result.fetchall(), columns=result.keys())
# connection closes automatically here

# BEGIN — for INSERT/UPDATE/DELETE (auto-commits on success, auto-rolls back on error)
with engine.begin() as conn:
    conn.execute(text("INSERT INTO employees (name) VALUES (:name)"), {"name": "Alice"})
    # NO conn.commit() needed — happens automatically when with block exits cleanly
    # If an exception is raised inside, it auto-rolls back — no data corruption

# RULE: use engine.begin() for DML, engine.connect() for SELECT


# ══════════════════════════════════════════════════════════
#  TOPIC 3 — VALIDATE — ROW-LEVEL NULL & RANGE CHECKS
# ══════════════════════════════════════════════════════════

def validate(df, required_cols, numeric_cols=None):
    # .notna().all(axis=1) — True only if ALL required cols are non-null in that row
    # Works for any column type (string, int, float, date)
    mask_valid = df[required_cols].notna().all(axis=1)

    # Separate numeric range check — only for columns where > 0 must hold
    if numeric_cols:
        for col in numeric_cols:
            mask_valid = mask_valid & (df[col] > 0)

    df_valid   = df[mask_valid].copy()
    df_invalid = df[~mask_valid].copy()
    df_invalid["reject_reason"] = "null or invalid value in required columns"
    return df_valid, df_invalid

# WHY SEPARATE null check from numeric check:
# df[required_cols] returns a DataFrame (2D) when given a list
# You CANNOT compare a string column to > 0 — TypeError
# Solution: .notna().all(axis=1) for nulls, separate loop for numeric rules

# Usage:
# validate(df_employees, required_cols=["name"])                          ← null only
# validate(df_salaries, required_cols=["salary"], numeric_cols=["salary"]) ← null + > 0


# ══════════════════════════════════════════════════════════
#  TOPIC 4 — TRANSFORM — COPY, MERGE, ENRICH
# ══════════════════════════════════════════════════════════

def transform(df_employees, df_salaries):
    df_e = df_employees.copy()   # ALWAYS copy — never mutate inputs
    df_s = df_salaries.copy()    # the caller may still need the originals

    # Clean
    df_e["name"]   = df_e["name"].str.strip().str.lower()
    df_s["salary"] = pd.to_numeric(df_s["salary"], errors="coerce")

    # Enrich
    def salary_band(s):
        if s >= 90000:   return "high"
        elif s >= 60000: return "mid"
        else:            return "low"

    # INNER JOIN — only records valid in BOTH sources pass through
    # LEFT JOIN would keep employees with no salary match → NaN → imputed → leaks into final
    df_merged = df_e.merge(df_s, on="employee_id", how="inner")
    df_merged["salary_band"] = df_merged["salary"].apply(salary_band)
    df_merged["join_date"]   = pd.to_datetime(df_merged["join_date"], errors="coerce")
    return df_merged

# JOIN TYPE MATTERS:
# how="left"  → keeps all employees, missing salary → NaN → gets imputed → BAD
# how="inner" → only employees with valid record in BOTH sources → CORRECT


# ══════════════════════════════════════════════════════════
#  TOPIC 5 — QUARANTINE PATTERN (REJECTED RECORDS)
# ══════════════════════════════════════════════════════════

# Real pipelines NEVER silently drop bad rows.
# Bad rows go to a quarantine/rejected table for investigation.

# ❌ WRONG — left join loses rejected rows from the right source
df_all_invalid = df_employees_invalid.merge(df_salaries_invalid, on="employee_id", how="left")

# ✅ CORRECT — concat stacks all invalid rows from all sources
df_all_invalid = pd.concat(
    [df_employees_invalid, df_salaries_invalid],
    ignore_index=True
)
# Load to quarantine table
df_all_invalid.to_sql("rejected_records", con=engine, if_exists="append", index=False)

# WHY concat NOT merge for invalid rows:
# Invalid rows from different sources rarely share the same employee_id
# merge would only keep the intersection — losing most rejected records
# concat stacks all of them independently


# ══════════════════════════════════════════════════════════
#  TOPIC 6 — INCREMENTAL LOAD vs FULL REPLACE
# ══════════════════════════════════════════════════════════

# FULL REPLACE — drop everything, reload from scratch every run
# Use when: table is small, source is always the complete dataset
df.to_sql("employees", con=engine, if_exists="replace", index=False)

# APPEND — add new rows, keep existing
# Use when: appending today's records to a historical log table
df_today.to_sql("sales_log", con=engine, if_exists="append", index=False)

# UPSERT (incremental) — insert only rows not already in the table
def upsert_table(df, table_name, key_column, engine):
    try:
        existing_ids = pd.read_sql(
            f"SELECT {key_column} FROM {table_name}", con=engine
        )[key_column].tolist()
        df_new = df[~df[key_column].isin(existing_ids)]
    except Exception:
        df_new = df   # table doesn't exist yet — insert everything

    if not df_new.empty:
        df_new.to_sql(table_name, con=engine, if_exists="append", index=False)
        print(f"Inserted {len(df_new)} new rows into '{table_name}'")
    else:
        print("No new rows to insert.")


# ══════════════════════════════════════════════════════════
#  TOPIC 7 — STRUCTURED ETL: THE FULL PATTERN
# ══════════════════════════════════════════════════════════

def extract(filepath):
    df = pd.read_csv(filepath)
    print(f"[EXTRACT] {len(df)} rows read from {filepath}")
    return df

def load(df, table_name, engine):
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    print(f"[LOAD] {len(df)} rows loaded into '{table_name}'")
    return len(df)

def pipeline(engine):
    # ── EXTRACT ───────────────────────────────────────────
    df_employees = extract("day5b/employees.csv")
    df_salaries  = extract("day5b/salaries.csv")

    # ── VALIDATE ──────────────────────────────────────────
    df_employees_valid, df_employees_invalid = validate(df_employees, required_cols=["name"])
    df_salaries_valid,  df_salaries_invalid  = validate(df_salaries, required_cols=["salary"], numeric_cols=["salary"])

    # ── QUARANTINE ────────────────────────────────────────
    df_all_invalid = pd.concat([df_employees_invalid, df_salaries_invalid], ignore_index=True)
    load(df_all_invalid, "rejected_records", engine)

    # ── TRANSFORM ─────────────────────────────────────────
    transformed_df = transform(df_employees_valid, df_salaries_valid)

    # ── LOAD ──────────────────────────────────────────────
    load(transformed_df, "employees_final", engine)

    # ── SUMMARY ───────────────────────────────────────────
    print("=" * 40)
    print("Pipeline Summary")
    print("Valid rows loaded :", len(transformed_df))
    print("Rejected rows     :", len(df_all_invalid))
    print("Target table      : employees_final")
    print("=" * 40)


# ══════════════════════════════════════════════════════════
#  DAY 5b — KEY TAKEAWAYS
# ══════════════════════════════════════════════════════════
"""
1.  engine.begin() for DML — auto-commit on success, auto-rollback on error
2.  engine.connect() for SELECT — no commit needed
3.  validate() separates null checks from numeric range checks
4.  df[list].notna().all(axis=1) → correct row-level boolean mask for multiple cols
5.  Never apply > 0 to string columns — separate numeric_cols param for range checks
6.  Always .copy() in transform — never mutate DataFrames passed as arguments
7.  inner join in transform — only records valid in BOTH sources pass through
8.  left join in transform leaks invalid records via NaN imputation — avoid
9.  pd.concat() to combine invalid rows — never merge across sources for rejections
10. Never silently drop bad rows — always quarantine to rejected_records table
11. if_exists="replace" for full reload, "append" for incremental/log tables
12. pool_pre_ping=True in production — survives dropped DB connections
"""

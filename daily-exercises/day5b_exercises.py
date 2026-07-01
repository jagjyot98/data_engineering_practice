"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 5b
 Topic : SQLAlchemy Deep Dive — Pipelines & Engines
 Date  : 2026-06-11
=============================================================
"""

from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine("sqlite:///day5b/company.db")

# Source 1 — employee info
employees_data = [
    {"employee_id": 1, "name": "  Alice Smith", "department": "Engineering", "join_date": "2021-03-15"},
    {"employee_id": 2, "name": "BOB JONES",     "department": "Marketing",   "join_date": "2020-07-01"},
    {"employee_id": 3, "name": "charlie  ",      "department": "Engineering", "join_date": "2022-01-10"},
    {"employee_id": 4, "name": "Diana Prince",   "department": "HR",          "join_date": "2019-11-20"},
    {"employee_id": 5, "name": "Eve Adams",      "department": "Engineering", "join_date": "2018-05-30"},
    {"employee_id": 6, "name": None,             "department": "Marketing",   "join_date": "2023-02-14"},
]

# Source 2 — salary info (from a separate system)
salaries_data = [
    {"employee_id": 1, "salary": 95000},
    {"employee_id": 2, "salary": 72000},
    {"employee_id": 3, "salary": None},      # missing salary
    {"employee_id": 4, "salary": -5000},     # invalid salary
    {"employee_id": 5, "salary": 88000},
    {"employee_id": 6, "salary": 76000},
]

pd.DataFrame(employees_data).to_csv("day5b/employees.csv", index=False)
pd.DataFrame(salaries_data).to_csv("day5b/salaries.csv", index=False)


# ── EXERCISE 1 — Extract ─────────────────────────────────

def extract(filepath):
    df = pd.read_csv(filepath)
    print(f"[EXTRACT] {len(df)} rows read from {filepath}")
    return df


# ── EXERCISE 2 — Validate ────────────────────────────────

def validate(df, required_cols, numeric_cols=None):
    # Step 1 — null check on all required columns (works for any dtype)
    mask_valid = df[required_cols].notna().all(axis=1)

    # Step 2 — numeric range check (optional, only for numeric columns)
    if numeric_cols:
        for col in numeric_cols:
            mask_valid = mask_valid & (df[col] > 0)

    df_valid   = df[mask_valid].copy()
    df_invalid = df[~mask_valid].copy()
    df_invalid["reject_reason"] = "null or invalid value in required columns"
    print(f"[VALIDATE] {len(df_valid)} valid rows, {len(df_invalid)} invalid rows")
    return df_valid, df_invalid


# ── EXERCISE 3 — Transform ───────────────────────────────

def transform(df_employees, df_salaries):
    df_e = df_employees.copy()   # always copy — never mutate inputs
    df_s = df_salaries.copy()

    df_e["name"]   = df_e["name"].str.strip().str.lower()
    df_s["salary"] = pd.to_numeric(df_s["salary"], errors="coerce")
    df_s["salary"] = df_s["salary"].fillna(df_s["salary"].median())

    def salary_band(s):
        if s >= 90000:   return "high"
        elif s >= 60000: return "mid"
        else:            return "low"

    # inner join — only employees valid in BOTH sources are kept
    df_merged = df_e.merge(df_s, on="employee_id", how="inner")
    df_merged["salary"]      = pd.to_numeric(df_merged["salary"], errors="coerce")
    df_merged["salary"]      = df_merged["salary"].fillna(df_merged["salary"].median())
    df_merged["salary_band"] = df_merged["salary"].apply(salary_band)
    df_merged["join_date"]   = pd.to_datetime(df_merged["join_date"], errors="coerce")
    print(f"[TRANSFORM] {len(df_merged)} rows transformed")
    return df_merged


# ── EXERCISE 4 — Load ────────────────────────────────────

def load(df, table_name, engine):
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    print(f"[LOAD] {len(df)} rows loaded into '{table_name}'")
    return len(df)


# ── EXERCISE 5 — Full Pipeline ───────────────────────────

def pipeline(engine):
    # Extract from both sources
    df_employees = extract("day5b/employees.csv")
    df_salaries  = extract("day5b/salaries.csv")

    # Validate each source independently
    df_employees_valid, df_employees_invalid = validate(
        df_employees, required_cols=["name"]
    )
    df_salaries_valid, df_salaries_invalid = validate(
        df_salaries, required_cols=["salary"], numeric_cols=["salary"]
    )

    # Quarantine all invalid rows from both sources
    df_all_invalid = pd.concat(
        [df_employees_invalid, df_salaries_invalid], ignore_index=True
    )
    load(df_all_invalid, "rejected_records", engine)

    # Transform valid records — inner join ensures both sources are valid
    transformed_df = transform(df_employees_valid, df_salaries_valid)
    load(transformed_df, "employees_final", engine)

    print("=" * 40)
    print("Pipeline Summary")
    print("Valid rows loaded :", len(transformed_df))    # 3
    print("Rejected rows     :", len(df_all_invalid))    # 3
    print("Target table      : employees_final")
    print("=" * 40)

pipeline(engine)


# ══════════════════════════════════════════════════════════
#  PIPELINE OUTPUT (VERIFIED)
# ══════════════════════════════════════════════════════════
"""
[EXTRACT] 6 rows read from day5b/employees.csv
[EXTRACT] 6 rows read from day5b/salaries.csv
[VALIDATE] 5 valid rows, 1 invalid rows
[VALIDATE] 4 valid rows, 2 invalid rows
[LOAD] 3 rows loaded into 'rejected_records'
[LOAD] 3 rows loaded into 'employees_final'
========================================
Pipeline Summary
Valid rows loaded : 3
Rejected rows     : 3
Target table      : employees_final
========================================

employees_final (3 rows):
  id=1  alice smith   Engineering  95000  high
  id=2  bob jones     Marketing    72000  mid
  id=5  eve adams     Engineering  88000  mid

rejected_records (3 rows):
  id=6  null name        (from employees)
  id=3  null salary      (from salaries)
  id=4  salary = -5000   (from salaries)
"""


# ══════════════════════════════════════════════════════════
#  EVALUATION & REVIEW
# ══════════════════════════════════════════════════════════
"""
ITERATION 1 — BUGS FOUND & FIXED:

BUG 1: validate() — wrong approach for mixed-type columns
  ❌ Applied > 0 check to all required_cols including name (TypeError on strings)
  ❌ df[required_cols] returns DataFrame — needed .all(axis=1) to get row mask
  ✅ Fix: separate null check (.notna().all(axis=1)) from numeric check (numeric_cols param)

ITERATION 2 — PIPELINE BUGS FOUND & FIXED:

BUG 2: Rejected records used left join — lost ids 3 and 4
  ❌ df_employees_invalid.merge(df_salaries_invalid, how="left")
     Left join of [id=6] with [id=3, id=4] → only id=6 kept, ids 3&4 lost
  ✅ Fix: pd.concat([df_employees_invalid, df_salaries_invalid]) — all 3 captured

BUG 3: transform() used left join — leaked bad salary employees into final table
  ❌ how="left" kept ids 3 & 4 with NaN salary → filled with median → in final table
  ✅ Fix: how="inner" — only employees valid in BOTH sources pass through

BUG 4: transform() mutated input DataFrames
  ❌ df_employees["name"] = ... directly modified df_employees_valid
  ✅ Fix: df_e = df_employees.copy() at start of transform

KEY LEARNINGS — DAY 5b:
  1. validate() must separate null checks from numeric range checks
  2. df[list].notna().all(axis=1) → correct row-level null mask for multiple cols
  3. pd.concat() to combine invalid rows — never merge invalid dfs across sources
  4. inner join in transform — both sources must be valid for a record to pass through
  5. Always .copy() inputs in transform — never mutate DataFrames you didn't create
  6. Quarantine bad rows to rejected_records — never silently drop or ignore them
  7. engine.begin() auto-commits; engine.connect() requires manual commit()
  8. Parameterise all SQL with text() + :param — never f-strings in queries
"""

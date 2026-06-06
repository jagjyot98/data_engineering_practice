"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 2
 Topic : Pandas — Loading, Inspecting & Cleaning Data
 Date  : 2026-06-07
=============================================================
"""

import csv
import pandas as pd

data = [
    {"employee_id": 1,  "name": "  Alice Smith",  "department": "Engineering", "salary": "95000",  "join_date": "2021-03-15", "manager": "Bob"},
    {"employee_id": 2,  "name": "BOB JONES",       "department": "Marketing",   "salary": "72000",  "join_date": "2020-07-01", "manager": None},
    {"employee_id": 3,  "name": "charlie  ",        "department": "Engineering", "salary": None,     "join_date": "2022-01-10", "manager": "Alice"},
    {"employee_id": 4,  "name": "Diana Prince",     "department": "HR",          "salary": "68000",  "join_date": "2019-11-20", "manager": None},
    {"employee_id": 5,  "name": "BOB JONES",        "department": "Marketing",   "salary": "72000",  "join_date": "2020-07-01", "manager": None},
    {"employee_id": 6,  "name": "Eve Adams",        "department": "Engineering", "salary": "105000", "join_date": "2018-05-30", "manager": "Alice"},
]

df = pd.DataFrame(data)


# ── EXERCISE 1 — Inspect ──────────────────────────────────

print(df.shape)           # (rows, columns)
print(df.columns)         # column names
print(df.dtypes)          # data types per column
print(df.isnull().sum())  # null count per column


# ── EXERCISE 2 — Clean ───────────────────────────────────

# Strip and lowercase name first
df["name"] = df["name"].str.strip().str.lower()

# Convert salary to numeric — errors="coerce" turns bad values into NaN
df["salary"] = pd.to_numeric(df["salary"], errors="coerce")
df["salary"] = df["salary"].astype("Int64")           # ✅ FIXED: Int64 (nullable int), not downcast

# Fill null salaries with median
df["salary"] = df["salary"].fillna(df["salary"].median())

# Convert join_date to datetime
df["join_date"] = pd.to_datetime(df["join_date"], errors="coerce")

# Drop duplicates on business key — NOT just employee_id
# BOB JONES has id=2 and id=5 (different IDs, same person)
df = df.drop_duplicates(subset=["name", "department", "join_date"])  # ✅ FIXED: real duplicate key


# ── EXERCISE 3 — Add Columns ─────────────────────────────

def salary_band(salary):
    if salary >= 90000:
        return "high"
    elif salary >= 60000:
        return "mid"
    else:
        return "low"

df["band"] = df["salary"].apply(salary_band)


def year_at_company(join_date):
    if pd.isnull(join_date):
        return None
    return 2026 - join_date.year

df["years_at_company"] = df["join_date"].apply(year_at_company)


# ── EXERCISE 4 — Save ────────────────────────────────────

df.to_csv("day2/clean_output.csv", index=False)   # ✅ FIXED: correct path


def load_csv(filepath):                            # ✅ FIXED: accepts filepath param
    try:
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:                      # ✅ FIXED: specific exception
        print(f"File not found: {filepath}")
        return []

records = load_csv("day2/clean_output.csv")
for r in records:
    print(r)


# ══════════════════════════════════════════════════════════
#  EVALUATION & REVIEW
# ══════════════════════════════════════════════════════════
"""
SCORE: 8 / 10

EXERCISE 1 — ✅ PERFECT
  + All four inspection methods used correctly

EXERCISE 2 — ✅ GOOD (with fixes)
  ❌ downcast="integer" removed in pandas 3.x — raises TypeError
     Fix: use .astype("Int64") after pd.to_numeric()
  ❌ drop_duplicates on employee_id misses real duplicates
     BOB JONES has id=2 and id=5 — different IDs, same person
     Fix: drop_duplicates on business key (name + department + join_date)
  + errors="coerce" used correctly
  + fillna(median()) — correct choice over mean for salary data

EXERCISE 3 — ✅ PERFECT
  + salary_band function clean and correct
  + pd.isnull() check in year_at_company — excellent defensive coding

EXERCISE 4 — ⚠️ NEEDS FIXES
  ❌ Save path "clean_output.csv" should be "day2/clean_output.csv"
  ❌ load_csv still catching broad Exception (Day 1 lesson repeated)
     Fix: catch FileNotFoundError specifically

KEY TAKEAWAYS:
  1. pd.to_numeric(errors="coerce") → converts bad values to NaN silently
  2. Int64 (capital I) = pandas nullable integer, handles NaN; int cannot
  3. fillna(median()) — prefer median over mean for salary/age (outliers skew mean)
  4. Duplicates rarely share the same ID — use business keys, not just primary key
  5. Always catch specific exceptions — FileNotFoundError, not Exception
  6. Save paths matter — wrong paths silently break downstream pipeline steps
"""

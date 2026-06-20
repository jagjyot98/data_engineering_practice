"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 4
 Topic : File Formats — CSV, JSON & Parquet
 Date  : 2026-06-09
=============================================================
"""

import glob
import json
import os
import pandas as pd

data = [
    {"employee_id": 1,  "name": "  Alice Smith",  "department": "Engineering", "salary": "95000",  "join_date": "2021-03-15"},
    {"employee_id": 2,  "name": "BOB JONES",       "department": "Marketing",   "salary": "72000",  "join_date": "2020-07-01"},
    {"employee_id": 3,  "name": "charlie  ",        "department": "Engineering", "salary": None,     "join_date": "2022-01-10"},
    {"employee_id": 4,  "name": "Diana Prince",     "department": "HR",          "salary": "68000",  "join_date": "2019-11-20"},
    {"employee_id": 5,  "name": "BOB JONES",        "department": "Marketing",   "salary": "72000",  "join_date": "2020-07-01"},
    {"employee_id": 6,  "name": "Eve Adams",        "department": "Engineering", "salary": "105000", "join_date": "2018-05-30"},
]


# ── EXERCISE 1 — CSV Read & Write ────────────────────────

# ✅ FIXED: keep full df separate — never overwrite source df
df_full = pd.DataFrame(data)
df_full.to_csv("day4/employees.csv", index=False)     # ✅ FIXED: correct path

df_slim = pd.read_csv(
    "day4/employees.csv",
    sep=",",
    header=0,
    usecols=["name", "department", "salary"],          # join_date excluded
    dtype={"salary": float},
    na_values=["N/A", "null", ""],
    # parse_dates removed — join_date not in usecols, can't parse excluded column
)
print(df_slim.dtypes)                                  # ✅ FIXED: print to verify


# ── EXERCISE 2 — JSON Read & Write ───────────────────────

# ✅ FIXED: use df_full so all columns are written
df_full.to_json("day4/employees.json", orient="records", indent=2)

# ✅ FIXED: use pd.read_json() — more idiomatic than json.load() + pd.DataFrame()
dfl = pd.read_json("day4/employees.json", orient="records")
print(dfl.head(3))                                     # ✅ FIXED: print to verify


# ── EXERCISE 3 — Parquet Read & Write ────────────────────

# ✅ FIXED: use df_full so all columns are written
df_full.to_parquet("day4/employees.parquet", index=False, compression="snappy")

df_parquet = pd.read_parquet("day4/employees.parquet", columns=["name", "salary"])
print(df_parquet.dtypes)                               # salary = object (was string in source)


# ── EXERCISE 4 — Compare File Sizes ──────────────────────

for fmt in ["day4/employees.csv", "day4/employees.json", "day4/employees.parquet"]:
    size = os.path.getsize(fmt) / 1024
    print(f"{fmt}: {size:.1f} KB")


# ── EXERCISE 5 — Combine Multiple Files ──────────────────

data1 = [
    {"employee_id": 1, "name": "  Alice Smith", "department": "Engineering", "salary": "95000",  "join_date": "2021-03-15"},
    {"employee_id": 2, "name": "BOB JONES",      "department": "Marketing",   "salary": "72000",  "join_date": "2020-07-01"},
    {"employee_id": 3, "name": "charlie  ",       "department": "Engineering", "salary": None,     "join_date": "2022-01-10"},
]
pd.DataFrame(data1).to_csv("day4/employees_part1.csv", index=False)  # ✅ FIXED: correct path

data2 = [
    {"employee_id": 4, "name": "Diana Prince", "department": "HR",          "salary": "68000",  "join_date": "2019-11-20"},
    {"employee_id": 5, "name": "BOB JONES",    "department": "Marketing",   "salary": "72000",  "join_date": "2020-07-01"},
    {"employee_id": 6, "name": "Eve Adams",    "department": "Engineering", "salary": "105000", "join_date": "2018-05-30"},
]
pd.DataFrame(data2).to_csv("day4/employees_part2.csv", index=False)  # ✅ FIXED: correct path

files = glob.glob("day4/employees_part*.csv")          # ✅ FIXED: path prefix in glob
df_combined = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
print(df_combined.shape)                               # (6, 5) — all rows present


# ══════════════════════════════════════════════════════════
#  EVALUATION & REVIEW
# ══════════════════════════════════════════════════════════
"""
SCORE: 7.5 / 10

EXERCISE 1 — ⚠️ CORRECT PATTERN, ISSUES
  ❌ Files saved to root directory, not day4/ folder
  ❌ print(df.dtypes) commented out — always validate output
  + parse_dates conflict correctly fixed (commented out)
  + dtype={"salary": float} used correctly

EXERCISE 2 — ⚠️ DF FLOW ISSUE
  ❌ Wrote the 3-column slim df to JSON (missing employee_id, join_date)
     because df was overwritten in Part 1 with usecols read
  ❌ Used json.load() + pd.DataFrame() instead of pd.read_json()
  ❌ print(dfl.head(3)) commented out
  + orient="records" + indent=2 correct

EXERCISE 3 — ⚠️ SAME DF FLOW ISSUE
  ❌ Parquet written from 3-column df, not full df
  + compression="snappy" correct
  + columns=["name", "salary"] on read correct
  + print(df.dtypes) present ✅

EXERCISE 4 — ✅ CORRECT PATTERN
  + os.path.getsize() used correctly
  + KB conversion correct

EXERCISE 5 — ⚠️ PATH ISSUES
  ❌ Files saved to root, not day4/
  ❌ glob pattern missing path prefix ("employees_v*.csv" → "day4/employees_part*.csv")
  + pd.concat() with ignore_index=True correct
  + print(df.shape) present ✅

KEY TAKEAWAYS:
  1. Never overwrite source df — use separate variable names (df_full, df_slim)
  2. Always use explicit folder paths — files land where the script runs otherwise
  3. Never comment out validation prints — always verify output shape and dtypes
  4. pd.read_json() over json.load() + pd.DataFrame() — stay in pandas
  5. Glob patterns need path prefix — "day4/*.csv" not "*.csv"
  6. parse_dates column must be in usecols — can't parse what you didn't load
  7. Parquet preserves types from source — if source is string, parquet stores string
"""

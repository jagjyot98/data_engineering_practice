"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 3
 Topic : Pandas — Filtering, Grouping & Aggregations
 Date  : 2026-06-08
=============================================================
"""

import pandas as pd

data = [
    {"employee_id": 1,  "name": "Alice",   "department": "Engineering", "salary": 95000,  "experience": 5,  "gender": "F"},
    {"employee_id": 2,  "name": "Bob",     "department": "Marketing",   "salary": 72000,  "experience": 3,  "gender": "M"},
    {"employee_id": 3,  "name": "Charlie", "department": "Engineering", "salary": 105000, "experience": 8,  "gender": "M"},
    {"employee_id": 4,  "name": "Diana",   "department": "HR",          "salary": 68000,  "experience": 2,  "gender": "F"},
    {"employee_id": 5,  "name": "Eve",     "department": "Engineering", "salary": 88000,  "experience": 4,  "gender": "F"},
    {"employee_id": 6,  "name": "Frank",   "department": "Marketing",   "salary": 76000,  "experience": 5,  "gender": "M"},
    {"employee_id": 7,  "name": "Grace",   "department": "HR",          "salary": 71000,  "experience": 4,  "gender": "F"},
    {"employee_id": 8,  "name": "Henry",   "department": "Engineering", "salary": 112000, "experience": 10, "gender": "M"},
    {"employee_id": 9,  "name": "Iris",    "department": "Marketing",   "salary": 69000,  "experience": 2,  "gender": "F"},
    {"employee_id": 10, "name": "Jack",    "department": "HR",          "salary": 74000,  "experience": 6,  "gender": "M"},
]

df = pd.DataFrame(data)


# ── EXERCISE 1 — Filtering ────────────────────────────────

filter_1_data = df[df["salary"] > 80000]

filter_2_data = df[(df["experience"] >= 5) & (df["department"] == "Engineering")]

filter_3_data = df[df["department"].isin(["Marketing", "HR"])]


# ── EXERCISE 2 — Sorting ─────────────────────────────────

sort_1_data = df.sort_values("salary", ascending=False)

sort_2_data = df.sort_values(["department", "experience"], ascending=[True, False])


# ── EXERCISE 3 — GroupBy & Aggregations ──────────────────

aggregate_results = df.groupby("department").agg(
    avg_salary      = ("salary",      "mean"),
    max_salary      = ("salary",      "max"),
    total_employees = ("employee_id", "count"),
    avg_experience  = ("experience",  "mean"),
).reset_index()


# ── EXERCISE 4 — Transform ───────────────────────────────

# ❌ Original attempt — .mean().reset_index() returns a DataFrame (3 rows),
#    can't assign to a 10-row column
# df["dept_avg_salary"] = df.groupby("department")["salary"].mean().reset_index()

# ✅ FIXED — .transform() broadcasts group value back to every original row
df["dept_avg_salary"] = df.groupby("department")["salary"].transform("mean")
print(df[["name", "department", "salary", "dept_avg_salary"]])


# ── EXERCISE 5 — Filter Groups ───────────────────────────

result = df.groupby("department").filter(lambda g: g["salary"].mean() > 80000)


# ══════════════════════════════════════════════════════════
#  EVALUATION & REVIEW
# ══════════════════════════════════════════════════════════
"""
SCORE: 9 / 10

EXERCISE 1 — ✅ PERFECT
  + All three filter patterns correct
  + Parentheses used correctly for multi-conditions
  + .isin() used correctly

EXERCISE 2 — ✅ PERFECT
  + Single and multi-column sort both correct
  + Mixed ascending=[True, False] used correctly

EXERCISE 3 — ✅ PERFECT
  + Named .agg() syntax correct
  + All four metrics correct
  + .reset_index() remembered
  ~ Used 'total_employees' instead of 'headcount' — both are fine,
    just be consistent with team conventions

EXERCISE 4 — ⚠️ NEEDED GUIDANCE
  ❌ .mean().reset_index() returns a 3-row DataFrame, not a 10-row Series
     Cannot be assigned directly to a DataFrame column
  ✅ Fix: use .transform("mean") — broadcasts group avg back to every row
     This is the pandas equivalent of SQL window function:
     AVG(salary) OVER (PARTITION BY department)

EXERCISE 5 — ✅ PERFECT
  + .filter(lambda g: ...) used correctly
  + Filters entire groups, not individual rows

KEY TAKEAWAYS:
  1. Multi-conditions need parentheses: (cond1) & (cond2)
  2. .isin([...]) = SQL IN (...) — cleaner than chaining | conditions
  3. Named .agg() is the professional standard for groupby
  4. .reset_index() after groupby — flattens result to clean DataFrame
  5. .transform("mean") != .mean() — transform broadcasts back to original shape
  6. .transform() = SQL window function: AVG() OVER (PARTITION BY ...)
  7. .filter(lambda g: ...) keeps/drops ENTIRE groups, not individual rows
"""

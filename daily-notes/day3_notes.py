"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 3 NOTES
 Topic : Pandas — Filtering, Grouping & Aggregations
 Date  : 2026-06-08
=============================================================
"""

import pandas as pd

df = pd.DataFrame({
    "name":       ["Alice", "Bob", "Charlie", "Diana", "Eve"],
    "department": ["Engineering", "Marketing", "Engineering", "HR", "Engineering"],
    "salary":     [95000, 72000, 105000, 68000, 88000],
    "experience": [5, 3, 8, 2, 4],
})


# ══════════════════════════════════════════════════════════
#  TOPIC 1 — FILTERING ROWS
# ══════════════════════════════════════════════════════════

# Single condition
df[df["salary"] > 80000]

# Multiple conditions — wrap EACH in parentheses, use & (and) | (or)
df[(df["salary"] > 80000) & (df["department"] == "Engineering")]
df[(df["salary"] < 70000) | (df["experience"] > 6)]

# RULE: without parentheses Python misreads operator precedence → wrong results
# ❌ df[df["salary"] > 80000 & df["department"] == "Engineering"]  # WRONG
# ✅ df[(df["salary"] > 80000) & (df["department"] == "Engineering")]

# .isin() — SQL equivalent of IN (...)
df[df["department"].isin(["Engineering", "HR"])]

# Filter out nulls
df[df["salary"].notna()]

# Negate with ~ (tilde = NOT)
df[~df["department"].isin(["Marketing"])]   # everyone NOT in Marketing


# ══════════════════════════════════════════════════════════
#  TOPIC 2 — SORTING
# ══════════════════════════════════════════════════════════

# Sort by one column, descending
df.sort_values("salary", ascending=False)

# Sort by multiple columns with mixed order
df.sort_values(["department", "experience"], ascending=[True, False])
# department A→Z, then highest experience first within each department


# ══════════════════════════════════════════════════════════
#  TOPIC 3 — GROUPBY & AGGREGATIONS
#  Equivalent to SQL: GROUP BY + aggregate functions
# ══════════════════════════════════════════════════════════

# Basic groupby — single aggregation
df.groupby("department")["salary"].mean()

# Multiple aggregations on one column
df.groupby("department")["salary"].agg(["mean", "min", "max", "count"])

# Named .agg() — PROFESSIONAL STANDARD — multiple columns, named output
df.groupby("department").agg(
    avg_salary  = ("salary",     "mean"),
    max_salary  = ("salary",     "max"),
    avg_exp     = ("experience", "mean"),
    headcount   = ("name",       "count"),
).reset_index()   # ← always reset_index() to flatten back to a DataFrame

# Group by multiple columns
df.groupby(["department", "experience"])["salary"].mean().reset_index()


# ══════════════════════════════════════════════════════════
#  TOPIC 4 — AGGREGATION FUNCTIONS REFERENCE
# ══════════════════════════════════════════════════════════

# "mean"    → average
# "sum"     → total
# "min"     → minimum value
# "max"     → maximum value
# "count"   → non-null count of rows
# "nunique" → count of distinct values
# "first"   → first value in group
# "last"    → last value in group
# "std"     → standard deviation
# "median"  → median value


# ══════════════════════════════════════════════════════════
#  TOPIC 5 — TRANSFORM vs MEAN (CRITICAL DIFFERENCE)
# ══════════════════════════════════════════════════════════

# .mean() → collapses each group into ONE value
#           returns N_groups rows (3 departments → 3 rows)
#           CANNOT be assigned back to the original DataFrame column

# .transform("mean") → broadcasts the group value back to EVERY row
#                      returns same number of rows as original DataFrame
#                      CAN be assigned as a new column

# ❌ WRONG — returns 3 rows, cannot assign to 10-row column
df["dept_avg"] = df.groupby("department")["salary"].mean().reset_index()

# ✅ CORRECT — returns 10 values, one per employee
df["dept_avg"] = df.groupby("department")["salary"].transform("mean")

# SQL equivalent (window function):
# AVG(salary) OVER (PARTITION BY department)

# Other transform uses:
df["dept_max_salary"] = df.groupby("department")["salary"].transform("max")
df["dept_rank"]       = df.groupby("department")["salary"].transform("rank")


# ══════════════════════════════════════════════════════════
#  TOPIC 6 — FILTER GROUPS
# ══════════════════════════════════════════════════════════

# .filter() keeps or drops ENTIRE GROUPS based on a condition
# Unlike row filtering, all rows in a qualifying group are kept

# Keep only departments where avg salary > 80,000
df.groupby("department").filter(lambda g: g["salary"].mean() > 80000)

# Keep only departments with more than 2 employees
df.groupby("department").filter(lambda g: len(g) > 2)

# DIFFERENCE from row filtering:
# Row filter  → df[df["salary"] > 80000]  — keeps individual rows
# Group filter → .filter(lambda g: ...)   — keeps/drops whole groups


# ══════════════════════════════════════════════════════════
#  TOPIC 7 — PIVOT TABLES
# ══════════════════════════════════════════════════════════

df.pivot_table(
    values  = "salary",
    index   = "department",
    aggfunc = "mean"
)

# Multiple values and functions
df.pivot_table(
    values  = ["salary", "experience"],
    index   = "department",
    aggfunc = {"salary": "mean", "experience": "max"}
)


# ══════════════════════════════════════════════════════════
#  TOPIC 8 — RESETTING THE INDEX
# ══════════════════════════════════════════════════════════

# groupby sets the group column as the index
# reset_index() turns it back into a regular column

result = df.groupby("department")["salary"].mean().reset_index()
result.columns = ["department", "avg_salary"]   # rename after reset


# ══════════════════════════════════════════════════════════
#  DAY 3 — KEY TAKEAWAYS
# ══════════════════════════════════════════════════════════
"""
1.  Multi-conditions MUST use parentheses: (cond1) & (cond2)
2.  .isin([...]) = SQL IN (...) — cleaner than chaining | conditions
3.  ~ (tilde) = NOT operator for filtering
4.  Named .agg() is the professional standard — readable, explicit
5.  Always .reset_index() after groupby to get a flat DataFrame
6.  .transform("mean") broadcasts group value to every row (same shape as input)
7.  .mean() collapses to one row per group — can't assign back to original df
8.  .transform() = SQL window function: AGG() OVER (PARTITION BY ...)
9.  .filter(lambda g: ...) keeps/drops ENTIRE groups — not individual rows
10. sort_values with ascending=[True, False] for mixed multi-column sort
"""

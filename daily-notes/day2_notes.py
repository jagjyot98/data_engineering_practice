"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 2 NOTES
 Topic : Pandas — Loading, Inspecting & Cleaning Data
 Date  : 2026-06-07
=============================================================
"""

import pandas as pd


# ══════════════════════════════════════════════════════════
#  TOPIC 1 — LOADING DATA INTO A DATAFRAME
# ══════════════════════════════════════════════════════════

# From CSV file
df = pd.read_csv("sales.csv")

# From JSON file
df = pd.read_json("data.json")

# From a list of dicts (common format from APIs and databases)
data = [
    {"name": "Alice", "age": 30, "salary": 85000},
    {"name": "Bob",   "age": 25, "salary": 72000},
]
df = pd.DataFrame(data)

# From dict of lists (column-oriented format)
df = pd.DataFrame({
    "name":   ["Alice", "Bob"],
    "age":    [30, 25],
    "salary": [85000, 72000],
})


# ══════════════════════════════════════════════════════════
#  TOPIC 2 — INSPECTING DATA
#  Run these FIRST on any new dataset in a pipeline
# ══════════════════════════════════════════════════════════

df.shape            # (rows, columns) — e.g. (1000, 8)
df.dtypes           # data type of each column
df.head(5)          # first 5 rows
df.tail(5)          # last 5 rows
df.info()           # column names, non-null counts, dtypes — summary
df.describe()       # stats for numeric columns: count, mean, std, min, max
df.columns          # list all column names
df.isnull().sum()   # count of missing values per column — always check this


# ══════════════════════════════════════════════════════════
#  TOPIC 3 — SELECTING DATA
# ══════════════════════════════════════════════════════════

df["name"]                  # single column → returns a Series
df[["name", "salary"]]      # multiple columns → returns a DataFrame

df.iloc[0]                  # first row by position
df.iloc[0:3]                # first 3 rows by position

df.loc[df["age"] > 25]      # rows matching a condition


# ══════════════════════════════════════════════════════════
#  TOPIC 4 — CLEANING DATA
# ══════════════════════════════════════════════════════════

# --- Rename columns ---
df = df.rename(columns={"emp_nm": "name", "sal": "salary"})

# --- Drop columns ---
df = df.drop(columns=["irrelevant_column"])

# --- Handle missing values ---
df["salary"].isnull().sum()                 # count nulls in a column
df = df.dropna(subset=["name"])             # drop rows where name is null
df["salary"] = df["salary"].fillna(0)       # fill nulls with fixed value
df["salary"] = df["salary"].fillna(df["salary"].median())  # fill with median ← preferred for salary/age

# --- Convert to numeric (handles mixed/dirty columns) ---
# errors="coerce" turns unparseable values into NaN instead of raising an error
df["salary"] = pd.to_numeric(df["salary"], errors="coerce")
df["salary"] = df["salary"].astype("Int64")  # Int64 (capital I) = nullable integer
# NOTE: regular int cannot hold NaN — always use Int64 after pd.to_numeric

# --- Convert to datetime ---
df["join_date"] = pd.to_datetime(df["join_date"], errors="coerce")
# errors="coerce" turns bad dates into NaT (Not a Time) instead of crashing

# --- String cleaning ---
df["name"] = df["name"].str.strip()           # remove leading/trailing whitespace
df["name"] = df["name"].str.lower()           # lowercase
df["name"] = df["name"].str.strip().str.lower()  # chain both at once

# --- Remove duplicates ---
df = df.drop_duplicates()                          # all columns must match
df = df.drop_duplicates(subset=["name"])           # based on one column
df = df.drop_duplicates(subset=["name", "department", "join_date"])  # business key

# RULE: duplicates rarely share the same ID — use BUSINESS KEYS not primary keys
# e.g. same person re-entered with a new employee_id — drop on name+dept+date


# ══════════════════════════════════════════════════════════
#  TOPIC 5 — ADDING & MODIFYING COLUMNS
# ══════════════════════════════════════════════════════════

# Add a simple calculated column
df["annual_bonus"] = df["salary"] * 0.10

# Conditional column using apply + function
def salary_band(salary):
    if salary >= 80000:
        return "high"
    elif salary >= 60000:
        return "mid"
    else:
        return "low"

df["band"] = df["salary"].apply(salary_band)

# Handling nulls inside apply functions
def year_at_company(join_date):
    if pd.isnull(join_date):   # always check for NaT/NaN before operating on dates
        return None
    return 2026 - join_date.year

df["years_at_company"] = df["join_date"].apply(year_at_company)

# Extract parts of a datetime column
df["join_year"]  = df["join_date"].dt.year
df["join_month"] = df["join_date"].dt.month

# String operations on a column
df["name_upper"] = df["name"].str.upper()


# ══════════════════════════════════════════════════════════
#  TOPIC 6 — SAVING DATA
# ══════════════════════════════════════════════════════════

# To CSV — ALWAYS use index=False
df.to_csv("output/clean_output.csv", index=False)
# Without index=False, pandas writes row numbers as an extra column
# that pollutes your data and breaks downstream reads

# To JSON
df.to_json("output/clean_output.json", orient="records", indent=2)
# orient="records" → list of dicts format [{"col": val}, ...]


# ══════════════════════════════════════════════════════════
#  TOPIC 7 — INT64 vs int64 (IMPORTANT!)
# ══════════════════════════════════════════════════════════

# int64  (lowercase) = NumPy integer — CANNOT hold NaN, will error
# Int64  (capital I) = Pandas nullable integer — CAN hold NaN safely

# Workflow for dirty numeric columns:
# Step 1: pd.to_numeric(errors="coerce")  → converts bad strings to NaN
# Step 2: .astype("Int64")                → store as nullable integer
# Step 3: .fillna(median)                 → fill NaN before further processing


# ══════════════════════════════════════════════════════════
#  DAY 2 — KEY TAKEAWAYS
# ══════════════════════════════════════════════════════════
"""
1.  Always inspect first: .shape, .dtypes, .isnull().sum(), .head()
2.  pd.to_numeric(errors="coerce") — bad values become NaN, no crash
3.  Int64 (capital I) for nullable integers after pd.to_numeric
4.  fillna(median) — prefer over mean for salary/age (outliers skew mean)
5.  pd.to_datetime(errors="coerce") — bad dates become NaT, no crash
6.  Always check pd.isnull() before operating on date values in apply()
7.  Duplicates use BUSINESS KEYS not just primary key IDs
8.  to_csv(index=False) — always, or you get a junk index column in your file
9.  Chain string ops: .str.strip().str.lower() in one line
10. downcast parameter removed in pandas 3.x — use .astype("Int64") instead
"""

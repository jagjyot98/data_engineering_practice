"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 4 NOTES
 Topic : File Formats — CSV, JSON & Parquet
 Date  : 2026-06-09
=============================================================
"""

import glob
import json
import os
import pandas as pd


# ══════════════════════════════════════════════════════════
#  TOPIC 1 — CSV: THE UNIVERSAL FORMAT
# ══════════════════════════════════════════════════════════

df = pd.DataFrame({
    "name": ["Alice", "Bob"],
    "salary": [95000, 72000],
    "join_date": ["2021-03-15", "2020-07-01"],
})

# --- Writing ---
df.to_csv("output.csv", index=False)    # index=False ALWAYS — prevents junk row number column
df.to_csv("output.csv", index=False, sep="|")   # pipe-delimited

# --- Reading ---
df = pd.read_csv("output.csv")

# Common options
df = pd.read_csv(
    "output.csv",
    sep=",",                              # delimiter (use "\t" for tab-separated)
    header=0,                             # row 0 = column names
    usecols=["name", "salary"],           # load only specific columns — saves memory
    dtype={"salary": float},              # set types on load — avoids guessing
    na_values=["N/A", "null", "none", ""], # treat these strings as NaN
    parse_dates=["join_date"],            # auto-convert to datetime
)

# RULE: if a column is in parse_dates, it MUST also be in usecols
# You cannot parse a column you didn't load

# CSV pros: human readable, universal, easy to debug
# CSV cons: no type info (everything loads as string/object), slow on large data, large file size


# ══════════════════════════════════════════════════════════
#  TOPIC 2 — JSON: THE API FORMAT
# ══════════════════════════════════════════════════════════

# --- Writing ---
df.to_json("output.json", orient="records", indent=2)
# orient="records" → [{"col": val, ...}, ...]  ← standard API format, use this

# Other orient options:
# "split"   → {"columns": [...], "data": [[...]]}
# "index"   → {"0": {"col": val}, "1": {...}}
# "columns" → {"col": {"0": val, "1": val}}

# --- Reading ---
df = pd.read_json("output.json", orient="records")   # preferred — stays in pandas

# Reading nested JSON from an API response
with open("api_response.json") as f:
    raw = json.load(f)
df = pd.DataFrame(raw["data"])   # data nested under a key

# JSON pros: supports nested structures, standard for APIs, human readable
# JSON cons: large file size, slow on large data, no schema enforcement


# ══════════════════════════════════════════════════════════
#  TOPIC 3 — PARQUET: THE DATA ENGINEERING STANDARD
# ══════════════════════════════════════════════════════════

# --- Writing ---
df.to_parquet("output.parquet", index=False)                          # default compression
df.to_parquet("output.parquet", index=False, compression="snappy")    # snappy = fast + small

# --- Reading ---
df = pd.read_parquet("output.parquet")
df = pd.read_parquet("output.parquet", columns=["name", "salary"])   # load specific columns only

# Parquet pros:
#   - Columnar storage — reads only columns you need (massive I/O savings)
#   - Preserves data types — no type guessing on load
#   - 10-20x smaller than CSV with compression
#   - Industry standard: used in Spark, dbt, Airflow, S3 data lakes
# Parquet cons:
#   - Not human readable
#   - Can't open in Excel
#   - Requires pyarrow or fastparquet


# ══════════════════════════════════════════════════════════
#  TOPIC 4 — COLUMNAR vs ROW STORAGE (WHY PARQUET IS FAST)
# ══════════════════════════════════════════════════════════

# CSV / JSON (Row storage) — stores one full row at a time:
#   [Alice | Engineering | 95000]
#   [Bob   | Marketing   | 72000]
#   → To get AVG(salary): must read ALL columns

# Parquet (Columnar storage) — stores one full column at a time:
#   [Alice, Bob, Charlie]     ← name column
#   [Engineering, Marketing]  ← dept column
#   [95000, 72000, 105000]    ← salary column
#   → To get AVG(salary): reads ONLY the salary column — far less I/O

# SQL equivalent intuition:
#   SELECT AVG(salary) FROM employees;
#   CSV   → scans entire file
#   Parquet → reads salary column only


# ══════════════════════════════════════════════════════════
#  TOPIC 5 — COMPARING FILE SIZES & PERFORMANCE
# ══════════════════════════════════════════════════════════

import time

df_large = pd.DataFrame({
    "id":         range(100000),
    "name":       ["Employee"] * 100000,
    "department": ["Engineering"] * 100000,
    "salary":     [95000] * 100000,
})

df_large.to_csv("test.csv", index=False)
df_large.to_json("test.json", orient="records")
df_large.to_parquet("test.parquet", index=False)

# File sizes
for fmt in ["test.csv", "test.json", "test.parquet"]:
    size_kb = os.path.getsize(fmt) / 1024
    print(f"{fmt}: {size_kb:.1f} KB")
# Typical result: CSV ~5000 KB, JSON ~8000 KB, Parquet ~300 KB

# Read speeds
for fmt, reader in [
    ("test.csv",     lambda: pd.read_csv("test.csv")),
    ("test.json",    lambda: pd.read_json("test.json")),
    ("test.parquet", lambda: pd.read_parquet("test.parquet")),
]:
    start = time.time()
    reader()
    print(f"{fmt}: {time.time() - start:.4f}s")
# Parquet is typically 5-10x faster to read than CSV


# ══════════════════════════════════════════════════════════
#  TOPIC 6 — WORKING WITH MULTIPLE FILES
# ══════════════════════════════════════════════════════════

# Read all CSVs in a folder into one DataFrame
files = glob.glob("data/sales_*.csv")       # glob finds files matching a pattern
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)
# ignore_index=True — resets row index, prevents duplicate index values

# Read all Parquet files
files = glob.glob("data/*.parquet")
df = pd.concat([pd.read_parquet(f) for f in files], ignore_index=True)

# RULE: glob pattern needs a path prefix
# ❌ glob.glob("*.csv")           — only searches current working directory
# ✅ glob.glob("day4/*.csv")      — searches inside day4/ folder


# ══════════════════════════════════════════════════════════
#  TOPIC 7 — VARIABLE NAMING (CRITICAL PATTERN)
# ══════════════════════════════════════════════════════════

# RULE: never overwrite your source df when reading a subset

# ❌ BAD — df is lost after this; parts 2 and 3 work on 3-column df
df = pd.DataFrame(data)
df.to_csv("output.csv", index=False)
df = pd.read_csv("output.csv", usecols=["name", "salary"])  # overwrites df!
df.to_json("output.json")   # only has 2 columns now — data lost

# ✅ GOOD — keep source and derived dfs separate
df_full = pd.DataFrame(data)         # full original
df_full.to_csv("output.csv", index=False)
df_slim = pd.read_csv("output.csv", usecols=["name", "salary"])  # subset
df_full.to_json("output.json")       # full df used for other formats


# ══════════════════════════════════════════════════════════
#  TOPIC 8 — FORMAT COMPARISON REFERENCE
# ══════════════════════════════════════════════════════════

# Format     | Size  | Speed | Types | Human Readable | Use When
# -----------|-------|-------|-------|----------------|----------
# CSV        | Large | Slow  | No    | Yes            | Sharing data with non-engineers, Excel users
# JSON       | Huge  | Slow  | No    | Yes            | API responses, nested data, configs
# Parquet    | Small | Fast  | Yes   | No             | Data pipelines, data lakes, large datasets


# ══════════════════════════════════════════════════════════
#  DAY 4 — KEY TAKEAWAYS
# ══════════════════════════════════════════════════════════
"""
1.  to_csv(index=False) ALWAYS — without it, a junk row number column is added
2.  parse_dates column must be in usecols — can't parse what you didn't load
3.  Never overwrite source df — use df_full / df_slim naming pattern
4.  pd.read_json() preferred over json.load() + pd.DataFrame()
5.  orient="records" for JSON — standard list-of-dicts format
6.  Parquet is the standard for data engineering pipelines — use it by default
7.  compression="snappy" — fastest compression for Parquet, minimal CPU overhead
8.  columns=[] on read_parquet() — load only what you need (columnar advantage)
9.  glob pattern needs a path prefix — "day4/*.csv" not "*.csv"
10. pd.concat(..., ignore_index=True) — always reset index when combining files
"""

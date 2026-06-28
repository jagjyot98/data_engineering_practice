# Data Engineering Practice

A structured, day-by-day learning repository for becoming a job-ready **Data Engineer** — built from the ground up using local tools before moving to cloud platforms.

This repository tracks daily practice exercises, concept notes, and hands-on projects covering the full data engineering stack: Python, dbt, Apache Airflow, PySpark, and beyond.

---

## Goals

- Build job-ready data engineering skills through daily hands-on practice
- Cover the full local data engineering stack before cloud platforms
- Maintain a portfolio of end-to-end pipeline projects for interviews

---

## Learning Roadmap

| Phase | Topics | Duration |
|-------|--------|----------|
| **Phase 1** | Python for Data Engineering | Weeks 1–2 |
| **Phase 2** | dbt (Data Build Tool) | Weeks 3–5 |
| **Phase 3** | Apache Airflow | Weeks 6–8 |
| **Phase 4** | Apache Spark / PySpark | Weeks 9–12 |
| **Phase 5** | Portfolio Projects | Week 13+ |

---

## Repository Structure

```
data-engineering-practice/
│
├── daily-exercises/              # Attempts, evaluations, fixes and scores
│   ├── day1_exercises.py
│   ├── day2_exercises.py
│   └── ...
│
├── daily-notes/                  # Full concept notes for each day's topics
│   ├── day1_notes.py
│   ├── day2_notes.py
│   └── ...
│
├── dayN/                         # Raw working/scratch files used during session
│   └── dayN_exercises.py
│
└── README.md
```

### Folder Descriptions

| Folder | Purpose |
|--------|---------|
| `daily-exercises/` | Polished exercise files — contains the original attempt, all corrections, evaluation score, and key takeaways |
| `daily-notes/` | Complete concept notes taught each day — syntax, rules, examples, and gotchas |
| `dayN/` | Raw scratch folder used during live coding — unpolished, as-written during the session |

---

## Day-wise Index

### Phase 1 — Python for Data Engineering

| Day | Topic | Concepts Covered | Score |
|-----|-------|-----------------|-------|
| [Day 1](daily-exercises/day1_exercises.py) | Python Basics | Data structures, functions, list comprehensions, file I/O (CSV/JSON), error handling, f-strings | 7.5/10 |
| [Day 2](daily-exercises/day2_exercises.py) | Pandas — Loading, Inspecting & Cleaning | DataFrame creation, inspection methods, pd.to_numeric, pd.to_datetime, fillna, drop_duplicates, apply, to_csv | 8/10 |
| [Day 3](daily-exercises/day3_exercises.py) | Pandas — Filtering, Grouping & Aggregations | Row filtering, .isin(), multi-condition filters, sort_values, groupby, named .agg(), .transform(), .filter() groups, pivot_table | 9/10 |
| [Day 4](daily-exercises/day4_exercises.py) | File Formats — CSV, JSON & Parquet | read_csv options, usecols, parse_dates, to_json orient, pd.read_json, to_parquet, columnar storage, glob, pd.concat | 7.5/10 |
| [Day 5](daily-exercises/day5_exercises.py) | SQLAlchemy — Connecting Python to Databases | create_engine, to_sql, pd.read_sql, text() parameterised queries, ETL pipeline pattern, inspect | 7.5/10 |
| Day 5b | SQLAlchemy — Deep Dive: Pipelines & Engines | *(upcoming)* | — |
| Day 6 | psycopg2 | *(upcoming)* | — |
| Day 7 | Mini ETL Project | *(upcoming)* | — |

---

## Day-wise Notes Summary

### Day 1 — Python Basics for Data Engineering
**Date:** 2026-06-06

**Topics covered:**
- **Data structures** — lists, dicts, list-of-dicts (most common pipeline format), tuples
- **Functions & list comprehensions** — writing reusable clean functions, replacing for-loops with comprehensions
- **File I/O** — reading and writing CSV (`csv.DictReader`, `csv.DictWriter`) and JSON (`json.load`, `json.dump`)
- **Error handling** — wrapping `open()` inside `try`, catching specific exceptions (`FileNotFoundError`, `ValueError`, `TypeError`), returning `None` for bad values instead of crashing
- **f-strings** — preferred over string concatenation for readability and performance
- **Record mutation** — always use `record.copy()` before modifying; never mutate original raw data in a pipeline

**Key rules learned:**
- `newline=""` is for CSV writers only — never use on JSON file handles
- Always wrap `open()` inside the `try` block, not outside
- Functions must accept parameters — no hardcoded paths in pipeline code
- Catch specific exceptions, not broad `Exception`

📄 [Full notes](daily-notes/day1_notes.py) | 📝 [Exercise & evaluation](daily-exercises/day1_exercises.py)

---

### Day 2 — Pandas: Loading, Inspecting & Cleaning Data
**Date:** 2026-06-07

**Topics covered:**
- **Loading data** — `pd.DataFrame()` from list of dicts, dict of lists, CSV, JSON
- **Inspecting data** — `.shape`, `.dtypes`, `.columns`, `.head()`, `.info()`, `.isnull().sum()`
- **Cleaning data** — `.str.strip()`, `.str.lower()`, `pd.to_numeric(errors="coerce")`, `pd.to_datetime(errors="coerce")`, `.fillna()`, `.drop_duplicates()`
- **Nullable integers** — `Int64` (capital I) vs `int64` — only `Int64` can hold `NaN`
- **Adding columns** — `.apply()` with custom functions, datetime extraction with `.dt.year`
- **Saving data** — `to_csv(index=False)` — always use `index=False`

**Key rules learned:**
- `pd.to_numeric(errors="coerce")` — bad values silently become `NaN`, pipeline doesn't crash
- Always use `Int64` (capital I) after `pd.to_numeric` — regular `int` cannot hold `NaN`
- Use `fillna(median())` not `fillna(mean())` for salary/age — outliers skew the mean
- Duplicates rarely share the same ID — drop on business keys (name + dept + date), not primary key
- `to_csv(index=False)` always — without it, row numbers appear as a junk extra column
- `downcast` parameter removed in pandas 3.x — use `.astype("Int64")` instead
- Always check `pd.isnull()` before operating on date values inside `.apply()`

📄 [Full notes](daily-notes/day2_notes.py) | 📝 [Exercise & evaluation](daily-exercises/day2_exercises.py)

---

### Day 3 — Pandas: Filtering, Grouping & Aggregations
**Date:** 2026-06-08

**Topics covered:**
- **Filtering** — single/multi-condition filters, `&` / `|` operators, `.isin()`, `~` (NOT), `.notna()`
- **Sorting** — `sort_values()` single and multi-column with mixed ascending order
- **GroupBy & Aggregations** — named `.agg()`, multiple metrics in one call, `.reset_index()`
- **Aggregation functions** — `mean`, `sum`, `min`, `max`, `count`, `nunique`, `median`, `std`
- **Transform** — `.transform("mean")` broadcasts group value back to every row (SQL window function equivalent)
- **Group filtering** — `.filter(lambda g: ...)` keeps or drops entire groups
- **Pivot tables** — `pivot_table()` with multiple values and functions

**Key rules learned:**
- Multi-conditions **must** use parentheses: `(cond1) & (cond2)` — without them, operator precedence breaks silently
- `.isin([...])` = SQL `IN (...)` — always prefer over chaining `|` conditions
- Named `.agg()` is the professional standard — explicit, readable, one call
- Always `.reset_index()` after groupby to flatten back to a clean DataFrame
- `.transform("mean")` ≠ `.mean()` — transform returns same shape as input; mean collapses to one row per group
- `.transform()` = SQL window function: `AVG(salary) OVER (PARTITION BY department)`
- `.filter(lambda g: ...)` drops **entire groups**, not individual rows

📄 [Full notes](daily-notes/day3_notes.py) | 📝 [Exercise & evaluation](daily-exercises/day3_exercises.py)

---

### Day 4 — File Formats: CSV, JSON & Parquet
**Date:** 2026-06-09

**Topics covered:**
- **CSV** — `read_csv` options: `usecols`, `dtype`, `na_values`, `parse_dates`, `sep`; `to_csv(index=False)`
- **JSON** — `to_json(orient="records")`, `pd.read_json()`, reading nested API responses with `json.load()`
- **Parquet** — `to_parquet(compression="snappy")`, `read_parquet(columns=[])`, columnar storage concept
- **Format comparison** — file sizes, read speeds, type preservation across CSV / JSON / Parquet
- **Multiple files** — `glob.glob()` pattern matching, `pd.concat(..., ignore_index=True)`
- **Variable naming** — `df_full` vs `df_slim` pattern to avoid overwriting source data

**Key rules learned:**
- `to_csv(index=False)` always — without it, a junk row number column is written
- `parse_dates` column must also be in `usecols` — can't parse a column you didn't load
- Never overwrite source df — use separate names (`df_full`, `df_slim`) when reading subsets
- `pd.read_json()` preferred over `json.load()` + `pd.DataFrame()` — stay in pandas
- `orient="records"` for JSON — standard list-of-dicts format used in APIs
- Parquet is the standard format for data pipelines — preserves types, columnar, compressed
- `columns=[]` on `read_parquet()` — load only what you need; this is the columnar advantage
- Glob patterns need a path prefix — `"day4/*.csv"` not `"*.csv"`
- `pd.concat(..., ignore_index=True)` — always reset index when combining files

📄 [Full notes](daily-notes/day4_notes.py) | 📝 [Exercise & evaluation](daily-exercises/day4_exercises.py)

---

### Day 5 — SQLAlchemy: Connecting Python to Databases
**Date:** 2026-06-10

**Topics covered:**
- **Engine creation** — `create_engine()` for SQLite and PostgreSQL; connection string format; lazy connection
- **Writing to database** — `to_sql()` with `if_exists`, `index=False`; difference between replace/append/fail
- **Reading from database** — `pd.read_sql()` with full queries, filters, aggregations
- **Parameterised queries** — `text()` + `:param` syntax; why f-strings in SQL = SQL injection
- **Raw SQL execution** — DDL and DML with `engine.connect()`, `conn.execute()`, `conn.commit()`
- **ETL pipeline pattern** — Extract (read CSV) → Transform (clean + enrich in Python) → Load (to_sql)
- **Database inspection** — `inspect(engine)`, `get_table_names()`, `get_columns()`

**Key rules learned:**
- `fetchall()` and `keys()` must be **inside** the `with engine.connect()` block — connection closes on exit
- NEVER use f-strings in SQL — always use `text()` + `:param` for parameterised queries (SQL injection)
- Functions should **return** DataFrames, not just print them — callers need the data
- ETL means transform your **extracted data** (`df_raw`) — don't bypass it and re-query the DB
- `if_exists="replace"` is safe to run repeatedly — it's not a one-time operation
- SQL type comparisons must match the column type — no quotes around number comparisons
- Always verify the correct table in `COUNT(*)` after load

📄 [Full notes](daily-notes/day5_notes.py) | 📝 [Exercise & evaluation](daily-exercises/day5_exercises.py)

---

## Tools & Stack

| Tool | Purpose | Phase |
|------|---------|-------|
| Python 3.11+ | Scripting and pipeline logic | 1 |
| pandas | Data manipulation | 1 |
| SQLAlchemy | Python ↔ database connector | 1 |
| psycopg2 | Raw SQL from Python | 1 |
| PyArrow | Parquet file format support | 1 |
| PostgreSQL | Local relational database | 1–3 |
| dbt-core | SQL-based data transformations | 2 |
| Apache Airflow | Pipeline orchestration (via Docker) | 3 |
| Apache Spark | Distributed data processing | 4 |
| Docker Desktop | Run Airflow and Spark locally | 3–4 |
| DBeaver | Database GUI | 1+ |
| VS Code | Primary IDE | All |

---

## Prerequisites

- Python 3.11+
- PostgreSQL (local install)
- Docker Desktop (from Phase 3)
- VS Code with Python + Pylance extensions

Install Phase 1 dependencies:
```bash
python -m venv venv
venv\Scripts\activate
pip install pandas sqlalchemy psycopg2-binary pyarrow openpyxl
```

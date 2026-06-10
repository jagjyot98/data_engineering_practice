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
| Day 3 | Pandas — Filtering & Aggregations | *(upcoming)* | — |
| Day 4 | File Formats | *(upcoming)* | — |
| Day 5 | SQLAlchemy | *(upcoming)* | — |
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

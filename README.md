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
| [Day 5b](daily-exercises/day5b_exercises.py) | SQLAlchemy — Deep Dive: Pipelines & Engines | Multi-source pipeline, validate(), quarantine pattern, inner vs left join in transform, pd.concat for rejections, engine.begin() | 9/10 |
| [Day 5c](daily-exercises/day5c_exercises.py) | SQLAlchemy — Pipeline Deep Practice (3 Pipelines) | Vectorised ops vs .apply(), dt.strftime, engine as param, left vs inner join for enrichment, incremental load with CREATE TABLE IF NOT EXISTS + isin dedup | A:8.5 B:9 C:8 |
| [Day 5d](daily-exercises/day5d_exercises.py) | ETL Deep Dive — Chunked Loading, Upsert + Audit, Checkpointing | chunksize iterator, mask-once pattern, INSERT OR REPLACE, audit columns (loaded_at/source_file/run_id), uuid, state table, idempotency, os.path.basename | A:9 B:9 C:9 |
| [Day 6](daily-exercises/day6_exercises.py) | psycopg2 — Raw Python to PostgreSQL | connect, cursor, commit/rollback, CREATE TABLE, %s placeholders, single-value tuple, execute, executemany, fetchone/fetchall/fetchmany, DictCursor, UPDATE, DELETE | 9.4/10 |
| [Day 7](daily-exercises/day7_exercises.py) | Mini ETL Project — pandas + psycopg2 + PostgreSQL | extract/validate/transform/load pipeline, execute_values bulk insert, NaN→None conversion, ON CONFLICT idempotency, two-table pattern (clean + rejected), aggregate reporting queries | 8/10 |

---

## Open Practice Projects Index

| Project | Topic | Dataset | Key Techniques | Status |
|---------|-------|---------|---------------|--------|
| [E-Commerce Massive Pipeline](open_massive_practice/op_massive_ecommerce.py) | Incremental ETL on a large, messy real-world dataset | 500K-row synthetic global orders (2022–2025); 3 overlapping daily batch files | Mixed date format parsing, currency/quantity cleaning, intra-batch dedup, incremental load by primary key, validate + quarantine, post-load aggregate | Complete |

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

### Day 5b — SQLAlchemy Deep Dive: Pipelines & Engines
**Date:** 2026-06-11

**Topics covered:**
- **Engine & connection pooling** — `pool_size`, `max_overflow`, `pool_pre_ping`; why pooling matters in pipelines
- **engine.begin() vs engine.connect()** — auto-commit/rollback vs manual commit; when to use each
- **validate()** — row-level null checks with `.notna().all(axis=1)`; separating null checks from numeric range checks
- **Quarantine pattern** — `pd.concat()` to combine all invalid rows; never silently drop bad data
- **Transform with inner join** — why `how="inner"` is correct; how `how="left"` leaks invalid records via NaN imputation
- **Incremental load** — `if_exists="append"` vs `"replace"`; upsert pattern to avoid duplicates
- **Structured ETL** — full Extract → Validate → Quarantine → Transform → Load pipeline with summary

**Key rules learned:**
- `df[list].notna().all(axis=1)` — correct row-level boolean mask across multiple columns
- Never apply `> 0` to string columns — use separate `numeric_cols` parameter for range checks
- Always `.copy()` inputs in `transform()` — never mutate DataFrames passed as arguments
- `how="inner"` in transform merge — only records valid in **both** sources pass through
- `how="left"` leaks rejected records via NaN imputation — always use inner join in transform
- `pd.concat()` to combine invalid rows from multiple sources — never merge them
- Never silently drop bad rows — always load to a quarantine/rejected table
- `engine.begin()` for DML — auto-commits on success, auto-rolls back on exception

📄 [Full notes](daily-notes/day5b_notes.py) | 📝 [Exercise & evaluation](daily-exercises/day5b_exercises.py)

---

### Day 5c — SQLAlchemy: Pipeline Deep Practice
**Date:** 2026-07-05

**Three progressively harder pipelines:**
- **Pipeline A** — Single-source sales pipeline with validate / transform / load and a post-load aggregate query
- **Pipeline B** — Multi-source orders + customer lookup; matched and unmatched orders split into separate tables
- **Pipeline C** — Incremental load: only new rows inserted per run; existing rows skipped by primary key check

**Topics covered:**
- **Vectorised operations** — `col1 * col2` always preferred over `.apply(axis=1)` for arithmetic
- **Date formatting** — `dt.strftime("%Y-%m")` for "YYYY-MM" strings; `dt.month` returns integers, not strings
- **Engine as parameter** — always pass `engine` into pipeline functions; never rely on global state
- **Left vs inner join in transform** — inner join when both sources must be valid; left join + flag when keeping all primary records
- **Incremental load pattern** — `CREATE TABLE IF NOT EXISTS` + read existing IDs + `~df["id"].isin(ids)` + `if_exists="append"`
- **Pipeline result dict** — returning a summary dict for monitoring and downstream use

**Key rules learned:**
- `dt.strftime("%Y-%m")` → "2024-01" string; `dt.month` → integer 1
- Vectorised column ops are always faster than `.apply(axis=1)` for simple arithmetic
- `CREATE TABLE IF NOT EXISTS` handles the first-run case — no `try/except` needed
- `if_exists="append"` for incremental; `if_exists="replace"` wipes all history — never mix them
- Must run earlier batch first to populate the table before testing the skip/dedup behavior
- Left join + `customer_found` flag = keep all orders, investigate which lookups failed

📄 [Full notes](daily-notes/day5c_notes.py) | 📝 [Exercise & evaluation](daily-exercises/day5c_exercises.py)

---

### Day 5d — ETL Deep Dive: Chunked Loading, Upsert + Audit, Checkpointing
**Date:** 2026-07-12

**Three pipelines covering untouched production ETL patterns:**
- **Pipeline A** — Chunked loading: 200-row CSV processed in chunks of 50; validate each chunk, accumulate counts
- **Pipeline B** — Upsert + audit columns: `INSERT OR REPLACE` with `loaded_at`, `source_file`, `run_id` auto-attached
- **Pipeline C** — Checkpointing: `pipeline_state` table tracks processed files; reruns skip already-completed files

**Topics covered:**
- **Chunked loading** — `pd.read_csv(chunksize=N)` returns an iterator; counters live outside the loop; `if_exists="append"` accumulates across chunks
- **Mask-once pattern** — compute validation mask once, apply with `mask` and `~mask`; never duplicate the condition
- **INSERT OR REPLACE** — SQLite upsert syntax; requires table + PRIMARY KEY to exist first; replaces full row on conflict
- **Audit columns** — `loaded_at`, `source_file`, `run_id` added to every row in Python before the SQL call
- **uuid.uuid4()** — generate one `run_id` per batch, not per row
- **Pipeline state table** — checkpoint pattern: check-before / write-after; `file_name` as PRIMARY KEY
- **Idempotency** — running the pipeline N times produces the same result as running it once
- **os.path.basename()** — portable filename extraction, handles both `/` and `\`

**Key rules learned:**
- `if_exists="append"` on every chunk — `"replace"` wipes all prior chunks
- Counters must be defined outside the loop — inside they reset every iteration
- `CREATE TABLE IF NOT EXISTS` must come before `INSERT OR REPLACE` — raw SQL won't create the table
- PRIMARY KEY on upsert column is mandatory — without it, `INSERT OR REPLACE` cannot dedup
- `df.to_dict(orient="records")` → list of dicts → directly usable by `conn.execute()`
- Write to state table AFTER successful load — never pre-mark as done
- `os.path.basename(filepath)` not `.split("/")[-1]` — portable across OS

📄 [Full notes](daily-notes/day5d_notes.py) | 📝 [Exercise & evaluation](daily-exercises/day5d_exercises.py)

---

### Day 6 — psycopg2: Raw Python to PostgreSQL
**Date:** 2026-07-19

**Topics covered:**
- **psycopg2 vs SQLAlchemy** — psycopg2 is low-level, PostgreSQL-only, full manual control; SQLAlchemy wraps it with higher-level abstractions
- **Connecting** — `psycopg2.connect(**DB)`, cursor creation, always close cursor and connection
- **Commit & rollback** — psycopg2 does NOT auto-commit; every DML/DDL needs `conn.commit()`; `conn.rollback()` undoes everything since last commit
- **DDL** — `CREATE TABLE IF NOT EXISTS` with PostgreSQL types (`SERIAL`, `VARCHAR`, `NUMERIC`, `DATE`)
- **Parameterised queries** — `%s` placeholder (not `:param`, not f-strings); single-value tuple rule: `(value,)` not `(value)`
- **INSERT** — `cursor.execute()` for single row, `cursor.executemany()` for batch
- **SELECT & fetch methods** — `fetchone()`, `fetchall()`, `fetchmany(N)` streaming loop
- **DictCursor** — `cursor_factory=psycopg2.extras.DictCursor` for column-name access instead of index
- **UPDATE & DELETE** — `cur.rowcount` to verify rows affected
- **PostgreSQL return types** — `NUMERIC` → `Decimal`, `DATE` → `datetime.date`

**Key rules learned:**
- psycopg2 does NOT auto-commit — always call `conn.commit()` after DML/DDL
- Every transaction ends with EITHER `commit()` OR `rollback()` — never both in sequence
- `rollback()` closes the transaction — `commit()` after it is a no-op and signals wrong intent
- `%s` placeholder always requires a tuple or list: `(value,)` for one value — bare string iterates its characters
- `executemany()` `rowcount` reports the last statement's count, not cumulative
- Always use `DictCursor` in production — tuple index access breaks when column order changes

📄 [Full notes](daily-notes/day6_notes.py) | 📝 [Exercise & evaluation](daily-exercises/day6_exercises.py)

---

### Day 7 — Mini ETL Project: pandas + psycopg2 + PostgreSQL
**Date:** 2026-07-19

**Topics covered:**
- **Pipeline architecture** — extract → validate → transform → load (clean) → load (rejected) → aggregate → result dict
- **Two-table pattern** — `sales_clean` for valid rows, `sales_rejected` for quarantined invalid rows
- **execute_values** — standalone bulk insert from `psycopg2.extras`; builds one large `INSERT ... VALUES (r1),(r2),...`; much faster than `executemany`
- **Column order alignment** — `df[cols].itertuples()` must list columns in the exact same order as the INSERT statement
- **NaN → None conversion** — `df[cols].astype(object).where(pd.notna(df[cols]), other=None)`; `astype(object)` required to prevent numpy reverting `None` to `NaN` through `itertuples`
- **ON CONFLICT DO NOTHING** — idempotent re-runs; duplicate `order_id`s silently skipped
- **Table definition before INSERT** — `CREATE TABLE IF NOT EXISTS` must run first; psycopg2 has no ORM, no auto-create
- **Derived columns in transform** — `total_price = quantity * unit_price`; `loaded_at` audit timestamp added in Python

**Key rules learned:**
- `execute_values(cur, sql, data)` — standalone function, not `cur.execute_values()`
- `astype(object)` before `where(..., None)` — without it, `itertuples` reads from numpy float64 and converts `None` back to `NaN`
- `ON CONFLICT (pk) DO NOTHING` on both tables — always make pipelines safe to re-run
- Always close `cur` and `conn` in every function — even query-only functions leak connections otherwise
- `~mask` is bitwise NOT on a boolean Series — flips valid rows to get the invalid set

📄 [Full notes](daily-notes/day7_notes.py) | 📝 [Exercise & evaluation](daily-exercises/day7_exercises.py)

---

## Open Practice Project — E-Commerce Massive Pipeline

An open-ended, self-directed practice project built alongside the daily exercises to apply all Phase 1 ETL concepts on a realistic, large-scale dataset.

### Dataset (`datasets/` — not committed, generated locally)

A synthetic **500,000-row global e-commerce orders dataset** (2022–2025) generated with intentional real-world messiness:

| Messiness | Detail |
|-----------|--------|
| ~3% duplicate rows | Same `order_id` re-sent, simulating upstream re-ingestion |
| Missing values | `customer_email` (~7%), `shipping_country` (~3%), `discount_pct`, `coupon_code` |
| Mixed date formats | ISO (`2024-01-15`), US (`01/15/2024`), EU (`15-01-2024`) in the same column |
| Dirty strings | Random ALL CAPS, lowercase, leading/trailing whitespace in names, countries, payment methods |
| Bad numeric values | ~1% negative unit prices, ~0.5% zero prices (data-entry errors) |
| Currency formatting | ~10% of `amount` values have stray `$` signs and commas (e.g. `$1,299.99`) |
| Mixed quantity types | ~5% of `quantity` values stored as strings (e.g. `"5 units"` instead of `5`) |

Three overlapping incremental batch files (`datasets/incremental/`) simulate daily source-system extracts:
- `orders_day1.csv` — order_ids 1–500 (500 rows, all new)
- `orders_day2.csv` — order_ids 401–900 (500 rows: 100 re-sent + 400 new)
- `orders_day3.csv` — order_ids 801–1500 (700 rows: 100 re-sent + 600 new)

### Pipeline (`open_massive_practice/op_massive_ecommerce.py`)

A full production-style incremental ETL pipeline combining all patterns learned across Days 5–5d:

| Stage | What it does |
|-------|-------------|
| **Extract** | Reads a daily batch CSV |
| **Incremental dedup** | `CREATE TABLE IF NOT EXISTS` + `order_id` primary key check — skips already-loaded rows |
| **Intra-batch dedup** | `drop_duplicates(subset="order_id")` — removes duplicates within the incoming batch itself |
| **Date parsing** | `parse_mixed_dates()` — tries ISO, US, EU formats in sequence; leaves unparseable dates as `NaT` |
| **Amount/quantity cleaning** | Strips `$` and commas from `amount`; strips `" units"` suffix from `quantity`; converts both to numeric |
| **Validate** | Row-level null and range checks on `customer_email`, `shipping_country`, `unit_price`, `amount_clean`, `quantity_clean` |
| **Transform** | Normalises casing and whitespace across all string columns |
| **Load** | Valid rows appended to `ecommerce_clean` (incremental); rejected rows to `ecommerce_rejected` |
| **Aggregate** | Post-load `GROUP BY product_category` revenue query to verify the load |

**Target tables in `ecommerce_orders.db`:**
- `ecommerce_clean` — validated, transformed orders (incremental, keyed on `order_id`)
- `ecommerce_rejected` — rows that failed validation with `reject_reason`

**Expected incremental results (correct pipeline):**
```
after day1: 500 rows in ecommerce_clean  (500 new,   0 skipped)
after day2: 900 rows in ecommerce_clean  (400 new, 100 skipped)
after day3: 1500 rows in ecommerce_clean (600 new, 100 skipped)
```

> **Note:** `datasets/` is excluded from version control (local generation only). The pipeline code and DB are committed under `open_massive_practice/`.

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

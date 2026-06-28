"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 5 NOTES
 Topic : SQLAlchemy — Connecting Python to Databases
 Date  : 2026-06-10
=============================================================
"""

from sqlalchemy import create_engine, inspect, text
import pandas as pd


# ══════════════════════════════════════════════════════════
#  TOPIC 1 — THE ENGINE: YOUR DATABASE CONNECTION
# ══════════════════════════════════════════════════════════

# The engine is the single object that manages your database connection.
# Create it once at the top of your script and pass it around.

# SQLite — file-based, zero setup, perfect for local development
engine = create_engine("sqlite:///day5/company.db")

# PostgreSQL — production standard
# engine = create_engine("postgresql://username:password@localhost:5432/dbname")

# MySQL
# engine = create_engine("mysql+pymysql://username:password@localhost/dbname")

# Connection string format:
# dialect+driver://username:password@host:port/database_name

# Engine does NOT open a connection immediately — it's lazy.
# Connections are opened only when you actually run a query.


# ══════════════════════════════════════════════════════════
#  TOPIC 2 — WRITING A DATAFRAME TO A TABLE
# ══════════════════════════════════════════════════════════

df = pd.DataFrame({
    "employee_id": [1, 2, 3],
    "name":        ["Alice", "Bob", "Charlie"],
    "salary":      [95000, 72000, 105000],
})

df.to_sql(
    name="employees",      # table name in the database
    con=engine,            # SQLAlchemy engine
    if_exists="replace",   # what to do if table exists already
    index=False,           # don't write the df row index as a column
)

# if_exists options:
# "replace" → drop table if exists, recreate and insert — safe to run repeatedly
# "append"  → keep existing table, add rows to it
# "fail"    → raise error if table already exists

# RULE: if_exists="replace" is safe to run anytime — it's not a one-time operation


# ══════════════════════════════════════════════════════════
#  TOPIC 3 — READING FROM A DATABASE
# ══════════════════════════════════════════════════════════

# Read full table
df = pd.read_sql("SELECT * FROM employees", con=engine)

# Read with filter
df = pd.read_sql("SELECT name, salary FROM employees WHERE salary > 80000", con=engine)

# Read aggregation
df = pd.read_sql("""
    SELECT department,
           AVG(salary) AS avg_salary,
           MAX(salary) AS max_salary,
           COUNT(*)    AS headcount
    FROM employees
    GROUP BY department
""", con=engine)


# ══════════════════════════════════════════════════════════
#  TOPIC 4 — PARAMETERISED QUERIES (CRITICAL — SECURITY)
# ══════════════════════════════════════════════════════════

# NEVER use f-strings to build SQL — this is SQL injection vulnerability
department = "Engineering"

# ❌ DANGEROUS — SQL injection risk
query = f"SELECT * FROM employees WHERE department = '{department}'"

# ✅ SAFE — parameterised with text() and :param syntax
with engine.connect() as conn:
    result = conn.execute(
        text("SELECT * FROM employees WHERE department = :dept"),
        {"dept": department}
    )
    df = pd.DataFrame(result.fetchall(), columns=result.keys())
# fetchall() and keys() MUST be inside the with block
# The connection closes when the with block exits — accessing result after = error


# ══════════════════════════════════════════════════════════
#  TOPIC 5 — EXECUTING RAW SQL (DDL & DML)
# ══════════════════════════════════════════════════════════

# DDL — create/alter/drop tables
with engine.connect() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS departments (
            dept_id   INTEGER PRIMARY KEY,
            dept_name TEXT NOT NULL
        )
    """))
    conn.commit()   # always commit after DDL or DML

# DML — insert, update, delete
with engine.connect() as conn:
    conn.execute(
        text("INSERT INTO departments (dept_id, dept_name) VALUES (:id, :name)"),
        {"id": 1, "name": "Engineering"}
    )
    conn.commit()

# Batch insert — pass a list of dicts
with engine.connect() as conn:
    conn.execute(
        text("INSERT INTO departments (dept_id, dept_name) VALUES (:id, :name)"),
        [{"id": 2, "name": "Marketing"}, {"id": 3, "name": "HR"}]
    )
    conn.commit()


# ══════════════════════════════════════════════════════════
#  TOPIC 6 — INSPECTING THE DATABASE
# ══════════════════════════════════════════════════════════

inspector = inspect(engine)

print(inspector.get_table_names())            # list all tables
print(inspector.get_columns("employees"))     # columns of a specific table


# ══════════════════════════════════════════════════════════
#  TOPIC 7 — THE ETL PIPELINE PATTERN
# ══════════════════════════════════════════════════════════

# This is the core pattern you will use every day as a data engineer.
# Extract → Transform → Load

def run_pipeline(csv_path, engine, target_table):
    # ── EXTRACT ──────────────────────────────────────────
    df_raw = pd.read_csv(csv_path)

    # ── TRANSFORM ─────────────────────────────────────────
    df_clean = df_raw.copy()                              # always copy, never mutate raw
    df_clean["name"]   = df_clean["name"].str.strip().str.lower()
    df_clean["salary"] = pd.to_numeric(df_clean["salary"], errors="coerce")
    df_clean["salary"] = df_clean["salary"].fillna(df_clean["salary"].median())

    def salary_band(salary):
        if salary >= 90000:   return "high"
        elif salary >= 60000: return "mid"
        else:                 return "low"

    df_clean["salary_band"] = df_clean["salary"].apply(salary_band)

    # ── LOAD ──────────────────────────────────────────────
    df_clean.to_sql(target_table, con=engine, if_exists="replace", index=False)

    cnt = pd.read_sql(f"SELECT COUNT(*) as cnt FROM {target_table}", con=engine)["cnt"][0]
    print(f"Table '{target_table}' loaded with {cnt} rows.")

    return df_clean   # return so caller can inspect the result


# ── Call the pipeline ─────────────────────────────────────
engine = create_engine("sqlite:///day5/pipeline.db")
result = run_pipeline("day5/raw_employees.csv", engine, "employees_enriched")
print(result.head())


# ══════════════════════════════════════════════════════════
#  TOPIC 8 — COMMON MISTAKES
# ══════════════════════════════════════════════════════════

# 1. fetchall() OUTSIDE the with block → ResourceClosedError
#    Fix: always fetch inside the with block

# 2. f-strings in SQL → SQL injection
#    Fix: always use text() + :param syntax

# 3. df_raw read but not used → transforms a different source than intended
#    Fix: transform df_raw, not a fresh DB query

# 4. Comparing number to string in SQL: salary >= '90000'
#    Works in SQLite (type coercion), fails in PostgreSQL
#    Fix: salary >= 90000 (no quotes)

# 5. COUNT(*) on wrong table after load
#    Fix: count the table you just wrote to

# 6. if_exists="replace" commented as "run only once"
#    Fix: it's safe to run repeatedly — that's the point of "replace"


# ══════════════════════════════════════════════════════════
#  DAY 5 — KEY TAKEAWAYS
# ══════════════════════════════════════════════════════════
"""
1.  Engine is created once, reused everywhere — it's lazy (no connection until query)
2.  to_sql(if_exists="replace") is safe to run repeatedly — not a one-time operation
3.  Always fetchall() and keys() INSIDE the with engine.connect() block
4.  NEVER use f-strings in SQL — use text() + :param syntax (SQL injection prevention)
5.  Functions should RETURN DataFrames, not just print them
6.  ETL: Extract from source → Transform in Python → Load to database
7.  Always transform df_raw — don't bypass it and re-query the DB
8.  SQL type comparisons must match column type — no quotes around numbers
9.  Always verify the correct table in COUNT(*) after load
10. Parameterise ALL user-controlled values — :param, never string concatenation
"""

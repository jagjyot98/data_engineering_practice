"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 5
 Topic : SQLAlchemy — Connecting Python to Databases
 Date  : 2026-06-10
=============================================================
"""

from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine("sqlite:///day5/company.db")

employees = [
    {"employee_id": 1,  "name": "Alice",   "department": "Engineering", "salary": 95000,  "experience": 5},
    {"employee_id": 2,  "name": "Bob",     "department": "Marketing",   "salary": 72000,  "experience": 3},
    {"employee_id": 3,  "name": "Charlie", "department": "Engineering", "salary": 105000, "experience": 8},
    {"employee_id": 4,  "name": "Diana",   "department": "HR",          "salary": 68000,  "experience": 2},
    {"employee_id": 5,  "name": "Eve",     "department": "Engineering", "salary": 88000,  "experience": 4},
    {"employee_id": 6,  "name": "Frank",   "department": "Marketing",   "salary": 76000,  "experience": 5},
    {"employee_id": 7,  "name": "Grace",   "department": "HR",          "salary": 71000,  "experience": 4},
    {"employee_id": 8,  "name": "Henry",   "department": "Engineering", "salary": 112000, "experience": 10},
    {"employee_id": 9,  "name": "Iris",    "department": "Marketing",   "salary": 69000,  "experience": 2},
    {"employee_id": 10, "name": "Jack",    "department": "HR",          "salary": 74000,  "experience": 6},
]

df = pd.DataFrame(employees)


# ── EXERCISE 1 — Write to database ───────────────────────

df.to_sql(
    name="employees",
    con=engine,
    if_exists="replace",   # safe to run repeatedly — drops and recreates each time
    index=False,
)
print(f"Table 'employees' loaded with {pd.read_sql('SELECT COUNT(*) as cnt FROM employees', con=engine)['cnt'][0]} rows.")


# ── EXERCISE 2 — Read from database ──────────────────────

df_verify = pd.read_sql("SELECT * FROM employees", con=engine)
print(df_verify.shape)

df_salary_filtered = pd.read_sql("SELECT name, salary FROM employees WHERE salary > 80000", con=engine)
print(df_salary_filtered)


# ── EXERCISE 3 — Parameterised query ─────────────────────

# ✅ FIXED: fetchall() and keys() moved INSIDE the with block
def get_employees_by_dept(engine, department):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM employees WHERE department = :department"),
            {"department": department}
        )
        df = pd.DataFrame(result.fetchall(), columns=result.keys())  # ✅ inside with
    return df   # ✅ return df, don't just print

print(get_employees_by_dept(engine, "Engineering"))


# ── EXERCISE 4 — Aggregation in SQL ──────────────────────

df_department_aggregates = pd.read_sql("""
    SELECT department,
           AVG(salary) AS avg_salary,
           MAX(salary) AS max_salary,
           COUNT(*)    AS headcount
    FROM employees
    GROUP BY department
""", con=engine)
print(df_department_aggregates)


# ── EXERCISE 5 — Full ETL pipeline ───────────────────────

df.to_csv("day5/raw_employees.csv", index=False)

# ✅ FIXED: df_raw used for transform, not bypassed
def run_pipeline(csv_path, engine):
    df_raw = pd.read_csv(csv_path)                    # Extract

    def salary_band(salary):                          # Transform
        if salary >= 90000:   return "high"
        elif salary >= 60000: return "mid"
        else:                 return "low"

    df_enriched = df_raw.copy()
    df_enriched["salary_band"] = df_enriched["salary"].apply(salary_band)

    df_enriched.to_sql(                               # Load
        name="employees_enriched",
        con=engine,
        if_exists="replace",
        index=False,
    )

    cnt = pd.read_sql(                                # ✅ FIXED: count correct table
        "SELECT COUNT(*) as cnt FROM employees_enriched", con=engine
    )["cnt"][0]
    print(f"Table 'employees_enriched' loaded with {cnt} rows.")

run_pipeline("day5/raw_employees.csv", engine)


# ══════════════════════════════════════════════════════════
#  EVALUATION & REVIEW
# ══════════════════════════════════════════════════════════
"""
SCORE: 7.5 / 10

EXERCISE 1 — ✅ PERFECT
  + to_sql() parameters all correct
  + COUNT(*) confirmation pattern correct
  ~ Comment "Run only once" is a misconception — if_exists="replace" is safe to run anytime

EXERCISE 2 — ✅ PERFECT
  + pd.read_sql() for full table read correct
  + Filtered SQL query correct

EXERCISE 3 — ❌ CRITICAL BUG
  ❌ result.fetchall() and result.keys() called OUTSIDE the with block
     Connection is already closed — raises ResourceClosedError
  ❌ Function only prints, doesn't return df — callers can't use the data
  ✅ Fix: move fetchall()/keys() inside with block, return the DataFrame

EXERCISE 4 — ✅ PERFECT
  + SQL GROUP BY aggregation correct
  + pd.read_sql() used correctly
  + Strong SQL skills applied correctly

EXERCISE 5 — ⚠️ MULTIPLE ISSUES
  ❌ df_raw read from CSV but never used — queried DB instead (bypassed the ETL transform)
  ❌ salary >= '90000' — comparing number to string literal (wrong type)
     Works in SQLite via coercion, fails in PostgreSQL
  ❌ Count query checked employees table, not employees_enriched
  ✅ to_sql() parameters correct
  ✅ if_exists="replace" correct

KEY TAKEAWAYS:
  1. Always fetchall() and keys() INSIDE the with engine.connect() block
  2. Functions should RETURN DataFrames, not just print them
  3. ETL: transform the data YOU EXTRACTED, don't bypass and query DB
  4. SQL CASE WHEN comparisons must match column type — no quotes on numbers
  5. Always verify the correct table in COUNT(*) after load
  6. if_exists="replace" is safe to run repeatedly — remove "run only once" thinking
"""

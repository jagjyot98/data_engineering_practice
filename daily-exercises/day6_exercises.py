"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 6
 Topic : psycopg2 — Raw Python to PostgreSQL
 Date  : 2026-07-19
=============================================================

 Connection details (local PostgreSQL 17):
   host     = localhost
   port     = 5432
   dbname   = postgres
   user     = postgres
   password = root

 psycopg2 vs SQLAlchemy:
   SQLAlchemy  → high-level ORM/toolkit, abstracts SQL, creates tables auto
   psycopg2    → low-level DB-API adapter, raw SQL only, full manual control
   In real pipelines: psycopg2 for performance-critical raw SQL;
                      SQLAlchemy for general ETL and ORM work
=============================================================
"""

import psycopg2
import psycopg2.extras
from datetime import datetime

DB = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "postgres",
    "user":     "postgres",
    "password": "root",
}

def log(step, message, rows=None):
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_info = f"{rows}" if rows is not None else ""
    print(f"[{ts}] [{step}] {message}{row_info}")


# ══════════════════════════════════════════════════════════
#  EXERCISE 1 — CONNECT AND CREATE A TABLE
# ══════════════════════════════════════════════════════════

conn = psycopg2.connect(**DB)
cur  = conn.cursor()

cur.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id  SERIAL PRIMARY KEY,
        name         VARCHAR(100) NOT NULL,
        department   VARCHAR(100),
        salary       NUMERIC(10,2),
        hire_date    DATE
    )
""")
conn.commit()
log("TABLE", "Table 'employees' created")
cur.close()
conn.close()


# ══════════════════════════════════════════════════════════
#  EXERCISE 1 — OUTPUT (VERIFIED)
# ══════════════════════════════════════════════════════════
"""
[2026-07-19 00:02:23] [TABLE] Table 'employees' created
"""


# ══════════════════════════════════════════════════════════
#  EXERCISE 1 — EVALUATION
# ══════════════════════════════════════════════════════════
"""
SCORE: 10/10
- Table created with correct columns and types
- conn.commit() called after DDL
- cur.close() and conn.close() called — clean teardown
"""


# ══════════════════════════════════════════════════════════
#  EXERCISE 2 — INSERT ROWS (single + batch)
# ══════════════════════════════════════════════════════════

conn = psycopg2.connect(**DB)
cur  = conn.cursor()

cur.execute(
    "INSERT INTO employees (employee_id, name, department, salary, hire_date) VALUES (%s, %s, %s, %s, %s)",
    (1, "Alice Smith", "Engineering", 95000.00, "2021-03-15")
)
log("INSERT", "Rows inserted into employees: ", cur.rowcount)
conn.commit()

employees = [
    (2, "Bob Jones",     "Marketing",   72000.00,  "2020-07-01"),
    (3, "Charlie Brown", "Engineering", 105000.00, "2019-11-20"),
    (4, "Diana Prince",  "HR",          68000.00,  "2022-01-10"),
    (5, "Eve Adams",     "Engineering", 88000.00,  "2018-05-30"),
]
cur.executemany(
    "INSERT INTO employees (employee_id, name, department, salary, hire_date) VALUES (%s, %s, %s, %s, %s)",
    employees
)
log("INSERT", "Rows inserted into employees: ", cur.rowcount)
conn.commit()

cur.close()
conn.close()


# ══════════════════════════════════════════════════════════
#  EXERCISE 2 — OUTPUT (VERIFIED)
# ══════════════════════════════════════════════════════════
"""
[2026-07-19 00:02:23] [INSERT] Rows inserted into employees: 1
[2026-07-19 00:02:23] [INSERT] Rows inserted into employees: 4
"""


# ══════════════════════════════════════════════════════════
#  EXERCISE 2 — EVALUATION
# ══════════════════════════════════════════════════════════
"""
SCORE: 9/10

ITERATION 1 — BUGS FOUND & FIXED:

BUG 1 — Eve (employee_id 5) missing from executemany list
  ❌ Only 3 employees in batch — Eve omitted
  ✅ Added (5, 'Eve Adams', 'Engineering', 88000.00, '2018-05-30') to list
  Impact: Exercise 5's DELETE WHERE employee_id = 5 returned 0 rows

NOTE — cur.rowcount after executemany
  executemany() reports rowcount of the LAST statement only (4 here, not cumulative).
  This is psycopg2 behaviour — not a bug in the code.
"""


# ══════════════════════════════════════════════════════════
#  EXERCISE 3 — FETCH RESULTS (fetchone, fetchall, fetchmany)
# ══════════════════════════════════════════════════════════

conn = psycopg2.connect(**DB)
cur  = conn.cursor()

cur.execute("SELECT * FROM employees")
log("FETCH", "Printing all rows from employees:")
for row in cur.fetchall():
    print(row)

cur.execute("SELECT * FROM employees ORDER BY salary DESC LIMIT 1")
log("FETCH", "Fetching row for Highest Earner:")
print(cur.fetchone())

depart = "Engineering"
cur.execute("SELECT * FROM employees WHERE department = %s", (depart,))
log("FETCH", "Fetching rows for engineering department:")
while True:
    batch = cur.fetchmany(2)
    if not batch:
        break
    for row in batch:
        print(row)

cur.close()
conn.close()


# ══════════════════════════════════════════════════════════
#  EXERCISE 3 — OUTPUT (VERIFIED)
# ══════════════════════════════════════════════════════════
"""
[FETCH] Printing all rows from employees:
(1, 'Alice Smith', 'Engineering', Decimal('95000.00'), datetime.date(2021, 3, 15))
(2, 'Bob Jones', 'Marketing', Decimal('72000.00'), datetime.date(2020, 7, 1))
(3, 'Charlie Brown', 'Engineering', Decimal('105000.00'), datetime.date(2019, 11, 20))
(4, 'Diana Prince', 'HR', Decimal('68000.00'), datetime.date(2022, 1, 10))
(5, 'Eve Adams', 'Engineering', Decimal('88000.00'), datetime.date(2018, 5, 30))

[FETCH] Fetching row for Highest Earner:
(3, 'Charlie Brown', 'Engineering', Decimal('105000.00'), datetime.date(2019, 11, 20))

[FETCH] Fetching rows for engineering department:
(1, 'Alice Smith', ...)
(3, 'Charlie Brown', ...)
(5, 'Eve Adams', ...)

NOTE — PostgreSQL returns Python types automatically:
  NUMERIC(10,2) → Decimal('95000.00')   (exact, not float)
  DATE          → datetime.date(2021, 3, 15)
"""


# ══════════════════════════════════════════════════════════
#  EXERCISE 3 — EVALUATION
# ══════════════════════════════════════════════════════════
"""
SCORE: 10/10

ITERATION 1 — BUG FIXED:
  ❌ cur.execute("... WHERE department = %s", depart)
     Passing a bare string — psycopg2 iterates its characters → TypeError
  ✅ cur.execute("... WHERE department = %s", (depart,))
     Single-value tuple — trailing comma required

KEY RULE: params must always be a tuple or list, even for one value.
  ("Engineering")   → just a string in parentheses — NOT a tuple
  ("Engineering",)  → one-element tuple — the comma makes the difference
"""


# ══════════════════════════════════════════════════════════
#  EXERCISE 4 — DictCursor
# ══════════════════════════════════════════════════════════

conn = psycopg2.connect(**DB)
cur  = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)

cur.execute("SELECT * FROM employees")
log("FETCH", "Fetching all rows from employees (as Dictionary):")
for row in cur.fetchall():
    print(row["name"], row["salary"])

cur.close()
conn.close()


# ══════════════════════════════════════════════════════════
#  EXERCISE 4 — OUTPUT (VERIFIED)
# ══════════════════════════════════════════════════════════
"""
[FETCH] Fetching all rows from employees (as Dictionary):
Alice Smith 95000.00
Bob Jones 72000.00
Charlie Brown 105000.00
Diana Prince 68000.00
Eve Adams 88000.00
"""


# ══════════════════════════════════════════════════════════
#  EXERCISE 4 — EVALUATION
# ══════════════════════════════════════════════════════════
"""
SCORE: 10/10
- DictCursor correctly passed as cursor_factory
- Columns accessed by name (row["name"], row["salary"]) not by index
- Clean connection open/close
"""


# ══════════════════════════════════════════════════════════
#  EXERCISE 5 — UPDATE, DELETE & ROLLBACK
# ══════════════════════════════════════════════════════════

conn = psycopg2.connect(**DB)
cur  = conn.cursor()

name = "Alice Smith"
cur.execute("SELECT * FROM employees WHERE name = %s", (name,))
log("FETCH", f"Salary for '{name}' BEFORE update: {cur.fetchone()}")

new_sal = 102000.00
cur.execute("UPDATE employees SET salary = %s WHERE name = %s", (new_sal, name))
conn.commit()
log("UPDATE", f"Salary for '{name}' updated to {new_sal}")

cur.execute("SELECT * FROM employees WHERE name = %s", (name,))
log("FETCH", f"Salary for '{name}' AFTER update: {cur.fetchone()}")

emp_id_delete = 5
cur.execute("DELETE FROM employees WHERE employee_id = %s", (emp_id_delete,))
log("DELETE", f"Row deleted for employee_id: {emp_id_delete}")
conn.commit()

# Rollback demo — update Bob then roll back
name = "Bob Jones"
cur.execute("UPDATE employees SET salary = %s WHERE name = %s", (999999.00, name))
conn.rollback()   # undoes the update — no commit after rollback

cur.execute("SELECT salary FROM employees WHERE name = %s", (name,))
log("FETCH", f"Bob's salary after rollback: {cur.fetchone()[0]}")
print("Rollback confirmed — Bob's salary unchanged.")

cur.close()
conn.close()


# ══════════════════════════════════════════════════════════
#  EXERCISE 5 — OUTPUT (VERIFIED)
# ══════════════════════════════════════════════════════════
"""
[FETCH] Salary for 'Alice Smith' BEFORE update: (1, 'Alice Smith', ..., Decimal('95000.00'), ...)
[UPDATE] Salary for 'Alice Smith' updated to 102000.0
[FETCH] Salary for 'Alice Smith' AFTER update:  (1, 'Alice Smith', ..., Decimal('102000.00'), ...)
[DELETE] Row deleted for employee_id: 5
[FETCH] Bob's salary after rollback: 72000.00
Rollback confirmed — Bob's salary unchanged.
"""


# ══════════════════════════════════════════════════════════
#  EXERCISE 5 — EVALUATION
# ══════════════════════════════════════════════════════════
"""
SCORE: 8/10

ITERATION 1 — BUG:
  ❌ rollback() was missing — file ended after DELETE, rollback never written
  ✅ Added rollback demo block

ITERATION 2 — BUG FIXED:
  ❌ conn.rollback() followed immediately by conn.commit()
     rollback() closes the transaction — nothing left to commit.
     commit() after rollback is a no-op but signals wrong intent.
  ✅ Removed conn.commit() after rollback

KEY RULE: every transaction ends with EITHER commit() OR rollback(), never both.
  rollback() closes the transaction — the slate is clean, no commit needed.

OVERALL DAY 6 SUMMARY:
  Exercise 1 — 10/10  connect, CREATE TABLE, commit, close
  Exercise 2 — 9/10   execute, executemany, %s placeholders, single-value tuple
  Exercise 3 — 10/10  fetchall, fetchone, fetchmany loop, (value,) tuple fix
  Exercise 4 — 10/10  DictCursor, column name access
  Exercise 5 — 8/10   UPDATE, DELETE, rollback — commit-after-rollback bug fixed
"""

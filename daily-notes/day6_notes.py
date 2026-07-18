"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 6 NOTES
 Topic : psycopg2 — Raw Python to PostgreSQL
 Date  : 2026-07-12
=============================================================
"""

import psycopg2
import psycopg2.extras
from datetime import datetime


# ══════════════════════════════════════════════════════════
#  TOPIC 1 — psycopg2 vs SQLAlchemy: WHEN TO USE WHICH
# ══════════════════════════════════════════════════════════

# SQLAlchemy
#   - High-level toolkit + ORM
#   - Creates tables automatically (to_sql, metadata)
#   - Works across multiple databases (SQLite, PostgreSQL, MySQL)
#   - Best for: general ETL pipelines, pandas integration (to_sql, read_sql)

# psycopg2
#   - Low-level DB-API 2.0 adapter — PostgreSQL only
#   - Full manual control over SQL and transactions
#   - Faster for bulk operations and raw SQL workloads
#   - Best for: production PostgreSQL pipelines, performance-critical inserts,
#               raw DDL/DML that needs explicit transaction control

# In practice: both are used together.
# psycopg2 for raw operations; SQLAlchemy engine wraps psycopg2 under the hood.


# ══════════════════════════════════════════════════════════
#  TOPIC 2 — CONNECTING TO POSTGRESQL
# ══════════════════════════════════════════════════════════

# Connection parameters
DB = {
    "host":     "localhost",
    "port":     5432,         # PostgreSQL default port
    "dbname":   "postgres",   # database name
    "user":     "postgres",   # login role
    "password": "root",
}

# Method 1 — keyword arguments (readable, recommended)
conn = psycopg2.connect(**DB)

# Method 2 — connection string (DSN)
conn = psycopg2.connect("host=localhost port=5432 dbname=postgres user=postgres password=root")

# Method 3 — URI format (same as SQLAlchemy engine string)
conn = psycopg2.connect("postgresql://postgres:root@localhost:5432/postgres")

# Always close the connection when done
conn.close()

# Better: use a context manager — auto-closes on exit
with psycopg2.connect(**DB) as conn:
    pass   # connection auto-closes here

# NOTE: psycopg2's context manager commits on clean exit, rolls back on exception.
# The connection itself is NOT closed — you must close it separately if needed.
# For simplicity in scripts, just call conn.close() at the end.


# ══════════════════════════════════════════════════════════
#  TOPIC 3 — CURSOR: YOUR QUERY EXECUTOR
# ══════════════════════════════════════════════════════════

# The cursor is the object you use to send SQL to PostgreSQL.
# One connection can have multiple cursors open at the same time.

conn = psycopg2.connect(**DB)
cur = conn.cursor()           # default cursor — returns tuples

# Always close cursor AND connection when done
cur.close()
conn.close()

# Cursor useful attributes after execute():
# cur.rowcount      → number of rows affected by last INSERT/UPDATE/DELETE
# cur.description   → column metadata (name, type code, etc.) after SELECT
# cur.statusmessage → PostgreSQL status string e.g. "INSERT 0 3"


# ══════════════════════════════════════════════════════════
#  TOPIC 4 — COMMIT AND ROLLBACK (CRITICAL)
# ══════════════════════════════════════════════════════════

# psycopg2 opens every connection in a TRANSACTION automatically.
# Nothing is saved to the database until you call conn.commit().
# If you close without committing, PostgreSQL rolls back ALL changes.

conn = psycopg2.connect(**DB)
cur  = conn.cursor()

cur.execute("INSERT INTO employees (name) VALUES (%s)", ("Alice",))
# At this point, Alice is NOT in the database yet — she's in a pending transaction.

conn.commit()    # NOW Alice is saved permanently
# conn.rollback()  # would undo the insert instead

cur.close()
conn.close()

# RULE: Every DDL (CREATE/DROP/ALTER) and DML (INSERT/UPDATE/DELETE) needs a commit.
# SELECT queries do NOT need a commit.

# Autocommit mode — turns off transaction wrapping (needed for CREATE DATABASE etc.)
conn = psycopg2.connect(**DB)
conn.autocommit = True   # each statement commits immediately
cur = conn.cursor()
cur.execute("CREATE DATABASE mydb")   # would fail inside a transaction block
conn.autocommit = False  # turn back off
conn.close()


# ══════════════════════════════════════════════════════════
#  TOPIC 5 — DDL: CREATE, DROP, ALTER TABLES
# ══════════════════════════════════════════════════════════

conn = psycopg2.connect(**DB)
cur  = conn.cursor()

# Create table — PostgreSQL data types
cur.execute("""
    CREATE TABLE IF NOT EXISTS employees (
        employee_id  SERIAL PRIMARY KEY,      -- auto-increment integer (no need to insert this)
        name         VARCHAR(100) NOT NULL,   -- variable-length string, max 100 chars
        department   VARCHAR(100),
        salary       NUMERIC(10, 2),          -- 10 total digits, 2 decimal places
        hire_date    DATE,                    -- date only, no time
        created_at   TIMESTAMP DEFAULT NOW()  -- auto-set to current time on insert
    )
""")
conn.commit()

# PostgreSQL data types quick reference:
# INTEGER / BIGINT          → whole numbers (BIGINT for very large)
# NUMERIC(p, s)             → exact decimal (use for money — never FLOAT)
# VARCHAR(n)                → variable string up to n chars
# TEXT                      → unlimited string length
# BOOLEAN                   → True / False
# DATE                      → date only (2024-01-15)
# TIMESTAMP                 → date + time (2024-01-15 10:30:00)
# SERIAL / BIGSERIAL        → auto-increment integer (PostgreSQL shorthand)
# UUID                      → universally unique identifier

# Drop table
cur.execute("DROP TABLE IF EXISTS employees")
conn.commit()

cur.close()
conn.close()


# ══════════════════════════════════════════════════════════
#  TOPIC 6 — PARAMETERISED QUERIES (CRITICAL — SECURITY)
# ══════════════════════════════════════════════════════════

conn = psycopg2.connect(**DB)
cur  = conn.cursor()

# ❌ NEVER use f-strings or string concatenation in SQL — SQL injection risk
name = "Alice'; DROP TABLE employees; --"
cur.execute(f"SELECT * FROM employees WHERE name = '{name}'")   # DANGEROUS

# ✅ ALWAYS use %s placeholders — psycopg2 escapes values safely
cur.execute("SELECT * FROM employees WHERE name = %s", (name,))

# Note the tuple syntax — even for a single value, pass a tuple: (value,)
# NOT:  cur.execute("... WHERE name = %s", name)        ← wrong, iterates string
# YES:  cur.execute("... WHERE name = %s", (name,))     ← correct

# Multiple placeholders
cur.execute(
    "SELECT * FROM employees WHERE department = %s AND salary > %s",
    ("Engineering", 80000)
)

# Named placeholders with %(name)s (alternative style)
cur.execute(
    "SELECT * FROM employees WHERE department = %(dept)s AND salary > %(sal)s",
    {"dept": "Engineering", "sal": 80000}
)

cur.close()
conn.close()

# RULE: %s in psycopg2 = :param in SQLAlchemy = ? in sqlite3
# The adapter handles quoting and escaping — you never build SQL strings manually.


# ══════════════════════════════════════════════════════════
#  TOPIC 7 — INSERT: single row, batch, RETURNING
# ══════════════════════════════════════════════════════════

conn = psycopg2.connect(**DB)
cur  = conn.cursor()

# Single row insert
cur.execute(
    "INSERT INTO employees (name, department, salary, hire_date) VALUES (%s, %s, %s, %s)",
    ("Alice Smith", "Engineering", 95000.00, "2021-03-15")
)
print("Rows inserted:", cur.rowcount)   # → 1
conn.commit()

# Batch insert — executemany() runs the same statement for each tuple
employees = [
    ("Bob Jones",     "Marketing",   72000.00, "2020-07-01"),
    ("Charlie Brown", "Engineering", 105000.00, "2019-11-20"),
    ("Diana Prince",  "HR",          68000.00,  "2022-01-10"),
]
cur.executemany(
    "INSERT INTO employees (name, department, salary, hire_date) VALUES (%s, %s, %s, %s)",
    employees
)
print("Batch rows inserted:", cur.rowcount)   # → 3
conn.commit()

# RETURNING — get back the auto-generated primary key after insert
cur.execute(
    "INSERT INTO employees (name, department, salary) VALUES (%s, %s, %s) RETURNING employee_id",
    ("Eve Adams", "Engineering", 88000.00)
)
new_id = cur.fetchone()[0]
print("New employee_id:", new_id)   # → auto-generated integer
conn.commit()

cur.close()
conn.close()


# ══════════════════════════════════════════════════════════
#  TOPIC 8 — SELECT: fetchone, fetchall, fetchmany
# ══════════════════════════════════════════════════════════

conn = psycopg2.connect(**DB)
cur  = conn.cursor()

# fetchall() — all rows at once, as list of tuples
cur.execute("SELECT * FROM employees ORDER BY salary DESC")
rows = cur.fetchall()
for row in rows:
    print(row)            # (1, 'Alice Smith', 'Engineering', 95000.00, ...)

# fetchone() — single row (next row in result set), or None if no more
cur.execute("SELECT * FROM employees ORDER BY salary DESC LIMIT 1")
top_earner = cur.fetchone()
print("Top earner:", top_earner)

# fetchmany(N) — next N rows; returns empty list when exhausted
cur.execute("SELECT * FROM employees WHERE department = 'Engineering'")
while True:
    batch = cur.fetchmany(2)    # get 2 rows at a time
    if not batch:
        break
    for row in batch:
        print(row)

# cur.description — column names after a SELECT
cur.execute("SELECT name, salary FROM employees")
col_names = [desc[0] for desc in cur.description]
print("Columns:", col_names)    # → ['name', 'salary']

cur.close()
conn.close()

# WHEN TO USE WHICH:
# fetchall()   → small result sets (fits in memory)
# fetchone()   → single row lookups (COUNT, MAX, specific record)
# fetchmany(N) → large result sets you want to stream in batches


# ══════════════════════════════════════════════════════════
#  TOPIC 9 — DictCursor: results as dicts, not tuples
# ══════════════════════════════════════════════════════════

conn = psycopg2.connect(**DB)

# Default cursor — returns tuples, access by index
cur = conn.cursor()
cur.execute("SELECT name, salary FROM employees WHERE employee_id = 1")
row = cur.fetchone()
print(row[0], row[1])    # fragile — what is index 0? what is index 1?

# DictCursor — returns dict-like rows, access by column name
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cur.execute("SELECT name, salary FROM employees WHERE employee_id = 1")
row = cur.fetchone()
print(row["name"], row["salary"])   # explicit, safe, readable

# RealDictCursor — returns actual Python dicts (not just dict-like)
cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
cur.execute("SELECT * FROM employees")
rows = cur.fetchall()
for row in rows:
    print(dict(row))    # converts to regular Python dict

cur.close()
conn.close()

# RULE: always use DictCursor or RealDictCursor in production.
# Tuple index access breaks silently when column order changes.


# ══════════════════════════════════════════════════════════
#  TOPIC 10 — UPDATE AND DELETE
# ══════════════════════════════════════════════════════════

conn = psycopg2.connect(**DB)
cur  = conn.cursor()

# UPDATE — always use WHERE or you update every row
cur.execute(
    "UPDATE employees SET salary = %s WHERE name = %s",
    (102000.00, "Alice Smith")
)
print("Rows updated:", cur.rowcount)   # → 1
conn.commit()

# UPDATE with RETURNING — get the updated values back
cur.execute(
    "UPDATE employees SET salary = salary * 1.10 WHERE department = %s RETURNING name, salary",
    ("Engineering",)
)
updated = cur.fetchall()
for name, new_salary in updated:
    print(f"{name} → {new_salary}")
conn.commit()

# DELETE
cur.execute("DELETE FROM employees WHERE employee_id = %s", (5,))
print("Rows deleted:", cur.rowcount)   # → 1
conn.commit()

cur.close()
conn.close()


# ══════════════════════════════════════════════════════════
#  TOPIC 11 — ROLLBACK: UNDOING UNCOMMITTED CHANGES
# ══════════════════════════════════════════════════════════

conn = psycopg2.connect(**DB)
cur  = conn.cursor()

# Check current salary
cur.execute("SELECT salary FROM employees WHERE name = %s", ("Bob Jones",))
print("Before:", cur.fetchone()[0])    # → 72000.00

# Make a change
cur.execute(
    "UPDATE employees SET salary = %s WHERE name = %s",
    (999999.00, "Bob Jones")
)

# Oops — this was a mistake. Rollback undoes everything since the last commit.
conn.rollback()

# Verify — salary must be unchanged
cur.execute("SELECT salary FROM employees WHERE name = %s", ("Bob Jones",))
print("After rollback:", cur.fetchone()[0])    # → 72000.00 (unchanged)

cur.close()
conn.close()

# RULE: rollback() undoes ALL changes since the last commit().
# Use it in error-handling: if something goes wrong mid-pipeline,
# rollback so you don't leave the database in a half-updated state.

# ❌ WRONG — rollback() immediately followed by commit()
cur.execute("UPDATE employees SET salary = %s WHERE name = %s", (999999.00, "Bob Jones"))
conn.rollback()   # undoes the update — transaction is now closed
conn.commit()     # no-op here, but signals wrong intent — nothing left to commit
                  # in a real pipeline this pattern causes confusion about what was saved

# ✅ CORRECT — rollback OR commit, never both in sequence
cur.execute("UPDATE employees SET salary = %s WHERE name = %s", (999999.00, "Bob Jones"))
conn.rollback()   # done — the update is gone, no commit needed or wanted

# WHY: rollback() closes the current transaction and starts a fresh one.
# There is nothing pending after a rollback — commit() after it is meaningless.
# The rule is: every transaction ends with EITHER commit() OR rollback(), not both.

# Pattern used in production error handling:
conn = psycopg2.connect(**DB)
cur  = conn.cursor()
try:
    cur.execute("INSERT INTO employees (name, salary) VALUES (%s, %s)", ("Test", 50000))
    cur.execute("UPDATE employees SET salary = %s WHERE name = %s", (55000, "Test"))
    conn.commit()    # both succeed → commit both
    print("Transaction committed.")
except Exception as e:
    conn.rollback()  # either failed → undo both
    print(f"Transaction rolled back: {e}")
finally:
    cur.close()
    conn.close()


# ══════════════════════════════════════════════════════════
#  TOPIC 12 — COMMON psycopg2 ERRORS
# ══════════════════════════════════════════════════════════

# 1. OperationalError — cannot connect (wrong host/port/password/DB not running)
#    psycopg2.OperationalError: connection to server at "localhost" failed

# 2. ProgrammingError — bad SQL (wrong table name, wrong column, syntax error)
#    psycopg2.errors.UndefinedTable: relation "employes" does not exist

# 3. UniqueViolation — inserting a duplicate primary key or unique value
#    psycopg2.errors.UniqueViolation: duplicate key value violates unique constraint

# 4. NotNullViolation — inserting NULL into a NOT NULL column
#    psycopg2.errors.NotNullViolation: null value in column "name" violates not-null constraint

# 5. InFailedSqlTransaction — running a query after an error without rollback
#    psycopg2.errors.InFailedSqlTransaction: current transaction is aborted
#    Fix: always conn.rollback() after catching an exception before retrying

# After ANY exception in psycopg2, you MUST rollback before the connection
# can be used again. The connection stays in an error state until you do.


# ══════════════════════════════════════════════════════════
#  TOPIC 13 — FULL PATTERN: psycopg2 PIPELINE FUNCTION
# ══════════════════════════════════════════════════════════

def run_pg_pipeline(employees_data, db_config):
    conn = psycopg2.connect(**db_config)
    cur  = conn.cursor()
    try:
        # DDL
        cur.execute("""
            CREATE TABLE IF NOT EXISTS employees (
                employee_id SERIAL PRIMARY KEY,
                name        VARCHAR(100) NOT NULL,
                department  VARCHAR(100),
                salary      NUMERIC(10,2),
                hire_date   DATE
            )
        """)

        # Batch insert
        cur.executemany(
            "INSERT INTO employees (name, department, salary, hire_date) VALUES (%s,%s,%s,%s)",
            employees_data
        )
        conn.commit()
        print(f"Inserted {cur.rowcount} rows.")

        # Read back with DictCursor
        cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
        cur.execute("SELECT name, salary FROM employees ORDER BY salary DESC")
        for row in cur.fetchall():
            print(f"  {row['name']:20s}  {row['salary']}")

    except Exception as e:
        conn.rollback()
        print(f"Pipeline failed, rolled back: {e}")
    finally:
        cur.close()
        conn.close()


# ══════════════════════════════════════════════════════════
#  DAY 6 — KEY TAKEAWAYS
# ══════════════════════════════════════════════════════════
"""
1.  psycopg2 = low-level PostgreSQL adapter; SQLAlchemy = high-level toolkit that wraps it
2.  psycopg2.connect(**DB) opens a connection; always close with conn.close()
3.  conn.cursor() creates a cursor — the object that executes SQL
4.  psycopg2 does NOT auto-commit — you MUST call conn.commit() after DML/DDL
5.  conn.rollback() undoes all changes since the last commit
6.  %s is the placeholder in psycopg2 (NOT :param, NOT ?, NOT f-strings)
7.  Single-value tuple: always write (value,) not (value) — trailing comma required
8.  cursor.execute(sql, params)        → single row
    cursor.executemany(sql, list)      → batch of rows (same SQL, many param sets)
9.  fetchone()   → one row (or None)
    fetchall()   → all rows as list of tuples
    fetchmany(N) → next N rows (for streaming large results)
10. DictCursor / RealDictCursor → access rows by column name, not index
11. RETURNING clause → get auto-generated values (SERIAL id) back after INSERT
12. After ANY exception, call rollback() before reusing the connection
13. NUMERIC(p,s) for money — never FLOAT (floating point rounding errors)
14. SERIAL PRIMARY KEY = auto-increment integer, PostgreSQL shorthand
15. cur.rowcount → rows affected by last INSERT/UPDATE/DELETE
    cur.description → column metadata (name, type) after SELECT
"""

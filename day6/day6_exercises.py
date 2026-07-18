"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 6
 Topic : psycopg2 — Raw Python to PostgreSQL
 Date  : 2026-07-12
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
import psycopg2.extras    # for DictCursor
from datetime import datetime

DB = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "postgres",
    "user":     "postgres",
    "password": "root",
}

def log(step, message, rows=None):                      #for creating pipeline logs
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_info = f"{rows}" if rows is not None else ""
    print(f"[{ts}] [{step}] {message}{row_info}")



# ══════════════════════════════════════════════════════════
#  EXERCISE 1 — CONNECT AND CREATE A TABLE
#
#  Task:
#  1. Open a connection using psycopg2.connect(**DB)
#  2. Get a cursor with conn.cursor()
#  3. Execute a CREATE TABLE IF NOT EXISTS for 'employees':
#       employee_id  SERIAL PRIMARY KEY
#       name         VARCHAR(100) NOT NULL
#       department   VARCHAR(100)
#       salary       NUMERIC(10,2)
#       hire_date    DATE
#  4. commit() the transaction
#  5. Print "Table created."
#  6. Close cursor and connection
#
#  Key difference from SQLAlchemy:
#  psycopg2 does NOT auto-commit — you must call conn.commit()
#  after every DDL or DML statement, or changes are rolled back.
# ══════════════════════════════════════════════════════════

# YOUR CODE HERE
conn = psycopg2.connect(**DB)
cur = conn.cursor()
                                    #employees table creation
cur.execute("""                         
    CREATE TABLE IF NOT EXISTS employees (
            employee_id  SERIAL PRIMARY KEY,
            name VARCHAR(100) NOT NULL,
            department  VARCHAR(100),
            salary  NUMERIC(10,2),
            hire_date DATE
            )
      """)
conn.commit()
log("TABLE","Table 'employees' Created")
cur.close()
conn.close()


# ══════════════════════════════════════════════════════════
#  EXERCISE 2 — INSERT ROWS (single + batch)
#
#  Task:
#  1. Insert ONE employee using cursor.execute() with %s placeholders:
#       (1, 'Alice Smith', 'Engineering', 95000.00, '2021-03-15')
#
#  2. Insert MULTIPLE employees at once using cursor.executemany():
#       (2, 'Bob Jones',     'Marketing',   72000.00, '2020-07-01')
#       (3, 'Charlie Brown', 'Engineering', 105000.00, '2019-11-20')
#       (4, 'Diana Prince',  'HR',          68000.00, '2022-01-10')
#       (5, 'Eve Adams',     'Engineering', 88000.00, '2018-05-30')
#
#  3. commit() after both inserts
#  4. Print "Rows inserted."
#
#  IMPORTANT — parameterised query syntax in psycopg2:
#  Use %s placeholders (NOT :param like SQLAlchemy, NOT f-strings)
#
#  cursor.execute(
#      "INSERT INTO employees VALUES (%s, %s, %s, %s, %s)",
#      (1, 'Alice', 'Engineering', 95000.00, '2021-03-15')
#  )
#
#  cursor.executemany(
#      "INSERT INTO employees VALUES (%s, %s, %s, %s, %s)",
#      list_of_tuples
#  )
# ══════════════════════════════════════════════════════════

# YOUR CODE HERE
conn = psycopg2.connect(**DB)
cur = conn.cursor()
                                #Inserting single entry into the table 'employees' 
cur.execute(
    "INSERT INTO employees (employee_id, name, department, salary, hire_date) VALUES (%s, %s, %s, %s, %s)",
    (1, 'Alice Smith', 'Engineering', 95000.00, '2021-03-15')
)
log("INSERT","Rows inserted into employees: ",cur.rowcount)
conn.commit()


employees = [
    (2, "Bob Jones",     "Marketing",   72000.00, "2020-07-01"),
    (3, "Charlie Brown", "Engineering", 105000.00, "2019-11-20"),
    (4, "Diana Prince",  "HR",          68000.00,  "2022-01-10"),
    (5, 'Eve Adams',     'Engineering', 88000.00, '2018-05-30')
    
]               
                                #Inserting multiple entries into table "employees"
cur.executemany(
    "INSERT INTO employees (employee_id, name, department, salary, hire_date) VALUES (%s, %s, %s, %s, %s)",
    employees
)
log("INSERT","Rows inserted into employees: ",cur.rowcount)
conn.commit()

cur.close()
conn.close()


# ══════════════════════════════════════════════════════════
#  EXERCISE 3 — FETCH RESULTS (fetchone, fetchall, fetchmany)
#
#  Task:
#  1. SELECT * FROM employees — use fetchall() and print all rows
#  2. SELECT the employee with the highest salary — use fetchone()
#  3. SELECT employees in 'Engineering' — use fetchmany(2) to get
#     2 rows at a time and loop until no rows remain
#
#  Key methods:
#  cursor.fetchone()    → returns one row as a tuple (or None)
#  cursor.fetchall()    → returns all rows as list of tuples
#  cursor.fetchmany(N)  → returns next N rows as list of tuples
#
#  HINT for fetchmany loop:
#  while True:
#      batch = cursor.fetchmany(2)
#      if not batch:
#          break
#      for row in batch:
#          print(row)
# ══════════════════════════════════════════════════════════

# YOUR CODE HERE
conn = psycopg2.connect(**DB)
cur  = conn.cursor()
                                    #Fetching all entries from table 'employees'
cur.execute("SELECT * FROM employees")
log("FETCH","Printing all rows from employees:")
rows = cur.fetchall()
for row in rows:
    print(row)

                                    #Fetching highest earner from table 'employees'
cur.execute("SELECT * FROM employees ORDER BY salary DESC LIMIT 1")
top_earner = cur.fetchone()
log("FETCH","Fetching row for Highest Earner:")
print(top_earner)

                                    #Fetching (in batches of 2) all entries of department ='Engineering' from table 'employees'
depart = "Engineering"
cur.execute("SELECT * FROM employees WHERE department = %s",(depart,))
log("FETCH","Fetching rows for engineering department:")
while True:
    batch = cur.fetchmany(2)    # get 2 rows at a time
    if not batch:
        break
    for row in batch:
        print(row)


cur.close()
conn.close()



# ══════════════════════════════════════════════════════════
#  EXERCISE 4 — DictCursor (results as dicts, not tuples)
#
#  Task:
#  1. Open a new connection
#  2. Get a DictCursor:
#       cursor = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
#  3. SELECT all employees
#  4. fetchall() and access columns by name (row["name"], row["salary"])
#     instead of by index (row[1], row[3])
#  5. Print each employee's name and salary using column names
#
#  Why DictCursor:
#  Default cursor returns plain tuples — you must remember column positions.
#  DictCursor returns dict-like rows — access by column name, much safer.
# ══════════════════════════════════════════════════════════

# YOUR CODE HERE
                                    #Fetching all entries from table 'employees' as dictionary of name and salary only
conn = psycopg2.connect(**DB)
cur = conn.cursor(cursor_factory=psycopg2.extras.DictCursor)
cur.execute("SELECT * FROM employees")
log("FETCH","Fetching all rows from employees (as Dictionary):")
rows = cur.fetchall()
for row in rows:
  print(row["name"], row["salary"])

cur.close()
conn.close()

# ══════════════════════════════════════════════════════════
#  EXERCISE 5 — UPDATE, DELETE & ROLLBACK
#
#  Task:
#  1. UPDATE Alice's salary to 102000.00 — use %s placeholder
#  2. Print Alice's salary before and after the update to confirm
#  3. DELETE the employee with employee_id = 5 (Eve)
#  4. commit() both changes
#
#  Then demonstrate rollback:
#  5. Start a new operation — UPDATE Bob's salary to 999999.00
#  6. Before committing, call conn.rollback() instead
#  7. SELECT Bob's salary — it must still be 72000.00 (rollback worked)
#  8. Print "Rollback confirmed — Bob's salary unchanged."
# ══════════════════════════════════════════════════════════

# YOUR CODE HERE
conn = psycopg2.connect(**DB)
cur  = conn.cursor()

                                    #Fetching salary for 'Alice Smith' BEFORE updation
name = "Alice Smith"
cur.execute("SELECT * FROM employees WHERE name = %s",(name,))
alice_sal_before = cur.fetchone()
log("FETCH",f"Salary for '{name}' BEFORE update is '{alice_sal_before}")


                                    #Updating salary for 'Alice Smith'
new_sal = 102000.00
cur.execute(
    "UPDATE employees SET salary = %s WHERE name = %s",
    (new_sal, name)
)
conn.commit()
log("UPDATE",f"Salary for '{name}' updated to {new_sal}")


                                    #Fetching all entries from table 'employees'
cur.execute("SELECT * FROM employees WHERE name = %s",(name,))
alice_sal_after = cur.fetchone()
log("FETCH",f"Salary for '{name}' AFTER update is '{alice_sal_after}")

                                    #Fetching salary for 'Alice Smith' AFTER updation
emp_id_delete = 5
cur.execute("DELETE FROM employees WHERE employee_id = %s", (emp_id_delete,))
log("DELETE",f"Row deleted for employee ID: '{emp_id_delete}'")
conn.commit()

                                    #Updating salary for 'Bob Jones'
new_sal = 999999.00
name = "Bob Jones"
cur.execute(
    "UPDATE employees SET salary = %s WHERE name = %s",
    (new_sal, name)
)
conn.rollback()                     #Rollback call

cur.execute("SELECT * FROM employees WHERE name = %s",(name,))
bob_sal_after = cur.fetchone()
log("FETCH",f"Salary for '{name}' is '{bob_sal_after}")

cur.close()
conn.close()
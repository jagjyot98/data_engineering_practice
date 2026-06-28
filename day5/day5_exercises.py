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

#PART_1

df.to_sql(                                    #Run only once to create table
    name="employees",       # table name
    con=engine,             # SQLAlchemy engine
    if_exists="replace",    # "replace" drops and recreates, "append" adds rows, "fail" errors if exists
    index=False,            # don't write the DataFrame index as a column
)

# df_verify = pd.read_sql("SELECT * FROM employees LIMIT 5", con=engine)
# print(df_verify)
print(f"Table 'employees' loaded with {pd.read_sql('SELECT COUNT(*) as cnt FROM employees', con=engine)['cnt'][0]} rows.")

#PART_2
df_verify = pd.read_sql("SELECT * FROM employees", con=engine)
print(df_verify.shape)

df_salary_filtered = pd.read_sql("SELECT name, salary FROM employees WHERE salary > 80000", con=engine)
print(df_salary_filtered)

#PART_3
def get_employees_by_dept(engine, department):
    with engine.connect() as conn:
        result = conn.execute(
            text("SELECT * FROM employees WHERE department = :department"),
           {"department": department}
        )
    df = pd.DataFrame(result.fetchall(), columns=result.keys())
    print(df)

get_employees_by_dept(engine, "Engineering")

#PART_4
df_department_aggregates = pd.read_sql("SELECT department, AVG(salary) as avg_salary, MAX(salary) as max_salary, count(*) as headcount from employees group by department", con=engine)
print(df_department_aggregates)

#PART_5
df.to_csv("day5/raw_employees.csv", index=False)

def run_pipeline(csv_path, engine):
    df_raw = pd.read_csv(csv_path)

    df_enriched = pd.read_sql("select *,case when salary >='90000' then 'high' when salary >='60000' then 'mid' else 'Low' end as salary_band from employees;", con=engine)
    df_enriched.to_sql(                                    #Run only once to create table
        name="employees_enriched",       # table name
        con=engine,             # SQLAlchemy engine
        if_exists="replace",    # "replace" drops and recreates, "append" adds rows, "fail" errors if exists
        index=False,            # don't write the DataFrame index as a column
    )
    # df_verify = pd.read_sql("SELECT * FROM employees_enriched", con=engine)
    # print(df_verify)
    print(f"Table 'employees_enriched' loaded with {pd.read_sql('SELECT COUNT(*) as cnt FROM employees', con=engine)['cnt'][0]} rows.")


run_pipeline("day5/raw_employees.csv", engine)
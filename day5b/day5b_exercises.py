from sqlalchemy import create_engine, text
import pandas as pd

engine = create_engine("sqlite:///day5b/company.db")

# Source 1 — employee info
employees_data = [
    {"employee_id": 1, "name": "  Alice Smith", "department": "Engineering", "join_date": "2021-03-15"},
    {"employee_id": 2, "name": "BOB JONES",     "department": "Marketing",   "join_date": "2020-07-01"},
    {"employee_id": 3, "name": "charlie  ",      "department": "Engineering", "join_date": "2022-01-10"},
    {"employee_id": 4, "name": "Diana Prince",   "department": "HR",          "join_date": "2019-11-20"},
    {"employee_id": 5, "name": "Eve Adams",      "department": "Engineering", "join_date": "2018-05-30"},
    {"employee_id": 6, "name": None,             "department": "Marketing",   "join_date": "2023-02-14"},
]

# Source 2 — salary info (separate system)
salaries_data = [
    {"employee_id": 1, "salary": 95000},
    {"employee_id": 2, "salary": 72000},
    {"employee_id": 3, "salary": None},     # missing salary
    {"employee_id": 4, "salary": -5000},    # invalid salary
    {"employee_id": 5, "salary": 88000},
    {"employee_id": 6, "salary": 76000},
]

pd.DataFrame(employees_data).to_csv("day5b/employees.csv", index=False)
pd.DataFrame(salaries_data).to_csv("day5b/salaries.csv", index=False)

def extract(filepath):
    df = pd.read_csv(filepath)
    print(f"[EXTRACT] {len(df)} rows read from {filepath}")
    return df



def validate(df, required_cols, numeric_cols=None):
    # Step 1 — check all required columns are non-null (works for any type)
    mask_valid = df[required_cols].notna().all(axis=1)

    # Step 2 — additionally check numeric columns are > 0
    if numeric_cols:
        for col in numeric_cols:
            mask_valid = mask_valid & (df[col] > 0)

    df_valid   = df[mask_valid].copy()
    df_invalid = df[~mask_valid].copy()
    df_invalid["reject_reason"] = "null or invalid value in required columns"
    print(f"[VALIDATE] {len(df_valid)} valid rows, {len(df_invalid)} invalid rows")
    return df_valid, df_invalid


def transform(df_employees, df_salaries):
    df_e = df_employees.copy()
    df_s = df_salaries.copy()
    df_e["name"]   = df_e["name"].str.strip().str.lower()
    df_s["salary"]  = pd.to_numeric(df_s["salary"], errors="coerce")
    df_s["salary"]  = df_s["salary"].fillna(df_s["salary"].median())

    def salary_band(s):
        if s >= 90000:   return "high"
        elif s >= 60000: return "mid"
        else:            return "low"

    df_merged = df_e.merge(df_s, on="employee_id", how="inner")
    df_merged["salary"] = pd.to_numeric(df_merged["salary"], errors="coerce")
    df_merged["salary"] = df_merged["salary"].fillna(df_merged["salary"].median())
    df_merged["salary_band"] = df_merged["salary"].apply(salary_band)
    df_merged["join_date"] = pd.to_datetime(df_merged["join_date"], errors="coerce")
    return df_merged


def load(df, table_name, engine):
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    print(f"[LOAD] {len(df)} rows loaded into '{table_name}'")
    return len(df)



def pipeline(engine):
                            #loading data from from employees and salaries
    df_employees = extract("day5b/employees.csv")
    df_salaries = extract("day5b/salaries.csv")
    
                            #validating data coming employees.csv
    df_employees_valid, df_employees_invalid = validate(
        df_employees,
        required_cols=["name"]
    )

                            #validating data coming salaries.csv
    df_salaries_valid, df_salaries_invalid = validate(
        df_salaries,
        required_cols=["salary"],
        numeric_cols=["salary"]
    )

                            #merging and loading invalid data into rejected records table to be checked
    df_merged_invalid = pd.concat([df_employees_invalid, df_salaries_invalid], ignore_index=True)
    load(df_merged_invalid, "rejected_records", engine)

                            #transforming and merging valid data from both employees and salries on employee_id
    transformed_df = transform(df_employees_valid, df_salaries_valid)
    load(transformed_df, "employees_final", engine)     #loadiong final valid data to employees_final table in database

    print("="*40)
    print("Valid rows loaded : ", len(transformed_df))
    print("Rejected rows     : ", len(df_merged_invalid))
    print("Target table      : employees_final")
    print("="*40)

pipeline(engine)
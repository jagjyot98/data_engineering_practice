import csv

import pandas as pd

data = [
    {"employee_id": 1,  "name": "  Alice Smith",  "department": "Engineering", "salary": "95000", "join_date": "2021-03-15", "manager": "Bob"},
    {"employee_id": 2,  "name": "BOB JONES",       "department": "Marketing",   "salary": "72000", "join_date": "2020-07-01", "manager": None},
    {"employee_id": 3,  "name": "charlie  ",        "department": "Engineering", "salary": None,    "join_date": "2022-01-10", "manager": "Alice"},
    {"employee_id": 4,  "name": "Diana Prince",     "department": "HR",          "salary": "68000", "join_date": "2019-11-20", "manager": None},
    {"employee_id": 5,  "name": "BOB JONES",        "department": "Marketing",   "salary": "72000", "join_date": "2020-07-01", "manager": None},
    {"employee_id": 6,  "name": "Eve Adams",        "department": "Engineering", "salary": "105000","join_date": "2018-05-30", "manager": "Alice"},
]

df = pd.DataFrame(data)

#PART _1

print(df.shape)
print(df.columns)
print(df.dtypes)
print(df.isnull().sum())


#PART _2


# --- Fix data types
df["salary"] = pd.to_numeric(df["salary"], errors="coerce", downcast="integer")  # convert to numeric, set errors to NaN
df["salary"] = df["salary"].fillna(df["salary"].median())  # fill nulls with a value

df["join_date"] = pd.to_datetime(df["join_date"], errors="coerce")  # convert to datetime, set errors to NaT

# --- Strip whitespace from string columns
df["name"] = df["name"].str.strip()

# --- Lowercase string columns
df["name"] = df["name"].str.lower()

# --- Remove duplicates baseed on employee id
df = df.drop_duplicates(subset=["employee_id"])  # based on specific column

#PART _3

# --- Adding columns band and year_at_company

def salary_band(salary):        # for salary band
    if salary >= 90000:
        return "high"
    elif salary >= 60000:
        return "mid"
    else:
        return "low"

df["band"] = df["salary"].apply(salary_band)


def year_at_company(join_date):     #for yaer at company
    if pd.isnull(join_date):
        return None
    return 2026 - join_date.year

df["years_at_company"] = df["join_date"].apply(year_at_company)

#PART _4

df.to_csv("clean_output.csv", index=False)

def load_csv(filename="clean_output.csv"):
        try:
            with open(filename, "r") as f:                #reading the csv file and loading it to a variable
                reader = csv.DictReader(f)
                return list(reader)
        except Exception as e:
            return list()  # Return an empty list if there's an error

read_data = load_csv()  # ✅ FIXED: default filename used
print(read_data)
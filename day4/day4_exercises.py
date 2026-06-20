import glob

import pandas as pd
import json
import os

#PART _1

data = [
    {"employee_id": 1,  "name": "  Alice Smith",  "department": "Engineering", "salary": "95000", "join_date": "2021-03-15"},
    {"employee_id": 2,  "name": "BOB JONES",       "department": "Marketing",   "salary": "72000", "join_date": "2020-07-01"},
    {"employee_id": 3,  "name": "charlie  ",        "department": "Engineering", "salary": None,    "join_date": "2022-01-10"},
    {"employee_id": 4,  "name": "Diana Prince",     "department": "HR",          "salary": "68000", "join_date": "2019-11-20"},
    {"employee_id": 5,  "name": "BOB JONES",        "department": "Marketing",   "salary": "72000", "join_date": "2020-07-01"},
    {"employee_id": 6,  "name": "Eve Adams",        "department": "Engineering", "salary": "105000","join_date": "2018-05-30"},
]

df = pd.DataFrame(data)

df.to_csv("employees.csv", index=False)   # index=False — always!

df = pd.read_csv(
    "employees.csv",
    sep=",",              # delimiter — use sep="\t" for tab-separated
    header=0,             # row number to use as column names (0 = first row)
    usecols=["name", "department", "salary"],   # only load specific columns (saves memory)
    dtype={"salary": float},      # set column types on load
    na_values=["N/A", "null", ""],  # treat these as NaN
    # parse_dates=["join_date"],    # auto-parse date columns
)
# print(df.dtypes)

#PART _2

df.to_json("employees.json", orient="records", indent=2)

with open("employees.json") as f:
    raw = json.load(f)

dfl = pd.DataFrame(raw)

# print(dfl.head(3))

#PART _3

df.to_parquet("employees.parquet", index=False, compression="snappy")

df = pd.read_parquet("employees.parquet", columns=["name", "salary"])
print(df.dtypes)

#PART _4

for fmt in ["employees.csv", "employees.json", "employees.parquet"]:
    size = os.path.getsize(fmt) / 1024   # size in KB
    print(f"{fmt}: {size:.1f} KB")

#PART _5

data1 = [{"employee_id": 1,  "name": "  Alice Smith",  "department": "Engineering", "salary": "95000", "join_date": "2021-03-15"},
    {"employee_id": 2,  "name": "BOB JONES",       "department": "Marketing",   "salary": "72000", "join_date": "2020-07-01"},
    {"employee_id": 3,  "name": "charlie  ",        "department": "Engineering", "salary": None,    "join_date": "2022-01-10"},
]

version1 = pd.DataFrame(data1)
version1.to_csv("employees_v1.csv", index=False)

data2 = [{"employee_id": 4,  "name": "Diana Prince",     "department": "HR",          "salary": "68000", "join_date": "2019-11-20"},
    {"employee_id": 5,  "name": "BOB JONES",        "department": "Marketing",   "salary": "72000", "join_date": "2020-07-01"},
    {"employee_id": 6,  "name": "Eve Adams",        "department": "Engineering", "salary": "105000","join_date": "2018-05-30"},
]
version2 = pd.DataFrame(data2)
version2.to_csv("employees_v2.csv", index=False)

files = glob.glob("employees_v*.csv")
df = pd.concat([pd.read_csv(f) for f in files], ignore_index=True)

print(df.shape)
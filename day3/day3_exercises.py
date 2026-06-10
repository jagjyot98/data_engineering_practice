import pandas as pd

data = [
    {"employee_id": 1,  "name": "Alice",   "department": "Engineering", "salary": 95000,  "experience": 5,  "gender": "F"},
    {"employee_id": 2,  "name": "Bob",     "department": "Marketing",   "salary": 72000,  "experience": 3,  "gender": "M"},
    {"employee_id": 3,  "name": "Charlie", "department": "Engineering", "salary": 105000, "experience": 8,  "gender": "M"},
    {"employee_id": 4,  "name": "Diana",   "department": "HR",          "salary": 68000,  "experience": 2,  "gender": "F"},
    {"employee_id": 5,  "name": "Eve",     "department": "Engineering", "salary": 88000,  "experience": 4,  "gender": "F"},
    {"employee_id": 6,  "name": "Frank",   "department": "Marketing",   "salary": 76000,  "experience": 5,  "gender": "M"},
    {"employee_id": 7,  "name": "Grace",   "department": "HR",          "salary": 71000,  "experience": 4,  "gender": "F"},
    {"employee_id": 8,  "name": "Henry",   "department": "Engineering", "salary": 112000, "experience": 10, "gender": "M"},
    {"employee_id": 9,  "name": "Iris",    "department": "Marketing",   "salary": 69000,  "experience": 2,  "gender": "F"},
    {"employee_id": 10, "name": "Jack",    "department": "HR",          "salary": 74000,  "experience": 6,  "gender": "M"},
]

df = pd.DataFrame(data)

#PART _1

filter_1_data = df[df["salary"] > 80000]
                   
filter_2_data = df[(df["experience"] >= 5) & (df["department"] == "Engineering")]

filter_3_data = df[df["department"].isin(["Marketing","HR"])]

#PART _2

sort_1_data = df.sort_values("salary", ascending=False)

sort_2_data = df.sort_values(["department", "experience"], ascending=[True, False])

#PART _3

aggregate_results =df.groupby("department").agg(
    avg_salary = ("salary", "mean"),
    max_salary = ("salary", "max"),
    total_employees = ("employee_id", "count"),
    avg_experience = ("experience", "mean")
).reset_index()

#PART _4 (need guidance)

# df["dept_avg_salary"] = df.groupby("department")["salary"].mean().reset_index()

#PART _5
result = df.groupby("department").filter(lambda g: g["salary"].mean() > 80000)
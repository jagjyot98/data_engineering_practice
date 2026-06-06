"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 1
 Topic : Python Basics for Data Engineering
 Date  : 2026-06-06
=============================================================
"""

import json
import csv

employees = [                   # list of dicts
    {"name": "  john smith ", "department": "Engineering", "salary": "85000"},
    {"name": "JANE DOE",      "department": "Marketing",   "salary": "72000"},
    {"name": " Bob Lee",      "department": "Engineering", "salary": "N/A"},
]

# ── EXERCISE 1 ────────────────────────────────────────────
# Clean employee records using a function + list comprehension

def clean_employee(record):         # Main func to clean each row
    cleaned_record = record.copy()
    cleaned_record["name"] = record["name"].strip().lower()
    cleaned_record["salary"] = clean_salary(record["salary"])
    return cleaned_record

def clean_salary(value):            # Func to clean salary values
    try:
        return int(value)
    except (ValueError, TypeError):
        return None

cleaned_employees = [clean_employee(emp) for emp in employees]


# ── EXERCISE 2 ────────────────────────────────────────────
# Write cleaned employees to JSON, then read and print

with open("clean_employees.json", "w") as f:          # ✅ FIXED: removed newline="" (CSV only)
    json.dump(cleaned_employees, f, indent=2)

with open("clean_employees.json", "r") as f:
    records = json.load(f)

for record in records:
    print(f'{record["name"]} - {record["salary"]} - {record["department"]}')  # ✅ FIXED: f-string


# ── EXERCISE 3 ────────────────────────────────────────────
# Reusable load_csv(filepath) with proper error handling

def load_csv(filepath):                               # ✅ FIXED: accepts filepath param
    try:                                              # ✅ FIXED: open() is inside try block
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:                         # ✅ FIXED: specific exception
        print(f"File not found: {filepath}")
        return []


# ══════════════════════════════════════════════════════════
#  EVALUATION & REVIEW
# ══════════════════════════════════════════════════════════
"""
SCORE: 7.5 / 10

EXERCISE 1 — ✅ PASS
  + record.copy() used — never mutate original data in pipelines
  + clean_salary() separated into its own function (clean decomposition)
  + try/except with correct types (ValueError, TypeError)
  + List comprehension applied correctly
  ~ Use f-strings instead of string concatenation (style)

EXERCISE 2 — ✅ PASS (with fix)
  ❌ newline="" used on json open() — this is for CSV only, not JSON
  ✅ Fix: remove newline="" from json open()
  ~ Use f-strings for print formatting

EXERCISE 3 — ⚠️ NEEDS FIX
  ❌ Function had no filepath parameter — hardcoded path, not reusable
  ❌ open() was OUTSIDE the try block — FileNotFoundError not caught
  ❌ Caught broad Exception instead of specific FileNotFoundError
  ✅ Fix: wrap open() inside try, accept filepath param, catch FileNotFoundError

KEY TAKEAWAYS:
  1. Always wrap open() inside try — file paths fail at runtime in pipelines
  2. Functions must be reusable — no hardcoded paths ever
  3. Catch specific exceptions (FileNotFoundError), not broad Exception
  4. newline="" is for CSV writers only
  5. Prefer f-strings over string concatenation
"""

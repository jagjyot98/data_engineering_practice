"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 1 NOTES
 Topic : Python Basics for Data Engineering
 Date  : 2026-06-06
=============================================================
"""


# ══════════════════════════════════════════════════════════
#  TOPIC 1 — DATA STRUCTURES
#  The four structures used constantly in data engineering
# ══════════════════════════════════════════════════════════

# List — ordered collection, used for rows of data
records = ["Alice", "Bob", "Charlie"]

# Dictionary — key-value pairs, represents a single table row
row = {"name": "Alice", "age": 30, "city": "NYC"}

# List of dicts — most common raw data format in pipelines
data = [
    {"name": "Alice", "age": 30},
    {"name": "Bob",   "age": 25},
]

# Tuple — immutable, used for database records
record = ("Alice", 30, "NYC")


# ══════════════════════════════════════════════════════════
#  TOPIC 2 — FUNCTIONS & LIST COMPREHENSIONS
# ══════════════════════════════════════════════════════════

# Regular function
def clean_name(name):
    return name.strip().lower()

# Lambda — inline function for simple one-liners
clean = lambda x: x.strip().lower()

# List comprehension — replaces for loops in data work (more Pythonic)
names = ["  Alice ", "BOB ", " Charlie"]
cleaned = [clean_name(n) for n in names]
# Output: ['alice', 'bob', 'charlie']

# List comprehension with condition
ages = [30, 17, 25, 15, 40]
adults = [age for age in ages if age >= 18]
# Output: [30, 25, 40]


# ══════════════════════════════════════════════════════════
#  TOPIC 3 — FILE I/O
#  Reading and writing CSV and JSON files
# ══════════════════════════════════════════════════════════

import csv
import json

# --- CSV READ ---
# csv.DictReader reads each row as a dictionary
with open("sales.csv", "r") as f:
    reader = csv.DictReader(f)
    for row in reader:
        print(row)  # {'product': 'Laptop', 'price': '999'}

# --- CSV WRITE ---
data = [
    {"product": "Laptop", "price": 999},
    {"product": "Phone",  "price": 499},
]
with open("output.csv", "w", newline="") as f:   # newline="" prevents double line breaks on Windows
    writer = csv.DictWriter(f, fieldnames=["product", "price"])
    writer.writeheader()
    writer.writerows(data)

# --- JSON READ ---
with open("data.json", "r") as f:
    records = json.load(f)   # returns list or dict

# --- JSON WRITE ---
with open("output.json", "w") as f:   # NO newline="" for JSON
    json.dump(data, f, indent=2)

# KEY RULE: newline="" is for CSV writers ONLY — never use on JSON files


# ══════════════════════════════════════════════════════════
#  TOPIC 4 — ERROR HANDLING
#  Critical in data pipelines — bad data must not crash the job
# ══════════════════════════════════════════════════════════

# Always handle bad/missing values gracefully
def parse_age(value):
    try:
        return int(value)
    except (ValueError, TypeError):
        return None   # return None instead of crashing the pipeline

print(parse_age("25"))   # 25
print(parse_age("N/A"))  # None
print(parse_age(None))   # None

# File not found — wrap open() INSIDE the try block
def load_csv(filepath):
    try:                              # open() must be INSIDE try
        with open(filepath, "r") as f:
            reader = csv.DictReader(f)
            return list(reader)
    except FileNotFoundError:         # catch SPECIFIC exception
        print(f"File not found: {filepath}")
        return []                     # return empty list, don't crash


# ══════════════════════════════════════════════════════════
#  TOPIC 5 — F-STRINGS (Best Practice)
# ══════════════════════════════════════════════════════════

name = "Alice"
salary = 85000

# ❌ Old style — string concatenation
print("Name: " + name + ", Salary: " + str(salary))

# ✅ Pythonic — f-string (faster, readable, no type casting needed)
print(f"Name: {name}, Salary: {salary}")


# ══════════════════════════════════════════════════════════
#  TOPIC 6 — RECORD MUTATION (Critical in Pipelines)
# ══════════════════════════════════════════════════════════

# ❌ Bad — modifies the original data
def bad_clean(record):
    record["name"] = record["name"].strip()   # mutates original!
    return record

# ✅ Good — always copy before modifying
def good_clean(record):
    cleaned = record.copy()                   # work on a copy
    cleaned["name"] = record["name"].strip()
    return cleaned

# In pipelines the original raw data must stay untouched
# so you can re-process, debug, or audit it later


# ══════════════════════════════════════════════════════════
#  DAY 1 — KEY TAKEAWAYS
# ══════════════════════════════════════════════════════════
"""
1. Use record.copy() — never mutate original data in pipelines
2. Always wrap open() INSIDE the try block — not outside
3. Catch specific exceptions (FileNotFoundError, ValueError)
   not broad Exception which hides bugs
4. newline="" is for CSV writers ONLY — never for JSON
5. Use f-strings instead of string concatenation
6. Functions must accept parameters — no hardcoded paths ever
7. List comprehensions replace for loops cleanly in data work
"""

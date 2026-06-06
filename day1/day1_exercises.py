import json
import csv

employees = [                   # list of dicts
    {"name": "  john smith ", "department": "Engineering", "salary": "85000"},
    {"name": "JANE DOE",      "department": "Marketing",   "salary": "72000"},
    {"name": " Bob Lee",      "department": "Engineering", "salary": "N/A"},
]

#PART _1

def clean_employee(record):         # MAin func to initiate each row cleaning
    cleaned_record = record.copy()
    cleaned_record["name"] = record["name"].strip().lower()
    cleaned_record["salary"] = clean_salary(record["salary"])
    # print(cleaned_record["name"]+" - "+str(cleaned_record["salary"])+" - "+cleaned_record["department"])
    return cleaned_record

def clean_salary(value):            #func to clean salary values
    try:
        return int(value)
    except (ValueError, TypeError):
        return None 
    
cleaned_employees = [clean_employee(emp) for emp in employees]      #calling each row and passing to Main cleaning func

#PART _2

with open("clean_employees.json", "w", newline="") as f:        #creating a json and writing cleaned data to it
    json.dump(cleaned_employees, f, indent=2)


with open("clean_employees.json", "r") as f:                    #reading the json file and loading it to a variable
    records = json.load(f)  # returns a list or dict

for record in records:                                          #iterating through the loaded json data and printing each record in a formatted way
    print(record["name"]+" - "+str(record["salary"])+" - "+record["department"])

#PART _3

def load_csv():
    with open("clean_employees.csv", "r") as f:                #reading the csv file and loading it to a variable
        try:
            reader = csv.DictReader(f)
            return list(reader)
        except Exception as e:
            return list()  # Return an empty list if there's an error
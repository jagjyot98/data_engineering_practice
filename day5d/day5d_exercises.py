"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 5d
 Topic : ETL Deep Dive — Untouched Patterns
 Pipelines: Chunked Loading | Upsert + Audit | Checkpointing
=============================================================
"""

from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime
import uuid

engine = create_engine("sqlite:///day5d/warehouse.db")

def log(step, message, rows=None):                      #for creating logs
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_info = f"{rows}" if rows is not None else ""
    print(f"[{ts}] [{step}] {message}{row_info}")


# # ══════════════════════════════════════════════════════════
# #  SETUP — generate source data files
# # ══════════════════════════════════════════════════════════

import random

random.seed(42)
products   = ["Laptop", "Phone", "Tablet", "Monitor", "Mouse", "Keyboard"]
customers  = [f"Customer_{i}" for i in range(1, 21)]

rows = []
for i in range(1, 201):
    rows.append({
        "order_id":   i,
        "customer":   random.choice(customers),
        "product":    random.choice(products),
        "quantity":   random.choice([None, -1, 1, 2, 3, 5]),
        "unit_price": random.choice([None, -50, 49.99, 99.99, 299.99, 599.99, 999.99]),
        "order_date": f"2024-{random.randint(1,12):02d}-{random.randint(1,28):02d}",
    })

pd.DataFrame(rows).to_csv("day5d/orders_large.csv", index=False)

# Two batch files for Pipeline C checkpointing
pd.DataFrame(rows[:100]).to_csv("day5d/batch_jan.csv", index=False)
pd.DataFrame(rows[100:]).to_csv("day5d/batch_feb.csv", index=False)

print("Source files generated.")
print(f"  orders_large.csv : 200 rows")
print(f"  batch_jan.csv    : 100 rows")
print(f"  batch_feb.csv    : 100 rows")


# ══════════════════════════════════════════════════════════
#  PIPELINE A — CHUNKED LOADING
#
#  Problem: orders_large.csv has 200 rows (imagine it has
#  10 million). Loading it all into memory at once would
#  crash or be very slow.
#
#  Your task:
#  1. Read orders_large.csv using chunksize=50 so only
#     50 rows are in memory at a time
#  2. For each chunk, validate rows:
#       - quantity must not be null and must be > 0
#       - unit_price must not be null and must be > 0
#  3. Load valid rows to table 'orders_clean' (append each chunk)
#  4. Load invalid rows to table 'orders_rejected' (append each chunk)
#  5. After all chunks are processed, print a summary:
#       Total chunks processed: X
#       Total valid rows loaded: X
#       Total rejected rows: X
#
#  Key concept: pd.read_csv("file.csv", chunksize=50)
#  returns an iterator — each iteration gives you a DataFrame
#  of 50 rows. You loop over it.
#
#  HINT:
#  reader = pd.read_csv("day5d/orders_large.csv", chunksize=50)
#  for chunk in reader:
#      # chunk is a DataFrame of 50 rows
#      ...
# ══════════════════════════════════════════════════════════

# YOUR CODE HERE
reader = pd.read_csv("day5d/orders_large.csv", chunksize=50)
chunks_processed = 0
total_valid_rows = 0
total_rejected_rows = 0

for chunk in reader:
                            # Validating rows
    mask         = (chunk["quantity"].notnull()) & (chunk["quantity"] > 0) & (chunk["unit_price"].notnull()) & (chunk["unit_price"] > 0)
    valid_rows   = chunk[mask]
    invalid_rows = chunk[~mask]
    invalid_rows["reject_reason"] = "null or invalid quantity/unit_price"

                            # Loading valid rows to 'orders_clean'
    valid_rows.to_sql("orders_clean", engine, if_exists="append", index=False)

                            # Loading invalid rows to 'orders_rejected'
    invalid_rows.to_sql("orders_rejected", engine, if_exists="append", index=False)

                            # Updating counters
    chunks_processed += 1
    total_valid_rows += len(valid_rows)
    total_rejected_rows += len(invalid_rows)
    log("LOAD", f"Loaded chunk {chunks_processed}")

print(f"Total chunks processed: {chunks_processed}")
print(f"Total valid rows loaded: {total_valid_rows}")
print(f"Total rejected rows: {total_rejected_rows}")





# ══════════════════════════════════════════════════════════
#  PIPELINE B — UPSERT + AUDIT COLUMNS
#
#  Problem: you receive updated order data. Some order_ids
#  are new, some already exist with different values.
#  You want to INSERT new rows and UPDATE existing ones —
#  not just append (which would create duplicates) and not
#  replace the whole table (which loses history).
#
#  Your task:
#  1. Use the data below (v1 first, then v2)
#  2. Before loading, add three audit columns to every row:
#       loaded_at   = current timestamp (string)
#       source_file = name of the "file" (pass as a param)
#       run_id      = a unique ID for this pipeline run
#                     use: str(uuid.uuid4())
#  3. Load v1 first using raw SQL INSERT OR REPLACE INTO
#     (this is SQLite's upsert — inserts if new, replaces if exists)
#  4. Load v2 and show that order_id 2 and 3 were updated,
#     order_id 4 and 5 are new
#  5. After each load, SELECT * and print the table
#
#  Key concept:
#  INSERT OR REPLACE INTO table (col1, col2, ...) VALUES (:col1, :col2, ...)
#  Pass a list of dicts as the second argument to conn.execute()
#
#  HINT for audit columns — add to every row before loading:
#  df["loaded_at"]   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
#  df["source_file"] = source_file
#  df["run_id"]      = str(uuid.uuid4())
# ══════════════════════════════════════════════════════════

v1 = [
    {"order_id": 1, "customer": "Alice", "amount": 500.00},
    {"order_id": 2, "customer": "Bob",   "amount": 300.00},
    {"order_id": 3, "customer": "Eve",   "amount": 750.00},
]

v2 = [
    {"order_id": 2, "customer": "Bob",     "amount": 350.00},  # updated amount
    {"order_id": 3, "customer": "Eve",     "amount": 800.00},  # updated amount
    {"order_id": 4, "customer": "Charlie", "amount": 200.00},  # new
    {"order_id": 5, "customer": "Diana",   "amount": 450.00},  # new
]

# YOUR CODE HERE
with engine.begin() as conn:            #Need to define table first before loading data
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS orders_audit (
            order_id    INTEGER PRIMARY KEY,
            customer    TEXT,
            amount      REAL,
            loaded_at   TEXT,
            source_file TEXT,
            run_id      TEXT
        )
    """))
    log("SETUP", "Created table 'orders_audit' in database")

for data, source_file in [(v1, "v1"), (v2, "v2")]:
    df = pd.DataFrame(data)
    df["loaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df["source_file"] = source_file
    df["run_id"] = str(uuid.uuid4())        #generating unique run_id for each load

    with engine.begin() as conn:            #checking against existing order_ids
        conn.execute(
            text("""
                INSERT OR REPLACE INTO orders_audit (order_id, customer, amount, loaded_at, source_file, run_id)
                VALUES (:order_id, :customer, :amount, :loaded_at, :source_file, :run_id)
            """),
            df.to_dict(orient="records")
        )

                            # Printing the table after each load
    result_df = pd.read_sql("SELECT * FROM orders_audit", engine)
    log("LOAD", f"Loaded data from {source_file} into 'orders_audit' | Rows in table: ", len(result_df))
    print(f"After loading {source_file}:")
    print(result_df)



# ══════════════════════════════════════════════════════════
#  PIPELINE C — CHECKPOINTING
#
#  Problem: you have two batch files. Your pipeline runs
#  every day. If it crashes halfway through, or if you
#  rerun it the next day, you don't want to reprocess
#  files that already succeeded.
#
#  Your task:
#  1. Create a 'pipeline_state' table (if not exists):
#       file_name   TEXT PRIMARY KEY
#       status      TEXT   ('success' or 'failed')
#       loaded_at   TEXT
#       rows_loaded INTEGER
#  2. Write a function process_file(filepath, engine) that:
#       a. Checks pipeline_state — if file_name already
#          has status='success', SKIP it and log "already processed"
#       b. If not processed, load the file's rows to
#          'orders_batched' table (append)
#       c. Write a record to pipeline_state marking it
#          status='success' with current timestamp and row count
#  3. Call process_file for batch_jan.csv, then batch_feb.csv
#  4. Call process_file for batch_jan.csv AGAIN — it must skip
#  5. Print the pipeline_state table at the end
#
#  This is the checkpoint pattern — every production pipeline
#  has some version of this so reruns are safe and idempotent.
#
#  HINT for checking state:
#  existing = pd.read_sql(
#      "SELECT file_name FROM pipeline_state WHERE status = 'success'",
#      engine
#  )["file_name"].tolist()
# ══════════════════════════════════════════════════════════

# YOUR CODE HERE
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pipeline_state (
            file_name   TEXT PRIMARY KEY,
            status      TEXT,
            loaded_at   TEXT,
            rows_loaded INTEGER
        )
    """))
log("SETUP", "Created table 'pipeline_state' in database")

def process_file(filepath, engine):
    file_name = filepath.split("/")[-1]     #clipping out filename out of filepath

    existing = pd.read_sql(                 #initial chcek for file record existence
        "SELECT file_name FROM pipeline_state WHERE status = 'success'",
        engine
    )["file_name"].tolist()

    if file_name in existing:
        print(f"File {file_name} already processed. Skipping.")
        return                              #if file exists, skip processing

    df = pd.read_csv(filepath)              #if not, load data to the table
    df.to_sql("orders_batched", engine, if_exists="append", index=False)

    with engine.begin() as conn:            #add file name to the processed records
        conn.execute(
            text("""
                INSERT INTO pipeline_state (file_name, status, loaded_at, rows_loaded)
                VALUES (:file_name, :status, :loaded_at, :rows_loaded)
            """),
            {
                "file_name": file_name,
                "status": "success",
                "loaded_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rows_loaded": len(df)
            }
        )
    print(f"Processed file {file_name}: {len(df)} rows loaded.")

process_file("day5d/batch_jan.csv", engine)
process_file("day5d/batch_feb.csv", engine)

process_file("day5d/batch_jan.csv", engine)     #should skip this time
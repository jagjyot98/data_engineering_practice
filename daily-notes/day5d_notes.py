"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 5d NOTES
 Topic : ETL Deep Dive — Untouched Patterns
         Chunked Loading | Upsert + Audit | Checkpointing
 Date  : 2026-07-12
=============================================================
"""

from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime
import uuid
import os


# ══════════════════════════════════════════════════════════
#  TOPIC 1 — CHUNKED LOADING
# ══════════════════════════════════════════════════════════

# Problem: a file with 10M rows cannot fit in memory at once.
# Solution: read it in fixed-size chunks, process each chunk,
#           accumulate results across all chunks.

# pd.read_csv(chunksize=N) returns a TextFileReader iterator.
# Each iteration yields a DataFrame of N rows.
reader = pd.read_csv("day5d/orders_large.csv", chunksize=50)

chunks_processed    = 0   # counters MUST live outside the loop
total_valid_rows    = 0
total_rejected_rows = 0

for chunk in reader:
    # Compute mask once, apply with mask and ~mask
    mask         = chunk["quantity"].notnull() & (chunk["quantity"] > 0)
    valid_rows   = chunk[mask].copy()
    invalid_rows = chunk[~mask].copy()

    # Append each chunk — table accumulates across iterations
    valid_rows.to_sql("orders_clean",    con=engine, if_exists="append", index=False)
    invalid_rows.to_sql("orders_rejected", con=engine, if_exists="append", index=False)

    chunks_processed    += 1
    total_valid_rows    += len(valid_rows)
    total_rejected_rows += len(invalid_rows)

# RULES:
# 1. if_exists="append" on every chunk — NOT "replace" (that wipes prior chunks)
# 2. Counters outside the loop — inside the loop they reset every chunk
# 3. Compute mask once — never duplicate the condition for valid and invalid splits
# 4. always .copy() after slicing — prevents SettingWithCopyWarning on column assignment
# 5. valid + rejected must equal total source rows — verify after run

# DO NOT call list(reader) — that defeats the purpose and loads everything into memory


# ══════════════════════════════════════════════════════════
#  TOPIC 2 — UPSERT WITH INSERT OR REPLACE
# ══════════════════════════════════════════════════════════

# Upsert = INSERT if new, UPDATE if already exists (by primary key)

# ❌ APPEND — adds duplicates if row already exists
df.to_sql("orders", con=engine, if_exists="append", index=False)

# ❌ REPLACE — wipes entire table, loses all other rows
df.to_sql("orders", con=engine, if_exists="replace", index=False)

# ✅ UPSERT — insert new rows, update existing ones by primary key
# Step 1: table must exist first — raw SQL cannot create it on the fly
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS orders_audit (
            order_id INTEGER PRIMARY KEY,   -- PRIMARY KEY is required for upsert to work
            customer TEXT,
            amount   REAL
        )
    """))

# Step 2: INSERT OR REPLACE (SQLite syntax)
# SQLite checks the PRIMARY KEY — if it exists, replaces the whole row; if new, inserts.
with engine.begin() as conn:
    conn.execute(
        text("""
            INSERT OR REPLACE INTO orders_audit (order_id, customer, amount)
            VALUES (:order_id, :customer, :amount)
        """),
        df.to_dict(orient="records")   # list of dicts — one dict per row
    )

# PostgreSQL equivalent (different syntax, same concept):
# INSERT INTO orders_audit (order_id, customer, amount)
# VALUES (:order_id, :customer, :amount)
# ON CONFLICT (order_id) DO UPDATE SET
#     customer = EXCLUDED.customer,
#     amount   = EXCLUDED.amount

# RULES:
# 1. PRIMARY KEY on the upsert column is mandatory — no key = no dedup = duplicates
# 2. CREATE TABLE before INSERT OR REPLACE — unlike to_sql, raw SQL won't create the table
# 3. df.to_dict(orient="records") → list of dicts → pass directly to conn.execute()
# 4. INSERT OR REPLACE replaces the ENTIRE row, not just changed columns


# ══════════════════════════════════════════════════════════
#  TOPIC 3 — AUDIT COLUMNS
# ══════════════════════════════════════════════════════════

# Every production table should have audit columns added automatically on load.
# These answer: when was this row loaded, where did it come from, which run loaded it?

def add_audit_columns(df, source_file):
    df = df.copy()
    df["loaded_at"]   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")  # timestamp of this load
    df["source_file"] = source_file                                    # filename or API endpoint
    df["run_id"]      = str(uuid.uuid4())                              # unique ID for this run
    return df

# run_id — generate ONCE per pipeline run, assign to ALL rows in that batch
# This lets you query "show me everything loaded in run X"
run_id = str(uuid.uuid4())
df["run_id"] = run_id   # same ID for every row in this batch

# ❌ WRONG — generates a different UUID for every single row
df["run_id"] = df.apply(lambda _: str(uuid.uuid4()), axis=1)

# Querying audit columns:
# SELECT * FROM orders_audit WHERE source_file = 'v2'     → all rows from v2
# SELECT * FROM orders_audit WHERE run_id = '<uuid>'      → all rows from one run
# SELECT MAX(loaded_at) FROM orders_audit                 → last load time


# ══════════════════════════════════════════════════════════
#  TOPIC 4 — PIPELINE CHECKPOINTING (STATE TABLE)
# ══════════════════════════════════════════════════════════

# Problem: pipeline runs daily. If it crashes or reruns, it must not
# reprocess files that already succeeded.
# Solution: a state table that records which files completed successfully.

# Step 1 — create state table
with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pipeline_state (
            file_name   TEXT PRIMARY KEY,   -- prevents duplicate entries
            status      TEXT,               -- 'success' or 'failed'
            loaded_at   TEXT,
            rows_loaded INTEGER
        )
    """))

def process_file(filepath, engine):
    file_name = os.path.basename(filepath)   # portable filename extraction

    # Step 2 — check state BEFORE processing
    processed = pd.read_sql(
        "SELECT file_name FROM pipeline_state WHERE status = 'success'",
        engine
    )["file_name"].tolist()

    if file_name in processed:
        print(f"[SKIP] {file_name} already processed.")
        return

    # Step 3 — process and load
    df = pd.read_csv(filepath)
    df.to_sql("orders_batched", engine, if_exists="append", index=False)

    # Step 4 — record success AFTER load confirms
    with engine.begin() as conn:
        conn.execute(
            text("""
                INSERT INTO pipeline_state (file_name, status, loaded_at, rows_loaded)
                VALUES (:file_name, :status, :loaded_at, :rows_loaded)
            """),
            {
                "file_name":   file_name,
                "status":      "success",
                "loaded_at":   datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
                "rows_loaded": len(df),
            }
        )
    print(f"[DONE] {file_name}: {len(df)} rows loaded.")

# Idempotent — safe to call multiple times, only processes once
process_file("day5d/batch_jan.csv", engine)   # → [DONE] 100 rows loaded
process_file("day5d/batch_jan.csv", engine)   # → [SKIP] already processed

# RULES:
# 1. Check state BEFORE processing — not after
# 2. Write to state AFTER the load succeeds — not before (don't pre-mark as done)
# 3. file_name as PRIMARY KEY — prevents duplicate checkpoint rows
# 4. os.path.basename(filepath) — cross-platform, handles both / and \
# 5. This pattern is called idempotency — running N times = running once


# ══════════════════════════════════════════════════════════
#  TOPIC 5 — os.path.basename vs .split("/")
# ══════════════════════════════════════════════════════════

import os

filepath = "day5d/batch_jan.csv"

# ❌ Fragile — only works with forward slashes (fails on Windows backslash paths)
file_name = filepath.split("/")[-1]

# ✅ Portable — works on all OS, handles both / and \
file_name = os.path.basename(filepath)

# Other useful os.path functions in pipelines:
os.path.basename("data/files/jan.csv")    # → "jan.csv"
os.path.dirname("data/files/jan.csv")     # → "data/files"
os.path.splitext("jan.csv")               # → ("jan", ".csv")
os.path.exists("day5d/batch_jan.csv")     # → True/False — check before reading


# ══════════════════════════════════════════════════════════
#  DAY 5d — KEY TAKEAWAYS
# ══════════════════════════════════════════════════════════
"""
PIPELINE A — CHUNKED LOADING:
  1.  pd.read_csv(chunksize=N) → iterator; loop over it, never list() it
  2.  Counters (chunks, valid, rejected) must be defined OUTSIDE the loop
  3.  if_exists="append" every chunk — "replace" would wipe previous chunks
  4.  Compute validation mask once, apply with mask/~mask — never duplicate
  5.  .copy() after slicing before assigning new columns

PIPELINE B — UPSERT + AUDIT COLUMNS:
  6.  INSERT OR REPLACE requires the table to exist — CREATE TABLE IF NOT EXISTS first
  7.  PRIMARY KEY on upsert column is mandatory — no key = no dedup = duplicates
  8.  df.to_dict(orient="records") → list of dicts → directly usable by conn.execute()
  9.  INSERT OR REPLACE replaces the whole row, not just changed columns
  10. Audit columns: loaded_at (timestamp), source_file (origin), run_id (batch ID)
  11. run_id = str(uuid.uuid4()) — generate ONCE per batch, not per row

PIPELINE C — CHECKPOINTING:
  12. State table tracks which files succeeded — prevents reprocessing on rerun
  13. Check state BEFORE processing; write state AFTER successful load
  14. file_name as PRIMARY KEY in state table — prevents duplicate checkpoint rows
  15. os.path.basename(filepath) — portable filename extraction, not .split("/")
  16. Idempotency: running the same pipeline N times produces the same result as once
"""

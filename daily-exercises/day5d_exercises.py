"""
=============================================================
 DATA ENGINEERING PRACTICE — DAY 5d
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

engine = create_engine("sqlite:///day5d/warehouse.db")


# ══════════════════════════════════════════════════════════
#  PIPELINE A — CHUNKED LOADING
# ══════════════════════════════════════════════════════════

reader = pd.read_csv("day5d/orders_large.csv", chunksize=50)
chunks_processed    = 0
total_valid_rows    = 0
total_rejected_rows = 0

for chunk in reader:
    mask         = (
        chunk["quantity"].notnull()   & (chunk["quantity"]   > 0) &
        chunk["unit_price"].notnull() & (chunk["unit_price"] > 0)
    )
    valid_rows   = chunk[mask].copy()
    invalid_rows = chunk[~mask].copy()
    invalid_rows["reject_reason"] = "null or invalid quantity/unit_price"

    valid_rows.to_sql("orders_clean",    engine, if_exists="append", index=False)
    invalid_rows.to_sql("orders_rejected", engine, if_exists="append", index=False)

    chunks_processed    += 1
    total_valid_rows    += len(valid_rows)
    total_rejected_rows += len(invalid_rows)

print(f"Total chunks processed : {chunks_processed}")
print(f"Total valid rows loaded: {total_valid_rows}")
print(f"Total rejected rows    : {total_rejected_rows}")


# ══════════════════════════════════════════════════════════
#  PIPELINE A — OUTPUT (VERIFIED)
# ══════════════════════════════════════════════════════════
"""
Total chunks processed : 4
Total valid rows loaded: 91
Total rejected rows    : 109
"""


# ══════════════════════════════════════════════════════════
#  PIPELINE A — EVALUATION & REVIEW
# ══════════════════════════════════════════════════════════
"""
SCORE: 9/10

ITERATION 1 — BUGS FOUND & FIXED:

BUG 1 — validation mask written twice
  ❌ valid_rows   = chunk[(notnull & > 0 & notnull & > 0)]
     invalid_rows = chunk[~(notnull & > 0 & notnull & > 0)]
     Same complex condition copy-pasted — if the rule changes, must update in two places
  ✅ mask         = (notnull & > 0 & notnull & > 0)
     valid_rows   = chunk[mask]
     invalid_rows = chunk[~mask]

BUG 2 — no reject_reason on invalid rows
  ❌ invalid_rows loaded without any reason column
  ✅ invalid_rows["reject_reason"] = "null or invalid quantity/unit_price"

POLISH NOTE — explicit .copy() on slices
  invalid_rows = chunk[~mask]          ← slice, no explicit copy
  invalid_rows = chunk[~mask].copy()   ← explicit copy, always safe
  Works in pandas 2.0+ either way (Copy-on-Write), but .copy() makes intent clear.

KEY LEARNINGS — PIPELINE A:
  1. pd.read_csv(chunksize=N) returns an iterator — loop over it, never call list() on it
  2. Compute validation mask once, apply with mask and ~mask — never duplicate the condition
  3. if_exists="append" on every chunk — the table accumulates across all chunks
  4. Counters (chunks_processed, total_valid, total_rejected) must live outside the loop
  5. valid + rejected counts must equal total source rows — verify after run
"""


# ══════════════════════════════════════════════════════════
#  PIPELINE B — UPSERT + AUDIT COLUMNS
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

# Table must exist before INSERT OR REPLACE can run
with engine.begin() as conn:
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

for data, source_file in [(v1, "v1"), (v2, "v2")]:
    df = pd.DataFrame(data)
    df["loaded_at"]   = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    df["source_file"] = source_file
    df["run_id"]      = str(uuid.uuid4())   # one unique ID per pipeline run/batch

    with engine.begin() as conn:   # upsert — replaces row if order_id exists, inserts if new
        conn.execute(
            text("""
                INSERT OR REPLACE INTO orders_audit
                    (order_id, customer, amount, loaded_at, source_file, run_id)
                VALUES
                    (:order_id, :customer, :amount, :loaded_at, :source_file, :run_id)
            """),
            df.to_dict(orient="records")
        )

    result_df = pd.read_sql("SELECT * FROM orders_audit", engine)
    print(f"After loading {source_file}:")
    print(result_df.to_string(index=False))
    print()


# ══════════════════════════════════════════════════════════
#  PIPELINE B — OUTPUT (VERIFIED)
# ══════════════════════════════════════════════════════════
"""
After loading v1:
 order_id customer  amount           loaded_at source_file  run_id
        1    Alice   500.0  2026-07-12 05:37:15          v1  <uuid>
        2      Bob   300.0  2026-07-12 05:37:15          v1  <uuid>
        3      Eve   750.0  2026-07-12 05:37:15          v1  <uuid>

After loading v2:
 order_id customer  amount           loaded_at source_file  run_id
        1    Alice   500.0  2026-07-12 05:37:15          v1  <uuid-1>   ← unchanged
        2      Bob   350.0  2026-07-12 05:37:15          v2  <uuid-2>   ← amount updated
        3      Eve   800.0  2026-07-12 05:37:15          v2  <uuid-2>   ← amount updated
        4  Charlie   200.0  2026-07-12 05:37:15          v2  <uuid-2>   ← new
        5    Diana   450.0  2026-07-12 05:37:15          v2  <uuid-2>   ← new
"""


# ══════════════════════════════════════════════════════════
#  PIPELINE B — EVALUATION & REVIEW
# ══════════════════════════════════════════════════════════
"""
SCORE: 9/10

CORRECT:
  - CREATE TABLE IF NOT EXISTS before INSERT OR REPLACE — required
  - Audit columns (loaded_at, source_file, run_id) added to every row
  - run_id generated once per batch — correct, one ID per load event
  - INSERT OR REPLACE correctly updated order_ids 2 & 3, inserted 4 & 5
  - order_id 1 (Alice) untouched — only rows in v2 were affected

POLISH NOTE — misleading comment
  ❌ with engine.begin() as conn:  # checking against existing order_ids
  ✅ with engine.begin() as conn:  # upsert — replaces if order_id exists, inserts if new
     INSERT OR REPLACE handles the check internally via the PRIMARY KEY constraint.
     No explicit lookup needed — SQLite does it automatically.

KEY LEARNINGS — PIPELINE B:
  1. INSERT OR REPLACE requires the table to exist first — to_sql creates it, raw SQL does not
  2. PRIMARY KEY on the upsert column is mandatory — without it, INSERT OR REPLACE
     has no key to check and inserts duplicates instead of replacing
  3. df.to_dict(orient="records") converts DataFrame to list of dicts for conn.execute()
  4. Audit columns (loaded_at, source_file, run_id) are added in Python before the SQL call
  5. run_id = str(uuid.uuid4()) — generate once per batch, same ID for all rows in that run
  6. INSERT OR REPLACE vs APPEND: append adds duplicates; INSERT OR REPLACE deduplicates by key
"""


# ══════════════════════════════════════════════════════════
#  PIPELINE C — CHECKPOINTING
# ══════════════════════════════════════════════════════════

with engine.begin() as conn:
    conn.execute(text("""
        CREATE TABLE IF NOT EXISTS pipeline_state (
            file_name   TEXT PRIMARY KEY,
            status      TEXT,
            loaded_at   TEXT,
            rows_loaded INTEGER
        )
    """))

def process_file(filepath, engine):
    file_name = os.path.basename(filepath)   # portable: handles both / and \ paths

    existing = pd.read_sql(
        "SELECT file_name FROM pipeline_state WHERE status = 'success'",
        engine
    )["file_name"].tolist()

    if file_name in existing:
        print(f"[SKIP] {file_name} already processed.")
        return

    df = pd.read_csv(filepath)
    df.to_sql("orders_batched", engine, if_exists="append", index=False)

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


process_file("day5d/batch_jan.csv", engine)
process_file("day5d/batch_feb.csv", engine)
process_file("day5d/batch_jan.csv", engine)   # must skip — already processed

print()
print("pipeline_state:")
print(pd.read_sql("SELECT * FROM pipeline_state", engine).to_string(index=False))


# ══════════════════════════════════════════════════════════
#  PIPELINE C — OUTPUT (VERIFIED)
# ══════════════════════════════════════════════════════════
"""
[DONE] batch_jan.csv: 100 rows loaded.
[DONE] batch_feb.csv: 100 rows loaded.
[SKIP] batch_jan.csv already processed.

pipeline_state:
    file_name  status           loaded_at  rows_loaded
batch_jan.csv success 2026-07-12 05:37:15          100
batch_feb.csv success 2026-07-12 05:37:15          100
"""


# ══════════════════════════════════════════════════════════
#  PIPELINE C — EVALUATION & REVIEW
# ══════════════════════════════════════════════════════════
"""
SCORE: 9/10

CORRECT:
  - CREATE TABLE IF NOT EXISTS pipeline_state — correct first-run handling
  - Checks state table before processing — correct idempotency pattern
  - Loads data with if_exists="append" — correct for batched accumulation
  - Writes success record to pipeline_state after load — correct checkpoint
  - batch_jan.csv skipped on second call — proves idempotency works

POLISH NOTE — filepath.split("/") is not portable
  ❌ file_name = filepath.split("/")[-1]   → breaks on Windows backslash paths
  ✅ file_name = os.path.basename(filepath) → handles / and \\ on all platforms

POLISH NOTE — print pipeline_state at end
  Always print (or log) the checkpoint table after a run so you can verify
  which files were processed without opening a DB browser.

KEY LEARNINGS — PIPELINE C:
  1. Checkpointing = state table that records which files/batches succeeded
  2. Check BEFORE processing — skip if already in state table with status='success'
  3. Write AFTER processing — only record success once the load is confirmed
  4. os.path.basename() for cross-platform filename extraction — not .split("/")
  5. file_name as PRIMARY KEY — prevents duplicate checkpoint entries
  6. This pattern makes any pipeline idempotent — safe to rerun without side effects

OVERALL DAY 5d SUMMARY:
  Pipeline A — 9/10  Chunked iteration, mask-once pattern, reject_reason, counters
  Pipeline B — 9/10  CREATE TABLE first, INSERT OR REPLACE, audit columns, uuid run_id
  Pipeline C — 9/10  State table, check-before/write-after, os.path.basename
"""

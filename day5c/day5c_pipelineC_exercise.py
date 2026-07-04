from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime

engine = create_engine("sqlite:///day5c/sales.db")

day1 = [
    {"order_id": 1, "customer": "Alice", "amount": 500},
    {"order_id": 2, "customer": "Bob",   "amount": 300},
]

day2 = [
    {"order_id": 1, "customer": "Alice", "amount": 500},
    {"order_id": 2, "customer": "Bob",   "amount": 300},
    {"order_id": 3, "customer": "Eve",   "amount": 750},
]

def log(step, message, rows=None):                      #for creating pipeline logs
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_info = f"{rows}" if rows is not None else ""
    print(f"[{ts}] [{step}] {message}{row_info}")


def run_incremental_pipeline(df, engine):
    df = pd.DataFrame(df)

    # Ensure target table exists
    with engine.begin() as conn:
        conn.execute(text("""
            CREATE TABLE IF NOT EXISTS orders_incremental (
                order_id INTEGER PRIMARY KEY,
                customer TEXT,
                amount REAL
            )
        """))

    existing_ids = pd.read_sql("SELECT order_id FROM orders_incremental", engine)["order_id"].tolist()

    new_rows = df[~df["order_id"].isin(existing_ids)]
    skipped = df[df["order_id"].isin(existing_ids)]

    if not new_rows.empty:
        new_rows.to_sql("orders_incremental", engine, if_exists="append", index=False)

    log("INCREMENTAL LOAD", "New Rows added: ", len(new_rows))
    log("INCREMENTAL LOAD", "Rows skipped (already loaded): ", len(skipped))


run_incremental_pipeline(day1, engine)    
run_incremental_pipeline(day2, engine)
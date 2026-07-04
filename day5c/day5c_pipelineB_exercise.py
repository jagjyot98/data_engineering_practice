from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime

engine = create_engine("sqlite:///day5c/sales.db")

orders_data = [
    {"order_id": 1, "customer_id": 101, "product": "Laptop",  "amount": 999.99},
    {"order_id": 2, "customer_id": 102, "product": "Phone",   "amount": 599.99},
    {"order_id": 3, "customer_id": 103, "product": "Tablet",  "amount": 449.99},
    {"order_id": 4, "customer_id": 999, "product": "Monitor", "amount": 299.99},  # unknown customer
    {"order_id": 5, "customer_id": 101, "product": "Mouse",   "amount": 49.99},
    {"order_id": 6, "customer_id": None,"product": "Keyboard","amount": 79.99},   # missing customer_id
]

customers_data = [
    {"customer_id": 101, "name": "Alice",   "region": "North"},
    {"customer_id": 102, "name": "Bob",     "region": "South"},
    {"customer_id": 103, "name": "Charlie", "region": "East"},
]

pd.DataFrame(orders_data).to_csv("day5c/orders.csv", index=False)
pd.DataFrame(customers_data).to_csv("day5c/customers.csv", index=False)

def log(step, message, rows=None):                      #for creating pipeline logs
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_info = f"{rows}" if rows is not None else ""
    print(f"[{ts}] [{step}] {message}{row_info}")

def extract(filepath):                                  #for extracting outsourced data (CSV File)
    df = pd.read_csv(filepath)
    log("EXTRACT", f"Extracted data from '{filepath}' | Rows extracted: ", len(df))
    return df

def validate(df):                                       #for filtering out valid and invalid data from orders data
    mask_valid = (
        df["customer_id"].notna()
    )
    df_valid   = df[mask_valid].copy()
    df_invalid = df[~mask_valid].copy()
    df_invalid["reject_reason"] = "null or invalid order data"
    log("VALIDATE", "Validated orders data | Valid Rows: ",len(df_valid))
    log("VALIDATE", "Found invalid orders | Invalid Rows: ",len(df_invalid))
    return df_valid, df_invalid

def transform(df_cust, df_ord):                                      #for merging and filtering out matched and unmatched data between customers and orders
    df_customers = df_cust.copy()
    df_orders = df_ord.copy()
    df_merged = df_orders.merge(df_customers, on="customer_id", how="left")
    df_merged["customer_found"] = df_merged["name"].notna()
    df_matched   = df_merged[df_merged["customer_found"] == True].copy()
    df_unmatched = df_merged[df_merged["customer_found"] == False].copy()
    log("TRANSFORM", "Transformed orders data | Matched Rows: ",len(df_matched))
    log("TRANSFORM", "Transformed orders data | Unmatched Rows: ",len(df_unmatched))
    return df_matched, df_unmatched

def load(df, table_name, engine):                       #for loading provided data into a database table 
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    log("LOAD", f"Loaded data into table '{table_name}' | Rows loaded: ", len(df))

def run_orders_pipeline(engine):                        #running the entire pipeline for sales data processing  
    orders_data = extract("day5c/orders.csv")
    customers_data = extract("day5c/customers.csv")

    valid_orders, invalid_orders = validate(orders_data)

    matched_orders, unmatched_orders = transform(customers_data, valid_orders)

    load(matched_orders, "orders_enriched", engine)
    load(unmatched_orders, "orders_unmatched", engine)

    print(f"Orders enriched: {len(matched_orders)}")        #pipeline result summary
    print(f"Orders unmatched: {len(unmatched_orders)}")
    print(f"Orders rejected: {len(invalid_orders)}")

run_orders_pipeline(engine)
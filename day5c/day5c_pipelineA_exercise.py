from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime

engine = create_engine("sqlite:///day5c/sales.db")

sales_data = [
    {"order_id": 1,  "customer": "Alice",   "product": "Laptop",  "quantity": 2,    "unit_price": 999.99,  "order_date": "2024-01-15"},
    {"order_id": 2,  "customer": "Bob",     "product": "Phone",   "quantity": 1,    "unit_price": 599.99,  "order_date": "2024-01-15"},
    {"order_id": 3,  "customer": "Charlie", "product": "Laptop",  "quantity": None, "unit_price": 999.99,  "order_date": "2024-01-16"},
    {"order_id": 4,  "customer": None,      "product": "Tablet",  "quantity": 3,    "unit_price": 449.99,  "order_date": "2024-01-16"},
    {"order_id": 5,  "customer": "Eve",     "product": "Phone",   "quantity": -1,   "unit_price": 599.99,  "order_date": "2024-01-17"},
    {"order_id": 6,  "customer": "Frank",   "product": "Laptop",  "quantity": 1,    "unit_price": 999.99,  "order_date": "2024-01-17"},
    {"order_id": 7,  "customer": "Grace",   "product": "Tablet",  "quantity": 2,    "unit_price": 449.99,  "order_date": "2024-01-18"},
    {"order_id": 8,  "customer": "Henry",   "product": "Phone",   "quantity": 1,    "unit_price": -50,     "order_date": "2024-01-18"},
]
pd.DataFrame(sales_data).to_csv("day5c/sales.csv", index=False)

def log(step, message, rows=None):                      #for creating puipoeline logs
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_info = f"{rows}" if rows is not None else ""
    print(f"[{ts}] [{step}] {message}{row_info}")

def extract(filepath):                                  #for extracting outsourced data (CSV File)
    df = pd.read_csv(filepath)
    log("EXTRACT", "Read sales data from csv | Rows extracted: ", len(df))
    return df

def validate(df):                                       #for filtering out valid and invalid data from extracted data
    mask_valid = (
        df["customer"].notna() &
        df["quantity"].notna() & (df["quantity"] > 0) &
        df["unit_price"].notna() & (df["unit_price"] > 0)
    )
    df_valid   = df[mask_valid].copy()
    df_invalid = df[~mask_valid].copy()
    df_invalid["reject_reason"] = "null or invalid order data (customer/quantity/unit_price)"
    log("VALIDATE", "Validated sales data | Valid Rows: ", len(df_valid))
    log("VALIDATE", "Found invalid sales data | Invalid Rows: ", len(df_invalid))
    return df_valid, df_invalid

def transform(df):                                      #for transforming valid data into clean and usable format
    df_transformed = df.copy()
    
    df_transformed["customer"]    = df_transformed["customer"].str.strip().str.lower()
    df_transformed["product"]    = df_transformed["product"].str.strip().str.lower()
    
    df_transformed["order_date"] = pd.to_datetime(df_transformed["order_date"], errors="coerce")
    
    df_transformed["total_price"] = df_transformed["quantity"] * df_transformed["unit_price"]       #adding new column for total_price for each processing order

    df_transformed["order_month"] = df_transformed["order_date"].dt.strftime("%Y-%m")
    log("TRANSFORM", "Transformed sales data | Rows transformed: ", len(df_transformed))
    return df_transformed

def load(df, table_name, engine):                       #for loading provided data into a database table 
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    log("LOAD", f"Loaded data into table '{table_name}' | Rows loaded: ", len(df))

def aggregate_sales_by_product(engine):                 #generating overall sales's aggregate (by product) for clear readbility
    query = text("""
        SELECT product, SUM(total_price) AS total_revenue, count(*) as orders
        FROM sales_clean
        GROUP BY product
        ORDER BY total_revenue DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    log("AGGREGATE", "Aggregated sales data by product | Rows aggregated: ", len(df))
    return df

def run_sales_pipeline(engine):                               #running the entire pipeline for sales data processing  
    extracted_data = extract("day5c/sales.csv")

    valid_data, invalid_data = validate(extracted_data)

    transformed_data = transform(valid_data)

    load(transformed_data, "sales_clean", engine)
    load(invalid_data, "sales_rejected", engine)

    aggregated_data = aggregate_sales_by_product(engine)
    print("Sales by product:")
    print(aggregated_data)

    result = {                                          #pipeline result summary
        "status":        "success",
        "rows_extracted": len(extracted_data),
        "rows_valid":     len(valid_data),
        "rows_rejected":  len(invalid_data),
        "rows_loaded":    len(transformed_data),
        "errors":         [],
    }
    return result

print(run_sales_pipeline(engine))

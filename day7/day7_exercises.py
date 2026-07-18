import psycopg2
from psycopg2.extras import execute_values
import pandas as pd
from datetime import datetime

DB = {
    "host":     "localhost",
    "port":     5432,
    "dbname":   "postgres",
    "user":     "postgres",
    "password": "root",
}

filepath = "day7/sales.csv"

def sales_clean_definition():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
                                        #sales_clean table creation
    cur.execute("""                         
        CREATE TABLE IF NOT EXISTS sales_clean (
            order_id         INTEGER PRIMARY KEY,
            customer         VARCHAR(100),
            region           VARCHAR(100),
            product_category VARCHAR(100),
            product_name     VARCHAR(100),
            quantity         INTEGER,
            unit_price       NUMERIC(10,2),
            order_date       DATE,
            total_price      NUMERIC(10,2),
            loaded_at        TIMESTAMP
                )
        """)
    conn.commit()
    log("DEFINE","Table 'sales_clean' defined")
    cur.close()
    conn.close()

def sales_reject_definition():
    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
                                        #sales_rejected table creation
    cur.execute("""                         
        CREATE TABLE IF NOT EXISTS sales_rejected (
            order_id         INTEGER PRIMARY KEY,
            customer         VARCHAR(100),
            region           VARCHAR(100),
            product_category VARCHAR(100),
            product_name     VARCHAR(100),
            quantity         INTEGER,
            unit_price       NUMERIC(10,2),
            order_date       DATE
            )
        """)
    conn.commit()
    log("DEFINE","Table 'sales_rejected' defined")
    cur.close()
    conn.close()

def log(step, message, rows=None):                      #for creating pipeline logs
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
    df_invalid["reject_reason"] = "null or invalid sales data (customer/quantity/unit_price)"
    log("VALIDATE", "Validated sales data | Valid Rows: ", len(df_valid))
    log("VALIDATE", "Found invalid sales data | Invalid Rows: ", len(df_invalid))
    return df_valid, df_invalid

def transform(df):                                      #for transforming valid data into clean and usable format
    df_transformed = df.copy()
    
    df_transformed["customer"]    = df_transformed["customer"].str.strip().str.lower()
    df_transformed["region"]       = df_transformed["region"].str.strip().str.lower()
    df_transformed["product_category"]    = df_transformed["product_category"].str.strip().str.lower()
    df_transformed["product_name"]    = df_transformed["product_name"].str.strip().str.lower()
    df_transformed["order_date"] = pd.to_datetime(df_transformed["order_date"], errors="coerce")

    df_transformed["total_price"] = df_transformed["quantity"] * df_transformed["unit_price"]       #adding new column for total_price for each processing order
    df_transformed["loaded_at"] = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    log("TRANSFORM", "Transformed sales data | Rows transformed: ", len(df_transformed))
    return df_transformed

def load_sales_clean(df):
    sales_clean_definition()

    cols = [
    "order_id", "customer", "region", "product_category", "product_name",
    "quantity", "unit_price", "order_date", "total_price", "loaded_at"
]
    sales_tuple = [tuple(row) for row in df[cols].itertuples(index=False)]

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    execute_values(cur,"INSERT INTO sales_clean (order_id, customer, region, product_category, product_name, quantity, unit_price, order_date, total_price, loaded_at) VALUES %s ON CONFLICT (order_id) DO NOTHING",    
    sales_tuple
    )
    conn.commit()
    log("INSERT","Validated data loaded into 'sales_clean' table  |  Rows Inserted: ",len(df))
    cur.close()
    conn.close()

def load_sales_rejected(df):
    sales_reject_definition()

    cols = [
    "order_id", "customer", "region", "product_category", "product_name",
    "quantity", "unit_price", "order_date"
    ]
    # astype(object) keeps None as Python None through itertuples (float64 would convert it back to NaN)
    df_clean = df[cols].astype(object).where(pd.notna(df[cols]), other=None)
    sales_tuple = [tuple(row) for row in df_clean.itertuples(index=False)]

    conn = psycopg2.connect(**DB)
    cur = conn.cursor()
    execute_values(cur,"INSERT INTO sales_rejected (order_id, customer, region, product_category, product_name, quantity, unit_price, order_date) VALUES %s ON CONFLICT (order_id) DO NOTHING",
    sales_tuple
    )
    conn.commit()
    log("INSERT","Rejected data loaded into 'sales_rejected' table  |  Rows Inserted: ",len(df_clean))
    cur.close()
    conn.close()

def aggregate_sales_by_product():
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()
    log("AGGREGATE", "Aggregated sales by product_category")
    cur.execute("SELECT product_category, count(*) as orders, SUM(total_price) AS total_revenue, ROUND(AVG(total_price), 2) AS avg_order_value FROM sales_clean GROUP BY product_category ORDER BY total_revenue DESC")
    for row in cur.fetchall():
        print(row)
    cur.close()
    conn.close()

def aggregate_sales_by_region():
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()
    log("AGGREGATE", "Aggregated sales by region")
    cur.execute("SELECT region, count(*) as orders, SUM(total_price) AS total_revenue FROM sales_clean GROUP BY region ORDER BY total_revenue DESC")
    for row in cur.fetchall():
        print(row)
    cur.close()
    conn.close()

def aggregate_sales_by_top_5_cust():
    conn = psycopg2.connect(**DB)
    cur  = conn.cursor()
    log("AGGREGATE", "Aggregated sales by Top 5 Customers")
    cur.execute("SELECT customer, COUNT(*) AS orders, SUM(total_price) AS total_spend FROM sales_clean GROUP BY customer ORDER BY total_spend DESC LIMIT 5")
    for row in cur.fetchall():
        print(row)
    cur.close()
    conn.close()

def main_pipeline_run():
    raw_data = extract(filepath)

    valid_sales, invalid_sales = validate(raw_data)

    transformed_sales = transform(valid_sales)

    load_sales_clean(transformed_sales)

    load_sales_rejected(invalid_sales)

    aggregate_sales_by_product()
    aggregate_sales_by_region()
    aggregate_sales_by_top_5_cust()

    result = {                                          #pipeline result summary
        "status":        "success",
        "rows_extracted": len(raw_data),
        "rows_valid":     len(valid_sales),
        "rows_rejected":  len(invalid_sales),
        "rows_loaded":    len(transformed_sales),
        "errors":         [],
    }
    return result

print(main_pipeline_run())


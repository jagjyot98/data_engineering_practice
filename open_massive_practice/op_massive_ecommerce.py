from sqlalchemy import create_engine, text
import pandas as pd
from datetime import datetime

engine = create_engine("sqlite:///open_massive_practice/ecommerce_orders.db")

def log(step, message, rows=None):                      #for creating pipeline logs
    ts = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    row_info = f"{rows}" if rows is not None else ""
    print(f"[{ts}] [{step}] {message}{row_info}")

def load(df, table_name, engine):                       #for loading provided data into a database table 
    df.to_sql(table_name, con=engine, if_exists="replace", index=False)
    log("LOAD", f"Loaded data into table '{table_name}' | Rows loaded: ", len(df))

def extract(filepath):                                  #for extracting outsourced data (CSV File)
    df = pd.read_csv(filepath)
    log("EXTRACT", "Read ecommerce data from csv | Rows extracted: ", len(df))
    return df

def parse_mixed_dates(series):                          #for parsing dates in mixed formats (YYYY-MM-DD, MM/DD/YYYY, DD-MM-YYYY) into a standard format
    known_formats = ["%Y-%m-%d", "%m/%d/%Y", "%d-%m-%Y"]
    result = pd.Series(pd.NaT, index=series.index)

    for fmt in known_formats:
        mask = result.isna()
        parsed = pd.to_datetime(series[mask], format=fmt, errors="coerce")
        result[mask] = parsed

    return result

def clean_amounts_and_quantities(df):                            #for cleaning and converting amount and quantity columns into numeric values
    processing_amount_and_quantity = df.copy()

    is_dirty = processing_amount_and_quantity["amount"].str.contains(r"[\$,]", regex=True, na=False)
    # print(f"Dirty amount values: {is_dirty.sum():,} / {len(processing_amount_and_quantity):,}")       #for testing
    # print(processing_amount_and_quantity.loc[is_dirty, "amount"].head(10).tolist())

    processing_amount_and_quantity["amount_clean"] = (
        processing_amount_and_quantity["amount"]
        .str.replace(r"[\$,]", "", regex=True)
        .astype(float)
    )

    processing_amount_and_quantity["quantity_clean"] = (
        processing_amount_and_quantity["quantity"].str.replace(r"[^\d]", "", regex=True).astype(int)
    )
    log("CLEAN", "Cleaned amount and quantity columns | Rows processed: ", len(processing_amount_and_quantity))

    # print(processing_amount_and_quantity["amount_clean"].isna().sum(), "rows failed to convert")              #for testing (should be 0)
    # print(processing_amount_and_quantity[["amount", "amount_clean"]].loc[is_dirty].head())
    return processing_amount_and_quantity

def transform(df):                                      #for transforming valid data into clean and usable format
    df_transformed = df.copy()
    
    df_transformed["customer_name"]    = df_transformed["customer_name"].str.strip().str.lower()
    df_transformed["customer_email"]    = df_transformed["customer_email"].str.strip().str.lower()
    df_transformed["product_category"]    = df_transformed["product_category"].str.strip().str.lower()
    df_transformed["product_name"]    = df_transformed["product_name"].str.strip().str.lower()
    df_transformed["payment_method"]    = df_transformed["payment_method"].str.strip().str.lower()
    df_transformed["shipping_country"]    = df_transformed["shipping_country"].str.strip().str.lower()
    df_transformed["order_status"]    = df_transformed["order_status"].str.strip().str.lower()

    log("TRANSFORM", "Transformed ecommerce data | Rows transformed: ", len(df_transformed))
    return df_transformed

def validate(df):                                       #for filtering out valid and invalid data from extracted data
    mask_valid = (
        df["customer_email"].notna() &
        df["shipping_country"].notna() &
        df["discount_pct"].notna() &
        df["coupon_code"].notna() &
        df["unit_price"].notna() & (df["unit_price"] > 0) &
        df["amount_clean"].notna() & (df["amount_clean"] > 0) &
        df["quantity_clean"].notna() & (df["quantity_clean"] > 0)
    )
    df_valid   = df[mask_valid].copy()
    df_invalid = df[~mask_valid].copy()
    df_invalid["reject_reason"] = "null or invalid order data"

    log("VALIDATE", "Validated ecommerce data | Valid Rows: ", len(df_valid))
    log("VALIDATE", "Found invalid ecommerce data | Invalid Rows: ", len(df_invalid))
    return df_valid, df_invalid

def aggregate_ecommerce_by_product_category(engine):                 #generating overall ecommerce's aggregate (by product_category) for clear readbility
    query = text("""
        SELECT product_category, SUM(amount_clean) AS total_revenue, count(*) as orders
        FROM ecommerce_clean
        GROUP BY product_category
        ORDER BY total_revenue DESC
    """)
    with engine.connect() as conn:
        result = conn.execute(query)
        df = pd.DataFrame(result.fetchall(), columns=result.keys())
    log("AGGREGATE", "Aggregated ecommerce data by product_category | Rows aggregated: ", len(df))
    return df

def run_ecommerce_pipeline(engine):                             #running the entire pipeline for ecommerce data processing  
    extracted_data = extract("datasets/ecommerce_orders_raw.csv")
    
    extracted_data = clean_amounts_and_quantities(extracted_data)

    valid_data, invalid_data = validate(extracted_data)

    transformed_data = transform(valid_data)

    load(transformed_data, "ecommerce_clean", engine)
    load(invalid_data, "ecommerce_rejected", engine)

    aggregated_data = aggregate_ecommerce_by_product_category(engine)
    print("Ecommerce by product category:")
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

print(run_ecommerce_pipeline(engine))
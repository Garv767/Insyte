import os
import sys
import math
import pandas as pd
import oracledb
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    # Attempt to connect using Wallet
    wallet_dir = os.path.abspath("wallet")
    db_user = os.getenv("APP_ADMIN_USER", "INSYTE_ADMIN")
    db_password = os.getenv("APP_ADMIN_PASSWORD", "AdminSecurePassword2026!")
    tns_name = "insyte_high"
    
    # Check if wallet config exists in .env
    if os.getenv("DB_SYS_USER"): 
        db_user = os.getenv("APP_ADMIN_USER", "INSYTE_ADMIN")
    else:
        # Fallback to local
        db_user = os.getenv("DB_USER", "ADMIN")
        db_password = os.getenv("DB_PASSWORD", "garv767@INSYTE")

    try:
        if os.path.exists(wallet_dir):
            conn = oracledb.connect(
                user=db_user,
                password=db_password,
                dsn=tns_name,
                config_dir=wallet_dir,
                wallet_location=wallet_dir,
                wallet_password=os.getenv("WALLET_PASSWORD", "")
            )
        else:
            conn = oracledb.connect(
                user=db_user,
                password=db_password,
                host=os.getenv("DB_HOST", "localhost"),
                port=int(os.getenv("DB_PORT", "1521")),
                service_name=os.getenv("DB_SERVICE", "FREEPDB1")
            )
        return conn
    except Exception as e:
        print(f"Error connecting: {e}")
        sys.exit(1)

def execute_schema(conn):
    print("Executing schema...")
    cursor = conn.cursor()
    schema_path = Path("database/02_schema.sql")
    with open(schema_path, "r", encoding="utf-8") as f:
        lines = f.readlines()
    
    # Remove comment lines and prompts before splitting
    valid_lines = []
    for line in lines:
        if not line.strip().startswith("--") and not line.strip().upper().startswith("PROMPT"):
            valid_lines.append(line)
            
    content = "\n".join(valid_lines)
    
    statements = content.split(";")
    for stmt in statements:
        clean_stmt = stmt.strip()
        # Remove slash if it exists
        clean_stmt = clean_stmt.strip('/')
        if not clean_stmt.strip(): continue
        try:
            cursor.execute(clean_stmt)
        except oracledb.Error as err:
            err_obj, = err.args
            if err_obj.code not in (942, 1920, 1921, 2289, 12003):
                print(f"Schema warning: {err_obj.message}")
    conn.commit()
    cursor.close()
    print("Schema rebuilt successfully.")

def load_data(conn):
    cursor = conn.cursor()
    cursor.execute("ALTER SESSION SET NLS_DATE_FORMAT = 'YYYY-MM-DD HH24:MI:SS'")
    cursor.execute("ALTER SESSION SET NLS_TIMESTAMP_FORMAT = 'YYYY-MM-DD HH24:MI:SS'")
    
    tables = [
        ("CUSTOMERS", "data/processed/customers.csv", "customer_id", 9),
        ("PRODUCTS", "data/processed/products.csv", "product_id", 10),
        ("PRODUCT_FEATURES", "data/processed/product_features.csv", "product_id", 13),
        ("REVIEWS", "data/processed/reviews.csv", "review_id", 12),
        ("REVIEW_IMAGES", "data/processed/review_images.csv", "image_id", 4)
    ]
    
    for table_name, csv_path, pk_col, col_count in tables:
        if not os.path.exists(csv_path):
            print(f"Skipping {table_name}, {csv_path} not found.")
            continue
            
        print(f"Loading {table_name}...")
        df = pd.read_csv(csv_path, low_memory=False)
        
        # Replace NaN with None for Oracle
        df = df.replace({float('nan'): None})
        
        # Identify date columns and convert to 'YYYY-MM-DD' strings for TO_DATE() binding
        date_cols = {}  # col_name -> col_index
        for i, col in enumerate(df.columns):
            if 'date' in col.lower():
                date_cols[col] = i
                def safe_date_str(v, _col=col):
                    if v is None or (isinstance(v, float) and pd.isna(v)):
                        return None
                    try:
                        return pd.to_datetime(v, dayfirst=True).strftime('%Y-%m-%d')
                    except:
                        return None
                df[col] = df[col].apply(safe_date_str)
            elif str(df[col].dtype).startswith('bool'):
                df[col] = df[col].astype(int)

        # Replace NaN introduced by bool conversion
        df = df.where(df.notna(), other=None)

        # Build INSERT with TO_DATE() for date columns
        bind_parts = []
        for i, col in enumerate(df.columns):
            if col in date_cols:
                bind_parts.append(f"TO_DATE(:{i+1}, 'YYYY-MM-DD')")
            else:
                bind_parts.append(f":{i+1}")

        col_names = ",".join(df.columns)
        bind_vars = ",".join(bind_parts)
        sql = f"INSERT INTO {table_name} ({col_names}) VALUES ({bind_vars})"
        data = [tuple(x) for x in df.to_numpy()]

        batch_size = 5000
        for i in range(0, len(data), batch_size):
            batch = data[i:i+batch_size]
            try:
                cursor.executemany(sql, batch)
            except Exception as e:
                print(f"Error inserting batch into {table_name}: {e}")
        conn.commit()
        print(f"  Loaded {len(data)} rows into {table_name}")

    cursor.close()

if __name__ == "__main__":
    conn = get_connection()
    execute_schema(conn)
    load_data(conn)
    conn.close()
    print("Database rebuild and load complete.")

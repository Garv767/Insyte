"""
INSYTE — Dynamic Ingestion & ETL Pipeline
Implements dynamic schema inspection, column variation detection, 
data sanitization, cancellation classification, and Oracle 23ai batch loading.
"""

import os
import sys
import re
from pathlib import Path
from datetime import datetime
import pandas as pd
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1521"))
DB_SERVICE = os.getenv("DB_SERVICE", "FREEPDB1")
DB_USER = os.getenv("APP_ADMIN_USER", "INSYTE_ADMIN")
DB_PASSWORD = os.getenv("APP_ADMIN_PASSWORD", "AdminSecurePassword2026!")

# Canonical Column Mappings
COLUMN_PATTERNS = {
    "invoice_no": [r"invoice.*", r"inv.*", r"order.*id", r"bill.*no"],
    "stock_code": [r"stock.*code", r"item.*code", r"sku", r"product.*id"],
    "description": [r"desc.*", r"product.*name", r"item.*name", r"title"],
    "quantity": [r"quant.*", r"qty", r"units", r"count"],
    "invoice_date": [r"invoice.*date", r"order.*date", r"date.*time", r"timestamp", r"^date$"],
    "unit_price": [r"price", r"unit.*price", r"rate", r"item.*price"],
    "customer_id": [r"customer.*id", r"client.*id", r"user.*id", r"cust.*id"],
    "country": [r"country", r"nation", r"region", r"shipping.*country"],
    # Optional Review & Media Mappings
    "review_text": [r"review.*text", r"comment", r"feedback", r"review"],
    "rating": [r"rating", r"review.*rating", r"stars", r"score"],
    "media_url": [r"media.*url", r"image.*url", r"photo.*url", r"video.*url"],
    "media_type": [r"media.*type", r"content.*type", r"mime.*type"]
}

def detect_column_mapping(df_columns):
    """Dynamically matches incoming dataframe columns against canonical targets."""
    mapping = {}
    lower_cols = {col.strip(): col for col in df_columns}
    
    for canonical_name, patterns in COLUMN_PATTERNS.items():
        matched = None
        for raw_name in lower_cols.keys():
            for pat in patterns:
                if re.fullmatch(pat, raw_name, re.IGNORECASE):
                    matched = lower_cols[raw_name]
                    break
            if matched:
                break
        if matched:
            mapping[canonical_name] = matched
            
    return mapping

def clean_description(val):
    if pd.isna(val):
        return "UNLABELLED ITEM"
    s = str(val).strip()
    s = re.sub(r"[^A-Za-z0-9 ]+", " ", s)
    s = re.sub(r"\s+", " ", s).strip().upper()
    return s[:500] if s else "UNLABELLED ITEM"

def parse_order_date(val):
    if pd.isna(val):
        return datetime.utcnow()
    try:
        return pd.to_datetime(val)
    except Exception:
        return datetime.utcnow()

def run_etl(source_file_path):
    print("=" * 70)
    print("INSYTE — Dynamic ETL & Data Ingestion Pipeline")
    print("=" * 70)
    print(f"Reading source file: {source_file_path}")

    path = Path(source_file_path)
    if not path.exists():
        print(f"[ERROR] Source file not found at: {source_file_path}")
        return

    # 1. Load Data
    if path.suffix.lower() in [".xlsx", ".xls"]:
        df = pd.read_excel(path)
    else:
        df = pd.read_csv(path, encoding="utf-8", low_memory=False)

    print(f"Loaded {len(df):,} total raw records.")

    # 2. Schema Detection & Mapping
    mapping = detect_column_mapping(df.columns)
    print("\n[Schema Mapping Layer Detected]")
    for canonical, source in mapping.items():
        print(f"  Canonical '{canonical:<15}' <-- Raw '{source}'")

    missing_core = [k for k in ["invoice_no", "stock_code", "quantity", "unit_price"] if k not in mapping]
    if missing_core:
        print(f"[ERROR] Missing indispensable core columns: {missing_core}")
        return

    # Check optional fields
    has_reviews = "review_text" in mapping or "rating" in mapping
    has_media = "media_url" in mapping
    print(f"  Optional Review Data: {'AVAILABLE' if has_reviews else 'NOT IN DATASET (Empty-State Mode)'}")
    print(f"  Optional Media Data : {'AVAILABLE' if has_media else 'NOT IN DATASET (Empty-State Mode)'}")

    # 3. Connect to Oracle Database 23ai
    try:
        import oracledb
        conn = oracledb.connect(
            user=DB_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            service_name=DB_SERVICE
        )
        cursor = conn.cursor()
        print("\n[Connected to Oracle Database 23ai Free]")
    except Exception as e:
        print(f"[ERROR connecting to Oracle]: {e}")
        return

    # 4. Process Records into Canonical Entities
    customers_set = {}      # customer_id -> country
    products_set = {}       # stock_code -> (orig_desc, norm_desc, unit_price)
    orders_set = {}         # invoice_no -> (customer_id, invoice_date, country, is_cancel, is_guest)
    order_items_list = []   # (invoice_no, stock_code, quantity, unit_price)
    adjustments_list = []   # (invoice_no, stock_code, quantity, unit_price, type, reason)
    audit_list = []         # (row_id, issue_type, issue_desc, raw_val)

    print("\nSanitizing, normalizing, and partitioning records...")
    for idx, row in df.iterrows():
        try:
            inv_no = str(row[mapping["invoice_no"]]).strip() if pd.notna(row.get(mapping["invoice_no"])) else None
            stock = str(row[mapping["stock_code"]]).strip().upper() if pd.notna(row.get(mapping["stock_code"])) else None
            
            if not inv_no or not stock:
                audit_list.append((idx, "NULL_KEY", "Missing invoice or stock code", str(row.to_dict())[:900]))
                continue

            raw_qty = row.get(mapping["quantity"], 0)
            raw_price = row.get(mapping["unit_price"], 0.0)

            try:
                qty = int(float(raw_qty))
                price = round(float(raw_price), 2)
            except Exception:
                audit_list.append((idx, "INVALID_NUMERIC", f"Bad qty={raw_qty} or price={raw_price}", inv_no))
                continue

            raw_desc = str(row.get(mapping.get("description"), "")) if mapping.get("description") else ""
            clean_desc = clean_description(raw_desc)
            inv_date = parse_order_date(row.get(mapping.get("invoice_date")))
            country = str(row.get(mapping.get("country"), "United Kingdom")).strip() if mapping.get("country") else "United Kingdom"

            cust_val = row.get(mapping.get("customer_id")) if "customer_id" in mapping else None
            cust_id = str(int(float(cust_val))).strip() if pd.notna(cust_val) else None
            is_guest = 1 if cust_id is None else 0

            is_cancellation = 1 if (inv_no.startswith("C") or qty < 0) else 0

            # Register Customer
            if cust_id:
                if cust_id not in customers_set:
                    customers_set[cust_id] = country

            # Register Product
            if stock not in products_set:
                products_set[stock] = (raw_desc[:500], clean_desc, price)

            # Register Order
            if inv_no not in orders_set:
                orders_set[inv_no] = (cust_id, inv_date, country, is_cancellation, is_guest)

            # Register Line Item or Adjustment
            if is_cancellation or qty <= 0:
                adjustments_list.append((inv_no, stock, qty, price, "CANCELLATION" if inv_no.startswith("C") else "RETURN", "Customer return / adjustment"))
            else:
                order_items_list.append((inv_no, stock, qty, price))

        except Exception as err:
            audit_list.append((idx, "ROW_PROCESSING_ERR", str(err)[:300], str(inv_no)[:50]))

    # 5. Batch Insert into Oracle Tables
    print(f"\n[Batch Insertion Summary]")
    print(f"  Customers to Insert : {len(customers_set):,}")
    print(f"  Products to Insert  : {len(products_set):,}")
    print(f"  Orders to Insert    : {len(orders_set):,}")
    print(f"  Order Items to Load : {len(order_items_list):,}")
    print(f"  Adjustments (Returns): {len(adjustments_list):,}")
    print(f"  Audit Diagnostics   : {len(audit_list):,}")

    # A. CUSTOMERS
    print("  Loading CUSTOMERS...")
    cust_data = [(cid, ctry, 0) for cid, ctry in customers_set.items()]
    cursor.executemany("""
        MERGE INTO CUSTOMERS tgt
        USING (SELECT :1 AS cid, :2 AS ctry, :3 AS ig FROM DUAL) src
        ON (tgt.customer_id = src.cid)
        WHEN NOT MATCHED THEN INSERT (customer_id, country, is_guest) VALUES (src.cid, src.ctry, src.ig)
    """, cust_data)

    # B. PRODUCTS
    print("  Loading PRODUCTS...")
    prod_data = [(stk, orig, norm, p) for stk, (orig, norm, p) in products_set.items()]
    cursor.executemany("""
        MERGE INTO PRODUCTS tgt
        USING (SELECT :1 AS stk, :2 AS orig, :3 AS norm, :4 AS p FROM DUAL) src
        ON (tgt.stock_code = src.stk)
        WHEN NOT MATCHED THEN INSERT (stock_code, original_description, normalized_description, unit_price)
                              VALUES (src.stk, src.orig, src.norm, src.p)
    """, prod_data)

    # C. ORDERS
    print("  Loading ORDERS...")
    ord_data = [(inv, cid, dt, ctry, is_c, is_g) for inv, (cid, dt, ctry, is_c, is_g) in orders_set.items()]
    cursor.executemany("""
        MERGE INTO ORDERS tgt
        USING (SELECT :1 AS inv, :2 AS cid, :3 AS dt, :4 AS ctry, :5 AS is_c, :6 AS is_g FROM DUAL) src
        ON (tgt.invoice_no = src.inv)
        WHEN NOT MATCHED THEN INSERT (invoice_no, customer_id, invoice_date, country, is_cancellation, is_guest)
                              VALUES (src.inv, src.cid, src.dt, src.ctry, src.is_c, src.is_g)
    """, ord_data)

    # D. ORDER_ITEMS
    print("  Loading ORDER_ITEMS (using order_item_seq surrogate keys)...")
    batch_size = 5000
    for i in range(0, len(order_items_list), batch_size):
        chunk = order_items_list[i:i + batch_size]
        cursor.executemany("""
            INSERT INTO ORDER_ITEMS (item_id, invoice_no, stock_code, quantity, unit_price)
            VALUES (order_item_seq.NEXTVAL, :1, :2, :3, :4)
        """, chunk)
        conn.commit()

    # E. TRANSACTION_ADJUSTMENTS
    if adjustments_list:
        print("  Loading TRANSACTION_ADJUSTMENTS...")
        cursor.executemany("""
            INSERT INTO TRANSACTION_ADJUSTMENTS (adjustment_id, invoice_no, stock_code, quantity, unit_price, adjustment_type, reason)
            VALUES (adj_seq.NEXTVAL, :1, :2, :3, :4, :5, :6)
        """, adjustments_list)

    # F. ETL_AUDIT
    if audit_list:
        print("  Recording ETL_AUDIT diagnostics...")
        cursor.executemany("""
            INSERT INTO ETL_AUDIT (audit_id, source_row_id, issue_type, issue_description, raw_value)
            VALUES (audit_seq.NEXTVAL, :1, :2, :3, :4)
        """, audit_list)

    conn.commit()
    cursor.close()
    conn.close()

    print("\n" + "=" * 70)
    print("[ETL COMPLETE] Dataset ingested into Oracle 23ai successfully!")
    print("=" * 70)

if __name__ == "__main__":
    target_path = sys.argv[1] if len(sys.argv) > 1 else "data/raw/online_retail_II.csv"
    run_etl(target_path)

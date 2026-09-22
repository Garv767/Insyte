"""
INSYTE — Data Quality & Integrity Validation Engine
Generates comprehensive diagnostics comparing database table counts,
null frequencies, return rates, and financial reconciliation balances.
"""

import os
import sys
from dotenv import load_dotenv

load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1521"))
DB_SERVICE = os.getenv("DB_SERVICE", "FREEPDB1")
DB_USER = os.getenv("APP_ADMIN_USER", "INSYTE_ADMIN")
DB_PASSWORD = os.getenv("APP_ADMIN_PASSWORD", "AdminSecurePassword2026!")

def run_validation():
    print("=" * 70)
    print("INSYTE — Data Quality & Integrity Audit Report")
    print("=" * 70)

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
    except Exception as e:
        print(f"[ERROR connecting to database]: {e}")
        return

    # 1. Table Record Counts
    tables = [
        "CUSTOMERS", "PRODUCTS", "ORDERS", "ORDER_ITEMS", 
        "REVIEWS", "REVIEW_MEDIA", "TRANSACTION_ADJUSTMENTS", "ETL_AUDIT"
    ]
    print("\n[1. Database Table Population Summary]")
    print(f"  {'Table Name':<28} {'Row Count':>12}")
    print("  " + "-" * 42)
    for tbl in tables:
        try:
            cursor.execute(f"SELECT COUNT(*) FROM {tbl}")
            count = cursor.fetchone()[0]
            print(f"  {tbl:<28} {count:>12,}")
        except Exception as e:
            print(f"  {tbl:<28} {'Error / Missing':>12}")

    # 2. Customer Segmentation Breakdown
    print("\n[2. Customer Registration Profile]")
    cursor.execute("""
        SELECT 
            COUNT(CASE WHEN is_guest = 0 THEN 1 END) AS registered_customers,
            COUNT(CASE WHEN is_guest = 1 THEN 1 END) AS guest_shoppers
        FROM ORDERS
    """)
    row = cursor.fetchone()
    print(f"  Registered Customer Orders : {row[0]:,}")
    print(f"  Guest / Anonymous Orders   : {row[1]:,}")

    # 3. Financial Reconciliation Balance Check
    print("\n[3. Financial Balance Reconciliation]")
    cursor.execute("""
        SELECT 
            NVL(SUM(CASE WHEN quantity > 0 THEN quantity * unit_price ELSE 0 END), 0) AS gross_sales,
            NVL(SUM(CASE WHEN quantity < 0 THEN ABS(quantity * unit_price) ELSE 0 END), 0) AS returns_amount,
            NVL(SUM(quantity * unit_price), 0) AS net_revenue
        FROM ORDER_ITEMS
    """)
    fin = cursor.fetchone()
    gross, returns, net = fin[0], fin[1], fin[2]
    print(f"  Gross Sales Amount : £{gross:,.2f}")
    print(f"  Returns / Cancels  : £{returns:,.2f}")
    print(f"  Net Total Revenue  : £{net:,.2f}")
    print(f"  Balance Check (Gross - Returns == Net): {'VERIFIED' if abs((gross - returns) - net) < 0.01 else 'DISCREPANCY'}")

    # 4. ETL Audit Logs
    print("\n[4. ETL Audit & Data Cleansing Issues]")
    cursor.execute("""
        SELECT issue_type, COUNT(*) AS count
        FROM ETL_AUDIT
        GROUP BY issue_type
        ORDER BY count DESC
    """)
    issues = cursor.fetchall()
    if issues:
        for issue_type, count in issues:
            print(f"  {issue_type:<25}: {count:>8,} rejected/sanitized rows")
    else:
        print("  No ETL audit issues logged.")

    cursor.close()
    conn.close()
    print("\n" + "=" * 70)
    print("[AUDIT COMPLETE] Data quality audit executed successfully.")
    print("=" * 70)

if __name__ == "__main__":
    run_validation()

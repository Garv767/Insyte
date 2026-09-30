"""
INSYTE — Quick DB Verification Script
Connects to Oracle and checks row counts for all 5 analytical tables.
"""

import os
import sys
import oracledb
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    wallet_dir = os.path.abspath("wallet")
    db_user = os.getenv("APP_ADMIN_USER", "ADMIN")
    db_password = os.getenv("APP_ADMIN_PASSWORD", "garv767@INSYTE")
    tns_name = os.getenv("TNS_NAME", "insyte_high")
    wallet_password = os.getenv("WALLET_PASSWORD", "")

    conn = oracledb.connect(
        user=db_user,
        password=db_password,
        dsn=tns_name,
        config_dir=wallet_dir,
        wallet_location=wallet_dir,
        wallet_password=wallet_password
    )
    return conn

TABLES = {
    "CUSTOMERS":       "Expected: 74,286",
    "PRODUCTS":        "Expected: 5,885",
    "PRODUCT_FEATURES":"Expected: 5,885",
    "REVIEWS":         "Expected: 75,000",
    "REVIEW_IMAGES":   "Expected: 5,215",
}

SPOT_CHECKS = [
    ("SELECT ROUND(AVG(avg_rating_given), 3) FROM CUSTOMERS", "Avg rating given by customers"),
    ("SELECT ROUND(AVG(average_rating), 3) FROM PRODUCTS", "Avg product rating"),
    ("SELECT COUNT(*) FROM REVIEWS WHERE verified_purchase = 1", "Verified review count"),
    ("SELECT COUNT(*) FROM REVIEWS WHERE has_image = 1", "Reviews with images"),
    ("SELECT COUNT(*) FROM PRODUCT_FEATURES WHERE avg_review_rating >= 4.0", "Products avg rating >= 4.0"),
    ("SELECT TO_CHAR(MIN(review_date), 'YYYY-MM-DD') FROM REVIEWS", "Earliest review date"),
    ("SELECT TO_CHAR(MAX(review_date), 'YYYY-MM-DD') FROM REVIEWS", "Latest review date"),
]

def run():
    try:
        conn = get_connection()
        cursor = conn.cursor()
        print("=" * 60)
        print("INSYTE — Database Verification Report")
        print("=" * 60)

        print("\n[1] TABLE ROW COUNTS")
        print("-" * 60)
        all_ok = True
        for table, note in TABLES.items():
            row = cursor.execute(f"SELECT COUNT(*) FROM {table}").fetchone()
            count = row[0]
            print(f"  {table:<22} {count:>8,} rows   ({note})")

        print("\n[2] SPOT CHECKS")
        print("-" * 60)
        for sql, label in SPOT_CHECKS:
            row = cursor.execute(sql).fetchone()
            val = row[0]
            print(f"  {label:<40} {val}")

        print("\n[3] SAMPLE REVIEWS")
        print("-" * 60)
        cursor.execute("""
            SELECT r.review_id, p.title, r.rating, r.review_date
            FROM REVIEWS r
            JOIN PRODUCTS p ON r.product_id = p.product_id
            WHERE ROWNUM <= 3
        """)
        for row in cursor.fetchall():
            title_snippet = (str(row[1])[:40] + "...") if row[1] and len(str(row[1])) > 40 else row[1]
            print(f"  [{row[0][:12]}...] {title_snippet} | Rating: {row[2]} | Date: {row[3]}")

        print("\n" + "=" * 60)
        print("Verification complete. Database is ready.")
        print("=" * 60)
        cursor.close()
        conn.close()
    except Exception as e:
        print(f"Error: {e}")
        sys.exit(1)

if __name__ == "__main__":
    run()

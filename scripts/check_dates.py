import os, oracledb
from dotenv import load_dotenv
load_dotenv()

conn = oracledb.connect(
    user=os.getenv('APP_ADMIN_USER','ADMIN'),
    password=os.getenv('APP_ADMIN_PASSWORD','garv767@INSYTE'),
    dsn='insyte_high',
    config_dir=os.path.abspath('wallet'),
    wallet_location=os.path.abspath('wallet'),
    wallet_password=os.getenv('WALLET_PASSWORD','')
)
cur = conn.cursor()

print("=== REVIEWS: Raw date column ===")
cur.execute("SELECT TO_CHAR(review_date, 'YYYY-MM-DD'), review_date FROM REVIEWS WHERE ROWNUM <= 5")
for row in cur.fetchall():
    print(row)

print("\n=== CUSTOMERS: first/last review dates ===")
cur.execute("SELECT TO_CHAR(first_review_date, 'YYYY-MM-DD'), TO_CHAR(last_review_date, 'YYYY-MM-DD') FROM CUSTOMERS WHERE ROWNUM <= 5")
for row in cur.fetchall():
    print(row)

conn.close()

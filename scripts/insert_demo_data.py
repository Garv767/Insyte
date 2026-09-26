import os
import random
from datetime import datetime, timedelta
import oracledb
from dotenv import load_dotenv

load_dotenv()

def insert_demo_data():
    print("Connecting to Oracle Autonomous Database...")
    conn = oracledb.connect(
        user=os.getenv('DB_USER'),
        password=os.getenv('DB_PASSWORD'),
        dsn=os.getenv('TNS_NAME'),
        wallet_location=os.path.abspath(os.getenv('WALLET_DIR', 'wallet')),
        config_dir=os.path.abspath(os.getenv('WALLET_DIR', 'wallet')),
        wallet_password=os.getenv('WALLET_PASSWORD')
    )
    cursor = conn.cursor()

    try:
        print("Clearing existing data...")
        cursor.execute("DELETE FROM order_items")
        cursor.execute("DELETE FROM orders")
        cursor.execute("DELETE FROM products")
        cursor.execute("DELETE FROM customers")
        conn.commit()

        print("Inserting Customers...")
        customers = []
        countries = ['United Kingdom', 'Germany', 'France', 'EIRE', 'Netherlands']
        for i in range(1, 101):
            cust_id = 10000 + i
            country = random.choice(countries)
            reg_date = datetime.now() - timedelta(days=random.randint(10, 365))
            customers.append((cust_id, country, reg_date, reg_date))
        cursor.executemany("INSERT INTO customers (customer_id, country, registration_date, created_at) VALUES (:1, :2, :3, :4)", customers)

        print("Inserting Products...")
        products = []
        categories = ['Home Decor', 'Kitchen', 'Apparel', 'Electronics']
        for i in range(1, 21):
            stock_code = f"SKU{i:03d}"
            desc = f"Premium E-Commerce Product {i}"
            price = round(random.uniform(5.0, 150.0), 2)
            meta = f'{{"category": "{random.choice(categories)}"}}'
            products.append((stock_code, desc, desc, price, meta))
        cursor.executemany("INSERT INTO products (stock_code, original_description, normalized_description, unit_price, metadata) VALUES (:1, :2, :3, :4, :5)", products)

        print("Inserting Orders and Items...")
        item_id = 1
        for i in range(1, 201):
            inv_no = f"INV2024{i:04d}"
            cust_id = random.choice(customers)[0]
            country = random.choice(countries)
            inv_date = datetime.now() - timedelta(days=random.randint(1, 300))
            cursor.execute("INSERT INTO orders (invoice_no, invoice_date, customer_id, country, order_status) VALUES (:1, :2, :3, :4, 'COMPLETED')", (inv_no, inv_date, cust_id, country))
            
            # 1 to 5 items per order
            for j in range(random.randint(1, 5)):
                prod = random.choice(products)
                qty = random.randint(1, 10)
                cursor.execute("INSERT INTO order_items (item_id, invoice_no, stock_code, quantity, unit_price) VALUES (:1, :2, :3, :4, :5)", (item_id, inv_no, prod[0], qty, prod[3]))
                item_id += 1

        conn.commit()
        
        print("Refreshing Materialized Views...")
        try:
            cursor.execute("BEGIN DBMS_MVIEW.REFRESH('MV_MONTHLY_REVENUE_TRENDS'); END;")
            cursor.execute("BEGIN DBMS_MVIEW.REFRESH('MV_CUSTOMER_RFM_SUMMARY'); END;")
        except Exception as e:
            print("MView refresh failed (may not exist yet).", e)

        print("Demo data inserted successfully!")

    except Exception as e:
        print("Error:", e)
        conn.rollback()
    finally:
        cursor.close()
        conn.close()

if __name__ == '__main__':
    insert_demo_data()

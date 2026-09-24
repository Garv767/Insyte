"""
INSYTE — Automated Database Initialization Engine
Executes SQL scripts 01 through 15 in sequential order against Oracle Database 23ai Free.
Uses python-oracledb Thin Driver with credentials from .env.
"""

import os
import sys
from pathlib import Path
from dotenv import load_dotenv

load_dotenv()

DB_CONNECT_STRING = os.getenv("DB_CONNECT_STRING", "")
DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1521"))
DB_SERVICE = os.getenv("DB_SERVICE", "FREEPDB1")
DB_USER = os.getenv("DB_USER", "ADMIN")
DB_PASSWORD = os.getenv("DB_PASSWORD", "garv767@INSYTE")
DB_SYS_USER = os.getenv("DB_SYS_USER", "SYS")
APP_ADMIN_USER = os.getenv("APP_ADMIN_USER", "ADMIN")
APP_ADMIN_PASSWORD = os.getenv("APP_ADMIN_PASSWORD", DB_PASSWORD)

try:
    import oracledb
except ImportError:
    print("[ERROR] 'oracledb' is not installed. Please run: pip install -r requirements.txt")
    sys.exit(1)

SQL_DIR = Path(__file__).resolve().parent.parent / "database"

SQL_SCRIPTS = [
    ("01_users_roles.sql", True),   # Needs ADMIN or SYS
    ("02_schema.sql", False),
    ("03_sequences.sql", False),
    ("04_constraints.sql", False),
    ("05_indexes.sql", False),
    ("06_etl.sql", False),
    ("07_views.sql", False),
    ("08_materialized_views.sql", False),
    ("09_json.sql", False),
    ("10_vector.sql", False),
    ("11_analytics.sql", False),
    ("12_review_analytics.sql", False),
    ("13_cohort.sql", False),
    ("14_sql_demonstrations.sql", False),
    ("15_data_dictionary.sql", False)
]

def execute_sql_file(connection, filepath):
    cursor = connection.cursor()
    with open(filepath, "r", encoding="utf-8") as f:
        content = f.read()

    # Split statements by semicolon or slash
    raw_statements = content.split(";")
    for stmt in raw_statements:
        clean_stmt = stmt.strip()
        # Skip SQL*Plus PROMPT and empty lines or container switches not allowed in serverless
        if not clean_stmt or clean_stmt.upper().startswith("PROMPT") or clean_stmt.startswith("--"):
            continue
        if "ALTER SESSION SET CONTAINER" in clean_stmt.upper():
            continue
        try:
            cursor.execute(clean_stmt)
        except oracledb.Error as err:
            err_obj, = err.args
            # Ignore harmless object already exists or drop errors
            if err_obj.code in (942, 1920, 1921, 2289, 12003):
                continue
            print(f"  [Notice in {filepath.name}] Code {err_obj.code}: {err_obj.message[:80]}")
    connection.commit()
    cursor.close()

def main():
    print("=" * 70)
    print("INSYTE — Database Initialization Engine")
    print("=" * 70)
    if DB_CONNECT_STRING:
        print("Target: Oracle Autonomous AI Database (OCI Serverless)")
    else:
        print(f"Target Service: {DB_HOST}:{DB_PORT}/{DB_SERVICE}")

    WALLET_DIR_ENV = os.getenv("WALLET_DIR", "")
    WALLET_DIR = os.path.abspath(WALLET_DIR_ENV) if WALLET_DIR_ENV else ""
    TNS_NAME = os.getenv("TNS_NAME", "insyte_high")
    WALLET_PASSWORD = os.getenv("WALLET_PASSWORD", "")

    # Connect to Autonomous Database or Local Oracle
    print(f"\nConnecting as {DB_USER} to deploy schema objects...")
    try:
        if WALLET_DIR and os.path.exists(WALLET_DIR):
            conn = oracledb.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                dsn=TNS_NAME,
                config_dir=WALLET_DIR,
                wallet_location=WALLET_DIR,
                wallet_password=WALLET_PASSWORD
            )
        elif DB_CONNECT_STRING:
            conn = oracledb.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                dsn=DB_CONNECT_STRING
            )
        else:
            conn = oracledb.connect(
                user=DB_USER,
                password=DB_PASSWORD,
                host=DB_HOST,
                port=DB_PORT,
                service_name=DB_SERVICE
            )
        print(f"  Connected successfully as {DB_USER}.")

        # Execute scripts sequentially
        for script_name, is_sys in SQL_SCRIPTS:
            script_path = SQL_DIR / script_name
            if script_path.exists():
                print(f"  Executing {script_name}...")
                execute_sql_file(conn, script_path)

        conn.close()
        print("\n" + "=" * 70)
        print("[SUCCESS] All Oracle database scripts deployed successfully!")
        print("=" * 70)
    except Exception as e:
        print(f"[ERROR]: {e}")

if __name__ == "__main__":
    main()

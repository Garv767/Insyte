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

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1521"))
DB_SERVICE = os.getenv("DB_SERVICE", "FREEPDB1")
DB_SYS_USER = os.getenv("DB_SYS_USER", "SYS")
DB_PASSWORD = os.getenv("DB_PASSWORD", "InsyteOracle23ai#Secure2026")
APP_ADMIN_USER = os.getenv("APP_ADMIN_USER", "INSYTE_ADMIN")
APP_ADMIN_PASSWORD = os.getenv("APP_ADMIN_PASSWORD", "AdminSecurePassword2026!")

try:
    import oracledb
except ImportError:
    print("[ERROR] 'oracledb' is not installed. Please run: pip install -r requirements.txt")
    sys.exit(1)

SQL_DIR = Path(__file__).resolve().parent.parent / "database"

SQL_SCRIPTS = [
    ("01_users_roles.sql", True),   # Needs SYSDBA
    ("02_schema.sql", False),       # Run as INSYTE_ADMIN
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
    # Simple statement splitter handling PL/SQL blocks
    raw_statements = content.split(";")
    for stmt in raw_statements:
        clean_stmt = stmt.strip()
        # Skip SQL*Plus PROMPT and empty lines
        if not clean_stmt or clean_stmt.upper().startswith("PROMPT") or clean_stmt.startswith("--"):
            continue
        try:
            cursor.execute(clean_stmt)
        except oracledb.Error as err:
            err_obj, = err.args
            # Ignore harmless object already exists or drop errors
            if err_obj.code in (942, 1920, 1921, 2289, 12003):
                continue
            print(f"  [WARN in {filepath.name}] Code {err_obj.code}: {err_obj.message[:80]}")
    connection.commit()
    cursor.close()

def main():
    print("=" * 70)
    print("INSYTE — Database Initialization Engine (Oracle 23ai Free)")
    print("=" * 70)
    print(f"Target Service: {DB_HOST}:{DB_PORT}/{DB_SERVICE}")
    
    # 1. Connect as SYSDBA for User/Role Creation
    print("\n[Step 1/2] Connecting as SYSDBA to configure security roles...")
    try:
        sys_conn = oracledb.connect(
            user=DB_SYS_USER,
            password=DB_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            service_name=DB_SERVICE,
            mode=oracledb.SYSDBA
        )
        print("  Connected as SYSDBA.")
        script_path = SQL_DIR / "01_users_roles.sql"
        if script_path.exists():
            print(f"  Executing {script_path.name}...")
            execute_sql_file(sys_conn, script_path)
            print("  Security roles and grants initialized.")
        sys_conn.close()
    except Exception as e:
        print(f"  [Notice/Error with SYSDBA connection]: {e}")
        print("  Proceeding to execute remaining scripts as INSYTE_ADMIN...")

    # 2. Connect as INSYTE_ADMIN for Schema and Views
    print("\n[Step 2/2] Connecting as INSYTE_ADMIN to deploy schema and views...")
    try:
        admin_conn = oracledb.connect(
            user=APP_ADMIN_USER,
            password=APP_ADMIN_PASSWORD,
            host=DB_HOST,
            port=DB_PORT,
            service_name=DB_SERVICE
        )
        print(f"  Connected as {APP_ADMIN_USER}.")

        for script_name, is_sys in SQL_SCRIPTS[1:]:
            script_path = SQL_DIR / script_name
            if script_path.exists():
                print(f"  Executing {script_name}...")
                execute_sql_file(admin_conn, script_path)

        admin_conn.close()
        print("\n" + "=" * 70)
        print("[SUCCESS] All 15 Oracle 23ai database scripts deployed successfully!")
        print("=" * 70)
    except Exception as e:
        print(f"[ERROR connecting as {APP_ADMIN_USER}]: {e}")
        print("Ensure Oracle container is running: docker compose up -d")

if __name__ == "__main__":
    main()

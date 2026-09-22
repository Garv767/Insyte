"""
INSYTE — Database Connection Verification Script
Tests connectivity to Oracle Database 23ai Free via python-oracledb Thin Driver.
Decoupled parameters are read directly from .env.
"""

import os
import sys
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

DB_HOST = os.getenv("DB_HOST", "localhost")
DB_PORT = int(os.getenv("DB_PORT", "1521"))
DB_SERVICE = os.getenv("DB_SERVICE", "FREEPDB1")
DB_USER = os.getenv("APP_ADMIN_USER", os.getenv("DB_SYS_USER", "INSYTE_ADMIN"))
DB_PASSWORD = os.getenv("APP_ADMIN_PASSWORD", os.getenv("DB_PASSWORD", ""))

print("=" * 60)
print("INSYTE — Oracle Database 23ai Connectivity Test")
print("=" * 60)
print(f"Target Host    : {DB_HOST}")
print(f"Target Port    : {DB_PORT}")
print(f"Service Name   : {DB_SERVICE}")
print(f"Database User  : {DB_USER}")
print("-" * 60)

try:
    import oracledb
except ImportError:
    print("[ERROR] 'oracledb' library is not installed.")
    print("Please install requirements using: pip install -r requirements.txt")
    sys.exit(1)

try:
    # Use python-oracledb in default Thin mode
    connection = oracledb.connect(
        user=DB_USER,
        password=DB_PASSWORD,
        host=DB_HOST,
        port=DB_PORT,
        service_name=DB_SERVICE
    )
    
    cursor = connection.cursor()
    
    # Query database version
    cursor.execute("SELECT banner FROM v$version")
    banner = cursor.fetchone()
    
    # Query container/PDB context
    cursor.execute("SELECT SYS_CONTEXT('USERENV', 'CON_NAME'), SYS_CONTEXT('USERENV', 'CURRENT_USER') FROM DUAL")
    con_info = cursor.fetchone()
    
    print("[SUCCESS] Connected successfully to Oracle Database!")
    print(f"Oracle Banner  : {banner[0] if banner else 'Unknown'}")
    print(f"Container / PDB: {con_info[0] if con_info else 'Unknown'}")
    print(f"Session User   : {con_info[1] if con_info else 'Unknown'}")
    print("-" * 60)
    print("Thin driver connection pool is ready for application deployment.")
    
    cursor.close()
    connection.close()
    sys.exit(0)

except oracledb.Error as e:
    error_obj, = e.args
    print(f"[FAILED] Oracle Database Error: {error_obj.message}")
    print(f"Error Code     : {error_obj.code}")
    print("\nTroubleshooting tips:")
    print(" 1. Ensure Docker container is running: docker compose ps")
    print(" 2. Verify port 1521 is exposed and healthy")
    print(" 3. Confirm password in .env matches docker-compose.yml ORACLE_PASSWORD")
    print(" 4. Verify PDB service name FREEPDB1 is open")
    sys.exit(1)
except Exception as ex:
    print(f"[FAILED] Unexpected error: {str(ex)}")
    sys.exit(1)

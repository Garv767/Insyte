import os
import json
import base64
import tempfile
import oracledb

_connection_pool = None

def _decode_wallet_to_tmpdir():
    """Decode WALLET_BASE64 to a temp directory and return the path."""
    wallet_b64 = os.environ.get("WALLET_BASE64")
    if not wallet_b64:
        raise RuntimeError("WALLET_BASE64 environment variable is not set")

    wallet_zip = base64.b64decode(wallet_b64)
    tmp_dir = tempfile.mkdtemp(prefix="insyte_wallet_")

    import zipfile, io
    with zipfile.ZipFile(io.BytesIO(wallet_zip)) as zf:
        zf.extractall(tmp_dir)

    return tmp_dir

def get_connection():
    """
    Returns an oracledb connection.
    On cold start: decodes wallet, creates connection.
    Reuses module-level pool on warm Lambda invocations.
    """
    global _connection_pool

    if _connection_pool is not None:
        try:
            return _connection_pool.acquire()
        except Exception:
            _connection_pool = None  # force re-init on stale pool

    # Try local wallet first, else decode base64
    wallet_dir = os.environ.get("WALLET_DIR", os.path.abspath("wallet"))
    if not os.path.isdir(wallet_dir):
        wallet_dir = _decode_wallet_to_tmpdir()

    db_user = os.environ.get("APP_ADMIN_USER", os.environ.get("DB_USER", "ADMIN"))
    db_password = os.environ.get("APP_ADMIN_PASSWORD", os.environ.get("DB_PASSWORD", ""))
    
    conn = oracledb.connect(
        user=db_user,
        password=db_password,
        dsn=os.environ.get("TNS_NAME", "insyte_high"),
        config_dir=wallet_dir,
        wallet_location=wallet_dir,
        wallet_password=os.environ.get("WALLET_PASSWORD", ""),
    )
    return conn

def execute_query(conn, sql: str, params: dict = None) -> list:
    """Execute a SELECT query and return list of dicts."""
    cursor = conn.cursor()
    cursor.execute(sql, params or {})
    columns = [col[0].lower() for col in cursor.description]
    rows = cursor.fetchall()
    cursor.close()
    return [dict(zip(columns, row)) for row in rows]

def send_json_response(handler, status_code: int, body: dict):
    handler.send_response(status_code)
    handler.send_header('Content-type', 'application/json')
    handler.send_header('Access-Control-Allow-Origin', '*')
    handler.end_headers()
    handler.wfile.write(json.dumps(body, default=str).encode('utf-8'))

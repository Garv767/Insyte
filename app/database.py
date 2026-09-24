"""
INSYTE — Database Connection Pool & Query Orchestrator
Uses python-oracledb Thin Mode with connection pooling.
Includes query orchestration, explain plan generation, and fallback demonstration cache.
"""

import time
import logging
from contextlib import contextmanager
from app.config import Config

logger = logging.getLogger(__name__)

_pool = None
_is_connected = False

def init_pool():
    global _pool, _is_connected
    try:
        import oracledb
        _pool = oracledb.create_pool(
            user=Config.DB_USER,
            password=Config.DB_PASSWORD,
            host=Config.DB_HOST,
            port=Config.DB_PORT,
            service_name=Config.DB_SERVICE,
            min=Config.DB_POOL_MIN,
            max=Config.DB_POOL_MAX,
            increment=Config.DB_POOL_INCREMENT
        )
        _is_connected = True
        logger.info(f"Oracle 23ai Connection Pool initialized for {Config.DB_USER}@{Config.DB_HOST}:{Config.DB_PORT}/{Config.DB_SERVICE}")
        return True
    except Exception as e:
        _is_connected = False
        logger.warning(f"Could not initialize Oracle connection pool: {e}. Running in standby/cache mode.")
        return False

def close_pool():
    global _pool, _is_connected
    if _pool:
        try:
            _pool.close()
            logger.info("Oracle Connection Pool closed gracefully.")
        except Exception as e:
            logger.error(f"Error closing pool: {e}")
        finally:
            _pool = None
            _is_connected = False

def is_database_connected():
    return _is_connected

@contextmanager
def get_connection():
    global _pool
    if not _pool:
        init_pool()
    if not _pool:
        yield None
        return

    conn = None
    try:
        conn = _pool.acquire()
        yield conn
    finally:
        if conn and _pool:
            try:
                _pool.release(conn)
            except Exception:
                pass

def execute_query(sql, params=None):
    """Executes a SQL query and returns (rows, columns, elapsed_ms)."""
    start_time = time.perf_counter()
    with get_connection() as conn:
        if not conn:
            return [], [], 0.0
        cursor = conn.cursor()
        try:
            cursor.execute(sql, params or {})
            columns = [col[0].lower() for col in cursor.description] if cursor.description else []
            rows = cursor.fetchall()
            elapsed_ms = round((time.perf_counter() - start_time) * 1000, 2)
            return rows, columns, elapsed_ms
        finally:
            cursor.close()

def execute_query_dict(sql, params=None):
    """Executes a SQL query and returns list of dictionaries."""
    rows, columns, elapsed_ms = execute_query(sql, params)
    result = []
    for row in rows:
        row_dict = {}
        for col_name, val in zip(columns, row):
            # Convert Lob / Vector / Datetime to serializable format
            if hasattr(val, "read"):
                val = val.read()
            elif hasattr(val, "isoformat"):
                val = val.isoformat()
            row_dict[col_name] = val
        result.append(row_dict)
    return result, elapsed_ms

def get_explain_plan(sql_text):
    """Generates and retrieves Oracle EXPLAIN PLAN for a given SQL statement."""
    with get_connection() as conn:
        if not conn:
            return [{"operation": "ORACLE_OFFLINE", "object": "N/A", "cost": 0, "rows": 0, "plan_table": "Oracle Database container currently offline"}]
        cursor = conn.cursor()
        try:
            cursor.execute(f"EXPLAIN PLAN FOR {sql_text}")
            cursor.execute("SELECT plan_table_output FROM TABLE(DBMS_XPLAN.DISPLAY())")
            lines = [row[0] for row in cursor.fetchall()]
            return lines
        except Exception as e:
            return [f"Explain plan error: {str(e)}"]
        finally:
            cursor.close()

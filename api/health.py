from http.server import BaseHTTPRequestHandler
import urllib.parse
from ._db import get_connection, execute_query, send_json_response

_HEALTH_CASE = """
    CASE
        WHEN pf.avg_review_rating >= 4.0
             AND (pf.rating_1_pct + pf.rating_2_pct) < 0.10 THEN 'HEALTHY'
        WHEN pf.avg_review_rating < 3.0
             OR  (pf.rating_1_pct + pf.rating_2_pct) > 0.25  THEN 'AT_RISK'
        ELSE 'WATCH'
    END
"""

class handler(BaseHTTPRequestHandler):
    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()

    def do_GET(self):
        parsed_path = urllib.parse.urlparse(self.path)
        path = parsed_path.path.rstrip("/")
        params = dict(urllib.parse.parse_qsl(parsed_path.query))

        try:
            conn = get_connection()

            if path.endswith("/summary"):
                data = self._get_product_health_summary(conn)
            elif path.endswith("/matrix"):
                status_filter = params.get("status")
                search = params.get("search")
                data = self._get_product_health_matrix(conn, status_filter, search)
            else:
                send_json_response(self, 404, {"error": f"Unknown path: {path}"})
                return

            send_json_response(self, 200, data)

        except Exception as e:
            send_json_response(self, 500, {"error": str(e)})

    # ─── Query Functions ────────────────────────────────────────────────────

    def _get_product_health_summary(self, conn) -> dict:
        sql = f"""
            SELECT
                COUNT(*) AS total_monitored,
                COUNT(CASE WHEN {_HEALTH_CASE} = 'HEALTHY' THEN 1 END) AS healthy_count,
                COUNT(CASE WHEN {_HEALTH_CASE} = 'WATCH' THEN 1 END) AS watch_count,
                COUNT(CASE WHEN {_HEALTH_CASE} = 'AT_RISK' THEN 1 END) AS at_risk_count
            FROM PRODUCTS p
            JOIN PRODUCT_FEATURES pf ON p.product_id = pf.product_id
        """
        rows = execute_query(conn, sql)
        if rows:
            r = rows[0]
            tot = r["total_monitored"]
            r["healthy_pct"] = round(r["healthy_count"] * 100.0 / tot, 1) if tot else 0
            r["watch_pct"] = round(r["watch_count"] * 100.0 / tot, 1) if tot else 0
            r["at_risk_pct"] = round(r["at_risk_count"] * 100.0 / tot, 1) if tot else 0
            return r
        return {}

    def _get_product_health_matrix(self, conn, status_filter=None, search=None) -> list:
        where_clauses = []
        params = {}

        if status_filter and status_filter != "ALL":
            where_clauses.append(f"{_HEALTH_CASE} = :status")
            params["status"] = status_filter
        if search:
            where_clauses.append("(UPPER(p.title) LIKE :s OR UPPER(p.product_id) LIKE :s)")
            params["s"] = f"%{search.upper()}%"

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""

        sql = f"""
            SELECT 
                p.product_id AS stock_code,
                p.title AS description,
                p.price AS unit_price,
                pf.review_count AS revenue,
                pf.review_count AS units_sold,
                ROUND((pf.rating_1_pct + pf.rating_2_pct) * 100, 1) AS negative_pct,
                pf.avg_review_rating AS avg_rating,
                pf.review_count,
                ROUND(pf.image_review_rate, 1) AS media_attachment_rate,
                {_HEALTH_CASE} AS health_status
            FROM PRODUCTS p
            JOIN PRODUCT_FEATURES pf ON p.product_id = pf.product_id
            {where_sql}
            ORDER BY pf.review_count DESC
            FETCH FIRST 50 ROWS ONLY
        """
        return execute_query(conn, sql, params)

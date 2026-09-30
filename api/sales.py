from http.server import BaseHTTPRequestHandler
import urllib.parse
from ._db import get_connection, execute_query, send_json_response

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
            if path.endswith("/overview"):
                data = self._get_sales_overview()
            elif path.endswith("/cohorts"):
                data = self._get_cohort_retention_matrix()
            elif path.endswith("/aov"):
                data = self._get_aov_trend()
            elif path.endswith("/trends"):
                data = self._get_sales_trends_mock()
            else:
                send_json_response(self, 404, {"error": f"Unknown path: {path}"})
                return

            send_json_response(self, 200, data)

        except Exception as e:
            send_json_response(self, 500, {"error": str(e)})

    # ─── DB Functions ────────────────────────────────────────────────────

    def _get_sales_overview(self) -> dict:
        conn = get_connection()
        sql = """
            SELECT 
                SUM(gross_sales) AS annual_gross_sales,
                SUM(return_amount) AS annual_returns,
                SUM(net_revenue) AS annual_net_revenue,
                SUM(total_orders) AS total_invoices,
                ROUND(SUM(units_sold) / NULLIF(SUM(total_orders), 0), 1) AS avg_basket_size,
                ROUND(SUM(net_revenue) / NULLIF(SUM(total_orders), 0), 2) AS overall_aov
            FROM V_MONTHLY_REVENUE
        """
        rows = execute_query(conn, sql)
        if rows:
            return rows[0]
        return {}

    def _get_cohort_retention_matrix(self) -> list:
        conn = get_connection()
        sql = "SELECT * FROM V_COHORT_RETENTION_MATRIX ORDER BY COHORT_MONTH"
        return execute_query(conn, sql)

    def _get_aov_trend(self) -> list:
        conn = get_connection()
        sql = """
            SELECT 
                MONTH_KEY AS "period", 
                AOV AS "aov", 
                TOTAL_ORDERS AS "orders"
            FROM V_MONTHLY_REVENUE
            ORDER BY MONTH_KEY
        """
        return execute_query(conn, sql)

    def _get_sales_trends_mock(self) -> list:
        conn = get_connection()
        sql = """
            SELECT 
                MONTH_KEY AS "period_label",
                NET_REVENUE AS "net_revenue",
                RETURN_AMOUNT AS "returns"
            FROM V_MONTHLY_REVENUE
            ORDER BY MONTH_KEY
        """
        return execute_query(conn, sql)

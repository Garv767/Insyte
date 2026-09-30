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
            else:
                send_json_response(self, 404, {"error": f"Unknown path: {path}"})
                return

            send_json_response(self, 200, data)

        except Exception as e:
            send_json_response(self, 500, {"error": str(e)})

    # ─── Mock Functions ────────────────────────────────────────────────────

    def _get_sales_overview(self) -> dict:
        return {
            "annual_gross_sales": 10542380.50,
            "annual_returns": 812450.20,
            "annual_net_revenue": 9729930.30,
            "total_invoices": 44820,
            "avg_basket_size": 21.9,
            "overall_aov": 217.09
        }

    def _get_cohort_retention_matrix(self) -> list:
        return [
            {"cohort_month": "2024-01", "cohort_size": 980, "m0_active": 980, "m1_retention_pct": 38.2, "m2_retention_pct": 34.5, "m3_retention_pct": 36.1, "m4_retention_pct": 32.8, "m5_retention_pct": 35.4, "m6_retention_pct": 39.2},
            {"cohort_month": "2024-02", "cohort_size": 650, "m0_active": 650, "m1_retention_pct": 32.4, "m2_retention_pct": 28.9, "m3_retention_pct": 30.5, "m4_retention_pct": 29.1, "m5_retention_pct": 31.8, "m6_retention_pct": 33.6},
            {"cohort_month": "2024-03", "cohort_size": 710, "m0_active": 710, "m1_retention_pct": 34.1, "m2_retention_pct": 31.2, "m3_retention_pct": 32.6, "m4_retention_pct": 30.8, "m5_retention_pct": 33.1, "m6_retention_pct": None},
            {"cohort_month": "2024-04", "cohort_size": 580, "m0_active": 580, "m1_retention_pct": 31.5, "m2_retention_pct": 29.8, "m3_retention_pct": 28.4, "m4_retention_pct": 32.2, "m5_retention_pct": None, "m6_retention_pct": None},
            {"cohort_month": "2024-05", "cohort_size": 620, "m0_active": 620, "m1_retention_pct": 35.8, "m2_retention_pct": 33.2, "m3_retention_pct": 34.6, "m4_retention_pct": None, "m5_retention_pct": None, "m6_retention_pct": None},
            {"cohort_month": "2024-06", "cohort_size": 540, "m0_active": 540, "m1_retention_pct": 33.9, "m2_retention_pct": 30.1, "m3_retention_pct": None, "m4_retention_pct": None, "m5_retention_pct": None, "m6_retention_pct": None},
            {"cohort_month": "2024-07", "cohort_size": 490, "m0_active": 490, "m1_retention_pct": 36.4, "m2_retention_pct": None, "m3_retention_pct": None, "m4_retention_pct": None, "m5_retention_pct": None, "m6_retention_pct": None}
        ]

    def _get_aov_trend(self) -> list:
        return [
            {"period": "2024-01", "aov": 204.60, "orders": 3120},
            {"period": "2024-02", "aov": 203.94, "orders": 3280},
            {"period": "2024-03", "aov": 200.92, "orders": 3890},
            {"period": "2024-04", "aov": 204.01, "orders": 3610},
            {"period": "2024-05", "aov": 198.81, "orders": 4120},
            {"period": "2024-06", "aov": 199.38, "orders": 4250},
            {"period": "2024-07", "aov": 203.00, "orders": 4030},
            {"period": "2024-08", "aov": 201.16, "orders": 4310},
            {"period": "2024-09", "aov": 200.43, "orders": 4820},
            {"period": "2024-10", "aov": 204.93, "orders": 5290},
            {"period": "2024-11", "aov": 202.86, "orders": 6450},
            {"period": "2024-12", "aov": 200.74, "orders": 5890}
        ]

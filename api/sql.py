from http.server import BaseHTTPRequestHandler
import urllib.parse
from ._db import send_json_response

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

        try:
            if path.endswith("/catalog"):
                data = self._get_sql_catalog()
            elif "/query/" in path:
                q_id = path.split("/query/")[-1]
                data = self._get_query_details(q_id)
            elif "/dictionary/" in path:
                category = path.split("/dictionary/")[-1]
                data = self._get_dictionary(category)
            else:
                send_json_response(self, 404, {"error": f"Unknown path: {path}"})
                return

            send_json_response(self, 200, data)

        except Exception as e:
            send_json_response(self, 500, {"error": str(e)})

    # ─── Mock Functions ────────────────────────────────────────────────────

    def _get_sql_catalog(self) -> list:
        return [
            {"id": "q1", "title": "Customer RFM Segmentation", "category": "Customer Analytics"},
            {"id": "q2", "title": "Product Health Matrix", "category": "Product Analytics"},
            {"id": "q3", "title": "Review Media Impact", "category": "Reviews"},
            {"id": "q4", "title": "Cohort Retention Matrix", "category": "Sales Trends"}
        ]

    def _get_query_details(self, q_id: str) -> dict:
        queries = {
            "q1": {
                "title": "Customer RFM Segmentation",
                "category": "Customer Analytics",
                "execution_time_ms": 14.8,
                "description": "Calculates Recency, Frequency, and Monetary scores using NTILE(5) window functions over the entire customer base.",
                "academic_features": ["NTILE", "Window Functions", "Common Table Expressions"],
                "sql": "WITH rfm_base AS (\\n  SELECT customer_id,\\n         MAX(review_date) AS max_date,\\n         COUNT(review_id) AS freq\\n  FROM reviews GROUP BY customer_id\\n)\\nSELECT * FROM rfm_base;",
                "explain_plan": ["Id  | Operation        | Name    | Rows  | Cost (%CPU)", "0   | SELECT STATEMENT |         | 74286 | 125 (2)"]
            },
            "q2": {
                "title": "Product Health Matrix",
                "category": "Product Analytics",
                "execution_time_ms": 8.5,
                "description": "Classifies products into HEALTHY, WATCH, or AT_RISK based on their review ratings and negative feedback percentage using CASE expressions.",
                "academic_features": ["CASE Statement", "JOINs", "Aggregation"],
                "sql": "SELECT p.product_id,\\n  CASE WHEN pf.avg_review_rating >= 4.0 THEN 'HEALTHY' ELSE 'AT_RISK' END AS status\\nFROM products p JOIN product_features pf ON p.product_id = pf.product_id;",
                "explain_plan": ["Id  | Operation        | Name    | Rows  | Cost (%CPU)", "0   | SELECT STATEMENT |         | 5885  | 45 (1)"]
            },
            "q3": {
                "title": "Review Media Impact",
                "category": "Reviews",
                "execution_time_ms": 6.2,
                "description": "Compares satisfaction rates and average ratings between reviews containing media (images/videos) and text-only reviews.",
                "academic_features": ["GROUP BY", "Conditional Aggregation"],
                "sql": "SELECT has_image, AVG(rating) as avg_rating FROM reviews GROUP BY has_image;",
                "explain_plan": ["Id  | Operation        | Name    | Rows  | Cost (%CPU)", "0   | SELECT STATEMENT |         | 2     | 18 (4)"]
            },
            "q4": {
                "title": "Cohort Retention Matrix",
                "category": "Sales Trends",
                "execution_time_ms": 22.1,
                "description": "Calculates customer retention across monthly cohorts using MIN() window functions and MONTHS_BETWEEN date logic.",
                "academic_features": ["Date Math", "Window Functions", "Complex Aggregation"],
                "sql": "SELECT cohort_month, COUNT(DISTINCT customer_id) FROM cohorts GROUP BY cohort_month;",
                "explain_plan": ["Id  | Operation        | Name    | Rows  | Cost (%CPU)", "0   | SELECT STATEMENT |         | 12    | 210 (3)"]
            }
        }
        return queries.get(q_id, {"error": "Query not found"})

    def _get_dictionary(self, category: str) -> list:
        if category == "tables":
            return [
                {"table_name": "PRODUCTS", "rows": 5885},
                {"table_name": "REVIEWS", "rows": 75000},
                {"table_name": "PRODUCT_FEATURES", "rows": 5885}
            ]
        elif category == "indexes":
            return [
                {"index_name": "IDX_REVIEWS_PROD", "table": "REVIEWS", "column": "PRODUCT_ID"},
                {"index_name": "IDX_REVIEWS_RATING", "table": "REVIEWS", "column": "RATING"}
            ]
        elif category == "mviews":
            return [
                {"mview_name": "MV_CUSTOMER_RFM_SUMMARY", "status": "VALID"}
            ]
        return []

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
            conn = get_connection()

            if path.endswith("/kpis"):
                data = self._get_kpis(conn)
            elif path.endswith("/trends"):
                data = self._get_review_trends(conn)
            elif path.endswith("/top-products"):
                limit = int(params.get("limit", 8))
                data = self._get_top_products(conn, limit)
            elif path.endswith("/categories"):
                data = self._get_category_performance(conn)
            elif path.endswith("/insights"):
                data = self._get_factual_insights(conn)
            else:
                send_json_response(self, 404, {"error": f"Unknown path: {path}"})
                return

            send_json_response(self, 200, data)

        except Exception as e:
            send_json_response(self, 500, {"error": str(e)})

    # ─── Query Functions ────────────────────────────────────────────────────

    def _get_kpis(self, conn) -> dict:
        sql = """
            SELECT
                (SELECT COUNT(*) FROM CUSTOMERS) AS total_customers,
                (SELECT COUNT(*) FROM PRODUCTS)  AS total_products,
                (SELECT COUNT(*) FROM REVIEWS)   AS total_reviews,
                (SELECT ROUND(AVG(rating), 2) FROM REVIEWS) AS avg_rating,
                (SELECT ROUND(SUM(verified_purchase) * 100.0 / COUNT(*), 1)
                 FROM REVIEWS) AS verified_rate,
                (SELECT ROUND(SUM(has_image) * 100.0 / COUNT(*), 1)
                 FROM REVIEWS) AS image_review_rate
            FROM dual
        """
        rows = execute_query(conn, sql)
        return rows[0] if rows else {}

    def _get_review_trends(self, conn) -> list:
        sql = """
            SELECT
                TO_CHAR(review_date, 'YYYY-MM') AS period_label,
                COUNT(*)                         AS total_reviews,
                ROUND(AVG(rating), 2)            AS avg_rating,
                SUM(verified_purchase)           AS verified_reviews,
                SUM(has_image)                   AS image_reviews
            FROM REVIEWS
            WHERE review_date IS NOT NULL
            GROUP BY TO_CHAR(review_date, 'YYYY-MM')
            ORDER BY period_label ASC
        """
        return execute_query(conn, sql)

    def _get_top_products(self, conn, limit: int = 8) -> list:
        sql = f"""
            SELECT
                p.product_id,
                p.title         AS description,
                p.price,
                p.average_rating,
                pf.review_count,
                pf.avg_review_rating,
                pf.verified_purchase_rate,
                pf.image_review_rate
            FROM PRODUCTS p
            JOIN PRODUCT_FEATURES pf ON p.product_id = pf.product_id
            ORDER BY pf.review_count DESC
            FETCH FIRST {limit} ROWS ONLY
        """
        return execute_query(conn, sql)

    def _get_category_performance(self, conn) -> list:
        sql = """
            SELECT
                COALESCE(main_category, 'Uncategorized') AS category,
                COUNT(product_id)                         AS product_count,
                ROUND(AVG(average_rating), 2)             AS avg_rating,
                ROUND(AVG(price), 2)                      AS avg_price
            FROM PRODUCTS
            GROUP BY main_category
            ORDER BY product_count DESC
            FETCH FIRST 10 ROWS ONLY
        """
        return execute_query(conn, sql)

    def _get_factual_insights(self, conn) -> list:
        kpis = self._get_kpis(conn)
        return [
            {
                "icon": "check-circle",
                "text": f"{kpis.get('verified_rate', 0)}% of all {kpis.get('total_reviews', 0):,} reviews come from verified purchases."
            },
            {
                "icon": "image",
                "text": f"{kpis.get('image_review_rate', 0)}% of reviews include user-uploaded product photos."
            },
            {
                "icon": "star",
                "text": f"The average rating across {kpis.get('total_products', 0):,} Appliances products is {kpis.get('avg_rating', 0)} stars."
            },
            {
                "icon": "users",
                "text": f"Dataset spans {kpis.get('total_customers', 0):,} unique reviewers across 20 years (2003-2023)."
            },
        ]

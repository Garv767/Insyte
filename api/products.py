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

            if path.endswith("/kpis"):
                data = self._get_product_kpis(conn)
            elif path.endswith("/list"):
                sort_by  = params.get("sort_by", "review_count")
                order    = params.get("order", "desc").upper()
                search   = params.get("search")
                page     = int(params.get("page", 1))
                per_page = int(params.get("per_page", 15))
                data = self._get_product_list(conn, sort_by, order, search, page, per_page)
            elif "/products/" in path:
                product_id = path.split("/products/")[-1]
                data = self._get_product_detail(conn, product_id)
            else:
                send_json_response(self, 404, {"error": f"Unknown path: {path}"})
                return

            send_json_response(self, 200, data)

        except Exception as e:
            send_json_response(self, 500, {"error": str(e)})

    # ─── Query Functions ────────────────────────────────────────────────────

    def _get_product_kpis(self, conn) -> dict:
        sql = f"""
            SELECT
                COUNT(*)                                                       AS total_products,
                ROUND(AVG(p.average_rating), 2)                               AS avg_catalog_rating,
                COUNT(CASE WHEN p.price IS NOT NULL THEN 1 END)               AS priced_products,
                ROUND(AVG(p.price), 2)                                        AS avg_price,
                COUNT(CASE WHEN {_HEALTH_CASE} = 'HEALTHY'  THEN 1 END)      AS healthy_count,
                COUNT(CASE WHEN {_HEALTH_CASE} = 'WATCH'    THEN 1 END)      AS watch_count,
                COUNT(CASE WHEN {_HEALTH_CASE} = 'AT_RISK'  THEN 1 END)      AS at_risk_count,
                SUM(pf.review_count)                                           AS total_reviews,
                ROUND(AVG(pf.verified_purchase_rate) * 100, 1)               AS avg_verified_pct
            FROM PRODUCTS p
            JOIN PRODUCT_FEATURES pf ON p.product_id = pf.product_id
        """
        rows = execute_query(conn, sql)
        return rows[0] if rows else {}

    def _get_product_list(self, conn, sort_by: str = "review_count", order: str = "DESC",
                           search: str = None, page: int = 1, per_page: int = 15) -> list:
        allowed_sorts = {
            "review_count": "pf.review_count",
            "avg_rating":   "pf.avg_review_rating",
            "price":        "p.price",
            "revenue":      "pf.review_count",  # Mock revenue using review_count
            "rating_5_pct": "pf.rating_5_pct",
            "helpful_votes":"pf.total_helpful_votes",
        }
        sort_col = allowed_sorts.get(sort_by, "pf.review_count")
        order_dir = "DESC" if order != "ASC" else "ASC"
        offset = (page - 1) * per_page

        where_sql = ""
        params = {}
        if search:
            where_sql = "WHERE UPPER(p.title) LIKE :search OR p.product_id LIKE :search"
            params["search"] = f"%{search.upper()}%"

        sql = f"""
            SELECT
                p.product_id,
                p.product_id AS stock_code,
                SUBSTR(p.title, 1, 100)    AS title,
                SUBSTR(p.title, 1, 100)    AS description,
                p.store,
                p.main_category,
                p.price AS unit_price,
                p.average_rating,
                pf.review_count,
                pf.avg_review_rating,
                pf.verified_purchase_rate,
                pf.image_review_rate,
                ROUND((pf.rating_4_pct + pf.rating_5_pct) * 100, 1) AS satisfaction_pct,
                ROUND((pf.rating_1_pct + pf.rating_2_pct) * 100, 1) AS negative_pct,
                pf.total_helpful_votes,
                {_HEALTH_CASE} AS health_status
            FROM PRODUCTS p
            JOIN PRODUCT_FEATURES pf ON p.product_id = pf.product_id
            {where_sql}
            ORDER BY {sort_col} {order_dir} NULLS LAST
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return execute_query(conn, sql, params)

    def _get_product_detail(self, conn, product_id: str) -> dict:
        product_sql = f"""
            SELECT
                p.product_id,
                p.title,
                p.store,
                p.main_category,
                p.categories,
                p.description,
                p.price,
                p.average_rating,
                p.rating_number,
                pf.review_count,
                pf.avg_review_rating,
                pf.total_helpful_votes,
                pf.verified_purchase_rate,
                pf.image_review_rate,
                pf.avg_images_per_review,
                ROUND(pf.rating_1_pct * 100, 1) AS pct_1star,
                ROUND(pf.rating_2_pct * 100, 1) AS pct_2star,
                ROUND(pf.rating_3_pct * 100, 1) AS pct_3star,
                ROUND(pf.rating_4_pct * 100, 1) AS pct_4star,
                ROUND(pf.rating_5_pct * 100, 1) AS pct_5star,
                {_HEALTH_CASE}                   AS health_status
            FROM PRODUCTS p
            JOIN PRODUCT_FEATURES pf ON p.product_id = pf.product_id
            WHERE p.product_id = :pid
        """
        rows = execute_query(conn, product_sql, {"pid": product_id})
        if not rows:
            return {"error": "Product not found"}

        product = rows[0]

        reviews_sql = """
            SELECT
                r.review_id,
                r.customer_id,
                r.rating,
                r.verified_purchase,
                r.has_image,
                r.helpful_vote,
                SUBSTR(r.text, 1, 200) AS review_snippet,
                TO_CHAR(r.review_date, 'YYYY-MM-DD') AS review_date
            FROM REVIEWS r
            WHERE r.product_id = :pid
            ORDER BY r.helpful_vote DESC NULLS LAST, r.review_date DESC
            FETCH FIRST 5 ROWS ONLY
        """
        product["top_reviews"] = execute_query(conn, reviews_sql, {"pid": product_id})

        images_sql = """
            SELECT image_id, image_url
            FROM REVIEW_IMAGES
            WHERE product_id = :pid
            FETCH FIRST 6 ROWS ONLY
        """
        product["images"] = execute_query(conn, images_sql, {"pid": product_id})

        return product

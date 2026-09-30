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
                data = self._get_review_kpis(conn)
            elif path.endswith("/ratings"):
                data = self._get_rating_distribution(conn)
            elif path.endswith("/media-comparison"):
                data = self._get_media_comparison(conn)
            elif path.endswith("/explorer"):
                rating = params.get("rating")
                sentiment = params.get("sentiment")
                media_only = params.get("media_only") in ("1", "true", "True")
                search = params.get("search")
                page = int(params.get("page", 1))
                per_page = int(params.get("per_page", 12))
                data = self._get_review_explorer(conn, rating, sentiment, media_only, search, page, per_page)
            elif path.endswith("/gallery"):
                limit = int(params.get("limit", 9))
                data = self._get_media_gallery(conn, limit)
            else:
                send_json_response(self, 404, {"error": f"Unknown path: {path}"})
                return

            send_json_response(self, 200, data)

        except Exception as e:
            send_json_response(self, 500, {"error": str(e)})

    # ─── Query Functions ────────────────────────────────────────────────────

    def _get_review_kpis(self, conn) -> dict:
        sql = """
            SELECT 
                COUNT(*) AS total_reviews,
                ROUND(AVG(rating), 2) AS avg_rating,
                COUNT(CASE WHEN rating >= 4 THEN 1 END) AS positive_count,
                COUNT(CASE WHEN rating = 3 THEN 1 END) AS neutral_count,
                COUNT(CASE WHEN rating <= 2 THEN 1 END) AS negative_count,
                COUNT(CASE WHEN has_image = 1 THEN 1 END) AS media_reviews_count,
                ROUND(COUNT(CASE WHEN has_image = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS media_rate_pct
            FROM REVIEWS
        """
        rows = execute_query(conn, sql)
        if rows and rows[0]["total_reviews"] > 0:
            row = rows[0]
            tot = row["total_reviews"]
            row["positive_pct"] = round(row["positive_count"] * 100.0 / tot, 1) if tot else 0
            row["negative_pct"] = round(row["negative_count"] * 100.0 / tot, 1) if tot else 0
            return row
        return {}

    def _get_rating_distribution(self, conn) -> list:
        sql = """
            SELECT 
                ROUND(rating) AS star_rating,
                COUNT(*) AS review_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS share_pct
            FROM REVIEWS
            WHERE rating IS NOT NULL
            GROUP BY ROUND(rating)
            ORDER BY star_rating DESC
        """
        return execute_query(conn, sql)

    def _get_media_comparison(self, conn) -> list:
        sql = """
            SELECT 
                CASE WHEN has_image = 1 THEN 'With Media' ELSE 'Text-Only' END AS media_type,
                COUNT(*) AS review_count,
                ROUND(AVG(rating), 2) AS avg_rating,
                ROUND(COUNT(CASE WHEN rating >= 4 THEN 1 END) * 100.0 / COUNT(*), 1) AS satisfaction_rate
            FROM REVIEWS
            GROUP BY has_image
        """
        return execute_query(conn, sql)

    def _get_review_explorer(self, conn, rating=None, sentiment=None, media_only=False, search=None, page=1, per_page=12) -> list:
        where_clauses = []
        params = {}

        if rating:
            where_clauses.append("r.rating = :rating")
            params["rating"] = int(rating)
        
        if sentiment and sentiment != "ALL":
            if sentiment == "POSITIVE":
                where_clauses.append("r.rating >= 4")
            elif sentiment == "NEGATIVE":
                where_clauses.append("r.rating <= 2")
            elif sentiment == "NEUTRAL":
                where_clauses.append("r.rating = 3")
                
        if media_only:
            where_clauses.append("r.has_image = 1")
            
        if search:
            where_clauses.append("(UPPER(TO_CHAR(p.title)) LIKE :search OR UPPER(TO_CHAR(r.text)) LIKE :search)")
            params["search"] = f"%{search.upper()}%"

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        offset = (page - 1) * per_page

        sql = f"""
            SELECT
                r.review_id,
                p.product_id AS stock_code,
                p.title AS product_name,
                r.customer_id,
                r.rating,
                CASE WHEN r.rating >= 4 THEN 'POSITIVE' WHEN r.rating <= 2 THEN 'NEGATIVE' ELSE 'NEUTRAL' END AS sentiment,
                r.text AS review_text,
                r.has_image AS has_media,
                (SELECT MIN(TO_CHAR(image_url)) FROM REVIEW_IMAGES ri WHERE ri.review_id = r.review_id) AS media_url,
                TO_CHAR(r.review_date, 'YYYY-MM-DD') AS review_date
            FROM REVIEWS r
            JOIN PRODUCTS p ON r.product_id = p.product_id
            {where_sql}
            ORDER BY r.helpful_vote DESC NULLS LAST, r.review_date DESC
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return execute_query(conn, sql, params)

    def _get_media_gallery(self, conn, limit=9) -> list:
        return self._get_review_explorer(conn, media_only=True, per_page=limit)

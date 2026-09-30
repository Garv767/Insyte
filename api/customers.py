from http.server import BaseHTTPRequestHandler
import urllib.parse
from ._db import get_connection, execute_query, send_json_response

_RFM_CTE = """
WITH rfm_base AS (
    SELECT
        customer_id,
        review_count,
        avg_rating_given,
        total_helpful_votes,
        verified_purchase_rate,
        first_review_date,
        last_review_date,
        ROUND(SYSDATE - last_review_date) AS recency_days,
        NTILE(5) OVER (ORDER BY ROUND(SYSDATE - last_review_date) DESC) AS r_score,
        NTILE(5) OVER (ORDER BY review_count ASC)                       AS f_score,
        NTILE(5) OVER (ORDER BY avg_rating_given ASC)                   AS m_score
    FROM CUSTOMERS
    WHERE last_review_date IS NOT NULL
),
rfm_scored AS (
    SELECT
        customer_id,
        review_count,
        avg_rating_given,
        total_helpful_votes,
        verified_purchase_rate,
        first_review_date,
        last_review_date,
        recency_days,
        r_score,
        f_score,
        m_score,
        (r_score + f_score + m_score) AS rfm_total,
        CASE
            WHEN r_score = 5 AND f_score >= 4              THEN 'Champions'
            WHEN r_score >= 4 AND f_score >= 3             THEN 'Loyal Reviewers'
            WHEN r_score >= 3 AND f_score >= 2             THEN 'Potential Loyalists'
            WHEN r_score = 5 AND f_score < 2               THEN 'New Reviewers'
            WHEN r_score <= 2 AND f_score >= 4             THEN 'At Risk'
            WHEN r_score = 1                               THEN 'Dormant'
            ELSE                                                'Occasional'
        END AS rfm_segment
    FROM rfm_base
)
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
                data = self._get_customer_kpis(conn)
            elif path.endswith("/segments") or path.endswith("/rfm-segments"):
                data = self._get_rfm_segments(conn)
            elif path.endswith("/heatmap") or path.endswith("/rfm-heatmap"):
                data = self._get_rfm_heatmap(conn)
            elif path.endswith("/list"):
                segment = params.get("segment")
                search  = params.get("search")
                page    = int(params.get("page", 1))
                per_page = int(params.get("per_page", 15))
                data = self._get_customer_list(conn, segment, search, page, per_page)
            elif "/customers/" in path:
                # /api/customers/{customer_id}
                customer_id = path.split("/customers/")[-1]
                data = self._get_customer_detail(conn, customer_id)
            else:
                send_json_response(self, 404, {"error": f"Unknown path: {path}"})
                return

            send_json_response(self, 200, data)

        except Exception as e:
            send_json_response(self, 500, {"error": str(e)})

    # ─── Query Functions ────────────────────────────────────────────────────

    def _get_customer_kpis(self, conn) -> dict:
        sql = _RFM_CTE + """
            SELECT
                COUNT(*)                                                       AS total_customers,
                COUNT(CASE WHEN review_count > 1 THEN 1 END)                  AS multi_review_customers,
                COUNT(CASE WHEN review_count = 1 THEN 1 END)                  AS single_review_customers,
                ROUND(AVG(review_count), 1)                                    AS avg_reviews_per_customer,
                ROUND(AVG(avg_rating_given), 2)                                AS avg_rating_given,
                ROUND(AVG(verified_purchase_rate) * 100, 1)                   AS avg_verified_pct,
                COUNT(CASE WHEN rfm_segment = 'Champions' THEN 1 END)         AS champion_count,
                COUNT(CASE WHEN rfm_segment = 'Dormant'   THEN 1 END)         AS dormant_count
            FROM rfm_scored
        """
        rows = execute_query(conn, sql)
        return rows[0] if rows else {}

    def _get_rfm_segments(self, conn) -> list:
        sql = _RFM_CTE + """
            SELECT
                rfm_segment,
                COUNT(*)                             AS customer_count,
                ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 1) AS customer_pct,
                ROUND(AVG(recency_days), 0)          AS avg_recency_days,
                ROUND(AVG(review_count), 1)          AS avg_order_frequency,
                ROUND(AVG(avg_rating_given), 2)      AS avg_rating_given,
                SUM(review_count)                    AS total_revenue
            FROM rfm_scored
            GROUP BY rfm_segment
            ORDER BY customer_count DESC
        """
        # Aliased total_revenue/avg_order_frequency to match frontend expectations
        return execute_query(conn, sql)

    def _get_rfm_heatmap(self, conn) -> list:
        sql = _RFM_CTE + """
            SELECT
                r_score AS "r", f_score AS "f",
                COUNT(*)    AS count,
                MAX(rfm_segment) AS segment
            FROM rfm_scored
            GROUP BY r_score, f_score
            ORDER BY r_score DESC, f_score ASC
        """
        return execute_query(conn, sql)

    def _get_customer_list(self, conn, segment=None, search=None,
                            page: int = 1, per_page: int = 15) -> list:
        where_clauses = []
        params = {}

        if segment and segment != "ALL":
            where_clauses.append("rfm_segment = :segment")
            params["segment"] = segment
        if search:
            where_clauses.append("UPPER(customer_id) LIKE :search")
            params["search"] = f"%{search.upper()}%"

        where_sql = ("WHERE " + " AND ".join(where_clauses)) if where_clauses else ""
        offset = (page - 1) * per_page

        sql = _RFM_CTE + f"""
            SELECT
                customer_id,
                review_count AS frequency_orders,
                ROUND(avg_rating_given * review_count, 2) AS monetary_spend,
                'Global' AS country,
                total_helpful_votes,
                verified_purchase_rate,
                recency_days,
                r_score, f_score, m_score,
                rfm_total,
                rfm_segment,
                TO_CHAR(first_review_date, 'YYYY-MM-DD') AS first_review_date,
                TO_CHAR(last_review_date,  'YYYY-MM-DD') AS last_review_date
            FROM rfm_scored
            {where_sql}
            ORDER BY rfm_total DESC, review_count DESC
            OFFSET {offset} ROWS FETCH NEXT {per_page} ROWS ONLY
        """
        return execute_query(conn, sql, params)

    def _get_customer_detail(self, conn, customer_id: str) -> dict:
        profile_sql = _RFM_CTE + """
            SELECT
                customer_id,
                review_count,
                avg_rating_given,
                total_helpful_votes,
                verified_purchase_rate,
                recency_days,
                r_score, f_score, m_score,
                rfm_segment,
                TO_CHAR(first_review_date, 'YYYY-MM-DD') AS first_review_date,
                TO_CHAR(last_review_date,  'YYYY-MM-DD') AS last_review_date
            FROM rfm_scored
            WHERE customer_id = :cid
        """
        profiles = execute_query(conn, profile_sql, {"cid": customer_id})
        if not profiles:
            return {"error": "Customer not found"}

        profile = profiles[0]

        reviews_sql = """
            SELECT
                r.review_id,
                p.title          AS product_title,
                r.rating,
                r.verified_purchase,
                r.has_image,
                r.helpful_vote,
                SUBSTR(r.text, 1, 150) AS review_snippet,
                TO_CHAR(r.review_date, 'YYYY-MM-DD') AS review_date
            FROM REVIEWS r
            JOIN PRODUCTS p ON r.product_id = p.product_id
            WHERE r.customer_id = :cid
            ORDER BY r.helpful_vote DESC NULLS LAST, r.review_date DESC
            FETCH FIRST 5 ROWS ONLY
        """
        profile["recent_reviews"] = execute_query(conn, reviews_sql, {"cid": customer_id})
        return profile

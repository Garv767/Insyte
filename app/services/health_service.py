"""
INSYTE — Commercial Product Health Analytics Service
Computes composite commercial viability matrix categorizing products into
HEALTHY, WATCH, or AT_RISK based on returns, ratings, and revenue trajectories.
"""

from app.database import execute_query_dict, is_database_connected

def get_product_health_summary():
    matrix = get_product_health_matrix()
    healthy = sum(1 for p in matrix if p["health_status"] == "HEALTHY")
    watch = sum(1 for p in matrix if p["health_status"] == "WATCH")
    at_risk = sum(1 for p in matrix if p["health_status"] == "AT_RISK")
    total = len(matrix)

    return {
        "total_monitored": total,
        "healthy_count": healthy,
        "healthy_pct": round(healthy * 100.0 / total, 1) if total else 0,
        "watch_count": watch,
        "watch_pct": round(watch * 100.0 / total, 1) if total else 0,
        "at_risk_count": at_risk,
        "at_risk_pct": round(at_risk * 100.0 / total, 1) if total else 0
    }

def get_product_health_matrix(status_filter=None, search=None):
    if is_database_connected():
        sql = """
            SELECT 
                stock_code,
                description,
                unit_price,
                revenue,
                units_sold,
                return_rate_pct,
                avg_rating,
                review_count,
                negative_pct,
                media_attachment_rate,
                health_status
            FROM V_PRODUCT_HEALTH_MATRIX
            WHERE 1=1
        """
        params = {}
        if status_filter and status_filter != "ALL":
            sql += " AND health_status = :status"
            params["status"] = status_filter
        if search:
            sql += " AND (UPPER(description) LIKE :s OR stock_code LIKE :s)"
            params["s"] = f"%{search.upper()}%"

        sql += " ORDER BY revenue DESC"
        data, _ = execute_query_dict(sql, params)
        if data:
            return data

    demo_matrix = [
        {"stock_code": "85123A", "description": "WHITE HANGING HEART T-LIGHT HOLDER", "unit_price": 2.55, "revenue": 182450.25, "units_sold": 54200, "return_rate_pct": 1.2, "avg_rating": 4.8, "review_count": 142, "negative_pct": 3.5, "media_rate": 19.7, "health_status": "HEALTHY", "rationale": "High sales velocity, minimal returns (<2%), high satisfaction."},
        {"stock_code": "22423", "description": "REGENCY CAKESTAND 3 TIER", "unit_price": 12.75, "revenue": 164820.50, "units_sold": 13200, "return_rate_pct": 2.1, "avg_rating": 4.6, "review_count": 98, "negative_pct": 5.1, "media_rate": 24.5, "health_status": "HEALTHY", "rationale": "Strong margin, steady reviews, low cancellation risk."},
        {"stock_code": "85099B", "description": "JUMBO BAG RED RETROSPOT", "unit_price": 1.95, "revenue": 128910.80, "units_sold": 48900, "return_rate_pct": 0.9, "avg_rating": 4.7, "review_count": 115, "negative_pct": 2.6, "media_rate": 14.8, "health_status": "HEALTHY", "rationale": "High volume essential, near zero returns."},
        {"stock_code": "47566", "description": "PARTY BUNTING", "unit_price": 4.65, "revenue": 115420.10, "units_sold": 26800, "return_rate_pct": 4.8, "avg_rating": 3.7, "review_count": 76, "negative_pct": 18.4, "media_rate": 11.8, "health_status": "WATCH", "rationale": "Elevated return rate (4.8%) and sub-4.0 average rating."},
        {"stock_code": "22720", "description": "SET OF 3 CAKE TINS PANTRY DESIGN", "unit_price": 4.95, "revenue": 84210.50, "units_sold": 18900, "return_rate_pct": 8.4, "avg_rating": 2.8, "review_count": 52, "negative_pct": 36.5, "media_rate": 28.8, "health_status": "AT_RISK", "rationale": "Severe returns (>8%) and elevated negative feedback on packaging dents."},
        {"stock_code": "21232", "description": "STRAWBERRY CERAMIC TRINKET BOX", "unit_price": 1.25, "revenue": 34120.00, "units_sold": 19400, "return_rate_pct": 9.2, "avg_rating": 2.6, "review_count": 48, "negative_pct": 41.7, "media_rate": 16.7, "health_status": "AT_RISK", "rationale": "High breakage in transit driving 9.2% return rate."},
        {"stock_code": "84879", "description": "ASSORTED COLOUR BIRD ORNAMENT", "unit_price": 1.69, "revenue": 98420.30, "units_sold": 38400, "return_rate_pct": 0.8, "avg_rating": 4.9, "review_count": 89, "negative_pct": 1.1, "media_rate": 31.5, "health_status": "HEALTHY", "rationale": "Top tier customer satisfaction (4.9 stars) and high photo sharing."},
        {"stock_code": "20725", "description": "LUNCH BAG RED RETROSPOT", "unit_price": 1.65, "revenue": 87640.20, "units_sold": 32100, "return_rate_pct": 5.2, "avg_rating": 3.6, "review_count": 64, "negative_pct": 15.6, "media_rate": 9.4, "health_status": "WATCH", "rationale": "Slightly elevated return rate and moderate zip durability complaints."}
    ]

    filtered = demo_matrix
    if status_filter and status_filter != "ALL":
        filtered = [p for p in filtered if p["health_status"] == status_filter]
    if search:
        s = search.upper()
        filtered = [p for p in filtered if s in p["description"].upper() or s in p["stock_code"].upper()]

    return filtered

"""
INSYTE — Customer Reviews & Media Analytics Service
Analyzes customer feedback, star ratings, transparent rule-based sentiment,
media attachment correlations, and interactive media gallery assets.
"""

from app.database import execute_query_dict, is_database_connected

def get_review_kpis():
    if is_database_connected():
        sql = """
            SELECT 
                COUNT(*) AS total_reviews,
                ROUND(AVG(rating), 2) AS avg_rating,
                COUNT(CASE WHEN sentiment_label = 'POSITIVE' OR rating >= 4 THEN 1 END) AS positive_count,
                COUNT(CASE WHEN sentiment_label = 'NEUTRAL' OR rating = 3 THEN 1 END) AS neutral_count,
                COUNT(CASE WHEN sentiment_label = 'NEGATIVE' OR rating <= 2 THEN 1 END) AS negative_count,
                COUNT(CASE WHEN has_media = 1 THEN 1 END) AS media_reviews_count,
                ROUND(COUNT(CASE WHEN has_media = 1 THEN 1 END) * 100.0 / NULLIF(COUNT(*), 0), 1) AS media_rate_pct
            FROM REVIEWS
        """
        data, _ = execute_query_dict(sql)
        if data and data[0]["total_reviews"] > 0:
            row = data[0]
            tot = row["total_reviews"]
            row["positive_pct"] = round(row["positive_count"] * 100.0 / tot, 1) if tot else 0
            row["negative_pct"] = round(row["negative_count"] * 100.0 / tot, 1) if tot else 0
            return row

    return {
        "total_reviews": 3480,
        "avg_rating": 4.38,
        "positive_count": 2680,
        "positive_pct": 77.0,
        "neutral_count": 480,
        "neutral_pct": 13.8,
        "negative_count": 320,
        "negative_pct": 9.2,
        "media_reviews_count": 780,
        "media_rate_pct": 22.4
    }

def get_rating_distribution():
    if is_database_connected():
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
        data, _ = execute_query_dict(sql)
        if data:
            return data

    return [
        {"star_rating": 5, "review_count": 2150, "share_pct": 61.8},
        {"star_rating": 4, "review_count": 530, "share_pct": 15.2},
        {"star_rating": 3, "review_count": 480, "share_pct": 13.8},
        {"star_rating": 2, "review_count": 180, "share_pct": 5.2},
        {"star_rating": 1, "review_count": 140, "share_pct": 4.0}
    ]

def get_media_comparison():
    if is_database_connected():
        sql = """
            SELECT 
                CASE WHEN has_media = 1 THEN 'With Media' ELSE 'Text-Only' END AS media_type,
                COUNT(*) AS review_count,
                ROUND(AVG(rating), 2) AS avg_rating,
                ROUND(COUNT(CASE WHEN rating >= 4 THEN 1 END) * 100.0 / COUNT(*), 1) AS satisfaction_rate
            FROM REVIEWS
            GROUP BY has_media
        """
        data, _ = execute_query_dict(sql)
        if data:
            return data

    return [
        {"media_type": "With Media (Photos/Video)", "review_count": 780, "avg_rating": 4.62, "satisfaction_rate": 84.6},
        {"media_type": "Text-Only Reviews", "review_count": 2700, "avg_rating": 4.31, "satisfaction_rate": 74.8}
    ]

def get_review_explorer(rating=None, sentiment=None, media_only=False, search=None, page=1, per_page=12):
    demo_reviews = [
        {"review_id": "REV-89102", "stock_code": "85123A", "product_name": "WHITE HANGING HEART T-LIGHT HOLDER", "customer_id": "14646", "rating": 5.0, "sentiment": "POSITIVE", "review_text": "Exceptional build quality. Shipped fast and looks beautiful in the showroom. Very pleased with this purchase.", "has_media": 1, "media_url": "https://images.unsplash.com/photo-1513519245088-0e12902e5a38?w=400", "review_date": "2024-11-28"},
        {"review_id": "REV-89103", "stock_code": "22423", "product_name": "REGENCY CAKESTAND 3 TIER", "customer_id": "17450", "rating": 5.0, "sentiment": "POSITIVE", "review_text": "Stunning vintage design. Easy to assemble and our tea party clients absolutely loved the presentation.", "has_media": 1, "media_url": "https://images.unsplash.com/photo-1578985545062-69928b1d9587?w=400", "review_date": "2024-11-25"},
        {"review_id": "REV-89104", "stock_code": "85099B", "product_name": "JUMBO BAG RED RETROSPOT", "customer_id": "14911", "rating": 4.0, "sentiment": "POSITIVE", "review_text": "Strong zippers and great capacity. Material is thicker than expected for the price. Would buy again.", "has_media": 0, "media_url": None, "review_date": "2024-11-20"},
        {"review_id": "REV-89105", "stock_code": "47566", "product_name": "PARTY BUNTING", "customer_id": "12415", "rating": 3.0, "sentiment": "NEUTRAL", "review_text": "Decent length but color was slightly lighter than pictured in the online catalog. Worked fine for the event.", "has_media": 0, "media_url": None, "review_date": "2024-11-15"},
        {"review_id": "REV-89106", "stock_code": "84879", "product_name": "ASSORTED COLOUR BIRD ORNAMENT", "customer_id": "17511", "rating": 5.0, "sentiment": "POSITIVE", "review_text": "Charming details on every bird. Packaged securely with bubble wrap so none were chipped.", "has_media": 1, "media_url": "https://images.unsplash.com/photo-1544816155-12df9643f363?w=400", "review_date": "2024-11-10"},
        {"review_id": "REV-89107", "stock_code": "22720", "product_name": "SET OF 3 CAKE TINS PANTRY DESIGN", "customer_id": "16029", "rating": 2.0, "sentiment": "NEGATIVE", "review_text": "Smallest tin lid arrived with a noticeable dent. Metal feels somewhat flimsy compared to last batch.", "has_media": 1, "media_url": "https://images.unsplash.com/photo-1588195538326-c5b1e9f80a1b?w=400", "review_date": "2024-10-28"},
        {"review_id": "REV-89108", "stock_code": "22197", "product_name": "SMALL POPCORN HOLDER", "customer_id": "16684", "rating": 5.0, "sentiment": "POSITIVE", "review_text": "Awesome novelty item for movie nights. Kids love them and disposable cleanup is quick.", "has_media": 0, "media_url": None, "review_date": "2024-10-20"},
        {"review_id": "REV-89109", "stock_code": "21212", "product_name": "PACK OF 72 RETROSPOT CAKE CASES", "customer_id": "18102", "rating": 4.0, "sentiment": "POSITIVE", "review_text": "Holds shape nicely during baking without oil staining the pattern. Excellent bulk value.", "has_media": 0, "media_url": None, "review_date": "2024-10-14"}
    ]

    filtered = demo_reviews
    if rating:
        filtered = [r for r in filtered if int(r["rating"]) == int(rating)]
    if sentiment and sentiment != "ALL":
        filtered = [r for r in filtered if r["sentiment"] == sentiment]
    if media_only:
        filtered = [r for r in filtered if r["has_media"] == 1]
    if search:
        s = search.lower()
        filtered = [r for r in filtered if s in r["product_name"].lower() or s in r["review_text"].lower() or s in r["stock_code"].lower()]

    return filtered

def get_media_gallery(limit=9):
    """Returns visual cards for reviews that have associated photo or video attachments."""
    reviews = get_review_explorer(media_only=True)
    return reviews[:limit]

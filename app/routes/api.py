"""
INSYTE — REST API Blueprint
Routes client requests through service layers with input validation and parameter binding.
"""

from flask import Blueprint, jsonify, request
from app.services import (
    overview_service,
    customer_service,
    product_service,
    sales_service,
    review_service,
    health_service,
    vector_service,
    sql_insights_service
)
from app.database import is_database_connected

api_bp = Blueprint("api", __name__, url_prefix="/api")

# System Health & Database Status
@api_bp.route("/health-check")
def health_check():
    connected = is_database_connected()
    return jsonify({
        "status": "online",
        "oracle_connected": connected,
        "database_mode": "Oracle 23ai Free (Thin Mode)" if connected else "Demonstration / Standby Mode",
        "port": 1521,
        "service": "FREEPDB1"
    })

# 1. Overview Endpoints
@api_bp.route("/overview/kpis")
def overview_kpis():
    country = request.args.get("country")
    date_range = request.args.get("date_range")
    return jsonify(overview_service.get_overview_kpis(date_range, country))

@api_bp.route("/overview/trends")
def overview_trends():
    granularity = request.args.get("granularity", "MONTH")
    return jsonify(overview_service.get_revenue_trends(granularity))

@api_bp.route("/overview/top-products")
def overview_top_products():
    limit = int(request.args.get("limit", 8))
    return jsonify(overview_service.get_top_products(limit))

@api_bp.route("/overview/countries")
def overview_countries():
    return jsonify(overview_service.get_country_performance())

@api_bp.route("/overview/insights")
def overview_insights():
    return jsonify(overview_service.get_factual_insights())

# 2. Customer Analytics Endpoints
@api_bp.route("/customers/kpis")
def customer_kpis():
    return jsonify(customer_service.get_customer_kpis())

@api_bp.route("/customers/rfm-segments")
def customer_rfm_segments():
    return jsonify(customer_service.get_rfm_segments())

@api_bp.route("/customers/rfm-heatmap")
def customer_rfm_heatmap():
    return jsonify(customer_service.get_rfm_heatmap())

@api_bp.route("/customers/list")
def customer_list():
    segment = request.args.get("segment")
    search = request.args.get("search")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 15))
    return jsonify(customer_service.get_customer_list(segment, search, page, per_page))

@api_bp.route("/customers/<customer_id>")
def customer_detail(customer_id):
    return jsonify(customer_service.get_customer_detail(customer_id))

# 3. Product Analytics Endpoints
@api_bp.route("/products/kpis")
def product_kpis():
    return jsonify(product_service.get_product_kpis())

@api_bp.route("/products/list")
def product_list():
    sort_by = request.args.get("sort_by", "revenue")
    order = request.args.get("order", "desc")
    search = request.args.get("search")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 15))
    return jsonify(product_service.get_product_list(sort_by, order, search, page, per_page))

@api_bp.route("/products/<stock_code>")
def product_detail(stock_code):
    return jsonify(product_service.get_product_detail(stock_code))

# 4. Sales & Trends Endpoints
@api_bp.route("/sales/overview")
def sales_overview():
    return jsonify(sales_service.get_sales_overview())

@api_bp.route("/sales/cohorts")
def sales_cohorts():
    return jsonify(sales_service.get_cohort_retention_matrix())

@api_bp.route("/sales/aov")
def sales_aov():
    return jsonify(sales_service.get_aov_trend())

# 5. Reviews & Media Endpoints
@api_bp.route("/reviews/kpis")
def review_kpis():
    return jsonify(review_service.get_review_kpis())

@api_bp.route("/reviews/ratings")
def review_ratings():
    return jsonify(review_service.get_rating_distribution())

@api_bp.route("/reviews/media-comparison")
def review_media_comparison():
    return jsonify(review_service.get_media_comparison())

@api_bp.route("/reviews/explorer")
def review_explorer():
    rating = request.args.get("rating")
    sentiment = request.args.get("sentiment")
    media_only = request.args.get("media_only") in ("1", "true", "True")
    search = request.args.get("search")
    page = int(request.args.get("page", 1))
    per_page = int(request.args.get("per_page", 12))
    return jsonify(review_service.get_review_explorer(rating, sentiment, media_only, search, page, per_page))

@api_bp.route("/reviews/gallery")
def review_gallery():
    limit = int(request.args.get("limit", 9))
    return jsonify(review_service.get_media_gallery(limit))

# 6. Commercial Product Health Endpoints
@api_bp.route("/health/summary")
def health_summary():
    return jsonify(health_service.get_product_health_summary())

@api_bp.route("/health/matrix")
def health_matrix():
    status_filter = request.args.get("status")
    search = request.args.get("search")
    return jsonify(health_service.get_product_health_matrix(status_filter, search))

# 7. Semantic Vector & Global Search
@api_bp.route("/search/semantic")
def search_semantic():
    q = request.args.get("q", "")
    top_k = int(request.args.get("top_k", 5))
    return jsonify(vector_service.search_semantic_products(q, top_k))

# 8. SQL Insights & Academic Viewer
@api_bp.route("/sql/catalog")
def sql_catalog():
    return jsonify(sql_insights_service.get_sql_catalog())

@api_bp.route("/sql/query/<query_id>")
def sql_query_details(query_id):
    return jsonify(sql_insights_service.get_sql_query_details(query_id))

@api_bp.route("/sql/dictionary/<category>")
def sql_dictionary(category):
    return jsonify(sql_insights_service.get_data_dictionary(category))

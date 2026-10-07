"""
Script to create and verify Stored Procedures, Views, and Subqueries in Oracle 23ai
for INSYTE Backend Demonstration.
"""

import os
import sys
import oracledb
from dotenv import load_dotenv

load_dotenv()

def get_connection():
    wallet_dir = os.path.abspath("wallet")
    db_user = os.getenv("APP_ADMIN_USER", "ADMIN")
    db_password = os.getenv("APP_ADMIN_PASSWORD", "garv767@INSYTE")
    tns_name = os.getenv("TNS_NAME", "insyte_high")
    wallet_password = os.getenv("WALLET_PASSWORD", "")

    return oracledb.connect(
        user=db_user,
        password=db_password,
        dsn=tns_name,
        config_dir=wallet_dir,
        wallet_location=wallet_dir,
        wallet_password=wallet_password
    )

def deploy_and_test():
    conn = get_connection()
    cursor = conn.cursor()
    print("[+] Connected to Oracle 23ai Database.")

    # 1. VIEWS
    views = [
        ("V_PRODUCT_PERFORMANCE_METRICS", """
            CREATE OR REPLACE VIEW V_PRODUCT_PERFORMANCE_METRICS AS
            SELECT 
                p.product_id,
                SUBSTR(p.title, 1, 60) AS product_name,
                p.main_category,
                p.store,
                p.price,
                p.average_rating,
                NVL(pf.review_count, 0) AS total_reviews,
                NVL(pf.total_helpful_votes, 0) AS helpful_votes,
                NVL(pf.verified_purchase_rate, 0) * 100 AS verified_purchase_pct,
                NVL(pf.image_review_rate, 0) * 100 AS image_review_pct
            FROM PRODUCTS p
            LEFT JOIN PRODUCT_FEATURES pf ON p.product_id = pf.product_id
        """),
        ("V_CUSTOMER_ENGAGEMENT_SUMMARY", """
            CREATE OR REPLACE VIEW V_CUSTOMER_ENGAGEMENT_SUMMARY AS
            SELECT 
                c.customer_id,
                c.review_count,
                c.product_count,
                ROUND(c.avg_rating_given, 2) AS avg_rating,
                c.total_helpful_votes,
                ROUND(c.verified_purchase_rate * 100, 1) AS verified_pct,
                c.first_review_date,
                c.last_review_date,
                ROUND(c.last_review_date - c.first_review_date) AS activity_span_days,
                CASE 
                    WHEN c.review_count >= 5 AND c.total_helpful_votes >= 10 THEN 'Elite Reviewer'
                    WHEN c.review_count >= 3 THEN 'Active Contributor'
                    ELSE 'Standard Customer'
                END AS reviewer_tier
            FROM CUSTOMERS c
        """),
        ("V_CATEGORY_BENCHMARK_ANALYSIS", """
            CREATE OR REPLACE VIEW V_CATEGORY_BENCHMARK_ANALYSIS AS
            SELECT 
                p.main_category,
                COUNT(p.product_id) AS total_products,
                ROUND(AVG(p.price), 2) AS avg_category_price,
                ROUND(AVG(p.average_rating), 2) AS avg_category_rating,
                SUM(NVL(pf.review_count, 0)) AS total_category_reviews,
                ROUND(AVG(NVL(pf.verified_purchase_rate, 0)) * 100, 2) AS avg_verified_rate_pct
            FROM PRODUCTS p
            LEFT JOIN PRODUCT_FEATURES pf ON p.product_id = pf.product_id
            WHERE p.main_category IS NOT NULL
            GROUP BY p.main_category
        """),
        ("V_HIGH_IMPACT_CRITICAL_REVIEWS", """
            CREATE OR REPLACE VIEW V_HIGH_IMPACT_CRITICAL_REVIEWS AS
            SELECT 
                r.review_id,
                r.product_id,
                SUBSTR(p.title, 1, 50) AS product_name,
                r.customer_id,
                r.rating,
                r.helpful_vote,
                r.review_date,
                r.verified_purchase,
                SUBSTR(TO_CHAR(r.title), 1, 80) AS review_headline,
                SUBSTR(TO_CHAR(r.text), 1, 150) AS review_snippet
            FROM REVIEWS r
            JOIN PRODUCTS p ON r.product_id = p.product_id
            WHERE r.rating <= 2.0 
              AND r.helpful_vote >= 3
        """)
    ]

    print("\n--- Deploying Analytical Views ---")
    for name, sql in views:
        cursor.execute(sql)
        print(f" View {name} created successfully.")
    conn.commit()

    # 2. PL/SQL STORED PROCEDURES & FUNCTIONS
    plsql_blocks = [
        ("FN_CALCULATE_CUSTOMER_TRUST_SCORE", """
            CREATE OR REPLACE FUNCTION FN_CALCULATE_CUSTOMER_TRUST_SCORE(
                p_customer_id IN VARCHAR2
            ) RETURN NUMBER IS
                v_verified_rate NUMBER := 0;
                v_helpful_votes NUMBER := 0;
                v_review_count  NUMBER := 0;
                v_trust_score   NUMBER := 0;
            BEGIN
                SELECT 
                    NVL(verified_purchase_rate, 0),
                    NVL(total_helpful_votes, 0),
                    NVL(review_count, 0)
                INTO 
                    v_verified_rate,
                    v_helpful_votes,
                    v_review_count
                FROM CUSTOMERS
                WHERE customer_id = p_customer_id;

                -- Weighted Trust Formula:
                -- 50% Verified Purchase Rate + 30% Helpful Votes capped + 20% Volume consistency
                v_trust_score := ROUND(
                    (v_verified_rate * 50) + 
                    (LEAST(v_helpful_votes, 20) / 20 * 30) + 
                    (LEAST(v_review_count, 10) / 10 * 20),
                    2
                );

                RETURN v_trust_score;
            EXCEPTION
                WHEN NO_DATA_FOUND THEN
                    RETURN 0;
                WHEN OTHERS THEN
                    RETURN NULL;
            END FN_CALCULATE_CUSTOMER_TRUST_SCORE;
        """),
        ("SP_RECALCULATE_PRODUCT_METRICS", """
            CREATE OR REPLACE PROCEDURE SP_RECALCULATE_PRODUCT_METRICS(
                p_product_id IN VARCHAR2,
                p_updated_count OUT NUMBER,
                p_new_avg_rating OUT NUMBER
            ) IS
                v_rev_count   NUMBER := 0;
                v_avg_rating  NUMBER := 0;
                v_helpful     NUMBER := 0;
                v_verified    NUMBER := 0;
                v_with_img    NUMBER := 0;
            BEGIN
                -- Aggregate stats from active REVIEWS
                SELECT 
                    COUNT(*),
                    ROUND(NVL(AVG(rating), 0), 2),
                    NVL(SUM(helpful_vote), 0),
                    ROUND(NVL(AVG(verified_purchase), 0), 4),
                    ROUND(NVL(AVG(has_image), 0), 4)
                INTO 
                    v_rev_count,
                    v_avg_rating,
                    v_helpful,
                    v_verified,
                    v_with_img
                FROM REVIEWS
                WHERE product_id = p_product_id;

                -- Update PRODUCT_FEATURES
                UPDATE PRODUCT_FEATURES
                SET 
                    review_count = v_rev_count,
                    avg_review_rating = v_avg_rating,
                    total_helpful_votes = v_helpful,
                    verified_purchase_rate = v_verified,
                    image_review_rate = v_with_img
                WHERE product_id = p_product_id;

                -- Also update PRODUCTS table aggregate
                UPDATE PRODUCTS
                SET 
                    average_rating = v_avg_rating,
                    rating_number = v_rev_count
                WHERE product_id = p_product_id;

                p_updated_count := v_rev_count;
                p_new_avg_rating := v_avg_rating;

                COMMIT;
            EXCEPTION
                WHEN OTHERS THEN
                    ROLLBACK;
                    RAISE;
            END SP_RECALCULATE_PRODUCT_METRICS;
        """),
        ("SP_GET_PRODUCT_INSIGHTS", """
            CREATE OR REPLACE PROCEDURE SP_GET_PRODUCT_INSIGHTS(
                p_product_id     IN VARCHAR2,
                p_product_title  OUT VARCHAR2,
                p_category       OUT VARCHAR2,
                p_price          OUT NUMBER,
                p_avg_rating     OUT NUMBER,
                p_total_reviews  OUT NUMBER,
                p_reviews_cursor OUT SYS_REFCURSOR
            ) IS
            BEGIN
                -- Fetch Product Metadata
                SELECT 
                    SUBSTR(p.title, 1, 100),
                    p.main_category,
                    p.price,
                    p.average_rating,
                    p.rating_number
                INTO 
                    p_product_title,
                    p_category,
                    p_price,
                    p_avg_rating,
                    p_total_reviews
                FROM PRODUCTS p
                WHERE p.product_id = p_product_id;

                -- Open Ref Cursor for the top 5 most helpful reviews
                OPEN p_reviews_cursor FOR
                    SELECT 
                        review_id,
                        customer_id,
                        rating,
                        helpful_vote,
                        verified_purchase,
                        review_date,
                        SUBSTR(TO_CHAR(title), 1, 80) AS review_title
                    FROM REVIEWS
                    WHERE product_id = p_product_id
                    ORDER BY helpful_vote DESC, review_date DESC
                    FETCH FIRST 5 ROWS ONLY;
            END SP_GET_PRODUCT_INSIGHTS;
        """),
        ("SP_CUSTOMER_ACTIVITY_REPORT", """
            CREATE OR REPLACE PROCEDURE SP_CUSTOMER_ACTIVITY_REPORT(
                p_customer_id       IN VARCHAR2,
                p_review_count      OUT NUMBER,
                p_avg_rating        OUT NUMBER,
                p_trust_score       OUT NUMBER,
                p_tier              OUT VARCHAR2,
                p_reviews_cursor    OUT SYS_REFCURSOR
            ) IS
            BEGIN
                SELECT 
                    c.review_count,
                    ROUND(c.avg_rating_given, 2),
                    FN_CALCULATE_CUSTOMER_TRUST_SCORE(c.customer_id),
                    CASE 
                        WHEN c.review_count >= 5 THEN 'Elite Reviewer'
                        WHEN c.review_count >= 3 THEN 'Active Contributor'
                        ELSE 'Standard Customer'
                    END
                INTO 
                    p_review_count,
                    p_avg_rating,
                    p_trust_score,
                    p_tier
                FROM CUSTOMERS c
                WHERE c.customer_id = p_customer_id;

                OPEN p_reviews_cursor FOR
                    SELECT 
                        r.review_id,
                        r.product_id,
                        SUBSTR(p.title, 1, 50) AS product_name,
                        r.rating,
                        r.helpful_vote,
                        r.review_date
                    FROM REVIEWS r
                    LEFT JOIN PRODUCTS p ON r.product_id = p.product_id
                    WHERE r.customer_id = p_customer_id
                    ORDER BY r.review_date DESC;
            END SP_CUSTOMER_ACTIVITY_REPORT;
        """)
    ]

    print("\n--- Deploying Stored Procedures & Functions ---")
    for name, code in plsql_blocks:
        cursor.execute(code)
        print(f" PL/SQL Object {name} compiled successfully.")
    conn.commit()

    print("\n--- Testing Views & Procedures ---")

    # Test View 1
    cursor.execute("SELECT * FROM V_PRODUCT_PERFORMANCE_METRICS WHERE total_reviews > 10 FETCH FIRST 2 ROWS ONLY")
    print(f" [V_PRODUCT_PERFORMANCE_METRICS sample]: {cursor.fetchall()}")

    # Test View 2
    cursor.execute("SELECT * FROM V_CUSTOMER_ENGAGEMENT_SUMMARY WHERE review_count >= 3 FETCH FIRST 2 ROWS ONLY")
    print(f" [V_CUSTOMER_ENGAGEMENT_SUMMARY sample]: {cursor.fetchall()}")

    # Test View 3
    cursor.execute("SELECT * FROM V_CATEGORY_BENCHMARK_ANALYSIS FETCH FIRST 3 ROWS ONLY")
    print(f" [V_CATEGORY_BENCHMARK_ANALYSIS sample]: {cursor.fetchall()}")

    # Test View 4
    cursor.execute("SELECT * FROM V_HIGH_IMPACT_CRITICAL_REVIEWS FETCH FIRST 2 ROWS ONLY")
    print(f" [V_HIGH_IMPACT_CRITICAL_REVIEWS sample]: {cursor.fetchall()}")

    # Find a sample customer_id and product_id for testing procedures
    cursor.execute("SELECT customer_id FROM CUSTOMERS WHERE review_count >= 3 FETCH FIRST 1 ROWS ONLY")
    test_cust = cursor.fetchone()[0]

    cursor.execute("SELECT product_id FROM PRODUCTS WHERE rating_number >= 5 FETCH FIRST 1 ROWS ONLY")
    test_prod = cursor.fetchone()[0]

    # Test Function
    cursor.execute("SELECT FN_CALCULATE_CUSTOMER_TRUST_SCORE(:1) FROM DUAL", [test_cust])
    score = cursor.fetchone()[0]
    print(f" [FN_CALCULATE_CUSTOMER_TRUST_SCORE for {test_cust}]: {score}/100")

    # Test SP_GET_PRODUCT_INSIGHTS
    out_title = cursor.var(oracledb.STRING)
    out_cat = cursor.var(oracledb.STRING)
    out_price = cursor.var(oracledb.NUMBER)
    out_rating = cursor.var(oracledb.NUMBER)
    out_reviews = cursor.var(oracledb.NUMBER)
    out_cur = cursor.var(oracledb.CURSOR)

    cursor.callproc("SP_GET_PRODUCT_INSIGHTS", [
        test_prod, out_title, out_cat, out_price, out_rating, out_reviews, out_cur
    ])
    rev_rows = out_cur.getvalue().fetchall()
    print(f" [SP_GET_PRODUCT_INSIGHTS for {test_prod}]: Title='{out_title.getvalue()}', Reviews={out_reviews.getvalue()}, Sample reviews returned={len(rev_rows)}")

    # Test SP_CUSTOMER_ACTIVITY_REPORT
    out_cnt = cursor.var(oracledb.NUMBER)
    out_avg = cursor.var(oracledb.NUMBER)
    out_trust = cursor.var(oracledb.NUMBER)
    out_tier = cursor.var(oracledb.STRING)
    out_c_cur = cursor.var(oracledb.CURSOR)

    cursor.callproc("SP_CUSTOMER_ACTIVITY_REPORT", [
        test_cust, out_cnt, out_avg, out_trust, out_tier, out_c_cur
    ])
    c_revs = out_c_cur.getvalue().fetchall()
    print(f" [SP_CUSTOMER_ACTIVITY_REPORT for {test_cust}]: Tier='{out_tier.getvalue()}', Reviews={out_cnt.getvalue()}, Trust={out_trust.getvalue()}, Details count={len(c_revs)}")

    cursor.close()
    conn.close()
    print("\n[+] ALL VIEWS AND PROCEDURES DEPLOYED & TESTED SUCCESSFULLY!")

if __name__ == "__main__":
    deploy_and_test()

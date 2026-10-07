"""
INSYTE: Interactive Oracle Backend Live Demonstration Runner
Enables Insyte team to demonstrate Stored Procedures, Views, and Subqueries
directly to evaluators/professors with clean tabular output.
"""

import os
import sys
import time
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

def print_table(headers, rows):
    if not rows:
        print("  (No rows returned)")
        return
    # Convert all items to string (truncating LOBs/long strings)
    str_rows = []
    for r in rows:
        str_rows.append([str(c)[:45] if c is not None else "NULL" for c in r])
    
    col_widths = [len(h) for h in headers]
    for r in str_rows:
        for i, val in enumerate(r):
            col_widths[i] = max(col_widths[i], len(val))
    
    header_line = " | ".join(h.ljust(col_widths[i]) for i, h in enumerate(headers))
    sep_line = "-+-".join("-" * col_widths[i] for i in range(len(headers)))
    
    print("  " + header_line)
    print("  " + sep_line)
    for r in str_rows:
        print("  " + " | ".join(r[i].ljust(col_widths[i]) for i in range(len(headers))))

def run_query(cursor, title, sql, params=None, max_rows=5):
    print("\n" + "=" * 80)
    print(f" DEMONSTRATION: {title}")
    print("=" * 80)
    print(f"SQL QUERY:\n{sql.strip()}\n")
    
    t0 = time.time()
    cursor.execute(sql, params or {})
    cols = [col[0] for col in cursor.description]
    rows = cursor.fetchall()
    elapsed = (time.time() - t0) * 1000
    
    display_rows = rows[:max_rows]
    print(f"OUTPUT ({len(rows)} rows matched, showing top {len(display_rows)}, took {elapsed:.1f}ms):")
    print_table(cols, display_rows)

def demo_views(cursor):
    print("\n" + "#" * 80)
    print(" SECTION 1: ORACLE ANALYTICAL VIEWS")
    print("#" * 80)

    run_query(cursor, "View 1: Product Performance Metrics (V_PRODUCT_PERFORMANCE_METRICS)", 
        "SELECT product_id, product_name, main_category, price, average_rating, total_reviews, verified_purchase_pct FROM V_PRODUCT_PERFORMANCE_METRICS WHERE total_reviews >= 20 FETCH FIRST 5 ROWS ONLY")

    run_query(cursor, "View 2: Customer Engagement Summary (V_CUSTOMER_ENGAGEMENT_SUMMARY)", 
        "SELECT customer_id, review_count, avg_rating, total_helpful_votes, activity_span_days, reviewer_tier FROM V_CUSTOMER_ENGAGEMENT_SUMMARY WHERE review_count >= 3 FETCH FIRST 5 ROWS ONLY")

    run_query(cursor, "View 3: Category Benchmark Analysis (V_CATEGORY_BENCHMARK_ANALYSIS)", 
        "SELECT main_category, total_products, avg_category_price, avg_category_rating, total_category_reviews FROM V_CATEGORY_BENCHMARK_ANALYSIS ORDER BY total_category_reviews DESC FETCH FIRST 5 ROWS ONLY")

    run_query(cursor, "View 4: High Impact Critical Reviews (V_HIGH_IMPACT_CRITICAL_REVIEWS)", 
        "SELECT review_id, product_id, rating, helpful_vote, review_headline, review_snippet FROM V_HIGH_IMPACT_CRITICAL_REVIEWS FETCH FIRST 4 ROWS ONLY")

def demo_subqueries(cursor):
    print("\n" + "#" * 80)
    print(" SECTION 2: ADVANCED ORACLE SUBQUERIES")
    print("#" * 80)

    run_query(cursor, "Subquery 1: Scalar Subquery in SELECT (Price vs Category Avg Benchmark)",
        """
        SELECT 
            p.product_id,
            SUBSTR(p.title, 1, 35) AS product_name,
            p.price,
            ROUND((SELECT AVG(p2.price) FROM PRODUCTS p2 WHERE p2.main_category = p.main_category), 2) AS category_avg_price,
            ROUND(p.price - (SELECT AVG(p2.price) FROM PRODUCTS p2 WHERE p2.main_category = p.main_category), 2) AS price_variance
        FROM PRODUCTS p
        WHERE p.price IS NOT NULL AND p.main_category = 'Amazon Home'
        FETCH FIRST 5 ROWS ONLY
        """)

    run_query(cursor, "Subquery 2: Correlated Subquery with EXISTS (High-Rated Products with Critical Complaints)",
        """
        SELECT 
            p.product_id,
            SUBSTR(p.title, 1, 40) AS product_name,
            p.average_rating,
            p.price
        FROM PRODUCTS p
        WHERE p.average_rating >= 4.0
          AND EXISTS (
              SELECT 1 
              FROM REVIEWS r 
              WHERE r.product_id = p.product_id 
                AND r.rating <= 2.0 
                AND r.helpful_vote >= 5
          )
        FETCH FIRST 5 ROWS ONLY
        """)

    run_query(cursor, "Subquery 3: Correlated Subquery in WHERE (Rating Higher than Category Average)",
        """
        SELECT 
            p.product_id,
            SUBSTR(p.title, 1, 40) AS product_name,
            p.main_category,
            p.average_rating
        FROM PRODUCTS p
        WHERE p.average_rating > (
            SELECT AVG(p_sub.average_rating)
            FROM PRODUCTS p_sub
            WHERE p_sub.main_category = p.main_category
        )
        AND p.main_category = 'Tools & Home Improvement'
        ORDER BY p.average_rating DESC
        FETCH FIRST 5 ROWS ONLY
        """)

    run_query(cursor, "Subquery 4: Subquery with NOT IN (Customers with 100% Verified Reviews)",
        """
        SELECT 
            c.customer_id,
            c.review_count,
            c.avg_rating_given
        FROM CUSTOMERS c
        WHERE c.review_count >= 3
          AND c.customer_id NOT IN (
              SELECT DISTINCT r.customer_id 
              FROM REVIEWS r 
              WHERE r.verified_purchase = 0
                AND r.customer_id IS NOT NULL
          )
        FETCH FIRST 5 ROWS ONLY
        """)

    run_query(cursor, "Subquery 5: Subquery with ALL Operator (Priced Above ALL Fashion Items)",
        """
        SELECT 
            p.product_id,
            SUBSTR(p.title, 1, 35) AS product_name,
            p.main_category,
            p.price
        FROM PRODUCTS p
        WHERE p.price > ALL (
            SELECT p2.price 
            FROM PRODUCTS p2 
            WHERE p2.main_category = 'AMAZON FASHION'
              AND p2.price IS NOT NULL
        )
        AND p.price IS NOT NULL
        ORDER BY p.price ASC
        FETCH FIRST 5 ROWS ONLY
        """)

    run_query(cursor, "Subquery 6: Inline View / Subquery in FROM (Reviewer Sentiment Cohorts)",
        """
        SELECT 
            sentiment_band,
            COUNT(*) AS total_customers,
            ROUND(AVG(review_count), 2) AS avg_reviews_written,
            ROUND(AVG(total_helpful_votes), 2) AS avg_helpful_votes
        FROM (
            SELECT 
                customer_id,
                review_count,
                total_helpful_votes,
                CASE 
                    WHEN avg_rating_given >= 4.5 THEN 'Highly Positive (4.5 - 5.0)'
                    WHEN avg_rating_given >= 3.0 THEN 'Moderate / Neutral (3.0 - 4.4)'
                    ELSE 'Critical / Negative (< 3.0)'
                END AS sentiment_band
            FROM CUSTOMERS
            WHERE review_count >= 2
        )
        GROUP BY sentiment_band
        ORDER BY total_customers DESC
        """)

    run_query(cursor, "Subquery 7: Subquery Factoring (WITH Clause / CTE - Category Rankings)",
        """
        WITH CategoryStats AS (
            SELECT 
                p.main_category,
                COUNT(DISTINCT p.product_id) AS product_count,
                COUNT(r.review_id) AS review_count,
                ROUND(AVG(r.rating), 2) AS avg_rating,
                ROUND(SUM(r.verified_purchase) / NULLIF(COUNT(r.review_id), 0) * 100, 2) AS verified_pct
            FROM PRODUCTS p
            JOIN REVIEWS r ON p.product_id = r.product_id
            WHERE p.main_category IS NOT NULL
            GROUP BY p.main_category
        ),
        RankedCategories AS (
            SELECT 
                main_category,
                product_count,
                review_count,
                avg_rating,
                verified_pct,
                DENSE_RANK() OVER (ORDER BY review_count DESC) AS popularity_rank
            FROM CategoryStats
            WHERE review_count > 50
        )
        SELECT *
        FROM RankedCategories
        WHERE popularity_rank <= 5
        """)

def demo_stored_procedures(cursor, conn):
    print("\n" + "#" * 80)
    print(" SECTION 3: PL/SQL STORED PROCEDURES & FUNCTIONS")
    print("#" * 80)

    # 1. FN_CALCULATE_CUSTOMER_TRUST_SCORE
    cursor.execute("SELECT customer_id FROM CUSTOMERS WHERE review_count >= 3 FETCH FIRST 1 ROWS ONLY")
    cust_id = cursor.fetchone()[0]

    cursor.execute("SELECT FN_CALCULATE_CUSTOMER_TRUST_SCORE(:1) FROM DUAL", [cust_id])
    score = cursor.fetchone()[0]
    print(f"\n[1] FUNCTION: FN_CALCULATE_CUSTOMER_TRUST_SCORE")
    print(f"    Input: Customer ID = {cust_id}")
    print(f"    Output: Trust Score = {score}/100 (Weighted Algorithm)")

    # 2. SP_GET_PRODUCT_INSIGHTS
    cursor.execute("SELECT product_id FROM PRODUCTS WHERE rating_number >= 10 FETCH FIRST 1 ROWS ONLY")
    prod_id = cursor.fetchone()[0]

    print(f"\n[2] STORED PROCEDURE: SP_GET_PRODUCT_INSIGHTS")
    print(f"    Input: Product ID = {prod_id}")
    out_title = cursor.var(oracledb.STRING)
    out_cat = cursor.var(oracledb.STRING)
    out_price = cursor.var(oracledb.NUMBER)
    out_rating = cursor.var(oracledb.NUMBER)
    out_reviews = cursor.var(oracledb.NUMBER)
    out_cur = cursor.var(oracledb.CURSOR)

    cursor.callproc("SP_GET_PRODUCT_INSIGHTS", [
        prod_id, out_title, out_cat, out_price, out_rating, out_reviews, out_cur
    ])
    print(f"    OUT Parameters:")
    print(f"      - Title:       {out_title.getvalue()}")
    print(f"      - Category:    {out_cat.getvalue()}")
    print(f"      - Price:       ${out_price.getvalue()}")
    print(f"      - Avg Rating:  {out_rating.getvalue()} / 5.0")
    print(f"      - Review Count:{out_reviews.getvalue()}")
    
    rev_cur = out_cur.getvalue()
    rev_cols = [c[0] for c in rev_cur.description]
    rev_rows = rev_cur.fetchall()
    print(f"    SYS_REFCURSOR (Top Helpful Reviews Stream):")
    print_table(rev_cols, rev_rows)

    # 3. SP_CUSTOMER_ACTIVITY_REPORT
    print(f"\n[3] STORED PROCEDURE: SP_CUSTOMER_ACTIVITY_REPORT")
    print(f"    Input: Customer ID = {cust_id}")
    out_cnt = cursor.var(oracledb.NUMBER)
    out_avg = cursor.var(oracledb.NUMBER)
    out_trust = cursor.var(oracledb.NUMBER)
    out_tier = cursor.var(oracledb.STRING)
    out_c_cur = cursor.var(oracledb.CURSOR)

    cursor.callproc("SP_CUSTOMER_ACTIVITY_REPORT", [
        cust_id, out_cnt, out_avg, out_trust, out_tier, out_c_cur
    ])
    print(f"    OUT Parameters:")
    print(f"      - Tier:             {out_tier.getvalue()}")
    print(f"      - Reviews Written:  {out_cnt.getvalue()}")
    print(f"      - Avg Rating Given: {out_avg.getvalue()}")
    print(f"      - Trust Score:      {out_trust.getvalue()} / 100")
    
    c_cur = out_c_cur.getvalue()
    c_cols = [c[0] for c in c_cur.description]
    c_rows = c_cur.fetchall()
    print(f"    SYS_REFCURSOR (Customer Reviews History):")
    print_table(c_cols, c_rows)

    # 4. SP_RECALCULATE_PRODUCT_METRICS
    print(f"\n[4] STORED PROCEDURE: SP_RECALCULATE_PRODUCT_METRICS (Transactional Recalculation)")
    print(f"    Input: Product ID = {prod_id}")
    out_upd_cnt = cursor.var(oracledb.NUMBER)
    out_new_avg = cursor.var(oracledb.NUMBER)
    cursor.callproc("SP_RECALCULATE_PRODUCT_METRICS", [prod_id, out_upd_cnt, out_new_avg])
    print(f"    OUT Parameters:")
    print(f"      - Recalculated Reviews:    {out_upd_cnt.getvalue()}")
    print(f"      - Recalculated Avg Rating: {out_new_avg.getvalue()}")
    print("    Transactional UPDATE committed to PRODUCT_FEATURES & PRODUCTS.")

def main():
    print("=" * 80)
    print(" INSYTE — ORACLE 23ai LIVE BACKEND DEMONSTRATION")
    print(" Connecting to Oracle Cloud Autonomous Database...")
    print("=" * 80)
    conn = get_connection()
    cursor = conn.cursor()
    print(" Connection Established successfully.\n")

    demo_views(cursor)
    demo_subqueries(cursor)
    demo_stored_procedures(cursor, conn)

    cursor.close()
    conn.close()
    print("\n" + "=" * 80)
    print(" LIVE BACKEND DEMONSTRATION COMPLETED SUCCESSFULLY!")
    print("=" * 80)

if __name__ == "__main__":
    main()

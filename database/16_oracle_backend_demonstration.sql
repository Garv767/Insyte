-- ==============================================================================
-- INSYTE: 16_oracle_backend_demonstration.sql
-- Oracle 23ai Backend Demonstration: Stored Procedures, Views & Subqueries
-- Authors: Garv & Aditi (CSE Core)
-- Target Environment: Oracle Database 23ai Autonomous Database (FREEPDB1)
-- ==============================================================================

PROMPT ====================================================================
PROMPT   INSYTE — ORACLE 23ai BACKEND DEMONSTRATION SUITE
PROMPT   Stored Procedures, PL/SQL Functions, Analytical Views & Subqueries
PROMPT ====================================================================

-- ##############################################################################
-- SECTION 1: ANALYTICAL & OPERATIONAL VIEWS
-- ##############################################################################

PROMPT [1/3] Creating Analytical Views...

-- ------------------------------------------------------------------------------
-- VIEW 1: V_PRODUCT_PERFORMANCE_METRICS
-- Purpose: Consolidates product catalog with real-time aggregated customer review 
--          metrics, helpful votes, and image penetration rates.
-- Demonstration Value: Joins core dimension (PRODUCTS) with pre-aggregated features (PRODUCT_FEATURES).
-- ------------------------------------------------------------------------------
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
    ROUND(NVL(pf.verified_purchase_rate, 0) * 100, 1) AS verified_purchase_pct,
    ROUND(NVL(pf.image_review_rate, 0) * 100, 1) AS image_review_pct
FROM PRODUCTS p
LEFT JOIN PRODUCT_FEATURES pf ON p.product_id = pf.product_id;

-- ------------------------------------------------------------------------------
-- VIEW 2: V_CUSTOMER_ENGAGEMENT_SUMMARY
-- Purpose: Segments customers into tiers ('Elite Reviewer', 'Active Contributor',
--          'Standard Customer') based on activity span, helpful votes, and volume.
-- Demonstration Value: Demonstrates conditional business logic (CASE expressions) 
--                      and date arithmetic directly in views.
-- ------------------------------------------------------------------------------
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
FROM CUSTOMERS c;

-- ------------------------------------------------------------------------------
-- VIEW 3: V_CATEGORY_BENCHMARK_ANALYSIS
-- Purpose: Provides high-level category benchmarks (mean price, rating, review volume)
--          to identify competitive pricing and high-performing categories.
-- Demonstration Value: Group aggregation with NVL handling and multi-column rollup.
-- ------------------------------------------------------------------------------
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
GROUP BY p.main_category;

-- ------------------------------------------------------------------------------
-- VIEW 4: V_HIGH_IMPACT_CRITICAL_REVIEWS
-- Purpose: Surfaces severe negative feedback (rating <= 2.0) that has high social 
--          validation (>= 3 helpful votes) for immediate seller intervention.
-- Demonstration Value: Filtering, join across transactional tables, and CLOB-to-VARCHAR substring handling.
-- ------------------------------------------------------------------------------
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
  AND r.helpful_vote >= 3;


-- ##############################################################################
-- SECTION 2: PL/SQL STORED PROCEDURES & FUNCTIONS
-- ##############################################################################

PROMPT [2/3] Compiling PL/SQL Functions & Stored Procedures...

-- ------------------------------------------------------------------------------
-- FUNCTION: FN_CALCULATE_CUSTOMER_TRUST_SCORE
-- Purpose: Deterministic algorithmic scoring engine calculating a Trust Index (0-100)
--          based on verified purchases, helpful votes, and review frequency.
-- Parameters:
--   p_customer_id: VARCHAR2 (Customer Identifier)
-- Returns: NUMBER (Trust Score between 0 and 100)
-- ------------------------------------------------------------------------------
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

    -- Formula:
    -- 50% Verified Purchase Rate weight + 30% Helpful Community Votes + 20% Volume Stability
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
/

-- ------------------------------------------------------------------------------
-- PROCEDURE 1: SP_GET_PRODUCT_INSIGHTS
-- Purpose: Returns product metadata through OUT scalars and opens a SYS_REFCURSOR 
--          streaming the top most helpful reviews for frontend rendering.
-- Parameters:
--   p_product_id:     IN VARCHAR2
--   p_product_title:  OUT VARCHAR2
--   p_category:       OUT VARCHAR2
--   p_price:          OUT NUMBER
--   p_avg_rating:     OUT NUMBER
--   p_total_reviews:  OUT NUMBER
--   p_reviews_cursor: OUT SYS_REFCURSOR
-- ------------------------------------------------------------------------------
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

    -- Open dynamic cursor for top validated reviews
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
/

-- ------------------------------------------------------------------------------
-- PROCEDURE 2: SP_CUSTOMER_ACTIVITY_REPORT
-- Purpose: Aggregates a customer's lifetime activity, computes their trust score
--          using FN_CALCULATE_CUSTOMER_TRUST_SCORE, and returns their review history.
-- Parameters:
--   p_customer_id:    IN VARCHAR2
--   p_review_count:   OUT NUMBER
--   p_avg_rating:     OUT NUMBER
--   p_trust_score:    OUT NUMBER
--   p_tier:           OUT VARCHAR2
--   p_reviews_cursor: OUT SYS_REFCURSOR
-- ------------------------------------------------------------------------------
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
/

-- ------------------------------------------------------------------------------
-- PROCEDURE 3: SP_RECALCULATE_PRODUCT_METRICS
-- Purpose: Backend maintenance and ETL routine. Re-computes review aggregates 
--          on demand from base table REVIEWS and updates PRODUCT_FEATURES & PRODUCTS.
-- Parameters:
--   p_product_id:     IN VARCHAR2
--   p_updated_count:  OUT NUMBER
--   p_new_avg_rating: OUT NUMBER
-- ------------------------------------------------------------------------------
CREATE OR REPLACE PROCEDURE SP_RECALCULATE_PRODUCT_METRICS(
    p_product_id     IN VARCHAR2,
    p_updated_count  OUT NUMBER,
    p_new_avg_rating OUT NUMBER
) IS
    v_rev_count   NUMBER := 0;
    v_avg_rating  NUMBER := 0;
    v_helpful     NUMBER := 0;
    v_verified    NUMBER := 0;
    v_with_img    NUMBER := 0;
BEGIN
    -- Real-time aggregation from base reviews
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

    -- Synchronize PRODUCT_FEATURES
    UPDATE PRODUCT_FEATURES
    SET 
        review_count = v_rev_count,
        avg_review_rating = v_avg_rating,
        total_helpful_votes = v_helpful,
        verified_purchase_rate = v_verified,
        image_review_rate = v_with_img
    WHERE product_id = p_product_id;

    -- Synchronize PRODUCTS dimension
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
/


-- ##############################################################################
-- SECTION 3: ADVANCED SUBQUERIES FOR DEMONSTRATION & VIVA
-- ##############################################################################

PROMPT [3/3] Ready for Subquery Execution & Demonstrations!

-- ------------------------------------------------------------------------------
-- SUBQUERY 1: SCALAR SUBQUERY IN SELECT CLAUSE
-- Question it answers: "How does each product's price compare to the category benchmark?"
-- ------------------------------------------------------------------------------
SELECT 
    p.product_id,
    SUBSTR(p.title, 1, 40) AS product_name,
    p.main_category,
    p.price,
    ROUND(
        (SELECT AVG(p2.price) 
         FROM PRODUCTS p2 
         WHERE p2.main_category = p.main_category), 
        2
    ) AS category_avg_price,
    ROUND(
        p.price - (SELECT AVG(p2.price) 
                   FROM PRODUCTS p2 
                   WHERE p2.main_category = p.main_category), 
        2
    ) AS price_variance
FROM PRODUCTS p
WHERE p.price IS NOT NULL AND p.main_category = 'Amazon Home'
FETCH FIRST 5 ROWS ONLY;

-- ------------------------------------------------------------------------------
-- SUBQUERY 2: CORRELATED SUBQUERY WITH 'EXISTS'
-- Question it answers: "Which top-tier products currently have critical issues (1-2 star reviews with >= 5 upvotes)?"
-- ------------------------------------------------------------------------------
SELECT 
    p.product_id,
    SUBSTR(p.title, 1, 50) AS product_name,
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
FETCH FIRST 5 ROWS ONLY;

-- ------------------------------------------------------------------------------
-- SUBQUERY 3: CORRELATED SUBQUERY IN WHERE CLAUSE (Aggregate Comparison)
-- Question it answers: "Find products whose average rating exceeds the overall category average rating."
-- ------------------------------------------------------------------------------
SELECT 
    p.product_id,
    SUBSTR(p.title, 1, 45) AS product_name,
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
FETCH FIRST 5 ROWS ONLY;

-- ------------------------------------------------------------------------------
-- SUBQUERY 4: SUBQUERY WITH 'NOT IN'
-- Question it answers: "Find loyal customers who have NEVER written an unverified review (100% verified authentic)."
-- ------------------------------------------------------------------------------
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
FETCH FIRST 5 ROWS ONLY;

-- ------------------------------------------------------------------------------
-- SUBQUERY 5: SUBQUERY WITH 'ALL' OPERATOR
-- Question it answers: "Find premium products priced higher than ALL products in the 'AMAZON FASHION' catalog."
-- ------------------------------------------------------------------------------
SELECT 
    p.product_id,
    SUBSTR(p.title, 1, 40) AS product_name,
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
FETCH FIRST 5 ROWS ONLY;

-- ------------------------------------------------------------------------------
-- SUBQUERY 6: INLINE VIEW (SUBQUERY IN FROM CLAUSE)
-- Question it answers: "Analyze reviewer rating polarization by grouping reviewers into rating sentiment cohorts."
-- ------------------------------------------------------------------------------
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
ORDER BY total_customers DESC;

-- ------------------------------------------------------------------------------
-- SUBQUERY 7: SUBQUERY FACTORING (WITH CLAUSE / COMMON TABLE EXPRESSIONS - CTE)
-- Question it answers: "Rank categories by verified review penetration and show top categories."
-- ------------------------------------------------------------------------------
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
WHERE popularity_rank <= 5;

PROMPT [INSYTE DEMO] All Scripts successfully loaded!

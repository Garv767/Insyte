-- ==============================================================================
-- INSYTE: 10_vector.sql
-- Oracle 23ai AI Vector Search & Semantic Similarity Queries
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE VECTOR] Configuring Oracle 23ai AI Vector Search Queries...

-- 1. Semantic Product Recommendation Template
-- Calculates exact or approximate cosine distance between catalog products and user search vectors
-- Parameter :query_vector is passed as a 384-element float array from Python/Flask
/*
SELECT 
    p.stock_code,
    p.normalized_description AS description,
    p.unit_price,
    ROUND(VECTOR_DISTANCE(p.embedding, :query_vector, COSINE), 4) AS cosine_distance,
    ROUND(1 - VECTOR_DISTANCE(p.embedding, :query_vector, COSINE), 4) AS similarity_score,
    NVL(agg.units_sold, 0) AS total_units_sold,
    NVL(agg.total_revenue, 0) AS total_revenue,
    NVL(rev.avg_rating, 0) AS avg_rating,
    NVL(rev.review_count, 0) AS review_count
FROM PRODUCTS p
LEFT JOIN (
    SELECT stock_code, SUM(quantity) AS units_sold, SUM(quantity * unit_price) AS total_revenue
    FROM ORDER_ITEMS
    GROUP BY stock_code
) agg ON p.stock_code = agg.stock_code
LEFT JOIN (
    SELECT stock_code, ROUND(AVG(rating), 1) AS avg_rating, COUNT(*) AS review_count
    FROM REVIEWS
    GROUP BY stock_code
) rev ON p.stock_code = rev.stock_code
WHERE p.embedding IS NOT NULL
ORDER BY cosine_distance ASC
FETCH FIRST 5 ROWS ONLY;
*/

-- 2. Behavioral Similarity View (RFM Vector Space)
-- Demonstrates distinction between semantic text embeddings and behavioral RFM vectors
CREATE OR REPLACE VIEW V_CUSTOMER_BEHAVIORAL_VECTOR AS
SELECT 
    c.customer_id,
    c.country,
    s.r_score,
    s.f_score,
    s.m_score,
    -- Construct a 3-dimensional normalized behavioral vector string
    '[' || ROUND(s.r_score / 5.0, 4) || ',' || 
           ROUND(s.f_score / 5.0, 4) || ',' || 
           ROUND(s.m_score / 5.0, 4) || ']' AS behavioral_vector_str
FROM CUSTOMERS c
JOIN MV_CUSTOMER_RFM_SUMMARY s ON c.customer_id = s.customer_id;

PROMPT [INSYTE VECTOR] Vector search queries and behavioral view configured.

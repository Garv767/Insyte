-- ==============================================================================
-- INSYTE: 12_review_analytics.sql
-- Review, Sentiment, Media & Commercial Product Health Analytics
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE REVIEWS] Deploying Review, Media and Product Health Analytics...

-- 1. Rating Distribution Summary View
CREATE OR REPLACE VIEW V_RATING_DISTRIBUTION AS
SELECT 
    ROUND(rating) AS star_rating,
    COUNT(*) AS review_count,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage_share
FROM REVIEWS
WHERE rating IS NOT NULL
GROUP BY ROUND(rating)
ORDER BY star_rating DESC;

-- 2. Sentiment Breakdown View (Transparent Rule-Based / Ingested)
CREATE OR REPLACE VIEW V_SENTIMENT_SUMMARY AS
SELECT 
    sentiment_label,
    COUNT(*) AS total_reviews,
    ROUND(COUNT(*) * 100.0 / SUM(COUNT(*)) OVER (), 2) AS percentage_share,
    ROUND(AVG(rating), 2) AS avg_rating
FROM REVIEWS
GROUP BY sentiment_label;

-- 3. Media vs Non-Media Impact Analysis
-- Directly compares rating and attachment metrics
CREATE OR REPLACE VIEW V_MEDIA_ENGAGEMENT_METRICS AS
SELECT 
    CASE WHEN has_media = 1 THEN 'Reviews with Media' ELSE 'Text-Only Reviews' END AS media_segment,
    COUNT(*) AS total_reviews,
    ROUND(AVG(rating), 2) AS avg_rating,
    COUNT(CASE WHEN sentiment_label = 'POSITIVE' THEN 1 END) AS positive_count,
    COUNT(CASE WHEN sentiment_label = 'NEGATIVE' THEN 1 END) AS negative_count,
    ROUND(
        COUNT(CASE WHEN sentiment_label = 'POSITIVE' THEN 1 END) * 100.0 / COUNT(*),
        2
    ) AS positive_pct
FROM REVIEWS
GROUP BY has_media;

-- 4. Review ↔ Transaction Behavioral Integration: Top Revenue vs Poor Ratings
-- Flags commercial disconnects (high sales volume but low customer satisfaction)
CREATE OR REPLACE VIEW V_REVENUE_VS_SATISFACTION AS
SELECT 
    p.stock_code,
    p.normalized_description AS description,
    agg.total_revenue,
    agg.units_sold,
    rev.avg_rating,
    rev.review_count,
    rev.negative_review_count,
    ROUND(rev.negative_review_count * 100.0 / NULLIF(rev.review_count, 0), 1) AS negative_sentiment_pct
FROM PRODUCTS p
JOIN (
    SELECT 
        stock_code, 
        SUM(quantity * unit_price) AS total_revenue, 
        SUM(quantity) AS units_sold
    FROM ORDER_ITEMS
    WHERE quantity > 0
    GROUP BY stock_code
) agg ON p.stock_code = agg.stock_code
JOIN (
    SELECT 
        stock_code, 
        ROUND(AVG(rating), 2) AS avg_rating, 
        COUNT(*) AS review_count,
        COUNT(CASE WHEN sentiment_label = 'NEGATIVE' OR rating <= 2 THEN 1 END) AS negative_review_count
    FROM REVIEWS
    GROUP BY stock_code
) rev ON p.stock_code = rev.stock_code
WHERE agg.total_revenue > 1000
ORDER BY rev.avg_rating ASC;

-- 5. Commercial Product Health Matrix (Unit 6 / Section 27)
-- Categorizes products into HEALTHY, WATCH, or AT_RISK based on documented business rules
CREATE OR REPLACE VIEW V_PRODUCT_HEALTH_MATRIX AS
WITH product_perf AS (
    SELECT 
        p.stock_code,
        p.normalized_description AS description,
        p.unit_price,
        NVL(sales.revenue, 0) AS revenue,
        NVL(sales.units, 0) AS units_sold,
        NVL(sales.order_count, 0) AS order_count,
        NVL(adj.returns_count, 0) AS returns_count,
        ROUND(NVL(adj.returns_count, 0) * 100.0 / NULLIF(sales.units, 0), 2) AS return_rate_pct,
        NVL(rev.avg_rating, 0) AS avg_rating,
        NVL(rev.review_count, 0) AS review_count,
        NVL(rev.neg_count, 0) AS negative_reviews,
        ROUND(NVL(rev.neg_count, 0) * 100.0 / NULLIF(rev.review_count, 0), 2) AS negative_pct,
        NVL(rev.media_rate, 0) AS media_attachment_rate
    FROM PRODUCTS p
    LEFT JOIN (
        SELECT stock_code, SUM(quantity * unit_price) AS revenue, SUM(quantity) AS units, COUNT(DISTINCT invoice_no) AS order_count
        FROM ORDER_ITEMS WHERE quantity > 0 GROUP BY stock_code
    ) sales ON p.stock_code = sales.stock_code
    LEFT JOIN (
        SELECT stock_code, SUM(ABS(quantity)) AS returns_count
        FROM TRANSACTION_ADJUSTMENTS GROUP BY stock_code
    ) adj ON p.stock_code = adj.stock_code
    LEFT JOIN (
        SELECT 
            stock_code, 
            ROUND(AVG(rating), 2) AS avg_rating, 
            COUNT(*) AS review_count,
            COUNT(CASE WHEN sentiment_label = 'NEGATIVE' OR rating <= 2 THEN 1 END) AS neg_count,
            ROUND(COUNT(CASE WHEN has_media = 1 THEN 1 END) * 100.0 / COUNT(*), 1) AS media_rate
        FROM REVIEWS GROUP BY stock_code
    ) rev ON p.stock_code = rev.stock_code
)
SELECT 
    stock_code,
    description,
    unit_price,
    revenue,
    units_sold,
    order_count,
    return_rate_pct,
    avg_rating,
    review_count,
    negative_pct,
    media_attachment_rate,
    CASE 
        -- AT_RISK: High returns (>8%) or poor ratings (<3.0 with reviews) or high negative sentiment (>30%)
        WHEN (return_rate_pct >= 8.0) OR (review_count >= 5 AND avg_rating < 3.0) OR (negative_pct >= 30.0) THEN 'AT_RISK'
        -- WATCH: Moderate returns (4-8%) or moderate rating (3.0-3.8) or low order frequency
        WHEN (return_rate_pct >= 4.0 AND return_rate_pct < 8.0) OR (review_count >= 3 AND avg_rating < 3.8) THEN 'WATCH'
        -- HEALTHY: Strong sales, low returns, satisfied reviews
        ELSE 'HEALTHY'
    END AS health_status
FROM product_perf
WHERE revenue > 0;

PROMPT [INSYTE REVIEWS] Review and Product Health analytics views deployed.

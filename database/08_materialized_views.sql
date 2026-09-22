-- ==============================================================================
-- INSYTE: 08_materialized_views.sql
-- Oracle 23ai Materialized Views for Performance Optimization
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE MVIEWS] Creating Materialized Views...

-- 1. Materialized View: Monthly Revenue Trends
-- Pre-computes month-by-month financial metrics to avoid repeated full table scans
BEGIN
    EXECUTE IMMEDIATE 'DROP MATERIALIZED VIEW MV_MONTHLY_REVENUE_TRENDS';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -12003 THEN RAISE; END IF;
END;
/
CREATE MATERIALIZED VIEW MV_MONTHLY_REVENUE_TRENDS
BUILD IMMEDIATE
REFRESH COMPLETE ON DEMAND
AS
SELECT 
    TO_CHAR(o.invoice_date, 'YYYY-MM') AS month_key,
    COUNT(DISTINCT o.invoice_no) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS total_customers,
    SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS units_sold,
    SUM(CASE WHEN oi.quantity > 0 THEN (oi.quantity * oi.unit_price) ELSE 0 END) AS gross_sales,
    SUM(CASE WHEN oi.quantity < 0 THEN ABS(oi.quantity * oi.unit_price) ELSE 0 END) AS returns_amount,
    SUM(oi.quantity * oi.unit_price) AS net_revenue,
    ROUND(
        SUM(oi.quantity * oi.unit_price) / NULLIF(COUNT(DISTINCT o.invoice_no), 0),
        2
    ) AS avg_order_value
FROM ORDERS o
JOIN ORDER_ITEMS oi ON o.invoice_no = oi.invoice_no
GROUP BY TO_CHAR(o.invoice_date, 'YYYY-MM');

COMMENT ON MATERIALIZED VIEW MV_MONTHLY_REVENUE_TRENDS IS 'Precomputed monthly e-commerce financial trends';

-- 2. Materialized View: Customer RFM Behavioral Segmentation
-- Materializes NTILE(5) ranking computations across customers
BEGIN
    EXECUTE IMMEDIATE 'DROP MATERIALIZED VIEW MV_CUSTOMER_RFM_SUMMARY';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -12003 THEN RAISE; END IF;
END;
/
CREATE MATERIALIZED VIEW MV_CUSTOMER_RFM_SUMMARY
BUILD IMMEDIATE
REFRESH COMPLETE ON DEMAND
AS
WITH customer_aggregations AS (
    SELECT 
        c.customer_id,
        c.country,
        ROUND(CAST(SYSTIMESTAMP AS DATE) - CAST(MAX(o.invoice_date) AS DATE)) AS recency_days,
        COUNT(DISTINCT o.invoice_no) AS frequency_orders,
        SUM(oi.quantity * oi.unit_price) AS monetary_spend,
        SUM(oi.quantity) AS total_units
    FROM CUSTOMERS c
    JOIN ORDERS o ON c.customer_id = o.customer_id
    JOIN ORDER_ITEMS oi ON o.invoice_no = oi.invoice_no
    WHERE o.is_cancellation = 0
    GROUP BY c.customer_id, c.country
),
customer_scores AS (
    SELECT 
        customer_id,
        country,
        recency_days,
        frequency_orders,
        monetary_spend,
        total_units,
        NTILE(5) OVER (ORDER BY recency_days DESC) AS r_score,
        NTILE(5) OVER (ORDER BY frequency_orders ASC) AS f_score,
        NTILE(5) OVER (ORDER BY monetary_spend ASC) AS m_score
    FROM customer_aggregations
)
SELECT 
    customer_id,
    country,
    recency_days,
    frequency_orders,
    monetary_spend,
    total_units,
    r_score,
    f_score,
    m_score,
    (r_score * 100 + f_score * 10 + m_score) AS rfm_combined,
    CASE 
        WHEN r_score >= 4 AND f_score >= 4 AND m_score >= 4 THEN 'Champions'
        WHEN r_score >= 3 AND f_score >= 3 THEN 'Loyal Customers'
        WHEN r_score >= 4 AND f_score <= 2 THEN 'Recent Customers'
        WHEN r_score <= 2 AND f_score >= 3 THEN 'At Risk'
        WHEN r_score <= 2 AND f_score <= 2 THEN 'Lost'
        ELSE 'Potential Loyalists'
    END AS rfm_segment
FROM customer_scores;

COMMENT ON MATERIALIZED VIEW MV_CUSTOMER_RFM_SUMMARY IS 'Precalculated RFM quintile segments and scores per customer';

-- 3. Procedure to Refresh All Materialized Views
CREATE OR REPLACE PROCEDURE sp_refresh_insyte_mviews IS
BEGIN
    DBMS_MVIEW.REFRESH('MV_MONTHLY_REVENUE_TRENDS', 'C');
    DBMS_MVIEW.REFRESH('MV_CUSTOMER_RFM_SUMMARY', 'C');
    DBMS_OUTPUT.PUT_LINE('[MVIEWS] Materialized views refreshed successfully.');
END;
/

PROMPT [INSYTE MVIEWS] Materialized views and refresh procedure created.

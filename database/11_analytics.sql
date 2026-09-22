-- ==============================================================================
-- INSYTE: 11_analytics.sql
-- Core In-Database Behavioral Analytics & RFM Segmentation Engine
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE ANALYTICS] Deploying Core In-Database Behavioral Queries...

-- 1. RFM Segment Aggregation Summary View
-- Computes customer count, total revenue, average spend, and contribution % per segment
CREATE OR REPLACE VIEW V_RFM_SEGMENT_PERFORMANCE AS
WITH total_portfolio AS (
    SELECT 
        COUNT(*) AS grand_total_customers,
        SUM(monetary_spend) AS grand_total_revenue
    FROM MV_CUSTOMER_RFM_SUMMARY
)
SELECT 
    s.rfm_segment,
    COUNT(s.customer_id) AS customer_count,
    ROUND(COUNT(s.customer_id) * 100.0 / tp.grand_total_customers, 2) AS customer_pct,
    ROUND(SUM(s.monetary_spend), 2) AS total_revenue,
    ROUND(SUM(s.monetary_spend) * 100.0 / NULLIF(tp.grand_total_revenue, 0), 2) AS revenue_pct,
    ROUND(AVG(s.recency_days), 1) AS avg_recency_days,
    ROUND(AVG(s.frequency_orders), 1) AS avg_order_frequency,
    ROUND(AVG(s.monetary_spend), 2) AS avg_spend_per_customer
FROM MV_CUSTOMER_RFM_SUMMARY s
CROSS JOIN total_portfolio tp
GROUP BY s.rfm_segment, tp.grand_total_customers, tp.grand_total_revenue
ORDER BY total_revenue DESC;

-- 2. Customer Spending Histogram (Using Oracle WIDTH_BUCKET Function)
CREATE OR REPLACE VIEW V_SPENDING_HISTOGRAM AS
SELECT 
    bucket_num,
    CASE 
        WHEN bucket_num = 1 THEN '£0 - £500'
        WHEN bucket_num = 2 THEN '£501 - £1,000'
        WHEN bucket_num = 3 THEN '£1,001 - £2,500'
        WHEN bucket_num = 4 THEN '£2,501 - £5,000'
        WHEN bucket_num = 5 THEN '£5,001 - £10,000'
        ELSE 'Over £10,000'
    END AS spend_bracket,
    COUNT(*) AS customer_count,
    ROUND(SUM(monetary_spend), 2) AS bracket_revenue
FROM (
    SELECT 
        customer_id,
        monetary_spend,
        CASE 
            WHEN monetary_spend <= 500 THEN 1
            WHEN monetary_spend <= 1000 THEN 2
            WHEN monetary_spend <= 2500 THEN 3
            WHEN monetary_spend <= 5000 THEN 4
            WHEN monetary_spend <= 10000 THEN 5
            ELSE 6
        END AS bucket_num
    FROM MV_CUSTOMER_RFM_SUMMARY
)
GROUP BY bucket_num
ORDER BY bucket_num;

-- 3. Top Products by Revenue & Units with Window Rank
CREATE OR REPLACE VIEW V_TOP_PRODUCTS_RANKED AS
SELECT 
    p.stock_code,
    p.normalized_description AS description,
    p.unit_price,
    agg.total_revenue,
    agg.total_units,
    agg.distinct_orders,
    DENSE_RANK() OVER (ORDER BY agg.total_revenue DESC) AS revenue_rank,
    DENSE_RANK() OVER (ORDER BY agg.total_units DESC) AS volume_rank
FROM PRODUCTS p
JOIN (
    SELECT 
        stock_code,
        SUM(quantity * unit_price) AS total_revenue,
        SUM(quantity) AS total_units,
        COUNT(DISTINCT invoice_no) AS distinct_orders
    FROM ORDER_ITEMS
    WHERE quantity > 0
    GROUP BY stock_code
) agg ON p.stock_code = agg.stock_code;

PROMPT [INSYTE ANALYTICS] Core analytical views successfully deployed.

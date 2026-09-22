-- ==============================================================================
-- INSYTE: 07_views.sql
-- Oracle 23ai Core Analytical Views
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE VIEWS] Constructing Analytical Reporting Views...

-- 1. Order Financials View
-- Calculates point-in-time gross sales, returns, and net order values
CREATE OR REPLACE VIEW V_ORDER_FINANCIALS AS
SELECT 
    o.invoice_no,
    o.customer_id,
    NVL(o.customer_id, 'GUEST') AS customer_display,
    o.invoice_date,
    TO_CHAR(o.invoice_date, 'YYYY-MM-DD') AS invoice_date_str,
    TO_CHAR(o.invoice_date, 'YYYY-MM') AS invoice_month,
    o.country,
    o.is_cancellation,
    o.is_guest,
    COUNT(oi.item_id) AS line_items_count,
    SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS valid_units,
    SUM(CASE WHEN oi.quantity < 0 THEN ABS(oi.quantity) ELSE 0 END) AS returned_units,
    SUM(CASE WHEN oi.quantity > 0 THEN (oi.quantity * oi.unit_price) ELSE 0 END) AS gross_sales,
    SUM(CASE WHEN oi.quantity < 0 THEN ABS(oi.quantity * oi.unit_price) ELSE 0 END) AS return_amount,
    SUM(oi.quantity * oi.unit_price) AS net_revenue
FROM ORDERS o
LEFT JOIN ORDER_ITEMS oi ON o.invoice_no = oi.invoice_no
GROUP BY 
    o.invoice_no,
    o.customer_id,
    o.invoice_date,
    o.country,
    o.is_cancellation,
    o.is_guest;

-- 2. Customer Lifetime Analytical View
CREATE OR REPLACE VIEW V_CUSTOMER_LIFETIME AS
SELECT 
    c.customer_id,
    c.country,
    c.is_guest,
    MIN(o.invoice_date) AS first_purchase_date,
    MAX(o.invoice_date) AS last_purchase_date,
    ROUND(CAST(SYSTIMESTAMP AS DATE) - CAST(MAX(o.invoice_date) AS DATE)) AS recency_days,
    COUNT(DISTINCT o.invoice_no) AS total_orders,
    SUM(oi.quantity) AS total_units_purchased,
    SUM(oi.quantity * oi.unit_price) AS total_lifetime_spend,
    ROUND(
        SUM(oi.quantity * oi.unit_price) / NULLIF(COUNT(DISTINCT o.invoice_no), 0),
        2
    ) AS avg_order_value
FROM CUSTOMERS c
JOIN ORDERS o ON c.customer_id = o.customer_id
JOIN ORDER_ITEMS oi ON o.invoice_no = oi.invoice_no
WHERE o.is_cancellation = 0
GROUP BY c.customer_id, c.country, c.is_guest;

-- 3. Product Sales Performance View
CREATE OR REPLACE VIEW V_PRODUCT_SALES_SUMMARY AS
SELECT 
    p.stock_code,
    p.normalized_description AS description,
    p.unit_price AS catalog_price,
    COUNT(DISTINCT oi.invoice_no) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS unique_customers,
    SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS units_sold,
    SUM(CASE WHEN oi.quantity > 0 THEN (oi.quantity * oi.unit_price) ELSE 0 END) AS total_revenue,
    ROUND(AVG(oi.unit_price), 2) AS avg_selling_price
FROM PRODUCTS p
JOIN ORDER_ITEMS oi ON p.stock_code = oi.stock_code
JOIN ORDERS o ON oi.invoice_no = o.invoice_no
WHERE o.is_cancellation = 0
GROUP BY p.stock_code, p.normalized_description, p.unit_price;

-- 4. Monthly Business Trends View
CREATE OR REPLACE VIEW V_MONTHLY_REVENUE AS
SELECT 
    TO_CHAR(o.invoice_date, 'YYYY-MM') AS month_key,
    COUNT(DISTINCT o.invoice_no) AS total_orders,
    COUNT(DISTINCT o.customer_id) AS distinct_customers,
    SUM(CASE WHEN oi.quantity > 0 THEN oi.quantity ELSE 0 END) AS units_sold,
    SUM(CASE WHEN oi.quantity > 0 THEN (oi.quantity * oi.unit_price) ELSE 0 END) AS gross_sales,
    SUM(CASE WHEN oi.quantity < 0 THEN ABS(oi.quantity * oi.unit_price) ELSE 0 END) AS return_amount,
    SUM(oi.quantity * oi.unit_price) AS net_revenue,
    ROUND(
        SUM(oi.quantity * oi.unit_price) / NULLIF(COUNT(DISTINCT o.invoice_no), 0),
        2
    ) AS aov
FROM ORDERS o
JOIN ORDER_ITEMS oi ON o.invoice_no = oi.invoice_no
GROUP BY TO_CHAR(o.invoice_date, 'YYYY-MM')
ORDER BY month_key;

PROMPT [INSYTE VIEWS] Analytical views successfully deployed.

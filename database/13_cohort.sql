-- ==============================================================================
-- INSYTE: 13_cohort.sql
-- In-Database Customer Cohort Modeling & Retention Matrix
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE COHORT] Compiling Cohort Retention Analysis Engine...

-- 1. Customer Monthly Cohort Assignment View
-- Groups each customer by their first recorded purchase month using MIN() OVER
CREATE OR REPLACE VIEW V_CUSTOMER_FIRST_COHORT AS
SELECT 
    o.customer_id,
    MIN(TRUNC(CAST(o.invoice_date AS DATE), 'MONTH')) AS first_cohort_month
FROM ORDERS o
WHERE o.is_cancellation = 0 
  AND o.customer_id IS NOT NULL
GROUP BY o.customer_id;

-- 2. Cohort Activity Lifecycle View
-- Calculates the relative activity offset using Oracle MONTHS_BETWEEN function
CREATE OR REPLACE VIEW V_COHORT_ACTIVITY_LIFECYCLE AS
SELECT 
    o.customer_id,
    c.first_cohort_month,
    TRUNC(CAST(o.invoice_date AS DATE), 'MONTH') AS activity_month,
    ROUND(MONTHS_BETWEEN(TRUNC(CAST(o.invoice_date AS DATE), 'MONTH'), c.first_cohort_month)) AS period_offset,
    COUNT(DISTINCT o.invoice_no) AS monthly_orders,
    SUM(oi.quantity * oi.unit_price) AS monthly_spend
FROM ORDERS o
JOIN V_CUSTOMER_FIRST_COHORT c ON o.customer_id = c.customer_id
JOIN ORDER_ITEMS oi ON o.invoice_no = oi.invoice_no
WHERE o.is_cancellation = 0
GROUP BY 
    o.customer_id, 
    c.first_cohort_month, 
    TRUNC(CAST(o.invoice_date AS DATE), 'MONTH');

-- 3. Comprehensive Cohort Retention Matrix View
-- Generates a canonical triangular retention matrix from Month 0 to Month 6
CREATE OR REPLACE VIEW V_COHORT_RETENTION_MATRIX AS
WITH cohort_aggregates AS (
    SELECT 
        first_cohort_month,
        COUNT(DISTINCT customer_id) AS cohort_size,
        COUNT(DISTINCT CASE WHEN period_offset = 0 THEN customer_id END) AS m0_active,
        COUNT(DISTINCT CASE WHEN period_offset = 1 THEN customer_id END) AS m1_active,
        COUNT(DISTINCT CASE WHEN period_offset = 2 THEN customer_id END) AS m2_active,
        COUNT(DISTINCT CASE WHEN period_offset = 3 THEN customer_id END) AS m3_active,
        COUNT(DISTINCT CASE WHEN period_offset = 4 THEN customer_id END) AS m4_active,
        COUNT(DISTINCT CASE WHEN period_offset = 5 THEN customer_id END) AS m5_active,
        COUNT(DISTINCT CASE WHEN period_offset = 6 THEN customer_id END) AS m6_active
    FROM V_COHORT_ACTIVITY_LIFECYCLE
    GROUP BY first_cohort_month
)
SELECT 
    TO_CHAR(first_cohort_month, 'YYYY-MM') AS cohort_month,
    cohort_size,
    m0_active,
    m1_active,
    ROUND(m1_active * 100.0 / NULLIF(cohort_size, 0), 1) AS m1_retention_pct,
    m2_active,
    ROUND(m2_active * 100.0 / NULLIF(cohort_size, 0), 1) AS m2_retention_pct,
    m3_active,
    ROUND(m3_active * 100.0 / NULLIF(cohort_size, 0), 1) AS m3_retention_pct,
    m4_active,
    ROUND(m4_active * 100.0 / NULLIF(cohort_size, 0), 1) AS m4_retention_pct,
    m5_active,
    ROUND(m5_active * 100.0 / NULLIF(cohort_size, 0), 1) AS m5_retention_pct,
    m6_active,
    ROUND(m6_active * 100.0 / NULLIF(cohort_size, 0), 1) AS m6_retention_pct
FROM cohort_aggregates
ORDER BY first_cohort_month;

-- 4. New vs Returning Customer Volume Trends
CREATE OR REPLACE VIEW V_NEW_VS_RETURNING_CUSTOMERS AS
SELECT 
    TO_CHAR(activity_month, 'YYYY-MM') AS activity_month_key,
    COUNT(DISTINCT CASE WHEN period_offset = 0 THEN customer_id END) AS new_customers,
    COUNT(DISTINCT CASE WHEN period_offset > 0 THEN customer_id END) AS returning_customers,
    COUNT(DISTINCT customer_id) AS total_active_customers,
    ROUND(
        COUNT(DISTINCT CASE WHEN period_offset > 0 THEN customer_id END) * 100.0 / 
        NULLIF(COUNT(DISTINCT customer_id), 0),
        1
    ) AS repeat_customer_rate
FROM V_COHORT_ACTIVITY_LIFECYCLE
GROUP BY TO_CHAR(activity_month, 'YYYY-MM')
ORDER BY activity_month_key;

PROMPT [INSYTE COHORT] Cohort retention views compiled successfully.

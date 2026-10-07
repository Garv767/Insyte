# INSYTE — Oracle Cloud Console SQL Demonstration Queries
**Target Environment:** Oracle Cloud Autonomous Database 23ai (`Database Actions` / `SQL Worksheet`)  
**Purpose:** Ready-to-copy SQL queries & PL/SQL blocks for backend viva demonstration.

---

## 💡 Quick Tips for Oracle Cloud Web UI (Database Actions)
- **For `SELECT` queries (Sections 1 & 2):** Select/highlight the query and click the **Run Statement (▶)** button or press `Ctrl + Enter`.
- **For PL/SQL blocks (Section 3):** Click the **Run Script (📄▶)** button or press `F5` so that the `DBMS_OUTPUT` panel captures and displays the printed output.
a
---

## 📊 SECTION 1: Analytical & Operational Views

### 1. Product Performance Metrics View
*Combines product catalog data with aggregated review counts, ratings, and verified review rates.*
```sql
SELECT 
    product_id, 
    product_name, 
    main_category, 
    price, 
    average_rating, 
    total_reviews, 
    verified_purchase_pct 
FROM V_PRODUCT_PERFORMANCE_METRICS 
WHERE total_reviews >= 20 
FETCH FIRST 5 ROWS ONLY;
```

---

### 2. Customer Engagement & Tier Segmentation View
*Dynamically segments customers into tiers (`Elite Reviewer`, `Active Contributor`, `Standard Customer`) using CASE expressions and date arithmetic.*
```sql
SELECT 
    customer_id, 
    review_count, 
    avg_rating, 
    total_helpful_votes, 
    activity_span_days, 
    reviewer_tier 
FROM V_CUSTOMER_ENGAGEMENT_SUMMARY 
WHERE review_count >= 3 
FETCH FIRST 5 ROWS ONLY;
```

---

### 3. Category Benchmark Analysis View
*Aggregates market averages (mean price, rating, review volume) grouped by category.*
```sql
SELECT 
    main_category, 
    total_products, 
    avg_category_price, 
    avg_category_rating, 
    total_category_reviews 
FROM V_CATEGORY_BENCHMARK_ANALYSIS 
ORDER BY total_category_reviews DESC 
FETCH FIRST 5 ROWS ONLY;
```

---

### 4. High-Impact Critical Negative Reviews View
*Filters severe negative feedback (`rating <= 2.0` with `helpful_vote >= 3`) for seller quality interventions.*
```sql
SELECT 
    review_id, 
    product_id, 
    rating, 
    helpful_vote, 
    review_headline, 
    review_snippet 
FROM V_HIGH_IMPACT_CRITICAL_REVIEWS 
FETCH FIRST 5 ROWS ONLY;
```

---

## 🔍 SECTION 2: Advanced Subqueries

### 1. Scalar Subquery in SELECT (Price Variance vs Category Benchmark)
*Calculates how much each product's price deviates from its specific category benchmark average.*
```sql
SELECT 
    p.product_id,
    SUBSTR(p.title, 1, 35) AS product_name,
    p.price,
    ROUND((SELECT AVG(p2.price) FROM PRODUCTS p2 WHERE p2.main_category = p.main_category), 2) AS category_avg_price,
    ROUND(p.price - (SELECT AVG(p2.price) FROM PRODUCTS p2 WHERE p2.main_category = p.main_category), 2) AS price_variance
FROM PRODUCTS p
WHERE p.price IS NOT NULL AND p.main_category = 'Amazon Home'
FETCH FIRST 5 ROWS ONLY;
```

---

### 2. Correlated Subquery with `EXISTS` (High-Rated Products with Critical Complaints)
*Finds products with 4+ star ratings that nevertheless have verified complaints with 5+ helpful votes.*
```sql
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
FETCH FIRST 5 ROWS ONLY;
```

---

### 3. Correlated Subquery in `WHERE` (Rating Higher than its Category Average)
*Finds standout products whose average rating exceeds the overall average of all products in their category.*
```sql
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
FETCH FIRST 5 ROWS ONLY;
```

---

### 4. Subquery with `NOT IN` (100% Verified Authentic Reviewers)
*Identifies customers who have never written an unverified review.*
```sql
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
```

---

### 5. Subquery with `ALL` Operator (Priced Above ALL Items in Fashion Catalog)
*Demonstrates set comparison operator `> ALL` against a subquery result set.*
```sql
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
FETCH FIRST 5 ROWS ONLY;
```

---

### 6. Inline View / Subquery in `FROM` (Customer Rating Polarization Breakdown)
*Pre-computes sentiment bands inside an inline view before applying outer group aggregation.*
```sql
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
```

---

### 7. Subquery Factoring (`WITH` Clause / CTE — Category Popularity Rankings)
*Multi-stage Common Table Expression using window function `DENSE_RANK()` to rank categories.*
```sql
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
```

---

## ⚙️ SECTION 3: PL/SQL Stored Procedures & Functions

### 1. Function Execution: `FN_CALCULATE_CUSTOMER_TRUST_SCORE`
*Calls the weighted trust scoring engine (0 to 100) directly inside a SQL query.*
```sql
SELECT 
    customer_id, 
    review_count, 
    verified_purchase_rate, 
    FN_CALCULATE_CUSTOMER_TRUST_SCORE(customer_id) AS trust_score
FROM CUSTOMERS 
WHERE review_count >= 3 
FETCH FIRST 5 ROWS ONLY;
```

---

### 2. Stored Procedure Execution: `SP_GET_PRODUCT_INSIGHTS`
*Retrieves scalar product metrics and streams top helpful reviews using a dynamic `SYS_REFCURSOR`.*
*(Run as Script / F5)*
```sql
SET SERVEROUTPUT ON;
DECLARE
    v_title       VARCHAR2(200);
    v_category    VARCHAR2(100);
    v_price       NUMBER;
    v_rating      NUMBER;
    v_reviews     NUMBER;
    v_cursor      SYS_REFCURSOR;
    -- Cursor variables
    v_rev_id      VARCHAR2(100);
    v_cust_id     VARCHAR2(100);
    v_rev_rating  NUMBER;
    v_helpful     NUMBER;
    v_verified    NUMBER;
    v_date        DATE;
    v_rev_title   VARCHAR2(200);
BEGIN
    SP_GET_PRODUCT_INSIGHTS(
        p_product_id     => 'B0BNWZMDVL',
        p_product_title  => v_title,
        p_category       => v_category,
        p_price          => v_price,
        p_avg_rating     => v_rating,
        p_total_reviews  => v_reviews,
        p_reviews_cursor => v_cursor
    );

    DBMS_OUTPUT.PUT_LINE('--- PRODUCT DETAILS ---');
    DBMS_OUTPUT.PUT_LINE('Title:       ' || v_title);
    DBMS_OUTPUT.PUT_LINE('Category:    ' || v_category);
    DBMS_OUTPUT.PUT_LINE('Price:       $' || v_price);
    DBMS_OUTPUT.PUT_LINE('Avg Rating:  ' || v_rating || ' / 5.0');
    DBMS_OUTPUT.PUT_LINE('Reviews:     ' || v_reviews);
    DBMS_OUTPUT.PUT_LINE('--- TOP HELPFUL REVIEWS (REFCURSOR) ---');

    LOOP
        FETCH v_cursor INTO v_rev_id, v_cust_id, v_rev_rating, v_helpful, v_verified, v_date, v_rev_title;
        EXIT WHEN v_cursor%NOTFOUND;
        DBMS_OUTPUT.PUT_LINE('[' || v_rev_id || '] ' || v_rev_rating || '★ | Helpful: ' || v_helpful || ' | ' || v_rev_title);
    END LOOP;
    CLOSE v_cursor;
END;
/
```

---

### 3. Stored Procedure Execution: `SP_CUSTOMER_ACTIVITY_REPORT`
*Computes trust index, activity tier, and review history via `SYS_REFCURSOR`.*
*(Run as Script / F5)*
```sql
SET SERVEROUTPUT ON;
DECLARE
    v_review_count  NUMBER;
    v_avg_rating    NUMBER;
    v_trust_score   NUMBER;
    v_tier          VARCHAR2(50);
    v_cursor        SYS_REFCURSOR;
    -- Cursor variables
    v_rev_id        VARCHAR2(100);
    v_prod_id       VARCHAR2(100);
    v_prod_name     VARCHAR2(100);
    v_rating        NUMBER;
    v_helpful       NUMBER;
    v_date          DATE;
BEGIN
    SP_CUSTOMER_ACTIVITY_REPORT(
        p_customer_id    => 'AHHGHAHP5PYIS27EWUBEFRD7B7NA',
        p_review_count   => v_review_count,
        p_avg_rating     => v_avg_rating,
        p_trust_score    => v_trust_score,
        p_tier           => v_tier,
        p_reviews_cursor => v_cursor
    );

    DBMS_OUTPUT.PUT_LINE('--- CUSTOMER PROFILE ---');
    DBMS_OUTPUT.PUT_LINE('Tier:         ' || v_tier);
    DBMS_OUTPUT.PUT_LINE('Review Count: ' || v_review_count);
    DBMS_OUTPUT.PUT_LINE('Avg Rating:   ' || v_avg_rating || '★');
    DBMS_OUTPUT.PUT_LINE('Trust Score:  ' || v_trust_score || ' / 100');
    DBMS_OUTPUT.PUT_LINE('--- REVIEW HISTORY (REFCURSOR) ---');

    LOOP
        FETCH v_cursor INTO v_rev_id, v_prod_id, v_prod_name, v_rating, v_helpful, v_date;
        EXIT WHEN v_cursor%NOTFOUND;
        DBMS_OUTPUT.PUT_LINE('[' || v_prod_id || '] ' || v_prod_name || ' | ' || v_rating || '★ | Date: ' || TO_CHAR(v_date, 'YYYY-MM-DD'));
    END LOOP;
    CLOSE v_cursor;
END;
/
```

---

### 4. Stored Procedure Execution: `SP_RECALCULATE_PRODUCT_METRICS`
*Demonstrates transactional synchronization: updates `PRODUCT_FEATURES` & `PRODUCTS` with `COMMIT`/`ROLLBACK`.*
*(Run as Script / F5)*
```sql
SET SERVEROUTPUT ON;
DECLARE
    v_updated_count   NUMBER;
    v_new_avg_rating  NUMBER;
BEGIN
    SP_RECALCULATE_PRODUCT_METRICS(
        p_product_id     => 'B0BNWZMDVL',
        p_updated_count  => v_updated_count,
        p_new_avg_rating => v_new_avg_rating
    );

    DBMS_OUTPUT.PUT_LINE('--- RECALCULATION COMPLETE ---');
    DBMS_OUTPUT.PUT_LINE('Recalculated Review Count: ' || v_updated_count);
    DBMS_OUTPUT.PUT_LINE('Recalculated Avg Rating:   ' || v_new_avg_rating);
    DBMS_OUTPUT.PUT_LINE('Status: Transaction committed to PRODUCT_FEATURES & PRODUCTS.');
END;
/
```

# INSYTE — Oracle 23ai Backend Demonstration & Viva Guide
**Prepared for:** Insyte  
**Target Database:** Oracle Cloud Autonomous Database 23ai (`insyte_high` / `FREEPDB1`)  
**Data Volume:** 75,000+ Reviews, 5,885 Products, 74,286 Customers  

---

## 🚀 Quick Execution (1-Click Demonstration)

To demonstrate everything live in front of ma'am with formatted tables, execution times, and outputs:

```bash
python scripts/demonstrate_backend.py
```

All SQL scripts are deployed on the live database and saved in:
📁 [`database/16_oracle_backend_demonstration.sql`](file:///c:/Users/DELL/Cooking/Insyte/database/16_oracle_backend_demonstration.sql)

---

## 1. 📊 Analytical & Operational Views

### View 1: `V_PRODUCT_PERFORMANCE_METRICS`
- **Purpose:** Combines catalog data (`PRODUCTS`) with aggregated behavioral metrics (`PRODUCT_FEATURES`).
- **Columns:** `product_id`, `product_name`, `main_category`, `price`, `average_rating`, `total_reviews`, `verified_purchase_pct`, `image_review_pct`.
- **Viva Point:** Demonstrates clean separation between dimensions and fact/feature aggregates with `NVL` null-safety.
```sql
SELECT product_id, product_name, price, average_rating, total_reviews 
FROM V_PRODUCT_PERFORMANCE_METRICS 
WHERE total_reviews >= 20;
```

### View 2: `V_CUSTOMER_ENGAGEMENT_SUMMARY`
- **Purpose:** Automatically segments customers into tiers (`Elite Reviewer`, `Active Contributor`, `Standard Customer`) based on activity span and helpful votes.
- **Viva Point:** Implements in-database conditional business rules via `CASE` expressions and date difference arithmetic (`last_review_date - first_review_date`).
```sql
SELECT customer_id, review_count, avg_rating, activity_span_days, reviewer_tier 
FROM V_CUSTOMER_ENGAGEMENT_SUMMARY 
WHERE reviewer_tier = 'Active Contributor';
```

### View 3: `V_CATEGORY_BENCHMARK_ANALYSIS`
- **Purpose:** Aggregates market benchmarks (mean price, rating, review volume, verified purchase rate) per category.
- **Viva Point:** Used by the analytics engine to identify underpriced or top-performing product categories.
```sql
SELECT main_category, total_products, avg_category_price, total_category_reviews 
FROM V_CATEGORY_BENCHMARK_ANALYSIS 
ORDER BY total_category_reviews DESC;
```

### View 4: `V_HIGH_IMPACT_CRITICAL_REVIEWS`
- **Purpose:** Surfaces high-risk negative reviews (`rating <= 2.0` with `helpful_vote >= 3`).
- **Viva Point:** Enables seller intervention and quality control by converting CLOB review text into displayable substrings.
```sql
SELECT review_id, product_id, rating, helpful_vote, review_headline 
FROM V_HIGH_IMPACT_CRITICAL_REVIEWS;
```

---

## 2. ⚙️ PL/SQL Stored Procedures & Functions

### Function: `FN_CALCULATE_CUSTOMER_TRUST_SCORE(p_customer_id)`
- **Type:** Deterministic PL/SQL Function
- **Logic:** Computes a 0–100 weighted Trust Index:
  - **50%** Verified purchase rate
  - **30%** Helpful community votes (capped at 20)
  - **20%** Review volume consistency (capped at 10)
- **Call in SQL:**
```sql
SELECT customer_id, FN_CALCULATE_CUSTOMER_TRUST_SCORE(customer_id) AS trust_score 
FROM CUSTOMERS 
WHERE review_count >= 3 FETCH FIRST 5 ROWS ONLY;
```

### Procedure 1: `SP_GET_PRODUCT_INSIGHTS`
- **Parameters:**
  - `p_product_id` (IN)
  - `p_product_title`, `p_category`, `p_price`, `p_avg_rating`, `p_total_reviews` (OUT Scalars)
  - `p_reviews_cursor` (OUT `SYS_REFCURSOR`)
- **Viva Point:** Shows how backend PL/SQL streams complex entity metadata and child record cursors back to an API with a single network round-trip.

### Procedure 2: `SP_CUSTOMER_ACTIVITY_REPORT`
- **Parameters:**
  - `p_customer_id` (IN)
  - `p_review_count`, `p_avg_rating`, `p_trust_score`, `p_tier` (OUT Scalars)
  - `p_reviews_cursor` (OUT `SYS_REFCURSOR`)
- **Viva Point:** Combines function invocation (`FN_CALCULATE_CUSTOMER_TRUST_SCORE`) inside a stored procedure alongside dynamic cursor streaming.

### Procedure 3: `SP_RECALCULATE_PRODUCT_METRICS`
- **Parameters:**
  - `p_product_id` (IN)
  - `p_updated_count`, `p_new_avg_rating` (OUT)
- **Viva Point:** Demonstrates transactional maintenance (`UPDATE ... SET ...`), consistency reconciliation between `REVIEWS`, `PRODUCT_FEATURES`, and `PRODUCTS`, with `COMMIT`/`ROLLBACK` exception handling.

---

## 3. 🔍 Advanced Subqueries Portfolio

| # | Subquery Technique | Purpose / Business Question | Key Syntax |
|---|-------------------|-----------------------------|------------|
| 1 | **Scalar Subquery in SELECT** | Price variance vs Category benchmark | `(SELECT AVG(...) FROM PRODUCTS ...)` in `SELECT` |
| 2 | **Correlated Subquery with `EXISTS`** | High-rated products that have critical negative complaints | `WHERE EXISTS (SELECT 1 FROM REVIEWS r WHERE r.product_id = p.product_id ...)` |
| 3 | **Correlated Subquery in WHERE** | Products outperforming their specific category average | `WHERE p.average_rating > (SELECT AVG(...) WHERE p2.category = p.category)` |
| 4 | **Subquery with `NOT IN`** | Reviewers with 100% verified purchase authenticity | `WHERE customer_id NOT IN (SELECT customer_id FROM REVIEWS WHERE verified = 0)` |
| 5 | **Subquery with `ALL`** | Premium products priced higher than ALL Fashion products | `WHERE price > ALL (SELECT price FROM PRODUCTS WHERE category = 'AMAZON FASHION')` |
| 6 | **Inline View (Subquery in FROM)** | Customer sentiment distribution cohort breakdown | `FROM (SELECT customer_id, CASE ... END AS sentiment_band FROM CUSTOMERS)` |
| 7 | **Subquery Factoring (`WITH` / CTE)** | Rank product categories by review engagement | `WITH CategoryStats AS (...), RankedCategories AS (...) SELECT ...` |

---

## 4. 🎓 Frequently Asked Viva Questions & Answers

1. **Q: Why use a View instead of querying base tables directly?**
   - *A:* Views provide data security (hiding sensitive internal fields), query simplicity for frontends, consistency of business logic (e.g. tier definitions), and optimize query execution plans.
2. **Q: What is the difference between a Correlated Subquery and an Uncorrelated Subquery?**
   - *A:* An uncorrelated subquery executes once independently for the entire outer query. A correlated subquery references columns from the outer query (`r.product_id = p.product_id`) and conceptually evaluates row-by-row.
3. **Q: Why use `EXISTS` instead of `IN`?**
   - *A:* `EXISTS` stops scanning as soon as the first matching row is found (short-circuit evaluation) and handles `NULL` values safely without unexpected evaluation failures.
4. **Q: Why use `SYS_REFCURSOR` in stored procedures?**
   - *A:* It allows PL/SQL procedures to pass back active result sets dynamically to client applications (Python/Node/Java) without materializing huge temporary arrays in memory.

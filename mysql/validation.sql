/*
============================================================
INSYTE - DATABASE VALIDATION
============================================================

Purpose:
    Validate row counts, duplicates, NULLs, relationships,
    and key data-quality conditions after importing the
    INSYTE dataset into MySQL.

Current accepted dataset:
    customers         = 74,286
    products          = 5,884
    reviews           = 74,991
    review_images     = 5,215
    product_features  = 5,884

Notes:
    - 9 review records were accepted as missing from the import.
    - 1 product is absent compared with the original validated subset.
    - These differences are accepted and do not affect referential
      integrity.
============================================================
*/


/*
------------------------------------------------------------
1. TABLE ROW COUNTS
------------------------------------------------------------
*/

SELECT 'customers' AS table_name, COUNT(*) AS row_count
FROM customers

UNION ALL

SELECT 'products', COUNT(*)
FROM products

UNION ALL

SELECT 'reviews', COUNT(*)
FROM reviews

UNION ALL

SELECT 'review_images', COUNT(*)
FROM review_images

UNION ALL

SELECT 'product_features', COUNT(*)
FROM product_features;

/*
EXPECTED CURRENT OUTPUT:

customers          | 74286
products           | 5884
reviews            | 74991
review_images      | 5215
product_features   | 5884
*/


/*
------------------------------------------------------------
2. CHECK DUPLICATE CUSTOMER IDs
------------------------------------------------------------
*/

SELECT
    customer_id,
    COUNT(*) AS duplicate_count
FROM customers
GROUP BY customer_id
HAVING COUNT(*) > 1;

/*
EXPECTED OUTPUT:

Empty result set
*/


/*
------------------------------------------------------------
3. CHECK DUPLICATE PRODUCT IDs
------------------------------------------------------------
*/

SELECT
    product_id,
    COUNT(*) AS duplicate_count
FROM products
GROUP BY product_id
HAVING COUNT(*) > 1;

/*
EXPECTED OUTPUT:

Empty result set
*/


/*
------------------------------------------------------------
4. CHECK DUPLICATE REVIEW IDs
------------------------------------------------------------
*/

SELECT
    review_id,
    COUNT(*) AS duplicate_count
FROM reviews
GROUP BY review_id
HAVING COUNT(*) > 1;

/*
EXPECTED OUTPUT:

Empty result set
*/


/*
------------------------------------------------------------
5. CHECK DUPLICATE REVIEW IMAGE IDs
------------------------------------------------------------
*/

SELECT
    image_id,
    COUNT(*) AS duplicate_count
FROM review_images
GROUP BY image_id
HAVING COUNT(*) > 1;

/*
EXPECTED OUTPUT:

Empty result set
*/


/*
------------------------------------------------------------
6. CHECK DUPLICATE PRODUCT FEATURE IDs
------------------------------------------------------------
*/

SELECT
    product_id,
    COUNT(*) AS duplicate_count
FROM product_features
GROUP BY product_id
HAVING COUNT(*) > 1;

/*
EXPECTED OUTPUT:

Empty result set
*/


/*
------------------------------------------------------------
7. REVIEWS -> CUSTOMERS
Check for reviews whose customer does not exist.
------------------------------------------------------------
*/

SELECT COUNT(*) AS orphan_reviews
FROM reviews r
LEFT JOIN customers c
    ON r.customer_id = c.customer_id
WHERE c.customer_id IS NULL;

/*
EXPECTED OUTPUT:

orphan_reviews
--------------
0
*/


/*
------------------------------------------------------------
8. REVIEWS -> PRODUCTS
Check for reviews whose product does not exist.
------------------------------------------------------------
*/

SELECT COUNT(*) AS orphan_review_products
FROM reviews r
LEFT JOIN products p
    ON r.product_id = p.product_id
WHERE p.product_id IS NULL;

/*
EXPECTED OUTPUT:

orphan_review_products
---------------------
0
*/


/*
------------------------------------------------------------
9. REVIEW IMAGES -> REVIEWS
------------------------------------------------------------
*/

SELECT COUNT(*) AS orphan_images
FROM review_images ri
LEFT JOIN reviews r
    ON ri.review_id = r.review_id
WHERE r.review_id IS NULL;

/*
EXPECTED OUTPUT:

orphan_images
-------------
0
*/


/*
------------------------------------------------------------
10. REVIEW IMAGES -> PRODUCTS
------------------------------------------------------------
*/

SELECT COUNT(*) AS orphan_image_products
FROM review_images ri
LEFT JOIN products p
    ON ri.product_id = p.product_id
WHERE p.product_id IS NULL;

/*
EXPECTED OUTPUT:

orphan_image_products
--------------------
0
*/


/*
------------------------------------------------------------
11. PRODUCT FEATURES -> PRODUCTS
------------------------------------------------------------
*/

SELECT COUNT(*) AS orphan_features
FROM product_features pf
LEFT JOIN products p
    ON pf.product_id = p.product_id
WHERE p.product_id IS NULL;

/*
EXPECTED OUTPUT:

orphan_features
---------------
0
*/


/*
------------------------------------------------------------
12. REVIEW RATING RANGE
------------------------------------------------------------
*/

SELECT
    MIN(rating) AS min_rating,
    MAX(rating) AS max_rating
FROM reviews;

/*
EXPECTED OUTPUT:

min_rating | max_rating
-----------+-----------
1          | 5
*/


/*
------------------------------------------------------------
13. INVALID RATINGS
------------------------------------------------------------
*/

SELECT COUNT(*) AS invalid_ratings
FROM reviews
WHERE rating < 1
   OR rating > 5
   OR rating IS NULL;

/*
EXPECTED OUTPUT:

invalid_ratings
---------------
0
*/


/*
------------------------------------------------------------
14. REVIEW IMAGE CONSISTENCY
has_image should agree with image_count.

If has_image = 1, image_count should be > 0.
If has_image = 0, image_count should be 0.
------------------------------------------------------------
*/

SELECT COUNT(*) AS inconsistent_image_rows
FROM reviews
WHERE (has_image = 1 AND image_count = 0)
   OR (has_image = 0 AND image_count > 0);

/*
EXPECTED OUTPUT:

inconsistent_image_rows
-----------------------
0
*/


/*
------------------------------------------------------------
15. VERIFIED PURCHASE VALUES
------------------------------------------------------------
*/

SELECT
    verified_purchase,
    COUNT(*) AS review_count
FROM reviews
GROUP BY verified_purchase
ORDER BY verified_purchase;

/*
EXPECTED CURRENT OUTPUT:

verified_purchase | review_count
------------------+-------------
0                 | 2756
1                 | 72235

Note:
    The original validated subset contained 72,244 verified
    reviews. The current MySQL import contains 72,235 because
    9 review records were accepted as missing.
*/


/*
------------------------------------------------------------
16. IMAGE-BACKED REVIEWS
------------------------------------------------------------
*/

SELECT
    has_image,
    COUNT(*) AS review_count
FROM reviews
GROUP BY has_image
ORDER BY has_image;

/*
EXPECTED CURRENT OUTPUT:

has_image | review_count
----------+-------------
0         | 71933
1         | 3058
*/


/*
------------------------------------------------------------
17. TOTAL REVIEW IMAGE COUNT
------------------------------------------------------------
*/

SELECT
    COUNT(*) AS total_review_images
FROM review_images;

/*
EXPECTED OUTPUT:

total_review_images
-------------------
5215
*/


/*
------------------------------------------------------------
18. PRODUCT FEATURE PRICE COVERAGE
------------------------------------------------------------
*/

SELECT
    COUNT(*) AS total_features,
    COUNT(price) AS products_with_price,
    COUNT(*) - COUNT(price) AS products_without_price,
    ROUND(100 * COUNT(price) / COUNT(*), 2) AS price_coverage_percentage
FROM product_features;

/*
EXPECTED CURRENT OUTPUT:

total_features | products_with_price | products_without_price | price_coverage_percentage
---------------+---------------------+------------------------+--------------------------
5884           | approximately 4225  | approximately 1659     | approximately 71.8

Note:
    Exact values depend on the imported product_features data.
*/


/*
------------------------------------------------------------
19. FINAL DATASET SUMMARY
------------------------------------------------------------
*/

SELECT
    (SELECT COUNT(*) FROM customers) AS customers,
    (SELECT COUNT(*) FROM products) AS products,
    (SELECT COUNT(*) FROM reviews) AS reviews,
    (SELECT COUNT(*) FROM review_images) AS review_images,
    (SELECT COUNT(*) FROM product_features) AS product_features,
    (SELECT ROUND(AVG(rating), 2) FROM reviews) AS avg_rating,
    (SELECT SUM(helpful_vote) FROM reviews) AS total_helpful_votes,
    (SELECT ROUND(100 * AVG(verified_purchase), 2) FROM reviews)
        AS verified_purchase_rate,
    (SELECT ROUND(100 * AVG(has_image), 2) FROM reviews)
        AS image_review_rate;

/*
EXPECTED CURRENT OUTPUT:

customers        | 74286
products         | 5884
reviews          | 74991
review_images    | 5215
product_features | 5884
avg_rating       | 4.10
total_helpful_votes | 76942
verified_purchase_rate | 96.32
image_review_rate | 4.08
*/


/*
============================================================
VALIDATION STATUS
============================================================

Current status:

    [PASS] All five tables imported
    [PASS] Primary-key duplicates checked
    [PASS] Foreign-key relationships checked
    [PASS] No orphan reviews
    [PASS] No orphan review products
    [PASS] No orphan review images
    [PASS] No orphan image products
    [PASS] No orphan product features
    [PASS] Rating range valid
    [PASS] Review image consistency valid

Accepted differences:

    - 9 reviews missing from the original 75,000-review subset
    - 1 product missing from the original 5,885-product subset

The current dataset is considered ready for INSYTE analytics,
dashboard development, and ML work.
============================================================
*/
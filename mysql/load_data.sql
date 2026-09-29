-- ============================================================
-- INSYTE - DATA LOADING
-- Database: insyte
-- Source: Amazon Reviews'23 Appliances subset
-- ============================================================

USE insyte;

-- ============================================================
-- 1. CUSTOMERS
-- ============================================================

LOAD DATA LOCAL INFILE 'data/processed/customers.csv'
INTO TABLE customers
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    customer_id,
    review_count,
    product_count,
    avg_rating_given,
    total_helpful_votes,
    verified_purchase_rate,
    image_review_rate,
    @first_review_date,
    @last_review_date
)
SET
    first_review_date = STR_TO_DATE(@first_review_date, '%d-%m-%Y'),
    last_review_date = STR_TO_DATE(@last_review_date, '%d-%m-%Y');


-- ============================================================
-- 2. PRODUCTS
-- ============================================================

LOAD DATA LOCAL INFILE 'data/processed/products.csv'
INTO TABLE products
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    product_id,
    title,
    store,
    main_category,
    categories,
    description,
    price,
    average_rating,
    rating_number,
    product_image_urls
);


-- ============================================================
-- 3. REVIEWS
-- ============================================================

LOAD DATA LOCAL INFILE 'data/processed/reviews.csv'
INTO TABLE reviews
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    review_id,
    customer_id,
    product_id,
    rating,
    title,
    text,
    timestamp,
    @review_date,
    @verified_purchase,
    helpful_vote,
    @has_image,
    image_count
)
SET
    review_date = STR_TO_DATE(@review_date, '%Y-%m-%d'),

    verified_purchase =
        CASE
            WHEN LOWER(TRIM(@verified_purchase))
                IN ('true', '1', 'yes') THEN 1
            WHEN LOWER(TRIM(@verified_purchase))
                IN ('false', '0', 'no') THEN 0
            ELSE NULL
        END,

    has_image =
        CASE
            WHEN LOWER(TRIM(@has_image))
                IN ('true', '1', 'yes') THEN 1
            WHEN LOWER(TRIM(@has_image))
                IN ('false', '0', 'no') THEN 0
            ELSE NULL
        END;


-- ============================================================
-- 4. REVIEW IMAGES
-- ============================================================

LOAD DATA LOCAL INFILE 'data/processed/review_images.csv'
INTO TABLE review_images
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    image_id,
    review_id,
    product_id,
    image_url
);


-- ============================================================
-- 5. PRODUCT FEATURES
-- ============================================================

LOAD DATA LOCAL INFILE 'data/processed/product_features.csv'
INTO TABLE product_features
FIELDS TERMINATED BY ','
ENCLOSED BY '"'
LINES TERMINATED BY '\n'
IGNORE 1 ROWS
(
    product_id,
    review_count,
    avg_review_rating,
    total_helpful_votes,
    verified_purchase_rate,
    image_review_rate,
    avg_images_per_review,
    rating_1_pct,
    rating_2_pct,
    rating_3_pct,
    rating_4_pct,
    rating_5_pct,
    price
);

/*
============================================================
INSYTE - DATABASE SCHEMA
============================================================

Database:
    insyte

Purpose:
    MySQL database for the INSYTE E-Commerce Customer
    Behaviour Analytics project.

Tables:
    customers
    products
    product_features
    reviews
    review_images

============================================================
*/


CREATE DATABASE IF NOT EXISTS insyte;

USE insyte;


/*
============================================================
1. CUSTOMERS
============================================================
*/

CREATE TABLE IF NOT EXISTS customers (
    customer_id VARCHAR(100) NOT NULL,
    review_count INT DEFAULT NULL,
    product_count INT DEFAULT NULL,
    avg_rating_given DECIMAL(6,4) NOT NULL,
    total_helpful_votes INT DEFAULT NULL,
    verified_purchase_rate DECIMAL(6,4) DEFAULT NULL,
    image_review_rate DECIMAL(6,4) DEFAULT NULL,
    first_review_date DATE DEFAULT NULL,
    last_review_date DATE DEFAULT NULL,

    PRIMARY KEY (customer_id)
);


/*
============================================================
2. PRODUCTS
============================================================
*/

CREATE TABLE IF NOT EXISTS products (
    product_id VARCHAR(100) NOT NULL,
    title TEXT,
    store VARCHAR(255) DEFAULT NULL,
    main_category VARCHAR(255) DEFAULT NULL,
    categories TEXT,
    description TEXT,
    price DECIMAL(10,2) DEFAULT NULL,
    average_rating DECIMAL(4,2) DEFAULT NULL,
    rating_number INT DEFAULT NULL,
    product_image_urls TEXT,

    PRIMARY KEY (product_id)
);


/*
============================================================
3. PRODUCT FEATURES
============================================================

Product-level analytical features used for:
    - Product Health
    - Product Analytics
    - ML product clustering
============================================================
*/

CREATE TABLE IF NOT EXISTS product_features (
    product_id VARCHAR(100) NOT NULL,
    review_count INT DEFAULT NULL,
    avg_review_rating DECIMAL(4,2) DEFAULT NULL,
    total_helpful_votes INT DEFAULT NULL,
    verified_purchase_rate DECIMAL(6,4) DEFAULT NULL,
    image_review_rate DECIMAL(6,4) DEFAULT NULL,
    avg_images_per_review DECIMAL(8,4) DEFAULT NULL,
    rating_1_pct DECIMAL(6,4) DEFAULT NULL,
    rating_2_pct DECIMAL(6,4) DEFAULT NULL,
    rating_3_pct DECIMAL(6,4) DEFAULT NULL,
    rating_4_pct DECIMAL(6,4) DEFAULT NULL,
    rating_5_pct DECIMAL(6,4) DEFAULT NULL,
    price DECIMAL(10,2) DEFAULT NULL,

    PRIMARY KEY (product_id),

    CONSTRAINT product_features_ibfk_1
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);


/*
============================================================
4. REVIEWS
============================================================
*/

CREATE TABLE IF NOT EXISTS reviews (
    review_id VARCHAR(100) NOT NULL,
    customer_id VARCHAR(100) DEFAULT NULL,
    product_id VARCHAR(100) DEFAULT NULL,
    rating DECIMAL(2,1) DEFAULT NULL,
    title TEXT,
    text TEXT,
    timestamp BIGINT DEFAULT NULL,
    review_date DATE DEFAULT NULL,
    verified_purchase TINYINT(1) DEFAULT NULL,
    helpful_vote INT DEFAULT NULL,
    has_image TINYINT(1) DEFAULT NULL,
    image_count INT DEFAULT NULL,

    PRIMARY KEY (review_id),

    KEY customer_id (customer_id),
    KEY product_id (product_id),

    CONSTRAINT reviews_ibfk_1
        FOREIGN KEY (customer_id)
        REFERENCES customers(customer_id),

    CONSTRAINT reviews_ibfk_2
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);


/*
============================================================
5. REVIEW IMAGES
============================================================
*/

CREATE TABLE IF NOT EXISTS review_images (
    image_id VARCHAR(100) NOT NULL,
    review_id VARCHAR(100) DEFAULT NULL,
    product_id VARCHAR(100) DEFAULT NULL,
    image_url TEXT,

    PRIMARY KEY (image_id),

    KEY product_id (product_id),
    KEY review_images_ibfk_1 (review_id),

    CONSTRAINT review_images_ibfk_1
        FOREIGN KEY (review_id)
        REFERENCES reviews(review_id),

    CONSTRAINT review_images_ibfk_2
        FOREIGN KEY (product_id)
        REFERENCES products(product_id)
);


/*
============================================================
6. ADDITIONAL ANALYTICAL INDEXES
============================================================

Indexes used by common INSYTE analytical queries.
============================================================
*/

CREATE INDEX idx_reviews_rating
    ON reviews(rating);

CREATE INDEX idx_reviews_date
    ON reviews(review_date);

CREATE INDEX idx_reviews_verified
    ON reviews(verified_purchase);

CREATE INDEX idx_reviews_has_image
    ON reviews(has_image);


/*
============================================================
SCHEMA SUMMARY
============================================================

customers
    PK: customer_id

products
    PK: product_id

product_features
    PK: product_id
    FK: product_id -> products.product_id

reviews
    PK: review_id
    FK: customer_id -> customers.customer_id
    FK: product_id  -> products.product_id

review_images
    PK: image_id
    FK: review_id  -> reviews.review_id
    FK: product_id -> products.product_id

============================================================
*/
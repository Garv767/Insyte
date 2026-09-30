-- ==============================================================================
-- INSYTE: 02_schema.sql (Updated to match ML Analytical Schema)
-- Oracle 23ai Database Schema
-- ==============================================================================

PROMPT Dropping old transactional tables if they exist...

DROP TABLE ETL_AUDIT CASCADE CONSTRAINTS;
DROP TABLE TRANSACTION_ADJUSTMENTS CASCADE CONSTRAINTS;
DROP TABLE REVIEW_MEDIA CASCADE CONSTRAINTS;
DROP TABLE ORDER_ITEMS CASCADE CONSTRAINTS;
DROP TABLE ORDERS CASCADE CONSTRAINTS;
DROP TABLE REVIEW_IMAGES CASCADE CONSTRAINTS;
DROP TABLE REVIEWS CASCADE CONSTRAINTS;
DROP TABLE PRODUCT_FEATURES CASCADE CONSTRAINTS;
DROP TABLE PRODUCTS CASCADE CONSTRAINTS;
DROP TABLE CUSTOMERS CASCADE CONSTRAINTS;

PROMPT Deploying New Analytical Relational Tables...

-- 1. CUSTOMERS Table
CREATE TABLE customers (
    customer_id VARCHAR2(100) NOT NULL,
    review_count NUMBER,
    product_count NUMBER,
    avg_rating_given NUMBER(6,4) NOT NULL,
    total_helpful_votes NUMBER,
    verified_purchase_rate NUMBER(6,4),
    image_review_rate NUMBER(6,4),
    first_review_date DATE,
    last_review_date DATE,
    CONSTRAINT pk_customers PRIMARY KEY (customer_id)
);

-- 2. PRODUCTS Table
CREATE TABLE products (
    product_id VARCHAR2(100) NOT NULL,
    title CLOB,
    store VARCHAR2(255),
    main_category VARCHAR2(255),
    categories CLOB,
    description CLOB,
    price NUMBER(10,2),
    average_rating NUMBER(4,2),
    rating_number NUMBER,
    product_image_urls CLOB,
    CONSTRAINT pk_products PRIMARY KEY (product_id)
);

-- 3. PRODUCT FEATURES Table
CREATE TABLE product_features (
    product_id VARCHAR2(100) NOT NULL,
    review_count NUMBER,
    avg_review_rating NUMBER(4,2),
    total_helpful_votes NUMBER,
    verified_purchase_rate NUMBER(6,4),
    image_review_rate NUMBER(6,4),
    avg_images_per_review NUMBER(8,4),
    rating_1_pct NUMBER(6,4),
    rating_2_pct NUMBER(6,4),
    rating_3_pct NUMBER(6,4),
    rating_4_pct NUMBER(6,4),
    rating_5_pct NUMBER(6,4),
    price NUMBER(10,2),
    CONSTRAINT pk_product_features PRIMARY KEY (product_id),
    CONSTRAINT fk_pf_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- 4. REVIEWS Table
CREATE TABLE reviews (
    review_id VARCHAR2(100) NOT NULL,
    customer_id VARCHAR2(100),
    product_id VARCHAR2(100),
    rating NUMBER(2,1),
    title CLOB,
    text CLOB,
    timestamp NUMBER,
    review_date DATE,
    verified_purchase NUMBER(1),
    helpful_vote NUMBER,
    has_image NUMBER(1),
    image_count NUMBER,
    CONSTRAINT pk_reviews PRIMARY KEY (review_id),
    CONSTRAINT fk_reviews_customer FOREIGN KEY (customer_id) REFERENCES customers(customer_id) ON DELETE SET NULL,
    CONSTRAINT fk_reviews_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE SET NULL
);

-- 5. REVIEW IMAGES Table
CREATE TABLE review_images (
    image_id VARCHAR2(100) NOT NULL,
    review_id VARCHAR2(100),
    product_id VARCHAR2(100),
    image_url CLOB,
    CONSTRAINT pk_review_images PRIMARY KEY (image_id),
    CONSTRAINT fk_ri_review FOREIGN KEY (review_id) REFERENCES reviews(review_id) ON DELETE CASCADE,
    CONSTRAINT fk_ri_product FOREIGN KEY (product_id) REFERENCES products(product_id) ON DELETE CASCADE
);

-- Indexes
CREATE INDEX idx_reviews_rating ON reviews(rating);
CREATE INDEX idx_reviews_date ON reviews(review_date);
CREATE INDEX idx_reviews_verified ON reviews(verified_purchase);
CREATE INDEX idx_reviews_has_image ON reviews(has_image);
CREATE INDEX idx_reviews_cust ON reviews(customer_id);
CREATE INDEX idx_reviews_prod ON reviews(product_id);
CREATE INDEX idx_ri_prod ON review_images(product_id);
CREATE INDEX idx_ri_rev ON review_images(review_id);

PROMPT Schema updated successfully.

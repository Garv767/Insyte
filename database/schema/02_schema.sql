-- ================================================================
-- INSYTE: 02_schema.sql
-- Oracle 23ai Core Relational Schema, JSON & Vector Definitions
-- Run as INSYTE_ADMIN on FREEPDB1
-- ================================================================

-- 1. Sequences for surrogate key generation
CREATE SEQUENCE order_item_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE review_media_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE adj_seq START WITH 1 INCREMENT BY 1 NOCACHE;
CREATE SEQUENCE audit_seq START WITH 1 INCREMENT BY 1 NOCACHE;

-- 2. CUSTOMERS Table (Known customer profiles; NULL customers handled as Guest transactions)
CREATE TABLE CUSTOMERS (
    customer_id         VARCHAR2(30) NOT NULL,
    country             VARCHAR2(100),
    registration_date   TIMESTAMP WITH TIME ZONE,
    is_guest            NUMBER(1) DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_customers PRIMARY KEY (customer_id)
);

-- 3. PRODUCTS Table (Incorporating native JSON and 384-dimensional Vector)
CREATE TABLE PRODUCTS (
    stock_code              VARCHAR2(20) NOT NULL,
    original_description    VARCHAR2(500),
    normalized_description  VARCHAR2(500),
    unit_price              NUMBER(10, 2),
    metadata                JSON,
    embedding               VECTOR(384, FLOAT32),
    created_at              TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_products PRIMARY KEY (stock_code)
);

-- 4. ORDERS Table (Explicit timezone tracking and cancellation flags)
CREATE TABLE ORDERS (
    invoice_no          VARCHAR2(20) NOT NULL,
    customer_id         VARCHAR2(30),
    invoice_date        TIMESTAMP WITH TIME ZONE NOT NULL,
    country             VARCHAR2(100),
    order_status        VARCHAR2(20) DEFAULT 'COMPLETED',
    is_cancellation     NUMBER(1) DEFAULT 0,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_orders PRIMARY KEY (invoice_no),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) 
        REFERENCES CUSTOMERS (customer_id) ON DELETE SET NULL
);

-- 5. ORDER_ITEMS Table (Historical transaction price integrity)
CREATE TABLE ORDER_ITEMS (
    item_id             NUMBER NOT NULL,
    invoice_no          VARCHAR2(20) NOT NULL,
    stock_code          VARCHAR2(20) NOT NULL,
    quantity            NUMBER(10) NOT NULL,
    unit_price          NUMBER(10, 2) NOT NULL,
    line_total          NUMBER(12, 2) GENERATED ALWAYS AS (quantity * unit_price),
    CONSTRAINT pk_order_items PRIMARY KEY (item_id),
    CONSTRAINT fk_items_order FOREIGN KEY (invoice_no) 
        REFERENCES ORDERS (invoice_no) ON DELETE CASCADE,
    CONSTRAINT fk_items_product FOREIGN KEY (stock_code) 
        REFERENCES PRODUCTS (stock_code)
);

-- 6. REVIEWS Table (Multi-modal customer reviews)
CREATE TABLE REVIEWS (
    review_id           VARCHAR2(50) NOT NULL,
    customer_id         VARCHAR2(30),
    stock_code          VARCHAR2(20),
    invoice_no          VARCHAR2(20),
    rating              NUMBER(2, 1),
    sentiment_label     VARCHAR2(20), -- 'POSITIVE', 'NEUTRAL', 'NEGATIVE'
    review_text         CLOB,
    has_media           NUMBER(1) DEFAULT 0,
    media_count         NUMBER(5) DEFAULT 0,
    review_date         TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_reviews PRIMARY KEY (review_id),
    CONSTRAINT fk_reviews_product FOREIGN KEY (stock_code) 
        REFERENCES PRODUCTS (stock_code) ON DELETE CASCADE
);

-- 7. REVIEW_MEDIA Table (Normalized media asset references)
CREATE TABLE REVIEW_MEDIA (
    media_id            NUMBER NOT NULL,
    review_id           VARCHAR2(50) NOT NULL,
    media_url           VARCHAR2(1000) NOT NULL,
    media_type          VARCHAR2(50), -- 'IMAGE', 'VIDEO', 'DOCUMENT'
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_review_media PRIMARY KEY (media_id),
    CONSTRAINT fk_media_review FOREIGN KEY (review_id) 
        REFERENCES REVIEWS (review_id) ON DELETE CASCADE
);

-- 8. TRANSACTION_ADJUSTMENTS Table (Audit of negative quantity items / returns)
CREATE TABLE TRANSACTION_ADJUSTMENTS (
    adjustment_id       NUMBER NOT NULL,
    invoice_no          VARCHAR2(20) NOT NULL,
    stock_code          VARCHAR2(20),
    quantity            NUMBER(10) NOT NULL,
    unit_price          NUMBER(10, 2),
    adjustment_type     VARCHAR2(30) DEFAULT 'CANCELLATION',
    reason              VARCHAR2(200),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_adj PRIMARY KEY (adjustment_id)
);

-- 9. ETL_AUDIT Table (Tracking rejected records and pipeline diagnostics)
CREATE TABLE ETL_AUDIT (
    audit_id            NUMBER NOT NULL,
    source_row_id       NUMBER,
    issue_type          VARCHAR2(50),
    issue_description   VARCHAR2(400),
    raw_value           VARCHAR2(1000),
    created_at          TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_audit PRIMARY KEY (audit_id)
);

-- Composite B-Tree Indexes for Performance
CREATE INDEX idx_orders_cust_date ON ORDERS (customer_id, invoice_date);
CREATE INDEX idx_orders_inv_date ON ORDERS (invoice_date);
CREATE INDEX idx_order_items_inv ON ORDER_ITEMS (invoice_no);
CREATE INDEX idx_order_items_stock ON ORDER_ITEMS (stock_code);
CREATE INDEX idx_reviews_stock ON REVIEWS (stock_code);
CREATE INDEX idx_reviews_cust ON REVIEWS (customer_id);

PROMPT [INSYTE] Core schema tables, sequences, and indexes successfully defined.

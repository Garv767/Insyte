-- ==============================================================================
-- INSYTE: 02_schema.sql
-- Oracle 23ai Core Relational Tables, Native JSON, and Vector Type Definitions
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE SCHEMA] Deploying Relational Tables...

-- 1. CUSTOMERS Table
-- Known customer profiles; NULL customer entries in raw data are treated as Guest transactions
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE CUSTOMERS CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF;
END;
/
CREATE TABLE CUSTOMERS (
    customer_id         VARCHAR2(30) NOT NULL,
    country             VARCHAR2(100),
    registration_date   TIMESTAMP WITH TIME ZONE,
    is_guest            NUMBER(1) DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_customers PRIMARY KEY (customer_id)
);
COMMENT ON TABLE CUSTOMERS IS 'Normalized customer registry distinguishing registered vs guest shoppers';

-- 2. PRODUCTS Table
-- Incorporates Oracle 23ai native binary JSON metadata and 384-dimensional Vector column
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE PRODUCTS CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF;
END;
/
CREATE TABLE PRODUCTS (
    stock_code              VARCHAR2(20) NOT NULL,
    original_description    VARCHAR2(500),
    normalized_description  VARCHAR2(500),
    unit_price              NUMBER(10, 2),
    metadata                JSON,
    embedding               VECTOR(384, FLOAT32),
    created_at              TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_products PRIMARY KEY (stock_code)
);
COMMENT ON TABLE PRODUCTS IS 'Product catalog with native JSON attributes and AI vector embeddings';

-- 3. ORDERS Table
-- Invoice headers with explicit timezone tracking and cancellation classification
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE ORDERS CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF;
END;
/
CREATE TABLE ORDERS (
    invoice_no          VARCHAR2(20) NOT NULL,
    customer_id         VARCHAR2(30),
    invoice_date        TIMESTAMP WITH TIME ZONE NOT NULL,
    country             VARCHAR2(100),
    order_status        VARCHAR2(20) DEFAULT 'COMPLETED',
    is_cancellation     NUMBER(1) DEFAULT 0,
    is_guest            NUMBER(1) DEFAULT 0,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_orders PRIMARY KEY (invoice_no),
    CONSTRAINT fk_orders_customer FOREIGN KEY (customer_id) 
        REFERENCES CUSTOMERS (customer_id) ON DELETE SET NULL
);
COMMENT ON TABLE ORDERS IS 'E-commerce transactional invoice headers';

-- 4. ORDER_ITEMS Table
-- Line items with permanent historical transaction prices (protects against future price changes)
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE ORDER_ITEMS CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF;
END;
/
CREATE TABLE ORDER_ITEMS (
    item_id             NUMBER NOT NULL,
    invoice_no          VARCHAR2(20) NOT NULL,
    stock_code          VARCHAR2(20) NOT NULL,
    quantity            NUMBER(10) NOT NULL,
    unit_price          NUMBER(10, 2) NOT NULL,
    line_total          NUMBER(12, 2) GENERATED ALWAYS AS (quantity * unit_price),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_order_items PRIMARY KEY (item_id),
    CONSTRAINT fk_items_order FOREIGN KEY (invoice_no) 
        REFERENCES ORDERS (invoice_no) ON DELETE CASCADE,
    CONSTRAINT fk_items_product FOREIGN KEY (stock_code) 
        REFERENCES PRODUCTS (stock_code)
);
COMMENT ON TABLE ORDER_ITEMS IS 'Order line items retaining point-in-time transaction prices';

-- 5. REVIEWS Table
-- Customer textual feedback, star ratings, sentiment, and media summary indicators
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE REVIEWS CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF;
END;
/
CREATE TABLE REVIEWS (
    review_id           VARCHAR2(50) NOT NULL,
    customer_id         VARCHAR2(30),
    stock_code          VARCHAR2(20) NOT NULL,
    invoice_no          VARCHAR2(20),
    rating              NUMBER(2, 1),
    sentiment_label     VARCHAR2(20) DEFAULT 'NEUTRAL',
    review_text         CLOB,
    has_media           NUMBER(1) DEFAULT 0,
    media_count         NUMBER(5) DEFAULT 0,
    review_date         TIMESTAMP WITH TIME ZONE,
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_reviews PRIMARY KEY (review_id),
    CONSTRAINT fk_reviews_product FOREIGN KEY (stock_code) 
        REFERENCES PRODUCTS (stock_code) ON DELETE CASCADE
);
COMMENT ON TABLE REVIEWS IS 'Customer product reviews with rating and derived/explicit sentiment';

-- 6. REVIEW_MEDIA Table
-- Normalized media asset references (photos, customer videos, attachments)
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE REVIEW_MEDIA CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF;
END;
/
CREATE TABLE REVIEW_MEDIA (
    media_id            NUMBER NOT NULL,
    review_id           VARCHAR2(50) NOT NULL,
    media_url           VARCHAR2(1000) NOT NULL,
    media_type          VARCHAR2(50) DEFAULT 'IMAGE',
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_review_media PRIMARY KEY (media_id),
    CONSTRAINT fk_media_review FOREIGN KEY (review_id) 
        REFERENCES REVIEWS (review_id) ON DELETE CASCADE
);
COMMENT ON TABLE REVIEW_MEDIA IS 'Normalized media assets attached to customer product reviews';

-- 7. TRANSACTION_ADJUSTMENTS Table
-- Audit store for cancellations, return adjustments, and damaged goods
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE TRANSACTION_ADJUSTMENTS CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF;
END;
/
CREATE TABLE TRANSACTION_ADJUSTMENTS (
    adjustment_id       NUMBER NOT NULL,
    invoice_no          VARCHAR2(20) NOT NULL,
    stock_code          VARCHAR2(20),
    quantity            NUMBER(10) NOT NULL,
    unit_price          NUMBER(10, 2),
    adjustment_type     VARCHAR2(30) DEFAULT 'CANCELLATION',
    reason              VARCHAR2(200),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_adj PRIMARY KEY (adjustment_id)
);
COMMENT ON TABLE TRANSACTION_ADJUSTMENTS IS 'Audit log of negative quantities, cancellations, and returns';

-- 8. ETL_AUDIT Table
-- Pipeline diagnostics logging invalid or rejected source rows
BEGIN
    EXECUTE IMMEDIATE 'DROP TABLE ETL_AUDIT CASCADE CONSTRAINTS';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -942 THEN RAISE; END IF;
END;
/
CREATE TABLE ETL_AUDIT (
    audit_id            NUMBER NOT NULL,
    source_row_id       NUMBER,
    issue_type          VARCHAR2(50),
    issue_description   VARCHAR2(400),
    raw_value           VARCHAR2(1000),
    created_at          TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP,
    CONSTRAINT pk_audit PRIMARY KEY (audit_id)
);
COMMENT ON TABLE ETL_AUDIT IS 'Data cleaning audit log recording rejected and sanitized rows';

PROMPT [INSYTE SCHEMA] Core relational tables created successfully.

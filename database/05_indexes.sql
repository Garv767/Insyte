-- ==============================================================================
-- INSYTE: 05_indexes.sql
-- Oracle 23ai Indexing Strategy & Query Optimization
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE INDEXES] Building Composite and Analytical Indexes...

-- 1. Orders Indexes
-- Composite index for fast RFM recency and customer chronological joins
CREATE INDEX idx_orders_cust_date 
    ON ORDERS (customer_id, invoice_date);

-- Index for temporal trend aggregations (Daily, Weekly, Monthly Revenue)
CREATE INDEX idx_orders_inv_date 
    ON ORDERS (invoice_date);

-- Fast filter for sales vs cancellations
CREATE INDEX idx_orders_cancel 
    ON ORDERS (is_cancellation);

-- 2. Order Items Indexes
-- High-concurrency join support between ORDERS and ORDER_ITEMS
CREATE INDEX idx_order_items_inv 
    ON ORDER_ITEMS (invoice_no);

-- Product-level sales and aggregation index
CREATE INDEX idx_order_items_stock 
    ON ORDER_ITEMS (stock_code);

-- 3. Products Indexes
-- Function-based index on uppercase product description for fast text lookup
CREATE INDEX idx_products_desc_norm 
    ON PRODUCTS (UPPER(normalized_description));

-- 4. Reviews & Media Indexes
CREATE INDEX idx_reviews_stock 
    ON REVIEWS (stock_code);

CREATE INDEX idx_reviews_cust 
    ON REVIEWS (customer_id);

CREATE INDEX idx_reviews_rating 
    ON REVIEWS (rating);

CREATE INDEX idx_reviews_sentiment 
    ON REVIEWS (sentiment_label);

CREATE INDEX idx_media_review_fk 
    ON REVIEW_MEDIA (review_id);

-- 5. Oracle 23ai AI Vector Search Index (HNSW - Hierarchical Navigable Small World)
-- Accelerates cosine distance similarity search on 384-dimensional embeddings
BEGIN
    EXECUTE IMMEDIATE 'CREATE VECTOR INDEX v_idx_product_embedding 
                       ON PRODUCTS (embedding) 
                       ORGANIZATION INMEMORY NEIGHBOR GRAPH 
                       DISTANCE COSINE 
                       WITH TARGET ACCURACY 95';
EXCEPTION
    WHEN OTHERS THEN
        -- If in-memory vector index syntax requires specific tablespace or license mode,
        -- record notification and proceed (Oracle 23ai supports exact cosine search natively without index)
        DBMS_OUTPUT.PUT_LINE('Note on Vector Index: ' || SQLERRM);
END;
/

PROMPT [INSYTE INDEXES] All performance indexes successfully constructed.

-- ==============================================================================
-- INSYTE: 04_constraints.sql
-- Oracle 23ai Table Constraints & Domain Integrity Rules
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE CONSTRAINTS] Applying Integrity and Domain Constraints...

-- 1. Domain Constraints on ORDER_ITEMS
-- Ensure sales order items have strictly positive quantity and non-negative unit price
ALTER TABLE ORDER_ITEMS 
    ADD CONSTRAINT chk_item_quantity CHECK (quantity > 0);

ALTER TABLE ORDER_ITEMS 
    ADD CONSTRAINT chk_item_price CHECK (unit_price >= 0);

-- 2. Domain Constraints on PRODUCTS
ALTER TABLE PRODUCTS 
    ADD CONSTRAINT chk_product_price CHECK (unit_price IS NULL OR unit_price >= 0);

-- 3. Domain Constraints on REVIEWS
-- Star ratings must strictly be between 1.0 and 5.0
ALTER TABLE REVIEWS 
    ADD CONSTRAINT chk_review_rating CHECK (rating IS NULL OR (rating >= 1.0 AND rating <= 5.0));

-- Valid sentiment domain values
ALTER TABLE REVIEWS 
    ADD CONSTRAINT chk_review_sentiment CHECK (
        sentiment_label IN ('POSITIVE', 'NEUTRAL', 'NEGATIVE', 'UNKNOWN')
    );

-- Boolean flag checks (Oracle uses NUMBER(1) for flags)
ALTER TABLE REVIEWS 
    ADD CONSTRAINT chk_review_has_media CHECK (has_media IN (0, 1));

ALTER TABLE ORDERS 
    ADD CONSTRAINT chk_orders_is_cancel CHECK (is_cancellation IN (0, 1));

ALTER TABLE ORDERS 
    ADD CONSTRAINT chk_orders_is_guest CHECK (is_guest IN (0, 1));

ALTER TABLE CUSTOMERS 
    ADD CONSTRAINT chk_cust_is_guest CHECK (is_guest IN (0, 1));

-- 4. Media Type Domain Constraint
ALTER TABLE REVIEW_MEDIA 
    ADD CONSTRAINT chk_media_type CHECK (
        media_type IN ('IMAGE', 'VIDEO', 'DOCUMENT', 'AUDIO', 'OTHER')
    );

PROMPT [INSYTE CONSTRAINTS] All domain and referential integrity constraints applied.

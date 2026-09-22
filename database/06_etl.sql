-- ==============================================================================
-- INSYTE: 06_etl.sql
-- In-Database SQL ETL, Data Cleaning & String Normalization Logic
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE ETL] Compiling In-Database Transformation Logic...

-- 1. Function to Normalize Product Descriptions
-- Demonstrates UPPER, TRIM, and REGEXP_REPLACE to remove noisy punctuation
CREATE OR REPLACE FUNCTION fn_clean_description(p_raw_desc IN VARCHAR2) 
RETURN VARCHAR2 DETERMINISTIC IS
    v_clean VARCHAR2(500);
BEGIN
    IF p_raw_desc IS NULL THEN
        RETURN 'UNLABELLED PRODUCT';
    END IF;
    
    -- Strip non-alphanumeric special characters, convert to single spaces, trim, uppercase
    v_clean := UPPER(
        TRIM(
            REGEXP_REPLACE(p_raw_desc, '[^[:alnum:] ]', ' ')
        )
    );
    -- Collapse multiple whitespace into single space
    v_clean := REGEXP_REPLACE(v_clean, '\s+', ' ');
    
    RETURN SUBSTR(v_clean, 1, 500);
END;
/

-- 2. Procedure: Classify and Archive Cancellation Adjustments
-- Demonstrates conditional logic with CASE, DECODE, and NVL
CREATE OR REPLACE PROCEDURE sp_archive_adjustments IS
    v_rows_adjusted NUMBER := 0;
BEGIN
    -- Move cancelled or negative transactions to TRANSACTION_ADJUSTMENTS table
    INSERT INTO TRANSACTION_ADJUSTMENTS (
        adjustment_id,
        invoice_no,
        stock_code,
        quantity,
        unit_price,
        adjustment_type,
        reason,
        created_at
    )
    SELECT 
        adj_seq.NEXTVAL,
        o.invoice_no,
        oi.stock_code,
        oi.quantity,
        oi.unit_price,
        CASE 
            WHEN o.invoice_no LIKE 'C%' THEN 'CANCELLATION'
            WHEN oi.quantity < 0 THEN 'RETURN'
            ELSE 'ADJUSTMENT'
        END AS adjustment_type,
        DECODE(
            SIGN(oi.quantity),
            -1, 'Customer Returned Quantity',
            0,  'Zero Quantity Entry Cleared',
            'Invoice Cancellation Notice'
        ) AS reason,
        SYSTIMESTAMP
    FROM ORDERS o
    JOIN ORDER_ITEMS oi ON o.invoice_no = oi.invoice_no
    WHERE o.is_cancellation = 1 OR oi.quantity <= 0;
    
    v_rows_adjusted := SQL%ROWCOUNT;
    COMMIT;
    
    DBMS_OUTPUT.PUT_LINE('[ETL] Successfully archived ' || v_rows_adjusted || ' transaction adjustments.');
END;
/

-- 3. Procedure: Populate Normalized Descriptions across PRODUCTS
CREATE OR REPLACE PROCEDURE sp_normalize_product_catalog IS
BEGIN
    UPDATE PRODUCTS
    SET normalized_description = fn_clean_description(original_description)
    WHERE normalized_description IS NULL AND original_description IS NOT NULL;
    
    COMMIT;
    DBMS_OUTPUT.PUT_LINE('[ETL] Product catalog descriptions normalized.');
END;
/

PROMPT [INSYTE ETL] In-database ETL procedures successfully compiled.

-- ==============================================================================
-- INSYTE: 03_sequences.sql
-- Oracle 23ai Sequences for Surrogate Key Generation
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE SEQUENCES] Initializing Database Sequences...

-- 1. Order Items Sequence (Generates item_id)
BEGIN
    EXECUTE IMMEDIATE 'DROP SEQUENCE order_item_seq';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -2289 THEN RAISE; END IF;
END;
/
CREATE SEQUENCE order_item_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- 2. Review Media Sequence (Generates media_id)
BEGIN
    EXECUTE IMMEDIATE 'DROP SEQUENCE review_media_seq';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -2289 THEN RAISE; END IF;
END;
/
CREATE SEQUENCE review_media_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- 3. Transaction Adjustments Sequence (Generates adjustment_id)
BEGIN
    EXECUTE IMMEDIATE 'DROP SEQUENCE adj_seq';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -2289 THEN RAISE; END IF;
END;
/
CREATE SEQUENCE adj_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- 4. ETL Audit Sequence (Generates audit_id)
BEGIN
    EXECUTE IMMEDIATE 'DROP SEQUENCE audit_seq';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -2289 THEN RAISE; END IF;
END;
/
CREATE SEQUENCE audit_seq
    START WITH 1
    INCREMENT BY 1
    NOCACHE
    NOCYCLE;

-- 5. Reviews Sequence (For auto-generating surrogate review IDs when not in raw dataset)
BEGIN
    EXECUTE IMMEDIATE 'DROP SEQUENCE review_seq';
EXCEPTION WHEN OTHERS THEN IF SQLCODE != -2289 THEN RAISE; END IF;
END;
/
CREATE SEQUENCE review_seq
    START WITH 100001
    INCREMENT BY 1
    CACHE 50
    NOCYCLE;

PROMPT [INSYTE SEQUENCES] Sequences configured successfully.

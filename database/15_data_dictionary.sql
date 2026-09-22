-- ==============================================================================
-- INSYTE: 15_data_dictionary.sql
-- Oracle 23ai Data Dictionary Introspection & Schema Audit Views
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE DICTIONARY] Constructing Schema Introspection Views...

-- 1. Schema Tables & Storage Audit View
CREATE OR REPLACE VIEW V_DICT_TABLES AS
SELECT 
    table_name,
    num_rows,
    blocks,
    avg_row_len,
    tablespace_name,
    last_analyzed
FROM USER_TABLES
ORDER BY table_name;

-- 2. Columns & Data Types Audit View
CREATE OR REPLACE VIEW V_DICT_COLUMNS AS
SELECT 
    table_name,
    column_id,
    column_name,
    data_type || 
    CASE 
        WHEN data_type IN ('VARCHAR2', 'CHAR') THEN '(' || data_length || ')'
        WHEN data_type = 'NUMBER' AND data_precision IS NOT NULL THEN '(' || data_precision || ',' || data_scale || ')'
        ELSE ''
    END AS formatted_type,
    nullable,
    data_default
FROM USER_TAB_COLUMNS
ORDER BY table_name, column_id;

-- 3. Constraints & Foreign Keys Audit View
CREATE OR REPLACE VIEW V_DICT_CONSTRAINTS AS
SELECT 
    c.constraint_name,
    c.table_name,
    DECODE(c.constraint_type, 
        'P', 'PRIMARY_KEY',
        'R', 'FOREIGN_KEY',
        'U', 'UNIQUE_KEY',
        'C', 'CHECK_CONSTRAINT',
        c.constraint_type
    ) AS constraint_type,
    cc.column_name,
    c.r_constraint_name AS referenced_pk,
    c.status
FROM USER_CONSTRAINTS c
LEFT JOIN USER_CONS_COLUMNS cc ON c.constraint_name = cc.constraint_name
WHERE c.constraint_name NOT LIKE 'BIN$%'
ORDER BY c.table_name, c.constraint_name;

-- 4. Indexes & Indexed Expressions Audit View
CREATE OR REPLACE VIEW V_DICT_INDEXES AS
SELECT 
    i.index_name,
    i.table_name,
    i.index_type,
    i.uniqueness,
    ic.column_name,
    ic.column_position
FROM USER_INDEXES i
JOIN USER_IND_COLUMNS ic ON i.index_name = ic.index_name
ORDER BY i.table_name, i.index_name, ic.column_position;

-- 5. Materialized Views Audit View
CREATE OR REPLACE VIEW V_DICT_MATERIALIZED_VIEWS AS
SELECT 
    mview_name,
    container_name,
    refresh_mode,
    refresh_method,
    compile_state,
    last_refresh_date
FROM USER_MVIEWS;

-- 6. Sequences Audit View
CREATE OR REPLACE VIEW V_DICT_SEQUENCES AS
SELECT 
    sequence_name,
    min_value,
    max_value,
    increment_by,
    cycle_flag,
    order_flag,
    cache_size,
    last_number
FROM USER_SEQUENCES;

PROMPT [INSYTE DICTIONARY] Data dictionary introspection views ready for evaluation.

-- ==============================================================================
-- INSYTE: 09_json.sql
-- Oracle 23ai Native JSON Capabilities & Document Query Operators
-- Execution: Run as INSYTE_ADMIN on FREEPDB1
-- ==============================================================================

PROMPT [INSYTE JSON] Deploying Oracle Native JSON Functions and Queries...

-- 1. Sample Procedure to Seed Derived JSON Product Attributes
-- Populates structured product attributes (category, color, packaging) when available
CREATE OR REPLACE PROCEDURE sp_enrich_product_json IS
BEGIN
    -- Demonstrates storing valid JSON directly into the binary JSON column
    UPDATE PRODUCTS
    SET metadata = JSON('{
        "category": "Home Decor",
        "subcategory": "Kitchenware",
        "color": "White",
        "material": "Ceramic",
        "packaging": "Gift Box",
        "is_derived": true
    }')
    WHERE stock_code = '85123A' AND metadata IS NULL;

    UPDATE PRODUCTS
    SET metadata = JSON('{
        "category": "Stationery",
        "subcategory": "Craft",
        "color": "Red",
        "material": "Paper",
        "packaging": "Pack of 6",
        "is_derived": true
    }')
    WHERE stock_code = '84879' AND metadata IS NULL;

    COMMIT;
    DBMS_OUTPUT.PUT_LINE('[JSON] Sample product metadata attributes seeded.');
END;
/

-- 2. Demonstration Query 1: Dot-Notation Syntax
-- Oracle 23ai allows intuitive JavaScript/Python-style navigation of JSON trees
-- SELECT p.stock_code, p.metadata.category.string() AS category, p.metadata.color.string() AS color FROM PRODUCTS p;

-- 3. Demonstration Query 2: JSON_EXISTS & JSON_VALUE Predicates
-- Filters products having specific metadata keys with scalar extraction
-- SELECT stock_code, description, JSON_VALUE(metadata, '$.category') AS category
-- FROM PRODUCTS
-- WHERE JSON_EXISTS(metadata, '$.category')
--   AND JSON_VALUE(metadata, '$.color') = 'White';

-- 4. Demonstration Query 3: JSON Aggregation (JSON_OBJECT and JSON_ARRAYAGG)
-- Generates clean, ready-to-consume JSON payloads directly inside Oracle
CREATE OR REPLACE VIEW V_PRODUCT_JSON_EXPORT AS
SELECT 
    JSON_OBJECT(
        'stock_code' VALUE p.stock_code,
        'description' VALUE p.normalized_description,
        'unit_price' VALUE p.unit_price,
        'metadata' VALUE p.metadata,
        'has_embedding' VALUE CASE WHEN p.embedding IS NOT NULL THEN 'YES' ELSE 'NO' END
    ) AS product_document
FROM PRODUCTS p;

PROMPT [INSYTE JSON] Native JSON utilities and view deployed.

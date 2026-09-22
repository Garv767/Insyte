-- ==============================================================================
-- INSYTE: 01_users_roles.sql
-- Oracle 23ai Free Security Architecture & Data Control Language (DCL)
-- Objective: Enforce least-privilege security between Admin and Analyst roles
-- Execution: Run as SYSDBA connected to PDB (FREEPDB1)
-- ==============================================================================

ALTER SESSION SET CONTAINER = FREEPDB1;

PROMPT [INSYTE SECURITY] Initializing Security Roles and Privileges...

-- 1. Create Application Admin User (INSYTE_ADMIN)
-- Owns all application schemas, tables, sequences, indexes, and materialized views
BEGIN
    EXECUTE IMMEDIATE 'CREATE USER INSYTE_ADMIN IDENTIFIED BY "AdminSecurePassword2026!"
                       DEFAULT TABLESPACE USERS
                       TEMPORARY TABLESPACE TEMP
                       QUOTA UNLIMITED ON USERS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE = -1920 THEN
            NULL; -- User already exists
        ELSE
            RAISE;
        END IF;
END;
/

-- Grant Administrative System Privileges
GRANT CREATE SESSION TO INSYTE_ADMIN;
GRANT CREATE TABLE TO INSYTE_ADMIN;
GRANT CREATE VIEW TO INSYTE_ADMIN;
GRANT CREATE MATERIALIZED VIEW TO INSYTE_ADMIN;
GRANT CREATE SEQUENCE TO INSYTE_ADMIN;
GRANT CREATE SYNONYM TO INSYTE_ADMIN;
GRANT CREATE PROCEDURE TO INSYTE_ADMIN;
GRANT CREATE TRIGGER TO INSYTE_ADMIN;
GRANT CREATE MINING MODEL TO INSYTE_ADMIN; -- For AI/Vector capabilities

-- 2. Create Reporting Analyst Role (INSYTE_ANALYST_ROLE)
-- Demonstrates enterprise least-privilege segregation (Read-only access)
BEGIN
    EXECUTE IMMEDIATE 'CREATE ROLE INSYTE_ANALYST_ROLE';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE = -1921 THEN
            NULL; -- Role already exists
        ELSE
            RAISE;
        END IF;
END;
/

-- 3. Create Restricted Reporting User (INSYTE_ANALYST)
BEGIN
    EXECUTE IMMEDIATE 'CREATE USER INSYTE_ANALYST IDENTIFIED BY "AnalystSecurePassword2026!"
                       DEFAULT TABLESPACE USERS
                       TEMPORARY TABLESPACE TEMP
                       QUOTA 0M ON USERS';
EXCEPTION
    WHEN OTHERS THEN
        IF SQLCODE = -1920 THEN
            NULL; -- User already exists
        ELSE
            RAISE;
        END IF;
END;
/

GRANT CREATE SESSION TO INSYTE_ANALYST;
GRANT INSYTE_ANALYST_ROLE TO INSYTE_ANALYST;

-- 4. Grant Selective Object Privileges to INSYTE_ANALYST_ROLE
-- The reporting user CANNOT perform INSERT, UPDATE, DELETE, ALTER, or DROP
GRANT SELECT ON INSYTE_ADMIN.CUSTOMERS TO INSYTE_ANALYST_ROLE;
GRANT SELECT ON INSYTE_ADMIN.PRODUCTS TO INSYTE_ANALYST_ROLE;
GRANT SELECT ON INSYTE_ADMIN.ORDERS TO INSYTE_ANALYST_ROLE;
GRANT SELECT ON INSYTE_ADMIN.ORDER_ITEMS TO INSYTE_ANALYST_ROLE;
GRANT SELECT ON INSYTE_ADMIN.REVIEWS TO INSYTE_ANALYST_ROLE;
GRANT SELECT ON INSYTE_ADMIN.REVIEW_MEDIA TO INSYTE_ANALYST_ROLE;
GRANT SELECT ON INSYTE_ADMIN.TRANSACTION_ADJUSTMENTS TO INSYTE_ANALYST_ROLE;
GRANT SELECT ON INSYTE_ADMIN.ETL_AUDIT TO INSYTE_ANALYST_ROLE;

-- 5. Create Private Synonyms for Convenient Reporting
-- Prevents hardcoding schema prefixes in reporting queries
CREATE OR REPLACE SYNONYM INSYTE_ANALYST.sales_orders FOR INSYTE_ADMIN.ORDERS;
CREATE OR REPLACE SYNONYM INSYTE_ANALYST.order_items FOR INSYTE_ADMIN.ORDER_ITEMS;
CREATE OR REPLACE SYNONYM INSYTE_ANALYST.catalog_products FOR INSYTE_ADMIN.PRODUCTS;
CREATE OR REPLACE SYNONYM INSYTE_ANALYST.customer_directory FOR INSYTE_ADMIN.CUSTOMERS;
CREATE OR REPLACE SYNONYM INSYTE_ANALYST.customer_reviews FOR INSYTE_ADMIN.REVIEWS;

PROMPT [INSYTE SECURITY] Users, roles, and privileges configured successfully.

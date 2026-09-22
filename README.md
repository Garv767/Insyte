# INSYTE — E-Commerce Customer Behaviour Analytics

> **Enterprise-Grade, Database-Centric Customer Intelligence Platform Powered by Oracle Database 23ai Free**

[![Oracle 23ai](https://img.shields.io/badge/Oracle-23ai%20Free-red.svg)](https://www.oracle.com/database/free/)
[![Docker](https://img.shields.io/badge/Docker-Compose-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://palletsprojects.com/p/flask/)
[![Vector Search](https://img.shields.io/badge/AI%20Vector-384--dim%20Cosine-purple.svg)](https://docs.oracle.com/en/database/oracle/oracle-database/23/vecse/)

---

## 1. Project Overview

**INSYTE** is an advanced academic and commercial database analytics system designed around Online Retail and E-Commerce transactional datasets (UCI Online Retail / Online Retail II structure), enhanced with customer review texts, ratings, and media asset tracking.

Unlike traditional web applications that offload analytics to Python or pandas memory, **INSYTE is strictly database-centric**:
- **Zero External ML Clustering:** Customer RFM segmentation is calculated natively inside Oracle SQL using analytic window functions (`NTILE(5)` over partitioned orders).
- **In-Database Cohort Modeling:** Retention matrices and customer lifecycle offsets are executed entirely within SQL using `MIN() OVER` and `MONTHS_BETWEEN()`.
- **Modern Oracle 23ai Innovations:** Leverages native `VECTOR(384, FLOAT32)` data types with cosine distance similarity (`VECTOR_DISTANCE`) and binary `JSON` attributes with dot-notation query execution.
- **Enterprise Security & Governance:** Implements Oracle Data Control Language (DCL) enforcing least-privilege role segregation between `INSYTE_ADMIN` and `INSYTE_ANALYST`.
- **Transparent Academic Evaluation:** Includes an in-app **SQL Insights** viewer detailing exact SQL syntax, bind parameters, execution durations, `EXPLAIN PLAN` tree structures, and live data dictionary introspection (`USER_TABLES`, `USER_CONSTRAINTS`, `USER_INDEXES`, `USER_MVIEWS`).

---

## 2. Deployment Architecture & Portability Strategy

INSYTE is designed for seamless, 1-click migration between a local development machine and a cloud droplet (e.g. DigitalOcean). All host and network configurations are decoupled via environment variables.

```
Browser (Interactive Web Dashboard)
      │
      ▼ HTTP / JSON
Flask Application & Connection Pool (python-oracledb Thin Mode)
      │
      ▼ Port 1521 (FREEPDB1)
Docker Container (container-registry.oracle.com/database/free:latest)
      ├── Storage: Persistent Mount (./oradata -> /opt/oracle/oradata)
      ├── Security: INSYTE_ADMIN (DDL/DML) & INSYTE_ANALYST (Read-Only)
      ├── Core Relational: CUSTOMERS, PRODUCTS, ORDERS, ORDER_ITEMS
      ├── Reviews & Media: REVIEWS, REVIEW_MEDIA
      ├── Native AI: VECTOR(384, FLOAT32) & HNSW Cosine Index
      ├── Native JSON: Dynamic Product Specs & Dot-Notation
      └── In-Database Compute: RFM Window Functions, Cohorts, Materialized Views
```

### Localhost vs DigitalOcean Configuration

To migrate to DigitalOcean:
1. Deploy `docker-compose.yml` to the Droplet.
2. In `.env`, change `DB_HOST=localhost` to `DB_HOST=<DROPLET_PUBLIC_IP>` (or the Docker network service name `oracle-db`).
3. No source code changes are required.

---

## 3. The 7 Core Application Modules

1. **Overview:** Executive summary displaying Gross Sales, Cancellations, Net Revenue, Units Sold, Average Order Value (AOV), monthly revenue trends, customer segment breakdowns, and SQL-derived business insights.
2. **Customer Analytics:** Comprehensive RFM segmentation (`Champions`, `Loyal`, `Potential Loyalists`, `Recent`, `At Risk`, `Lost`), RFM heatmaps, customer lifetime spend distributions, and customer drill-down drawers.
3. **Product Analytics:** Best-selling products by revenue and units, price elasticity distributions, product detail views, and dynamic attributes parsed from Oracle JSON.
4. **Sales & Trends:** Multi-granularity revenue and order volume trends, country performance maps, and complete customer cohort retention matrices.
5. **Reviews & Media:** Combined transactional and sentiment analytics, star rating distributions, media attachment rates (images/video links), and visual media galleries.
6. **Product Health:** Commercial health matrix (`HEALTHY`, `WATCH`, `AT_RISK`) correlating sales velocity against return rates and customer sentiment.
7. **SQL Insights:** Interactive evaluator console allowing inspection of all underlying queries, execution times, `EXPLAIN PLAN` diagrams, and data dictionary audits.

---

## 4. Database Schema & Dynamic Mapping Layer

### Dynamic Column Mapping
The ingestion pipeline automatically detects variations in the input data schema and creates a normalized mapping:

| Raw Dataset Field | Canonical Column | Database Table | Description |
| :--- | :--- | :--- | :--- |
| `Invoice` / `InvoiceNo` | `invoice_no` | `ORDERS`, `ORDER_ITEMS` | Handles cancellation prefixes (`C%`). |
| `StockCode` / `sku` | `stock_code` | `PRODUCTS`, `ORDER_ITEMS` | Alphanumeric product identifier. |
| `Description` | `original_description` | `PRODUCTS` | Preserved raw and normalized via REGEXP. |
| `Quantity` | `quantity` | `ORDER_ITEMS` | Negative quantities moved to `TRANSACTION_ADJUSTMENTS`. |
| `InvoiceDate` | `invoice_date` | `ORDERS` | `TIMESTAMP WITH TIME ZONE`. |
| `Price` / `UnitPrice` | `unit_price` | `ORDER_ITEMS`, `PRODUCTS` | Preserved at order item level. |
| `Customer ID` | `customer_id` | `CUSTOMERS`, `ORDERS` | Null customer IDs tracked as Guest orders. |
| `Country` | `country` | `CUSTOMERS`, `ORDERS` | Normalized geographic attribute. |
| `Review Text` | `review_text` | `REVIEWS` | Textual feedback (optional). |
| `Rating` | `rating` | `REVIEWS` | 1-to-5 star rating (optional). |
| `Media URL` | `media_url` | `REVIEW_MEDIA` | Image/Video link (optional). |

---

## 5. Quickstart & Local Setup

### Step 1: Clone Repository & Configure Environment
```bash
git clone https://github.com/Garv767/Insyte.git
cd Insyte
copy .env.example .env
```

### Step 2: Start Oracle Database 23ai Free Container
```bash
docker compose up -d
```
*Note: Oracle 23ai initializes within 1–2 minutes. Storage is automatically persisted inside `./oradata`.*

### Step 3: Install Python Dependencies
```bash
python -m venv venv
venv\Scripts\activate     # Windows
pip install -r requirements.txt
```

### Step 4: Verify Database Connectivity
```bash
python scripts/test_connection.py
```

### Step 5: Execute Database Initialization Scripts
Connect via SQLcl, SQL Developer, or Python and execute:
```sql
@database/security/01_users_roles.sql
@database/schema/02_schema.sql
```

---

## 6. Academic & Viva Demonstration Highlights

- **SQL Window Functions:** `NTILE(5)` for RFM segmentation, `ROW_NUMBER()` / `DENSE_RANK()` for product tiering, `SUM(...) OVER` running totals.
- **Set Operators:** `MINUS` to detect customer churn between fiscal quarters; `UNION` for combining active and guest segments.
- **Oracle JSON:** Dot-notation queries and `JSON_VALUE` / `JSON_EXISTS` predicates on `PRODUCTS.metadata`.
- **Oracle AI Vector Search:** Native 384-dimensional cosine distance similarity via `VECTOR_DISTANCE(embedding, :query_vec, COSINE)`.
- **Materialized Views:** Precomputed aggregations via `MV_CUSTOMER_RFM_SUMMARY` and `MV_MONTHLY_REVENUE_TRENDS`.
- **Execution Plan:** In-app inspection of cost, estimated rows, and index scans via `EXPLAIN PLAN`.

---

## 7. License & Academic Integrity
Developed as an advanced database architecture and behavioral analytics demonstration. All source queries and designs adhere strictly to reproducible SQL standards without synthetic or fabricated data.

# INSYTE — E-Commerce Customer Behaviour Analytics

> **Enterprise-Grade, Database-Centric Customer Intelligence Platform Powered by Oracle Cloud Infrastructure (OCI) Autonomous AI Database (26ai Serverless)**

[![Oracle AI Database](https://img.shields.io/badge/Oracle-Autonomous%20AI%2026ai%20Serverless-red.svg)](https://www.oracle.com/autonomous-database/)
[![OCI Cloud Serverless](https://img.shields.io/badge/OCI-Cloud%20Serverless%20(ap--hyderabad--1)-orange.svg)](https://cloud.oracle.com/)
[![Security](https://img.shields.io/badge/Security-mTLS%20Wallet%20TCPS-green.svg)](https://docs.oracle.com/en-us/iaas/autonomous-database-serverless/doc/connect-preparing.html)
[![Python](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-blue.svg)](https://palletsprojects.com/p/flask/)
[![Vector Search](https://img.shields.io/badge/AI%20Vector-384--dim%20Cosine-purple.svg)](https://docs.oracle.com/en/database/oracle/oracle-database/23/vecse/)

---

## 1. Project Overview

**INSYTE** is an enterprise-grade academic and commercial database analytics system designed around Online Retail and E-Commerce transactional datasets (UCI Online Retail / Online Retail II structure), enhanced with customer review texts, ratings, and media asset tracking.

Unlike conventional web applications that load bulk tables into memory and perform calculations in Python or pandas, **INSYTE is strictly database-centric**:
- **Zero External ML Clustering:** Customer RFM segmentation is computed natively inside Oracle SQL using analytic window functions (`NTILE(5)` over partitioned customer transactions).
- **In-Database Cohort Modeling:** Retention matrices, customer lifecycle offsets, and active churn states execute entirely within SQL via `MIN() OVER` and `MONTHS_BETWEEN()`.
- **Modern Oracle 26ai Innovations:** Employs native `VECTOR(384, FLOAT32)` data types with cosine distance similarity (`VECTOR_DISTANCE`) and binary `JSON` attributes with dot-notation query execution.
- **Enterprise Security & Governance:** Enforces Oracle Data Control Language (DCL) least-privilege role segregation between Administrative operations and read-only Analytical querying (`INSYTE_ANALYST`).
- **Transparent Academic Evaluation:** Built-in **SQL Insights** evaluator exposes live query text, bind variables, execution durations, hierarchical `EXPLAIN PLAN` tree structures, and live data dictionary introspection (`USER_TABLES`, `USER_CONSTRAINTS`, `USER_INDEXES`, `USER_MVIEWS`).

---

## 2. Cloud Architecture: OCI Autonomous AI Database (26ai Serverless)

The platform is deployed against **Oracle Cloud Infrastructure (OCI) Autonomous AI Database (26ai Serverless)** in region `ap-hyderabad-1`, utilizing Mutual TLS (mTLS) certificate wallets for encrypted enterprise communication.

```
┌─────────────────────────────────────────────────────────────┐
│                 Browser Client (Dashboard)                  │
└──────────────────────────────┬──────────────────────────────┘
                               │ HTTP / JSON
                               ▼
┌─────────────────────────────────────────────────────────────┐
│               Flask Web Application (Port 5000)             │
│        app/config.py  │  app/database.py Connection Pool     │
│             python-oracledb Driver (Thin Mode)              │
└──────────────────────────────┬──────────────────────────────┘
                               │ Mutual TLS (mTLS) / TCPS :1522
                               │ Client Credentials Wallet (cwallet.sso)
                               ▼
┌─────────────────────────────────────────────────────────────┐
│      OCI Autonomous AI Database Serverless (26ai Cloud)     │
│                  Service Profile: insyte_high               │
│               PDB: GA7D40B1C599299_INSYTE                   │
│                                                             │
│  ├── Relational Core: CUSTOMERS, PRODUCTS, ORDERS, ITEMS    │
│  ├── Reviews & Media: REVIEWS, REVIEW_MEDIA                 │
│  ├── Adjustments Audit: TRANSACTION_ADJUSTMENTS, ETL_AUDIT  │
│  ├── AI Vector Engine: VECTOR(384, FLOAT32) & Cosine Metric │
│  ├── Native JSON Store: Dynamic Product Spec Attributes     │
│  ├── Analytical MVs: MV_MONTHLY_REVENUE_TRENDS, RFM_SUMMARY │
│  └── In-Database Compute: NTILE(5), Cohorts, Running Totals │
└─────────────────────────────────────────────────────────────┘
```

### OCI Autonomous TNS Profiles
Connections utilize Oracle Net Services with pre-configured workload profiles defined in `wallet/tnsnames.ora`:
- **`insyte_high`** *(Default)*: Highest parallelism and system resources, optimal for heavy analytical aggregations, cohort queries, and batch ETL.
- **`insyte_medium`**: Balanced concurrency and resource allocation.
- **`insyte_low`**: High concurrency for lightweight, single-row lookups.

---

## 3. The 7 Core Application Modules

1. **Overview:** Executive summary displaying Gross Sales, Cancellations, Net Revenue, Units Sold, Average Order Value (AOV), monthly revenue trends, customer segment distributions, and automated SQL-derived business insights.
2. **Customer Analytics:** Complete RFM segmentation (`Champions`, `Loyal`, `Potential Loyalists`, `Recent`, `At Risk`, `Lost`), RFM score distribution heatmaps, customer lifetime spend histograms, and detailed customer drill-down views.
3. **Product Analytics:** Best-selling products ranked by revenue and units, price elasticity distributions, product detail views, dynamic specs parsed from Oracle JSON, and AI-powered semantic similarity.
4. **Sales & Trends:** Multi-granularity revenue and order volume trends, geographic sales distributions, and complete customer cohort retention matrices.
5. **Reviews & Media:** Combined transactional and sentiment analytics, rating distributions, media attachment rates (image/video links), and visual media galleries.
6. **Product Health:** Commercial health matrix (`HEALTHY`, `WATCH`, `AT_RISK`) correlating sales volume against return rates, cancellations, and customer sentiment.
7. **SQL Insights:** Live query inspection console showing exact SQL queries, bind parameters, execution durations in milliseconds, `EXPLAIN PLAN` diagrams, and data dictionary audits.

---

## 4. Database Schema & Dynamic Mapping Layer

### Core Database Entities

| Table Name | Description | Key Innovations |
| :--- | :--- | :--- |
| `CUSTOMERS` | Master customer directory | First-seen cohort derivation, RFM score assignment |
| `PRODUCTS` | Product catalogue with metadata | `JSON` attributes for specs, `VECTOR(384, FLOAT32)` for semantic search |
| `ORDERS` | Transactional order headers | Status handling (`COMPLETED`, `CANCELLED`), temporal indexing |
| `ORDER_ITEMS` | Line item transactional records | Composite B-Tree indexes, integrity constraints |
| `REVIEWS` | Customer feedback & sentiment | Star ratings, sentiment flags, normalized text |
| `REVIEW_MEDIA` | User-generated media assets | Image/video URL tracking, verification badges |
| `TRANSACTION_ADJUSTMENTS` | Audit trail for negative adjustments | Isolates refunds, damaged items, cancellations |
| `ETL_AUDIT` | Batch pipeline execution metrics | Execution times, processed row counts, status |

### Materialized Views
- **`MV_MONTHLY_REVENUE_TRENDS`**: Precomputes monthly gross revenue, net revenue, cancelled volume, and active customer counts with fast refresh capability.
- **`MV_CUSTOMER_RFM_SUMMARY`**: Materializes customer recency, frequency, monetary value, and tier assignments for sub-millisecond dashboard queries.

### Dynamic Column Mapping
The ingestion pipeline automatically inspects incoming dataset headers and maps them to canonical database fields:

| Raw Dataset Field | Canonical Column | Target Table | Handling & Cleansing |
| :--- | :--- | :--- | :--- |
| `Invoice` / `InvoiceNo` | `invoice_no` | `ORDERS`, `ORDER_ITEMS` | Detects cancellation prefixes (`C%`) |
| `StockCode` / `sku` | `stock_code` | `PRODUCTS`, `ORDER_ITEMS` | Normalized alphanumeric product code |
| `Description` | `original_description` | `PRODUCTS` | Preserved raw; normalized via REGEXP |
| `Quantity` | `quantity` | `ORDER_ITEMS` | Negative quantities tracked as adjustments |
| `InvoiceDate` | `invoice_date` | `ORDERS` | `TIMESTAMP WITH TIME ZONE` |
| `Price` / `UnitPrice` | `unit_price` | `ORDER_ITEMS`, `PRODUCTS` | Preserved at order item level |
| `Customer ID` | `customer_id` | `CUSTOMERS`, `ORDERS` | Null customer IDs tracked as Guest orders |
| `Country` | `country` | `CUSTOMERS`, `ORDERS` | Standardized geographic attribute |
| `Review Text` | `review_text` | `REVIEWS` | Customer textual review (optional) |
| `Rating` | `rating` | `REVIEWS` | 1-to-5 star rating (optional) |
| `Media URL` | `media_url` | `REVIEW_MEDIA` | Verified media link (optional) |

---

## 5. Quickstart & Setup Guide

### Prerequisites
- Python 3.11+
- Git
- Oracle Cloud Infrastructure (OCI) Autonomous Database client credentials wallet (`Wallet_INSYTE.zip`)

### Step 1: Clone Repository & Configure Environment
```powershell
git clone https://github.com/Garv767/Insyte.git
cd Insyte
copy .env.example .env
```

### Step 2: Extract OCI Autonomous Database Wallet
Place `Wallet_INSYTE.zip` in the project root and extract into the `wallet/` directory:
```powershell
python -c "import zipfile; zipfile.ZipFile('Wallet_INSYTE.zip').extractall('wallet')"
```

Verify that the following files exist in `wallet/`:
- `cwallet.sso`, `ewallet.p12`, `tnsnames.ora`, `sqlnet.ora`

### Step 3: Configure Environment Variables (.env)
Edit `.env` with your Autonomous Database credentials:
```env
# Autonomous Database Credentials
DB_USER=ADMIN
DB_PASSWORD=your_secure_password

# OCI Autonomous Database Wallet Configuration
TNS_NAME=insyte_high
WALLET_DIR=./wallet
WALLET_PASSWORD=your_secure_password

# Flask Web Server
FLASK_APP=app/app.py
FLASK_ENV=development
FLASK_PORT=5000
FLASK_DEBUG=1
SECRET_KEY=insyte_secret_key_oracle23ai_academic_2026

# AI Vector Embeddings
EMBEDDING_MODEL=all-MiniLM-L6-v2
EMBEDDING_DIM=384
```

### Step 4: Install Python Dependencies
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 5: Test Database Connectivity
Run the connection verification script to confirm mTLS communication with OCI Autonomous Database:
```powershell
python scripts/test_connection.py
```
*Expected output: `[SUCCESS] Connected successfully to Oracle Database!` reporting Oracle AI Database 26ai Enterprise Edition.*

### Step 6: Deploy Database Schema & Analytical Views
Execute the automated DDL initialization script:
```powershell
python scripts/initialize_db.py
```
This deploys all 8 relational tables, 5 sequences, 2 materialized views, and 16 analytical views.

### Step 7: Ingest Dataset & Generate Vector Embeddings
1. Place your raw dataset (e.g. `online_retail_II.csv`) inside `data/raw/`.
2. Run data ingestion:
   ```powershell
   python scripts/import_data.py data/raw/online_retail_II.csv
   ```
3. Generate AI vector embeddings for products:
   ```powershell
   python scripts/generate_embeddings.py
   ```
4. Validate data quality and generate audit report:
   ```powershell
   python scripts/validate_data.py
   ```

### Step 8: Launch the Analytics Dashboard
```powershell
python app/app.py
```
Open your browser and navigate to:
```
http://localhost:5000
```

---

## 6. Academic & Viva Demonstration Highlights

- **SQL Window Functions:** `NTILE(5)` for RFM segmentation, `ROW_NUMBER()` / `DENSE_RANK()` for product tiering, `SUM(...) OVER` running totals.
- **Set Operators:** `MINUS` to detect customer churn between fiscal quarters; `UNION` for combining active and guest segments.
- **Oracle JSON:** Dot-notation queries and `JSON_VALUE` / `JSON_EXISTS` predicates on `PRODUCTS.metadata`.
- **Oracle AI Vector Search:** Native 384-dimensional cosine distance similarity via `VECTOR_DISTANCE(embedding, :query_vec, COSINE)`.
- **Materialized Views:** Precomputed aggregations via `MV_CUSTOMER_RFM_SUMMARY` and `MV_MONTHLY_REVENUE_TRENDS`.
- **Execution Plan:** In-app inspection of cost, estimated rows, and index scans via `EXPLAIN PLAN`.
- **Data Dictionary Introspection:** Direct querying of `USER_TABLES`, `USER_TAB_COLUMNS`, `USER_INDEXES`, and `USER_MVIEWS`.

---

## 7. Security & Credential Protection

- **Encrypted Transmission:** All client-database communications run over secure Mutual TLS (mTLS) on TCPS port 1522.
- **Credential Protection:** Wallet keys (`*.sso`, `*.p12`, `*.jks`, `*.pem`, `Wallet_*.zip`) and `.env` files are strictly excluded from version control via `.gitignore`.
- **Role-Based Privilege Separation:** Schema design supports dual administrative (`ADMIN`) and read-only analytical (`INSYTE_ANALYST`) execution contexts.

---

## 8. License & Academic Integrity
Developed as an advanced database architecture and behavioral analytics demonstration. All source queries and designs adhere strictly to reproducible SQL standards without synthetic or fabricated data.

# INSYTE — E-Commerce Customer Behaviour Analytics

> **Enterprise-Grade, Database-Centric Customer Intelligence Platform Powered by Oracle AI Database (Autonomous AI 26ai / 23ai Free)**

[![Oracle AI Database](https://img.shields.io/badge/Oracle-Autonomous%20AI%2026ai%20%2F%2023ai-red.svg)](https://www.oracle.com/autonomous-database/)
[![OCI Cloud Serverless](https://img.shields.io/badge/OCI-Autonomous%20Serverless-orange.svg)](https://cloud.oracle.com/)
[![Docker](https://img.shields.io/badge/Docker-Compose%20Ready-blue.svg)](https://www.docker.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-yellow.svg)](https://www.python.org/)
[![Flask](https://img.shields.io/badge/Flask-3.0+-green.svg)](https://palletsprojects.com/p/flask/)
[![Vector Search](https://img.shields.io/badge/AI%20Vector-384--dim%20Cosine-purple.svg)](https://docs.oracle.com/en/database/oracle/oracle-database/23/vecse/)

---

## 1. Project Overview

**INSYTE** is an advanced academic and commercial database analytics system designed around Online Retail and E-Commerce transactional datasets (UCI Online Retail / Online Retail II structure), enhanced with customer review texts, ratings, and media asset tracking.

Unlike traditional web applications that offload analytics to Python or pandas memory, **INSYTE is strictly database-centric**:
- **Zero External ML Clustering:** Customer RFM segmentation is calculated natively inside Oracle SQL using analytic window functions (`NTILE(5)` over partitioned orders).
- **In-Database Cohort Modeling:** Retention matrices and customer lifecycle offsets are executed entirely within SQL using `MIN() OVER` and `MONTHS_BETWEEN()`.
- **Modern Oracle AI Database Innovations:** Leverages native `VECTOR(384, FLOAT32)` data types with cosine distance similarity (`VECTOR_DISTANCE`) and binary `JSON` attributes with dot-notation query execution.
- **Enterprise Security & Governance:** Implements Oracle Data Control Language (DCL) enforcing least-privilege role segregation between `INSYTE_ADMIN` and `INSYTE_ANALYST`.
- **Transparent Academic Evaluation:** Includes an in-app **SQL Insights** viewer detailing exact SQL syntax, bind parameters, execution durations, `EXPLAIN PLAN` tree structures, and live data dictionary introspection (`USER_TABLES`, `USER_CONSTRAINTS`, `USER_INDEXES`, `USER_MVIEWS`).

---

## 2. Deployment Architecture & Portability Strategy

INSYTE features a **dual-mode deployment architecture**, allowing seamless switching between Oracle Cloud Infrastructure (OCI) Autonomous Database Serverless and a local Docker container:

```
Browser (Interactive Web Dashboard)
      │
      ▼ HTTP / JSON
Flask Application & Connection Pool (python-oracledb Thin Mode)
      │
      ├── Mode 1: OCI Autonomous AI Database Serverless (Production Cloud)
      │     ├── Connection: Mutual TLS (mTLS) via Client Credentials Wallet
      │     ├── Service Profiles: insyte_high, insyte_medium, insyte_low
      │     └── Host: adb.ap-hyderabad-1.oraclecloud.com:1522
      │
      └── Mode 2: Local Docker Container (Oracle Database 23ai Free)
            ├── Connection: TCP Port 1521 (FREEPDB1)
            └── Storage: Persistent Volume Mount (./oradata -> /opt/oracle/oradata)
```

### Decoupled Connection Layer
All database configuration parameters reside in `.env`, handled transparently by `app/config.py` and `app/database.py`:
- When `WALLET_DIR` contains client credentials (`cwallet.sso`, `tnsnames.ora`), the driver automatically connects via **mTLS** to Autonomous Database.
- When `WALLET_DIR` is omitted or empty, the driver falls back to standard host/port/service TCP connection (ideal for local Docker or DigitalOcean self-hosted instances).

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
- `MV_MONTHLY_REVENUE_TRENDS`: Precomputes monthly gross revenue, net revenue, cancelled volume, and active customer counts with fast refresh capability.
- `MV_CUSTOMER_RFM_SUMMARY`: Materializes customer recency, frequency, monetary value, and tier assignments for sub-millisecond dashboard queries.

---

## 5. Quickstart & Setup Guide

### Prerequisites
- Python 3.11+
- Git
- Oracle Autonomous Database Wallet (OCI) OR Docker Engine (for local 23ai Free)

### Step 1: Clone Repository & Configure Environment
```bash
git clone https://github.com/Garv767/Insyte.git
cd Insyte
copy .env.example .env
```

### Step 2: Configure Database Credentials (.env)

#### Option A: Oracle Cloud Autonomous Database (Recommended)
1. Download your Autonomous Database client credentials zip (`Wallet_INSYTE.zip`) from OCI Console.
2. Extract the contents into the `wallet/` directory:
   ```powershell
   python -c "import zipfile; zipfile.ZipFile('Wallet_INSYTE.zip').extractall('wallet')"
   ```
3. Set your credentials in `.env`:
   ```env
   DB_USER=ADMIN
   DB_PASSWORD=your_secure_password
   TNS_NAME=insyte_high
   WALLET_DIR=./wallet
   WALLET_PASSWORD=your_secure_password
   ```

#### Option B: Local Oracle Database 23ai Free (Docker)
1. Start the container:
   ```bash
   docker compose up -d
   ```
2. Configure `.env` for direct TCP:
   ```env
   DB_HOST=localhost
   DB_PORT=1521
   DB_SERVICE=FREEPDB1
   DB_USER=INSYTE_ADMIN
   DB_PASSWORD=your_password
   # WALLET_DIR left commented out
   ```

### Step 3: Install Dependencies
```powershell
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
```

### Step 4: Verify Database Connectivity
```powershell
python scripts/test_connection.py
```

### Step 5: Deploy Schema & Objects
Deploy all DDL, sequences, materialized views, and analytical views:
```powershell
python scripts/initialize_db.py
```

### Step 6: Ingest Dataset & Generate Vectors
1. Place your raw dataset (e.g. `online_retail_II.csv`) inside `data/raw/`.
2. Run data ingestion:
   ```powershell
   python scripts/import_data.py data/raw/online_retail_II.csv
   ```
3. Generate AI vector embeddings for products:
   ```powershell
   python scripts/generate_embeddings.py
   ```
4. Validate data quality:
   ```powershell
   python scripts/validate_data.py
   ```

### Step 7: Launch the Analytics Dashboard
```powershell
python app/app.py
```
Open your browser and navigate to `http://localhost:5000`.

---

## 6. Academic & Viva Demonstration Highlights

- **SQL Window Functions:** `NTILE(5)` for RFM segmentation, `ROW_NUMBER()` / `DENSE_RANK()` for product tiering, `SUM(...) OVER` running totals.
- **Set Operators:** `MINUS` to detect customer churn between fiscal quarters; `UNION` for combining active and guest segments.
- **Oracle JSON:** Dot-notation queries and `JSON_VALUE` / `JSON_EXISTS` predicates on `PRODUCTS.metadata`.
- **Oracle AI Vector Search:** Native 384-dimensional cosine distance similarity via `VECTOR_DISTANCE(embedding, :query_vec, COSINE)`.
- **Materialized Views:** Precomputed aggregations via `MV_CUSTOMER_RFM_SUMMARY` and `MV_MONTHLY_REVENUE_TRENDS`.
- **Execution Plan:** In-app inspection of cost, estimated rows, and index scans via `EXPLAIN PLAN`.

---

## 7. Security & Credential Protection
- All database credentials, tokens, and encryption keys are strictly excluded from version control via `.gitignore`.
- OCI Wallet files (`*.sso`, `*.p12`, `*.jks`, `*.pem`, `Wallet_*.zip`) and local database storage (`oradata/`) are permanently ignored.
- Dual database roles (`INSYTE_ADMIN` and `INSYTE_ANALYST`) ensure the web application can operate under least-privilege principles.

---

## 8. License & Academic Integrity
Developed as an advanced database architecture and behavioral analytics demonstration. All source queries and designs adhere strictly to reproducible SQL standards without synthetic or fabricated data.

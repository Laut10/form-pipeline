# User Form Data Pipeline

![Python](https://img.shields.io/badge/Python-3.10%2B-blue?logo=python)
![Apache Airflow](https://img.shields.io/badge/Apache%20Airflow-2.9-017CEE?logo=apacheairflow)
![PostgreSQL](https://img.shields.io/badge/PostgreSQL-15%2B-336791?logo=postgresql)
![Docker](https://img.shields.io/badge/Docker-Compose-2496ED?logo=docker)

An end-to-end data engineering pipeline that ingests raw JSON form submissions, validates, cleans and transforms the data, and loads it into PostgreSQL — fully orchestrated with Apache Airflow running in Docker.

---

## What this project demonstrates

| Skill | Implementation |
|---|---|
| Data ingestion | Reads raw JSON (168 records with intentional quality issues) |
| Data validation | Schema checks, null-rate analysis, hard stops on critical failures |
| Data cleaning | Deduplication, email repair, country normalization, date parsing |
| ETL orchestration | 5-task Airflow DAG with retries and task dependencies |
| Data modeling | Separate raw and clean PostgreSQL tables |
| Containerization | Docker Compose with Airflow + dedicated metadata DB |
| Analytics readiness | Post-load metrics: distribution by country, source, quality stats |

---

## Pipeline architecture

```
raw_submissions.json
        │
        ▼
  ┌─────────────┐
  │   extract   │  Loads 168 JSON records into a DataFrame
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │  validate   │  Schema check · null rates · duplicate count
  └──────┬──────┘      (aborts if critical fields are >80% null)
         │
         ▼
  ┌─────────────┐
  │    clean    │  Dedup · fix emails · normalize countries · parse dates
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │    load     │  Upsert into PostgreSQL (ON CONFLICT DO NOTHING)
  └──────┬──────┘
         │
         ▼
  ┌─────────────┐
  │   metrics   │  Queries DB → logs distribution report
  └─────────────┘
```

---

## Data quality issues handled

The raw dataset contains intentional data quality problems that mirror real-world form submissions:

| Issue | Example (raw) | After pipeline |
|---|---|---|
| Duplicate submissions | `form_id: 123` appears twice | First occurrence kept |
| Invalid email | `juan@gmail,com` | `juan@gmail.com` |
| Unrecoverable email | `cristinahotmail.com` | `NULL` |
| Double `@` in email | `user@@yahoo.com` | `user@yahoo.com` |
| Inconsistent country | `ES`, `españa`, `SPAIN`, `esp` | `España` |
| Mixed date formats | `05/04/25`, `April 05, 2025`, `2025-07-10` | `2025-04-05` |
| Mixed name casing | `JUAN perez`, `juan MARTINEZ` | `Juan Perez`, `Juan Martinez` |
| Inconsistent source | `LANDING_PAGE`, `Landing_Page` | `landing_page` |
| ~5% null fields | Random missing values | `NULL` in DB |

---

## Database schema

```sql
-- Stores processed, analysis-ready records
CREATE TABLE users_clean (
    id           SERIAL PRIMARY KEY,
    form_id      VARCHAR(50)  UNIQUE NOT NULL,
    name         VARCHAR(255),
    email        VARCHAR(255),
    country      VARCHAR(100),
    created_at   DATE,
    source       VARCHAR(100),
    processed_at TIMESTAMP    NOT NULL DEFAULT NOW()
);
```

---

## Tech stack

- **Apache Airflow 2.9** — DAG orchestration, scheduling, retries, task logging
- **PostgreSQL 18** — relational storage for clean data
- **pandas** — DataFrame-based transformations
- **psycopg2** — PostgreSQL driver
- **Docker Compose** — reproducible local environment

---

## Local setup

### Requirements
- Docker Desktop
- PostgreSQL running locally with a `form_pipeline` database

### 1. Clone and configure

```bash
git clone https://github.com/YOUR_USERNAME/form-pipeline.git
cd form-pipeline
cp .env.example .env
# Edit .env and set your PostgreSQL password
```

### 2. Start Airflow

```bash
docker compose up --build -d
```

First run downloads the Airflow image (~500 MB). Takes 2–3 minutes.

### 3. Open the UI

Navigate to `http://localhost:8080` — login: `admin` / `admin`

### 4. Run the pipeline

1. Find the `form_pipeline` DAG
2. Toggle it **on** (it starts paused)
3. Click **▶ Trigger DAG**
4. Watch the 5 tasks turn green in the Graph view

### 5. Query results in PostgreSQL

```sql
-- Clean records loaded by the pipeline
SELECT * FROM users_clean LIMIT 10;

-- Distribution by country
SELECT country, COUNT(*) FROM users_clean GROUP BY country ORDER BY 2 DESC;

-- Emails that couldn't be recovered
SELECT name, source FROM users_clean WHERE email IS NULL;
```

### Run standalone (no Docker needed)

```bash
python scripts/run_pipeline.py
```

---

## Project structure

```
form-pipeline/
├── dags/
│   └── form_pipeline_dag.py   # Airflow DAG (5 tasks)
├── scripts/
│   ├── generate_data.py       # Generates raw_submissions.json with quality issues
│   ├── extract.py             # Loads JSON into DataFrame
│   ├── validate.py            # Schema and null-rate checks
│   ├── clean.py               # All transformations
│   ├── load.py                # Upsert into PostgreSQL
│   ├── metrics.py             # Post-load summary report
│   └── run_pipeline.py        # Standalone runner (no Airflow)
├── sql/
│   └── schema.sql             # Table definitions
├── data/
│   ├── raw/                   # raw_submissions.json (168 records)
│   └── processed/             # Intermediate files written by the DAG
├── config/
│   └── settings.py            # DB config from environment variables
├── Dockerfile                 # Airflow image + project dependencies
├── docker-compose.yml         # Airflow + metadata DB
└── .env.example               # Environment variable template
```

---

## Sample pipeline output

```
[extract]  Loaded 168 records from raw_submissions.json
[validate] Total records       : 168
[validate] Duplicate form_ids  : 18
[validate] Records to drop     : 0  (missing form_id or name)
[validate] Null rates per field:
             form_id         0 nulls  (0.0%)
             name            0 nulls  (0.0%)
           ⚠  email           8 nulls  (4.8%)
             country         2 nulls  (1.2%)
             created_at      0 nulls  (0.0%)
             source          3 nulls  (1.8%)
[validate] Validation PASSED ✓
[clean]    Duplicates removed : 18
[clean]    Invalid emails     : 6   (set to NULL)
[clean]    Unparseable dates  : 0   (set to NULL)
[clean]    Records after clean: 150
[load]     Rows inserted : 150
[load]     Rows skipped  : 0   (already exist)
==================================================
PIPELINE METRICS REPORT
==================================================
  Total clean records : 150
  Date range          : 2025-01-03  →  2025-08-28
  Null emails         : 6  (4.0%)
  Records by country:
    España        38  (25.3%)  ████████
    México        31  (20.7%)  ██████
    Argentina     25  (16.7%)  █████
    ...
```

---

## Author
Lautaro Arozarena
Portfolio project — data engineering, ETL pipelines, and workflow orchestration.

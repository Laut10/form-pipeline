-- Raw ingestion table — stores unprocessed submissions as-is
CREATE TABLE IF NOT EXISTS raw_forms (
    id          SERIAL PRIMARY KEY,
    raw_data    JSONB        NOT NULL,
    ingested_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- Clean table — stores validated, normalized records
CREATE TABLE IF NOT EXISTS users_clean (
    id           SERIAL PRIMARY KEY,
    form_id      VARCHAR(50)  UNIQUE NOT NULL,
    name         VARCHAR(255),
    email        VARCHAR(255),
    country      VARCHAR(100),
    created_at   DATE,
    source       VARCHAR(100),
    processed_at TIMESTAMP    NOT NULL DEFAULT NOW()
);

-- Index for lookups by email and country
CREATE INDEX IF NOT EXISTS idx_users_clean_email   ON users_clean (email);
CREATE INDEX IF NOT EXISTS idx_users_clean_country ON users_clean (country);

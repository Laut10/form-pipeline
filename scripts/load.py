import math
import os
import psycopg2
import psycopg2.extras
import pandas as pd


def _get_connection(db_config: dict):
    return psycopg2.connect(**db_config)


def _create_tables(conn):
    schema_path = os.path.join(os.path.dirname(__file__), "..", "sql", "schema.sql")
    with open(schema_path, "r") as f:
        ddl = f.read()
    with conn.cursor() as cur:
        cur.execute(ddl)
    conn.commit()


def _normalize(val):
    """Convert NaN, NaT, and None to proper SQL NULLs."""
    if val is None:
        return None
    if isinstance(val, float) and math.isnan(val):
        return None
    if val is pd.NaT:
        return None
    return val


def load(df: pd.DataFrame, db_config: dict) -> int:
    conn = _get_connection(db_config)
    _create_tables(conn)

    records = df.to_dict(orient="records")
    for r in records:
        for k, v in r.items():
            r[k] = _normalize(v)
        if r.get("created_at") is not None:
            r["created_at"] = str(r["created_at"])[:10]  # keep YYYY-MM-DD only

    insert_sql = """
        INSERT INTO users_clean (form_id, name, email, country, created_at, source)
        VALUES (%(form_id)s, %(name)s, %(email)s, %(country)s, %(created_at)s, %(source)s)
        ON CONFLICT (form_id) DO NOTHING
    """

    loaded = 0
    with conn.cursor() as cur:
        for record in records:
            cur.execute(insert_sql, record)
            loaded += cur.rowcount

    conn.commit()
    conn.close()

    skipped = len(records) - loaded
    print(f"[load]  Rows inserted : {loaded}")
    print(f"[load]  Rows skipped  : {skipped}  (already exist)")
    return loaded

from __future__ import annotations

import psycopg2
import psycopg2.extras


def generate_metrics(db_config: dict) -> dict:
    """
    Queries users_clean and logs a summary report.
    Returns a dict with the metrics so Airflow can store it via XCom.
    """
    conn = psycopg2.connect(**db_config)
    metrics = {}

    with conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor) as cur:

        # Total records
        cur.execute("SELECT COUNT(*) AS total FROM users_clean;")
        metrics["total_records"] = cur.fetchone()["total"]

        # Records by country
        cur.execute("""
            SELECT country, COUNT(*) AS count
            FROM users_clean
            GROUP BY country
            ORDER BY count DESC;
        """)
        metrics["by_country"] = [dict(r) for r in cur.fetchall()]

        # Records by source
        cur.execute("""
            SELECT source, COUNT(*) AS count
            FROM users_clean
            GROUP BY source
            ORDER BY count DESC;
        """)
        metrics["by_source"] = [dict(r) for r in cur.fetchall()]

        # Data quality stats
        cur.execute("""
            SELECT
                COUNT(*) FILTER (WHERE email IS NULL)      AS null_emails,
                COUNT(*) FILTER (WHERE country IS NULL)    AS null_countries,
                COUNT(*) FILTER (WHERE created_at IS NULL) AS null_dates
            FROM users_clean;
        """)
        quality = dict(cur.fetchone())
        metrics["null_emails"]    = quality["null_emails"]
        metrics["null_countries"] = quality["null_countries"]
        metrics["null_dates"]     = quality["null_dates"]

        # Date range
        cur.execute("""
            SELECT
                MIN(created_at) AS earliest,
                MAX(created_at) AS latest
            FROM users_clean
            WHERE created_at IS NOT NULL;
        """)
        dates = cur.fetchone()
        metrics["date_range"] = {
            "earliest": str(dates["earliest"]),
            "latest":   str(dates["latest"]),
        }

    conn.close()
    _print_report(metrics)
    return metrics


def _print_report(m: dict):
    total = m["total_records"]
    print("=" * 50)
    print("PIPELINE METRICS REPORT")
    print("=" * 50)
    print(f"  Total clean records : {total}")
    print(f"  Date range          : {m['date_range']['earliest']}  →  {m['date_range']['latest']}")
    print(f"  Null emails         : {m['null_emails']}  ({m['null_emails']/total:.1%})")
    print(f"  Null countries      : {m['null_countries']}")
    print(f"  Null dates          : {m['null_dates']}")

    print("\n  Records by country:")
    for row in m["by_country"]:
        pct = row["count"] / total * 100
        bar = "█" * int(pct / 3)
        print(f"    {row['country'] or 'NULL':<12} {row['count']:>4}  ({pct:.1f}%)  {bar}")

    print("\n  Records by source:")
    for row in m["by_source"]:
        pct = row["count"] / total * 100
        bar = "█" * int(pct / 3)
        print(f"    {row['source'] or 'NULL':<20} {row['count']:>4}  ({pct:.1f}%)  {bar}")
    print("=" * 50)

"""
Standalone pipeline runner — mirrors the Airflow DAG for local testing.
Steps: extract → validate → clean → load → metrics
"""

import sys
import os

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from config.settings import DB, RAW_DATA_PATH
from scripts.extract import extract
from scripts.validate import validate
from scripts.clean import clean
from scripts.load import load
from scripts.metrics import generate_metrics


def run():
    print("=" * 50)
    print("STEP 1 — EXTRACT")
    print("=" * 50)
    raw_df = extract(RAW_DATA_PATH)

    print("\n" + "=" * 50)
    print("STEP 2 — VALIDATE")
    print("=" * 50)
    validate(raw_df)

    print("\n" + "=" * 50)
    print("STEP 3 — CLEAN & TRANSFORM")
    print("=" * 50)
    clean_df = clean(raw_df)

    print("\n--- Sample clean records ---")
    print(clean_df[["name", "email", "country", "created_at"]].head(5).to_string(index=False))

    print("\n" + "=" * 50)
    print("STEP 4 — LOAD TO POSTGRESQL")
    print("=" * 50)
    loaded = load(clean_df, DB)

    print("\n" + "=" * 50)
    print("STEP 5 — METRICS")
    print("=" * 50)
    generate_metrics(DB)

    print(f"\nPIPELINE COMPLETE — {loaded} new records loaded into users_clean")


if __name__ == "__main__":
    run()

"""
DAG: form_pipeline
Runs daily. Full ETL with validation and metrics:
  extract → validate → clean → load → metrics
Data flows through intermediate JSON files in data/processed/.
"""

from __future__ import annotations

import os
import sys

import pandas as pd
from airflow import DAG
from airflow.operators.python import PythonOperator
from datetime import datetime, timedelta

sys.path.insert(0, "/opt/airflow/project")

from scripts.extract import extract
from scripts.validate import validate
from scripts.clean import clean
from scripts.load import load
from scripts.metrics import generate_metrics
from config.settings import DB, RAW_DATA_PATH

PROCESSED_DIR = "/opt/airflow/project/data/processed"
EXTRACTED_PATH = os.path.join(PROCESSED_DIR, "extracted.json")
CLEAN_PATH     = os.path.join(PROCESSED_DIR, "clean.json")


# ─── Task callables ───────────────────────────────────────────────────────────

def task_extract():
    df = extract(RAW_DATA_PATH)
    os.makedirs(PROCESSED_DIR, exist_ok=True)
    df.to_json(EXTRACTED_PATH, orient="records", indent=2)
    print(f"[dag:extract] {len(df)} records saved → {EXTRACTED_PATH}")
    return len(df)


def task_validate():
    df = pd.read_json(EXTRACTED_PATH, orient="records")
    report = validate(df)
    return report


def task_clean():
    df = pd.read_json(EXTRACTED_PATH, orient="records")
    clean_df = clean(df)
    clean_df["created_at"] = clean_df["created_at"].apply(
        lambda x: x.isoformat() if x is not None else None
    )
    clean_df.to_json(CLEAN_PATH, orient="records", indent=2)
    print(f"[dag:clean] {len(clean_df)} records saved → {CLEAN_PATH}")
    return len(clean_df)


def task_load():
    df = pd.read_json(CLEAN_PATH, orient="records")
    loaded = load(df, DB)
    print(f"[dag:load] {loaded} new records inserted into users_clean")
    return loaded


def task_metrics():
    metrics = generate_metrics(DB)
    return metrics


# ─── DAG definition ───────────────────────────────────────────────────────────

default_args = {
    "owner": "airflow",
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="form_pipeline",
    default_args=default_args,
    description="ETL pipeline for user form submissions",
    schedule="@daily",
    start_date=datetime(2025, 1, 1),
    catchup=False,
    tags=["etl", "forms"],
) as dag:

    extract_task = PythonOperator(
        task_id="extract",
        python_callable=task_extract,
    )

    validate_task = PythonOperator(
        task_id="validate",
        python_callable=task_validate,
    )

    clean_task = PythonOperator(
        task_id="clean",
        python_callable=task_clean,
    )

    load_task = PythonOperator(
        task_id="load",
        python_callable=task_load,
    )

    metrics_task = PythonOperator(
        task_id="metrics",
        python_callable=task_metrics,
    )

    extract_task >> validate_task >> clean_task >> load_task >> metrics_task

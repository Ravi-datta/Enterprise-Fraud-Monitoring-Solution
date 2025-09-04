from __future__ import annotations

import os
from datetime import datetime, timedelta

from airflow import DAG
from airflow.operators.bash import BashOperator


PROJECT_DIR = "/opt/fraud-e2e"
ENV = {
    "PYTHONPATH": PROJECT_DIR,
}

default_args = {
    "owner": "airflow",
    "depends_on_past": False,
    "retries": 1,
    "retry_delay": timedelta(minutes=5),
}

with DAG(
    dag_id="fraud_daily_dag",
    description="Daily fraud pipeline: generate -> features -> rules -> predict -> report",
    schedule_interval="@daily",
    start_date=datetime(2024, 1, 1),
    catchup=False,
    default_args=default_args,
) as dag:

    gen = BashOperator(
        task_id="generate_today",
        bash_command=f"cd {PROJECT_DIR} && python -m src.cli generate --days 1 --tx-per-day 50000",
        env=ENV,
    )

    features = BashOperator(
        task_id="build_features",
        bash_command=f"cd {PROJECT_DIR} && python -m src.cli features",
        env=ENV,
    )

    rules = BashOperator(
        task_id="rules_score",
        bash_command=f"cd {PROJECT_DIR} && python -m src.cli rulescore",
        env=ENV,
    )

    predict = BashOperator(
        task_id="model_predict",
        bash_command=f"cd {PROJECT_DIR} && python -m src.cli predict",
        env=ENV,
    )

    report = BashOperator(
        task_id="daily_report",
        bash_command=f"cd {PROJECT_DIR} && python -m src.cli report",
        env=ENV,
    )

    gen >> features >> [rules, predict] >> report


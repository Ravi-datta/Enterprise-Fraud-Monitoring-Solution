from __future__ import annotations

from datetime import datetime
from airflow import DAG
from airflow.operators.bash import BashOperator

PROJECT_DIR = "/opt/fraud-e2e"
ENV = {"PYTHONPATH": PROJECT_DIR}

with DAG(
    dag_id="backfill_transactions_dag",
    description="Backfill historical synthetic transactions",
    schedule_interval=None,
    start_date=datetime(2024, 1, 1),
    catchup=False,
) as dag:
    # Adjust days/tx-per-day via dag_run.conf if desired
    backfill = BashOperator(
        task_id="backfill",
        bash_command=f"cd {PROJECT_DIR} && python -m src.cli generate --days 30 --tx-per-day 50000",
        env=ENV,
    )


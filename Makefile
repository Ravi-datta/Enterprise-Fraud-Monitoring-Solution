SHELL := /bin/bash

PY := python
PIP := pip

VENV := .venv
ACT := source $(VENV)/bin/activate

export PYTHONPATH := .

.PHONY: setup db seed gen features rules train predict evaluate dashboard airflow-init airflow-up airflow-down test

setup:
	python3.11 -m venv $(VENV) && \
		$(ACT) && $(PIP) install -U pip && $(PIP) install -r requirements.txt

db:
	@echo "Run db scripts manually or via psql; in Docker the db container starts automatically."

seed:
	$(PY) -m src.cli seed

gen:
	$(PY) -m src.cli generate --days $${DAYS:-7} --tx-per-day $${TX_PER_DAY:-50000}

features:
	$(PY) -m src.cli features

rules:
	$(PY) -m src.cli rulescore

train:
	$(PY) -m src.cli trainsklearn --algo $${ALGO:-rf}

predict:
	$(PY) -m src.cli predict

evaluate:
	$(PY) -m src.cli evaluate

dashboard:
	$(PY) dashboard/app.py

airflow-init:
	docker compose run --rm airflow-init

airflow-up:
	docker compose up -d airflow-webserver airflow-scheduler

airflow-down:
	docker compose down

test:
	pytest -q

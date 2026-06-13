.PHONY: all ingest transform app test lint

all: ingest transform

ingest:
	python ingestion/bronze_historical.py
	python ingestion/bronze_squads.py
	python ingestion/bronze_market_value.py
	python ingestion/bronze_geo.py

transform:
	cd transform/dbt_project && dbt run && dbt test

app:
	streamlit run app/main.py

test:
	pytest tests/ -v --cov=ingestion --cov-report=term-missing
	cd transform/dbt_project && dbt test

lint:
	ruff check .

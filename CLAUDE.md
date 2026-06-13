# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## What This Repo Is

End-to-end data engineering pipeline for FIFA World Cup 2026 analytics. Ingests public data (historical results, player stats, market values, GeoJSON), transforms through a medallion architecture (Bronze → Silver → Gold) using DuckDB + dbt, and serves a Streamlit dashboard with maps and indicators.

## Quick Start

```bash
# Install dependencies
pip install -r requirements.txt

# Full pipeline
make all

# Individual steps
make ingest      # Run all Bronze ingestion scripts
make transform   # Run dbt models (Silver + Gold)
make app         # Launch Streamlit dashboard
make test        # Run pytest + dbt tests
```

## Common Commands

```bash
# Ingestion
python ingestion/bronze_historical.py
python ingestion/bronze_squads.py
python ingestion/bronze_market_value.py
python ingestion/bronze_geo.py

# dbt
cd transform/dbt_project
dbt run --select silver.*
dbt run --select gold.*
dbt test

# App
streamlit run app/main.py

# Lint
ruff check .

# Tests
pytest tests/ -v --cov=ingestion
```

## Architecture

```
ingestion/          Bronze: raw ingestion scripts (one per source)
transform/
  dbt_project/
    models/
      silver/       Cleaned, typed, normalized staging models
      gold/         Aggregated marts ready for the dashboard
    tests/          dbt data quality tests
app/
  main.py           Streamlit entry point
  pages/            One file per dashboard page (Streamlit multipage)
data/
  raw/              Bronze output — gitignored
  silver/           Parquet from dbt — gitignored
  gold/             Parquet from dbt — gitignored
tests/              pytest unit tests for ingestion
```

**Storage engine:** single DuckDB file (`data/world_cup.duckdb`). All dbt models write to it.

## Data Sources

| Script | Source | What it fetches |
|--------|--------|----------------|
| `bronze_historical.py` | Kaggle CSV | Match results 1930–2022 |
| `bronze_squads.py` | FBref (scraping) | Player stats per squad |
| `bronze_market_value.py` | Transfermarkt (scraping) | Market value, age, club |
| `bronze_geo.py` | Natural Earth GeoJSON | Country boundaries for maps |

Scrapers use `time.sleep(2)` between requests and a declared `User-Agent` header.

## Dashboard Pages

1. `1_Mapa_Participantes.py` — Folium map of all 48 nations, colored by confederation
2. `2_Ranking_Historico.py` — Historical performance bar charts and heatmaps
3. `3_Brasil_Deep_Dive.py` — Brazil edition-by-edition, head-to-head, top scorers
4. `4_Perfil_Jogadores.py` — 2026 squad scatter plots, market value, age distribution

## dbt Model Conventions

- Silver models prefix: `stg_` (staging)
- Gold models prefix: `mart_`
- All models materialized as `parquet` via dbt-duckdb
- Every model has `not_null` and `unique` tests on primary keys

## Running with Docker

```bash
docker-compose up        # Builds image and runs the Streamlit app on :8501
docker-compose run app make ingest transform   # Run pipeline inside container
```

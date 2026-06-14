# 🏆 World Cup 2026 Analytics

[![Python 3.11](https://img.shields.io/badge/Python-3.11-3776AB?logo=python&logoColor=white)](https://python.org)
[![dbt](https://img.shields.io/badge/dbt-DuckDB-FF694B?logo=dbt&logoColor=white)](https://docs.getdbt.com)
[![Streamlit](https://img.shields.io/badge/Streamlit-1.53-FF4B4B?logo=streamlit&logoColor=white)](https://streamlit.io)
[![License MIT](https://img.shields.io/badge/License-MIT-green)](LICENSE)
[![Docker ready](https://img.shields.io/badge/Docker-ready-2496ED?logo=docker&logoColor=white)](Dockerfile)

Pipeline ETL end-to-end para a Copa do Mundo FIFA 2026 — ingestão de fontes públicas, transformação em camadas **Medallion (Bronze → Silver → Gold)** com dbt + DuckDB, e dashboard interativo com mapas, rankings e análise profunda do Brasil.

---

## 📸 Dashboard

| Página | Descrição |
|--------|-----------|
| **Principal** | Cards de navegação, KPIs ao vivo, próximas partidas e grupos da fase de grupos |
| **Mapa Participantes** | Mapa Folium interativo com tooltip de confederação e histórico de cada uma das 48 nações |
| **Ranking Histórico** | Barras horizontais/verticais por métrica, filtro de confederação, scatter ofensivo×defensivo |
| **Análise por Nação** | Seletor de nação, histórico Copa a Copa, head-to-head e destaques de títulos |
| **Perfil dos Jogadores** | Figurinhas estilo Panini com foto (Wikipedia Commons), valor de mercado, radar de desempenho |

---

## 🏗️ Arquitetura

```
ingestion/                  Bronze — scripts de ingestão por fonte
  bronze_historical.py      Kaggle CSV: resultados 1930–2022
  bronze_squads.py          FBref: estatísticas de jogadores por seleção
  bronze_market_value.py    Transfermarkt: valor de mercado, idade e clube
  bronze_geo.py             Natural Earth: GeoJSON de países

transform/
  dbt_project/
    seeds/                  CSVs versionados (elencos e valores de mercado)
      bronze_squads.csv     Elenco oficial 2026 por seleção (Brasil: conv. Ancelotti)
      bronze_market_value.csv  Valores de mercado atualizados
    models/
      silver/               Staging: tipagem, normalização e limpeza
        stg_matches.sql     Histórico de partidas (1930–2022)
        stg_players.sql     Estatísticas de jogadores
        stg_nations.sql     Metadados de seleções
      gold/                 Marts prontos para o dashboard
        mart_brazil_deep.sql         Desempenho do Brasil edição a edição
        mart_nations_performance.sql Ranking histórico geral de nações
        mart_players_profile.sql     Perfil completo dos convocados 2026

app/
  main.py                   Página principal (Streamlit multipage)
  style.py                  Design system: CSS, cores, plotly_layout, nation_pt()
  player_photos.py          Cache de fotos Wikipedia Commons
  pages/
    1_Mapa_Participantes.py
    2_Ranking_Historico.py
    3_Brasil_Deep_Dive.py
    4_Perfil_Jogadores.py

data/
  raw/                      Bronze: CSVs e GeoJSONs brutos
  world_cup.duckdb          Banco único (Silver + Gold via dbt)
  player_photos.json        Cache de URLs de fotos dos jogadores
```

**Storage engine:** arquivo DuckDB único (`data/world_cup.duckdb`). Todos os modelos dbt escrevem nele como tabelas.

---

## ⚡ Quick Start

```bash
# 1. Clone e instale dependências
git clone https://github.com/Victormartinsilva/world-cup-2026-analytics.git
cd world-cup-2026-analytics
pip install -r requirements.txt

# 2. Pipeline completo (ingestão + transformação)
make all

# 3. Dashboard
make app
# Acesse: http://localhost:8501
```

### Passos individuais

```bash
# Ingestão Bronze
python ingestion/bronze_historical.py
python ingestion/bronze_squads.py
python ingestion/bronze_market_value.py
python ingestion/bronze_geo.py

# Transformação dbt (Silver + Gold)
cd transform/dbt_project
dbt seed          # carrega os CSVs versionados
dbt run           # executa todos os modelos
dbt test          # valida not_null e unique nos PKs

# App
streamlit run app/main.py

# Lint
ruff check .

# Testes unitários
pytest tests/ -v --cov=ingestion
```

---

## 🐳 Docker

```bash
# Sobe o dashboard na porta 8501
docker-compose up

# Executa o pipeline dentro do container
docker-compose run app make ingest transform
```

---

## 🗄️ Fontes de Dados

| Script | Fonte | O que busca |
|--------|-------|-------------|
| `bronze_historical.py` | Kaggle CSV | Resultados de partidas 1930–2022 |
| `bronze_squads.py` | FBref (scraping) | Estatísticas de jogadores por seleção |
| `bronze_market_value.py` | Transfermarkt (scraping) | Valor de mercado, idade, clube |
| `bronze_geo.py` | Natural Earth GeoJSON | Fronteiras de países para mapas |
| `seeds/bronze_squads.csv` | FIFA (manual) | Elenco oficial Copa 2026 por seleção |
| `seeds/bronze_market_value.csv` | Transfermarkt (manual) | Valores atualizados para 2026 |

> Scrapers respeitam `time.sleep(2)` entre requisições e declaram `User-Agent` explícito.

---

## 🇧🇷 Elenco Brasil 2026 — Convocação Ancelotti

| Posição | Jogadores |
|---------|-----------|
| **Goleiros** | Alisson (Liverpool), Ederson (Fenerbahçe), Weverton (Grêmio) |
| **Defensores** | Alex Sandro, Danilo, Léo Pereira (Flamengo) · Gabriel Magalhães (Arsenal) · Marquinhos (PSG) · Bremer (Juventus) · Wesley (Roma) · Douglas Santos (Zenit) · Ibañez (Al-Ahli) |
| **Meias** | Bruno Guimarães (Newcastle) · Lucas Paquetá (Flamengo) · Casemiro (Man. Utd) · Danilo Santos (Botafogo) · Fabinho (Al-Ittihad) |
| **Atacantes** | Vinicius Junior (Real Madrid) · Raphinha (Barcelona) · Neymar Junior (Santos) · Gabriel Martinelli (Arsenal) · Matheus Cunha (Man. Utd) · Endrick (Lyon) · Igor Thiago (Brentford) · Luiz Henrique (Zenit) · Rayan (Bournemouth) |

---

## 🛠️ Stack Técnica

| Camada | Tecnologia |
|--------|-----------|
| Linguagem | Python 3.11 |
| Storage | DuckDB 1.4 |
| Transformação | dbt-duckdb 1.10 |
| Dashboard | Streamlit 1.53 |
| Mapas | Folium + streamlit-folium |
| Gráficos | Plotly Express + Graph Objects |
| Scraping | requests + BeautifulSoup4 |
| Containers | Docker + docker-compose |
| Qualidade | ruff · pytest · dbt tests |

---

## 📐 Convenções dbt

- Modelos Silver: prefixo `stg_` — tipagem, deduplicação, normalização
- Modelos Gold: prefixo `mart_` — agregações prontas para o dashboard
- Materialização: `table` (DuckDB nativo)
- Testes obrigatórios: `not_null` + `unique` nas chaves primárias de todos os modelos

---

## 📄 Licença

[MIT](LICENSE) © 2026 Victor Martins da Silva

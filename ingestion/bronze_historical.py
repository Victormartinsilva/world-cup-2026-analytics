"""
Ingests FIFA World Cup historical data (1930-2022) from Kaggle CSV files.
Download manually from: https://www.kaggle.com/datasets/abecklas/fifa-world-cup
Place files in data/raw/kaggle/ before running.
"""

import pandas as pd
import duckdb
from pathlib import Path

RAW_DIR = Path("data/raw/kaggle")
DB_PATH = Path("data/world_cup.duckdb")


def ingest_matches():
    path = RAW_DIR / "WorldCupMatches.csv"
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def ingest_cups():
    path = RAW_DIR / "WorldCups.csv"
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def ingest_players():
    path = RAW_DIR / "WorldCupPlayers.csv"
    df = pd.read_csv(path)
    df.columns = [c.strip().lower().replace(" ", "_") for c in df.columns]
    return df


def main():
    con = duckdb.connect(str(DB_PATH))

    print("Ingesting matches...")
    df_matches = ingest_matches()
    con.execute("CREATE OR REPLACE TABLE bronze_matches AS SELECT * FROM df_matches")

    print("Ingesting cups...")
    df_cups = ingest_cups()
    con.execute("CREATE OR REPLACE TABLE bronze_cups AS SELECT * FROM df_cups")

    print("Ingesting players...")
    df_players = ingest_players()
    con.execute("CREATE OR REPLACE TABLE bronze_players AS SELECT * FROM df_players")

    print(f"Done. Matches: {len(df_matches)}, Cups: {len(df_cups)}, Players: {len(df_players)}")
    con.close()


if __name__ == "__main__":
    main()

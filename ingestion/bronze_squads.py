"""
Scrapes 2026 World Cup squad statistics from FBref.
Respects rate limits with sleep between requests.
"""

import time
import requests
import pandas as pd
import duckdb
from pathlib import Path
from bs4 import BeautifulSoup

DB_PATH = Path("data/world_cup.duckdb")
HEADERS = {"User-Agent": "world-cup-2026-analytics/1.0 (portfolio project; victoreagri@gmail.com)"}

# FBref national team stats pages for key confederations
SQUAD_URLS = {
    "Brazil": "https://fbref.com/en/squads/e8a695a0/Brazil-Stats",
    "Argentina": "https://fbref.com/en/squads/f9fddd6e/Argentina-Stats",
    "France": "https://fbref.com/en/squads/e7a3f1f4/France-Stats",
    "Germany": "https://fbref.com/en/squads/054efa67/Germany-Stats",
    "England": "https://fbref.com/en/squads/cff3d9bb/England-Stats",
    "Spain": "https://fbref.com/en/squads/7c21e445/Spain-Stats",
    "Portugal": "https://fbref.com/en/squads/e8a695a1/Portugal-Stats",
}


def scrape_squad(nation: str, url: str) -> pd.DataFrame:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    table = soup.find("table", {"id": "stats_standard"})
    if not table:
        print(f"  [warn] No stats table found for {nation}")
        return pd.DataFrame()

    df = pd.read_html(str(table))[0]
    df.columns = ["_".join(str(c).strip().lower().split()) for c in df.columns.droplevel(0)]
    df.insert(0, "nation", nation)
    return df


def main():
    con = duckdb.connect(str(DB_PATH))
    frames = []

    for nation, url in SQUAD_URLS.items():
        print(f"Scraping {nation}...")
        try:
            df = scrape_squad(nation, url)
            if not df.empty:
                frames.append(df)
        except Exception as e:
            print(f"  [error] {nation}: {e}")
        time.sleep(2)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        con.execute("CREATE OR REPLACE TABLE bronze_squads AS SELECT * FROM combined")
        print(f"Done. {len(combined)} player rows ingested.")
    else:
        print("No data ingested.")

    con.close()


if __name__ == "__main__":
    main()

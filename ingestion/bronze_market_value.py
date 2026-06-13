"""
Scrapes player market values from Transfermarkt for key national teams.
Respects rate limits with sleep between requests.
"""

import time
import requests
import pandas as pd
import duckdb
from pathlib import Path
from bs4 import BeautifulSoup

DB_PATH = Path("data/world_cup.duckdb")
HEADERS = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36",
}

TEAM_URLS = {
    "Brazil": "https://www.transfermarkt.com.br/brasilien/kader/verein/3439",
    "Argentina": "https://www.transfermarkt.com.br/argentinien/kader/verein/3437",
    "France": "https://www.transfermarkt.com.br/frankreich/kader/verein/3377",
    "Germany": "https://www.transfermarkt.com.br/deutschland/kader/verein/3376",
    "England": "https://www.transfermarkt.com.br/england/kader/verein/3166",
    "Spain": "https://www.transfermarkt.com.br/spanien/kader/verein/3375",
    "Portugal": "https://www.transfermarkt.com.br/portugal/kader/verein/3438",
}


def parse_market_value(value_str: str) -> float:
    """Convert '€50M' or '€500k' strings to float (millions)."""
    if not value_str or value_str == "-":
        return 0.0
    s = value_str.replace("€", "").replace(",", ".").strip()
    if "M" in s:
        return float(s.replace("M", ""))
    if "k" in s or "K" in s:
        return float(s.replace("k", "").replace("K", "")) / 1000
    return 0.0


def scrape_team(nation: str, url: str) -> pd.DataFrame:
    resp = requests.get(url, headers=HEADERS, timeout=15)
    resp.raise_for_status()
    soup = BeautifulSoup(resp.text, "lxml")

    rows = []
    for tr in soup.select("table.items tbody tr"):
        cells = tr.find_all("td")
        if len(cells) < 6:
            continue
        name_tag = tr.select_one(".spielprofil_tooltip")
        if not name_tag:
            continue
        rows.append({
            "nation": nation,
            "player_name": name_tag.text.strip(),
            "position": cells[4].text.strip() if len(cells) > 4 else None,
            "age": cells[5].text.strip() if len(cells) > 5 else None,
            "market_value_eur_m": parse_market_value(cells[-1].text.strip()),
        })

    return pd.DataFrame(rows)


def main():
    con = duckdb.connect(str(DB_PATH))
    frames = []

    for nation, url in TEAM_URLS.items():
        print(f"Scraping {nation}...")
        try:
            df = scrape_team(nation, url)
            if not df.empty:
                frames.append(df)
                print(f"  {len(df)} players")
        except Exception as e:
            print(f"  [error] {nation}: {e}")
        time.sleep(3)

    if frames:
        combined = pd.concat(frames, ignore_index=True)
        con.execute("CREATE OR REPLACE TABLE bronze_market_value AS SELECT * FROM combined")
        print(f"Done. {len(combined)} rows ingested.")

    con.close()


if __name__ == "__main__":
    main()

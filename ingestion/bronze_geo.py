"""
Downloads Natural Earth GeoJSON with country boundaries.
Filters to the 48 nations qualified for the 2026 World Cup.
"""

import json
import requests
import duckdb
import pandas as pd
from pathlib import Path

DB_PATH = Path("data/world_cup.duckdb")
RAW_DIR = Path("data/raw/geo")
GEOJSON_URL = (
    "https://raw.githubusercontent.com/datasets/geo-countries/master/data/countries.geojson"
)

# 48 qualified nations for 2026 (CONMEBOL 6 + UEFA 16 + CAF 9 + AFC 8 + CONCACAF 6 + OFC 1 + hosts)
QUALIFIED_NATIONS = {
    # Hosts (auto-qualified)
    "United States of America", "Canada", "Mexico",
    # CONMEBOL
    "Argentina", "Brazil", "Colombia", "Uruguay", "Ecuador", "Venezuela",
    # UEFA (indicative — final spots TBD)
    "France", "Germany", "Spain", "England", "Portugal", "Netherlands",
    "Italy", "Belgium", "Austria", "Denmark", "Switzerland", "Croatia",
    "Poland", "Serbia", "Scotland", "Türkiye",
    # CAF
    "Morocco", "Senegal", "Egypt", "Nigeria", "Cameroon",
    "South Africa", "Ghana", "Ivory Coast", "Algeria",
    # AFC
    "Japan", "South Korea", "Iran", "Saudi Arabia", "Australia",
    "Qatar", "Uzbekistan", "Jordan",
    # CONCACAF (excl. hosts)
    "Costa Rica", "Jamaica", "Panama", "Honduras",
    # OFC
    "New Zealand",
}


def main():
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    geo_path = RAW_DIR / "countries.geojson"

    if not geo_path.exists():
        print("Downloading GeoJSON...")
        resp = requests.get(GEOJSON_URL, timeout=30)
        resp.raise_for_status()
        geo_path.write_bytes(resp.content)
        print(f"Saved to {geo_path}")
    else:
        print("GeoJSON already cached.")

    with open(geo_path, encoding="utf-8") as f:
        geojson = json.load(f)

    records = []
    for feature in geojson["features"]:
        props = feature["properties"]
        name = props.get("ADMIN") or props.get("name") or ""
        iso = props.get("ISO_A3", "")
        qualified = name in QUALIFIED_NATIONS
        records.append({"country_name": name, "iso_a3": iso, "qualified_2026": qualified})

    df = pd.DataFrame(records)
    qualified_path = RAW_DIR / "qualified_nations.geojson"

    filtered_features = [
        f for f in geojson["features"]
        if (f["properties"].get("ADMIN") or f["properties"].get("name", "")) in QUALIFIED_NATIONS
    ]
    filtered_geo = {"type": "FeatureCollection", "features": filtered_features}
    qualified_path.write_text(json.dumps(filtered_geo), encoding="utf-8")

    con = duckdb.connect(str(DB_PATH))
    con.execute("CREATE OR REPLACE TABLE bronze_countries AS SELECT * FROM df")
    print(f"Done. {df['qualified_2026'].sum()} qualified nations registered.")
    con.close()


if __name__ == "__main__":
    main()

import json
import streamlit as st
import folium
from streamlit_folium import st_folium
import duckdb
from pathlib import Path

st.set_page_config(page_title="Mapa das Nações", layout="wide")
st.title("🗺️ Nações Participantes — Copa 2026")

DB_PATH = Path("data/world_cup.duckdb")
GEO_PATH = Path("data/raw/geo/qualified_nations.geojson")

CONFEDERATION_COLORS = {
    "CONMEBOL": "#2ecc71",
    "UEFA": "#3498db",
    "CAF": "#e74c3c",
    "AFC": "#f39c12",
    "CONCACAF": "#9b59b6",
    "OFC": "#1abc9c",
}


@st.cache_data
def load_nations():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM mart_nations_performance WHERE qualified_2026 = TRUE").df()
    con.close()
    return df


@st.cache_data
def load_geojson():
    with open(GEO_PATH, encoding="utf-8") as f:
        return json.load(f)


try:
    df = load_nations()
    geojson = load_geojson()

    m = folium.Map(location=[20, 0], zoom_start=2, tiles="CartoDB positron")

    folium.GeoJson(
        geojson,
        name="Nações 2026",
        tooltip=folium.GeoJsonTooltip(fields=["ADMIN"], aliases=["País:"]),
        style_function=lambda _: {
            "fillColor": "#f39c12",
            "color": "white",
            "weight": 1,
            "fillOpacity": 0.7,
        },
    ).add_to(m)

    st_folium(m, width=1200, height=550)

    st.subheader("Tabela — Desempenho histórico das 48 nações")
    st.dataframe(
        df[["nation", "editions_played", "wins", "draws", "losses",
            "total_goals_for", "world_cup_titles", "win_pct"]].sort_values(
            "world_cup_titles", ascending=False
        ),
        use_container_width=True,
    )

except Exception as e:
    st.warning(f"Execute o pipeline primeiro (`make all`). Detalhe: {e}")

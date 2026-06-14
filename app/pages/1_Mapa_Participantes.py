import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import streamlit as st
import folium
from streamlit_folium import st_folium
import duckdb
from style import (
    inject_css, page_header, confederation_legend_html,
    add_flag_column, GREEN, YELLOW,
)

st.set_page_config(page_title="Mapa das Nações", layout="wide")
inject_css()
page_header(
    "🗺️ Nações Participantes — Copa 2026",
    "48 seleções classificadas. Explore o mapa e a tabela de desempenho histórico.",
)

DB_PATH  = Path("data/world_cup.duckdb")
GEO_PATH = Path("data/raw/geo/qualified_nations.geojson")


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

    m = folium.Map(
        location=[20, 0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
    )

    folium.GeoJson(
        geojson,
        name="Nações 2026",
        tooltip=folium.GeoJsonTooltip(fields=["name"], aliases=["País:"]),
        style_function=lambda _: {
            "fillColor": GREEN,
            "color": YELLOW,
            "weight": 1.2,
            "fillOpacity": 0.65,
        },
        highlight_function=lambda _: {
            "fillColor": YELLOW,
            "color": "#FFFFFF",
            "weight": 2,
            "fillOpacity": 0.85,
        },
    ).add_to(m)

    st_folium(m, width=None, height=520, returned_objects=[])

    st.markdown(confederation_legend_html(), unsafe_allow_html=True)

    st.markdown("### Tabela — Desempenho histórico das 48 nações")
    table_df = add_flag_column(
        df[["nation", "editions_played", "wins", "draws", "losses",
            "total_goals_for", "world_cup_titles", "win_pct"]].sort_values(
            "world_cup_titles", ascending=False
        )
    )
    st.dataframe(
        table_df,
        column_config={
            "flag_url": st.column_config.ImageColumn("🏳️", width="small"),
            "nation":           st.column_config.TextColumn("Nação"),
            "editions_played":  st.column_config.NumberColumn("Edições"),
            "wins":             st.column_config.NumberColumn("Vitórias"),
            "draws":            st.column_config.NumberColumn("Empates"),
            "losses":           st.column_config.NumberColumn("Derrotas"),
            "total_goals_for":  st.column_config.NumberColumn("Gols pró"),
            "world_cup_titles": st.column_config.NumberColumn("Títulos"),
            "win_pct":          st.column_config.NumberColumn("% vitórias", format="%.1f%%"),
        },
        use_container_width=True,
        hide_index=True,
    )

except Exception as e:
    st.warning(f"Execute o pipeline primeiro (`make all`). Detalhe: {e}")

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import duckdb
from pathlib import Path

st.set_page_config(page_title="Brasil — Deep Dive", layout="wide")
st.title("🇧🇷 Brasil — Análise Completa")

DB_PATH = Path("data/world_cup.duckdb")


@st.cache_data
def load_brazil():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM mart_brazil_deep ORDER BY edition_year").df()
    con.close()
    return df


@st.cache_data
def load_matches():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("""
        SELECT * FROM stg_matches
        WHERE home_team = 'Brazil' OR away_team = 'Brazil'
        ORDER BY edition_year
    """).df()
    con.close()
    return df


try:
    df = load_brazil()

    col1, col2, col3, col4 = st.columns(4)
    col1.metric("Títulos", "5")
    col2.metric("Edições participadas", str(df["editions_played"].iloc[0] if "editions_played" in df.columns else len(df)))
    col3.metric("Total de vitórias", str(df["wins"].sum()))
    col4.metric("Gols marcados", str(int(df["goals_scored"].sum())))

    st.subheader("Desempenho por edição")
    fig = go.Figure()
    fig.add_trace(go.Bar(x=df["edition_year"], y=df["goals_scored"], name="Gols marcados", marker_color="#009C3B"))
    fig.add_trace(go.Bar(x=df["edition_year"], y=df["goals_conceded"], name="Gols sofridos", marker_color="#FFDF00"))
    fig.add_trace(go.Scatter(x=df["edition_year"], y=df["wins"], name="Vitórias", mode="lines+markers", yaxis="y2", line=dict(color="#002776")))
    fig.update_layout(
        barmode="group",
        title="Gols e vitórias do Brasil por edição (1930–2022)",
        yaxis=dict(title="Gols"),
        yaxis2=dict(title="Vitórias", overlaying="y", side="right"),
        xaxis=dict(title="Edição"),
    )
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Resultado por partida")
    df_matches = load_matches()
    st.dataframe(df_matches, use_container_width=True)

except Exception as e:
    st.warning(f"Execute o pipeline primeiro (`make all`). Detalhe: {e}")

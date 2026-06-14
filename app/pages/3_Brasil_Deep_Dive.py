import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.graph_objects as go
import duckdb
from style import inject_css, page_header, plotly_layout, flag_url, GREEN, YELLOW, BLUE

st.set_page_config(page_title="Brasil — Deep Dive", layout="wide")
inject_css()

# ── Header com bandeira ────────────────────────────────────────────────────────
br_flag = flag_url("br", width=80)
st.markdown(
    f"""<div style="
        background:linear-gradient(135deg,#012A1C 0%,#014D24 60%,#002776 100%);
        padding:1.8rem 2.2rem;border-radius:12px;
        border-left:5px solid #FFDF00;margin-bottom:1.8rem;
        display:flex;align-items:center;gap:1.5rem">
      <img src="{br_flag}" width="80"
           style="border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,0.5);flex-shrink:0">
      <div>
        <h1 style="color:#FFDF00;font-family:'Barlow Condensed',sans-serif;
            font-size:2.4rem;margin:0;font-weight:700;letter-spacing:0.03em">
          🇧🇷 Brasil — Análise Completa
        </h1>
        <p style="color:#cce8d8;margin:0.5rem 0 0;font-size:1rem;font-family:Inter,sans-serif">
          5 títulos, 22 edições e a história mais vitoriosa do futebol mundial.
        </p>
      </div>
    </div>""",
    unsafe_allow_html=True,
)

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
    col2.metric(
        "Edições participadas",
        str(df["editions_played"].iloc[0] if "editions_played" in df.columns else len(df)),
    )
    col3.metric("Total de vitórias", str(df["wins"].sum()))
    col4.metric("Gols marcados", str(int(df["goals_scored"].sum())))

    st.markdown("### Desempenho por edição")
    fig = go.Figure()
    fig.add_trace(go.Bar(
        x=df["edition_year"], y=df["goals_scored"],
        name="Gols marcados", marker_color=GREEN,
    ))
    fig.add_trace(go.Bar(
        x=df["edition_year"], y=df["goals_conceded"],
        name="Gols sofridos", marker_color=YELLOW,
    ))
    fig.add_trace(go.Scatter(
        x=df["edition_year"], y=df["wins"],
        name="Vitórias", mode="lines+markers", yaxis="y2",
        line=dict(color="#40C4FF", width=2),
        marker=dict(size=7, color="#40C4FF", line=dict(color=BLUE, width=1.5)),
    ))

    base = plotly_layout()
    base["yaxis2"] = dict(
        title="Vitórias",
        overlaying="y",
        side="right",
        gridcolor="#1a3d25",
        linecolor=GREEN,
        tickfont=dict(color="#F0F0F0"),
        titlefont=dict(color="#F0F0F0"),
    )
    fig.update_layout(
        **base,
        barmode="group",
        title="Gols e vitórias do Brasil por edição (1930–2022)",
        xaxis_title="Edição",
        yaxis_title="Gols",
    )
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Resultado por partida")
    df_matches = load_matches()
    st.dataframe(df_matches, use_container_width=True)

except Exception as e:
    st.warning(f"Execute o pipeline primeiro (`make all`). Detalhe: {e}")

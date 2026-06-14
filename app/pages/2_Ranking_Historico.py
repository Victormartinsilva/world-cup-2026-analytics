import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.express as px
import duckdb
from style import inject_css, page_header, plotly_layout, add_flag_column, SEQUENTIAL_SCALE

st.set_page_config(page_title="Ranking Histórico", layout="wide")
inject_css()
page_header(
    "🏆 Ranking Histórico por Nação",
    "Comparativo de desempenho entre as seleções classificadas para 2026.",
)

DB_PATH = Path("data/world_cup.duckdb")

METRIC_LABELS = {
    "world_cup_titles":  "Títulos",
    "wins":              "Vitórias",
    "total_goals_for":   "Gols marcados",
    "editions_played":   "Edições disputadas",
}


@st.cache_data
def load_data():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM mart_nations_performance").df()
    con.close()
    return df


try:
    df = load_data()

    col_ctrl1, col_ctrl2 = st.columns([1, 2])
    with col_ctrl1:
        top_n = st.slider("Top N nações", 5, 30, 15)
    with col_ctrl2:
        metric = st.selectbox("Métrica", list(METRIC_LABELS.keys()),
                              format_func=lambda k: METRIC_LABELS[k])

    top = df.nlargest(top_n, metric)

    fig = px.bar(
        top,
        x="nation",
        y=metric,
        color="world_cup_titles",
        color_continuous_scale=SEQUENTIAL_SCALE,
        title=f"Top {top_n} nações — {METRIC_LABELS[metric]}",
        labels={"nation": "Nação", metric: METRIC_LABELS[metric], "world_cup_titles": "Títulos"},
    )
    fig.update_layout(**plotly_layout())
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    st.markdown("### Eficiência ofensiva × defensiva")
    fig2 = px.scatter(
        df[df["total_matches"] > 5],
        x="total_goals_for",
        y="total_goals_against",
        size="total_matches",
        color="world_cup_titles",
        hover_name="nation",
        color_continuous_scale=SEQUENTIAL_SCALE,
        title="Gols marcados × sofridos (tamanho = jogos disputados)",
        labels={
            "total_goals_for":     "Gols marcados",
            "total_goals_against": "Gols sofridos",
            "world_cup_titles":    "Títulos",
            "total_matches":       "Jogos",
        },
    )
    fig2.update_layout(**plotly_layout())
    st.plotly_chart(fig2, use_container_width=True)

    # Tabela com bandeiras
    st.markdown(f"### Top {top_n} — tabela detalhada")
    table_df = add_flag_column(
        top[["nation", "world_cup_titles", "wins", "draws", "losses",
             "total_goals_for", "editions_played", "win_pct"]].reset_index(drop=True)
    )
    st.dataframe(
        table_df,
        column_config={
            "flag_url":          st.column_config.ImageColumn("🏳️", width="small"),
            "nation":            st.column_config.TextColumn("Nação"),
            "world_cup_titles":  st.column_config.NumberColumn("Títulos"),
            "wins":              st.column_config.NumberColumn("Vitórias"),
            "draws":             st.column_config.NumberColumn("Empates"),
            "losses":            st.column_config.NumberColumn("Derrotas"),
            "total_goals_for":   st.column_config.NumberColumn("Gols pró"),
            "editions_played":   st.column_config.NumberColumn("Edições"),
            "win_pct":           st.column_config.NumberColumn("% vitórias", format="%.1f%%"),
        },
        use_container_width=True,
        hide_index=True,
    )

except Exception as e:
    st.warning(f"Execute o pipeline primeiro (`make all`). Detalhe: {e}")

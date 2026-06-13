import streamlit as st
import plotly.express as px
import duckdb
from pathlib import Path

st.set_page_config(page_title="Ranking Histórico", layout="wide")
st.title("🏆 Ranking Histórico por Nação")

DB_PATH = Path("data/world_cup.duckdb")


@st.cache_data
def load_data():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM mart_nations_performance").df()
    con.close()
    return df


try:
    df = load_data()

    top_n = st.slider("Top N nações", 5, 30, 15)
    metric = st.selectbox("Métrica", ["world_cup_titles", "wins", "total_goals_for", "editions_played"])

    top = df.nlargest(top_n, metric)

    fig = px.bar(
        top,
        x="nation",
        y=metric,
        color="world_cup_titles",
        color_continuous_scale="Viridis",
        title=f"Top {top_n} nações — {metric.replace('_', ' ').title()}",
        labels={"nation": "Nação", metric: metric.replace("_", " ").title()},
    )
    fig.update_layout(xaxis_tickangle=-45)
    st.plotly_chart(fig, use_container_width=True)

    st.subheader("Gols marcados × sofridos")
    fig2 = px.scatter(
        df[df["total_matches"] > 5],
        x="total_goals_for",
        y="total_goals_against",
        size="total_matches",
        color="world_cup_titles",
        hover_name="nation",
        color_continuous_scale="Blues",
        title="Eficiência ofensiva vs. defensiva (tamanho = jogos disputados)",
    )
    st.plotly_chart(fig2, use_container_width=True)

except Exception as e:
    st.warning(f"Execute o pipeline primeiro (`make all`). Detalhe: {e}")

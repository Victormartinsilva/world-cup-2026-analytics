import streamlit as st
import plotly.express as px
import duckdb
from pathlib import Path

st.set_page_config(page_title="Perfil dos Jogadores", layout="wide")
st.title("👤 Perfil dos Jogadores Convocados — 2026")

DB_PATH = Path("data/world_cup.duckdb")


@st.cache_data
def load_players():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM mart_players_profile").df()
    con.close()
    return df


try:
    df = load_players()

    nations = ["Todas"] + sorted(df["nation"].unique().tolist())
    selected_nation = st.selectbox("Filtrar por seleção", nations)

    filtered = df if selected_nation == "Todas" else df[df["nation"] == selected_nation]

    col1, col2 = st.columns(2)

    with col1:
        st.subheader("Valor de mercado × Idade")
        fig = px.scatter(
            filtered.dropna(subset=["market_value_eur_m"]),
            x="age",
            y="market_value_eur_m",
            color="position_group",
            hover_name="player_name",
            hover_data=["nation", "goals", "assists"],
            title="Valor de mercado (€M) × Idade",
            labels={"age": "Idade", "market_value_eur_m": "Valor (€M)", "position_group": "Posição"},
        )
        st.plotly_chart(fig, use_container_width=True)

    with col2:
        st.subheader("Distribuição por posição")
        pos_counts = filtered["position_group"].value_counts().reset_index()
        pos_counts.columns = ["Posição", "Jogadores"]
        fig2 = px.pie(pos_counts, names="Posição", values="Jogadores", title="Jogadores por posição")
        st.plotly_chart(fig2, use_container_width=True)

    st.subheader(f"Top 10 por valor de mercado — {selected_nation}")
    top10 = filtered.nlargest(10, "market_value_eur_m")[
        ["player_name", "nation", "position_group", "age", "goals", "assists", "market_value_eur_m"]
    ]
    st.dataframe(top10, use_container_width=True)

except Exception as e:
    st.warning(f"Execute o pipeline primeiro (`make all`). Detalhe: {e}")

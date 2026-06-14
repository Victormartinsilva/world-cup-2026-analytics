import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.express as px
import duckdb
from style import (
    inject_css, page_header, plotly_layout,
    add_flag_column, nation_pt, SEQUENTIAL_SCALE,
)

st.set_page_config(page_title="Ranking Histórico", layout="wide")
inject_css()
page_header(
    "🏆 Ranking Histórico por Nação",
    "Comparativo de desempenho entre as seleções classificadas para 2026.",
)

DB_PATH = Path("data/world_cup.duckdb")

# ── Mapeamento nação → confederação ───────────────────────────────────────────
_CONFED: dict[str, str] = {
    # CONMEBOL
    **{n: "CONMEBOL" for n in [
        "Brazil", "Argentina", "Uruguay", "Paraguay", "Chile", "Colombia",
        "Ecuador", "Peru", "Bolivia", "Venezuela",
    ]},
    # UEFA
    **{n: "UEFA" for n in [
        "Germany", "West Germany", "France", "Spain", "Italy", "England",
        "Netherlands", "Holland", "Belgium", "Portugal", "Croatia", "Poland",
        "Denmark", "Switzerland", "Sweden", "Norway", "Austria",
        "Czech Republic", "Czechia", "Czechoslovakia", "Hungary", "Romania",
        "Scotland", "Wales", "Turkey", "Türkiye", "Serbia", "Yugoslavia",
        "Slovakia", "Slovenia", "Bulgaria", "Russia", "Soviet Union", "Ukraine",
        "Bosnia and Herzegovina", "Montenegro", "Georgia", "North Macedonia",
        "Albania", "Kosovo", "Northern Ireland", "Finland", "Iceland", "Ireland",
    ]},
    # CONCACAF
    **{n: "CONCACAF" for n in [
        "United States", "USA", "Mexico", "Canada", "Costa Rica", "Honduras",
        "Jamaica", "Panama", "El Salvador", "Haiti", "Cuba",
        "Trinidad and Tobago", "Curaçao", "Guatemala",
    ]},
    # CAF
    **{n: "CAF" for n in [
        "Morocco", "Senegal", "Nigeria", "Egypt", "Cameroon", "Ghana",
        "Ivory Coast", "Côte d'Ivoire", "Tunisia", "Algeria", "South Africa",
        "Mali", "DR Congo", "Cape Verde", "Burkina Faso", "Guinea",
        "Angola", "Congo", "Togo", "Gabon", "Zambia", "Zimbabwe",
        "Tanzania", "Kenya",
    ]},
    # AFC
    **{n: "AFC" for n in [
        "Japan", "South Korea", "Korea Republic", "Iran", "Saudi Arabia",
        "Australia", "Qatar", "Iraq", "UAE", "United Arab Emirates",
        "China", "North Korea", "Indonesia", "Kuwait", "Bahrain",
        "Uzbekistan", "Jordan",
    ]},
    # OFC
    **{n: "OFC" for n in ["New Zealand", "Fiji"]},
}

METRIC_LABELS: dict[str, str] = {
    "world_cup_titles": "Títulos",
    "wins":             "Vitórias",
    "total_goals_for":  "Gols marcados",
    "editions_played":  "Edições disputadas",
    "win_pct":          "Aproveitamento %",
    "goals_per_game":   "Gols por jogo",
}


@st.cache_data
def load_data():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM mart_nations_performance").df()
    con.close()
    return df


try:
    df = load_data()

    # Calcula métricas derivadas
    df["goals_per_game"] = (
        df["total_goals_for"] / df["total_matches"].clip(lower=1)
    ).round(2)
    df["confederation"] = df["nation"].map(lambda n: _CONFED.get(n, "Outro"))
    df["nacao"] = df["nation"].map(nation_pt)

    # ── Controles ──────────────────────────────────────────────────────────────
    ctrl1, ctrl2, ctrl3 = st.columns([1, 2, 2])
    with ctrl1:
        top_n = st.slider("Top N nações", 5, 30, 15)
    with ctrl2:
        metric = st.selectbox(
            "Métrica",
            list(METRIC_LABELS.keys()),
            format_func=lambda k: METRIC_LABELS[k],
        )
    with ctrl3:
        confeds = sorted(df["confederation"].unique().tolist())
        sel_confeds = st.multiselect(
            "Confederação",
            confeds,
            default=confeds,
            placeholder="Todas",
        )

    # Filtra por confederação e seleciona top-N
    filtered = df[df["confederation"].isin(sel_confeds)] if sel_confeds else df
    top = filtered.nlargest(top_n, metric).copy()

    # ── Gráfico de barras ──────────────────────────────────────────────────────
    horizontal = top_n > 12
    bar_kwargs = dict(
        color="world_cup_titles",
        color_continuous_scale=SEQUENTIAL_SCALE,
        labels={
            "nacao": "Nação",
            "nation": "Nação (EN)",
            metric: METRIC_LABELS[metric],
            "world_cup_titles": "Títulos",
        },
        text=metric,
    )

    if horizontal:
        top_sorted = top.sort_values(metric, ascending=True)
        fig = px.bar(
            top_sorted,
            y="nacao",
            x=metric,
            orientation="h",
            **bar_kwargs,
        )
        fig.update_traces(
            texttemplate="%{x:.1f}" if "pct" in metric or "per" in metric
                         else "%{x}",
            textposition="outside",
        )
        fig.update_layout(
            **plotly_layout(title=f"Top {top_n} nações — {METRIC_LABELS[metric]}"),
            height=max(380, top_n * 28),
            yaxis_title="",
            xaxis_title=METRIC_LABELS[metric],
        )
    else:
        fig = px.bar(top, x="nacao", y=metric, **bar_kwargs)
        fig.update_traces(
            texttemplate="%{y:.1f}" if "pct" in metric or "per" in metric
                         else "%{y}",
            textposition="outside",
        )
        fig.update_layout(
            **plotly_layout(title=f"Top {top_n} nações — {METRIC_LABELS[metric]}"),
            xaxis_tickangle=-40,
            yaxis_title=METRIC_LABELS[metric],
        )

    st.plotly_chart(fig, use_container_width=True)

    # ── Scatter: eficiência ofensiva × defensiva ───────────────────────────────
    st.markdown("### ⚽ Eficiência ofensiva × defensiva")
    scatter_df = filtered[filtered["total_matches"] > 5].copy()
    fig2 = px.scatter(
        scatter_df,
        x="total_goals_for",
        y="total_goals_against",
        size="total_matches",
        color="world_cup_titles",
        hover_name="nacao",
        color_continuous_scale=SEQUENTIAL_SCALE,
        labels={
            "total_goals_for":     "Gols marcados",
            "total_goals_against": "Gols sofridos",
            "world_cup_titles":    "Títulos",
            "total_matches":       "Jogos",
        },
    )
    # Rótulos de texto nas bolhas (apenas quando há ≤ 20 nações para não poluir)
    if len(scatter_df) <= 20:
        fig2.update_traces(
            text=scatter_df["nacao"],
            textposition="top center",
            textfont=dict(size=8, color="#cce8d8"),
            mode="markers+text",
        )

    # Linha diagonal (x = y) como referência de equilíbrio
    max_v = max(scatter_df["total_goals_for"].max(), scatter_df["total_goals_against"].max())
    fig2.add_shape(
        type="line", x0=0, y0=0, x1=max_v, y1=max_v,
        line=dict(color="rgba(255,255,255,0.15)", width=1, dash="dot"),
    )
    fig2.update_layout(
        **plotly_layout(title="Gols marcados × sofridos (tamanho = jogos disputados)")
    )
    st.plotly_chart(fig2, use_container_width=True)

    # ── Tabela detalhada ───────────────────────────────────────────────────────
    st.markdown(f"### 📋 Top {top_n} — tabela detalhada")
    tbl_df = top[
        ["nation", "nacao", "confederation", "world_cup_titles", "wins", "draws",
         "losses", "total_goals_for", "editions_played", "win_pct", "goals_per_game"]
    ].reset_index(drop=True)
    table_df = add_flag_column(tbl_df, nation_col="nation")
    st.dataframe(
        table_df[[
            "flag_url", "nacao", "confederation", "world_cup_titles",
            "wins", "draws", "losses", "total_goals_for",
            "editions_played", "win_pct", "goals_per_game",
        ]],
        column_config={
            "flag_url":          st.column_config.ImageColumn("🏳️", width="small"),
            "nacao":             st.column_config.TextColumn("Nação"),
            "confederation":     st.column_config.TextColumn("Confed."),
            "world_cup_titles":  st.column_config.NumberColumn("Títulos"),
            "wins":              st.column_config.NumberColumn("V"),
            "draws":             st.column_config.NumberColumn("E"),
            "losses":            st.column_config.NumberColumn("D"),
            "total_goals_for":   st.column_config.NumberColumn("Gols pró"),
            "editions_played":   st.column_config.NumberColumn("Edições"),
            "win_pct":           st.column_config.NumberColumn("Aproveito.", format="%.1f%%"),
            "goals_per_game":    st.column_config.NumberColumn("Gols/jogo", format="%.2f"),
        },
        use_container_width=True,
        hide_index=True,
    )

except Exception:
    st.warning(
        "Os dados ainda não estão disponíveis. "
        "Certifique-se de que a ingestão e a transformação foram concluídas antes de abrir o painel."
    )

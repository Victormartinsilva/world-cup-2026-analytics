import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import pandas as pd
import plotly.graph_objects as go
import streamlit as st
import duckdb
from style import (
    inject_css, plotly_layout, flag_url, nation_pt,
    NATION_TO_ISO2, GREEN, YELLOW, BLUE, SEQUENTIAL_SCALE,
)

st.set_page_config(page_title="Análise por Nação", layout="wide")
inject_css()

DB_PATH = Path("data/world_cup.duckdb")

# ── Dicionário de títulos por nação ───────────────────────────────────────────
_TITLE_YEARS: dict[str, list[int]] = {
    "Brazil":       [1958, 1962, 1970, 1994, 2002],
    "Germany":      [1954, 1974, 1990, 2014],
    "West Germany": [1954, 1974, 1990],
    "Italy":        [1934, 1938, 1982, 2006],
    "Argentina":    [1978, 1986, 2022],
    "France":       [1998, 2018],
    "Uruguay":      [1930, 1950],
    "England":      [1966],
    "Spain":        [2010],
}

_STAGE_PT = {
    "Group Stage": "Fase de Grupos", "Round of 16": "Oitavas de Final",
    "Quarter-finals": "Quartas de Final", "Semi-finals": "Semifinal",
    "Third Place": "3º Lugar", "Final": "Final",
}

# ── Carga de dados ────────────────────────────────────────────────────────────

@st.cache_data
def load_nations_list() -> list[str]:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    rows = con.execute("""
        SELECT DISTINCT home_team AS n FROM stg_matches
        UNION SELECT DISTINCT away_team FROM stg_matches
        ORDER BY n
    """).fetchall()
    con.close()
    return [r[0] for r in rows if r[0]]


@st.cache_data
def load_history(nation: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    if nation == "Brazil":
        try:
            df = con.execute("SELECT * FROM mart_brazil_deep ORDER BY edition_year").df()
            con.close()
            if not df.empty:
                return df
        except Exception:
            pass
    df = con.execute("""
        SELECT
            edition_year,
            COUNT(*)                                                                 AS games,
            SUM(CASE WHEN (home_team=? AND home_goals>away_goals)
                       OR (away_team=? AND away_goals>home_goals) THEN 1 ELSE 0 END) AS wins,
            SUM(CASE WHEN home_goals=away_goals THEN 1 ELSE 0 END)                 AS draws,
            SUM(CASE WHEN (home_team=? AND home_goals<away_goals)
                       OR (away_team=? AND away_goals<home_goals) THEN 1 ELSE 0 END) AS losses,
            SUM(CASE WHEN home_team=? THEN home_goals ELSE away_goals END)         AS goals_scored,
            SUM(CASE WHEN home_team=? THEN away_goals ELSE home_goals END)         AS goals_conceded
        FROM stg_matches
        WHERE home_team=? OR away_team=?
        GROUP BY edition_year
        ORDER BY edition_year
    """, [nation]*8).df()
    con.close()
    return df


@st.cache_data
def load_matches(nation: str) -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("""
        SELECT * FROM stg_matches
        WHERE home_team=? OR away_team=?
        ORDER BY edition_year, stage
    """, [nation, nation]).df()
    con.close()
    return df


# ── Seletor de nação ──────────────────────────────────────────────────────────
try:
    _all_nations = load_nations_list()
except Exception:
    _all_nations = ["Brazil"]

_POPULAR = [
    "Brazil", "Germany", "Argentina", "France", "Italy",
    "Spain", "England", "Uruguay", "Portugal", "Netherlands",
]
_popular_avail = [n for n in _POPULAR if n in _all_nations]
_others        = sorted(n for n in _all_nations if n not in _POPULAR)

ctrl_col, _ = st.columns([2, 3])
with ctrl_col:
    selected_nation = st.selectbox(
        "🌍 Selecionar nação",
        _popular_avail + _others,
        index=0,
        format_func=lambda n: f"{nation_pt(n)} ({n})" if nation_pt(n) != n else n,
        key="deep_dive_nation",
    )

nation_name_pt = nation_pt(selected_nation)
iso            = NATION_TO_ISO2.get(selected_nation, "")
flag_img       = f'<img src="{flag_url(iso, width=72)}" width="72" style="border-radius:6px;box-shadow:0 4px 16px rgba(0,0,0,0.5);flex-shrink:0">' if iso else ""
titles_years   = _TITLE_YEARS.get(selected_nation, [])
n_titles       = len(titles_years)
titles_str     = ", ".join(str(y) for y in sorted(titles_years)) if titles_years else "—"

st.markdown(
    f'<div style="background:linear-gradient(135deg,#012A1C 0%,#014D24 60%,#002776 100%);'
    f'padding:1.6rem 2rem;border-radius:12px;border-left:5px solid #FFDF00;'
    f'margin-bottom:1.6rem;display:flex;align-items:center;gap:1.4rem">'
    f'{flag_img}'
    f'<div>'
    f'<h1 style="color:#FFDF00;font-family:\'Barlow Condensed\',sans-serif;'
    f'font-size:2.2rem;margin:0;font-weight:700;letter-spacing:0.03em">'
    f'{nation_name_pt} — Análise Completa</h1>'
    f'<p style="color:#cce8d8;margin:0.5rem 0 0;font-size:0.95rem;font-family:Inter,sans-serif">'
    f'{"🏆 " + str(n_titles) + " título(s): " + titles_str if n_titles else "Nenhum título mundial"}'
    f'</p>'
    f'</div></div>',
    unsafe_allow_html=True,
)

try:
    df = load_history(selected_nation)

    if df.empty:
        st.info(f"{nation_name_pt} não possui dados históricos no banco. Execute `make all`.")
        st.stop()

    # Normaliza colunas (mart_brazil_deep pode ter nomes ligeiramente diferentes)
    if "goals_scored"   not in df.columns and "goals_for"    in df.columns:
        df = df.rename(columns={"goals_for": "goals_scored"})
    if "goals_conceded" not in df.columns and "goals_against" in df.columns:
        df = df.rename(columns={"goals_against": "goals_conceded"})
    if "games"          not in df.columns and "matches_played" in df.columns:
        df = df.rename(columns={"matches_played": "games"})

    # ── KPIs ─────────────────────────────────────────────────────────────────
    editions  = int(df["edition_year"].nunique())
    total_w   = int(df["wins"].sum())     if "wins"           in df.columns else "—"
    total_g   = int(df["goals_scored"].sum()) if "goals_scored" in df.columns else "—"
    total_gc  = int(df["goals_conceded"].sum()) if "goals_conceded" in df.columns else "—"

    k1, k2, k3, k4, k5 = st.columns(5)
    k1.metric("Títulos", n_titles if n_titles else "0")
    k2.metric("Edições", editions)
    k3.metric("Vitórias", total_w)
    k4.metric("Gols marcados", total_g)
    k5.metric("Gols sofridos", total_gc)

    # ── Cards de destaque (melhor/pior edição) ────────────────────────────────
    if "wins" in df.columns and "goals_scored" in df.columns:
        df["pts"] = df["wins"] * 3 + df.get("draws", 0).fillna(0) if "draws" in df.columns \
                    else df["wins"] * 3
        df_card = df[df["games"] >= 3] if "games" in df.columns else df
        if not df_card.empty:
            best_row  = df_card.loc[df_card["pts"].idxmax()]
            worst_row = df_card.loc[df_card["pts"].idxmin()]
            best_y    = int(best_row["edition_year"])
            worst_y   = int(worst_row["edition_year"])
            best_is_title = best_y in titles_years

            def _highlight_card(year: int, label: str, pts: int, wins: int,
                                 gols: int, color: str, icon: str) -> str:
                return (
                    f'<div style="background:#012A1C;border-radius:10px;'
                    f'border:1px solid {color};padding:1rem 1.2rem;height:100%">'
                    f'<div style="color:{color};font-size:0.65rem;font-weight:700;'
                    f'text-transform:uppercase;letter-spacing:1px;font-family:Inter,sans-serif;'
                    f'margin-bottom:4px">{label}</div>'
                    f'<div style="display:flex;align-items:baseline;gap:8px">'
                    f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:2.2rem;'
                    f'font-weight:700;color:{color}">{icon} {year}</span>'
                    f'</div>'
                    f'<div style="color:#9E9E9E;font-size:0.78rem;margin-top:4px;'
                    f'font-family:Inter,sans-serif">'
                    f'{wins} vitórias · {gols} gols · {pts} pts</div>'
                    f'</div>'
                )

            hc1, hc2, hc3 = st.columns(3)
            with hc1:
                st.markdown(_highlight_card(
                    best_y, "Melhor Copa",
                    int(best_row["pts"]), int(best_row["wins"]),
                    int(best_row["goals_scored"]),
                    YELLOW, "🏆" if best_is_title else "⭐",
                ), unsafe_allow_html=True)
            with hc2:
                st.markdown(_highlight_card(
                    worst_y, "Copa mais difícil",
                    int(worst_row["pts"]), int(worst_row["wins"]),
                    int(worst_row["goals_scored"]) if "goals_scored" in worst_row else 0,
                    "#EF5350", "📉",
                ), unsafe_allow_html=True)
            with hc3:
                avg_wins  = round(df["wins"].mean(), 1)
                avg_goals = round(df["goals_scored"].mean(), 1) if "goals_scored" in df.columns else "—"
                st.markdown(
                    f'<div style="background:#012A1C;border-radius:10px;'
                    f'border:1px solid {GREEN};padding:1rem 1.2rem;height:100%">'
                    f'<div style="color:{GREEN};font-size:0.65rem;font-weight:700;'
                    f'text-transform:uppercase;letter-spacing:1px;font-family:Inter,sans-serif;'
                    f'margin-bottom:4px">Média por Copa</div>'
                    f'<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:2rem;'
                    f'font-weight:700;color:{GREEN}">{avg_wins} V</div>'
                    f'<div style="color:#9E9E9E;font-size:0.78rem;margin-top:4px;'
                    f'font-family:Inter,sans-serif">'
                    f'{avg_goals} gols/Copa · {editions} edições</div>'
                    f'</div>',
                    unsafe_allow_html=True,
                )
        st.markdown("")

    # ── Gráfico: desempenho por edição ────────────────────────────────────────
    st.markdown("### 📈 Desempenho por edição")

    fig = go.Figure()

    # Realces nas edições de título
    for yr in titles_years:
        if yr in df["edition_year"].values:
            fig.add_vrect(
                x0=yr - 1, x1=yr + 1,
                fillcolor="rgba(255,223,0,0.08)",
                line_width=0,
                annotation_text="🏆",
                annotation_position="top left",
                annotation_font_size=14,
            )

    if "goals_scored" in df.columns:
        fig.add_trace(go.Bar(
            x=df["edition_year"], y=df["goals_scored"],
            name="Gols marcados", marker_color=GREEN,
        ))
    if "goals_conceded" in df.columns:
        fig.add_trace(go.Bar(
            x=df["edition_year"], y=df["goals_conceded"],
            name="Gols sofridos", marker_color=YELLOW,
        ))
    if "wins" in df.columns:
        fig.add_trace(go.Scatter(
            x=df["edition_year"], y=df["wins"],
            name="Vitórias", mode="lines+markers", yaxis="y2",
            line=dict(color="#40C4FF", width=2.5),
            marker=dict(size=8, color="#40C4FF", line=dict(color=BLUE, width=1.5)),
        ))

    layout = plotly_layout(
        title=f"Gols e vitórias de {nation_name_pt} por edição"
    )
    layout["yaxis2"] = dict(
        title=dict(text="Vitórias", font=dict(color="#F0F0F0")),
        overlaying="y", side="right",
        gridcolor="#1a3d25", linecolor=GREEN,
        tickfont=dict(color="#F0F0F0"),
    )
    fig.update_layout(**layout, barmode="group", xaxis_title="Edição", yaxis_title="Gols")
    st.plotly_chart(fig, use_container_width=True)

    # ── Tabela de confrontos ───────────────────────────────────────────────────
    st.markdown("### 📋 Resultado por partida")
    df_matches = load_matches(selected_nation)

    _col_map = {
        "edition_year": "Edição", "stage": "Fase",
        "home_team": "Mandante", "home_goals": "Gols (M)",
        "away_goals": "Gols (V)", "away_team": "Visitante",
        "stadium": "Estádio", "city": "Cidade",
    }
    show_cols = [c for c in _col_map if c in df_matches.columns]
    tbl = df_matches[show_cols].copy()

    for tc in ("home_team", "away_team"):
        if tc in tbl.columns:
            tbl[tc] = tbl[tc].map(lambda n: nation_pt(str(n)) if n else n)
    if "stage" in tbl.columns:
        tbl["stage"] = tbl["stage"].map(lambda s: _STAGE_PT.get(str(s), str(s)))

    # Destaca finais e semifinais
    def _row_style(row):
        if row.get("stage") in ("Final", "Semifinal", "3º Lugar"):
            return ["background-color: rgba(255,223,0,0.06)"] * len(row)
        return [""] * len(row)

    tbl.rename(columns={c: _col_map[c] for c in show_cols}, inplace=True)
    st.dataframe(tbl, use_container_width=True, hide_index=True)

    # ── Aproveitamento vs adversários (confrontos diretos) ─────────────────────
    if not df_matches.empty and "home_team" in df_matches.columns:
        st.markdown("### 🤝 Confrontos diretos — aproveitamento por adversário")
        records = []
        for _, r in df_matches.iterrows():
            opp = r["away_team"] if r["home_team"] == selected_nation else r["home_team"]
            my_goals = r["home_goals"] if r["home_team"] == selected_nation else r["away_goals"]
            op_goals = r["away_goals"] if r["home_team"] == selected_nation else r["home_goals"]
            result = "V" if my_goals > op_goals else ("E" if my_goals == op_goals else "D")
            records.append({"opp": opp, "result": result, "gf": my_goals, "ga": op_goals})

        h2h = pd.DataFrame(records)
        agg = (
            h2h.groupby("opp")
            .agg(
                Jogos=("result", "count"),
                Vitórias=("result", lambda x: (x == "V").sum()),
                Empates=("result",  lambda x: (x == "E").sum()),
                Derrotas=("result", lambda x: (x == "D").sum()),
                GolsPro=("gf", "sum"),
                GolsCon=("ga", "sum"),
            )
            .reset_index()
            .rename(columns={"opp": "Adversário"})
        )
        agg["Aproveit.%"] = (agg["Vitórias"] * 3 / (agg["Jogos"] * 3) * 100).round(1)
        agg["Adversário"] = agg["Adversário"].map(nation_pt)
        agg = agg.sort_values("Jogos", ascending=False)

        import plotly.express as px
        top_opps = agg.head(15)
        fig_h2h = px.bar(
            top_opps,
            x="Adversário",
            y="Vitórias",
            color="Aproveit.%",
            color_continuous_scale=SEQUENTIAL_SCALE,
            text="Jogos",
            labels={"Vitórias": "Vitórias", "Adversário": "Adversário"},
        )
        fig_h2h.update_traces(texttemplate="%{text}j", textposition="outside")
        fig_h2h.update_layout(
            **plotly_layout(title=f"Vitórias de {nation_name_pt} por adversário (Top 15)"),
            xaxis_tickangle=-40,
        )
        st.plotly_chart(fig_h2h, use_container_width=True)

        with st.expander("Ver tabela completa de confrontos diretos"):
            st.dataframe(agg, use_container_width=True, hide_index=True)

except Exception as e:
    st.error(f"Não foi possível carregar os dados. Tente recarregar a página. ({type(e).__name__})")

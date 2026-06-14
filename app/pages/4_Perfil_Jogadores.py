import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import streamlit as st
import plotly.express as px
import plotly.graph_objects as go
import pandas as pd
import duckdb
from style import (
    inject_css, page_header, plotly_layout,
    add_flag_column, nation_flag_html, nation_pt,
    CHART_PALETTE, POSITION_COLORS, SEQUENTIAL_SCALE,
    GREEN, YELLOW, BLUE,
)
from player_photos import load_photos

st.set_page_config(page_title="Perfil dos Jogadores", layout="wide")
inject_css()
page_header(
    "👤 Perfil dos Jogadores Convocados — 2026",
    "Figurinhas, valor de mercado, distribuição etária e radar de desempenho.",
)

DB_PATH = Path("data/world_cup.duckdb")

# ── Pré-seleção vinda da página principal ─────────────────────────────────────
_preselect = st.session_state.pop("selected_nation", "Todas") if "selected_nation" in st.session_state else "Todas"

# ── Tradução de posições ──────────────────────────────────────────────────────
_POS_PT: dict[str, str] = {
    "Goalkeeper": "Goleiro",  "GK": "Goleiro",
    "Defender":   "Defensor", "DF": "Defensor",
    "Midfielder": "Meia",     "MF": "Meia",
    "Forward":    "Atacante", "FW": "Atacante",
    "Unknown":    "Outro",
}

# nation_pt() importado de style.py — substitui o dict local anterior
_POS_COLORS_PT: dict[str, str] = {
    "Goleiro":  YELLOW,
    "Defensor": "#40C4FF",
    "Meia":     GREEN,
    "Atacante": "#FF5252",
    "Outro":    "#757575",
}


@st.cache_data(show_spinner="Carregando dados dos jogadores…")
def load_players() -> pd.DataFrame:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute("SELECT * FROM mart_players_profile").df()
    con.close()
    # Adiciona coluna de posição em português para uso nos gráficos
    df["posicao"] = df["position_group"].map(lambda x: _POS_PT.get(str(x), str(x)))
    return df


try:
    df = load_players()
except Exception as e:
    st.warning(f"Execute o pipeline primeiro (`make all`). Detalhe: {e}")
    st.stop()

# ── Filtros principais ────────────────────────────────────────────────────────
nations = ["Todas"] + sorted(df["nation"].dropna().unique().tolist())
default_idx = nations.index(_preselect) if _preselect in nations else 0

col_sel, col_pos = st.columns([2, 2])
with col_sel:
    selected_nation = st.selectbox("🏳️ Seleção", nations, index=default_idx)
with col_pos:
    pos_options_pt = ["Todas"] + sorted(
        df["posicao"].dropna().unique().tolist(), key=lambda x: ["Goleiro","Defensor","Meia","Atacante","Outro"].index(x) if x in ["Goleiro","Defensor","Meia","Atacante","Outro"] else 99
    )
    selected_pos_pt = st.selectbox("🎽 Posição", pos_options_pt)

filtered = df.copy()
if selected_nation != "Todas":
    filtered = filtered[filtered["nation"] == selected_nation]
if selected_pos_pt != "Todas":
    filtered = filtered[filtered["posicao"] == selected_pos_pt]

# Indicador de filtros ativos
if selected_nation != "Todas" or selected_pos_pt != "Todas":
    chips_html = ""
    if selected_nation != "Todas":
        flag_chip = nation_flag_html(selected_nation, width=22)
        nation_display = nation_pt(selected_nation)
        chips_html += (
            f'<span style="display:inline-flex;align-items:center;gap:6px;'
            f'background:#013d20;border:1px solid {GREEN};border-radius:20px;'
            f'padding:3px 10px 3px 6px;font-size:0.82rem;color:#cce8d8;'
            f'font-family:Inter,sans-serif">{flag_chip} {nation_display}</span>'
        )
    if selected_pos_pt != "Todas":
        pos_color = _POS_COLORS_PT.get(selected_pos_pt, "#80CBC4")
        chips_html += (
            f'<span style="display:inline-flex;align-items:center;gap:5px;'
            f'background:#013d20;border:1px solid {pos_color};border-radius:20px;'
            f'padding:3px 10px;font-size:0.82rem;color:{pos_color};'
            f'font-family:Inter,sans-serif;font-weight:600">🎽 {selected_pos_pt}</span>'
        )
    st.markdown(
        f'<div style="display:flex;align-items:center;gap:8px;margin-bottom:0.8rem;flex-wrap:wrap">'
        f'<span style="color:{YELLOW};font-size:0.7rem;font-weight:600;text-transform:uppercase;'
        f'letter-spacing:1px;font-family:Inter,sans-serif">Filtrando</span>'
        f'{chips_html}'
        f'<span style="color:#80CBC4;font-size:0.82rem">{len(filtered)} jogadores</span>'
        f'</div>',
        unsafe_allow_html=True,
    )

# ── Métricas rápidas ─────────────────────────────────────────────────────────
m1, m2, m3, m4 = st.columns(4)
mv_total = filtered["market_value_eur_m"].sum()
avg_age = filtered["age"].mean()
top_scorer = filtered.nlargest(1, "goals")
scorer_name = top_scorer["player_name"].iloc[0] if not top_scorer.empty else "—"
scorer_goals = int(top_scorer["goals"].iloc[0]) if not top_scorer.empty else 0
scorer_short = scorer_name[:10] + "…" if len(scorer_name) > 10 else scorer_name

m1.metric("Valor total do elenco", f"€{mv_total:.0f}M")
m2.metric("Média de idade", f"{avg_age:.1f} anos" if not pd.isna(avg_age) else "—")
m3.metric("Jogadores", str(len(filtered)))
m4.metric(
    "Artilheiro",
    scorer_short,
    delta=f"{scorer_goals} gols" if scorer_goals else None,
    help=scorer_name,
)

st.markdown("---")

# ══════════════════════════════════════════════════════════════════════════════
# TABS
# ══════════════════════════════════════════════════════════════════════════════
tab_cards, tab_analysis, tab_detail = st.tabs(["🃏 Figurinhas", "📊 Análise", "🔬 Jogador"])

# ─────────────────────────────────────────────────────────────────────────────
# TAB 1 — FIGURINHAS
# ─────────────────────────────────────────────────────────────────────────────
with tab_cards:
    _search_col, _sort_col_ui = st.columns([2, 2])
    with _search_col:
        search_query = st.text_input(
            "🔍 Buscar jogador",
            placeholder="Ex: Vinícius, Kane, Mbappé…",
            key="player_search",
        )
    with _sort_col_ui:
        sort_by = st.radio(
            "Ordenar por",
            ["💰 Valor", "⚽ Gols", "🎯 Assist.", "📅 Idade"],
            horizontal=True,
            key="cards_sort",
        )

    cards_df = filtered.copy()
    if search_query.strip():
        cards_df = cards_df[
            cards_df["player_name"].str.contains(search_query.strip(), case=False, na=False)
        ]

    player_names = cards_df["player_name"].dropna().tolist()

    with st.spinner("Buscando fotos (Wikipedia Commons)…"):
        photos = load_photos(player_names)

    def _tier(mv: float) -> tuple[str, str, str, str]:
        """(label, border_color, glow_color, badge_gradient)"""
        if mv >= 100:
            return (
                "OURO", "#FFD700",
                "rgba(255,215,0,0.55)",
                "linear-gradient(135deg,#B8860B,#FFD700,#B8860B)",
            )
        if mv >= 50:
            return (
                "PRATA", "#C0C0C0",
                "rgba(192,192,192,0.4)",
                "linear-gradient(135deg,#808080,#D8D8D8,#808080)",
            )
        return (
            "BASE", GREEN,
            "rgba(0,156,59,0.25)",
            f"linear-gradient(135deg,#013d20,{GREEN},#013d20)",
        )

    def _initials_avatar(name: str, color: str = GREEN) -> str:
        parts = [p for p in name.split() if p]
        if len(parts) >= 2:
            ini = f"{parts[0][0]}{parts[-1][0]}".upper()
        else:
            ini = name[:2].upper()
        return (
            f'<div style="width:72px;height:72px;border-radius:50%;'
            f'background:linear-gradient(135deg,#013d20,{color});'
            f'display:flex;align-items:center;justify-content:center;'
            f'font-family:Barlow Condensed,sans-serif;font-size:1.55rem;'
            f'font-weight:700;color:#FFDF00;letter-spacing:1px">{ini}</div>'
        )

    def _stat_cell(val: str, label: str, color: str) -> str:
        return (
            f'<div style="text-align:center;background:#011a10;border-radius:4px;padding:3px 1px">'
            f'<div style="color:{color};font-weight:700;font-size:0.82rem;'
            f'font-family:\'Barlow Condensed\',sans-serif">{val}</div>'
            f'<div style="color:#424242;font-size:0.48rem;text-transform:uppercase;'
            f'letter-spacing:0.5px;font-family:Inter,sans-serif">{label}</div>'
            f'</div>'
        )

    def _card_html(row: pd.Series, photo_url: str) -> str:
        mv = float(row.get("market_value_eur_m") or 0)
        goals = int(row.get("goals") or 0)
        assists = int(row.get("assists") or 0)
        mp = int(row.get("matches_played") or 0)
        age = int(row.get("age") or 0)
        pos_raw = str(row.get("position_group") or "")
        pos_pt = _POS_PT.get(pos_raw, pos_raw) or "?"
        is_gk = pos_raw in ("Goalkeeper", "GK")
        nation = str(row.get("nation") or "")
        name = str(row.get("player_name") or "")
        tier_label, border, glow, badge_bg = _tier(mv)

        # Nome — fonte menor para nomes longos
        name_size = "0.78rem" if len(name) > 16 else "0.88rem" if len(name) > 12 else "0.94rem"

        flag_img = nation_flag_html(nation, width=26)
        pos_color = _POS_COLORS_PT.get(pos_pt, "#80CBC4")

        # Seção da foto
        if photo_url:
            photo_section = (
                f'<div style="height:130px;overflow:hidden;background:#011a10;'
                f'display:flex;align-items:center;justify-content:center">'
                f'<img src="{photo_url}" '
                f'style="width:100%;height:100%;object-fit:cover;object-position:top center" '
                f'onerror="this.onerror=null;this.style.display=\'none\';'
                f'this.parentNode.innerHTML=\'<div style=&quot;width:100%;height:130px;'
                f'display:flex;align-items:center;justify-content:center;&quot;>'
                f'<div style=&quot;width:72px;height:72px;border-radius:50%;'
                f'background:linear-gradient(135deg,#013d20,#009C3B);'
                f'display:flex;align-items:center;justify-content:center;'
                f'font-size:1.55rem;font-weight:700;color:#FFDF00&quot;>👤</div></div>\'">'
                f'</div>'
            )
        else:
            tier_color = {"OURO": "#FFD700", "PRATA": "#C0C0C0"}.get(tier_label, GREEN)
            photo_section = (
                f'<div style="height:130px;background:linear-gradient(160deg,#012A1C,#011a10);'
                f'display:flex;align-items:center;justify-content:center">'
                + _initials_avatar(name, tier_color)
                + f'</div>'
            )

        # Badge
        badge_html = (
            f'<div style="position:absolute;top:6px;right:6px;'
            f'background:{badge_bg};padding:2px 7px;border-radius:20px;'
            f'font-size:0.5rem;font-weight:800;color:{"#000" if tier_label in ("OURO","PRATA") else "#fff"};'
            f'letter-spacing:1.5px;font-family:Inter,sans-serif;'
            f'text-transform:uppercase;white-space:nowrap">{tier_label}</div>'
        )

        # Stats bottom (goleiros: JGS no lugar de GOL)
        if is_gk:
            stat1 = _stat_cell(str(mp), "JGS", YELLOW)
            stat2 = _stat_cell("GK", "POS", "#80CBC4")
        else:
            stat1 = _stat_cell(str(goals), "GOL", YELLOW)
            stat2 = _stat_cell(str(assists), "ASS", "#40C4FF")

        stat3 = _stat_cell(f"€{mv:.0f}M" if mv >= 1 else "—", "VALOR", "#69F0AE")

        return (
            f'<div style="width:158px;background:linear-gradient(165deg,#012A1C 0%,#011a10 100%);'
            f'border-radius:14px;border:2px solid {border};'
            f'box-shadow:0 4px 22px {glow};overflow:hidden;position:relative;'
            f'display:inline-block;margin:6px;vertical-align:top">'
            f'{photo_section}'
            f'{badge_html}'
            f'<div style="padding:8px 9px 9px">'
            f'<div style="color:#FFDF00;font-family:\'Barlow Condensed\',sans-serif;'
            f'font-size:{name_size};font-weight:700;line-height:1.2;margin-bottom:5px;'
            f'white-space:nowrap;overflow:hidden;text-overflow:ellipsis" title="{name}">'
            f'{name}</div>'
            f'<div style="display:flex;align-items:center;gap:5px;margin-bottom:7px">'
            f'{flag_img}'
            f'<span style="background:#013d20;padding:1px 6px;border-radius:3px;'
            f'color:{pos_color};font-size:0.58rem;font-family:Inter,sans-serif;'
            f'font-weight:600;white-space:nowrap">{pos_pt}</span>'
            f'<span style="color:#616161;font-size:0.6rem">{age}a</span>'
            f'</div>'
            f'<div style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:3px">'
            f'{stat1}{stat2}{stat3}'
            f'</div>'
            f'</div>'
            f'</div>'
        )

    # Ordenação conforme seleção do usuário
    _sort_map = {
        "💰 Valor":   ("market_value_eur_m", False),
        "⚽ Gols":    ("goals", False),
        "🎯 Assist.": ("assists", False),
        "📅 Idade":   ("age", True),
    }
    _sort_field, _sort_asc = _sort_map.get(sort_by, ("market_value_eur_m", False))
    sorted_df = cards_df.sort_values(_sort_field, ascending=_sort_asc, na_position="last")

    if sorted_df.empty:
        st.info("Nenhum jogador encontrado para os filtros selecionados.")
    else:
        st.markdown(
            f'<div style="display:flex;flex-wrap:wrap;gap:0px">'
            + "".join(
                _card_html(row, photos.get(row["player_name"], ""))
                for _, row in sorted_df.iterrows()
            )
            + "</div>",
            unsafe_allow_html=True,
        )

# ─────────────────────────────────────────────────────────────────────────────
# TAB 2 — ANÁLISE
# ─────────────────────────────────────────────────────────────────────────────
with tab_analysis:
    plot_df = filtered.dropna(subset=["age", "market_value_eur_m"]).copy()
    plot_df["goals"] = plot_df["goals"].fillna(0)
    plot_df["assists"] = plot_df["assists"].fillna(0)
    plot_df["matches_played"] = plot_df["matches_played"].fillna(0)

    if plot_df.empty:
        st.info("Nenhum dado disponível para os filtros selecionados.")
    else:
        # ── Scatter: Idade × Valor de mercado ────────────────────────────────
        st.markdown("### 💰 Valor de mercado × Idade")
        fig_scatter = px.scatter(
            plot_df,
            x="age",
            y="market_value_eur_m",
            color="posicao",
            color_discrete_map=_POS_COLORS_PT,
            size="market_value_eur_m",
            size_max=32,
            custom_data=[
                "player_name", "nation", "goals", "assists",
                "matches_played", "posicao", "market_value_eur_m",
            ],
            labels={
                "age": "Idade",
                "market_value_eur_m": "Valor (€M)",
                "posicao": "Posição",
            },
        )
        fig_scatter.update_traces(
            hovertemplate=(
                "<b>%{customdata[0]}</b><br>"
                "🏳️ %{customdata[1]}<br>"
                "📅 %{x} anos · 🎽 %{customdata[5]}<br>"
                "💰 <b>€%{customdata[6]:.1f}M</b><br>"
                "⚽ %{customdata[2]:.0f} gols · 🎯 %{customdata[3]:.0f} assist.<br>"
                "🎮 %{customdata[4]:.0f} partidas"
                "<extra></extra>"
            ),
            marker=dict(opacity=0.88, line=dict(width=0.8, color="#0B1A12")),
        )
        fig_scatter.update_layout(**plotly_layout(), height=420)
        st.plotly_chart(fig_scatter, use_container_width=True)

        col_left, col_right = st.columns(2)

        # ── Bar: Valor médio por posição ──────────────────────────────────────
        with col_left:
            st.markdown("### 📊 Valor médio por posição")
            pos_mv = (
                plot_df.groupby("posicao")["market_value_eur_m"]
                .agg(["mean", "count", "sum"])
                .reset_index()
                .rename(columns={
                    "posicao": "Posição",
                    "mean": "Valor médio (€M)",
                    "count": "Jogadores",
                    "sum": "Total (€M)",
                })
                .sort_values("Valor médio (€M)", ascending=False)
            )
            fig_bar = px.bar(
                pos_mv,
                x="Posição",
                y="Valor médio (€M)",
                color="Posição",
                color_discrete_map=_POS_COLORS_PT,
                text="Jogadores",
                custom_data=["Jogadores", "Total (€M)"],
            )
            fig_bar.update_traces(
                texttemplate="%{text} jog.",
                textposition="outside",
                hovertemplate=(
                    "<b>%{x}</b><br>"
                    "Valor médio: €%{y:.1f}M<br>"
                    "Jogadores: %{customdata[0]}<br>"
                    "Total do grupo: €%{customdata[1]:.0f}M"
                    "<extra></extra>"
                ),
            )
            fig_bar.update_layout(**plotly_layout(), showlegend=False, height=360)
            st.plotly_chart(fig_bar, use_container_width=True)

        # ── Histograma: Distribuição etária ───────────────────────────────────
        with col_right:
            st.markdown("### 📅 Distribuição etária")
            # CORREÇÃO: px.histogram não aceita custom_data — removido
            fig_hist = px.histogram(
                plot_df,
                x="age",
                color="posicao",
                color_discrete_map=_POS_COLORS_PT,
                nbins=15,
                barmode="stack",
                labels={"age": "Idade", "count": "Jogadores", "posicao": "Posição"},
            )
            fig_hist.update_traces(
                hovertemplate="Idade: %{x}<br>%{y} jogadores<extra>%{fullData.name}</extra>",
            )
            fig_hist.update_layout(
                **plotly_layout(),
                height=360,
                xaxis_title="Idade",
                yaxis_title="Jogadores",
                bargap=0.05,
            )
            st.plotly_chart(fig_hist, use_container_width=True)

        # ── Treemap: distribuição por seleção × posição ───────────────────────
        if selected_nation == "Todas":
            st.markdown("### 🗺️ Distribuição de valor por seleção")
            treemap_df = (
                plot_df.groupby(["nation", "posicao"])["market_value_eur_m"]
                .sum()
                .reset_index()
                .rename(columns={"market_value_eur_m": "Valor (€M)"})
            )
            fig_tree = px.treemap(
                treemap_df,
                path=["nation", "posicao"],
                values="Valor (€M)",
                color="Valor (€M)",
                color_continuous_scale=SEQUENTIAL_SCALE,
            )
            fig_tree.update_traces(
                hovertemplate="<b>%{label}</b><br>Valor: €%{value:.1f}M<extra></extra>",
            )
            fig_tree.update_layout(**plotly_layout(), height=420)
            st.plotly_chart(fig_tree, use_container_width=True)

# ─────────────────────────────────────────────────────────────────────────────
# TAB 3 — DETALHE DE JOGADOR (Radar)
# ─────────────────────────────────────────────────────────────────────────────
with tab_detail:
    st.markdown("### 🔬 Comparativo individual — Radar de desempenho")

    valid_players = sorted(
        filtered.dropna(subset=["player_name"])["player_name"].tolist()
    )
    if not valid_players:
        st.info("Selecione uma seleção com jogadores cadastrados.")
    else:
        _STAR_PLAYERS = [
            "Vinicius Junior", "Kylian Mbappé", "Lionel Messi", "Jude Bellingham",
            "Harry Kane", "Lamine Yamal", "Rodri", "Raphinha", "Pedri",
            "Phil Foden", "Bukayo Saka", "Rafael Leão", "Florian Wirtz",
        ]
        _default_radar_idx = 0
        for _star in _STAR_PLAYERS:
            if _star in valid_players:
                _default_radar_idx = valid_players.index(_star)
                break
        selected_player = st.selectbox(
            "Escolha o jogador", valid_players, index=_default_radar_idx, key="radar_player"
        )
        row = filtered[filtered["player_name"] == selected_player].iloc[0]

        try:
            # Normaliza 0-100 em relação ao dataset completo
            ref = df.copy()
            ref["goals"] = ref["goals"].fillna(0)
            ref["assists"] = ref["assists"].fillna(0)
            ref["market_value_eur_m"] = ref["market_value_eur_m"].fillna(0)
            ref["matches_played"] = ref["matches_played"].fillna(0)
            ref["minutes_90s"] = ref["minutes_90s"].fillna(1).clip(lower=0.1)
            ref["g90"] = ref["goals"] / ref["minutes_90s"]
            ref["a90"] = ref["assists"] / ref["minutes_90s"]

            def pct_rank(val: float, col_series: pd.Series, higher_is_better: bool = True) -> float:
                s = col_series.dropna()
                if s.max() == s.min():
                    return 50.0
                norm = (val - s.min()) / (s.max() - s.min()) * 100
                return max(3.0, norm if higher_is_better else 100 - norm)

            mv_val  = float(row.get("market_value_eur_m") or 0)
            mp_val  = float(row.get("matches_played") or 0)
            m90_val = max(float(row.get("minutes_90s") or 0.1), 0.1)
            g_val   = float(row.get("goals") or 0)
            a_val   = float(row.get("assists") or 0)
            age_val = float(row.get("age") or 25)

            scores = [
                pct_rank(g_val / m90_val, ref["g90"]),
                pct_rank(a_val / m90_val, ref["a90"]),
                pct_rank(mp_val, ref["matches_played"]),
                pct_rank(mv_val, ref["market_value_eur_m"]),
                pct_rank(age_val, ref["age"], higher_is_better=False),
            ]
            categories = ["Gols/90", "Assist./90", "Partidas", "Valor (€M)", "Juventude"]

            fig_radar = go.Figure()
            fig_radar.add_trace(go.Scatterpolar(
                r=scores + [scores[0]],
                theta=categories + [categories[0]],
                fill="toself",
                name=selected_player,
                line=dict(color=YELLOW, width=2.5),
                fillcolor="rgba(255,223,0,0.2)",
                hovertemplate="%{theta}: %{r:.0f}<extra></extra>",
            ))

            # Linha de média da posição como referência
            pos_g = row.get("position_group", "")
            pos_ref = ref[ref["position_group"] == pos_g].copy()
            if len(pos_ref) > 1:
                pos_ref["g90"] = pos_ref["goals"].fillna(0) / pos_ref["minutes_90s"].clip(lower=0.1)
                pos_ref["a90"] = pos_ref["assists"].fillna(0) / pos_ref["minutes_90s"].clip(lower=0.1)
                avg_scores = [
                    pct_rank(pos_ref["g90"].mean(), ref["g90"]),
                    pct_rank(pos_ref["a90"].mean(), ref["a90"]),
                    pct_rank(pos_ref["matches_played"].mean(), ref["matches_played"]),
                    pct_rank(pos_ref["market_value_eur_m"].mean(), ref["market_value_eur_m"]),
                    pct_rank(pos_ref["age"].mean(), ref["age"], higher_is_better=False),
                ]
                pos_pt_label = _POS_PT.get(str(pos_g), str(pos_g))
                fig_radar.add_trace(go.Scatterpolar(
                    r=avg_scores + [avg_scores[0]],
                    theta=categories + [categories[0]],
                    fill="toself",
                    name=f"Média {pos_pt_label}",
                    line=dict(color=GREEN, width=1.5, dash="dot"),
                    fillcolor="rgba(0,156,59,0.09)",
                    hovertemplate="%{theta}: %{r:.0f}<extra>Média " + pos_pt_label + "</extra>",
                ))

            fig_radar.update_layout(
                **plotly_layout(),
                height=460,
                polar=dict(
                    bgcolor="#011a10",
                    radialaxis=dict(
                        visible=True, range=[0, 100],
                        tickfont=dict(size=9, color="#80CBC4"),
                        gridcolor="#1a3d25",
                        linecolor="#1a3d25",
                        tickvals=[25, 50, 75, 100],
                    ),
                    angularaxis=dict(
                        tickfont=dict(size=12, color="#FFDF00"),
                        gridcolor="#1a3d25",
                        linecolor="#1a3d25",
                    ),
                ),
                showlegend=True,
            )
            fig_radar.update_layout(
                title=dict(
                    text=f"{selected_player} vs. Média por Posição",
                    font=dict(size=18, color=YELLOW, family="'Barlow Condensed', sans-serif"),
                )
            )

            rcol, infocol = st.columns([2, 1])
            with rcol:
                st.plotly_chart(fig_radar, use_container_width=True)
            with infocol:
                st.markdown("#### Estatísticas")
                m90_str = f"{m90_val:.1f}" if m90_val > 0.1 else "—"
                pos_display = _POS_PT.get(str(row.get("position_group", "")), str(row.get("position_group", "—")))
                st.markdown(f"""
| Métrica | Valor |
|---|---|
| **Posição** | {pos_display} |
| **Idade** | {int(row.get("age") or 0)} anos |
| **Partidas** | {int(row.get("matches_played") or 0)} |
| **Gols** | {int(row.get("goals") or 0)} |
| **Assistências** | {int(row.get("assists") or 0)} |
| **Minutos/90** | {m90_str} |
| **Valor** | €{mv_val:.1f}M |
""")
                tier_label_r, border_c, _, _ = _tier(mv_val)
                tier_display = {"OURO": "🥇 OURO", "PRATA": "🥈 PRATA", "BASE": "🟢 TITULAR"}[tier_label_r]
                st.markdown(
                    f'<div style="margin-top:1rem;padding:0.8rem 1rem;border-radius:8px;'
                    f'border:2px solid {border_c};text-align:center;'
                    f'background:#012A1C;font-family:\'Barlow Condensed\',sans-serif;'
                    f'font-size:1.3rem;font-weight:700;color:{border_c}">'
                    f'{tier_display}</div>',
                    unsafe_allow_html=True,
                )

        except Exception as ex:
            st.error(f"Erro ao calcular radar para {selected_player}: {ex}")

# ── Tabela detalhada ──────────────────────────────────────────────────────────
st.markdown("---")
_nation_title = nation_pt(selected_nation)
st.markdown(f"### 📋 Tabela completa — {_nation_title}")
top_df = (
    filtered
    .sort_values("market_value_eur_m", ascending=False)
    [["player_name", "nation", "posicao", "age",
      "goals", "assists", "matches_played", "market_value_eur_m"]]
    .reset_index(drop=True)
)
top_df["nacao"] = top_df["nation"].map(nation_pt)
top_df = add_flag_column(top_df, nation_col="nation", width=28)
st.dataframe(
    top_df[["flag_url", "player_name", "nacao", "posicao", "age",
            "goals", "assists", "matches_played", "market_value_eur_m"]],
    column_config={
        "flag_url":           st.column_config.ImageColumn("🏳️", width="small"),
        "player_name":        st.column_config.TextColumn("Jogador"),
        "nacao":              st.column_config.TextColumn("Seleção"),
        "posicao":            st.column_config.TextColumn("Posição"),
        "age":                st.column_config.NumberColumn("Idade"),
        "goals":              st.column_config.NumberColumn("Gols"),
        "assists":            st.column_config.NumberColumn("Assist."),
        "matches_played":     st.column_config.NumberColumn("Partidas"),
        "market_value_eur_m": st.column_config.NumberColumn("Valor (€M)", format="€%.1fM"),
    },
    use_container_width=True,
    hide_index=True,
)

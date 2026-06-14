import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb
import streamlit as st
from style import inject_css, page_header, nations_flag_grid_html, nation_flag_html

DB_PATH = Path("data/world_cup.duckdb")

st.set_page_config(
    page_title="World Cup 2026 Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

page_header(
    "⚽ World Cup 2026 Analytics",
    "Análise de dados da Copa do Mundo FIFA 2026 — histórico por nação, "
    "estatísticas de jogadores convocados e indicadores do Brasil.",
)

st.markdown("**Navegue pelas páginas na barra lateral.**")

col1, col2, col3, col4 = st.columns(4)
col1.metric("Nações participantes", "48")
col2.metric("Edições analisadas", "22")
col3.metric("Países sede", "3 (EUA, CAN, MEX)")
col4.metric("Jogos na fase de grupos", "104")

# ── Bandeiras das 48 seleções ─────────────────────────────────────────────────
st.markdown("### 🌍 As 48 seleções classificadas")
try:
    con = duckdb.connect(str(DB_PATH), read_only=True)
    nations = (
        con.execute(
            "SELECT nation FROM mart_nations_performance "
            "WHERE qualified_2026 = TRUE ORDER BY nation"
        )
        .df()["nation"]
        .tolist()
    )
    con.close()
    st.markdown(nations_flag_grid_html(nations), unsafe_allow_html=True)
except Exception:
    st.info("Execute `make all` para carregar os dados e ver as bandeiras das 48 nações.")

# ══════════════════════════════════════════════════════════════════════════════
# DADOS DA FASE DE GRUPOS — Copa 2026 (atualizado em 13/06/2026)
# ══════════════════════════════════════════════════════════════════════════════

def _s(team, p=0, v=0, e=0, d=0, gp=0, gc=0, pts=None):
    """Cria entrada de classificação. pts calculado automaticamente se omitido."""
    if pts is None:
        pts = v * 3 + e
    return {"team": team, "p": p, "v": v, "e": e, "d": d,
            "gp": gp, "gc": gc, "sg": gp - gc, "pts": pts}


GROUPS: dict[str, list] = {
    "A": [
        _s("Mexico",       p=1, v=1, e=0, d=0, gp=2, gc=0),
        _s("South Korea",  p=1, v=1, e=0, d=0, gp=2, gc=1),
        _s("Czechia",      p=1, v=0, e=0, d=1, gp=1, gc=2),
        _s("South Africa", p=1, v=0, e=0, d=1, gp=0, gc=2),
    ],
    "B": [
        _s("Canada",                   p=1, v=0, e=1, d=0, gp=1, gc=1),
        _s("Bosnia and Herzegovina",   p=1, v=0, e=1, d=0, gp=1, gc=1),
        _s("Qatar",                    p=1, v=0, e=1, d=0, gp=1, gc=1),
        _s("Switzerland",              p=1, v=0, e=1, d=0, gp=1, gc=1),
    ],
    "C": [
        _s("Scotland",  p=1, v=1, e=0, d=0, gp=1, gc=0),
        _s("Brazil",    p=1, v=0, e=1, d=0, gp=1, gc=1),
        _s("Morocco",   p=1, v=0, e=1, d=0, gp=1, gc=1),
        _s("Haiti",     p=1, v=0, e=0, d=1, gp=0, gc=1),
    ],
    "D": [
        _s("United States", p=1, v=1, e=0, d=0, gp=4, gc=1),
        _s("Australia",     p=0, v=0, e=0, d=0, gp=0, gc=0),
        _s("Türkiye",       p=0, v=0, e=0, d=0, gp=0, gc=0),
        _s("Paraguay",      p=1, v=0, e=0, d=1, gp=1, gc=4),
    ],
    "E": [_s("Germany"), _s("Ivory Coast"), _s("Ecuador"),  _s("Curaçao")],
    "F": [_s("Netherlands"), _s("Japan"),  _s("Sweden"),   _s("Tunisia")],
    "G": [_s("Belgium"),  _s("Egypt"),    _s("Iran"),      _s("New Zealand")],
    "H": [_s("Spain"),    _s("Uruguay"),  _s("Saudi Arabia"), _s("Cape Verde")],
    "I": [_s("France"),   _s("Senegal"), _s("Iraq"),       _s("Norway")],
    "J": [_s("Argentina"), _s("Algeria"), _s("Austria"),   _s("Jordan")],
    "K": [_s("Portugal"), _s("Colombia"), _s("DR Congo"),  _s("Uzbekistan")],
    "L": [_s("England"),  _s("Croatia"), _s("Ghana"),      _s("Panama")],
}

RESULTS = [
    {"date": "11/06", "grp": "A", "home": "Mexico",        "hs": 2, "as_": 0, "away": "South Africa"},
    {"date": "11/06", "grp": "A", "home": "South Korea",   "hs": 2, "as_": 1, "away": "Czechia"},
    {"date": "12/06", "grp": "B", "home": "Canada",        "hs": 1, "as_": 1, "away": "Bosnia and Herzegovina"},
    {"date": "12/06", "grp": "D", "home": "United States", "hs": 4, "as_": 1, "away": "Paraguay"},
    {"date": "13/06", "grp": "B", "home": "Qatar",         "hs": 1, "as_": 1, "away": "Switzerland"},
    {"date": "13/06", "grp": "C", "home": "Brazil",        "hs": 1, "as_": 1, "away": "Morocco"},
    {"date": "13/06", "grp": "C", "home": "Haiti",         "hs": 0, "as_": 1, "away": "Scotland"},
]

# ── Funções de renderização HTML ──────────────────────────────────────────────

def _flag_img(nation: str, w: int = 24) -> str:
    return nation_flag_html(nation, width=w)


def standings_html(rows: list) -> str:
    header = (
        '<div style="display:flex;align-items:center;padding:0.45rem 1rem;'
        'background:#013d20;border-radius:8px 8px 0 0">'
        '<span style="flex:1;color:#FFDF00;font-size:0.68rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:1px;font-family:Inter,sans-serif">Seleção</span>'
        + "".join(
            f'<span style="width:36px;text-align:center;color:#FFDF00;font-size:0.68rem;'
            f'font-weight:700;text-transform:uppercase;letter-spacing:0.5px;font-family:Inter,sans-serif">{h}</span>'
            for h in ["P", "V", "E", "D", "SG", "PTS"]
        )
        + "</div>"
    )

    body_rows = []
    for i, r in enumerate(rows):
        pts_color = "#FFDF00" if r["pts"] > 0 else "#9E9E9E"
        sg_str = f'+{r["sg"]}' if r["sg"] > 0 else str(r["sg"])
        border = "border-top:1px solid rgba(0,156,59,0.15);" if i > 0 else ""
        short_name = r["team"][:16] + ("…" if len(r["team"]) > 16 else "")
        body_rows.append(
            f'<div style="display:flex;align-items:center;padding:0.55rem 1rem;{border}">'
            f'<div style="flex:1;display:flex;align-items:center;gap:8px">'
            f'<span style="color:#616161;font-size:0.75rem;width:14px;text-align:center">{i+1}</span>'
            f'{_flag_img(r["team"], 24)}'
            f'<span style="color:#F0F0F0;font-family:\'Barlow Condensed\',sans-serif;font-size:1rem">{short_name}</span>'
            f'</div>'
            + "".join(
                f'<span style="width:36px;text-align:center;color:#B0B0B0;font-size:0.88rem">{r[k]}</span>'
                for k in ["p", "v", "e", "d"]
            )
            + f'<span style="width:36px;text-align:center;color:#B0B0B0;font-size:0.88rem">{sg_str}</span>'
            + f'<span style="width:36px;text-align:center;color:{pts_color};'
            f'font-family:\'Barlow Condensed\',sans-serif;font-size:1.1rem;font-weight:700">{r["pts"]}</span>'
            + "</div>"
        )

    return (
        f'<div style="background:#012A1C;border-radius:10px;'
        f'border:1px solid rgba(0,156,59,0.25);overflow:hidden">'
        + header + "".join(body_rows) + "</div>"
    )


def match_card_html(m: dict) -> str:
    hflag = _flag_img(m["home"], 36)
    aflag = _flag_img(m["away"], 36)
    draw = m["hs"] == m["as_"]
    score_color = "#FFDF00" if not draw else "#B0BEC5"
    home_w = "font-weight:700;" if m["hs"] > m["as_"] else ""
    away_w = "font-weight:700;" if m["as_"] > m["hs"] else ""
    home_nm = m["home"][:18] + ("…" if len(m["home"]) > 18 else "")
    away_nm = m["away"][:18] + ("…" if len(m["away"]) > 18 else "")
    return (
        f'<div style="background:#012A1C;border-radius:10px;padding:0.8rem 1.2rem;'
        f'border:1px solid rgba(0,156,59,0.25);margin-bottom:0.6rem">'
        f'<div style="display:flex;justify-content:space-between;margin-bottom:0.5rem">'
        f'<span style="color:#FFDF00;font-size:0.65rem;font-weight:700;text-transform:uppercase;'
        f'letter-spacing:1px;font-family:Inter,sans-serif">Grupo {m["grp"]}</span>'
        f'<span style="color:#757575;font-size:0.65rem;font-family:Inter,sans-serif">{m["date"]}/2026</span>'
        f'</div>'
        f'<div style="display:flex;align-items:center;justify-content:space-between">'
        # home
        f'<div style="display:flex;align-items:center;gap:8px;flex:1">'
        f'{hflag}'
        f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.1rem;'
        f'color:#F0F0F0;{home_w}">{home_nm}</span>'
        f'</div>'
        # placar
        f'<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.8rem;'
        f'font-weight:700;color:{score_color};min-width:70px;text-align:center;letter-spacing:2px">'
        f'{m["hs"]} – {m["as_"]}</div>'
        # away
        f'<div style="display:flex;align-items:center;justify-content:flex-end;gap:8px;flex:1">'
        f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.1rem;'
        f'color:#F0F0F0;{away_w}">{away_nm}</span>'
        f'{aflag}'
        f'</div>'
        f'</div>'
        f'</div>'
    )


# ── Renderização na página ────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 📊 Grupos — Copa 2026")

group_letters = list(GROUPS.keys())
tabs = st.tabs([f"Grupo {g}" for g in group_letters])

for tab, letter in zip(tabs, group_letters):
    with tab:
        rows = sorted(GROUPS[letter], key=lambda r: (-r["pts"], -r["sg"], -r["gp"]))
        st.markdown(standings_html(rows), unsafe_allow_html=True)

st.markdown("---")
st.markdown(f"## 🎯 Jogos realizados — {len(RESULTS)} partidas")

# Agrupar por data para exibir com separadores
dates_seen = []
results_by_date: dict[str, list] = {}
for m in RESULTS:
    results_by_date.setdefault(m["date"], []).append(m)

for date, matches in results_by_date.items():
    st.markdown(
        f'<p style="color:#FFDF00;font-family:\'Barlow Condensed\',sans-serif;'
        f'font-size:1rem;font-weight:700;text-transform:uppercase;letter-spacing:1px;'
        f'margin:1rem 0 0.4rem">{date}/2026</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(min(len(matches), 3))
    for col, m in zip(cols, matches):
        with col:
            st.markdown(match_card_html(m), unsafe_allow_html=True)

# ── Navegação rápida para perfil de jogadores ─────────────────────────────────
st.markdown("---")
st.markdown("## 🔍 Explorar seleção")

_squad_nations = [
    "Argentina", "Brazil", "England", "France", "Germany",
    "Portugal", "Spain",
]

nav_col, btn_col = st.columns([3, 1])
with nav_col:
    selected_nav = st.selectbox(
        "Escolha uma seleção para ver o perfil dos jogadores:",
        _squad_nations,
        key="nav_nation_select",
    )
with btn_col:
    st.write("")
    st.write("")
    if st.button("Ver jogadores →", type="primary", use_container_width=True):
        st.session_state["selected_nation"] = selected_nav
        st.switch_page("pages/4_Perfil_Jogadores.py")

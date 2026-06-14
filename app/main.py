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

# ══════════════════════════════════════════════════════════════════════════════
# DADOS — Copa 2026 (atualizado em 13/06/2026)
# ══════════════════════════════════════════════════════════════════════════════

def _s(team, p=0, v=0, e=0, d=0, gp=0, gc=0, pts=None):
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
        _s("Canada",                 p=1, v=0, e=1, d=0, gp=1, gc=1),
        _s("Bosnia and Herzegovina", p=1, v=0, e=1, d=0, gp=1, gc=1),
        _s("Qatar",                  p=1, v=0, e=1, d=0, gp=1, gc=1),
        _s("Switzerland",            p=1, v=0, e=1, d=0, gp=1, gc=1),
    ],
    "C": [
        _s("Scotland", p=1, v=1, e=0, d=0, gp=1, gc=0),
        _s("Brazil",   p=1, v=0, e=1, d=0, gp=1, gc=1),
        _s("Morocco",  p=1, v=0, e=1, d=0, gp=1, gc=1),
        _s("Haiti",    p=1, v=0, e=0, d=1, gp=0, gc=1),
    ],
    "D": [
        _s("United States", p=1, v=1, e=0, d=0, gp=4, gc=1),
        _s("Australia",     p=0),
        _s("Türkiye",       p=0),
        _s("Paraguay",      p=1, v=0, e=0, d=1, gp=1, gc=4),
    ],
    "E": [_s("Germany"),     _s("Ivory Coast"), _s("Ecuador"),      _s("Curaçao")],
    "F": [_s("Netherlands"), _s("Japan"),       _s("Sweden"),       _s("Tunisia")],
    "G": [_s("Belgium"),     _s("Egypt"),       _s("Iran"),         _s("New Zealand")],
    "H": [_s("Spain"),       _s("Uruguay"),     _s("Saudi Arabia"), _s("Cape Verde")],
    "I": [_s("France"),      _s("Senegal"),     _s("Iraq"),         _s("Norway")],
    "J": [_s("Argentina"),   _s("Algeria"),     _s("Austria"),      _s("Jordan")],
    "K": [_s("Portugal"),    _s("Colombia"),    _s("DR Congo"),     _s("Uzbekistan")],
    "L": [_s("England"),     _s("Croatia"),     _s("Ghana"),        _s("Panama")],
}

# yt = YouTube video ID para thumbnail e link de highlights
RESULTS = [
    {"date": "11/06", "grp": "A", "home": "Mexico",        "hs": 2, "as_": 0, "away": "South Africa",         "yt": "K61nLm218Fs"},
    {"date": "11/06", "grp": "A", "home": "South Korea",   "hs": 2, "as_": 1, "away": "Czechia",              "yt": "QWoDfCkh7f8"},
    {"date": "12/06", "grp": "B", "home": "Canada",        "hs": 1, "as_": 1, "away": "Bosnia and Herzegovina","yt": "w-_rY5morQY"},
    {"date": "12/06", "grp": "D", "home": "United States", "hs": 4, "as_": 1, "away": "Paraguay",             "yt": "jdnyNn9XsDc"},
    {"date": "13/06", "grp": "B", "home": "Qatar",         "hs": 1, "as_": 1, "away": "Switzerland",          "yt": "Z-9EIWllZNM"},
    {"date": "13/06", "grp": "C", "home": "Brazil",        "hs": 1, "as_": 1, "away": "Morocco",              "yt": "c1qsNkpBoT8"},
    {"date": "13/06", "grp": "C", "home": "Haiti",         "hs": 0, "as_": 1, "away": "Scotland",             "yt": "CpCnbQkeY0E"},
]

# ── Funções de renderização HTML ──────────────────────────────────────────────

def _flag(nation: str, w: int = 28) -> str:
    return nation_flag_html(nation, width=w)


def match_card_html(m: dict) -> str:
    """Card de resultado com thumbnail do YouTube como imagem de fundo."""
    yt_id   = m.get("yt", "")
    yt_url  = f"https://www.youtube.com/watch?v={yt_id}" if yt_id else "#"
    thumb   = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg" if yt_id else ""

    draw      = m["hs"] == m["as_"]
    sc_color  = "#FFDF00" if not draw else "#CFD8DC"
    home_bold = "font-weight:800;" if m["hs"] > m["as_"] else ""
    away_bold = "font-weight:800;" if m["as_"] > m["hs"] else ""

    # ── thumbnail com overlay e botão play ──
    if thumb:
        img_section = (
            f'<div style="position:relative;height:148px;overflow:hidden">'
            # imagem com saturação aumentada e escurecida
            f'<img src="{thumb}" '
            f'style="width:100%;height:100%;object-fit:cover;display:block;'
            f'filter:brightness(0.45) saturate(1.4)" '
            f'onerror="this.style.display=\'none\'">'
            # gradiente inferior para fundir com o card
            f'<div style="position:absolute;inset:0;background:'
            f'linear-gradient(0deg,#012A1C 0%,transparent 55%)"></div>'
            # badge grupo + data
            f'<div style="position:absolute;top:9px;left:11px;display:flex;align-items:center;gap:6px">'
            f'<span style="background:#FFDF00;color:#000;font-size:0.58rem;font-weight:800;'
            f'padding:2px 9px;border-radius:20px;font-family:Inter,sans-serif;letter-spacing:0.5px">'
            f'GRUPO {m["grp"]}</span>'
            f'</div>'
            f'<div style="position:absolute;top:10px;right:11px">'
            f'<span style="color:rgba(255,255,255,0.55);font-size:0.6rem;font-family:Inter,sans-serif">'
            f'{m["date"]}/2026</span>'
            f'</div>'
            # botão play (link para YouTube)
            f'<a href="{yt_url}" target="_blank" style="position:absolute;top:50%;left:50%;'
            f'transform:translate(-50%,-55%);text-decoration:none">'
            f'<div style="width:46px;height:46px;border-radius:50%;'
            f'background:rgba(200,0,0,0.88);display:flex;align-items:center;'
            f'justify-content:center;border:2px solid rgba(255,255,255,0.75);'
            f'box-shadow:0 2px 12px rgba(0,0,0,0.6)">'
            f'<span style="color:#fff;font-size:1.1rem;margin-left:4px;line-height:1">▶</span>'
            f'</div></a>'
            f'</div>'
        )
    else:
        img_section = (
            f'<div style="height:60px;background:linear-gradient(135deg,#013d20,#012A1C);'
            f'display:flex;align-items:center;justify-content:space-between;padding:0 1rem">'
            f'<span style="color:#FFDF00;font-size:0.6rem;font-weight:700">GRUPO {m["grp"]}</span>'
            f'<span style="color:#757575;font-size:0.6rem">{m["date"]}/2026</span>'
            f'</div>'
        )

    # ── linha de placar ──
    score_section = (
        f'<div style="padding:10px 14px 13px">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;gap:4px">'
        # casa
        f'<div style="display:flex;align-items:center;gap:7px;flex:1;min-width:0">'
        f'{_flag(m["home"], 26)}'
        f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:0.95rem;'
        f'color:#F0F0F0;{home_bold}white-space:nowrap;overflow:hidden;text-overflow:ellipsis">'
        f'{m["home"]}</span>'
        f'</div>'
        # placar
        f'<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.55rem;'
        f'font-weight:700;color:{sc_color};flex-shrink:0;padding:0 8px;letter-spacing:3px">'
        f'{m["hs"]} – {m["as_"]}</div>'
        # fora
        f'<div style="display:flex;align-items:center;justify-content:flex-end;gap:7px;flex:1;min-width:0">'
        f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:0.95rem;'
        f'color:#F0F0F0;{away_bold}white-space:nowrap;overflow:hidden;'
        f'text-overflow:ellipsis;text-align:right">{m["away"]}</span>'
        f'{_flag(m["away"], 26)}'
        f'</div>'
        f'</div>'
        # link highlights
        + (
            f'<div style="margin-top:7px;text-align:center">'
            f'<a href="{yt_url}" target="_blank" '
            f'style="color:#FF4444;font-size:0.65rem;font-family:Inter,sans-serif;'
            f'font-weight:600;text-decoration:none;letter-spacing:0.5px">'
            f'▶ VER HIGHLIGHTS</a></div>'
            if yt_id else ""
        )
        + f'</div>'
    )

    return (
        f'<div style="background:#012A1C;border-radius:12px;overflow:hidden;'
        f'border:1px solid rgba(0,156,59,0.3);'
        f'box-shadow:0 4px 18px rgba(0,0,0,0.4)">'
        + img_section + score_section
        + f'</div>'
    )


def standings_html(rows: list) -> str:
    header = (
        '<div style="display:flex;align-items:center;padding:0.45rem 1rem;'
        'background:#013d20;border-radius:8px 8px 0 0">'
        '<span style="flex:1;color:#FFDF00;font-size:0.67rem;font-weight:700;'
        'text-transform:uppercase;letter-spacing:1px;font-family:Inter,sans-serif">Seleção</span>'
        + "".join(
            f'<span style="width:34px;text-align:center;color:#FFDF00;font-size:0.67rem;'
            f'font-weight:700;text-transform:uppercase;font-family:Inter,sans-serif">{h}</span>'
            for h in ["P", "V", "E", "D", "SG", "PTS"]
        )
        + "</div>"
    )

    rows_html = []
    for i, r in enumerate(rows):
        qual   = i < 2          # top 2 se classificam diretamente
        pts_c  = "#FFDF00" if r["pts"] > 0 else "#757575"
        sg_str = f'+{r["sg"]}' if r["sg"] > 0 else str(r["sg"])
        border = "border-top:1px solid rgba(0,156,59,0.13);" if i > 0 else ""
        short  = r["team"][:16] + ("…" if len(r["team"]) > 16 else "")
        rank_color = "#009C3B" if qual else "#424242"
        rows_html.append(
            f'<div style="display:flex;align-items:center;padding:0.5rem 1rem;{border}">'
            f'<div style="flex:1;display:flex;align-items:center;gap:7px">'
            f'<span style="color:{rank_color};font-size:0.72rem;font-weight:700;'
            f'width:14px;text-align:center">{i+1}</span>'
            f'{_flag(r["team"], 22)}'
            f'<span style="color:#F0F0F0;font-family:\'Barlow Condensed\',sans-serif;'
            f'font-size:0.97rem">{short}</span>'
            f'</div>'
            + "".join(
                f'<span style="width:34px;text-align:center;color:#9E9E9E;font-size:0.85rem">{r[k]}</span>'
                for k in ["p", "v", "e", "d"]
            )
            + f'<span style="width:34px;text-align:center;color:#9E9E9E;font-size:0.85rem">{sg_str}</span>'
            + f'<span style="width:34px;text-align:center;color:{pts_c};'
            f'font-family:\'Barlow Condensed\',sans-serif;font-size:1.05rem;font-weight:700">'
            f'{r["pts"]}</span>'
            + "</div>"
        )

    return (
        '<div style="background:#012A1C;border-radius:10px;'
        'border:1px solid rgba(0,156,59,0.22);overflow:hidden">'
        + header + "".join(rows_html) + "</div>"
    )


# ══════════════════════════════════════════════════════════════════════════════
# RENDERIZAÇÃO
# ══════════════════════════════════════════════════════════════════════════════

# ── Resultados com thumbnails ──────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f'<div style="display:flex;align-items:baseline;gap:12px;margin-bottom:0.2rem">'
    f'<h2 style="color:#FFDF00;font-family:\'Barlow Condensed\',sans-serif;'
    f'font-size:1.6rem;font-weight:700;margin:0">🎬 Últimos Resultados</h2>'
    f'<span style="color:#009C3B;font-size:0.75rem;font-family:Inter,sans-serif;'
    f'font-weight:600;text-transform:uppercase;letter-spacing:1px">'
    f'atualizado 13/06/2026 · {len(RESULTS)} partidas</span>'
    f'</div>',
    unsafe_allow_html=True,
)

results_by_date: dict[str, list] = {}
for m in RESULTS:
    results_by_date.setdefault(m["date"], []).append(m)

for date, matches in results_by_date.items():
    st.markdown(
        f'<p style="color:#616161;font-family:Inter,sans-serif;font-size:0.75rem;'
        f'font-weight:600;text-transform:uppercase;letter-spacing:1px;'
        f'margin:1rem 0 0.5rem;border-left:3px solid #009C3B;padding-left:8px">'
        f'{date}/2026</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(len(matches))
    for col, m in zip(cols, matches):
        with col:
            st.markdown(match_card_html(m), unsafe_allow_html=True)

# ── Grupos ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 📊 Grupos — Copa 2026")
st.caption("🟢 Top 2 de cada grupo avançam diretamente · os 8 melhores terceiros colocados também avançam")

tabs = st.tabs([f"Grupo {g}" for g in GROUPS])
for tab, letter in zip(tabs, GROUPS):
    with tab:
        rows = sorted(GROUPS[letter], key=lambda r: (-r["pts"], -r["sg"], -r["gp"]))
        st.markdown(standings_html(rows), unsafe_allow_html=True)

# ── Bandeiras das 48 seleções ─────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 🌍 As 48 seleções classificadas")
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

# ── Navegação rápida para perfil de jogadores ─────────────────────────────────
st.markdown("---")
st.markdown("## 🔍 Explorar elenco de uma seleção")

_squad_nations = [
    "Argentina", "Brazil", "England", "France", "Germany",
    "Portugal", "Spain", "Mexico", "Morocco", "Scotland",
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

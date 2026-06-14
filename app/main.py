import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

import duckdb
import streamlit as st
from style import inject_css, page_header, nation_flag_url, NATION_TO_ISO2

DB_PATH = Path("data/world_cup.duckdb")

st.set_page_config(
    page_title="World Cup 2026 Analytics",
    page_icon="⚽",
    layout="wide",
    initial_sidebar_state="expanded",
)

inject_css()

# ── Navegação via click nas bandeiras (query param) ───────────────────────────
if "nav_nation" in st.query_params:
    _nav = st.query_params["nav_nation"]
    st.query_params.clear()
    st.session_state["selected_nation"] = _nav
    st.switch_page("pages/4_Perfil_Jogadores.py")

# ── Hero ──────────────────────────────────────────────────────────────────────
page_header(
    "⚽ World Cup 2026 Analytics",
    "Análise de dados da Copa do Mundo FIFA 2026 — histórico por nação, "
    "estatísticas de jogadores convocados e indicadores do Brasil.",
)

# ── Cards de navegação ────────────────────────────────────────────────────────
_NAV_PAGES = [
    (
        '<span style="font-size:1.7rem">🗺️</span>',
        "Mapa dos Participantes",
        "48 seleções no mapa interativo com tooltip de curiosidades",
        "pages/1_Mapa_Participantes.py",
    ),
    (
        '<span style="font-size:1.7rem">📊</span>',
        "Ranking Histórico",
        "Compare nações por títulos e desempenho em 22 edições da Copa",
        "pages/2_Ranking_Historico.py",
    ),
    (
        '<img src="https://flagcdn.com/w40/br.png" '
        'style="height:30px;border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.5)">',
        "Brasil Deep Dive",
        "Análise do Brasil Copa a Copa, confrontos e artilheiros históricos",
        "pages/3_Brasil_Deep_Dive.py",
    ),
    (
        '<span style="font-size:1.7rem">🃏</span>',
        "Perfil dos Jogadores",
        "Figurinhas estilo Panini, valor de mercado e radar de desempenho",
        "pages/4_Perfil_Jogadores.py",
    ),
]

nav_cols = st.columns(4)
for col, (icon, title, desc, path) in zip(nav_cols, _NAV_PAGES):
    with col:
        st.markdown(
            f'<div style="background:linear-gradient(135deg,#012A1C,#013d20);'
            f'border:1px solid rgba(0,156,59,0.35);border-radius:12px;'
            f'padding:1.1rem 1.2rem;margin-bottom:0.4rem;min-height:96px">'
            f'<div style="margin-bottom:7px;line-height:1">{icon}</div>'
            f'<div style="color:#FFDF00;font-family:\'Barlow Condensed\',sans-serif;'
            f'font-size:1.05rem;font-weight:700;margin-bottom:4px">{title}</div>'
            f'<div style="color:#9E9E9E;font-size:0.72rem;font-family:Inter,sans-serif;'
            f'line-height:1.4">{desc}</div>'
            f'</div>',
            unsafe_allow_html=True,
        )
        if st.button("Explorar →", key=f"nav_{path}", use_container_width=True):
            st.switch_page(path)

# ── KPIs ──────────────────────────────────────────────────────────────────────
k1, k2, k3, k4 = st.columns(4)
k1.metric("Nações participantes", "48")
k2.metric("Edições analisadas", "22")
k3.metric("Países sede", "3", help="EUA, Canadá e México co-sediam a Copa 2026")
k4.metric("Jogos na fase de grupos", "104")

# ══════════════════════════════════════════════════════════════════════════════
# DADOS — Copa 2026 (atualizado em 14/06/2026)
# ══════════════════════════════════════════════════════════════════════════════

def _s(team, p=0, v=0, e=0, d=0, gp=0, gc=0, pts=None):
    if pts is None:
        pts = v * 3 + e
    return {"team": team, "p": p, "v": v, "e": e, "d": d,
            "gp": gp, "gc": gc, "sg": gp - gc, "pts": pts}


# Tradução dos nomes das seleções para português (chave interna em inglês)
_TEAM_PT: dict[str, str] = {
    "Mexico": "México",          "South Korea": "Coreia do Sul",
    "Czechia": "República Tcheca","South Africa": "África do Sul",
    "Canada": "Canadá",          "Bosnia and Herzegovina": "Bósnia-Herz.",
    "Qatar": "Catar",            "Switzerland": "Suíça",
    "Scotland": "Escócia",       "Brazil": "Brasil",
    "Morocco": "Marrocos",       "Haiti": "Haiti",
    "United States": "EUA",      "Australia": "Austrália",
    "Türkiye": "Turquia",        "Paraguay": "Paraguai",
    "Germany": "Alemanha",       "Ivory Coast": "Costa do Marfim",
    "Ecuador": "Equador",        "Curaçao": "Curaçao",
    "Netherlands": "Holanda",    "Japan": "Japão",
    "Sweden": "Suécia",          "Tunisia": "Tunísia",
    "Belgium": "Bélgica",        "Egypt": "Egito",
    "Iran": "Irã",               "New Zealand": "Nova Zelândia",
    "Spain": "Espanha",          "Uruguay": "Uruguai",
    "Saudi Arabia": "Arábia Sau.","Cape Verde": "Cabo Verde",
    "France": "França",          "Senegal": "Senegal",
    "Iraq": "Iraque",            "Norway": "Noruega",
    "Argentina": "Argentina",    "Algeria": "Argélia",
    "Austria": "Áustria",        "Jordan": "Jordânia",
    "Portugal": "Portugal",      "Colombia": "Colômbia",
    "DR Congo": "Congo RD",      "Uzbekistan": "Uzbequistão",
    "England": "Inglaterra",     "Croatia": "Croácia",
    "Ghana": "Gana",             "Panama": "Panamá",
    "Jamaica": "Jamaica",        "Honduras": "Honduras",
    "Costa Rica": "Costa Rica",  "Cameroon": "Camarões",
    "Poland": "Polônia",         "Denmark": "Dinamarca",
    "Italy": "Itália",           "Serbia": "Sérvia",
    "Nigeria": "Nigéria",        "Mali": "Mali",
    "Senegal": "Senegal",        "Tunisia": "Tunísia",
    "Indonesia": "Indonésia",    "Venezuela": "Venezuela",
    "Bolivia": "Bolívia",        "Chile": "Chile",
    "Peru": "Peru",              "El Salvador": "El Salvador",
    "Cuba": "Cuba",              "Trinidad and Tobago": "Trinidad",
    "Burkina Faso": "Burkina F.", "Kenya": "Quênia",
    "Tanzania": "Tanzânia",      "Zimbabwe": "Zimbábue",
    "Zambia": "Zâmbia",
}


def _t(name: str) -> str:
    """Retorna o nome da seleção em português (ou o original se não mapeado)."""
    return _TEAM_PT.get(name, name)


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

# Data da 1ª partida de cada grupo (para indicador "aguardando")
_GROUP_START: dict[str, str] = {
    "A": "11/06", "B": "12/06", "C": "13/06", "D": "12/06",
    "E": "14/06", "F": "14/06", "G": "15/06", "H": "15/06",
    "I": "16/06", "J": "16/06", "K": "17/06", "L": "17/06",
}

RESULTS = [
    {"date": "11/06", "grp": "A", "home": "Mexico",        "hs": 2, "as_": 0, "away": "South Africa",          "yt": "K61nLm218Fs", "br": False},
    {"date": "11/06", "grp": "A", "home": "South Korea",   "hs": 2, "as_": 1, "away": "Czechia",               "yt": "QWoDfCkh7f8", "br": False},
    {"date": "12/06", "grp": "B", "home": "Canada",        "hs": 1, "as_": 1, "away": "Bosnia and Herzegovina","yt": "w-_rY5morQY",  "br": False},
    {"date": "12/06", "grp": "D", "home": "United States", "hs": 4, "as_": 1, "away": "Paraguay",              "yt": "jdnyNn9XsDc", "br": False},
    {"date": "13/06", "grp": "B", "home": "Qatar",         "hs": 1, "as_": 1, "away": "Switzerland",           "yt": "Z-9EIWllZNM", "br": False},
    {"date": "13/06", "grp": "C", "home": "Brazil",        "hs": 1, "as_": 1, "away": "Morocco",               "yt": "c1qsNkpBoT8", "br": True},
    {"date": "13/06", "grp": "C", "home": "Haiti",         "hs": 0, "as_": 1, "away": "Scotland",              "yt": "CpCnbQkeY0E", "br": False},
]

UPCOMING = [
    {"date": "14/06", "grp": "D", "home": "Australia",    "away": "Türkiye",      "time": "13:00"},
    {"date": "14/06", "grp": "E", "home": "Germany",      "away": "Ivory Coast",  "time": "16:00"},
    {"date": "14/06", "grp": "E", "home": "Ecuador",      "away": "Curaçao",      "time": "19:00"},
    {"date": "14/06", "grp": "F", "home": "Netherlands",  "away": "Japan",        "time": "22:00"},
    {"date": "15/06", "grp": "F", "home": "Sweden",       "away": "Tunisia",      "time": "13:00"},
    {"date": "15/06", "grp": "G", "home": "Belgium",      "away": "Egypt",        "time": "16:00"},
    {"date": "15/06", "grp": "G", "home": "Iran",         "away": "New Zealand",  "time": "19:00"},
    {"date": "15/06", "grp": "H", "home": "Spain",        "away": "Uruguay",      "time": "22:00"},
    {"date": "16/06", "grp": "H", "home": "Saudi Arabia", "away": "Cape Verde",   "time": "13:00"},
    {"date": "16/06", "grp": "I", "home": "France",       "away": "Senegal",      "time": "16:00"},
    {"date": "16/06", "grp": "I", "home": "Iraq",         "away": "Norway",       "time": "19:00"},
    {"date": "16/06", "grp": "J", "home": "Argentina",    "away": "Algeria",      "time": "22:00"},
]

# ── Helpers de renderização ───────────────────────────────────────────────────

def _flag(nation: str, w: int = 26) -> str:
    """Bandeira robusta: img flagcdn + emoji Unicode como fallback inline."""
    iso = NATION_TO_ISO2.get(nation, "")
    if not iso:
        return ""
    url  = f"https://flagcdn.com/w40/{iso.lower()}.png"
    h    = max(int(w * 0.67), 12)
    # Emoji Unicode de bandeira (funciona no Chrome mesmo no Windows)
    base = iso.split("-")[0].upper()
    emoji = "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in base)
    return (
        f'<span style="display:inline-flex;align-items:center;'
        f'flex-shrink:0;width:{w}px;height:{h}px;overflow:hidden;'
        f'border-radius:3px;box-shadow:0 1px 4px rgba(0,0,0,0.45)">'
        f'<img src="{url}" width="{w}" height="{h}" '
        f'style="object-fit:cover;display:block;width:{w}px;height:{h}px" '
        f'onerror="this.parentElement.innerHTML=\'<span style=&quot;font-size:{w-4}px;line-height:1&quot;>{emoji}</span>\'" '
        f'loading="eager"></span>'
    )


def match_card_html(m: dict) -> str:
    """Card de resultado com thumbnail YouTube e destaque especial para o Brasil."""
    yt_id   = m.get("yt", "")
    yt_url  = f"https://www.youtube.com/watch?v={yt_id}" if yt_id else "#"
    thumb   = f"https://img.youtube.com/vi/{yt_id}/hqdefault.jpg" if yt_id else ""
    is_br   = m.get("br", False)

    border_color = "rgba(0,156,59,0.3)"
    if is_br:
        border_color = "#FFDF00"

    draw      = m["hs"] == m["as_"]
    sc_color  = "#FFDF00" if not draw else "#CFD8DC"
    home_bold = "font-weight:800;" if m["hs"] > m["as_"] else ""
    away_bold = "font-weight:800;" if m["as_"] > m["hs"] else ""

    br_badge = (
        f'<div style="position:absolute;top:0;left:0;right:0;'
        f'background:linear-gradient(90deg,#009C3B,#FFDF00,#009C3B);'
        f'height:3px"></div>'
        if is_br else ""
    )

    if thumb:
        img_section = (
            f'<div style="position:relative;height:148px;overflow:hidden">'
            f'{br_badge}'
            f'<img src="{thumb}" '
            f'style="width:100%;height:100%;object-fit:cover;display:block;'
            f'filter:brightness(0.45) saturate(1.4)" '
            f'onerror="this.style.display=\'none\'">'
            f'<div style="position:absolute;inset:0;background:'
            f'linear-gradient(0deg,#012A1C 0%,transparent 55%)"></div>'
            f'<div style="position:absolute;top:9px;left:11px">'
            f'<span style="background:{"#FFDF00" if is_br else "#013d20"};'
            f'color:{"#000" if is_br else "#FFDF00"};'
            f'font-size:0.58rem;font-weight:800;'
            f'padding:2px 9px;border-radius:20px;font-family:Inter,sans-serif;letter-spacing:0.5px">'
            f'{"🇧🇷 BRASIL · " if is_br else ""}GRUPO {m["grp"]}</span>'
            f'</div>'
            f'<div style="position:absolute;top:10px;right:11px">'
            f'<span style="color:rgba(255,255,255,0.55);font-size:0.6rem;font-family:Inter,sans-serif">'
            f'{m["date"]}/2026</span>'
            f'</div>'
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
            f'<div style="height:52px;background:linear-gradient(135deg,#013d20,#012A1C);'
            f'display:flex;align-items:center;justify-content:space-between;padding:0 1rem;'
            f'position:relative">'
            f'{br_badge}'
            f'<span style="color:#FFDF00;font-size:0.6rem;font-weight:700">GRUPO {m["grp"]}</span>'
            f'<span style="color:#757575;font-size:0.6rem">{m["date"]}/2026</span>'
            f'</div>'
        )

    home_pt = _t(m["home"])
    away_pt = _t(m["away"])
    # Fonte menor para nomes longos (>12 chars) para evitar truncamento
    home_size = "0.78rem" if len(home_pt) > 12 else "0.88rem"
    away_size = "0.78rem" if len(away_pt) > 12 else "0.88rem"

    score_section = (
        f'<div style="padding:10px 14px 13px">'
        f'<div style="display:flex;align-items:center;justify-content:space-between;gap:4px;min-height:42px">'
        f'<div style="display:flex;align-items:center;gap:6px;flex:1;min-width:0">'
        f'{_flag(m["home"], 24)}'
        f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:{home_size};'
        f'color:#F0F0F0;{home_bold}line-height:1.2;word-break:break-word;overflow-wrap:break-word">'
        f'{home_pt}</span>'
        f'</div>'
        f'<div style="font-family:\'Barlow Condensed\',sans-serif;font-size:1.45rem;'
        f'font-weight:700;color:{sc_color};flex-shrink:0;padding:0 7px;letter-spacing:2px">'
        f'{m["hs"]} – {m["as_"]}</div>'
        f'<div style="display:flex;align-items:center;justify-content:flex-end;gap:6px;flex:1;min-width:0">'
        f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:{away_size};'
        f'color:#F0F0F0;{away_bold}line-height:1.2;word-break:break-word;'
        f'overflow-wrap:break-word;text-align:right">{away_pt}</span>'
        f'{_flag(m["away"], 24)}'
        f'</div>'
        f'</div>'
        + (
            f'<div style="margin-top:7px;text-align:center">'
            f'<a href="{yt_url}" target="_blank" '
            f'style="color:#FF4444;font-size:0.65rem;font-family:Inter,sans-serif;'
            f'font-weight:600;text-decoration:none;letter-spacing:0.5px">'
            f'▶ VER DESTAQUES</a></div>'
            if yt_id else ""
        )
        + f'</div>'
    )

    return (
        f'<div style="background:#012A1C;border-radius:12px;overflow:hidden;'
        f'border:2px solid {border_color};'
        f'box-shadow:0 4px 18px {"rgba(255,223,0,0.12)" if is_br else "rgba(0,0,0,0.4)"}">'
        + img_section + score_section + f'</div>'
    )


def next_match_card_html(m: dict) -> str:
    """Card compacto de próxima partida (sem placar, sem vídeo)."""
    return (
        f'<div style="background:#012A1C;border-radius:10px;'
        f'border:1px solid rgba(0,156,59,0.2);padding:11px 13px">'
        f'<div style="display:flex;justify-content:space-between;'
        f'align-items:center;margin-bottom:9px">'
        f'<span style="background:#013d20;color:#FFDF00;font-size:0.55rem;'
        f'font-weight:800;padding:2px 8px;border-radius:20px;'
        f'font-family:Inter,sans-serif;letter-spacing:0.5px">GRP {m["grp"]}</span>'
        f'<span style="color:#616161;font-size:0.6rem;font-family:Inter,sans-serif">'
        f'{m["date"]}/2026 · {m["time"]}</span>'
        f'</div>'
        f'<div style="display:flex;align-items:center;justify-content:space-between;gap:4px">'
        f'<div style="display:flex;align-items:center;gap:6px;flex:1;min-width:0">'
        f'{_flag(m["home"], 22)}'
        f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:0.82rem;'
        f'color:#F0F0F0;line-height:1.2;word-break:break-word;overflow-wrap:break-word">'
        f'{_t(m["home"])}</span>'
        f'</div>'
        f'<div style="color:#616161;font-family:\'Barlow Condensed\',sans-serif;'
        f'font-size:0.85rem;font-weight:700;flex-shrink:0;padding:0 6px">VS</div>'
        f'<div style="display:flex;align-items:center;justify-content:flex-end;gap:6px;flex:1;min-width:0">'
        f'<span style="font-family:\'Barlow Condensed\',sans-serif;font-size:0.82rem;'
        f'color:#F0F0F0;line-height:1.2;word-break:break-word;'
        f'overflow-wrap:break-word;text-align:right">'
        f'{_t(m["away"])}</span>'
        f'{_flag(m["away"], 22)}'
        f'</div>'
        f'</div>'
        f'</div>'
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
        qual    = i < 2
        pts_c   = "#FFDF00" if r["pts"] > 0 else "#757575"
        sg_str  = f'+{r["sg"]}' if r["sg"] > 0 else str(r["sg"])
        border  = "border-top:1px solid rgba(0,156,59,0.13);" if i > 0 else ""
        display = _t(r["team"])
        short   = display[:18] + ("…" if len(display) > 18 else "")
        rank_color = "#009C3B" if qual else "#424242"
        is_br   = r["team"] == "Brazil"
        name_style = "color:#FFDF00;font-weight:700;" if is_br else "color:#F0F0F0;"
        rows_html.append(
            f'<div style="display:flex;align-items:center;padding:0.5rem 1rem;{border}'
            f'{"background:rgba(255,223,0,0.04);" if is_br else ""}">'
            f'<div style="flex:1;display:flex;align-items:center;gap:7px">'
            f'<span style="color:{rank_color};font-size:0.72rem;font-weight:700;'
            f'width:14px;text-align:center">{i+1}</span>'
            f'{_flag(r["team"], 22)}'
            f'<span style="font-family:\'Barlow Condensed\',sans-serif;'
            f'font-size:0.97rem;{name_style}">{short}</span>'
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


def _nations_interactive_grid(nations: list[str]) -> str:
    """Grid de bandeiras: nações com elenco cadastrado são clicáveis."""
    _HAS_SQUAD = {"Argentina", "Brazil", "England", "France", "Germany", "Portugal", "Spain"}
    cards = []
    for nation in nations:
        url    = nation_flag_url(nation, width=40)
        has_sq = nation in _HAS_SQUAD
        short  = _t(nation)[:13] + ("…" if len(_t(nation)) > 13 else "")

        img = (
            f'<img src="{url}" width="40" '
            f'style="border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.5);'
            f'object-fit:cover;height:27px;width:40px">'
            if url else
            '<div style="width:40px;height:27px;border-radius:4px;background:#1a3d25"></div>'
        )

        badge = (
            f'<div style="position:absolute;top:-4px;right:-4px;'
            f'background:#009C3B;border-radius:50%;width:12px;height:12px;'
            f'border:1.5px solid #0B1A12;display:flex;align-items:center;'
            f'justify-content:center;font-size:0.45rem;color:#fff">⭐</div>'
            if has_sq else ""
        )

        inner = (
            f'<div style="display:flex;flex-direction:column;align-items:center;'
            f'width:70px;gap:4px;position:relative">'
            f'<div style="position:relative">{img}{badge}</div>'
            f'<span style="font-size:0.57rem;color:{"#FFDF00" if has_sq else "#cce8d8"};'
            f'text-align:center;line-height:1.2;font-family:Inter,sans-serif;'
            f'font-weight:{"600" if has_sq else "400"}">{short}</span>'
            f'</div>'
        )

        if has_sq:
            cards.append(
                f'<a href="?nav_nation={nation}" title="Ver elenco de {_t(nation)}" '
                f'style="text-decoration:none;cursor:pointer">{inner}</a>'
            )
        else:
            cards.append(inner)

    return (
        '<div style="background:#012A1C;padding:1.2rem 1.4rem;border-radius:12px;'
        'border:1px solid rgba(0,156,59,0.3);margin-top:0.6rem;'
        'display:flex;flex-wrap:wrap;gap:12px;justify-content:flex-start">'
        + "".join(cards) + "</div>"
        + '<p style="color:#616161;font-size:0.65rem;font-family:Inter,sans-serif;'
        + 'margin-top:6px">⭐ <span style="color:#009C3B">Verde</span> = elenco detalhado disponível — clique para explorar</p>'
    )


# ══════════════════════════════════════════════════════════════════════════════
# SEÇÕES DA PÁGINA
# ══════════════════════════════════════════════════════════════════════════════

# ── Últimos Resultados ────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f'<div style="display:flex;align-items:baseline;gap:12px;margin-bottom:0.2rem">'
    f'<h2 style="color:#FFDF00;font-family:\'Barlow Condensed\',sans-serif;'
    f'font-size:1.6rem;font-weight:700;margin:0">🎬 Últimos Resultados</h2>'
    f'<span style="color:#009C3B;font-size:0.75rem;font-family:Inter,sans-serif;'
    f'font-weight:600;text-transform:uppercase;letter-spacing:1px">'
    f'atualizado 14/06/2026 · {len(RESULTS)} partidas</span>'
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
    ncols = min(len(matches), 3)
    cols = st.columns(ncols)
    for col, match in zip(cols, matches):
        with col:
            st.markdown(match_card_html(match), unsafe_allow_html=True)

# ── Próximas Partidas ─────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    f'<div style="display:flex;align-items:baseline;gap:12px;margin-bottom:0.2rem">'
    f'<h2 style="color:#FFDF00;font-family:\'Barlow Condensed\',sans-serif;'
    f'font-size:1.6rem;font-weight:700;margin:0">📅 Próximas Partidas</h2>'
    f'<span style="color:#009C3B;font-size:0.75rem;font-family:Inter,sans-serif;'
    f'font-weight:600;text-transform:uppercase;letter-spacing:1px">'
    f'{len(UPCOMING)} jogos confirmados · dias 14–16/06</span>'
    f'</div>',
    unsafe_allow_html=True,
)

upcoming_by_date: dict[str, list] = {}
for m in UPCOMING:
    upcoming_by_date.setdefault(m["date"], []).append(m)

for date, matches in upcoming_by_date.items():
    st.markdown(
        f'<p style="color:#616161;font-family:Inter,sans-serif;font-size:0.75rem;'
        f'font-weight:600;text-transform:uppercase;letter-spacing:1px;'
        f'margin:1rem 0 0.5rem;border-left:3px solid #424242;padding-left:8px">'
        f'{date}/2026</p>',
        unsafe_allow_html=True,
    )
    cols = st.columns(3)
    for col, match in zip(cols, matches + [None] * (3 - len(matches))):
        with col:
            if match:
                st.markdown(next_match_card_html(match), unsafe_allow_html=True)

# ── Grupos ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 📊 Grupos — Copa 2026")
st.caption("🟢 Top 2 de cada grupo avançam diretamente · os 8 melhores terceiros colocados também avançam")

tabs = st.tabs([f"Grupo {g}" for g in GROUPS])
for tab, letter in zip(tabs, GROUPS):
    with tab:
        rows = sorted(GROUPS[letter], key=lambda r: (-r["pts"], -r["sg"], -r["gp"]))
        st.markdown(standings_html(rows), unsafe_allow_html=True)

        # Indicador de "aguardando" quando nenhuma partida foi disputada
        if all(r["p"] == 0 for r in rows):
            first = _GROUP_START.get(letter, "em breve")
            st.markdown(
                f'<div style="margin-top:10px;padding:10px 14px;border-radius:8px;'
                f'background:#011a10;border:1px dashed rgba(0,156,59,0.3);'
                f'display:flex;align-items:center;gap:8px">'
                f'<span style="font-size:1.2rem">⏳</span>'
                f'<span style="color:#757575;font-size:0.8rem;font-family:Inter,sans-serif">'
                f'Aguardando 1ª rodada · Inicia em '
                f'<strong style="color:#9E9E9E">{first}/2026</strong></span>'
                f'</div>',
                unsafe_allow_html=True,
            )

# ── As 48 seleções ────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 🌍 As 48 seleções classificadas")
st.caption("Clique nas seleções destacadas (⭐) para ver o perfil completo dos jogadores")

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
    st.markdown(_nations_interactive_grid(nations), unsafe_allow_html=True)
except Exception:
    st.info("Execute `make all` para carregar os dados e ver as bandeiras das 48 nações.")

# ── Explorar elenco ───────────────────────────────────────────────────────────
st.markdown("---")
st.markdown("## 🔍 Explorar elenco de uma seleção")

_squad_nations = ["Brazil", "Argentina", "England", "France", "Germany", "Portugal", "Spain"]

nav_col, btn_col = st.columns([3, 1])
with nav_col:
    selected_nav = st.selectbox(
        "Escolha uma seleção para ver figurinhas, análises e radar de desempenho:",
        _squad_nations,
        index=0,  # Brasil como padrão
        key="nav_nation_select",
    )
with btn_col:
    st.write("")
    st.write("")
    if st.button("Ver jogadores →", type="primary", use_container_width=True):
        st.session_state["selected_nation"] = selected_nav
        st.switch_page("pages/4_Perfil_Jogadores.py")

# ── Rodapé ────────────────────────────────────────────────────────────────────
st.markdown("---")
st.markdown(
    '<div style="background:#011a10;border-radius:10px;padding:1rem 1.4rem;'
    'border:1px solid rgba(0,156,59,0.15);display:flex;flex-wrap:wrap;'
    'justify-content:space-between;align-items:center;gap:10px">'
    # links rápidos
    '<div style="display:flex;gap:20px;flex-wrap:wrap">'
    + "".join(
        f'<a href="{href}" style="color:#9E9E9E;font-size:0.72rem;'
        f'font-family:Inter,sans-serif;text-decoration:none;'
        f'font-weight:500;transition:color 0.2s" '
        f'onmouseover="this.style.color=\'#FFDF00\'" '
        f'onmouseout="this.style.color=\'#9E9E9E\'">{label}</a>'
        for label, href in [
            ("🗺️ Mapa", "1_Mapa_Participantes"),
            ("📊 Ranking", "2_Ranking_Historico"),
            ("🇧🇷 Brasil", "3_Brasil_Deep_Dive"),
            ("👤 Jogadores", "4_Perfil_Jogadores"),
        ]
    )
    + '</div>'
    # fonte dos dados
    '<div style="color:#424242;font-size:0.65rem;font-family:Inter,sans-serif;text-align:right">'
    'Dados: FIFA · Transfermarkt · Wikipedia Commons · Natural Earth<br>'
    '<span style="color:#616161">Atualizado em 14/06/2026 · Copa do Mundo FIFA 2026</span>'
    '</div>'
    '</div>',
    unsafe_allow_html=True,
)

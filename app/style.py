"""Shared design system — paleta, CSS e helpers de layout para o dashboard Copa 2026."""
import pandas as pd
import streamlit as st

# ── Paleta Brasil ──────────────────────────────────────────────────────────────
GREEN  = "#009C3B"
YELLOW = "#FFDF00"
BLUE   = "#002776"
DARK_BG     = "#0B1A12"
SIDEBAR_BG  = "#012A1C"
MID_GREEN   = "#013d20"

# Sequência categórica
CHART_PALETTE = [BLUE, GREEN, YELLOW, "#1565C0", "#00C853", "#FFD600", "#26A69A", "#EF5350"]

# Escala sequencial: azul → verde → amarelo (bandeira)
SEQUENTIAL_SCALE = [[0.0, "#002776"], [0.5, "#009C3B"], [1.0, "#FFDF00"]]

# Cores por confederação (vibrantes para fundo escuro)
CONFEDERATION_COLORS = {
    "CONMEBOL": "#00E676",
    "UEFA":     "#40C4FF",
    "CAF":      "#FF5252",
    "AFC":      "#FFAB40",
    "CONCACAF": "#CE93D8",
    "OFC":      "#64FFDA",
}

# Cores por posição
POSITION_COLORS = {
    "GK":         YELLOW,
    "Goalkeeper": YELLOW,
    "Defender":   "#40C4FF",
    "Midfielder": GREEN,
    "Forward":    "#FF5252",
    "Unknown":    "#757575",
}

# ── Layout base Plotly ─────────────────────────────────────────────────────────
_PLOTLY_BASE: dict = dict(
    paper_bgcolor=DARK_BG,
    plot_bgcolor=DARK_BG,
    font=dict(color="#F0F0F0", family="'Barlow Condensed', 'Inter', sans-serif"),
    # title_font removido: criava objeto title.font sem title.text → Plotly JS
    # renderizava "undefined" (exibido como "indefinido" em locale PT)
    xaxis=dict(gridcolor="#1a3d25", linecolor=GREEN, zerolinecolor="#1a3d25"),
    yaxis=dict(gridcolor="#1a3d25", linecolor=GREEN, zerolinecolor="#1a3d25"),
    legend=dict(bgcolor=SIDEBAR_BG, bordercolor=GREEN, borderwidth=1,
                font=dict(color="#F0F0F0")),
    coloraxis_colorbar=dict(
        tickfont=dict(color="#F0F0F0"),
        title_font=dict(color="#F0F0F0"),
    ),
    margin=dict(t=60, b=40, l=40, r=40),
)

_TITLE_FONT = dict(size=20, color=YELLOW, family="'Barlow Condensed', sans-serif")


def plotly_layout(title: str | None = None) -> dict:
    """Retorna o dict de layout base.
    Passa ``title`` para gráficos que precisam de título com fonte amarela.
    """
    base = dict(_PLOTLY_BASE)
    if title:
        base["title"] = dict(text=title, font=_TITLE_FONT)
    return base


# ── CSS global ─────────────────────────────────────────────────────────────────
_CSS = """
<style>
@import url('https://fonts.googleapis.com/css2?family=Barlow+Condensed:wght@400;600;700&family=Inter:wght@400;500&display=swap');

html, body, [class*="css"] {
    font-family: 'Inter', sans-serif;
}
h1, h2, h3 {
    font-family: 'Barlow Condensed', sans-serif !important;
    font-weight: 700 !important;
    letter-spacing: 0.03em;
}

/* ── Sidebar ── */
[data-testid="stSidebar"] {
    background: linear-gradient(180deg, #012A1C 0%, #001a10 100%) !important;
    border-right: 2px solid #009C3B;
}
[data-testid="stSidebarNav"] a span,
[data-testid="stSidebarNav"] a { color: #cce8d8 !important; }
[data-testid="stSidebarNav"] a:hover span,
[data-testid="stSidebarNav"] a:hover { color: #FFDF00 !important; }

/* ── Metric cards ── */
[data-testid="metric-container"] {
    background: linear-gradient(135deg, #012A1C 0%, #013d20 100%) !important;
    border: 1px solid #009C3B !important;
    border-radius: 12px !important;
    padding: 1.2rem !important;
    transition: transform 0.2s ease, box-shadow 0.2s ease, border-color 0.2s ease;
}
[data-testid="metric-container"]:hover {
    transform: translateY(-4px) !important;
    box-shadow: 0 8px 24px rgba(0,156,59,0.35) !important;
    border-color: #FFDF00 !important;
}
[data-testid="stMetricLabel"] > div {
    color: #FFDF00 !important;
    font-size: 0.72rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1.3px !important;
}
[data-testid="stMetricValue"] {
    color: #FFFFFF !important;
    font-family: 'Barlow Condensed', sans-serif !important;
    font-size: 2.2rem !important;
    font-weight: 700 !important;
    line-height: 1.1 !important;
}

/* ── Headings com linha de acento ── */
[data-testid="stMarkdownContainer"] h2,
[data-testid="stMarkdownContainer"] h3 {
    border-bottom: 2px solid #009C3B;
    padding-bottom: 0.3rem;
    color: #FFDF00 !important;
}

/* ── Labels de controles ── */
[data-testid="stSlider"] label,
[data-testid="stSelectbox"] label {
    color: #FFDF00 !important;
    font-size: 0.78rem !important;
    font-weight: 600 !important;
    text-transform: uppercase !important;
    letter-spacing: 1px !important;
}

/* ── Dataframe ── */
[data-testid="stDataFrame"] {
    border: 1px solid rgba(0,156,59,0.3) !important;
    border-radius: 8px !important;
}

/* ── Alert / warning ── */
[data-testid="stAlert"] {
    border-left: 4px solid #FFDF00 !important;
    background: #012A1C !important;
}
</style>
"""


def inject_css() -> None:
    st.markdown(_CSS, unsafe_allow_html=True)


def page_header(title: str, subtitle: str = "") -> None:
    """Banner hero com gradiente verde-azul e borda amarela."""
    sub_html = (
        f'<p style="color:#cce8d8;margin:0.5rem 0 0;font-size:1rem;'
        f'font-family:Inter,sans-serif">{subtitle}</p>'
        if subtitle else ""
    )
    st.markdown(
        f"""<div style="
            background:linear-gradient(135deg,#012A1C 0%,#014D24 60%,#002776 100%);
            padding:1.8rem 2.2rem;border-radius:12px;
            border-left:5px solid #FFDF00;margin-bottom:1.8rem">
          <h1 style="color:#FFDF00;font-family:'Barlow Condensed',sans-serif;
              font-size:2.4rem;margin:0;font-weight:700;letter-spacing:0.03em">{title}</h1>
          {sub_html}
        </div>""",
        unsafe_allow_html=True,
    )


# ── Tradução de nomes de nações: inglês → português ──────────────────────────
NATION_PT: dict[str, str] = {
    "Brazil": "Brasil",          "Argentina": "Argentina",
    "Colombia": "Colômbia",      "Uruguay": "Uruguai",
    "Ecuador": "Equador",        "Venezuela": "Venezuela",
    "Chile": "Chile",            "Peru": "Peru",
    "Paraguay": "Paraguai",      "Bolivia": "Bolívia",
    "United States": "EUA",      "USA": "EUA",
    "Mexico": "México",          "Canada": "Canadá",
    "Costa Rica": "Costa Rica",  "Honduras": "Honduras",
    "Jamaica": "Jamaica",        "Panama": "Panamá",
    "El Salvador": "El Salvador","Haiti": "Haiti",
    "Trinidad and Tobago": "Trinidad e Tobago",
    "Cuba": "Cuba",              "Curaçao": "Curaçao",
    "Germany": "Alemanha",       "West Germany": "Alemanha Ocid.",
    "France": "França",          "Spain": "Espanha",
    "Italy": "Itália",           "England": "Inglaterra",
    "Netherlands": "Holanda",    "Holland": "Holanda",
    "Belgium": "Bélgica",        "Portugal": "Portugal",
    "Croatia": "Croácia",        "Poland": "Polônia",
    "Denmark": "Dinamarca",      "Switzerland": "Suíça",
    "Sweden": "Suécia",          "Norway": "Noruega",
    "Austria": "Áustria",        "Czech Republic": "República Tcheca",
    "Czechia": "República Tcheca","Hungary": "Hungria",
    "Romania": "Romênia",        "Scotland": "Escócia",
    "Wales": "Gales",            "Turkey": "Turquia",
    "Türkiye": "Turquia",        "Greece": "Grécia",
    "Russia": "Rússia",          "Soviet Union": "URSS",
    "Ukraine": "Ucrânia",        "Slovakia": "Eslováquia",
    "Slovenia": "Eslovênia",     "Serbia": "Sérvia",
    "Yugoslavia": "Iugoslávia",  "Bulgaria": "Bulgária",
    "Bosnia and Herzegovina": "Bósnia e Herzegovina",
    "Montenegro": "Montenegro",  "Georgia": "Geórgia",
    "North Macedonia": "Macedônia do Norte",
    "Albania": "Albânia",        "Kosovo": "Kosovo",
    "Ireland": "Irlanda",        "Finland": "Finlândia",
    "Iceland": "Islândia",       "Luxembourg": "Luxemburgo",
    "Morocco": "Marrocos",       "Senegal": "Senegal",
    "Nigeria": "Nigéria",        "Egypt": "Egito",
    "Cameroon": "Camarões",      "Ghana": "Gana",
    "Ivory Coast": "Costa do Marfim",
    "Côte d'Ivoire": "Costa do Marfim",
    "Tunisia": "Tunísia",        "Algeria": "Argélia",
    "South Africa": "África do Sul",
    "Mali": "Mali",              "Guinea": "Guiné",
    "DR Congo": "Congo RD",      "Congo": "Congo",
    "Cape Verde": "Cabo Verde",  "Burkina Faso": "Burkina Faso",
    "Zambia": "Zâmbia",          "Angola": "Angola",
    "Tanzania": "Tanzânia",      "Kenya": "Quênia",
    "Zimbabwe": "Zimbábue",      "Libya": "Líbia",
    "Japan": "Japão",            "South Korea": "Coreia do Sul",
    "Korea Republic": "Coreia do Sul",
    "Iran": "Irã",               "Saudi Arabia": "Arábia Saudita",
    "Australia": "Austrália",    "Qatar": "Catar",
    "Iraq": "Iraque",            "UAE": "Emirados Árabes",
    "United Arab Emirates": "Emirados Árabes",
    "China": "China",            "North Korea": "Coreia do Norte",
    "Indonesia": "Indonésia",    "Uzbekistan": "Uzbequistão",
    "Jordan": "Jordânia",        "New Zealand": "Nova Zelândia",
    "Fiji": "Fiji",
}


def nation_pt(name: str) -> str:
    """Retorna o nome da nação em português (mantém original se não mapeado)."""
    return NATION_PT.get(name, name)


# ── Bandeiras (flagcdn.com) ────────────────────────────────────────────────────
# Mapeamento nome FIFA → código ISO 3166-1 alpha-2
NATION_TO_ISO2: dict[str, str] = {
    # CONMEBOL
    "Brazil": "br", "Argentina": "ar", "Colombia": "co", "Uruguay": "uy",
    "Ecuador": "ec", "Venezuela": "ve", "Chile": "cl", "Peru": "pe",
    "Paraguay": "py", "Bolivia": "bo",
    # CONCACAF
    "United States": "us", "USA": "us", "Mexico": "mx", "Canada": "ca",
    "Costa Rica": "cr", "Honduras": "hn", "Jamaica": "jm", "Panama": "pa",
    "El Salvador": "sv", "Haiti": "ht", "Trinidad and Tobago": "tt",
    "Cuba": "cu", "Guatemala": "gt", "Curacao": "cw", "Curaçao": "cw",
    # UEFA
    "Germany": "de", "West Germany": "de", "East Germany": "de",
    "France": "fr", "Spain": "es", "Italy": "it", "England": "gb-eng",
    "Netherlands": "nl", "Holland": "nl", "Belgium": "be", "Portugal": "pt",
    "Croatia": "hr", "Poland": "pl", "Denmark": "dk", "Switzerland": "ch",
    "Sweden": "se", "Norway": "no", "Austria": "at", "Czech Republic": "cz",
    "Czechia": "cz", "Czechoslovakia": "cz", "Hungary": "hu", "Romania": "ro",
    "Scotland": "gb-sct", "Wales": "gb-wls", "Northern Ireland": "gb-nir",
    "Yugoslavia": "rs", "Serbia": "rs", "Turkey": "tr", "Türkiye": "tr", "Greece": "gr",
    "Russia": "ru", "Soviet Union": "ru", "Ukraine": "ua", "Slovakia": "sk",
    "Slovenia": "si", "Bulgaria": "bg", "Albania": "al", "Kosovo": "xk",
    "North Macedonia": "mk", "Finland": "fi", "Iceland": "is", "Ireland": "ie",
    "Bosnia and Herzegovina": "ba", "Montenegro": "me", "Georgia": "ge",
    "Luxembourg": "lu", "Estonia": "ee", "Latvia": "lv", "Lithuania": "lt",
    "Cyprus": "cy", "Malta": "mt", "Andorra": "ad",
    # CAF
    "Morocco": "ma", "Senegal": "sn", "Nigeria": "ng", "Egypt": "eg",
    "Cameroon": "cm", "Ghana": "gh", "Ivory Coast": "ci", "Côte d'Ivoire": "ci",
    "Tunisia": "tn", "Algeria": "dz", "South Africa": "za", "Mali": "ml",
    "Guinea": "gn", "Zambia": "zm", "Angola": "ao", "Ethiopia": "et",
    "DR Congo": "cd", "Congo": "cg", "Togo": "tg", "Gabon": "ga",
    "Cape Verde": "cv", "Burkina Faso": "bf", "Benin": "bj",
    "Mozambique": "mz", "Tanzania": "tz", "Uganda": "ug", "Sudan": "sd",
    "Zimbabwe": "zw", "Kenya": "ke", "Libya": "ly",
    # AFC
    "Japan": "jp", "South Korea": "kr", "Korea Republic": "kr",
    "Iran": "ir", "Saudi Arabia": "sa", "Australia": "au", "Qatar": "qa",
    "Iraq": "iq", "UAE": "ae", "United Arab Emirates": "ae", "China": "cn",
    "North Korea": "kp", "Indonesia": "id", "Thailand": "th", "Vietnam": "vn",
    "Uzbekistan": "uz", "Jordan": "jo", "Kuwait": "kw", "Bahrain": "bh",
    "Oman": "om", "Palestine": "ps", "Syria": "sy", "Lebanon": "lb",
    "India": "in", "Pakistan": "pk",
    # OFC
    "New Zealand": "nz", "Fiji": "fj", "Papua New Guinea": "pg",
    "Solomon Islands": "sb",
}

_FLAG_CDN = "https://flagcdn.com"
_FLAG_CDN_ALT = "https://hatscripts.github.io/circle-flags/flags"


def _iso2_base(iso2: str) -> str:
    """Normaliza código ISO: sub-nacionais (gb-eng) → base (gb) para CDN alternativo."""
    return iso2.split("-")[0].lower()


def _flag_emoji(iso2: str) -> str:
    """Converte ISO 3166-1 alpha-2 em emoji de bandeira Unicode."""
    base = _iso2_base(iso2)
    try:
        return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in base.upper())
    except Exception:
        return "🏳"


def flag_url(iso2: str, width: int = 40) -> str:
    """URL primária da bandeira no flagcdn.com."""
    return f"{_FLAG_CDN}/w{width}/{iso2.lower()}.png"


def flag_url_alt(iso2: str) -> str:
    """URL alternativa (SVG circular) como fallback."""
    return f"{_FLAG_CDN_ALT}/{_iso2_base(iso2)}.svg"


def flag_img_html(iso2: str, width: int = 40, style_extra: str = "") -> str:
    """<img> com onerror que tenta CDN alternativo e depois exibe emoji."""
    if not iso2:
        return f'<span style="font-size:{int(width*0.7)}px">🏳</span>'
    primary = flag_url(iso2, width)
    alt = flag_url_alt(iso2)
    emoji = _flag_emoji(iso2)
    h = int(width * 0.67)
    base_style = (
        f"width:{width}px;height:{h}px;object-fit:cover;"
        f"border-radius:3px;vertical-align:middle;"
        f"box-shadow:0 1px 4px rgba(0,0,0,0.4);{style_extra}"
    )
    return (
        f'<img src="{primary}" width="{width}" style="{base_style}" '
        f'onerror="if(this.dataset.tried){{this.style.display=\'none\';'
        f'this.insertAdjacentHTML(\'afterend\',\'<span>{emoji}</span>\');}}'
        f'else{{this.dataset.tried=1;this.src=\'{alt}\';}}">'
    )


def nation_flag_url(nation: str, width: int = 40) -> str:
    """URL da bandeira pelo nome da nação (retorna string vazia se não mapeado)."""
    iso = NATION_TO_ISO2.get(nation, "")
    return flag_url(iso, width) if iso else ""


def nation_flag_html(nation: str, width: int = 40) -> str:
    """Retorna tag <img> HTML da bandeira pelo nome da nação."""
    url = nation_flag_url(nation, width)
    if not url:
        h = int(width * 0.67)
        return (
            f'<span style="width:{width}px;height:{h}px;background:#1a3d25;'
            f'border-radius:2px;display:inline-block;vertical-align:middle"></span>'
        )
    h = int(width * 0.67)
    return (
        f'<img src="{url}" width="{width}" '
        f'style="border-radius:2px;object-fit:cover;height:{h}px;'
        f'vertical-align:middle;box-shadow:0 1px 4px rgba(0,0,0,0.4)">'
    )


def nation_flag_html(nation: str, width: int = 40, style_extra: str = "") -> str:
    """<img> com fallback completo pelo nome da nação."""
    iso = NATION_TO_ISO2.get(nation, "")
    if not iso:
        return f'<span style="font-size:{int(width*0.7)}px">🏳</span>'
    return flag_img_html(iso, width, style_extra)


def add_flag_column(df: pd.DataFrame, nation_col: str = "nation",
                    width: int = 40) -> pd.DataFrame:
    """Adiciona coluna 'flag_url' ao DataFrame para uso com st.column_config.ImageColumn."""
    out = df.copy()
    out.insert(0, "flag_url", out[nation_col].map(lambda n: nation_flag_url(n, width)))
    return out


def nations_flag_grid_html(nations: list[str], cols: int = 10) -> str:
    """Gera grid HTML de bandeiras + nomes para uso em st.markdown."""
    cards = []
    for nation in nations:
        url = nation_flag_url(nation, width=40)
        img = (
            f'<img src="{url}" width="40" '
            f'style="border-radius:4px;box-shadow:0 2px 8px rgba(0,0,0,0.5);'
            f'object-fit:cover;height:27px;width:40px">'
            if url else
            '<div style="width:40px;height:27px;border-radius:4px;background:#1a3d25"></div>'
        )
        short = nation[:12] + ("…" if len(nation) > 12 else "")
        cards.append(
            f'<div style="display:flex;flex-direction:column;align-items:center;'
            f'width:70px;gap:4px">'
            f'{img}'
            f'<span style="font-size:0.58rem;color:#cce8d8;text-align:center;'
            f'line-height:1.2;font-family:Inter,sans-serif">{short}</span>'
            f'</div>'
        )
    return (
        '<div style="background:#012A1C;padding:1.2rem 1.4rem;border-radius:12px;'
        'border:1px solid rgba(0,156,59,0.3);margin-top:1rem;'
        f'display:flex;flex-wrap:wrap;gap:12px;justify-content:flex-start">'
        + "".join(cards) + "</div>"
    )


def confederation_legend_html() -> str:
    """HTML de legenda das confederações para uso em st.markdown."""
    items = "".join(
        f'<span style="display:inline-flex;align-items:center;gap:6px;margin-right:18px;margin-bottom:6px">'
        f'<span style="width:14px;height:14px;border-radius:3px;'
        f'background:{color};display:inline-block;flex-shrink:0"></span>'
        f'<span style="color:#F0F0F0;font-size:0.85rem;font-family:Inter,sans-serif">{conf}</span></span>'
        for conf, color in CONFEDERATION_COLORS.items()
    )
    return (
        f'<div style="background:#012A1C;padding:0.8rem 1.4rem;border-radius:8px;'
        f'border:1px solid rgba(0,156,59,0.3);margin-top:0.8rem;'
        f'display:flex;flex-wrap:wrap;align-items:center">'
        f'<span style="color:#FFDF00;font-size:0.72rem;font-weight:600;'
        f'text-transform:uppercase;letter-spacing:1px;margin-right:16px">Confederações</span>'
        f'{items}</div>'
    )

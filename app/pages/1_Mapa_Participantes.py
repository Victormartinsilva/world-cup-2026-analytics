import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

import json
import streamlit as st
import folium
from streamlit_folium import st_folium
import duckdb
from style import (
    inject_css, page_header, confederation_legend_html,
    add_flag_column, nation_pt, NATION_TO_ISO2,
)

st.set_page_config(page_title="Mapa das Nações", layout="wide")
inject_css()
page_header(
    "🗺️ Nações Participantes — Copa 2026",
    "48 seleções classificadas. Passe o mouse sobre o país para ver curiosidades e destaques.",
)

DB_PATH  = Path("data/world_cup.duckdb")
GEO_PATH = Path("data/raw/geo/qualified_nations.geojson")

# ── Cores por nação (fill, stroke) — cores primárias das bandeiras ────────────
NATION_COLORS: dict[str, tuple[str, str]] = {
    # CONMEBOL
    "Brazil":       ("#009C3B", "#FFDF00"),
    "Argentina":    ("#74ACDF", "#FFFFFF"),
    "Colombia":     ("#FCD116", "#003087"),
    "Uruguay":      ("#5EB6E4", "#FFFFFF"),
    "Ecuador":      ("#FFD100", "#003087"),
    "Paraguay":     ("#D52B1E", "#FFFFFF"),
    "Bolivia":      ("#D52B1E", "#F4E400"),
    # CONCACAF
    "United States":("#3C3B6E", "#B22234"),
    "Mexico":       ("#006847", "#CE1126"),
    "Canada":       ("#FF0000", "#FFFFFF"),
    "Panama":       ("#DA121A", "#FFFFFF"),
    "Haiti":        ("#003087", "#D21034"),
    "Curaçao":      ("#002B7F", "#F9E526"),
    # UEFA
    "Germany":      ("#222222", "#FFCE00"),
    "France":       ("#002395", "#ED2939"),
    "Spain":        ("#AA151B", "#F1BF00"),
    "England":      ("#CF091F", "#FFFFFF"),
    "Netherlands":  ("#AE1C28", "#FFFFFF"),
    "Belgium":      ("#222222", "#FAE042"),
    "Portugal":     ("#006600", "#FF0000"),
    "Croatia":      ("#CC0000", "#FFFFFF"),
    "Switzerland":  ("#FF0000", "#FFFFFF"),
    "Austria":      ("#ED2939", "#FFFFFF"),
    "Sweden":       ("#006AA7", "#FECC02"),
    "Norway":       ("#EF2B2D", "#FFFFFF"),
    "Scotland":     ("#003399", "#FFFFFF"),
    "Czechia":      ("#D7141A", "#11457E"),
    "Bosnia and Herzegovina": ("#002395", "#FCD116"),
    "Türkiye":      ("#E30A17", "#FFFFFF"),
    # CAF
    "Morocco":      ("#C1272D", "#006233"),
    "Senegal":      ("#00853F", "#FDEF42"),
    "Egypt":        ("#CE1126", "#FFFFFF"),
    "Ghana":        ("#006B3F", "#FCD116"),
    "Ivory Coast":  ("#F77F00", "#009A44"),
    "Tunisia":      ("#E70013", "#FFFFFF"),
    "Algeria":      ("#006233", "#FFFFFF"),
    "South Africa": ("#007A4D", "#FFB612"),
    "DR Congo":     ("#007FFF", "#F7D618"),
    "Cape Verde":   ("#003893", "#CF2027"),
    # AFC
    "Japan":        ("#BC002D", "#FFFFFF"),
    "South Korea":  ("#003478", "#CD2E3A"),
    "Iran":         ("#239F40", "#DA0000"),
    "Saudi Arabia": ("#165D31", "#FFFFFF"),
    "Australia":    ("#00008B", "#FF0000"),
    "Qatar":        ("#8D1B3D", "#FFFFFF"),
    "Iraq":         ("#CE1126", "#222222"),
    "Jordan":       ("#007A3D", "#FFFFFF"),
    "Uzbekistan":   ("#1EB53A", "#FFFFFF"),
    # OFC
    "New Zealand":  ("#00247D", "#CC142B"),
}

_DEFAULT_COLORS: tuple[str, str] = ("#4CAF50", "#FFDF00")

# ── Informações por nação ─────────────────────────────────────────────────────
NATION_INFO: dict[str, dict] = {
    "Brazil": {
        "group": "C", "confederation": "CONMEBOL",
        "titles": 5, "editions": 22,
        "curiosity": "Único país a disputar todas as 22 edições da Copa do Mundo",
        "players": ["Vinicius Jr.", "Rodrygo", "Endrick", "Alisson"],
    },
    "Argentina": {
        "group": "J", "confederation": "CONMEBOL",
        "titles": 3, "editions": 19,
        "curiosity": "Messi conquistou o título em 2022 no Qatar para completar seu legado",
        "players": ["Lionel Messi", "Lautaro Martínez", "Julián Álvarez", "Emiliano Martínez"],
    },
    "France": {
        "group": "I", "confederation": "UEFA",
        "titles": 2, "editions": 16,
        "curiosity": "Geração de ouro com Mbappé e Griezmann busca o tricampeonato",
        "players": ["Kylian Mbappé", "Antoine Griezmann", "Ousmane Dembélé", "Mike Maignan"],
    },
    "Germany": {
        "group": "E", "confederation": "UEFA",
        "titles": 4, "editions": 20,
        "curiosity": "Segunda maior vencedora; Florian Wirtz é a nova joia da seleção",
        "players": ["Florian Wirtz", "Jamal Musiala", "Kai Havertz", "Joshua Kimmich"],
    },
    "Spain": {
        "group": "H", "confederation": "UEFA",
        "titles": 1, "editions": 16,
        "curiosity": "Lamine Yamal (17 anos) é a sensação da nova geração espanhola",
        "players": ["Lamine Yamal", "Pedri", "Rodri", "Álvaro Morata"],
    },
    "England": {
        "group": "L", "confederation": "UEFA",
        "titles": 1, "editions": 17,
        "curiosity": "Único título em 1966 como sede; Bellingham lidera a geração mais talentosa em décadas",
        "players": ["Jude Bellingham", "Harry Kane", "Bukayo Saka", "Phil Foden"],
    },
    "Portugal": {
        "group": "K", "confederation": "UEFA",
        "titles": 0, "editions": 8,
        "curiosity": "Cristiano Ronaldo em sua possível última Copa; melhor resultado foi 3º em 1966",
        "players": ["Cristiano Ronaldo", "Bruno Fernandes", "Rafael Leão", "Bernardo Silva"],
    },
    "Netherlands": {
        "group": "F", "confederation": "UEFA",
        "titles": 0, "editions": 11,
        "curiosity": "Tricampeã vice (1974, 1978, 2010) — a maior 'zebra' da história do futebol",
        "players": ["Virgil van Dijk", "Frenkie de Jong", "Cody Gakpo", "Memphis Depay"],
    },
    "Croatia": {
        "group": "L", "confederation": "UEFA",
        "titles": 0, "editions": 7,
        "curiosity": "Vice em 2018 e bronze em 2022; Modrić ainda comanda o meio-campo",
        "players": ["Luka Modrić", "Mateo Kovačić", "Ivan Perišić", "Marcelo Brozović"],
    },
    "Belgium": {
        "group": "G", "confederation": "UEFA",
        "titles": 0, "editions": 14,
        "curiosity": "Geração de ouro chegou ao 3º lugar em 2018; De Bruyne ainda no comando",
        "players": ["Kevin De Bruyne", "Romelu Lukaku", "Thibaut Courtois", "Yannick Carrasco"],
    },
    "Switzerland": {
        "group": "B", "confederation": "UEFA",
        "titles": 0, "editions": 12,
        "curiosity": "Consistentemente presentes; melhor resultado foi 4º lugar em 1954",
        "players": ["Granit Xhaka", "Xherdan Shaqiri", "Yann Sommer", "Manuel Akanji"],
    },
    "Austria": {
        "group": "J", "confederation": "UEFA",
        "titles": 0, "editions": 7,
        "curiosity": "Retornou com força após décadas de ausência; 3º lugar em 1954",
        "players": ["Marcel Sabitzer", "David Alaba", "Christoph Baumgartner", "Marko Arnautović"],
    },
    "Sweden": {
        "group": "F", "confederation": "UEFA",
        "titles": 0, "editions": 12,
        "curiosity": "Vice-campeã em 1958 como anfitriã; Alexander Isak é o novo artilheiro",
        "players": ["Alexander Isak", "Dejan Kulusevski", "Viktor Gyökeres", "Emil Forsberg"],
    },
    "Norway": {
        "group": "I", "confederation": "UEFA",
        "titles": 0, "editions": 3,
        "curiosity": "Erling Haaland em sua estreia na Copa — goleador mais temido do mundo",
        "players": ["Erling Haaland", "Martin Ødegaard", "Alexander Sørloth", "Sander Berge"],
    },
    "Scotland": {
        "group": "C", "confederation": "UEFA",
        "titles": 0, "editions": 8,
        "curiosity": "Volta à Copa após 28 anos; eliminou a Noruega de Haaland na repescagem",
        "players": ["Andrew Robertson", "Scott McTominay", "Callum McGregor", "John McGinn"],
    },
    "Czechia": {
        "group": "A", "confederation": "UEFA",
        "titles": 0, "editions": 9,
        "curiosity": "Herdeira da Tchecoslováquia, vice-campeã em 1934 e 1962",
        "players": ["Tomáš Souček", "Patrik Schick", "Vladimír Coufal", "Lukáš Provod"],
    },
    "Bosnia and Herzegovina": {
        "group": "B", "confederation": "UEFA",
        "titles": 0, "editions": 1,
        "curiosity": "Apenas a segunda Copa do Mundo na história; campanha surpreendente em 2014",
        "players": ["Edin Džeko", "Miralem Pjanić", "Sead Kolašinac", "Ermedin Demirović"],
    },
    "Türkiye": {
        "group": "D", "confederation": "UEFA",
        "titles": 0, "editions": 3,
        "curiosity": "3º lugar em 2002 no Japão/Coreia; Arda Güler é a nova estrela turca",
        "players": ["Arda Güler", "Hakan Çalhanoğlu", "Cengiz Ünder", "Kaan Ayhan"],
    },
    "Colombia": {
        "group": "K", "confederation": "CONMEBOL",
        "titles": 0, "editions": 6,
        "curiosity": "James Rodríguez artilheiro em 2014; Luis Díaz é a nova joia cafetera",
        "players": ["James Rodríguez", "Luis Díaz", "Falcao", "Richard Ríos"],
    },
    "Uruguay": {
        "group": "H", "confederation": "CONMEBOL",
        "titles": 2, "editions": 14,
        "curiosity": "Bicampeã mundial (1930, 1950); Darwin Núñez e Valverde lideram a geração atual",
        "players": ["Darwin Núñez", "Federico Valverde", "Rodrigo Bentancur", "Luis Suárez"],
    },
    "Ecuador": {
        "group": "E", "confederation": "CONMEBOL",
        "titles": 0, "editions": 4,
        "curiosity": "Moisés Caicedo (Chelsea) é um dos melhores volantes do mundo",
        "players": ["Moisés Caicedo", "Enner Valencia", "Piero Hincapié", "Gonzalo Plata"],
    },
    "Paraguay": {
        "group": "D", "confederation": "CONMEBOL",
        "titles": 0, "editions": 9,
        "curiosity": "Quartas de final em 2010; Miguel Almirón lidera a nova geração",
        "players": ["Miguel Almirón", "Antonio Sanabria", "Gustavo Gómez", "Omar Alderete"],
    },
    "United States": {
        "group": "D", "confederation": "CONCACAF",
        "titles": 0, "editions": 11,
        "curiosity": "Co-sede com Canadá e México; geração jovem e talentosa lidera a seleção",
        "players": ["Christian Pulisic", "Gio Reyna", "Tyler Adams", "Antonee Robinson"],
    },
    "Mexico": {
        "group": "A", "confederation": "CONCACAF",
        "titles": 0, "editions": 17,
        "curiosity": "Passou das oitavas em 7 Copas seguidas (1994-2018) mas nunca foi além",
        "players": ["Hirving Lozano", "Alexis Vega", "Guillermo Ochoa", "Edson Álvarez"],
    },
    "Canada": {
        "group": "B", "confederation": "CONCACAF",
        "titles": 0, "editions": 2,
        "curiosity": "Alphonso Davies é um dos laterais mais rápidos do mundo; co-sede do torneio",
        "players": ["Alphonso Davies", "Jonathan David", "Tajon Buchanan", "Cyle Larin"],
    },
    "Panama": {
        "group": "L", "confederation": "CONCACAF",
        "titles": 0, "editions": 2,
        "curiosity": "Segunda Copa do Mundo; estreou em 2018 e fez história para o país",
        "players": ["Rommel Quiñones", "Roderick Miller", "Andrés Andrade", "Édgar Bárcenas"],
    },
    "Haiti": {
        "group": "C", "confederation": "CONCACAF",
        "titles": 0, "editions": 2,
        "curiosity": "Retorna à Copa após 52 anos de ausência; última participação foi em 1974",
        "players": ["Frantzdy Pierrot", "Duckens Nazon", "Mechack Jérôme", "Steeven Saba"],
    },
    "Curaçao": {
        "group": "E", "confederation": "CONCACAF",
        "titles": 0, "editions": 1,
        "curiosity": "Estreia histórica! Ilha do Caribe com apenas 150 mil habitantes",
        "players": ["Cuco Martina", "Leandro Bacuna", "Jurickson Profar", "Elson Hooi"],
    },
    "Morocco": {
        "group": "C", "confederation": "CAF",
        "titles": 0, "editions": 7,
        "curiosity": "Sensação em 2022 — 1ª seleção africana a chegar numa semifinal de Copa",
        "players": ["Achraf Hakimi", "Hakim Ziyech", "Yassine Bounou", "Sofyan Amrabat"],
    },
    "Senegal": {
        "group": "I", "confederation": "CAF",
        "titles": 0, "editions": 3,
        "curiosity": "Campeã da AFCON 2021 e 2022; Sadio Mané lidera a geração mais forte da história",
        "players": ["Sadio Mané", "Édouard Mendy", "Kalidou Koulibaly", "Ismaïla Sarr"],
    },
    "Egypt": {
        "group": "G", "confederation": "CAF",
        "titles": 0, "editions": 3,
        "curiosity": "Mo Salah busca brilhar em sua Copa; recordista em gols pela seleção egípcia",
        "players": ["Mohamed Salah", "Ahmed El-Shenawy", "Mostafa Mohamed", "Amr El-Sulaya"],
    },
    "Ghana": {
        "group": "L", "confederation": "CAF",
        "titles": 0, "editions": 4,
        "curiosity": "Eliminada nos pênaltis pelo Uruguai em 2010 num dos momentos mais polêmicos da Copa",
        "players": ["Mohammed Kudus", "Thomas Partey", "Jordan Ayew", "André Ayew"],
    },
    "Ivory Coast": {
        "group": "E", "confederation": "CAF",
        "titles": 0, "editions": 4,
        "curiosity": "País de Didier Drogba; nova geração liderada por Franck Kessié e Sébastien Haller",
        "players": ["Sébastien Haller", "Franck Kessié", "Nicolas Pépé", "Simon Adingra"],
    },
    "Tunisia": {
        "group": "F", "confederation": "CAF",
        "titles": 0, "editions": 6,
        "curiosity": "1ª seleção africana a eliminar um país europeu numa Copa (1978 vs México)",
        "players": ["Wahbi Khazri", "Hannibal Mejbri", "Aymen Dahmen", "Youssef Msakni"],
    },
    "Algeria": {
        "group": "J", "confederation": "CAF",
        "titles": 0, "editions": 4,
        "curiosity": "Campeã da AFCON 2019; Riyad Mahrez é o maior jogador da história do país",
        "players": ["Riyad Mahrez", "Islam Slimani", "Yacine Brahimi", "Andy Delort"],
    },
    "South Africa": {
        "group": "A", "confederation": "CAF",
        "titles": 0, "editions": 4,
        "curiosity": "Único país a sediar uma Copa do Mundo (2010) e não avançar da fase de grupos",
        "players": ["Percy Tau", "Themba Zwane", "Ronwen Williams", "Bongani Zungu"],
    },
    "DR Congo": {
        "group": "K", "confederation": "CAF",
        "titles": 0, "editions": 2,
        "curiosity": "Jogou a Copa em 1974 como Zaire; primeira aparição desde então",
        "players": ["Chancel Mbemba", "Cédric Bakambu", "Yannick Bolasie", "Arthur Masuaku"],
    },
    "Cape Verde": {
        "group": "H", "confederation": "CAF",
        "titles": 0, "editions": 1,
        "curiosity": "Estreia histórica na Copa do Mundo! Pequenas ilhas do Atlântico com grande coração",
        "players": ["Ryan Mendes", "Garry Rodrigues", "Stopira", "João Tavares"],
    },
    "Japan": {
        "group": "F", "confederation": "AFC",
        "titles": 0, "editions": 8,
        "curiosity": "Eliminou Espanha e Alemanha em 2022; o Japão surpreende a cada Copa",
        "players": ["Kaoru Mitoma", "Takumi Minamino", "Shuichi Gonda", "Wataru Endō"],
    },
    "South Korea": {
        "group": "A", "confederation": "AFC",
        "titles": 0, "editions": 11,
        "curiosity": "Semifinalista em 2002 como co-sede; Son Heung-min é o maior ídolo da história",
        "players": ["Son Heung-min", "Lee Kang-in", "Kim Min-jae", "Hwang Hee-chan"],
    },
    "Iran": {
        "group": "G", "confederation": "AFC",
        "titles": 0, "editions": 7,
        "curiosity": "País com mais participações na Copa entre as seleções asiáticas sem sediar",
        "players": ["Sardar Azmoun", "Alireza Jahanbakhsh", "Ali Gholizadeh", "Alireza Beiranvand"],
    },
    "Saudi Arabia": {
        "group": "H", "confederation": "AFC",
        "titles": 0, "editions": 7,
        "curiosity": "Venceu a Argentina 2x1 em 2022 — maior zebra recente da história das Copas",
        "players": ["Salem Al-Dawsari", "Firas Al-Buraikan", "Mohammed Al-Owais", "Saleh Al-Shehri"],
    },
    "Australia": {
        "group": "D", "confederation": "AFC",
        "titles": 0, "editions": 6,
        "curiosity": "Semifinalista em 2006 com Viduka e Kewell; migrou da OFC para a AFC em 2006",
        "players": ["Mat Ryan", "Martin Boyle", "Jackson Irvine", "Mathew Leckie"],
    },
    "Qatar": {
        "group": "B", "confederation": "AFC",
        "titles": 0, "editions": 2,
        "curiosity": "Sede da Copa 2022; primeira anfitriã eliminada na fase de grupos da história",
        "players": ["Akram Afif", "Almoez Ali", "Saad Al-Sheeb", "Hassan Al-Haydos"],
    },
    "Iraq": {
        "group": "I", "confederation": "AFC",
        "titles": 0, "editions": 2,
        "curiosity": "Campeão asiático em 2007; retorna ao palco mundial após décadas de ausência",
        "players": ["Mohanad Ali", "Amjad Attwan", "Bashar Resan", "Ali Faez"],
    },
    "Jordan": {
        "group": "J", "confederation": "AFC",
        "titles": 0, "editions": 1,
        "curiosity": "Estreia histórica na Copa do Mundo; foi finalista da Copa da Ásia 2023",
        "players": ["Yazan Al-Naimat", "Musa Al-Taamari", "Hamza Al-Dardour", "Salem Al-Ajalin"],
    },
    "Uzbekistan": {
        "group": "K", "confederation": "AFC",
        "titles": 0, "editions": 1,
        "curiosity": "Estreia histórica! Nação da Ásia Central com futebol em rápido crescimento",
        "players": ["Eldor Shomurodov", "Jasur Yakhshiboev", "Otabek Shukurov", "Abbosbek Fayzullaev"],
    },
    "New Zealand": {
        "group": "G", "confederation": "OFC",
        "titles": 0, "editions": 3,
        "curiosity": "Única seleção a vencer e empatar em uma Copa sem avançar de fase (2010)",
        "players": ["Chris Wood", "Clayton Lewis", "Winston Reid", "Matthew Garbett"],
    },
}


# ── Helpers ───────────────────────────────────────────────────────────────────
def _nation_flag_emoji(nation: str) -> str:
    iso2 = NATION_TO_ISO2.get(nation, "")
    if not iso2:
        return "🏳️"
    base = iso2.split("-")[0].upper()
    try:
        return "".join(chr(0x1F1E6 + ord(c) - ord("A")) for c in base)
    except Exception:
        return "🏳️"


def _build_tooltip(name: str, info: dict, flag_emoji: str) -> str:
    titles = info.get("titles", 0)
    editions = info.get("editions", "—")
    conf = info.get("confederation", "—")
    group = info.get("group", "—")
    curiosity = info.get("curiosity", "")
    players = info.get("players", [])

    trophy_str = ("🏆 " * titles).strip() if titles > 0 else "—"

    players_rows = "".join(
        f'<div style="padding:3px 0 3px 8px;border-left:2px solid #009C3B;'
        f'margin-bottom:3px;color:#F0F0F0;font-size:0.8rem">⭐ {p}</div>'
        for p in players[:4]
    )

    curiosity_block = (
        f'<div style="color:#cce8d8;font-size:0.76rem;font-style:italic;'
        f'margin-bottom:10px;border-left:3px solid #FFDF00;'
        f'padding-left:8px;line-height:1.5">{curiosity}</div>'
    ) if curiosity else ""

    players_block = (
        f'<div style="color:#FFDF00;font-size:0.68rem;font-weight:700;'
        f'text-transform:uppercase;letter-spacing:1px;margin-bottom:6px">'
        f'Destaques 2026</div>{players_rows}'
    ) if players_rows else ""

    return (
        f'<div style="font-family:Arial,sans-serif;min-width:230px;max-width:290px;'
        f'background:#011a0f;border-radius:10px;overflow:hidden;'
        f'border:1px solid rgba(255,223,0,0.35)">'
        # header
        f'<div style="background:#012A1C;padding:10px 14px;'
        f'border-bottom:2px solid #FFDF00;display:flex;align-items:center;gap:10px">'
        f'<span style="font-size:1.9rem;line-height:1">{flag_emoji}</span>'
        f'<div>'
        f'<div style="color:#FFDF00;font-size:1.05rem;font-weight:700;line-height:1.2">{name}</div>'
        f'<div style="color:#009C3B;font-size:0.72rem;margin-top:2px">{conf} · Grupo {group}</div>'
        f'</div></div>'
        # body
        f'<div style="padding:10px 14px">'
        f'<div style="display:flex;gap:24px;margin-bottom:10px">'
        f'<div style="text-align:center">'
        f'<div style="color:#FFDF00;font-size:1.25rem;font-weight:700">{editions}</div>'
        f'<div style="color:#9E9E9E;font-size:0.63rem;text-transform:uppercase;letter-spacing:0.5px">Edições</div>'
        f'</div>'
        f'<div style="text-align:center">'
        f'<div style="color:#FFDF00;font-size:1rem;font-weight:700;min-width:40px">{trophy_str}</div>'
        f'<div style="color:#9E9E9E;font-size:0.63rem;text-transform:uppercase;letter-spacing:0.5px">Títulos</div>'
        f'</div>'
        f'</div>'
        f'{curiosity_block}'
        f'{players_block}'
        f'</div></div>'
    )


def _make_style(fill: str, stroke: str):
    return lambda f: {
        "fillColor": fill,
        "color": stroke,
        "weight": 1.4,
        "fillOpacity": 0.72,
    }


def _make_highlight(fill: str):
    return lambda f: {
        "fillColor": fill,
        "color": "#FFFFFF",
        "weight": 2.5,
        "fillOpacity": 0.95,
    }


# ── Data ──────────────────────────────────────────────────────────────────────
@st.cache_data
def load_nations():
    con = duckdb.connect(str(DB_PATH), read_only=True)
    df = con.execute(
        "SELECT * FROM mart_nations_performance WHERE qualified_2026 = TRUE"
    ).df()
    con.close()
    return df


@st.cache_data
def load_geojson():
    with open(GEO_PATH, encoding="utf-8") as f:
        return json.load(f)


# ── Render ────────────────────────────────────────────────────────────────────
try:
    df = load_nations()
    geojson = load_geojson()

    m = folium.Map(
        location=[20, 0],
        zoom_start=2,
        tiles="CartoDB dark_matter",
    )

    for feature in geojson.get("features", []):
        name: str = feature.get("properties", {}).get("name", "")
        if not name:
            continue

        fill, stroke = NATION_COLORS.get(name, _DEFAULT_COLORS)
        info = NATION_INFO.get(name, {})
        emoji = _nation_flag_emoji(name)
        tooltip_html = _build_tooltip(name, info, emoji)

        folium.GeoJson(
            feature,
            style_function=_make_style(fill, stroke),
            highlight_function=_make_highlight(fill),
            tooltip=folium.Tooltip(tooltip_html, sticky=True),
        ).add_to(m)

    st_folium(m, width=None, height=540, returned_objects=[])

    st.markdown(
        '<div style="display:flex;align-items:center;gap:18px;'
        'padding:6px 12px;border-radius:8px;margin:4px 0 8px;'
        'background:rgba(0,156,59,0.07);border:1px solid rgba(0,156,59,0.2)">'
        '<span style="color:#616161;font-size:0.72rem;font-family:Inter,sans-serif;'
        'display:flex;gap:14px">'
        '<span>🖱️ <b style="color:#9E9E9E">Scroll</b> para zoom</span>'
        '<span>✋ <b style="color:#9E9E9E">Arrastar</b> para mover</span>'
        '<span>🖱️ <b style="color:#9E9E9E">Hover</b> para curiosidades</span>'
        '</span></div>',
        unsafe_allow_html=True,
    )

    st.markdown(confederation_legend_html(), unsafe_allow_html=True)

    st.markdown("### Tabela — Desempenho histórico das 48 nações")
    tbl_base = (
        df[["nation", "editions_played", "wins", "draws", "losses",
            "total_goals_for", "world_cup_titles", "win_pct"]]
        .sort_values("world_cup_titles", ascending=False)
        .copy()
    )
    tbl_base["nacao"] = tbl_base["nation"].map(nation_pt)
    table_df = add_flag_column(tbl_base, nation_col="nation")
    st.dataframe(
        table_df[["flag_url", "nacao", "editions_played", "wins", "draws",
                  "losses", "total_goals_for", "world_cup_titles", "win_pct"]],
        column_config={
            "flag_url":         st.column_config.ImageColumn("🏳️", width="small"),
            "nacao":            st.column_config.TextColumn("Nação"),
            "editions_played":  st.column_config.NumberColumn("Edições"),
            "wins":             st.column_config.NumberColumn("Vitórias"),
            "draws":            st.column_config.NumberColumn("Empates"),
            "losses":           st.column_config.NumberColumn("Derrotas"),
            "total_goals_for":  st.column_config.NumberColumn("Gols pró"),
            "world_cup_titles": st.column_config.NumberColumn("Títulos"),
            "win_pct":          st.column_config.NumberColumn("% vitórias", format="%.1f%%"),
        },
        use_container_width=True,
        hide_index=True,
    )

except Exception as e:
    st.warning(f"Execute o pipeline primeiro (`make all`). Detalhe: {e}")

"""
Player photo lookup via Wikipedia REST API.
Results are cached to disk (data/player_photos.json) so each player
is only fetched once across all sessions.
"""

import json
import requests
from pathlib import Path
from urllib.parse import quote

_CACHE_PATH = Path("data/player_photos.json")
_WIKI_API = "https://en.wikipedia.org/api/rest_v1/page/summary"
_HEADERS = {"User-Agent": "world-cup-2026-analytics/1.0 (portfolio; victoreagri@gmail.com)"}

# Disambiguation overrides: player name → Wikipedia article slug
_OVERRIDES: dict[str, str] = {
    # Brazil
    "Vinícius Jr":          "Vinícius_Júnior",
    "Éderson":              "Ederson_Moraes",          # sem acento no slug funciona
    "Éder Militão":         "Éder_Militão",
    "Gabriel Magalhães":    "Gabriel_Magalhães",
    "Gabriel (Gabigol)":    "Gabriel_Barbosa",
    "Gabriel Martinelli":   "Gabriel_Martinelli",
    "Bruno Guimarães":      "Bruno_Guimarães",
    "Andreas Pereira":      "Andreas_Pereira",         # sem disambiguation
    "Gerson":               "Gerson_(footballer,_born_1997)",
    "Weverton":             "Weverton",
    "Vanderson":            "Vanderson",
    "Danilo":               "Danilo_(footballer,_born_1991)",
    "Endrick":              "Endrick",
    # Argentina
    "Lautaro Martínez":     "Lautaro_Martínez",
    "Julián Álvarez":       "Julián_Álvarez_(footballer)",
    "Alexis Mac Allister":  "Alexis_Mac_Allister",
    "Lionel Messi":         "Lionel_Messi",
    "Rodrigo De Paul":      "Rodrigo_De_Paul",
    "Emiliano Martínez":    "Emiliano_Martínez",       # slug simples funciona
    "Leandro Paredes":      "Leandro_Paredes",
    "Enzo Fernández":       "Enzo_Fernández",
    "Cristian Romero":      "Cristian_Romero",
    "Nicolás González":     "Nicolás_González_(footballer,_born_1998)",
    "Paulo Dybala":         "Paulo_Dybala",
    "Lisandro Martínez":    "Lisandro_Martínez",
    "Nahuel Molina":        "Nahuel_Molina",
    "Nicolás Tagliafico":   "Nicolás_Tagliafico",
    # Portugal
    "Cristiano Ronaldo":    "Cristiano_Ronaldo",
    "Bruno Fernandes":      "Bruno_Fernandes_(footballer,_born_1994)",
    "Rafael Leão":          "Rafael_Leão",
    "Gonçalo Ramos":        "Gonçalo_Ramos",
    "Vitinha":              "Vitinha_(footballer)",
    "Diogo Costa":          "Diogo_Costa",             # slug simples funciona
    "Nuno Mendes":          "Nuno_Mendes_(footballer,_born_2002)",
    "Rúben Dias":           "Rúben_Dias",
    "João Cancelo":         "João_Cancelo",
    "António Silva":        "António_Silva_(footballer)",
    "Bernardo Silva":       "Bernardo_Silva",
    # France
    "Kylian Mbappé":        "Kylian_Mbappé",
    "Antoine Griezmann":    "Antoine_Griezmann",
    "Ousmane Dembélé":      "Ousmane_Dembélé",
    "Marcus Thuram":        "Marcus_Thuram",
    "Aurélien Tchouaméni":  "Aurélien_Tchouaméni",
    "N'Golo Kanté":         "N'Golo_Kanté",
    "Mike Maignan":         "Mike_Maignan",
    "Theo Hernández":       "Theo_Hernández",
    "Randal Kolo Muani":    "Randal_Kolo_Muani",
    # Germany
    "Jamal Musiala":        "Jamal_Musiala",
    "Florian Wirtz":        "Florian_Wirtz",
    "Joshua Kimmich":       "Joshua_Kimmich",
    "Antonio Rüdiger":      "Antonio_Rüdiger",
    "Kai Havertz":          "Kai_Havertz",
    "Niclas Füllkrug":      "Niclas_Füllkrug",
    # England
    "Jude Bellingham":      "Jude_Bellingham",
    "Bukayo Saka":          "Bukayo_Saka",
    "Phil Foden":           "Phil_Foden",
    "Harry Kane":           "Harry_Kane",
    "Declan Rice":          "Declan_Rice",
    "Cole Palmer":          "Cole_Palmer",             # sem disambiguation
    # Spain
    "Rodri":                "Rodri_(footballer)",
    "Pedri":                "Pedri",
    "Lamine Yamal":         "Lamine_Yamal",
    "Gavi":                 "Gavi_(footballer)",
    "Dani Olmo":            "Dani_Olmo",
    "Nico Williams":        "Nico_Williams",           # sem disambiguation
    "Álvaro Morata":        "Álvaro_Morata",
}


def _fetch_wiki_photo(name: str) -> str:
    """Fetch thumbnail URL from Wikipedia. Returns empty string on any failure."""
    slug = _OVERRIDES.get(name, name.replace(" ", "_"))
    # Encode only non-ASCII and special URL chars; keep underscores (Wikipedia word sep)
    encoded = quote(slug, safe="_")
    try:
        r = requests.get(f"{_WIKI_API}/{encoded}", headers=_HEADERS, timeout=6)
        if r.status_code == 200:
            src = r.json().get("thumbnail", {}).get("source", "")
            if src:
                # Upgrade to larger thumbnail
                for small in ("/50px-", "/80px-", "/100px-", "/150px-", "/200px-"):
                    src = src.replace(small, "/320px-")
            return src
    except Exception:
        pass
    return ""


def load_photos(player_names: list[str]) -> dict[str, str]:
    """
    Return {player_name: photo_url} for all requested names.
    Reads from disk cache; fetches Wikipedia for:
      - names not yet in cache
      - names cached as "" that have an explicit override (so we retry with fixed slugs)
    """
    cache: dict[str, str] = {}
    if _CACHE_PATH.exists():
        try:
            cache = json.loads(_CACHE_PATH.read_text(encoding="utf-8"))
        except Exception:
            cache = {}

    missing = [
        n for n in player_names
        if n not in cache or (cache.get(n) == "" and n in _OVERRIDES)
    ]
    for name in missing:
        cache[name] = _fetch_wiki_photo(name)

    if missing:
        _CACHE_PATH.parent.mkdir(parents=True, exist_ok=True)
        _CACHE_PATH.write_text(
            json.dumps(cache, ensure_ascii=False, indent=2), encoding="utf-8"
        )

    return {n: cache.get(n, "") for n in player_names}

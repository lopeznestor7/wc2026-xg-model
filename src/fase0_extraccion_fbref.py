"""
================================================================================
 FASE 0 — Extracción de datos agregados de FBref
================================================================================
Objetivo:
    Descargar las tablas agregadas por selección del Mundial 2026 desde FBref
    (categorías 'standard' y 'shooting', variantes 'for' y 'against') y el
    calendario completo con resultados.

Por qué un lector propio:
    La función scrape_stats() de ScraperFC 4.5.0 falla sobre este torneo con
        ValueError: Length of values (48) does not match length of index (50)
    Causa: construye el DataFrame con pandas.read_html() (que lee 50 filas,
    incluyendo 2 cabeceras repetidas <tr class="thead"> a mitad de tabla) y
    extrae los IDs de equipo con un filtro que solo cuenta filas con enlace <a>
    (48). No hay alineación fila-a-fila -> revienta.

    Solución: recorrer el <tbody> a mano, descartar filas 'thead', extraer cada
    celda por su atributo data-stat y asignar el team_id desde el enlace de la
    propia fila. La alineación queda garantizada por construcción.

Salida:
    data/standard_for.csv, standard_against.csv, shooting_for.csv,
    shooting_against.csv, calendario.csv
    (y un cache HTML local para no repetir peticiones durante la depuración)

Nota sobre ScraperFC:
    La versión 4.5.0 abre Chrome de forma visible (headless=False) con 6 s de
    espera entre peticiones, conforme a la política de tráfico de Sports
    Reference. NO cierres las ventanas mientras corre.
================================================================================
"""
import os
import re
import pandas as pd
from bs4 import BeautifulSoup
import ScraperFC as sfc

# --- Configuración -----------------------------------------------------------
BASE = "https://fbref.com/en/comps/1"
# OJO: la temporada EN CURSO no lleva año en la ruta (World-Cup-Stats),
# a diferencia de las cerradas (2022/2022-World-Cup-Stats).
SEASON_SLUG_STATS = "World-Cup-Stats"
SEASON_SLUG_SCHED = "World-Cup-Scores-and-Fixtures"
CATEGORIAS = {"standard": "stats", "shooting": "shooting"}
DATA = os.path.join(os.path.dirname(__file__), "..", "data")

pd.set_option("display.max_columns", None)
pd.set_option("display.width", 250)


# --- Utilidades --------------------------------------------------------------
def get_html(url, cache_name):
    """Descarga con cache en disco. Si el .html existe, no toca FBref."""
    cache = os.path.join(DATA, cache_name)
    if os.path.exists(cache):
        print(f">>> Cache: {cache_name}")
        return open(cache, encoding="utf-8").read()
    print(f">>> Descargando {url}")
    print(">>> Se abrirá Chrome. NO cierres las ventanas.")
    html = str(sfc.FBref(wait_time=6)._get_soup(url))
    with open(cache, "w", encoding="utf-8") as f:
        f.write(html)
    print(f">>> Guardado {cache_name} ({len(html):,} chars)")
    return html


def parse_tabla(table_tag):
    """Parsea una tabla de FBref fila a fila.
    Descarta cabeceras repetidas, extrae por data-stat, asigna team_id
    desde el enlace de la fila (o None si no lo hay). Alineado por construcción."""
    filas = []
    tbody = table_tag.find("tbody") or table_tag
    for tr in tbody.find_all("tr"):
        if "thead" in (tr.get("class") or []):
            continue
        celdas = {c.get("data-stat"): c.get_text(strip=True)
                  for c in tr.find_all(["th", "td"]) if c.get("data-stat")}
        if not celdas:
            continue
        a = tr.find("a", href=re.compile(r"/squads/"))
        celdas["team_id"] = a["href"].split("/")[3] if a else None
        filas.append(celdas)
    return pd.DataFrame(filas)


# --- Extracción de stats por categoría ---------------------------------------
def extraer_categoria(categoria):
    url = f"{BASE}/{CATEGORIAS[categoria]}/{SEASON_SLUG_STATS}"
    html = get_html(url, f"cache_{categoria}.html")
    soup = BeautifulSoup(html, "html.parser")
    for sufijo in ["for", "against"]:
        tag = soup.find("table", {"id": re.compile(f"{categoria}_{sufijo}")})
        if tag is None:
            print(f"  !! tabla '{categoria}_{sufijo}' NO encontrada")
            continue
        df = parse_tabla(tag)
        n_sin_id = df["team_id"].isna().sum()
        print(f"  {categoria}_{sufijo}: {df.shape[0]} filas, "
              f"{df['team_id'].notna().sum()} con ID, {n_sin_id} sin ID")
        df.to_csv(os.path.join(DATA, f"{categoria}_{sufijo}.csv"),
                  index=False, encoding="utf-8")


# --- Extracción del calendario -----------------------------------------------
def extraer_calendario():
    url = f"{BASE}/schedule/{SEASON_SLUG_SCHED}"
    html = get_html(url, "cache_schedule.html")
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("table", {"id": re.compile("sched")})
    if tag is None:
        print("  !! tabla de calendario no encontrada")
        return
    filas = []
    for tr in (tag.find("tbody") or tag).find_all("tr"):
        if "thead" in (tr.get("class") or []):
            continue
        d = {c.get("data-stat"): c.get_text(strip=True)
             for c in tr.find_all(["th", "td"]) if c.get("data-stat")}
        if not d or not d.get("home_team"):
            continue
        # IDs desde los enlaces (robusto, sin emparejar nombres)
        for lado in ["home_team", "away_team"]:
            cel = tr.find(attrs={"data-stat": lado})
            a = cel.find("a", href=re.compile(r"/squads/")) if cel else None
            d[f"{lado}_id"] = a["href"].split("/")[3] if a else None
        filas.append(d)
    df = pd.DataFrame(filas)
    jugados = df["score"].astype(str).str.contains("–", na=False).sum()
    print(f"  calendario: {len(df)} partidos, {jugados} disputados")
    df.to_csv(os.path.join(DATA, "calendario.csv"), index=False, encoding="utf-8")


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    for cat in CATEGORIAS:
        print(f"\n{'='*60}\n{cat.upper()}")
        extraer_categoria(cat)
    print(f"\n{'='*60}\nCALENDARIO")
    extraer_calendario()
    print("\n>>> Fase 0 completa. CSVs en data/")

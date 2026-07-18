"""
================================================================================
 FASE 1 — Extracción de xG a nivel de disparo desde Sofascore
================================================================================
Objetivo:
    FBref no publica expected goals (xG) para este torneo (se verificó buscando
    los atributos data-stat 'xg'/'npxg' en el HTML: no existen). Sofascore sí
    publica un valor de xG por cada disparo en su shotmap, con un modelo
    propietario entrenado sobre datos posicionales. Esta fase descarga los
    shotmaps de los 102 partidos y agrega el xG a favor y en contra por partido.

Mecánica:
    ScraperFC accede a la API de Sofascore en modo headless (sin ventana
    visible), mucho más rápido que FBref. Endpoint por partido:
        /event/{match_id}/shotmap
    El shotmap trae, por disparo: xg, xgot (expected goals on target),
    coordenadas del disparo y del remate, parte del cuerpo, tipo de jugada.

Precaución de datos:
    El campo de RESULTADO de Sofascore (gh/ga) incluye los goles de las tandas
    de penales: un 1-1 resuelto 4-3 en la tanda aparece como "4-5". NO usar
    esos goles para nada cuantitativo -> el recuento de goles se toma de FBref
    en la Fase 2. El xG NO se ve afectado (las tandas no generan disparos de
    juego). Aquí solo agregamos xG; gh/ga se guardan solo como referencia visual.

Salida:
    data/sofa_xg.csv  (una fila por partido: xG a favor de local y visitante)
================================================================================
"""
import os
import time
import pickle
import pandas as pd
import ScraperFC as sfc

LIGA, YEAR = "FIFA World Cup", "2026"
DATA = os.path.join(os.path.dirname(__file__), "..", "data")

ss = sfc.Sofascore()


def obtener_lista_partidos():
    """Descarga (con cache) la lista de partidos del torneo con sus match_id."""
    cache = os.path.join(DATA, "sofa_matches.pkl")
    if os.path.exists(cache):
        matches = pickle.load(open(cache, "rb"))
        print(f">>> Cache: {len(matches)} partidos")
    else:
        # Verificar que la clave de temporada de Sofascore sea la esperada.
        seasons = ss.get_valid_seasons(LIGA)
        if YEAR not in seasons:
            raise SystemExit(f"'{YEAR}' no está entre {list(seasons)[:6]}")
        print(f">>> Descargando lista de partidos (season_id {seasons[YEAR]})...")
        matches = ss.get_match_dicts(YEAR, LIGA)
        pickle.dump(matches, open(cache, "wb"))
    return matches


def xg_del_partido(m):
    """Agrega el xG a favor de local y visitante desde el shotmap de un partido.
    Robusto ante shotmaps vacíos o sin columna xg."""
    mid = m["id"]
    home, away = m["homeTeam"]["name"], m["awayTeam"]["name"]
    try:
        s = ss.scrape_match_shots(mid)
    except Exception as e:
        print(f"  !! {home} vs {away}: {e}")
        return None
    if s.empty or "xg" not in s.columns:
        print(f"  !! {home} vs {away}: sin shotmap/xg")
        return None
    s["xg"] = pd.to_numeric(s["xg"], errors="coerce").fillna(0)
    return dict(
        match_id=mid, home=home, away=away,
        home_id=m["homeTeam"]["id"], away_id=m["awayTeam"]["id"],
        gh=m.get("homeScore", {}).get("current"),   # incluye tanda: solo referencia
        ga=m.get("awayScore", {}).get("current"),
        xg_home=round(s.loc[s["isHome"] == True, "xg"].sum(), 3),
        xg_away=round(s.loc[s["isHome"] == False, "xg"].sum(), 3),
        n_shots=len(s),
    )


if __name__ == "__main__":
    os.makedirs(DATA, exist_ok=True)
    matches = obtener_lista_partidos()
    print(f"Total: {len(matches)} partidos\n")

    salida = os.path.join(DATA, "sofa_xg.csv")
    if os.path.exists(salida):
        print(f">>> {salida} ya existe. Bórralo para re-extraer.")
        raise SystemExit

    filas = []
    for i, m in enumerate(matches):
        r = xg_del_partido(m)
        if r:
            filas.append(r)
        if (i + 1) % 10 == 0:
            print(f"  {i+1}/{len(matches)}...")
        time.sleep(0.3)   # cortesía con la API (~3 min en total)

    df = pd.DataFrame(filas)
    df.to_csv(salida, index=False)
    print(f"\n>>> Guardado sofa_xg.csv: {len(df)}/{len(matches)} partidos con xG")
    if len(matches) - len(df):
        print(f"    ({len(matches)-len(df)} partidos sin shotmap)")

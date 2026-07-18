"""
================================================================================
 FASE 2 — Construcción de la tabla maestra y validación de consistencia
================================================================================
Objetivo:
    Unir en una sola tabla por selección:
      - de FBref  : minutos, goles (con y sin penal), penales, tiros a puerta
      - de Sofascore : xG a favor y en contra
    Los goles se toman de FBref (limpios de tanda de penales); el xG de
    Sofascore. NUNCA se mezclan los recuentos de gol de ambas fuentes.

Validaciones incluidas (todas deben pasar):
    1. Goles a favor totales == goles en contra totales
    2. xG a favor total == xG en contra total
    3. Cruce 48/48 selecciones entre FBref y Sofascore
    4. Exposición derivada del calendario == minutos de FBref (hasta redondeo)

Trampas resueltas:
    - Nombres: FBref antepone un código de país de 2 letras (esSpain) y para las
      naciones británicas usa 3 (engEngland). Un regex ^[a-z]{2} rompe England
      -> se corrigen a mano. Sofascore usa nombres distintos (South Korea vs
      Korea Republic) -> mapa explícito.

Salida:
    data/master_xg.csv   (una fila por selección, 48 filas)
================================================================================
"""
import os
import re
import numpy as np
import pandas as pd

DATA = os.path.join(os.path.dirname(__file__), "..", "data")

# Correcciones de nombres FBref mal limpiados (códigos de país de 3 letras)
FIX_FBREF = {"gEngland": "England", "tScotland": "Scotland",
             "sWales": "Wales", "hNorthern Ireland": "Northern Ireland"}

# Mapa de nombres Sofascore -> FBref para los que difieren
SOFA_A_FBREF = {
    "Bosnia & Herzegovina": "Bosnia–Herz", "DR Congo": "Congo DR",
    "South Korea": "Korea Republic", "Iran": "IR Iran", "USA": "United States",
}


def limpiar_fbref(nombre):
    """Quita el prefijo de país de FBref ('esSpain' -> 'Spain', 'vs ' en against)."""
    s = re.sub(r"^vs\s*", "", re.sub(r"^[a-z]{2}", "", nombre)).strip()
    return FIX_FBREF.get(s, s)


def cargar_fbref():
    d = {}
    for f in ["standard_for", "standard_against", "shooting_for", "shooting_against"]:
        x = pd.read_csv(os.path.join(DATA, f"{f}.csv"))
        x["eq"] = x["team"].map(limpiar_fbref)
        d[f] = x
    m = (d["standard_for"][["eq", "team_id", "minutes_90s", "goals", "goals_pens",
                            "pens_made", "pens_att"]]
         .rename(columns={"minutes_90s": "x90", "goals": "G", "goals_pens": "Gnp",
                          "pens_made": "penM", "pens_att": "penA"}))
    m = m.merge(d["shooting_for"][["team_id", "shots", "shots_on_target"]], on="team_id") \
         .rename(columns={"shots": "Sh", "shots_on_target": "SoT"})
    m = m.merge(d["standard_against"][["team_id", "goals", "goals_pens"]], on="team_id") \
         .rename(columns={"goals": "Ga", "goals_pens": "Gnpa"})
    m = m.merge(d["shooting_against"][["team_id", "shots_on_target"]], on="team_id") \
         .rename(columns={"shots_on_target": "SoTa"})
    m["eq"] = m["eq"].replace(FIX_FBREF)
    return m


def agregar_xg():
    x = pd.read_csv(os.path.join(DATA, "sofa_xg.csv"))
    norm = lambda n: SOFA_A_FBREF.get(n, n)
    rows = {}
    for _, r in x.iterrows():
        for eq, xgf, xga in [(norm(r["home"]), r["xg_home"], r["xg_away"]),
                             (norm(r["away"]), r["xg_away"], r["xg_home"])]:
            d = rows.setdefault(eq, dict(xGf=0.0, xGa=0.0))
            d["xGf"] += xgf
            d["xGa"] += xga
    return pd.DataFrame(rows).T.reset_index().rename(columns={"index": "eq"})


def validar(m):
    print("  Goles a favor / en contra:", m["G"].sum(), "/", m["Ga"].sum())
    assert m["G"].sum() == m["Ga"].sum(), "goles a favor != en contra"
    dif_xg = abs(m["xGf"].sum() - m["xGa"].sum())
    print(f"  xG a favor / en contra: {m['xGf'].sum():.1f} / {m['xGa'].sum():.1f}"
          f"  (dif {dif_xg:.2f})")
    assert dif_xg < 0.5, "xG a favor != en contra"

    cal = pd.read_csv(os.path.join(DATA, "calendario.csv"))
    cal = cal[cal["score"].astype(str).str.contains("–", na=False)]
    et = cal["notes"].astype(str).str.contains("extra time", case=False, na=False)
    exp = 2 * ((~et).sum() * 1.0 + et.sum() * 4 / 3)
    print(f"  Exposición calendario / FBref: {exp:.2f} / {m['x90'].sum():.2f}")
    assert abs(exp - m["x90"].sum()) < 3, "exposición inconsistente"
    print("  >>> Todas las validaciones pasaron")


if __name__ == "__main__":
    m = cargar_fbref()
    xg = agregar_xg()
    M = m.merge(xg, on="eq", how="left", indicator=True)
    faltan = M[M["_merge"] != "both"]["eq"].tolist()
    if faltan:
        huerfanos = sorted(set(xg["eq"]) - set(m["eq"]))
        raise SystemExit(f"NO cruzaron: {faltan}\nSofascore sin pareja: {huerfanos}")
    print(f">>> Cruce: {(M['_merge']=='both').sum()}/48 selecciones")

    M = M.drop(columns="_merge")
    validar(M)
    M.to_csv(os.path.join(DATA, "master_xg.csv"), index=False)
    print(f">>> Guardado master_xg.csv ({len(M)} selecciones)")

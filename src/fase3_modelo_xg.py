"""
================================================================================
 FASE 3 — Modelo de expected goals con ajuste por rival
================================================================================
Objetivo:
    Estimar las fuerzas de ataque (generación de xG) y defensa (supresión de xG)
    de las 48 selecciones, ajustadas por la calidad de los rivales, y predecir
    el resultado de la final España-Argentina.

Modelo:
    xG_ij ~ Poisson(mu * alpha_i * delta_j * t_ij)
      alpha_i : generación de xG del equipo i    (mayor = mejor ataque)
      delta_j : supresión de xG del equipo j      (menor = mejor defensa)
      mu      : tasa media del torneo
      t_ij    : exposición del partido (1.0 normal, 4/3 con prórroga)
    Sin término de localía (todo el torneo en sede neutral).
    Sin paso de conversión: el xG YA es el gol esperado, luego lambda = mu*a*d.

Suficiencia:
    En forma log-lineal, los estadísticos suficientes son los totales marginales
    (xG total a favor y en contra de cada selección). Ref: Birch (1963).


Salida:
    data/fuerzas_xg.csv           (alpha, delta de las 48 selecciones)
    outputs/prediccion_xg.txt     (resumen de la predicción)
    outputs/matriz_marcadores.csv (distribución de marcadores)
================================================================================
"""
import os
import numpy as np
import pandas as pd
from scipy.optimize import minimize
from scipy.stats import poisson

DATA = os.path.join(os.path.dirname(__file__), "..", "data")
OUT = os.path.join(os.path.dirname(__file__), "..", "outputs")


# --- Preparación del calendario ----------------------------------------------
def cargar_partidos():
    """Deriva los partidos jugados desde el calendario, con exposición t."""
    c = pd.read_csv(os.path.join(DATA, "calendario.csv"))
    c = c[c["score"].astype(str).str.contains("–", na=False)].copy()
    et = c["notes"].astype(str).str.contains("extra time", case=False, na=False)
    c["t"] = np.where(et, 4 / 3, 1.0)
    return c


# --- Estimación de fuerzas por MLE -------------------------------------------
def ajustar_por_rival(M, cal):
    """MLE de E[xG_ij] = mu*alpha_i*delta_j*t_ij. Depende solo de marginales + diseño."""
    ids = list(M["team_id"]); idx = {t: i for i, t in enumerate(ids)}; n = len(ids)
    I = cal["home_team_id"].map(idx).values
    K = cal["away_team_id"].map(idx).values
    T = cal["t"].values
    xGf = M.set_index("team_id").loc[ids, "xGf"].values.astype(float)
    xGa = M.set_index("team_id").loc[ids, "xGa"].values.astype(float)
    mu = xGf.sum() / (2 * T.sum())

    def nll(p):
        A = p[:n] - p[:n].mean(); D = p[n:]
        return -(xGf @ A + xGa @ D
                 - (mu * T * (np.exp(A[I] + D[K]) + np.exp(A[K] + D[I]))).sum())

    def grad(p):
        A = p[:n] - p[:n].mean(); D = p[n:]
        gA, gD = xGf.copy(), xGa.copy()
        l1 = mu * T * np.exp(A[I] + D[K]); l2 = mu * T * np.exp(A[K] + D[I])
        np.subtract.at(gA, I, l1); np.subtract.at(gD, K, l1)
        np.subtract.at(gA, K, l2); np.subtract.at(gD, I, l2)
        return -np.concatenate([gA, gD])

    r = minimize(nll, np.zeros(2 * n), jac=grad, method="L-BFGS-B",
                 options=dict(maxiter=100000, ftol=1e-16, gtol=1e-12))
    A = r.x[:n] - r.x[:n].mean(); D = r.x[n:]
    a, d = np.exp(A), np.exp(D)

    # VALIDACIÓN obligatoria sobre los marginales
    ff = np.zeros(n); fa = np.zeros(n)
    l1 = mu * T * a[I] * d[K]; l2 = mu * T * a[K] * d[I]
    np.add.at(ff, I, l1); np.add.at(fa, K, l1)
    np.add.at(ff, K, l2); np.add.at(fa, I, l2)
    err = max(np.abs(ff - xGf).max(), np.abs(fa - xGa).max())
    assert err < 1e-4, f"MLE no reproduce los marginales (err={err}); NO confiar"

    F = pd.DataFrame({"eq": M["eq"], "team_id": ids, "alpha": a, "delta": d})
    return mu, F, err


# --- Predicción del partido --------------------------------------------------
def resolver_partido(mu, F, M, eq1="Spain", eq2="Argentina", N=9):
    lam_pen = (M["penA"].sum() / M["x90"].sum()) * (M["penM"].sum() / M["penA"].sum())

    def g(eq):
        r = F[F["eq"] == eq].iloc[0]
        return r["alpha"], r["delta"]

    (a1, d1), (a2, d2) = g(eq1), g(eq2)
    l1 = mu * a1 * d2 + lam_pen    # xG ya es gol esperado -> sin paso de conversión
    l2 = mu * a2 * d1 + lam_pen

    P = np.outer(poisson.pmf(np.arange(N), l1), poisson.pmf(np.arange(N), l2))
    w, dr, l = np.tril(P, -1).sum(), np.trace(P), np.triu(P, 1).sum()
    # Prórroga: 30' = exposición 1/3; tanda de penales 50/50
    Pe = np.outer(poisson.pmf(np.arange(N), l1 / 3), poisson.pmf(np.arange(N), l2 / 3))
    ew, ed, el = np.tril(Pe, -1).sum(), np.trace(Pe), np.triu(Pe, 1).sum()
    return dict(lam1=l1, lam2=l2, P=P, win=w, draw=dr, lose=l,
                campeon1=w + dr * (ew + ed * 0.5),
                campeon2=l + dr * (el + ed * 0.5))


# --- Bootstrap paramétrico ---------------------------------------------------
def bootstrap(mu, F, M, aE, dE, aA, dA, n_rep=4000, seed=11):
    rng = np.random.default_rng(seed)
    lam_pen = (M["penA"].sum() / M["x90"].sum()) * (M["penM"].sum() / M["penA"].sum())
    E0 = M[M["eq"] == "Spain"].iloc[0]; A0 = M[M["eq"] == "Argentina"].iloc[0]

    def camp(a1, d1, a2, d2, N=9):
        l1 = mu * a1 * d2 + lam_pen; l2 = mu * a2 * d1 + lam_pen
        P = np.outer(poisson.pmf(np.arange(N), l1), poisson.pmf(np.arange(N), l2))
        w, dr, l = np.tril(P, -1).sum(), np.trace(P), np.triu(P, 1).sum()
        Pe = np.outer(poisson.pmf(np.arange(N), l1 / 3), poisson.pmf(np.arange(N), l2 / 3))
        ew, ed, _ = np.tril(Pe, -1).sum(), np.trace(Pe), np.triu(Pe, 1).sum()
        return w + dr * (ew + ed * 0.5)

    out = []
    for _ in range(n_rep):
        sE = rng.gamma(E0["xGf"], 1) / E0["xGf"]
        sEa = rng.gamma(E0["xGa"], 1) / E0["xGa"]
        sA = rng.gamma(A0["xGf"], 1) / A0["xGf"]
        sAa = rng.gamma(A0["xGa"], 1) / A0["xGa"]
        out.append(camp(aE * sE, dE * sEa, aA * sA, dA * sAa))
    out = np.array(out)
    return np.percentile(out, [2.5, 50, 97.5]), (out > 0.5).mean()


if __name__ == "__main__":
    os.makedirs(OUT, exist_ok=True)
    M = pd.read_csv(os.path.join(DATA, "master_xg.csv"))
    cal = cargar_partidos()

    mu, F, err = ajustar_por_rival(M, cal)
    F.to_csv(os.path.join(DATA, "fuerzas_xg.csv"), index=False)
    print(f"MLE validado (max err marginales): {err:.2e}\n")

    r = resolver_partido(mu, F, M)
    aE, dE = F[F["eq"] == "Spain"].iloc[0][["alpha", "delta"]]
    aA, dA = F[F["eq"] == "Argentina"].iloc[0][["alpha", "delta"]]
    (lo, med, hi), fav = bootstrap(mu, F, M, aE, dE, aA, dA)

    lineas = [
        "=" * 56,
        "PREDICCIÓN — Final Mundial 2026: España vs Argentina",
        "=" * 56,
        f"mu (xG medio del torneo) : {mu:.4f}",
        f"lambda España            : {r['lam1']:.3f}",
        f"lambda Argentina         : {r['lam2']:.3f}",
        f"total esperado           : {r['lam1']+r['lam2']:.2f} goles",
        "",
        f"90 minutos  -> ESP {r['win']*100:.1f}% | X {r['draw']*100:.1f}% | ARG {r['lose']*100:.1f}%",
        f"Campeón     -> ESP {r['campeon1']*100:.1f}% | ARG {r['campeon2']*100:.1f}%",
        "",
        f"Bootstrap P(España campeón): mediana {med*100:.1f}%  IC95% [{lo*100:.1f}%, {hi*100:.1f}%]",
        f"España favorita en {fav*100:.1f}% de las réplicas",
    ]
    txt = "\n".join(lineas)
    print(txt)
    open(os.path.join(OUT, "prediccion_xg.txt"), "w", encoding="utf-8").write(txt + "\n")

    # Matriz de marcadores a CSV
    P = r["P"][:6, :6]
    mat = pd.DataFrame(P * 100,
                       index=[f"ESP {i}" for i in range(6)],
                       columns=[f"ARG {j}" for j in range(6)]).round(2)
    mat.to_csv(os.path.join(OUT, "matriz_marcadores.csv"))
    print(f"\n>>> Salidas en outputs/")

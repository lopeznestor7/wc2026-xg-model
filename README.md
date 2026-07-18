# Modelo de Expected Goals — Final Mundial 2026 (España vs Argentina)

Modelo probabilístico para predecir el resultado de la final de la Copa Mundial
de la FIFA 2026 (España vs. Argentina, MetLife Stadium, 19 de julio de 2026),
construido a partir de los 102 partidos ya disputados del torneo.

El modelo estima las fuerzas de **ataque** (generación de expected goals) y
**defensa** (supresión de xG) de las 48 selecciones, **ajustadas por la calidad
del rival**, mediante un modelo log-lineal de Poisson. Los datos de xG a nivel de
disparo provienen de Sofascore; el recuento de goles y el calendario, de FBref.

## Resultado

| | 90 minutos | Campeón |
|---|---|---|
| **España** | 41.7 % | **64.9 %** |
| Empate | 41.9 % | — |
| **Argentina** | 16.5 % | **35.1 %** |

λ España = 0.77 · λ Argentina = 0.37 · Total esperado 1.14 goles
Bootstrap: IC 95 % [35.6 %, 89.1 %]. Marcador más probable: **0–0** (32.1 %).

## Hallazgo principal

El relato dominante ("mejor ataque contra mejor defensa") **describe el pasado
pero no lo predice**. Por xG, ambos finalistas generan peligro de forma casi
idéntica (~1.92 xG por 90 min); la diferencia entre 18 y 12 goles es **varianza
de finalización**, no calidad de las ocasiones. La ventaja de España es
**defensiva**: concede el menor xG por 90 minutos de todo el torneo.

## Estructura del repositorio

```
.
├── src/
│   ├── fase0_extraccion_fbref.py        # Descarga tablas y calendario de FBref
│   ├── fase1_extraccion_sofascore_xg.py # Descarga xG por disparo de Sofascore
│   ├── fase2_tabla_maestra.py           # Une fuentes + validaciones de consistencia
│   └── fase3_modelo_xg.py               # MLE ajustado por rival + predicción
├── data/                                # CSVs de datos (versionados)
├── outputs/                             # Predicción y matriz de marcadores
├── docs/                                # Informe LaTeX y PDF
├── requirements.txt
└── README.md
```

## Instalación

```bash
git clone https://github.com/lopeznestor7/wc2026-xg-model.git
cd wc2026-xg-model
python -m venv .venv
source .venv/bin/activate        # Windows: .venv\Scripts\activate
pip install -r requirements.txt
```

## Uso

El repositorio incluye los datos ya extraídos en `data/`, de modo que puedes
reproducir la predicción directamente sin volver a scrapear:

```bash
python src/fase2_tabla_maestra.py    # reconstruye master_xg.csv y valida
python src/fase3_modelo_xg.py        # estima el modelo y predice
```

Para re-extraer los datos desde cero (requiere conexión y abre Chrome):

```bash
python src/fase0_extraccion_fbref.py         # ~5 min, abre ventanas de Chrome
python src/fase1_extraccion_sofascore_xg.py  # ~3 min, headless
```

## Metodología

El modelo es `xG_ij ~ Poisson(μ · αᵢ · δⱼ · tᵢⱼ)`, donde `αᵢ` es la generación de
xG del equipo *i*, `δⱼ` la supresión de xG del equipo *j*, `μ` la tasa media del
torneo y `tᵢⱼ` la exposición del partido (1.0 en tiempo reglamentario, 4/3 con
prórroga). No hay término de localía (torneo en sede neutral) ni paso de
conversión (el xG ya es el gol esperado).

**Suficiencia:** al ser un modelo log-lineal de Poisson, los estadísticos
suficientes son los totales marginales de xG. Por eso el ajuste por rival no
requiere el xG partido a partido, solo el agregado por selección más el diseño
del torneo. La estimación se hace por máxima verosimilitud (L-BFGS-B) con una
aserción que verifica que los marginales ajustados reproducen los observados.

Detalle completo en `docs/informe_xg.pdf`.

## Datos y limitaciones

- El xG de Sofascore proviene de un **modelo propietario** de caja negra: es una
  medición valiosa pero no una verdad de campo.
- El campo de resultado de Sofascore **incluye los goles de las tandas de
  penales**; por eso el recuento de goles se toma de FBref (limpio de tanda) y
  solo el xG de Sofascore.
- Muestra corta (7 partidos por finalista): el intervalo de confianza es ancho
  por construcción.

## Fuentes

- **FBref** (Sports Reference) — tablas agregadas y calendario
- **Sofascore** — expected goals a nivel de disparo
- Extracción vía [ScraperFC](https://github.com/oseymour/ScraperFC) 4.5.0

## Autor

Nestor Lopez — Maestría en Estadística, PUCP

## Licencia

MIT (ver `LICENSE`). Los datos pertenecen a sus respectivas fuentes y se incluyen
únicamente con fines de reproducibilidad académica.

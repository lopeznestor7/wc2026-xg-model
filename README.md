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

Por xG, ambos finalistas generan peligro de forma casi
idéntica (~1.92 xG por 90 min); la diferencia entre 18 y 12 goles es **varianza
de finalización**, no calidad de las ocasiones. La ventaja de España es
**defensiva**: concede el menor xG por 90 minutos de todo el torneo.

## Goles frente a xG: la varianza de finalización

| | | Goles | xG | Diferencia |
|---|---|---|---|---|
| **Ataque** | Argentina | 18 | 14.79 | +3.21 |
| | España | 12 | 13.47 | −1.47 |
| **Defensa** | Argentina | 7 | 3.94 | −3.06 |
| | España | 1 | 2.13 | +1.13 |

*Recuento de goles de FBref (con penales de juego), xG de Sofascore, tras 7 partidos.*

Argentina marcó 3.21 goles **por encima** de su xG (fortuna ofensiva) pero
recibió 3.06 **por encima** del xG que concedió (infortunio defensivo): las dos
desviaciones actúan en sentidos opuestos y **prácticamente se cancelan** (saldo
neto ≈ +0.15). Sus registros reflejan, por tanto, bastante bien su nivel real.
La ventaja de España no viene de que Argentina tuviera suerte neta, sino de que
España **genera casi el mismo xG** (1.92 vs 1.92 por 90 min) pese a marcar menos,
y **concede mucho menos** (0.305 vs 0.512 por 90 min).

> **Nota sobre la normalización.** El xG se mide *por 90 minutos jugados*, no por
> partido. Argentina disputó dos prórrogas (vs. Cabo Verde y Suiza), de modo que
> jugó el equivalente a **7.70** partidos de 90 minutos, no 7. Por eso su xG por
> 90 es 14.79 / 7.70 = **1.92**, y no 14.79 / 7 = 2.11: dividir entre partidos le
> daría crédito extra por los 60 minutos adicionales. España, sin prórrogas, jugó
> 7.00 exactos (13.47 / 7.00 = 1.92). Normalizados por tiempo real en cancha,
> ambos ataques generan el mismo peligro.

## Trayectorias en el torneo

| Fase | Rival de España | Rival de Argentina |
|---|---|---|
| Grupos | Cabo Verde (0–0) | Argelia (3–0) |
| Grupos | Arabia Saudí (4–0) | Austria (2–0) |
| Grupos | Uruguay (1–0) | Jordania (3–1) |
| Dieciseisavos | Austria (3–0) | Cabo Verde (3–2, pr.) |
| Octavos | **Portugal** (1–0) | Egipto (3–2) |
| Cuartos | **Bélgica** (2–1) | Suiza (3–1, pr.) |
| Semifinal | **Francia** (2–0) | Inglaterra (2–1) |

El cuadro de España (Uruguay, Portugal, Bélgica, Francia) fue **sustancialmente
más exigente** que el de Argentina (Argelia, Jordania, Cabo Verde, Egipto,
Suiza). Por eso el ajuste por rival mejora la fuerza ofensiva de España un
**+37.7 %** y la de Argentina apenas nada: el modelo cuantifica esta asimetría
sin recurrir a la reputación de los nombres.

## Matriz de marcadores (90 minutos, %)

Filas: goles de España · Columnas: goles de Argentina · La diagonal son los empates.

| ESP \ ARG | 0 | 1 | 2 | 3 |
|---|---|---|---|---|
| **0** | **32.07** | 11.93 | 2.22 | 0.28 |
| **1** | 24.54 | 9.13 | 1.70 | 0.21 |
| **2** | 9.39 | 3.49 | 0.65 | 0.08 |
| **3** | 2.40 | 0.89 | 0.17 | 0.02 |

El marcador más probable es el **empate sin goles (32.1 %)**, seguido de España
1–0 (24.5 %). Con medias tan bajas, la masa de probabilidad se concentra en los
marcadores mínimos, muchos de ellos igualados: de ahí que el empate en 90
minutos (41.9 %) sea tan probable como la victoria de España.

## Probabilidades derivadas

| Suceso | Probabilidad |
|---|---|
| Menos de 2.5 goles | 89.3 % |
| Más de 2.5 goles | 10.7 % |
| Ambos equipos marcan | 16.6 % |
| España mantiene la portería a cero | 68.9 % |
| Argentina mantiene la portería a cero | 46.5 % |
| El partido llega a la prórroga | 41.9 % |

Una final **cerrada y de pocos goles**: el modelo asigna un 89 % a que se marquen
menos de tres goles y un 42 % a que haya que resolver en la prórroga. Es la
consecuencia directa de enfrentar a las dos mejores defensas del torneo.

## Estructura del repositorio

```
.
├── src/
│   ├── fase0_extraccion_fbref.py        # Descarga tablas y calendario de FBref
│   ├── fase1_extraccion_sofascore_xg.py # Descarga xG por disparo de Sofascore
│   ├── fase2_tabla_maestra.py           # Une fuentes + validaciones de consistencia
│   └── fase3_modelo_xg.py               # MLE ajustado por rival + predicción
├── data/                                # CSVs de datos (versionados)
│   └── DICCIONARIO.md                   # Descripción de cada archivo y columna
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

Detalle completo en `informe_xg.pdf`. (solicitarlo al correo lopez.nestor@pucp.edu.pe)

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

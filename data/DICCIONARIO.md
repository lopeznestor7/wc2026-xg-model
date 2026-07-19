# Diccionario de datos

Descripción de cada archivo de la carpeta `data/` y de sus columnas. Los nombres
de columna abreviados (`Gnp`, `SoTa`, `x90`, etc.) provienen del pipeline de
análisis; aquí se explican todos.

**Convención de sufijos** en la tabla maestra:
- Sin sufijo o `f` = **a favor** (lo que el equipo genera / hace)
- `a` = **en contra / concedido** (lo que el equipo recibe del rival)

**Nota sobre penales:** FBref excluye los penales del recuento de tiros. Por eso
se distingue entre goles totales (`G`) y goles sin penal (`Gnp`): para que las
tasas de conversión tiro→gol sean coherentes, numerador y denominador deben
excluir ambos los penales.

---

## Archivos fuente (extraídos por las Fases 0 y 1)

### `standard_for.csv` / `standard_against.csv`
Estadísticas estándar agregadas por selección (FBref). La variante `_for` son
los valores **a favor** de cada equipo; `_against`, los que **concede** a sus
rivales. Una fila por selección (48 filas).

| Columna | Significado |
|---|---|
| `team` | Nombre de la selección (con prefijo de país de FBref, p. ej. `esSpain`) |
| `players_used` | Jugadores utilizados en el torneo |
| `avg_age` | Edad media de la plantilla |
| `possession` | Posesión media (%) |
| `games` | Partidos jugados |
| `games_starts` | Titularidades acumuladas |
| `minutes` | Minutos totales jugados |
| `minutes_90s` | Minutos en unidades de 90 (= `minutes` / 90). **Clave**: refleja las prórrogas |
| `goals` | Goles (incluye penales) |
| `assists` | Asistencias |
| `goals_assists` | Goles + asistencias |
| `goals_pens` | Goles **sin** penales |
| `pens_made` | Penales convertidos |
| `pens_att` | Penales intentados |
| `cards_yellow` | Tarjetas amarillas |
| `cards_red` | Tarjetas rojas |
| `goals_per90` | Goles por 90 minutos |
| `assists_per90` | Asistencias por 90 |
| `goals_assists_per90` | Goles + asistencias por 90 |
| `goals_pens_per90` | Goles sin penal por 90 |
| `goals_assists_pens_per90` | (Goles sin penal + asistencias) por 90 |
| `team_id` | Identificador del equipo en FBref (8 caracteres, p. ej. `b561dd30`) |

### `shooting_for.csv` / `shooting_against.csv`
Estadísticas de tiro agregadas por selección (FBref). Misma lógica `_for` /
`_against`. Una fila por selección.

| Columna | Significado |
|---|---|
| `team` | Nombre de la selección |
| `players_used` | Jugadores utilizados |
| `minutes_90s` | Minutos en unidades de 90 |
| `goals` | Goles (incluye penales) |
| `shots` | Tiros totales (excluye penales) |
| `shots_on_target` | Tiros a puerta (excluye penales) |
| `shots_on_target_pct` | % de tiros que van a puerta |
| `shots_per90` | Tiros por 90 minutos |
| `shots_on_target_per90` | Tiros a puerta por 90 |
| `goals_per_shot` | Goles por tiro (conversión) |
| `goals_per_shot_on_target` | Goles por tiro a puerta |
| `pens_made` | Penales convertidos |
| `pens_att` | Penales intentados |
| `team_id` | Identificador del equipo en FBref |

### `sofa_xg.csv`
Expected goals agregados por partido (Sofascore). Una fila por partido disputado
(102 filas). El xG se obtiene sumando el xG de cada disparo del *shotmap*.

| Columna | Significado |
|---|---|
| `match_id` | Identificador del partido en Sofascore |
| `home` | Nombre del equipo local |
| `away` | Nombre del equipo visitante |
| `home_id` | Identificador del equipo local en Sofascore |
| `away_id` | Identificador del equipo visitante en Sofascore |
| `gh` | Goles del local. **Ojo**: incluye tanda de penales (solo referencia, no usar) |
| `ga` | Goles del visitante (misma advertencia que `gh`) |
| `xg_home` | xG total generado por el local (suma del shotmap) |
| `xg_away` | xG total generado por el visitante |
| `n_shots` | Número de disparos en el partido |

> **Advertencia sobre `gh` / `ga`:** el campo de resultado de Sofascore suma los
> goles de las tandas de penales (un 1–1 resuelto 4–3 aparece como "4–5"). Por eso
> el recuento de goles del modelo se toma de FBref, no de estas columnas. El xG
> (`xg_home` / `xg_away`) **no** se ve afectado: las tandas no generan disparos de
> juego.

### `calendario.csv`
Calendario completo del torneo con resultados (FBref). 104 filas (102 disputadas
+ final + tercer puesto pendientes en el momento de la extracción).

| Columna | Significado |
|---|---|
| `round` | Fase del torneo (Group stage, Round of 32, ...) |
| `gameweek` | Jornada |
| `dayofweek` | Día de la semana |
| `date` | Fecha del partido |
| `start_time` | Hora de inicio |
| `home_team` | Equipo local |
| `score` | Marcador (vacío si no se ha jugado; formato `2–0`) |
| `away_team` | Equipo visitante |
| `attendance` | Asistencia |
| `venue` | Estadio (todos marcados "Neutral Site") |
| `referee` | Árbitro |
| `match_report` | Enlace al informe del partido |
| `notes` | Notas; **"Required Extra Time"** o "penalty shoot-out" marcan las prórrogas |
| `home_team_id` | Identificador FBref del local |
| `away_team_id` | Identificador FBref del visitante |

---

## Archivos derivados (generados por las Fases 2 y 3)

### `master_xg.csv`
Tabla maestra: una fila por selección (48), con todo lo necesario para el modelo.
Combina goles y tiros de FBref con xG de Sofascore. **Este es el archivo central
del análisis.**

| Columna | Significado |
|---|---|
| `eq` | Nombre limpio de la selección (sin prefijo de país, p. ej. `Spain`) |
| `team_id` | Identificador del equipo en FBref |
| `x90` | Minutos jugados en unidades de 90 (refleja prórrogas; p. ej. Argentina = 7.70) |
| `G` | Goles marcados (incluye penales) |
| `Gnp` | Goles marcados **sin** penales |
| `penM` | Penales convertidos (*made*) |
| `penA` | Penales intentados (*attempted*) |
| `Sh` | Tiros generados (*shots*, excluye penales) |
| `SoT` | Tiros a puerta generados (*shots on target*) |
| `Ga` | Goles encajados (incluye penales) |
| `Gnpa` | Goles encajados **sin** penales (*goals non-penalty against*) |
| `SoTa` | Tiros a puerta concedidos al rival (*shots on target against*) |
| `xGf` | xG total generado (*xG for*, Sofascore) |
| `xGa` | xG total concedido (*xG against*, Sofascore) |

### `fuerzas_xg.csv`
Fuerzas estimadas por el modelo (Fase 3), ajustadas por rival. Una fila por
selección (48). Escala: `1.00` = media del torneo.

| Columna | Significado |
|---|---|
| `eq` | Nombre limpio de la selección |
| `team_id` | Identificador del equipo en FBref |
| `alpha` | Fuerza de **ataque**: generación de xG ajustada por rival. Mayor = mejor ataque |
| `delta` | Fuerza de **defensa**: supresión de xG ajustada por rival. **Menor = mejor defensa** |

---

## Notas técnicas

- **Codificación de fin de línea:** los CSV extraídos de FBref usan CRLF (`\r\n`,
  convención de Windows); los derivados (`master_xg.csv`, `fuerzas_xg.csv`) usan
  LF (`\n`). `pandas.read_csv` maneja ambos sin problema.
- **Identificadores de equipo:** FBref y Sofascore usan sistemas de ID distintos.
  El cruce entre fuentes se hace por nombre de selección (con un mapa de
  correcciones en `src/fase2_tabla_maestra.py`), no por ID.
- **Nombres de selección:** FBref antepone un código de país al nombre en las
  tablas crudas (`esSpain`, `arArgentina`). La columna `eq` de los archivos
  derivados ya está limpia.

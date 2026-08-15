# Partidos sin fecha

Estos partidos **están completos salvo por una cosa: no sabemos qué día se
jugaron.** Todo lo demás —equipos, marcador, jornada, torneo, temporada— salió de
Wikipedia igual que el resto del dataset y pasó por los mismos chequeos.

Van acá y no en `data/` porque el dataset principal promete una fecha en cada
fila, y esa promesa vale la pena mantenerla. Pero **que falte la fecha no es lo
mismo que no tener el partido**, y tirarlos sería perder mil partidos reales por
un campo.

## Qué hay

| temporada | torneo | partidos |
|---|---|---|
| 2008 | Primera C 2008-09 | 384 |
| 2009 | Primera C 2009-10 | 385 |
| 2010 | Primera C 2010-11 | 385 |

Mismo esquema y mismas columnas que `data/partidos-AAAA.csv`, con `date` vacío.
Un archivo por **temporada**, igual que allá.

```python
import pandas as pd, glob
con_fecha = pd.concat(map(pd.read_csv, sorted(glob.glob("data/partidos-*.csv"))))
sin_fecha = pd.concat(map(pd.read_csv, sorted(glob.glob("data/sin-fecha/*.csv"))))
```

Sirven para todo lo que no dependa del calendario: tabla de posiciones, historial
entre dos clubes, goles a favor y en contra, rachas por jornada. No sirven para
nada que necesite ordenar por día o medir descanso entre partidos.

Unas pocas filas **sí** traen fecha (4, 5 y 5): son partidos de definición que la
página publica en una tabla aparte, con día y estadio. Se dejan como están.

## Por qué no tienen fecha

Las páginas de Primera C de esos años publican los resultados en tablas de **tres
columnas** —`Local | Resultado | Visitante`— y nada más. No hay una columna de
fecha que el parser esté leyendo mal: no existe.

Es el mismo caso que la Primera B Nacional 2007-2011, que sí se pudo resolver
cruzando con [worldfootball.net](https://www.worldfootball.net/) para sacar de ahí
—y sólo de ahí— la fecha. **Con Primera C esa salida no está**: el selector de
worldfootball lista para Argentina únicamente Primera División, Primera Nacional,
Primera B Metropolitana, Copa Argentina y Supercopa. Primera C no figura.

### Qué se descartó, y para no volver a mirarlo

**Primera B Metropolitana en worldfootball no llega tan atrás.** Su selector lista
25 temporadas y la más vieja es **2018/2019** — contra las 55 de Primera Nacional,
que llegan hasta 2002. Así que esa vía tampoco sirve para las temporadas viejas de
Primera B, que es la otra categoría con partidos sin fecha esperando
(2010-11, 474 partidos).

Medido sobre el selector de `co5199`, no deducido.

## Si aparece una fuente de fechas

El plan es completarlas y mudarlas a `data/`. Mientras tanto quedan parseadas y
verificadas, así que probar una fuente candidata no obliga a volver a leer las
tres temporadas desde Wikipedia.

El cruce ya está escrito y es el mismo que se usó para la B Nacional
([`fad/fechas.py`](../../fad/fechas.py)): empareja por jornada y marcador único,
sin depender de cómo la otra fuente escriba los nombres, y **sólo copia la fecha
si las dos coinciden también en el resultado**.

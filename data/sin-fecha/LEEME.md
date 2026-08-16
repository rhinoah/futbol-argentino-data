# Partidos sin fecha

Estos partidos **están completos salvo por una cosa: no sabemos qué día se
jugaron.** Son **2 345**, de seis temporadas. Todo lo demás —equipos, marcador, jornada, torneo, temporada— salió de
Wikipedia igual que el resto del dataset y pasó por los mismos chequeos.

Van acá y no en `data/` porque el dataset principal promete una fecha en cada
fila, y esa promesa vale la pena mantenerla. Pero **que falte la fecha no es lo
mismo que no tener el partido**, y tirarlos sería perder mil partidos reales por
un campo.

## Qué hay

| temporada | torneo | partidos | por qué |
|---|---|---|---|
| 2008 | Primera C 2008-09 | 384 | la tabla no tiene columna de fecha |
| 2009 | Primera C 2009-10 | 385 | la tabla no tiene columna de fecha |
| 2010 | Primera C 2010-11 | 385 | la tabla no tiene columna de fecha |
| 2010 | Torneo Argentino A 2010-11 | 438 | **la tiene y la deja vacía** |
| 2010 | Primera B 2010-11 | 474 | **la tiene y la deja vacía** |
| 2005 | Torneo Argentino A 2005-06 | 279 | **la tiene y la deja vacía** |

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

Unas pocas filas **sí** traen fecha: 4, 5 y 5 en las de Primera C —partidos de
definición que la página publica en una tabla aparte, con día y estadio— y unas pocas de las tres que sí la tienen —65 de 438
en el Argentino A 2010-11, 12 de 474 en la Primera B, 12 de 279 en el Argentino A
2005-06—. Se dejan como están.

## Por qué no tienen fecha

Son **dos motivos distintos**, y conviene no confundirlos: uno es que la fuente no
tiene el dato, y el otro es que lo tiene y no lo escribió.

### Primera C: la columna no existe

Las páginas de Primera C de esos años publican los resultados en tablas de **tres
columnas** —`Local | Resultado | Visitante`— y nada más. No hay una columna de
fecha que el parser esté leyendo mal: no existe.

Es el mismo caso que la Primera B Nacional 2007-2011, que sí se pudo resolver
cruzando con [worldfootball.net](https://www.worldfootball.net/) para sacar de ahí
—y sólo de ahí— la fecha. **Con Primera C esa salida no está**: el selector de
worldfootball lista para Argentina únicamente Primera División, Primera Nacional,
Primera B Metropolitana, Copa Argentina y Supercopa. Primera C no figura.

### Argentino A 2010-11 y Primera B 2010-11: la columna existe y está vacía

Éste es el caso raro, y son dos temporadas del mismo año. Sus tablas **sí** traen la columna de fecha —el parser la lee
sin problema en 65 partidos— pero la página la deja en blanco en casi todas las filas.
La Fecha 9 no fecha ninguno de sus 22 partidos; la Fecha 1 fecha 12 de 22.

No es un bug del parser, y verificarlo importaba: si lo fuera, la solución sería
arreglar el parser y no archivar 438 partidos. Se midió jornada por jornada.

La Primera B 2010-11 tiene lo mismo (12 fechadas de 474) más otra cosa: **la mitad
de sus jornadas escribe los clubes con el nombre cortado** —`Sp. Italiano`,
`T. Suárez`, `D. de Belgrano`—. Se resolvieron contra el plantel del propio torneo,
donde la forma larga está y los partidos suman: `Brown (A)` 16 + `Brown de Adrogué`
28 = 44, como los demás.

El **Argentino A 2005-06** cerró la parte más cara: trajo **diez clubes del interior**
que el padrón no tenía —Luján de Cuyo, Ñuñorco, La Plata FC, Atlético Candelaria,
General Paz Juniors, Talleres de Perico…—. Ninguno se dedujo de la abreviatura: cada
uno sale del **artículo que enlaza la tabla de participantes de su propia página**,
que además da la ciudad. Y trajo una corrección que el fixture arbitra solo: su
Apertura es una rueda única —130 de 131 pares se cruzan una vez— y el único par que
se cruzaba dos veces delataba una fila con el club equivocado.

Los 438 del Argentino A 2010-11 están completos y **auditados**: nueve nombres de club venían mal en la
fuente y se corrigieron con la grilla de la zona, cada uno documentado en
[`fad/correcciones.py`](../../fad/correcciones.py). Cuatro eran Unión de Mar del
Plata escrito «Unión (S)», que es el de Sunchales — un club real, que además jugaba
ese mismo torneo en otra zona.

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

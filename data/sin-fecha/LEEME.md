# Partidos sin fecha

Estos partidos **están completos salvo por una cosa: no sabemos qué día se
jugaron.** Son **148**. Todo lo demás —equipos, marcador, jornada, torneo,
temporada— pasó por los mismos chequeos que el resto del dataset.

Van acá y no en `data/` porque el dataset principal promete una fecha en cada
fila, y esa promesa vale la pena mantenerla. Pero **que falte la fecha no es lo
mismo que no tener el partido**, y tirarlos sería perder partidos reales por un
campo.

## Eran 2 345

Esta carpeta tenía seis temporadas enteras: las tres de Primera C 2008-2011, la
Primera B 2010-11 y los dos Argentinos A. Ya no. Lo que quedó son **148** filas en
doce torneos, y salvo el bloque del Argentino A 2004-05 que se explica acá abajo,
**ninguna está acá porque su torneo no tenga fuente de fechas**: están una por
una, por su propio motivo.

| de dónde sale la fecha en el resto del dataset | filas |
|---|---|
| [ESPN](https://www.espn.com.ar/) | 1 547 |
| [worldfootball](https://www.worldfootball.net/) | 1 520 |
| [RSSSF](https://www.rsssf.org/) | 263 |

El crédito viaja **fila por fila** en la columna `source`, que queda compuesta:

```
https://es.wikipedia.org/wiki/Campeonato_de_Primera_C_2009-10_(Argentina) + https://www.espn.com.ar/
```

Ninguna de esas fuentes aporta otra cosa que la fecha. Equipos, marcador y
jornada siguen saliendo de Wikipedia, y el marcador de la otra fuente se usa
**para verificar** que las dos partes hablan del mismo partido: si no coinciden,
no se completa nada y se avisa.

## Las 41 del Argentino A 2004-05 son otra cosa

Y conviene separarlas, porque no les falta la fecha por el mismo motivo que a las
demás. A ésas **no la tiene la fuente**.

De ese torneo Wikipedia publica la fase final sólo como cuadro, y un cuadro no
dice quién jugó de local. RSSSF sí lo dice, pero su archivo de esa temporada está
escrito en un formato compacto que pone las dos patas en un renglón y la fecha
como **rango**:

```
Quarterfinals [Nov 20-28]
Aldosivi                 0-1 1-3 Luján de Cuyo
```

De ahí sale todo salvo el día: quién fue local en cada pata, el marcador de cada
una y de qué ronda son. **Un rango no es una fecha**, así que no se reparte: el
28 de noviembre no es «la fecha de la vuelta», es el final de una ventana. Las 41
filas entran acá enteras y sin inventar el día.

Son también las primeras de esta carpeta cuyo marcador **no** sale de Wikipedia.
La columna `source` lo dice fila por fila, y son las únicas: de las 148, 41 traen
a RSSSF como fuente del partido y las otras 107 sólo esperaban una fecha.

Ese torneo tiene 61 filas acá en total. Las otras 20 ya estaban, y están por los
motivos de la sección siguiente.

## Por qué quedaron las otras

Son tres motivos, y los tres son honestos.

**Las dos fuentes cuentan el partido distinto.** Diez casos. Nuestro marcador y
el de la otra fuente no coinciden, así que el emparejamiento no está verificado y
la fecha no se toma. Es la regla funcionando: un partido que dos fuentes cuentan
distinto es información sobre los datos, no un problema a tapar.

**El cruce no identifica un solo partido.** La mayoría. Los playoffs vuelven a
cruzar a los mismos dos clubes, y cuando la fuente no publica el número de
jornada —el feed de ESPN no lo hace— ese par deja de identificar. Ahí se
descartan los dos: *lo que no identifica uno solo, no identifica nada*.

**Y uno solo del Argentino A 2005-06**, que antes eran quince. Los otros
catorce se arreglaron: la página había **copiado las tablas de dos jornadas del
Clausura dentro del Apertura**, y sus propias tablas de posiciones —que el
copy-paste no tocó— dijeron qué iba ahí. El que queda es La Florida vs Sportivo
Patria: se abandonó y el fallo fue *«0-1 en contra de los dos»*, que no es un
marcador y este esquema no puede expresarlo. Es el mismo caso que
Laferrere–Dock Sud en la Primera C 2015.

## Cómo se usan

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

## Cómo llega una fila acá

Ya no hace falta marcar nada en el catálogo. **El reparto es por fila**: la que
tiene fecha va a `data/`, la que no, viene acá. Antes se decidía por torneo, y esa
regla tenía las dos mitades mal — un torneo marcado iba entero a esta carpeta
aunque tuviera fechas, y en cualquier otro las filas sin fecha **se tiraban**, que
es justo lo contrario de lo que dice esta página. Al arreglarlo aparecieron 16
partidos reales que se venían descartando en Primera Nacional 2007, 2023 y 2026,
Federal A 2024 y Primera C 2024.

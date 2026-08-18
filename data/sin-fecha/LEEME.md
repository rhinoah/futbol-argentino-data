# Partidos sin fecha

Estos partidos **están completos salvo por una cosa: no sabemos qué día se
jugaron.** Son **71**. Todo lo demás —equipos, marcador, jornada, torneo,
temporada— salió de Wikipedia igual que el resto del dataset y pasó por los
mismos chequeos.

Van acá y no en `data/` porque el dataset principal promete una fecha en cada
fila, y esa promesa vale la pena mantenerla. Pero **que falte la fecha no es lo
mismo que no tener el partido**, y tirarlos sería perder partidos reales por un
campo.

## Eran 2 345

Esta carpeta tenía seis temporadas enteras: las tres de Primera C 2008-2011, la
Primera B 2010-11 y los dos Argentinos A. Ya no. Lo que quedó es un resto de
setenta y dos filas repartido en diez torneos, y **ninguna está acá porque su
torneo no tenga fuente de fechas**: están una por una, por su propio motivo.

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

## Por qué quedaron estas setenta y dos

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

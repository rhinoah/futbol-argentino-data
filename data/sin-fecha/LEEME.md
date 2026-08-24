# Partidos sin fecha

Estos partidos **están completos salvo por una cosa: no sabemos qué día se
jugaron.** Son **29**. Todo lo demás —equipos, marcador, jornada, torneo,
temporada— pasó por los mismos chequeos que el resto del dataset.

Con una excepción que conviene decir arriba de todo, porque contradice el
párrafo anterior: **seis de las 29 no esperan ninguna fecha, porque no se
jugaron.** Son los que el Torneo Federal A 2024 le dio por perdidos a Sansinena
cuando desertó del torneo. Llevan `status = no disputado` en el CSV, así que se
los distingue sin leer esto: el marcador está porque cuenta para la tabla, pero
no salió de una cancha y no hay día que buscarle. La página lo escribe en la
estructura de la fila —una sola celda tapando Estadio, Fecha y Hora— y de ahí
sale la marca.

Van acá y no en `data/` porque el dataset principal promete una fecha en cada
fila, y esa promesa vale la pena mantenerla. Pero **que falte la fecha no es lo
mismo que no tener el partido**, y tirarlos sería perder partidos reales por un
campo.

## Eran 2 345

Esta carpeta tenía seis temporadas enteras: las tres de Primera C 2008-2011, la
Primera B 2010-11 y los dos Argentinos A. Ya no. Lo que quedó son **29** filas en
cuatro torneos, y salvo el bloque del Argentino A 2004-05 que se explica acá abajo,
**ninguna está acá porque su torneo no tenga fuente de fechas**: están una por
una, por su propio motivo.

| de dónde sale la fecha en el resto del dataset | filas |
|---|---|
| [RSSSF](https://www.rsssf.org/) | 3 545 |
| [worldfootball](https://www.worldfootball.net/) | 1 519 |
| [el blog de José Carluccio](http://josecarluccio.blogspot.com/) | 36 |
| [ESPN](https://www.espn.com.ar/) | 21 |

RSSSF pasó de aportar 263 fechas a 3 545 al arreglar tres cosas que le impedían
leer, ninguna de ellas en los datos: la fase regular de sus archivos **no lleva
encabezado de zona** cuando el torneo no tiene zonas y el lector devolvía cero
partidos sin un aviso; desde 2010-11 las divisiones **comparten archivo** y hay
que acotar la sección o los partidos de siete torneos caen en la misma bolsa; y un
título como `Third Phase Reválida` no era título de nada.

Ese mismo movimiento le sacó filas a ESPN, que las fechaba antes. **Cuando dos
fuentes dan días distintos se conserva la primera y se avisa** — son 82 partidos
en diez páginas, y hasta que ese aviso existió el árbitro era el orden en que
corrían los completadores.

El crédito viaja **fila por fila** en la columna `source`, que queda compuesta:

```
https://es.wikipedia.org/wiki/Campeonato_de_Primera_C_2009-10_(Argentina) + https://www.rsssf.org/
```

Ninguna de esas fuentes aporta otra cosa que la fecha. Equipos, marcador y
jornada siguen saliendo de Wikipedia, y el marcador de la otra fuente se usa
**para verificar** que las dos partes hablan del mismo partido: si no coinciden,
no se completa nada y se avisa.

## Las 21 del Argentino A 2004-05 son otra cosa

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
28 de noviembre no es «la fecha de la vuelta», es el final de una ventana. Las
filas entran acá enteras y sin inventar el día.

Eran 57 y son 21. Las otras 36 las fechó una fuente citada —un blog que publica
esa temporada partido por partido, con día, sede y goleadores— y es el **único
lugar del repo donde un dato se copió a mano**. Va con el mismo contrato que
cualquier otro completador: los clubes **y la llave** identifican el partido y el
marcador lo verifica, así que una línea mal copiada no se cuela. La llave hace
falta porque esa temporada tiene Apertura y Clausura, y los playoffs vuelven a
cruzar a los mismos dos clubes: sin ella las dos filas caen en la misma casilla y
se pierden las dos. De ahí sale la fecha y nada más, y si algún día una base de
datos la contradice, gana la base de datos. El detalle está en `fad/citadas.py`.

Hay un testigo a favor de esa fuente, que es lo más fuerte que se consiguió:
`Ben Hur 5-0 Talleres (P)` lo fecha el blog el 03/04/2005 y lo fecha Wikipedia el
2005-04-03, por caminos separados. Y un límite: la vuelta de la final de la
Reválida del Apertura el blog la da 28/12 y 4-1, contra 26/12 y 2-0 de la página
y del artículo del club. No entró, y no hizo falta decidirlo a mano — con ese
marcador la cita no verifica y el completador la frenó solo.

Son también las únicas de esta carpeta cuyo marcador **no** sale de Wikipedia.
La columna `source` lo dice fila por fila: de las 29, 21 traen a RSSSF como fuente
del partido, 6 son las que no se jugaron y las otras 2 sólo esperan una fecha.

## Por qué quedaron las otras

Sacando las 21 del Argentino A 2004-05 y los 6 que no se jugaron, quedan **2**.

**Las dos fuentes cuentan el partido distinto.** Platense vs Estudiantes (BA),
fecha 6 de la Primera B 2010-11: nosotros tenemos 1-1 y la otra fuente 0-0. El
emparejamiento no está verificado, así que la fecha no se toma. Es la regla
funcionando: un partido que dos fuentes cuentan distinto es información sobre los
datos, no un problema a tapar.

**Y uno que sigue en juego.** San Martín (SJ) vs Nueva Chicago, fecha 17 de la
Primera Nacional 2026, con `status = suspendido`. Ese va a tener fecha cuando la
temporada la tenga.

Eran 13 hace poco, y las once que salieron no necesitaron ninguna fuente nueva:

- **Cuatro** —las promociones de la B Nacional 2007-08— estaban en RSSSF y el repo
  no las leía, porque sus archivos de esa temporada escriben la fecha entre
  paréntesis (`(Jun 21)` suelto, `Second Legs (Jun 28)`) donde los demás usan
  corchetes.
- **Cinco** —cuatro de la fecha 35 de la Primera Nacional 2023 y una de la fecha
  19 de la Primera C 2024— estaban en ESPN, que el repo ya lee para otras
  temporadas y no estaba enchufado para éstas.
- **Dos** —las patas de la Tercera Fase del Argentino A 2010-11— resultaron ser un
  error de la página: tenía los dos partidos con la localía al revés, y al
  corregirla se emparejaron con RSSSF y quedaron fechadas.

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

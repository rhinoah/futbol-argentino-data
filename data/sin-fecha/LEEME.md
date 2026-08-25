# Partidos sin fecha

Estos partidos **están completos salvo por una cosa: no sabemos qué día se
jugaron.** Son **9**. Todo lo demás —equipos, marcador, jornada, torneo,
temporada— pasó por los mismos chequeos que el resto del dataset.

Con una excepción que conviene decir arriba de todo, porque contradice el
párrafo anterior: **seis de las 9 no esperan ninguna fecha, porque no se
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
Primera B 2010-11 y los dos Argentinos A. Ya no. Lo que quedó son **9** filas en
tres torneos, y salvo el bloque del Argentino A 2004-05 que se explica acá abajo,
**ninguna está acá porque su torneo no tenga fuente de fechas**: están una por
una, por su propio motivo.

| de dónde sale la fecha en el resto del dataset | filas |
|---|---|
| [RSSSF](https://www.rsssf.org/) | 3 551 |
| [worldfootball](https://www.worldfootball.net/) | 1 519 |
| [el blog de José Carluccio](http://josecarluccio.blogspot.com/) | 55 |
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

## Las 2 del Argentino A 2004-05 son otra cosa

Eran **61**. De ese torneo Wikipedia publica la fase final sólo como cuadro, y un
cuadro no dice quién jugó de local; RSSSF sí, pero su archivo de esa temporada
está en formato compacto, con las dos patas en un renglón y la fecha como
**rango**. Un rango no es una fecha, así que no se reparte.

Las **55** las fechó una fuente citada —un blog que publica esa temporada partido
por partido, con día, sede y goleadores— y es el **único lugar del repo donde un
dato se copió a mano**. Va con el mismo contrato que cualquier otro completador:
los clubes y la llave identifican, y el marcador verifica. El detalle está en
`fad/citadas.py`, con dos cosas que costaron y conviene saber:

- **El post es la fase.** Los mismos dos clubes con el mismo resultado aparecen en
  dos torneos distintos: `Desamparados 1-0 Luján de Cuyo` es la semifinal del
  Apertura del 01/12/2004 *y* la segunda fecha de la Zona Cuyo del Clausura del
  22/01/2005. Buscar por par y marcador en todo el blog da una fecha que parece
  única y es de otro partido; se busca en el post de la fase de la fila.
- **La fuente puede errarle al día aunque el marcador coincida.** El blog escribe
  `01/02/2004 en Rafaela: Ben Hur 2, Atlético Tucumán 1` entre un partido del
  01/12 y otro del 05/12, en las semifinales de un torneo que empezó en
  septiembre. Hay un test que exige que toda cita caiga en la ventana de su
  temporada, y ése no entra.

Las 2 que quedan son ésa y la vuelta de la final de la Reválida del Apertura,
cuyo marcador el blog da 4-1 contra el 2-0 de la página.

## Por qué quedó la otra

Sacando las 2 del Argentino A 2004-05 y los 6 que no se jugaron, queda **1**.

**Uno que sigue en juego.** San Martín (SJ) vs Nueva Chicago, fecha 17 de la
Primera Nacional 2026, con `status = suspendido`. Ese va a tener fecha cuando la
temporada la tenga.

Acá había un segundo, y salió: **Platense vs Estudiantes (BA)**, fecha 6 de la
Primera B 2010-11. Estaba porque las dos fuentes lo contaban distinto —la página
1-1 y las otras 0-0—, y sin marcador que verifique el emparejamiento la fecha no
se toma. Lo arbitró el **historial de la propia página**: el artículo se editaba
en vivo, y entre la revisión del 30/08/2010 y la del 31/08 —con el partido jugado
en el medio— los dos clubes suman un partido, un empate y un punto **y los goles
no se mueven**. Era 0-0. El detalle está en `fad/correcciones.py`.

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

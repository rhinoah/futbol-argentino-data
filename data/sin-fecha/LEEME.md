# Partidos sin fecha

Acá van los partidos del dataset que **no tienen fecha**. Hoy son **6**, y ninguno
la espera: **no se jugaron.** Todo lo demás —equipos, marcador, jornada, torneo,
temporada— pasó por los mismos chequeos que el resto del dataset.

Son los seis que el Torneo Federal A 2024 le dio por perdidos a Sansinena
cuando desertó del torneo, de la fecha 13 a la 18. Llevan `status = no disputado` en el CSV, así que se
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
Primera B 2010-11 y los dos Argentinos A. Ya no. Lo que quedó son **6** filas de
un solo torneo, y **ninguna espera una fecha**. Las que la esperaban la fueron
consiguiendo: casi todas en bloque —la carpeta pasó de 2 345 a 72 en una tarde, el 17 de
agosto de 2026—, y las últimas una por una, cada una por su propio motivo. Lo que sigue
cuenta cómo.

| qué segunda fuente nombra `source` en el resto del dataset | filas |
|---|---|
| [RSSSF](https://www.rsssf.org/) | 8 082 |
| [worldfootball](https://www.worldfootball.net/) | 1 519 |
| [el blog de José Carluccio](http://josecarluccio.blogspot.com/) | 76 |
| [ESPN](https://www.espn.com.ar/) | 21 |
| otras cuatro, citadas fila por fila | 5 |

Medido el 11 de octubre de 2026.

RSSSF pasó de aportar 263 fechas a 3 545 al arreglar tres cosas que le impedían
leer, ninguna de ellas en los datos: la fase regular de sus archivos **no lleva
encabezado de zona** cuando el torneo no tiene zonas y el lector devolvía cero
partidos sin un aviso; desde 2010-11 las divisiones **comparten archivo** y hay
que acotar la sección o los partidos de siete torneos caen en la misma bolsa; y un
título como `Third Phase Reválida` no era título de nada.

Ese mismo movimiento le sacó filas a ESPN, que las fechaba antes. **Cuando dos
fuentes dan días distintos se conserva la primera y se avisa** — eran 82 partidos
en diez páginas, y hasta que ese aviso existió el árbitro era el orden en que
corrían los completadores. Hoy el build no avisa ninguno: se cerraron uno por uno, y
los que hubo que declarar a mano están en `fad/correcciones.py` (13 donde nuestra
fecha estaba bien y 22 donde no; ahí hay otras 6 fechas corregidas a mano que no
salieron de este aviso).

El crédito viaja **fila por fila** en la columna `source`, que queda compuesta:

```
https://es.wikipedia.org/wiki/Campeonato_de_Primera_C_2009-10_(Argentina) + https://www.rsssf.org/
```

En la mayoría de esas filas la otra fuente aporta la fecha y nada más. Equipos,
marcador y jornada siguen saliendo de Wikipedia, y el marcador de la otra fuente se
usa **para verificar** que las dos partes hablan del mismo partido: si no coinciden,
no se completa nada y se avisa.

La excepción son 3 959 filas, y es la razón de que RSSSF figure con 8 082. En once
torneos la página de Wikipedia publica la tabla y no los partidos —la Primera División
de 1985-86 a 1989-90, el Apertura 1990, el Clausura 1991 y los Argentino A de 2006-07 a
2009-10—, y ahí las 3 812 filas salen enteras de RSSSF: Wikipedia pone la tabla de
posiciones que las verifica, salvo en las 190 de las fechas 20 a 38 de la 1988-89, que
sólo cierran contra la tabla de la propia RSSSF. Las otras 147 son llaves de fase final
que la página trae sólo como cuadro: 133 salen de RSSSF y 14, las de la Primera C
2011-12, de ESPN.

## Las del Argentino A 2004-05 eran otra cosa

Eran **61**. De ese torneo Wikipedia publica la fase final sólo como cuadro, y un
cuadro no dice quién jugó de local; RSSSF sí, pero su archivo de esa temporada
está en formato compacto, con las dos patas en un renglón y la fecha como
**rango**. Un rango no es una fecha, así que no se reparte.

Las **55** las fechó una fuente citada —un blog que publica esa temporada partido
por partido, con día, sede y goleadores—, **copiadas a mano**. No son las únicas: hay
otras 28 fechas escritas a mano en `fad/correcciones.py`, 20 de ellas de ese mismo blog. Va con el mismo contrato que cualquier otro completador:
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

Quedaban 2: ésa y la vuelta de la final de la Reválida del Apertura, cuyo marcador
el blog da 4-1 contra el 2-0 de la página. Salieron las dos. La final se arbitró a
favor del blog —nombra a los cinco goleadores, y en un 2-0 no entran cinco goles—, y
con el marcador verificado entró su fecha: 28/12/2004. A la semifinal la fechó una
segunda fuente citada, la página de un hincha de Ben Hur, que da el 01/12/2004 y
coincide con el blog en las otras tres fechas de esa llave.

## Por qué quedaba la otra

Cuando la carpeta tenía 9 filas —el 25 de agosto de 2026—, sacando las 2 del Argentino A
2004-05 y los 6 que no se jugaron quedaba **1**.

**Uno que seguía en juego.** San Martín (SJ) vs Nueva Chicago, fecha 17 de la
Primera Nacional 2026, que figuraba con `status = suspendido`. Tuvo fecha cuando la
temporada se la dio: hoy está en `data/partidos-2026.csv`, con el 26/08/2026.

Acá había un segundo, y salió: **Platense vs Estudiantes (BA)**, fecha 6 de la
Primera B 2010-11. Estaba porque las dos fuentes lo contaban distinto —la página
1-1 y las otras 0-0—, y sin marcador que verifique el emparejamiento la fecha no
se toma. Lo arbitró el **historial de la propia página**: el artículo se editaba
en vivo, y entre la revisión del 30/08/2010 y la del 31/08 —con el partido jugado
en el medio— los dos clubes suman un partido, un empate y un punto **y los goles
no se mueven**. Era 0-0. El detalle está en `fad/correcciones.py`.

Eran 13 el 24 de agosto de 2026, y las once que salieron ese día no necesitaron ninguna fuente nueva:

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

## Y tres que entraron y salieron

Al sumar la Primera División de 1991 a 1996 —que Wikipedia publica sin día y RSSSF
fecha— cayeron acá tres partidos más, el 29 de agosto de 2026. En dos, RSSSF publica
el marcador de la cancha y la página el que homologó el Tribunal: `Racing 0-1 River`
del Apertura 1991 y `Vélez 1-0 Boca` del Clausura 1993. Arbitrado el marcador, tomaron
la fecha de RSSSF ese mismo día. El tercero, `Gimnasia (LP) 1-1 Boca` del Apertura
1993, tenía dos días candidatos y lo zanjó el diario del día siguiente: Página/12, en
la Hemeroteca Digital de la Biblioteca Nacional. Salió el 9 de septiembre, y desde
entonces acá quedan sólo los seis de Sansinena.

## Cómo se usan

Mismo esquema y mismas columnas que `data/partidos-AAAA.csv`, con `date` vacío.
Un archivo por **temporada**, igual que allá.

```python
import pandas as pd, glob
con_fecha = pd.concat(map(pd.read_csv, sorted(glob.glob("data/partidos-*.csv"))))
sin_fecha = pd.concat(map(pd.read_csv, sorted(glob.glob("data/sin-fecha/*.csv"))))
```

Las seis de hoy sirven para una sola cosa: que la tabla de posiciones cierre. Sin
ellas Sansinena figura con 12 partidos y 15 goles en contra; con ellas, con los 18 y
los 21 que publica la tabla del Federal A 2024. No sirven para nada que cuente lo que
pasó en una cancha —goles, rachas, historial entre dos clubes—, porque esos 1-0 no
los hizo nadie, ni para nada que necesite ordenar por día o medir descanso entre
partidos.

## Cómo llega una fila acá

Ya no hace falta marcar nada en el catálogo. **El reparto es por fila**: la que
tiene fecha va a `data/`, la que no, viene acá. Antes se decidía por torneo, y esa
regla tenía las dos mitades mal — un torneo marcado iba entero a esta carpeta
aunque tuviera fechas, y en cualquier otro las filas sin fecha **se tiraban**, que
es justo lo contrario de lo que dice esta página. Al arreglarlo aparecieron 16
partidos reales que se venían descartando en Primera Nacional 2007, 2023 y 2026,
Federal A 2024 y Primera C 2024.

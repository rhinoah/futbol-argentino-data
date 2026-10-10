# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 47 127 | 6 | 158 | 1075 | 478 |

Medidos el 10 de octubre de 2026.

## 2004–2026 — Cerrado, con fechas por corregir

`41 999` partidos y no falta ninguno. **Ningún partido queda con dos marcadores en disputa,
ninguno con dos días distintos —eran `61`—, ninguna tabla queda sin contrastar contra su
grilla, y las `56` verificaciones a mano fijan el estado que verificaron, así que caducan
solas —ya caducaron cuatro y se fueron—. `251` clubes de `13` temporadas tienen además el
respaldo de una fuente independiente.** De los `173` avisos, **ninguno es grave**; cada
clase tiene su explicación en el archivo que la produce y no se repite acá.

**Pero «adentro» no era «bien fechado».** Un barrido de todo el CSV buscando grupos de
partidos separados del resto por meses encontró `36` filas con la fecha mal y una dudosa.
Están publicadas así hoy; ninguna tiene mal el marcador.

- **`24` partidos de la `Copa de la Liga 2020` están un año antes.** Son los de enero de
  2021 —entre ellos el `Boca 2-2 River` del 2 de enero— y figuran en enero de 2020. Al
  torneo le falta decir que cruza de año (`anio_fin`).
- **`8` partidos de la `Primera C 2019-20` están un año después.** La fecha 1 del Apertura
  se jugó a fines de julio de 2019 y figura en julio de 2020, cuando no había fútbol. El
  corte de año está en agosto y el torneo arrancó el 27 de julio; la Primera División de
  esa misma temporada ya tiene el arreglo (`mes_inicio=7`) y a la C nunca le llegó.
- **`4` fechas que no existen:** un `31 de noviembre` en la Primera B 2014 (`Platense 1-2
  Deportivo Morón`, fecha 19) y tres `31 de junio` en la Primera B 2015 (fecha 21). Falta
  encontrar el día verdadero de cada uno.
- **Una dudosa:** `Acassuso 1-0 Argentino de Quilmes`, Primera B 2019-20, fecha 8 del
  Clausura, fechado el 29 de noviembre de 2020 — ocho meses después de que la pandemia
  cortara ese torneo.
- **El chequeo que tenía que ver los años corridos tiene un punto ciego.**
  `anios_bien_asignados` agrupa por número de jornada, así que cuando la página reusa
  «Fecha 1» para el Apertura y para el Clausura mezcla las dos y no ve nada. Y no hay
  ningún chequeo de que la fecha exista en el calendario.
- **Las temporadas cerradas no se enteran de las correcciones de Wikipedia.** No se
  vuelven a leer —es lo que las protege de una edición mala—, así que tampoco les llegan
  las buenas hasta que alguien corre `--rehacer`. Hoy la única divergencia entre el CSV y
  un reprocesado completo era la del Apertura 2007, que ya se aplicó.

**El `Apertura 2007`, y una corrección a este mismo archivo.** Sus fechas 18 y 19 estaban
cruzadas en el CSV: veinte filas, sólo la jornada. Este archivo lo tuvo anotado desde
septiembre como «una regresión de Wikipedia», y estaba al revés. Aquella lectura miraba
qué día *arranca* cada fecha —y la 19 arranca antes, por dos partidos adelantados al 28 de
noviembre— sin buscar un testigo. RSSSF numera las rondas por su cuenta: su `Round 18` va
del 30/11 al 2/12 y su `Round 19` del 7 al 9/12, y los veinte partidos coinciden con la
página de hoy y ninguno con la versión vieja. La edición del 26/08/2026 corrigió la página.

Ningún partido espera una fecha: los `6` que están sin fecha no se jugaron —son los que el
Federal A 2024 le dio por perdidos a Sansinena—. Y lo único sin arreglo posible no es una
tarea sino una propiedad de la fuente: la foja no puede cruzar el `Argentino A 2004-05`
porque RSSSF no publica ninguna tabla de esa temporada.

**Dos arbitrajes sobre un torneo en curso dejaron una regla.** Un `Marcador` se identifica
por el marcador que la página publicaba, así que cuando la página se corrige deja de
enganchar; eso era grave y tumbó el build el 26/09/2026, justo porque Wikipedia le dio la
razón al arbitraje. Ahora, si la fila ya dice lo que la corrección pedía, se reporta sin
frenar; si cambió a otra cosa, sigue siendo grave. Queda uno vivo: la celda del `Claypole
0-0 Central Córdoba (R)` de la Primera C 2026 lleva más de cuatro meses mal y el dataset
publica el `2-2`.

## 1997–2003 — Cerrado

**2 469 partidos, y salieron casi gratis**

Las páginas `Anexo:Torneo Apertura/Clausura AAAA (Argentina)` traen los resultados completos —`190` por torneo, que es veinte clubes todos contra todos— y el parser ya las leía **sin un solo cambio**. Entraron 13 temporadas, del Apertura 1997 al Clausura 2003, con cero graves.

No queda nada pendiente. El padrón de estos años está completo: los dos nombres que
figuraban como desconocidos no son clubes —`Deportivo Maniyú` es la página escribiendo
mal `Deportivo Mandiyú`, que ya está, y `Gimnasia J)` es markup roto—.

Eran 14 y entraron 13: el Clausura 1997 cae del otro lado de la línea de las fechas y se fue con la capa de abajo.

## 1991–1996 — Cerrada

**Wikipedia pone los partidos, RSSSF pone las fechas**

Esta sección decía «acá se termina Wikipedia» y **estaba equivocada**. Afirmaba que ninguna página de estos años trae sección de resultados, y eso vale para las de temporada pero no para los anexos: el `Anexo:Torneo Apertura 1993` da `190` partidos, 20 clubes con **ninguno desconocido** y 19 fechas de diez exactas. Un todos contra todos perfecto.

Wikipedia publica estos años **sin una sola fecha**, y RSSSF los publica con sus
rondas y sus días. Entraron **los trece torneos de la capa**, del `Clausura 1991` al `Clausura 1997`:
`2 470` partidos, **todos con su fecha**. Cero graves.

La fuente los escribe de tres maneras y las tres están cubiertas: `arg92`–`arg95`
separan con tabs, `arg97` alinea por espacios y abrevia los nombres, y `arg96`
alinea por espacios **y** separa el guion del marcador (`2 - 0`), que fue lo único
que obligó a tocar el lector.

**La capa está cerrada y sin pendientes.**

- **`Huracán Corrientes` ya está en el padrón**, que era el único club de verdad que
  estos años traen y faltaba.
- **Ya no queda ningún partido sin fecha en esta capa.** El último era el
  `Gimnasia (LP) 1-1 Boca` de la fecha 19 del Apertura 1993, y lo zanjó **Página/12 del
  domingo 20 de marzo de 1994**, que lo cuenta jugado el día anterior con los dos
  goleadores, el árbitro y los dos expulsados que coinciden con la ficha. Es la única
  cita del repo que le gana a una base de datos: RSSSF lo fechaba el viernes 18.
- **La página del Clausura 1993 usa dos criterios distintos** para el mismo tipo de
  hecho: publica el marcador del fallo en el `Vélez–Boca` de la fecha 4 y el de la cancha
  en el `Talleres–River` de la fecha 16. El segundo quedó arbitrado por su propia tabla de
  posiciones y por prensa.
- **Los `3` clubes que no cerraban ya cierran**, y los `20` de esa página con ellos.
  Eran dos partidos que Talleres ganó en la cancha y perdió en el escritorio; la
  aritmética de la tabla dijo cuáles y con qué marcador **antes** de mirar la fuente, y
  RSSSF resultó decir exactamente eso.
- **Curiosidad medida, sin efecto sobre el dataset:** a `Rosario Central` le
  descontaron `2` puntos en ese Clausura. RSSSF lo aplica (`19 [-2]`) y `zerozero` no
  (le deja 21). No nos toca porque acá se guardan partidos y no tablas, pero explica
  por qué dos fuentes buenas pueden diferir en una posición sin diferir en un marcador.
- **El `Clausura 1991` entró sin grilla de Wikipedia, y durante un mes sin árbitro.** Sus
  190 partidos son los de RSSSF, y este archivo decía que la tabla de Wikipedia los
  verificaba. Era cierto medido a mano, pero el build no lo hacía: `wikitexto` no seguía
  las redirecciones y devolvía el stub de 83 bytes, así que la tabla nunca llegaba. Desde
  el 9/10/2026 la sigue. Los `20` clubes coinciden en PJ, G-E-P, GF y GC; el build cuenta
  `19` porque la fila de San Lorenzo trae mal la diferencia de gol (13 por 11) y la
  descarta como testigo.
- Fuente candidata para lo que no cubra RSSSF: planillas de la AFA, *Torneos y Certámenes Oficiales 1990-91 … 1994-95*.

El muro se corrió y después se cayó: era «no hay datos», pasó a ser «no hay fechas»,
y lo último que quedaba —el Clausura 1991— resultó que tampoco era un muro. Estaba
publicado y nadie lo había mirado.

## 1985–1990 — Abierta

**Dejó de ser un muro: RSSSF también fecha estos años**

Es cuando el campeonato pasa al calendario europeo, agosto a junio. Wikipedia no trae los
partidos —sólo las tablas—, así que entran por el mismo camino que el Clausura 1991: los
partidos de RSSSF, la tabla de Wikipedia como árbitro.

- **El `Apertura 1990` ya está adentro**: `189` partidos en 19 fechas, todos con su día.
  **18 de 20 clubes cierran al dígito** contra la tabla. Los otros dos son Boca y San
  Lorenzo, y desvían exactamente igual —un partido, un gol en contra y una derrota cada
  uno—, que es la firma del fallo que les dio por perdido el mismo partido a los dos.
- Son `189` y no `190` porque ese partido **no se puede escribir**: una fila del CSV
  afirma un solo resultado y acá hay dos. Es el sexto `Dividido` del repo y el primero que
  no sale de Wikipedia.
- **Las cinco temporadas que faltan tienen la puerta abierta.** `arg86` a `arg90` publican
  encabezados de fecha igual que `arg91`. Falta medir cada una: cuántos partidos trae, si
  el padrón reconoce los nombres y si la tabla de Wikipedia alcanza para verificarlos. No
  comparten formato: `arg87` separa los marcadores con espacios y no trae tabla arriba.
- **El `arg85` es la excepción:** tiene las rondas pero ni un encabezado de fecha, y una
  fila sin día no se escribe. Ése sigue dependiendo de las planillas de la AFA.

## 1967–1984 — El bloque grande

**3 501 partidos que el parser ya lee**

Acá se jugaban **dos torneos por año**: el Metropolitano, con los clubes de AFA, y el Nacional, que sumaba equipos del interior. Por eso el Nacional parsea con zonas *y* eliminación.

- **Campeonato Nacional 1967-1982 — `3 501` partidos con fecha, sin tocar una línea de código.**
- El costo está en el padrón: `544` apariciones de clubes que no conoce —San Lorenzo de Mar del Plata, Atlético Ledesma, Jorge Newbery de Jujuy, Juventud Alianza, Renato Cesarini—. Son 60 a 100 entradas, y `nombres_en_el_padron` es grave, así que van todas antes.
- **Metropolitano** — vive bajo `Campeonato de Primera División AAAA (Argentina)`. 1981 y 1984 parsean (`305` y `342`).
- **Hueco de parser:** 1980, 1982 y 1983 tienen entre 44k y 54k de wikitexto y devuelven `0`.
- **Hueco:** el Nacional de 1983, 1984 y 1985 también da cero.

## 1933–1966 — Sin fuente digital

**Sólo planillas**

Wikipedia no tiene los partidos y no hay otra fuente estructurada identificada. Todo depende de la biblioteca de la AFA.

- **Hueco de la propia biblioteca:** **1964 a 1968** no está digitalizado. Entre las planillas 1955-1963 y las 1969-1973 no hay nada.

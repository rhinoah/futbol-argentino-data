# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 46 331 | 9 | 156 | 1043 | 452 |

## 2004–2026 — Cerrado

`41 559` partidos y no falta ninguno. **Ningún partido queda con dos marcadores en disputa,
ninguno con dos días distintos —eran `61`—, ninguna tabla queda sin contrastar contra su
grilla, y las `60` verificaciones a mano fijan el estado que verificaron, así que caducan
solas. `251` clubes de `13` temporadas tienen además el respaldo de una fuente independiente.** De los `164` avisos, **ninguno es grave**; cada clase tiene su explicación en el
archivo que la produce y no se repite acá.

**No queda nada pendiente en esta capa.** Ningún partido espera una fecha: los `6` que
están sin fecha no se jugaron —son los que el Federal A 2024 le dio por perdidos a
Sansinena—. Lo único que no tiene arreglo posible no es una tarea sino una propiedad de
la fuente: la foja no puede cruzar el `Argentino A 2004-05` porque RSSSF no publica
ninguna tabla de esa temporada, y su archivo son `306` renglones de índice.

## 1997–2003 — Cerrado

**2 469 partidos, y salieron casi gratis**

Las páginas `Anexo:Torneo Apertura/Clausura AAAA (Argentina)` traen los resultados completos —`190` por torneo, que es veinte clubes todos contra todos— y el parser ya las leía **sin un solo cambio**. Entraron 13 temporadas, del Apertura 1997 al Clausura 2003, con cero graves.

No queda nada pendiente. El padrón de estos años está completo: los dos nombres que
figuraban como desconocidos no son clubes —`Deportivo Maniyú` es la página escribiendo
mal `Deportivo Mandiyú`, que ya está, y `Gimnasia J)` es markup roto—.

Eran 14 y entraron 13: el Clausura 1997 cae del otro lado de la línea de las fechas y se fue con la capa de abajo.

## 1991–1996 — Doce de trece

**Wikipedia pone los partidos, RSSSF pone las fechas**

Esta sección decía «acá se termina Wikipedia» y **estaba equivocada**. Afirmaba que ninguna página de estos años trae sección de resultados, y eso vale para las de temporada pero no para los anexos: el `Anexo:Torneo Apertura 1993` da `190` partidos, 20 clubes con **ninguno desconocido** y 19 fechas de diez exactas. Un todos contra todos perfecto.

Wikipedia publica estos años **sin una sola fecha**, y RSSSF los publica con sus
rondas y sus días. Entraron **los doce torneos que la fuente cubre**, del `Apertura 1991`
al `Clausura 1997`: `2 280` partidos, de los que `2 277` quedaron escritos con su
fecha y `3` no. Cero graves.

La fuente los escribe de tres maneras y las tres están cubiertas: `arg92`–`arg95`
separan con tabs, `arg97` alinea por espacios y abrevia los nombres, y `arg96`
alinea por espacios **y** separa el guion del marcador (`2 - 0`), que fue lo único
que obligó a tocar el lector.

**No queda nada por hacer acá salvo el hueco de fuente.**

- **`Huracán Corrientes` ya está en el padrón**, que era el único club de verdad que
  estos años traen y faltaba. El pendiente estaba anotado en la capa de arriba y ahí el
  club no aparece: sólo está en el `Apertura 1996` y en el `Clausura 1997`, las dos de
  esta capa.
- **Tres partidos sin fecha**, de dos clases. Dos terminaron en un escritorio y cada
  fuente publica un marcador distinto —el de la cancha y el del fallo—: `Racing–River`
  (Fecha 3 del Apertura 1991) y `Vélez–Boca` (Fecha 4 del Clausura 1993, donde además
  la página cuelga una nota sobre el fallo que el parser no supo leer). El tercero,
  `Gimnasia (LP)–Boca` (Fecha 19 del Apertura 1993), no es un marcador sino una
  **localía**: las dos fuentes dan la misma ronda y el mismo `1-1` y difieren en quién
  fue local.
- **Hueco:** `Anexo:Torneo Clausura 1991` es un stub de 83 bytes. Ese torneo hay que buscarlo en otro lado.
- Fuente candidata para lo que no cubra RSSSF: planillas de la AFA, *Torneos y Certámenes Oficiales 1990-91 … 1994-95*.

El muro se corrió y después se cayó: era «no hay datos», pasó a ser «no hay fechas»
y ahora las fechas están. Lo único que sobrevive es el stub del Clausura 1991.

## 1985–1990 — Muro

**Mismo muro, misma salida**

Es cuando el campeonato pasa al calendario europeo, agosto a junio, con un solo campeón por temporada. Wikipedia tampoco trae los partidos.

- Planillas AFA *1985-1989* y *Torneos y Certámenes 1990-91*.

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

# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 44 044 | 6 | 149 | 1032 | 450 |

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

- **Sumar Huracán Corrientes al padrón.** Es el único club de verdad que estos años traen y que no está. Los otros dos nombres desconocidos no son clubes: `Deportivo Maniyú` es la página escribiendo mal `Deportivo Mandiyú`, que ya está, y `Gimnasia J)` es markup roto.

Eran 14 y entraron 13: el Clausura 1997 cae del otro lado de la línea de las fechas y se fue con la capa de abajo.

## 1991–1996 — Lo próximo

**Los partidos están; lo que falta es la fecha**

Esta sección decía «acá se termina Wikipedia» y **estaba equivocada**. Afirmaba que ninguna página de estos años trae sección de resultados, y eso vale para las de temporada pero no para los anexos: el `Anexo:Torneo Apertura 1993` da `190` partidos, 20 clubes con **ninguno desconocido** y 19 fechas de diez exactas. Un todos contra todos perfecto.

Son **2 280** partidos que ya parsean, y **2 270** de ellos **no traen una sola fecha**. Una fila sin fecha no se escribe, así que quedan afuera hasta conseguir de dónde fecharlos.

- **RSSSF publica Primera de estos años.** Es el mismo mecanismo que fechó cinco temporadas del Argentino A esta semana, y la fuente ya está acreditada en el repo.
- El **Clausura 1997** entra acá: de sus 190 partidos, 10 traen fecha.
- **Hueco:** `Anexo:Torneo Clausura 1991` es un stub de 83 bytes. Ese torneo hay que buscarlo en otro lado.
- Fuente candidata para lo que no cubra RSSSF: planillas de la AFA, *Torneos y Certámenes Oficiales 1990-91 … 1994-95*.

El muro se corrió: ya no es «no hay datos» sino «no hay fechas», que es un problema con solución conocida.

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

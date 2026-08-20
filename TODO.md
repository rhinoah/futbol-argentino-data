# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 39 890 | 71 | 132 | 761 | 264 |

## 2004–2026 — Cerrado

**Todo lo que Wikipedia da de esta era está adentro**

`39 890` partidos, cero filas sin fecha. Lo único que queda son verificaciones de calidad, no partidos faltantes: `285` avisos abiertos, y todos los que quedan pueden mover un dato.

- **Las 4 tablas que siguen sin cerrar.** Primera C 2011-12 (3) y Primera C 2026 (1). Las de 2011-12 sobreviven una búsqueda *exhaustiva* sobre sus seis cruces con toda combinación de uno, dos y tres arreglos: ninguna cierra. Existe solución matemática sólo si hay errores que se cancelan en clubes que nunca aparecen desviados, lo cual no se decide desde adentro. Y Cañuelas (2026) tiene un *rival ciego*, Central Córdoba (R), no comparable: un partido entre ellos podría explicarlo y no lo vemos. Las cuatro necesitan contrastar la temporada de esos clubes contra una fuente externa.
- **Fechar un desacuerdo.** Ninguno de los testigos actuales puede decir *cuándo* la página cambió de opinión, y ésa es la deuda más cara que queda. La "Evolución de las posiciones" era el camino y no alcanzó: chequear su contenido pide simular la tabla fecha por fecha —puntajes que cambian, byes, zonas, postergados que mueven el corte al calendario— y medido dio 12% de desvíos, que es un modelo incompleto haciendo ruido. Hay que terminar ese modelo, empezando por el corte por fecha de calendario, o cruzar contra una fuente de afuera.
- **Las tres temporadas de RSSSF que faltan.** `2006-07` ya entró: 334 partidos, cero graves, con `source` acreditando a las dos fuentes. Faltan `2007-08` (`arg3-int08`) y `2008-09` (`arg3-int09`), y encontrar la de `2009-10`, que **no** está en `arg3-int10` — da 404 —. El mapa de cada una se arma con la misma técnica de cardinalidad, pero `2007-08` **no** tiene la forma de las otras dos y hay que mirarla antes de forzar nada: sus secciones son `First Phase - Fase Campeonato`, `Group A` — *Group*, no *Zona* — y rondas `Interzonal Group A-B` intercaladas, así que no es un Apertura y un Clausura sobre las mismas zonas. `2008-09` no muestra ningún encabezado reconocible y todavía no sabemos qué forma tiene. Las dos traen además cuatro líneas con el marcador escrito en palabras (`abd` / `awd`), que el lector ya sabe leer desde que se arregló 2006-07.

- **Las cinco fases finales que sólo existen como cuadro.** Son los 37 avisos del árbitro nuevo, y están *bloqueados*, no pendientes. En Primera C 2008-09 y 2011-12 y en Argentino A 2005-06, 2011-12 y 2012-13, la sección de la fase final —«Torneo reducido», «Segunda fase», «Quinta y sexta fase»— contiene el cuadro de llaves y **nada más**: ni tabla de resultados ni plantillas `{{Partido}}`. Y un cuadro no sabe quién fue local, medido: la convención *arriba es local en la ida* acierta 55.6% contra 761 patas donde la grilla sí lo dice, así que escribir esas filas sería inventarle la localía a la mitad. Son ~80 patas y necesitan una fuente de afuera, igual que las 4 tablas que no cierran. Ojo con una trampa: buscarlas por par+marcador da falsos positivos, porque esos clubes también se cruzaron en la liga y los marcadores bajos se repiten.

## 1997–2003 — Lo próximo

**2 478 partidos, y casi gratis**

Las páginas `Anexo:Torneo Apertura/Clausura AAAA (Argentina)` tienen los resultados completos: `190` partidos por torneo. Medido de punta a punta, falta **un solo club** en el padrón.

- Agregar las 14 entradas al catálogo, Apertura y Clausura de 1997 a 2003.
- Sumar **Huracán Corrientes** al padrón.
- **Hueco:** el Clausura 1997 devuelve `9` partidos en vez de 190. Averiguar si la página está incompleta o si el torneo se anota en otro lado.

## 1991–1996 — Muro

Verificado en las trece temporadas de 1991 a 2003: las páginas existen y tienen entre 18k y 36k de wikitexto, pero **ninguna trae una sección de resultados**. Sólo posiciones, promedios y descensos.

De 1997 en adelante zafamos porque los torneos tienen su propia página aparte. De 1996 para atrás, no.

- Fuente candidata: planillas de la AFA, *Torneos y Certámenes Oficiales 1990-91 … 1994-95*.
- **Hueco sin fuente:** **1995-96 y 1996-97** no están en la biblioteca de la AFA, que corta en 1994-95.

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

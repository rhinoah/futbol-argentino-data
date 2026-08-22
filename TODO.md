# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 43 706 | 107 | 149 | 791 | 273 |

## 2004–2026 — Cerrado

**Todo lo que Wikipedia da de esta era está adentro**

`41 237` partidos. Lo único que queda son verificaciones de calidad, no partidos faltantes: del corpus entero quedan `294` avisos abiertos y cero graves, y todos los que quedan pueden mover un dato.

- **Las 4 tablas que siguen sin cerrar.** Primera C 2011-12 (3) y Primera C 2026 (1). Las de 2011-12 sobreviven una búsqueda *exhaustiva* sobre sus seis cruces con toda combinación de uno, dos y tres arreglos: ninguna cierra. Existe solución matemática sólo si hay errores que se cancelan en clubes que nunca aparecen desviados, lo cual no se decide desde adentro. Y Cañuelas (2026) tiene un *rival ciego*, Central Córdoba (R), no comparable: un partido entre ellos podría explicarlo y no lo vemos. Las cuatro necesitan contrastar la temporada de esos clubes contra una fuente externa.
- **Fechar un desacuerdo.** Ninguno de los testigos actuales puede decir *cuándo* la página cambió de opinión, y ésa es la deuda más cara que queda. La "Evolución de las posiciones" era el camino y no alcanzó: chequear su contenido pide simular la tabla fecha por fecha —puntajes que cambian, byes, zonas, postergados que mueven el corte al calendario— y medido dio 12% de desvíos, que es un modelo incompleto haciendo ruido. Hay que terminar ese modelo, empezando por el corte por fecha de calendario, o cruzar contra una fuente de afuera.
- **27 partidos del Argentino A 2012-13 entran sin fecha.** RSSSF no publica esa fase partido a partido, y donde el cruce queda ambiguo el chequeo se niega a fechar en vez de adivinar. Necesitan una fuente de afuera, igual que las 4 tablas que no cierran.

- **El chequeo de la cadena de llaves: quedan 15 páginas sin revisar.** Arrancó el día en `38` avisos de *no se pudo revisar el cuadro de eliminación* y era el bloque más grande; hoy son **15**, más 10 llaves que quedaron *nombradas* en vez de salteadas. `validar._por_ronda` devuelve `None` —y hace bien, no adivina— apenas UNA jornada de eliminación no cae en `parser.RONDAS`, y con eso el cuadro entero se queda sin mirar. Lo que se destrabó, en orden: `Preclasificatorio` y `Ronda previa`, que estaban afuera a propósito pero por una limitación ya levantada (la Copa Argentina 2012-13 se revisa entera, **63 partidos** que nadie miraba); los cuadros de **una sola ronda**, que no tienen cadena y ahora callan en vez de decir que se salteó algo; las **llaves paralelas**, que se reconocen sin leer el título porque ninguna de sus rondas comparte un solo club con otra; y las etiquetas con algo pegado alrededor (`Semifinal 2`, `Revalida - Segunda ronda`), que se pelan sólo si abajo queda una ronda conocida. Eso último destapó un bug que ya estaba y nunca había disparado: `_por_ronda` **ordenaba** por el nombre normalizado pero **agrupaba** por el de la página, así que tomaba las dos semifinales por rondas consecutivas y acusaba al finalista de llegar sin ganar nada. Lo que queda son dos familias que **no** se arreglan con vocabulario:
  - **8 páginas rotulan la pata, no la ronda** — `Partidos de ida` / `Partidos de vuelta` en plural y `Partido de ida` / `Partido de vuelta` en singular. Es la Reválida del Federal A y la familia más grande. Y no alcanza con juntar ida con vuelta: en el Federal A 2024 los 27 «Partidos de ida» abarcan **seis semanas**, o sea que ahí están todas las idas de todas las rondas juntas. La ronda no está en ningún campo; sólo saldría agrupando por fecha, que es exactamente lo que este chequeo tiene prohibido desde que inventó errores en datos perfectos.
  - **7 sueltas** — `Llave 1..6` y `Partido 1/2/3`, que son llaves y no rondas; `Fase final i`/`ii` en la Copa Argentina 2013-14; `Final Reválida` / `Final por la Promoción` en el Argentino A 2004-05; `Tercer ascenso` en el Transición Federal A 2020; y dos páginas con la jornada **vacía**, que es un hueco del dato y no un problema de nombre.
- **Las cuatro fases finales que sólo existen como cuadro.** Eran cinco: el lector de tablas de llaves destrabó entera la del `Argentino A 2012-13`, que hoy no deja ningún aviso y aporta 29 partidos de eliminación. Quedan Primera C 2008-09 y 2011-12 y Argentino A 2005-06 y 2011-12, y están *bloqueadas*, no pendientes: la sección de la fase final —«Torneo reducido», «Segunda fase», «Quinta y sexta fase»— trae el cuadro y nada que diga la localía. Y un cuadro no la sabe, medido: la convención *arriba es local en la ida* acierta 55.6% contra 761 patas donde la grilla sí lo dice, así que escribir esas filas sería inventársela a la mitad. Necesitan una fuente de afuera, igual que las 4 tablas que no cierran. Ojo con una trampa: buscarlas por par+marcador da falsos positivos, porque esos clubes también se cruzaron en la liga y los marcadores bajos se repiten.

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

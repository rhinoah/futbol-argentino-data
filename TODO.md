# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 43 841 | 148 | 149 | 836 | 308 |

## 2004–2026 — Cerrado

**Todo lo que Wikipedia da de esta era está adentro**

`41 372` partidos. Lo único que queda son verificaciones de calidad, no partidos faltantes: del corpus entero quedan `240` avisos abiertos y cero graves.

Dos bloques se cerraron enteros. Los **desacuerdos entre el cuadro y la grilla** eran `56` y son `0`: las cinco fases finales que Wikipedia sólo dibujaba entraron desde RSSSF y ESPN, y los últimos cuatro no eran arbitrajes sino síntomas — a tres les faltaba una pata de la llave que un separador de un espacio se comía en silencio, y el cuarto era un homónimo que zanjó la foja. Y los **27 desvíos de PJ entre la tabla y la grilla** quedaron en `8`: los 19 del Argentino A 2009-10 no eran de nadie — sus 25 clubes juegan 16 de zona y diez juegan 4 más en el interzonal, así que la tabla y la grilla contaban bien, cosas distintas.

- **Los 8 desvíos de PJ que quedan.** Uno por página, y los ocho tienen la misma forma: **dos clubes corridos lo mismo y para el mismo lado**, que es la firma de un partido entre ellos que una parte tiene y la otra no. El aviso ya lo dice y nombra a los dos —`Atlanta y Chacarita Juniors`, `Huracán y San Lorenzo`, `Almagro y Boca Juniors`…—, así que cada uno es una búsqueda acotada: mirar si la grilla trae ese cruce que la tabla no cuenta, o al revés. No necesitan fuente externa; necesitan abrir la página.

- **Las 4 tablas que siguen sin cerrar.** Primera C 2011-12 (3) y Primera C 2026 (1). Las de 2011-12 sobreviven una búsqueda *exhaustiva* sobre sus seis cruces con toda combinación de uno, dos y tres arreglos: ninguna cierra. Existe solución matemática sólo si hay errores que se cancelan en clubes que nunca aparecen desviados, lo cual no se decide desde adentro. Y Cañuelas (2026) tiene un *rival ciego*, Central Córdoba (R), no comparable: un partido entre ellos podría explicarlo y no lo vemos. Las cuatro necesitan contrastar la temporada de esos clubes contra una fuente externa.
- **Fechar un desacuerdo.** Ninguno de los testigos actuales puede decir *cuándo* la página cambió de opinión, y ésa es la deuda más cara que queda. La "Evolución de las posiciones" era el camino y no alcanzó: chequear su contenido pide simular la tabla fecha por fecha —puntajes que cambian, byes, zonas, postergados que mueven el corte al calendario— y medido dio 12% de desvíos, que es un modelo incompleto haciendo ruido. Hay que terminar ese modelo, empezando por el corte por fecha de calendario, o cruzar contra una fuente de afuera.
- **27 partidos del Argentino A 2012-13 entran sin fecha.** RSSSF no publica esa fase partido a partido, y donde el cruce queda ambiguo el chequeo se niega a fechar en vez de adivinar. Necesitan una fuente de afuera, igual que las 4 tablas que no cierran.

- **El chequeo de la cadena de llaves: quedan 4 cuadros sin revisar.** Empezó el día en `38` avisos de *no se pudo revisar el cuadro de eliminación* y era el bloque más grande de la era; hoy son **4**, más 10 llaves *nombradas* como lo que son. Lo que se destrabó, en orden: `Preclasificatorio` y `Ronda previa` (la Copa Argentina 2012-13 se revisa entera, 63 partidos que nadie miraba); los cuadros de **una sola ronda** y las **llaves paralelas**, que no tienen cadena y decían que el chequeo se había salteado; las etiquetas con algo pegado alrededor (`Semifinal 2`, `Revalida - Segunda ronda`) —que destapó un bug latente: `_por_ronda` ordenaba por el nombre normalizado pero agrupaba por el de la página—; `Fase final I` y `II`, que en la Copa Argentina 2013-14 van *antes* de los dieciseisavos; y las tres formas de numerar una ronda (`fase`, `ronda`, `instancia`), que además llenaron el `matchday` de 24 filas del dataset.
  - **La familia grande se resolvió deduciendo la ronda.** 8 páginas rotulan la *pata* —`Partidos de ida` / `Partidos de vuelta`— y nunca dicen qué ronda es: el dato no está en ningún campo. Pero si dos rótulos tienen el **mismo plantel exacto** no son dos rondas, son la misma jugada dos veces, y los cuatro rótulos colapsan en las dos rondas de verdad. El agrupado es estructural y sólo el orden usa la fecha, que es distinto de agrupar por fecha —lo que este módulo tiene prohibido desde que inventó errores en datos perfectos—.
  - **Ojo con la fuerza de ese chequeo.** En esas páginas el grupo de las idas junta varias rondas (los 25 del Federal A 2025 abarcan ocho semanas), así que lo que se verifica es *«el finalista ganó algún partido de la Reválida»*, no *«ganó su semifinal»*. Es más débil que el chequeo ronda por ronda del resto del corpus. No es decorativo —el test le hace perder a un finalista sus dos patas y exige que aparezca acusado—, pero conviene no leerlo como si fuera lo mismo.
  - **Los 4 que quedan no son cadenas y no se pueden probar que no lo sean.** `Llave 1..6` (Primera División 2015) y `Partido 1/2/3` (B Nacional 2014) son llaves, no rondas; `Final Reválida` / `Final por la Promoción` (Argentino A 2004-05); y `Tercer ascenso` (Transición Federal A 2020). Este último marca el límite conceptual del chequeo: un partido de consolación lo juegan los que **perdieron** la ronda anterior, y el modelo «el que juega ganó lo anterior» no lo contempla — meterlo en el vocabulario generaría acusaciones falsas.
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

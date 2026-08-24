# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 43 835 | 148 | 149 | 870 | 335 |

## 2004–2026 — Cerrado

**Todo lo que Wikipedia da de esta era está adentro**

`41 366` partidos. Lo único que queda son verificaciones de calidad, no partidos faltantes: del corpus entero quedan `212` avisos abiertos y cero graves.

Dos bloques se cerraron enteros. Los **desacuerdos entre el cuadro y la grilla** eran `56` y son `0`: las cinco fases finales que Wikipedia sólo dibujaba entraron desde RSSSF y ESPN, y los últimos cuatro no eran arbitrajes sino síntomas — a tres les faltaba una pata de la llave que un separador de un espacio se comía en silencio, y el cuarto era un homónimo que zanjó la foja. Y los **27 desvíos de PJ entre la tabla y la grilla** quedaron en `1`. Diecinueve eran del Argentino A 2009-10 y no eran de nadie —sus 25 clubes juegan 16 de zona y diez juegan 4 más en el interzonal, así que las dos partes contaban bien, cosas distintas—, y siete eran la consecuencia aritmética de un `Dividido` ya declarado: el partido se jugó, el fallo le dio un marcador distinto a cada club y el esquema no puede escribir eso, así que la fila no entra pero la tabla lo cuenta. Ahora se deriva de la declaración en vez de anotarse aparte.

- **La localía importada de 2012-13 no tiene testigo.** El solapamiento con la página es lo que examina a una fuente externa: donde las dos traen el mismo partido, la página dice quién fue local con una columna rotulada. Medido, el `Argentino A 2004-05` coincide en **40 de 45** y el `2011-12` en **6 de 28** — 21%, peor que el 55.6% de la convención que este repo ya rechazó por inventar, así que su importación quedó bloqueada y sus 6 partidos salieron del dataset. Pero el `Argentino A 2012-13` importa 6 partidos con **cero** en común: no reprobó el examen, no se lo pudo tomar. Entran igual y queda dicho. Para cerrarlo hace falta un tercer testigo de esa fase.
- **Los 10 clubes del Argentino A 2008-09 que no cierran contra Wikipedia no son un error nuestro.** Sus partidos no salen de la página sino de RSSSF, y la tabla que la propia RSSSF publica al lado de ellos coincide **exacta** con nuestra suma —PJ, G, E, P, GF, GC— en los **25** clubes de la temporada. La lectura es fiel: lo que hay es un desacuerdo entre fuentes por `8` goles repartidos en unos cinco partidos, y arbitrarlo pide una **tercera fuente**. El aviso ya lo dice así en vez de mandar a releer un partido que no está mal.
- **La foja de la fuente sólo se puede cruzar en 2 de las 4 páginas sin grilla.** El `2008-09` cruza sus tres zonas y el `2007-08` diecisiete clubes; el `2006-07` no publica ninguna tabla rotulada, y el `2009-10` corre **dos fases rotulando las dos `Zone 1`**, así que no se sabe qué tabla cubre qué conjunto de partidos y el cruce se abstiene. Destrabarlo pide atribuirle a cada tabla su fase, que la fuente no rotula.
- **El cruce contra la foja hoy mira 4 páginas y podría mirar muchas más.** Sólo corre donde los partidos *vienen* de RSSSF. Pero RSSSF publica tablas de temporadas que en este repo salen de la grilla de Wikipedia, y ahí la misma comparación sería un testigo nuevo —y gratis— de nuestras lecturas de Wikipedia. Falta el mapa de nombres por temporada, que es lo caro.
- **La única zona despareja que queda la cortó la pandemia.** Eran `15` en 9 páginas y es `1`: la Primera Nacional 2019-20, cuyo último partido es del **16/03/2020** y donde 28 clubes jugaron 21 y cuatro jugaron 20. El torneo terminó sin completar el fixture, así que el aviso dice algo cierto y no se va a cerrar solo. Los otros 14 eran dos bugs: el chequeo agrupaba **por nombre de zona** —y una temporada con fases repite los nombres, así que la «Zona B» de la Primera fase y la de la Reválida caían en la misma bolsa— y no contaba los **partidos divididos**, que se jugaron aunque no tengan fila.
- **Los 29 «entran al cuadro sin venir de la ronda anterior» son ambiguos por naturaleza.** Se midieron dos formas de desambiguarlos y las dos son falsas: *«el que entra es el mejor ubicado, o sea un sembrado»* lo es en 8 de 29 (entra Douglas Haig doceavo de 14), y *«perdió antes en otra llave»* tampoco, porque casi ninguno tiene un partido anterior en la página. La razón de fondo es que no hay de dónde agarrarse: si a la ronda anterior le falta un partido, sus **dos** clubes desaparecen y sólo el ganador reaparece — exactamente lo que se ve cuando el formato siembra a alguien. Separarlos pide saber cuántos clubes entran al cuadro y en qué ronda, que es un dato del reglamento y no de los partidos.
- **El único desvío de PJ que queda es transitorio.** Eran `27`, después `8`, y ahora `1`: `Nueva Chicago` vs `San Martín (SJ)` de la Primera Nacional 2026, **suspendido a los 45' con 1-0 y todavía sin fallo**. La tabla no lo cuenta y nuestra grilla sí, y las dos hacen bien. Se va a cerrar solo cuando el tribunal falle y Wikipedia lo escriba. *Se probó* la regla «un suspendido no cuenta como jugado» y se midió antes de escribirla: hay **76 filas suspendidas** en el corpus y en las **otras 75** la tabla sí las cuenta — ésta es la única que no. Aplicarla rompería 75 para arreglar una.

- **Las 4 tablas que siguen sin cerrar.** Primera C 2011-12 (3) y Primera C 2026 (1). Las de 2011-12 sobreviven una búsqueda *exhaustiva* sobre sus seis cruces con toda combinación de uno, dos y tres arreglos: ninguna cierra. Existe solución matemática sólo si hay errores que se cancelan en clubes que nunca aparecen desviados, lo cual no se decide desde adentro. Y Cañuelas (2026) tiene un *rival ciego*, Central Córdoba (R), no comparable: un partido entre ellos podría explicarlo y no lo vemos. Las cuatro necesitan contrastar la temporada de esos clubes contra una fuente externa.
- **Fechar un desacuerdo.** Ninguno de los testigos actuales puede decir *cuándo* la página cambió de opinión, y ésa es la deuda más cara que queda. La "Evolución de las posiciones" era el camino y no alcanzó: chequear su contenido pide simular la tabla fecha por fecha —puntajes que cambian, byes, zonas, postergados que mueven el corte al calendario— y medido dio 12% de desvíos, que es un modelo incompleto haciendo ruido. Hay que terminar ese modelo, empezando por el corte por fecha de calendario, o cruzar contra una fuente de afuera.
- **8 partidos del Argentino A 2012-13 entran sin fecha.** Eran `27`: los otros 19 se fecharon al enchufar las llaves de RSSSF a esa página. De los que quedan, RSSSF no publica su fase partido a partido, y donde el cruce queda ambiguo el chequeo se niega a fechar en vez de adivinar.

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

# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 44 021 | 29 | 149 | 934 | 380 |

## 2004–2026 — Cerrado

**Todo lo que Wikipedia da de esta era está adentro**

`41 552` partidos. Lo único que queda son verificaciones de calidad, no partidos faltantes: del corpus entero quedan `192` avisos abiertos y cero graves.

Dos bloques se cerraron enteros. Los **desacuerdos entre el cuadro y la grilla** eran `56` y son `0`: las cinco fases finales que Wikipedia sólo dibujaba entraron desde RSSSF y ESPN, y los últimos cuatro no eran arbitrajes sino síntomas — a tres les faltaba una pata de la llave que un separador de un espacio se comía en silencio, y el cuarto era un homónimo que zanjó la foja. Y los **27 desvíos de PJ entre la tabla y la grilla** quedaron en `1`. Diecinueve eran del Argentino A 2009-10 y no eran de nadie —sus 25 clubes juegan 16 de zona y diez juegan 4 más en el interzonal, así que las dos partes contaban bien, cosas distintas—, y siete eran la consecuencia aritmética de un `Dividido` ya declarado: el partido se jugó, el fallo le dio un marcador distinto a cada club y el esquema no puede escribir eso, así que la fila no entra pero la tabla lo cuenta. Ahora se deriva de la declaración en vez de anotarse aparte.

- **El `21%` del Argentino A 2011-12 no era la fuente: era la página.** El solapamiento con la página es lo que examina a una fuente externa, y esa temporada coincidía en **6 de 28**. Resultó que sus cuatro tablas de eliminación tienen **cambiados los rótulos** de dos columnas: lo que llaman `Local - Vuelta` es el local de la ida. La prueba es la temporada siguiente —el `2012-13` usa **el mismo orden de columnas** y el mismo lector, y da `30` identificados con **cero** al revés— más la sede, que el blog de José Carluccio publica partido por partido: las cuatro idas de la Reválida se jugaron en la ciudad del club que la página pone a la izquierda. Se espejaron las **28** filas de esas tablas, que son todas: corregir algunas y dejar otras sería tratar como fila lo que es un encabezado. Espejar no toca el marcador ni el día —RSSSF coincide con nuestra fecha en 18 de 20—; lo que se va son los 22 «desacuerdos de día» que salían de emparejar nuestra ida con su vuelta. Quedan `7` desacuerdos de **marcador** en esa página, que son otra cosa y siguen abiertos. Medido en las demás: el `2004-05` coincide en 40 de 45, el `2010-11` en 6 de 8 —los 2 que faltaban eran un error de la página, ya corregido— y el `2012-13` en 30 de 30.
- **Los 10 clubes del Argentino A 2008-09 quedaron cerrados, y la que estaba sola era la página.** Sus filas no salen de Wikipedia sino de RSSSF, y hay dos tablas que coinciden con nuestra suma: la que la propia RSSSF publica al lado de esos partidos (los **25** clubes, las seis cifras cada uno) y la de la Wikipedia en **inglés** (los 10 discutidos, uno por uno). La española es la única que dice otra cosa, y siempre para arriba. La aritmética además **nombra los cinco partidos en disputa**: los desvíos se emparejan dentro de su zona salvo uno, que cruza —Zone 1 tiene 6 goles a favor contra 5 en contra y Zone 2 tiene 1 en contra con 0 a favor—, y el único interzonal posible es `Cipolletti` vs `Real Arroyo Seco`. Queda anotado con su límite: nuestra suma y la tabla de RSSSF son **un** testigo, no dos, y no se pudo verificar que la página en inglés no derive de RSSSF. Cerrarlo del todo pide una fuente que publique esos cinco partidos uno por uno; se buscó y no la hay.
- **La foja de la fuente sólo se puede cruzar en 2 de las 4 páginas sin grilla.** El `2008-09` cruza sus tres zonas y el `2007-08` diecisiete clubes; el `2006-07` no publica ninguna tabla rotulada, y el `2009-10` corre **dos fases rotulando las dos `Zone 1`**, así que no se sabe qué tabla cubre qué conjunto de partidos y el cruce se abstiene. Destrabarlo pide atribuirle a cada tabla su fase, que la fuente no rotula.
- **El cruce contra la foja hoy mira 4 páginas y podría mirar muchas más.** Sólo corre donde los partidos *vienen* de RSSSF. Pero RSSSF publica tablas de temporadas que en este repo salen de la grilla de Wikipedia, y ahí la misma comparación sería un testigo nuevo —y gratis— de nuestras lecturas de Wikipedia. Falta el mapa de nombres por temporada, que es lo caro.
- **La única zona despareja que queda la cortó la pandemia.** Eran `15` en 9 páginas y es `1`: la Primera Nacional 2019-20, cuyo último partido es del **16/03/2020** y donde 28 clubes jugaron 21 y cuatro jugaron 20. El torneo terminó sin completar el fixture, así que el aviso dice algo cierto y no se va a cerrar solo. Los otros 14 eran dos bugs: el chequeo agrupaba **por nombre de zona** —y una temporada con fases repite los nombres, así que la «Zona B» de la Primera fase y la de la Reválida caían en la misma bolsa— y no contaba los **partidos divididos**, que se jugaron aunque no tengan fila.
- **Los 29 «entran al cuadro sin venir de la ronda anterior» son ambiguos por naturaleza.** Se midieron dos formas de desambiguarlos y las dos son falsas: *«el que entra es el mejor ubicado, o sea un sembrado»* lo es en 8 de 29 (entra Douglas Haig doceavo de 14), y *«perdió antes en otra llave»* tampoco, porque casi ninguno tiene un partido anterior en la página. La razón de fondo es que no hay de dónde agarrarse: si a la ronda anterior le falta un partido, sus **dos** clubes desaparecen y sólo el ganador reaparece — exactamente lo que se ve cuando el formato siembra a alguien. Separarlos pide saber cuántos clubes entran al cuadro y en qué ronda, que es un dato del reglamento y no de los partidos.
- **El partido del Argentino A 2009-10 que se pierde ya no es un pendiente: se fue a buscar y no vuelve.** `Juventud Antoniana` vs `Gimnasia y Esgrima (CdU)`, fecha 5 del Grupo B del Clausura, **abandonado 1-1 a los 68'**. La pregunta era si alguna vez se jugó lo que faltaba. El blog del propio club lo cuenta el mismo día —*«El Santo cerró su participación con un pálido empate 1a1 […] El cotejo se suspendió a los 23 del Segundo tiempo por invación de campo»*— y no hay mención de reanudación en ningún lado; la tabla final de RSSSF lo confirma dándole `3` PJ a esos dos clubes y `4` a los otros tres. La fila no entra porque **no hay resultado que escribir**: el 1-1 es el marcador al momento del abandono, no uno final, y escribirlo sería afirmar lo que ninguna fuente afirma. Queda documentado en `fad/rsssf.py`, al lado del aviso que lo dice.
- **Cuando dos fuentes dan días distintos, no se sabe cuál tiene razón.** Son `60` partidos en diez páginas y hasta ahora eran invisibles: el completador salteaba en silencio las filas que ya tenían fecha, así que **el árbitro era el orden** en que corrían las fuentes. Se vio al enchufar RSSSF a temporadas que ya fechaba ESPN — 23 filas cambiaron de día, una de ellas por **dieciséis**: `Excursionistas` vs `Argentino de Merlo` de la fecha 3 del Primera C 2008-09, que RSSSF pone el 18/08 con su propio encabezado de día y ESPN el 03/09. Ahora se conserva la primera y se avisa, que es lo honesto mientras no haya con qué decidir. Cerrarlo pide una tercera fuente, o una regla de precedencia que hoy no está medida.
- **El único desvío de PJ que queda es transitorio.** Eran `27`, después `8`, y ahora `1`: `Nueva Chicago` vs `San Martín (SJ)` de la Primera Nacional 2026, **suspendido a los 45' con 1-0 y todavía sin fallo**. La tabla no lo cuenta y nuestra grilla sí, y las dos hacen bien. Se va a cerrar solo cuando el tribunal falle y Wikipedia lo escriba. *Se probó* la regla «un suspendido no cuenta como jugado» y se midió antes de escribirla: hay **76 filas suspendidas** en el corpus y en las **otras 75** la tabla sí las cuenta — ésta es la única que no. Aplicarla rompería 75 para arreglar una.

- **La tabla que sigue sin cerrar es una, y es de la temporada en curso.** Cañuelas, Primera C 2026. Tiene un *rival ciego* —Central Córdoba (R), no comparable—: un partido entre ellos podría explicarlo y no lo vemos. Las tres de la **Primera C 2011-12** se cerraron y el dataset no cambió, porque no había nada que corregir: la que está mal es la tabla de la página. Lo dicen los propios desvíos —Sacachispas desvía `-1` a favor con `0` en contra, y un marcador mal leído mueve a dos clubes con deltas espejados, así que no hay partido que lo explique— y lo confirma el blog de José Carluccio, cuyos 380 partidos parseados dan exactamente nuestra suma. La Wikipedia en inglés no es un segundo testigo: copia las mismas cifras erradas. Queda declarado en `fad/correcciones.py`.
- **Fechar un desacuerdo.** Ninguno de los testigos actuales puede decir *cuándo* la página cambió de opinión, y ésa es la deuda más cara que queda. La "Evolución de las posiciones" era el camino y no alcanzó: chequear su contenido pide simular la tabla fecha por fecha —puntajes que cambian, byes, zonas, postergados que mueven el corte al calendario— y medido dio 12% de desvíos, que es un modelo incompleto haciendo ruido. Hay que terminar ese modelo, empezando por el corte por fecha de calendario, o cruzar contra una fuente de afuera.
- **Quedan 29 partidos sin fecha, y 21 son de una sola temporada.** Eran `148`, y casi nada de lo que se cerró necesitó una fuente nueva: estaba en fuentes que el repo ya bajaba y no leía bien —RSSSF sin encabezado de zona, las divisiones que comparten archivo desde 2010-11, un título que no era título de nada, «repetido» incluyendo al partido publicado sin día, la fecha **entre paréntesis** de los archivos de 2007-08, y ESPN sin enchufar en dos temporadas que sí cubre—. Lo que queda: 21 del `Argentino A 2004-05` —las patas que la fuente citada no publica—, **6 que no esperan ninguna fecha porque no se jugaron** (los que el Federal A 2024 le dio por perdidos a Sansinena, hoy con `status = no disputado`), uno con el marcador en disputa y uno de la temporada en curso.

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

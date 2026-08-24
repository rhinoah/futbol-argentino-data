# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 44 027 | 29 | 149 | 939 | 385 |

## 2004–2026 — Cerrado

**Todo lo que Wikipedia da de esta era está adentro.** `41 558` partidos, y no falta
ninguno: lo que queda son verificaciones de calidad.

Del corpus entero salen `187` avisos y **cero graves**, pero ese número por sí solo
engaña:
`94` son **informativos** —el sistema contando lo que hizo: «no se duplicó», «no es un
error por sí mismo», «se corrigió a mano y acá está la evidencia»— y `93` señalan algo
para mirar. Abajo están agrupados por causa, que son muchas menos que 93.

### Lo que falta

- **`60` partidos que dos fuentes fechan distinto**, en 9 páginas. Se conserva el de la
  página y se avisa, que es lo honesto mientras no haya con qué decidir. La más grande
  es 16 días: `Excursionistas` vs `Argentino de Merlo` de la fecha 3 de la Primera C
  2008-09, que RSSSF pone el 18/08 con su propio encabezado y ESPN el 03/09. Cerrarlo
  pide una tercera fuente, o una regla de precedencia que hoy no está medida.
- **`6` partidos que dos fuentes cuentan con otro marcador.** Cuatro en el Argentino A
  2011-12 (las dos patas `Juventud Unida Universitario`–`Juventud Antoniana` y las dos
  `Libertad (S)`–`Central Norte (S)`), uno en la Primera B 2010-11 (`Platense` 1-1 o
  0-0) y uno en la B Nacional 2008-09. Sin verificación no se toma la fecha, que es la
  regla funcionando.
- **`29` partidos sin fecha**, y `6` de ellos no esperan ninguna porque no se jugaron
  —los que el Federal A 2024 le dio por perdidos a Sansinena, hoy con
  `status = no disputado`—. De los 23 que sí esperan, 21 son las patas del `Argentino A
  2004-05` que la fuente citada no publica.
- **`6` tablas que no cierran, y ninguna es un error de lectura.** Son dos familias.
  Tres desvían **un club** y las tres son de la temporada en curso: `San Miguel`
  (Primera Nacional 2026) por un gol, y `Real Pilar` (Primera B 2026) y `Muñiz`
  (Primera C 2026) en G-E-P **con los goles coincidiendo exacto** —la firma de un
  partido que se definió afuera de la cancha, no de un dígito mal leído—. Las otras
  tres son la tabla contradiciéndose **a sí misma** por un gol, sin que ningún club
  desvíe: Torneo Final 2013, Copa de la Liga 2023 y el Clausura de la Primera C 2024.
- **`3` clubes que el cuadro de eliminación nombra y la grilla no hace jugar.**
  `Estudiantes` en la Primera B 2014, `Juventud Unida` en la Copa Argentina 2015-16 y
  `Los Andes` en la Copa Argentina 2022. O al padrón le falta el nombre, o a la página
  le faltan partidos.
- **`1` desvío de PJ, y es transitorio.** `Nueva Chicago` vs `San Martín (SJ)` de la
  Primera Nacional 2026, suspendido a los 45' con 1-0 y todavía sin fallo: la tabla no
  lo cuenta y la grilla sí, y las dos hacen bien. *Se probó* la regla «un suspendido no
  cuenta como jugado» y se midió antes de escribirla: hay `76` filas suspendidas en el
  corpus y en las otras `75` la tabla sí las cuenta. Aplicarla rompería 75 para
  arreglar una.
- **La foja de RSSSF cruza 3 de las 4 páginas sin grilla; falta el `2009-10`.** Y
  tampoco ahí el problema es la fuente: **sí rotula la fase** (`Apertura` / `Clausura`),
  que es justo lo que hay que darle a cada tabla para desambiguar sus dos `Zone 1`, y
  nuestras propias filas ya traen esa fase en `llave`. Falta que `leer_tabla` devuelva
  la fase junto a la zona y que la suma se acote por `(llave, zona)` exacta.
- **Y podría cruzarse en las páginas que SÍ tienen grilla**, que es donde sería un
  testigo nuevo y gratis de nuestras lecturas de Wikipedia. Hoy sólo corre donde los
  partidos *vienen* de RSSSF. Falta el mapa de nombres por temporada, que es lo caro.
- **Fechar un desacuerdo.** Ninguno de los testigos actuales puede decir *cuándo* la
  página cambió de opinión, y ésa es la deuda más cara que queda. La «Evolución de las
  posiciones» era el camino y no alcanzó: chequear su contenido pide simular la tabla
  fecha por fecha —puntajes que cambian, byes, zonas, postergados que mueven el corte al
  calendario— y medido dio 12% de desvíos, que es un modelo incompleto haciendo ruido.
  Hay que terminar ese modelo, empezando por el corte por fecha de calendario, o cruzar
  contra una fuente de afuera.

### Lo que no se cierra con lo que hay

**Esto no es una lista de tareas.** Es lo que se fue a buscar y no está, escrito para
que no se vuelva a buscar. Cada caso tiene su evidencia en el código, en el archivo que
lo produce.

- Los **`31`** avisos de *«entra al cuadro sin venir de la ronda anterior»*, en 22
  páginas, son ambiguos por naturaleza: si a la ronda previa le falta un partido sus
  **dos** clubes desaparecen y sólo el ganador reaparece, que es exactamente lo que se
  ve cuando el formato siembra a alguien. Separarlos pide saber cuántos clubes entran al
  cuadro y en qué ronda —un dato del reglamento, no de los partidos—. Ver
  `fad/validar.py`.
- Los **`4`** cuadros cuya cadena no se puede revisar no son cadenas: `Llave 1..6`
  (Primera División 2015) y `Partido 1/2/3` (B Nacional 2014) son llaves paralelas, y
  `Tercer ascenso` (Transición Federal A 2020) lo juegan los que **perdieron** la ronda
  anterior — meterlo en el vocabulario generaría acusaciones falsas.
- Los **`10`** partidos que quedan afuera del dataset se jugaron, pero cada club terminó
  con un resultado distinto por un fallo y una fila no puede decir eso. La tabla los
  cuenta y la grilla no, y las dos hacen bien.
- La **zona despareja de la Primera Nacional 2019-20** la cortó la pandemia: su último
  partido es del 16/03/2020 y el torneo terminó sin completar el fixture. El aviso dice
  algo cierto y no se va a cerrar.
- Los **10 clubes del Argentino A 2008-09** están declarados con su límite escrito: la
  tabla de la página en español es la única que dice otra cosa, la aritmética nombra los
  cinco partidos en disputa, y cerrarlo del todo pediría una fuente que los publique uno
  por uno — se buscó y no la hay. Ver `_TABLA_2008_09` en `fad/correcciones.py`.

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

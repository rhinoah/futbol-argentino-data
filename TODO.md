# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 50 251 | 6 | 171 | 1630 | 904 |

Medidos el 24 de octubre de 2026. Los mutantes son los cambios que `mutar.py` le hace
al código a propósito para comprobar que algún test los detecta.

Las marcas de cada era: **cerrado** = está en el CSV, aunque le queden cosas por
revisar; **al alcance** = el parser de hoy lo lee y falta cargarlo; **falta el lector** =
la fuente lo publica y hoy no se lee.

## 2004–2026 — Cerrado

`43 103` partidos de los torneos que están en el catálogo. De los `201` avisos del
build —`174` de esta era—, ninguno es grave. Hay `59` verificaciones a mano. `176` clubes
de `9` temporadas tienen el respaldo de una fuente independiente: sus partidos son de
Wikipedia y cierran con la tabla de RSSSF. Otros `75`, del Argentino A 2006-07 a
2009-10, también cierran con la tabla de RSSSF, pero sus partidos salen de ahí mismo:
los respalda la tabla de Wikipedia. Ningún partido espera una fecha: los `6` que están
sin fecha no se jugaron.

- **Antes de donde arranca cada división del ascenso Wikipedia casi no publica
  partidos.** Medida la temporada anterior de cada una, la B Nacional 2006-07 da 7 sin
  fecha, la Primera B 2009-10 y la Primera C 2007-08 dan 4, y el Argentino A 2003-04 da
  195, 8 con fecha. Para ir más atrás hace falta otra fuente.
- **`status`: cuatro filas que ninguna regla arregla.** La página no dice lo que pasó,
  o lo dice con una palabra que en las demás filas significa otra cosa. Desde 2004 hay
  `54` `suspendido`.
  - `Deportivo Riestra 0-1 UAI Urquiza` (Primera B 2015, «Partidos suspendidos debido a
    la muerte del futbolista Cristian Gómez») y `Excursionistas 0-0 Juventud Unida`
    (Primera C 2014, cuya única nota es un enlace rotulado «Suspendido» a una nota de
    Mundo Ascenso del 15/08/2014: «Por falta de escenario, fue suspendido») salen
    `suspendido` y se postergaron antes de empezar. RSSSF los da jugados sin nota el
    10/06/2015 y el 18/09/2014, que es el día de cada fila.
  - `Arsenal 3-0 Newell's Old Boys` (Primera 2015) sale `suspendido` porque el
    suspendido era un jugador. RSSSF: `orgnl 3-0, awd 0-1 May 22, rvk Jul 23`.
  - `San Martín (T) 0-2 Alumni (VM)` (Argentino A 2011-12) sale vacío, y el build lo
    avisa: la única nota es una cita titulada «AFA decide darle por perdido 0-2». El
    blog de José Carluccio lo da «Suspendido a los 40', con el marcador 0-2 [...]. No
    continuó ni se modificó el resultado».

  Las cuatro piden una corrección a mano que toque sólo el `status`; ver el ítem que
  sigue.
- **`status`: al menos `19` filas que RSSSF da sin terminar salen vacías**, porque su
  página no lo dice: `10` de 1991–1997 (de `arg91` a `arg97`) y `9` de 2005–2024.
  - `Sportivo Patria 0-3 Villa Mitre` (`2005-12-11`), `Cipolletti 1-2 Guillermo Brown`
    (`2006-02-05`) y `Gimnasia y Esgrima (CdU) 2-1 Atlético Candelaria` (`2006-02-12`), los
    tres de `arg3-int06`, que el build ya lee;
  - `Deportivo Español 0-0 Sportivo Italiano` (`2011-05-09`);
  - `River Plate 3-1 San Martín (SJ)` (`2013-06-23`, abandonado en el 90+1);
  - `Quilmes 0-1 River` y `Platense 0-3 Almagro`, de 2014;
  - `Alianza (CC) 1-1 General Belgrano (SR)` (`2014-11-08`), que el Boletín 79/14 del
    Tribunal del Interior da por suspendido a los 84' por un corte de luz;
  - `Central Norte (S) 2-0 Sarmiento (LB)` (`2024-07-21`, «abandoned at 2-0 in 90m,
    awarded»).

  El marcador no cambia. No hay cómo arbitrar sólo el `status`: esa rama se sacó a
  propósito, y falta decidir si se vuelve a poner, con un testigo obligatorio. La otra
  salida es cruzar las notas de RSSSF en los torneos que tienen grilla.
- **Una nota que es un plan cuenta como un partido completado.** `_SE_COMPLETO` acepta
  «Se jugará el…» y «Se juega el…», así que una nota que termine en el plan y siga con
  un abandono saldría sin `status` y sin aviso. Hoy hay `4` notas así en el catálogo
  —`3` en futuro y `1` en presente— y ninguna cuenta nada después del plan.
- **`Villa Dálmine 0-0 Ferrocarril Midland` (Primera C 2009-10) figura el día en que se
  terminó.** Está el `2010-03-31`, el día en que RSSSF da jugados los 21 minutos que
  faltaban; empezó el 19 de febrero (`abandoned at 0-0 in 69'`). La nota dice «jugados
  los 21´ dos días después», y no coincide con RSSSF ni en el motivo ni en la demora.
  Un partido completado otro día se fecha por el día en que empezó: falta una fuente del
  día que diga cuál de los dos es.
- **`16` filas de eliminación de `10` páginas salen con `matchday` vacío.** Son `15`
  partidos —`Sarmiento (LB) 0-1 Los Andes`, el tercer ascenso de 2024, está en dos
  páginas—, todos de una plantilla `{{Partido}}` (`7`) o `{{Partidos}}` (`9`) colgada de
  un título que no es un nombre de ronda, como `Desempate del primer puesto`, `Partido por la
  permanencia`, `Desempate del octavo puesto`. Si la plantilla sin ronda tomara la del
  título más cercano que la contiene y no es de relleno (`Resultados`, `Partidos`,
  `Tabla de posiciones`), cambiarían las `15` que había el 16 de octubre y ningún aviso, pero algunos
  rótulos quedan por decidir: la final del tercer ascenso de la Transición 2020 saldría
  `Partido final` en la página de la Primera B, y su copia en la del Federal A dice
  `Tercer ascenso`.
- **`venue` copia el estadio que declara la página, y al menos `18` filas del Federal A
  2014 y 2015 se jugaron en otra cancha** según el blog de José Carluccio y, donde se
  fue a buscar, la crónica del día. Catorce son localías de Unión Aconquija, que figuran
  en «Municipal de Aconquija» y fueron en Andalgalá; las otras cuatro son de 2015. RSSSF
  acompaña a la página cancha por cancha, así que para este campo no es testigo.
  `correcciones.Cancha` acepta como testigo sólo a la misma página: falta decidir si una
  crónica del día alcanza. En el Federal A 2016 y 2016-17 la página ya pone Andalgalá en
  `11` de las `23` localías de Unión Aconquija; las otras `12` no se revisaron.
- **Dos marcadores del Federal A 2015 tienen un testigo en contra:** `Deportivo Madryn
  2-1 Cipolletti` (el blog de Carluccio da 2-0) y `Sportivo Patria 2-0 Andino` (da 2-1 y
  nombra al goleador). La página y RSSSF coinciden entre sí. Falta una crónica.
- **`rsssf._por_el_padron('Mitre (Salta)')` devuelve `Mitre (SdE)`:** `Mitre` a secas
  es alias y el padrón no tiene otro Mitre que se lo dispute. Ninguna página del
  catálogo pasa por ahí —el de Salta juega rondas de la Copa Argentina que no se leen—,
  pero `arg2013.txt` lo trae.
- **Las dos páginas del Federal A enlazan a Juventud Unida de Gualeguaychú por un título
  que es redirección** (`Club Social y Deportivo Juventud Unida`). Hoy resuelve por el
  nombre. Agregar la clave a `ARTICULOS` puede dejar huérfano el `Homonimo` de la Copa
  Argentina 2015-16: falta medirlo.
- **Dos localías del Reducido de la Primera C 2011-12 no tienen testigo fuera del
  blog:** las de la semifinal `Ferrocarril Midland – Dock Sud`. Las otras doce patas
  tienen una programación o una previa de esos días que nombra al local; a estas dos
  las sostiene la regla del torneo —el mejor ubicado juega la vuelta en su cancha— y el
  build lo avisa en cada `--rehacer`. Falta una crónica.
- **El cruce de la grilla contra el cuadro calla cuando las dos patas de una llave
  tienen el mismo par de números.** `posiciones.marcadores_del_cuadro` pregunta si la
  grilla tiene algún partido entre los dos clubes con el marcador que el cuadro publica,
  sin mirar cuál pata es: en una llave que sale 1-0 y 0-1, romper una no lo hace hablar.
  Las llaves cuyas dos patas dan el mismo resultado para cada club son `20` en toda la
  caché, `16` de esta era. Las 2 del Reducido de la Primera C 2011-12 ya se comparan pata
  por pata, porque son llaves citadas. Quedan `14` (`28` partidos), y en 3 de ellas son
  dos empates iguales. Falta en las que salen de RSSSF y en las de la página.
- **El blog de José Carluccio no publica condiciones de uso.** `90` filas lo nombran: en
  `76` puso el día y en las `14` del Reducido de la Primera C 2011-12, el día y la
  localía. No prohíbe nada, pero tampoco autoriza por escrito.
- **ESPN sigue nombrada como testigo en `36` correcciones a mano**, en `31` renglones de
  `fad/correcciones.py`: `24` `Dia`, `10` `Marcador`, un `Dividido` y un `Revisado`. `18`
  de las `Dia` lo heredan del texto compartido sobre el blog de José Carluccio, que
  arbitra entre RSSSF y ESPN. En al menos dos marcadores es el primer testigo nombrado:
  `Platense 1-0 Belgrano` (2019) y `Gimnasia y Esgrima (J) 0-2 Estudiantes` (2008).
  Ninguna fila sale de ahí ni la nombra en `source`. Falta decidir si se buscan otros
  testigos.
- **`fuente_fecha` guarda dos créditos distintos en un campo:** de dónde sale la fila y
  quién le puso el día. Tres lugares lo escriben y sólo uno los distingue.
  `corregir_fechas` —una `Dia`— lo reemplaza entero, y el completador de worldfootball
  lo borra junto con la fecha cuando cae fuera de la temporada: en las `3 945` filas que
  salen de RSSSF se llevarían el crédito del partido. Hoy no pasa en ninguna. Y
  `fechas.completar` suma el que la fila ya traía aunque no haya puesto nada, si un
  lector devuelve un partido sin día: hoy son `0`. Arreglarlo pide un campo aparte.
- **Los nombres de los autores de RSSSF se cotejan a mano.** `tests/test_licencia.py`
  exige que cada archivo que se usa tenga su renglón en `LICENSE-DATOS.md`, pero no
  puede mirar que el nombre sea el del pie: los archivos no se versionan, y tres
  —`arg2015`, `arg2015a` y `arg2020`— ni siquiera están en la caché. En los otros `25`,
  el nombre coincide con el pie del archivo en la caché.
- **El lector de RSSSF no espera entre un pedido y el siguiente.** Con la caché no se
  nota; un `--rehacer` sin caché le pide 24 archivos seguidos a RSSSF.
- **No hay chequeo de que una fecha exista en el calendario**, y falta decidir cómo
  falla. `a_iso` arma `2014-11-31` sin validarlo. Si es grave, un día mal tipeado en una
  página en curso frena la actualización de todas hasta que alguien cargue la corrección;
  si no lo es, la fila sale publicada con una fecha que no existe.
- **Un partido escrito dos veces se reconoce sólo por `(date, home_team, away_team)`.**
  Si las dos páginas lo publicaran con la localía dada vuelta o en días distintos,
  `dataset.reconciliar_copias` no vería que es el mismo, y las dos copias podrían decir
  cosas distintas sin aviso. Hoy no pasa en ninguno de los `15`: con la localía dada
  vuelta el mismo día hay `0`, y con el mismo cruce y el mismo marcador a 1–3 días, `0`.
- **`20` horas no tienen la forma `HH:MM`** (`11.00`, `15::00`, `9:00`): `14` son de
  2024, `2` de 2020, `2` de 2015, una de 2011 y una de 2003.
- **`venue` es la cancha del programado aunque la nota diga otra.** En `11` filas la
  oración que da el día también nombra la cancha en que se jugó —`Racing Club 0-1 San
  Lorenzo`, Apertura 2006: «se jugó el 21 de febrero de 2007 en el Estadio Presidente
  Perón», y figura en `Ciudad de La Plata`; `Deportivo Español 1-0 Excursionistas`,
  Primera C 2021: «Se jugó en el estadio Enrique Sexto», y figura en `Nueva España`—.
  Leerla de esa oración, como el día y la hora, es otra regla y pide su propia medición.
- **Los `5` `no disputado` que salen de una nota publican la hora y la cancha del
  programado**, de 2013 a 2025. El día es el del programado, como el `Instituto 0-1 San
  Lorenzo` de la 1987-88, que no tiene ni hora ni cancha; las de estos cinco son las de un
  partido que no se jugó. Falta decidir si se vacían.
- **Dos dudas que piden una fuente de afuera,** las dos de `{{Partido}}`:
  - la hora de `Fénix 1-1 Deportivo Español`, ida de la final de la Primera C 2012-13: la
    plantilla dice `15:30` y la AFA, `15:00`. En esa programación otras dos horas difieren
    en cinco minutos: la ida de `Brown de Adrogué – Almagro` y `Deportivo Español –
    Sacachispas`.
  - quién fue local en `Central Córdoba (R) 0-0 Cañuelas`, cuartos de la Primera C 2017-18:
    la plantilla pone local a Central Córdoba en la cancha de Cañuelas.
- **Falta la fase final del Argentino A 2006-07 a 2009-10: entre `55` y `65` partidos.**
  Las cuatro páginas son `sin_grilla`: sus `1 573` filas salen de RSSSF y son todas de
  zonas. `build.procesar` llama a `rsssf.leer_llaves` sólo en la rama con grilla, y sobre
  `arg3-int07` a `arg3-int2010` esa función ya da `53` partidos con día. Faltan 7 a 9 por
  nombres que el mapa no traduce, y nadie lee las rondas finales por grupos de 2008-09 y
  2009-10. Las páginas traen además `14` plantillas que arrancan `{{Partidos|`, con el `|`
  en el renglón del nombre: `_ARRANQUE_PARTIDO` no ve ese arranque, y las páginas sin
  grilla no pasan por el lector de plantillas. Son `12` partidos por el ascenso; los otros
  `2` (`Ramón Santamarina – CAI`) ya entran por la B Nacional 2009-10. La final de 2006-07
  difiere en el día: 5 de julio en la plantilla, 8 en `arg3-int07`. Falta decidir si una
  página `sin_grilla` puede traer también sus llaves de RSSSF, como el 2005-06.
- **La promoción `Luján – Argentino de Quilmes` de 2012 tiene los dos días en duda.** El
  CSV pone la ida el `2012-06-26` y la vuelta el `2012-07-01`; la previa de Infobae del
  sábado 30 de junio dice que la ida fue «el miércoles último» (27) y que la vuelta se
  jugaba ese sábado. RSSSF no la trae. Falta una segunda fuente.
- **Una corrección a mano que hay que sacar a tiempo:** Wikipedia sigue mostrando
  `Claypole 0-0 Central Córdoba (R)` (Primera C 2026) y el dataset publica el `2-2`.
  Cuando la página lo corrija el build va a avisar, y ahí se saca la entrada de
  `fad/correcciones.py` y su renglón de `tests/huellas_correcciones.txt`.
- **El `Argentino A 2004-05` no se puede cruzar contra la tabla de posiciones que
  publica RSSSF.** Son tres cosas:
  - `leer_tabla` no lee las 12 tablas de zona de `arg3-int05` por tres trabas a la vez:
    las filas van sin punto tras el puesto, el mapa del torneo no tiene claves de zona y
    ningún rótulo abre la tabla.
  - Aun leídas no cierran: el CSV tiene `20` de los `200` partidos de zonas, y a cada club
    de la Zona Norte del Apertura le faltan sus 2 interzonales. Esos 10 están en el blog
    que ya fecha esas filas, y con ellos cierran 4 de 5 clubes. Hasta hoy de ahí sale la
    fecha y nada más: falta decidir si también puede sumar partidos.
  - El cruce no va a cerrar entero: la tabla de esa zona en Wikipedia está rota —21 o 22
    PJ por club en una fase de 10—, y las de RSSSF no cierran consigo mismas (en el
    Clausura, 74 ganados contra 75 perdidos).
- **`anios_bien_asignados` tiene tres comparaciones medidas y sin poner.** Es el chequeo
  que frena el build cuando una jornada cae medio año antes que la anterior. Falta
  decidir si se agregan:
  - **Entre los grupos de una misma sección.** Es la única que vería un grupo entero con
    el año corrido, como el `Interzonal` de una sola fecha de la Copa de la Liga 2022,
    2023 y 2024 (`42` partidos). Medida: 0 avisos de más en el catálogo, en `659` páginas
    de afuera y en `52 997` revisiones. En contra: en el peor caso medido queda a `13`
    días del umbral (`147` contra `160`), y sería un grave también en un torneo en curso.
  - **Hacia adelante.** Hoy sólo se mira lo que cae antes: un tramo o una llave de una
    sola ronda (`55` llaves, `125` partidos) que se van un año para adelante no se ven. La
    comparación simétrica —más de 300 días después del tramo anterior— dio 0 avisos sobre
    el dataset sano.
  - **Contra la fecha de inicio que trae la ficha de cada página.** «Ninguna fila más de
    30 días antes» dio 0 avisos en las `67` páginas que escriben el año.

  Aparte quedan `8` torneos donde el año corrido no lo frena nadie, ni el chequeo ni
  `tests/test_torneos.py`: las Copa Argentina 2012-13 a 2018-19 (`7`), que se pueden
  correr adentro de los dos años de su título, y el Clausura 1991, cuyo título es una
  redirección y lo que se mira es el alias.
- **Cuatro formas de `_HABLA_DE_FALLO` no tienen mutante:** `suspendid`, `otorgandole`,
  `inclusion indebida` y `mala inclusion`. El clasificador también las lee, así que una
  nota que las dice ya sale con `status` y el detector no decide nada con ellas: sacarlas
  no cambia ninguna salida. Siguen ahí como red por si el clasificador deja de leerlas.
- **Cuatro renglones que repiten el texto de uno mutado no los cuida ningún test.** Son
  el otro sitio de anclas que estaban repetidas en `mutar.py`, y el mismo cambio puesto
  ahí sobrevive: el corte del bloque en `_alcance_de_cada_tabla` y la firma del desvío
  de goles en `clubes_desviados` (`fad/posiciones.py`), el `len(candidatos) != 1` de
  las `CANCHAS` en `correcciones.aplicar` y el canonizar de `corregida` en `build.py`.
  Otros tres —la nota al pie en `_por_wikitabla` y la página de las `CANCHAS` y de los
  `REEMPLAZOS`— mueren con la suite de hoy.

## 1997–2003 — Cerrado

`2 469` partidos de 13 torneos, del Apertura 1997 al Apertura 2003, todos de Wikipedia y
con cero graves. Falta uno a propósito: el `San Lorenzo – Huracán` del Apertura 1997, que
perdieron los dos y una fila no puede escribir.

- **Dos fechas sospechosas:**
  - `Racing 2-1 Gimnasia (LP)` del `1999-05-24`, con Gimnasia jugando el clásico el 23.
    La página lo anota postergado y RSSSF lo fecha igual. Falta prensa del día: Página/12
    de esos años está en la Hemeroteca Digital. El build lo avisa en cada corrida.
  - `River Plate 3-1 Racing Club`, Fecha 16 del Apertura 2003, figura el `2004-06-03`:
    casi seis meses después de terminado el torneo y cinco días después del River–Racing
    del Clausura 2004. La celda dice «3 de junio de 2004», postergado por la Copa
    Sudamericana. Puede ser cierto, pero falta una fuente del día.

## 1991–1996 — Cerrada

`2 470` partidos de 13 torneos, del Clausura 1991 al Clausura 1997, todos con fecha y con
cero graves. Los partidos son de Wikipedia y las fechas de RSSSF; el Clausura 1991 viene
entero de RSSSF. La capa no tiene hora y casi no tiene cancha (`2 462` filas sin ella):
esas fuentes no las publican.

- **Falta la Liguilla Pre-Libertadores de la 1991-92: `11` partidos**, del 10 de julio al
  2 de agosto de 1992. La página de Wikipedia los publica con día y cancha, el parser ya
  los lee y `arg92` coincide en los 11 en día, local y marcador. Al cargarlos hay que:
  - fecharlos con el año 1992 (con la temporada cruzada, el del 2 de agosto sale en 1991);
  - leer la tanda de `Vélez 1-1 Deportivo Español` (4-2), escrita como las cuatro de
    1985–1990.

  Tampoco están dos desempates sueltos por la Libertadores, `Racing 1-0 Gimnasia` (1996)
  y `Colón 1-0 Independiente` (1997). El parser los lee y `arg96` y `arg97` coinciden, pero
  los fecha un año antes. Falta decidir si entran: es la misma pregunta que las liguillas
  de 1985–1990.
- **Dos fechas sospechosas:** `Belgrano 2-0 Vélez` del `1994-05-05` y `River 4-0 Belgrano`
  del `1994-05-06`. El CSV copia lo que dice RSSSF. Falta prensa del día, o las planillas
  de la AFA (*Torneos y Certámenes Oficiales 1990-91 … 1994-95*), que además darían la
  hora y la cancha. El build avisa el par en cada corrida.

## 1985–1990 — La liga y el Nacional 1985, cerrados

`2 209` partidos, todos con su día: el Nacional 1985 (`160`), el Apertura 1990 (`189`) y
los cinco campeonatos de 1985-86 a 1989-90 (`342`, `380`, `380`, `379` y `379`). Los de la
liga salen de RSSSF y la tabla de Wikipedia arbitra; los del Nacional, de la grilla de su
página. Tres no tienen fila porque el fallo fue contra los dos clubes:
`Boca – San Lorenzo` (Apertura 1990, fecha 18), `Newell's – Rosario Central` (1988-89,
fecha 13) y `Rosario Central – Newell's` (1989-90, fecha 38).

- **`16` partidos del Nacional 1985 difieren de `arg85` en el día o en quién figura de
  local, y no tienen un testigo que desempate.** La página toma fechas y canchas de
  «Fútbol Argentino: Crónicas y Estadísticas», así que esa obra no cuenta. Son:
  - `6` de la vuelta de la primera fase de perdedores: la página y la obra dicen
    miércoles 27 de marzo y RSSSF, que fecha por ronda, domingo 24. Los otros `2` de los
    `8` de esa ronda tienen prensa —La Capital de Mar del Plata y La Capital de
    Rosario—, fueron el 24 y ya están corregidos. Falta decidir si estos `6` pasan al 24
    como ronda, que es lo que se hizo con las llaves del Argentino A 2011-12
    (`_LLAVES_2011_12` en `fad/correcciones.py`): ahí se corrigió el encabezado entero
    y no sólo las filas que tenían testigo;
  - `4` de la cuarta fase de perdedores, 9 o 10 de julio; uno, `Newell's 1-0
    Chacarita`, difiere además en quién fue local;
  - la localía de `Central Norte (S) – Ramón Santamarina` y la de `Gimnasia y Esgrima
    (LP) – Deportivo Español`, las dos en cancha neutral;
  - `4` días de zona en los que la página, la obra y el blog de José Carluccio dicen lo
    mismo y RSSSF da el de la ronda; el blog puede salir de la misma obra.
- **`matchday=Final` no dice de qué cuadro es.** En el Nacional 1985 lo llevan `5` filas
  de tres finales —la de ganadores (`2`), la de perdedores (`1`) y la del campeonato
  (`2`)—, y desde el CSV sólo las separa la fecha. La página las distingue por el título
  de nivel 2 (`== Ronda de ganadores ==`, `== Ronda de perdedores ==`, `== Final ==`), que
  el parser ya lee como `llave` y que no va al CSV. No es sólo de este torneo: en `11`
  páginas hay filas `Final` de más de un cuadro, `33` en total, y en `13` páginas `227`
  filas de eliminación tienen una ronda que se repite en otro cuadro de su página. Hay
  precedente: `157` filas de `7` páginas ya llevan el cuadro adelante («Zona Campeonato
  - Final», de las llaves de RSSSF). Llevarlo también a las plantillas cambia esas `33`
  filas `Final`, o las `227` si va en toda ronda repetida.
- **La cancha de `Círculo Deportivo 2-3 Central Norte (S)`** (Nacional 1985, 24 de
  marzo): la página dice Estadio General San Martín; La Capital de Mar del Plata y
  RSSSF, el Mundialista. `correcciones.Cancha` acepta como testigo sólo a la propia
  página.
- **Faltan las liguillas, los desempates y las finales: `158` partidos**, todos con día
  en RSSSF —`37`, `15`, `34`, `49` y `7` de 1985-86 a 1989-90 y `16` de 1990-91—. 15 de
  los 37 son el Octogonal de la Primera B 1986, que no está en la página de Primera:
  Wikipedia publica `143`, y el parser ya lee `128`. Falta decidir si entran, la misma
  pregunta que los desempates de 1933–1966. Antes de cargarlos hay que arreglar siete
  cosas:
  - la 1986-87 da 0 porque sus celdas empiezan con un espacio; la página trae los 15;
  - `a_iso` no lee `dd/mm/aaaa`: son 34 fechas, de la 1986-87 y la 1987-88;
  - el corte de año fecha mal 18: los 16 de 1990-91 salen en 1990, y la final de la
    liguilla 1988-89, en 1988;
  - se pierden 4 tandas de penales, escritas `0 - 0 <small>(4 - 3) (p)</small>`;
  - la página de la 1989-90 entrega además `37` filas rotas de su grilla parcial, sin
    fecha y con el día en el lugar del local: hay que tomar sólo la eliminación. Hoy no
    toca el dataset porque esa temporada se lee sin grilla;
  - Wikipedia escribe `Concepción Fútbol Club` en 2 partidos de la 1985-86 y el padrón no
    lo reconoce (con el artículo sí resuelve a `Concepción FC`): frenaría el build;
  - `14` de los 34 partidos de la 1987-88 tienen vacía la celda de la fecha: el día hay
    que tomarlo de RSSSF.

  Y las fuentes se contradicen en la semifinal `Boca – Platense` de la liguilla 1988-89
  (los dos partidos, 1-1): Wikipedia pone a Platense de local el 11 de junio y a Boca el
  14, y RSSSF al revés. Falta un tercero. Las fuentes difieren además en el día de
  `Racing 3-1 Argentinos Juniors` (12 de junio de 1988 en Wikipedia, 11 en RSSSF) y de
  `Boca 0-0 Platense`, ida de la final de la Liguilla Clasificación (2 y 3 de julio de
  1988).
- **Cargar la tanda de `Rosario Central 1-1 Instituto`** (1988-89, fecha 12): fue 5-3
  para Central según «Fútbol Argentino: Crónicas y Estadísticas, 1ª División 1988-89»,
  que la da pateador por pateador, y El Gráfico. La otra tanda en que El Gráfico difiere
  del CSV —3-1 en `Central – Talleres`, fecha 3— no se toca: esa obra y En Una Baldosa
  dan el 2-1 que ya está.
- **`Newell's 1-2 Boca` de la 1989-90 (fecha 29) lleva el marcador de la cancha.** Se
  suspendió a los 89 minutos y, según historiadeboca.com.ar, la AFA lo falló 0-2; la tabla
  final de RSSSF lleva el fallo y por eso difiere de sus propios partidos en un gol. Es
  una sola fuente: falta decidir si la fila pasa a 0-2. El mismo sitio difiere en el día
  de otros 3 partidos de Boca de esa temporada.
- **Los goles de las fechas 20 a 38 de la 1988-89 no están cruzados con nada fuera de
  RSSSF.** La tabla final de Wikipedia tiene mal GF/GC de `14` clubes. Falta cruzarlos
  contra «Crónicas y Estadísticas», que trae las 38 fechas partido por partido y de la
  que hasta ahora sólo se cruzaron las tandas —coinciden 130 de las 131 del CSV, y la
  otra es una errata de su encabezado—, y poner en un chequeo las columnas G-E-P y de
  tandas de la tabla de Wikipedia, que coinciden en los 20 clubes.
- **La tabla que verifica la 1985-86, la 1986-87 y la 1989-90 puede no ser
  independiente:** la única fuente que citan esas páginas es el propio archivo de RSSSF.
  Que cierren dice que el archivo se leyó bien, no que una segunda fuente lo confirme.
  Falta una tercera.

## 1967–1984 — Al alcance

**`5 570` partidos con fecha que el parser ya lee**

Acá se jugaban dos torneos por año: el Metropolitano, con los clubes de AFA, y el
Nacional, que sumaba equipos del interior. Nada de esto está cargado.

- **Renovar la cache antes que nada.** Once archivos son la redirección sin seguir, y
  Wikipedia cambió desde agosto: el Nacional 1983 pasó de 30 partidos a 198. Con la cache
  de hoy el mismo parser da `4 564` y no `5 570`.
- **Padrón: faltan `19` clubes, y van antes que todo lo demás:** `nombres_en_el_padron`
  es grave. Son `16` en el Nacional 1967-82 —`478` apariciones, `140` de ellas de `San
  Lorenzo (MdP)`— y 3 más en 1983-84. Hay que decidir además con qué nombre entra
  `Alianza Juventud Pringles`, que pasa sin aviso porque la página lo enlaza a otro club
  (entraría como `Juventud Unida Universitario`), y mirar lo mismo en `Los Andes (SJ)`,
  que enlaza a `Club Atlético Trinidad`, y en `Huracán (IW)`, que aparece 15 de sus 29
  veces sin enlace.
- **Campeonato Nacional 1967-1984: `3 839` con fecha** (`3 515` en las 16 páginas de
  1967-82, `198` en 1983 y `126` en 1984). Con el padrón completo entran todos salvo 1973,
  que pide una corrección a mano: la página escribe `Atlético Tucumán 4-0 San Martín (T)`
  en la Zona B (21/10/1973), donde San Martín no juega; su propia tabla dice que el rival
  fue Gimnasia y Esgrima (J), y RSSSF repite el error. Y entrar no es entrar limpio.
  Quedan avisos que no frenan y hay que mirar: en 1978 la grilla y la tabla no coinciden
  en `Huracán`, `Platense`, `San Martín (SM)` y `San Martín (T)`; en 1982, en `Central
  Norte (S)`; y en 1977, 1979 y 1981 el cuadro de llaves trae una «v» —la regla del gol
  de visitante— que el parser toma por un club.
- **Metropolitano 1980-1984: `1 332` con fecha.** Viven bajo `Campeonato de Primera
  División AAAA (Argentina)`. 1980, 1983 y 1984 dan `342` cada uno; 1981, `305` y uno más
  sin fecha; 1982, sólo el desempate (`1`). Que parsee no es que entre limpio: en 1980 la
  grilla contradice su propia tabla en 9 clubes y hay cuatro nombres rotos; en 1981, uno.
  Contra `arg80` —leído con un lector provisorio— difieren además unos 12 marcadores, y
  los ocho partidos de la Fecha 17 están un mes corridos: 28 de abril en la página, 28 de
  mayo en RSSSF. El chequeo de años no ve un mes; hay que arbitrarlo antes de cargar.
  Los otros años tampoco entran limpios:
  - en 1981, `Argentinos Juniors`, `San Lorenzo` y `Talleres (C)` no cierran con su tabla
    (San Lorenzo tiene `58` goles en contra en la tabla y `48` en la grilla), y
    `Argentinos – Talleres` de la Fecha 28 tiene otro ganador;
  - en 1983, `San Lorenzo 2-0 Ferro` (Fecha 21) es 2-1 en la tabla y en `arg83`;
  - en 1984 no cierran `Argentinos Juniors`, `Chacarita` y `Rosario Central`, y la tabla no
    cierra consigo misma (`789` goles a favor contra `786` en contra).

  En 1980 hay además unos `23` partidos que difieren de `arg80` en uno o dos días.
- **Metropolitano 1982: sale de RSSSF.** La grilla de Wikipedia está armada y vacía,
  marcada «en uso» por un editor (`{{enuso}}`) y sin cambios desde el 18 de septiembre.
  `rsssf.leer` ya lee los `342` de `arg82` con fecha, y los 19 clubes cierran contra la
  tabla de la propia fuente. Mirar la página antes de importar: puede llenarse sola.
  `arg80`, `arg81` y `arg83` escriben las rondas en otro formato y no sirven de árbitro sin
  un lector nuevo.
- **Metropolitano 1967-1979: `399` con fecha.** Viven bajo `Campeonato Metropolitano AAAA
  (Argentina)`. 1973 entra entero (`272`), 1976 por la tercera parte (`121` de 353) y 1979
  sólo con semifinales y final (`6`); 1973 tiene dos avisos que no frenan (Boca y
  Estudiantes, un gol de diferencia con la tabla) y 1976 uno (`Quilmes 4-1 River` marcado
  como empate). Lo demás:
  - 1967, 1970 y 1978 (en viñetas) y 1977 (en renglones sueltos, por la mitad) tienen
    `1 215` resultados en lista, con el día arriba, que el parser no lee: es el mismo
    lector que falta para 1933–1966.
  - 1969 trae `242` partidos sin fecha: la grilla no tiene esa columna.
  - Wikipedia no publica los partidos de la liga de 1968, 1971, 1972, 1974 y 1975, ni la
    ronda de clasificación de 1979; de 1976 faltan `232` de `353` (la segunda rueda y la
    serie por el descenso).
  - `14` partidos de semifinales, finales y desempates están en tablas de filas
    indentadas que el parser saltea.

## 1933–1966 — Falta el lector

**Hay fuente: RSSSF publica las 34 temporadas**

Por ronda y con día: `8 903` partidos de liga, todos presentes, `8 881` con marcador y
todos con día salvo 10. Wikipedia tiene resultados en 17 de las 34 páginas y tabla final
en las 34: sirve de testigo.

- **Extender el lector de RSSSF.** Hoy lee tal cual una sola de las 34 temporadas
  (`arg65`). Le faltan el marcador escrito `N:N` (26 archivos), cuatro formas de
  encabezado de ronda, tres de día, el recorte de cada sección y un mapa de nombres por
  temporada. 1936 son tres archivos: `arg36`, `arg-hon36` y `arg-oro36`. Y hay dos rarezas
  que tiene que contemplar: `arg55` trae un partido dos veces en la ronda 27 (abandonado y
  adjudicado), y `arg53` escribe una ronda postergada como texto.
- **`22` partidos sin marcador numérico.** `21` son adjudicados sin goles (12 de 1940) y
  no tienen marcador que escribir: falta decidir cómo van. Wikipedia y RSSSF coinciden en
  cuáles son: `Lanús – Banfield`, fecha 5 de 1940, que Wikipedia daba `0 - 5`, figura
  adjudicado desde una edición del 12 de octubre de 2026. El otro es un `0 6` mal tipeado
  en `arg66`.
- **Los desempates van aparte.** RSSSF trae `19` fuera de la liga (`arg37`, `arg39`,
  `arg49`, `arg50`, `arg51` y `arg58`), que no están en los `8 903`; Wikipedia ya le da 14
  al parser. Falta decidir si entran, igual que las liguillas de 1985–1990.
- **Wikipedia como testigo:** `4 098` líneas de partido en seis formatos, `3 834` con día.
  El parser lee `248` de ellas (las 240 de 1961 y 8 de 1944). Falta el lector de listas,
  y hay `362` filas que sí son tabla y tampoco lee (1940, 1951 y 1960). La sección de 1946
  tiene el formato de RSSSF: ese año no cuenta como testigo independiente. Y la tabla
  final de 1950 no cierra consigo misma.

## Otras divisiones, si se cargan

Hoy ninguna capa las pide. Son notas de páginas que se midieron de paso, para el día que
entren.

- `Torneo Argentino B 2000-01`: tiene rondas regionales con «Fecha 1, Fecha 2» bajo
  secciones llamadas `Primera ronda`, `Segunda ronda` y `Tercera ronda`, y el parser las
  lee como eliminación (`84` partidos). Hay que arreglarlo antes.
- `Copa Entre Ríos 2021-22`: `16` celdas dicen enero de 2021 en una fecha que se jugó en
  2022. El chequeo de años la frena con 8 graves; hay que corregirlas al cargarla.
- `Primera División B 1978`: la Fecha 4 dice «26 de agosto», entre una de febrero y una
  de marzo. Son 9 partidos; el chequeo no los ve —175 días, y es un mes mal, no un año—
  y van a mano.
- `Primera División D 1978`: el desempate por el ascenso dice «6 de enero» sin año. Hay
  que fecharlo en 1979; fechado en 1978, el chequeo lo frena.

## Las planillas de la AFA, de segunda fuente

Lo que pueden dar que hoy no da nadie es la hora, la cancha y un testigo para las fechas
en duda. El 11 de octubre de 2026 el sitio de la biblioteca respondía con un error de
certificado; el 15 anda de nuevo, con HTTPS válido y las páginas en JPG, así que lo que
sigue ya se puede revisar.

- **Volver a mirar qué cubren y cómo están.** Lo anotado es que cubren 1933-1963 y
  1969-1995, en los volúmenes *Torneos y Certámenes Oficiales 1990-91 … 1994-95* y
  *Planillas 1985-1989*, *1979-1984*, *1974-1978*, *1969-1973* y *1955-1963* hacia atrás;
  que se ven en un visor por página (`libros/libro_NN/pages/N.jpg`), sin capa de texto ni
  PDF; y que las de los 80 y 90 están escritas a máquina y las viejas a mano.
- **Si se leen, de las más recientes hacia atrás**, y con el riesgo resuelto primero: un
  OCR no falla, lee mal. Cruzar contra las tablas de posiciones, que están en Wikipedia
  para todos los años.
- Revisar la licencia antes de publicar: los resultados como hecho no son de nadie, las
  imágenes escaneadas sí son de la AFA.

## El mapa

| era | partidos | fuente | estado |
|---|---:|---|---|
| 2004–2026 | 37 908 | Wikipedia sola | cerrado |
| 2004–2026, con segunda fuente | 5 195 | Wikipedia + RSSSF / worldfootball / otras | cerrado |
| 1997–2003 | 2 469 | Wikipedia | cerrado |
| 1991–1996 | 2 470 | Wikipedia (partidos) + RSSSF (fechas) | cerrado |
| 1985–1990 | 2 209 | RSSSF (partidos) + Wikipedia (tabla); el Nacional 1985, Wikipedia | cerrado |
| 1985–1990, liguillas | 158 | Wikipedia + RSSSF | al alcance 94; 34 sin fecha legible; 30 sin lector |
| 1967–1984 | 5 570 | Wikipedia | al alcance, falta padrón |
| 1933–1966 | 8 903 | RSSSF, con Wikipedia de testigo | falta el lector |

Las cinco primeras filas suman los `50 251` del dataset. Las tres últimas suman `14 631`
y son un piso de lo que falta: la fila 1967–1984 cuenta sólo lo que el parser ya lee con
fecha, sin los 342 del Metropolitano 1982 ni los 1 215 resultados en lista.

# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 50 020 | 6 | 170 | 1262 | 588 |

Medidos el 13 de octubre de 2026. Los mutantes son los cambios que `mutar.py` le hace
al código a propósito para comprobar que algún test los detecta.

Las marcas de cada era: **cerrado** = está en el CSV, aunque le queden cosas por
revisar; **al alcance** = el parser de hoy lo lee y falta cargarlo; **falta el lector** =
la fuente lo publica y hoy no se lee.

## 2004–2026 — Cerrado

`43 032` partidos de los torneos que están en el catálogo. De los `174` avisos
del build, ninguno es grave. Hay `59` verificaciones a mano, y `251` clubes de `13`
temporadas tienen el respaldo de una fuente independiente. Ningún partido espera una
fecha: los `6` que están sin fecha no se jugaron.

- **Antes de donde arranca cada división del ascenso Wikipedia casi no publica
  partidos.** Medida la temporada anterior de cada una, la B Nacional 2006-07 da 7 sin
  fecha, la Primera B 2009-10 y la Primera C 2007-08 dan 4, y el Argentino A 2003-04 da
  195, 8 con fecha. Para ir más atrás hace falta otra fuente.
- **`status`: cinco `suspendido` publicados que la nota de su propia página desmiente.**
  - En dos la palabra sale del titular de una cita y la nota dice «Postergado»: `Racing
    Club 1-0 Rosario Central` (Clausura 2002) y `Unión (MdP) 0-0 Alvarado` (Argentino A
    2013-14). RSSSF da los dos jugados, sin nota. El lector ya no lee la dirección de la
    cita; falta el rótulo del enlace y el `cita=`, y no se puede tirar la cita entera:
    en otras dos filas el rótulo es toda la nota y tiene razón.
  - En tres el partido se completó y el lector no lo ve porque el día no viene pegado al
    verbo: `Acassuso 1-0 Estudiantes (BA)` (Primera B 2012-13, «Se completó el miércoles
    27 de marzo»), `Guillermo Brown 4-2 Juventud Unida Universitario` (Argentino A
    2012-13) y `Deportivo Español 1-0 Excursionistas` (Primera C 2021), que además lleva
    el día programado.
  - Sin verificar quedan `San Martín (B) – Midland` (Primera C 2015) y `Excursionistas
    0-0 Juventud Unida` (Primera C 2014).
- **`status`: dos filas con fallo salen vacías y sin aviso.** `Real Arroyo Seco 0-1
  Gimnasia y Esgrima (CdU)` (Argentino A 2004-05; la nota dice «Se le dió por ganado»,
  con tilde) y `San Martín (T) 0-2 Alumni (VM)` (Argentino A 2011-12; la única nota es
  una cita titulada «AFA decide darle por perdido 0-2»). El lector no lee ninguna de las
  dos formas, ni para clasificar ni para avisar.
- **`status`: tres partidos del Federal A 2015 que no empezaron salen `suspendido`:**
  `San Jorge (T) 0-1 Unión Aconquija` (falta de médico), `Independiente (C) 1-0 Alianza
  (CC)` y `Altos Hornos Zapla 1-0 Andino` (no se presentó el visitante). El lector
  escribe `no disputado` sólo cuando la celda del estadio dice «Sin disputar»; cambiar
  la regla toca filas ya publicadas.
- **`status`: al menos `11` filas que RSSSF da sin terminar salen vacías** porque su
  página no lo dice: ocho de 1991–1997, `Quilmes 0-1 River` y `Platense 0-3 Almagro` de
  2014, y `Alianza (CC) 1-1 General Belgrano (SR)` (`2014-11-08`), que el Boletín 79/14
  del Tribunal del Interior da por suspendido a los 84' por un corte de luz, con el
  resultado de la cancha. El marcador no cambia, y no hay cómo arbitrar sólo el
  `status`: esa rama se sacó a propósito. Si se cierra, es cruzando las notas de RSSSF
  en los torneos que tienen grilla.
- **«Se jugará el…» se lee como «se jugó».** `Cañuelas 0-2 Colegiales` y `Ferrocarril
  Midland 0-1 Flandria` (Primera B 2024) terminan su nota en «Se jugará el 2 de
  septiembre» y figuran el `2024-08-31`, que es el día de la suspensión. Una nota que
  termine en el plan y siga con un abandono saldría sin `status` y sin aviso.
- **Tres tandas de penales del Federal A 2014 no están.** La página las publica sólo en
  la tabla «Global» de cada fase y no en la fila de la vuelta: `CAI 4-3 Juventud Unida
  Universitario`, `Unión (VK) 3-4 Gimnasia y Esgrima (M)` y `Talleres (C) 4-3 Mitre
  (SdE)`. RSSSF las confirma. Cargadas a mano, dos de las tres disparan un grave:
  `serie_igualada` no reconoce «Partidos de ida» y «Partidos de vuelta» como una serie.
  Las `146` filas de eliminación del Federal A 2016, 2016-17 y 2017-18 tampoco llevan
  penales: falta medir si es el mismo hueco.
- **`matchday` no dice de qué fase es un partido cuando la página rotula sólo la pata.**
  `358` filas de `11` páginas dicen «Partidos de ida» o «Partidos de vuelta» y nada más:
  la ronda está en el título de la sección y el lector lo pisa con el encabezado de la
  tabla. En el Federal A 2014 eso deja además el cuadro sin revisar —`cadena_de_llaves`
  no puede separar tres fases con el mismo rótulo—; se revisó a mano.
- **`venue` copia el estadio que declara la página, y al menos `18` filas del Federal A
  2014 y 2015 se jugaron en otra cancha** según el blog de José Carluccio y, donde se
  fue a buscar, la crónica del día. Catorce son localías de Unión Aconquija, que figuran
  en «Municipal de Aconquija» y fueron en Andalgalá; las otras cuatro son de 2015. RSSSF
  acompaña a la página cancha por cancha, así que para este campo no es testigo.
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
  Medido en el Reducido de la Primera C 2011-12: avisa en `7` de sus `14` partidos. Las
  llaves citadas a mano ya se comparan pata por pata; falta en las que salen de RSSSF y
  en las de la página.
- **El blog de José Carluccio no publica condiciones de uso.** `90` filas lo nombran: en
  `76` puso el día y en las `14` del Reducido de la Primera C 2011-12, el día y la
  localía. No prohíbe nada, pero tampoco autoriza por escrito.
- **`arg2011` tiene otro encabezado de fecha sin cerrar**, `[Apr 9`, en la sección del
  Argentino B, que hoy no lee ningún torneo.
- **ESPN sigue nombrada como testigo en `31` renglones de `fad/correcciones.py`.**
  Ninguna fila sale de ahí ni la nombra en `source`, pero varios marcadores corregidos a
  mano citan su ficha entre otros testigos.
- **`source` nombra a RSSSF por el sitio y no por el archivo.** `8 116` filas llevan
  `https://www.rsssf.org/` y `6` la URL de un archivo. El pie de cada archivo pide
  reconocer a su autor y la fila no dice de cuál salió: hoy lo resuelve la tabla de
  `LICENSE-DATOS.md`, porque cada torneo usa un solo archivo. Falta decidir si
  `rsssf.CREDITO` pasa a ser la URL del archivo; reescribe esas filas, de `22` CSV.
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
  —`arg2015`, `arg2015a` y `arg2020`— ni siquiera están en la caché.
- **El lector de RSSSF no espera entre un pedido y el siguiente.** Con la caché no se
  nota; un `--rehacer` sin caché le pide 24 archivos seguidos a RSSSF.
- **La descripción del repositorio en GitHub quedó vieja:** dice 22.270 partidos desde
  2016 y nombra sólo a Wikipedia.
- **No hay chequeo de que una fecha exista en el calendario**, y falta decidir cómo
  falla. `a_iso` arma `2014-11-31` sin validarlo. Si es grave, un día mal tipeado en una
  página en curso frena la actualización de todas hasta que alguien cargue la corrección;
  si no lo es, la fila sale publicada con una fecha que no existe.
- **`15` partidos están escritos dos veces**, una por cada torneo: las promociones entre
  divisiones de 2010-11 y 2011-12 y el tercer ascenso de 2020, 2023 y 2024. Las `50 020`
  filas son `50 005` partidos distintos. `sin_duplicados` mira torneo por torneo: falta
  decidir si es a propósito. Y las dos copias no siempre dicen lo mismo: `San Telmo –
  Deportivo Madryn` del `2021-02-04` es `neutral=false` en su fila de Primera B y `true` en
  la del Federal A.
- **La hora.** El parser saca el día de la nota «se jugó el…» pero la hora la saca de la
  celda, así que unos `190` partidos reprogramados en `64` páginas tienen el día real y la
  hora del programado. Hay además `37` horas que no tienen la forma `HH:MM` (`15:00
  (TV)`, `11.00`, `15::00`), una de ellas de 2003, y las tres definiciones de la Copa de
  la Liga 2020 en San Juan figuran `neutral=false`.
- **La promoción `Luján – Argentino de Quilmes` de 2012 tiene los dos días en duda.** El
  CSV pone la ida el `2012-06-26` y la vuelta el `2012-07-01`; la previa de Infobae del
  sábado 30 de junio dice que la ida fue «el miércoles último» (27) y que la vuelta se
  jugaba ese sábado. RSSSF no la trae. Falta una segunda fuente.
- **Una corrección a mano que hay que sacar a tiempo:** Wikipedia sigue mostrando
  `Claypole 0-0 Central Córdoba (R)` (Primera C 2026) y el dataset publica el `2-2`.
  Cuando la página lo corrija el build va a avisar, y ahí se saca la entrada de
  `fad/correcciones.py`.
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
- **Renovar la cache y correr `--rehacer`.** Las temporadas cerradas no se vuelven a
  leer, así que no les llegan las correcciones buenas de Wikipedia, y la cache de hoy es
  de agosto y septiembre.
- **Comentarios que quedaron viejos en el código:**
  - Tres de `fad/torneos.py`, en el bloque de 1997–2003, dan por afuera la capa 1991–1996
    y al Clausura 1991 por un stub.
  - `fad/citadas.py` dice que quedan 2 filas en `data/sin-fecha/`, y `build.py`, que
    hay un único camino por el que una fila no viene de Wikipedia.
  - Dicen que de la segunda fuente sale sólo la fecha, o que hay un único lugar por el
    que una fila no viene de Wikipedia: `fad/fechas.py` (`Ajeno`),
    `fad/torneos.py` (dos bloques), `fad/rsssf.py` (`a_partidos`),
    `fad/correcciones.py`, `fad/equipos.py` y un docstring de `tests/test_build.py`.
  - El docstring de `build.py` —lo que muestra `--help`— dice que `--sin-cache` «vuelve a
    pedirle todo a Wikipedia»: pide sólo las páginas que parsea.
  - Un docstring de `tests/test_equipos.py` cuenta seis Gimnasia y Esgrima donde hay
    cinco.
  - `fad/equipos.py` dice que los alias con el desambiguador desplegado «son 34
    nombres»: el Federal A 2014 y el 2015 sumaron cinco.
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
- **A siete de los catorce chequeos del validador no los cuida ningún test que pase por
  `revisar`:** `campos_completos`, `penales_solo_en_empates`, `sin_duplicados`,
  `nadie_juega_contra_si_mismo`, `todos_tienen_zona`, `jornadas_sin_huecos` y
  `cadena_de_llaves`. Sacándolos de `CHEQUEOS` la suite pasa igual, porque sus tests los
  llaman a mano. Falta un test por cada uno que pase por el recorrido completo.
- **Falta escribir el chequeo de dataset entero «nadie juega dos partidos distintos en
  días seguidos».** Hoy daría dos casos, los de 1994 y 1999 que están más abajo. Tiene
  que saltear los 15 partidos escritos dos veces.
- **`build.py` le pasa a RSSSF la etiqueta de temporada como año de cierre**
  (`t.anio_fin or t.temporada`, en tres lugares), y tendría que pasarle el año con que se
  fecha. Hoy no produce nada mal porque el test del catálogo ata la etiqueta al título.
- **Un aviso que dice más de lo que hace.** Cuando una segunda fuente trae fechas fuera de
  la temporada, `build` avisa que «se descartan», y vacía sólo las tres primeras.
- **Las correcciones a mano casi no tienen test propio.** Sacar el `Dividido` del
  Federal A 2014 o cualquiera de los tres `Revisado` del 2015, o cambiarles el club o la
  firma, deja la suite verde: lo nota el build con un aviso que no frena, y sólo con
  `--rehacer`. De los `59` `Revisado`, a lo sumo `7` tienen su página y su club nombrados
  juntos en un test. Tampoco se mira el CSV contra el catálogo: borrar una entrada pasa
  los tests y frena al build del día siguiente por la guarda contra achicarse.
- **Los regex del `status` aceptan formas que ningún dato recorre y ningún test fija.**
  De `35` mutantes de ese tipo sobre los cuatro regex, sobreviven `33`.
- **`mutar.py`:**
  - Dos mutantes tienen el mismo texto que otros dos, en `fad/correcciones.py` y en
    `fad/parser.py`; como se reemplaza la primera aparición, el segundo sitio de cada par
    queda sin mutar.
  - Hay `15` mutantes cuya ancla —el texto que `mutar.py` busca para aplicar el cambio—
    aparece más de una vez en su archivo. Además de los dos pares de arriba, otros dos
    caen en una función distinta de la que su descripción nombra.
  - En Windows deja en CRLF los fuentes que muta: los lee y los escribe en modo texto.
  - Un import roto en `tests/conftest.py` sale por un camino que el detector de «no se
    pudo importar» no ve, y lo contaría como muerto. Hoy no se alcanza: no muta `tests/`.

## 1997–2003 — Cerrado

`2 469` partidos de 13 torneos, del Apertura 1997 al Apertura 2003, todos de Wikipedia y
con cero graves. Falta uno a propósito: el `San Lorenzo – Huracán` del Apertura 1997, que
perdieron los dos y una fila no puede escribir.

- **Una fecha sospechosa:** `Racing 2-1 Gimnasia (LP)` del `1999-05-24`, con Gimnasia
  jugando el clásico el 23. La página lo anota postergado y RSSSF lo fecha igual. Falta
  prensa del día: Página/12 de esos años está en la Hemeroteca Digital.

## 1991–1996 — Cerrada

`2 470` partidos de 13 torneos, del Clausura 1991 al Clausura 1997, todos con fecha y con
cero graves. Los partidos son de Wikipedia y las fechas de RSSSF; el Clausura 1991 viene
entero de RSSSF. La capa no tiene hora y casi no tiene cancha (`2 462` filas sin ella):
esas fuentes no las publican.

- **Falta la Liguilla Pre-Libertadores de la 1991-92: `11` partidos**, del 10 de julio al
  2 de agosto de 1992. `arg92` los trae con día y la página de Wikipedia tiene la sección.
  Tampoco están dos desempates sueltos por la Libertadores, de 1996 y 1997, que traen
  `arg96` y `arg97`.
- **Dos fechas sospechosas:** `Belgrano 2-0 Vélez` del `1994-05-05` y `River 4-0 Belgrano`
  del `1994-05-06`. El CSV copia lo que dice RSSSF. Falta prensa del día, o las planillas
  de la AFA (*Torneos y Certámenes Oficiales 1990-91 … 1994-95*), que además darían la
  hora y la cancha.

## 1985–1990 — La liga, cerrada

`2 049` partidos, todos con su día: el Apertura 1990 (`189`) y los cinco campeonatos de
1985-86 a 1989-90 (`342`, `380`, `380`, `379` y `379`). Los partidos salen de RSSSF y la
tabla de Wikipedia arbitra. Tres no tienen fila porque el fallo fue contra los dos clubes:
`Boca – San Lorenzo` (Apertura 1990, fecha 18), `Newell's – Rosario Central` (1988-89,
fecha 13) y `Rosario Central – Newell's` (1989-90, fecha 38).

- **Falta el Nacional 1985: `160` partidos.** La página `Campeonato Nacional 1985
  (Argentina)` ya parsea los 160 con fecha, y para entrar le faltan dos clubes en el
  padrón (`Argentino (F)` y `Juventud Alianza`). El `arg85` de RSSSF trae los mismos 160
  con el día en cada encabezado de ronda (`Round 1.1.1: 17 Feb`), formato que el lector no
  reconoce. Cruzados club por club, `140` son idénticos y `20` difieren: 16 sólo en el día
  —8 de ellos una ronda entera, 24 contra 27 de marzo—, 3 sólo en quién figura de local, 1
  en las dos cosas y ninguno en el marcador. Al cargarlo quedan dos cosas por arbitrar:
  - la tabla de la Zona C cuenta el `Guaraní Antonio Franco 2-2 Talleres (C)` de la fecha
    5 como un 2-0; la grilla y RSSSF dan 2-2;
  - `Independiente 1-0 Boca` figura en RSSSF como abandonado a los 85 minutos y la página
    lo publica sin estado.

  Y el cruce no vale por dos testigos: la página enlaza a `arg85`, y RSSSF fecha por
  ronda —sólo 5 partidos llevan día propio—.
- **Faltan las liguillas, los desempates y las finales: `158` partidos**, todos con día
  en RSSSF —`37`, `15`, `34`, `49` y `7` de 1985-86 a 1989-90 y `16` de 1990-91—. 15 de
  los 37 son el Octogonal de la Primera B 1986, que no está en la página de Primera:
  Wikipedia publica `143`, y el parser ya lee `128`. Antes de cargarlos hay que arreglar
  cinco cosas:
  - la 1986-87 da 0 porque sus celdas empiezan con un espacio; la página trae los 15;
  - `a_iso` no lee `dd/mm/aaaa`: son 34 fechas, de la 1986-87 y la 1987-88;
  - el corte de año fecha mal 18: los 16 de 1990-91 salen en 1990, y la final de la
    liguilla 1988-89, en 1988;
  - se pierden 4 tandas de penales, escritas `0 - 0 <small>(4 - 3) (p)</small>`;
  - la página de la 1989-90 entrega además `37` filas rotas de su grilla parcial, sin
    fecha y con el día en el lugar del local: hay que tomar sólo la eliminación. Hoy no
    toca el dataset porque esa temporada se lee sin grilla.

  Y las fuentes se contradicen en la semifinal `Boca – Platense` de la liguilla 1988-89
  (los dos partidos, 1-1): Wikipedia pone a Platense de local el 11 de junio y a Boca el
  14, y RSSSF al revés. Falta un tercero.
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
- **Padrón: faltan `21` clubes, y van antes que todo lo demás:** `nombres_en_el_padron`
  es grave. Son `17` en el Nacional 1967-82 —`494` apariciones, `140` de ellas de `San
  Lorenzo (MdP)`— y 4 más en 1983-85; los dos que pide el Nacional 1985 están entre estos
  21. Hay que decidir además con qué nombre entra `Alianza Juventud Pringles`, que pasa
  sin aviso porque la página lo enlaza a otro club (entraría como `Juventud Unida
  Universitario`), y mirar lo mismo en `Los Andes (SJ)`, que enlaza a `Club Atlético
  Trinidad`, y en `Huracán (IW)`, que aparece 15 de sus 29 veces sin enlace.
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
- **Metropolitano 1982: sale de RSSSF.** La grilla de Wikipedia está armada y vacía, con
  un editor trabajándola desde septiembre (`{{enuso}}`). `rsssf.leer` ya lee los `342` de
  `arg82` con fecha, y los 19 clubes cierran contra la tabla de la propia fuente. Mirar la
  página antes de importar: puede llenarse sola. `arg80`, `arg81` y `arg83` escriben las
  rondas en otro formato y no sirven de árbitro sin un lector nuevo.
- **Metropolitano 1967-1979: `399` con fecha.** Viven bajo `Campeonato Metropolitano AAAA
  (Argentina)`. 1973 entra entero (`272`), 1976 por la tercera parte (`121` de 353) y 1979
  sólo con semifinales y final (`6`). Lo demás:
  - 1967, 1970 y 1978 (en viñetas) y 1977 (en renglones sueltos, por la mitad) tienen
    `1 215` resultados en lista, con el día arriba, que el parser no lee: es el mismo
    lector que falta para 1933–1966.
  - 1969 trae `242` partidos sin fecha: la grilla no tiene esa columna.
  - 1971, 1972 y 1975 no tienen resultados.
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
  no tienen marcador que escribir: falta decidir cómo van. En uno las fuentes difieren:
  `Lanús – Banfield`, fecha 5 de 1940, es `0 - 5` en Wikipedia y adjudicado en RSSSF. El
  otro es un `0 6` mal tipeado en `arg66`.
- **Los desempates van aparte.** RSSSF trae `19` fuera de la liga (`arg37`, `arg39`,
  `arg49`, `arg50`, `arg51` y `arg58`), que no están en los `8 903`; Wikipedia ya le da 14
  al parser. Falta decidir si entran, igual que las liguillas de 1985–1990.
- **Wikipedia como testigo:** `4 100` líneas de partido en seis formatos, `3 834` con día.
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
en duda. Nada de lo que sigue se pudo verificar el 11 de octubre de 2026: el sitio de la
biblioteca responde con un error de certificado.

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
| 2004–2026 | 37 838 | Wikipedia sola | cerrado |
| 2004–2026, con segunda fuente | 5 194 | Wikipedia + RSSSF / worldfootball / otras | cerrado |
| 1997–2003 | 2 469 | Wikipedia | cerrado |
| 1991–1996 | 2 470 | Wikipedia (partidos) + RSSSF (fechas) | cerrado |
| 1985–1990 | 2 049 | RSSSF (partidos) + Wikipedia (tabla) | cerrado |
| 1985–1990, Nacional 1985 y liguillas | 318 | Wikipedia + RSSSF | al alcance 288; 30 sin lector |
| 1967–1984 | 5 570 | Wikipedia | al alcance, falta padrón |
| 1933–1966 | 8 903 | RSSSF, con Wikipedia de testigo | falta el lector |

Las cinco primeras filas suman los `50 020` del dataset. Las tres últimas suman `14 791`
y son un piso de lo que falta: la fila 1967–1984 cuenta sólo lo que el parser ya lee con
fecha, sin los 342 del Metropolitano 1982 ni los 1 215 resultados en lista.

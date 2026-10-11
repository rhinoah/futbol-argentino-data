# Lo que falta

Excavación hacia 1933, era por era. Acá está **sólo lo pendiente**: lo
terminado se documenta en los mensajes de commit y en los docstrings, que es
donde alguien lo va a buscar. Los números están medidos sobre las páginas
reales, no estimados.

| partidos | sin fecha | torneos | tests | mutantes |
|---|---|---|---|---|
| 48 995 | 6 | 163 | 1196 | 562 |

Medidos el 11 de octubre de 2026. Los mutantes son los cambios que `mutar.py` le hace
al código a propósito para comprobar que algún test los detecta.

Las marcas de cada era: **cerrado** = está en el CSV, aunque le queden cosas por
revisar; **al alcance** = el parser de hoy lo lee y falta cargarlo; **falta el lector** =
la fuente lo publica y hoy no se lee.

## 2004–2026 — Cerrado

`42 007` partidos, y no falta ninguno de los que Wikipedia publica. De los `180` avisos
del build, ninguno es grave. Hay `56` verificaciones a mano, y `251` clubes de `13`
temporadas tienen el respaldo de una fuente independiente. Ningún partido espera una
fecha: los `6` que están sin fecha no se jugaron.

- **No hay chequeo de que una fecha exista en el calendario**, y falta decidir cómo
  falla. `a_iso` arma `2014-11-31` sin validarlo. Si es grave, un día mal tipeado en una
  página en curso frena la actualización de todas hasta que alguien cargue la corrección;
  si no lo es, la fila sale publicada con una fecha que no existe.
- **`15` partidos están escritos dos veces**, una por cada torneo: las promociones entre
  divisiones de 2010-11 y 2011-12 y el tercer ascenso de 2020, 2023 y 2024. Las `48 995`
  filas son `48 980` partidos distintos. `sin_duplicados` mira torneo por torneo y el
  README dice «sin duplicados»: falta decidir si es a propósito y escribirlo.
- **La hora.** El parser saca el día de la nota «se jugó el…» pero la hora la saca de la
  celda, así que unos `190` partidos reprogramados en `63` páginas tienen el día real y la
  hora del programado. Hay además `36` horas que no tienen la forma `HH:MM` (`15:00
  (TV)`, `11.00`, `15::00`), una de ellas de 2003, y las tres definiciones de la Copa de
  la Liga 2020 en San Juan figuran `neutral=false`.
- **La promoción `Luján – Argentino de Quilmes` de 2012 tiene los dos días en duda.** El
  CSV pone la ida el `2012-06-26` y la vuelta el `2012-07-01`; la previa de Infobae del
  sábado 30 de junio dice que la ida fue «el miércoles último» (27) y que la vuelta se
  jugaba ese sábado. RSSSF y ESPN no la traen. Falta una segunda fuente.
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
- **Arreglar la consulta a ESPN.** El feed rechaza con un 400 los pedidos por rango de
  fechas, que es como los arma `fad/espn.py`. El build diario no lo nota, porque los
  torneos cerrados salen del CSV; un `--rehacer` sin cache dejaría sin fecha las páginas
  que dependen de ESPN.
- **Documentación que quedó vieja:**
  - El primer bloque del `README.md` dice `partidos-2004.csv … 2026`, `39 255` partidos
    desde febrero de 2004, `208` clubes, `131` torneos y `72` sin fecha; son archivos
    desde 1985, `48 995` partidos desde julio de 1985, `212` clubes, `163` torneos y `6`.
    El ejemplo de encabezado no trae la columna `status`.
  - El ítem 8 del plan del README tiene en un solo renglón sin tildar «1991-2003», que ya
    está, y «la era Metropolitano/Nacional», que falta.
  - La sección del README sobre el Argentino A 2004-05 dice que RSSSF no publica ninguna
    tabla de esa temporada.
  - `data/sin-fecha/LEEME.md` dice 9 filas en tres torneos; son 6, todas del Federal A
    2024. Su tabla de fuentes también es vieja.
  - Tres comentarios de `fad/torneos.py`, en el bloque de 1997–2003, dan por afuera la
    capa 1991–1996 y al Clausura 1991 por un stub.
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
| 2004–2026 | 36 813 | Wikipedia sola | cerrado |
| 2004–2026, con segunda fuente | 5 194 | Wikipedia + RSSSF / worldfootball / otras | cerrado |
| 1997–2003 | 2 469 | Wikipedia | cerrado |
| 1991–1996 | 2 470 | Wikipedia (partidos) + RSSSF (fechas) | cerrado |
| 1985–1990 | 2 049 | RSSSF (partidos) + Wikipedia (tabla) | cerrado |
| 1985–1990, Nacional 1985 y liguillas | 318 | Wikipedia + RSSSF | al alcance 288; 30 sin lector |
| 1967–1984 | 5 570 | Wikipedia | al alcance, falta padrón |
| 1933–1966 | 8 903 | RSSSF, con Wikipedia de testigo | falta el lector |

Las cinco primeras filas suman los `48 995` del dataset. Las tres últimas suman `14 791`
y son un piso de lo que falta: la fila 1967–1984 cuenta sólo lo que el parser ya lee con
fecha, sin los 342 del Metropolitano 1982 ni los 1 215 resultados en lista.

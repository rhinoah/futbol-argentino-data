# Licencia y fuentes de los datos

El **código** de este repositorio está bajo licencia MIT (ver [`LICENSE`](LICENSE)).

Los **datos** (`data/partidos-AAAA.csv` y `data/sin-fecha/`) no, y no pueden
estarlo: este repositorio no los hizo, los juntó. Salen de **Wikipedia en español**
y, donde Wikipedia no publica los partidos o no les pone día, de **RSSSF**; unas
pocas filas usan además fuentes menores. Este archivo dice qué se toma de cada una,
con qué condición, y cómo se la reconoce.

## Creative Commons Atribución-CompartirIgual 4.0 (CC BY-SA 4.0)

El dataset se publica bajo esta licencia.

- Texto completo: https://creativecommons.org/licenses/by-sa/4.0/legalcode.es
- Resumen: https://creativecommons.org/licenses/by-sa/4.0/deed.es

No es una elección. Más de nueve de cada diez partidos salen de Wikipedia en
español, y lo que se extrae de ahí es una obra derivada: hereda su licencia.

Podés **usarlos, copiarlos, modificarlos y redistribuirlos, incluso
comercialmente**, con dos condiciones:

1. **Atribución.** Hay que decir de dónde salen. La columna `source` de cada fila
   trae la URL exacta de la página de Wikipedia de su torneo y, si otra fuente le
   puso el partido, el día o la localía, la nombra después de un ` + `: la
   procedencia viaja con el dato. A RSSSF casi siempre la nombra por el sitio y no
   por el archivo, y por eso el reconocimiento a sus autores está escrito más abajo.
2. **CompartirIgual.** Si publicás una versión modificada del dataset, va con la
   misma licencia.

**Los archivos de RSSSF no son Creative Commons**, y este repositorio no los
relicencia ni los redistribuye: toma de ellos resultados de partidos, con el
permiso y la condición que están más abajo. Si reusás esas filas, la condición
—reconocer al autor— va con ellas. Lo mismo pasa con lo que sale de worldfootball,
que llega con términos propios y más estrictos: si le vas a dar un uso comercial,
miralos antes.

Las filas sin ` + ` en `source` no toman de otra fuente ni el partido ni el día. En
medio centenar de ellas, eso sí, el marcador —o la tanda de penales— no es el que
trae la página: se corrigió a mano, casi siempre contra testigos de afuera que la
fila no nombra. Cada caso está declarado, con su evidencia, en
`fad/correcciones.py`. Ahí también están los 70 partidos de fases finales cuyo
`neutral` dice `true` por una declaración a mano —en 61 lo dice la propia página, en una
sección que habla de varias rondas, y en los otros nueve sólo la prensa o la ficha del
partido en una obra de estadística—, y los seis del Nacional 1985 que dicen `false`
aunque la frase de su sección hable de campo neutral, porque la misma frase los da de
local. Los 76 citan un testigo de afuera. Y en los quince partidos que publican las páginas de dos
torneos, lo que una de las dos no trae —la hora, la cancha, `neutral`—, o lo que
escribe distinto, puede venir de la otra, que también es Wikipedia, aunque `source`
nombre sólo la suya.

## Las fuentes

| fuente | qué pone | filas |
|---|---|---:|
| [Wikipedia en español](https://es.wikipedia.org) | todo, en cuatro de cada cinco filas; en el resto, lo que no pone otra | |
| [RSSSF](https://www.rsssf.org/) | el partido entero | 3 945 |
| | sólo el día | 4 177 |
| [worldfootball](https://www.worldfootball.net/) | sólo el día | 1 519 |
| el [blog de José Carluccio](http://josecarluccio.blogspot.com/) | sólo el día | 76 |
| | el día y la localía | 14 |
| doce citas sueltas | sólo el día | 8 |
| | el día y la hora | 4 |

Medido el 24 de octubre de 2026. Ninguno de esos números se mueve con la
actualización de todos los días: son de torneos terminados. Son 9 706 filas y la
tabla suma 9 743 porque en 37 —las llaves del Torneo Argentino A 2004-05— el
partido sale de RSSSF y el día de un blog, y están contadas en los dos.

### Wikipedia en español

La fuente de casi todo: equipos, marcadores, jornadas, estadios, horarios. Y en los
once torneos cuyos partidos salen de RSSSF sigue estando: pone la tabla de
posiciones contra la que se verifican —en la 1988-89, sólo los de la primera
rueda: las fechas 20 a 38 cierran contra la tabla de la propia RSSSF—.

### RSSSF

[RSSSF](https://www.rsssf.org/) —la Rec.Sport.Soccer Statistics Foundation— publica
el fútbol argentino temporada por temporada, en archivos que preparan y mantienen
sus autores. De ahí sale lo que Wikipedia no publica:

- **El partido entero, en 3 945 filas.** Once torneos de los que Wikipedia tiene la
  tabla de posiciones y no los resultados —la Primera División de 1985-86 al
  Clausura 1991 (2 239 filas) y el Torneo Argentino A de 2006-07 a 2009-10
  (1 573); de la 1989-90 publica sólo las ocho primeras fechas—, y 133 partidos de
  fases finales del ascenso que Wikipedia trae sólo como cuadro.
- **El día, en 4 177.** Partidos que Wikipedia publica sin fecha: la Primera
  División del Apertura 1991 al Clausura 1997 (2 268) y nueve torneos del ascenso
  entre 2005-06 y 2012-13 (1 903). Las otras 6 son fechas sueltas: cinco
  corregidas a mano y una, de la Primera C 2024, puesta a mano donde la página
  deja la celda vacía.

Las 8 122 la nombran en `source`.

Lo que se toma son **resultados de partidos**: qué clubes jugaron, qué día, cómo
salieron y quién fue local. En las filas que salen enteras de ahí viaja además lo
que el archivo diga de la ronda, la zona, la tanda de penales o un partido que no
terminó. Nada más entra al dataset: sus tablas de posiciones se leen para
verificar, y los archivos no están en este repositorio (`.cache/` no se versiona).
Lo que sí hay en el código, en los tests y en el README son renglones sueltos,
citados para documentar el formato o como evidencia de una corrección, y dos tablas
de `arg89` transcriptas en `tests/test_build.py` como testigo de la temporada
1988-89: la final del campeonato —seis de sus trece columnas— y la de tandas de
penales, entera.

**La condición.** El pie de cada uno de esos archivos autoriza a copiarlo, entero o
en parte, a condición de reconocer a quien lo hizo —«provided that proper
acknowledgement is given to the author», o «to the authors» en dos de ellos— y
reserva todos los derechos. No es una licencia Creative Commons: es un permiso con
una condición, y la condición se cumple en la sección que sigue.

RSSSF se consultó además para verificar temporadas de las que no aporta ninguna
fila.

### Las menores

Ponen el día de un partido que ya está; la excepción son los 14 partidos del
Reducido de la Primera C 2011-12, que Wikipedia trae sólo como cuadro: los clubes y
el marcador de cada uno salen de ese cuadro, y el día y quién fue local, del blog de
José Carluccio. En algunas pesaron además en otro campo: worldfootball en
doce de las suyas —el marcador en 8, la localía en 3 y el rival en 1—, el blog de
José Carluccio en el marcador de una y una revisión vieja de Wikipedia en el de
otra. Cada caso está declarado, con su evidencia, en `fad/correcciones.py`. Cada
una va nombrada en el `source` de las filas a las que les puso el día o la localía.

- **[worldfootball](https://www.worldfootball.net/)** — el día de 1 519 partidos de
  la Primera B Nacional de 2007-08 a 2010-11, que Wikipedia publica en tablas de
  tres columnas, sin fecha. Sus términos de uso limitan el aprovechamiento a fines
  personales y no comerciales.
- **El [blog de José Carluccio](http://josecarluccio.blogspot.com/)** — el día de
  76 partidos, copiado a mano: 56 del Torneo Argentino A 2004-05 y 20 de la
  Primera C de 2008-09 a 2010-11 y la Primera B 2010-11. Y el día y la localía de
  los 14 del Reducido de la Primera C 2011-12, también a mano: cada pata entra sólo
  si el cuadro de Wikipedia publica ese cruce con ese marcador. El blog no publica
  condiciones de uso ni licencia; esas 14 filas nombran el post del que se copió.
- **Doce citas sueltas** — el día de 12 partidos, cada uno con su URL en `source`:
  Página/12 en la [Hemeroteca Digital](https://hemerotecadigital.bn.gob.ar/) de la
  Biblioteca Nacional, [historiadeboca.com.ar](https://historiadeboca.com.ar/),
  [soybh.blogspot.com](http://soybh.blogspot.com/) —la página de un hincha de Ben
  Hur—, en dos una revisión vieja de la propia página de Wikipedia,
  [La Nueva](https://www.lanueva.com/) en la vuelta de la final de la Primera B
  2012-13, la síntesis de [Solo Ascenso](https://www.soloascenso.com.ar/) en tres
  partidos de la Primera B 2024 y 2025 que se jugaron otro día que el programado y
  la crónica de [Ascenso del Interior](http://ascensodelinterior.com.ar/) en uno del
  Torneo Argentino A 2012-13 que tampoco se jugó el día de la celda, y
  [La Capital de Mar del Plata](https://www.lacapitalmdp.com/) y
  [La Capital de Rosario](https://www.lacapital.com.ar/) en dos del Nacional 1985 que
  la página fecha tres días tarde. Las síntesis de Solo Ascenso dan también la hora;
  la del partido del Argentino A sale de la nota de la página.

Este proyecto no persigue ningún fin comercial.

## Reconocimiento a los autores de RSSSF

Los resultados que este dataset toma de RSSSF son trabajo de quienes prepararon y
mantienen cada archivo para la Rec.Sport.Soccer Statistics Foundation. El
reconocimiento va por archivo y con nombre, porque cada uno lo firma quien lo armó.

«Entero» quiere decir que el partido sale de RSSSF —equipos, localía, marcador,
ronda y día—. «Sólo el día», que el partido es de Wikipedia y RSSSF le puso la
fecha.

| temporada | archivo | qué aporta | entero | sólo el día | autores |
|---|---|---|---:|---:|---|
| 1985-86 | [`arg86`](https://www.rsssf.org/tablesa/arg86.html) | Primera División 1985-86 | 342 | | Pablo Ciullini |
| 1986-87 | [`arg87`](https://www.rsssf.org/tablesa/arg87.html) | Primera División 1986-87 | 380 | | Javier Roimiser y Pablo Ciullini |
| 1987-88 | [`arg88`](https://www.rsssf.org/tablesa/arg88.html) | Primera División 1987-88 | 380 | | Javier Roimiser y Pablo Ciullini |
| 1988-89 | [`arg89`](https://www.rsssf.org/tablesa/arg89.html) | Primera División 1988-89, con la tanda de penales de sus empates | 379 | | Pablo Ciullini |
| 1989-90 | [`arg90`](https://www.rsssf.org/tablesa/arg90.html) | Primera División 1989-90 | 379 | | Pablo Ciullini |
| 1990-91 | [`arg91`](https://www.rsssf.org/tablesa/arg91.html) | Apertura 1990 y Clausura 1991 | 379 | | Pablo Ciullini |
| 1991-92 | [`arg92`](https://www.rsssf.org/tablesa/arg92.html) | Apertura 1991 y Clausura 1992 | | 380 | Pablo Ciullini |
| 1992-93 | [`arg93`](https://www.rsssf.org/tablesa/arg93.html) | Apertura 1992 y Clausura 1993 | | 380 | Pablo Ciullini |
| 1993-94 | [`arg94`](https://www.rsssf.org/tablesa/arg94.html) | Apertura 1993 y Clausura 1994 | | 379 | Pablo Ciullini |
| 1994-95 | [`arg95`](https://www.rsssf.org/tablesa/arg95.html) | Apertura 1994 y Clausura 1995 | | 380 | Pablo Ciullini |
| 1995-96 | [`arg96`](https://www.rsssf.org/tablesa/arg96.html) | Apertura 1995 y Clausura 1996 | | 379 | Pablo Wally |
| 1996-97 | [`arg97`](https://www.rsssf.org/tablesa/arg97.html) | Apertura 1996 y Clausura 1997 | | 370 | Ian King y Pablo Ciullini |
| 2004-05 | [`arg3-int05`](https://www.rsssf.org/tablesa/arg3-int05.html) | Torneo Argentino A 2004-05: las llaves de las dos fases finales, sin el día | 37 | | Juan Pablo Andrés |
| 2005-06 | [`arg3-int06`](https://www.rsssf.org/tablesa/arg3-int06.html) | Torneo Argentino A 2005-06: la fase final entera y el día de la fase de zonas | 60 | 263 | Juan Pablo Andrés |
| 2006-07 | [`arg3-int07`](https://www.rsssf.org/tablesa/arg3-int07.html) | Torneo Argentino A 2006-07 | 334 | | Juan Pablo Andrés |
| 2007-08 | [`arg2-08`](https://www.rsssf.org/tablesa/arg2-08.html) | Primera B Nacional 2007-08: los cuatro partidos de la promoción | | 4 | Juan Pablo Andrés |
| 2007-08 | [`arg3-int08`](https://www.rsssf.org/tablesa/arg3-int08.html) | Torneo Argentino A 2007-08 | 400 | | Juan Pablo Andrés |
| 2008-09 | [`arg4-09`](https://www.rsssf.org/tablesa/arg4-09.html) | Primera C 2008-09: el Reducido entero y el día de la fase regular | 10 | 374 | Juan Pablo Andrés |
| 2008-09 | [`arg3-int09`](https://www.rsssf.org/tablesa/arg3-int09.html) | Torneo Argentino A 2008-09 | 400 | | Juan Pablo Andrés |
| 2009-10 | [`arg4-2010`](https://www.rsssf.org/tablesa/arg4-2010.html) | Primera C 2009-10 | | 370 | Juan Pablo Andrés |
| 2009-10 | [`arg3-int2010`](https://www.rsssf.org/tablesa/arg3-int2010.html) | Torneo Argentino A 2009-10 | 439 | | Juan Pablo Andrés |
| 2010-11 | [`arg2011`](https://www.rsssf.org/tablesa/arg2011.html) | Primera B 2010-11 y Primera C 2010-11: el día. Torneo Argentino A 2010-11: 14 partidos de la fase final enteros y el día de otros 8 | 14 | 844 | Juan Pablo Andrés |
| 2011-12 | [`arg2012`](https://www.rsssf.org/tablesa/arg2012.html) | Torneo Argentino A 2011-12: las semifinales y la final enteras y el día de 28 partidos de eliminación | 6 | 28 | Ian King, Pablo Ciullini y Osvaldo José Gorgazzi |
| 2012-13 | [`arg3-int2013`](https://www.rsssf.org/tablesa/arg3-int2013.html) | Torneo Argentino A 2012-13: las semifinales y la final enteras y el día de 20 partidos de eliminación | 6 | 20 | Pablo Ciullini |
| 2014 | [`arg2015`](https://www.rsssf.org/tablesa/arg2015.html) | Primera B 2014: un día corregido a mano | | 1 | Osvaldo José Gorgazzi |
| 2015 | [`arg2015a`](https://www.rsssf.org/tablesa/arg2015a.html) | Primera B 2015: tres días corregidos a mano | | 3 | Osvaldo José Gorgazzi |
| 2020 | [`arg2020`](https://www.rsssf.org/tablesa/arg2020.html) | Copa de la Liga 2020: un día corregido a mano | | 1 | Osvaldo José Gorgazzi |
| 2024 | [`arg2024`](https://www.rsssf.org/tablesa/arg2024.html) | Primera C 2024: un día puesto a mano, el de un partido que la página publica sin fecha | | 1 | Osvaldo José Gorgazzi |
| | | **total: 8 122 filas** | **3 945** | **4 177** | |

En algunas de las de «sólo el día» RSSSF pesó además en la localía o en el
marcador; cada caso está declarado, con su evidencia, en `fad/correcciones.py`.
Fue además uno de los testigos en una decena de los marcadores corregidos a mano,
en filas que no la nombran.

Los nombres son los que firman el pie de cada archivo, copiados de ahí y cotejados
contra la página publicada el 13 de octubre de 2026.

**En `source`**, las filas de RSSSF dicen `… + https://www.rsssf.org/`: el sitio,
no el archivo. Con la página de Wikipedia que va antes del primer ` + ` se llega al
archivo por esta tabla, porque cada torneo usa uno solo. Las seis de los cuatro
últimos renglones sí traen la URL del archivo.

## Atribución sugerida

> Datos de [futbol-argentino-data](https://github.com/rhinoah/futbol-argentino-data),
> extraídos de [Wikipedia en español](https://es.wikipedia.org) —disponibles bajo
> [CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/deed.es)— y de los
> archivos que Pablo Ciullini, Juan Pablo Andrés, Javier Roimiser, Ian King,
> Osvaldo José Gorgazzi y Pablo Wally prepararon para la
> [Rec.Sport.Soccer Statistics Foundation](https://www.rsssf.org/) (RSSSF).

Si usás una sola temporada de las que salen de RSSSF, alcanza con nombrar a su
autor: está en la tabla de arriba.

## Si sos una de las fuentes

RSSSF autoriza la copia en el pie de sus archivos, y este dataset se apoya en eso.
Aun así: si **RSSSF o cualquiera de los autores** de esos archivos considera que
este uso no corresponde, o quiere que el reconocimiento se escriba de otra manera,
alcanza con [abrir un
issue](https://github.com/rhinoah/futbol-argentino-data/issues) y se corrige o se
retira. Retirar tiene un costo y conviene decirlo: las 4 177 filas donde RSSSF pone
el día se quedarían sin él —salvo las que pueda fechar otra fuente—, y las 3 945
donde pone el partido saldrían del dataset: once torneos enteros y 133 partidos de
las fases finales de otros seis.

Lo mismo vale para **worldfootball**: si considera que su aporte no corresponde, se
retira, y sus 1 519 partidos quedarían como estaban, sin la fecha. Y vale para
cualquiera de las otras: los 14 del Reducido de la Primera C 2011-12 saldrían del
dataset si el blog de José Carluccio pidiera que no se lo use.

Ya pasó una vez. Hasta octubre de 2026 el dataset tomaba 21 filas del feed de ESPN
—los 14 partidos de ese Reducido y el día de otros 7—. Sus condiciones de uso no
autorizan a extraer contenido para armar una base de datos, así que se retiró
entero: las 21 filas siguen, con los mismos días, tomadas de la propia Wikipedia,
de RSSSF y del blog.

## Por qué Wikipedia y no una API

Las alternativas obvias — las APIs de resultados deportivos — tienen datos mejor
estructurados y **términos de uso que prohíben redistribuirlos**. Sirven para
consultar, no para armar un dataset y publicarlo. Wikipedia es la única fuente
con cobertura del ascenso argentino y una licencia abierta, que permite justamente
esto. RSSSF no tiene una licencia así, pero autoriza a copiar reconociendo al
autor: por eso entra donde Wikipedia no llega, a completar. Cuando corrige un dato
que la página sí publica —un día, una localía, un marcador—, cada caso está
declarado, con su evidencia, en `fad/correcciones.py`.

Es la razón por la que el parser existe en vez de un `requests.get` a un endpoint
JSON: el laburo de sacar los partidos del wikitexto es el precio de poder
compartir el resultado.

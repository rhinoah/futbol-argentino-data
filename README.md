# futbol-argentino-data

Un dataset abierto de partidos del fútbol argentino, armado a partir de
Wikipedia en español y actualizable solo.

`data/partidos-2004.csv` … `data/partidos-2026.csv` — **un archivo por
temporada**. Los de temporadas terminadas no se tocan nunca más; sólo cambia el
del año en curso.

```python
import pandas as pd, glob
df = pd.concat(map(pd.read_csv, sorted(glob.glob("data/partidos-*.csv"))))
```

```
date,time,home_team,away_team,home_score,away_score,home_pens,away_pens,tournament,season,phase,group,matchday,venue,neutral,source
2026-01-22,17:00,Aldosivi,Defensa y Justicia,0,0,,,Primera Division - Apertura,2026,zonas,Interzonal,Fecha 1,José María Minella,false,https://es.wikipedia.org/wiki/...
```

**Estado:** **39 255 partidos entre febrero de 2004 y hoy** — veintitrés años de
Primera División, quince de Primera Nacional, once de Primera B, Primera C y
Torneo Federal A, y diez ediciones de la Copa Argentina. **208 clubes**, 131
torneos, cero partidos sin fecha, sin marcador ni duplicados. Se actualiza solo,
todos los días.

Aparte, en [`data/sin-fecha/`](data/sin-fecha/) quedan **72 partidos que están
completos salvo por el día en que se jugaron**. Eran 2 345 y eran seis temporadas
enteras; hoy son un resto suelto, y ninguno está ahí porque a su torneo le falte
fuente de fechas: están uno por uno, por su propio motivo. Van separados
justamente para que el dataset principal pueda seguir prometiendo una fecha en
cada fila.

## Por qué

Para selecciones existe
[martj42/international_results](https://github.com/martj42/international_results),
que es excelente y tiene 50 años de partidos. Para el fútbol argentino de clubes
no encontré nada equivalente que siga vivo:

| fuente | estado |
|---|---|
| [openfootball/argentina](https://github.com/openfootball/argentina) | último dato real 05/2025, mientras el feed de Brasil sigue al día |
| [footballcsv](https://github.com/footballcsv) | frenado en 2024 |
| APIs comerciales | los datos están, pero los términos de uso **prohíben redistribuirlos** |
| **la AFA** | tiene resultados oficiales, pero **sin histórico** y sin licencia para republicar — ver abajo |

Esa última columna es la que decide todo. Se puede *consultar* una API; no se
puede publicar un dataset con lo que devuelve. Wikipedia es la única fuente con
cobertura del ascenso argentino cuya licencia (CC BY-SA) permite exactamente lo
que hace falta: tomar, transformar y volver a publicar.

De ahí que exista un parser de wikitexto en vez de un `requests.get`. Ese laburo
es el precio de poder compartir el resultado.

### ¿Y la AFA?

Es la pregunta obvia y la respuesta es interesante. Sí publica resultados, pero
no en `afa.com.ar` — ahí la sección "Fixture" son PDFs y los más nuevos son de
2024. Los datos vivos entran por un `<iframe>` desde otro host,
`info.afa.org.ar/deposito/html/v3/`, como fragmentos de HTML (no hay API JSON).
Están bien estructurados, con IDs de club estables, y traen cosas que Wikipedia
no tiene: **árbitro de cada partido**, horario y estado.

Tres cosas lo descartan como base del dataset:

1. **No hay histórico.** Es un archivo por competencia que se pisa. Hoy
   `primeraa` va del 23/07 al 12/12/2026: sólo el Clausura. El Apertura, que
   terminó en mayo, ya no está.
2. **Licencia.** El pie dice "Todos los derechos reservados" y no hay términos de
   uso publicados. El `robots.txt` sólo bloquea `/cache/`, así que bajarlo no
   está prohibido — pero eso regula el crawleo, no la redistribución. Mismo
   callejón que las APIs comerciales.
3. **Ya tiene un canal abandonado**: Primera D quedó congelada en 2023.

Donde sí sirve es como **testigo**. Los 60 partidos jugados del Clausura 2026,
bajados del feed oficial y cruzados contra lo que este repo sacó de Wikipedia:

```
equipos: AFA 30, Wikipedia 30
60/60 coinciden exacto
marcador distinto : 0
```

## Fuentes y atribución

**Wikipedia en español** es la fuente de todo: equipos, marcadores, jornadas,
estadios. Los datos están bajo [CC BY-SA 4.0](LICENSE-DATOS.md) y la columna
`source` de cada fila lleva la URL exacta de la página de la que salió, así que
la atribución viaja con el dato.

**Tres fuentes más aportan un solo campo**, y sólo en **3 330 filas de 39 255**
(8,5 %): la **fecha del calendario** de partidos que Wikipedia publica sin fecha.
Una decena de temporadas del ascenso entre 2005 y 2011 usan tablas de tres
columnas (`Local | Resultado | Visitante`) y nada más. El partido, los equipos, el
marcador y la jornada siguen saliendo de Wikipedia.

Son tres y no una porque ninguna cubre todo: **[worldfootball](https://www.worldfootball.net/)**
tiene la Primera B Nacional 2007-2011 (1 520 filas) pero su Primera B
Metropolitana arranca en 2018/19 y no lista Primera C ni el Argentino A; el feed
de **[ESPN](https://www.espn.com.ar/)** cubre Primera B y C de esos años (1 547);
y **[RSSSF](https://www.rsssf.org/)** tiene el Argentino A viejo (263), que no
está en ninguna de las otras dos.

Sin ese campo esas cuatro temporadas no entrarían: el esquema promete una fecha en
cada fila, así que los 1 520 partidos se descartaban enteros. La diferencia no es
"peor calidad", es que el torneo no existe.

El cruce no empareja por nombre. Dentro de una jornada, **un marcador que aparece
una sola vez de cada lado identifica el partido sin ambigüedad**, y de paso dice
quién es cada equipo: así se deduce el padrón de ids de la otra fuente sin
depender de cómo escriba los nombres. Después la fecha se copia sólo si las dos
fuentes coinciden en equipos, jornada **y marcador**. Los 9 partidos donde no
coincidían se resolvieron con un árbitro que no es ninguna de las dos (ver abajo) — un partido que dos fuentes cuentan
distinto es información sobre los datos, no algo para tapar.

Cuando una fila usa esa segunda fuente, **su `source` nombra las dos**:

```
https://es.wikipedia.org/wiki/... + https://www.worldfootball.net/
```

Fila por fila, y sólo en las que de verdad la usaron. Nombrarla donde no se usó
sería tan incorrecto como omitirla donde sí.

#### Un instante y una fecha disfrazada de instante

Cada partido de esa fuente trae un `data-datetime` en UTC. Parece un campo y son
dos cosas distintas, y confundirlas corrió **760 fechas un día entero**.

Cuando el sitio conoce la hora del partido, el instante es real y lo que vale es
la fecha **argentina**: `18:30Z` son las 15:30 de un sábado a la tarde. Cuando no
la conoce —el bloque dice `match-time-unknown`— `data-datetime` no es un instante:
es la **medianoche de ese día en Berlín**, que es donde vive el sitio. Se nota
porque en dos temporadas enteras toma **dos valores nada más**, `22:00Z` en verano
europeo y `23:00Z` en invierno. Restarle tres horas a una medianoche cae en el día
anterior.

Eso son las temporadas 2007-08 y 2008-09 completas. Y no fallaba: escribía una
fecha plausible, contigua a las demás, un día antes de la que el propio sitio
publica al lado del partido. Se vio comparando las 1 520 fechas calculadas contra
la fecha visible de la página: 0 % de coincidencia en esas dos, 100 % en las otras
dos.

De paso quedó al descubierto una premisa al revés. El código usaba UTC-3 fijo
"porque Argentina no tiene horario de verano desde 2009 y las temporadas que
interesan son anteriores". Las que tuvieron horario de verano son **justamente**
las anteriores a 2009 — 191 de estos partidos caen dentro de esas ventanas. Ahora
va con `zoneinfo`.

Sus términos limitan el uso a fines personales y no comerciales, y este proyecto
no tiene ninguno: es un dataset abierto hecho por gusto. **Si worldfootball pide
que se retire ese aporte, se retira** — los partidos seguirían estando, sin la
fecha, como estaban antes.

El acceso es respetuoso por diseño: caché en disco para no volver a pedir lo
mismo, pausa mínima entre pedidos, y User-Agent identificado con el link a este
repositorio.

## Cómo se usa

```bash
python build.py              # baja, parsea, valida y escribe data/partidos-AAAA.csv
python build.py --dry-run    # parsea y valida, sin escribir
python build.py --sin-cache  # vuelve a pedirle todo a Wikipedia
python build.py --forzar     # escribe aunque el dataset se achique
pytest                       # la suite
python mutar.py              # rompe el código a propósito y exige que la suite lo note
```

Sin dependencias: Python 3.11+ y la biblioteca estándar. `pandas` no hace falta
para *armar* el dataset — si lo vas a *usar*, el `glob` de arriba
y listo.

## El esquema

Las seis primeras columnas son iguales a las de martj42, a propósito: el código
que ya lee aquel dataset lee este casi sin tocar nada.

| columna | qué trae |
|---|---|
| `date` `time` | ISO (`2026-01-22`) y hora local |
| `home_team` `away_team` | los equipos |
| `home_score` `away_score` | el marcador de los 90 (más alargue si hubo) |
| `home_pens` `away_pens` | la tanda de penales, vacío si no hubo |
| `tournament` `season` | `Primera Division - Apertura`, `Copa Argentina`, `2026` |
| | ojo: `season` es la **temporada**, no el año del partido. La 2016-17 lleva `season=2016` y sus partidos van de agosto de 2016 a junio de 2017. La fecha real está en `date`. |
| `phase` | `zonas` o `eliminacion` |
| `group` | `Zona A`, `Zona B`, `Interzonal` |
| `matchday` | `Fecha 7`, o la ronda: `Dieciseisavos`, `Semifinales` |
| `venue` | el estadio, tal como figura |
| `neutral` | si se jugó en cancha neutral — ver abajo |
| `source` | la URL de la página de la que salió esa fila |
| `status` | de dónde salió el marcador: vacío, `suspendido` o `escritorio` — ver abajo |

Sobre **`neutral`**: sale del **reglamento de la competencia**, no de comparar el
estadio contra el de cada club. La Copa Argentina se juega a partido único en
cancha neutral y su propia página lo dice ronda por ronda, así que ahí el dato se
puede afirmar. En las ligas es `false`, con este alcance exacto: *el partido se
jugó donde dice el fixture*. **No detecta mudanzas puntuales** — un partido de
liga que se muda de cancha sigue figurando `false`. Prefiero decir eso y
documentarlo antes que deducir la localía con un padrón de estadios que todavía
no existe.

Sobre **`status`**: un partido puede terminar de otra forma que jugándose
completo. Se suspende por incidentes, o se juega entero y después un tribunal
cambia el resultado por una inclusión indebida. Hasta ahora esas filas salían con
un marcador **indistinguible de uno jugado en cancha**.

| valor | qué afirma | filas |
|---|---|---:|
| vacío | **nada.** La página no dijo otra cosa. No certifica que se jugaran los 90: dice que nadie dijo lo contrario | 39 189 |
| `suspendido` | la fuente dice que el partido **no llegó al final** | 56 |
| `escritorio` | el partido **sí terminó** y el número publicado lo puso un fallo | 7 |

**El eje no es el que parece.** Lo natural sería distinguir "el tribunal ratificó
el marcador de la cancha" de "el tribunal lo cambió", y no se puede: la fuente no
lo dice de forma decidible. La misma fórmula sostiene los tres casos —

- ratificando: *«Suspendido a los 39' […] con el resultado 1 a 1. Se dio por finalizado.»*
- cambiándolo: *«decidió darlo por terminado con resultado 4-0»*, sobre una cancha que iba 4-1
- y cambiándolo **distinto para cada club**: *«Se dio por finalizado, dándolo por perdido a Deportivo Español y empatado a Sacachispas.»*

Se clasificaron 53 casos a mano, con la página entera a la vista y sin apuro, y
**dos de las tres correcciones que hizo la verificación cruzaron justamente esa
frontera**. Un parser que corre todos los días a las 10:00 la decidiría por
keyword. Así que el eje es el único que la fuente marca siempre y sin ambigüedad:
**¿el partido llegó al final?**

**El default es la parte peligrosa.** Vacío significa "la página no dijo nada", y
nunca puede pasar a significar "dijo algo que no supe leer" — si eso ocurriera,
las 39 mil filas vacías dejarían de ser una ausencia y pasarían a ser una
afirmación sin verificar. Por eso una fila que menciona un fallo y no se puede
clasificar **no queda callada**: emite un aviso. Hoy son cero.

### Los que la columna no arregla

Cinco partidos terminaron con **un resultado distinto para cada club**. El
Clausura 2005 es el más claro: Almagro–Boca se suspendió a los 64' con Almagro
ganando 3-2, y el Tribunal se lo dio por perdido **a los dos** —0-2 para Almagro,
2-3 para Boca—. La celda del wikitexto trae los dos marcadores (`0 - 2<br>3 - 2`)
y el parser se quedaba con el primero: **el CSV publicaba a Boca ganando 2-0 un
partido que Boca también perdió.**

Una fila tiene un `home_score` y un `away_score`: cualquier par de números afirma
un solo resultado. No es una limitación del parser sino del esquema, así que esos
cinco **no entran**, y el build los nombra uno por uno con su cita. Cuatro de los
cinco estaban entrando mal hasta ahora.

### Leer un CSV de antes

Agregar una columna rompe a quien lee el archivo anterior, y el que lo lee es el
propio `build.py`: reusa los torneos terminados leyendo el CSV publicado. Así que
`dataset.leer` acepta un encabezado al que sólo le falten columnas **del final**
y las completa vacías. Cualquier otra diferencia —columnas de más, reordenadas,
renombradas— sigue siendo un error: un CSV corrupto no se lee «lo mejor posible»,
se rechaza.

## Lo que hace difícil esto

El wikitexto es prosa con formato, no una base de datos. **Un parser mal escrito
no explota: miente.** Todos los errores de abajo estuvieron en el código, y
ninguno tiraba una excepción. Son tres formatos distintos en la misma Wikipedia,
y el peligro no es que un formato nuevo rompa el parser: es que *no* lo rompa.

**1. El `rowspan`.** Cuando varios partidos comparten día u horario, la celda
aparece una sola vez y las filas siguientes vienen con menos celdas. Un parser
que asuma seis columnas por fila corre todo y guarda el estadio en la fecha.

**2. Los paréntesis no son los penales.**

```
|resultado = 2:0''' (1:0)
```

Ese `(1:0)` es el **entretiempo**. Los penales viven en su propio parámetro
(`|resultado penalti = 4:3`). Leerlos de los paréntesis inventa definiciones por
penales en partidos que se ganaron en los 90 — y después alguien arma el cuadro
de eliminación al revés.

**3. Cada fecha es su propia tabla, y entre una y otra no hay separador de fila.**

```
|22 de enero
|17:00
|}                        ← cierra la tabla de la Fecha 1
{|class="wikitable ..."   ← abre la de la Fecha 2
!colspan=6|Fecha 2
```

Partiendo sólo por `\n|-`, la última fila de una fecha y el encabezado de la
siguiente caen en el mismo pedazo. Los 30 interzonales del Apertura 2026 —
siempre el último bloque de su jornada — quedaron anotados una fecha adelante.
Equipos, marcador y fecha del calendario, todos correctos. El único campo mal era
`matchday`.

**4. Y hay un tercer formato.** La Copa Argentina no usa ninguno de los dos
anteriores: es una tabla por ronda, con las celdas separadas por `||` en un solo
renglón. Trajo dos trampas más.

La primera es que sombrea una fila de cada dos, y ese atributo va pegado al
separador (`|- bgcolor="#F5FAFF"`). Contarlo como celda corre todas las columnas
un lugar; la fila corrida no tiene marcador donde el parser lo busca y se
descarta sola. Resultado: **se perdía exactamente la mitad de los partidos** —
16 de 32 treintaidosavos, 8 de 16 dieciseisavos. Una pérdida del 50% en silencio.

La segunda es que **el mismo paréntesis significa lo contrario según el formato**:

```
{{Partido|resultado = 2:0''' (1:0)}}   ← (1:0) es el ENTRETIEMPO
{{small|(5)}} 1 - 1 {{small|(6)}}      ← (5) y (6) son los PENALES
```

Se distinguen por lo que hay adentro: dos números con `:` es el primer tiempo,
uno solo es la tanda de ese equipo. Y hay que sacarlos **antes** de limpiar la
celda, porque la tanda vive dentro de una plantilla y limpiar la borra: leyéndola
después, el partido queda 1-1 y la definición por penales desaparece sin que nada
falle.

**5b. Una `s` que borraba 284 partidos.** `{{Partido}}` es la plantilla de un
partido de eliminación, y el parser la buscaba pidiendo `Partido` seguido de
`\s*\n`. Resulta que **`{{Partidos}}`, en plural, es una redirección a la misma
plantilla**: se renderiza igual y trae los mismos parámetros. Pero la `s` no es
whitespace, así que el regex no la veía. **27 páginas del catálogo la usan**, y en
24 de ellas el singular no aparece ni una vez: tenían la fase eliminatoria
completa afuera del dataset, sin un solo aviso.

El cierre tenía el mismo problema de fondo. Pidiendo `\n\s*\}\}` se exige que el
`}}` esté solo en su renglón, cuando lo más común es cerrarla pegada al último
parámetro (`|árbitro=[[Fulano]]}}`). Cuando cierra así, el `.*?` **sigue de largo y
se come las plantillas del medio** — y como los campos van a un diccionario, el
último `local` pisa al primero. En la Primera B 2021 tres plantillas colapsaban en
una: los equipos y el marcador de la final, los penales de la semifinal, el rótulo
de ronda de la primera. Un partido que nunca se jugó, con todos los campos llenos.
Ahora el cierre se cuenta por balance de llaves.

**5c. Una ronda no es una zona.** La tabla de una fecha y la de una llave se
escriben igual; el encabezado es lo único que las distingue: `!colspan=12|Fecha 7`
contra `!colspan=12|Desempate`. El parser tomaba cualquiera como **zona**, así que
las rondas terminaban en la columna `group` —que promete una zona y decía
`Octavos de final`— y los partidos quedaban como fase de grupos.

Eso dejó a la **Primera B 2017-18 entera afuera**, con un cartel en el catálogo
que culpaba a la numeración de fechas y era falso. Lo que la frenaba era **un**
partido: el desempate que definió el campeonato, contra 306 sin zona. Son 317
filas reetiquetadas y 317 partidos que entran.

**5d. Los partidos que no cuelgan de «Resultados».** Los reducidos, las
promociones y las finales de ascenso viven bajo títulos propios, y la búsqueda por
sección nunca se los pasaba al parser: **109 partidos** con fecha y estadio que se
perdían enteros.

Leerlos exige una guarda: **la tabla tiene que declararse a sí misma**, o sea traer
`Local | Resultado | Visitante` en su encabezado. Lo que evita, medido: sin la
guarda entran 117 filas y con ella 108. Las 9 de diferencia **no son partidos
inventados** —eso lo afirmé primero y era falso— sino partidos reales con el
nombre roto: uno sale como `San Martín (F) {{Tabla de posiciones`, comiéndose el
arranque de una plantilla. Un club así entra al padrón como desconocido y frena el
build.

Y evita el **arrastre de etiquetas**: parseando la página como un solo bloque, la
zona se hereda de una tabla a la siguiente, así que el partido por el tercer
descenso de la Primera Nacional 2024 salía con `zona='Amonestaciones'` —el último
encabezado visto, en la caja de goleadores—. El partido existe; la etiqueta no.

**5e. Y el mismo rótulo significa cosas distintas.** Después de sacar las rondas de
la columna `group` quedaban 98 filas con algo que no era una zona. Se fueron
resolviendo por partes, y ninguna con una lista de nombres:

*Cuando la sección se llama «Tabla de posiciones»* (44 filas). Varias páginas ponen
el calendario **debajo** de la tabla, así que el `===== Resultados =====` cuelga de
`==== Tabla de posiciones ====` y ese nombre terminaba como zona. Vaciarlo no
alcanzaba: los partidos quedaban sin zona mezclados con los que sí tenían, y
`todos_tienen_zona` frenaba el build en cuatro torneos.

El que estaba mal era el chequeo. Comparaba **toda la página** cuando una página
puede tener una fase con grupos y otra sin: la Primera B 2020 reparte la «Fase
segundo ascenso» en Grupo A y Grupo B, y la «Fase primer ascenso» es un solo
grupo. Ahora la mezcla se mira dentro de cada fase, y vaciar la etiqueta es
seguro.

*Cuando el nombre no alcanza* (8 filas). «Primera fase» es una fase de grupos en el
Federal A 2017 —con sus Fecha 1, Fecha 2— y una **llave** en el Transición 2020,
donde es hermana de «Semifinales» y «Final» bajo `== Etapa eliminatoria ==`. El
nombre no distingue; **el lugar sí**. Una sección bajo una etapa eliminatoria es
una ronda, se llame como se llame.

Quedan 46 filas, y están bien: `Nonagonal final` son **9 equipos, 36 partidos, 9
fechas de 4** —un todos contra todos de nueve, que es lo que significa la
palabra— y `Tercera fase` son **5 equipos, 10 partidos, 5 fechas de 2**.

**6. Una página puede traer varios torneos.** Bajar al ascenso rompió el supuesto
más silencioso de todos: que hay **una** sección "Resultados" por página.

No la hay. El ascenso pone `== Zona A ==` y `== Zona B ==` de primer nivel, cada
una con la suya; Primera B y C meten `== Torneo Apertura ==` y
`== Torneo Clausura ==`, o sea dos torneos completos en la misma página. Leyendo
una sola sección se perdía **exactamente la mitad**: la Primera Nacional 2025 daba
26 equipos donde hay 38. Y la mitad que quedaba estaba perfecta, que es lo que lo
hace difícil de ver.

Arreglarlo destapó tres más:

- si una sección "Resultados" contiene otra, el cuerpo de la de afuera ya incluye
  a la de adentro — tomándola igual, **cada partido entra dos veces**;
- la zona y la fase no son lo mismo. La Copa de la Liga 2020 tuvo Fase
  Clasificatoria, Campeonato y Complementación, y **cada una con su Grupo A y su
  Fecha 1**, con los mismos equipos. Quedándose sólo con el título de arriba, las
  tres colapsan en una;
- una página del ascenso tiene varios cuadros de eliminación (la final del
  campeonato, el torneo reducido, la definición de un ascenso). Encadenarlos como
  si fueran uno daba 21 avisos sobre datos correctos.

**5. Ir para atrás rompe supuestos que uno no sabía que tenía.** Diez temporadas,
y de golpe:

*El título "Resultados" está en nivel 2, no en 3.* De 2016 a 2024 es
`== Resultados ==`; recién en 2025 pasa a `=== Resultados ===`. Mi regex pedía
tres `=` o más, así que **nueve temporadas devolvían cero partidos** — y cero
partidos no se distingue de "todavía no empezó el torneo".

*Las temporadas cruzan de año, y la página no escribe el año.* Las tablas dicen
"26 de agosto", nada más; el año se sobreentiende. Para 2016-17 hay que deducirlo
del mes, y el corte no es siempre el mismo: **la 2019-20 arrancó el 26 de julio**.
Con el corte habitual en agosto, sus doce partidos de la Fecha 1 quedaban fechados
en julio de **2020** — la primera jornada del torneo, coherente consigo misma, con
el marcador correcto, y a doce meses de donde iba.

*Los íconos son enlaces a archivos, no texto.* `[[Archivo:Trophy.svg|15px|Campeón
matemático]]` marca al campeón y a los descendidos. Tratándolo como un wikilink
común deja el último parámetro pegado y el club pasa a llamarse
`Boca Juniors 15px|Campeón matemático`. Veinte nombres así.

*La fecha a veces viene en una plantilla.* `|fecha = {{fecha|17|1|2021}}, 22:10`.
Como limpiar borra las plantillas, la celda quedaba en `, 22:10 (UTC-3)`: partido
sin fecha. Y ahí la plantilla trae el año **explícito**, que no es un lujo — la
final de la Copa de la Liga 2020 se jugó en enero de 2021, así que cualquier año
deducido del torneo la habría puesto doce meses antes.

*Y un chequeo mío que estaba de más.* Exigir que todo partido de fase de grupos
tuviera zona convertía nueve temporadas correctas en nueve errores graves: de 2017
a 2024 el campeonato fue de **zona única**, veintipico de equipos en una sola
tabla. Lo que delata un encabezado no reconocido es la *mezcla* — unos con zona y
otros sin —, no el vacío.

### Lo que encontró en la fuente

Dos cosas que no son bugs míos y quedan documentadas porque afectan al dataset:

- **A la temporada 2019-20 le falta la Fecha 4.** No es que no la parsee: el
  texto "Fecha 4" no aparece en ninguna parte de esa página. Faltan 12 partidos.
  Esa temporada además quedó trunca — el último partido es del **9 de marzo de
  2020**, cuando la pandemia la suspendió, y nunca se completó.
- **Un club se llama `Tallleres (C)`**, con tres eles, en la Copa de la Liga 2022.
  Va cargado como alias: la alternativa era que el build se frene todos los días
  por una letra de más en una fuente que no controlamos.
- **`Aldovisi` por Aldosivi**, una vez en la B Nacional 2008-09. No lo encontró
  nadie leyendo: el padrón que se deduce del cruce vio 17 partidos de un mismo id
  llamados *Aldosivi* y uno *Aldovisi*, y avisó que ese id tenía votos
  contradictorios.
### El árbitro: la tabla de posiciones

Nueve partidos del ascenso 2007-2011 tenían un problema que parecía irresoluble:
Wikipedia y worldfootball coincidían en los equipos y en la jornada, y **discrepaban
en el marcador**. Como el marcador es lo que usa el cruce para *verificar* que las
dos fuentes hablan del mismo partido, no emparejaban, se quedaban sin fecha y se
caían del dataset.

La salida no fue elegir "la fuente que suele tener razón". La misma página de
Wikipedia publica, aparte de los resultados, su **tabla de posiciones**: partidos
jugados, goles a favor y en contra de cada club. Es una afirmación *independiente*
sobre la misma temporada, y sumar los marcadores tiene que dar exactamente eso.

Uno de los dos candidatos hace cerrar la tabla y el otro no:

```
Aldosivi      tabla GF44 GC54  |  con Wikipedia GF44 GC58  |  con la otra fuente GF44 GC54  ✓
Boca Unidos   tabla GF42 GC48  |  con Wikipedia GF45 GC48  |  con la otra fuente GF42 GC48  ✓
```

Los nueve quedaron resueltos. Y lo que muestra que el método mide algo es que **no
contesta siempre lo mismo**: ocho le dan la razón a worldfootball y uno a Wikipedia
(Talleres 0-4 Atlético Tucumán, donde el 1-4 de worldfootball rompe a los dos
clubes). Si el árbitro dijera siempre lo mismo, sería indistinguible de haber
elegido una fuente de antemano.

El cruce quedó como chequeo permanente en
[`fad/posiciones.py`](fad/posiciones.py), y **se calla cuando no puede opinar**: una
fila que no cierra consigo misma (`GF − GC ≠ DIF`) no desmiente a nadie, y si la
cantidad de partidos jugados no coincide, las dos partes no están hablando del
mismo conjunto.

**Y la tabla se escribe de dos formas.** Además de la `wikitable` habitual, muchas
páginas la arman con plantillas —`{{Tabla de posiciones equipo|g=23|e=12|p=3|gf=59|gc=15|eq=…}}`—
y buscando sólo `{|` se perdían enteras. Leyendo las dos, el árbitro pasó de
**19 torneos a 113**.

De esos 113, **94** llegan a comparar algún club: en los otros la cantidad de
partidos jugados no coincide —páginas de varias fases, donde la tabla es de una
sola— y el módulo se calla, que es lo correcto. De los 94, **73 cierran al gol** y
21 tienen algo que no.

Que 73 temporadas cierren contra una tabla que escribió otra mano es la
corroboración más fuerte que tiene el dataset.

#### Media página sin árbitro

Con eso andando, el árbitro seguía teniendo un punto ciego que no se veía desde
ningún contador: **leía una sola tabla por página**.

Un torneo por zonas publica una tabla por zona, y el título no las distingue — las
dos se llaman «Tabla de posiciones final» y lo que cambia es el `== Zona A ==` de
arriba. Son **91 de las 279 páginas**. En el Federal A 2019-20 los quince clubes de
la Zona B volvían sin tabla; en la Primera C 2026, la Zona B escondía cuatro
contradicciones que el aviso nunca denunció.

Leyendo todas y uniéndolas —cuando un club aparece en dos, gana la fila con **más
partidos**, que es lo que separa una zona distinta de la «parcial de la primera
rueda»—, los clubes efectivamente cruzados pasaron de **1722 a 2193**, sin perder
ninguno. Tres torneos que figuraban como que cerraban resultó que no.

Y en el camino aparecieron dos formas de perder un club en silencio, las dos por
el nombre:

- La **nota al pie pegada al nombre** en la tabla: `eq=[[Club Atlético Colón|Colón]]{{refn|…Se le descontaron 6 puntos…}}`.
  El club dejaba de reconocerse y se caía del cruce — y no es cualquier club: el que
  tiene quita de puntos es justo el que hay que mirar. Eran doce.
- El **artículo del wikilink**, que estaba ahí mismo y se tiraba para buscar el
  nombre visible en un mapa de toda la página.

#### Localizar no es arbitrar

De los que no cierran, los deltas por club **localizan** el partido: si a uno le
sobra un gol a favor y a otro le sobra uno en contra, el error está entre esos dos.
Y a veces hay **un único** ajuste de un gol que hace cerrar el torneo entero, lo que
parece una prueba.

No lo es. Se probaron **nueve** casos contra la prensa —buscando crónicas que
nombraran a los goleadores, no marcadores sueltos— y la tabla tenía razón en siete:

| caso | lo que pedía la tabla | lo que dice la prensa |
|---|---|---|
| Federal A 2019-20 | San Martín (F) 2-0 → **3-0** Unión (S) | confirmado — **corregido** |
| Primera Nacional 2024 | Alvarado 1-0 → **2-0** Talleres (RdE) | 2-0, con los dos goles — **corregido** |
| Primera C 2023 | Laferrere 1-0 → **1-1** Excursionistas | 1-1, con los dos goles — **corregido** |
| Federal A 2022 | Ciudad de Bolívar 1-1 → **2-1** JUU | 2-1, con los tres goles — **corregido** |
| Primera C 2026 | Centro Español 2-3 → 1-2 Juventud Unida | **2-3**: Wikipedia estaba bien |
| B Nacional 2012-13 | At. Tucumán 2-0 → 3-0 Olimpo | **2-0**, con los dos goleadores nombrados |
| Primera C 2026 | Claypole 0-0 → **2-2** Central Córdoba (R) | 2-2, con los cuatro goles — **corregido** |
| Primera Nacional 2022 | Estudiantes (RC) 2-1 → **2-0** Riestra | 2-0, ficha cerrada con dos goles — **corregido** |
| Primera Nacional 2022 | Santamarina 1-1 → **2-1** Chacarita | 2-1, con los tres goles — **corregido** |

Los tres últimos salieron de una tanda sobre **los únicos cuatro pares que
identifican un partido sin ambigüedad** — en una liga de ida y vuelta los dos clubes
se cruzan dos veces y la aritmética no puede elegir la fecha. Dos de ellos traen su
propia prueba dentro de la página, y vale distinguirlas:

- En **Estudiantes (RC) 2-1 Riestra** el ganados-empatados-perdidos coincide exacto
  con los partidos, así que la tabla ya computaba una victoria: sólo sobraba un gol.
  El 2-2 quedaba descartado por aritmética antes de abrir un solo diario.
- En **Santamarina 1-1 Chacarita** el G-E-P **no** coincide: la tabla le da a
  Santamarina un ganado más y un empatado menos. O sea que la propia página computa
  una victoria donde su grilla pone empate.
- En **Claypole 0-0** la sospecha de siempre —que la prensa haya copiado de
  Wikipedia— está muerta por construcción: Wikipedia publica 0-0, así que un medio
  que diga 2-2 no puede venir de ahí.

De paso, dos de los tres encargos salieron con la premisa invertida: los deltas se
midieron como `sumado − tabla` y se describieron como si fueran `tabla − sumado`. Lo
corrigieron los propios verificadores, y es la razón por la que conviene que el que
verifica rehaga la medición en vez de creerle al que pregunta.

En los dos que dieron «la tabla está mal» la equivocada era ella, igual que con Platense. Así que la
aritmética dice *dónde* mirar, no *quién* tiene razón: para eso hace falta salir a
buscar afuera, partido por partido. Va como **aviso**, no como error: lo que denuncia
es una contradicción de la fuente consigo misma.

Con una excepción, que apareció después y vale la pena adelantar: cuando la tabla no
balancea —su columna GF y su columna GC no suman lo mismo— sí dice quién tiene razón,
porque se está contradiciendo a sí misma y no hace falta ninguna otra fuente. Está
abajo, en los cinco de un solo club.

#### Una llave no tiene tabla

Todo lo anterior supone que existe una tabla. **La eliminación directa no la tiene**, y
ahí el árbitro de siempre no está. En la Reválida del Argentino A 2011-12 quedaban
cuatro patas donde Wikipedia y RSSSF daban marcadores distintos y ninguna aritmética
podía separarlas. Se cerraron por dos caminos, y la diferencia entre ellos es el punto.

**La tercera ronda la desmiente la propia página.** Escribe su regla con todas las
letras —«en caso de empate en puntos y diferencia de goles […] clasificarán las
posiciones 1; actuarán de local en el primer partido las posiciones 2»— y publica la
tabla de la ronda anterior, donde `Libertad (S)` es 1º con 13 puntos y `Central Norte (S)`
2º con 9. Con los marcadores que ella misma publica la serie termina **2-2**, y entonces
su regla manda pasar a Libertad. Pasa Central Norte: la página lo pone en negrita y lo
hace jugar la fase siguiente seis días después. Con el `2-0` de RSSSF la serie da 3-1 y no
hay desempate que aplicar.

No hizo falta traer una fuente para decidir: **la página se contradice sola**, igual que
cuando una tabla no balancea. De paso, esa misma regla confirma por otro lado el espejo
de la localía —el 2º es local en la ida, y el 2º es Central Norte—, que ya estaba resuelto
con otra evidencia.

**La segunda ronda no se contradice, y hubo que salir.** Ahí las dos versiones dan la
serie 1-1 y las dos dejan pasar a Juventud Unida por ventaja deportiva: la aritmética no
discrimina y no hay nada que arbitrar adentro de la página. Lo cerró **el blog del propio
club**, que publica las dos patas la semana que se jugaron —«Juventud Antoniana 1 / JUV
Univ DE SAN LUIS 1 / GOLES ACOSTA (CJA) SELTSER (JUUSL)», y la vuelta «sin abrir el
marcador», con las dos formaciones completas y un cero al lado de cada nombre—. El título
del post de la ida, *«El empate no sirve»*, sólo tiene sentido con el 1-1: con el 1-0 que
publica Wikipedia el empate **sí** le servía.

Y antes de creerle a nadie, la prueba de que no están copiando: de las **seis llaves** de
esas dos rondas, RSSSF reproduce **cuatro** dato por dato tal como las da la página, y
difiere sólo en estas dos. Una fuente derivada coincidiría en las seis.

#### Y una tabla que cierra puede no estar diciendo nada

El último partido del dataset que dos fuentes contaban distinto —`Platense` vs
`Estudiantes (BA)`, fecha 6 de la Primera B 2010-11, Wikipedia 1-1 contra el 0-0 de RSSSF
y de ESPN— parecía el caso más fácil de todos: **la tabla de la página cierra al gol en los
22 clubes con el 1-1**. Árbitro clásico, causa cerrada.

No. **RSSSF también cierra consigo misma**: su tabla final da `Platense 30-33` y
`Estudiantes 53-42`, que es exactamente su grilla con el 0-0. Las dos fuentes son
internamente coherentes, así que la aritmética no elige — y el G-E-P menos todavía, porque
el partido es empate en las dos versiones y lo único que se mueve son dos goles. Que una
tabla cierre prueba que la página no se contradice; **no prueba que la tabla sea un testigo
independiente**. Cuando las dos mitades derivan juntas, cerrar es exactamente lo que se
espera.

Lo que decidió fue **el historial de la propia página**. El artículo se editaba en vivo,
fecha por fecha, y dos revisiones separadas por veintiséis horas tienen el partido en el
medio:

| | Platense | Estudiantes |
|---|---|---|
| 30/08 03:30 UTC | Pts 4, PJ 5, G0 E4 P1, **2-4** | Pts 13, PJ 5, G4 E1 P0, **7-2** |
| 31/08 05:29 UTC | Pts 5, PJ 6, G0 E5 P1, **2-4** | Pts 14, PJ 6, G4 E2 P0, **7-2** |

Los dos suman un partido, un empate y un punto **y los goles no se mueven**. Eso es un 0-0,
anotado por el que estaba mirando esa misma noche. No hay que inferirlo de una suma
acumulada: el delta es cero y el partido que entró es uno solo. El gol de más apareció entre
el 4 y el 16 de septiembre de 2010 y se quedó en las dos mitades del artículo, que es *por
qué* la página de hoy cierra consigo misma.

Y el mismo delta fecha el partido: la tabla no lo tenía a las 00:30 del 30 y sí a las 02:29
del 31, así que se jugó el lunes 30 —el día que da ESPN, no el 31 de RSSSF, que es el que
quedó escrito—. Ese sigue abierto: corregir un día pediría un noveno tipo de corrección, y
no se agrega uno por una fila.

#### Diez de esas 61 no eran un desacuerdo: eran una fecha inventada

Antes de salir a buscar una tercera fuente conviene mirar de dónde sale la propia. Diez de
los 61 salían de acá: las tablas de llaves de ida y vuelta no traen columna de fecha, así
que el lector la saca del **título de la tabla**, y pedía «que nombre exactamente dos
días». `Cuarta fase - 2 y 9 de junio` nombra dos y son los dos días de partido.
**`Cuarta fase - 26 al 31 de mayo` también nombra dos, y no son dos días: son una
ventana.** Les ponía el 26 a las cuatro idas y el 31 a las cuatro vueltas.

Los días reales de esas cuatro llaves fueron **26, 26, 27 y 28** las idas y **30, 30, 30 y
31** las vueltas —el blog de José Carluccio las publica una por una, con sede y
goleadores—, o sea que de las ocho filas **tres caían bien y cinco llevaban un día que
nadie observó**.

La preposición es lo único que los separa, y los separa sin ambigüedad: `al` abre un
rango, `y` enumera. Y el corte no es una intuición, está medido sobre el corpus:

| forma del título | cuántos | de qué páginas |
|---|---|---|
| `X al Y` — un rango de 4 a 11 días | 6 | de donde salían casi todos los desacuerdos |
| `X y Y`, `X - Y` — dos días | 7 | del Argentino A 2004-05, **sin un solo desacuerdo** |

Separa exactamente al grupo que discute del que no. El repo ya tenía la regla escrita en
otro lado —`citadas` dice *«un rango no es una fecha, así que no se reparte»*— y acá la
rompía. Sacándolo, las ocho filas de esa fase quedan **8 de 8** contra el blog, y los
desacuerdos de día del dataset bajan de **61 a 51** sin que ninguna fila pierda su día:
la fuente que publica partido por partido las rellena, que es lo que corresponde.

**Y destapó una segunda cosa, que es la que casi se escapa.** Al quedarse sin fecha, esas
filas dejan de emparejar por `(par, fecha)` y el cruce cae en la rama que identifica por el
**marcador**… crudo. Los cuatro partidos de la Reválida de esa misma página tienen su
marcador arbitrado —la página dice `1-0` y el dataset escribe `1-1`—, así que `{0,1}` no
encontraba a `{1,1}` y el build volvía a denunciar los cuatro desacuerdos que dos pasos más
abajo están resueltos y declarados. Lo que identifica tiene que ser el marcador **que la
fila va a tener**, no el que la página escribió.

#### La página decía el día bueno y no lo leíamos: la nota de un `rowspan`

Con 46 desacuerdos de día en pie, lo que parecía faltar era **una tercera fuente**. Medido,
no: de los 46, **15 los explicaba la propia página**.

Cuando se suspende una tanda entera, la tabla no repite la fecha fila por fila — pone una
celda con `rowspan` y le cuelga la nota:

> `rowspan=3|12 de marzo {{refn|Suspendidos por las condiciones climáticas. **Se jugaron el
> 22 de marzo**, desde las 15:30.}}`

El lector ya sabía leer esa nota —`_fecha_de_la_nota` existe y está bien hecha— pero la
buscaba **sólo en el texto de la fila**. Con un `rowspan`, la nota vive en la primera fila
del grupo: la primera quedaba con el 22 y las otras dos con el 12. *El mismo partido de la
misma tanda, fechado con diez días de diferencia según dónde cayera.* Por eso la nota habla
en plural — cubre a las tres.

La celda original ya viajaba con el grupo, guardada sin limpiar para los penales; alcanzaba
con mirarla.

**Movió 65 filas en diez temporadas, y las 65 tienen una nota de la propia página que dice
exactamente el día al que se movieron** — verificado fila por fila contra el wikitexto,
porque la mayoría de esas filas no las mira ninguna segunda fuente y un error ahí sería
silencioso. Los desacuerdos de día bajaron de **46 a 34**.

De paso quedó medido de dónde sale nuestra fecha en los que quedan: **20 de los 34 son
Primera C 2008-2011, donde la página no publica el día** y nuestra fecha ya viene de RSSSF.
Ahí la disputa es RSSSF contra ESPN y Wikipedia no puede desempatar: haría falta una cuarta
fuente, no una tercera.

#### Y cuánto rinde ese testigo: 3 de 61

El historial arbitró un marcador. La pregunta obvia era si sirve para las **61
discrepancias de día** que el dataset arrastra —dos fuentes que dan el mismo partido en
días distintos—, porque si sirviera valdría la pena construir el mecanismo para escribir la
corrección. Se midió antes de construir nada, y la respuesta es **no**:

| | |
|---|---|
| llaves de eliminación, que no entran en ninguna tabla | 12 |
| páginas sin una sola revisión en la ventana del partido | 18 |
| corchete ilegible, o que no identifica el partido | 11 |
| **corchetes válidos** | **20** |
| de esos, los que deciden | **3** |

Tres de sesenta y una. El motivo es estructural: la cota **de arriba** es la única sólida
—si la tabla ya contaba el partido a las 02:29 de la madrugada, no se jugó esa tarde—, y
esa cota sólo puede descartar la fecha **más tardía**. Con dos candidatas separadas por un
día, que es el caso de 34 de las 61, casi nunca alcanza.

**Y el atajo que parecía duplicar el rendimiento resultó falso.** La cota *de abajo* —«a
las 00:30 la tabla no lo tenía, así que no se había jugado»— sumaría 15 casos, pero
depende de que el editor estuviera al día. Midiendo el atraso real de cada página, la
mediana de la Primera C 2024 es de **259 horas**: once días. Nueve de esos quince casos
están ahí, y aplicarles la cota de abajo les daría la razón a la otra fuente *porque el
editor era lento*, no porque el partido se hubiera jugado ese día. En el Argentino A
2012-13 la mediana es de 7,5 horas y ahí sí valdría. El atajo existe pero hay que
calibrarlo página por página, y con eso deja de ser un atajo.

**Una trampa del método, que casi se lleva puesto el resultado.** El primer predicado
buscaba la revisión donde `PJ_a + PJ_b` sube en dos. Esa suma sube en dos con *dos partidos
cualesquiera* de esos clubes —A jugando dos veces, o A y B cada uno contra otro rival—, no
con el partido entre ellos: en la Primera C 2024, con fechas cada tres o cuatro días,
enganchaba la fecha 12 y contestaba sobre la 13. Daba **8 de 61**, y seis de esas ocho eran
sobre el partido equivocado. Lo destapó que dos casos devolvieran un corchete *anterior a
las dos fechas candidatas*, que es imposible. El predicado ahora pide que suban **los dos
clubes en la misma edición** y que la transición caiga en la jornada del partido; con eso,
1 de los 21 corchetes se descarta por incoherente y el resto queda auditado.

#### Y lo dijo una tercera vez: la nota que se define una vez y se referencia por nombre

Con 34 desacuerdos en pie, la `Primera C 2024` aportaba cuatro. Al abrir el wikitexto, dos
de ellos estaban así:

> `|15 de abril {{refn|group=n.|name=tres}}`

Una nota **vacía**. MediaWiki deja definirla una sola vez y referenciarla después por
nombre; al renderizar, las tres filas del grupo muestran el mismo texto, pero en el
wikitexto crudo dos de las tres no dicen nada. El cuerpo vive en la tercera:

> `{{refn|group=n.|name=tres|Suspendidos por las condiciones climáticas. **Se jugaron el 17
> de abril**, desde las 15:30}}`

Es **la misma forma que el `rowspan`** —una nota, varias filas, una sola con el texto— por
otro mecanismo, y con la misma consecuencia. Se resuelve como ya se resolvía la ambigüedad
de los rótulos de zona: juntando las notas de la **página entera** antes de leer ninguna
fila. Tiene que ser de la página y no de la tabla, porque la definición y la referencia no
tienen por qué caer en la misma, y desde adentro de una tabla una nota referenciada es
indistinguible de una que no existe.

Medido sobre el corpus: `31` referencias por nombre, `28` con el cuerpo en la misma página,
**`5` cuyo cuerpo dice cuándo se jugó**. Movió cinco filas y cerró **cuatro** desacuerdos.

**La quinta no estaba en disputa, y es la que mejor lo prueba.** En la `Primera C 2018-19`,
`Deportivo Armenio` vs `Cañuelas` y `Argentino de Quilmes` vs `Sportivo Italiano` **cuelgan
de la misma nota** —una la define, la otra la referencia— y estaban fechados con diecisiete
días de diferencia. Ahora los dos dicen 28 de noviembre. Ninguna segunda fuente lo había
denunciado: era un error silencioso que el propio artículo contradecía.

Las otras tres referencias por nombre no tienen cuerpo en su página: apuntan a notas de
otro artículo. Ésas se dejan como están.

#### Los que no eran un error de nadie: dos convenciones para un mismo partido

Tres de los desacuerdos que quedaban tenían una forma distinta, y aparecieron juntos al
preguntarle al corpus algo muy concreto: *¿cuántos de estos partidos tienen una nota de
completado que nombre justo la fecha de la otra fuente?* Eran **3 de 34**.

Los tres son partidos que **empezaron un día y se completaron otro**. `Claypole` vs
`Berazategui`, suspendido a los 36 minutos por incidentes y completado seis semanas
después; `Gimnasia y Esgrima (J)` vs `Atlético de Rafaela`, a los 15 minutos por un corte
de luz; `Quilmes` vs `Gimnasia y Esgrima (M)`, en el entretiempo, completado a puertas
cerradas en cancha de Platense. RSSSF lo publica en dos renglones, que es la lectura más
clara que hay:

> `[Sep 24, Tue] CA Claypole  -  AD Berazategui   abandoned at 0-0 in 35m`
> `[Nov  6, Wed] CA Claypole 0-2 AD Berazategui   remaining 55m`

Ninguna de las dos fechas está mal: el repo usa la del día en que empezó y la otra fuente
usa la del día en que se completó. Y eso **ya estaba decidido**, por escrito, desde antes
—`_SE_JUGO` deja `completó`, `reanudó` y `terminó` afuera a propósito, y son **105**
partidos—. Lo que faltaba era reconocer el caso al verlo.

**La trampa, que casi se lleva puesto uno de los tres.** El de Jujuy estuvo a punto de
entrar como *corrección de fecha*: Transfermarkt publica la ficha con `Sat, 18/03/23` y
betexplorer da lo mismo, así que parecían tres fuentes contra una y el criterio de mayoría
decía corregir. Las tres fechan por el día en que se completó. **Contar cuántas fuentes
dicen cada cosa no sirve cuando no están midiendo lo mismo** — y con 105 partidos del mismo
tipo tratados al revés, corregir ése habría metido una inconsistencia, no un arreglo.

#### `Dia`, el tipo que sí toca el dato

Quedaron dos casos donde nuestra fecha estaba mal de verdad, los dos de la `Primera B
2010-11`, y los arbitra el historial de la propia página —que acá es un tercero: nuestra
fecha viene de RSSSF y quien discute es ESPN, así que Wikipedia no es parte—. Uno de los
corchetes es de **treinta y nueve segundos**.

`Dia` es el hermano de `Fechado` que reescribe la fecha, y por eso pide más:

- **Una fuente tercera, con su URL suelta**, que además va al `source` de la fila. Si la
  fecha la puso esta declaración, dejar acreditando a quien la tenía mal sería escribir en
  el dataset una procedencia falsa.
- **La fecha que esperaba encontrar.** La fecha que se pisa la escribe un completador, y un
  completador se puede arreglar solo. El día que RSSSF publique una fe de erratas, esta
  declaración deja de enganchar y avisa, en vez de pisar en silencio una fecha ya correcta.
- **Se aplica al final**, después de los completadores y no en `aplicar` como las demás: la
  fecha que hay que pisar muchas veces todavía no existe cuando `aplicar` corre.
- Y entra a la lista de verificados con **tres campos y no con cinco**, porque la propia
  corrección fabrica un desacuerdo nuevo: al mover la fila al día bueno, la fuente que la
  tenía mal pasa a discrepar con la nueva.

**Una lección que costó.** Las primeras siete declaraciones incluían cuatro de la
`Primera C 2024` que **compartían el texto de la justificación** —el temporal del 12 de
marzo—. El texto era correcto para una de ellas. Las otras tres hablaban de partidos de
abril y de septiembre, y compartir el `porque` las volvió invisibles: leerlo no delataba
nada, porque lo que estaba mal no era el texto sino a quién se le había pegado. Las cuatro
se fueron: tres las resolvió el parser y una era el choque de convenciones. Hoy sólo se
comparte **la regla**, y cada entrada guarda su evidencia propia.

#### Los 20 de la Primera C: la cuarta fuente ya estaba adentro

Quedaba un bloque duro: **20 partidos de la `Primera C` 2008-2011 con dos días distintos**,
donde la página no publica el día, nuestra fecha sale de RSSSF y quien discute es ESPN. Sin
un tercero, no hay con qué decidir.

**Primero se midió si el problema era nuestro.** Cinco hipótesis, las cinco cerradas con un
número:

| | |
|---|---|
| RSSSF da una fecha por jornada y la repartimos | falso: parte el **91%** de las jornadas en 2 a 4 días |
| los 20 caen donde RSSSF *no* partió | falso: **50%** vienen de tandas grandes contra un **61%** de base |
| las jornadas de un solo día son poco fiables | falso: ESPN confirma **8 de las 10** exactas |
| leemos mal la hora de ESPN, que viene en UTC | ya estaba resuelto, y documentado, en `fad/espn.py` |
| ESPN duplica pares y elegimos el equivocado | falso: los 39 pares repetidos son revanchas del reducido, y **ninguno** es de los 20 |

Y se calibraron las dos fuentes contra las páginas que **sí** publican el día: RSSSF acierta
`588/593` (99,2%) y ESPN `1596/1602` (99,6%). Parece que ESPN gana, pero **no hay una sola
página donde estén las dos**: son corpus distintos, de épocas distintas. Con eso no se
prefiere a nadie. Sobre las tres temporadas las dos coinciden en `1068` de `1095` y difieren
en `21`, que es el tamaño real del problema.

**La cuarta fuente estaba en el repo desde antes.** `fad/citadas.py` acredita el compendio
`historiayfutbol` de José Carluccio para el Argentino A 2004-05. Publica también las tres
temporadas de `Primera C`, partido por partido, y nadie lo había mirado para esta categoría.

Antes de creerle se lo midió, que es lo que separa una fuente de una opinión:

- **`1132`** partidos leídos de los 1140 —los 8 huecos son erratas de la propia fuente—.
- **`1035` de `1038` marcadores** coinciden con los que publica Wikipedia: **99,71%**. Eso
  es lo que verifica que habla de los mismos partidos.
- **No es un espejo.** Tiene tres errores de marcador propios, que una copia no tendría. Y
  en los 21 desacuerdos le da la razón a ESPN en 19 y a RSSSF en 2: un espejo de ESPN daría
  21 a 0. Un verificador adversarial hizo el cruce completo de la 2008-09 contra RSSSF y
  obtuvo `361/371`.

**Y hay un límite, dicho:** es una compilación de 2014-2015, posterior a RSSSF y a ESPN. Se
probó que no las copia; no se puede probar que nunca las miró.

#### Los cuatro que tienen testigo de la época

Por eso las que se pudieron apoyar en prensa contemporánea lo dicen, y son las más firmes.
Estas cuatro se leyeron verbatim:

- **`Villa Dálmine` vs `Argentino de Rosario`** — El Viola, el sitio del club, publica la
  tabla de la temporada con la fecha **declarada**: `26 | 08/03/2009 | Villa Dálmine | 2 |
  1 | Argentino de Rosario`. En los otros 40 partidos de Villa Dálmine de esa temporada
  coincide con RSSSF; se aparta sólo en éste.
- **`Excursionistas` vs `Luján`** — los dos blogs del club publicaron la programación
  *antes*: «Programación confirmada / Fecha 28 / **Sábado 21/3** - 15:00h. / Árbitro: Ramiro
  López». El día está escrito, no deducido.
- **`Luján` vs `Barracas Bolívar`** — el blog Rumores del Ascenso lista los resultados
  agrupados por día: «PRIMERA C: **VIERNES**: … LUJÁN 1 BARRACAS BOLÍVAR 0». Los otros dos
  de esa lista ya los teníamos fechados el viernes 9.
- **`Excursionistas` vs `Barracas Bolívar`**, que además *explica* el desacuerdo: el club
  publica «Fecha 38 / **Sábado 30/5** - 14:00 hs.», después «:: PARTIDO SUSPENDIDO», y
  después «Fecha 38 - **REPROGRAMADO POR SUBSEF** / **Lunes 1/6** - 15:00 hs.». **RSSSF se
  quedó con el día programado.**

Ese último caso obliga a una distinción que es fácil pasar por alto y se resuelve **al
revés** según cuál sea: un partido que **se posterga entero** lleva el día en que se jugó;
uno que **empieza y se completa después** lleva el primero. `Excursionistas` vs `Argentino
de Merlo` es del segundo tipo —empezó el 18/8, se suspendió a los 25 minutos y se completó
el 3/9— y por eso nuestra fecha ahí estaba bien: va como `Fechado` y no como `Dia`.

**Resultado: 18 `Dia`, 2 `Fechado`.** El único que cae para nuestro lado es
`Defensores de Cambaceres` vs `Argentino de Merlo`, y vale escribirlo justamente porque si
el compendio nos hubiera contradicho en los veinte sería indistinguible de una copia de
ESPN.

Los desacuerdos de día quedaron en **`4`**, en tres páginas, y ninguno es de Primera C.

#### Lo que se probó y no sirvió

Vale dejarlo escrito para que nadie lo vuelva a caminar:

- **El historial de Wikipedia**: 604 revisiones de las tres páginas, bajadas enteras.
  Ninguna publicó nunca el día. Y las secciones de resultados aparecieron en 2012-2013
  **citando a RSSSF**, así que además habría sido contar su voto dos veces.
- **Soccerway/Flashscore**: tiene las tres temporadas con fecha por partido, y parecía el
  mejor candidato. Publica la fecha **en UTC**: de cinco partidos de prueba, tres estaban
  corridos un día. Sirve, pero hay que convertir el timestamp, no leer la fecha.
- **La fixture oficial de AFA**, rescatada de la Wayback Machine. Es la fuente primaria y
  parecía inmejorable, pero es un **plan publicado antes**: para `Luján` vs `Barracas
  Bolívar` anunciaba el 11 de octubre y el partido se jugó el 9. Un listado de resultados
  posterior le gana a un fixture anterior.
- **Promiedos** sólo guarda la temporada en curso.

#### Los últimos cuatro, y el número que estaba escrito al lado de una lista

Quedaban cuatro desacuerdos sueltos, uno por página, y los cuatro los cerró **la misma
fuente**: el compendio de Carluccio, que a esta altura ya no era una apuesta sino algo
medido. Vale contarlos porque cada uno tiene una forma distinta.

**`Cipolletti` vs `Gimnasia y Esgrima (CdU)`, `Argentino A 2012-13`.** Este no hacía falta
buscarlo: el comentario que ya estaba en `fad/correcciones.py` decía *«RSSSF corre **las
cinco** un día para atrás»* y debajo había **cuatro** declaraciones. La quinta se siguió
denunciando en cada corrida hasta que alguien fue a mirarla. Un número escrito al lado de
una lista es un invariante gratis, y éste estuvo desmintiéndose solo un buen rato.

**`Flandria` vs `Colegiales` y `Almagro` vs `Barracas Central`, `Primera B 2010-11`.** Los
dos con el mismo argumento, y es más fuerte que «una fuente dice otra cosa»: el compendio
**no usa nuestro día en toda la jornada**. La Fecha 14 la parte en 15, 16, 18 y 19 de
octubre —el 17 no aparece— y la Fecha 36 en 22, 23, 24 y 26 de abril —sin el 25—. No es que
la fuente ponga el partido en otro de los días de la fecha: es que ese día no es de la
fecha. Los dos se corrigen.

**`Ferro Carril Oeste` vs `Independiente Rivadavia`, `Primera B Nacional 2007-08`.** Acá
nuestra fecha es la de la propia página y quien discute es worldfootball, que da el
**29 de febrero**. 2008 fue bisiesto, así que el día existe y no es un error de calendario
—que es lo primero que uno sospecha—. Lo que pasa es otra cosa: el compendio pone dos
partidos el 28 (éste y `Quilmes` vs `Platense`) y **uno el 29, que es otro**,
`Ben Hur` vs `Almagro`. worldfootball no inventó un día: corrió este partido al de al lado.

**Con esto los desacuerdos de día quedan en cero.** Eran `61` cuando se empezaron a mirar.
Ninguno se cerró eligiendo la fuente más prestigiosa: se cerraron leyendo mejor la página
—el `rowspan`, el rango, la nota con nombre—, reconociendo dos convenciones que no se
contradicen, o trayendo un tercero y midiéndolo antes de creerle.

#### Las cuatro tablas de la temporada en curso: la equivocada era la tabla

Quedaban cuatro filas de tabla que no cerraban con la grilla, y las cuatro de temporadas
**todavía en juego**. Dos se resolvieron sin salir de la página; las otras dos parecían
pedir una crónica y terminaron pidiendo otra cosa.

**`San Miguel`, Primera Nacional 2026.** La tabla le da `GF19`; nuestra grilla, `GF20`. Y la
propia tabla lo demuestra: sus dos columnas de goles suman **905 y 906** sobre los mismos
partidos, y tienen que dar igual. Sobra un gol en contra que ningún club declara haber
convertido, y es exactamente el que le falta a esa fila.

**`Muñiz`, Primera C 2026.** Acá no se desvían los goles sino el G-E-P: la tabla dice
`4-11-10` y la grilla `4-10-11`, **con los goles coincidiendo exacto en 17:26**. Un marcador
mal leído mueve siempre los goles; si los goles coinciden y el reparto no, ningún partido
puede explicarlo.

**`Real Pilar` y `San Martín (B)`, Primera B 2026 — el par que casi pasa.** Real Pilar tiene
2 goles a favor de más en nuestra grilla y San Martín (B) 2 en contra de más: la firma
exacta de un partido entre ellos mal leído. Y lo que hace **invisible** al par es que las
dos tablas cierran consigo mismas — bajar dos goles a favor de un club y dos en contra de
otro deja los totales iguales, 688 contra 688 y 690 contra 690. La suma no denuncia nada.

Pero no hay tal partido. La tabla publica también el G-E-P y **coincide con el nuestro**
—`14-9-9` y `9-13-10`—, así que ningún resultado cambia de ganador; y los dos cruces entre
ellos son `San Martín (B) 1-2 Real Pilar` y un `0-0`. Quitarle dos goles a Real Pilar en el
primero lo convierte en derrota, que contradice el G-E-P de la propia tabla, y del segundo
no hay dos goles que quitar. **La aritmética descarta la explicación que la aritmética
sugería.**

**Y las cuatro las confirma la misma fuente de afuera.** Para la temporada en curso el
árbitro natural es Promiedos —y el único posible: su archivo sólo guarda la temporada que se
está jugando, que es justo lo que acá hace falta—. Coincide **exacto** con nuestra grilla en
las cuatro:

| | Wikipedia | nosotros | Promiedos |
|---|---|---|---|
| San Miguel | GF19 GC28 | GF20 GC28 | `20:28` |
| Real Pilar | GF34 GC31 | GF36 GC31 | `36:31`, 51 pts |
| San Martín (B) | GF31 GC32 | GF31 GC34 | `31:34`, 40 pts |
| Muñiz | 4-11-10 | 4-10-11 | `4-10-11`, 22 pts |

Muñiz tiene además un testigo aritmético: la plantilla de la tabla calcula los puntos sola,
y con `g=4|e=11|p=10` muestra **23**. Promiedos publica **22**, que es lo que sale de nuestro
`4-10-11`. La tabla se contradice con el número que ella misma publica.

**Un detalle de método que casi arruina la comparación.** Promiedos ya tenía jugada una fecha
que la página todavía no cargaba, así que seis clubes tenían `PJ 32` de un lado y `31` del
otro. Comparar goles acumulados entre dos cortes distintos del calendario da una diferencia
que no es error de nadie. Sólo se compararon los clubes con el **mismo PJ en las tres
partes**.

**Lo que este trabajo deja abierto.** Éstas son las primeras `Revisado` sobre páginas
**vivas**: las 56 anteriores son de temporadas cerradas, donde la tabla ya no se mueve. Y
`Revisado` se identifica por (página, club) y nada más: si la tabla se arregla, la guarda de
huérfanos avisa, pero si aparece un desvío *distinto* en el mismo club, la declaración vieja
lo tapa en silencio. Es el hueco que `Fechado` y `Dia` ya cierran guardando el estado que
verificaron, y que `Revisado` todavía no.

#### Una verificación que no dice de qué habla puede tapar otra cosa

Las cuatro tablas de la temporada en curso dejaron un pendiente y vale cerrarlo acá porque
el arreglo se encontró a sí mismo un problema.

`Revisado` se identificaba por **(página, club) y nada más**. Con temporadas cerradas eso
alcanza: la tabla ya no se mueve, así que el desvío que se verificó es el único que puede
haber. Con una página en curso no: si al mismo club le aparece un desvío **distinto**, la
declaración vieja lo tapa —engancha por nombre— y nadie se entera. `revisados_huerfanos`
sólo veía la otra mitad, la fácil: que el club dejara de desviarse.

Es el hueco que `Fechado` y `Dia` ya cerraban a su manera —el uno guarda las dos fechas en
disputa, el otro exige `dice`—, y la solución es la misma: **que la declaración diga de qué
estado habla**.

**Lo que se fija es la diferencia, no los números.** Es todo el asunto: en una página viva
la fila entera cambia cada fecha —sube el PJ, suben los goles—, así que fijar la fila haría
caducar la declaración todas las semanas y el aviso volvería sin que nada esté mal. Lo que
*no* cambia mientras la errata siga ahí es cuánto y en qué se aparta la tabla. `GF-2` sigue
siendo `GF-2` la fecha que viene.

Las **58** declaraciones de tabla que ya existían se midieron, no se tipearon: 58 diferencias
de seis campos escritas a mano son 58 oportunidades de una errata que después no encuentra
nadie. Salen agrupadas así —`GF-1` siete veces, `GC-1` seis, `PJ+1 GC+1 P+1` cinco— y las
dos de llave quedan afuera, porque verifican un cruce del cuadro y ahí no hay columnas que
firmar. Un test exige que ninguna de tabla se escriba sin su firma.

**Y hay un quinto llamador que pregunta otra cosa.** `build.la_fuente_se_respalda` cruza la
tabla de RSSSF contra los partidos de RSSSF: otra tabla, otro conjunto, así que la firma de
nuestro desvío contra Wikipedia no significa nada ahí; lo único que quiere saber es si ese
club ya tiene una conclusión escrita, para no repetirla. Se aprendió rompiéndolo — al poner
firma en las 58, ese llamador dejó de enganchar y volvió un aviso que ya estaba explicado.
Lo agarró su test.

#### Y a los cinco minutos de existir, la firma encontró algo

Al medir, apareció **un aviso nuevo** donde no debía haber ninguno: el chequeo de PJ
denunciaba a `La Florida` y `Sportivo Patria` en el **Torneo Apertura** del Argentino A
2005-06. Ese aviso lo venía callando el `Revisado` de esos clubes… que habla del desvío del
**Clausura**. Una verificación tapando otra cosa, que es exactamente lo que el campo vino a
impedir.

La causa estaba dos capas más abajo. El `Dividido` de `La Florida` vs `Sportivo Patria` —el
partido abandonado a los 90' y dado por perdido a los dos— no declaraba su sección, y
`clubes_divididos` lee eso como *«la página tiene una sola tabla»*: le aplicaba la
consecuencia al Apertura **y** al Clausura. Pero el anulado es el del Clausura, y en el
Apertura esos mismos dos clubes juegan **otro** partido, que está escrito y cierra perfecto.
Así que en el Apertura el chequeo esperaba un hueco que no existe.

Se arregla declarando la sección. Los avisos quedan en los mismos `166` de antes: el
mecanismo es neutro sobre el estado de hoy, que es lo que tiene que ser.

#### Los 16 que no cierran, ordenados

Vale separarlos, porque no son un problema sino tres, con costos muy distintos.

**Cinco tienen un solo club desviado.** Ahí no hay nada que corregir: un marcador mal
leído toca siempre a **dos** clubes, así que un club solo y sin pareja no puede venir
de un partido. La equivocada es su fila de la tabla. Son Platense en la B Nacional
2009-10 —el caso que enseñó el patrón—, más Boca Juniors en el Clausura 2005, Unión en
el Final 2013, Racing Club en la Copa de la Liga 2023 y Deportivo Español en la
Primera B 2017-18.

Eso era un razonamiento, y tenía un agujero que había que tapar antes de creerle: el
árbitro **saltea** a los clubes cuyo PJ no coincide, así que el socio del desviado
podía estar afuera de la comparación y el club sólo parecer solo. Se midió: en los
cinco torneos se compararon **todas** las filas, cero salteados y cero huérfanos. El
agujero no estaba.

Y después apareció algo mejor que un razonamiento. **Todo gol convertido es un gol
recibido por alguien**, así que en una tabla que cubre un conjunto cerrado de partidos
la columna GF y la columna GC tienen que sumar lo mismo. **Cuatro de las cinco no
suman lo mismo**, y el desbalance es clavado el delta del club desviado:

| torneo | club | ΣGF | ΣGC | sobran |
|---|---|---|---|---|
| Clausura 2005 | Boca Juniors | 514 | 517 | 3 en contra |
| Final 2013 | Unión | 435 | 436 | 1 en contra |
| Copa de la Liga 2023 | Racing Club | 388 | 389 | 1 en contra |
| Primera B 2017-18 | Deportivo Español | 652 | 653 | 1 en contra |

No es una comparación contra nuestra grilla ni contra ninguna otra fuente: es la tabla
contradiciéndose sola. Hay goles recibidos que **ningún club declara haber
convertido**. Ahí no queda nada que arbitrar.

Platense es el que sobrevive al chequeo, y por el motivo que lo hizo el arquetipo: su
error de tipeo baja **las dos** columnas de la misma fila (la tabla dice GF39 GC40 y
sus 38 partidos dan 40 y 41), así que la resta se cancela y el total de la liga sigue
cerrando. El balance es ciego a esos, a propósito. Para eso está el cruce.

El más raro era Boca, porque tres goles es mucho para un tipeo y porque además su fila
cambia un **resultado**: la tabla le pone 6-4-9 y los partidos dan 7-4-8. Se fue a
buscar afuera y RSSSF publica la fila idéntica a la de Wikipedia —`19 6 4 9 26-30 22`—,
que parecía darle la razón a la tabla. Pero sumando sus veinte filas, **RSSSF tiene el
mismo desbalance de 3**: no es un testigo independiente, es el ancestro del error. Y de
paso regala el argumento que faltaba: su columna GF suma 514, que son *exactamente* los
goles de nuestra grilla. Si Boca hubiera recibido tres goles más, algún rival los habría
convertido y su GF sería tres más alto. Ninguno de los diecinueve los reclama. Los tres
goles no los hizo nadie.

> **El infobox no es un testigo, salvo cuando contradice.** Se había usado el «462
> partidos, 984 goles» de la B Nacional 2013-14 como comprobante gratis, y ahí valía
> porque *discrepaba* de la tabla. Cuando coincide no prueba nada, porque sale de ahí: el
> infobox del Clausura 2005 dice 517 goles, que es la suma de la columna GC **rota**, no
> los 514 que hay en la cancha. Quien lo escribió sumó una columna de la misma tabla.

Aun si uno quisiera corregir la grilla, no podría: para Boca hay **siete** partidos que
encajan con el desvío y para Deportivo Español **once**. *Localizar no es arbitrar*, y
acá ni siquiera localiza.

El chequeo quedó permanente en `posiciones.desbalance`, al lado del cruce. Sólo opina
si la tabla reclama exactamente el mismo conjunto de partidos que la grilla —mismos
clubes de los dos lados y mismo PJ—, porque sin esa guarda sería un generador de ruido:
una fila descartada por no cerrar sola, o una zona con partidos interzonales como la
Copa de la Liga 2023, descuadran el total sin que nadie esté equivocado. Con la guarda
puesta, sobre los 131 torneos denuncia esos cuatro y **ningún falso positivo**.

**Ocho tienen todos sus desvíos apareados.** Cada par localiza un partido: los dos
clubes se cruzan, y a uno le sobran los goles que al otro le faltan. Pero *localizar
no es arbitrar*, y hay dos cosas que lo empeoran.

La primera: en una liga de ida y vuelta los dos clubes se cruzan **dos veces**, y la
aritmética no puede decir cuál de las dos fechas es la mala. De los 26 pares del
dataset, sólo cuatro identifican un partido único.

La segunda apareció al mirarlos de cerca, y obligó a rehacer la cuenta. **Cuando tres
o más clubes comparten el mismo delta, el apareo es degenerado**: si Douglas Haig y
Las Parejas tienen los dos `+1 GF −1 GC`, y Independiente (C) y Unión (S) los dos
`−1 GF +1 GC`, hay cuatro maneras de emparejarlos y la aritmética no prefiere ninguna.
Con sólo dos clubes desviados el par está forzado aunque compartan delta, porque no
hay con quién más.

Contando así hay **tres torneos genuinamente degenerados** —la B Nacional 2011-12, la
Primera Nacional 2021 y el Federal A 2023— y el resto son pares forzados. Vale decirlo
porque la primera versión de este párrafo contaba los cuatro emparejamientos posibles
del Federal A como cuatro hallazgos, y son uno solo sin resolver.

Los seis pares forzados que había se probaron contra la prensa, y el reparto es el que
ya venía saliendo: **dos correcciones, tres veces la tabla equivocada, una sin
decidir.** Los dos corregidos salieron de la lista; los otros cuatro siguen adentro
como avisos abiertos, que es lo que corresponde cuando el error es de la fuente y no
nuestro.

| | |
|---|---|
| Primera Nacional 2023 | Aldosivi 0-0 → **1-1** Villa Dálmine — **corregido** |
| Primera C 2015 | Argentino de Merlo 0-2 → **1-2** Cañuelas — **corregido** |
| B Nacional 2013-14 | los dos partidos confirmados: la tabla le pone 4 goles de más a Brown |
| Primera C 2015 ×2 | Talleres (RdE)/Argentino de Quilmes y Central Córdoba (R)/Sacachispas, igual |
| Primera C 2015 | Laferrere/Dock Sud: **sin decidir**, y por un motivo interesante |

El de la B Nacional 2013-14 trae un testigo que no habíamos usado y que es gratis: el
**infobox de la propia página** dice «462 partidos, 984 goles». La grilla suma 984; la
tabla, 988. La página se contradice sola y el lado que queda solo es la tabla.

Y el de Laferrere destapó otro Clausura 2007: la prensa no da marcador final **porque
el partido no terminó**. Se abandonó a los 73 minutos, 1-1, por incidentes de la barra
con la policía —catorce policías heridos, el plantel de Dock Sud atrincherado en el
vestuario—. Wikipedia publica 2-2 y la página tiene una nota al pie del Tribunal de
Disciplina. Ninguna de las cuatro crónicas nombra goleadores: son todas policiales. Sin
eso no se toca, pero queda dicho que el 2-2 no es un marcador de cancha.

Van **veinte** casos probados contra la prensa: la tabla acertó en catorce, se
equivocó en cinco, y uno quedó abierto. Los cinco últimos —los dos del Clausura 2008 y
los tres de la Primera Nacional 2019-20— le dieron la razón a la tabla. Eso no cambia
la moraleja, la refuerza: la tabla acierta bastante más de lo que falla, y justamente
por eso es tan tentador creerle siempre. Falla una de cada cuatro veces, y no avisa
cuál.

**Siete tenían algún club sin pareja.** Eso significa más de un error en la misma
página, o un error de tabla mezclado con uno de partido. Eran los caros: el Federal A
2021, el 2022, la Primera Nacional 2019-20 y 2026, la Primera C 2011-12 y 2026, y el
Clausura 2008.

Al abrirlos apareció algo que el apareo de a dos **no puede ver**. Un club puede tener
más de un partido mal leído, y entonces sus desvíos se suman en una sola fila y ya no
aparean con nadie: queda huérfano sin que la página tenga más de un tipo de error. Es
exactamente lo que pasaba en la **Primera Nacional 2019-20**, el caso más extremo del
dataset: Belgrano con `GF+9` y tres clubes con sólo goles en contra de más —Platense
+4, Agropecuario +3, Morón +2— sumando 9 clavados. No eran cuatro huérfanos: era un
club con **tres** partidos mal leídos, los tres de visitante y los tres de la primera
rueda.

Y ahí apareció el testigo interno que los volvía únicos, que estaba en la misma página
y no se había usado nunca: la **tabla parcial de la primera rueda**. Contra la tabla
final sola, la aritmética admite repartir el ajuste entre la ida y la vuelta; la
parcial confina los desvíos a una rueda y deja un solo cruce posible por club. Los
cruces de la segunda rueda tienen además su propia síntesis, que los confirma como
están.

El **Clausura 2008** salió por otro lado, y es el hallazgo que más me gustó del grupo:
no es un error de nadie, es **daño de edición**, y se puede seguir en el historial de
la propia Wikipedia.

| revisión | Gimnasia (J)–Estudiantes | Lanús–Banfield | Racing–Estudiantes |
|---|---|---|---|
| 2021-10-09 · `138916082` | `0 - 2` | `0 - 5` | `0 - 2` |
| 2021-11-19 · `139838699` | `- 2` | `- 5` | `- 2` |
| 2022-09-15 · `145987834` | **`1 - 2`** | **`1 - 5`** | **`1 - 2`** |

Una edición que normalizaba ceros a la izquierda en toda la página (`01.º` → `1.º`,
`pos=01` → `pos=1`) se comió de paso el `0` del local en las líneas de marcador donde
el local no había convertido. Diez meses después, otra edición comentada
«Mantenimiento» rellenó los huecos, y en tres de ellos escribió `1`. **El 1 no viene
de ninguna fuente: es un dígito repuesto a ojo sobre un dato que Wikipedia había
roto.** El de Lanús ya lo arregló alguien y hoy vuelve a decir `0 - 5`; por eso
desviaban tres clubes y no cinco. Los otros dos se corrigieron acá, con ESPN e
historiayfutbol nombrando a Enzo Pérez y Luguercio, y —en el de Racing— con el 0-2 que
además es el resultado **homologado**: el partido se suspendió a los 78' y el Tribunal
lo dio por ganado a Estudiantes, igual que el Newell's–River de 2007.

El **Federal A 2021** cerró entero con dos correcciones, y una de ellas dejó una
lección sobre cómo se descarta una fuente. Su único testigo era una nota de La Nueva de
Bahía Blanca, y el slug de la URL decía *«…ven acción esta tarde por la fecha 22»*: una
previa, publicada a las 06:00, antes de los partidos. Parecía descartable. Las capturas
de Wayback mostraron otra cosa: la temprana tiene `datePublished` igual a `dateModified`
y título de previa; la posterior tiene `dateModified` a las 22:32 del mismo día y el
título reescrito como crónica. **El diario reutilizó la nota y dejó el slug viejo.** No
alcanzaba con mirar la URL, había que mirar los metadatos de las dos capturas.
Aparecieron además dos testigos mejores, uno de ellos del diario de la ciudad del club
local, con fotógrafo propio en la cancha.

La **Primera C 2011-12** cerró su par —Villa Dálmine 1-0 → 0-1 Cambaceres— con cuatro
crónicas de tres redacciones distintas, y con un detalle que explica el error sin
suponer mala fe: la celda de Wikipedia se cargó a las **19:15**, menos de dos horas
después del final y *antes de que se publicara una sola crónica*. Una IP la tipeó de un
marcador en vivo y la puso al revés; desde entonces la página dijo `1 - 0` y nunca otra
cosa en catorce años. Vale subrayar que acá **la aritmética no señalaba ese partido**:
hay siete arreglos de dos partidos que reproducen las mismas columnas. La corrección se
apoya enteramente en las crónicas, que es como tiene que ser.

Aplicadas las nueve correcciones, cuatro de esos siete torneos salieron del grupo y
quedan **tres**: la Primera C 2011-12 —que cerró su par pero conserva un trío sin
resolver— y las dos temporadas en curso, Primera Nacional 2026 y Primera C 2026, que
son otra cosa y están abajo.

##### El Federal A 2022, o la trampa del Clausura 2005 dada vuelta

Este merece párrafo propio porque **cambió de veredicto al auditarlo**, y por el motivo
más incómodo posible.

Se habían encontrado dos correcciones acopladas, las dos con crónica. La segunda —San
Martín (F) 2-2 → 0-0 Central Norte (S)— tenía como testigo una nota de **Ascenso del
Interior**. Y la página de Wikipedia cita a ese sitio seis veces. La primera revisión
dijo «riesgo bajo»: las citas eran de formato y fechas, y las tablas de posiciones no
llevan `<ref>`. Pero *ausencia de cita no es ausencia de procedencia*.

ADI publica sus tablas **como imágenes de imgur** —por eso nadie las había leído nunca—.
Bajando la captura de Wayback del 07/11/2022 y leyendo la imagen, los diecisiete equipos
de su Zona B coinciden **dígito por dígito** con la tabla final del artículo. No parecida:
idéntica. Y la captura del 23/05/2022, contra la grilla acumulada, difiere en exactamente
dos equipos, los dos por `−2/−2`.

O sea que para esa corrección la crónica, la tabla publicada, la tabla en vivo y la
aritmética **son un solo testigo contado cuatro veces**. Es la misma trampa que RSSSF en
el Clausura 2005, invertida: allá una fuente externa replicaba el error de Wikipedia;
acá Wikipedia replica la tabla de la fuente externa. Sin un relato del 03/04/2022 ajeno
a ADI, ese partido **no se toca**.

La otra corrección sí entró, sola: Misiones Online publicó su crónica del Crucero 3-1
San Martín a las 17:37 del 24/08/2022, con los cuatro goles, y la celda de Wikipedia se
tipeó **nueve horas después**. No puede ser su ancestro. Eso deja la página sin cerrar a
propósito, y con un residuo más informativo que el que tenía: donde había tres clubes
desviados y ningún par, ahora hay **un par limpio y forzado** que apunta justo al partido
que queda abierto.

##### Las dos en curso son otro problema

La **Primera Nacional 2026** y la **Primera C 2026** están jugándose, y ahí hay que
tener cuidado con una tentación: dar por errónea una tabla que sólo está
desactualizada. Se separan los dos fenómenos.

En la Primera Nacional 2026 la tabla tiene **dos filas atrasadas** —Nueva Chicago 23
partidos contra 24, San Martín (SJ) 22 contra 23—, y ésos son exactamente los clubes
que el árbitro saltea. Eso abre el agujero de siempre: el socio del desviado podría
estar afuera de la comparación. Se comprobó y no está: **Los Andes no juega contra
ninguna de las dos filas atrasadas**, y el único cruce de Racing (C) con San Martín
(SJ) fue un 0-0, donde no hay gol que esconder. Los dos son casos genuinos de club
solo, y la tabla les queda un gol corta a cada uno. La suma lo confirma: la tabla
desbalancea en −2, y sumándole un gol a favor a cada uno de los dos, cierra exacto.

Con la reserva de que ese último argumento no es una prueba acá: con dos filas
atrasadas, el conjunto de partidos que declara la tabla no es el mismo que el de la
grilla, así que el balance podría descuadrar por el atraso y no por un dato malo. Por
eso `posiciones.desbalance` **se calla** en esta página, y está bien que se calle. Lo
que decide es el club solo, no la suma.

En la Primera C 2026 no hay filas atrasadas y el detector sí habla: la tabla suma
`GF606` contra `GC605`, o sea que hay un gol convertido que ningún club declara haber
recibido. El faltante es un gol *en contra*, y el único club con delta sólo de GC es
Cañuelas. Eso es parsimonia, no demostración —el balance prueba que falta un gol, no
en qué celda—, y así queda anotado. Los otros dos desviados de esa página, Centro
Español y Juventud Unida, aparean entre sí y ya estaban resueltos: Wikipedia tenía
razón y la tabla no.

En ninguna de las dos hay nada que corregir en los datos. Cuando el torneo termine y
la página se estabilice, vuelven a mirarse.

La conclusión práctica sigue siendo incómoda: **sólo un puñado se puede cerrar sin
salir a buscar fuente por partido.** Los cinco del primer grupo ya están explicados
por su propio aviso; los del segundo necesitan una crónica que diga cuál de las dos
fechas; los del tercero, varias.

Un caso salió distinto a todos. En el **Clausura 2007**, Newell's 1-2 River no era
un error de nadie: el partido se **suspendió a los 90'** por incidentes, con River
ganando 2-1, y el Tribunal de Disciplina de la AFA se lo dio ganado **2 a 0**. La
página se contradice a sí misma —la celda tiene el marcador de cancha y la nota al
pie, citando el Boletín N° 3980, tiene el oficial— y la tabla está armada con el
0-2. Se guarda el oficial, que es el que homologó la AFA, y queda asentado en la
corrección que el 1-2 existió.

#### Y encontró un error en la tabla

**Platense 2009-10 no cierra con ninguna de las dos fuentes**, que coinciden entre
sí en sus 38 partidos. La tabla le pone GF39 GC40 y los partidos dan 40 y 41.

El árbitro se puede arbitrar a sí mismo. Un marcador mal leído toca siempre a
**dos** clubes: si a uno le sobra un gol a favor, al rival le sobra uno en contra.
Acá **ningún otro club se desvía** — las otras diecinueve filas cierran perfecto —,
así que la diferencia no puede venir de un partido. Está mal la fila.

Es un error de tipeo difícil de ver, porque los dos números están bajos por uno y
eso deja intactos la diferencia de gol (−1), los puntos (47) y el
ganados-empatados-perdidos (11-14-13). Incluso la suma de toda la liga sigue dando
**GF total = GC total = 878**, que es el chequeo obvio para una tabla. La
[Wikipedia en inglés](https://en.wikipedia.org/wiki/2009%E2%80%9310_Primera_B_Nacional)
publica los mismos números, así que el error viene de más atrás.

Por eso el aviso ahora dice **de qué lado** está el problema: si el club desviado
está solo, acusa a la tabla; si hay más de uno, deja abierta la posibilidad de un
partido mal leído.

### Las siete correcciones a mano

Hay **siete** filas del dataset que no dicen lo que dice Wikipedia, y viven en
[`fad/correcciones.py`](fad/correcciones.py) con su evidencia escrita. Las cinco
salen de que **la fuente se contradice sola**.

**Un club escrito con un nombre ambiguo.** La Primera Nacional 2022 dice
«San Martín» a secas, sin enlace, y ese torneo lo juegan el de San Juan y el de
Tucumán. Se resolvió sin fuentes externas: en la Fecha 5, San Martín (SJ) ya juega
contra Belgrano y San Martín (T) no juega ninguna vez —y cada club juega una vez
por fecha—. Además (T) queda con 35 partidos contra los 36 de (SJ), exactamente el
que falta. Ese solo partido dejaba **680 afuera del dataset**.

Las otras cuatro son de la B Nacional 2009-10.

**Un club que juega dos veces la misma fecha.** La página pone a Belgrano dos
veces en la Fecha 12 —contra All Boys y contra CAI— y deja a Gimnasia y Esgrima (J)
sin jugar. En una fecha de veinte equipos eso es imposible, y lo agarra
`una_vez_por_jornada` sin mirar nada de afuera. *Cuál* de los dos está mal lo dice
la segunda fuente, que trae los mismos diez partidos con los mismos diez
marcadores y el primero como **All Boys 0-0 GyE Jujuy**.

**Tres localías al revés.** Belgrano–Instituto, Ferro–Unión y Merlo–Platense
figuran con **el mismo local en las dos ruedas**. En un ida y vuelta cada par
juega una vez en cada cancha, así que una de las dos está invertida — lo agarra
`localias_repartidas`, también sin fuentes externas.

Los tres son **empates**, y ahí está lo interesante: como el marcador es
simétrico, las dos fuentes coinciden en todo salvo en quién jugaba en su casa. Por
eso el cruce no los emparejaba —busca `(jornada, local, visitante)` y del otro
lado están al revés—, se quedaban sin fecha y **se caían del dataset**. O sea que
el error de la fuente no producía un dato malo: producía tres partidos que no
existían.

Un lugar donde se puede escribir "este partido en realidad fue así" es la puerta
por la que se cuela un dataset que dice lo que a uno le gustaría. Por eso el
módulo es más estricto que el resto:

- una corrección **identifica el partido por completo** — jornada, los dos equipos
  y el marcador. Si algo no coincide, no se aplica;
- si engancha con **más de un** partido, no se aplica con ninguno;
- si **deja de enganchar** — porque alguien arregló la página — el build para y
  avisa que hay que sacarla. Una corrección vieja que nadie borró es una mentira
  dormida;
- y sin evidencia escrita no entra: hay un test que lo exige.

La alternativa era dejar afuera los 380 partidos de la temporada por una celda.

## Por eso el validador

No se le cree al parser: se le exige que lo que devuelve cumpla cosas que sólo
pueden cumplirse si está bien. Un aviso **grave** no escribe el archivo, y el
dataset de ayer queda como estaba — porque el modo de fallar de un scraper
automático no es tirar una excepción, es escribir un CSV plausible y equivocado.

| chequeo | qué agarra |
|---|---|
| campos completos, marcador verosímil | filas a medias, columnas corridas |
| no faltan jornadas en el medio | huecos, propios o de la fuente |
| ninguna jornada cae medio año antes que la anterior | el año mal asignado en temporadas que cruzan |
| todos los clubes están en el padrón | un ascenso, un torneo nuevo, un alias sin cargar |
| penales sólo en empates (salvo serie ida y vuelta igualada) | haber leído el entretiempo como si fuera la tanda |
| sin duplicados, nadie contra sí mismo | filas leídas dos veces, columnas corridas |
| todos los partidos de zona tienen zona | un encabezado que no se reconoció |
| **cada equipo juega una vez por fecha** | etiquetas corridas |
| **el que juega una ronda ganó la anterior** | cualquier cosa, en la eliminación |
| zona = todos contra todos completo | partidos faltantes (aviso, no error) |
| **la localía se reparte entre los dos cruces** | una localía al revés, o un club escrito de dos formas |
| **cada club juega en una sola zona** | un club escrito con el nombre de OTRO club que existe |
| **los goles suman lo que dice la tabla de posiciones** | un marcador mal leído, o mal publicado (aviso, no error) |

Los dos en negrita son los fuertes, y los dos son **autocontenidos**: no
consultan ninguna fuente externa, salen de cómo está armado un torneo.

### La dirección del chequeo de llaves

Al principio preguntaba lo simétrico — *cada ganador, ¿reaparece después?* — y
sobre un torneo terminado da lo mismo. Sobre uno en curso, no: los 16 ganadores
de dieciseisavos de la Copa 2026 todavía no jugaron sus octavos, así que tiraba
**14 avisos por día hasta noviembre**. Un chequeo que grita todos los días deja
de leerse, y ahí ya no sirve para nada.

Preguntado al revés valida lo que **hay** en vez de exigir lo que todavía no se
jugó, y no pierde nada: el mismo error que rompe una punta rompe la otra.
Verificado a mano — invirtiendo el dieciseisavos que clasificó a Atlético
Tucumán, el aviso salta; con los datos reales, cero.

Las rondas se agrupan por **nombre**, nunca por fecha. Agrupar por fecha parece
razonable y está mal por los dos lados: la Copa solapa rondas (los treintaidosavos
2026 van de enero a abril y los dieciseisavos de abril a julio, compartiendo días)
y una misma ronda se juega en varios días, con lo cual el segundo día parece una
ronda nueva cuyos participantes "no ganaron la anterior". Si algún partido de
eliminación no trae ronda reconocida, el chequeo **avisa que se salteó** en vez de
saltearse callado: un chequeo mudo es peor que uno ausente, porque parece que algo
se está mirando.

### El que costó encontrar

El primer intento contra las etiquetas corridas fue cronológico: *la Fecha 7 no
puede empezar antes que la Fecha 6*. Falló por los dos lados. **No vio el bug
real** — las dos jornadas arrancaban el mismo día, y un empate no es un `<` — y
además **se quejaba de datos correctos**: la Fecha 9 del Apertura 2026 se jugó
entera en mayo, dos meses después de la Fecha 10, y está perfecta.

El que anda no mira el calendario, mira cómo está armado el torneo: con 30
equipos y 15 partidos por fecha, **cada equipo juega exactamente una vez**. Si un
partido se anota en la jornada equivocada, alguien aparece dos veces ahí y falta
en la de al lado. Sobre los datos reales: **15 errores con el bug, 0 después de
arreglarlo**, y las reprogramaciones no lo molestan.

## El padrón de clubes

`fad/equipos.py` tiene **una** estructura con el nombre canónico de cada club y
sus alias. Una sola, y los índices de búsqueda se derivan de ella al importar. La
tentación es tener un diccionario para AFA, otro para Wikipedia y otro para los
nombres cortos; cuando esos se desincronizan nadie se entera, porque cada uno
anda bien por su cuenta.

Emparejar por parecido de texto no alcanza, y no es una intuición: el primer
cruce contra AFA lo hizo así y **26 de 60 partidos quedaron sin pareja**. Los
casos que lo rompen:

| se escribe | y es |
|---|---|
| `Gimnasia` | el de **La Plata** (Mendoza siempre lleva `(M)` o `(Mendoza)`) |
| `Estudiantes` | el de **La Plata** (el de Río Cuarto siempre lleva `(RC)`) |
| `Independiente` | **no** es Independiente Rivadavia, aunque sea prefijo |
| `Talleres`, `Sarmiento` | los de Córdoba y Junín |
| ``Newell`s`` | AFA usa acento grave, Wikipedia apóstrofe |

Con el padrón escrito a mano, 60 de 60.

La Copa Argentina lo llevó de 30 clubes a 64, y el histórico a **69** — Arsenal,
Colón, Patronato, Quilmes y Chacarita jugaron Primera en estos años y ya no
están; solos son ~670 partidos. De paso mostró para qué sirve el padrón:
entran **cuatro** Gimnasia y Esgrima (LP, M, C, J) más un Gimnasia y Tiro que es
otro club, **tres** San Martín (F, SJ, T), **tres** Estudiantes (LP, RC, BA) y
**dos** Sarmiento (J, LB).

El riesgo propio de un padrón no es que falte un club: es que **un alias se le
asigne al club equivocado**. Eso no rompe nada — reparte los partidos de un
Gimnasia entre los dos y sigue andando. Dos defensas contra eso:

- un alias reclamado por dos clubes **revienta al construir el índice**, no en
  producción;
- los tests usan un **testigo externo** (`tests/afa_snapshot.py`): la AFA numera
  sus clubes con un sistema propio que no sabe nada de cómo los escribe
  Wikipedia, así que exigir que las dos numeraciones se correspondan es una
  restricción real. Si `Gimnasia` se resolviera al de Mendoza, el id deja de
  coincidir y el test cae.

Eso último viene de una lección del proyecto hermano: al fusionar cinco
estructuras en una, ~49 tests quedaron comparando la estructura consigo misma y
pasaban siempre. Un padrón unificado necesita que sus casos de prueba vengan de
afuera.

Un club que el padrón no conoce es un **aviso grave**: no se escribe el CSV. Es
el caso de un ascenso o de un torneo que se suma, y conviene que haga ruido una
vez en vez de colarse para siempre como un club distinto.

## Correr solo

Dos workflows en `.github/workflows/`:

- **`tests.yml`** — la suite en Python 3.11 y 3.13 en cada push, más el mutation
  testing en una de las dos.
- **`actualizar.yml`** — todos los días a las 12:00 UTC (09:00 en Argentina, con
  los partidos de la noche anterior ya cargados): corre la suite, reconstruye el
  dataset y commitea **sólo si cambió algo**.

Lo importante no es el cron, es qué lo frena. Un scraper desatendido no falla
explotando: falla escribiendo algo plausible y equivocado, y nadie lo mira.

| se frena por | y entonces |
|---|---|
| un aviso **grave** del validador | no escribe; queda el dataset de ayer |
| **el dataset se achicó** | no escribe; hay que revisarlo a mano |
| una página que no se puede bajar | no escribe; el workflow falla y avisa |

### La guarda contra achicarse

Es la única que mira lo que **ya no está**, y es la que hace falta justamente
cuando nadie está mirando. Si mañana Wikipedia reordena una página y el parser
saca 40 partidos donde había 240, esos 40 pueden estar perfectos: ningún chequeo
del validador los ve mal, porque **mirados solos están bien**. Lo único que
delata la pérdida es compararla contra lo de ayer.

Se cuenta por torneo y no partido por partido, porque durante un torneo en curso
los partidos se reprograman y cambian de fecha todo el tiempo — comparándolos uno
a uno habría bajas y altas todos los días. La cantidad, en cambio, sólo baja
cuando se perdió algo. Si la baja es real, `python build.py --forzar`.

Esa guarda tuvo un bug que vale contar: comparaba `season` como entero de un lado
(recién salido del parser) y como texto del otro (leído del CSV), así que las
claves nunca se cruzaban y **todos** los torneos figuraban desaparecidos. Habría
frenado el primer build real, todos los días. Los tests no lo veían porque usaban
la misma función de los dos lados; el bug vivía justo en la juntura que no se
estaba probando.

### Dos detalles de GitHub Actions

- Los workflows programados corren **sólo en la rama por defecto**.
- GitHub **desactiva** los cron de un repo sin actividad por 60 días y manda un
  mail. Si el dataset deja de actualizarse de golpe, mirar eso primero.

## El artículo manda sobre el nombre

El padrón resolvía por nombre, y eso se rompió al bajar al ascenso: **`Estudiantes`
a secas apunta a tres artículos distintos** según la página. En Primera es el de La
Plata; en Primera B, el de Caseros. Lo mismo `Talleres`, que en Primera B 2017-18
es el de Remedios de Escalada y no el de Córdoba. Con el padrón anterior, media
Primera B entraba en la historia del club equivocado — sin fallar.

Resolverlo *por división* tampoco sirve: los clubes ascienden y descienden, la
regla no se mueve con ellos. Lo que sí es estable es el **enlace que la propia
página usa**, específico de esa temporada por construcción — y que el parser
estaba tirando a la basura al limpiar la celda.

Así que `ARTICULOS` mapea título de artículo → club, y `canonizar()` resuelve
primero por ahí. El índice se generó recorriendo el catálogo y quedándose sólo con
los nombres visibles que apuntan a **un único** artículo en todo el corpus. Si
dentro de una página un nombre apunta a dos, no se devuelve ninguno: ahí no hay
testigo, y adivinar es justo lo que no hay que hacer.

Tres torneos quedaron **afuera**, comentados en el catálogo con su motivo: Primera
B 2017-18 (lista dos veces las fechas de la primera rueda), Primera B 2021 (una
plantilla que mezcla dos resultados) y Primera Nacional 2022 (un partido dice "San
Martín" a secas y sin enlace, con el (SJ) y el (T) en el mismo torneo). Prefiero
tres torneos afuera y dicho, que adentro y mal atribuidos.

### Y una entrada del índice estaba mal

El índice de artículos resuelve bien *siempre que la entrada sea correcta*, y una
no lo era: `Club Atlético Racing` apuntaba a **Racing Club**, el de Avellaneda.

Es el de Córdoba. Avellaneda se llama «Racing Club» a secas y su artículo es ése.
Mientras el índice dijo lo otro, **248 partidos de Racing de Córdoba quedaron a
nombre de Racing de Avellaneda** — en Primera Nacional 2007, 2023, 2025 y 2026,
Argentino A 2011 y 2012, y Federal A 2018, 2021 y 2022. Torneos que Avellaneda no
jugó nunca.

No lo agarró ningún chequeo, y no podía: los dos clubes están en el padrón, los dos
nombres son legítimos, y ninguna regla del fixture se rompe porque un club juegue
un torneo que no le toca. Apareció por un lado inesperado — el cruce contra la
tabla dejó de encontrar a `Racing (C)` en la Primera Nacional 2024 y se notó que la
fila y la suma coincidían dígito por dígito pero nunca se comparaban.

La verificación fue medir el corpus, no razonar: las **22 páginas** de la caché que
enlazan ese artículo lo muestran como «Racing», «Racing (C)», «Racing (Cba.)» o
«Racing (Córdoba)», y ninguna como el de Avellaneda. Y la B Nacional 2007-08, que
tiene a los dos, los distingue bien: `[[Club Atlético Racing|Racing (C)]]` para el
cordobés y `[[Racing Club]]` para la promoción que jugó Avellaneda contra Belgrano.
Esa fila quedó como estaba, que es lo correcto.

La lección no es «revisar el índice». Es que un índice generado
automáticamente hereda la ambigüedad de la fuente, y **una entrada mal apuntada no
falla: miente en silencio**, en la escala de todos los partidos de un club.

### Y como no falla, hay que ir a buscarlo

Un error así no se encuentra esperando a que salte. Salieron dos detectores de la
forma que tenía el de Racing, y los dos son baratos:

**El nombre visible contra el artículo.** Cuando la página escribe
`[[Club Atlético Racing|Racing (C)]]`, el `(C)` lo puso un editor a propósito. Si
el nombre ya viene desambiguado y el artículo dice otro club —y los dos existen en
el padrón— uno de los dos está mal. Sobre las 279 páginas, **un solo caso** además
de Racing: `[[Club Atlético San Martín (Tucumán)|San Martín (SJ)]]`, con la bandera
de San Juan al lado, en la Copa Argentina 2019-20. Ahí el equivocado es el enlace,
no el nombre — y no ensucia nada, porque la misma página también usa el enlace
correcto y la guarda del mapa se abstiene, que es justo para lo que está.

**Un club en dos categorías incompatibles.** Sin mirar nombres: si un club aparece
la misma temporada en dos divisiones, o asciende —y entonces el salto es de un
nivel y ocurre una vez— o hay un error. De 46 casos, 45 son ascensos y descensos
legítimos (la temporada argentina cruza dos años calendario, así que un club
promovido figura en las dos). **Uno saltaba dos divisiones**: Estudiantes de La
Plata en la Primera B 2015.

### La tilde que mandó 44 partidos al club equivocado

Estudiantes de La Plata nunca jugó la Primera B. Esos 44 partidos son de
Estudiantes de Caseros, y el mecanismo es distinto al de Racing — más fino, y
peor.

El mapa por página existe porque las tablas de resultados escriben el club **sin
enlace**: un «Estudiantes» pelado se resuelve con el enlace que la misma página usó
en la lista de participantes. Y tiene una guarda deliberada: *si un nombre apunta a
dos artículos, no devuelve ninguno*, porque ahí no hay testigo.

La página enlaza a Caseros ocho veces bien y **dos veces sin la tilde**, como
`Club Atletico Estudiantes`. Son el mismo artículo y un typo — pero la guarda
comparaba por igualdad de cadena, vio dos, se abstuvo, y el «Estudiantes» pelado
cayó al nombre solo: que en Primera es el de La Plata.

O sea que **la guarda contra adivinar terminó forzando la adivinanza**. El padrón
ya toleraba el typo —`buscar()` normaliza el artículo antes de buscarlo—; el único
eslabón que comparaba en crudo era ése.

Comparando normalizado: **44 ambigüedades falsas** en el corpus, de las cuales una
sola cambiaba de club. Y la guarda sigue firme donde tiene que estarlo — los dos
San Martín siguen sin testigo, porque ahí los artículos son distintos de verdad.

#### El testigo estaba en el CSV

Lo mejor del caso es que el dataset venía diciendo la verdad en una columna que
nadie miraba. Los 23 partidos de local de ese «Estudiantes» se jugaron en
**Ciudad de Caseros**; Estudiantes de La Plata juega en el Ciudad de La Plata, el
Jorge Luis Hirschi y el Centenario. Cero superposición, sin ambigüedad posible.

Así que la cancha pasó a ser un chequeo: `dataset.casas_compartidas`.

### El chequeo de la cancha, y las cuatro versiones que no funcionaron

La primera idea era la obvia — *comparar las canchas del club en un torneo contra
las que usa en el resto* — y se hundió en algo que no tiene arreglo por cadenas:
**los nombres de los estadios**. «Ciudad de Río Cuarto» y «Antonio Candini» son el
mismo estadio y no comparten una letra. «Kolbowsky» aparece escrito de tres formas.
«Coloso Marcelo Bielsa» y «Coloso del Parque» también son uno solo. Cada intento de
unificarlos —contención de tokens, quitar palabras vacías, atribuir cada cancha a su
dueño— movía el ruido de lugar: 21 avisos, después 120, después 34.

La cuarta versión falló distinto y es la más instructiva. Comparar un torneo contra
el resto **no encuentra un error sistemático**: como Racing estaba mal en nueve
temporadas, «Miguel Sancho» también aparecía en el resto y el chequeo lo daba por
normal. Un error repetido se vuelve la norma contra la que se lo compara. Estudiantes
se agarraba sólo porque era una temporada suelta.

Lo que funciona es no comparar canchas entre sí, sino preguntar otra cosa:

> **¿Hay dos clubes de nombre confundible que juegan de local en la misma cancha?**

```
Ciudad de Caseros   Estudiantes (BA) (248)  vs  Estudiantes (LP) (21)
Miguel Sancho       Racing Club (119)       vs  Racing (C) (19)
```

La cancha se compara por **cadena exacta**, a propósito: dos clubes que aparecen bajo
el mismo string son sospechosos justamente *porque* comparten la grafía, que es lo que
pasa cuando en realidad son uno. Y la condición de los nombres es lo que lo deja sin
ruido — compartir estadio es normal (Argentinos y Chacarita, los municipales de
provincia), compartirlo *además de llamarse igual* no lo es. Medido: **8 avisos sin
esa condición, 2 con ella, y los 2 eran los dos bugs**.

Corrido contra el dataset como estaba **antes** de los dos arreglos, el chequeo los
señala a los dos. Contra el de ahora, cero.

### Y encontró un tercero

Bajando el umbral a un solo partido aparecieron cuatro casos más, y uno era real:

| | |
|---|---|
| **Ferro Carril Oeste** en el Federal A 2016 | la página se olvida el `(GP)` en **una** fila de diez, y el partido se juega en El Coloso del Barrio Talleres — el estadio que ella misma declara de Ferro de General Pico. El de Caballito jugaba la Primera Nacional ese año. **Corregido.** |

### Los otros avisos, y una tercera forma de contradecirse

Los tres restantes salieron distintos, y dos de ellos revelaron algo que no
estábamos buscando: **partidos bien atribuidos con la cancha del vecino**.

| | qué resultó ser |
|---|---|
| **Gimnasia y Esgrima (J)** en el Legrotaglie, Primera Nacional 2022 | el Legrotaglie es de Gimnasia de **Mendoza**. Y el equivocado es el estadio, no el club: San Martín (T) ya había jugado contra el de Mendoza en la Fecha 29, y en un torneo de una sola rueda no se cruzan dos veces. **Corregido a 23 de Agosto.** |
| **Sarmiento (LB)** en el Centenario, Federal A 2025 | el Centenario es de Sarmiento de **Resistencia**; la tabla de participantes de la misma página pone a La Banda en el Ciudad de La Banda. El local sí es Sarmiento (LB) — la ida fue de visitante y el cuadro de la llave lo confirma. **Corregido.** |
| **Huracán 4-1 Atlético Tucumán** en Malvinas Argentinas | no es un error: es el **Desempate por el ascenso** de 2014, en cancha neutral de Mendoza y ganado en tiempo suplementario. El dato está bien. |

Así que `correcciones.py` aprendió una tercera cosa. Antes sabía arreglar **nombres**
(un club escrito mal) y **marcadores** (un gol de más); ahora también **canchas**. Con
la misma condición de siempre, y en estos dos casos se cumple de la forma más limpia:
el testigo es la propia página, que en su tabla de participantes dice en qué estadio
juega cada club. La fuente se contradice sola y no hay que traer nada de afuera.

Cuando *no* se resuelve así, no entra. El aviso queda abierto y listo: este repo no
inventa canchas.

### Y los dos que sí eran alquileres

Los otros dos no se podían resolver desde la página, así que fue a buscar prensa —
con una regla: **una crónica anterior al partido**, que no puede haber copiado de
Wikipedia.

| | |
|---|---|
| **Argentino de Quilmes** en el Centenario, Primera C 2018-19 | Solo Ascenso, cuatro días antes: «El Mate será local en un estadio de primer nivel como el Centenario, la cancha de Quilmes». Y el presidente del club, en El Sol de Quilmes: «Hemos hecho un esfuerzo enorme para poder llevar el partido al estadio de Quilmes». |
| **Huracán Las Heras** en Malvinas Argentinas, Federal A 2023 | Los Andes, cuatro días antes: «Se jugará el domingo desde las 16 en el estadio Malvinas Argentinas, con ambos públicos». Y la revancha del mismo cruce, esa misma temporada, figura en General San Martín: la página distingue las dos canchas. |

El alquiler verificado va a `dataset.ALQUILERES`, con la evidencia y el link. Un
chequeo que grita todos los días por algo que ya se miró deja de leerse, y ahí se
pierde el único aviso que importaba — pero silenciar es peligroso, así que se le pide
lo mismo que a una corrección: evidencia escrita y citada, y hay un test que lo exige.

Y **no se silencia después: no entra al recuento**. Es lo mismo en el resultado y más
conservador — si ese club tuviera *otro* problema en esa cancha, seguiría apareciendo.

Con eso los cuatro avisos quedaron en **cero**. Pero de los dos alquileres sólo uno
sigue en la lista, y el motivo es lo que viene.

## `neutral` dejó de ser del torneo

El Desempate de 2014 iba con `neutral=false` siendo que se jugó en cancha neutral,
porque el campo era del **torneo**: la Copa Argentina entera es neutral, una liga no,
y no había forma de que un partido dijera lo suyo.

Lo interesante es que **la fuente sí lo dice, y de una forma que se puede leer**.
Cuando no hay local, la tabla rotula sus columnas «Equipo 1 / Equipo 2» en vez de
«Local / Visitante». No es una interpretación: es la única manera que tiene una tabla
de decir que los dos son visitantes, y la usa siempre para lo mismo. Son **232 tablas
en 51 páginas**.

Así que `neutral` pasó a resolverse en dos niveles: el torneo lo dice para todos sus
partidos, el partido puede decirlo por sí mismo, y **gana el partido cuando opina**.
Sólo puede *marcar* neutral, nunca desmarcar — una tabla que rotula «Local» está
etiquetando su columna, no afirmando nada sobre la cancha.

**36 partidos** cambiaron de `false` a `true`, y son exactamente lo que uno esperaría:
34 de fase eliminación —finales, desempates, reducidos, definiciones de ascenso y
descenso— más dos que la página llama «partido de desempate» con todas las letras.
Ninguno es de temporada regular.

```
2006-12-13  Boca Juniors  1-2  Estudiantes (LP)      Desempate    José Amalfitani
2014-12-14  Huracán       4-1  Atlético Tucumán      Desempate    Malvinas Argentinas
2021-11-22  Tigre         1-0  Barracas Central      Final        Florencio Sola
2024-11-03  Aldosivi      2-0  San Martín (T)        Final        Gigante de Arroyito
```

Ninguno se juega en cancha de los que juegan, que es el punto.

## Cuando «Zona 1» son dos zonas distintas

Un torneo multifase puede llamar **«Zona 1» a dos cosas**: la Zona 1 de la Primera
fase y la Zona 1 de la Revélida, con otros equipos. El rótulo sale de un encabezado
de la tabla, y la tabla no sabe de qué sección cuelga — así que los partidos de las
dos caían en el mismo balde. El Argentino A 2010-11 quedaba con **132 partidos en su
Zona 1 cuando son 112 más 20**, y con eso ninguna cuenta por zona se podía hacer.

Ahora, cuando la página reusa un rótulo entre fases, la zona se escribe
`Primera fase - Zona 1`. La fase ya viajaba hasta ahí; sólo faltaba usarla.

**La calificación es condicional, y eso importa.** Ponerle la fase a toda zona
cambiaría el `group` de las 38 109 filas para arreglar **tres páginas, ninguna del
catálogo**. Se mide sobre la página entera —la ambigüedad de un rótulo es una
propiedad de la página, no se ve desde adentro de una sección— y se aplica sólo
donde hay choque. La huella de las 128 páginas del catálogo salió idéntica.

Medir esto bien costó dos intentos. Buscando sólo `Zona ...` daba una página;
aflojando a cualquier encabezado daban **34 del catálogo** — y era falso: contaba
«Fecha 1», que está en todas las fases de casi todos los torneos y que el parser
nunca trata como zona, porque esa rama corre antes. El detector tiene que replicar
la lógica del parser, no parecerse a ella. Con eso: **cero del catálogo, tres afuera**
—Argentino A 2010-11, Nacional 1985 y B Nacional 2004-05—, dos de ellas en la hoja
de ruta.

### Ocho clubes desconocidos, y ninguno era un club

Con las zonas separadas, esa página quedó denunciando **ocho clubes que el padrón no
conoce**. Ninguno resultó ser un club nuevo: eran typos y formas cortas.

Y no se resolvieron por parecido de cadenas, que es justo lo que este repo no hace.
Se resolvieron con **la grilla de la zona**: en la fecha donde aparece el nombre raro,
el club que falta es exactamente ése.

```
Fecha 1    falta Gimnasia y Esgrima (CdU)   raro Gimnasia (CdU)
Fecha 16   falta Central Norte (S)          raro Centrl Norte
Fecha 20   falta Libertad (S)               raro Libertad
Fecha 22   faltan Central Norte (S) y Gimnasia y Esgrima (CdU)
```

Cinco entraron como alias —`Cipoletti`, `Desamprados`, `Centrl Norte`,
`Gimnasia (CdU)`, `Libertad`— y uno como artículo: la página escribe «Rivadavia» a
secas, que el padrón no resuelve porque hay tres, pero enlaza
`Rivadavia de Lincoln`, y el artículo sí desambigua.

**Dos quedaron afuera a propósito, y ésa es la parte que importa.** «Gimnasia y
Esgrima» a secas tiene **seis** candidatos. Y «Central Norte (SE)» no es un typo de
escritura sino un desambiguador equivocado: en esa misma página `(SE)` significa
Santiago del Estero —ahí está «Central Córdoba (SE)», que resuelve bien—, así que
dárselo al de **Salta** sería escribir en el padrón algo que la fuente no dice.

Los dos siguen como club desconocido, que es un aviso grave y frena el build. Es lo
correcto: un alias mal puesto no falla, le da los partidos al club equivocado.

### Y con eso la página entró

Los nueve nombres que quedaban mal van a `correcciones.py`, cada uno arbitrado por la
grilla de su zona. Los cuatro de Unión tienen además prueba aritmética: con ellos
Unión (MdP) llega a los **28 partidos que publica la tabla** de su zona, y los ocho
clubes de la Zona 1 cierran en 28. Sin ellos queda en 24 y ningún otro reparto da 28.

| | |
|---|---|
| ×4 | `Unión (S)` → **Unión (MdP)** en la Zona 1 (el de Sunchales juega la Zona 3) |
| ×1 | Fecha 21: `Douglas Haig` → **Huracán (TA)** (Douglas Haig ya jugaba esa fecha) |
| ×2 | `Gimnasia y Esgrima` → **(CdU)** |
| ×1 | `Central Norte (SE)` → **Central Norte (S)** |
| ×1 | `Unión` → **Unión (S)** |

Ese último es el que más incomoda: «Unión» a secas **sí** está en el padrón —es Unión
de Santa Fe— así que no se caía como desconocido. Resolvía calladito a un club de
Primera que nunca jugó el Argentino A.

**Los 438 partidos fueron a `data/sin-fecha/`**, con este razonamiento escrito al
lado: *«Que no fuera un bug del parser había que verificarlo: si lo fuera, la
solución sería arreglar el parser, no archivar 438 partidos.»*

La pregunta estaba bien y la respuesta estaba mal. **Era un bug del parser**, y los
438 volvieron a `data/` con fecha. Está contado abajo, en [El corrimiento que
escondía 373 fechas](#el-corrimiento-que-escondía-373-fechas); vale como recordatorio
de que verificar una hipótesis no sirve si se la verifica mirando el mismo síntoma
que la generó.

De paso se cayó un test que decía «exactamente tres torneos sin fecha, todos de
Primera C». Eso no era un invariante sino el estado de ese día. Lo reemplazan dos que
sí lo son: que cada `sin_fecha` esté **explicado** en el catálogo, y que ninguno
termine escribiendo en `data/`.

### Y casi se lleva puesto el chequeo que lo motivó

`una_zona_por_club` reconocía las zonas por el arranque del nombre
(`^(zona|grupo)`). Con la zona escrita `Primera fase - Zona 1` dejaron de contar, y
el chequeo **se calló justo en la página que su propio docstring cita** — los cuatro
partidos de Unión de Mar del Plata escritos «Unión (S)».

No lo agarró ningún test: lo agarró correr el chequeo a mano sobre esa página y notar
que el aviso ya no salía. Ahora el patrón acepta el prefijo de fase, y hay un test y
un mutante para cada mitad — que la zona calificada cuente, y que `Interzonal` siga
sin contar.

### Y una entrada de la lista se volvió inerte

Con el Desempate marcado neutral, `casas_compartidas` dejó de contarlo como casa de
nadie — y con eso desapareció la pareja que hacía saltar el aviso de Huracán Las
Heras. Su entrada en `ALQUILERES` pasó a no silenciar nada.

**Se sacó.** Una entrada que hoy no sostiene nada no es gratis: es un permiso abierto
para tapar el aviso de mañana. Es la misma regla que ya tenían las correcciones —
cuando dejan de enganchar, el build avisa para que se borren.

### Los otros dos, que miran otra cosa

Un club mal atribuido deja tres rastros distintos, y cada uno se ve con un chequeo
que no comparte nada con los otros dos.

**Dónde juega** — [`dataset.categorias_incompatibles`](fad/dataset.py). Un club en
dos divisiones el mismo año es normal y pasa todo el tiempo: la temporada argentina
cruza dos años calendario, así que el que desciende en junio juega el Clausura en
Primera y desde agosto la Primera Nacional, con el mismo año en las dos filas. Son
45 de los 46 casos del dataset.

Lo que no existe es un **salto de dos**. Para ir de Primera a Primera B en un año
calendario habría que descender dos veces, y no hay calendario donde eso entre. Eso
lo vuelve un invariante y no un umbral elegido a dedo.

**Cómo se lo nombra** — [`equipos.articulos_que_contradicen`](fad/equipos.py). Que
el nombre visible y el artículo digan clubes distintos es lo *normal*: para eso está
el índice. `[[Club Atlético Estudiantes|Estudiantes]]` significa «de los tres
Estudiantes, éste». Avisar ahí sería avisar en cada página del ascenso.

Lo que sí es un error es cuando el nombre visible **ya viene desambiguado** y aun
así difiere. `[[Club Atlético Racing|Racing (C)]]`: ese `(C)` lo escribió alguien a
propósito, así que no hay ambigüedad que resolver. Hacen falta las tres condiciones
juntas —el nombre trae paréntesis, el artículo está en el índice, y el nombre solo
también resuelve a un club conocido—; sin la tercera entran ocho casos donde el
artículo no contradice nada, sólo traduce.

Los tres, corridos contra el dataset **tal como estaba antes** de los dos arreglos:

| chequeo | antes | ahora |
|---|---|---|
| `casas_compartidas` (la cancha) | Estudiantes **y** Racing | 4 avisos, ninguno resuelto |
| `categorias_incompatibles` (la división) | Estudiantes **y** Racing, en 6 temporadas | 0 |
| `articulos_que_contradicen` (el enlace) | 1 | 1, y es real |

Que se solapen no es redundancia: **la cancha se le escapaba a Racing** en las
temporadas donde las dos grafías no convivían bajo el mismo estadio, y la división
no ve nada cuando el club mal atribuido juega la categoría que le corresponde. Cada
uno tapa el agujero del otro.

Uno de los tres tiene una limitación que conviene decir: el del enlace mira el
wikitexto, así que **sólo corre cuando la página se re-parsea**. Un torneo terminado
sale del CSV sin bajarse, y ahí no opina hasta el próximo `--rehacer`. Es la misma
propiedad que tiene el cruce contra la tabla de posiciones.

## El corrimiento que escondía 373 fechas

Salió buscando otra cosa. Yendo a ver si se podían reponer las fechas que faltan
—2 345 partidos en seis temporadas— apareció que **una de esas seis no estaba sin
fecha: las tenía y no las leíamos**.

El catálogo lo explicaba así, y la frase es del proyecto, no de nadie más:

> *Sus tablas **sí** traen la columna de fecha, pero la página la deja en blanco en
> casi todas las filas. Quedan 65 de 438 con fecha, y **no es el parser: la fuente
> no la trae**.*

Era el parser. `_partir` terminaba con un filtro que parecía inocuo:

```python
return [c for c in partes[1:] if c.strip()]     # descarta las celdas vacías
```

**La posición es el dato.** Descartar una celda vacía corre todas las columnas que
vienen después, y lo que sale no es un hueco: es un valor equivocado en la columna
de al lado. De la Fecha 18 en adelante, el Argentino A 2010-11 deja el **estadio**
en blanco y pone la fecha con `rowspan`:

```
|Villa Mitre  |1 - 2  |Huracán (TA)  |            |rowspan=4|2 de febrero  |
                                      ↑ vacía              ↓ aterriza acá
                                   estadio = "2 de febrero"      fecha = ""
```

Así que esos partidos no salían «sin fecha»: salían **con una fecha por cancha**.
`venue = "2 de febrero"`. Un dato faltante es honesto; un dato falso, no.

Cambiar el filtro por `return partes[1:]` recupera **376 fechas** y limpia otras
tantas canchas. Verificado con arnés de equivalencia sobre las 131 páginas
cacheadas: mismo total de partidos (39 327), ninguna página cambia de cantidad, y
los únicos campos que se mueven son `fecha` y `estadio` en dos páginas. El Argentino
A 2010-11 pasa de 65/438 a **438/438** y se muda a `data/`.

Un detalle metodológico que vale más que el arreglo. El comentario decía que se
había medido «jornada por jornada» — y era cierto. Pero se midió **sobre la salida
del parser**, que es donde vivía el bug: la medición confirmó el síntoma («estos
partidos no tienen fecha») y por eso pareció confirmar la causa («la fuente no la
trae»). Para verlo había que mirar el wikitexto crudo y contar columnas. *Verificar
una hipótesis mirando el mismo síntoma que la generó no la verifica.*

Y una trampa al medir el arreglo, que casi me la como. Buscando canchas con forma de
fecha para ver si quedaban corrimientos, el contador daba **1 367 después de
arreglarlo**. Casi todas eran estadios de verdad: en Argentina hay canchas que se
llaman **9 de Julio**, **20 de Febrero**, **25 de Mayo**. La señal buena no es «la
cancha parece una fecha» sino «la cancha parece una fecha **y el partido no tiene
fecha**». Medido así: **373 antes, 0 después**.

## Las cinco temporadas que no tenían fecha

Quedaban cinco: el Argentino A 2005-06, las tres de Primera C 2008-2011 y la
Primera B 2010-11. **2 345 partidos completos salvo por el día.** Sus páginas
publican los resultados en tablas de tres columnas —`Local | Resultado |
Visitante`— y no hay columna de fecha que estemos leyendo mal: no existe.

Antes de salir a buscar hubo que medir una cosa, porque de ella dependía todo el
enfoque: **en el ascenso argentino una jornada casi nunca se juega en un día.**

| días que abarca una jornada | % |
|---|---|
| 1 | 19,2 % |
| 2 | 26,7 % |
| 3 | 25,7 % |
| 4 o más | 28,4 % |

Medido sobre 3 237 jornadas reales del propio dataset. O sea que la vía cómoda
—tomar la fecha del titular de una crónica de jornada y repartirla entre sus once
partidos— dejaría el **41,5 %** con el día equivocado, y sin avisar. Queda
descartada por evidencia, no por prudencia. Lo que sirve es una fuente con **fecha
por partido**.

Aparecieron dos, y ninguna es la prensa:

- **RSSSF** tiene el Argentino A 2005-06 entero en una página de texto plano.
- **El feed de ESPN** devuelve cada temporada de Primera B y C en una sola llamada.

### Usar RSSSF justo después de haberla desenmascarado

Vale detenerse acá, porque a cuatro secciones de distancia este README cuenta que
RSSSF resultó ser **el ancestro del error** en el Clausura 2005: publicaba la
tabla de Wikipedia con el mismo desbalance de 3 goles, así que no era un testigo
sino un eco.

No es contradicción, y la diferencia importa más que el caso. **La circularidad
existe cuando las dos fuentes pueden haberse copiado el dato en disputa.** Acá el
dato en disputa es la fecha, y Wikipedia no publica ninguna —es exactamente la
razón por la que esos partidos estaban en `sin-fecha/`—. La fecha de RSSSF no
puede ser un eco de Wikipedia ni al revés: es información nueva. Y el marcador,
que sí podría ser un eco, **no se importa**: se usa para verificar.

### Sin número de jornada

El feed de ESPN no lo publica, y la regla del proyecto es *«los equipos y la
jornada identifican el partido, el marcador lo verifica»*. Lo que se hizo no fue
aflojarla sino cambiarle el identificador, y se midió antes de decidirlo: en una
liga de ida y vuelta cada par se cruza **una vez en cada cancha**, así que
`(local, visitante)` ya identifica. Sobre nuestros propios datos: 384 pares
distintos sobre 384 partidos en la Primera C 2008-09.

Lo que sostiene el cambio no es esa aritmética sino que la regla de colisión sigue
puesta: los playoffs vuelven a cruzar a los mismos, y ahí el par deja de
identificar, así que **se caen los dos**. Es la mayor parte de las 72 filas que
todavía no tienen fecha.

### La guarda que el marcador no da

Un nombre mal traducido en el mapa manda el partido al club equivocado, y el
marcador **no lo agarra**: dos partidos de la misma temporada pueden coincidir en
resultado por casualidad. Por eso `espn.contrastar_plantel` exige que los clubes
que la fuente pone en esa temporada sean los mismos que los nuestros. Un club que
no jugó no puede aparecer.

Los nombres cortos son el peligro concreto, y es el mismo que el README ya cuenta
con «Estudiantes»: resolverlos por el padrón devuelve un club que existe y que no
es. RSSSF escribe «Racing», que en la Zona Sur es el de Olavarría y en la Norte el
de Córdoba —dos clubes distintos, en el mismo torneo—; el padrón devuelve Racing
Club de Avellaneda, que nunca jugó el Argentino A. Y «Talleres», que ahí es el de
Perico, devuelve el de Córdoba. Por eso los mapas van **a mano y por zona**.

El que obligó a mirar dos veces fue `FC Urquiza`, y se resolvió sin adivinar:
ESPN tiene **además** un `J. J. de Urquiza` con otro id, o sea que para ESPN son
dos clubes, y lo son. En la 2010-11 nuestro plantel trae los dos, así que es UAI;
en la 2009-10 UAI no jugó, así que ahí no se traduce.

### El resultado

| | antes | ahora |
|---|---|---|
| con fecha | 36 966 | **39 255** |
| sin fecha | 2 345 | **72** |

Y una consecuencia que no estaba en el plan: una vez que las cinco temporadas
tuvieron fuente, **no quedó un solo torneo marcado `sin_fecha`**. El flag se sacó.
El test que lo custodiaba traía escrita su propia condición de muerte —«si no
queda ninguno, sobra la carpeta y sobra el flag»— y esta vez se cumplió.

En su lugar el reparto pasó a ser **por fila**: la que tiene fecha va a `data/`,
la que no, a `sin-fecha/`. Antes se decidía por torneo, y esa regla tenía las dos
mitades mal — un torneo marcado iba entero a la carpeta aparte aunque tuviera
fechas, y en cualquier otro las filas sin fecha **se tiraban**, que contradice lo
que el LEEME de esa misma carpeta viene diciendo desde el principio. Al
arreglarlo aparecieron 16 partidos reales que se venían descartando.

## La página que se copió a sí misma

El Argentino A 2005-06 dejó, después de fecharlo, quince partidos sin día y diez
filas duplicadas. Las dos cosas tenían la misma causa, y no es un error de
lectura: **la página copió las tablas de las Fechas 5 y 6 de la Zona Sur del
Clausura dentro del Apertura.** No parecidas — los mismos doce cruces, los mismos
locales y los mismos marcadores.

Eso solo ya prueba que está mal, sin traer nada de afuera: dos rondas de dos
torneos distintos no pueden ser idénticas. Lo que no prueba es **qué iba ahí**.

### El testigo estaba en la misma página, y nadie lo había mirado

Esta página tiene cuatro tablas de posiciones —Apertura y Clausura por zona— y el
copy-paste no las tocó. Contrastadas contra las dos versiones del fixture:

| tabla | nuestra grilla | RSSSF |
|---|---|---|
| Apertura Zona Sur | **0 / 12** | 12 / 12 |
| Apertura Zona Norte | 9 / 12 | **12 / 12** |
| Clausura Zona Sur | 12 / 12 | 12 / 12 |

La tabla le da la razón a RSSSF en cada club y se la quita a la grilla, y el
Clausura empata 12-12 — o sea que lo copiado es el Apertura, no al revés. **La
página se arbitra a sí misma.**

Y no la veíamos porque `posiciones` busca sus tablas bajo un encabezado que diga
«Tabla de posiciones», y acá viven bajo `=== Primera fase ===`. Eso se arregló
después, y destapó siete páginas más en la misma situación: ver [Ocho páginas que
tenían árbitro y no lo sabían](#ocho-páginas-que-tenían-árbitro-y-no-lo-sabían).

### `Reemplazo`, y por qué hacía falta un tipo nuevo

Los tres tipos de corrección que había arreglan **un campo** de una fila que por
lo demás describe el partido que dice describir: el nombre de un club, el
marcador, la cancha. Acá eso no se sostiene — la fila entera está de más y el
partido que iba ahí falta.

Y ninguno podía expresarlo por otra razón, más concreta: emparejan por
`(jornada, local, visita)`, y las filas copiadas son **idénticas** en los dos
torneos. Una corrección del Apertura enganchaba con dos partidos y no se
aplicaba, que es la conducta correcta. Por eso `Reemplazo` lleva **llave** —la
sección de nivel 2— y con eso identifica una sola.

Son catorce: diez filas del copy-paste y cuatro marcadores sueltos que la misma
tabla arbitra. Aplicadas, las tres tablas cierran exacto, los diez duplicados
desaparecen, y el torneo pasa de **15 partidos sin fecha a 1**.

### El que queda, y por qué no se toca

La Florida vs Sportivo Patria, Clausura Fecha 10. Se abandonó y el fallo fue
**«0-1 en contra de los dos»** — los dos equipos pierden 0-1, que no es un
marcador y nuestro esquema no puede expresarlo. Es el mismo caso que
Laferrere–Dock Sud en la Primera C 2015. Queda sin fecha y anotado, que es lo
único honesto que se puede hacer con él.

## Ocho páginas que tenían árbitro y no lo sabían

Al arreglar el copy-paste del Argentino A quedó una punta suelta: sus tablas de
posiciones existen, y `posiciones` no las encontraba. Las busca bajo un encabezado
que diga «Tabla de posiciones», y ahí viven bajo `=== Primera fase ===`.

Una tabla de posiciones **se declara**: su fila de encabezado nombra las columnas
—`Equipo | Pts | PJ | PG | PE | PP | GF | GC | Dif`—. Buscarla por ahí, y no por
el título de la sección que la contiene, es lo único que encuentra las que viven
bajo cualquier otro rótulo.

### La trampa, que apareció al medirla

El primer intento tomó también las **tablas de descenso**, que tienen exactamente
las mismas columnas. Y por el desempate de max-PJ —traen 22 partidos contra los
11 de una fase— **desplazaban a las tablas de zona**, que son las primarias.

No es un problema teórico y se midió: la tabla de descenso del Argentino A
2005-06 coincide con la suma de las cuatro de zona en 17 de 23 clubes, o sea que
es exactamente eso, una suma. Y en el club donde no coincide, **el equivocado es
el agregado**: a 9 de Julio (R) le pone `GF29` donde las de zona suman 39. Dejarla
entrar hacía que el árbitro comparara contra una tabla derivada y con un error
propio, y denunciara tres contradicciones que no existen. Se excluyen las
secciones de descenso, promedios, anual y acumulada.

### Y encontrarlas no alcanzaba

Con las tablas ya visibles, el árbitro seguía sin poder usarlas: **0 comparables**.
Esas páginas reparten sus tablas por fase —una por `== Torneo Apertura ==` y otra
por `== Torneo Clausura ==`, once fechas cada una— y `sumar()` agrega el torneo
entero, veintidós. El PJ no coincidía en ningún club y el cruce se salteaba a
todos.

Así que cada tabla se compara ahora contra los partidos **de su alcance**, y la
regla que lo hace seguro es una condición: el alcance es la sección de nivel 2 en
que vive la tabla, **y sólo cuando esa sección es también una llave de los
partidos parseados**. En una página normal las tablas cuelgan de `== Tabla de
posiciones ==`, que no es la llave de ningún partido, así que el alcance queda
vacío y todo sigue como estaba.

### El resultado

**Ocho páginas pasaron de no tener árbitro a tenerlo**, y traen 27 discrepancias
que antes no se veían:

| página | filas de tabla | avisos |
|---|---|---|
| Primera C 2024 | 50 | 6 |
| Torneo Federal A 2024 | 75 | 6 |
| Torneo Federal A 2025 | 76 | 4 |
| Torneo Argentino A 2010-11 | 35 | 4 |
| Primera B 2021 | 43 | 2 |
| Primera B 2024 | 44 | 2 |
| Torneo Federal A 2017-18 | 83 | 2 |
| Torneo Federal A 2016-17 | 77 | 1 |

Lo que dice que el alcance está bien elegido no es que aparezcan avisos: es que
**el PJ coincide**. En cinco de las ocho lo hace en el 100 % de las filas, y en
las otras tres en la mayoría. Si el alcance fuera el equivocado, no cuadraría.

El dataset no cambia: son avisos, no correcciones.

## La columna que se escribe con signo

Salió de una verificación adversarial que fue a preguntarse algo simple: por qué la
tabla del Argentino A 2010-11 tenía **menos filas que clubes**.

La respuesta es una línea:

```python
numeros = [c for c in celdas if re.fullmatch(r"-?\d+", c)]     # rechaza "+31"
```

La columna DIF se escribe **con signo cuando es positiva**. Con ese regex la celda no
cuenta como número: la fila pierde una, el corte de las últimas ocho columnas se corre,
y la guarda de coherencia —`GF − GC == DIF`— la descarta entera.

Y descarta **justo a los punteros**: caen todas y sólo las filas con diferencia de gol
positiva. Eso es lo que lo hacía difícil de ver — la tabla seguía existiendo, con la
mitad de arriba faltando, y nada fallaba.

| página | filas antes | después |
|---|---|---|
| Primera C 2008-09 | 10 | **20** |
| Primera C 2009-10 | 13 | **20** |
| Torneo Argentino A 2010-11 | 19 | **25** |

**23 filas recuperadas, ninguna perdida.** Y con ellas el diagnóstico cambia: en el
Argentino A 2010-11, Huracán (TA) dejaba de tener socio porque su socio era una de las
ocho filas que se caían. El cruce inventaba un huérfano que no existía.

## Dos páginas que tenían árbitro y grilla, y no se hablaban

El TODO decía que el Argentino A 2011-12 y el 2012-13 «tienen tabla y ni un
partido». La mitad era falsa: **los partidos estaban**, los 385 de cada una, con
su `Fecha 1`, su marcador y su día. Lo que fallaba era la **clasificación de
fase** — todos quedaban como `eliminacion`, y `posiciones.sumar` sólo cuenta la
fase de zonas. La página tenía sus tablas leídas y cero partidos con que
cruzarlas.

La causa es un default razonable que envejeció. El parser busca los resultados
bajo un `=== Resultados ===`; lo que no cuelga de ahí cae a un camino de respaldo
—el que recoge reducidos y promociones— que **forzaba** `fuera_de_la_liga=True`.
Estas páginas ponen su fase regular bajo `== Primera fase ==` → `=== Zona Norte
===`, sin «Resultados» en el medio.

Ahora no se fuerza: **se le pregunta a la tabla**. Si rotula sus bloques `Fecha N`
es fase regular, salvo que la sección que la contiene diga lo contrario — y esa
salvedad conserva el caso que motivó el flag, un `Resultados` colgado de
`== Ronda de desempate ==`.

Con una trampa que vale la pena decir: **`Fecha` es también el nombre de una
columna**, la del día. Contarla haría pasar por fase regular a cualquier tabla que
publique cuándo se jugó cada partido, así que sólo se miran los encabezados con
`colspan`, que son los que separan bloques dentro de la tabla.

770 partidos cambian de fase, en dos páginas. Ningún otro campo se mueve y
ninguna página cambia de cantidad. Las dos pasan a tener árbitro: 39 y 26 clubes
comparables, con diez desvíos que antes eran invisibles.

Quedan tres partidos del Federal A 2018-19 con la misma firma que **no** cambian:
su tabla no rotula `Fecha N` con `colspan`. Se dejan anotados en vez de aflojar el
criterio para que entren.

## 34 nombres que apagaban al árbitro, y uno que le daba los partidos a otro club

La tabla de posiciones y la grilla de resultados están en la misma página y se
escriben distinto. La grilla usa la sigla —`Central Córdoba (SdE)`— y la tabla
despliega el nombre entero: `Central Córdoba (Santiago del Estero)`. Son 34
nombres así, todos del Argentino A y el Federal A, que es donde los clubes
comparten nombre. La celda de la tabla no lleva wikilink, así que no hay artículo
con que resolverla: la fila queda a nombre de un club que el padrón no conoce y
**se cae del cruce sin decir nada**.

Diez de los 44 que se contaron al principio no eran nombres sino **llamadas al
pie**: `Cipolletti (*)`, `Unión (Sunchales) <sup>1</sup>`. El barrido general de
tags saca el `<sup>` y deja el número suelto, y el club pasa a llamarse «Unión
(Sunchales) 1». Eso es limpieza, no padrón, y se arregló en `limpiar`.

Los 34 restantes **no se emparejaron por parecido** — el propio
[`fad/equipos.py`](fad/equipos.py) prohíbe eso desde su docstring, con el ejemplo
de que «Estudiantes» a secas es sólo el de La Plata. Se emparejaron por
**cardinalidad**: la tabla tiene tantas filas como clubes el plantel, así que si
en una zona sobra un solo nombre desconocido y falta un solo club, la identidad
está forzada. Treinta cerraron así. De los otros cuatro, tres cerraron por
eliminación dentro de su zona, y el último —`Sportivo AC`— por sus números: su
fila dice `G=5 E=2 P=3, 13:8` y ésos son exactamente los de Sportivo Las Parejas
en esa reválida, contra `3-2-3, 12:11` del otro Sportivo de la misma tabla.

**229 filas de tabla pasaron a tener árbitro**, en ocho páginas.

### El que no era lo que parecía

`Juventud Unida (SL)` cerraba por cardinalidad contra el `Juventud Unida` pelado
del padrón. Era falso: la página escribe
`[[Club Atlético Juventud Unida Universitario|Juventud Unida (SL)]]`, o sea que
es el de San Luis. La cardinalidad había emparejado **dos errores**, porque del
otro lado el Argentino A 2010-11 escribe la grilla con el nombre pelado y sus 36
partidos estaban cayendo en el club de Primera C que se llama igual.

Eso no se arregla con un alias: el alias arregla esta página y rompe las otras
seis, donde `Juventud Unida` es de verdad el de Primera C. Va por página, en
`correcciones.HOMONIMOS`, que es exactamente lo que el docstring del padrón venía
prediciendo que iba a hacer falta.

Se escribieron seis homónimos y **cinco eran redundantes**: ya estaban resueltos
uno por uno como `Correccion`, con el mismo razonamiento. Lo descubrió el aviso
de «este homónimo no engancha con nada», que se había escrito en el mismo commit.

### El detector que faltaba

`fuera_del_padron` pide que el nombre sea **ilegible**. Pero un nombre puede estar
perfectamente en el padrón y apuntar al club equivocado, y entonces nadie se
queja. El chequeo general es otro: **una fila de tabla cuyo club no jugó ningún
partido en ese alcance**. Encontró un caso más —el Argentino A 2005-06, donde la
que abrevia es la tabla y no la grilla— y al resolverlo apareció un desbalance
que estaba tapado hacía rato: la tabla del Clausura suma 406 goles a favor y 408
en contra sobre los mismos partidos, y tienen que dar igual. El chequeo de
balance exige que los clubes de la tabla y de la grilla sean el mismo conjunto, y
el nombre distinto rompía esa igualdad: **un nombre mal escrito estaba apagando
un chequeo que no tiene nada que ver con los nombres.**

### Y el testigo que se apagó solo

Al enseñarle a `limpiar` a sacar el `<sup>`, murió el test que mantenía vivo a
otro mutante: el que resolvía la wikitabla por el nombre visible en vez del
wikilink. Lo mataba el caso de «Deportivo Merlo 1», y cuando la limpieza dejó de
necesitar el wikilink **ahí**, el mutante quedó vivo sin que ningún test se
pusiera rojo. Es la segunda vez que pasa lo mismo en este repo. El testigo se
repuso con el único caso donde el wikilink es irremplazable: dos filas con el
mismo nombre visible y distinto artículo, donde el índice de la página se
abstiene a propósito.

## El error que no falla nunca: el nombre pelado de la grilla

Los tres chequeos del cruce miraban la **tabla**. `fuera_del_padrón` pide que el
nombre sea ilegible; `sin_partidos`, que la fila no tenga contra qué cruzarse;
`contrastar`, que los goles no cierren. Ninguno ve el error que entra por la
**grilla**, y es el único que no falla nunca: un nombre pelado —`Juventud Unida`,
`Gimnasia y Esgrima`, `San Martín`— que el padrón resuelve solo, y lo resuelve al
club equivocado. Los partidos quedan prolijos, con fecha y marcador y cancha, a
nombre de otro.

Se midieron **seis señales** distintas en paralelo, cada una sobre las 131
páginas y con un escéptico atrás. El criterio no fue «parece razonable» sino uno
objetivo: **cuántos de los ocho casos históricos detecta con las correcciones
desactivadas, y cuánto ruido deja con ellas puestas.** Tres sobrevivieron.

### `homonimo_de_la_pagina` — el que faltaba

Un club sin desambiguador al que la página **no enlaza nunca**, teniendo un
homónimo al que sí enlaza **y además pone en su tabla**. Las tres condiciones
están medidas, y la tercera es la que hace el trabajo:

| variante | de los 8 | casos con las correcciones puestas |
|---|---:|---:|
| crudo pelado + sin wikilink + familia del padrón > 1 | 4 | **3683** |
| \+ la página enlaza otro candidato | 6 | 21 |
| \+ ese candidato además tiene fila de tabla | 6 | **0** |

Sin la tercera quedan catorce falsos de la Copa Argentina, donde `Independiente`
pelado es el de Avellaneda. Pedir la fila los apaga a los catorce, porque la Copa
es eliminación directa y no publica tabla. Con las correcciones puestas **no dice
nada**; sacándolas prende seis veces y las seis tiene razón.

Una reserva medida, que vale más que el titular: de los ocho casos, **cinco ya
los agarraba `validar.nombres_en_el_padrón`**, que además es grave y frena el
build — son nombres que el padrón no resuelve *en absoluto*. Los verdaderamente
silenciosos, donde el padrón contesta y contesta mal, son **tres**: `Juventud
Unida` del Argentino A 2010-11 (36 partidos), `Unión` de la misma página, y
`Ferro Carril Oeste` del Federal A 2016-17. El agujero era más chico de lo que
parecía, y ahora está tapado.

### `filas_que_no_cierran` — lo que la guarda tiraba en silencio

Una fila de wikitabla tiene que cerrar consigo misma (`GF − GC == DIF` y
`PG + PE + PP == PJ`). La guarda es correcta —una fila mal tipeada no puede
desmentir a nadie— pero descartaba **sin decirlo**, y eso deja al club sin
árbitro. Ningún otro chequeo puede suplirlo: no se opina sobre una fila que no se
parseó. Son tres en 131 páginas, y las tres son erratas de la fuente que la
grilla desmiente sola:

| página | fila | qué no cierra |
|---|---|---|
| B Nacional 2011-12 | Almirante Brown | `14+13+10 = 37`, PJ dice 38 |
| B Nacional 2011-12 | Guillermo Brown | `9+11+17 = 37`, PJ dice 38 |
| Primera C 2010-11 | Leandro N. Alem | `32−48 = −16`, DIF dice −15 |

Esas dos tablas quedaban con 18 filas para 20 clubes y 19 para 20, sin que nadie
lo mencionara.

### `pj_que_no_coincide` — lo que `contrastar` mira para callarse

`contrastar` compara goles y se calla cuando el PJ no coincide, con razón: sumar
sobre conjuntos distintos daba 38 avisos falsos por torneo con reducido. Pero un
PJ distinto es un síntoma por derecho propio, y ahí se callaba justo cuando había
que hablar.

La guarda **no es un umbral sobre la diferencia sino sobre cuánta tabla se
mueve**: si se desvía más de la mitad de los clubes comparados, el alcance no
opina. Esa forma separa las dos causas sin tocar la magnitud — un club mal
atribuido corre uno o dos de veinte; una tabla que cuenta otra cosa se mueve
entera y con el mismo delta. De 67 desvíos quedan 11, sin perder ningún caso
conocido.

Y los avisos se agrupan **por delta**, porque un partido toca a dos clubes: dos
clubes corridos lo mismo y para el mismo lado son *un partido entre ellos*. Los
11 avisos son 6, cada uno nombrando el par. Dos ejemplos de lo que encontraron:

- **Primera C 2016**: Defensores de Cambaceres y Sportivo Barracas **nunca se
  enfrentan** en la grilla, y en un todos-contra-todos de veinte tienen que
  haberlo hecho. Falta ese partido.
- **B Nacional 2017-18**: la grilla tiene *dos* Aldosivi–Almagro, y el segundo es
  del 4 de mayo, después de la fase regular y sin número de fecha: un partido de
  reducido clasificado como fase de zonas.

Los dos quedan como aviso abierto. Localizar no es arbitrar.

## El partido que faltaba en la Primera C 2016

Lo encontró el chequeo de PJ, y resultó ser el caso más limpio de todo el repo:
**cuál** es el partido no hay que elegirlo, y **cuánto salió** tampoco.

El torneo es todos contra todos: 20 clubes, 19 fechas. Los veinte juegan 19
partidos salvo Defensores de Cambaceres y Sportivo Barracas, que juegan 18; la
Fecha 1 tiene nueve partidos en vez de diez; y el único par que no se cruza nunca
en todo el campeonato es exactamente ése. No hay nada que decidir.

La fila **está** en el wikitexto. Lo que está roto es la celda del marcador:

```
|Defensores de Cambaceres
|bgcolor="#d0e7ff"|`''' - 0`
|Sportivo Barracas
|12 de Octubre
|rowspan=2|5 de febrero
```

Se perdió el gol del local en alguna edición, y el parser hace bien en descartar
la fila. Lo que faltaba era el aviso, y ahora existe.

### El marcador, con dos testigos que no dependen uno del otro

**La tabla de posiciones.** Es el único partido que les falta a los dos clubes,
así que restar la grilla de la tabla da sus goles exactos — y se puede leer dos
veces, una por club:

| club | tabla | grilla | delta |
|---|---|---|---|
| Defensores de Cambaceres | PJ19 GF20 GC27 | PJ18 GF20 GC27 | `PJ+1 GF+0 GC+0` |
| Sportivo Barracas | PJ19 GF22 GC24 | PJ18 GF22 GC24 | `PJ+1 GF+0 GC+0` |

Las dos lecturas dan lo mismo y la tabla además **cierra sola** (ΣGF = ΣGC = 457).

**El resaltado de la propia fila.** La página pinta la celda del resultado cuando
el partido terminó empatado, y el nombre del ganador cuando no. Verificado en sus
189 filas legibles **sin una sola excepción**: 54 empates, los 54 pintados; 135
con ganador, ninguno. La fila rota está pintada. Y el `0` del visitante sobrevivió.

Los dos testigos dicen **0-0**, y hay un tercero de confirmación: con ese
marcador puesto, `contrastar` deja de encontrar desvíos en **toda** la tabla. Si
hubiera sido cualquier otro, los goles de esos dos clubes no cerrarían.

### `Faltante`, el quinto tipo de corrección

Es el único que **agrega** una fila en vez de arreglar una, así que la vara es
más alta: el marcador tiene que salir de la página misma y con dos testigos
independientes. Si hay que ir a buscarlo afuera, no entra y queda el aviso
abierto — que es lo que sigue pasando con Laferrere–Dock Sud y con La
Florida–Sportivo Patria.

Dos detalles que el mecanismo cuida:

- **El contexto se hereda de un hermano de la misma jornada** en vez de
  escribirse a mano. Torneo, fase y zona son de la ronda; escribirlos aparte haría
  que esta fila fuera la única del torneo que dice otra cosa, y eso no falla: sale
  al CSV con otro `group` y el que lo consuma cuenta dos zonas donde hay una.
- **Si la página se arregla, avisa.** El día que alguien complete la celda en
  Wikipedia el parser va a leer la fila, y sin la guarda el partido entraría dos
  veces.

Con el partido puesto, la Primera C 2016 cierra entera: 190 partidos, los veinte
clubes con 19, las diecinueve fechas con diez, y cero desvíos contra su tabla.

## Media solución que estuvo dos años a la vista

El otro hallazgo del chequeo de PJ era el **desempate por el título** de la B
Nacional 2017-18: Almagro y Aldosivi terminaron empatados en el primer puesto y
jugaron un partido único en cancha neutral para definir al campeón. Ese partido
estaba en el dataset como **fase regular**, así que los dos aparecían con 25
partidos donde su propia tabla les contaba 24.

Lo interesante es que el parser ya lo conocía. Este comentario estaba escrito
desde antes, palabra por palabra:

> Un titulo de Wikipedia cierra la jornada. Dentro de la seccion de resultados
> puede aparecer `=== Partido de desempate del primer puesto ===` — la final del
> campeonato, cuando dos equipos terminan igualados — y ese partido NO es de la
> ultima fecha: es otra cosa.

El arreglo de entonces era correcto y estaba a mitad de camino. Cortaba la
jornada —sin eso, la Fecha 25 terminaba con trece partidos y dos equipos jugando
dos veces— pero se quedaba ahí: **miraba el título para borrar estado, no para
etiquetar**. El partido dejaba de ser de la Fecha 25 y seguía siendo fase
regular, que es la mitad que faltaba.

Y no era invisible: el dato estaba mal a la vista de cualquiera que sumara
partidos por club. Lo que no había era quién lo mirara. El chequeo de PJ lo
encontró a los cinco minutos de existir.

### El arreglo

Un título de Wikipedia dentro del cuerpo es una etiqueta de sección igual que un
`!colspan|...`, así que ahora se lee igual: si además **nombra una ronda**, lo que
sigue es una llave y no fase regular.

Con una salvedad que es todo el diseño: la lista de rondas
(`parser._ES_RONDA`) es corta y explícita a propósito, y sigue siéndolo. Un
título cualquiera cierra la jornada y nada más. Convertir en llave a todo lo que
tenga título propio sacaría de la fase de zonas a páginas enteras del ascenso,
que cuelgan su fase regular de títulos propios — es exactamente el error opuesto,
el de las 770 filas que hubo que reclasificar en la otra dirección.

Lo único que hizo falta agregar a la lista fue `desempate` en la alternativa que
ya decía `partido de ida|vuelta`: el título empieza con «Partido de», así que el
`^desempate` que ya estaba no lo alcanzaba.

**Cambian exactamente dos partidos en las 131 páginas**, y el segundo no lo
buscaba: el Sarmiento (J)–Arsenal de la B Nacional 2018-19, que era el mismo caso
y era el otro aviso de PJ que había quedado abierto. Un arreglo, dos avisos
cerrados. Los dos pasan a `eliminacion`, con su ronda por `matchday` y con
`neutral` ya en `true`, que eso el parser lo venía leyendo bien del encabezado
`Equipo 1 / Equipo 2`.

## El partido que existe y que el esquema no puede escribir

El último aviso de PJ que quedaba abierto era la Reválida del Federal A 2018-19:
la tabla le contaba ocho partidos a Deportivo Roca y a Independiente (N), y la
grilla les daba siete. La aritmética lo dejaba servido — Zona A de cinco clubes
y diez fechas, todos los pares con dos partidos salvo ése con uno, y la Fecha 10
con un partido en vez de dos.

La fila estaba. Su resultado, no:

```
|Independiente (N)
|PP - PP{{refn|El partido finalizó 4 a 1, pero se le dio por perdido a ambos
equipos al considerarse que procedieron de manera dolosa para asegurar el
resultado a favor de Deportivo Roca con la inclusión indebida del jugador
Joan Manuel Artaza por parte de Independiente (N).}}
|Deportivo Roca
```

`PP - PP` es **partido perdido para los dos**. Terminó 4 a 1 y el Tribunal se lo
dio por perdido a ambos por arreglar el resultado.

**Y eso no se puede escribir.** Una fila del CSV tiene un `home_score` y un
`away_score`; cualquier par de números que se ponga ahí afirma que alguien ganó.
No es una limitación del parser sino del esquema, y por eso este partido **no
entra** — igual que La Florida–Sportivo Patria del Argentino A 2005-06, que es el
mismo caso desde 2006.

La tabla lo confirma y de paso explica otra cosa: le pone `GF+0 GC+1` **a cada
uno**, o sea 0-1 en contra de los dos. Por eso la tabla de esa Reválida suma 184
goles a favor y 186 en contra: es la única del corpus que no cierra por un motivo
legítimo. El desbalance *es* el fallo.

### Lo que sí se arregla: que lo diga

Descartar la fila es correcto; hacerlo en silencio no. Sin aviso, el hueco
aparece como un partido que falta —el chequeo de PJ lo denuncia, porque la tabla
sí lo cuenta— y manda a buscar un error de lectura que no existe. Es «vacío no es
lo mismo que ilegible» otra vez, la tercera en este repo.

`parser.partidos_anulados` lo nombra. Dos casos en las 131 páginas: éste y la
Copa Argentina 2013-14, donde Estudiantes Unidos y Belgrano de Esquel
abandonaron el torneo por problemas económicos. El segundo obligó a que el
detector no mire una posición fija: la liga ordena Local-Resultado-Visitante y la
copa Fecha-Estadio-Equipo 1-Partido-Equipo 2, así que se busca la celda anulada
donde caiga y los clubes se toman de sus dos vecinas.

Ahora la página lleva los dos avisos, y juntos cuentan la historia entera: uno
dice que la tabla cuenta un partido más, el otro dice por qué.

## Doce tandas de penales que no estaban

El repo ya sabía leer una tanda escrita como `{{small|(5)}} 1 - 1 {{small|(4)}}`.
Wikipedia la escribe de otra forma más, y esa no la leía nadie:

```
|San Martín (T)
|'''1 - 1'''<br><hr><small>[[Penaltis|Pen.]]<br>3 - 4</small>
|Villa Mitre
```

Son **doce partidos**, y no cualquiera: la final del Argentino A 2005-06, la del
Federal A 2022, la del 2023, el desempate por el tercer ascenso de 2023. Es
justo donde la tanda no es un detalle sino **quién ascendió**.

La segunda notación pide la **palabra escrita** y no sólo dos números, y eso no
es cosmético: `0:1 (0:0)` es el **entretiempo**, y leerlo como penales es el
error que el docstring del parser pone como ejemplo de código que miente en vez
de fallar. Entre la palabra y los números se tolera marcado, porque la palabra
suele venir dentro de un wikilink y la tanda en el renglón de abajo.

La celda cruda se lleva **por columna y no por índice**: con un `rowspan` en una
columna temprana los índices se corren, y buscar la tanda en `celdas[1]` la
leería de la columna de al lado.

### Y un partido que se perdía por una raya

`1 – 0` con raya media (U+2013) se ve igual que `1 - 0` y no lo es. `_marcador`
aceptaba `-` y `:`, así que esa fila **no tenía marcador y el partido se
descartaba entero**: el desempate por el descenso del Argentino A 2005-06,
General Paz Juniors–Cipolletti, no existía en el dataset. Es uno solo en las 131
páginas, y esa es exactamente la razón por la que no se veía.

## El triangular que estaba como llave

El chequeo de PJ dejó abierto un último caso: tres partidos del Federal A 2018-19
en fase de eliminación teniendo jornada `Fecha 1`, `2` y `3`. **Y mi propia nota
sobre por qué era falsa** — decía «su tabla no rotula los bloques con `colspan`»,
y las tres tablas los rotulan.

Lo que pasaba es otra cosa. Gimnasia y Tiro, Juventud Antoniana y San Martín (F)
terminaron empatados en 25 puntos en la tabla de descenso, y jugaron un
**triangular** de tres fechas —una por ronda, con un libre cada vez— para definir
quién bajaba. La sección se llama `Ronda de desempate`, y ese nombre lo matchea
`_ES_RONDA`, así que la sección le ganaba al rótulo de la tabla.

Una mini-liga no es una llave. Ahora **la tabla decide**: si rotula sus bloques
`Fecha N`, es fase regular aunque la sección se llame como una ronda. Es la misma
pregunta que ya hacía el camino de respaldo, así que los dos coinciden.

Se midió antes de tocarlo, porque el riesgo era tragarse las llaves de verdad: de
las **dieciséis** secciones del corpus cuyo título parece una ronda, ésta es la
**única** que rotula fechas. Las otras quince —octavos, cuartos, semis, finales,
primera, segunda y tercera ronda— no rotulan ninguna y no se mueven. Cambian tres
partidos, y ninguno más.

Y hay confirmación independiente, que no busqué: al pasar a fase de zonas, esa
mini-liga entra al cruce contra **su propia tabla de posiciones**, y coincide
clavado en los tres clubes — `2, 3-3` / `2, 2-2` / `2, 1-1` de un lado y del
otro. La página se verifica sola.

## La región ciega, y el testigo que sí tiene una copa

Los cuatro chequeos del cruce comparan la grilla contra **la tabla de
posiciones**. Eso deja una región donde ninguno puede opinar: **una copa no
publica tabla.** Sus catorce páginas son casi todo el punto ciego —1 299 lados de
partido, el 1,7 % del dataset—, y ahí una grilla equivocada no tiene contra qué
contrastarse. Se probó por inyección: falsificando la tabla del Argentino A
2010-11 para que coincida con la grilla, los nueve chequeos quedan mudos.

Pero una copa sí tiene un segundo testigo: **el cuadro de llaves**. Lo escribe
otra mano, con otros nombres y en otro formato, que es exactamente lo que hace
falta. `fuera_del_cuadro` lo pone a trabajar.

### Leerlo cuesta más de lo que parece

Tres cosas rompen la lectura ingenua, y las tres estaban:

- **Partir los parámetros por cualquier `|`** rompe el wikilink:
  `[[Arsenal Fútbol Club|Arsenal]]` queda en dos y el club pasa a llamarse
  `[[Arsenal Fútbol Club`. Hay que partir a nivel cero.
- **Cortar en el fin de línea** tampoco sirve: la mitad de los cuadros escriben
  varios parámetros en el mismo renglón.
- **Cerrar en el primer `}}`** deja afuera medio cuadro, porque adentro hay otras
  plantillas (`{{small}}`, `{{bandera}}`). Va por llaves balanceadas — y el `}}`
  final **no** entra en el cuerpo: si entra, se lo queda pegado el último
  parámetro y ese club se pierde sin que nada falle.

### Qué encuentra

23 avisos, en dos niveles porque son dos cosas distintas:

- **Uno por club** cuando el que falta tiene un **homónimo que sí juega**. Son 14,
  y es la firma que este chequeo vino a buscar: la Primera B 2014, 2015 y 2017-18
  escriben `Estudiantes` a secas en el cuadro —que el padrón resuelve al de La
  Plata, un club de Primera— mientras la grilla juega Estudiantes (BA). El
  Argentino A 2005-06 nombra `Talleres (C)` donde la grilla juega Talleres (P).
- **Uno por página** cuando no hay homónimo: ahí lo que falta no es un nombre sino
  **los partidos**. La Copa Argentina 2019-20 tiene un cuadro de 64 y la grilla
  trae 42. Es un hueco de completitud conocido, y se dice en una línea y no en
  noventa y seis.

### Lo que se resigna, dicho

Los nombres que el padrón no reconoce se saltean. Un cuadro trae, mezcladas con
los clubes, marcas que no lo son —`w/o`, `p.` por penales, `t. s.` por tiempo
suplementario, el `1:` de la siembra— y no se distinguen por su forma de un club
que al padrón le falte. El costo es no ver las grafías que **sólo** aparecen en el
cuadro: `Sarmiento (Junín)` y `San Martin (F)` sin tilde son clubes de verdad
escritos de una forma que el padrón no tiene, y como no entran por ningún partido,
`nombres_en_el_padrón` tampoco los ve. Es una elección, no una propiedad.

## 240 partidos que las copas no entregaban

El chequeo del cuadro dejó dicho que a las Copa Argentina viejas les faltaban
partidos: el cuadro tiene 64 clubes —63 llaves— y la grilla traía 20, 22, 39, 40.
Lo que hacía sospechar que no era un problema de la fuente es que **la 2025
parsea 63 de 63 con el mismo parser**. Lo que cambia es cómo están escritas las
páginas viejas.

Se diagnosticaron las catorce ediciones en paralelo, con un escéptico por lote. La
causa principal es una sola, y es de las que no fallan:

```
<small>(4)</small> 0 - 0 <small>(5)</small>      la tanda, como la escriben las viejas
{{small|(4)}} 0 - 0 {{small|(5)}}                como la escriben las nuevas
```

`limpiar` **borra las plantillas enteras** pero de los tags HTML saca sólo el tag
y deja el contenido. Así que la celda vieja queda en `(4) 0 - 0 (5)` y la nueva en
`0 - 0`. Y `_marcador` está anclado al principio —a propósito: sin el ancla,
cualquier par de números de la celda pasaría por marcador—, así que la fila se
descartaba entera. Con un comentario que además mentía: *«ronda en curso: la fila
está pero sin marcador»*, sobre un torneo de 2013.

Son cuatro arreglos, ninguno inventa un dato y todos salen de la misma tabla que
el parser ya leía:

| | qué | rinde |
|---|---|---:|
| **la tanda adelante** | `_marcador` reintenta sacando un `(N)` inicial | +155 |
| **`{{nowrap}}` anidada** | el no-goloso cerraba en el `}}` de la `{{bandera}}` de adentro, el desenvuelto quedaba mal armado y el barrido general **se comía al club**: la celda quedaba vacía | +28 |
| **rondas de entrada** | `Preclasificatorio`, `Ronda previa`, `Fase final I/II` no estaban en el regex de títulos, así que esas secciones no se miraban nunca | +35 |
| **rondas anidadas** | `=== Semifinales ===` ya se come sus `==== Semifinal 1/2 ====`, y los dos matchean: cada semi entraba dos veces | −2 |

Los dos últimos son obligatorios y no por lo que rinden: sin ellos el corpus pasa
de **0 avisos graves a 5** —dos duplicados y tres clubes fuera del padrón— y el
build corta. Los tres clubes que hubo que dar de alta son reales y entran por
estas rondas nuevas: Alianza de Moldes, Jorge Gibson Brown y Villa Cubas.

Una decisión que vale anotar: `Preclasificatorio` y `Ronda previa` van **sólo** en
el regex de títulos y **no** en la cadena de llaves. A la Ronda previa entran
cuarenta equipos frescos que no ganaron el Preclasificatorio, así que pedirle a
cada uno que venga de la ronda anterior da cuarenta y ocho avisos falsos. Se
saltea con uno solo, que es más barato y no miente.

**Resultado: 240 filas nuevas, cero perdidas.** Trece de las catorce ediciones
quedan en su total exacto —2013-14 son 53 y no 63, porque su cuadro arranca en
dieciseisavos— y la 2026 está en curso. La única que sigue incompleta es la
2018-19, a la que le falta un partido cuya fila está rota en la fuente
(`|-bgcolor=#F5FAFF}|align=center|...`, sin salto de línea) y que ningún arreglo
de parser recupera.

## El mapa de zonas, y tres maneras de no publicar una tabla

El pendiente decía que a los cinco `Torneo Argentino A` les faltaba **el mapa de
nombres de cada temporada, que es lo caro**. Al medirlos, eso era cierto para
ninguno: son cinco páginas y **tres causas distintas**, otra vez.

### La fuente tiene dos formatos de tabla

Desde 2011-12 RSSSF publica los goles a favor y en contra en **columnas
separadas** (`42  23`) en vez de pegados con un guion (`42-23`). Nuestro lector
sólo conocía el segundo, así que `arg2012` y `arg3-int2013` figuraban como *«no
publican ninguna tabla»* — una afirmación sobre nuestro lector, no sobre la
fuente.

**Cuál de los dos es se lee, no se adivina.** El formato nuevo trae un encabezado
que nombra sus columnas:

```
No. Team 			      G   W   D   L  Gf  Ga   P
```

Distinguirlos por el regex sería peligroso: el permisivo también matchea una fila
del formato viejo, corriendo las columnas y leyendo números que no son. Y además
el encabezado separa **dos cosas que se escriben igual** — los archivos viejos
rotulan `Table:` a secas las tablas de *media* temporada, y el Argentino A 2006-07
tiene seis. Abrirlas como si fueran la acumulada le mete a cada zona una segunda
tabla distinta, y los ocho clubes que esa página respalda se van a cero. El
encabezado no aparece en ninguna: medido, está en `arg2012` y `arg3-int2013` y en
ningún otro archivo de los que leemos.

### El mapa de zonas, que no existía

Existía `FASES` —cómo rotula la fuente cada **fase** y cómo la llamamos nosotros—
y no existía el equivalente para la **zona**. El cruce comparaba los dos rótulos
literalmente, y por eso funcionaba sólo cuando coincidían solos:

- en las páginas **sin grilla** los partidos salen de RSSSF, así que la zona de
  nuestras filas *es* el rótulo de RSSSF y la comparación es contra sí misma;
- en las de una sola zona los dos lados dicen `""` y también coinciden.

En cuanto los dos lados nombran la misma zona distinto —`Zone 1` contra
`Primera fase - Zona 1`— no cruza ni un club, la tabla se descarta por
cardinalidad, y desde afuera se ve igual que *«la fuente no publica tablas»*.

`ZONAS` lo declara, con la **fase en la clave**: un archivo repite los nombres de
zona entre fases, y el Argentino A 2010-11 rotula `Zone 1` en la regular y otra vez
en la final. Por defecto la traducción es la **identidad**, y tiene que serlo:
volverla obligatoria se lleva puestas las cuatro temporadas que ya cruzaban.

Con eso más el recorte de su sección —`arg2011` es la página del año, con siete
divisiones adentro— el **Argentino A 2010-11 respalda sus 24 clubes**, las tres
zonas de la fase regular, y el dataset no se mueve ni una fila.

| | páginas | clubes respaldados |
|---|---:|---:|
| antes | 9 | 177 |
| ahora | 10 | **201** |

### Y las tres que faltan, ahora sí con su motivo

- **2004-05** — RSSSF no publica **ninguna** tabla de esa temporada: `arg3-int05`
  son 306 renglones de índice. No hay nada que leer mejor.
- **2005-06, 2011-12 y 2012-13** — las tres tienen tablas legibles y clubes que
  calzan, y lo que falta es **nuestro** lado: las páginas publican
  `=== Zona Norte` / `===== Zona Sur` y el parser no las mira. Los partidos entran
  por el camino de respaldo, que pasa la llave pero **no** la zona, así que sus
  filas salen con la columna `group` vacía.

Ese último es el hallazgo que vale más que el cruce: no es una limitación de la
fuente sino un agujero nuestro, y taparlo llena una columna que hoy se publica
vacía en unas 1 150 filas. Va con su propio arnés de equivalencia, porque cambia
el dataset y no sólo un chequeo.

## El testigo que estaba escrito y miraba el archivo equivocado

La **foja** es el cruce que le pregunta a RSSSF si nuestra suma coincide con la
tabla que ella misma publica al lado de sus partidos. Existía hacía rato, pero
corría en cuatro páginas: las que no tienen grilla y sacan los partidos de ahí. En
las otras diez que tienen mapa de RSSSF escrito devolvía **cero** respaldos, y esa
línea de ceros parecía un límite del formato.

No lo era. Eran tres cosas distintas, y las tres se veían igual desde afuera.

### RSSSF publica su tabla dos veces

La B Nacional 2007-08 y las Primera C 2008-09 y 2009-10 traen **dos tablas
idénticas** bajo la misma clave: RSSSF imprime la tabla final arriba del archivo,
como resumen antes de la primera fecha, y de nuevo abajo después de la última.

El cruce exige *una sola* tabla por clave y se abstiene cuando hay dos. Y hace
bien —dos tablas **distintas** bajo el mismo rótulo no dicen cuál cubre qué
partidos—, pero ante una copia no hay nada que elegir. Sesenta clubes sin respaldo
por una guarda que estaba cuidando una ambigüedad que no existía.

El descarte va por **clave y contenido**, así que la guarda queda entera: dos zonas
distintas no se tocan nunca, y dos tablas distintas de la misma zona siguen siendo
dos.

### El recorte estaba escrito dos veces, y faltaba la tercera

Desde 2010-11 RSSSF deja de darle archivo propio a cada división y las mete todas
en la página del año: `arg2011` trae la Primera, la B Nacional, la B Metropolitana,
el Argentino A, la Primera C, el Argentino B y la Primera D, una atrás de otra.

Los lectores de partidos y de llaves ya se acotaban a su sección. **El de tablas
no.** Así que en esas páginas los partidos salían de la Primera C y las tablas eran
las veinte de las siete divisiones — el cruce veía veinte bajo una clave y se
abstenía.

Es el bug más silencioso de los tres, y de una familia conocida: el recorte estaba
escrito **dos veces**, una en cada lector que lo pedía, y cuando algo se escribe dos
veces tarde o temprano se escribe distinto. Acá pasó la variante rara —la tercera
copia no se escribió nunca—, que es peor: dos copias que divergen se notan cuando
dan resultados distintos, y una que falta no da ningún resultado. Ahora vive en un
solo `_acotar` que los tres piden.

Eso mueve la red de tests, y hay que moverla a propósito: antes cada copia tenía su
mutante; ahora el mutante compartido muere por cualquiera de los tres, y lo que hay
que sostener pasa a ser **que cada lector pida su recorte**. Va con un mutante por
lector. Es la lección de `teams.py` del repo hermano —unificar sin mover la red deja
tests que ya no miran nada—, esta vez aplicada en el mismo commit.

### Y la tercera no se arregló

Los cinco Argentino A publican **una tabla por zona**, y para cruzarlas hace falta
el mapa de nombres de cada temporada, que no está escrito. Siguen en cero. Pero
ahora están en cero por abstención declarada y no por leer el archivo equivocado,
que no es lo mismo aunque el número sea igual.

### Lo que rinde

| | páginas | clubes respaldados |
|---|---:|---:|
| antes | 4 | 75 |
| ahora | 9 | **177** |

Cinco temporadas enteras nuevas —B Nacional 2007-08, Primera C 2008-09, 2009-10 y
2010-11, y Primera B 2010-11— en las que RSSSF le da la razón a nuestra grilla en
las seis cifras, club por club. **Cero desacuerdos**, y el dataset no se mueve: la
foja no escribe filas, mejora un aviso.

Corre cuando la página se reprocesa —`python build.py --rehacer`—, igual que todos
los chequeos de una temporada cerrada: el build diario reusa sus filas del CSV y no
vuelve a bajar la página. Que es el punto de tenerlas cerradas.

### El aviso decía algo que iba a volverse falso

Cuando un club no cierra contra su tabla y la foja lo respalda, el aviso escribía:

> *«esos partidos no salen de esta página sino de una fuente externa»*

Cierto mientras la foja corría **sólo** sin grilla. Falso apenas corre con grilla:
ahí los partidos sí salen de esta página, los leímos de su grilla.

Y la conclusión, además, es distinta y más fuerte. Sin grilla, que la tabla de la
fuente coincida descarta haberla leído mal y deja un desacuerdo **entre fuentes**,
que pide una tercera para arbitrar. Con grilla, que una fuente independiente
publique nuestras seis cifras respalda nuestra lectura, y el desacuerdo queda
**adentro de Wikipedia**: su tabla contra su propia grilla. No hay tercera que
traer.

Son dos ramas, y hasta hoy estaba escrita una sola — la que nunca se había visto
con una grilla al lado.

### Y la mutación encontró dos agujeros, los dos de la misma forma

Al correr `mutar.py` sobrevivieron dos mutantes nuevos, y no era casualidad que
fueran dos: son el mismo agujero visto de dos lados. Los tests probaban **las
piezas** —que `leer_tabla` sabe acotarse, que `contrastar` sabe redactar las dos
conclusiones— y ninguno probaba que **`build` se las pidiera**. El cableado no lo
miraba nadie.

Es un punto ciego con forma propia: una función chica y testeable es fácil de
probar, y justamente por eso la línea que la llama se siente ya cubierta. No lo
está. Un mutante que cambia `de_afuera=t.sin_grilla` por `de_afuera=True` no toca
ninguna función probada — cambia qué se le pasa a una.

Se tapó con tres tests que van por `build`: uno le pasa a la foja una página real
con su recorte real (con anclas inventadas se prueba el mecanismo, no el dato), y
dos espían qué recibe `contrastar` desde los dos lados del `sin_grilla`. De paso
quedó cubierto el camino sin grilla, que no tenía un solo test.

## Tests

1001 tests, sin red — se prueba el parseo, y un test que depende de que Wikipedia
esté arriba no prueba el parseo, prueba internet.

Que pasen no alcanza, así que hay mutation testing: `mutar.py` rompe el código a
propósito de 429 maneras y exige que la suite se dé cuenta de cada una.

```bash
python mutar.py
```

Encontró once agujeros reales. Uno resultó ser un **mutante equivalente** —
escribir `None` en vez de cadena vacía no cambiaba nada, porque el módulo `csv`
ya convierte `None` en campo vacío — y ahí lo que sobraba era el código, no el
test.

Otro corrigió una explicación, no un bug. El orden "normalizar y después validar"
estaba justificado en un comentario con que si no, los alias se reportarían como
clubes desconocidos. Al mutar el orden la suite no se inmutó, y mirándolo de
cerca esa razón era falsa: el chequeo del padrón acepta los alias, así que por
ese lado da igual. El orden importa por otra cosa — los demás chequeos comparan
nombres **entre sí** por igualdad de cadena, y como las llaves salen de
plantillas y las zonas de tablas, el mismo club convive escrito de dos maneras en
la misma página. Sin normalizar antes, "nadie juega dos veces por fecha" ve dos
clubes distintos y deja pasar justo lo que tenía que agarrar.

Hay una tercera manera de que un test deje de probar, más boba que las otras dos y
por eso más fácil de comer: que **no corra**. Un módulo de pytest es un módulo de
Python, así que dos funciones con el mismo nombre no son dos tests — la segunda pisa
a la primera y la primera desaparece, sin error ni warning. Pasó escribiendo el
chequeo de balance: se agregó un `test_si_no_coinciden_los_partidos_jugados_se_calla`
sin ver que el archivo ya tenía uno igual doce tests más arriba, y el original dejó de
correr. Se notó de casualidad, y para no depender de la casualidad quedó
[`tests/test_suite.py`](tests/test_suite.py), que parsea cada archivo de tests y
falla si hay un nombre repetido.

## De dónde salen los datos

Wikipedia en español, vía la API de MediaWiki, pidiendo el **wikitexto** y no el
HTML: es lo que editan las personas, y las plantillas vienen con sus parámetros
nombrados en vez de aplastadas en un `<table>`.

Las páginas están listadas a mano en [`fad/torneos.py`](fad/torneos.py). Se
podría adivinar el título por patrón, pero el fútbol argentino le cambió el
nombre y el formato al campeonato casi todos los años — Inicial/Final,
Transición, Superliga, Copa de la Liga, Apertura/Clausura otra vez — y no hay
patrón que sobreviva a eso. Una lista escrita a mano falla al agregar una
temporada, que es cuando conviene que falle.

Hay caché en disco (`.cache/`, no versionada) y una pausa mínima entre pedidos.

## El plan

- [x] **1.** Primera División 2026 (Apertura + Clausura)
- [x] **2.** Padrón de clubes con normalización, validado contra el feed de la AFA
- [x] **3.** Histórico 2016-2025 — diez temporadas, siete nombres distintos para el mismo campeonato
- [x] **4.** Copa Argentina — 2016-2026, tercer formato de página; es el único torneo donde se cruzan las divisiones
- [x] **5.** Primera Nacional, Primera B, Primera C y Federal A — 2016-2026, las cuatro divisiones que juegan la Copa Argentina
- [x] **6.** Actualización automática — dos workflows, con guarda contra achicarse
- [x] **7.** Publicado y actualizándose solo
- [ ] **8.** Seguir hacia atrás: 1991-2003, y después la era Metropolitano/Nacional

## Licencia

Código **MIT**. Datos **CC BY-SA 4.0**, heredada de Wikipedia — ver
[`LICENSE-DATOS.md`](LICENSE-DATOS.md). La columna `source` lleva la atribución
fila por fila, así que viaja con el dato.

---

Hermano mayor: [world-cup-predictor](https://github.com/rhinoah/world-cup-predictor),
el modelo de predicción del Mundial 2026 del que salió la idea de necesitar esto.

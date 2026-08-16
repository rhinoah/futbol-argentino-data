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

**Estado:** **36 966 partidos entre febrero de 2004 y hoy** — veintitrés años de
Primera División, quince de Primera Nacional, once de Primera B, Primera C y
Torneo Federal A, y diez ediciones de la Copa Argentina. **208 clubes**, 131
torneos, cero partidos sin fecha, sin marcador ni duplicados. Se actualiza solo,
todos los días.

Aparte, en [`data/sin-fecha/`](data/sin-fecha/) hay **2 345 partidos que están
completos salvo por el día en que se jugaron** — tres temporadas de Primera C, cuyas
tablas no tienen columna de fecha, y tres del ascenso que la tienen y la dejan
vacía. Van separados justamente para que el dataset
principal pueda seguir prometiendo una fecha en cada fila.

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

**[worldfootball.net](https://www.worldfootball.net/)** aporta un solo campo, y
sólo en **1 520 filas de 36 966** (4,1 %): la **fecha del calendario** de partidos
que Wikipedia publica sin fecha — las cuatro temporadas de Primera B Nacional
entre 2007 y 2011 usan tablas de tres columnas (`Local | Resultado | Visitante`) y
nada más. El partido, los equipos, el marcador y la jornada siguen saliendo de
Wikipedia.

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

Sobre **`neutral`**: sale del **reglamento de la competencia**, no de comparar el
estadio contra el de cada club. La Copa Argentina se juega a partido único en
cancha neutral y su propia página lo dice ronda por ronda, así que ahí el dato se
puede afirmar. En las ligas es `false`, con este alcance exacto: *el partido se
jugó donde dice el fixture*. **No detecta mudanzas puntuales** — un partido de
liga que se muda de cancha sigue figurando `false`. Prefiero decir eso y
documentarlo antes que deducir la localía con un padrón de estadios que todavía
no existe.

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

#### Los 21 que no cierran, ordenados

Vale separarlos, porque no son un problema sino tres, con costos muy distintos.

**Cinco tienen un solo club desviado.** Ahí no hay nada que corregir, y no es una
opinión: un marcador mal leído toca siempre a **dos** clubes, así que un club solo y
sin pareja no puede venir de un partido. La equivocada es su fila de la tabla. Son
Platense en la B Nacional 2009-10 —el caso que enseñó el patrón—, más Boca Juniors en
el Clausura 2005, Unión en el Final 2013, Racing Club en la Copa de la Liga 2023 y
Deportivo Español en la Primera B 2017-18.

**Nueve tienen todos sus desvíos apareados.** Cada par localiza un partido: los dos
clubes se cruzan, y a uno le sobran los goles que al otro le faltan. Pero *localizar
no es arbitrar*, y hay algo peor: en una liga de ida y vuelta los dos clubes se cruzan
**dos veces**, y la aritmética no puede decir cuál de las dos fechas es la mala. De
los 26 pares del dataset, sólo **cuatro** identifican un partido único.

**Siete tienen algún club sin pareja.** Eso significa más de un error en la misma
página, o un error de tabla mezclado con uno de partido. Son los caros: el Federal A
2021, el 2022, la Primera Nacional 2019-20 y 2026, la Primera C 2011-12 y 2026, y el
Clausura 2008.

La conclusión práctica es incómoda y conviene decirla: **de los 21, sólo un puñado se
puede cerrar sin salir a buscar fuente por partido.** Los cinco del primer grupo ya
están explicados por su propio aviso; los del segundo necesitan una crónica que diga
cuál de las dos fechas; los del tercero, varias.

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

**Los 438 partidos van a `data/sin-fecha/`**, que ahora tiene 1 592 y dos motivos
distintos: las tablas de Primera C no tienen columna de fecha, y ésta la tiene y la
deja vacía —la Fecha 9 no fecha ninguno de sus 22 partidos—. Que no fuera un bug del
parser había que verificarlo: si lo fuera, la solución sería arreglar el parser, no
archivar 438 partidos.

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

## Tests

512 tests, sin red — se prueba el parseo, y un test que depende de que Wikipedia
esté arriba no prueba el parseo, prueba internet.

Que pasen no alcanza, así que hay mutation testing: `mutar.py` rompe el código a
propósito de 154 maneras y exige que la suite se dé cuenta de cada una.

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

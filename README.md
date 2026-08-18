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

Con una excepción, que apareció después y vale la pena adelantar: cuando la tabla no
balancea —su columna GF y su columna GC no suman lo mismo— sí dice quién tiene razón,
porque se está contradiciendo a sí misma y no hace falta ninguna otra fuente. Está
abajo, en los cinco de un solo club.

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

## Tests

649 tests, sin red — se prueba el parseo, y un test que depende de que Wikipedia
esté arriba no prueba el parseo, prueba internet.

Que pasen no alcanza, así que hay mutation testing: `mutar.py` rompe el código a
propósito de 216 maneras y exige que la suite se dé cuenta de cada una.

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

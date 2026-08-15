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

**Estado:** **36 935 partidos entre febrero de 2004 y hoy** — veintitrés años de
Primera División, quince de Primera Nacional, once de Primera B, Primera C y
Torneo Federal A, y diez ediciones de la Copa Argentina. **198 clubes**, 128
torneos, cero partidos sin fecha, sin marcador ni duplicados. Se actualiza solo,
todos los días.

Aparte, en [`data/sin-fecha/`](data/sin-fecha/) hay **1 154 partidos que están
completos salvo por el día en que se jugaron** — tres temporadas de Primera C que
la fuente publica sin fecha. Van separados justamente para que el dataset
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
sólo en **1 520 filas de 36 935** (4,1 %): la **fecha del calendario** de partidos
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
**19 torneos a 113**: 91 cierran perfecto y 22 tienen algo que no.

Que 91 temporadas cierren al gol contra una tabla que escribió otra mano es la
corroboración más fuerte que tiene el dataset.

#### Localizar no es arbitrar

De los 22 que no cierran, los deltas por club **localizan** el partido: si a uno le
sobra un gol a favor y a otro le sobra uno en contra, el error está entre esos dos.
Y en algunos casos hay **un único** ajuste de un gol que hace cerrar el torneo
entero, lo que parece una prueba.

No lo es. Se probaron los dos casos con solución única contra la prensa, y
**acertó uno solo**:

| caso | ajuste único | lo que dicen las fuentes |
|---|---|---|
| Federal A 2019-20 | San Martín (F) 2-0 → **3-0** Unión (S) | 3-0, confirmado — **corregido** |
| Primera C 2026 | Centro Español 2-3 → 1-2 Juventud Unida | **2-3**, o sea que Wikipedia estaba bien |

En el segundo la equivocada era la tabla, igual que con Platense. Así que la
aritmética dice *dónde* mirar, no *quién* tiene razón: para eso hace falta salir a
buscar afuera, partido por partido. Va como **aviso**, no como error: lo que denuncia
es una contradicción de la fuente consigo misma.

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

## Tests

310 tests, sin red — se prueba el parseo, y un test que depende de que Wikipedia
esté arriba no prueba el parseo, prueba internet.

Que pasen no alcanza, así que hay mutation testing: `mutar.py` rompe el código a
propósito de 64 maneras y exige que la suite se dé cuenta de cada una.

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

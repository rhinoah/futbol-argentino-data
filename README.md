# futbol-argentino-data

Un dataset abierto de partidos del fútbol argentino, armado a partir de
Wikipedia en español y actualizable solo.

```
date,time,home_team,away_team,home_score,away_score,home_pens,away_pens,tournament,season,phase,group,matchday,venue,neutral,source
2026-01-22,17:00,Aldosivi,Defensa y Justicia,0,0,,,Primera Division - Apertura,2026,zonas,Interzonal,Fecha 1,José María Minella,false,https://es.wikipedia.org/wiki/...
```

**Estado:** **4836 partidos entre febrero de 2016 y hoy** — once años de Primera
División, más la Copa Argentina 2026. 69 clubes, cero partidos sin fecha ni
marcador. Abajo está el plan.

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

## Cómo se usa

```bash
python build.py              # baja, parsea, valida y escribe data/partidos.csv
python build.py --dry-run    # parsea y valida, sin escribir
python build.py --sin-cache  # vuelve a pedirle todo a Wikipedia
pytest                       # la suite
```

Sin dependencias: Python 3.11+ y la biblioteca estándar. `pandas` no hace falta
para *armar* el dataset — si lo vas a *usar*, `pd.read_csv("data/partidos.csv")`
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
| penales sólo en empates | haber leído el entretiempo como si fuera la tanda |
| sin duplicados, nadie contra sí mismo | filas leídas dos veces, columnas corridas |
| todos los partidos de zona tienen zona | un encabezado que no se reconoció |
| **cada equipo juega una vez por fecha** | etiquetas corridas |
| **el que juega una ronda ganó la anterior** | cualquier cosa, en la eliminación |
| zona = todos contra todos completo | partidos faltantes (aviso, no error) |

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

## Tests

270 tests, sin red — se prueba el parseo, y un test que depende de que Wikipedia
esté arriba no prueba el parseo, prueba internet.

Que pasen no alcanza, así que hay mutation testing: `mutar.py` rompe el código a
propósito de 44 maneras y exige que la suite se dé cuenta de cada una.

```bash
python mutar.py
```

Encontró nueve agujeros reales. Uno resultó ser un **mutante equivalente** —
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
- [x] **4.** Copa Argentina — tercer formato de página, y llevó el padrón de 30 clubes a 64
- [ ] **5.** Primera Nacional y Federal A
- [ ] **6.** Actualización automática (GitHub Actions) y publicación

## Licencia

Código **MIT**. Datos **CC BY-SA 4.0**, heredada de Wikipedia — ver
[`LICENSE-DATOS.md`](LICENSE-DATOS.md). La columna `source` lleva la atribución
fila por fila, así que viaja con el dato.

---

Hermano mayor: [world-cup-predictor](https://github.com/rhinoah/world-cup-predictor),
el modelo de predicción del Mundial 2026 del que salió la idea de necesitar esto.

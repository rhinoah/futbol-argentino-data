#!/usr/bin/env python3
"""
fad/fechas.py
=============
Completar la FECHA de partidos que ya tenemos, desde una segunda fuente.

Por que existe: unas 3000 filas del ascenso 2004-2010 salen de paginas de
Wikipedia cuyas tablas tienen tres columnas -- `Local | Resultado | Visitante` --
y nada mas. El partido esta, el marcador esta, la jornada esta; la fecha del
calendario no, porque la fuente no la escribe. Sin fecha esos partidos no entran
al dataset, y son partidos reales.

QUE ES Y QUE NO ES ESTE MODULO
------------------------------
NO parsea partidos: no crea filas, no toca equipos ni marcadores. Recibe partidos
que ya existen y les pone una fecha, o no se la pone. Todo lo demas sigue saliendo
de Wikipedia, y `source` lo dice fila por fila.

La regla que lo hace confiable esta en `completar()`: **no se importa una fecha
porque los nombres se parezcan**. Tienen que coincidir los dos equipos, el
marcador Y la jornada. Si las dos fuentes describen el mismo partido con
resultados distintos, no se completa nada y se avisa -- eso es informacion sobre
los datos, no un problema a tapar.

SOBRE LA FUENTE
---------------
worldfootball.net (el mismo operador que livefutbol.com, que la propia Wikipedia
cita como fuente en esas paginas) declara su politica en robots.txt:

    User-agent: *
    Content-Signal: search=yes, ai-train=no, use=reference
    Allow: /

`use=reference` es exactamente esto. Lo que bloquea son crawlers de IA, no un
script identificado que consulta fechas. Ademas un hecho aislado -- "este partido
se jugo tal dia" -- no es obra protegida; lo que se protege es la seleccion y
organizacion de una base, no los hechos sueltos.

DOS TRAMPAS DEL HTML
--------------------
1. `data-datetime` viene en **UTC**. El partido `2007-08-09T22:00:00Z` se jugo el
   9 de agosto a las 19:00 en Argentina, pero el encabezado visible de la pagina
   dice "10.08.2007". Tomando el UTC sin convertir, todos los partidos nocturnos
   quedan corridos un dia.
2. La respuesta **no viene en UTF-8**. Sin leer el charset del header, los nombres
   llegan rotos ("C rdoba") y no cruzan con nada.
"""
from __future__ import annotations

import html
import re
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass
from datetime import datetime
from zoneinfo import ZoneInfo

from fad import wiki

# Dos husos, y hace falta distinguirlos.
#
# `data-datetime` es un instante UTC de verdad. El sitio es aleman y lo MUESTRA
# en su propio huso: se comprobo sobre los 1520 partidos cacheados que la fecha
# visible al lado de cada partido coincide con la de Berlin en el 100%, y su
# `match-time` tambien (18:30Z se muestra 20:30, que es Berlin, no las 15:30 de
# Buenos Aires). O sea que la hora que se ve NO es la del partido.
#
# Argentina va con tzdata y no con UTC-3 a mano. La razon por la que estaba fijo
# -- "no hay horario de verano desde 2009 y las temporadas que interesan son
# anteriores" -- esta al reves: las que tuvieron DST son justamente las de antes
# de 2009, y hay 191 instantes cacheados dentro de esas ventanas.
ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")
BERLIN = ZoneInfo("Europe/Berlin")

# La URL canonica lleva el id de la COMPETENCIA y el de la TEMPORADA, y los dos
# los publica el propio sitio en sus selectores. Los slugs legibles del estilo
# `arg-primera-b-nacional-2007-2008` son atajos que a veces existen y a veces no:
# probandolos a ciegas salieron 404 en casi todos y un par de 403, que es el
# servidor diciendo que no se hace asi.
BASE = "https://www.worldfootball.net/competition/{co}/{se}/all-matches/"

# Lo que se escribe en `source` de las filas cuya fecha salio de aca. El credito
# va fila por fila y no en una nota al pie: quien lea el CSV tiene que poder ver
# de donde vino cada dato sin abrir el README.
CREDITO = "https://www.worldfootball.net/"


@dataclass(frozen=True)
class Ajeno:
    """Un partido segun la otra fuente. Nada de esto entra al dataset salvo la
    fecha: lo demas esta para poder verificar que hablamos del mismo partido."""
    fecha: str                # ISO, ya en hora argentina
    jornada: int
    local: str
    visita: str
    goles_local: int
    goles_visita: int
    id_local: str = ""        # `te17568`: testigo estable, no depende del nombre
    id_visita: str = ""
    # La seccion de nivel 2 de la pagina, cuando la fuente la distingue y nosotros
    # tambien. Vacio = no se usa, que es como venia y como sigue para worldfootball.
    #
    # Hace falta cuando UNA pagina trae dos torneos con la misma numeracion de
    # jornadas: el Argentino A 2005-06 tiene un Apertura y un Clausura, los dos
    # con Fecha 1 a 11. Sin esto, "Fecha 5 Douglas Haig vs Cipolletti" es una sola
    # casilla para dos partidos distintos, y ahi pasan las dos cosas malas: si la
    # fuente trae los dos se chocan y se pierden los dos, y si trae uno solo, sus
    # datos se le ponen TAMBIEN al otro. Eso ultimo es lo peor: la pagina del
    # Argentino A copio las tablas de dos jornadas del Clausura dentro del
    # Apertura, y sin la llave las veinte filas se llevaban una fecha de febrero
    # de 2006 que para las del Apertura es imposible.
    llave: str = ""

    # La zona, cuando la fuente reparte el torneo en grupos. Vacio = no se usa.
    #
    # Es el mismo problema que `llave` un escalon mas abajo, y se descubrio igual:
    # el Argentino A 2006-07 corre tres zonas en paralelo y CADA UNA numera sus
    # jornadas desde 1, asi que "Fecha 1" son tres partidos distintos. Importando
    # sin la zona, `validar.una_vez_por_jornada` -- que agrupa por (llave, zona,
    # jornada) -- veia a los tres grupos en la misma casilla y acusaba a medio
    # torneo de jugar dos veces por fecha: catorce avisos graves que no eran del
    # dato sino de esta linea faltando.
    zona: str = ""

    # De donde salio el marcador, con el mismo vocabulario que
    # `parser.status_de_la_fila`: "" / "suspendido" / "escritorio" /
    # "no disputado". Vacio es lo normal y quiere decir "la fuente no dijo otra
    # cosa".
    status: str = ""


# Cache propia, al lado de la de Wikipedia y por la misma razon: durante el
# desarrollo la misma temporada se lee decenas de veces. Aca ademas importa por
# educacion -- es un sitio ajeno que nos deja consultarlo, y no hay ninguna razon
# para pedirle mil veces una temporada de 2007 que ya no va a cambiar.
CACHE = wiki.CACHE / "wf"
PAUSA_MIN = 2.0          # segundos entre pedidos; mas espaciado que con Wikipedia
_ULTIMO = 0.0


def descargar(co: str, se: str, usar_cache: bool = True) -> str:
    """El HTML de una temporada, con el charset que el servidor declara.

    `co` y `se` son los ids de competencia y temporada que usa el sitio
    (`co1787`, `se19981`). Salen de `temporadas_de()`, no de adivinar.
    """
    global _ULTIMO
    archivo = CACHE / f"{co}-{se}.html"
    if usar_cache and archivo.exists():
        return archivo.read_text(encoding="utf-8")

    espera = PAUSA_MIN - (time.monotonic() - _ULTIMO)
    if espera > 0:
        time.sleep(espera)
    req = urllib.request.Request(BASE.format(co=co, se=se),
                                 headers={"User-Agent": wiki.UA})
    # El reloj de la pausa se toca en `finally`, no despues del pedido exitoso.
    # Estando afuera, un pedido que fallaba no registraba su hora y el siguiente
    # salia sin esperar: cuatro 403 seguidos con 0.000 s entre uno y otro. O sea
    # que la autolimitacion se desactivaba justo en el escenario en que el sitio
    # esta diciendo que no, que es el peor momento para insistir rapido.
    try:
        with urllib.request.urlopen(req, timeout=60) as r:
            crudo = r.read()
            tipo = r.headers.get("Content-Type", "")
    finally:
        _ULTIMO = time.monotonic()
    m = re.search(r"charset=([\w-]+)", tipo, re.I)
    texto = crudo.decode(m.group(1) if m else "utf-8", errors="replace")

    # No se cachea cualquier cosa que venga con status 200. Un interstitial de
    # firewall, un "access denied" o una pagina de mantenimiento se sirven con
    # 200 igual que la buena, y guardado queda para siempre: todas las corridas
    # siguientes leen ESE archivo y devuelven cero partidos sin dar ningun error,
    # que es la forma de fallar que este proyecto trata de no tener.
    if "data-match_id" not in texto:
        raise OSError(f"{co}/{se}: la respuesta no parece una pagina de temporada "
                      f"({len(texto)} caracteres, sin un solo partido); no se cachea")
    CACHE.mkdir(parents=True, exist_ok=True)
    archivo.write_text(texto, encoding="utf-8")
    return texto


_JORNADA = re.compile(r'class="[^"]*round-head[^"]*"[^>]*>\s*Matchday\s*(\d+)', re.I)
# El bloque de un partido va desde su `data-match_id` hasta el proximo. Los
# atributos NO vienen siempre en el mismo orden, asi que se captura el bloque
# entero y despues se le sacan los campos: pidiendolos en un orden fijo se leian
# 113 partidos de 380, y los 267 que faltaban no daban ningun error.
_PARTIDO = re.compile(r'<div\s+data-match_id="\d+"(.*?)(?=<div\s+data-match_id=|\Z)', re.S)
_ATRIBUTO_FECHA = re.compile(r'data-datetime="([^"]+)"')
# `<div class="match-time match-time-unknown"></div>`: el sitio no sabe a que
# hora se jugo, y entonces su `data-datetime` es un relleno. Ver `_a_hora_local`.
_HORA_DESCONOCIDA = re.compile(r'class="[^"]*match-time-unknown')
_CLASE = re.compile(r'class="([^"]*)"')
# Los equipos salen de sus ENLACES, no de la clase del div que los envuelve.
# Pedir `class="team-name team-name-home"` exacto leia un solo equipo en 267 de
# los 380 bloques -- la clase no siempre viene asi -- y esos partidos se
# descartaban por "menos de dos equipos" sin dar ningun error.
#
# Cada equipo aparece varias veces en su bloque (nombre largo, nombre corto,
# escudo) SIEMPRE con el mismo id, asi que se deduplica por id y se toman los dos
# primeros: local y visitante, en el orden en que estan escritos.
# El `[^"]*?` antes de /teams/ acepta el enlace relativo Y el absoluto. Cuando
# la pagina se guarda desde el navegador, este reescribe `/teams/te123/` como
# `https://www.worldfootball.net/teams/te123/`, y pidiendo que empiece en `/` se
# leen CERO equipos: los 380 partidos se descartan por "menos de dos equipos"
# sin dar ningun error.
_EQUIPO = re.compile(r'href="[^"]*?/teams/(te\d+)/[^"]*"[^>]*>([^<]+)</a>')
# El marcador sale de SU elemento, no del primer `N:N` del bloque. Al lado vive
# `<div class="match-time">20:30</div>` con el horario, que tiene exactamente la
# misma forma: tomando el primero, los partidos con hora cargada quedaban con
# marcador 20-30 o 19-0, y el cruce los reportaba como "las dos fuentes dicen
# cosas distintas" cuando el que decia cualquier cosa era este parser.
_CELDA_RESULTADO = re.compile(r'class="match-result[^"]*"[^>]*>(.*?)</div>', re.S)
_MARCADOR = re.compile(r">\s*(\d+):(\d+)\s*<")


def _goles(bloque: str) -> tuple[int, int] | None:
    celda = _CELDA_RESULTADO.search(bloque)
    if not celda:
        return None
    m = _MARCADOR.search(celda.group(1))
    return (int(m.group(1)), int(m.group(2))) if m else None


def _dos_equipos(bloque: str) -> list[tuple[str, str]]:
    vistos: dict[str, str] = {}
    for id_eq, nombre in _EQUIPO.findall(bloque):
        vistos.setdefault(id_eq, html.unescape(nombre).strip())
    return list(vistos.items())[:2]


def partidos_de(pagina: str) -> list[Ajeno]:
    """Los partidos terminados de una pagina de temporada.

    Los partidos son `<div>` con atributos de datos, no filas de tabla -- por eso
    buscarlos como `<tr>` no encontraba ninguno aunque estuvieran los 380.
    """
    jornadas = [(m.start(), int(m.group(1))) for m in _JORNADA.finditer(pagina)]
    fuera = []
    for m in _PARTIDO.finditer(pagina):
        bloque = m.group(1)
        clase = _CLASE.search(bloque)
        cuando = _ATRIBUTO_FECHA.search(bloque)
        if not cuando or not clase or "finished" not in clase.group(1):
            continue                       # suspendido, aplazado o por jugarse
        equipos = _dos_equipos(bloque)
        goles = _goles(bloque)
        if len(equipos) < 2 or not goles:
            continue
        (id_l, local), (id_v, visita) = equipos
        fuera.append(Ajeno(
            fecha=_a_hora_local(cuando.group(1),
                                not _HORA_DESCONOCIDA.search(bloque)),
            jornada=_jornada_en(m.start(), jornadas),
            local=local, visita=visita,
            goles_local=goles[0], goles_visita=goles[1],
            id_local=id_l, id_visita=id_v))
    return fuera


def _a_hora_local(iso_utc: str, hora_conocida: bool = True) -> str:
    """El dia en que se jugo el partido. `2010-08-07T18:30:00Z` -> `2010-08-07`.

    CUANDO EL SITIO SABE LA HORA, el instante es real y la fecha que vale es la
    argentina: 18:30 UTC son las 15:30 de un sabado a la tarde. Sin convertir, un
    partido de las 21:00 figura al dia siguiente.

    CUANDO NO LA SABE (`match-time-unknown`), `data-datetime` no es un instante:
    es un relleno: la medianoche de ese dia en Berlin. Se nota porque toma DOS
    valores nada mas -- 22:00Z en verano europeo y 23:00Z en invierno -- en las
    dos temporadas enteras donde aparece. Restarle tres horas a una medianoche
    cae en el dia anterior, y asi quedaron corridos los 760 partidos de 2007-08 y
    2008-09: cada uno un dia antes del que el propio sitio publica al lado.

    Por eso el huso depende de si hay hora. No es una preferencia: es que en un
    caso el dato es un instante y en el otro es una fecha disfrazada de instante.
    """
    try:
        t = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    except ValueError:
        return ""
    return t.astimezone(ARGENTINA if hora_conocida else BERLIN).date().isoformat()


def _jornada_en(pos: int, jornadas: list[tuple[int, int]]) -> int:
    n = 0
    for donde, numero in jornadas:
        if donde > pos:
            break
        n = numero
    return n


# --------------------------------------------------------------------------
# el cruce
# --------------------------------------------------------------------------
def derivar_padron(nuestros: list, ajenos: list[Ajeno],
                   minimo: int = 2) -> tuple[dict[str, str], list[str]]:
    """Deduce {id de la otra fuente: club nuestro} SIN mirar los nombres.

    La idea: dentro de una jornada, un marcador que aparece UNA sola vez de cada
    lado identifica el partido sin ambiguedad. Ese cruce dice, a la vez, quien es
    el local y quien el visitante -- o sea que da dos correspondencias de id a
    club, y no dependen de como cada fuente escriba los nombres.

    Se usan SOLO los marcadores unicos. Un 1-0 que aparece tres veces en la
    misma fecha no identifica nada, y forzarlo seria adivinar.

    Un id se acepta solo si todos sus votos apuntan al mismo club y hay al menos
    `minimo`. Con un solo voto un cruce casual alcanzaria para fijar un club
    equivocado para siempre; pidiendo dos, ese error tendria que repetirse en dos
    jornadas distintas con el mismo marcador unico.
    """
    from collections import Counter, defaultdict

    votos: dict[str, Counter] = defaultdict(Counter)
    por_jornada: dict[int, list] = defaultdict(list)
    for p in nuestros:
        por_jornada[_numero(p.jornada)].append(p)

    for j, mios in por_jornada.items():
        suyos = [a for a in ajenos if a.jornada == j]
        cuenta_mia = Counter((p.goles_local, p.goles_visita) for p in mios)
        cuenta_suya = Counter((a.goles_local, a.goles_visita) for a in suyos)
        for p in mios:
            k = (p.goles_local, p.goles_visita)
            if cuenta_mia[k] != 1 or cuenta_suya[k] != 1:
                continue                     # ese marcador no identifica nada
            a = next(x for x in suyos if (x.goles_local, x.goles_visita) == k)
            votos[a.id_local][p.local] += 1
            votos[a.id_visita][p.visita] += 1

    mapa, dudosos, minoria = {}, [], []
    for id_eq, cuenta in votos.items():
        (club, favor), = cuenta.most_common(1)
        contra = sum(cuenta.values()) - favor
        if favor < minimo:
            continue
        # Pedir unanimidad era demasiado. Un solo voto en contra entre veinte
        # basta para que el club quede sin id, y con el se van sus 38 partidos:
        # asi se perdieron 22 fechas de la B Nacional 2009-10 por UN partido que
        # Wikipedia anota con la localia al reves (Ferro 2-2 Union en la fecha
        # 25; la otra fuente lo da Union 2-2 Ferro, y como el marcador es
        # simetrico el cruce empareja los equipos cambiados).
        #
        # Alcanza con exigir una mayoria amplia -- cuatro a uno -- en vez de
        # perfecta. {19 a 1} entra; {10 a 9} no, que es lo que hay que evitar.
        # Y el voto disidente igual se informa: casi siempre esta senalando algo
        # de verdad, aunque este afuera del mapa.
        if contra * 4 > favor:
            dudosos.append(f"{id_eq}: {dict(cuenta)}")
            continue
        if contra:
            minoria.append(f"{id_eq} ({club}): {dict(cuenta)}")
        mapa[id_eq] = club

    avisos = []
    if dudosos:
        avisos.append(f"{len(dudosos)} ids con votos contradictorios, se dejan afuera: "
                      + "; ".join(dudosos[:3]))
    if minoria:
        avisos.append(f"{len(minoria)} ids con algun voto en minoria, se acepta la mayoria: "
                      + "; ".join(minoria[:3]))
    flojos = len(votos) - len(mapa) - len(dudosos)
    if flojos:
        avisos.append(f"{flojos} ids con menos de {minimo} votos, se dejan afuera")
    if len(set(mapa.values())) != len(mapa):
        avisos.append("HAY DOS IDS APUNTANDO AL MISMO CLUB: el mapa no sirve")
    return mapa, avisos


def completar(nuestros: list, ajenos: list[Ajeno],
              mapa: dict[str, str] | None = None,
              arbitrados: set | None = None,
              credito: str = CREDITO,
              verificadas: set | None = None,
              usadas: set | None = None) -> tuple[int, list[str]]:
    """Le pone fecha a los partidos que no la tienen. Devuelve (cuantos, avisos).

    LA REGLA: los equipos y la jornada IDENTIFICAN el partido, y el marcador lo
    VERIFICA. Si las dos fuentes coinciden en quienes jugaron y en que fecha del
    calendario, pero no en el resultado, no se completa nada -- se avisa. Un
    partido que dos fuentes cuentan distinto es informacion sobre los datos, no
    un problema a tapar, y meterle la fecha igual seria decidir que una de las
    dos tiene razon sin haberlo mirado.

    Los nombres del otro lado pasan por el mismo padron que todo lo demas. Los
    que no resuelven se informan en vez de emparejarse por parecido: es lo que
    evito que "Estudiantes" terminara siendo el club equivocado.

    `arbitrados` son los partidos cuyo desacuerdo de marcador YA se resolvio por
    otro camino -- la tabla de posiciones de la propia pagina, ver
    `fad/correcciones.py`. Para esos el marcador ya no hace falta como
    verificacion, porque el emparejamiento esta confirmado, y la fecha se toma
    igual. Es una excepcion nombrada partido por partido y no un aflojamiento de
    la regla: sin la lista, un desacuerdo sigue frenando la fecha.
    """
    from fad import equipos

    def club(id_eq, nombre):
        if mapa and id_eq in mapa:
            return mapa[id_eq]
        eq = equipos.buscar(nombre)
        return eq.nombre if eq else None

    # Si la fuente distingue llaves, la clave las incluye de los dos lados.
    con_llave = any(a.llave for a in ajenos)
    # Y si NO trae numero de jornada -- el feed de ESPN no lo publica --, el
    # identificador pasa a ser el par (local, visita) solo. No es aflojar la
    # regla, es cambiarle el identificador: en una liga de ida y vuelta cada par
    # se cruza UNA VEZ EN CADA CANCHA, asi que el par ya identifica el partido.
    # Medido sobre nuestros datos antes de decidirlo: 384 pares distintos sobre
    # 384 partidos en la Primera C 2008-09.
    #
    # Lo que sostiene esto no es la aritmetica sino que la regla de colision
    # sigue puesta: si el par NO identifica uno solo -- los playoffs vuelven a
    # cruzar a los mismos --, se caen los dos y no se completa nada. Y el
    # marcador sigue verificando.
    con_jornada = any(a.jornada for a in ajenos)
    indice, sin_padron, chocados = {}, set(), set()
    for a in ajenos:
        el, ev = club(a.id_local, a.local), club(a.id_visita, a.visita)
        for nombre, c in ((a.local, el), (a.visita, ev)):
            if c is None:
                sin_padron.add(nombre)
        if el and ev:
            # Si dos ajenos caen en la misma casilla se sacan los dos. Antes el
            # segundo pisaba al primero en silencio, y eso da las dos formas de
            # equivocarse: con otro marcador el partido perdia la fecha y el
            # aviso mentia sobre lo que dice la otra fuente; con el mismo, se
            # importaba la fecha del partido equivocado sin decir nada. Es el
            # mismo criterio que `derivar_padron` usa con los marcadores
            # repetidos: lo que no identifica uno solo, no identifica nada.
            k = (a.llave, a.jornada if con_jornada else 0, el, ev)
            if k in indice:
                chocados.add(k)
            indice[k] = a

    for k in chocados:
        del indice[k]

    def clave(p):
        # `p.llave or ""` contra `a.llave`: si la fuente no distingue llaves las
        # deja vacias y la clave queda como estaba.
        #
        # UNA RONDA DE ELIMINACION NO TIENE NUMERO DE FECHA, y preguntarselo a
        # `_numero` --que devuelve el primer digito del nombre-- da uno inventado:
        # `1/8 Finals - First leg` daba 1, el uno de "1/8". Con eso, las dieciseis
        # filas asi del corpus compartian clave con la Round 1 de la fase regular.
        # En el Argentino A 2005-06 la ida de los octavos se comparaba contra
        # `Villa Mitre 2-1 Sportivo Desamparados` de la primera fecha del
        # Clausura, y el aviso denunciaba tres desacuerdos entre partidos
        # distintos; con el marcador coincidiendo habria escrito la fecha
        # equivocada.
        #
        # Se pregunta por la FASE y no por como esta escrita la etiqueta. El campo
        # ya existe y no hay que adivinarlo: son 80 filas --`1/8 Finals`,
        # `Promoción N`, `Semifinal N`, `Llave N`, `Partido N`--, todas de
        # eliminacion, y ninguna fuente que numere rondas de liga puede estar
        # hablando de ellas. Las llaves se fechan por otro camino, `leer_llaves`.
        numerada = con_jornada and getattr(p, "fase", "") != "eliminacion"
        return (getattr(p, "llave", "") if con_llave else "",
                _numero(p.jornada) if numerada else 0,
                p.local, p.visita)

    # LA REGLA DE COLISION TAMBIEN VALE DE ESTE LADO. Arriba se descartan los
    # ajenos que caen en la misma casilla; faltaba mirar si son VARIAS FILAS
    # NUESTRAS las que caen en una. Pasa cuando la fuente no numera la jornada y
    # la llave no separa lo suficiente: en el Argentino A 2004-05 la fase regular
    # y las rondas de la Segunda Fase comparten `llave` --las dos son "Torneo
    # Apertura"--, asi que `Gimnasia y Tiro (S) vs Atlético Tucumán` de la fecha 5
    # y el mismo cruce de la Tercera ronda son la misma clave.
    #
    # No llegaba a escribir una fecha equivocada, porque el marcador verifica
    # antes. Lo que si hacia era DENUNCIAR UN DESACUERDO QUE NO EXISTE: la fila de
    # la Tercera ronda se comparaba contra la cita de la fase regular y el aviso
    # decia "esta fuente la da distinta" sobre dos partidos distintos.
    #
    # Se resuelve con el mismo criterio de siempre: lo que no identifica uno solo
    # no identifica nada, y el marcador --que ya es el verificador-- desempata. Si
    # entre las filas que comparten clave hay EXACTAMENTE UNA con el marcador del
    # ajeno, esa es; las demas quedan sin pareja y en silencio.
    mias: dict = {}
    for p in nuestros:
        mias.setdefault(clave(p), []).append(p)

    puestos, sin_par, avisos = 0, 0, []
    discrepan = []
    for p in nuestros:
        k = clave(p)
        a = indice.get(k)
        if a is not None and len(mias[k]) > 1:
            iguales = [x for x in mias[k]
                       if (x.goles_local, x.goles_visita) == (a.goles_local, a.goles_visita)]
            if len(iguales) != 1 or iguales[0] is not p:
                a = None
        if p.fecha:
            # YA TIENE FECHA, PERO ESTA FUENTE PUEDE DECIR OTRA. Saltearla en
            # silencio -- que es como venia -- convierte el ORDEN de los
            # completadores en el arbitro: el que corre primero gana y el segundo
            # no dice nada. Se vio al enchufar RSSSF a temporadas que ya fechaba
            # ESPN: veintitres filas cambiaron de dia sin que nada lo denunciara,
            # y una de ellas por dieciseis dias.
            #
            # No se pisa la que ya esta: la primera fuente sigue mandando. Lo que
            # cambia es que el desacuerdo se ve.
            if a is not None and a.fecha and a.fecha != p.fecha:
                # SALVO QUE ALGUIEN YA LO HAYA MIRADO. `verificadas` trae los
                # desacuerdos que se fueron a contrastar contra una TERCERA
                # fuente y volvieron dandole la razon a la nuestra. No hay nada
                # que corregir en esos y repetir el aviso en cada corrida
                # convierte la lista en ruido; ver `correcciones.Fechado`.
                #
                # Se pide la tupla ENTERA, con las dos fechas: si alguna de las
                # dos fuentes cambia de opinion, la declaracion deja de enganchar
                # y el aviso vuelve, que es lo que tiene que pasar -- lo que se
                # verifico era ese desacuerdo y no otro.
                # `mirado` y no `clave`: asi se llama la funcion local que arma
                # la clave del indice, y pisarla con una tupla rompe el resto del
                # bucle -- `'tuple' object is not callable` --.
                mirado = (p.jornada, p.local, p.visita, p.fecha, a.fecha)
                # Dos formas, y la corta es mas fuerte: con CINCO campos es un
                # desacuerdo puntual ya verificado; con TRES es un partido cuya
                # fecha se zanjo a mano, y ahi calla cualquier desacuerdo sobre esa
                # fila. Ver `correcciones.fechados`.
                zanjado = next((k for k in (mirado, mirado[:3])
                                if k in (verificadas or ())), None)
                if zanjado is not None:
                    if usadas is not None:
                        usadas.add(zanjado)
                else:
                    discrepan.append(f"{p.jornada} {p.local} vs {p.visita}: nosotros "
                                     f"{p.fecha}, esta fuente {a.fecha}")
            continue
        if a is None:
            sin_par += 1
            continue
        if (a.goles_local, a.goles_visita) != (p.goles_local, p.goles_visita):
            if (p.jornada, p.local, p.visita) not in (arbitrados or ()):
                avisos.append(f"marcador distinto en {p.jornada} {p.local} vs {p.visita}: "
                              f"nosotros {p.goles_local}-{p.goles_visita}, "
                              f"la otra fuente {a.goles_local}-{a.goles_visita}; no se completo")
                continue
            avisos.append(f"marcador distinto en {p.jornada} {p.local} vs {p.visita} "
                          f"({p.goles_local}-{p.goles_visita} contra "
                          f"{a.goles_local}-{a.goles_visita}), pero el partido ya esta "
                          f"arbitrado: se toma la fecha y se deja el marcador nuestro")
        p.fecha = a.fecha
        # El credito es de la fuente que puso la fecha, y no siempre es la misma:
        # worldfootball no tiene el Argentino A y esas fechas salen de RSSSF. Va
        # a `source` fila por fila, asi que el dataset dice de donde salio cada
        # dato aunque el torneo se haya armado con dos fuentes.
        p.fuente_fecha = credito
        puestos += 1

    if chocados:
        avisos.append(f"{len(chocados)} cruces de la otra fuente aparecen dos veces en la "
                      f"misma jornada y no identifican nada: "
                      + "; ".join(f"{k + ' ' if k else ''}F{j} {l} vs {v}"
                                  for k, j, l, v in sorted(chocados)[:3]))
    if sin_padron:
        avisos.append(f"{len(sin_padron)} nombres de la otra fuente que el padron no "
                      f"conoce: {', '.join(sorted(sin_padron)[:6])}")
    if sin_par:
        avisos.append(f"{sin_par} partidos sin pareja en la otra fuente")
    if discrepan:
        avisos.append(f"{len(discrepan)} partidos que ya tenian fecha y esta fuente "
                      f"la da distinta; se conserva la que ya estaba: "
                      + " | ".join(discrepan[:3]))
    # LA DENUNCIA DEL HUERFANO NO VA ACA, y se aprendio poniendola aca. Una
    # pagina pasa por VARIOS completadores -- worldfootball, RSSSF, el de llaves,
    # las citas -- y cada uno ve solo los desacuerdos que a el le tocan. Si cada
    # uno denuncia las declaraciones que no uso, las cinco del Argentino A
    # 2012-13 salen como huerfanas en el completador que no las mira, que es lo
    # normal y no un problema. `usadas` se acumula entre todos y quien avisa es
    # `build.procesar`, que es el que sabe cuando se termino la pagina.
    return puestos, avisos


def _numero(jornada: str) -> int:
    m = re.search(r"(\d+)", jornada or "")
    return int(m.group(1)) if m else 0


# --------------------------------------------------------------------------
# descubrir que temporadas hay
# --------------------------------------------------------------------------
_OPCION = re.compile(r'<option[^>]*value="([^"]+)"[^>]*>([^<]*)</option>')
_IDS = re.compile(r"/(co\d+)/(?:[^/]+/)?(se\d+)/")


def temporadas_de(pagina: str) -> dict[str, tuple[str, str]]:
    """{etiqueta: (competencia, temporada)} segun el selector de la propia pagina.

    Bajando UNA temporada cualquiera de una competencia, su selector lista todas
    las demas. Cinco pedidos alcanzan para catalogar el sitio entero, contra la
    bateria a ciegas que probamos primero -- que ademas de descortes se corto
    sola con 403.

    Y aparecen temporadas que uno no imaginaria: "2025 Playoffs",
    "2024 Relegation", "2025 Gran Final". Adivinando nombres no se encuentran.
    """
    fuera = {}
    for valor, etiqueta in _OPCION.findall(pagina):
        m = _IDS.search(valor)
        if m:
            fuera[html.unescape(etiqueta).strip()] = (m.group(1), m.group(2))
    return fuera


def competencias_de(pagina: str) -> dict[str, str]:
    """{nombre: competencia} -- las otras ligas del mismo pais."""
    fuera = {}
    for valor, etiqueta in _OPCION.findall(pagina):
        m = re.fullmatch(r"/competition/(co\d+)/", valor)
        if m:
            fuera[html.unescape(etiqueta).strip()] = m.group(1)
    return fuera

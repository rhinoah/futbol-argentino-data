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
from datetime import datetime, timedelta, timezone

from fad import wiki

# Argentina no tiene horario de verano desde 2009 y las temporadas que nos
# interesan son anteriores; UTC-3 fijo alcanza y evita depender de tzdata.
ARGENTINA = timezone(timedelta(hours=-3))

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
    with urllib.request.urlopen(req, timeout=60) as r:
        crudo = r.read()
        tipo = r.headers.get("Content-Type", "")
    _ULTIMO = time.monotonic()
    m = re.search(r"charset=([\w-]+)", tipo, re.I)
    texto = crudo.decode(m.group(1) if m else "utf-8", errors="replace")

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
_CLASE = re.compile(r'class="([^"]*)"')
# Los equipos salen de sus ENLACES, no de la clase del div que los envuelve.
# Pedir `class="team-name team-name-home"` exacto leia un solo equipo en 267 de
# los 380 bloques -- la clase no siempre viene asi -- y esos partidos se
# descartaban por "menos de dos equipos" sin dar ningun error.
#
# Cada equipo aparece varias veces en su bloque (nombre largo, nombre corto,
# escudo) SIEMPRE con el mismo id, asi que se deduplica por id y se toman los dos
# primeros: local y visitante, en el orden en que estan escritos.
_EQUIPO = re.compile(r'href="/teams/(te\d+)/[^"]*"[^>]*>([^<]+)</a>')
_MARCADOR = re.compile(r">\s*(\d+):(\d+)\s*<")


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
        goles = _MARCADOR.search(bloque)
        if len(equipos) < 2 or not goles:
            continue
        (id_l, local), (id_v, visita) = equipos
        fuera.append(Ajeno(
            fecha=_a_hora_local(cuando.group(1)),
            jornada=_jornada_en(m.start(), jornadas),
            local=local, visita=visita,
            goles_local=int(goles.group(1)), goles_visita=int(goles.group(2)),
            id_local=id_l, id_visita=id_v))
    return fuera


def _a_hora_local(iso_utc: str) -> str:
    """`2007-08-09T22:00:00Z` -> `2007-08-09`, en hora argentina.

    Sin convertir, un partido de las 19:00 del 9 figura el 10: son las 22 UTC.
    """
    try:
        t = datetime.fromisoformat(iso_utc.replace("Z", "+00:00"))
    except ValueError:
        return ""
    return t.astimezone(ARGENTINA).date().isoformat()


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

    mapa, dudosos = {}, []
    for id_eq, cuenta in votos.items():
        if len(cuenta) > 1:
            dudosos.append(f"{id_eq}: {dict(cuenta)}")
        elif cuenta.most_common(1)[0][1] >= minimo:
            mapa[id_eq] = cuenta.most_common(1)[0][0]

    avisos = []
    if dudosos:
        avisos.append(f"{len(dudosos)} ids con votos contradictorios, se dejan afuera: "
                      + "; ".join(dudosos[:3]))
    flojos = len(votos) - len(mapa) - len(dudosos)
    if flojos:
        avisos.append(f"{flojos} ids con menos de {minimo} votos, se dejan afuera")
    if len(set(mapa.values())) != len(mapa):
        avisos.append("HAY DOS IDS APUNTANDO AL MISMO CLUB: el mapa no sirve")
    return mapa, avisos


def completar(nuestros: list, ajenos: list[Ajeno],
              mapa: dict[str, str] | None = None) -> tuple[int, list[str]]:
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
    """
    from fad import equipos

    def club(id_eq, nombre):
        if mapa and id_eq in mapa:
            return mapa[id_eq]
        eq = equipos.buscar(nombre)
        return eq.nombre if eq else None

    indice, sin_padron = {}, set()
    for a in ajenos:
        el, ev = club(a.id_local, a.local), club(a.id_visita, a.visita)
        for nombre, c in ((a.local, el), (a.visita, ev)):
            if c is None:
                sin_padron.add(nombre)
        if el and ev:
            indice[(a.jornada, el, ev)] = a

    puestos, sin_par, avisos = 0, 0, []
    for p in nuestros:
        if p.fecha:
            continue
        a = indice.get((_numero(p.jornada), p.local, p.visita))
        if a is None:
            sin_par += 1
            continue
        if (a.goles_local, a.goles_visita) != (p.goles_local, p.goles_visita):
            avisos.append(f"marcador distinto en {p.jornada} {p.local} vs {p.visita}: "
                          f"nosotros {p.goles_local}-{p.goles_visita}, "
                          f"la otra fuente {a.goles_local}-{a.goles_visita}; no se completo")
            continue
        p.fecha = a.fecha
        p.fuente_fecha = CREDITO
        puestos += 1

    if sin_padron:
        avisos.append(f"{len(sin_padron)} nombres de la otra fuente que el padron no "
                      f"conoce: {', '.join(sorted(sin_padron)[:6])}")
    if sin_par:
        avisos.append(f"{sin_par} partidos sin pareja en la otra fuente")
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

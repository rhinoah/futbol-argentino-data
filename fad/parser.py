#!/usr/bin/env python3
"""
fad/parser.py
=============
Sacar los partidos del wikitexto de una temporada.

Conviven DOS formatos en la misma pagina, y el segundo es mucho mas amable:

1. FASE DE GRUPOS -- una `wikitable` con columnas
   `Local | Resultado | Visitante | Estadio | Fecha | Hora`.
   Lo dificil es el `rowspan`: cuando varios partidos comparten fecha u horario,
   la celda aparece UNA sola vez y las filas siguientes vienen con menos celdas.
   Un parser que asuma "6 celdas por fila" corre las columnas y termina leyendo
   el estadio como si fuera la fecha, sin fallar.

2. ELIMINACION -- plantillas `{{Partido|local=...|resultado=...}}` con parametros
   nombrados, practicamente un JSON.

EL ERROR QUE HAY QUE NO COMETER
-------------------------------
En `|resultado = 0:1''' (0:0)` lo que esta entre parentesis es el ENTRETIEMPO,
no la tanda de penales. Los penales viven en su propio parametro
(`|resultado penalti = 4:3`). Leer los parentesis como penales no falla: inventa
definiciones por penales en partidos que se ganaron en los 90, y despues el que
consume el dataset arma un cuadro de eliminacion equivocado.

Esa es la forma tipica de fallar de todo esto: un parser mal escrito no explota,
miente. Por eso `validar.py` chequea invariantes en vez de confiar.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
         "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
         "noviembre": 11, "diciembre": 12}

COLUMNAS = ["local", "resultado", "visita", "estadio", "fecha", "hora"]


@dataclass
class Partido:
    fecha: str = ""              # ISO, YYYY-MM-DD
    hora: str = ""
    local: str = ""
    visita: str = ""
    goles_local: int | None = None
    goles_visita: int | None = None
    penales_local: int | None = None
    penales_visita: int | None = None
    torneo: str = ""
    fase: str = ""               # "zonas" / "eliminacion"
    zona: str = ""
    jornada: str = ""
    estadio: str = ""
    fecha_cruda: str = field(default="", repr=False)   # para diagnosticar


# --------------------------------------------------------------------------
# limpieza de wikitexto
# --------------------------------------------------------------------------
_ATRIBUTO = re.compile(r"=|bgcolor|style|align|width|span|scope", re.I)


def limpiar(texto: str) -> str:
    """Deja el contenido visible de una celda: sin plantillas, links ni formato."""
    s = texto.strip()
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S | re.I)
    s = re.sub(r"<ref[^>]*/>", "", s, flags=re.I)
    # `{{nowrap|X}}` se DESENVUELVE, no se borra: es puro formato, pero adentro
    # esta el dato. Borrarla junto con las demas plantillas hacia desaparecer
    # equipos enteros ("{{nowrap|Gimnasia y Esgrima (LP)}}" quedaba en nada).
    s = re.sub(r"\{\{\s*nowrap\s*\|(.*?)\}\}", r"\1", s, flags=re.I | re.S)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    s = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", s)    # [[destino|texto]] -> texto
    s = s.replace("'''", "").replace("''", "")
    s = re.sub(r"<[^>]+>", " ", s)
    return re.sub(r"\s+", " ", s).strip()


def _celda(bruta: str) -> tuple[int, str]:
    """Separa atributos de contenido. Devuelve (cuantas filas ocupa, contenido).

    `rowspan=3|22 de enero` -> (3, '22 de enero');  `Boca Juniors` -> (1, 'Boca Juniors')
    """
    m = re.match(r"^\s*([^|]*?)\|(?!\|)(.*)$", bruta, re.S)
    if not m or not _ATRIBUTO.search(m.group(1)):
        return 1, limpiar(bruta)
    n = re.search(r"rowspan\s*=\s*\"?(\d+)", m.group(1), re.I)
    return (int(n.group(1)) if n else 1), limpiar(m.group(2))


def _seccion(cab: str) -> str:
    """Normaliza la etiqueta de una seccion.

    La misma pagina escribe "Interzonal" en 15 fechas e "Interzonales" en una.
    Es lo mismo, pero salen dos valores distintos en la columna `group` y quien
    consuma el CSV los cuenta como dos cosas.
    """
    if re.match(r"(?i)^interzonal", cab):
        return "Interzonal"
    return cab


def _partir(fila: str) -> list[str]:
    """Las celdas crudas de una fila, en los DOS estilos que usa Wikipedia.

    Las tablas de liga ponen una celda por linea (`\\n|`); las de la Copa meten
    la fila entera en un renglon separando con `||`. Es la misma tabla para
    MediaWiki, pero un parser que solo conozca un estilo lee la fila de la Copa
    como una unica celda gigante y no encuentra ningun partido.

    Lo que va ANTES de la primera celda son atributos de la fila, no un dato:
    `|- bgcolor="#F5FAFF"`. Se descarta. Contarlo como celda corre todas las
    columnas un lugar, y como la Copa sombrea una fila de cada dos, se perdia
    exactamente la mitad de los partidos -- 16 de 32 treintaidosavos, 8 de 16
    dieciseisavos. Nada fallaba: la fila corrida no tenia un marcador donde
    buscarlo y se descartaba sola.
    """
    partes = re.split(r"\n\|", "\n" + fila.replace("||", "\n|"))
    return [c for c in partes[1:] if c.strip()]


def a_iso(texto: str, anio: int) -> str:
    """'22 de enero' -> '2026-01-22'. Cadena vacia si no se entiende."""
    m = re.search(r"(\d{1,2})\s*de\s+([a-záéíóúñ]+)", texto, re.I)
    if not m:
        return ""
    mes_txt = unicodedata.normalize("NFKD", m.group(2).lower()).encode("ascii", "ignore").decode()
    mes = MESES.get(mes_txt)
    return f"{anio}-{mes:02d}-{int(m.group(1)):02d}" if mes else ""


def _marcador(texto: str) -> tuple[int, int] | None:
    m = re.match(r"^\s*(\d+)\s*[-:]\s*(\d+)", texto)
    return (int(m.group(1)), int(m.group(2))) if m else None


# --------------------------------------------------------------------------
# fase de grupos: la wikitable con rowspan
# --------------------------------------------------------------------------
def _cortar_en_tablas(bloque: str) -> str:
    """Convierte el cierre y la apertura de tabla en separadores de fila.

    Cada jornada es su propia `wikitable`, y entre el cierre de una y la apertura
    de la siguiente NO hay `|-`:

        |22 de enero
        |17:00
        |}
        {|class="wikitable ..."
        !colspan=6|Fecha 2

    Partiendo solo por `\\n|-`, esa ultima fila y el encabezado de la jornada
    siguiente caen en el mismo pedazo. Como los encabezados se leen antes que las
    celdas, la fila terminaba anotada en la fecha que venia: los 30 interzonales
    (siempre el ultimo bloque de su jornada) quedaron corridos una fecha. No
    rompia nada, solo mentia. Lo mira `validar.jornadas_en_orden`.
    """
    bloque = re.sub(r"\n\|\}", "\n|-", bloque)          # cierre  |}
    return re.sub(r"\n\{\|[^\n]*", "\n|-", bloque)      # apertura {|class=...


def partidos_de_tabla(bloque: str, anio: int, torneo: str) -> list[Partido]:
    partidos: list[Partido] = []
    pendientes: dict[str, list] = {}        # columna -> [valor, filas restantes]
    jornada = zona = ""

    for fila in re.split(r"\n\|-", _cortar_en_tablas(bloque)):
        fila = fila.strip()
        if not fila:
            continue

        # Dentro de esta seccion todo encabezado `colspan` es o la jornada
        # ("Fecha 7") o la etiqueta de la seccion que sigue ("Zona A",
        # "Interzonal"). Los nombres de columna no llevan colspan, asi que no
        # entran. Se toma cualquier etiqueta y no una lista cerrada: la primera
        # version solo conocia "Zona|Grupo", los bloques "Interzonal" caian al
        # vacio y heredaban en silencio la zona anterior -- 30 partidos quedaron
        # marcados como Zona B. Lo agarro `validar.zonas_completas`.
        for cab in re.findall(r"!\s*colspan\s*=\s*\"?\d+\"?\s*\|\s*(.+)", fila):
            cab = limpiar(cab)
            if not cab:
                continue
            pendientes.clear()      # un rowspan no cruza de una seccion a otra
            if re.match(r"(?i)fecha\s*\d+", cab):
                jornada = cab
            else:
                zona = _seccion(cab)
        if fila.lstrip().startswith("!"):
            continue                                   # fila de encabezado

        celdas = _partir(fila)
        if len(celdas) < 3:
            continue

        valores, i = {}, 0
        for col in COLUMNAS:
            if pendientes.get(col, [None, 0])[1] > 0:
                valores[col] = pendientes[col][0]
                pendientes[col][1] -= 1
                continue
            if i >= len(celdas):
                valores[col] = ""
                continue
            filas, contenido = _celda(celdas[i]); i += 1
            valores[col] = contenido
            if filas > 1:
                pendientes[col] = [contenido, filas - 1]

        goles = _marcador(valores["resultado"])
        if not goles or not valores["local"] or not valores["visita"]:
            continue
        partidos.append(Partido(
            fecha=a_iso(valores["fecha"], anio), hora=valores["hora"],
            local=valores["local"], visita=valores["visita"],
            goles_local=goles[0], goles_visita=goles[1],
            torneo=torneo, fase="zonas", zona=zona, jornada=jornada,
            estadio=valores["estadio"], fecha_cruda=valores["fecha"]))
    return partidos


# --------------------------------------------------------------------------
# eliminacion: plantillas {{Partido}}
# --------------------------------------------------------------------------
def partidos_de_plantillas(texto: str, anio: int, torneo: str) -> list[Partido]:
    titulos = _titulos_de_ronda(texto)
    partidos: list[Partido] = []
    for m in re.finditer(r"\{\{\s*Partido\s*\n(.*?)\n\s*\}\}", texto, re.S | re.I):
        cuerpo = m.group(1)
        campos = {}
        for linea in cuerpo.split("\n|"):
            if "=" not in linea:
                continue
            k, v = linea.split("=", 1)
            campos[k.strip().lstrip("|").lower()] = v.strip()

        goles = _marcador(limpiar(campos.get("resultado", "")))
        if not goles:
            continue
        # OJO: los penales NO salen de los parentesis de `resultado` (eso es el
        # entretiempo). Ver el docstring del modulo.
        pen = _marcador(limpiar(campos.get("resultado penalti", "")))
        partidos.append(Partido(
            fecha=a_iso(limpiar(campos.get("fecha", "")), anio),
            local=limpiar(campos.get("local", "")),
            visita=limpiar(campos.get("visita", "")),
            goles_local=goles[0], goles_visita=goles[1],
            penales_local=pen[0] if pen else None,
            penales_visita=pen[1] if pen else None,
            torneo=torneo, fase="eliminacion",
            jornada=_ronda_en(m.start(), titulos),
            estadio=limpiar(campos.get("estadio", "")),
            fecha_cruda=limpiar(campos.get("fecha", ""))))
    return partidos


# --------------------------------------------------------------------------
# copa: una tabla por ronda
# --------------------------------------------------------------------------
# En orden. Sirve para encontrar las secciones y para saber cual va despues de
# cual, que en la Copa no se puede deducir de las fechas: las rondas se solapan
# (los treintaidosavos 2026 se jugaron entre enero y abril, y los dieciseisavos
# entre abril y julio, con dias compartidos).
RONDAS = ("Treintaidosavos", "Dieciseisavos", "Octavos", "Cuartos",
          "Semifinales", "Final")

# "Semifinal" y "Semifinales" son la misma ronda escrita de dos maneras; si
# quedan como dos, el orden de las rondas se parte en dos mitades.
_TITULO_RONDA = re.compile(
    r"^=+\s*(Treintaidosavos|Dieciseisavos|Octavos|Cuartos|Semifinales|Semifinal|Final)"
    r"[^=\n]*=+\s*$", re.M | re.I)

_COL_COPA = ["fecha", "estadio", "local", "resultado", "visita"]


def _titulos_de_ronda(texto: str) -> list[tuple[int, str]]:
    """(posicion, ronda) de cada titulo de ronda de la pagina."""
    return [(m.start(), _nombre_de_ronda(m.group(1))) for m in _TITULO_RONDA.finditer(texto)]


def _nombre_de_ronda(crudo: str) -> str:
    n = crudo.capitalize()
    return "Semifinales" if n == "Semifinal" else n


def _ronda_en(pos: int, titulos: list[tuple[int, str]]) -> str:
    """La ronda a la que pertenece lo que esta en `pos`: la del ultimo titulo
    que quedo atras.

    Las llaves de liga vienen como plantillas `{{Partido}}` que no dicen a que
    ronda pertenecen; lo unico que lo dice es bajo que titulo estan. Sin esto,
    todos los partidos de eliminacion quedan sin ronda y `cadena_de_llaves` tiene
    que caer al agrupado por fecha, que no distingue dos partidos de octavos
    jugados en dias distintos de un octavos y un cuartos.
    """
    ronda = ""
    for donde, nombre in titulos:
        if donde > pos:
            break
        ronda = nombre
    return ronda

# Los penales de la Copa: `{{small|(5)}} 1 - 1 {{small|(4)}}`, o con la etiqueta
# HTML `<small>(5)</small>`. OJO que esto es lo OPUESTO a lo que significa un
# parentesis en una plantilla {{Partido}}, donde `1:1 (0:0)` es el entretiempo.
# Se distinguen por lo que hay adentro: un solo numero es la tanda de ese equipo,
# dos numeros separados por `:` son los goles del primer tiempo.
_PENAL = re.compile(r"(?:\{\{\s*small\s*\||<small>)\s*\((\d+)\)", re.I)


def _penales(celda_cruda: str) -> tuple[int, int] | None:
    """Los penales de una celda de marcador, ANTES de limpiarla.

    Tiene que correr sobre el texto crudo: `limpiar` borra las plantillas, y la
    tanda vive adentro de una. Limpiando primero, `{{small|(5)}} 1 - 1
    {{small|(4)}}` queda en `1 - 1` y la definicion desaparece sin que nada falle.
    """
    n = _PENAL.findall(celda_cruda)
    return (int(n[0]), int(n[1])) if len(n) == 2 else None


def partidos_de_rondas(texto: str, anio: int, torneo: str) -> list[Partido]:
    """La Copa Argentina: una tabla por ronda, `Fecha | Estadio | Eq1 | Partido | Eq2`."""
    partidos: list[Partido] = []
    for m in _TITULO_RONDA.finditer(texto):
        # La seccion termina en el proximo titulo, sea del nivel que sea, y no en
        # la proxima ronda: la ultima ronda jugada es la ultima seccion de ronda
        # de la pagina, pero abajo siguen "Goleadores", "Referencias" y sus
        # tablas, que sin este corte entran como si fueran partidos.
        sig = re.search(r"^=+[^=\n]", texto[m.end():], re.M)
        fin = m.end() + (sig.start() if sig else len(texto) - m.end())
        ronda = _nombre_de_ronda(m.group(1))
        for fila in re.split(r"\n\|-", texto[m.end():fin]):
            if not fila.strip() or fila.lstrip().startswith("!"):
                continue
            celdas = _partir(fila)
            if len(celdas) < len(_COL_COPA):
                continue
            v = dict(zip(_COL_COPA, (_celda(c)[1] for c in celdas)))
            goles = _marcador(v["resultado"])
            if not goles or not v["local"] or not v["visita"]:
                continue          # ronda en curso: la fila esta pero sin marcador
            pen = _penales(celdas[_COL_COPA.index("resultado")])
            partidos.append(Partido(
                fecha=a_iso(v["fecha"], anio), local=v["local"], visita=v["visita"],
                goles_local=goles[0], goles_visita=goles[1],
                penales_local=pen[0] if pen else None,
                penales_visita=pen[1] if pen else None,
                torneo=torneo, fase="eliminacion", jornada=ronda,
                estadio=v["estadio"], fecha_cruda=v["fecha"]))
    return partidos


# --------------------------------------------------------------------------
def partidos(texto: str, anio: int, torneo: str, formato: str = "liga") -> list[Partido]:
    """Todos los partidos de una pagina.

    `formato` lo dice el catalogo y no se adivina: una pagina de copa y una de
    liga se parecen lo suficiente como para que una deteccion automatica devuelva
    cero partidos en vez de fallar.
    """
    if formato == "copa":
        return partidos_de_rondas(texto, anio, torneo)
    m = re.search(r"===+\s*Resultados\s*===+(.*?)(?=\n==[^=])", texto, re.S)
    zonas = partidos_de_tabla(m.group(1), anio, torneo) if m else []
    return zonas + partidos_de_plantillas(texto, anio, torneo)

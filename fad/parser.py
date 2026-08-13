#!/usr/bin/env python3
"""
fad/parser.py
=============
Sacar los partidos del wikitexto de una temporada.

Conviven TRES formatos, y el mismo torneo cambia de uno a otro segun el anio:

1. FASE DE GRUPOS -- una `wikitable` con columnas
   `Local | Resultado | Visitante | Estadio | Fecha | Hora`.
   Lo dificil es el `rowspan`: cuando varios partidos comparten fecha u horario,
   la celda aparece UNA sola vez y las filas siguientes vienen con menos celdas.
   Un parser que asuma "6 celdas por fila" corre las columnas y termina leyendo
   el estadio como si fuera la fecha, sin fallar.

2. ELIMINACION -- plantillas `{{Partido|local=...|resultado=...}}` con parametros
   nombrados, practicamente un JSON.

3. COPA -- una tabla por ronda, `Fecha | Estadio | Equipo 1 | Partido | Equipo 2`,
   con las celdas separadas por `||` en un solo renglon. Cual usar lo dice el
   catalogo (`torneos.Torneo.formato`) y no se adivina: el parser equivocado no
   falla, devuelve cero partidos.

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

# Nombres de columna que a veces vienen con colspan. NO son etiquetas de seccion.
_COLUMNAS_CONOCIDAS = {"local", "resultado", "visitante", "visita", "estadio",
                       "fecha", "hora", "partido", "equipo 1", "equipo 2",
                       "equipo", "arbitro", "árbitro", "ciudad"}

# El titulo "Resultados" aparece en nivel 2 o en nivel 3 segun la temporada: las
# de Primera de 2016 a 2024 lo ponen como `== Resultados ==` y las de 2025-26
# como `=== Resultados ===`. Pidiendo tres `=` o mas, nueve temporadas devolvian
# CERO partidos -- que no se distingue de "todavia no empezo el torneo".
_TITULO_RESULTADOS = re.compile(r"^(=+)\s*Resultados\s*=+\s*$", re.M)
# Cualquier titulo de Wikipedia. Sirve para cortar la jornada: lo que viene
# despues de un titulo no pertenece a la tabla de arriba.
_TITULO_CUALQUIERA = re.compile(r"^=+[^=\n]+=+\s*$", re.M)

# Un titulo de zona de primer nivel: `== Zona A ==`. En el ascenso la zona no
# viene en un encabezado de tabla sino en el titulo de la seccion que la contiene.
_TITULO_ZONA = re.compile(r"^==\s*((?:Zona|Grupo)\b[^=\n]*?)\s*==\s*$", re.M | re.I)


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
    llave: str = ""              # que cuadro de eliminacion: una pagina tiene varios
    # A que ARTICULO de Wikipedia enlaza cada equipo. Es el unico dato que
    # identifica al club sin ambiguedad: "Estudiantes" a secas es el de La Plata
    # en Primera y el de Caseros en Primera B, pero los articulos son distintos.
    local_art: str = field(default="", repr=False)
    visita_art: str = field(default="", repr=False)
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
    # La misma plantilla SIN cerrar tambien existe, y como no cierra no la agarra
    # ni la de arriba ni el barrido general: un club quedaba llamandose
    # "{{nowrap|Defensores de Cambaceres".
    s = re.sub(r"\{\{\s*nowrap\s*\|", "", s, flags=re.I)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    # Un enlace a un archivo NO es texto: `[[Archivo:Copa.svg|15px|Campeón]]` es
    # una imagen. Tratandolo como un wikilink comun queda "15px|Campeón" pegado
    # al nombre, y el equipo pasa a llamarse "Boca Juniors 15px|Campeón
    # matematico". Van 20 nombres asi en las temporadas 2016-2024, donde se
    # marcaba al campeon y a los descendidos con un iconito.
    s = re.sub(r"\[\[\s*(?:Archivo|File|Imagen|Image)\s*:[^\]]*\]\]", "", s, flags=re.I)
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


def articulos_de_la_pagina(texto: str) -> dict[str, str]:
    """{nombre visible: articulo} para toda la pagina, y SOLO cuando es univoco.

    Las tablas de resultados muchas veces escriben el equipo sin enlace, pero la
    seccion de equipos participantes si lo enlaza. Con este mapa, un "Estudiantes"
    pelado en una tabla se resuelve con el enlace que la misma pagina uso en otro
    lado.

    Si dentro de UNA pagina el mismo nombre visible apunta a dos articulos, no se
    devuelve ninguno: ahi no hay testigo, y adivinar es justo lo que no hay que
    hacer.
    """
    vistos: dict[str, set] = {}
    for destino, visible in re.findall(r"\[\[([^\]|]+)\|([^\]]+)\]\]", texto):
        d = destino.strip()
        if d.lower().startswith(("estadio", "provincia", "anexo", "archivo", "file")):
            continue
        vistos.setdefault(limpiar(visible), set()).add(d)
    return {v: next(iter(d)) for v, d in vistos.items() if len(d) == 1}


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


# Mes en que arranca una temporada que cruza el calendario. Los partidos de ese
# mes en adelante son del PRIMER anio; los anteriores, del segundo. Es el valor
# mas comun (agosto), pero NO sirve para todas: la 2019-20 arranco el 26 de julio
# de 2019, y con el corte en agosto su Fecha 1 entera quedaba fechada en julio de
# 2020 -- la primera jornada del torneo, un anio adelante, al final de la
# temporada. Por eso el mes va por temporada en el catalogo.
MES_INICIO_HABITUAL = 8


def a_iso(texto: str, anio: int, anio_fin: int | None = None,
          mes_inicio: int = MES_INICIO_HABITUAL) -> str:
    """'22 de enero' -> '2026-01-22'. Cadena vacia si no se entiende.

    Las paginas escriben el dia y el mes pero NO el anio, porque en la pagina se
    sobreentiende. Para un torneo dentro de un mismo anio alcanza con ponerselo;
    para los que cruzan -- 2016-17, 2017-18, 2018-19, 2019-20 -- hay que decidirlo
    por el mes, y equivocarse ahi no falla: fecha media temporada un anio entero
    para atras, el partido queda antes de que el torneo empezara, y cualquiera
    que despues filtre por fecha lo lee donde no corresponde.
    """
    m = re.search(r"(\d{1,2})\s*de\s+([a-záéíóúñ]+)", texto, re.I)
    if not m:
        return ""
    mes_txt = unicodedata.normalize("NFKD", m.group(2).lower()).encode("ascii", "ignore").decode()
    mes = MESES.get(mes_txt)
    if not mes:
        return ""
    y = anio if (anio_fin is None or mes >= mes_inicio) else anio_fin
    return f"{y}-{mes:02d}-{int(m.group(1)):02d}"


_PLANTILLA_FECHA = re.compile(r"\{\{\s*fecha\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})\s*\|\s*(\d{4})\s*\}\}",
                              re.I)


def _fecha_de_plantilla(crudo: str) -> str:
    """`{{fecha|17|1|2021}}` -> '2021-01-17'. Vacio si no es esa forma.

    Hay que leerla ANTES de limpiar, porque limpiar borra las plantillas y deja
    la celda en ', 22:10 (UTC-3)' -- un partido sin fecha.

    Ademas trae el anio EXPLICITO, que acá no es un lujo: la final de la Copa de
    la Liga 2020 se jugo el 17 de enero de 2021. Cualquier anio deducido del
    torneo la habria puesto un anio antes.
    """
    m = _PLANTILLA_FECHA.search(crudo)
    if not m:
        return ""
    dia, mes, anio = (int(g) for g in m.groups())
    return f"{anio}-{mes:02d}-{dia:02d}" if 1 <= mes <= 12 and 1 <= dia <= 31 else ""


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
    rompia nada, solo mentia. Lo mira `validar.una_vez_por_jornada`.
    """
    bloque = re.sub(r"\n\|\}", "\n|-", bloque)          # cierre  |}
    return re.sub(r"\n\{\|[^\n]*", "\n|-", bloque)      # apertura {|class=...


def partidos_de_tabla(bloque: str, anio: int, torneo: str, anio_fin: int | None = None,
                      mes_inicio: int = MES_INICIO_HABITUAL,
                      zona_defecto: str = "", llave: str = "",
                      arts: dict[str, str] | None = None) -> list[Partido]:
    partidos: list[Partido] = []
    pendientes: dict[str, list] = {}        # columna -> [valor, filas restantes]
    # La zona puede venir de un encabezado de tabla (`!colspan=6|Zona A`) o del
    # titulo de la seccion que contiene a esta tabla, que es como lo hace el
    # ascenso. Si aparece un encabezado, pisa al de la seccion.
    jornada, zona = "", zona_defecto

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
        # `[^|\n]*` entre el colspan y la barra: el encabezado puede traer mas
        # atributos, y muchas paginas del ascenso escriben
        # `!colspan=3 align=center|Fecha 1`. Exigiendo la barra pegada al numero,
        # esas jornadas no se leian -- los 380 partidos de una temporada quedaban
        # todos sin `matchday`, sin que nada fallara.
        for cab in re.findall(r"!\s*colspan\s*=\s*\"?\d+\"?[^|\n]*\|\s*(.+)", fila):
            cab = limpiar(cab)
            if not cab:
                continue
            # Un encabezado cuyo texto es el nombre de una COLUMNA no es una
            # seccion: `!colspan=2 ...|Partido` encabeza la columna del marcador.
            # Antes no molestaba porque el regex no los veia; al aflojarlo para
            # leer `!colspan=3 align=center|Fecha 1`, uno de estos se colaba como
            # zona y dejaba una temporada con 1 partido con zona y 300 sin.
            if cab.lower() in _COLUMNAS_CONOCIDAS:
                continue
            pendientes.clear()      # un rowspan no cruza de una seccion a otra
            if re.match(r"(?i)fecha\s*\d+", cab):
                jornada = cab
            else:
                zona = _seccion(cab)
        if fila.lstrip().startswith("!"):
            continue                                   # fila de encabezado

        # Un titulo de Wikipedia cierra la jornada. Dentro de la seccion de
        # resultados puede aparecer `=== Partido de desempate del primer puesto ===`
        # -- la final del campeonato, cuando dos equipos terminan igualados -- y
        # ese partido NO es de la ultima fecha: es otra cosa. Sin cortar, se
        # quedaba con la jornada de la tabla anterior y dejaba a la Fecha 25 con
        # 13 partidos y dos equipos jugando dos veces, que es imposible.
        if _TITULO_CUALQUIERA.search(fila):
            jornada = ""
            pendientes.clear()

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
            fecha=a_iso(valores["fecha"], anio, anio_fin, mes_inicio), hora=valores["hora"],
            local=valores["local"], visita=valores["visita"],
            goles_local=goles[0], goles_visita=goles[1],
            torneo=torneo, fase="zonas", zona=zona, jornada=jornada, llave=llave,
            local_art=(arts or {}).get(valores["local"], ""),
            visita_art=(arts or {}).get(valores["visita"], ""),
            estadio=valores["estadio"], fecha_cruda=valores["fecha"]))
    return partidos


# --------------------------------------------------------------------------
# eliminacion: plantillas {{Partido}}
# --------------------------------------------------------------------------
def partidos_de_plantillas(texto: str, anio: int, torneo: str, anio_fin: int | None = None,
                           mes_inicio: int = MES_INICIO_HABITUAL,
                       arts: dict[str, str] | None = None) -> list[Partido]:
    titulos = _titulos_de_ronda(texto)
    arts = arts or articulos_de_la_pagina(texto)
    partidos: list[Partido] = []
    # Una pagina puede traer VARIOS cuadros: la final del campeonato, el torneo
    # reducido y la definicion de un ascenso son tres eliminaciones distintas que
    # no se encadenan entre si. Cual es cual lo dice la seccion de nivel 2.
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
            fecha=(_fecha_de_plantilla(campos.get("fecha", ""))
                   or a_iso(limpiar(campos.get("fecha", "")), anio, anio_fin, mes_inicio)),
            local=limpiar(campos.get("local", "")),
            visita=limpiar(campos.get("visita", "")),
            goles_local=goles[0], goles_visita=goles[1],
            penales_local=pen[0] if pen else None,
            penales_visita=pen[1] if pen else None,
            torneo=torneo, fase="eliminacion",
            jornada=_ronda_en(m.start(), titulos, _inicio_de_llave(m.start(), texto)),
            local_art=arts.get(limpiar(campos.get("local", "")), ""),
            visita_art=arts.get(limpiar(campos.get("visita", "")), ""),
            llave=_contexto(m.start(), 3, texto),
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
# En orden, de la mas lejana a la final. El ascenso agrega las "fases" del
# torneo reducido, que van antes de las semis.
RONDAS = ("Primera fase", "Segunda fase", "Tercera fase",
          "Treintaidosavos", "Dieciseisavos", "Octavos", "Cuartos",
          "Semifinales", "Final")

# "Semifinal" y "Semifinales" son la misma ronda escrita de dos maneras; si
# quedan como dos, el orden de las rondas se parte en dos mitades.
_TITULO_RONDA = re.compile(
    r"^=+\s*(Primera fase|Segunda fase|Tercera fase|Treintaidosavos|Dieciseisavos"
    r"|Octavos|Cuartos|Semifinales|Semifinal|Final)[^=\n]*=+\s*$", re.M | re.I)

_COL_COPA = ["fecha", "estadio", "local", "resultado", "visita"]


def _titulos_de_ronda(texto: str) -> list[tuple[int, str]]:
    """(posicion, ronda) de cada titulo de ronda de la pagina."""
    return [(m.start(), _nombre_de_ronda(m.group(1))) for m in _TITULO_RONDA.finditer(texto)]


def _nombre_de_ronda(crudo: str) -> str:
    n = crudo.capitalize()
    return "Semifinales" if n == "Semifinal" else n


def _inicio_de_llave(pos: int, texto: str) -> int:
    """Donde empieza la seccion de nivel 2 que contiene a `pos`."""
    inicio = 0
    for m in _TITULO.finditer(texto[:pos]):
        if len(m.group(1)) <= 2:
            inicio = m.start()
    return inicio


def _ronda_en(pos: int, titulos: list[tuple[int, str]], desde: int = 0) -> str:
    """La ronda a la que pertenece lo que esta en `pos`: la del ultimo titulo
    que quedo atras.

    Las llaves de liga vienen como plantillas `{{Partido}}` que no dicen a que
    ronda pertenecen; lo unico que lo dice es bajo que titulo estan.

    `desde` acota la busqueda al cuadro actual, y hace falta: una pagina del
    ascenso tiene una seccion `== Final ==` (la del campeonato) y despues un
    `== Torneo reducido ==` con sus propias fases. Sin acotar, los partidos de la
    "Primera fase" del reducido se quedaban con el "Final" arrastrado de la
    seccion anterior, y el chequeo del cuadro encadenaba semifinales con finales
    que no tenian nada que ver: 21 avisos sobre datos correctos.
    """
    ronda = ""
    for donde, nombre in titulos:
        if donde > pos:
            break
        if donde >= desde:          # solo las rondas de ESTE cuadro
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


def partidos_de_rondas(texto: str, anio: int, torneo: str, anio_fin: int | None = None,
                       mes_inicio: int = MES_INICIO_HABITUAL,
                       arts: dict[str, str] | None = None) -> list[Partido]:
    """La Copa Argentina: una tabla por ronda, `Fecha | Estadio | Eq1 | Partido | Eq2`."""
    partidos: list[Partido] = []
    for m in _TITULO_RONDA.finditer(texto):
        # La seccion termina en el proximo titulo, sea del nivel que sea, y no en
        # la proxima ronda: la ultima ronda jugada es la ultima seccion de ronda
        # de la pagina, pero abajo siguen "Goleadores", "Referencias" y sus
        # tablas, que sin este corte entran como si fueran partidos.
        # Corta en el proximo titulo del MISMO nivel o mas alto, no en cualquiera.
        # Las ediciones viejas de la Copa parten cada ronda en subsecciones, y
        # cortando en el primer subtitulo se leia solo la primera tabla: la
        # 2011-12 daba UN partido de sesenta. Los subtitulos entran en la ronda;
        # la ronda siguiente, no.
        nivel = len(re.match(r"=+", m.group(0)).group(0))
        sig = re.search(rf"^={{1,{nivel}}}[^=]", texto[m.end():], re.M)
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
                fecha=a_iso(v["fecha"], anio, anio_fin, mes_inicio), local=v["local"], visita=v["visita"],
                goles_local=goles[0], goles_visita=goles[1],
                penales_local=pen[0] if pen else None,
                penales_visita=pen[1] if pen else None,
                torneo=torneo, fase="eliminacion", jornada=ronda,
                local_art=(arts or {}).get(v["local"], ""),
                visita_art=(arts or {}).get(v["visita"], ""),
                estadio=v["estadio"], fecha_cruda=v["fecha"]))
    return partidos


# --------------------------------------------------------------------------
def secciones_de_resultados(texto: str) -> list[tuple[str, str, str]]:
    """(zona, fase, cuerpo) de CADA seccion "Resultados" de la pagina.

    Son varias, no una, y cada una pertenece a algo distinto:

      * en el ascenso, `== Zona A ==` y `== Zona B ==` son secciones de primer
        nivel y cada una trae su propio `=== Resultados ===`;
      * en Primera B y C, lo que hay arriba es `== Torneo Apertura ==` y
        `== Torneo Clausura ==`, o sea DOS torneos en una pagina, cada uno con su
        Fecha 1.

    Buscando una sola seccion se leia la mitad: la Primera Nacional 2025 daba 26
    equipos donde hay 38. Y sin el contexto, las dos "Fecha 1" de Primera B se
    mezclaban en una y todos los equipos parecian jugar dos veces por fecha.

    El corte va hasta el proximo titulo del MISMO nivel o mas alto, asi que una
    seccion con subsecciones entra entera pero no se come a su hermana.
    """
    fuera, hasta = [], 0
    for m in _TITULO_RESULTADOS.finditer(texto):
        # Una seccion "Resultados" ADENTRO de otra ya vino en el cuerpo de la de
        # afuera. Tomandola igual, cada partido entra dos veces y todos los
        # equipos parecen jugar dos veces por fecha. Se saltea la de adentro.
        if m.start() < hasta:
            continue
        nivel = len(m.group(1))
        resto = texto[m.end():]
        sig = re.search(rf"^={{1,{nivel}}}[^=]", resto, re.M)
        cuerpo = resto[:sig.start()] if sig else resto
        hasta = m.end() + len(cuerpo)
        # Dos contextos, y hacen falta los dos. El PADRE inmediato es la zona
        # ("Grupo A"); la seccion de nivel 2 es la fase del torneo ("Fase
        # Campeonato"). La Copa de la Liga 2020 tuvo Fase Clasificatoria, Campeonato
        # y Complementacion, y CADA UNA con su Grupo A y su Fecha 1: quedandose solo
        # con el padre, los mismos equipos aparecian jugando dos veces la misma fecha.
        # `min(nivel, 3)`: la fase nunca se busca en un nivel igual o mayor al
        # del propio titulo "Resultados". Cuando este es de nivel 2 -- como en
        # los torneos de 2004-2015 -- pedir nivel 3 devolvia la seccion de nivel 2
        # ANTERIOR, que no lo contiene: los 190 partidos del Inicial 2012
        # quedaban bajo una fase llamada "Tabla de posiciones final".
        fuera.append((_contexto(m.start(), nivel, texto),
                      _contexto(m.start(), min(nivel, 3), texto), cuerpo))
    return fuera


_TITULO = re.compile(r"^(=+)\s*([^=\n]+?)\s*=+\s*$", re.M)


def _contexto(pos: int, nivel: int, texto: str) -> str:
    """El titulo de la seccion que CONTIENE a esta.

    Es el ultimo titulo de nivel MENOR que quedo atras. Que sea menor y no
    "cualquiera" importa: en las paginas de Primera de 2016 a 2024 el propio
    `== Resultados ==` es de nivel 2, y tomando el titulo anterior sin mirar el
    nivel, los 4400 partidos de esas temporadas quedaban agrupados bajo la
    seccion que estuviera arriba.
    """
    ctx = ""
    for m in _TITULO.finditer(texto[:pos]):
        if len(m.group(1)) < nivel:
            ctx = _seccion(limpiar(m.group(2)))
    return ctx


def partidos(texto: str, anio: int, torneo: str, formato: str = "liga",
             anio_fin: int | None = None,
             mes_inicio: int = MES_INICIO_HABITUAL) -> list[Partido]:
    """Todos los partidos de una pagina.

    `formato` lo dice el catalogo y no se adivina: una pagina de copa y una de
    liga se parecen lo suficiente como para que una deteccion automatica devuelva
    cero partidos en vez de fallar.
    """
    if formato == "copa":
        return partidos_de_rondas(texto, anio, torneo, anio_fin, mes_inicio,
                                  articulos_de_la_pagina(texto))
    arts = articulos_de_la_pagina(texto)
    zonas = []
    for zona, fase, cuerpo in secciones_de_resultados(texto):
        zonas += partidos_de_tabla(cuerpo, anio, torneo, anio_fin, mes_inicio,
                                   zona_defecto=zona, llave=fase, arts=arts)
    return zonas + partidos_de_plantillas(texto, anio, torneo, anio_fin, mes_inicio)

#!/usr/bin/env python3
"""
fad/rsssf.py
============
Sacar de RSSSF la FECHA de partidos que ya tenemos, igual que `fad/fechas.py`
hace con worldfootball. Nada mas que la fecha: equipos, marcador y jornada siguen
saliendo de Wikipedia, y `source` lo dice fila por fila.

POR QUE HACE FALTA OTRA FUENTE
------------------------------
worldfootball no llega: su selector para Argentina lista Primera, Primera
Nacional, Primera B Metropolitana (desde 2018/19), Copa Argentina y Supercopa. El
Torneo Argentino A -- la tercera categoria del interior -- no figura. RSSSF si lo
tiene, y lo tiene entero en una sola pagina de texto plano.

UNA ADVERTENCIA SOBRE ESTA FUENTE EN PARTICULAR
-----------------------------------------------
Este proyecto ya se encontro a RSSSF del otro lado. Arbitrando el Clausura 2005
resulto que su tabla de posiciones era identica a la de Wikipedia CON EL MISMO
desbalance de 3 goles: no era un testigo independiente sino el ancestro del error.

Aca eso no aplica, y conviene decir por que en vez de dar por hecho que no aplica.
El riesgo de circularidad existe cuando las dos fuentes pueden haberse copiado el
dato en disputa. Para estos torneos Wikipedia NO PUBLICA FECHA -- es la razon por
la que sus partidos estaban en `data/sin-fecha/` --, asi que la fecha de RSSSF no
puede ser un eco de Wikipedia ni al reves. Es informacion nueva.

Y el marcador, que si podria ser un eco, no se importa: se usa como VERIFICACION.
Si RSSSF y nosotros no coincidimos en el resultado, no se toma la fecha.

EL FORMATO
----------
Texto plano dentro de un `<pre>`, con la fecha por partido y no por jornada, que
es exactamente lo que hace falta -- en el ascenso argentino solo el 19% de las
jornadas se juega en un solo dia:

    Round 1 [Aug 21]
    Sportivo Desamparados        0-1 Villa Mitre

    Round 2
    [Aug 27]
    La Plata FC                  2-0 Cipolletti
    [Aug 28]
    Guillermo Brown              2-0 Sportivo Desamparados

DOS TRAMPAS
-----------
1. La pagina NO declara charset y no es UTF-8: es latin-1. Sin eso "Lujan de
   Cuyo" llega roto y no cruza con nada.
2. Las anotaciones van entre corchetes y ENCABALGADAS en varias lineas:

    Ñuñorco                  1-2 Atlético Candelaria     [abandoned at 2-1 in 85',
                                                          awarded 0-1 against both]

   Un regex de "nombre  N-N nombre" lee la continuacion como si fuera un partido y
   se inventa clubes que se llaman "Atlético Candelaria     [abandoned at 2-1 in
   85',". Por eso se corta la linea en el primer `[` y se exige que lo que quede
   cierre como partido.

POR QUE EL MAPA DE NOMBRES VA A MANO
------------------------------------
Porque resolverlos por el padron da el club EQUIVOCADO, no un error. RSSSF escribe
los nombres cortos, y en este torneo:

    "Racing"   -> `equipos.buscar` devuelve Racing Club, el de Avellaneda, que
                  nunca jugo el Argentino A. Aca es Racing de Olavarria en la Zona
                  Sur y Racing de Cordoba en la Zona Norte: DOS clubes distintos
                  bajo el mismo nombre, en el mismo torneo.
    "Talleres" -> devuelve Talleres (C), el de Cordoba. Aca es el de Perico.
    "San Martin", "Juventud", "Gimnasia y Esgrima", "9 de Julio" -> lo mismo.

Es el error que el proyecto ya conoce y que ningun chequeo de padron agarra: el
nombre existe, resuelve, y apunta a otro lado. Asi que el mapa es explicito y POR
ZONA, y lo que no esta en el mapa no se empareja.
"""
from __future__ import annotations

import re
import urllib.request
from pathlib import Path

from fad import wiki
from fad.fechas import Ajeno

CREDITO = "https://www.rsssf.org/"

_CACHE = Path(__file__).resolve().parent.parent / ".cache" / "rsssf"

_MESES = {m: i + 1 for i, m in enumerate(
    "Jan Feb Mar Apr May Jun Jul Aug Sep Oct Nov Dec".split())}

# El dia viene entre corchetes o entre parentesis segun la temporada, y no hay una
# forma "correcta": 2005-06 y 2008-09 escriben `[Oct 14]` en las 106 y las 120
# lineas, 2007-08 escribe `(Aug 24)` en las 195 sin un solo corchete, y 2006-07
# mezcla -- 175 corchetes y un unico parentesis --.
#
# Aceptar una sola forma no deja el partido afuera, que seria lo benigno: la fecha
# ANTERIOR sigue viva y se les pega a los partidos de abajo. Ese unico parentesis
# de 2006-07 fecho `La Plata FC 1-2 Juventud` el 15 de octubre cuando la linea de
# arriba dice 16. Y 2007-08 entero habria entrado con cero partidos, sin ruido.
#
# El par desparejo -- `[Oct 16)` -- tambien pasa, y esta bien que pase: la forma ya
# es inconfundible por dentro (mes de tres letras y dia, solos en la linea), asi
# que ser laxo con el delimitador no admite nada que no sea una fecha.
_DIA = r"[\[(]([A-Z][a-z]{2})\s+(\d+)[\])]"
_RONDA = re.compile(r"^Round\s+(\d+)(?:\s*" + _DIA + r")?\s*$")
# "Apertura 2006" / "Clausura 2007": la llave sin la palabra "Torneo" adelante.
# RSSSF escribe las dos formas segun la temporada, y la diferencia no es cosmetica:
# el Argentino A 2006-07 corre un Apertura y un Clausura sobre LAS MISMAS tres
# zonas, los dos numerando sus fechas de 1 a 14. Leyendo esta linea como texto
# suelto, las dos mitades caian en la misma casilla y cada zona terminaba con el
# doble de partidos por fecha -- 112 donde van 56 --, que es como se encontro.
_LLAVE_PELADA = re.compile(r"^(Apertura|Clausura)\s+\d{4}$")

_SOLO_FECHA = re.compile(r"^" + _DIA + r"\s*$")
# Dos espacios o mas separan las columnas. El nombre del local no puede tener
# corchetes: si los tiene es una anotacion encabalgada, no un partido.
#
# Y el visitante corta en la proxima corrida de dos espacios, porque la anotacion
# de un partido puede DERRAMARSE sobre la linea del siguiente, que es un partido
# de verdad:
#
#     La Florida                   awd Sportivo Patria         [abandoned at 2-2
#     Gimnasia y Esgrima           5-2 Ñuñorco                  in 90', awarded
#
# El de abajo es Gimnasia 5-2 Ñuñorco; lo que sigue es la cola del de arriba. Sin
# cortar, el visitante pasaba a llamarse "Ñuñorco   in 90', awarded" y el partido
# se perdia. Se perdia UNO solo, y por eso importa que el mapa avise en vez de
# saltearse en silencio lo que no traduce: fue el aviso el que lo delato.
#
# El separador antes del marcador es `\s+` y no `\s{2,}`, aunque a la vista la
# tabla parezca de columnas anchas. El marcador arranca en la columna 29 fija, y
# "Juventud Unida Universitario" mide 28: le queda UN espacio. Con `\s{2,}` se
# perdian sus doce partidos de local, y como el club es el mismo en todos, se
# perdian de a bloques y no al azar -- que es la forma de fallar mas facil de no
# ver, porque no rompe nada, solo deja un club sin fechar.
_PARTIDO = re.compile(
    r"^([^\[\]]{3,34}?)\s+(\d+)-(\d+)\s+([^\[\]\s](?:[^\[\]]*?[^\[\]\s])?)(?:\s{2,}.*)?$")


def descargar(archivo: str, usar_cache: bool = True) -> str:
    """El texto de la pagina de RSSSF, en latin-1."""
    destino = _CACHE / f"{archivo}.txt"
    if usar_cache and destino.exists():
        return destino.read_text(encoding="utf-8")
    url = f"https://www.rsssf.org/tablesa/{archivo}.html"
    req = urllib.request.Request(url, headers={"User-Agent": wiki.UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        crudo = r.read()
    # La pagina no declara charset y no es UTF-8.
    texto = crudo.decode("latin-1")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    return texto


def _fecha_iso(mes: int, dia: int, anio: int, anio_fin: int, mes_inicio: int) -> str:
    """El anio sale de si el mes cae antes o despues del arranque de temporada.

    Es la misma regla que usa `parser.a_iso` y por el mismo motivo: la temporada
    cruza el calendario, y agosto es del primer anio mientras que marzo es del
    segundo."""
    return f"{anio if mes >= mes_inicio else anio_fin:04d}-{mes:02d}-{dia:02d}"


def leer(texto: str, mapa: dict[str, dict[str, str]], anio: int, anio_fin: int,
         mes_inicio: int = 8) -> tuple[list[Ajeno], list[str]]:
    """Los partidos de la fase de zonas, ya con el club canonico.

    `mapa` es {seccion de zona: {nombre en RSSSF: nombre canonico}}. Solo se leen
    las secciones que estan en el mapa: los playoffs mezclan las dos zonas y ahi
    un nombre corto deja de identificar a un club, asi que no se emparejan.
    """
    fuera: list[Ajeno] = []
    desconocidos: set[str] = set()
    zona = llave = ""
    ronda: int | None = None
    fecha: tuple[int, int] | None = None
    for linea in texto.split("\n"):
        cruda = linea.rstrip()
        pelada = cruda.strip()
        if not pelada:
            continue
        if (pelada.startswith(("Torneo ", "Zona ", "Second Phase", "Final", "Promoci",
                               "NB:", "Champion", "Relegation"))
                or _LLAVE_PELADA.match(pelada)):
            # Cualquier encabezado cierra la ronda abierta: un `[Aug 27]` no cruza
            # de una seccion a la siguiente.
            #
            # "Torneo Apertura"/"Torneo Clausura" se guardan como LLAVE, que es
            # como los rotula nuestro parser, porque los dos numeran sus jornadas
            # de 1 a 11 y sin eso "Fecha 5" no identifica un partido.
            if pelada.startswith("Torneo "):
                llave, zona = pelada, ""
            elif m_llave := _LLAVE_PELADA.match(pelada):
                # La misma llave, escrita sin el "Torneo" adelante. Se normaliza al
                # nombre largo -- el que usa nuestro parser y el que quedo en el
                # mapa de 2005-06 -- porque el cruce contra la tabla de Wikipedia
                # agrupa por llave, y dos vocabularios no cruzan.
                llave, zona = "Torneo " + m_llave.group(1), ""
            elif pelada.startswith("Zona "):
                zona = pelada
            else:
                zona = ""
            ronda = fecha = None
            continue
        m = _RONDA.match(pelada)
        if m:
            ronda = int(m.group(1))
            fecha = (_MESES[m.group(2)], int(m.group(3))) if m.group(2) else None
            continue
        m = _SOLO_FECHA.match(pelada)
        if m:
            fecha = (_MESES[m.group(1)], int(m.group(2)))
            continue
        if zona not in mapa or ronda is None or fecha is None:
            continue
        m = _PARTIDO.match(cruda)
        if not m:
            continue
        local, gl, gv, visita = m.group(1).strip(), int(m.group(2)), int(m.group(3)), m.group(4).strip()
        cl, cv = mapa[zona].get(local), mapa[zona].get(visita)
        for nombre, c in ((local, cl), (visita, cv)):
            if c is None:
                desconocidos.add(f"{zona}: {nombre}")
        if not cl or not cv:
            continue
        fuera.append(Ajeno(fecha=_fecha_iso(*fecha, anio, anio_fin, mes_inicio),
                           jornada=ronda, local=cl, visita=cv,
                           goles_local=gl, goles_visita=gv, llave=llave,
                           zona=zona))
    avisos = ([f"{len(desconocidos)} nombres de RSSSF que el mapa no traduce: "
               + "; ".join(sorted(desconocidos)[:6])] if desconocidos else [])
    return fuera, avisos


def a_partidos(ajenos: list, torneo: str, temporada: int) -> list:
    """Los `Ajeno` de RSSSF convertidos en filas del dataset.

    ES EL UNICO LUGAR DEL REPO DONDE UNA FILA NO SALE DE WIKIPEDIA, y por eso vale
    decir cuando corresponde usarlo: cuando la pagina de Wikipedia NO TIENE
    GRILLA. Pasa con el Argentino A entre 2006-07 y 2009-10, cuyos articulos
    publican los equipos, la tabla final de cada zona y la fase final, y ningun
    resultado fecha por fecha. Ahi no hay un segundo testigo que elegir: hay una
    sola fuente o no hay temporada.

    LOS CAMPOS QUE `Ajeno` NO TRAE QUEDAN VACIOS, no inventados. RSSSF publica
    fecha, jornada, clubes y marcador, y nada mas: no trae hora, ni cancha, ni
    penales. Rellenar eso con un valor plausible seria afirmar algo que nadie
    verifico, que es justo lo que este repo no hace. Vacio se lee como vacio; un
    dato inventado se lee como un dato.

    `neutral` es la excepcion, y no por descuido: no lo pone esta funcion sino
    `dataset.a_fila`, a partir de la declaracion del TORNEO. Es un dato del
    torneo y no del partido -- la Copa Argentina se juega entera en cancha
    neutral, una liga no --, asi que vale igual venga la fila de donde venga. Por
    eso ninguna de las filas del dataset lo tiene vacio.

    `fuente_fecha` lleva el credito de RSSSF, que es lo que despues termina en la
    columna `source` de esa fila. Un consumidor que quiera solo lo que tambien
    esta en Wikipedia puede filtrar por ahi.

    La `fase` es "zonas" porque `leer` solo devuelve las secciones que el mapa
    nombra, y el mapa nombra zonas: los playoffs mezclan las dos y ahi un nombre
    corto deja de identificar a un club, asi que no se leen. Si algun dia se leen,
    esto tiene que dejar de ser una constante.
    """
    from fad.parser import Partido

    fuera = []
    for a in ajenos:
        fuera.append(Partido(
            fecha=a.fecha,
            local=a.local,
            visita=a.visita,
            goles_local=a.goles_local,
            goles_visita=a.goles_visita,
            torneo=torneo,
            fase="zonas",
            zona=a.zona,
            jornada=f"Fecha {a.jornada}",
            llave=a.llave,
            fuente_fecha=CREDITO,
        ))
    return fuera


# --------------------------------------------------------------------------
# Los mapas, uno por torneo. A mano y por zona: ver el docstring de arriba.
# --------------------------------------------------------------------------
# Torneo Argentino A 2005-06. Doce clubes por zona.
#
# Los que obligan a que esto sea por zona y no un diccionario suelto:
#   "Racing"    Zona Sur   = Racing de Olavarria   (nuestro `Racing (O)`)
#               Zona Norte = Racing de Cordoba     (nuestro `Racing (C)`)
#   "Villa Mitre" aparece en las dos y es el MISMO club (Bahia Blanca), asi que
#               no molesta -- pero conviene saber que no es un descuido.
ARGENTINO_A_2005 = {
    "Zona A - Sur": {
        "Cipolletti": "Cipolletti",
        "Douglas Haig": "Douglas Haig",
        "Guillermo Brown": "Guillermo Brown",
        "Huracán": "Huracán (CR)",
        "Independiente Rivadavia": "Independiente Rivadavia",
        "Juventud": "Juventud (P)",
        "Juventud Unida Universitario": "Juventud Unida Universitario",
        "La Plata FC": "La Plata FC",
        "Luján de Cuyo": "Luján de Cuyo",
        "Racing": "Racing (O)",
        "Sportivo Desamparados": "Desamparados",
        "Villa Mitre": "Villa Mitre",
    },
    "Zona B - Norte": {
        "9 de Julio": "9 de Julio (R)",
        "Atlético Candelaria": "Atlético Candelaria",
        "Atlético Tucumán": "Atlético Tucumán",
        "General Paz Juniors": "General Paz Juniors",
        "Gimnasia y Esgrima": "Gimnasia y Esgrima (CdU)",
        "La Florida": "La Florida",
        "Racing": "Racing (C)",
        "San Martín": "San Martín (T)",
        "Sportivo Patria": "Sportivo Patria",
        "Talleres": "Talleres (P)",
        "Unión de Sunchales": "Unión (S)",
        "Ñuñorco": "Ñuñorco",
    },
}

# {pagina de Wikipedia: (archivo en RSSSF, mapa)}
# Torneo Argentino A 2006-07. Tres zonas de ocho.
#
# ESTA TEMPORADA NO TIENE GRILLA EN WIKIPEDIA. Su articulo publica los equipos
# participantes, la tabla de posiciones final de cada zona y la fase final, y
# ningun resultado fecha por fecha -- se comprobo cargandola al catalogo, que dio
# cero partidos y cien avisos, y se revirtio. Asi que aca RSSSF no es el segundo
# testigo de nada: es la unica fuente que tiene esos partidos, y `source` lo dice
# fila por fila.
#
# COMO SE ARMO EL MAPA, porque no se puede emparejar por parecido: los nombres de
# RSSSF son cortos y el mismo "Racing" es Cordoba aca y Olavarria en 2005-06. Se
# forzo por CARDINALIDAD contra los clubes de cada zona, que salen de las tablas
# de posiciones de la propia Wikipedia -- lo unico que esa pagina si publica --.
# Ocho nombres de RSSSF contra ocho clubes por zona, en las tres.
#
# Dieciocho entraron por el padron o por coincidencia exacta dentro de su zona.
# Los seis restantes no resolvian por texto y quedaron forzados porque en cada
# zona sobraban exactamente dos nombres y dos clubes, y la abreviatura dice cual
# es cual sin ambiguedad:
#
#   Zona A  "Dep. Santamarina"         -> Ramon Santamarina
#   Zona A  "La Plata FC"              -> La Plata FC
#   Zona B  "Indep. Rivadavia"         -> Independiente Rivadavia
#   Zona B  "Juv. Unida Universitario" -> Juventud Unida Universitario
#   Zona C  "Juv. Antoniana"           -> Juventud Antoniana
#   Zona C  "Union de Sunchales"       -> Union (S)
#
# El corte de las zonas de Wikipedia hay que hacerlo por NIVEL de titulo y no
# hasta el proximo `==`: los `Zona A/B/C` son de nivel 3 adentro de una seccion
# de nivel 2, asi que cortar en el proximo `==` se lleva las tres tablas juntas.
# Con eso Zona A daba 24 clubes en vez de 8 y "Juventud" quedaba ambiguo entre
# los tres Juventud del torneo, cuando en su zona hay uno solo.
ARGENTINO_A_2006 = {
    "Zona A": {
        "Dep. Santamarina": "Ramón Santamarina",
        "Douglas Haig": "Douglas Haig",
        "Gimnasia y Esgrima (CdU)": "Gimnasia y Esgrima (CdU)",
        "Guillermo Brown": "Guillermo Brown",
        "Juventud": "Juventud (P)",
        "La Plata FC": "La Plata FC",
        "Real Arroyo Seco": "Real Arroyo Seco",
        "Rivadavia": "Rivadavia (L)",
    },
    "Zona B": {
        "Alumni": "Alumni (VM)",
        "Gimnasia y Esgrima (M)": "Gimnasia y Esgrima (M)",
        "Indep. Rivadavia": "Independiente Rivadavia",
        "Juv. Unida Universitario": "Juventud Unida Universitario",
        "Luján de Cuyo": "Luján de Cuyo",
        "Racing": "Racing (C)",
        "San Martín": "San Martín (SM)",
        "Sp. Desamparados": "Desamparados",
    },
    "Zona C": {
        "9 de Julio": "9 de Julio (R)",
        "Atl. Tucumán": "Atlético Tucumán",
        "Central Norte": "Central Norte (S)",
        "Juv. Antoniana": "Juventud Antoniana",
        "La Florida": "La Florida",
        "Sp. Patria": "Sportivo Patria",
        "Talleres (P)": "Talleres (P)",
        "Unión de Sunchales": "Unión (S)",
    },
}


FUENTES: dict[str, tuple[str, dict]] = {
    "Torneo Argentino A 2005-06": ("arg3-int06", ARGENTINO_A_2005),
    "Torneo Argentino A 2006-07": ("arg3-int07", ARGENTINO_A_2006),
}

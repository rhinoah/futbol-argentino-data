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

import html
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
# Una ronda puede traer anotaciones colgadas: `Round 21 [interzonal 1-2]`,
# `Round 29 [Apr 12] [interzonal 1-2]`. Sin tolerarlas la linea no es una ronda,
# no es una fecha y no es un partido, asi que cae al piso y los partidos que
# vienen abajo se quedan con la RONDA Y LA FECHA ANTERIORES. No faltan: mienten,
# que es la unica forma de fallar que no se nota.
# La cola de una ronda admite las DOS formas en que la fuente marca el
# interzonal: entre corchetes -- `Round 21 [interzonal 1-2]`, 2008-09 -- o
# detras de un guion -- `Round 5 - Interzonal 1-2`, 2009-10 --. La segunda hacia
# fallar el patron entero, y el efecto era el peor posible: la linea dejaba de
# ser una ronda, sus partidos heredaban la ronda ANTERIOR y entraban dos veces,
# una por zona, porque tampoco se los reconocia como interzonales.
_RONDA = re.compile(r"^Round\s+(\d+)(?:\s*" + _DIA + r")?"
                    r"((?:\s*\[[^\]]*\])*"
                    r"(?:\s*-\s*[Ii]nterzonal[^\[]*)?)\s*$")
# "Apertura 2006" / "Clausura 2007": la llave sin la palabra "Torneo" adelante.
# RSSSF escribe las dos formas segun la temporada, y la diferencia no es cosmetica:
# el Argentino A 2006-07 corre un Apertura y un Clausura sobre LAS MISMAS tres
# zonas, los dos numerando sus fechas de 1 a 14. Leyendo esta linea como texto
# suelto, las dos mitades caian en la misma casilla y cada zona terminaba con el
# doble de partidos por fecha -- 112 donde van 56 --, que es como se encontro.
# La llave escrita sin el "Torneo" adelante, con anio ("Apertura 2005") o sin el
# ("Apertura", que es como los rotula 2009-10). El anio es opcional y hace falta
# que lo sea: sin reconocer la forma pelada, los dos torneos de 2009-10 caian bajo
# la misma llave y sus jornadas chocaban -- la fecha 8 del Apertura contra la fecha
# 8 del Clausura --, que es un error ruidoso pero que se arregla en el lugar
# equivocado si uno cree que el problema son los nombres.
_LLAVE_PELADA = re.compile(r"^(Apertura|Clausura)(?:\s+\d{4})?$")

# La fecha tambien la trae adentro: `[Sep 27, interzonal 1-2]`.
_SOLO_FECHA = re.compile(r"^[\[(]([A-Z][a-z]{2})\s+(\d+)(,[^\])]*)?[\])]\s*$")
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


# Un partido cuyo marcador NO ES UN MARCADOR. RSSSF escribe una palabra en la
# columna del resultado -- `abd` abandonado, `awd` fallado -- y cuelga la
# explicacion entre corchetes:
#
#     La Florida               abd Talleres (P)   [abandoned at 3-2 in 88';
#     Sp. Patria               3-1 9 de Julio      result stood]
#
# Estas lineas se venian SALTEANDO EN SILENCIO, que es la cuarta vez que este
# modulo falla de la misma manera. Son diez en las cuatro temporadas, y no todas
# significan lo mismo: dos eran partidos que faltaban de verdad en el dataset y el
# resto son casos que efectivamente no tienen que entrar. El lector no las podia
# distinguir porque nunca las miraba.
#
# El token va suelto -- cualquier palabra corta -- en vez de una lista cerrada,
# porque la lista se queda corta sola en cuanto la fuente use otra abreviatura. Lo
# que hace segura esa laxitud es el filtro de abajo: LOS DOS FLANCOS TIENEN QUE
# TRADUCIR POR EL MAPA DE LA ZONA. Una linea de prosa -- "Douglas Haig and Villa
# Mitre to overall semifinals" -- tambien tiene forma de partido, pero sus flancos
# no son dos clubes del mapa. Medido sobre las dos temporadas catalogadas: con el
# token suelto y sin el filtro entran 74 lineas de prosa; con el filtro quedan las
# 6 reales y ni una de mas.
#
# Los dos espacios antes del token tampoco son decoracion. Con uno solo, el `local`
# no-codicioso parte "Central Norte  awd  9 de Julio" en local="Central",
# token="Norte", y el partido se pierde igual que antes.
_SIN_MARCADOR = re.compile(
    r"^([^\[\]]{3,34}?)\s{2,}([A-Za-z][A-Za-z.]{1,5})\s+"
    r"([^\[\]\s](?:[^\[\]]*?[^\[\]\s])?)(?:\s{2,}(.*))?$")

def _cola(texto: str) -> str:
    """Lo que sobra de una linea despues de lo que ya es otra cosa.

    La nota se derrama sobre la columna libre de la derecha, y esa columna convive
    con lo que la linea de abajo tenga por su cuenta: otro partido, o una fecha
    suelta. Las dos se sacan y queda la cola.
    """
    m = re.match(r"\s*[\[(][A-Z][a-z]{2}\s+\d+[\])]", texto)
    if m:
        return texto[m.end():].strip()
    if _PARTIDO.match(texto) or _SIN_MARCADOR.match(texto):
        partes = re.split(r"\s{2,}", texto.strip())
        return partes[-1].strip() if len(partes) > 1 else ""
    return texto.strip()


def _anotacion(lineas: list[str], i: int, desde: int = 0) -> str:
    """La nota entre corchetes que explica un marcador que no es un marcador.

    Puede arrancar en la linea del partido o varias mas abajo, y sigue hasta que
    cierre. `desde` es donde termina el nombre del visitante, y hace falta: sin
    el, el parentesis de "Talleres (P)" abre la nota y la nota queda siendo "(P)".
    """
    trozos: list[str] = []
    profundidad = 0
    for j in range(i, min(i + 5, len(lineas))):
        texto = lineas[j].rstrip()[desde:] if j == i else _cola(lineas[j].rstrip())
        texto = texto.strip()
        if not profundidad:
            corte = [texto.index(c) for c in "[(" if c in texto]
            if not corte:
                if trozos or j > i + 2:
                    break                    # ya cerro, o no habia nota que buscar
                continue
            texto = texto[min(corte):]
        elif not texto:
            continue
        trozos.append(texto)
        profundidad += texto.count("[") + texto.count("(")
        profundidad -= texto.count("]") + texto.count(")")
        if profundidad <= 0:
            break
    return " ".join(trozos).strip()


_FALLADO = re.compile(r"awarded\s+(\d+)\s*-\s*(\d+)")
_ABANDONADO = re.compile(r"abandoned at\s+(\d+)\s*-\s*(\d+)")


# El motivo del abandono va en una constante y no suelto en el return porque
# `_los_que_se_pierden` lo compara: la pregunta "hay otra linea con este
# partido?" solo tiene sentido para un abandono, que puede tener continuacion.
# Un partido DIVIDIDO no tiene otra linea por definicion, y preguntarselo daba
# un aviso alarmante sobre una decision que ya estaba tomada y escrita.
# EL UNICO QUE SE PIERDE DE VERDAD YA SE FUE A BUSCAR, y no vuelve. Es
# `Juventud Antoniana` vs `Gimnasia y Esgrima (CdU)`, fecha 5 del Grupo B del
# Clausura 2009-10: abandonado 1-1 a los 68'. La pregunta que quedaba abierta era
# si alguna vez se jugo lo que faltaba, porque de eso depende que el partido
# tenga un resultado que escribir.
#
# La respuesta es que no. El blog del propio club --`juveantoniana.blogspot.com`,
# post "LA BANDA DESPIDIO AL SANTO ALENTANDO", del 5 de mayo de 2010-- lo cuenta
# el mismo dia: "El Santo CERRO SU PARTICIPACION con un palido empate 1a1 ante
# Gimnasia de Concepcion del Uruguay en un cotejo, que solo servia para las
# estadisticas. [...] El cotejo se suspendio a los 23 del Segundo tiempo por
# invacion de campo". Ni ese post ni ningun otro menciona una reanudacion, y la
# frase "cerro su participacion" dice que para ese club la temporada termino ahi.
# La tabla final de la propia RSSSF lo confirma por su lado: le da 3 partidos
# jugados a esos dos clubes y 4 a los otros tres del grupo.
#
# Asi que la fila NO ENTRA y no es un pendiente: no hay resultado que escribir
# porque el partido no lo tuvo. Lo que si tiene es el 1-1 al momento del
# abandono, y eso no es un marcador final -- escribirlo seria afirmar algo que
# ninguna fuente afirma.
_SIN_DESENLACE = ("se abandono y la nota no dice que el resultado quedara "
                  "firme: si se completo despues, la fila que entra es la del "
                  "partido completo")


def _leer_anotacion(nota: str) -> tuple[tuple[int, int] | None, str, str]:
    """(marcador, status, motivo). Marcador None = esta fila NO entra.

    El eje del `status` es el de `parser.status_de_la_fila` y con su misma
    precedencia, que no es un detalle: NO LLEGAR AL FINAL MANDA SOBRE EL FALLO.
    Un partido abandonado a los 72' cuyo resultado despues puso un tribunal es
    "suspendido" y no "escritorio", porque lo que la fuente dice sin ambiguedad es
    que no se jugaron los noventa.
    """
    n = nota.lower()
    if "to both" in n or "against both" in n:
        return None, "", ("el fallo le dio derrota a los DOS clubes: son dos "
                          "resultados para un partido y una fila tiene un solo "
                          "marcador, asi que va a `correcciones.DIVIDIDOS`")
    m_ab = _ABANDONADO.search(n)
    m_fa = _FALLADO.search(n)
    if m_ab and "result stood" not in n and not m_fa:
        return None, "", _SIN_DESENLACE
    if m_fa:
        return ((int(m_fa.group(1)), int(m_fa.group(2))),
                "suspendido" if m_ab else "escritorio", "")
    if m_ab:
        return (int(m_ab.group(1)), int(m_ab.group(2))), "suspendido", ""
    return None, "", "la nota no dice como termino" if nota else "no hay nota que leer"



def _sin_etiquetas(texto: str) -> str:
    """El texto sin HTML. Se guarda crudo en la cache y se limpia al leer.

    Hasta 2012-13 no hizo falta y por eso no estaba: los archivos viejos traen sus
    115 etiquetas en la cabecera y el pie, lejos de los partidos, asi que el lector
    nunca las cruzaba. El de 2012-13 las mete ENTRE las filas, y el efecto no fue un
    error sino un cero: la temporada entera leia 0 partidos, sin ruido, que es la
    forma en que este modulo fallo las cinco veces anteriores.
    """
    return html.unescape(re.sub(r"<[^>]+>", "", texto))


def descargar(archivo: str, usar_cache: bool = True) -> str:
    """El texto de la pagina de RSSSF, en latin-1."""
    destino = _CACHE / f"{archivo}.txt"
    if usar_cache and destino.exists():
        return _sin_etiquetas(destino.read_text(encoding="utf-8"))
    url = f"https://www.rsssf.org/tablesa/{archivo}.html"
    req = urllib.request.Request(url, headers={"User-Agent": wiki.UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        crudo = r.read()
    # La pagina no declara charset y no es UTF-8.
    texto = crudo.decode("latin-1")
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(texto, encoding="utf-8")
    return _sin_etiquetas(texto)


# El par de una ronda interzonal, escrito de las dos formas que usa la fuente:
# `Round 21 [interzonal 1-2]` en 2008-09 y el encabezado `Interzonal Group A-B`
# en 2007-08. Por eso admite letras y no solo digitos.
_INTERZONAL = re.compile(r"interzonal\s+(?:group\s+)?([A-Za-z0-9]+\s*-\s*[A-Za-z0-9]+)",
                         re.I)


_SEDE = re.compile(r"\s*\(at\s[^)]*\)\s*$", re.I)


def _sin_sede(nombre: str) -> str:
    """El nombre sin la cancha pegada.

    RSSSF pone la sede en una columna aparte cuando se juega fuera de casa --
    `Boca Unidos 4-1 Alumni    (at Huracán)` -- y ahi el separador de dos
    espacios la deja afuera sola. Pero cuando el nombre del club YA termina en
    parentesis queda pegada a un solo espacio: `Gimnasia y Esgr. (CdU) (at
    Huracán-C)`. Sin despegarla, el mismo club entra como tres clubes distintos
    -- son 2 en el Argentino A 2007-08, que hacian declarar 18 nombres donde
    hay 16 -- y ninguno de los tres esta en el padron, asi que sus partidos se
    caen del cruce sin ruido.
    """
    return _SEDE.sub("", nombre).strip()


def _par_interzonal(anotacion: str) -> str:
    """El par de una ronda interzonal ("1-2"), o "" si la ronda no lo es."""
    m = _INTERZONAL.search(anotacion or "")
    return m.group(1).replace(" ", "") if m else ""


def _fecha_iso(mes: int, dia: int, anio: int, anio_fin: int, mes_inicio: int) -> str:
    """El anio sale de si el mes cae antes o despues del arranque de temporada.

    Es la misma regla que usa `parser.a_iso` y por el mismo motivo: la temporada
    cruza el calendario, y agosto es del primer anio mientras que marzo es del
    segundo."""
    return f"{anio if mes >= mes_inicio else anio_fin:04d}-{mes:02d}-{dia:02d}"


def leer(texto: str, mapa: dict[str, dict[str, str]], anio: int, anio_fin: int,
         mes_inicio: int = 8, desde: str = "",
         hasta: str = "") -> tuple[list[Ajeno], list[str]]:
    """Los partidos de la fase de zonas, ya con el club canonico.

    `mapa` es {seccion de zona: {nombre en RSSSF: nombre canonico}}. Solo se leen
    las secciones que estan en el mapa: los playoffs mezclan las dos zonas y ahi
    un nombre corto deja de identificar a un club, asi que no se emparejan.
    """
    # `desde`/`hasta` acotan a una seccion, y hacen falta desde 2010-11: a partir
    # de ahi RSSSF deja de darle archivo propio a cada division y las mete todas en
    # la pagina del ano. `arg2011` trae la Primera Division, la B Nacional, la B
    # Metropolitana, el Argentino A, la Primera C, el Argentino B y la Primera D,
    # una atras de otra y todas con sus `Round N`.
    #
    # SIN EL CORTE SE LEEN TODAS COMO SI FUERAN LA MISMA. Los encabezados de
    # division no son encabezados de zona -- `Primera C Metropolitano` no empieza
    # con ninguna de las palabras que abren seccion -- asi que la zona no cambia y
    # los partidos de siete torneos caen en la misma bolsa. Que es peor que no
    # leer: el completador de fechas fecharia partidos con la fecha de otro
    # torneo.
    #
    # `hasta` NO ES OPCIONAL EN LA PRACTICA aunque lo sea en la firma: sin el, la
    # seccion se come todo lo que viene abajo. Si se pide y no aparece, se avisa en
    # vez de seguir de largo, porque leer de mas aca es silencioso.
    raros: list[str] = []
    if desde:
        i = texto.find(desde)
        if i < 0:
            return [], [f"no se encontro la seccion {desde.splitlines()[0]!r}"]
        texto = texto[i:]
    if hasta:
        j = texto.find(hasta)
        if j < 0:
            raros.append(f"no se encontro el final de la seccion "
                         f"{hasta.splitlines()[0]!r}; se leyo hasta el final del "
                         f"archivo y puede haber partidos de otro torneo")
        else:
            texto = texto[:j]

    fuera: list[Ajeno] = []
    desconocidos: set[str] = set()
    # Los partidos que la nota deja afuera, con su ronda y sus dos clubes, para
    # poder decir al final cuales se recuperan y cuales se pierden de verdad.
    caidos: list[tuple] = []
    # De que par es la ronda interzonal abierta ("1-2"), o "" si no lo es.
    interzonal = ""
    # Un encabezado interzonal ya visto, esperando a su ronda.
    pendiente = ""
    zona = llave = ""
    ronda: int | None = None
    fecha: tuple[int, int] | None = None
    lineas = texto.split("\n")
    for idx, linea in enumerate(lineas):
        cruda = linea.rstrip()
        pelada = cruda.strip()
        if not pelada:
            continue
        # Un encabezado interzonal NO abre una seccion: dice que la ronda que
        # viene abajo pertenece a DOS grupos y esta impresa bajo los dos. Se
        # anota como pendiente y se aplica a la proxima ronda, una sola vez; si
        # borrara la zona, sus partidos se quedarian sin ella.
        if _par_interzonal(pelada) and pelada.lower().startswith("interzonal"):
            pendiente = _par_interzonal(pelada)
            continue
        if (pelada.startswith(("Torneo ", "Zona ", "Zone ", "Group ", "Undecagonal",
                               "First Phase", "Second Phase", "Final", "Promoci",
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
                #
                # UNA LLAVE QUE NO CAMBIA LA LLAVE NO CIERRA NADA, y esa condicion
                # es la que deja convivir dos temporadas que se contradicen. El
                # 2009-10 rotula sus dos torneos con la palabra sola -- `Apertura`,
                # `Clausura` -- y sin reconocerla sus jornadas chocan de a pares.
                # Pero una palabra suelta REPETIDA adentro de una zona ya abierta no
                # es un encabezado, y tratarla como tal apaga la zona y se lleva en
                # silencio todos los partidos que vengan atras. Al exigir que la
                # llave cambie, la primera se lee y la segunda no hace nada.
                nueva = "Torneo " + m_llave.group(1)
                if nueva == llave:
                    continue
                llave, zona = nueva, ""
            elif pelada.startswith(("Zona ", "Zone ", "Group ", "Undecagonal")):
                # "Undecagonal Final" es una seccion de once equipos que el
                # Argentino A 2012-13 corre despues de las dos zonas. Sin
                # reconocerla, sus partidos se quedan sin seccion y no entran --
                # y son exactamente los 28 que Wikipedia publica sin fecha, o sea
                # los unicos que esta fuente tenia para aportar.
                # RSSSF escribe "Zona" en unas temporadas y "Zone" en otras -- el
                # Argentino A 2008-09 usa `Zone 1`, `Zone 2`, `Zone 3` --. Sin
                # reconocerlo, sus tres zonas no son encabezados de nada: la
                # temporada entera entra con cero partidos y sin ruido, que es
                # como fallo este modulo las cuatro veces anteriores.
                zona = pelada
            else:
                zona = ""
            ronda = fecha = None
            interzonal = pendiente = ""
            continue
        m = _RONDA.match(pelada)
        if m:
            ronda = int(m.group(1))
            fecha = (_MESES[m.group(2)], int(m.group(3))) if m.group(2) else None
            # El pendiente manda sobre la anotacion de la linea, y se consume:
            # vale para UNA ronda. Si sobreviviera, la ronda normal que viene
            # despues del bloque se saltearia bajo la segunda zona del par.
            interzonal = pendiente or _par_interzonal(m.group(4))
            pendiente = ""
            continue
        m = _SOLO_FECHA.match(pelada)
        if m:
            fecha = (_MESES[m.group(1)], int(m.group(2)))
            interzonal = _par_interzonal(m.group(3)) or interzonal
            continue
        if zona not in mapa or ronda is None or fecha is None:
            continue
        # Una ronda INTERZONAL pertenece a las dos zonas, y RSSSF la imprime dos
        # veces: una bajo el listado de cada una. Se lee bajo la PRIMERA del par y
        # se saltea bajo la segunda, o cada partido entra dos veces -- son 16 en el
        # Argentino A 2008-09, y con ellos 20 avisos graves.
        if interzonal and not zona.rstrip().endswith(interzonal.split("-")[0]):
            continue
        m = _PARTIDO.match(cruda)
        if not m:
            # Puede ser un partido cuyo marcador no es un marcador. Se decide con
            # la nota, y PASE LO QUE PASE se avisa: la unica forma de fallar que
            # este modulo tuvo siempre es callarse.
            m2 = _SIN_MARCADOR.match(cruda)
            if m2:
                loc, vis = m2.group(1).strip(), m2.group(3).strip()
                cl2, cv2 = mapa[zona].get(loc), mapa[zona].get(vis)
                # Y la COLA decide, que es lo que separa un partido de la prosa.
                # RSSSF siempre explica por que el marcador no es un marcador, asi
                # que despues del visitante o no hay nada -- la nota arranca en la
                # linea de abajo -- o hay una nota. Si lo que sigue son palabras,
                # la linea es prosa: "La Florida and Talleres (P) to overall
                # semifinals" tiene forma de partido y hasta dos clubes del mapa.
                cola = (m2.group(4) or "").lstrip()
                if cl2 and cv2 and (not cola or cola[0] in "[("):
                    nota = _anotacion(lineas, idx, m2.end(3))
                    marcador, estado, motivo = _leer_anotacion(nota)
                    donde = f"{llave} {zona} ronda {ronda}: {cl2} {m2.group(2)} {cv2}"
                    if marcador is None:
                        # No se puede decir todavia si el partido se PIERDE o si
                        # su continuacion entra unas lineas mas abajo: eso se
                        # sabe cuando esta leido todo. Ver `_los_que_se_pierden`.
                        caidos.append((f"{donde} NO entra -- {motivo}",
                                       ronda, llave, zona, cl2, cv2))
                    else:
                        raros.append(f"{donde} entra {marcador[0]}-{marcador[1]}"
                                     f"{' (' + estado + ')' if estado else ''}"
                                     f" por la nota: {nota}")
                        fuera.append(Ajeno(
                            fecha=_fecha_iso(*fecha, anio, anio_fin, mes_inicio),
                            jornada=ronda, local=cl2, visita=cv2,
                            goles_local=marcador[0], goles_visita=marcador[1],
                            llave=llave, zona=zona, status=estado))
            continue
        local, gl, gv = m.group(1).strip(), int(m.group(2)), int(m.group(3))
        visita = _sin_sede(m.group(4).strip())
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
    avisos += raros + _los_que_se_pierden(caidos, fuera)
    return fuera, avisos


def _los_que_se_pierden(caidos: list, fuera: list) -> list[str]:
    """Separa el partido que se recupera del que se pierde. No son lo mismo.

    Cuando la nota deja un partido afuera hay dos finales muy distintos, y desde
    la linea no se distinguen: puede ser que su CONTINUACION este unas lineas mas
    abajo -- RSSSF escribe el abandonado y despues la reanudacion, `[remaining
    32']` -- o puede ser que no haya nada mas y el partido no exista en ningun
    lado. Lo primero es el sistema funcionando; lo segundo es un agujero.

    Medido sobre el corpus: de tres, dos se recuperan. El que se pierde es el
    `Juv. Antoniana abd Gimnasia y Esgrima CdU` del Argentino A 2009-10,
    abandonado 1-1 a los 68' y nunca reanudado -- y la tabla que la propia RSSSF
    publica debajo lo confirma sin que haya que ir a buscar afuera: les da 3
    partidos jugados a esos dos clubes y 4 a los otros tres del grupo.

    Decirlo junto era mandar a revisar tres cosas cuando hay una sola.
    """
    dichos = []
    for texto, ronda, llave, zona, cl, cv in caidos:
        if not texto.endswith(_SIN_DESENLACE):
            dichos.append(texto)
            continue
        hay = any(a.jornada == ronda and a.llave == llave and a.zona == zona
                  and {a.local, a.visita} == {cl, cv} for a in fuera)
        dichos.append(f"{texto}; su continuacion si entra, unas lineas mas abajo"
                      if hay else
                      f"{texto}, Y NO HAY OTRA LINEA CON ESE PARTIDO: no se "
                      f"recupera de ningun lado y el dataset se queda sin el")
    return dichos



# --------------------------------------------------------------------------
# Las llaves: la fase que Wikipedia publica SOLO como cuadro
# --------------------------------------------------------------------------
# Un cuadro de eliminacion dibuja quien jugo contra quien y con que marcador, pero
# NO dice quien fue local. Se midio: la convencion "arriba es local en la ida"
# acierta 55.6% contra 761 patas donde la grilla si lo dice, o sea que escribir esas
# filas desde el cuadro seria inventarse la localia a la mitad.
#
# RSSSF la tiene. Publica las llaves en dos formatos distintos:
#
#   EXPANDIDO -- cada pata por separado, con su fecha exacta:
#       Quarterfinals
#       First Legs [Nov 23]
#       Sportivo Desamparados        2-0 Douglas Haig
#       Second Legs [Nov 27]
#       Douglas Haig                 2-0 Sportivo Desamparados
#
#   COMPACTO -- los dos marcadores en un renglon y la fecha como RANGO:
#       Quarterfinals
#       [Nov 20-28]
#       Aldosivi                 0-1 1-3 Luján de Cuyo
#
# Esta funcion lee SOLO el expandido, a proposito: el compacto no trae la fecha de
# cada pata y el repo no escribe una fila sin fecha. Un rango no es una fecha.
# `Third Phase` y `Fourth Phase` son rondas de eliminacion en el Argentino A
# 2011-12 y NO se confunden con las fases de liga: una fase de liga no trae
# encabezados de pata, asi que aunque el titulo entre, no se lee ningun partido.
# El titulo puede traerse la fecha puesta -- "Quarterfinals [Jun 4, one leg]" --,
# y cuando la trae es porque la ronda se juega A PARTIDO UNICO y no hay
# encabezados de ida y vuelta abajo. Tambien admite una cola descriptiva que
# empiece con un numero: "Promotion/Relegation Playoff 3rd/4th level
# Metropolitano". La cola NO es libre a proposito: con texto libre, "Final
# Table:" pasaria por "Final" y una tabla de posiciones entraria como una llave.
#
# Y ADMITE LA PALABRA "Reválida", que es la otra cola que existe. Se censaron las
# de los once archivos que el repo baja y son doce: cuarenta y seis `Table:`, diez
# `Tables:`, cuatro `Reválida` y ocho sueltas que describen niveles ("3rd/4th level
# Interior") o zonas. Las de `Table` son justo las que hay que dejar afuera, asi
# que la cola sigue siendo una lista cerrada y no un comodin.
#
# Sin ella, el `Third Phase Reválida` y el `Fourth Phase Reválida` del Argentino A
# 2012-13 no eran titulos de nada: sus dieciseis partidos no se leian, y en
# silencio, porque un titulo que no matchea no genera aviso -- simplemente no abre
# ninguna ronda y los renglones de abajo caen sin ronda abierta.
_LLAVE_TITULO = re.compile(
    r"^(?:Overall\s+)?(1/8\s+Finals|Quarterfinals|Semifinals|Final"
    r"|Second Round|Third Round|Third Phase|Fourth Phase"
    r"|Promotion/Relegation Playoff|Promotion Playoff|Relegation Playoff)"
    r"(?:\s+(?:\d[^\[\]]*|Reválida))?(?:\s*\[([^\]]*)\])?\s*$", re.I)
# "First Legs [Nov 23]", "First leg", "Second Legs". El plural es opcional porque
# RSSSF lo escribe de las dos formas.
#
# Y "Secoond leg" SE TOLERA, con el typo y todo: es como esta escrito el Third
# Phase del Argentino A 2011-12 en la fuente. Ignorarlo no dejaba esos cuatro
# partidos afuera, que seria lo de menos: los dejaba adentro con la pata
# ANTERIOR, o sea etiquetados como ida cuando son la vuelta. Un dato mal puesto
# es peor que un dato que falta.
# Y EL CORCHETE PUEDE SER UN PARENTESIS. Los archivos de 2007-08 escriben
# "Second Legs (Jun 28)" donde los demas escriben "Second Legs [Jun 28]". No
# reconocer la variante no perdia el encabezado y ya: lo dejaba pasar de largo,
# asi que la VUELTA se quedaba con la pata de la ida -- que es el mismo dato mal
# puesto que el typo "Secoond" -- y ademas con la fecha de la ida.
_LLAVE_PATA = re.compile(r"^(First|Second|Secoond)\s+Legs?\s*(?:[\[(]([^\])]+)[\])])?\s*$",
                         re.I)
# El renglon que trae SOLO la fecha, entre corchetes o entre parentesis: los
# archivos de 2007-08 usan "(Jun 21)" y los demas "[Jun 21]". Es la unica forma
# en que RSSSF fecha las patas de la promocion de la B Nacional 2007-08.
_LLAVE_FECHA = re.compile(r"^[\[(]\s*([A-Za-z]{3})\s+(\d{1,2})\s*[\])]$")
# Lo de adentro de un corchete puede traer mas que la fecha: "Jun 4, one leg".
# Se lee el mes y el dia del principio y se ignora el resto.
_LLAVE_DIA = re.compile(r"^\s*([A-Za-z]{3})\s+(\d{1,2})\b")


def _dia_de(corchete: str) -> tuple[int, int] | None:
    m = _LLAVE_DIA.match(corchete or "")
    if m and m.group(1).capitalize() in _MESES:
        return (_MESES[m.group(1).capitalize()], int(m.group(2)))
    return None
# "Sportivo Desamparados        2-0 Douglas Haig     [6-7 pen]". El separador entre
# el nombre y el marcador es de dos o mas espacios (o un tab, que RSSSF mezcla).
# El separador es UNO O MAS espacios, o un tab. Empezo pidiendo dos espacios --
# RSSSF alinea en columnas -- y eso perdia en SILENCIO los renglones donde el
# nombre llena la columna justo y el relleno queda en un solo espacio:
#
#     Juventud Unida Universitario 2-2 Independiente Rivadavia
#
# Era la vuelta de una llave del Argentino A 2005-06, y su falta se veia recien
# dos pasos mas adelante: el chequeo del cuadro comparaba la ida contra la
# vuelta que publica el dibujo y cantaba un desacuerdo que no existia.
#
# Aflojarlo no abre la puerta a las tablas de posiciones -- que traen cosas como
# `0  25- 6  43` y matchearian --, porque de eso no se ocupa el separador sino
# `_LLAVE_CIERRA`: una tabla cierra la ronda abierta y sin ronda no se lee nada.
_LLAVE_CRUCE = re.compile(
    r"^(.+?)(?:\t+|[ ]+)(\d+)\s*-\s*(\d+)(?:\t+|[ ]+)(.+?)(?:(?:\t+|[ ]{2,})\[(.+)\])?\s*$")
# ...y a veces el separador se come, porque el nombre trae la sede entre
# parentesis y el marcador queda pegado o a un solo espacio:
#
#     Gimnasia y Esgrima (CdU)1-1 Racing (Olavarria)
#     Gimnasia y Esgrima(CdU) 0-0 Central Norte (Salta)
#
# Se despega antes de mirar el renglon, que es mas barato que enseñarle el caso al
# regex. Vale SOLO despues de un parentesis: un espacio suelto en el medio de un
# nombre no alcanza para partirlo, y ahi esta la diferencia entre despegar y
# adivinar donde termina el nombre.
_LLAVE_PEGADO = re.compile(r"\)[ ]?(\d+\s*-\s*\d+)")

# Un encabezado de ronda de LIGA cierra la eliminacion abierta. Los renglones de
# una fecha de liga tienen exactamente el mismo formato que los de una llave, asi
# que sin esto una seccion de liga que viniera despues de una de eliminacion --
# hoy no pasa en ninguna pagina, pero depende del orden en que RSSSF las imprima --
# entraria entera como si fueran llaves.
_LLAVE_CIERRA = re.compile(r"^(Round\s+\d+|Table:|Aggregate Table:|Final Table:"
                           r"|First Phase|Second Phase|Topscorer.*)\s*$", re.I)
_LLAVE_PENALES = re.compile(r"(\d+)\s*-\s*(\d+)\s*pen", re.I)
_LLAVE_SEDE = re.compile(r"^at\s+(.+)$", re.I)


def _club(nombre: str, mapa: dict, zona: str, vistos: dict) -> tuple[str, str]:
    """El club canonico de un nombre corto de RSSSF, o ("", motivo).

    CARDINALIDAD, NO PARECIDO. Dentro de una zona el mapa manda y listo. Pero las
    rondas "Overall" mezclan las dos zonas, y ahi un nombre corto puede dejar de
    identificar a un club: en el Argentino A 2005-06 `Racing` es Racing (C) en una
    zona y Racing (O) en la otra -- es la UNICA ambiguedad del corpus, medida sobre
    los seis mapas.

    Cuando pasa, no se elige por parecido ni por el orden del mapa: se restringe a
    los clubes que YA JUGARON una llave de este mismo torneo, que son los que
    pudieron clasificar. Si queda exactamente uno, es ese. Si quedan dos, se
    devuelve el motivo y el partido no se escribe.
    """
    # UNA NOTA PARTIDA EN DOS RENGLONES ENSUCIA LOS DOS. RSSSF corta las notas
    # largas por ancho de columna, y el pedazo cae encima del renglon siguiente:
    #
    #     Douglas Haig     0-1 Juventud                [Douglas Haig on record
    #     Guillermo Brown  5-2 Independiente Rivadavia  regular season]
    #
    # Arriba queda un corchete que ABRE y no cierra; abajo, uno que CIERRA y no
    # abrio, pegado al nombre del visitante de un partido que no tiene nada que
    # ver. Se sacan los dos: sin esto son tres partidos que se pierden por un
    # problema de tipografia, no de datos.
    limpio = re.sub(r"\s*\[[^\]]*$", "", nombre)            # abre y no cierra
    limpio = re.sub(r"\s{2,}[^\[\]]*\]\s*$", "", limpio)     # cierra y no abrio
    corto = _sin_sede(limpio.strip())
    if zona in mapa and corto in mapa[zona]:
        return mapa[zona][corto], ""
    candidatos = {d[corto] for d in mapa.values() if corto in d}
    if not candidatos:
        return _por_el_padron(corto)
    if len(candidatos) == 1:
        return candidatos.pop(), ""
    achicado = candidatos & set(vistos)
    if len(achicado) == 1:
        return achicado.pop(), ""
    return "", (f"{corto!r} es ambiguo: {sorted(candidatos)}"
                + (f", y de esos ya jugaron {sorted(achicado)}" if achicado else
                   ", y ninguno jugo antes en este cuadro"))


def _por_el_padron(corto: str) -> tuple[str, str]:
    """El ultimo recurso cuando el mapa no lo tiene: preguntarle al padron.

    Existe por las secciones de PROMOCION, que son las unicas donde el mapa no
    puede ayudar: cruzan clubes de dos divisiones, asi que ni siquiera pertenecen
    al torneo de la pagina. RSSSF lo sabe y ahi escribe la ciudad entre
    parentesis -- `Rivadavia (Lincoln)`, `Racing (Olavarria)` -- porque el nombre
    corto ya no identifica. El padron entiende esos nombres: son ocho partidos
    del Argentino A 2005-06 que se perdian enteros.

    Y NO ES UN DICCIONARIO PARALELO, que es lo que este repo tiene prohibido. Es
    el padron, el mismo que ya normaliza todo lo demas.

    LA CIUDAD SE PELA SOLO SI EL NOMBRE PELADO TIENE UN SOLO DUENO. RSSSF escribe
    la ciudad aunque sea redundante -- `Real Arroyo Seco (Arroyo Seco)`,
    `General Paz Juniors (Cordoba)` -- y ahi hay que sacarla para que el padron lo
    reconozca. Pero pelar sin mirar seria un desastre: `Racing (Olavarria)` pelado
    da `Racing`, que el padron resuelve a Racing Club de Avellaneda, un club de
    Primera que no jugo nunca ese torneo. Ese caso se salva solo porque el nombre
    entero resuelve primero -- pero el que no resolviera entraria mal y en
    silencio, que es la unica forma en que este modulo hace dano.
    """
    from fad import equipos

    eq = equipos.buscar(corto)
    if eq is not None:
        return eq.nombre, ""
    pelado = re.sub(r"\s*\([^)]*\)\s*$", "", corto).strip()
    if pelado != corto and equipos.unico_dueno(pelado):
        eq = equipos.buscar(pelado)
        if eq is not None:
            return eq.nombre, ""
    return "", f"el mapa no traduce {corto!r} y el padron tampoco lo reconoce"


# --------------------------------------------------------------------------
# La foja que publica la propia fuente
# --------------------------------------------------------------------------
# El separador es UN espacio o mas, no dos. Un nombre que llena la columna --
# `Juventud Unida Universitario (San Luis)` -- deja uno solo, y al no matchear
# la fila no solo se pierde ella: cierra la tabla y se lleva las de abajo.
_FOJA = re.compile(r"^\s*\d+\.(?:.+?)\s+"
                   r"(\d+)\s+(\d+)\s+(\d+)\s+(\d+)\s+(\d+)-\s?(\d+)\s+\d+")


def leer_tabla(texto: str,
               mapa: dict[str, dict[str, str]]) -> list[tuple[str, list[tuple]]]:
    """[(zona, [(PJ, GF, GC, G, E, P)])] -- las tablas que publica la fuente.

    UNA ENTRADA POR TABLA Y NO POR ZONA, aunque dos tablas caigan bajo el mismo
    nombre. El Argentino A 2009-10 corre dos fases y las dos rotulan sus
    secciones `Zone 1`, `Zone 2`, `Zone 3`: son seis tablas y seis conjuntos de
    partidos distintos. Juntar por nombre las fusionaria de a pares y el cruce
    compararia un conjunto contra otro. Devueltas por separado, el que cruza
    puede exigir que la zona traiga UNA sola -- la misma cardinalidad que este
    repo le exige a cualquier emparejamiento -- y abstenerse cuando no.

    Es un TESTIGO DE NUESTRA PROPIA LECTURA, y sale gratis. Cuando los partidos
    de una pagina vienen de aca y su suma no cierra contra la tabla de Wikipedia,
    hay dos explicaciones muy distintas: los leimos mal, o las dos fuentes no
    coinciden. La tabla que la fuente publica al lado de sus propios partidos
    separa una de la otra sin traer nada de afuera.

    NO SE EMPAREJA NI UN NOMBRE. La tabla escribe `Deportivo Santamarina
    (Tandil)` donde la lista de partidos escribe `Dvo Santamarina`, y emparejar
    por parecido es justo lo que este repo no hace nunca. No hace falta: la foja
    de una zona es un CONJUNTO de filas, y comparar el conjunto entero contra el
    conjunto de nuestras sumas responde la pregunta igual. La zona de cada tabla
    se sabe por donde esta parada en el documento, que es un dato estructural.

    SOLO CUENTAN LAS TABLAS ROTULADAS `Final Table:`. El mapa tambien nombra las
    secciones de playoff -- `Group A`, `Group B` --, y esas traen su propia tabla
    de cuatro filas que cubre nada mas que el playoff. Sus clubes ya jugaron la
    zona, asi que cruzarla contra la suma de la temporada entera da cuatro filas
    contra cuatro filas y todas distintas: una alarma perfecta y perfectamente
    falsa. El rotulo lo escribe la fuente, y es lo unico que distingue una tabla
    que cubre lo que venimos sumando de una que no.
    """
    fuera: list[tuple[str, list[tuple]]] = []
    zona = ""
    abierta = False
    for linea in texto.split("\n"):
        pelada = linea.strip()
        if not pelada:
            continue
        if pelada.startswith("Final Table"):
            # El rotulo sobrevive la linea en blanco que lo separa de sus filas.
            abierta = True
            if zona in mapa:
                fuera.append((zona, []))
            continue
        if m := _FOJA.match(linea):
            if abierta and zona in mapa:
                pj, g, e, pp, gf, gc = (int(x) for x in m.groups())
                fuera[-1][1].append((pj, gf, gc, g, e, pp))
            continue
        if set(pelada) <= {"-", " "}:
            # La linea de guiones que la fuente dibuja para marcar el corte de
            # clasificacion NO cierra la tabla. Tratarla como si la cerrara no
            # pierde una fila: pierde TODAS LAS DE ABAJO, y en silencio. El
            # Argentino A 2009-10 lleva dos cortes en su primera tabla, asi que
            # sus ocho filas se leian como tres y la zona quedaba sin cruzar sin
            # que nada lo dijera.
            continue
        # Cualquier otra linea con texto cierra la tabla, y si ademas es un
        # encabezado de seccion cambia la zona.
        abierta = False
        if pelada in mapa:
            zona = pelada
        elif pelada.startswith(("Torneo ", "Zona ", "Zone ", "Group ", "Undecagonal",
                                "First Phase", "Second Phase", "Final", "Promoci",
                                "Champion", "Relegation")):
            zona = ""
    return [(z, f) for z, f in fuera if f]


def leer_llaves(texto: str, mapa: dict, anio: int, anio_fin: int,
                mes_inicio: int = 8, desde: str = "",
                hasta: str = "") -> tuple[list, list[str]]:
    """Los partidos de eliminacion, con su localia y su fecha de dia.

    Devuelve `Partido` y no `Ajeno` porque estas filas ENTRAN al dataset -- no
    estan para completarle la fecha a una fila de Wikipedia, que es para lo que
    existe `Ajeno` --. Y porque un `Ajeno` numera la jornada con un entero, y una
    ronda tiene nombre: "Quarterfinals", no 3.
    """
    from fad.parser import Partido

    # `desde` acota a una seccion, y hace falta cuando la temporada no tiene archivo
    # propio sino que vive dentro de la pagina del ano: ahi el mismo texto que abre
    # la seccion aparece ANTES en el indice y despues en las referencias cruzadas.
    # Se busca el ancla ENTERA, con lo que la sigue, para no quedarse con el indice
    # -- ese error ya se cometio dos veces en este repo con los titulos de Wikipedia.
    raros: list[str] = []
    if desde:
        i = texto.find(desde)
        if i < 0:
            return [], [f"no se encontro la seccion {desde.splitlines()[0]!r}"]
        texto = texto[i:]
    # Y ACOTA POR ABAJO, por el mismo motivo que `leer`: en la pagina del anio las
    # divisiones van una atras de otra y la fase final de una desemboca en la de la
    # siguiente. Sin el corte, la del Argentino A 2010-11 seguia de largo hasta la
    # Primera C y el Argentino B, y sus clubes -- `UAI-Urquiza`, `Dvo. Laferrere`,
    # `Dvo Roca` -- caian como nombres que el mapa no traduce. Trece avisos sobre
    # partidos que no son de este torneo.
    if hasta:
        j = texto.find(hasta)
        if j < 0:
            raros.append(f"no se encontro el final de la seccion "
                         f"{hasta.splitlines()[0]!r}; se leyo hasta el final del "
                         f"archivo y puede haber llaves de otro torneo")
        else:
            texto = texto[:j]

    fuera = []
    # (indice en `fuera`, penales del local, del visitante) de las tandas que no
    # se pueden decidir hasta tener las dos patas. Ver el comentario largo abajo.
    pendientes: list[tuple[int, int, int]] = []
    zona = llave = ronda = pata = ""
    fecha: tuple[int, int] | None = None
    vistos: dict[str, None] = {}
    for cruda in texto.split("\n"):
        linea = cruda.rstrip()
        pelada = linea.strip()
        if not pelada:
            continue
        if pelada.startswith("Torneo "):
            llave, zona, ronda, pata, fecha = pelada, "", "", "", None
            continue
        if pelada in mapa:
            zona, ronda, pata, fecha = pelada, "", "", None
            continue
        if _LLAVE_CIERRA.match(pelada):
            ronda, pata, fecha = "", "", None
            continue
        m = _LLAVE_TITULO.match(pelada)
        if m:
            # "Overall Semifinals" mezcla las dos zonas: se sale de la zona a
            # proposito, para que `_club` tenga que forzar la cardinalidad en vez
            # de resolver con un mapa que ya no corresponde.
            ronda = m.group(1).strip()
            if pelada.lower().startswith("overall"):
                zona = ""
            # Si el titulo trae la fecha, la ronda es a partido unico: no hay
            # encabezados de pata abajo y los partidos vienen enseguida.
            pata, fecha = "", _dia_de(m.group(2) or "")
            continue
        if not ronda:
            continue
        m = _LLAVE_PATA.match(pelada)
        if m:
            pata = "Second" if m.group(1).lower() == "secoond" else m.group(1).capitalize()
            fecha = None
            if m.group(2):
                fecha = _dia_de(m.group(2))
            continue
        m = _LLAVE_FECHA.match(pelada)
        if m and m.group(1).capitalize() in _MESES:
            fecha = (_MESES[m.group(1).capitalize()], int(m.group(2)))
            continue
        # UNA FILA DE LA TABLA NO ES UN PARTIDO, y tiene forma de partido: en
        # `4.Douglas Haig (Pergamino)  8  5  3  0  14-6  18` el patron de cruce lee
        # el `14-6` como marcador y parte el renglon en dos "clubes".
        #
        # ESTE GUARD YA ESTUVO Y SE SACO, y volver a ponerlo tiene su historia. La
        # primera vez se agrego por las dudas, y se lo saco al medirlo: con el y
        # sin el, el corpus daba los mismos partidos y los mismos avisos. Un
        # mutante que no se puede matar es codigo muerto con un comentario que
        # afirma un peligro que nadie midio.
        #
        # El peligro aparecio despues, al enchufar la fase final del Argentino A
        # 2010-11: su seccion termina en un `Final Tables:` con las tablas de las
        # tres zonas de la Revalida, y sus quince filas entraban al lector de
        # llaves. Ahora si se puede medir, y por eso vuelve.
        #
        # Se descarta con el mismo regex que lee la foja: es la definicion de una
        # fila de tabla y ya estaba escrita.
        if _FOJA.match(linea):
            continue
        m = _LLAVE_CRUCE.match(_LLAVE_PEGADO.sub(r")\t\1", linea))
        if not m:
            continue
        # La puerta es la FECHA, no la pata: una ronda a partido unico no tiene
        # pata, y pedirsela dejaba afuera los cuatro cuartos de final del Reducido
        # de la Primera C 2008-09, que se jugaron a un solo partido.
        if fecha is None:
            raros.append(f"{ronda}: {pelada[:60]} viene sin fecha; queda afuera")
            continue
        nota = m.group(5) or ""
        cl, porque1 = _club(m.group(1), mapa, zona, vistos)
        cv, porque2 = _club(m.group(4), mapa, zona, vistos)
        if not cl or not cv:
            raros.append(f"{ronda}: {porque1 or porque2}; el partido queda afuera")
            continue
        # LA TANDA ES DE LA SERIE, NO DEL PARTIDO. En una llave a doble partido se
        # patea cuando el GLOBAL queda igualado, y para eso la vuelta no tiene que
        # haber empatado: Racing (C) 2-1 San Martin (T) fue a penales porque la ida
        # habia sido 2-1 al reves. El dataset guarda los penales por PARTIDO, asi
        # que ponerlos en esa fila afirma que ese partido termino empatado y se
        # definio por penales, y es falso.
        #
        # Lo agarro el chequeo del propio repo -- "penales en un partido que no fue
        # empate" -- apenas se importo, y tenia razon. Se escriben solo cuando la
        # pata SI quedo igualada; si no, se avisa y la columna queda vacia, que es
        # lo que corresponde cuando el dato no tiene donde vivir.
        gl, gv = int(m.group(2)), int(m.group(3))
        pl = pv = None
        pen = _LLAVE_PENALES.search(nota)
        if pen and gl == gv:
            pl, pv = int(pen.group(1)), int(pen.group(2))
        elif pen:
            # LA VUELTA NO TIENE POR QUE HABER QUEDADO IGUALADA. La tanda es de la
            # SERIE y se patea al final del segundo partido, que perfectamente
            # puede terminar 1-0: la final del Argentino A 2005-06 fue General Paz
            # 1-0 Villa Mitre y despues Villa Mitre 1-0 General Paz, 1-1 global,
            # penales 9-8. La fuente cuelga la tanda de la pata donde se pateo, y
            # esta bien -- es lo mismo que hacen las plantillas de Wikipedia, y el
            # chequeo `penales_solo_en_empates` ya lo contempla desde que aparecio
            # en once partidos de una sola vez.
            #
            # Aca todavia no se puede decidir porque falta la otra pata, asi que se
            # anota y se resuelve al final, con la MISMA funcion que usa el chequeo
            # y no con una copia. Tenerla dos veces era tenerla distinta: este
            # lector exigia que la PATA hubiera quedado igualada, que es mas
            # estricto, y por eso venia tirando veintidos tandas que el chequeo
            # habria aceptado sin chistar.
            pendientes.append((len(fuera), int(pen.group(1)), int(pen.group(2))))
        fuera.append(Partido(
            fecha=_fecha_iso(*fecha, anio, anio_fin, mes_inicio),
            local=cl, visita=cv,
            goles_local=gl, goles_visita=gv,
            penales_local=pl, penales_visita=pv,
            fase="eliminacion",
            jornada=f"{ronda} - {pata} leg" if pata else ronda,
            llave=llave or ronda,
            fuente_fecha=CREDITO))
        vistos[cl] = vistos[cv] = None
        # `[at Quilmes]` dice que se jugo en cancha de un tercero. NO se marca
        # `neutral`: en este repo eso sale del REGLAMENTO de la competencia y no
        # del estadio, y una mudanza puntual de un partido de liga sigue siendo
        # `false` -- esta escrito en `dataset` y vale igual venga la fila de donde
        # venga. Tampoco va a `estadio`, porque RSSSF nombra al club anfitrion y no
        # a la cancha, y un club en la columna de estadio es un dato de otra cosa.
        # Se dice y ya: el hecho no se pierde y no se afirma de mas.
        if _LLAVE_SEDE.search(nota):
            raros.append(f"{ronda}: {cl} vs {cv} se jugo en cancha de "
                         f"{_LLAVE_SEDE.search(nota).group(1).strip()}; el dataset "
                         f"no lo distingue de un partido en casa")
    fuera, mas = _resolver_tandas(fuera, pendientes)
    return fuera, raros + mas


def _resolver_tandas(fuera: list, pendientes: list) -> tuple[list, list[str]]:
    """Escribe las tandas que la serie explica, y avisa las que no.

    Se hace al final y no al vuelo porque la pregunta necesita las DOS patas, y
    cuando se lee la segunda la primera ya esta en la lista. La responde
    `validar.serie_igualada`, que es la misma que audita el resultado: si la
    escribiera este modulo con su propio criterio, el lector y el chequeo podrian
    opinar distinto sobre la misma fila -- que es exactamente lo que pasaba.
    """
    from dataclasses import replace

    from fad import validar

    raros: list[str] = []
    for i, pl, pv in pendientes:
        p = fuera[i]
        if validar.serie_igualada(p, fuera):
            fuera[i] = replace(p, penales_local=pl, penales_visita=pv)
        else:
            raros.append(f"{p.jornada}: {p.local} {p.goles_local}-{p.goles_visita} "
                         f"{p.visita} define por penales {pl}-{pv}, pero su serie no "
                         f"quedo igualada y la tanda no tiene donde vivir; la "
                         f"columna queda vacia")
    return fuera, raros


# --------------------------------------------------------------------------
# El formato COMPACTO: las dos patas en un renglon y la fecha como rango
# --------------------------------------------------------------------------
# El archivo del Argentino A 2004-05 es el unico del corpus escrito asi:
#
#     Quarterfinals [Mar 27-Apr 3]
#     Guillermo Brown          1-0 1-3 Luján de Cuyo
#     La Florida               3-1 0-2 Unión de Sunchales  [2-3pen]
#
# Trae la localia -- el primero nombrado es local en la IDA y el segundo en la
# vuelta -- pero NO la fecha de cada pata: el corchete cubre las dos. Un rango no
# es una fecha, asi que estas filas salen SIN FECHA y terminan en `data/sin-fecha`.
# Es la carpeta que existe justo para esto: que falte la fecha no es lo mismo que
# no tener el partido.
#
# LOS DOS MARCADORES VAN DESDE LA PERSPECTIVA DEL PRIMERO. No es una suposicion:
# se verifico contra la progresion del propio torneo tres veces. En
# "Atlético Candelaria 2-2 2-1 Sp. Desamparados" (Semifinals Revalida), leyendo la
# vuelta como local-visitante pasaria Desamparados, y el que juega la final es
# Candelaria. Idem "General Paz Juniors 2-1 0-3 Luján de Cuyo", donde avanza Luján,
# y "Gimnasia y Tiro 4-0 2-6 Atlético Tucumán [2-4pen]", donde el global 6-6 y la
# tanda mandan a Tucuman, que es el que aparece en semifinales.
# El separador va de UNO o mas, por lo mismo que en `_LLAVE_CRUCE`: cuando el
# nombre llena la columna justo, el relleno queda en un solo espacio y el
# renglon se pierde en silencio. Era la llave `Juv. Unida Universitario 1-0
# 2-5 Aldosivi`, y su falta se veia recien dos pasos mas adelante, en el
# chequeo del cuadro, disfrazada de "la grilla no tiene ese partido".
_COMPACTO = re.compile(
    r"^(.+?)[ \t]+(\d+)-(\d+)[ \t]+(\d+)-(\d+)[ \t]+(.+?)"
    r"(?:[ \t]{2,}\[(.+?)\])?\s*$")
_COMPACTO_ZONA = re.compile(r"^(Zona\s+\w+.*)$")
_COMPACTO_RONDA = re.compile(
    r"^(Quarterfinals|Semifinals|Final|Round\s+\d+)\s*(?:\[.*\])?\s*$", re.I)


def leer_llaves_compacto(texto: str, mapa: dict) -> tuple[list, list[str]]:
    """Los partidos de las llaves de un archivo en formato compacto, SIN fecha.

    Devuelve dos filas por renglon -- la ida con el primero de local y la vuelta
    con el segundo --, y el marcador de la vuelta dado vuelta, porque en el
    original venia desde la perspectiva del primero.
    """
    from fad.parser import Partido

    fuera, raros = [], []
    llave = zona = ronda = ""
    for cruda in texto.split("\n"):
        linea = cruda.rstrip()
        pelada = linea.strip()
        if not pelada:
            continue
        if pelada.startswith("Torneo "):
            llave, zona, ronda = pelada, "", ""
            continue
        if _COMPACTO_ZONA.match(pelada):
            zona, ronda = pelada, ""
            continue
        m = _COMPACTO_RONDA.match(pelada)
        if m:
            ronda = m.group(1).strip()
            continue
        m = _COMPACTO.match(linea)
        if not m or not ronda:
            continue
        cl, porque1 = _club(m.group(1), mapa, "", {})
        cv, porque2 = _club(m.group(6), mapa, "", {})
        if not cl or not cv:
            raros.append(f"{ronda}: {porque1 or porque2}; la llave queda afuera")
            continue
        ida = (int(m.group(2)), int(m.group(3)))
        vuelta = (int(m.group(4)), int(m.group(5)))
        nota = m.group(7) or ""
        # La tanda es de la SERIE y se patea despues de la vuelta, asi que se
        # escribe si el GLOBAL quedo igualado -- no si la vuelta quedo igualada,
        # que es mas estricto y falso: una serie 1-0 y 1-0 termina 1-1 y va a
        # penales sin que ninguna de las dos patas haya empatado.
        #
        # Aca el global se calcula en el acto porque las dos patas vienen en la
        # misma linea, que es toda la diferencia con el formato expandido.
        pen = _LLAVE_PENALES.search(nota)
        pl = pv = None
        if pen and ida[0] + vuelta[0] == ida[1] + vuelta[1]:
            # la vuelta se juega en cancha del segundo, asi que la tanda tambien
            # va desde su perspectiva
            pl, pv = int(pen.group(2)), int(pen.group(1))
        elif pen:
            raros.append(f"{ronda}: {cl} vs {cv} define por penales "
                         f"{pen.group(1)}-{pen.group(2)}, pero su serie no quedo "
                         f"igualada y la tanda no tiene donde vivir; la columna "
                         f"queda vacia")
        # LA ZONA VA EN LA LLAVE, NO EN LA JORNADA. "Zona Campeonato" y "Zona
        # Revalida" son dos CUADROS distintos del mismo torneo, cada uno con su
        # final: metiendolas en la jornada, las dos finales quedaban en la misma
        # llave y el normalizador las colapsaba en una sola ronda -- que es peor
        # que no revisar, porque compara contra el conjunto equivocado. `llave` es
        # justamente "que cuadro de eliminacion", y esto es lo que quiere decir.
        #
        # Y va en la llave ADEMAS de en la jornada, no en vez de. `llave` no se
        # exporta: sacandola de la jornada, el CSV publicaba dos filas que dicen
        # "Final" sin forma de saber cual es la del Campeonato y cual la de la
        # Revalida. El chequeo necesita la llave y el que lee el dataset necesita
        # la jornada, y no cuesta nada dárselas a los dos.
        cuadro = f"{llave} - {zona}" if zona else llave
        jornada = f"{zona} - {ronda}" if zona else ronda
        fuera.append(Partido(local=cl, visita=cv,
                             goles_local=ida[0], goles_visita=ida[1],
                             fase="eliminacion", jornada=jornada, llave=cuadro,
                             fuente_fecha=CREDITO))
        fuera.append(Partido(local=cv, visita=cl,
                             goles_local=vuelta[1], goles_visita=vuelta[0],
                             penales_local=pl, penales_visita=pv,
                             fase="eliminacion", jornada=jornada, llave=cuadro,
                             fuente_fecha=CREDITO))
    return fuera, raros

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
            status=a.status,
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
        # TYPO DE LA FUENTE, tolerado a mano y no por parecido: en la vuelta
        # de la semifinal del Apertura RSSSF escribe "Villa Mitra". Sin esto
        # esa pata no entraba, y la falta se veia dos pasos mas adelante --
        # el chequeo del cuadro comparaba la ida contra la vuelta que publica
        # el dibujo y cantaba un desacuerdo que no existia.
        "Villa Mitra": "Villa Mitre",
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


# El Argentino A 2008-09. Forzado por cardinalidad contra las tablas de la pagina,
# igual que 2006-07, y con una sorpresa que la cardinalidad misma destapo: RSSSF
# rotula `Zone 1`, `Zone 2` y `Zone 3`, pero sus Zone 1 y 2 NO son las Zona 1 y 2
# de la pagina. Traen los MISMOS 16 clubes -- son dos etapas sobre un mismo grupo,
# y por eso su membresia es identica -- mientras que la pagina reparte esos 16 en
# dos zonas de 8. La Zone 3 si es la Zona 3, y balancea 9 contra 9.
#
# Con la correspondencia bien hecha la cuenta cierra sola: 16 contra 16 y 9 contra
# 9, ocho nombres coinciden exacto en el primer grupo y dos en el segundo, y cada
# sobrante tiene UN solo candidato posible:
#
#   "9 de Julio"              -> 9 de Julio (R)          el otro esta en la Zone 3
#   "Dvo Santamarina"         -> Ramón Santamarina
#   "Gimnasia y Esgrima (CU)" -> Gimnasia y Esgrima (CdU)  el (M) esta en la Zone 3
#   "Juventud"                -> Juventud (P)            Juventud Unida, en la 3
#   "Libertad" "Rivadavia" "Unión" -> (S) (L) (S)        uno solo de cada uno
#   "Sp. Desamparados" "Dvo Maipú" "Talleres" "Racing" "Alumni"
#   "Central Córdoba" "Juventud Unida Univ."             idem, uno solo de cada uno
#
# Ninguno se aparea por parecido: el que no queda forzado no entra.
ARGENTINO_A_2008: dict[str, dict[str, str]] = {
    "Zone 1": {
        "9 de Julio": "9 de Julio (R)",
        "Alvarado": "Alvarado",
        "Ben Hur": "Ben Hur",
        "Boca Unidos": "Boca Unidos",
        "Cipolletti": "Cipolletti",
        "Dvo Santamarina": "Ramón Santamarina",
        "Gimnasia y Esgrima (CU)": "Gimnasia y Esgrima (CdU)",
        "Guillermo Brown": "Guillermo Brown",
        "Huracán (TA)": "Huracán (TA)",
        "Juventud": "Juventud (P)",
        "Libertad": "Libertad (S)",
        "Patronato": "Patronato",
        "Real Arroyo Seco": "Real Arroyo Seco",
        "Rivadavia": "Rivadavia (L)",
        "Unión": "Unión (S)",
        "Villa Mitre": "Villa Mitre",
    },
    "Zone 2": {
        "9 de Julio": "9 de Julio (R)",
        "Alvarado": "Alvarado",
        "Ben Hur": "Ben Hur",
        "Boca Unidos": "Boca Unidos",
        "Cipolletti": "Cipolletti",
        "Dvo Santamarina": "Ramón Santamarina",
        "Gimnasia y Esgrima (CU)": "Gimnasia y Esgrima (CdU)",
        "Guillermo Brown": "Guillermo Brown",
        "Huracán (TA)": "Huracán (TA)",
        "Juventud": "Juventud (P)",
        "Libertad": "Libertad (S)",
        "Patronato": "Patronato",
        "Real Arroyo Seco": "Real Arroyo Seco",
        "Rivadavia": "Rivadavia (L)",
        "Unión": "Unión (S)",
        "Villa Mitre": "Villa Mitre",
    },
    "Zone 3": {
        "Alumni": "Alumni (VM)",
        "Central Córdoba": "Central Córdoba (SdE)",
        "Dvo Maipú": "Deportivo Maipú",
        "Gimnasia y Esgrima (M)": "Gimnasia y Esgrima (M)",
        "Juventud Antoniana": "Juventud Antoniana",
        "Juventud Unida Univ.": "Juventud Unida Universitario",
        "Racing": "Racing (C)",
        "Sp. Desamparados": "Desamparados",
        "Talleres": "Talleres (P)",
    },
}


# El Argentino A 2007-08. NO tiene la forma de 2008-09, aunque de lejos la imita:
# aca `Group A` es la Zona 1 de la pagina y `Group B` es la Zona 2, dos zonas de 8
# de verdad. Lo que confunde es que cada bloque nombra 16 clubes, y por eso la
# primera lectura fue que eran dos etapas sobre un plantel unico, como en 2008-09.
# No lo son, y lo dice la cuenta de partidos: 8 clubes todos contra todos, ida y
# vuelta, dos ruedas, son 112, y eso es exactamente lo que trae cada bloque en sus
# rondas normales -- 112 y 112 --, contra los 480 que tendria un grupo de 16. La
# Zona 3 son 9 clubes y 144.
#
# Los otros 8 nombres de cada bloque entran por el INTERZONAL, que RSSSF imprime
# bajo los dos grupos: 8 pares por 4 cruces = 32 partidos, escritos 64 veces. Por
# eso el mapa de `Group A` tiene que conocer igual a los clubes de la Zona 2 -- sus
# rivales interzonales --, y el de `Group B` a los de la Zona 1. De ahi que los dos
# dicts nombren los mismos 16 clubes sin ser el mismo grupo.
#
# La cuenta cierra sola: 112 + 112 + 32 + 144 = 400 partidos.
#
# Contra el plantel de la pagina emparejan solos 13 de 16 y 7 de 9. Los que
# faltaban no se aparearon por parecerse:
#
#   "Juv.Antoniana"    -> Juventud Antoniana   la Zona 1 tiene 8, siete ya ocupados
#   "Dep. Santamarina" -> Ramón Santamarina    la Zona 3 tiene 9, ocho ya ocupados
#   "Gimnasia y Esgr. (CdU)" y "Talleres" no son clubes que falten sino SEGUNDAS
#     GRAFIAS de dos que ya estaban. La prueba es del torneo, no del texto: en una
#     zona todos se enfrentan con todos, y ninguna de las dos grafias cortas juega
#     nunca contra su larga ni aporta un solo rival que la larga no tenga. La corta
#     de Gimnasia aparece en 2 partidos de 34; "Talleres" en 1 de 36, contra Lujan
#     de Cuyo, que es de su misma zona. Y las dos cierran los PJ: 31 + 1 = 32, que
#     es lo que la tabla final del propio RSSSF le da a Talleres (Perico).
#   "Alumni" -> Alumni (VM)                  recien una vez colapsada la de Gimnasia
#     queda un solo nombre libre en la Zona 2 y un solo club sin duenio.
#
# Las cuatro las confirma ademas la TABLA FINAL de RSSSF, que ahi si escribe los
# nombres enteros -- "Alumni (Villa Maria) ... (Cordoba)", "Talleres (Perico) ...
# (Jujuy)", "Deportivo Santamarina (Tandil)", "Juventud Antoniana (Salta)" -- y da
# fojas que coinciden digito por digito con las sumadas sobre la grilla.
#
# `Talleres` pelado se traduce ACA y no en el padron a proposito: global, "Talleres"
# es el de Cordoba, que ademas JUEGA en este mismo documento -- el playoff de
# promocion contra Racing (C) --, asi que un alias global le daria a Perico partidos
# de un club que esta en la misma pagina.
ARGENTINO_A_2007: dict[str, dict[str, str]] = {
    # Los mismos 16 clubes bajo los dos rotulos: son dos etapas, no dos zonas.
    "Group A": {
        "9 De Julio (R)": "9 de Julio (R)",
        "Alumni": "Alumni (VM)",
        "Atl. Tucuman": "Atlético Tucumán",
        "Boca Unidos": "Boca Unidos",
        "Gimnasia y Esgr. (CdU)": "Gimnasia y Esgrima (CdU)",
        "Gimnasia y Esgrima (CdU)": "Gimnasia y Esgrima (CdU)",
        "Gimnasia y Esgrima (M)": "Gimnasia y Esgrima (M)",
        "Juv.Antoniana": "Juventud Antoniana",
        "Juventud U. U.": "Juventud Unida Universitario",
        "La Florida": "La Florida",
        "Libertad": "Libertad (S)",
        "Lujan de Cuyo": "Luján de Cuyo",
        "Racing (C)": "Racing (C)",
        "Sp. Desamparados": "Desamparados",
        "Sp. Patria": "Sportivo Patria",
        "Talleres": "Talleres (P)",
        "Talleres (P)": "Talleres (P)",
        "Unión (S)": "Unión (S)",
    },
    "Group B": {
        "9 De Julio (R)": "9 de Julio (R)",
        "Alumni": "Alumni (VM)",
        "Atl. Tucuman": "Atlético Tucumán",
        "Boca Unidos": "Boca Unidos",
        "Gimnasia y Esgr. (CdU)": "Gimnasia y Esgrima (CdU)",
        "Gimnasia y Esgrima (CdU)": "Gimnasia y Esgrima (CdU)",
        "Gimnasia y Esgrima (M)": "Gimnasia y Esgrima (M)",
        "Juv.Antoniana": "Juventud Antoniana",
        "Juventud U. U.": "Juventud Unida Universitario",
        "La Florida": "La Florida",
        "Libertad": "Libertad (S)",
        "Lujan de Cuyo": "Luján de Cuyo",
        "Racing (C)": "Racing (C)",
        "Sp. Desamparados": "Desamparados",
        "Sp. Patria": "Sportivo Patria",
        "Talleres": "Talleres (P)",
        "Talleres (P)": "Talleres (P)",
        "Unión (S)": "Unión (S)",
    },
    "Group C": {
        "Cipolletti": "Cipolletti",
        "Dep. Santamarina": "Ramón Santamarina",
        "Guillermo Brown": "Guillermo Brown",
        "Huracan (TA)": "Huracán (TA)",
        "Juventud (P)": "Juventud (P)",
        "La Plata FC": "La Plata FC",
        "Real Arroyo Seco": "Real Arroyo Seco",
        "Rivadavia (L)": "Rivadavia (L)",
        "Villa Mitre": "Villa Mitre",
    },
}

# QUE TEMPORADAS PUBLICA RSSSF, Y CON QUE NOMBRE DE ARCHIVO
# ---------------------------------------------------------
# Buscar `arg3-int10` para 2009-10 da 404, y la conclusion facil -- "no la
# publican" -- es falsa. Lo que cambio es la convencion del NOMBRE: dos digitos
# hasta 2008-09 y cuatro desde 2009-10.
#
#   arg3-int05 .. arg3-int09   2004-05 .. 2008-09
#   arg3-int2010               2009-10
#   arg3-int2013               2012-13
#
# 2010-11 y 2011-12 no tienen archivo de partidos: el resumen anual (`arg2011`,
# `arg2012`) trae sus TABLAS finales y nada mas. No hace falta: 2010-11 ya entra
# por Wikipedia, que si publica la grilla.
#
# El camino para encontrarlos no fue adivinar nombres sino dejar que la fuente lo
# dijera: cada archivo enlaza al de la temporada anterior y al de la siguiente, y
# `arg3-int09` apunta derecho a `arg3-int2010.html`. Vale para la proxima vez.


# El Argentino A 2009-10. Dos torneos en un archivo -- Apertura y Clausura -- y la
# novedad de la temporada: LOS CLUBES SE REPARTEN DISTINTO EN CADA UNO. La Zone 1
# del Apertura no tiene el mismo plantel que la Zone 1 del Clausura, asi que el
# forzado se hizo por (torneo, zona) y recien despues se unio por rotulo, que es la
# clave que usa `leer`. Al unir se verifico que ningun nombre apunte a dos clubes:
# ninguno lo hace.
#
# Zone 1 y Zone 2 son de 8 clubes -- 14 fechas intrazonales mas 2 rondas
# `Round N - Interzonal 1-2`, que son de 8 partidos porque cruzan las dos zonas
# enteras -- y por eso sus dos mapas terminan siendo el mismo: cada bloque tiene que
# poder traducir a los 16. Zone 3 es de 9 y no tiene interzonal.
#
# LA PRUEBA ES LA FOJA, y esta fuente la regala: cada zona termina en un bloque
# `Final Table:` que escribe los clubes ENTEROS y con la ciudad -- "Rivadavia
# (Lincoln)", "Atletico Union (Mar del Plata)", "Deportivo Santamarina (Tandil)" --
# junto a PJ, G, E, P y GF-GC. Asi que cada nombre corto se cierra sumando sus
# partidos y buscando la fila que coincida en las seis cifras. Cerraron las diez
# secciones y los 25 clubes, sin un solo ambiguo.
#
# Las tres grafias dobles salieron de la misma prueba, no del parecido: "Dvo.
# Santamarina" da 15 partidos y "Dvo Santamarina" 1, y ninguna cierra sola; juntas
# dan exacto el 16 6-5-5 15-16 de su fila. Y no se enfrentan nunca, que en una zona
# de todos contra todos es imposible entre dos clubes. Idem "Svo. Belgrano" (15+1) y
# "Svo. Desamparados".
#
# OJO, ACA "Talleres" ES EL DE CORDOBA y no el de Perico como en 2007-08 y 2008-09.
# No es una regresion: en todo el documento no hay una sola mencion de Perico ni de
# Jujuy, las tres tablas finales dicen "Talleres (Cordoba)" y la pagina lo enlaza a
# [[Club Atletico Talleres (Cordoba)]]. Perico no jugo esta temporada. Es justamente
# la razon por la que el mapa es por temporada y no un alias del padron.
#
# Lo mismo con los otros pelados, que el padron resuelve al club de PRIMERA y que
# aca son del ascenso: "Huracan" es el de Tres Arroyos y no el de Parque Patricios,
# "Estudiantes" el de Rio Cuarto y no el de La Plata, "Racing" el de Cordoba y no el
# de Avellaneda, "Union-S" el de Sunchales y no el de Santa Fe.
#
# NO se mapean las secciones de semifinales, final y promocion, igual que en las
# temporadas anteriores: los playoffs mezclan zonas. Queda anotado que ahi RSSSF
# escribe "Union" SIN TILDE -- un string distinto de "Union" con tilde --, y que esa
# cadena hoy resuelve a Union de Santa Fe. Si algun dia se mapea ese bloque, es
# Union (S), de Sunchales: lo fuerzan el NB del Apertura y la seccion Semifinales de
# la pagina, con los mismos 2-1, 3-2 y los penales 2:4.
ARGENTINO_A_2009: dict[str, dict[str, str]] = {
    "Group A": {
        "Crucero del Norte": "Crucero del Norte",
        "Dvo Santamarina": "Ramón Santamarina",
        "Estudiantes": "Estudiantes (RC)",
        "Huracán": "Huracán (TA)",
        "Juv. Antoniana": "Juventud Antoniana",
        "Libertad": "Libertad (S)",
        "Patronato": "Patronato",
        "Svo Desamparados": "Desamparados",
        "Talleres": "Talleres (C)",
        "Unión": "Unión (S)",
    },
    "Group B": {
        "Central Córdoba": "Central Córdoba (SdE)",
        "Cipolletti": "Cipolletti",
        "Crucero del Norte": "Crucero del Norte",
        "Dvo Maipú": "Deportivo Maipú",
        "Gimnasia y Esgrima CdU": "Gimnasia y Esgrima (CdU)",
        "Guillermo Brown": "Guillermo Brown",
        "Huracán": "Huracán (TA)",
        "Juv. Antoniana": "Juventud Antoniana",
        "Patronato": "Patronato",
        "Rivadavia": "Rivadavia (L)",
    },
    "Zone 1": {
        "9 de Julio": "9 de Julio (R)",
        "Ben Hur": "Ben Hur",
        "Central Córdoba": "Central Córdoba (SdE)",
        "Cipolletti": "Cipolletti",
        "Crucero del Norte": "Crucero del Norte",
        "Dvo Santamarina": "Ramón Santamarina",
        "Dvo. Santamarina": "Ramón Santamarina",
        "Gimnasia y Esgrima CdU": "Gimnasia y Esgrima (CdU)",
        "Guillermo Brown": "Guillermo Brown",
        "Huracán": "Huracán (TA)",
        "Juv. Antoniana": "Juventud Antoniana",
        "Juventud": "Juventud (P)",
        "Libertad": "Libertad (S)",
        "Patronato": "Patronato",
        "Racing": "Racing (C)",
        "Rivadavia": "Rivadavia (L)",
        "Svo Belgrano": "Sportivo Belgrano",
        "Svo. Belgrano": "Sportivo Belgrano",
        "Talleres": "Talleres (C)",
        "Unión-MdP": "Unión (MdP)",
        "Unión-S": "Unión (S)",
        "Villa Mitre": "Villa Mitre",
    },
    "Zone 2": {
        "9 de Julio": "9 de Julio (R)",
        "Ben Hur": "Ben Hur",
        "Central Córdoba": "Central Córdoba (SdE)",
        "Cipolletti": "Cipolletti",
        "Crucero del Norte": "Crucero del Norte",
        "Dvo Santamarina": "Ramón Santamarina",
        "Dvo. Santamarina": "Ramón Santamarina",
        "Gimnasia y Esgrima CdU": "Gimnasia y Esgrima (CdU)",
        "Guillermo Brown": "Guillermo Brown",
        "Huracán": "Huracán (TA)",
        "Juv. Antoniana": "Juventud Antoniana",
        "Juventud": "Juventud (P)",
        "Libertad": "Libertad (S)",
        "Patronato": "Patronato",
        "Racing": "Racing (C)",
        "Rivadavia": "Rivadavia (L)",
        "Svo Belgrano": "Sportivo Belgrano",
        "Svo. Belgrano": "Sportivo Belgrano",
        "Talleres": "Talleres (C)",
        "Unión-MdP": "Unión (MdP)",
        "Unión-S": "Unión (S)",
        "Villa Mitre": "Villa Mitre",
    },
    "Zone 3": {
        "Alumni": "Alumni (VM)",
        "Central Córdoba": "Central Córdoba (SdE)",
        "Cipolletti": "Cipolletti",
        "Dvo Maipú": "Deportivo Maipú",
        "Estudiantes": "Estudiantes (RC)",
        "Guillermo Brown": "Guillermo Brown",
        "Huracán": "Huracán (TA)",
        "Juv. Antoniana": "Juventud Antoniana",
        "Juventud Unida Univ.": "Juventud Unida Universitario",
        "Racing": "Racing (C)",
        "Svo Desamparados": "Desamparados",
        "Svo. Desamparados": "Desamparados",
        "Talleres": "Talleres (C)",
        "Villa Mitre": "Villa Mitre",
    },
}


# El Argentino A 2012-13. La mas facil de las cinco, y por una razon que conviene
# anotar: esta fuente escribe LA CIUDAD al lado del club -- "Racing (Olavarria)",
# "Central Cordoba (Sgo.del Estero)", "Union (Mar del Plata)" --, asi que los
# nombres se desambiguan solos y el padron resuelve casi todos sin ayuda. Es lo
# contrario de 2007-08, donde el mismo club era "Talleres" a secas.
#
# Lo que queda no son homonimos sino ABREVIATURAS, y el mismo club aparece hasta
# de tres formas: "Alvarado (Mar d Plata)", "Alvarado (Mar del Plata)" y
# "Alvarado (MdP)". Las tres van al mapa apuntando al mismo canonico. Las unicas
# que el padron no reconocia de ninguna manera son "Guarani A.Franco",
# "Juv.Unida Univ." y "Gimnasia y Esgrima (Cd Uruguay)", y las cierra la propia
# `Table:` del archivo, que arriba de cada zona escribe el nombre entero con la
# ciudad: en la temporada hay un solo club de cada uno.
#
# Van en el mapa y no en el padron por la regla de siempre: son grafias de ESTA
# fuente en ESTA temporada, y un alias global las suelta sobre todas las demas.
ARGENTINO_A_2012: dict[str, dict[str, str]] = {
    "Undecagonal Final": {
        "Deportivo Maipú (Mza)": "Deportivo Maipú",
        "Gimnasia y Esgrima (CdU)": "Gimnasia y Esgrima (CdU)",
        "Gimnasia y Esgrima(CdU)": "Gimnasia y Esgrima (CdU)",
        "Gimnasia y Tiro (S)": "Gimnasia y Tiro (S)",
        "Juv.Unida Univ. (SL)": "Juventud Unida Universitario",
        "Juventud Antoniana (S)": "Juventud Antoniana",
        "Racing (Olavarría)": "Racing (O)",
        "Ramón Santamarina (T)": "Ramón Santamarina",
        "San Jorge (Tucumán)": "San Jorge (T)",
        "San Martín (Tucumán)": "San Martín (T)",
        "Sp.Belgrano (S.Fco)": "Sportivo Belgrano",
        "Talleres (Córdoba)": "Talleres (C)",
    },
    "Zona Norte": {
        "Alumni (Villa María)": "Alumni (VM)",
        "Central Córdoba (SdE)": "Central Córdoba (SdE)",
        "Central Norte (Salta)": "Central Norte (S)",
        "Gimnasia y Tiro (Salta)": "Gimnasia y Tiro (S)",
        "Guaraní A.Franco (P)": "Guaraní Antonio Franco",
        "Juventud Antoniana (S)": "Juventud Antoniana",
        "Libertad (Sunchales)": "Libertad (S)",
        "Racing (Córdoba)": "Racing (C)",
        "San Jorge (Tucumán)": "San Jorge (T)",
        "San Martín (Tucumán)": "San Martín (T)",
        "Sp.Belgrano (S.Fco)": "Sportivo Belgrano",
        "Talleres (Córdoba)": "Talleres (C)",
        "Tiro Federal (Ros)": "Tiro Federal",
    },
    "Zona Sur": {
        "Alvarado (Mar d Plata)": "Alvarado",
        "Alvarado (Mar del Plata)": "Alvarado",
        "Alvarado (MdP)": "Alvarado",
        "Central Córdoba (SdE)": "Central Córdoba (SdE)",
        "Central Córdoba (Sgo.del Estero)": "Central Córdoba (SdE)",
        "Cipolletti (Río Negro)": "Cipolletti",
        "Def.de Belgrano (VR)": "Defensores de Belgrano (VR)",
        "Defensores de Belgrano (Villa Ramallo)": "Defensores de Belgrano (VR)",
        "Deportivo Maipú (Mendoza)": "Deportivo Maipú",
        "Deportivo Maipú (Mza)": "Deportivo Maipú",
        "Gimnasia y Esgrima (CdU)": "Gimnasia y Esgrima (CdU)",
        "Gimnasia y Esgrima (Concepción del Uruguay)": "Gimnasia y Esgrima (CdU)",
        "Gimnasia y Esgrima(CdU)": "Gimnasia y Esgrima (CdU)",
        "Gimnasia y Tiro (Salta)": "Gimnasia y Tiro (S)",
        "Guaraní A.Franco (P)": "Guaraní Antonio Franco",
        "Guaraní A.Franco (Posadas)": "Guaraní Antonio Franco",
        "Guillermo Brown (PM)": "Guillermo Brown",
        "Juv.Unida Univ. (SL)": "Juventud Unida Universitario",
        "Juventud Antoniana (S)": "Juventud Antoniana",
        "Juventud Antoniana (Salta)": "Juventud Antoniana",
        "Juventud Unida Universitario (San Luis)": "Juventud Unida Universitario",
        "Libertad (Sunchales)": "Libertad (S)",
        "Racing (Olavarría)": "Racing (O)",
        "Ramón Santamarina (T)": "Ramón Santamarina",
        "Ramón Santamarina (Tandil)": "Ramón Santamarina",
        "Rivadavia (Lincoln)": "Rivadavia (L)",
        "San Jorge (Tucumán)": "San Jorge (T)",
        "San Martín (Tucumán)": "San Martín (T)",
        "Sp.Desamparados (SJ)": "Desamparados",
        "Sportivo Belgrano (SF)": "Sportivo Belgrano",
        "Sportivo Belgrano (San Francisco)": "Sportivo Belgrano",
        "Tiro Federal (Rosario)": "Tiro Federal",
        "Unión (Mar del Plata)": "Unión (MdP)",
        "Unión (MdP)": "Unión (MdP)",
    },
}

# El Argentino A 2011-12 no tiene archivo propio: vive dentro de `arg2012`, y sus
# llaves traen la ciudad pegada al nombre. Eso resuelve la ambiguedad que en
# 2005-06 habia que forzar -- aca `Racing (Cordoba)` y `Racing (Olavarria)` se
# distinguen solos -- pero crea otra: el MISMO club se escribe distinto entre la
# ida y la vuelta, porque RSSSF abrevia para que entre en la columna.
#
#     Sportivo Belgrano (San Francisco)  /  Sp.Belgrano (S.Fco)
#     Juventud Unida Universitario (San Luis)  /  Juv.Unida Univ. (SL)
#     Crucero del Norte (Misiones)  /  Crucero del Norte (M)
#     Ramon Santamarina (Tandil)  /  Ramon Santamarina (T)
#
# Por eso van las dos formas: son 30 nombres para 24 clubes. Resolverlos por el
# padron NO alcanza -- se midio, y once de los treinta vuelven sin traducir --, y
# ahi es donde un nombre corto termina siendo el club equivocado.
ARGENTINO_A_2011 = {
    "Llaves": {
        "Alumni (Villa María)": "Alumni (VM)",
        "CAI (Comodoro Rivadavia)": "CAI",
        "Central Córdoba (Santiago del Estero)": "Central Córdoba (SdE)",
        "Central Córdoba (SdE)": "Central Córdoba (SdE)",
        "Central Norte (Salta)": "Central Norte (S)",
        "Cipolletti (Río Negro)": "Cipolletti",
        "Crucero del Norte (M)": "Crucero del Norte",
        "Crucero del Norte (Misiones)": "Crucero del Norte",
        "Def.de Belgrano (VR)": "Defensores de Belgrano (VR)",
        "Deportivo Roca (RN)": "Deportivo Roca",
        "Gimnasia y Esgrima (Concepción del Uruguay)": "Gimnasia y Esgrima (CdU)",
        # sin el espacio antes del parentesis, tal cual lo escribe la fuente. El
        # mapa de 2012-13 ya traia esta misma variante: la rareza no es nueva.
        "Gimnasia y Esgrima(CdU)": "Gimnasia y Esgrima (CdU)",
        "Gimnasia y Tiro (Salta)": "Gimnasia y Tiro (S)",
        "Guillermo Brown (PM)": "Guillermo Brown",
        "Guillermo Brown (Puerto Madryn)": "Guillermo Brown",
        "Juv.Unida Univ. (SL)": "Juventud Unida Universitario",
        "Juventud Antoniana (S)": "Juventud Antoniana",
        "Juventud Antoniana (Salta)": "Juventud Antoniana",
        "Juventud Unida Universitario (San Luis)": "Juventud Unida Universitario",
        "Libertad (Sunchales)": "Libertad (S)",
        "Racing (Córdoba)": "Racing (C)",
        "Racing (Olavarría)": "Racing (O)",
        "Ramón Santamarina (T)": "Ramón Santamarina",
        "Ramón Santamarina (Tandil)": "Ramón Santamarina",
        "Rivadavia (Lincoln)": "Rivadavia (L)",
        "San Jorge (Tucumán)": "San Jorge (T)",
        "San Martín (Tucumán)": "San Martín (T)",
        "Sp.Belgrano (S.Fco)": "Sportivo Belgrano",
        "Sportivo Belgrano (San Francisco)": "Sportivo Belgrano",
        "Talleres (Córdoba)": "Talleres (C)",
        "Unión (Mar del Plata)": "Unión (MdP)",
    }
}

# El ancla de la seccion, para las temporadas que viven dentro de la pagina del
# ano. Va con lo que la SIGUE y no sola: "Torneo Argentino A" aparece seis veces en
# `arg2012` -- una en el indice de arriba, otra en la seccion de verdad y cuatro en
# referencias cruzadas del final -- y quedarse con la primera da un texto que no
# tiene ninguna llave.
SECCION: dict[str, tuple[str, str]] = {
    # Tres lineas y no una: `Promotion Playoff` a secas aparece dos veces en
    # `arg2011`, una por el Argentino A y otra por la Primera D. Y el corte de
    # abajo hace falta porque la fase final de una division desemboca en la de la
    # siguiente sin nada que las separe.
    "Torneo Argentino A 2010-11": ("Promotion Playoff\n\nFirst Legs [May 18]",
                                   'Primera C Metropolitano "Efectivo Sí"'),
    "Torneo Argentino A 2011-12": ("Torneo Argentino A\n\n\nFirst Phase", ""),
    # `Promotion/Relegation Playoff` a secas aparece dos veces en `arg2-08` -- una
    # es el titulo de la seccion y la otra el encabezado de una tabla anterior --,
    # asi que el corte de arriba lleva pegado el `First Legs` que la abre de
    # verdad. El de abajo es la nota al pie de la propia seccion.
    "Campeonato de Primera B Nacional 2007-08": (
        "Promotion/Relegation Playoff\n \nFirst Legs",
        "NB: Nueva Chicago relegated"),
}

# El Reducido de la Primera C 2008-09. Es OTRA division y otro archivo: `arg4-09`,
# "Argentina Fourth Level (Primera C - Metropolitana) 2008/09". Cuidado con
# `arg4-int09`, que es el cuarto nivel del INTERIOR -- el Argentino B -- y es el
# error facil de cometer.
#
# Nueve nombres para nueve clubes: aca RSSSF no cambia de forma entre patas. Pero
# tres de los nueve el padron no los resuelve solo (`Dvo Laferrere`,
# `Gral. Lamadrid`, `L.N. Alem`), asi que el mapa va igual y va entero: media
# traduccion es la que despues mete el club de al lado.
PRIMERA_C_2008 = {
    # LA FASE REGULAR NO LLEVA ENCABEZADO DE ZONA, y la clave vacia es eso: este
    # torneo no tiene zonas. Son veinte clubes y 38 fechas seguidas, y RSSSF las
    # escribe una atras de otra despues de la tabla final, sin nada que las
    # anuncie. `leer` solo lee las secciones que el mapa nombra, asi que sin esta
    # clave devolvia CERO partidos -- sin un aviso, que es como este modulo falla
    # siempre-- y los 380 de la temporada se quedaban sin poder fechar a nadie.
    #
    # Se noto por el otro lado: catorce filas de la pagina entraban sin fecha y
    # el aviso decia "380 partidos sin pareja en la otra fuente". Trescientos
    # ochenta es la temporada entera; que no emparejara NINGUNO era el sintoma.
    #
    # Con la clave puesta lee los 380, los 380 con fecha, 38 jornadas de diez
    # partidos, sin un par repetido y sin un aviso: el todos-contra-todos ida y
    # vuelta de veinte clubes, exacto. Los playoffs no se cuelan porque no
    # numeran sus rondas como `Round N`.
    "": {
        "Argentino (M)": "Argentino de Merlo",
        "Argentino (R)": "Argentino de Rosario",
        "Barracas Bolívar": "Barracas Bolívar",
        "Barracas Central": "Barracas Central",
        "Berazategui": "Berazategui",
        "Cañuelas": "Cañuelas",
        # las cuatro que el padron no reconoce abreviadas. Ninguna es ambigua:
        # los veinte clubes de esta Primera C estan en el padron y ninguna otra
        # abreviatura del corpus colisiona con estas.
        "Def. de Cambaceres": "Defensores de Cambaceres",
        "Defensores Unidos": "Defensores Unidos",
        "Dvo Laferrere": "Deportivo Laferrere",
        "El Porvenir": "El Porvenir",
        "Excursionistas": "Excursionistas",
        "Fénix": "Fénix",
        "Gral. Lamadrid": "General Lamadrid",
        "J.J. de Urquiza": "J. J. de Urquiza",
        "L.N. Alem": "Leandro N. Alem",
        "Luján": "Luján",
        "Sacachispas": "Sacachispas",
        "San Miguel": "San Miguel",
        "Villa Dálmine": "Villa Dálmine",
        "Villa San Carlos": "Villa San Carlos",
    },
    "Reducido": {
        "Argentino (R)": "Argentino de Rosario",
        "Berazategui": "Berazategui",
        "Defensores Unidos": "Defensores Unidos",
        "Dvo Laferrere": "Deportivo Laferrere",
        # de la otra promocion de la misma pagina, la de Primera C - Primera D:
        # entran para que se crucen contra la grilla, que ya los tiene
        "Dvo Riestra": "Deportivo Riestra",
        "Excursionistas": "Excursionistas",
        "Gral. Lamadrid": "General Lamadrid",
        "J.J. de Urquiza": "J. J. de Urquiza",
        "L.N. Alem": "Leandro N. Alem",
        "San Telmo": "San Telmo",
        "Villa Dálmine": "Villa Dálmine",
    }
}

# El Torneo Argentino A 2004-05. Su archivo es el UNICO del corpus escrito entero
# en el formato COMPACTO -- las dos patas en un renglon y la fecha como rango --,
# asi que sus filas entran sin fecha. Ver `leer_llaves_compacto`.
#
# Doce de los veintiocho nombres el padron no los resuelve solo, y tres de esos
# doce ni siquiera son nombres: son restos de una nota partida en dos renglones
# ("Ben Hur             [2nd leg abd at 0-3 in 85',"), que `_club` limpia antes de
# buscar. Los otros nueve van en el mapa.
ARGENTINO_A_2004 = {
    "Llaves": {
        "Atl. Ñuñorco": "Ñuñorco",
        "Atlético Ñuñorco": "Ñuñorco",
        "Gimnasia y Esgrima-CdU": "Gimnasia y Esgrima (CdU)",
        "Indep. Rivadavia": "Independiente Rivadavia",
        "Indepte. Rivadavia": "Independiente Rivadavia",
        "JU Universitario": "Juventud Unida Universitario",
        "Juv. Unida Universitario": "Juventud Unida Universitario",
        "Juventud (Pergamino)": "Juventud (P)",
        "Racing-CBA": "Racing (C)",
        "Unión de Sunchales": "Unión (S)",
        # los que el padron si resuelve, escritos igual para que el mapa sea el
        # padron de ESTE archivo y no una lista de excepciones a medias
        "Aldosivi": "Aldosivi",
        "Atl. Candelaria": "Atlético Candelaria",
        "Atlético Candelaria": "Atlético Candelaria",
        "Atlético Tucumán": "Atlético Tucumán",
        "Ben Hur": "Ben Hur",
        "Cipolletti": "Cipolletti",
        "Desamparados": "Desamparados",
        "Douglas Haig": "Douglas Haig",
        "General Paz Juniors": "General Paz Juniors",
        "Gimnasia y Tiro": "Gimnasia y Tiro (S)",
        "Guillermo Brown": "Guillermo Brown",
        "La Florida": "La Florida",
        "Luján de Cuyo": "Luján de Cuyo",
        "Rosario Puerto Belgrano": "Rosario Puerto Belgrano",
        "Sp. Desamparados": "Desamparados",
        # PERICO, NO CORDOBA. El de Cordoba jugaba la Primera Division esa
        # temporada -- tiene sus 19 partidos en `Primera Division - Clausura
        # 2004` -- y el que juega este torneo es el de Perico, Jujuy: la fase
        # regular, que sale de la grilla de Wikipedia, trae solo a ese, y la
        # propia RSSSF lo nombra `Talleres (Perico) ... (Jujuy)` en su tabla.
        #
        # Estaba mal y le puso el club equivocado a SEIS filas del dataset, todas
        # de las llaves: son las unicas de ese torneo donde aparecia Talleres (C).
        # Lo encontro un testigo externo al que se le habia pedido una fecha.
        "Talleres": "Talleres (P)",
        "Villa Mitre": "Villa Mitre",
    }
}

# DONDE VIVE CADA TEMPORADA EN RSSSF, incluido lo que todavia no se importa.
# Verificado archivo por archivo el 2026-08-22, y cada URL abierta y leida por dos
# agentes distintos: uno buscando y otro tratando de refutarlo.
#
# RSSSF no mantiene una sola convencion, y buscar por analogia lleva a un 404:
#
#   2004-05 .. 2008-09   archivo propio      arg3-int05 .. arg3-int09
#   2009-10              archivo propio      arg3-int2010
#   2010-11              SECCION de la temporada    arg2011.html#arga
#   2011-12              SECCION de la temporada    arg2012.html#arga
#   2012-13              archivo propio      arg3-int2013
#
# O sea que la serie de archivos propios se corta despues de 2009-10, vuelve en
# 2012-13, y en el medio el Argentino A es una seccion dentro de la pagina general
# del ano. No existe arg3-int2012 ni arg3-int11 ni arg3-int12: los cuatro dan 404.
# El indice viejo `tablesa/arg.html` tambien da 404; el que sirve es
# `tablesa/argint-champ.html`, que enlaza la temporada de cada campeon.
#
# Y hay dos divisiones mas, para lo que falta de la Primera C:
#
#   Primera C 2008-09    arg4-09.html   -- "Argentina Fourth Level (Primera C -
#                        Metropolitana) 2008/09". Trae el Reducido entero con
#                        localia y fecha. OJO: `arg4-int09` es OTRA competencia
#                        (el Argentino B), y confundirlas es el error facil.
#   Primera C 2011-12    RSSSF NO la cubre. La tiene el feed de ESPN (`arg.4`),
#                        que el repo ya usa: la localia sale de `homeAway` y NO
#                        del `venue`, que en dos partidos nombra una cancha que no
#                        es de ninguno de los dos.
#
# Dos trampas del formato que valen para todos: RSSSF NO escribe el ano en los
# corchetes -- `[May 26]`, no `[May 26, 2012]` --, asi que hay que deducirlo del
# arco de la temporada; y las paginas se sirven en latin-1 SIN meta charset, asi
# que leerlas como UTF-8 rompe los acentos.
# Primera C 2009-10, en `arg4-2010`. Igual que la temporada anterior: la fase
# regular no lleva encabezado de zona porque el torneo no tiene zonas, y por eso
# la clave es la vacia.
#
# ESTE ARCHIVO ESCRIBE VARIOS CLUBES DE DOS MANERAS, y las dos van al mapa: la
# fuente alterna `Barracas Bolìvar` con acento grave y `Barracas Bolívar` con
# agudo, `Gral Lamadrid` y `Gral. Lamadrid`, `Dvo Laferrere` y `Dvo. Laferrere`,
# `Fenix` y `Fénix`. No hay una forma canonica que elegir: hay que aceptar las
# dos o se pierden los partidos de la otra.
#
# Y `Talleres` A SECAS ES EL DE REMEDIOS DE ESCALADA, no el de Cordoba. El padron
# solo, preguntado por "Talleres", contesta `Talleres (C)`, que jugaba en otra
# division: es el homonimo mas caro del corpus y el motivo por el que este mapa
# se armo contra los VEINTE CLUBES QUE LA PAGINA HACE JUGAR esa temporada, y no
# contra el padron suelto. Cardinalidad, no parecido.
PRIMERA_C_2009 = {
    "": {
        "Argentino-M": "Argentino de Merlo",
        "Argentino-R": "Argentino de Rosario",
        "Barracas Bolìvar": "Barracas Bolívar",
        "Barracas Bolívar": "Barracas Bolívar",
        "Barracas Central": "Barracas Central",
        "Berazategui": "Berazategui",
        "Def. Unidos": "Defensores Unidos",
        "Def. de Cambaceres": "Defensores de Cambaceres",
        "Dvo Laferrere": "Deportivo Laferrere",
        "Dvo. Laferrere": "Deportivo Laferrere",
        "El Porvenir": "El Porvenir",
        "Excursionistas": "Excursionistas",
        "FC Midland": "Ferrocarril Midland",
        "Fenix": "Fénix",
        "Fénix": "Fénix",
        "Gral Lamadrid": "General Lamadrid",
        "Gral. Lamadrid": "General Lamadrid",
        "J.J. de Urquiza": "J. J. de Urquiza",
        "Leandro N. Alem": "Leandro N. Alem",
        "Luján": "Luján",
        "Sacachispas": "Sacachispas",
        "San Miguel": "San Miguel",
        "Talleres": "Talleres (RdE)",
        "Villa Dálmine": "Villa Dálmine",
    },
}


# Primera B Metropolitana 2010-11 y Primera C 2010-11, las dos dentro de
# `arg2011`. Desde esa temporada RSSSF deja de darle archivo propio a cada
# division y las mete todas en la pagina del ano, una atras de otra: la Primera
# Division, la B Nacional, la B Metropolitana, el Argentino A, la Primera C, el
# Argentino B y la Primera D, todas con sus `Round N`. Por eso el lector necesita
# el recorte de `SECCION_LIGA`, y por eso la clave del mapa es la vacia: adentro
# de su seccion, estos dos torneos no tienen zonas.
#
# Los mapas se armaron contra LOS CLUBES QUE LA PAGINA HACE JUGAR esa temporada,
# no contra el padron suelto, y eso decide dos nombres que el padron habria
# contestado mal: `Central Córdoba` a secas es el de Rosario y no el de Santiago
# del Estero, y `Talleres (RE)` es el de Remedios de Escalada. Cardinalidad.
PRIMERA_B_2010 = {
    "": {
        "Acassuso": "Acassuso",
        "Almagro": "Almagro",
        "Atlanta": "Atlanta",
        "Barracas Central": "Barracas Central",
        "Brown": "Brown de Adrogué",
        "Colegiales": "Colegiales",
        "Comunicaciones": "Comunicaciones",
        "Def. de Belgrano": "Defensores de Belgrano",
        "Dvo. Armenio": "Deportivo Armenio",
        "Dvo. Morón": "Deportivo Morón",
        "Estudiantes": "Estudiantes (BA)",
        "Flandria": "Flandria",
        "Los Andes": "Los Andes",
        "Nueva Chicago": "Nueva Chicago",
        "Platense": "Platense",
        "San Telmo": "San Telmo",
        "Sarmiento": "Sarmiento (J)",
        # el club se llamaba Deportivo Español; RSSSF lo escribe por su nombre
        # social, como tambien hace ESPN en la temporada siguiente.
        "Social Español": "Deportivo Español",
        "Svo. Italiano": "Sportivo Italiano",
        "Temperley": "Temperley",
        "Tristán Suárez": "Tristán Suárez",
        "Villa San Carlos": "Villa San Carlos",
    },
}

PRIMERA_C_2010 = {
    "": {
        "Argentino (M)": "Argentino de Merlo",
        "Berazategui": "Berazategui",
        "Central Córdoba": "Central Córdoba (R)",
        "Def. de Cambaceres": "Defensores de Cambaceres",
        "Defensores Unidos": "Defensores Unidos",
        "Dvo. Laferrere": "Deportivo Laferrere",
        "El Porvenir": "El Porvenir",
        "Excursionistas": "Excursionistas",
        "FC Midland": "Ferrocarril Midland",
        "Fénix": "Fénix",
        "Gral. Lamadrid": "General Lamadrid",
        "JJ de Urquiza": "J. J. de Urquiza",
        "Leandro N. Alem": "Leandro N. Alem",
        "Liniers": "Liniers",
        "Luján": "Luján",
        "Sacachispas": "Sacachispas",
        "San Miguel": "San Miguel",
        "Talleres (RE)": "Talleres (RdE)",
        "UAI-Urquiza": "UAI Urquiza",
        "Villa Dálmine": "Villa Dálmine",
    },
}


# De donde a donde va la fase regular de cada torneo, cuando su archivo trae
# varios. El corte de arriba es el titulo de la division y el de abajo es
# `Topscorers`, que en estas paginas viene justo despues de la ultima fecha y
# antes del `Reducido`: sin el, el reducido entraria como fase regular.
SECCION_LIGA: dict[str, tuple[str, str]] = {
    "Campeonato de Primera B 2010-11 (Argentina)": (
        'Primera B Metropolitano "Efectivo Sí"', "Topscorers"),
    "Campeonato de Primera C 2010-11 (Argentina)": (
        'Primera C Metropolitano "Efectivo Sí"', "Topscorers"),
}


# Torneo Argentino A 2010-11, dentro de `arg2011`. De aca sale SOLO la fase final:
# la fase regular tiene zonas y ya la trae la pagina, y lo que faltaba eran los
# ocho partidos de la Tercera Fase -- que RSSSF llama `Promotion Playoff` --, que
# la pagina publica sin dia.
#
# La seccion arranca en un ancla de tres lineas y no en `Promotion Playoff` a
# secas, porque ese titulo aparece dos veces en el archivo: una para el Argentino
# A y otra para la Primera D. Con la cola puesta identifica una sola.
#
# El mapa se armo contra los VEINTISIETE clubes que la pagina hace jugar esa
# temporada. Trae dos de mas -- `Defensores de Belgrano (VR)` y `Deportivo Roca`,
# que vienen del Argentino B a la promocion -- y esos salen del padron.
ARGENTINO_A_2010 = {
    "": {
        "9 de Julio": "9 de Julio (R)",
        "Alumni": "Alumni (VM)",
        "Alumni (Villa María)": "Alumni (VM)",
        "Central Córdoba": "Central Córdoba (SdE)",
        "Central Norte": "Central Norte (S)",
        "Cipolletti": "Cipolletti",
        "Crucero del Norte": "Crucero del Norte",
        "Def. de Belgrano (Villa Ramallo)": "Defensores de Belgrano (VR)",
        "Douglas Haig": "Douglas Haig",
        "Dvo Maipú": "Deportivo Maipú",
        "Dvo Roca (General Roca)": "Deportivo Roca",
        "Dvo Santamarina": "Ramón Santamarina",
        "Estudiantes": "Estudiantes (RC)",
        "Estudiantes (Río Cuarto)": "Estudiantes (RC)",
        "Gimnasia y Esgrima": "Gimnasia y Esgrima (CdU)",
        "Huracán": "Huracán (TA)",
        "Juv. Antoniana": "Juventud Antoniana",
        "Juventud Unida Univ.": "Juventud Unida Universitario",
        "Libertad": "Libertad (S)",
        "Racing": "Racing (C)",
        "Rivadavia": "Rivadavia (L)",
        "Svo Belgrano": "Sportivo Belgrano",
        "Svo Desamparados": "Desamparados",
        "Talleres": "Talleres (C)",
        "Unión (MdP)": "Unión (MdP)",
        "Unión (S)": "Unión (S)",
        "Villa Mitre": "Villa Mitre",
    },
}


# La promocion de la B Nacional 2007-08, dentro de `arg2-08`. De aca sale SOLO
# esa seccion: la fase regular de esa temporada la fecha worldfootball entera y
# lo unico que le faltaba a la pagina eran los cuatro partidos de las dos
# promociones, que publica sin dia.
#
# Cuatro clubes y cuatro entradas aunque el padron los resuelva a los cuatro sin
# ayuda. Es la regla del repo y no una formalidad: un mapa a medias es el que
# despues mete al club de al lado, y ademas asi queda escrito como los nombra la
# fuente. `Racing (C)` y `Talleres (C)` son los de Cordoba.
B_NACIONAL_2007 = {
    "": {
        "Los Andes": "Los Andes",
        "Nueva Chicago": "Nueva Chicago",
        "Racing (C)": "Racing (C)",
        "Talleres (C)": "Talleres (C)",
    },
}


FUENTES: dict[str, tuple[str, dict]] = {
    "Torneo Argentino A 2005-06": ("arg3-int06", ARGENTINO_A_2005),
    "Torneo Argentino A 2006-07": ("arg3-int07", ARGENTINO_A_2006),
    "Torneo Argentino A 2007-08": ("arg3-int08", ARGENTINO_A_2007),
    "Torneo Argentino A 2008-09": ("arg3-int09", ARGENTINO_A_2008),
    "Torneo Argentino A 2009-10": ("arg3-int2010", ARGENTINO_A_2009),
    "Torneo Argentino A 2012-13": ("arg3-int2013", ARGENTINO_A_2012),
    "Torneo Argentino A 2011-12": ("arg2012", ARGENTINO_A_2011),
    "Campeonato de Primera C 2008-09 (Argentina)": ("arg4-09", PRIMERA_C_2008),
    "Campeonato de Primera C 2009-10 (Argentina)": ("arg4-2010", PRIMERA_C_2009),
    "Campeonato de Primera C 2010-11 (Argentina)": ("arg2011", PRIMERA_C_2010),
    "Campeonato de Primera B 2010-11 (Argentina)": ("arg2011", PRIMERA_B_2010),
    "Torneo Argentino A 2004-05": ("arg3-int05", ARGENTINO_A_2004),
    "Torneo Argentino A 2010-11": ("arg2011", ARGENTINO_A_2010),
    "Campeonato de Primera B Nacional 2007-08": ("arg2-08", B_NACIONAL_2007),
}

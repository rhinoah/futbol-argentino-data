#!/usr/bin/env python3
"""
fad/posiciones.py
=================
Cruzar los partidos parseados contra la tabla de posiciones de la misma pagina.

POR QUE ESTE CHEQUEO ES DISTINTO A LOS DEMAS
--------------------------------------------
Casi todo `validar.py` mira los partidos entre si: que nadie juegue dos veces por
fecha, que el ganador reaparezca en la ronda siguiente, que la localia se reparta.
Son invariantes del fixture, y agarran los errores que TIENEN forma de fixture.

Este mira otra cosa. La pagina publica, aparte de los resultados, una tabla con
los partidos jugados y los goles a favor y en contra de cada club. Es una
afirmacion INDEPENDIENTE sobre la misma temporada, escrita por otra mano y
normalmente copiada de la planilla oficial. Sumando los marcadores tiene que dar
exactamente eso.

Eso lo convierte en la unica cosa del repo que puede decidir *cual de dos fuentes
tiene razon sobre un marcador* sin salir a preguntarle a una tercera. Se uso para
arbitrar los nueve partidos que Wikipedia y worldfootball contaban distinto, y en
uno de los nueve le dio la razon a Wikipedia -- que es lo que muestra que mide
algo y no siempre lo mismo.

CUANDO NO OPINA
---------------
Si la pagina no trae tabla, o los PJ no coinciden, este modulo no dice nada:
callarse es correcto, inventar un aviso no.

En el formato wikitabla una fila ademas tiene que cerrar CONSIGO MISMA
(`GF - GC == DIF` y `PG + PE + PP == PJ`) para que se la use. Ojo con creer que
esa guarda protege siempre: el otro formato, `{{Tabla de posiciones equipo}}`,
publica solo `g/e/p/gf/gc` y deja que la plantilla calcule PJ y DIF, asi que ahi
no hay contra que chequear y las filas entran crudas. Y es el formato mayoritario
-- de los 113 torneos que hoy tienen arbitro, la mayoria vienen por esa rama.
Lo que sostiene esas filas no es una resta interna sino el cruce mismo: si el
G-E-P publicado reproduce los partidos parseados y solo discrepan los goles, la
fila es de fiar salvo en un digito.
"""
from __future__ import annotations

import re
from collections import Counter

from fad import correcciones, equipos, parser

# Pts, PJ, PG, PE, PP, GF, GC, DIF: las ocho columnas numericas de la fila.
_COLUMNAS = 8


# La tabla se escribe de DOS formas, y la segunda no es una tabla: es una lista
# de plantillas, una por club.
#
#   {{Tabla de posiciones equipo|pos=01|g=23|e=12|p=3|gf=59|gc=15|eq=[[...|Barracas Central]]}}
#
# Buscando solo `{|` se pierden esas paginas enteras -- y con ellas el arbitro, que
# es lo unico que decide cual de dos fuentes tiene razon sobre un marcador.
_FILA_PLANTILLA = re.compile(r"\{\{\s*Tabla de posiciones equipo\s*\|(.*?)\}\}", re.I | re.S)
# El nombre NO se saca partiendo por `|`: el wikilink de adentro tambien lleva
# uno, asi que "eq=[[Club Atlético San Telmo|San Telmo]]" se parte al medio y el
# club queda llamandose "[[Club Atlético San Telmo".
_CAMPO_EQUIPO = re.compile(r"(?<![a-zA-Z])eq\s*=\s*(.*?)(?:\|\s*#?\s*color\s*=|$)", re.S)
# Adentro del `eq=` casi siempre hay un wikilink, y ese wikilink trae el ARTICULO,
# que es lo que desambigua de verdad. Sacandolo de ahi se arreglan de una tres
# cosas a la vez, todas medidas:
#
#   eq=[[Club Atlético Colón|Colón]]{{refn|group="n."|Se le descontaron 6 puntos...
#       la nota al pie quedaba pegada al nombre y el club se caia del cruce. Y no
#       es cualquier club: el que tiene quita de puntos es justo el que hay que
#       mirar. Van doce asi, entre quitas y clasificaciones a copas.
#   eq=[[...|Boca Juniors]]||color=#cfc   /   eq=[[...|Rosario Central]]|#color=#cfc
#       un pipe de mas o un `#` adelante, y el club se llamaba "Boca Juniors|".
#   eq=[[Asociación Civil Leones de Rosario Fútbol Club|Leones (Rosario)]]
#       la tabla lo llama "Leones (Rosario)" y los partidos "Leones de Rosario".
#       Por el nombre visible son dos clubes; por el articulo son el mismo.
_EQ_WIKILINK = re.compile(r"\[\[\s*([^\]|]+?)\s*(?:\|([^\]]*))?\]\]")
_NUMEROS = {k: re.compile(rf"(?<![a-zA-Z]){k}\s*=\s*(\d+)") for k in ("g", "e", "p", "gf", "gc")}
# Donde empieza la nota al pie que cuelga del nombre, cuando el nombre no es un
# wikilink. Ver `_por_plantillas`.
_COLA_DE_NOTA = re.compile(r"\{\{|<ref")
_ENCABEZADO = re.compile(r"^==+[^=\n]*Tabla de posiciones[^=\n]*==+[^\n]*$", re.M | re.I)
_CUALQUIER_ENCABEZADO = re.compile(r"^==+[^=\n]+==+", re.M)
# Una wikitabla cierra con `\n|}` -- salvo cuando la cierra la plantilla de la
# leyenda, que es lo que hace la Primera C 2010-11: sus veinte filas van en una
# wikitabla comun pero abajo lleva `{{Tabla de posiciones fin|color1=...}}` en
# vez del `|}`. Buscando solo `\n|}` esa tabla no termina nunca; el codigo viejo
# la encontraba igual porque escaneaba la pagina entera y cerraba en la tabla de
# promedios, dos secciones mas abajo. Eso funcionaba de casualidad.
# El cierre va como lookahead y no adentro del match: si se lo lleva puesto, queda
# pegado a la ultima fila y esa fila se pierde. En la Primera C 2010-11 se perdian
# dos de los veinte clubes por eso, y no se notaba porque los otros dieciocho
# alcanzaban para que la pagina "tuviera tabla".
_WIKITABLA = re.compile(r"\{\|.*?(?=\n\|\}|\{\{\s*Tabla de posiciones fin)", re.S | re.I)


# Una tabla de posiciones SE DECLARA: su fila de encabezado nombra las columnas.
# Buscarla por ahi, y no por el titulo de la seccion que la contiene, es lo unico
# que encuentra las que viven bajo cualquier otro rotulo.
#
# El caso que lo motivo: el Torneo Argentino A 2005-06 pone sus CUATRO tablas
# -- Apertura y Clausura por zona -- debajo de `=== Primera fase ===`, sin la
# frase "Tabla de posiciones" en ningun lado. La pagina tenia arbitro y el
# arbitro no lo encontraba, y eso importo de verdad: cuando aparecio que la
# pagina se habia copiado dos jornadas a si misma, fueron esas cuatro tablas las
# que dijeron cual de las dos versiones era la buena.
_CELDA_ENCABEZADO = re.compile(r"^!(.+)$", re.M)
# Las seis que definen la forma. `Pts` y `Pos` quedan afuera a proposito: hay
# tablas de posiciones sin columna de posicion, y `Pts` sola aparece en tablas
# que no son de posiciones.
_COLUMNAS_DECLARADAS = {"pj", "pg", "pe", "pp", "gf", "gc"}


def _etiquetas(tabla: str) -> set[str]:
    """Los rotulos de columna que declara la fila de encabezado."""
    fuera = set()
    for m in _CELDA_ENCABEZADO.finditer(tabla):
        for celda in m.group(1).split("!!"):
            # `width=5% | PJ` -> `PJ`. Lo que va antes del ultimo `|` son
            # atributos de la celda, no el rotulo.
            fuera.add(parser.limpiar(celda.split("|")[-1]).strip().lower())
    return fuera


def _declara_ser_tabla_de_posiciones(tabla: str) -> bool:
    etiquetas = _etiquetas(tabla)
    # La de PROMEDIOS tiene las mismas columnas y una mas, y es la trampa clasica
    # de esta pagina: su PJ es de tres temporadas, asi que si entra se lleva
    # puesto el desempate por max-PJ y el club termina con los partidos de tres
    # anios donde tenia que tener los de uno.
    if any("prom" in e for e in etiquetas):
        return False
    return _COLUMNAS_DECLARADAS <= etiquetas


# Las secciones cuyas tablas son AGREGADOS y no la tabla de una fase. Se excluyen
# aunque declaren las mismas columnas, y el motivo no es de forma sino de fondo:
# son una SUMA de las otras, asi que no aportan nada -- pero traen mas partidos y
# por el desempate de max-PJ desplazan a las primarias, que son las buenas.
#
# Medido en el Argentino A 2005-06: su tabla de descenso coincide con la suma de
# las cuatro tablas de zona en 17 de 23 clubes, o sea que es exactamente eso, una
# suma. Y en el que no coincide, el equivocado es el agregado: a 9 de Julio (R)
# le pone GF29 donde las de zona suman 39. Dejandola entrar, el arbitro pasaba a
# comparar contra una tabla derivada y con un error propio, y denunciaba tres
# contradicciones que no existen.
_SECCION_AGREGADA = re.compile(r"(?i)descenso|promedio|anual|acumulad")


def _tablas_declaradas(texto: str):
    """Las wikitablas de toda la pagina cuyo encabezado dice que son de posiciones.

    Salvo las que cuelgan de una seccion de agregados: ver `_SECCION_AGREGADA`.
    """
    encabezados = [(m.start(), m.group(0)) for m in _CUALQUIER_ENCABEZADO.finditer(texto)]
    for m in re.finditer(r"\{\|.*?\n\|\}", texto, re.S):
        if not _declara_ser_tabla_de_posiciones(m.group(0)):
            continue
        previos = [h for off, h in encabezados if off < m.start()]
        if previos and _SECCION_AGREGADA.search(previos[-1]):
            continue
        yield m.group(0)


def _bloques(texto: str):
    """El texto que sigue a CADA encabezado "Tabla de posiciones", hasta el
    proximo encabezado.

    Son varios y hay que leerlos todos. Un torneo por zonas publica una tabla
    por zona, y el titulo no las distingue -- las dos se llaman "Tabla de
    posiciones final" y lo que cambia es el `== Zona A ==` de arriba. Mientras
    esto leia solo la primera, la mitad de esas paginas se cruzaba contra nada:
    en el Federal A 2019-20 los quince clubes de la Zona B volvian sin tabla, y
    en la Primera C 2026 la Zona B escondia dos contradicciones mas que el aviso
    nunca denuncio. Son 91 de las 279 paginas.
    """
    for m in _ENCABEZADO.finditer(texto):
        sig = _CUALQUIER_ENCABEZADO.search(texto, m.end())
        yield texto[m.end():sig.start()] if sig else texto[m.end():]


def _por_plantillas(bloque: str, arts: dict[str, str]) -> list[tuple[str, str, tuple[int, int, int]]]:
    """Las filas escritas como `{{Tabla de posiciones equipo|...}}`.

    Devuelve las filas CRUDAS -- `(nombre visible, articulo, (PJ, GF, GC))` -- y no
    el club ya canonizado. Canonizar aca parecia mas prolijo y escondia justo lo
    que hay que ver: si el padron no conoce ese nombre, `canonizar` lo devuelve
    intacto, la fila queda con un club que no existe y se cae sola del cruce, en
    silencio. Guardando el nombre como vino, `fuera_del_padron` puede denunciarlo.
    """
    fuera = []
    for fila in _FILA_PLANTILLA.finditer(bloque):
        cuerpo = fila.group(1)
        nums = {}
        for k, rx in _NUMEROS.items():
            hit = rx.search(cuerpo)
            if hit:
                nums[k] = int(hit.group(1))
        eq = _CAMPO_EQUIPO.search(cuerpo)
        if len(nums) < 5 or not eq:
            continue
        enlace = _EQ_WIKILINK.search(eq.group(1))
        if enlace:
            articulo = enlace.group(1)
            club = parser.limpiar(enlace.group(2) or articulo)
        else:
            # Sin wikilink el nombre viene crudo, y atras puede colgar una nota
            # al pie: `eq=Huracán Las Heras{{refn|group=n.|Se le descontaron 3
            # puntos.<ref...`. `limpiar` no la saca, y encima la plantilla ni
            # siquiera cierra -- `_FILA_PLANTILLA` corta en el primer `}}`, que
            # es el del propio refn.
            #
            # La rama del wikilink ya estaba a salvo de esto, y por eso el
            # arreglo tardo en aparecer: parecia cubierto. No lo estaba para el
            # club escrito a mano, y justamente el que lleva nota al pie es el
            # que tiene quita de puntos, que es el que mas importa mirar. Un solo
            # club se caia asi en todo el corpus, el Huracan Las Heras del
            # Federal A 2022, y con el se caia el cruce de esa pagina entera.
            corte = parser.limpiar(_COLA_DE_NOTA.split(eq.group(1), 1)[0])
            # Si cortar deja la celda vacia es porque la plantilla venia ADELANTE
            # (`eq={{bandera|Mendoza}} Huracán Las Heras`), y ese caso ya se perdio
            # antes: `_FILA_PLANTILLA` corto la fila en el `}}` de la bandera. Se
            # devuelve el crudo igual, sucio, a proposito -- un nombre ilegible
            # queda como club desconocido y `fuera_del_padron` lo denuncia, y una
            # celda vacia hace desaparecer la fila sin que nadie se entere.
            club = corte or parser.limpiar(eq.group(1))
            articulo = arts.get(club, "")
        if not club:
            continue
        fuera.append((club, articulo,
                      (nums["g"] + nums["e"] + nums["p"], nums["gf"], nums["gc"],
                       nums["g"], nums["e"], nums["p"])))
    return fuera


def tabla(texto: str, arts: dict[str, str] | None = None, pagina: str = "") -> dict[str, tuple[int, int, int]]:
    """{club canonico: (PJ, GF, GC)} segun las tablas que publica la pagina.

    Se busca por DOS caminos, y hacen falta los dos:

      * las secciones tituladas "Tabla de posiciones", que es donde estan la
        mayoria y el unico camino por el que entra el formato de plantillas
        (`{{Tabla de posiciones equipo}}`), que no tiene fila de encabezado;
      * las wikitablas que SE DECLARAN de posiciones por sus propias columnas,
        vivan bajo el titulo que vivan.

    El segundo se agrego tarde y por un caso concreto: el Torneo Argentino A
    2005-06 tiene cuatro tablas debajo de `=== Primera fase ===`, sin la frase
    "Tabla de posiciones" en ningun lado, asi que la pagina tenia arbitro y el
    arbitro no lo encontraba. Aparecio buscando otra cosa -- la misma pagina se
    habia copiado dos jornadas a si misma, y fueron esas cuatro tablas las que
    dijeron cual version era la buena.

    Cuando un club aparece en dos, gana la que tiene mas partidos. Es lo que
    separa los dos motivos por los que una pagina trae varias: si son zonas
    distintas los clubes son disjuntos y no se pisan, y si es la "parcial de la
    primera rueda" contra la final, la parcial tiene la mitad de los partidos y
    pierde. Antes esto se resolvia leyendo solo la primera tabla, que arreglaba
    la parcial y rompia las zonas.
    """
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    fuera: dict[str, tuple[int, int, int]] = {}
    for club, articulo, datos in _todas_las_filas(texto, arts):
        canonico = _canonico(club, articulo, pagina)
        if canonico not in fuera or datos[0] > fuera[canonico][0]:
            # Se recorta a (PJ, GF, GC) a proposito. Las filas traen tambien el
            # G-E-P -- lo usa `resultados_que_no_coinciden` --, pero esta funcion
            # es la vieja y publica, y ensancharle la tupla obligaria a cada
            # llamador a saber de una columna que no le importa.
            fuera[canonico] = tuple(datos[:3])
    return fuera


def _todas_las_filas(texto: str, arts: dict[str, str], descartadas: list | None = None):
    """Las filas crudas de TODAS las tablas de la pagina, por los dos caminos.

    Existe para que `tabla` y `fuera_del_padron` no puedan mirar cosas distintas.
    Antes miraban: `tabla` leia los dos caminos y `fuera_del_padron` solo el del
    encabezado, asi que en las paginas cuyas tablas no dicen "Tabla de
    posiciones" el detector de padron no veia nada. Se notaba en el Argentino A
    2005-06, que devolvia cero nombres desconocidos aunque su tabla los tenga --
    `Cipolletti (*)`, `Juventud (P) (*)` -- y esos son justo los que hay que
    agregar para que sus filas entren al cruce.
    """
    for bloque in _bloques(texto):
        yield from _filas(bloque, arts, descartadas)
    for t in _tablas_declaradas(texto):
        yield from _por_wikitabla(t, arts, descartadas)


def _filas(bloque: str, arts: dict[str, str],
           descartadas: list | None = None) -> list[tuple[str, str, tuple[int, int, int]]]:
    """Las filas crudas del bloque, venga en el formato que venga."""
    return _por_plantillas(bloque, arts) or _por_wikitabla(bloque, arts, descartadas)


def _canonico(nombre: str, articulo: str, pagina: str) -> str:
    """El nombre de una fila de tabla, ya resuelto: padron y homonimos.

    Es la UNICA puerta por la que un nombre de tabla se vuelve canonico. Va junto
    porque las dos resoluciones tienen que ser la misma que la de los partidos:
    si una fila resuelve por un camino distinto, no falla, se saltea el cruce.
    """
    return correcciones.homonimo(pagina, equipos.canonizar(nombre, articulo))


def fuera_del_padron(texto: str, arts: dict[str, str] | None = None,
                     pagina: str = "") -> list[str]:
    """Los clubes que la tabla nombra y el padron no conoce.

    Los nombres de la TABLA nunca pasaban por ningun control. El del padron mira
    los clubes de los PARTIDOS -- ahi un desconocido frena el build -- pero la
    tabla entra por otra puerta, y `canonizar` devuelve intacto lo que no
    reconoce. Entonces la fila queda a nombre de un club que no existe, no
    engancha con ningun partido, y el cruce la descarta sin decir nada. El
    arbitro se debilita justo donde nadie mira.

    Lo destapo la Primera C 2026: la tabla escribe `[[Asociación Civil Leones de
    Rosario Fútbol Club|Leones (Rosario)]]` y la grilla escribe "Leones de
    Rosario". Por el nombre visible son dos clubes; por el articulo son el mismo,
    y el articulo faltaba en el padron. Con esa fila afuera, la pagina entera
    dejaba de tener veredicto -- y apenas volvio, resulto que su tabla ni
    siquiera balancea.

    Es el mismo error del que el proyecto ya aprendio una vez: vacio no es lo
    mismo que ilegible. Un club que no se puede leer no puede tratarse como un
    club que no esta.
    """
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    vistos: dict[str, str] = {}
    for club, articulo, _ in _todas_las_filas(texto, arts):
        if not equipos.conocido(club, articulo):
            vistos.setdefault(club, articulo)
    return [f"la tabla de posiciones nombra a \"{club}\""
            + (f" (articulo: {art})" if art else " (sin articulo que lo desambigue)")
            + ", que el padron no conoce: esa fila no engancha con ningun partido "
              "y se cae del cruce en silencio"
            for club, art in sorted(vistos.items())]


def sin_partidos(ps: list, texto: str, arts: dict[str, str] | None = None,
                 pagina: str = "") -> list[str]:
    """Los clubes que la tabla nombra y que en la pagina no jugaron nunca.

    Es el hermano general de `fuera_del_padron`, y agarra mas que el: aquel pide
    que el nombre sea ilegible, y este solo que la fila no tenga con que cruzarse.
    Un nombre puede estar perfectamente en el padron y aun asi apuntar al club
    equivocado -- el Argentino A 2005-06 escribe "Juventud Unida" en la tabla y
    "Juventud Unida Universitario" en los partidos, y son dos clubes distintos de
    verdad, asi que `canonizar` los deja como estan y nadie se queja. La fila se
    cae del cruce igual que si el nombre no existiera.

    Se mide contra el ALCANCE, no contra el torneo entero: una tabla de zona
    tiene que cruzarse con los partidos de su zona. Y solo se mira lo que la
    tabla afirma de mas; que un club jugo y no tiene fila es otra cosa (pasa en
    toda reválida, donde la tabla cubre a la mitad del torneo) y no se avisa.
    """
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    huerfanos: dict[str, str] = {}
    for alcance, filas in _alcance_de_cada_tabla(texto, arts, ps, pagina):
        jugaron = {p.local for p in ps if not alcance or p.llave == alcance}
        jugaron |= {p.visita for p in ps if not alcance or p.llave == alcance}
        for club in filas:
            if club not in jugaron:
                huerfanos.setdefault(club, alcance)
    return [f"la tabla de \"{alcance or 'la pagina'}\" tiene una fila de {club}, "
            f"que ahi no jugo ningun partido: o la tabla lo nombra de otra forma "
            f"que la grilla -- y entonces va un homonimo en fad/correcciones.py --, "
            f"o le sobra una fila"
            for club, alcance in sorted(huerfanos.items())]


_ENLACE = re.compile(r"\[\[\s*([^\]|#]+?)\s*(?:\|[^\]]*)?\]\]")
_DESAMBIGUADOR = re.compile(r"\s*\([^)]*\)\s*$")


def _sin_desambiguador(nombre: str) -> str:
    return equipos.normalizar(_DESAMBIGUADOR.sub("", nombre))


def _homonimos_de(club: str) -> set[str]:
    """Los clubes del padron que comparten el nombre base con `club`.

    Mira TODOS los nombres de cada uno y no solo el canonico, y eso no es un
    detalle: el homonimo de "Juventud Unida" es "Juventud Unida Universitario",
    y lo que los emparenta es su alias "Juventud Unida (SL)". Comparando
    canonicos, el caso mas grande que tuvo el repo -- 36 partidos -- no se ve.
    """
    base = _sin_desambiguador(club)
    return {e.nombre for e in equipos.PADRON
            if any(_sin_desambiguador(n) == base for n in (e.nombre, *e.alias))} - {club}


def homonimo_de_la_pagina(ps: list, texto: str, arts: dict[str, str] | None = None,
                          pagina: str = "") -> list[str]:
    """Un club sin desambiguar que la pagina no enlaza nunca, y que tiene un
    homonimo al que la pagina SI enlaza y ademas pone en su tabla.

    Es el aviso del lado de la GRILLA, y es el ultimo de los cuatro. Los otros
    tres miran la tabla: `fuera_del_padron` pide que el nombre sea ilegible,
    `sin_partidos` que la fila no tenga contra que cruzarse, `contrastar` que los
    goles no cierren. Ninguno ve el error que entra por la grilla, que es el
    unico que no falla NUNCA: un nombre pelado que el padron resuelve solo, y lo
    resuelve al club equivocado. Los partidos quedan prolijos -- con fecha, con
    marcador, con cancha -- a nombre de otro.

    Las tres condiciones son las tres necesarias, y estan medidas sobre las 131
    paginas:

      * el club no lleva desambiguador. Sin esto entran 34 casos mas, todos
        clubes bien atribuidos a los que les falta el articulo en `ARTICULOS`.
      * la pagina no lo enlaza NUNCA. Un wikilink no se adivina: si esta, la
        resolucion es segura y no hay nada que denunciar.
      * el homonimo esta enlazado Y tabulado. Solo enlazado deja 14 falsos de la
        Copa Argentina, donde "Independiente" pelado es el de Avellaneda y la
        pagina lo enlaza con un articulo que el padron no tenia. Pedir la fila de
        tabla los apaga a los catorce: la Copa es eliminacion directa.

    Se mide sobre los nombres YA corregidos, asi que una correccion lo apaga:
    sobre el corpus de hoy no dice nada. Desarmando las correcciones prende en
    cuatro paginas y las seis veces tiene razon.
    """
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    enlazados = {eq.nombre for d in _ENLACE.findall(texto)
                 if (eq := equipos.buscar("", d)) is not None}
    en_tabla = {_canonico(club, art, pagina)
                for club, art, _ in _todas_las_filas(texto, arts)}
    fuera = []
    for club in sorted({p.local for p in ps} | {p.visita for p in ps}):
        if "(" in club or club in enlazados:
            continue
        otros = sorted(_homonimos_de(club) & en_tabla & enlazados)
        if otros:
            fuera.append(
                f"la grilla nombra a \"{club}\" sin desambiguar y la pagina no lo "
                f"enlaza nunca, pero si enlaza y tabula a {', '.join(otros)}: el "
                f"padron resolvio el nombre pelado por su cuenta y la pagina dice "
                f"otra cosa. Si tiene razon la pagina, va un homonimo en "
                f"fad/correcciones.py")
    return fuera


def filas_que_no_cierran(texto: str, arts: dict[str, str] | None = None,
                         pagina: str = "") -> list[str]:
    """Las filas que la pagina publica y la guarda de coherencia descarta.

    Una fila de wikitabla tiene que cerrar CONSIGO MISMA para que se la use:
    `GF - GC == DIF` y `PG + PE + PP == PJ`. Es una guarda barata y correcta --
    una fila mal tipeada no puede desmentir a nadie --, pero descartaba en
    SILENCIO, y eso deja al club sin arbitro sin que nada lo diga. Ni
    `contrastar` ni `desbalance` pueden suplirlo: no opinan sobre una fila que no
    llego a parsearse, asi que el aviso que falta es justamente este.

    Son tres en las 131 paginas, y las tres son erratas de la fuente que la
    grilla desmiente sola: Almirante Brown y Guillermo Brown del B Nacional
    2011-12 suman 37 partidos con PJ 38 (la grilla dice que perdieron uno mas de
    los que la tabla les cuenta), y Leandro N. Alem de la Primera C 2010-11
    publica DIF -15 sobre 32:48, que es -16. Las dos tablas quedaban con una fila
    menos que clubes -- 18 de 20 y 19 de 20 -- sin que nadie lo mencionara.
    """
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    descartadas: list = []
    for _ in _todas_las_filas(texto, arts, descartadas):
        pass
    vistas: dict[str, str] = {}
    for club, (pts, pj, pg, pe, pp, gf, gc, dif) in descartadas:
        falla = []
        if gf - gc != dif:
            falla.append(f"dice DIF{dif:+d} y GF{gf} - GC{gc} da {gf - gc:+d}")
        if pg + pe + pp != pj:
            falla.append(f"dice PJ{pj} y {pg}+{pe}+{pp} da {pg + pe + pp}")
        vistas.setdefault(
            _canonico(club, "", pagina),
            f"la fila de {club} no cierra sola ({'; '.join(falla)}), asi que no se "
            f"usa y ese club se queda sin cruzar. La equivocada es la tabla salvo "
            f"que la grilla tambien falle: contra que numero mira el que la lea")
    return [v for _, v in sorted(vistas.items())]


def clubes_desviados(ps: list, texto: str, arts: dict[str, str] | None = None,
                     pagina: str = "") -> set[str]:
    """Los clubes cuya tabla no cierra con la grilla, SIN filtrar los revisados.

    Existe justamente para que `revisados_huerfanos` pueda preguntar por los
    desvios crudos. Si preguntara por los que quedan despues del filtro, cada
    `Revisado` se justificaria a si mismo -- tapa el desvio, el desvio desaparece,
    y por lo tanto nunca aparece como huerfano -- y la guarda no guardaria nada.
    """
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    fuera = set()
    for alcance, filas in _alcance_de_cada_tabla(texto, arts, ps, pagina):
        propios = _propios_de(ps, alcance)
        for club, datos in filas.items():
            if club not in propios or propios[club][0] != datos[0]:
                continue
            if tuple(datos[1:3]) != tuple(propios[club][1:3]) or                     (len(datos) >= 6 and tuple(datos[3:6]) != tuple(propios[club][3:6])):
                fuera.add(club)
    return fuera


# Los dos clubes de una acusacion del resaltado, que el aviso escribe al
# principio: "Local G-V Visita: los numeros dicen...".
_ACUSADOS = re.compile(r"^(.*?) (\d+)-(\d+) (.*?): ")


def resaltado_sin_respuesta(ps: list, texto: str, arts: dict[str, str] | None = None,
                            pagina: str = "",
                            ya_arbitrados: set | None = None) -> list[str]:
    """Las acusaciones del resaltado que la TABLA no puede contestar.

    `parser.resaltado_que_desmiente` marca la fila cuyo color contradice a sus
    propios digitos, y es un buen acusador: medido contra los marcadores que el
    repo ya tiene arbitrados, cuando contradice a su fila acerta 4 de 4. Pero no
    es el unico que sabe quien gano. La tabla lo dice en su columna G-E-P, y ese
    testigo tambien se midio -- acerto las dos veces que se lo pudo contrastar --
    con la ventaja de que no depende de un color.

    Cuando los dos coinciden, el aviso vale. Cuando se contradicen, hay que mirar
    cual de los dos escenarios es, y la evidencia esta del lado de la tabla:

      * en los cuatro casos donde el resaltado acerto, el arreglo CAMBIABA la
        direccion del partido, asi que la tabla se desviaba tambien y los dos
        testigos decian lo mismo;
      * cuando la tabla dice que la direccion de la grilla esta bien, para que el
        color tuviera razon tendrian que estar mal la grilla Y la tabla, las dos
        del mismo lado. Es mas barato que se le haya pintado la celda equivocada
        a quien coloreo la fila, que es un error de una tecla y no toca ningun
        numero.

    Por eso esta funcion se queda solo con las acusaciones que la tabla NO puede
    contestar: aquellas donde alguno de los dos clubes no es comparable -- la
    tabla y la grilla le cuentan distintos partidos, asi que no opina -- o donde
    la tabla efectivamente se desvia y acompania al color.

    No es silenciar: es no publicar como pregunta abierta algo que la propia
    pagina ya contesto. Las 19 que habia se contestan todas, y las cuatro que le
    dieron su credibilidad al metodo habrian sobrevivido a este filtro, porque en
    las cuatro el arreglo cambiaba la direccion y la tabla acusaba junto con el
    color.
    """
    acusaciones = parser.resaltado_que_desmiente(texto, ya_arbitrados or frozenset())
    if not acusaciones:
        return []
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    # Los clubes a los que la tabla les cuenta los mismos partidos que la grilla
    # Y ademas les da la misma direccion. Sobre esos, la tabla ya contesto.
    contesta = set()
    for alcance, filas in _alcance_de_cada_tabla(texto, arts, ps, pagina):
        propios = _propios_de(ps, alcance)
        for club, datos in filas.items():
            if club not in propios or len(datos) < 6:
                continue
            # No hace falta comparar el PJ aparte: la fila de la tabla solo
            # entra si G+E+P == PJ, y la suma de la grilla tambien cuenta sus
            # propios partidos, asi que dos trios iguales ya implican el mismo
            # PJ. Pedirlo dos veces daba un mutante que nada podia distinguir.
            if tuple(datos[3:6]) == tuple(propios[club][3:6]):
                contesta.add(club)
    fuera = []
    for aviso in acusaciones:
        m = _ACUSADOS.match(aviso)
        if not m:
            fuera.append(aviso)
            continue
        clubes = [_canonico(m.group(1), "", pagina), _canonico(m.group(4), "", pagina)]
        if all(c in contesta for c in clubes):
            continue
        fuera.append(
            aviso + ". Y la tabla no lo contesta: " +
            ", ".join(f"a {c} le cuenta distinto" for c in clubes if c not in contesta))
    return fuera


def resultados_que_no_coinciden(ps: list, texto: str, arts: dict[str, str] | None = None,
                                pagina: str = "") -> list[str]:
    """Los clubes a los que la tabla y la grilla les cuentan distintos G-E-P.

    `contrastar` compara GOLES y este compara RESULTADOS, y esa diferencia es
    todo el punto. Los dos miran la misma tabla y la misma grilla, pero preguntan
    cosas distintas: cuantos goles hubo, y quien gano. Un aviso de `contrastar`
    hoy tapa dos averias que no se arreglan igual:

      * si el G-E-P COINCIDE, todos los partidos de ese club estan del lado
        correcto y lo que falla es un DIGITO. La correccion, si aparece, no puede
        cambiar el resultado de ningun partido -- y eso refuta candidatos sin
        mirar una sola fuente de afuera.
      * si el G-E-P DIFIERE y los GOLES TAMBIEN, y difiere en espejo con otro
        club, entonces hay un partido entero al reves entre esos dos. Es mas
        grave y mas facil de localizar: son los cruces del par donde el arreglo
        CAMBIA el ganador.
      * si el G-E-P difiere y los goles NO, no hay partido posible. Un marcador
        mal leido mueve siempre los goles -- cambiarle un digito le toca el GF o
        el GC a los dos clubes --, asi que un resultado corrido con los goles
        intactos solo puede ser la fila de la tabla mal tipeada. Ahi el aviso
        dice que no hay nada que buscar, que es tan util como decir donde buscar.
        Es uno en el corpus: Defensores de Belgrano en la Primera Nacional 2025,
        con la tabla en 12-13-9 y la grilla en 12-12-10 sobre los mismos goles.

    Es un testigo de direccion y no de magnitud: dice quien gano, nunca cuantos
    goles. Por eso no propone marcadores -- un 2-1 y un 3-0 le dan lo mismo -- y
    por eso vale, porque no es la misma pregunta que ya hace `contrastar`.

    Medido sobre las 131 paginas: 545 clubes coinciden y 31 se desvian,
    repartidos en 4 paginas. Y el desvio cae donde tiene que caer: tres de esas
    cuatro son paginas cuya tabla ya no cerraba.

    Lo que hizo en el Argentino A 2010-11, que es para lo que se escribio: sus
    seis clubes desviados forman tres pares, y hasta aca los tres se veian igual.
    El G-E-P los parte en dos clases -- dos pares con el G-E-P intacto y uno con
    una victoria cambiada de dueno -- y con eso, de los nueve arreglos posibles
    quedan cuatro: dos pares con candidato UNICO y uno con dos. Ninguno se aplica
    -- localizar no es arbitrar --, pero el conjunto a verificar se achico a la
    mitad y cada sobreviviente dice exactamente que hay que buscar.
    """
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    publicada, contada = {}, {}
    for alcance, filas in _alcance_de_cada_tabla(texto, arts, ps, pagina):
        propios = _propios_de(ps, alcance)
        for club, datos in filas.items():
            if len(datos) < 6:
                continue
            if club not in publicada or datos[0] > publicada[club][0]:
                publicada[club] = datos
                if club in propios:
                    contada[club] = propios[club]
    fuera = []
    for club, datos in sorted(publicada.items()):
        if club not in contada or correcciones.revisado(pagina, club):
            continue
        pj, suyo = datos[0], tuple(datos[3:6])
        # Misma guarda que `contrastar`, y por el mismo motivo: con distinta
        # cantidad de partidos las dos partes no hablan del mismo conjunto y
        # comparar no significa nada.
        if contada[club][0] != pj:
            continue
        mio = tuple(contada[club][3:6])
        if suyo == mio:
            continue
        cabeza = (f"{club}: la tabla dice {suyo[0]}-{suyo[1]}-{suyo[2]} (G-E-P) en "
                  f"{pj} partidos y la grilla da {mio[0]}-{mio[1]}-{mio[2]}.")
        # Y ahora la mitad que decide que hacer. Un marcador mal leido mueve
        # SIEMPRE los goles: cambiarle un digito a un partido le cambia el GF o el
        # GC a los dos clubes. Asi que si los goles coinciden exacto y lo unico
        # que se corrio es el resultado, no hay ningun partido que pueda explicarlo
        # y no hay nada que buscar afuera: la que esta mal es la fila.
        if tuple(datos[1:3]) == tuple(contada[club][1:3]):
            fuera.append(
                f"{cabeza} Pero los GOLES coinciden exacto, y un marcador mal "
                f"leido mueve siempre los goles. Ningun partido puede explicar "
                f"esto: la que esta mal es la fila de la tabla, no la grilla. No "
                f"hay nada que ir a buscar afuera")
        else:
            fuera.append(
                f"{cabeza} No es un digito mal leido sino un PARTIDO ENTERO que "
                f"las dos partes dan a distinto ganador. Buscá el otro club "
                f"desviado al reves: el cruce entre los dos donde el arreglo "
                f"cambie el ganador es el sospechoso")
    return fuera


def pj_que_no_coincide(ps: list, texto: str, arts: dict[str, str] | None = None,
                       pagina: str = "") -> list[str]:
    """Los clubes a los que la tabla y la grilla les cuentan distintos partidos.

    `contrastar` se calla cuando el PJ no coincide, y hace bien: compara GOLES, y
    sumarlos sobre conjuntos distintos de partidos daba 38 avisos falsos por
    torneo con reducido. Pero el PJ distinto es un sintoma por derecho propio --
    si un partido quedo a nombre del club de al lado, el PJ de los dos se mueve
    --, y ahi `contrastar` se calla justo cuando habria que hablar.

    LA GUARDA NO ES UN UMBRAL SOBRE LA DIFERENCIA sino sobre CUANTA TABLA SE
    MUEVE: si se desvia mas de la mitad de los clubes comparados, el alcance no
    opina. Esa forma separa las dos causas sin tocar la magnitud. Un club mal
    atribuido mueve uno o dos clubes de veinte; una tabla que cuenta otra cosa --
    la de la fase regular contra una grilla que trae ademas el reducido -- se
    mueve entera y con el mismo delta. Medido sobre las 131 paginas: 67 desvios
    en 8 paginas, de los cuales 56 son cuatro tablas corridas en bloque
    (24 de 24 clubes en -1, 15 de 24 en -14, 14 de 14 en +22, 3 de 3 en +22).
    Con la guarda quedan 11 y no se pierde ninguno de los casos conocidos.
    """
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    fuera = []
    for alcance, publicada in _alcance_de_cada_tabla(texto, arts, ps, pagina):
        contada = sumar([p for p in ps if not alcance or p.llave == alcance])
        comunes = sorted(set(publicada) & set(contada))
        desviados = [c for c in comunes if publicada[c][0] != contada[c][0]]
        if not comunes or len(desviados) * 2 > len(comunes):
            continue
        # Los desvios se agrupan por su DELTA, porque un partido toca a DOS
        # clubes: si dos se corren lo mismo y para el mismo lado, lo que hay es
        # un partido entre esos dos, y decirlo en un solo aviso que los nombra a
        # los dos ahorra la mitad del trabajo al que lo lea. Es la misma idea que
        # el discriminador del cruce de goles: un club solo no puede venir de un
        # partido.
        por_delta: dict[int, list[str]] = {}
        for c in desviados:
            por_delta.setdefault(contada[c][0] - publicada[c][0], []).append(c)
        for delta, clubes in sorted(por_delta.items()):
            donde = alcance or "la pagina"
            if len(clubes) == 2:
                a, b = clubes
                lado = "la grilla" if delta > 0 else "la tabla"
                fuera.append(
                    f"{a} y {b}: a los dos les cuenta {abs(delta)} partido(s) de mas "
                    f"{lado} que la otra parte, en \"{donde}\". Dos clubes corridos lo "
                    f"mismo y para el mismo lado es un PARTIDO ENTRE ELLOS: fijate si "
                    f"{lado} tiene un {a} vs {b} que la otra no")
            else:
                for c in clubes:
                    fuera.append(
                        f"{c}: la tabla de \"{donde}\" le cuenta {publicada[c][0]} "
                        f"partidos y en la grilla tiene {contada[c][0]}, y se desvia "
                        f"entre {len(comunes)} clubes que coinciden. O falta un partido "
                        f"o hay uno a nombre del club equivocado")
    return list(dict.fromkeys(fuera))


def fuera_del_cuadro(ps: list, texto: str, pagina: str = "") -> list[str]:
    """Los clubes que el CUADRO DE LLAVES nombra y que en la grilla no juegan.

    Los otros chequeos de este modulo cruzan la grilla contra la tabla de
    posiciones. Una copa no publica tabla, asi que sus catorce paginas son casi
    toda la region donde ningun chequeo puede opinar: si la grilla se equivoca,
    no hay contra que contrastarla. El cuadro es el segundo testigo que una copa
    SI tiene -- lo escribe otra mano, con otros nombres y en otro formato -- y
    esto lo pone a trabajar.

    Reporta en dos niveles porque son dos cosas distintas:

      * UNO POR CLUB cuando el que falta tiene un HOMONIMO que si juega. Esa es
        la firma de una mala atribucion, y es lo que este chequeo vino a buscar:
        la Primera B 2014, 2015 y 2017-18 escriben "Estudiantes" a secas en el
        cuadro -- que el padron resuelve al de La Plata, un club de Primera --
        mientras la grilla juega Estudiantes (BA).
      * UNO POR NOMBRE que el padron no reconoce. Ese aviso existe desde que
        `clubes_del_cuadro` aprendio a sacarle al cuadro la siembra y las marcas
        con wikilink: sin eso eran 26 nombres, la mayoria basura, y el chequeo
        prefería callarse. Hoy es uno solo y es real.
      * UNO POR PAGINA cuando no hay homonimo. Ahi lo que falta no es un nombre
        sino los PARTIDOS: la Copa Argentina 2019-20 tiene un cuadro de 64 y la
        grilla trae 42 partidos. Es un hueco de completitud conocido y se dice en
        una linea, no en noventa y seis.
    """
    del_cuadro = parser.clubes_del_cuadro(texto)
    if not del_cuadro:
        return []
    juegan = {p.local for p in ps} | {p.visita for p in ps}
    faltan, fuera, desconocidos = [], [], []
    for crudo, articulo in sorted(del_cuadro.items()):
        # Lo que el padron no reconoce YA NO SE SALTEA. Antes si, y la razon era
        # buena: un cuadro trae marcas mezcladas con los clubes -- "t. s." por
        # tiempo suplementario, "(p.)" por penales, "1:" de la siembra -- que no
        # se distinguen por su forma de un club que al padron le falte, y avisar
        # por cada una era peor que callarse. El costo de callarse eran las
        # grafias que SOLO viven en el cuadro: como no entran por ningun partido,
        # `validar.nombres_en_el_padron` tampoco las ve, asi que no las denunciaba
        # nadie.
        #
        # Se resolvio sacando el ruido en vez de tolerarlo, en `clubes_del_cuadro`:
        # la siembra se despega del nombre y las dos marcas que SI llevan wikilink
        # se descartan por su articulo. Con eso, de 26 nombres que el padron no
        # reconocia quedo UNO, y ese uno es un caso de verdad -- "Def. de
        # Belgrano" sin enlace en la Copa Argentina 2015-16, donde juegan los DOS
        # Defensores de Belgrano y el nombre no alcanza para elegir --. Los otros
        # 25 se cerraron: cuatro entraron por su articulo, cuatro por alias y
        # trece eran siembra.
        if not equipos.buscar(crudo, articulo):
            desconocidos.append(
                f"el cuadro de llaves escribe \"{crudo}\" y el padron no lo "
                f"reconoce" + (f" (articulo \"{articulo}\")" if articulo else
                               ", y la pagina no lo enlaza, asi que no hay con que "
                               "resolverlo") + ". O es un club al que le falta el "
                f"alias, o es un nombre ambiguo que solo la pagina puede desatar")
            continue
        club = _canonico(crudo, articulo, pagina)
        if club in juegan:
            continue
        hermanos = sorted(_homonimos_de(club) & juegan)
        if hermanos:
            fuera.append(
                f"el cuadro de llaves nombra a \"{crudo}\" -- que el padron lee "
                f"como {club} -- y en la grilla no juega ni un partido, pero si "
                f"juega {', '.join(hermanos)}. O al padron le falta ese nombre, o "
                f"la grilla le dio los partidos al club de al lado")
        else:
            faltan.append(club)
    fuera = desconocidos + fuera
    if faltan:
        fuera.append(
            f"el cuadro de llaves nombra {len(faltan)} clubes que no juegan ningun "
            f"partido en la grilla ({', '.join(faltan[:6])}"
            f"{', ...' if len(faltan) > 6 else ''}): a la pagina le faltan partidos, "
            f"no nombres")
    return fuera


def _por_wikitabla(bloque: str, arts: dict[str, str],
                   descartadas: list | None = None) -> list[tuple[str, str, tuple[int, int, int]]]:
    """Las filas de una tabla escrita como wikitabla (`{| ... |}`).

    Mismo contrato que `_por_plantillas`: crudas, sin canonizar."""
    m = _WIKITABLA.search(bloque)
    if not m:
        return []
    fuera: list[tuple[str, str, tuple[int, int, int]]] = []
    for fila in m.group(0).split("\n|-"):
        # Las celdas van separadas por `||` o por `\n|`, y arrancan con un `|`
        # suelto que hay que sacar antes de pasarlas por `_celda` -- si no, el
        # separador se lee como parte del contenido y "71" queda como "|71".
        crudas = [c.lstrip("|") for c in fila.replace("\n|", "||").split("||")
                  if c.strip("| \n")]
        celdas = [parser._celda(c)[1] for c in crudas]
        # `[-+]?` y no `-?`: la columna DIF se escribe con signo cuando es
        # POSITIVA -- `||+31` --, y con `-?` esa celda no contaba como numero. La
        # fila perdia una, el corte de las ultimas ocho se corria, y la guarda de
        # coherencia (`gf - gc == dif`) la descartaba entera.
        #
        # Y descartaba justo a los punteros: caen todas y solo las filas con
        # diferencia de gol positiva. En el Argentino A 2010-11 se perdian 8 de
        # 24 -- los ocho mejores de cada zona --, la tabla quedaba en 16 filas y
        # el cruce inventaba un huerfano que no existia. Lo encontro una
        # verificacion adversarial que fue a mirar por que la tabla tenia menos
        # filas que clubes.
        numeros = [c for c in celdas if re.fullmatch(r"[-+]?\d+", c)]
        # El nombre es la ultima celda con letras que no sea un atributo de
        # estilo (`style="background: ..."` tambien tiene letras).
        nombres = [i for i, c in enumerate(celdas)
                   if re.search(r"[A-Za-zÁ-ú]{3}", c) and "=" not in c]
        if len(numeros) < _COLUMNAS or not nombres:
            continue
        pts, pj, pg, pe, pp, gf, gc, dif = (int(x) for x in numeros[-_COLUMNAS:])
        # El articulo se saca del wikilink de la celda CRUDA, igual que en las
        # plantillas. Antes se resolvia por `arts`, un mapa de nombres visibles de
        # toda la pagina, y eso falla dos veces: cuando la tabla y los partidos
        # escriben distinto al mismo club, y cuando la celda trae basura pegada al
        # nombre. La Primera B 2015 pone `[[Club Social y Deportivo Merlo|Deportivo
        # Merlo]] <sup>1</sup>` y el club terminaba llamandose "Deportivo Merlo 1"
        # -- que no esta en el padron, asi que su fila se caia del cruce sin decir
        # nada. Con el wikilink, la llamada al pie queda afuera sola.
        enlace = _EQ_WIKILINK.search(crudas[nombres[-1]])
        if enlace:
            articulo = enlace.group(1)
            club = parser.limpiar(enlace.group(2) or articulo)
        else:
            club = celdas[nombres[-1]]
            articulo = arts.get(club, "")
        if not club:
            continue
        if gf - gc != dif or pg + pe + pp != pj:
            # La fila no cierra sola, asi que no opina. Pero se la anota si
            # alguien pregunta: descartarla en silencio deja a ese club sin
            # arbitro y NADA lo dice -- ni `contrastar` ni `desbalance`, que no
            # pueden opinar sobre una fila que no llego a parsearse.
            if descartadas is not None:
                descartadas.append((club, (pts, pj, pg, pe, pp, gf, gc, dif)))
            continue
        fuera.append((club, articulo, (pj, gf, gc, pg, pe, pp)))
    return fuera


def sumar(ps: list) -> dict[str, tuple[int, int, int, int, int, int]]:
    """{club: (PJ, GF, GC, G, E, P)} sumando los partidos parseados.

    El G-E-P va junto con los goles y no aparte porque son las dos mitades de la
    misma pregunta y tienen que salir del MISMO conjunto de partidos. Sumarlos en
    dos recorridos con dos filtros parecidos es exactamente como se cuelan los
    desvios que despues nadie entiende.
    """
    pj: Counter = Counter()
    gf: Counter = Counter()
    gc: Counter = Counter()
    g: Counter = Counter()
    e: Counter = Counter()
    pp: Counter = Counter()
    for p in ps:
        # Solo la fase regular. La tabla de posiciones cuenta esos partidos y no
        # los del reducido ni los de la promocion, que viven en la misma pagina.
        if p.fase != "zonas" or p.goles_local is None or p.goles_visita is None:
            continue
        pj[p.local] += 1
        pj[p.visita] += 1
        gf[p.local] += p.goles_local
        gc[p.local] += p.goles_visita
        gf[p.visita] += p.goles_visita
        gc[p.visita] += p.goles_local
        if p.goles_local > p.goles_visita:
            g[p.local] += 1
            pp[p.visita] += 1
        elif p.goles_local < p.goles_visita:
            g[p.visita] += 1
            pp[p.local] += 1
        else:
            e[p.local] += 1
            e[p.visita] += 1
    return {c: (pj[c], gf[c], gc[c], g[c], e[c], pp[c]) for c in pj}


_NIVEL_2 = re.compile(r"^==[^=][^\n]*==\s*$", re.M)


def _alcance_de_cada_tabla(texto: str, arts: dict[str, str], ps: list, pagina: str = ""):
    """(alcance, {club: (PJ, GF, GC)}) para cada tabla que publica la pagina.

    El ALCANCE es la seccion de nivel 2 en que vive la tabla, y solo cuando esa
    seccion es tambien una LLAVE de los partidos parseados. Esa condicion es toda
    la regla, y es lo que la hace segura:

      * En una pagina normal las tablas cuelgan de `== Tabla de posiciones ==`,
        que no es la llave de ningun partido, asi que el alcance queda vacio y la
        comparacion es contra el torneo entero, como siempre.
      * En una que reparte por fase -- el Argentino A tiene `== Torneo Apertura ==`
        y `== Torneo Clausura ==`, cada uno con sus tablas y sus once fechas --,
        el alcance coincide con la llave y cada tabla se compara contra los
        partidos de SU fase.

    Sin esto, esas paginas tenian tabla y no tenian arbitro igual: la tabla dice
    once partidos por club y la suma del torneo entero da veintidos, asi que
    `contrastar` se saltea a todos por PJ distinto y no denuncia nada.
    """
    llaves = {p.llave for p in ps if p.fase == "zonas" and p.llave}
    encabezados = [(m.start(), m.group(0).strip().strip("=").strip())
                   for m in _NIVEL_2.finditer(texto)]

    def alcance_en(offset: int) -> str:
        previos = [h for off, h in encabezados if off < offset]
        return previos[-1] if previos and previos[-1] in llaves else ""

    # Las tablas del MISMO alcance se fusionan; no se comparan de a una. Una
    # pagina por zonas publica una tabla por zona y sus clubes son disjuntos: si
    # cada una se comparara sola, sus catorce clubes no coincidirian nunca con
    # los veintiocho de la grilla y el chequeo se callaria.
    #
    # No es hipotetico: separarlas rompio dos avisos que ya existian -- la Copa
    # de la Liga 2023 y la Primera C 2026 perdieron su desbalance --, y por eso
    # el agrupado va antes que la comparacion y no despues.
    por_alcance: dict[str, dict] = {}
    vistas = set()

    def sumar_a(alcance: str, filas: dict) -> None:
        destino = por_alcance.setdefault(alcance, {})
        for club, datos in filas.items():
            if club not in destino or datos[0] > destino[club][0]:
                destino[club] = datos

    for m in re.finditer(r"\{\|.*?\n\|\}", texto, re.S):
        if m.group(0) in vistas or not _declara_ser_tabla_de_posiciones(m.group(0)):
            continue
        previos = [h for off, h in encabezados if off < m.start()]
        if previos and _SECCION_AGREGADA.search(previos[-1]):
            continue
        vistas.add(m.group(0))
        sumar_a(alcance_en(m.start()),
                {_canonico(n, a, pagina): d for n, a, d in _por_wikitabla(m.group(0), arts)})
    # Y las que entran por el titulo de la seccion, que incluyen el formato de
    # plantillas. Ahi el alcance sale igual, del nivel 2 que las contiene.
    for m in _ENCABEZADO.finditer(texto):
        sig = _CUALQUIER_ENCABEZADO.search(texto, m.end())
        bloque = texto[m.end():sig.start()] if sig else texto[m.end():]
        sumar_a(alcance_en(m.start()),
                {_canonico(n, a, pagina): d for n, a, d in _filas(bloque, arts)})
    for alcance, filas in por_alcance.items():
        if filas:
            yield alcance, filas


def _propios_de(ps: list, alcance: str) -> dict:
    """Los partidos que le tocan a una tabla de ese alcance, ya sumados.

    Existe para que `contrastar` y `resultados_que_no_coinciden` no puedan mirar
    conjuntos distintos: preguntan cosas distintas -- cuantos goles y quien gano
    -- sobre EL MISMO conjunto, y si el recorte se escribe dos veces, tarde o
    temprano se escriben distinto.
    """
    return sumar([p for p in ps if not alcance or p.llave == alcance])


def contrastar(ps: list, texto: str, arts: dict[str, str] | None = None,
               pagina: str = "") -> list[str]:
    """Los clubes cuyos totales no coinciden con la tabla de la pagina.

    Solo se comparan los clubes que estan en las dos partes. Un club de la tabla
    que no aparece en ningun partido no se denuncia: puede ser que la pagina
    liste la tabla de una zona y los partidos de otra, y eso no es un error del
    parseo.
    """
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    # Cada tabla se compara contra los partidos DE SU ALCANCE, y no contra el
    # torneo entero. Ver `_alcance_de_cada_tabla`: cuando la pagina reparte sus
    # tablas por fase -- una por `== Torneo Apertura ==` y otra por
    # `== Torneo Clausura ==` --, el PJ de la tabla es de once y el de nuestra
    # suma de veintidos, y el cruce se saltea TODOS los clubes por no coincidir.
    # Es lo que dejaba sin arbitro al Argentino A 2005-06 aun despues de que sus
    # tablas se encontraran.
    publicada, contada = {}, {}
    for alcance, filas in _alcance_de_cada_tabla(texto, arts, ps, pagina):
        propios = _propios_de(ps, alcance)
        for club, datos in filas.items():
            if club not in publicada or datos[0] > publicada[club][0]:
                publicada[club] = datos
                if club in propios:
                    contada[club] = propios[club]
    if not publicada:
        return []
    # Cuantos clubes se desvian en total. Sirve para decir DE QUE LADO esta el
    # error, que es la mitad util del aviso -- ver `_de_quien_es_la_culpa`.
    desviados = sum(1 for c, (pj, gf, gc, *_) in publicada.items()
                    if c in contada and contada[c][0] == pj
                    and contada[c][1:3] != (gf, gc))
    fuera = []
    for club, (pj, gf, gc, *_) in sorted(publicada.items()):
        if club not in contada or correcciones.revisado(pagina, club):
            continue
        pj2, gf2, gc2 = contada[club][:3]
        # Si no coincide la CANTIDAD de partidos, las dos partes no estan
        # hablando del mismo conjunto -- una tabla por zona contra los partidos
        # de todas, o una temporada con reducido -- y comparar goles no significa
        # nada. La contradiccion de verdad es: misma cantidad de partidos y
        # distintos goles. Ahi si, uno de los dos numeros esta mal.
        if pj != pj2:
            continue
        if (gf, gc) != (gf2, gc2):
            fuera.append(f"{club}: la tabla dice GF{gf} GC{gc} en {pj} partidos y "
                         f"sumandolos dan GF{gf2} GC{gc2}. "
                         + _de_quien_es_la_culpa(desviados))
    return fuera


def desbalance(ps: list, texto: str, arts: dict[str, str] | None = None,
               pagina: str = "") -> list[str]:
    """La tabla publicada que no cierra CONSIGO MISMA: suma de GF != suma de GC.

    Todo gol convertido es un gol recibido por alguien. En una tabla que cubre un
    conjunto cerrado de partidos, la columna GF y la columna GC tienen que sumar
    lo mismo, siempre. No es una comparacion contra nuestra grilla ni contra
    ninguna otra fuente: es la tabla contradiciendose sola. Cuando salta, la
    equivocada es ella, y no hay tercera fuente que discutirlo.

    Es el complemento exacto de `contrastar`. Aquel dice QUE club se desvia pero
    no puede probar de que lado esta el error sin razonar sobre parejas; este no
    dice quien, pero lo que dice lo demuestra. Juntos cerraron cuatro de los cinco
    torneos con un solo club desviado -- Clausura 2005, Final 2013, Copa de la
    Liga 2023 y Primera B 2017-18 -- donde el desbalance resulto ser, clavado, el
    delta del club desviado.

    El caso que NO agarra es igual de instructivo: cuando el error de tipeo baja
    los dos numeros de la misma fila (Platense en la B Nacional 2009-10 va GF39
    GC40 contra 40 y 41), las dos columnas se corren juntas y el balance
    sobrevive. Este chequeo es ciego a esos, y esta bien que lo sea: prefiere no
    opinar antes que opinar de mas.

    CUANDO NO OPINA
    ---------------
    Solo mide si la tabla reclama EXACTAMENTE el mismo conjunto de partidos que
    la grilla: los mismos clubes de los dos lados y el mismo PJ para cada uno.
    Sin esa guarda el chequeo seria un generador de ruido, porque hay tres
    maneras normales de que una tabla no balancee sin estar mal:

      - una fila que no paso el filtro de `_por_wikitabla` (no cierra sola, se
        descarta) deja sus goles afuera y descuadra el total;
      - una zona que juega partidos interzonales -- la Copa de la Liga 2023 es
        justo asi, trece fechas adentro de la zona y una cruzada -- reparte goles
        con clubes que su tabla no lista;
      - una tabla de una zona junto a los partidos de todas.
    """
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    # Tabla por tabla y contra los partidos de SU alcance, igual que `contrastar`.
    # Sumando la pagina entera, una que reparte por fase nunca cuadra -- la tabla
    # dice once partidos y la suma da veintidos -- y el chequeo se calla siempre.
    fuera = []
    for alcance, publicada in _alcance_de_cada_tabla(texto, arts, ps, pagina):
        contada = sumar([p for p in ps if not alcance or p.llave == alcance])
        if not publicada or set(publicada) != set(contada):
            continue
        if any(publicada[c][0] != contada[c][0] for c in publicada):
            continue
        gf = sum(v[1] for v in publicada.values())
        gc = sum(v[2] for v in publicada.values())
        if gf != gc:
            fuera.append(_texto_del_desbalance(gf, gc, alcance))
    # Una misma tabla puede entrar por los dos caminos -- el titulo y las
    # columnas -- y entonces el aviso saldria repetido.
    return list(dict.fromkeys(fuera))


def _texto_del_desbalance(gf: int, gc: int, alcance: str) -> str:
    n = abs(gf - gc)
    sobra = "gol" if n == 1 else "goles"
    # De que lado sobran, dicho por lo que le falta al otro lado. Es la mitad
    # util del aviso: "sobran goles en contra" quiere decir que hay goles que
    # alguien recibio y que NINGUN club se atribuye haber convertido.
    quien = ("a favor que ningun club declara haber recibido" if gf > gc
             else "en contra que ningun club declara haber convertido")
    return (f"{alcance + ': ' if alcance else ''}"
            f"la tabla suma GF{gf} y GC{gc} sobre los mismos partidos, y tienen que dar "
            f"igual: sobra{'' if n == 1 else 'n'} {n} {sobra} {quien}. "
            f"La tabla se contradice sola, sin necesidad de cruzarla contra nada")


def _de_quien_es_la_culpa(desviados: int) -> str:
    """De que lado esta el error, deducido de cuantos clubes se desvian.

    Un marcador mal leido toca siempre a DOS clubes: si a uno le sobra un gol a
    favor, al rival le sobra uno en contra. Asi que un club solo, desviado y sin
    pareja, no puede venir de un partido -- tiene que ser su fila de la tabla.

    Es lo que paso con Platense en la B Nacional 2009-10: la tabla le pone
    GF39 GC40 y sus 38 partidos dan 40 y 41, con las otras diecinueve filas
    cerrando perfecto. El error de tipeo es doble y por eso es tan dificil de
    ver: al estar los dos numeros bajos por uno, quedan intactos la diferencia
    de gol, los puntos y el ganados-empatados-perdidos, y hasta la suma de toda
    la liga sigue dando GF total == GC total.
    """
    if desviados == 1:
        return ("Es el unico club desviado, y un marcador mal leido tocaria a dos: "
                "lo mas probable es que la fila de la tabla este mal transcripta")
    return ("Hay mas clubes desviados, asi que puede venir de un partido mal leido. "
            "OJO: que exista un unico ajuste de un gol que haga cerrar todo NO "
            "alcanza para corregirlo. Se probaron seis contra la prensa y la tabla "
            "tenia razon en cuatro; en los otros dos (Primera C 2026 y B Nacional "
            "2012-13) la cronica confirma el marcador de Wikipedia y la equivocada "
            "era ella. Buscar una cronica que nombre a los goleadores")

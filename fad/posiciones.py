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

from fad import equipos, parser

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


def _por_plantillas(bloque: str, arts: dict[str, str]) -> dict[str, tuple[int, int, int]]:
    """Las filas escritas como `{{Tabla de posiciones equipo|...}}`."""
    fuera = {}
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
            club = parser.limpiar(eq.group(1))
            articulo = arts.get(club, "")
        if not club:
            continue
        fuera[equipos.canonizar(club, articulo)] = (
            nums["g"] + nums["e"] + nums["p"], nums["gf"], nums["gc"])
    return fuera


def tabla(texto: str, arts: dict[str, str] | None = None) -> dict[str, tuple[int, int, int]]:
    """{club canonico: (PJ, GF, GC)} segun las tablas que publica la pagina.

    Se leen TODAS las secciones "Tabla de posiciones" y se unen. Vacio si no hay.

    Cuando un club aparece en dos, gana la que tiene mas partidos. Es lo que
    separa los dos motivos por los que una pagina trae varias: si son zonas
    distintas los clubes son disjuntos y no se pisan, y si es la "parcial de la
    primera rueda" contra la final, la parcial tiene la mitad de los partidos y
    pierde. Antes esto se resolvia leyendo solo la primera tabla, que arreglaba
    la parcial y rompia las zonas.
    """
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    fuera: dict[str, tuple[int, int, int]] = {}
    for bloque in _bloques(texto):
        filas = _por_plantillas(bloque, arts) or _por_wikitabla(bloque, arts)
        for club, datos in filas.items():
            if club not in fuera or datos[0] > fuera[club][0]:
                fuera[club] = datos
    return fuera


def _por_wikitabla(bloque: str, arts: dict[str, str]) -> dict[str, tuple[int, int, int]]:
    """Las filas de una tabla escrita como wikitabla (`{| ... |}`)."""
    m = _WIKITABLA.search(bloque)
    if not m:
        return {}
    fuera: dict[str, tuple[int, int, int]] = {}
    for fila in m.group(0).split("\n|-"):
        # Las celdas van separadas por `||` o por `\n|`, y arrancan con un `|`
        # suelto que hay que sacar antes de pasarlas por `_celda` -- si no, el
        # separador se lee como parte del contenido y "71" queda como "|71".
        celdas = [parser._celda(c.lstrip("|"))[1]
                  for c in fila.replace("\n|", "||").split("||") if c.strip("| \n")]
        numeros = [c for c in celdas if re.fullmatch(r"-?\d+", c)]
        # El nombre es la ultima celda con letras que no sea un atributo de
        # estilo (`style="background: ..."` tambien tiene letras).
        nombres = [c for c in celdas if re.search(r"[A-Za-zÁ-ú]{3}", c) and "=" not in c]
        if len(numeros) < _COLUMNAS or not nombres:
            continue
        pts, pj, pg, pe, pp, gf, gc, dif = (int(x) for x in numeros[-_COLUMNAS:])
        if gf - gc != dif or pg + pe + pp != pj:
            continue                       # la fila no cierra sola: no opina
        fuera[equipos.canonizar(nombres[-1], arts.get(nombres[-1], ""))] = (pj, gf, gc)
    return fuera


def sumar(ps: list) -> dict[str, tuple[int, int, int]]:
    """{club: (PJ, GF, GC)} sumando los partidos parseados."""
    pj: Counter = Counter()
    gf: Counter = Counter()
    gc: Counter = Counter()
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
    return {c: (pj[c], gf[c], gc[c]) for c in pj}


def contrastar(ps: list, texto: str, arts: dict[str, str] | None = None) -> list[str]:
    """Los clubes cuyos totales no coinciden con la tabla de la pagina.

    Solo se comparan los clubes que estan en las dos partes. Un club de la tabla
    que no aparece en ningun partido no se denuncia: puede ser que la pagina
    liste la tabla de una zona y los partidos de otra, y eso no es un error del
    parseo.
    """
    publicada = tabla(texto, arts)
    if not publicada:
        return []
    contada = sumar(ps)
    # Cuantos clubes se desvian en total. Sirve para decir DE QUE LADO esta el
    # error, que es la mitad util del aviso -- ver `_de_quien_es_la_culpa`.
    desviados = sum(1 for c, (pj, gf, gc) in publicada.items()
                    if c in contada and contada[c][0] == pj and contada[c][1:] != (gf, gc))
    fuera = []
    for club, (pj, gf, gc) in sorted(publicada.items()):
        if club not in contada:
            continue
        pj2, gf2, gc2 = contada[club]
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


def desbalance(ps: list, texto: str, arts: dict[str, str] | None = None) -> list[str]:
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
    publicada = tabla(texto, arts)
    if not publicada:
        return []
    contada = sumar(ps)
    if set(publicada) != set(contada):
        return []
    if any(publicada[c][0] != contada[c][0] for c in publicada):
        return []
    gf = sum(v[1] for v in publicada.values())
    gc = sum(v[2] for v in publicada.values())
    if gf == gc:
        return []
    n = abs(gf - gc)
    sobra = "gol" if n == 1 else "goles"
    # De que lado sobran, dicho por lo que le falta al otro lado. Es la mitad
    # util del aviso: "sobran goles en contra" quiere decir que hay goles que
    # alguien recibio y que NINGUN club se atribuye haber convertido.
    quien = ("a favor que ningun club declara haber recibido" if gf > gc
             else "en contra que ningun club declara haber convertido")
    return [f"la tabla suma GF{gf} y GC{gc} sobre los mismos partidos, y tienen que dar "
            f"igual: sobra{'' if n == 1 else 'n'} {n} {sobra} {quien}. "
            f"La tabla se contradice sola, sin necesidad de cruzarla contra nada"]


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

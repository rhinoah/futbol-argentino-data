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
Una fila solo se usa si cierra CONSIGO MISMA: `GF - GC == DIF` y
`PG + PE + PP == PJ`. Una tabla mal tipeada no puede desmentir a nadie, y esas
dos restas la delatan sin costo. Si la pagina no trae tabla, o la trae partida
por zonas y los partidos no, este modulo no dice nada: callarse es correcto,
inventar un aviso no.
"""
from __future__ import annotations

import re
from collections import Counter

from fad import equipos, parser

# El titulo de la seccion cambia de pagina en pagina ("Tabla de posiciones",
# "Tabla de posiciones final"). Entre el titulo y la tabla puede haber un
# `<center>`, asi que se acepta cualquier cosa que no abra la tabla.
_SECCION = re.compile(r"==+\s*Tabla de posiciones[^=]*==+[^{]*(\{\|.*?\n\|\})", re.S | re.I)

# Pts, PJ, PG, PE, PP, GF, GC, DIF: las ocho columnas numericas de la fila.
_COLUMNAS = 8


def tabla(texto: str, arts: dict[str, str] | None = None) -> dict[str, tuple[int, int, int]]:
    """{club canonico: (PJ, GF, GC)} segun la tabla que publica la pagina.

    Devuelve solo las filas que cierran consigo mismas. Vacio si no hay tabla.
    """
    m = _SECCION.search(texto)
    if not m:
        return {}
    arts = arts if arts is not None else parser.articulos_de_la_pagina(texto)
    fuera: dict[str, tuple[int, int, int]] = {}
    for fila in m.group(1).split("\n|-"):
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
                         f"sumandolos dan GF{gf2} GC{gc2}")
    return fuera

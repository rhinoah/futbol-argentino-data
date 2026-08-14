#!/usr/bin/env python3
"""Tests del cruce contra la tabla de posiciones.

Este chequeo es el unico del repo que puede decidir cual de dos fuentes tiene
razon sobre un marcador. Por eso lo que mas importa probar es CUANDO SE CALLA:
un arbitro que opina de mas es peor que no tener arbitro.
"""
from __future__ import annotations

from fad import posiciones
from fad.parser import Partido


def fila(pos, club, pts, pj, pg, pe, pp, gf, gc):
    return (f"|- style=\"text-align:center\"\n"
            f"||'''{pos}º'''||align=\"left\"|[[{club}]]\n"
            f"||'''{pts}'''||{pj}||{pg}||{pe}||{pp}||{gf}||{gc}||{gf - gc}")


def pagina(*filas, titulo="Tabla de posiciones"):
    return (f"== {titulo} ==\n<center>\n"
            "{| class=\"wikitable sortable\"\n"
            "|- style=\"background:#dddddd;\"\n"
            "! Pos\n! Equipo\n! Pts\n! PJ\n! PG\n! PE\n! PP\n! GF\n! GC\n! DIF\n"
            + "\n".join(filas) + "\n|}")


def zona(local, visita, gl, gv):
    return Partido(fecha="2010-01-01", local=local, visita=visita, goles_local=gl,
                   goles_visita=gv, fase="zonas", jornada="Fecha 1")


# --------------------------------------------------------------------------
# leer la tabla
# --------------------------------------------------------------------------
def test_lee_la_tabla():
    t = posiciones.tabla(pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1)))
    assert t == {"Boca Juniors": (2, 3, 1)}


def test_el_center_entre_el_titulo_y_la_tabla_no_molesta():
    """Varias paginas meten un `<center>` en el medio. Pidiendo la tabla pegada
    al titulo, la de la B Nacional 2007-08 no se encontraba."""
    assert posiciones.tabla(pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1)))


def test_el_titulo_puede_decir_final():
    t = posiciones.tabla(pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1),
                                titulo="Tabla de posiciones final"))
    assert t == {"Boca Juniors": (2, 3, 1)}


def test_una_fila_que_no_cierra_sola_no_se_usa():
    """Una tabla mal tipeada no puede desmentir a nadie. `GF - GC == DIF` y
    `PG + PE + PP == PJ` la delatan sin costo."""
    rota = (f"|-\n||'''1º'''||align=\"left\"|[[Boca Juniors]]\n"
            f"||'''4'''||2||1||1||0||3||1||99")          # DIF dice 99 y es 2
    assert posiciones.tabla(pagina(rota)) == {}


def test_una_pagina_sin_tabla_no_devuelve_nada():
    assert posiciones.tabla("== Resultados ==\nnada por aca") == {}


# --------------------------------------------------------------------------
# contrastar: sobre todo, cuando se calla
# --------------------------------------------------------------------------
def test_cuando_los_goles_cierran_no_dice_nada():
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1),
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 3))
    assert posiciones.contrastar(ps, p) == []


def test_un_gol_de_diferencia_se_denuncia():
    """La contradiccion de verdad: los mismos partidos, distintos goles."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 4, 1),      # dice 4, suman 3
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 3))
    avisos = posiciones.contrastar(ps, p)
    assert len(avisos) == 1 and "Boca Juniors" in avisos[0]


def test_si_no_coinciden_los_partidos_jugados_se_calla():
    """La tabla cuenta la fase regular; la pagina trae ademas el reducido y la
    promocion. Comparando goles sobre conjuntos distintos salian 38 avisos
    falsos, uno por cada club de un torneo con reducido."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 9, 9))       # PJ2 contra PJ1
    assert posiciones.contrastar(ps, p) == []


def test_los_partidos_de_eliminacion_no_cuentan():
    """Los del reducido estan en la misma pagina y no en la tabla.

    El caso esta armado para que se note: la tabla dice DOS partidos, y hay uno
    de zona y uno de eliminacion. Sumando los dos, el PJ coincide y la
    comparacion de goles se hace -- y denuncia. Contando solo el de zona, el PJ
    no coincide y el modulo se calla, que es lo correcto."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1),
          Partido(fecha="2010-06-01", local="Boca Juniors", visita="River Plate",
                  goles_local=5, goles_visita=0, fase="eliminacion", jornada="Final")]
    p = pagina(fila(1, "Boca Juniors", 6, 2, 2, 0, 0, 8, 0))
    assert posiciones.contrastar(ps, p) == []


def test_un_club_de_la_tabla_que_no_jugo_no_se_denuncia():
    """Puede ser la tabla de otra zona. No opinar es lo correcto."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1)]
    p = pagina(fila(1, "Racing Club", 4, 2, 1, 1, 0, 3, 1))
    assert posiciones.contrastar(ps, p) == []


# --------------------------------------------------------------------------
# los nueve arbitrados
# --------------------------------------------------------------------------
def test_los_marcadores_arbitrados_estan_justificados():
    from fad import correcciones
    for m in correcciones.MARCADORES:
        assert len(m.porque) > 80, f"{m.jornada} {m.local}: la evidencia es muy flaca"
        assert "tabla de posiciones" in m.porque, "el arbitro tiene que quedar nombrado"


def test_el_arbitraje_no_le_da_siempre_la_razon_al_mismo():
    """Que el metodo mide algo se ve en que no contesta siempre lo mismo. Si
    todos dijeran worldfootball, seria indistinguible de haberla elegido."""
    from fad import correcciones
    sin_cambio = [m for m in correcciones.MARCADORES if m.debe == m.dice]
    assert sin_cambio, "ninguno le da la razon a Wikipedia: sospechoso"


def test_los_arbitrados_se_pueden_buscar_por_pagina():
    from fad import correcciones
    clave = correcciones.arbitrados("Campeonato de Primera B Nacional 2010-11")
    assert ("Fecha 22", "San Martín (T)", "Patronato") in clave
    assert correcciones.arbitrados("Una Pagina Cualquiera") == set()

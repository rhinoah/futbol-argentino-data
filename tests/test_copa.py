#!/usr/bin/env python3
"""Tests del formato de copa: una tabla por ronda.

Es el TERCER formato de la misma Wikipedia, y no comparte casi nada con los otros
dos. Lo peligroso es que se parece lo suficiente como para que el parser de liga
corra sin fallar y devuelva cero partidos, que se confunde facil con "el torneo
todavia no empezo".
"""
from __future__ import annotations

import pytest

from fad import parser
from tests.conftest import COPA


@pytest.fixture
def copa():
    return parser.partidos_de_rondas(COPA, 2026, "Copa Argentina")


# --------------------------------------------------------------------------
def test_saca_los_partidos_jugados(copa):
    assert len(copa) == 4
    assert all(p.fase == "eliminacion" for p in copa)


def test_bug_el_sombreado_de_fila_no_corre_las_columnas(copa):
    """La Copa sombrea una fila de cada dos, y ese `bgcolor` va pegado al `|-`.

    Contarlo como celda corre todas las columnas un lugar. No falla: la fila
    corrida no tiene un marcador donde el parser lo busca y se descarta sola,
    asi que se perdia EXACTAMENTE la mitad de los partidos -- 16 de 32
    treintaidosavos, 8 de 16 dieciseisavos. Una perdida del 50% que no hace ruido.
    """
    t32 = [p for p in copa if p.jornada == "Treintaidosavos"]
    assert len(t32) == 3, "faltan las filas con bgcolor"
    assert {p.local for p in t32} == {"Lanús", "Argentinos Juniors",
                                      "Gimnasia y Esgrima (LP)"}


def test_las_celdas_van_separadas_por_dos_barras(copa):
    """Las tablas de liga ponen una celda por linea; esta mete la fila entera en
    un renglon. Un parser que solo conozca `\\n|` lee la fila como una sola celda."""
    lanus = [p for p in copa if p.local == "Lanús"][0]
    assert (lanus.goles_local, lanus.goles_visita) == (4, 1)
    assert lanus.visita == "Sarmiento (LB)"
    assert lanus.estadio == "Ciudad de Caseros"
    assert lanus.fecha == "2026-01-18"


def test_bug_los_penales_sobreviven_a_la_limpieza(copa):
    """`{{small|(5)}} 1 - 1 {{small|(6)}}`: la tanda vive DENTRO de una plantilla,
    y `limpiar` borra las plantillas. Sacandolos despues de limpiar, el partido
    queda 1-1 y la definicion desaparece sin que nada falle."""
    p = [p for p in copa if p.local == "Argentinos Juniors"][0]
    assert (p.goles_local, p.goles_visita) == (1, 1)
    assert (p.penales_local, p.penales_visita) == (5, 6)


def test_el_parentesis_de_la_copa_no_es_el_de_las_plantillas():
    """LA trampa. El mismo parentesis significa lo contrario en cada formato:

      * `{{Partido|resultado = 2:0''' (1:0)}}`  -> (1:0) es el ENTRETIEMPO
      * `{{small|(5)}} 1 - 1 {{small|(6)}}`      -> (5) y (6) son los PENALES

    Se distinguen por lo que hay adentro: dos numeros con `:` es el primer
    tiempo, uno solo es la tanda de ese equipo.
    """
    assert parser._penales("{{small|(5)}} 1 - 1 {{small|(6)}}") == (5, 6)
    assert parser._penales("2:0''' (1:0)") is None
    assert parser._penales("0 - 3") is None


def test_penales_tambien_con_la_etiqueta_html():
    assert parser._penales("<small>(3)</small> 0 - 0 <small>(4)</small>") == (3, 4)


def test_bug_nowrap_se_desenvuelve_y_no_se_borra(copa):
    """`{{nowrap|X}}` es formato, pero adentro esta el dato. Borrandola junto con
    las demas plantillas desaparecia el equipo entero."""
    assert any(p.local == "Gimnasia y Esgrima (LP)" for p in copa)


def test_una_fila_sin_marcador_no_entra(copa):
    """La ronda esta en curso: la fila existe pero todavia no hay resultado."""
    d16 = [p for p in copa if p.jornada == "Dieciseisavos"]
    assert len(d16) == 1
    assert d16[0].local == "Ferrocarril Midland"


def test_la_seccion_termina_en_el_proximo_titulo(copa):
    """Despues de la ultima ronda sigue "Goleadores", con su tabla. Sin cortar en
    el titulo, esa tabla entra como si fuera una ronda mas -- y la fila de un
    goleador con "7 - 0" pasa por un partido."""
    assert not any(p.goles_local == 7 for p in copa)
    assert {p.jornada for p in copa} == {"Treintaidosavos", "Dieciseisavos"}


def test_la_ronda_sale_del_titulo(copa):
    assert [p.jornada for p in copa].count("Treintaidosavos") == 3
    assert [p.jornada for p in copa].count("Dieciseisavos") == 1


# --------------------------------------------------------------------------
# el despacho por formato
# --------------------------------------------------------------------------
def test_el_formato_lo_dice_el_catalogo_y_no_se_adivina():
    """El parser de liga sobre una pagina de copa no falla: devuelve cero
    partidos, que se confunde con "todavia no empezo el torneo"."""
    assert parser.partidos(COPA, 2026, "X", formato="liga") == []
    assert len(parser.partidos(COPA, 2026, "X", formato="copa")) == 4


def test_la_ronda_de_las_llaves_de_liga_sale_del_titulo():
    """Las plantillas {{Partido}} no dicen a que ronda pertenecen; lo unico que
    lo dice es bajo que titulo estan. Sin la ronda, `cadena_de_llaves` no puede
    ordenar el cuadro."""
    texto = """
=== Octavos de final ===
{{Partido
|local = Boca Juniors
|resultado = 2:0
|visita = Instituto
|fecha = 1 de mayo
}}

=== Semifinal ===
{{Partido
|local = Boca Juniors
|resultado = 1:0
|visita = Racing Club
|fecha = 10 de mayo
}}
"""
    ps = parser.partidos_de_plantillas(texto, 2026, "X")
    assert [p.jornada for p in ps] == ["Octavos", "Semifinales"]


def test_semifinal_y_semifinales_son_la_misma_ronda():
    """Si quedan como dos rondas distintas, el orden del cuadro se parte al medio."""
    assert parser._nombre_de_ronda("Semifinal") == "Semifinales"
    assert parser._nombre_de_ronda("Semifinales") == "Semifinales"

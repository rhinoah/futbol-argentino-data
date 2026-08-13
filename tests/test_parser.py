#!/usr/bin/env python3
"""Tests del parser.

Casi todos apuntan a lo mismo: que el parser falle en vez de mentir. Cada uno de
los de mas abajo con nombre `test_bug_*` corresponde a un error que efectivamente
estuvo en el codigo y que ninguna excepcion delataba.
"""
from __future__ import annotations

import pytest

from fad import parser
from tests.conftest import LLAVES, TABLA


# --------------------------------------------------------------------------
# limpieza
# --------------------------------------------------------------------------
@pytest.mark.parametrize("crudo, limpio", [
    ("[[Club Atlético Unión|Unión]]", "Unión"),
    ("[[Boca Juniors]]", "Boca Juniors"),
    ("'''River Plate'''", "River Plate"),
    ("Talleres<ref name=x>nota</ref>", "Talleres"),
    ("Lanús<ref name=y/>", "Lanús"),
    ("{{bandera|ARG}} Racing", "Racing"),
    ("Vélez<br/>Sarsfield", "Vélez Sarsfield"),
    ("  Huracán   ", "Huracán"),
])
def test_limpiar(crudo, limpio):
    assert parser.limpiar(crudo) == limpio


# --------------------------------------------------------------------------
# celdas y rowspan
# --------------------------------------------------------------------------
@pytest.mark.parametrize("celda, filas, valor", [
    ("Boca Juniors", 1, "Boca Juniors"),
    ("rowspan=3|22 de enero", 3, "22 de enero"),
    ('rowspan="2"|21:00', 2, "21:00"),
    ("bgcolor=#d0e7ff|'''River Plate", 1, "River Plate"),
    ("width=21%|Local", 1, "Local"),
])
def test_celda(celda, filas, valor):
    assert parser._celda(celda) == (filas, valor)


def test_celda_no_confunde_contenido_con_atributos():
    """Un `|` dentro del contenido no es el separador de atributos.

    `[[Club Atlético Unión|Unión]]` tiene una barra y no lleva atributos: si se
    corta ahi, el equipo pasa a llamarse "Unión]]".
    """
    assert parser._celda("[[Club Atlético Unión|Unión]]") == (1, "Unión")


# --------------------------------------------------------------------------
# fechas
# --------------------------------------------------------------------------
@pytest.mark.parametrize("texto, iso", [
    ("22 de enero", "2026-01-22"),
    ("3 de marzo", "2026-03-03"),
    ("17 de Mayo", "2026-05-17"),
    ("9 de setiembre", "2026-09-09"),
    ("9 de septiembre", "2026-09-09"),
    ("1 de diciembre", "2026-12-01"),
])
def test_a_iso(texto, iso):
    assert parser.a_iso(texto, 2026) == iso


@pytest.mark.parametrize("basura", ["", "a confirmar", "32 de tarzo", "manana"])
def test_a_iso_no_inventa(basura):
    assert parser.a_iso(basura, 2026) == ""


# --------------------------------------------------------------------------
# marcadores
# --------------------------------------------------------------------------
@pytest.mark.parametrize("texto, goles", [
    ("2 - 1", (2, 1)), ("0-0", (0, 0)), ("1:1", (1, 1)), ("10 - 0", (10, 0)),
])
def test_marcador(texto, goles):
    assert parser._marcador(texto) == goles


@pytest.mark.parametrize("texto", ["", "vs", "a jugarse", "- 1", "Susp."])
def test_marcador_sin_partido(texto):
    assert parser._marcador(texto) is None


# --------------------------------------------------------------------------
# la tabla de la fase de grupos
# --------------------------------------------------------------------------
def test_tabla_completa():
    ps = parser.partidos_de_tabla(TABLA, 2026, "Apertura")
    assert len(ps) == 4
    assert all(p.fase == "zonas" for p in ps)


def test_tabla_lee_los_campos():
    union = parser.partidos_de_tabla(TABLA, 2026, "Apertura")[0]
    assert (union.local, union.visita) == ("Unión", "Platense")
    assert (union.goles_local, union.goles_visita) == (0, 0)
    assert union.fecha == "2026-01-23"
    assert union.hora == "20:00"
    assert union.estadio == "15 de Abril"
    assert (union.zona, union.jornada) == ("Zona A", "Fecha 1")


def test_bug_rowspan_no_corre_las_columnas():
    """La 2a fila trae 5 celdas porque hereda la fecha por `rowspan`.

    Un parser que asuma 6 celdas por fila lee el estadio como fecha y la hora
    como estadio, sin fallar. Boca-Instituto es esa fila.
    """
    boca = parser.partidos_de_tabla(TABLA, 2026, "Apertura")[1]
    assert boca.local == "Boca Juniors"
    assert boca.estadio == "La Bombonera"
    assert boca.fecha == "2026-01-23"       # heredada de la fila de arriba
    assert boca.hora == "22:00"


def test_bug_etiqueta_no_se_corre_entre_tablas():
    """El interzonal esta en la Fecha 1, aunque el `!colspan=6|Fecha 2` de la
    tabla siguiente aparezca sin un `|-` que lo separe de su ultima fila.

    Este fue el bug: los 30 interzonales del Apertura 2026 quedaron anotados una
    fecha adelante. Todo lo demas de la fila estaba bien.
    """
    ps = parser.partidos_de_tabla(TABLA, 2026, "Apertura")
    inter = [p for p in ps if p.zona == "Interzonal"]
    assert len(inter) == 1
    assert inter[0].local == "Aldosivi"
    assert inter[0].jornada == "Fecha 1"

    siguiente = [p for p in ps if p.jornada == "Fecha 2"]
    assert [p.local for p in siguiente] == ["Platense"]


TABLA_SIN_HORA = """
{|class="wikitable"
!colspan=5|Fecha 1
|-
!colspan=5|Zona A
|-
!Local
!Resultado
!Visitante
!Estadio
!Fecha
|-
|Boca Juniors
|2 - 1
|Instituto
|La Bombonera
|23 de enero
|}
"""


def test_el_cierre_de_tabla_no_se_cuela_como_dato():
    """El `|}` que cierra la tabla no es una celda.

    En las tablas de hoy sobra siempre, porque la fila tiene las seis columnas y
    el `}` queda de mas. Pero las temporadas viejas se publicaron SIN la columna
    Hora, y ahi ese `}` cae justo en la primera columna que nadie lleno. No
    falla: escribe un partido que se jugo a las `}`.
    """
    p = parser.partidos_de_tabla(TABLA_SIN_HORA, 2026, "Apertura")[0]
    assert p.estadio == "La Bombonera"
    assert p.fecha == "2026-01-23"
    assert p.hora == "", f"se colo el cierre de tabla: {p.hora!r}"


TABLA_ROWSPAN_PASADO = """
{|class="wikitable"
!colspan=6|Fecha 1
|-
!colspan=6|Zona A
|-
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Boca Juniors
|2 - 1
|Instituto
|La Bombonera
|rowspan=4|23 de enero
|20:00
|-
!colspan=6|Zona B
|-
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Racing Club
|0 - 0
|Tigre
|Cilindro
|26 de enero
|18:00
|}
"""


def test_un_rowspan_no_cruza_de_una_seccion_a_otra():
    """Un `rowspan=4` con dos filas debajo es markup roto, y Wikipedia lo tiene.

    Sin cortar el arrastre en cada encabezado, esa fecha pendiente le gana a la
    celda que la fila siguiente SI trae, y toda la Zona B queda fechada con el
    dia de la Zona A. El marcador y los equipos, bien; solo la fecha, mal.
    """
    ps = parser.partidos_de_tabla(TABLA_ROWSPAN_PASADO, 2026, "Apertura")
    racing = [p for p in ps if p.local == "Racing Club"][0]
    assert racing.fecha == "2026-01-26", "arrastro la fecha de la seccion anterior"
    assert racing.hora == "18:00"


def test_bloque_interzonal_no_hereda_la_zona():
    """"Interzonal" no empieza con "Zona": la primera version del parser no lo
    reconocia como etiqueta y esos partidos heredaban la zona anterior."""
    ps = parser.partidos_de_tabla(TABLA, 2026, "Apertura")
    assert {p.zona for p in ps} == {"Zona A", "Interzonal"}


@pytest.mark.parametrize("crudo", ["Interzonal", "Interzonales", "interzonal"])
def test_interzonal_es_una_sola_etiqueta(crudo):
    """La misma pagina lo escribe en singular y en plural."""
    assert parser._seccion(crudo) == "Interzonal"


def test_encabezados_no_son_partidos():
    """Las filas `!width=21%|Local ...` no tienen que entrar como partido."""
    ps = parser.partidos_de_tabla(TABLA, 2026, "Apertura")
    assert not any(p.local == "Local" for p in ps)


# --------------------------------------------------------------------------
# las llaves: plantillas {{Partido}}
# --------------------------------------------------------------------------
def test_plantillas():
    ps = parser.partidos_de_plantillas(LLAVES, 2026, "Apertura")
    assert len(ps) == 2
    assert all(p.fase == "eliminacion" for p in ps)
    assert ps[0].local == "River Plate"
    assert ps[0].fecha == "2026-05-17"
    assert ps[0].estadio == "Monumental"


def test_bug_los_parentesis_son_el_entretiempo_no_los_penales():
    """EL error a no cometer.

    `|resultado = 2:0''' (1:0)` -- el (1:0) es el ENTRETIEMPO. Los penales tienen
    su propio parametro. Leerlos de los parentesis no falla: inventa tandas de
    penales en partidos que se ganaron en los 90, y despues alguien arma el
    cuadro de eliminacion al reves.
    """
    river, belgrano = parser.partidos_de_plantillas(LLAVES, 2026, "Apertura")

    # este SI fue a penales, y estan en `resultado penalti`
    assert (river.goles_local, river.goles_visita) == (1, 1)
    assert (river.penales_local, river.penales_visita) == (4, 3)

    # este NO: gano 2-0 en los 90, el (1:0) es el entretiempo
    assert (belgrano.goles_local, belgrano.goles_visita) == (2, 0)
    assert belgrano.penales_local is None
    assert belgrano.penales_visita is None


# --------------------------------------------------------------------------
# la pagina entera
# --------------------------------------------------------------------------
def test_pagina_junta_las_dos_fases(pagina):
    ps = parser.partidos(pagina, 2026, "Apertura")
    assert len(ps) == 6
    assert sum(p.fase == "zonas" for p in ps) == 4
    assert sum(p.fase == "eliminacion" for p in ps) == 2


def test_pagina_sin_resultados_no_explota():
    assert parser.partidos("== Nada ==\ntexto suelto\n", 2026, "X") == []

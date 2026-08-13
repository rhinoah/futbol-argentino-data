#!/usr/bin/env python3
"""Tests del ascenso: una pagina puede traer VARIOS torneos y VARIAS zonas.

Todo lo de aca sale de errores que estuvieron en el codigo, y ninguno fallaba:
devolvian la mitad de los partidos, o el doble.
"""
from __future__ import annotations

from fad import parser, validar
from fad.parser import Partido

FILA = ("|-\n|{a}\n|1 - 0\n|{b}\n|Un Estadio\n|{d} de marzo\n|20:00\n")


def tabla(*cruces, cabecera=""):
    filas = "".join(FILA.format(a=a, b=b, d=i + 1) for i, (a, b) in enumerate(cruces))
    cab = f"!colspan=6|{cabecera}\n|-\n" if cabecera else ""
    return ('{|class="wikitable"\n!colspan=6|Fecha 1\n|-\n' + cab +
            "!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n" + filas + "|}\n")


def test_lee_TODAS_las_secciones_de_resultados():
    """El ascenso pone `== Zona A ==` y `== Zona B ==` de primer nivel, cada una
    con su propio `=== Resultados ===`. Leyendo una sola se perdia la mitad: la
    Primera Nacional 2025 daba 26 equipos donde hay 38, y la mitad que quedaba
    estaba perfecta, que es lo que lo hace dificil de ver."""
    pagina = f"""
== Zona A ==
=== Resultados ===
{tabla(("Boca Juniors", "River Plate"))}
== Zona B ==
=== Resultados ===
{tabla(("Racing Club", "Independiente"))}
== Goleadores ==
"""
    ps = parser.partidos(pagina, 2026, "X")
    assert len(ps) == 2
    assert {p.zona for p in ps} == {"Zona A", "Zona B"}


def test_una_seccion_anidada_no_se_cuenta_dos_veces():
    """Si `== Resultados ==` contiene un `=== Resultados ===`, el anidado ya vino
    en el cuerpo del padre. Tomandolo igual, cada partido entra dos veces y todos
    los equipos parecen jugar dos veces por fecha."""
    pagina = f"""
== Resultados ==
=== Resultados ===
{tabla(("Boca Juniors", "River Plate"))}
== Goleadores ==
"""
    assert len(parser.partidos(pagina, 2026, "X")) == 1


def test_la_zona_y_la_fase_son_cosas_distintas():
    """La Copa de la Liga 2020 tuvo Fase Campeonato y Fase Complementacion, CADA
    UNA con su Grupo A y su Fecha 1, con los mismos equipos. Quedandose solo con
    el padre inmediato las dos fases colapsan en una y los equipos aparecen
    jugando dos veces la misma fecha."""
    pagina = f"""
== Fase Campeonato ==
=== Grupo A ===
==== Resultados ====
{tabla(("Boca Juniors", "River Plate"))}
== Fase Complementación ==
=== Grupo A ===
==== Resultados ====
{tabla(("Boca Juniors", "River Plate"))}
== Goleadores ==
"""
    ps = parser.partidos(pagina, 2026, "X")
    assert {p.zona for p in ps} == {"Grupo A"}
    assert {p.llave for p in ps} == {"Fase Campeonato", "Fase Complementación"}
    assert validar.una_vez_por_jornada(ps) == [], "las dos fases se mezclaron"


def test_dos_torneos_en_una_pagina_no_comparten_la_fecha_1():
    """Primera B y C meten `== Torneo Apertura ==` y `== Torneo Clausura ==` en
    la misma pagina, cada uno con su Fecha 1."""
    ps = [Partido(fecha="2026-03-01", local="Boca Juniors", visita="River Plate",
                  goles_local=1, goles_visita=0, fase="zonas", jornada="Fecha 1",
                  llave=t) for t in ("Torneo Apertura", "Torneo Clausura")]
    assert validar.una_vez_por_jornada(ps) == []


def test_la_ronda_no_se_arrastra_de_un_cuadro_al_siguiente():
    """Una pagina del ascenso tiene un `== Final ==` (la del campeonato) y despues
    un `== Torneo reducido ==` con sus propias fases. Sin acotar la busqueda al
    cuadro actual, los partidos de la "Primera fase" del reducido se quedaban con
    el "Final" arrastrado de la seccion anterior."""
    texto = """
== Final ==
{{Partido
|local = Boca Juniors
|resultado = 2:0
|visita = River Plate
|fecha = 1 de mayo
}}

== Torneo reducido ==
=== Primera fase ===
{{Partido
|local = Racing Club
|resultado = 1:0
|visita = Independiente
|fecha = 10 de mayo
}}
"""
    ps = parser.partidos_de_plantillas(texto, 2026, "X")
    assert [p.jornada for p in ps] == ["Final", "Primera fase"]
    assert [p.llave for p in ps] == ["Final", "Torneo reducido"]


def test_una_ronda_desconocida_queda_vacia_y_no_hereda_la_de_al_lado():
    """El caso que de verdad distingue arrastrar de no arrastrar.

    Si el cuadro siguiente empieza con un titulo que no esta en `RONDAS`, lo
    correcto es quedarse sin ronda -- y que `cadena_de_llaves` avise que no puede
    revisar ese cuadro. Heredando la de la seccion anterior, esos partidos pasan
    por "Final" y el chequeo encadena cosas que no tienen nada que ver: fueron 21
    avisos sobre datos correctos en la Primera Nacional 2024.
    """
    texto = """
== Final ==
{{Partido
|local = Boca Juniors
|resultado = 2:0
|visita = River Plate
|fecha = 1 de mayo
}}

== Torneo reducido ==
=== Ronda preliminar ===
{{Partido
|local = Racing Club
|resultado = 1:0
|visita = Independiente
|fecha = 10 de mayo
}}
"""
    ps = parser.partidos_de_plantillas(texto, 2026, "X")
    assert [p.jornada for p in ps] == ["Final", ""], "heredo la ronda del cuadro anterior"


def test_la_fase_no_se_busca_en_el_nivel_del_propio_titulo():
    """Cuando `== Resultados ==` es de NIVEL 2 -- como en todos los torneos de
    2004-2015 -- no hay seccion que lo contenga, y la fase tiene que quedar
    vacia. Buscandola en nivel 2 se toma la seccion ANTERIOR, que no lo contiene:
    los 190 partidos del Inicial 2012 quedaban bajo una fase llamada "Tabla de
    posiciones final"."""
    pagina = f"""
== Tabla de posiciones final ==
texto

== Resultados ==
{tabla(("Boca Juniors", "River Plate"))}
== Goleadores ==
"""
    zona, fase, _ = parser.secciones_de_resultados(pagina)[0]
    assert fase == "", f"tomo la seccion anterior como fase: {fase!r}"

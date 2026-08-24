#!/usr/bin/env python3
"""Tests de las fechas copiadas a mano de una fuente citada.

Es el unico lugar del repo donde un dato se copia a mano, asi que lo que hay que
probar no es tanto el codigo -- son tres lineas -- como las promesas del
docstring: que el marcador verifica, que solo se toma la fecha, y que la tabla no
se desincroniza del resto del repo.
"""
from __future__ import annotations

import build
from fad import citadas, fechas, torneos
from fad.parser import Partido


def test_las_citas_apuntan_a_paginas_que_existen():
    """Una pagina mal escrita en la tabla no rompe nada: simplemente no se aplica
    nunca, en silencio. Es la forma en que este tipo de tabla se muere sola."""
    paginas = {t.pagina for t in torneos.TODOS}
    for pagina in citadas.FECHAS:
        assert pagina in paginas, f"{pagina!r} no es una pagina del catalogo"


def test_los_clubes_de_las_citas_estan_en_el_padron():
    """Van en canonico porque `fechas.completar` compara contra nuestros nombres
    ya canonizados. Uno mal escrito no emparejaria nunca."""
    from fad import equipos

    for citas in citadas.FECHAS.values():
        for c in citas:
            for club in (c.local, c.visita):
                assert equipos.canonizar(club) == club, f"{club!r} no es canonico"


def test_ninguna_cita_esta_repetida():
    """Dos citas del mismo partido son dos fechas para una fila. La regla de
    colision de `completar` las tiraria a las dos, asi que el efecto seria perder
    la fecha en vez de duplicarla -- pero igual es un error de tipeo que conviene
    que salte aca."""
    for pagina, citas in citadas.FECHAS.items():
        pares = [(c.local, c.visita, c.goles_local, c.goles_visita) for c in citas]
        assert len(pares) == len(set(pares)), f"{pagina}: hay citas repetidas"


def test_las_citas_van_como_ajeno_sin_jornada():
    """`jornada=0` a proposito, igual que el feed de ESPN: la fuente rotula sus
    fechas de otra manera que la pagina -- "1ra. Fase" contra "Fecha 1" -- asi que
    el identificador es el par de clubes."""
    a = citadas.ajenos("Torneo Argentino A 2004-05")
    assert a and all(x.jornada == 0 for x in a)
    assert all(x.fecha and x.local and x.visita for x in a)


def test_el_marcador_verifica_la_fecha():
    """EL CONTRATO, que es el mismo que el de cualquier otro completador: los
    clubes identifican el partido y el marcador lo verifica. Una linea mal copiada
    no se cuela -- no empareja, y se avisa."""
    nuestro = Partido(local="Atlético Tucumán", visita="La Florida", goles_local=2,
                      goles_visita=0, fase="zonas", jornada="Fecha 1")
    puestas, _ = fechas.completar(
        [nuestro], [fechas.Ajeno(fecha="2004-09-12", jornada=0,
                                 local="Atlético Tucumán", visita="La Florida",
                                 goles_local=2, goles_visita=0)],
        credito=citadas.CREDITO)
    assert (puestas, nuestro.fecha) == (1, "2004-09-12")

    otro = Partido(local="Atlético Tucumán", visita="La Florida", goles_local=9,
                   goles_visita=9, fase="zonas", jornada="Fecha 1")
    puestas, avisos = fechas.completar(
        [otro], [fechas.Ajeno(fecha="2004-09-12", jornada=0,
                              local="Atlético Tucumán", visita="La Florida",
                              goles_local=2, goles_visita=0)],
        credito=citadas.CREDITO)
    assert puestas == 0 and otro.fecha == ""
    assert any("marcador distinto" in a for a in avisos)


def test_de_la_cita_sale_la_fecha_y_nada_mas():
    """SOLO LA FECHA. La fuente es un blog, de otra categoria que RSSSF o ESPN, y
    lo que la hace aceptable para este uso puntual es justamente que de aca no
    sale ni un marcador, ni una localia, ni un club. Y queda el credito puesto en
    la fila, que es como el dataset dice de donde salio cada fecha."""
    nuestro = Partido(local="Aldosivi", visita="Luján de Cuyo", goles_local=0,
                      goles_visita=1, fase="eliminacion",
                      jornada="Zona Campeonato - Quarterfinals")
    antes = (nuestro.local, nuestro.visita, nuestro.goles_local, nuestro.goles_visita)
    fechas.completar([nuestro], citadas.ajenos("Torneo Argentino A 2004-05"),
                     credito=citadas.CREDITO)
    assert nuestro.fecha == "2004-11-20"
    assert (nuestro.local, nuestro.visita,
            nuestro.goles_local, nuestro.goles_visita) == antes
    assert nuestro.fuente_fecha == citadas.CREDITO


_PAGINA = """
== Resultados ==
{|class="wikitable"
!colspan=6|Fecha 1
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
|River Plate
|Un Estadio
|
|
|}

== Otra cosa ==
"""


def test_el_build_las_aplica(monkeypatch):
    """El punto de llamada, que es lo que un test sobre la funcion no cubre."""
    from fad.torneos import Torneo

    t = Torneo("Anexo:Prueba", "Prueba", 2004, anio_fin=2005)
    monkeypatch.setitem(
        citadas.FECHAS, "Anexo:Prueba",
        (citadas.Cita("2004-09-12", "Boca Juniors", "River Plate", 2, 1),))
    ps, _ = build.procesar(_PAGINA, t)
    assert [p.fecha for p in ps] == ["2004-09-12"]


def test_sin_citas_no_se_llama_al_completador(monkeypatch):
    """Llamarlo en las 149 paginas cuando una sola tiene citas emitia un "sin
    pareja" en cada una: trece avisos nuevos por una tabla de veinticuatro
    filas."""
    from fad.torneos import Torneo

    def explotar(*a, **k):
        raise AssertionError("no se tiene que llamar")

    monkeypatch.setattr(citadas, "ajenos", explotar)
    build.procesar(_PAGINA, Torneo("Anexo:Otra", "Prueba", 2004, anio_fin=2005))

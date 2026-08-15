#!/usr/bin/env python3
"""Tests de las correcciones a mano.

Este modulo es el unico lugar del proyecto donde se sobrescribe lo que dice la
fuente, asi que lo que hay que probar no es que corrija -- eso es una asignacion
-- sino que **se niegue a corregir** cuando no esta parada sobre el partido que
cree. Una correccion que engancha donde no debe no falla: cambia un club por otro
y el dataset queda mintiendo con toda confianza.
"""
from __future__ import annotations

from fad import correcciones
from fad.correcciones import Correccion
from fad.parser import Partido


def partido(local, visita, gl=0, gv=0, jornada="Fecha 12"):
    return Partido(fecha="2009-10-29", local=local, visita=visita, goles_local=gl,
                   goles_visita=gv, fase="zonas", jornada=jornada)


UNA = Correccion(pagina="Una Pagina", jornada="Fecha 12",
                 dice=("All Boys", "Belgrano", 0, 0),
                 debe=("All Boys", "Gimnasia y Esgrima (J)"),
                 porque="de prueba")


def con(monkeypatch, *cs):
    monkeypatch.setattr(correcciones, "CORRECCIONES", cs)


def test_corrige_el_partido_que_identifica(monkeypatch):
    con(monkeypatch, UNA)
    ps = [partido("All Boys", "Belgrano")]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert (n, avisos) == (1, [])
    assert (ps[0].local, ps[0].visita) == ("All Boys", "Gimnasia y Esgrima (J)")


def test_no_toca_los_partidos_de_otra_pagina(monkeypatch):
    con(monkeypatch, UNA)
    ps = [partido("All Boys", "Belgrano")]
    n, _ = correcciones.aplicar(ps, "Otra Pagina")
    assert (n, ps[0].visita) == (0, "Belgrano")


def test_el_marcador_es_parte_de_la_identificacion(monkeypatch):
    """All Boys y Belgrano se cruzan dos veces por temporada. Sin el marcador, la
    correccion podria caer sobre el otro partido."""
    con(monkeypatch, UNA)
    ps = [partido("All Boys", "Belgrano", 2, 1)]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0
    assert ps[0].visita == "Belgrano"
    assert any("ya no engancha" in a for a in avisos)


def test_la_jornada_tambien(monkeypatch):
    con(monkeypatch, UNA)
    ps = [partido("All Boys", "Belgrano", jornada="Fecha 31")]
    n, _ = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0


def test_una_correccion_que_ya_no_aplica_avisa(monkeypatch):
    """Cuando alguien arregle la pagina en Wikipedia, esta entrada queda al pedo.
    Si se callara, quedaria ahi para siempre esperando enganchar con algo."""
    con(monkeypatch, UNA)
    ps = [partido("All Boys", "Gimnasia y Esgrima (J)")]   # ya corregido en la fuente
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0
    assert any("sacala de fad/correcciones.py" in a for a in avisos)


def test_si_engancha_con_dos_no_corrige_ninguno(monkeypatch):
    """Ante la duda, no se toca nada: elegir uno de los dos seria adivinar."""
    con(monkeypatch, UNA)
    ps = [partido("All Boys", "Belgrano"), partido("All Boys", "Belgrano")]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0
    assert all(p.visita == "Belgrano" for p in ps)
    assert any("2 partidos" in a for a in avisos)


# --------------------------------------------------------------------------
# la tabla de verdad
# --------------------------------------------------------------------------
def test_todas_las_correcciones_estan_justificadas():
    """Sin evidencia escrita no entra: es la unica defensa contra que esto se
    convierta en el lugar donde se arregla cualquier dato molesto."""
    for c in correcciones.CORRECCIONES:
        assert len(c.porque) > 80, f"{c.pagina} {c.jornada}: la evidencia es muy flaca"
        assert c.dice[:2] != c.debe, "una correccion que no cambia nada"


def test_las_correcciones_usan_nombres_del_padron():
    """`debe` va en canonico. Un nombre que el padron no conoce dejaria el
    partido peor de lo que estaba, y `nombres_en_el_padron` recien lo agarraria
    despues."""
    from fad import equipos
    for c in correcciones.CORRECCIONES:
        for n in c.debe:
            assert equipos.buscar(n) is not None, f"{n!r} no esta en el padron"


def test_un_marcador_arbitrado_que_ya_no_engancha_avisa(monkeypatch):
    """Si Wikipedia corrige el marcador, el arbitraje queda sin efecto. Tiene que
    decirlo en vez de reventar o de tocar el partido que no es."""
    from fad.correcciones import Marcador
    monkeypatch.setattr(correcciones, "MARCADORES", (
        Marcador(pagina="Una Pagina", jornada="Fecha 1", local="All Boys",
                 visita="Belgrano", dice=(0, 1), debe=(1, 0), porque="x" * 90),))
    ps = [partido("All Boys", "Belgrano", 1, 0, jornada="Fecha 1")]   # ya esta bien
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0
    assert any("no se aplica" in a for a in avisos)


def test_un_marcador_arbitrado_se_aplica(monkeypatch):
    from fad.correcciones import Marcador
    monkeypatch.setattr(correcciones, "MARCADORES", (
        Marcador(pagina="Una Pagina", jornada="Fecha 1", local="All Boys",
                 visita="Belgrano", dice=(0, 1), debe=(1, 0), porque="x" * 90),))
    ps = [partido("All Boys", "Belgrano", 0, 1, jornada="Fecha 1")]
    n, _ = correcciones.aplicar(ps, "Una Pagina")
    assert n == 1 and (ps[0].goles_local, ps[0].goles_visita) == (1, 0)


# --------------------------------------------------------------------------
# la cancha: la tercera forma que tiene la fuente de contradecirse
# --------------------------------------------------------------------------
from fad.correcciones import Cancha

UNA_CANCHA = Cancha(pagina="Una Pagina", jornada="Fecha 36",
                    local="Gimnasia y Esgrima (J)", visita="San Martín (T)",
                    dice="Víctor Antonio Legrotaglie", debe="23 de Agosto",
                    porque="de prueba")


def _con_cancha(estadio, jornada="Fecha 36", local="Gimnasia y Esgrima (J)"):
    p = partido(local, "San Martín (T)", jornada=jornada)
    p.estadio = estadio
    return p


def test_corrige_la_cancha(monkeypatch):
    monkeypatch.setattr(correcciones, "CANCHAS", (UNA_CANCHA,))
    ps = [_con_cancha("Víctor Antonio Legrotaglie")]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert (n, avisos) == (1, [])
    assert ps[0].estadio == "23 de Agosto"


def test_la_cancha_vieja_es_parte_de_la_identificacion(monkeypatch):
    """Si la pagina ya dice otra cosa, la correccion no se aplica a ciegas: o la
    arreglaron, o esta parada sobre un partido que no es."""
    monkeypatch.setattr(correcciones, "CANCHAS", (UNA_CANCHA,))
    ps = [_con_cancha("23 de Agosto")]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0 and len(avisos) == 1 and "engancha con 0" in avisos[0]


def test_una_cancha_corregida_que_ya_no_engancha_avisa(monkeypatch):
    """Cuando alguien arregle la pagina, esta entrada queda sin efecto y el build
    lo dice. Una correccion vieja que nadie saco es una mentira dormida."""
    monkeypatch.setattr(correcciones, "CANCHAS", (UNA_CANCHA,))
    n, avisos = correcciones.aplicar([_con_cancha("Otra", jornada="Fecha 1")], "Una Pagina")
    assert n == 0 and avisos and "sacala de fad/correcciones.py" in avisos[0]


def test_no_toca_las_canchas_de_otra_pagina(monkeypatch):
    monkeypatch.setattr(correcciones, "CANCHAS", (UNA_CANCHA,))
    ps = [_con_cancha("Víctor Antonio Legrotaglie")]
    assert correcciones.aplicar(ps, "Otra Pagina") == (0, [])
    assert ps[0].estadio == "Víctor Antonio Legrotaglie"


def test_las_canchas_corregidas_estan_justificadas():
    """La condicion del modulo: la fuente se contradice sola y se dice donde. Las
    dos que hay salen de la tabla de participantes de la propia pagina."""
    for c in correcciones.CANCHAS:
        assert len(c.porque) > 80, f"{c.jornada} {c.local}: la evidencia es muy flaca"
        assert "participantes" in c.porque, "hay que nombrar al testigo"
        assert c.dice != c.debe

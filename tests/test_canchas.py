#!/usr/bin/env python3
"""Tests del padron de canchas: `fad/canchas.py`.

Los nombres de los ejemplos son grafias que el dataset publicaba antes del padron,
medidas el 13/11/2026: no salen del padron mismo, asi que no lo comparan consigo.
"""
from __future__ import annotations

from collections import Counter
from pathlib import Path

import pytest

from fad import canchas, correcciones, dataset, torneos

DATOS = Path(__file__).resolve().parent.parent / "data"


# ---- la clave ------------------------------------------------------------------
@pytest.mark.parametrize("una, otra", [
    ("Raul Conti", "Raúl Conti"),                         # tildes
    ("15 de Abril", "15 de abril"),                       # mayusculas
    ('Claudio "Chiqui" Tapia', "Claudio Chiqui Tapia"),   # comillas
    ("Estadio La Bombonera", "La Bombonera"),             # el "Estadio" adelante
    ("Estadio de Chacarita Juniors", "Chacarita Juniors"),
    ("Héctor Odicino - Pedro Benoza", "Héctor Odicino y Pedro Benoza"),
    ("Coliseo del Golfo", "El Coliseo del Golfo"),
])
def test_la_clave_junta_el_mismo_nombre_escrito_de_dos_formas(una, otra):
    assert canchas.clave(una) == canchas.clave(otra)


@pytest.mark.parametrize("una, otra", [
    ("Don León Kolbovsky", "Don León Kolbowsky"),         # un apellido mal escrito
    ("Tomás A. Ducó", "Tomás Adolfo Ducó"),               # un nombre largo y uno corto
    ("Chateau Carreras", "Mario Alberto Kempes"),         # el nombre viejo y el nuevo
    ("Malvinas Argentinas", "Islas Malvinas"),            # dos canchas distintas
])
def test_la_clave_no_junta_nombres_distintos(una, otra):
    """Juntar estos es afirmar que son la misma cancha, y eso pide fuente: lo hace
    un alias del padron, no la clave."""
    assert canchas.clave(una) != canchas.clave(otra)


# ---- el padron ------------------------------------------------------------------
@pytest.mark.parametrize("dice, publica", [
    ("Raul Conti", "Raúl Conti"),
    ("Estadio La Bombonera", "La Bombonera"),
    ("15 de Abril", "15 de abril"),
    ("Tomas A. Ducó", "Tomás A. Ducó"),
    ("Estadio Ciudad de Córdoba", "Ciudad de Córdoba"),   # sin "Estadio", aunque perdia
    ("Jose Moraños", "José Moraños"),                     # empate: la de las tildes
])
def test_canonica_da_el_nombre_del_padron(dice, publica):
    assert canchas.canonica(dice) == publica


@pytest.mark.parametrize("dice, publica", [
    ("Chateau Carreras", "Mario Alberto Kempes"),          # el nombre viejo
    ("Estadio Don León Kolbovsky", "Don León Kolbowsky"),  # el alias, con su "Estadio"
    ("El Viaducto", "El Viaducto"),                        # el nombre, que es el apodo
    ("Julio Humberto Grondona", "El Viaducto"),
    ("Coloso del Parque", "Marcelo Bielsa"),
])
def test_un_alias_publica_el_nombre_de_su_cancha(dice, publica):
    assert canchas.canonica(dice) == publica


@pytest.mark.parametrize("cancha", [
    "Cancha Inventada", "",
    "La Doble Visera",          # la cancha vieja de Independiente: Wikipedia la separa
    "De la Avenida",            # la de Unión de Sunchales, no el 15 de Abril
    "Malvinas Argentinas",      # nombra dos canchas: no se junta con nada
])
def test_una_cancha_sin_alias_queda_con_su_nombre(cancha):
    assert canchas.canonica(cancha) == cancha


def test_cada_clave_del_padron_es_de_una_sola_cancha():
    """Dos nombres con la misma clave: el ultimo pisaria al primero en el indice."""
    claves = Counter(canchas.clave(n) for c in canchas.PADRON for n in (c.nombre,) + c.alias)
    assert [k for k, n in claves.items() if n > 1] == []


def test_un_alias_que_reclaman_dos_canchas_revienta_al_armar_el_indice(monkeypatch):
    monkeypatch.setattr(canchas, "PADRON", (
        canchas.Cancha("Una", alias=("Otra",), articulo="Estadio Una"),
        canchas.Cancha("Otra")))
    with pytest.raises(ValueError, match="dos canchas"):
        canchas._armar_indice()


def test_ningun_nombre_del_padron_empieza_con_estadio():
    nombres = [n for c in canchas.PADRON for n in (c.nombre,) + c.alias]
    assert [n for n in nombres if n.lower().startswith("estadio")] == []


def test_una_cancha_con_alias_nombra_su_articulo_y_una_sin_alias_no():
    assert [c.nombre for c in canchas.PADRON if bool(c.alias) != bool(c.articulo)] == []


# ---- los testigos de los alias ----------------------------------------------------
TESTIGOS = Path(__file__).resolve().parent / "testigos_canchas.txt"


def _testigos() -> list[tuple[str, str, str, str]]:
    renglones = [r for r in TESTIGOS.read_text(encoding="utf-8").splitlines()
                 if r.strip() and not r.startswith("#")]
    return [tuple(x.strip() for x in r.split(" | ", 3)) for r in renglones]


def test_cada_alias_tiene_su_testigo_y_cada_testigo_su_alias():
    """El padron y la evidencia, cruzados en los dos sentidos: un alias agregado sin
    enlace que lo sostenga falla aca, y tambien uno que se borre del padron dejando
    su testigo colgado."""
    del_padron = {(n, c.articulo) for c in canchas.PADRON if c.alias
                  for n in (c.nombre,) + c.alias}
    de_testigos = {(g, art) for g, art, _, _ in _testigos()}
    assert len(de_testigos) > 70
    assert del_padron - de_testigos == set(), "alias sin testigo"
    assert de_testigos - del_padron == set(), "testigo sin alias"


def test_el_enlace_de_cada_testigo_muestra_su_grafia():
    """Que el renglon diga de que grafia es no alcanza: el texto del enlace tiene que
    ser esa grafia, con a lo sumo tildes, mayusculas o un "Estadio" de diferencia."""
    for grafia, _, pagina, enlace in _testigos():
        visible = enlace.strip("[]").split("|")[-1]
        assert canchas.clave(visible) == canchas.clave(grafia), (grafia, pagina, enlace)


def test_unificar_cambia_solo_la_cancha_y_cuenta_las_filas():
    filas = [{"venue": "Raul Conti", "home_team": "Guillermo Brown"},
             {"venue": "Raúl Conti", "home_team": "Guillermo Brown"},
             {"venue": "", "home_team": "Guillermo Brown"},
             {"venue": "Cancha Inventada", "home_team": "Guillermo Brown"}]
    assert canchas.unificar(filas) == 1
    assert filas == [{"venue": "Raúl Conti", "home_team": "Guillermo Brown"},
                     {"venue": "Raúl Conti", "home_team": "Guillermo Brown"},
                     {"venue": "", "home_team": "Guillermo Brown"},
                     {"venue": "Cancha Inventada", "home_team": "Guillermo Brown"}]


def test_sueltas_avisa_una_cancha_nueva_escrita_de_dos_formas():
    filas = [{"venue": "Cancha Nueva"}, {"venue": "Estadio Cancha Nueva"},
             {"venue": "Cancha Nueva"}, {"venue": "Raúl Conti"}, {"venue": ""}]
    assert canchas.sueltas(filas) == [
        "una cancha escrita de 2 formas: 'Cancha Nueva' (2) / 'Estadio Cancha Nueva' (1)."
        " Va en fad/canchas.py, con la que se publica"]


def test_sueltas_no_avisa_una_cancha_escrita_siempre_igual():
    assert canchas.sueltas([{"venue": "Raúl Conti"}, {"venue": "Raúl Conti"}]) == []


# ---- las declaraciones escriben la cancha como el padron ---------------------------
def test_las_declaraciones_escriben_la_cancha_como_la_publica_el_padron():
    """El build unifica DESPUES de aplicarlas. Una que escribiera `Estadio X` se
    publicaria como `X`, y su test sobre lo publicado fallaria sin decir por que."""
    escritas = ([("CANCHAS", c.debe) for c in correcciones.CANCHAS]
                + [("COPIAS", d.valor) for d in correcciones.COPIAS if d.campo == "venue"]
                + [("FALTANTES", x.estadio) for x in correcciones.FALTANTES]
                + [("ALQUILERES", cancha) for cancha, _ in dataset.ALQUILERES])
    assert len(escritas) > 100
    assert [(d, c) for d, c in escritas if canchas.canonica(c) != c] == []


# ---- sobre lo publicado -------------------------------------------------------------
def test_en_los_torneos_cerrados_cada_cancha_se_escribe_de_una_sola_forma():
    """Mira solo los cerrados: una grafia nueva que trae una pagina en curso la avisa
    el build, y no tiene que tumbar la corrida diaria."""
    filas = dataset.leer_carpeta(DATOS)
    if not filas:
        pytest.skip("hace falta el dataset")
    cerradas = {t.url for t in torneos.TODOS if t.cerrado}
    filas = [f for f in filas if dataset.pagina_de(f) in cerradas]
    assert len(filas) > 40000
    assert canchas.sueltas(filas) == []

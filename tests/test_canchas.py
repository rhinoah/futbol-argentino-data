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
    ("La Doble Visera", "Libertadores de América"),       # un apodo
    ("Malvinas Argentinas", "Islas Malvinas"),            # dos canchas distintas
])
def test_la_clave_no_junta_nombres_distintos(una, otra):
    """Juntar estos es afirmar que son la misma cancha, y eso pide fuente."""
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


@pytest.mark.parametrize("cancha", ["Cancha Inventada", "Comandante A. Guacurarí", ""])
def test_una_cancha_que_no_esta_en_el_padron_queda_como_vino(cancha):
    assert canchas.canonica(cancha) == cancha


def test_cada_cancha_del_padron_tiene_una_sola_clave():
    """Dos nombres con la misma clave: el ultimo pisaria al primero en el indice."""
    repetidas = [k for k, n in Counter(canchas.clave(c) for c in canchas.PADRON).items()
                 if n > 1]
    assert repetidas == []


def test_ningun_nombre_del_padron_empieza_con_estadio():
    assert [c for c in canchas.PADRON if c.lower().startswith("estadio")] == []


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

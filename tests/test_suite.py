#!/usr/bin/env python3
"""Chequeos sobre la suite misma.

El repo ya tiene dos redes contra los tests que dejan de probar: mutation
testing, que agarra al test que no mata a su mutante, y el testigo externo, que
agarra al test que se volvio tautologico despues de un refactor. Falta la
tercera, que es la mas boba y por eso la mas facil de comer:

    un test que directamente NO CORRE.

En pytest un modulo es un modulo de Python, asi que dos funciones con el mismo
nombre no son dos tests: la segunda pisa a la primera y la primera desaparece.
No hay error, no hay warning, y el contador de tests baja en uno -- que es un
numero que nadie mira cuando acaba de agregar tests y el total subio igual.

Paso escribiendo el chequeo de balance de `posiciones.desbalance`: se agrego un
`test_si_no_coinciden_los_partidos_jugados_se_calla` sin ver que
`test_posiciones.py` ya tenia uno con ese nombre exacto, doce tests mas arriba,
y el de `contrastar` dejo de correr. Se noto de casualidad. Este test es para no
depender de la casualidad la proxima vez.
"""
from __future__ import annotations

import ast
import pathlib

import pytest

TESTS = sorted(pathlib.Path(__file__).parent.glob("test_*.py"))


def test_hay_tests_que_mirar():
    """Si el glob no encuentra nada, el test de abajo pasa por vacio."""
    assert len(TESTS) > 5


@pytest.mark.parametrize("archivo", TESTS, ids=lambda p: p.name)
def test_ningun_nombre_de_test_esta_duplicado(archivo: pathlib.Path):
    """Dos funciones con el mismo nombre en un modulo: la segunda pisa a la
    primera, y la primera no corre nunca mas."""
    arbol = ast.parse(archivo.read_text(encoding="utf-8"))
    nombres = [n.name for n in arbol.body
               if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef))
               and n.name.startswith("test_")]
    repetidos = sorted({n for n in nombres if nombres.count(n) > 1})
    assert not repetidos, (
        f"{archivo.name}: {repetidos} esta(n) definido(s) mas de una vez. "
        f"La ultima definicion pisa a las anteriores y esas no corren")

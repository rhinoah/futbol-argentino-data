#!/usr/bin/env python3
"""Tests de `mutar.py`: que no cuente como muerto a un mutante que nadie miro.

`mutar.py` corre la suite contra cada mutante y da por muerto al que la hace
fallar. Pero pytest sale con error por dos motivos que no se parecen en nada: un
test que falla, o un modulo que no se pudo importar -- y en el segundo no corrio
ningun test. Darlo por muerto es decir que la red lo agarro cuando la red no
estaba puesta. Lo mismo vale para el mutante que ni siquiera compila.

La primera version de esa distincion buscaba una frase que pytest, llamado con
`-x`, no escribe. No disparo nunca, y no habia un test que lo dijera.
"""
from __future__ import annotations

import pytest

import mutar

# Lo que escribe pytest 9.1 en cada caso, llamado como lo llama `correr_suite`
# (`-q -x --no-header`). Son los renglones de corridas de verdad, del 10/10/2026.
FALLA = """\
FAILED tests/test_a.py::test_a - assert 2 == 1
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 failed in 0.22s
"""
NOMBRE_QUE_NO_EXISTE = """\
ERROR tests/test_a.py - NameError: name 'no_existe' is not defined
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 error in 0.23s
"""
IMPORT_QUE_NO_EXISTE = """\
ERROR tests/test_a.py
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 error in 0.19s
"""
SIN_LA_X = """\
ERROR tests/test_ascenso.py - NameError: name 'no_existe_este_nombre' is not ...
!!!!!!!!!!!!!!!!!!! Interrupted: 4 errors during collection !!!!!!!!!!!!!!!!!!!
4 errors in 1.60s
"""
FIXTURE_ROTA = """\
ERROR tests/test_a.py::test_a - RuntimeError: x
!!!!!!!!!!!!!!!!!!!!!!!!!! stopping after 1 failures !!!!!!!!!!!!!!!!!!!!!!!!!!
1 error in 0.19s
"""


@pytest.mark.parametrize("salida, como", [
    (FALLA, "falla"),
    (NOMBRE_QUE_NO_EXISTE, "no corrio"),
    (IMPORT_QUE_NO_EXISTE, "no corrio"),
    (SIN_LA_X, "no corrio"),
    (FIXTURE_ROTA, "falla"),
], ids=["falla", "nombre", "import", "sin -x", "fixture"])
def test_que_un_modulo_no_se_importe_no_es_que_un_test_falle(salida, como):
    """Los dos renglones de un error de colecta -- con el motivo y pelado -- y el
    que se les parece y no lo es: un error de FIXTURE lleva `::test`, porque ahi
    el test si se junto y algo de el corrio."""
    assert mutar.como_salio(1, salida) == como


def test_si_pytest_sale_bien_la_suite_paso_diga_lo_que_diga():
    assert mutar.como_salio(0, NOMBRE_QUE_NO_EXISTE) == "pasa"


def test_contra_el_pytest_que_esta_instalado(tmp_path, monkeypatch):
    """Los textos de arriba son de UNA version de pytest, y el error que esto
    corrige fue justamente suponer lo que pytest escribia. Asi que una vez se le
    pregunta al de verdad: un proyecto minimo cuyo modulo no se puede importar,
    por la misma `correr_suite` y con los mismos flags.

    El segundo archivo de tests esta para que el roto no sea el ultimo que se
    junta: en ese caso pytest SI escribe "error during collection", y el test
    pasaria por el motivo equivocado."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "roto.py").write_text("X = no_existe\n", encoding="utf-8")
    (tmp_path / "tests" / "test_a.py").write_text(
        "import roto\ndef test_a():\n    assert roto.X == 1\n", encoding="utf-8")
    (tmp_path / "tests" / "test_b.py").write_text("def test_b():\n    pass\n", encoding="utf-8")
    monkeypatch.setattr(mutar, "RAIZ", tmp_path)
    assert mutar.correr_suite() == "no corrio"


# ---- lo que `main` hace con cada veredicto -----------------------------------
def _un_mutante(tmp_path, monkeypatch, nuevo, *veredictos):
    """Un proyecto de un archivo y un mutante, y la suite que contesta lo que se le
    diga: primero la corrida de base, despues la del mutante."""
    (tmp_path / "x.py").write_text("A = 1\n", encoding="utf-8")
    monkeypatch.setattr(mutar, "RAIZ", tmp_path)
    monkeypatch.setattr(mutar, "MUTANTES", [("x.py", "el mutante de prueba", "A = 1", nuevo)])
    pendientes = list(veredictos)
    monkeypatch.setattr(mutar, "correr_suite", lambda: pendientes.pop(0))
    return pendientes


def test_un_mutante_que_no_se_pudo_importar_NO_murio(tmp_path, monkeypatch, capsys):
    _un_mutante(tmp_path, monkeypatch, "A = no_existe", "pasa", "no corrio")
    assert mutar.main() == 1, "que CI se entere"
    salida = capsys.readouterr().out
    assert "NO SE PUDO IMPORTAR  el mutante de prueba" in salida
    assert "muere" not in salida
    assert (tmp_path / "x.py").read_text(encoding="utf-8") == "A = 1\n", "y el fuente vuelve"


def test_un_mutante_que_no_compila_tampoco_y_ni_se_corre(tmp_path, monkeypatch, capsys):
    """Con una sola respuesta cargada: si `main` le corriera la suite al mutante,
    se quedaria sin que contestar y este test reventaria."""
    pendientes = _un_mutante(tmp_path, monkeypatch, "A = (", "pasa")
    assert mutar.main() == 1
    salida = capsys.readouterr().out
    assert "NO COMPILA  el mutante de prueba" in salida and "muere" not in salida
    assert pendientes == []
    assert (tmp_path / "x.py").read_text(encoding="utf-8") == "A = 1\n", "ni se llego a escribir"


def test_el_que_hace_fallar_un_test_si_murio(tmp_path, monkeypatch, capsys):
    _un_mutante(tmp_path, monkeypatch, "A = 2", "pasa", "falla")
    assert mutar.main() == 0
    assert "ok  muere      el mutante de prueba" in capsys.readouterr().out


def test_el_que_deja_pasar_la_suite_sobrevive(tmp_path, monkeypatch, capsys):
    _un_mutante(tmp_path, monkeypatch, "A = 2", "pasa", "pasa")
    assert mutar.main() == 1
    assert "SOBREVIVE  el mutante de prueba" in capsys.readouterr().out

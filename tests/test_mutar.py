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

from collections import Counter

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


@pytest.mark.parametrize("codigo", [2, 3, 4, 5])
def test_solo_el_1_puede_ser_un_test_que_fallo(codigo):
    """Los otros codigos son de una corrida que no llego a juzgar nada: interrumpida,
    error interno, error de uso, ningun test juntado."""
    assert mutar.como_salio(codigo, "") == "no corrio"


def test_un_conftest_que_no_se_importa_tampoco_es_un_test_que_falla(tmp_path, monkeypatch):
    """pytest sale con 4 y escribe el motivo en stderr, que `correr_suite` no le pasa
    a `_NO_JUNTO`: por la salida no se lo distingue de nada. Contra el pytest de
    verdad, como el de arriba."""
    (tmp_path / "tests").mkdir()
    (tmp_path / "tests" / "__init__.py").write_text("", encoding="utf-8")
    (tmp_path / "tests" / "conftest.py").write_text("import no_existe_este_modulo\n",
                                                    encoding="utf-8")
    (tmp_path / "tests" / "test_b.py").write_text("def test_b():\n    pass\n", encoding="utf-8")
    monkeypatch.setattr(mutar, "RAIZ", tmp_path)
    assert mutar.correr_suite() == "no corrio"


# ---- las anclas -----------------------------------------------------------------
def test_cada_ancla_esta_una_sola_vez_en_su_archivo():
    """`main` muta la PRIMERA aparicion del texto. Si esta dos veces, el mutante cae
    en la de mas arriba, y cuando entra codigo parecido antes en el archivo se corre
    a otra funcion sin que nada lo note. Asi quedaron cuatro renglones sin mutante:
    dos mutantes caian en otra funcion que la que decia su descripcion, y otros dos
    eran, por lo mismo, iguales a un vecino.

    Cero veces tambien es un error: es el ancla cuyo renglon cambio, y sin esto se
    veia recien al correr `mutar.py`."""
    fuentes: dict[str, str] = {}
    mal = []
    for archivo, desc, viejo, _ in mutar.MUTANTES:
        if archivo not in fuentes:
            fuentes[archivo] = (mutar.RAIZ / archivo).read_bytes().decode("utf-8")
        veces = fuentes[archivo].count(viejo)
        if veces != 1:
            mal.append(f"{archivo}: {desc!r} esta {veces} veces")
    assert mal == [], "alargar el ancla con un renglon vecino:\n" + "\n".join(mal)


def test_no_hay_dos_mutantes_iguales():
    vistos = Counter((a, v, n) for a, _, v, n in mutar.MUTANTES)
    assert [d for a, d, v, n in mutar.MUTANTES if vistos[(a, v, n)] > 1] == []


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


@pytest.mark.parametrize("fin", ["\n", "\r\n"], ids=["LF", "CRLF"])
def test_el_fuente_se_escribe_con_los_finales_que_tenia(tmp_path, monkeypatch, fin):
    """El mutado y el original, en bytes. En modo texto cada sistema escribe sus
    propios finales de renglon: en Windows un fuente LF volvia en CRLF, y en Linux
    uno CRLF volveria en LF. Por eso van los dos casos, y cada sistema tiene el suyo."""
    original = f"A = 1{fin}B = 2{fin}".encode("utf-8")
    (tmp_path / "x.py").write_bytes(original)
    monkeypatch.setattr(mutar, "RAIZ", tmp_path)
    monkeypatch.setattr(mutar, "MUTANTES", [("x.py", "el mutante de prueba", "B = 2", "B = 3")])
    vistos = []

    def suite():
        vistos.append((tmp_path / "x.py").read_bytes())
        return "pasa" if len(vistos) == 1 else "falla"

    monkeypatch.setattr(mutar, "correr_suite", suite)
    assert mutar.main() == 0
    assert vistos[1] == f"A = 1{fin}B = 3{fin}".encode("utf-8"), "el mutado, con sus finales"
    assert (tmp_path / "x.py").read_bytes() == original, "y el original, byte por byte"

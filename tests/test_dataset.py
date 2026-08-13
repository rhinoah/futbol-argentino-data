#!/usr/bin/env python3
"""Tests del CSV."""
from __future__ import annotations

import csv

import pytest

from fad import dataset
from fad.parser import Partido


def fila(fecha, local, visita, hora="20:00", **kw):
    p = Partido(fecha=fecha, hora=hora, local=local, visita=visita,
                goles_local=1, goles_visita=0, fase="zonas", zona="Zona A",
                jornada="Fecha 1", estadio="La Bombonera", **kw)
    return dataset.a_fila(p, "Primera", 2026, "https://ejemplo")


def test_ida_y_vuelta(tmp_path):
    destino = tmp_path / "p.csv"
    original = [fila("2026-03-01", "Boca", "River")]
    dataset.escribir(original, destino)
    leido = dataset.leer(destino)
    assert len(leido) == 1
    assert leido[0]["home_team"] == "Boca"
    assert leido[0]["home_score"] == "1"


def test_el_encabezado_es_el_esquema(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    with destino.open(encoding="utf-8", newline="") as f:
        assert next(csv.reader(f)) == dataset.COLUMNAS


def test_las_filas_salen_ordenadas(tmp_path):
    """Este archivo se regenera solo y se commitea. Si el orden dependiera de
    como Wikipedia acomodo las tablas, cada commit seria un diff de miles de
    lineas movidas y no se veria que cambio de verdad."""
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-05-01", "Racing", "Union"),
                      fila("2026-03-01", "Boca", "River"),
                      fila("2026-03-01", "Aldosivi", "Tigre", hora="17:00")], destino)
    fechas = [(f["date"], f["time"]) for f in dataset.leer(destino)]
    assert fechas == sorted(fechas)
    assert fechas[0] == ("2026-03-01", "17:00")


def test_el_mismo_dataset_da_el_mismo_archivo(tmp_path):
    """Sin esto, una tarea diaria commitea un cambio aunque no haya pasado nada."""
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    filas = [fila("2026-05-01", "Racing", "Union"), fila("2026-03-01", "Boca", "River")]
    dataset.escribir(filas, a)
    dataset.escribir(list(reversed(filas)), b)
    assert a.read_bytes() == b.read_bytes()


def test_los_penales_vacios_no_dicen_None(tmp_path):
    """`str(None)` en un CSV es la cadena 'None', y quien lo lea despues tiene un
    equipo que convirtio None penales."""
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    assert dataset.leer(destino)[0]["home_pens"] == ""
    assert "None" not in destino.read_text(encoding="utf-8")


def test_los_penales_cuando_los_hay(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River",
                           penales_local=4, penales_visita=3)], destino)
    leido = dataset.leer(destino)[0]
    assert (leido["home_pens"], leido["away_pens"]) == ("4", "3")


def test_no_quedan_saltos_de_linea_de_mas(tmp_path):
    """En Windows, `csv` sin `newline=''` escribe \\r\\r\\n y sale una fila vacia
    entre cada dos."""
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River"),
                      fila("2026-03-02", "Racing", "Union")], destino)
    assert b"\r\r\n" not in destino.read_bytes()
    assert len(destino.read_text(encoding="utf-8").strip().splitlines()) == 3


def test_no_deja_el_archivo_temporal(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    assert [p.name for p in tmp_path.iterdir()] == ["p.csv"]


def test_pisa_el_archivo_anterior(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    dataset.escribir([fila("2026-04-01", "Racing", "Union")], destino)
    leido = dataset.leer(destino)
    assert len(leido) == 1 and leido[0]["home_team"] == "Racing"


def test_crea_la_carpeta_si_no_esta(tmp_path):
    destino = tmp_path / "nueva" / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    assert destino.exists()


def test_un_encabezado_distinto_se_rechaza(tmp_path):
    """Si alguien edito el CSV a mano o cambio el esquema, mejor romper que
    devolver diccionarios con las claves equivocadas."""
    destino = tmp_path / "p.csv"
    destino.write_text("fecha,local,visita\n2026-03-01,Boca,River\n", encoding="utf-8")
    with pytest.raises(ValueError, match="encabezado"):
        dataset.leer(destino)


def test_un_campo_de_mas_no_pasa_desapercibido(tmp_path):
    """`extrasaction='raise'`: si el parser empieza a devolver un campo que el
    esquema no tiene, se entera alguien."""
    mala = fila("2026-03-01", "Boca", "River") | {"inventado": 1}
    with pytest.raises(ValueError):
        dataset.escribir([mala], tmp_path / "p.csv")


def test_neutral_sale_del_torneo(tmp_path):
    """La Copa Argentina se juega toda en cancha neutral por reglamento; las
    ligas son local y visitante. El dato es de la competencia, no del partido."""
    destino = tmp_path / "p.csv"
    p = Partido(fecha="2026-03-01", local="Boca", visita="River", goles_local=1,
                goles_visita=0, fase="eliminacion")
    dataset.escribir([dataset.a_fila(p, "Copa", 2026, "url", neutral=True)], destino)
    assert dataset.leer(destino)[0]["neutral"] == "true"


def test_neutral_por_defecto_es_false(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    assert dataset.leer(destino)[0]["neutral"] == "false"


def test_neutral_no_sale_capitalizado(tmp_path):
    """`str(True)` en Python es "True" con mayuscula, que no es lo que espera
    quien lea el CSV con pandas o R."""
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    texto = destino.read_text(encoding="utf-8")
    assert "True" not in texto and "False" not in texto


def test_acentos(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Unión", "Vélez Sarsfield")], destino)
    assert dataset.leer(destino)[0]["home_team"] == "Unión"

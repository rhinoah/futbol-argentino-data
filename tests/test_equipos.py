#!/usr/bin/env python3
"""Tests del padron.

El riesgo especifico de un padron no es que falte un club: es que un alias se le
asigne al club equivocado. Eso no rompe nada -- reparte los partidos de Gimnasia
de La Plata entre los dos Gimnasia y sigue andando. Casi todo lo de abajo apunta
ahi, y se apoya en `afa_snapshot`, que es data de afuera.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from fad import dataset, equipos
from tests.afa_snapshot import AFA, WIKIPEDIA

DATOS = Path(__file__).resolve().parent.parent / "data"


# --------------------------------------------------------------------------
# normalizacion
# --------------------------------------------------------------------------
@pytest.mark.parametrize("a, b", [
    ("Vélez Sarsfield", "velez sarsfield"),
    ("BOCA JUNIORS", "boca juniors"),
    ("  Racing   Club  ", "racing club"),
    ("Dep. Riestra", "dep riestra"),
    ("Indep.Mza.", "indep mza"),
    ("Central Córdoba ( SdE )", "central cordoba (sde)"),
])
def test_normalizar(a, b):
    assert equipos.normalizar(a) == b


def test_las_comillas_raras_son_la_misma_comilla():
    """AFA escribe "Newell`s" con acento grave y Wikipedia con apostrofe. Para
    una comparacion literal son dos clubes distintos."""
    assert equipos.normalizar("Newell`s") == equipos.normalizar("Newell's")
    assert equipos.normalizar("Newell’s") == equipos.normalizar("Newell's")


# --------------------------------------------------------------------------
# el testigo externo: las dos numeraciones tienen que corresponderse
# --------------------------------------------------------------------------
@pytest.mark.parametrize("id_afa, largo, corto", AFA)
def test_los_nombres_de_afa_resuelven(id_afa, largo, corto):
    assert equipos.conocido(largo), f"el padron no conoce {largo!r}"
    assert equipos.conocido(corto), f"el padron no conoce {corto!r}"


@pytest.mark.parametrize("id_afa, largo, corto", AFA)
def test_cada_alias_de_afa_cae_en_el_club_de_ese_id(id_afa, largo, corto):
    """EL test que importa.

    La AFA numera sus clubes con un sistema propio, que no sabe nada de como los
    escribe Wikipedia. Si el alias "Gimnasia" se le asigna por error al de
    Mendoza, resolverlo devuelve un club con `afa=816` y este test cae contra el
    8 que dice el feed. Ninguna otra verificacion lo notaria: los dos clubes
    existen, los dos nombres son plausibles y el dataset se arma igual.
    """
    for nombre in (largo, corto):
        eq = equipos.buscar(nombre)
        assert eq is not None and eq.afa == id_afa, (
            f"{nombre!r} resuelve a {eq.nombre if eq else None!r} "
            f"(afa={eq.afa if eq else None}), pero el feed dice que es el {id_afa}")


@pytest.mark.parametrize("nombre", WIKIPEDIA)
def test_los_nombres_de_wikipedia_resuelven(nombre):
    assert equipos.canonical(nombre) == nombre, "el canonico es el de Wikipedia"


def test_el_padron_cubre_a_los_30_de_primera():
    """Los 30 son el piso, no el total: la Copa Argentina mezcla divisiones y
    trae clubes que no juegan Primera."""
    assert set(WIKIPEDIA) <= {e.nombre for e in equipos.PADRON}


def test_no_hay_dos_clubes_con_el_mismo_nombre():
    nombres = [e.nombre for e in equipos.PADRON]
    assert len(nombres) == len(set(nombres))


def test_los_ids_de_afa_no_se_repiten():
    ids = [e.afa for e in equipos.PADRON if e.afa is not None]
    assert len(ids) == len(set(ids))
    assert set(ids) == {i for i, _, _ in AFA}


# --------------------------------------------------------------------------
# los que se parecen y no son
# --------------------------------------------------------------------------
@pytest.mark.parametrize("nombre, canonico", [
    ("Gimnasia", "Gimnasia y Esgrima (LP)"),
    ("Gimnasia (Mendoza)", "Gimnasia y Esgrima (M)"),
    ("Gimnasia (M)", "Gimnasia y Esgrima (M)"),
    ("Estudiantes", "Estudiantes (LP)"),
    ("Estudiantes RC", "Estudiantes (RC)"),
    ("Independiente", "Independiente"),
    ("Independiente Riv. (M)", "Independiente Rivadavia"),
    ("Indep.Mza.", "Independiente Rivadavia"),
    ("Talleres", "Talleres (C)"),
    ("Sarmiento", "Sarmiento (J)"),
])
def test_los_homonimos_no_se_mezclan(nombre, canonico):
    """"Gimnasia" a secas es el de La Plata; "Estudiantes" a secas es el de La
    Plata; "Independiente" NO es Independiente Rivadavia aunque sea prefijo.
    Emparejar por similitud fallaba justo en estos: 26 de 60 partidos sin par."""
    assert equipos.canonical(nombre) == canonico


def test_los_dos_gimnasia_son_dos_clubes():
    assert equipos.canonical("Gimnasia") != equipos.canonical("Gimnasia (Mendoza)")


def test_los_dos_estudiantes_son_dos_clubes():
    assert equipos.canonical("Estudiantes") != equipos.canonical("Estudiantes (RC)")


def test_independiente_no_es_independiente_rivadavia():
    assert equipos.canonical("Independiente") != equipos.canonical("Independiente Rivadavia")


# --------------------------------------------------------------------------
# el indice no se escribe al lado del padron: se deriva
# --------------------------------------------------------------------------
def test_un_alias_peleado_por_dos_clubes_no_arranca(monkeypatch):
    """Si dos clubes reclaman el mismo alias, tiene que reventar al construir el
    indice. Un alias ambiguo no da error en produccion: le da los partidos al
    club equivocado, calladito."""
    monkeypatch.setattr(equipos, "PADRON", (
        equipos.Equipo("Gimnasia y Esgrima (LP)", 8, ("Gimnasia",)),
        equipos.Equipo("Gimnasia y Esgrima (M)", 816, ("Gimnasia",)),
    ))
    with pytest.raises(ValueError, match="dos clubes"):
        equipos._armar_indice()


def test_el_indice_sale_del_padron_y_no_de_otro_lado(monkeypatch):
    monkeypatch.setattr(equipos, "PADRON", (equipos.Equipo("Inventado FC", 999, ("IFC",)),))
    indice = equipos._armar_indice()
    assert set(indice) == {"inventado fc", "ifc"}


# --------------------------------------------------------------------------
# desconocidos: ruido una vez, no silencio para siempre
# --------------------------------------------------------------------------
def test_un_club_que_no_esta_levanta():
    with pytest.raises(equipos.EquipoDesconocido):
        equipos.canonical("Deportivo Wanderers de Pehuajó")


def test_canonizar_deja_pasar_al_desconocido_tal_cual():
    """`canonizar` corre ANTES de validar. El que no se pudo traducir tiene que
    llegar entero al aviso, porque el aviso existe para decir como venia escrito."""
    raro = "Deportivo Wanderers de Pehuajó"
    assert equipos.canonizar(raro) == raro
    assert not equipos.conocido(raro)


def test_canonizar_traduce_al_que_si_conoce():
    assert equipos.canonizar("Newell`s") == "Newell's Old Boys"


def test_por_afa():
    assert equipos.por_afa(124).nombre == "Belgrano"
    assert equipos.por_afa(999999) is None


# --------------------------------------------------------------------------
# el dataset que se publica
# --------------------------------------------------------------------------
@pytest.mark.skipif(not list(DATOS.glob("partidos-*.csv")),
                    reason="hay que correr build.py primero")
def test_el_csv_publicado_usa_nombres_canonicos():
    nombres = {f[c] for f in dataset.leer_carpeta(DATOS) for c in ("home_team", "away_team")}
    canonicos = {e.nombre for e in equipos.PADRON}
    assert nombres <= canonicos, f"nombres fuera del padron: {sorted(nombres - canonicos)}"


# --------------------------------------------------------------------------
# el articulo manda sobre el nombre visible
# --------------------------------------------------------------------------
def test_el_articulo_desempata_lo_que_el_nombre_no_puede():
    """"Estudiantes" a secas apunta a TRES articulos distintos segun la pagina:
    en Primera es el de La Plata, en Primera B el de Caseros. El nombre no
    alcanza; el articulo si, y ademas no depende de la division ni del anio, asi
    que los ascensos y descensos dejan de importar."""
    assert equipos.canonizar("Estudiantes") == "Estudiantes (LP)"
    assert equipos.canonizar("Estudiantes", "Club Atlético Estudiantes") == "Estudiantes (BA)"
    assert equipos.canonizar("Talleres", "Club Atlético Talleres (Remedios de Escalada)") \
        == "Talleres (RdE)"


def test_sin_articulo_se_cae_al_nombre():
    assert equipos.canonizar("Newell`s", "") == "Newell's Old Boys"


def test_un_articulo_desconocido_no_pisa_al_nombre():
    assert equipos.canonizar("Boca Juniors", "Club Inventado") == "Boca Juniors"


def test_todo_articulo_apunta_a_un_club_del_padron():
    """La guarda que evita la desincronizacion: `ARTICULOS` es una segunda
    estructura, y si apunta a un club que no existe revienta al importar."""
    nombres = {e.nombre for e in equipos.PADRON}
    assert set(equipos.ARTICULOS.values()) <= nombres


def test_el_mapa_de_la_pagina_no_adivina():
    """Si dentro de UNA pagina el mismo nombre visible apunta a dos articulos, no
    hay testigo y no se devuelve ninguno."""
    from fad import parser
    texto = "[[Club A|Equipo]] y [[Club B|Equipo]] y [[Club C|Otro]]"
    assert parser.articulos_de_la_pagina(texto) == {"Otro": "Club C"}


def test_una_tilde_de_menos_no_es_un_desacuerdo():
    """La Primera B 2015 enlaza a Estudiantes de Caseros ocho veces bien y dos
    veces como "Club Atletico Estudiantes", sin la tilde. Es el mismo articulo y
    un typo, pero comparando por igualdad de cadena la guarda lo tomaba por un
    desacuerdo: "Estudiantes" pelado se quedaba sin testigo y caia al nombre
    solo, que en Primera es el de La Plata. Cuarenta y cuatro partidos de Caseros
    quedaron en la historia de un club que nunca jugo esa categoria.

    O sea que la guarda contra adivinar terminaba forzando la adivinanza."""
    from fad import parser
    texto = ("[[Club Atlético Estudiantes|Estudiantes]] "
             "[[Club Atletico Estudiantes|Estudiantes]]")
    assert parser.articulos_de_la_pagina(texto)["Estudiantes"] in (
        "Club Atlético Estudiantes", "Club Atletico Estudiantes")
    # y el club sale bien con cualquiera de las dos grafias
    mapa = parser.articulos_de_la_pagina(texto)
    assert equipos.canonizar("Estudiantes", mapa["Estudiantes"]) == "Estudiantes (BA)"


def test_dos_articulos_de_verdad_distintos_siguen_sin_testigo():
    """El arreglo de arriba no puede aflojar la guarda. La Copa Argentina 2019-20
    tiene un enlace mal puesto -- `[[Club Atlético San Martín (Tucumán)|San Martín
    (SJ)]]`, con la bandera de San Juan al lado -- junto con el correcto. Son dos
    articulos genuinamente distintos, asi que el mapa se tiene que seguir
    callando y dejar que resuelva el nombre, que ahi es el que tiene razon."""
    from fad import parser
    texto = ("[[Club Atlético San Martín (Tucumán)|San Martín (SJ)]] "
             "[[Club Atlético San Martín (San Juan)|San Martín (SJ)]]")
    assert "San Martín (SJ)" not in parser.articulos_de_la_pagina(texto)

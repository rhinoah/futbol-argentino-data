#!/usr/bin/env python3
"""Tests del pipeline: parsear -> normalizar nombres -> validar.

El pegamento tambien se rompe, y calladito: sacar el paso de normalizacion no
hace fallar nada, solo escribe "Newell`s" en el CSV publicado y al mes hay dos
clubes con media historia cada uno.
"""
from __future__ import annotations

import build
from fad.torneos import Torneo

T = Torneo("Anexo:Prueba", "Prueba", 2026)


def tabla(*cruces: tuple[str, str]) -> str:
    filas = "".join(
        f"|-\n|{local}\n|2 - 1\n|{visita}\n|Un Estadio\n|{23 + i} de enero\n|20:00\n"
        for i, (local, visita) in enumerate(cruces))
    return f"""
=== Resultados ===
{{|class="wikitable"
!colspan=6|Fecha 1
|-
!colspan=6|Zona A
|-
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
{filas}|}}

== Otra cosa ==
"""


def test_los_nombres_llegan_al_canonico():
    """Como los escribe la AFA -> como los titula Wikipedia."""
    ps, _ = build.procesar(tabla(("Newell`s", "Gimnasia")), T)
    assert len(ps) == 1
    assert ps[0].local == "Newell's Old Boys"
    assert ps[0].visita == "Gimnasia y Esgrima (LP)"


def test_un_nombre_que_ya_es_canonico_no_se_toca():
    ps, _ = build.procesar(tabla(("Boca Juniors", "River Plate")), T)
    assert (ps[0].local, ps[0].visita) == ("Boca Juniors", "River Plate")


def test_un_club_desconocido_frena_el_build():
    """Grave: `main` no escribe el CSV y queda el dataset de ayer, que estaba
    bien. Es el caso de un ascenso o de un torneo que se suma."""
    ps, avisos = build.procesar(tabla(("Boca Juniors", "Deportivo Inventado")), T)
    graves = [a for a in avisos if a.grave]
    assert graves, "un club fuera del padron tiene que ser un aviso grave"
    assert any("padron" in a.que for a in graves)


def test_el_aviso_dice_como_venia_escrito():
    """Sin el nombre crudo el aviso no sirve: hay que poder buscarlo en la
    pagina para saber que alias agregar."""
    _, avisos = build.procesar(tabla(("Boca Juniors", "Deportivo Inventado")), T)
    assert any("Deportivo Inventado" in a.detalle for a in avisos)


def test_un_alias_no_frena_el_build():
    _, avisos = build.procesar(tabla(("Newell`s", "Gimnasia")), T)
    assert not any("padron" in a.que for a in avisos)


def test_se_normaliza_ANTES_de_validar():
    """El orden de los dos pasos, y por que no da igual.

    Los chequeos que comparan nombres entre si lo hacen por igualdad de cadena.
    Aca Newell's juega dos veces en la Fecha 1, una escrita como la AFA y otra
    como Wikipedia. Normalizando primero son el mismo club y salta el aviso;
    validando primero son dos clubes distintos y no salta nada.

    No es hipotetico: las llaves salen de plantillas y las zonas de tablas, asi
    que en la misma pagina conviven dos maneras de escribir al mismo club.
    """
    _, avisos = build.procesar(
        tabla(("Newell`s", "Boca Juniors"), ("River Plate", "Newell's Old Boys")), T)
    assert any("dos veces" in a.que for a in avisos), (
        "sin normalizar antes, las dos grafias pasan por dos clubes distintos")

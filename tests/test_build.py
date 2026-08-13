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


# --------------------------------------------------------------------------
# el build entero, que es lo que va a correr solo todos los dias
# --------------------------------------------------------------------------
def correr(monkeypatch, tmp_path, pagina: str, argv=()):
    """`build.main` contra una pagina de mentira y un CSV temporal."""
    monkeypatch.setattr(build.torneos, "TODOS", [T])
    monkeypatch.setattr(build.wiki, "wikitexto", lambda *a, **k: pagina)
    monkeypatch.setattr(build, "SALIDA", tmp_path / "data" / "partidos.csv")
    return build.main(list(argv))


def test_el_build_escribe(monkeypatch, tmp_path):
    assert correr(monkeypatch, tmp_path,
                  tabla(("Boca Juniors", "River Plate"), ("Racing Club", "Huracán"))) == 0
    assert len(build.dataset.leer(tmp_path / "data" / "partidos.csv")) == 2


def test_un_club_desconocido_no_escribe_nada(monkeypatch, tmp_path):
    assert correr(monkeypatch, tmp_path, tabla(("Boca Juniors", "Deportivo Inventado"))) == 1
    assert not (tmp_path / "data" / "partidos.csv").exists()


def test_si_el_dataset_se_achica_no_pisa_el_anterior(monkeypatch, tmp_path):
    """La guarda que importa cuando esto corre solo. Los 1 partido que quedan
    pueden estar perfectos: ningun chequeo de `validar` los ve mal, porque
    mirados solos estan bien. Lo unico que delata la perdida es lo de ayer."""
    correr(monkeypatch, tmp_path,
           tabla(("Boca Juniors", "River Plate"), ("Racing Club", "Huracán")))
    assert correr(monkeypatch, tmp_path, tabla(("Boca Juniors", "River Plate"))) == 1
    assert len(build.dataset.leer(tmp_path / "data" / "partidos.csv")) == 2, \
        "pisó el dataset bueno con el achicado"


def test_forzar_deja_pasar_el_achicamiento(monkeypatch, tmp_path):
    """Para cuando la baja es real: Wikipedia saco un partido que no iba."""
    correr(monkeypatch, tmp_path,
           tabla(("Boca Juniors", "River Plate"), ("Racing Club", "Huracán")))
    assert correr(monkeypatch, tmp_path,
                  tabla(("Boca Juniors", "River Plate")), argv=["--forzar"]) == 0
    assert len(build.dataset.leer(tmp_path / "data" / "partidos.csv")) == 1


def test_dry_run_no_escribe(monkeypatch, tmp_path):
    assert correr(monkeypatch, tmp_path, tabla(("Boca Juniors", "River Plate")),
                  argv=["--dry-run"]) == 0
    assert not (tmp_path / "data" / "partidos.csv").exists()


def test_una_pagina_que_no_se_puede_bajar_no_escribe(monkeypatch, tmp_path):
    def explota(*a, **k):
        raise LookupError("no existe")
    monkeypatch.setattr(build.torneos, "TODOS", [T])
    monkeypatch.setattr(build.wiki, "wikitexto", explota)
    monkeypatch.setattr(build, "SALIDA", tmp_path / "data" / "partidos.csv")
    assert build.main([]) == 1
    assert not (tmp_path / "data" / "partidos.csv").exists()


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

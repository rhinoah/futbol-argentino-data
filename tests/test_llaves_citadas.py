#!/usr/bin/env python3
"""Tests de las llaves citadas a mano: el Reducido de la Primera C 2011-12.

Son catorce filas que no salen de ningun lector, asi que lo que hay que sostener
no es codigo sino tres frases de `citadas.Pata`: que los clubes y el marcador los
dice el cuadro de la pagina, que de la fuente citada salen el dia y la localia, y
que una pata mal copiada no entra.

Cada testigo de este archivo esta escrito por OTRA MANO que la tabla que mira --el
cuadro de Wikipedia, los renglones del post, la programacion de esos dias, la tabla
de posiciones--, que es lo unico que hace que un test de datos copiados no sea la
misma tabla escrita dos veces.
"""
from __future__ import annotations

import datetime
import re
from dataclasses import replace

import pytest

import build
from fad import citadas, dataset, equipos, posiciones, torneos

PAGINA = "Campeonato de Primera C 2011-12 (Argentina)"
POST = "http://josecarluccio.blogspot.com/2015/07/argentina-1ra-c-afa-201112-torneo.html"

# El cuadro de la pagina, tal cual lo publica (revision 168417834). La errata de
# la cabecera --`maypo`-- es de la pagina.
CUADRO = """
== Torneo reducido ==

{{Copa de 8 clubes

| RD1= Cuartos de final
| RD2= Semifinal
| RD3= Final
<!--Fechas-->
|cuartos = 28 de maypo al 3 de junio
|semifinal = 6 al 10 de junio
|final = 17 y 21 de junio

<!-- Cuartos de final -->
| RD1-equipo01 = Deportivo Laferrere
| RD1-equipo02 = '''Central Córdoba (R)
| RD1-goles01ida = 1
| RD1-goles02ida = 1
| RD1-goles01vuelta = 1
| RD1-goles02vuelta = 3

| RD1-equipo03 = UAI Urquiza
| RD1-equipo04 = '''Berazategui'''
| RD1-goles03ida = 1
| RD1-goles04ida = 1
| RD1-goles03vuelta = 1
| RD1-goles04vuelta = 3

| RD1-equipo05 = J. J. Urquiza
| RD1-equipo06 = '''Dock Sud'''
| RD1-goles05ida = 0
| RD1-goles06ida = 1
| RD1-goles05vuelta = 0
| RD1-goles06vuelta = 1

| RD1-equipo07 = Defensores de Cambaceres
| RD1-equipo08 = '''Midland'''
| RD1-goles07ida = 1
| RD1-goles08ida = 4
| RD1-goles07vuelta = 1
| RD1-goles08vuelta = 0

<!-- Semifinales -->
| RD2-equipo01 = Berazategui
| RD2-equipo02 = '''Central Córdoba (R)
| RD2-goles01ida = 0
| RD2-goles02ida = 1
| RD2-goles01vuelta = 0
| RD2-goles02vuelta = 1

| RD2-equipo03 = '''Midland'''
| RD2-equipo04 = Dock Sud
| RD2-goles03ida = 1
| RD2-goles04ida = 0
| RD2-goles03vuelta = 0
| RD2-goles04vuelta = 0

<!-- Final -->
| RD3-equipo01 = Midland
| RD3-equipo02 = '''Central Córdoba (R)
| RD3-goles01ida = 1
| RD3-goles02ida = 2
| Dos finales = sí
| RD3-goles01vuelta = 0
| RD3-goles02vuelta = 0
|
}}

== Promociones ==
"""

# Los catorce renglones del post, bajado el 13/10/2026, sin los goleadores:
# `dia en ciudad: local goles, visitante goles`.
DEL_POST = """
28/05/2012 en Libertad: Ferrocarril Midland 4, Defensores de Cambaceres 1
28/05/2012 en Dock Sud: Sportivo Dock Sud 1, Justo José de Urquiza 0
28/05/2012 en Rosario: Central Córdoba de Rosario 1, Deportivo Laferrere 1
29/05/2012 en Berisso: Berazategui 1, UAI Urquiza 1
03/06/2012 en Villa Lynch: UAI Urquiza 1, Berazategui 3
03/06/2012 en Remedios de Escalada: Defensores de Cambaceres 1, Ferrocarril Midland 0
03/06/2012 en Loma Hermosa: Justo José de Urquiza 0, Sportivo Dock Sud 1
03/06/2012 en Gregorio de Laferrere: Deportivo Laferrere 1, Central Córdoba de Rosario 3
06/06/2012 en Remedios de Escalada: Berazategui 0, Central Córdoba de Rosario 1
06/06/2012 en Libertad: Ferrocarril Midland 1, Sportivo Dock Sud 0
09/06/2012 en Dock Sud: Sportivo Dock Sud 0, Ferrocarril Midland 0
10/06/2012 en Rosario: Central Córdoba de Rosario 1, Berazategui 0
17/06/2012 en Libertad: Ferrocarril Midland 1, Central Córdoba de Rosario 2
21/06/2012 en Rosario: Central Córdoba de Rosario 0, Ferrocarril Midland 0
"""
# Como escribe el post a los tres clubes que el padron llama de otra manera.
_EN_EL_POST = {"Sportivo Dock Sud": "Dock Sud",
               "Justo José de Urquiza": "J. J. de Urquiza",
               "Central Córdoba de Rosario": "Central Córdoba (R)"}
_RENGLON = re.compile(r"^(\d\d)/(\d\d)/(\d{4}) en [^:]+: (.+?) (\d+), (.+?) (\d+)$")


def _patas():
    return list(citadas.LLAVES[PAGINA])


def _cruces():
    return posiciones.llaves_del_cuadro(CUADRO, PAGINA)


def _clave(p):
    return (p.fecha, p.local, p.goles_local, p.goles_visita, p.visita)


# ---- la tabla contra el resto del repo ---------------------------------------
def test_las_llaves_citadas_apuntan_a_paginas_del_catalogo_y_a_clubes_del_padron():
    """Una pagina mal escrita no rompe nada: no se aplica nunca, en silencio. Y un
    club que no esta en canonico no cruza con el cuadro, que es peor que no estar."""
    paginas = {t.pagina for t in torneos.TODOS}
    for pagina, patas in citadas.LLAVES.items():
        assert pagina in paginas, f"{pagina!r} no es una pagina del catalogo"
        for p in patas:
            for club in (p.local, p.visita):
                assert equipos.canonizar(club) == club, f"{club!r} no es canonico"
            assert p.fuente.startswith("http"), "el credito va por pata y no hay default"
            assert p.ronda and p.llave


# ---- lo que sale de la fuente citada: el dia y la localia -----------------------
def test_las_catorce_son_los_catorce_renglones_del_post():
    """EL TESTIGO ES EL POST, renglon por renglon, y lo puede contradecir cualquiera
    que lo abra. Una pata de mas, una de menos, un dia corrido o una localia dada
    vuelta se ven aca."""
    del_post = set()
    for renglon in DEL_POST.strip().splitlines():
        d, m, a, local, gl, visita, gv = _RENGLON.match(renglon).groups()
        del_post.add((f"{a}-{m}-{d}", _EN_EL_POST.get(local, local), int(gl), int(gv),
                      _EN_EL_POST.get(visita, visita)))
    assert len(del_post) == 14
    assert {_clave(p) for p in _patas()} == del_post
    assert len(_patas()) == 14, "ninguna repetida"
    assert {p.fuente for p in _patas()} == {POST}


def test_cada_dia_cae_en_la_ronda_que_dice_la_cabecera_del_cuadro():
    """El dia sale del blog y la pagina no lo trae partido por partido, pero SI dice
    cuando se jugo cada ronda: `cuartos = 28 de maypo al 3 de junio`, `semifinal = 6
    al 10 de junio`, `final = 17 y 21 de junio`. Es Wikipedia acotando al blog."""
    ventana = {"Cuartos de final": ("2012-05-28", "2012-06-03"),
               "Semifinal": ("2012-06-06", "2012-06-10"),
               "Final": ("2012-06-17", "2012-06-21")}
    for texto in ("28 de maypo al 3 de junio", "6 al 10 de junio", "17 y 21 de junio"):
        assert texto in CUADRO, "la cabecera es la de la pagina"
    for p in _patas():
        desde, hasta = ventana[p.ronda]
        assert desde <= p.fecha <= hasta, f"{_clave(p)} cae fuera de {p.ronda}"
    assert sorted(p.fecha for p in _patas() if p.ronda == "Final") == [
        "2012-06-17", "2012-06-21"], "la final son esos dos dias y ningun otro"


@pytest.mark.parametrize("fecha, dia, cuantos", [
    ("2012-06-03", 6, 4),      # `Domingo 3 de junio`, las cuatro vueltas de cuartos
    ("2012-06-17", 6, 1),      # `Domingo 17 de junio 15.00-- Midland-Central Córdoba`
    ("2012-06-21", 3, 1),      # `Jueves 21 de junio 21.00-- Central Córdoba-Midland`
])
def test_el_dia_de_la_semana_es_el_de_la_programacion(fecha, dia, cuantos):
    """El blog `Rumores del Ascenso` publico esos dias la programacion con el dia de
    la semana escrito. Un digito mal copiado cambia el dia de la semana."""
    assert datetime.date.fromisoformat(fecha).weekday() == dia
    assert sum(p.fecha == fecha for p in _patas()) == cuantos


def test_el_unico_dia_que_se_aparta_de_la_programacion_es_el_que_tiene_que_ser():
    """La programacion del 25/05 ponia las cuatro idas de cuartos el LUNES 28, con
    Berazategui-UAI Urquiza a las 14. Tres se jugaron ese dia y esa no: a las 23:22
    del 28 el cuadro de la pagina ya tenia los otros tres marcadores y ese casillero
    seguia vacio (revision 56569780), y se lleno el 29 a las 17:05 (56587212). El
    blog citado dice 29. Que sea UNA y sea esa es lo que este test cuida."""
    idas = [p for p in _patas() if p.ronda == "Cuartos de final" and p.fecha < "2012-06-01"]
    assert len(idas) == 4
    fuera_del_lunes = [(p.local, p.visita, p.fecha) for p in idas if p.fecha != "2012-05-28"]
    assert fuera_del_lunes == [("Berazategui", "UAI Urquiza", "2012-05-29")]
    assert datetime.date(2012, 5, 28).weekday() == 0 and datetime.date(2012, 5, 29).weekday() == 1


def test_en_cada_llave_la_localia_alterna_y_define_en_casa_el_mejor_ubicado():
    """EL TESTIGO DE LA LOCALIA QUE NO ES EL POST: la tabla de posiciones. El
    Reducido lo jugaron del segundo al noveno, y el mejor ubicado de cada cruce --el
    de la ventaja deportiva-- jugo la vuelta de local. Lo dice Pagina/12 Rosario del
    06/06/2012 para la serie de Central Cordoba y se cumple en las siete.

    Es lo unico que sostiene, fuera del post, a las dos patas de Midland-Dock Sud:
    Dock Sud fue septimo con 54 puntos y Midland octavo con 53."""
    puesto = {"UAI Urquiza": 2, "Defensores de Cambaceres": 3, "J. J. de Urquiza": 4,
              "Deportivo Laferrere": 5, "Central Córdoba (R)": 6, "Dock Sud": 7,
              "Ferrocarril Midland": 8, "Berazategui": 9}
    llaves: dict = {}
    for p in _patas():
        llaves.setdefault((p.ronda, frozenset((p.local, p.visita))), []).append(p)
    assert len(llaves) == 7
    for (ronda, _), patas in llaves.items():
        ida, vuelta = sorted(patas, key=lambda p: p.fecha)
        assert (ida.local, ida.visita) == (vuelta.visita, vuelta.local), ronda
        assert puesto[vuelta.local] < puesto[ida.local], (
            f"{ronda}: la vuelta la jugo de local {vuelta.local}, que no es el mejor ubicado")


# ---- lo que NO sale de la fuente citada: los clubes y el marcador ---------------
def test_el_cuadro_de_la_pagina_publica_las_siete_llaves_con_esos_marcadores():
    """La condicion para entrar, contra el cuadro de verdad: las catorce pasan y no
    hay nada que avisar."""
    entran, avisos = citadas.segun_el_cuadro(
        citadas.llaves(PAGINA, "Primera C"), _cruces())
    assert avisos == []
    assert len(entran) == 14
    assert len(_cruces()) == 7


@pytest.mark.parametrize("indice", range(14))
def test_un_gol_mal_copiado_deja_afuera_a_la_llave_entera(indice):
    """LAS CATORCE, una por una. `posiciones.marcadores_del_cuadro` se calla en siete
    de estas --cuando la otra pata de la llave tiene el mismo par de numeros, como
    en Dock Sud 1-0 / 0-1-- y esa mitad ciega es justo la razon de que exista
    `segun_el_cuadro`."""
    patas = citadas.llaves(PAGINA, "Primera C")
    rota = patas[indice]
    rota.goles_local += 1
    entran, avisos = citadas.segun_el_cuadro(patas, _cruces())
    assert len(entran) == 12, "no entra ninguna de las dos patas de esa llave"
    cruce = {rota.local, rota.visita}
    assert not any({p.local, p.visita} == cruce for p in entran)
    assert len(avisos) == 1 and "el cuadro de la pagina publica" in avisos[0]


def test_la_ida_y_la_vuelta_con_las_fechas_cruzadas_no_entran(monkeypatch):
    """El cuadro dice cual marcador es el de la ida y cual el de la vuelta, asi que
    una cita con los dos dias intercambiados tampoco pasa. Midland 4-1 Cambaceres
    fue la ida; puesto como vuelta, el par de marcadores es el mismo y el orden no."""
    cruzadas = {"2012-05-28": "2012-06-03", "2012-06-03": "2012-05-28"}
    patas = tuple(
        replace(p, fecha=cruzadas[p.fecha])
        if {p.local, p.visita} == {"Ferrocarril Midland", "Defensores de Cambaceres"}
        else p for p in _patas())
    monkeypatch.setitem(citadas.LLAVES, PAGINA, patas)
    entran, avisos = citadas.segun_el_cuadro(
        citadas.llaves(PAGINA, "Primera C"), _cruces())
    assert len(entran) == 12 and len(avisos) == 1
    assert "1-4, 1-0 y la cita 1-0, 1-4" in avisos[0]


def test_un_cruce_que_el_cuadro_no_publica_no_entra():
    """Una llave citada que la pagina no dibuja no tiene quien le diga los clubes ni
    el marcador: seria una fila entera salida de un blog, que es lo que este
    mecanismo no hace."""
    patas = citadas.llaves(PAGINA, "Primera C")
    for p in patas:
        if p.local == "Dock Sud":
            p.local = "Excursionistas"
        elif p.visita == "Dock Sud":
            p.visita = "Excursionistas"
    entran, avisos = citadas.segun_el_cuadro(patas, _cruces())
    assert not any("Excursionistas" in (p.local, p.visita) for p in entran)
    assert len(entran) == 10, "las dos llaves de Dock Sud, cuatro patas"
    assert len(avisos) == 2 and all("no publica ese cruce" in a for a in avisos)


# ---- el punto de llamada -----------------------------------------------------
_PAGINA_CON_CUADRO = """
== Resultados ==
{|class="wikitable"
!colspan=6|Fecha 1
|-
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Boca Juniors
|2 - 1
|River Plate
|Un Estadio
|3 de marzo
|
|}

== Final ==
{{Copa de 2 clubes
| RD1= Final
| RD1-equipo01 = Boca Juniors
| RD1-equipo02 = River Plate
| RD1-goles01ida = 0
| RD1-goles02ida = 1
| RD1-goles01vuelta = 2
| RD1-goles02vuelta = 2
}}

== Otra cosa ==
"""


def _final(gl_ida=1):
    cita = "https://example.org/la-final"
    return (citadas.Pata("2012-06-10", "River Plate", "Boca Juniors", gl_ida, 0, "Final",
                         llave="Final", fuente=cita),
            citadas.Pata("2012-06-17", "Boca Juniors", "River Plate", 2, 2, "Final",
                         llave="Final", fuente=cita))


def test_el_build_las_importa_con_su_credito(monkeypatch):
    """Por `procesar`, que es donde se decide que entra: las dos patas pasan a ser
    filas de eliminacion, con la ronda en `matchday` y la URL citada en `source`."""
    from fad.torneos import Torneo

    t = Torneo("Anexo:Prueba", "Prueba", 2012)
    monkeypatch.setitem(citadas.LLAVES, "Anexo:Prueba", _final())
    ps, avisos = build.procesar(_PAGINA_CON_CUADRO, t)
    llaves = [p for p in ps if p.fase == "eliminacion"]
    assert [(p.fecha, p.local, p.goles_local, p.goles_visita, p.visita, p.jornada)
            for p in llaves] == [
        ("2012-06-10", "River Plate", 1, 0, "Boca Juniors", "Final"),
        ("2012-06-17", "Boca Juniors", 2, 2, "River Plate", "Final")]
    fila = dataset.a_fila(llaves[0], t.torneo, t.temporada, t.url, t.neutral)
    assert fila["source"] == t.url + dataset.SEPARADOR + "https://example.org/la-final"
    assert not any(a.grave for a in avisos), [str(a) for a in avisos if a.grave]


def test_el_build_no_importa_la_llave_que_el_cuadro_desmiente(monkeypatch):
    """Y lo dice: una fila que desaparece callada es el peor de los dos errores."""
    from fad.torneos import Torneo

    t = Torneo("Anexo:Prueba", "Prueba", 2012)
    monkeypatch.setitem(citadas.LLAVES, "Anexo:Prueba", _final(gl_ida=3))
    ps, avisos = build.procesar(_PAGINA_CON_CUADRO, t)
    assert [p for p in ps if p.fase == "eliminacion"] == []
    assert any("llaves citadas a mano" in str(a) and "publica 0-1, 2-2" in str(a)
               for a in avisos), [str(a) for a in avisos]


def test_sin_llaves_citadas_el_build_ni_mira_el_cuadro(monkeypatch):
    """Son 170 paginas y una sola tiene llaves citadas: en las demas no hay nada que
    preguntarle al cuadro, y preguntarselo igual es un aviso de mas por pagina."""
    from fad.torneos import Torneo

    def explotar(*a, **k):
        raise AssertionError("no se tiene que llamar")

    monkeypatch.setattr(citadas, "segun_el_cuadro", explotar)
    build.procesar(_PAGINA_CON_CUADRO, Torneo("Anexo:Otra", "Prueba", 2012))


def test_las_catorce_filas_publicadas_son_las_catorce_citadas():
    """El dato publicado contra la tabla: en `data/` las filas del Reducido son
    estas catorce, con este credito, y ninguna otra fila de la pagina lo lleva."""
    import csv
    from pathlib import Path

    ruta = Path(__file__).resolve().parent.parent / "data" / "partidos-2011.csv"
    with open(ruta, encoding="utf-8", newline="") as f:
        filas = [x for x in csv.DictReader(f) if x["source"].endswith(POST)]
    assert {(x["date"], x["home_team"], int(x["home_score"]), int(x["away_score"]),
             x["away_team"]) for x in filas} == {_clave(p) for p in _patas()}
    assert len(filas) == 14
    assert {x["phase"] for x in filas} == {"eliminacion"}
    assert {x["matchday"] for x in filas} == {"Cuartos de final", "Semifinal", "Final"}

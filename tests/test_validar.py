#!/usr/bin/env python3
"""Tests del validador.

Un chequeo que nunca dispara es peor que no tenerlo: da la sensacion de que algo
se esta mirando. Asi que cada uno se prueba de los dos lados -- que se queje con
datos rotos y que se calle con datos sanos.
"""
from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from fad import dataset, torneos, validar
from fad.parser import Partido


def zona(local, visita, gl=1, gv=0, *, fecha="2026-03-01", z="Zona A", j="Fecha 1"):
    return Partido(fecha=fecha, local=local, visita=visita, goles_local=gl,
                   goles_visita=gv, fase="zonas", zona=z, jornada=j)


def llave(local, visita, gl, gv, fecha, pl=None, pv=None, ronda="Octavos"):
    return Partido(fecha=fecha, local=local, visita=visita, goles_local=gl,
                   goles_visita=gv, penales_local=pl, penales_visita=pv,
                   fase="eliminacion", jornada=ronda)


# Clubes de verdad: `validar.nombres_en_el_padron` rechaza los inventados, y con
# razon. Van escritos a mano y no sacados de `equipos.PADRON` para no atar estos
# tests, que son de otra cosa, a la estructura del padron.
CLUBES = ("Boca Juniors", "River Plate", "Racing Club", "Independiente",
          "San Lorenzo", "Huracán", "Tigre", "Platense")


def torneo_de(n: int, jornada="Fecha 1") -> list[Partido]:
    """UNA jornada de un torneo de `n` equipos (n par): cada uno juega una vez."""
    eq = list(CLUBES[:n])
    return [zona(eq[i], eq[i + n // 2], j=jornada) for i in range(n // 2)]


def zona_entera(n: int) -> list[Partido]:
    """Un todos-contra-todos terminado, con su calendario: `n-1` jornadas y cada
    equipo jugando una vez en cada una. Es lo unico que no le debe una
    explicacion a ningun chequeo, asi que hay que armarlo bien -- el fixture
    anterior repartia los cruces de cualquier manera y hacia jugar a uno tres
    veces en la Fecha 1."""
    eq = list(CLUBES[:n])
    fijo, rueda = eq[0], eq[1:]
    partidos = []
    for j in range(n - 1):                      # metodo del circulo
        vuelta = [fijo] + rueda
        for i in range(n // 2):
            local, visita = vuelta[i], vuelta[n - 1 - i]
            partidos.append(zona(local, visita, fecha=f"2026-03-{j + 1:02d}",
                                 j=f"Fecha {j + 1}"))
        rueda = rueda[1:] + rueda[:1]
    return partidos


# --------------------------------------------------------------------------
def test_sano_no_avisa_nada():
    assert validar.revisar(zona_entera(4)) == []


def test_torneo_en_curso_avisa_pero_no_frena():
    """Un torneo a mitad de camino incumple el todos-contra-todos y esta bien:
    el Clausura 2026 va por la Fecha 4. Tiene que avisar SIN gravedad, porque un
    aviso grave no escribe el CSV y el dataset se quedaria sin actualizar todas
    las semanas hasta que termine el torneo."""
    avisos = validar.revisar(torneo_de(4))
    assert avisos, "algo tiene que decir: la zona no esta completa"
    assert not any(a.grave for a in avisos)


# --------------------------------------------------------------------------
# campos completos
# --------------------------------------------------------------------------
@pytest.mark.parametrize("roto, texto", [
    (Partido(fecha="2026-03-01", local="", visita="Boca", goles_local=1,
             goles_visita=0, fase="zonas", zona="Zona A"), "sin equipos"),
    (Partido(fecha="2026-03-01", local="Boca", visita="River",
             fase="zonas", zona="Zona A"), "sin marcador"),
    (Partido(fecha="2026-03-01", local="Boca", visita="River", goles_local=99,
             goles_visita=0, fase="zonas", zona="Zona A"), "inverosimil"),
])
def test_campos_completos_avisa(roto, texto):
    avisos = validar.campos_completos([roto])
    assert avisos and texto in avisos[0].que
    assert avisos[0].grave


def test_los_partidos_sin_fecha_avisan_pero_no_frenan():
    """Se van del dataset -- el esquema promete una fecha en cada fila -- pero el
    aviso los nombra: ocho filas de cinco mil no justifican frenar el build, y las
    dos causas (una rareza de la fuente o el parser leyendo mal) se parecen."""
    sin = Partido(fecha="", local="Boca", visita="River", goles_local=1,
                  goles_visita=0, fase="zonas", zona="Zona A")
    avisos = validar.fechas_presentes([sin])
    assert len(avisos) == 1 and not avisos[0].grave
    assert "Boca" in avisos[0].detalle and "1 partidos" in avisos[0].que


def test_con_fecha_no_dice_nada():
    assert validar.fechas_presentes(torneo_de(4)) == []


def test_campos_completos_calla():
    assert validar.campos_completos(torneo_de(4)) == []


# --------------------------------------------------------------------------
# penales
# --------------------------------------------------------------------------
def test_penales_en_un_partido_que_no_empato():
    """La firma de haber leido el entretiempo como si fuera la tanda."""
    p = llave("River", "San Lorenzo", 2, 0, "2026-05-17", pl=4, pv=3)
    avisos = validar.penales_solo_en_empates([p])
    assert len(avisos) == 1 and avisos[0].grave


def test_penales_sobre_un_empate_estan_bien():
    p = llave("River", "San Lorenzo", 1, 1, "2026-05-17", pl=4, pv=3)
    assert validar.penales_solo_en_empates([p]) == []


# --------------------------------------------------------------------------
# duplicados y contra si mismo
# --------------------------------------------------------------------------
def test_duplicados():
    p = zona("Boca", "River")
    assert len(validar.sin_duplicados([p, p])) == 1
    assert validar.sin_duplicados([p]) == []


def test_mismo_partido_en_fechas_distintas_no_es_duplicado():
    """Se juegan dos veces: ida y vuelta."""
    ida = zona("Boca", "River", fecha="2026-03-01")
    vuelta = zona("Boca", "River", fecha="2026-08-01")
    assert validar.sin_duplicados([ida, vuelta]) == []


def test_contra_si_mismo():
    assert len(validar.nadie_juega_contra_si_mismo([zona("Boca", "Boca")])) == 1
    assert validar.nadie_juega_contra_si_mismo([zona("Boca", "River")]) == []


# --------------------------------------------------------------------------
# zonas
# --------------------------------------------------------------------------
# --------------------------------------------------------------------------
# el padron
# --------------------------------------------------------------------------
def test_un_club_fuera_del_padron_es_grave():
    avisos = validar.nombres_en_el_padron([zona("Boca Juniors", "Deportivo Inventado")])
    assert len(avisos) == 1 and avisos[0].grave
    assert "Deportivo Inventado" in avisos[0].detalle


def test_los_clubes_del_padron_no_avisan():
    assert validar.nombres_en_el_padron(torneo_de(4)) == []


def test_un_alias_conocido_tampoco_avisa():
    """`canonizar` corre antes, pero el chequeo tiene que aceptar el alias igual:
    si no, el orden de los pasos se vuelve una trampa silenciosa."""
    assert validar.nombres_en_el_padron([zona("Newell`s", "Gimnasia")]) == []


def test_avisa_una_vez_por_club_y_no_por_partido():
    """Un club nuevo juega 16 partidos. Dieciseis avisos identicos tapan todo lo
    demas que el build tenga para decir."""
    ps = [zona("Deportivo Inventado", "Boca Juniors"),
          zona("River Plate", "Deportivo Inventado", fecha="2026-03-08")]
    avisos = validar.nombres_en_el_padron(ps)
    assert len(avisos) == 1


def test_zonas_a_medias():
    """Lo que delata un encabezado no reconocido es la MEZCLA, no el vacio: la
    zona se arrastra de fila en fila, asi que unos partidos quedan con etiqueta y
    otros no."""
    ps = [zona("Boca", "River", z="Zona A"), zona("Racing", "Independiente", z="")]
    avisos = validar.todos_tienen_zona(ps)
    assert len(avisos) == 1 and avisos[0].grave


def test_un_torneo_entero_sin_zonas_esta_bien():
    """De 2017 a 2024 el campeonato fue de zona unica: veintipico de equipos en
    una sola tabla, sin ningun encabezado de zona. Exigirle una zona convertia
    nueve temporadas correctas en nueve errores graves que frenaban el build."""
    ps = [zona("Boca", "River", z=""), zona("Racing", "Independiente", z="")]
    assert validar.todos_tienen_zona(ps) == []


def test_eliminacion_sin_zona_esta_bien():
    """La fase de eliminacion no tiene zonas, y no se le reclama una."""
    assert validar.todos_tienen_zona([llave("Boca", "River", 1, 0, "2026-05-17")]) == []


def test_zona_despareja():
    eq = ["A", "B", "C", "D"]
    ps = [zona(eq[0], eq[1]), zona(eq[0], eq[2]), zona(eq[0], eq[3])]
    avisos = validar.zonas_completas(ps)
    assert len(avisos) == 1 and not avisos[0].grave


def test_zona_todos_contra_todos_completa():
    eq = ["A", "B", "C", "D"]
    ps = [zona(a, b) for i, a in enumerate(eq) for b in eq[i + 1:]]
    assert validar.zonas_completas(ps) == []


def test_al_interzonal_no_se_le_pide_que_cierre():
    """Cruza equipos de zonas distintas: no tiene por que ser un todos-contra-
    todos, y exigirselo llenaba la salida de ruido."""
    ps = [zona("A", "B", z="Interzonal"), zona("A", "C", z="Interzonal")]
    assert validar.zonas_completas(ps) == []


# --------------------------------------------------------------------------
# una vez por jornada -- el que agarra las etiquetas corridas
# --------------------------------------------------------------------------
def test_nadie_juega_dos_veces_en_la_misma_fecha():
    ps = torneo_de(4) + [zona(CLUBES[0], CLUBES[3], j="Fecha 1")]
    avisos = validar.una_vez_por_jornada(ps)
    assert len(avisos) == 1 and avisos[0].grave
    assert CLUBES[0] in avisos[0].detalle


def test_jugar_una_vez_por_fecha_esta_bien():
    ps = torneo_de(6, "Fecha 1") + torneo_de(6, "Fecha 2")
    assert validar.una_vez_por_jornada(ps) == []


def test_una_jornada_postergada_no_es_un_error():
    """La Fecha 9 del Apertura 2026 se jugo entera en mayo, dos meses despues de
    la 10. Esta bien. El chequeo cronologico que probamos primero se quejaba de
    eso Y ADEMAS no veia el bug real; este no depende del calendario."""
    tarde = [zona(p.local, p.visita, fecha="2026-05-02", j="Fecha 9")
             for p in torneo_de(6)]
    temprano = [zona(p.local, p.visita, fecha="2026-03-10", j="Fecha 10")
                for p in torneo_de(6)]
    assert validar.una_vez_por_jornada(tarde + temprano) == []


# --------------------------------------------------------------------------
# huecos y anios mal puestos
# --------------------------------------------------------------------------
def test_falta_una_jornada_en_el_medio():
    """La pagina del campeonato 2019-20 no tiene la Fecha 4: no esta escrita,
    faltan sus 12 partidos en la fuente. No es culpa del parser, pero un hueco en
    el medio de una temporada es indistinguible de "el modelo no vio esos
    partidos" para quien use el dataset."""
    ps = (torneo_de(4, "Fecha 1") + torneo_de(4, "Fecha 2") + torneo_de(4, "Fecha 4"))
    avisos = validar.jornadas_sin_huecos(ps)
    assert len(avisos) == 1 and not avisos[0].grave
    assert "3" in avisos[0].detalle


def test_jornadas_seguidas_no_avisan():
    ps = torneo_de(4, "Fecha 1") + torneo_de(4, "Fecha 2") + torneo_de(4, "Fecha 3")
    assert validar.jornadas_sin_huecos(ps) == []


QUE_JORNADA = "una jornada cae medio anio antes que la anterior"
QUE_RONDA = "una ronda cae medio anio antes que la anterior"
QUE_SECCION = "una seccion entera cae medio anio antes que la anterior"
QUE_FINAL = "una ronda de eliminacion antes de que empiece la fase de zonas"


def _jornada(n, fecha, *, llave="", z="Zona A", equipos=6):
    """Una jornada entera jugada el mismo dia: `equipos / 2` partidos. Tres por
    defecto: con menos, el chequeo la trata como jornada chica."""
    return [Partido(fecha=fecha, local=p.local, visita=p.visita, goles_local=1,
                    goles_visita=0, fase="zonas", llave=llave, zona=z,
                    jornada=f"Fecha {n}") for p in torneo_de(equipos)]


def _ronda(nombre, fecha, *, llave="", partidos=2):
    eq = CLUBES[:partidos * 2]
    return [Partido(fecha=fecha, local=eq[2 * i], visita=eq[2 * i + 1], goles_local=1,
                    goles_visita=0, fase="eliminacion", llave=llave, jornada=nombre)
            for i in range(partidos)]


# ---- pista 1: las jornadas de cada grupo ----------------------------------
def test_una_jornada_un_anio_fuera_de_lugar():
    """El caso de la 2019-20 con el corte en el mes equivocado: la Fecha 1 entera
    fechada doce meses adelante, coherente consigo misma y con el marcador bien."""
    ps = _jornada(1, "2020-07-26") + _jornada(2, "2019-08-02")
    avisos = validar.anios_bien_asignados(ps)
    assert len(avisos) == 1 and avisos[0].grave


def test_una_postergacion_de_dos_meses_no_es_un_anio_mal_puesto():
    """La Fecha 9 del Apertura 2026 se jugo entera dos meses despues de la 10 y
    esta perfecta. El umbral es generoso justamente por esto."""
    ps = _jornada(9, "2026-05-02") + _jornada(10, "2026-03-10")
    assert validar.anios_bien_asignados(ps) == []


def test_la_postergacion_MAS_LARGA_que_existe_no_es_un_anio_mal_puesto():
    """El borde de abajo del umbral, con el caso real: la Fecha 7 de la B Nacional
    2016-17 se jugo entera el 14 y 15 de marzo de 2017, 158 dias despues de la 8."""
    ps = _jornada(7, "2017-03-15") + _jornada(8, "2016-10-08")
    assert validar.anios_bien_asignados(ps) == []


def test_revisar_SI_corre_el_chequeo_de_los_anios():
    """Todos los tests de este chequeo lo llaman a mano. El build llama a
    `revisar`, que recorre la lista `CHEQUEOS`: sacandolo de esa lista la suite
    entera pasaba, y el dia que hiciera falta no corria."""
    ps = _jornada(1, "2020-07-26") + _jornada(2, "2019-08-02")
    assert QUE_JORNADA in [a.que for a in validar.revisar(ps) if a.grave]


def test_la_liga_comun_SIN_llave_ni_zona_tambien_se_mira():
    """98 de las 170 paginas son esto: un todos contra todos sin zonas y sin
    secciones, donde `llave` y `zona` vienen vacias. Un chequeo que mirara solo
    los grupos CON nombre dejaria ciegas a seis de cada diez.

    Y fija lo que dice el aviso: sin donde, no queda un ": " colgado adelante."""
    ps = (_jornada(1, "2020-07-26", z="") + _jornada(2, "2019-08-02", z="")
          + _jornada(3, "2019-08-09", z=""))
    avisos = validar.anios_bien_asignados(ps)
    assert [(a.que, a.grave) for a in avisos] == [(QUE_JORNADA, True)]
    assert avisos[0].detalle.startswith("Fecha 2 en 2019-08-02 contra Fecha 1 en 2020-07-26;")


def test_con_zona_y_sin_llave_el_aviso_dice_la_zona_a_secas():
    ps = _jornada(1, "2020-07-26") + _jornada(2, "2019-08-02")
    avisos = validar.anios_bien_asignados(ps)
    assert len(avisos) == 1
    assert avisos[0].detalle.startswith("Zona A: Fecha 2 en 2019-08-02 contra Fecha 1")


def test_el_apertura_y_el_clausura_NO_se_juntan_por_numero_de_fecha():
    """LA CEGUERA CON LA QUE NACIO ESTE CHEQUEO, y es la Primera C 2019-20 tal cual.

    La pagina trae el Apertura y el Clausura, los dos con su "Fecha 1". La Fecha 1
    del Apertura se jugo en julio de 2019 y salia fechada en julio de 2020. Juntando
    por numero, esos partidos caian en la misma bolsa que la Fecha 1 del Clausura
    -- de enero de 2020, y con mas partidos --: el del medio de la bolsa era de
    enero y no desentonaba con nada. Ocho filas un anio corridas, publicadas dos
    meses.

    Mirando cada torneo por separado la Fecha 2 del Apertura queda 358 dias antes
    que su Fecha 1."""
    apertura = dict(llave="Torneo Apertura", z="Torneo Apertura")
    clausura = dict(llave="Torneo Clausura", z="Torneo Clausura", equipos=8)
    ps = (_jornada(1, "2020-07-27", **apertura) + _jornada(2, "2019-08-04", **apertura)
          + _jornada(3, "2019-08-11", **apertura) + _jornada(4, "2019-08-18", **apertura)
          + _jornada(1, "2020-01-27", **clausura) + _jornada(2, "2020-02-01", **clausura)
          + _jornada(3, "2020-02-08", **clausura) + _jornada(4, "2020-02-15", **clausura))
    avisos = validar.anios_bien_asignados(ps)
    assert len(avisos) == 1 and avisos[0].grave, [str(a) for a in avisos]
    assert avisos[0].detalle.startswith("Torneo Apertura: Fecha 2 en 2019-08-04"), \
        "dice de que torneo es, y una sola vez aunque la zona se llame igual"


def test_dos_fases_con_grupos_del_mismo_nombre_tampoco_se_juntan():
    """La otra pagina que paso de largo, la Copa de la Liga 2020: una Fase
    Clasificatoria y una Fase Campeonato, las dos con su "Grupo A" y su "Fecha 4".
    La Fecha 4 de la segunda era de enero de 2021 y salia en enero de 2020; mezclada
    con la Fecha 4 de la primera, de noviembre, no se veia."""
    ps = (_jornada(3, "2020-11-14", llave="Fase Clasificatoria", z="Grupo A", equipos=8)
          + _jornada(4, "2020-11-21", llave="Fase Clasificatoria", z="Grupo A", equipos=8)
          + _jornada(3, "2020-12-27", llave="Fase Campeonato", z="Grupo A")
          + _jornada(4, "2020-01-03", llave="Fase Campeonato", z="Grupo A"))
    avisos = validar.anios_bien_asignados(ps)
    assert len(avisos) == 1, [str(a) for a in avisos]
    assert "Fase Campeonato Grupo A: Fecha 4 en 2020-01-03" in avisos[0].detalle


def test_dos_grupos_de_la_misma_fase_tampoco_se_juntan():
    """Y adentro de una fase, cada grupo es su propia pista: el Grupo B, sano y con
    mas partidos, no tapa al Grupo A."""
    ps = (_jornada(3, "2020-12-27", llave="Fase Campeonato", z="Grupo A")
          + _jornada(4, "2020-01-03", llave="Fase Campeonato", z="Grupo A")
          + _jornada(3, "2020-12-28", llave="Fase Campeonato", z="Grupo B", equipos=8)
          + _jornada(4, "2021-01-04", llave="Fase Campeonato", z="Grupo B", equipos=8))
    avisos = validar.anios_bien_asignados(ps)
    assert len(avisos) == 1, [str(a) for a in avisos]
    assert "Grupo A" in avisos[0].detalle


def test_las_jornadas_van_por_NUMERO_aunque_la_pagina_las_traiga_en_otro_orden():
    """Una pagina puede publicar la Fecha 2 antes que la 1. Lo que tiene orden es
    el numero: recorridas como vienen, una temporada sana de agosto a mayo parece
    ir para atras."""
    ps = _jornada(2, "2020-05-17") + _jornada(1, "2019-08-01")
    assert validar.anios_bien_asignados(ps) == []


def test_la_Fecha_10_va_despues_de_la_9_y_no_entre_la_1_y_la_2():
    """"Por numero" es por NUMERO. Ordenadas como texto las fechas quedan 1, 10,
    11, ..., 19, 2, 20, ...: en una temporada de 38 fechas la 3 aparece despues de
    la 29, siete meses para atras. Con ese error el dataset sano da mas de cien
    avisos graves."""
    from datetime import date, timedelta
    primera = date(2007, 8, 11)
    ps = [p for n in range(1, 39)
          for p in _jornada(n, (primera + timedelta(weeks=n - 1)).isoformat(), z="")]
    assert validar.anios_bien_asignados(ps) == []


def test_el_grupo_se_mira_ENTERO_y_no_solo_sus_dos_primeras_fechas():
    ps = (_jornada(1, "2019-08-03") + _jornada(2, "2019-08-10") + _jornada(3, "2019-08-17")
          + _jornada(4, "2018-08-24") + _jornada(5, "2019-08-31"))
    avisos = validar.anios_bien_asignados(ps)
    assert [a.que for a in avisos] == [QUE_JORNADA], [str(a) for a in avisos]
    assert "Fecha 4 en 2018-08-24 contra Fecha 3 en 2019-08-17" in avisos[0].detalle


def test_dos_saltos_en_un_mismo_grupo_son_dos_avisos():
    ps = (_jornada(1, "2020-07-27") + _jornada(2, "2019-08-04")
          + _jornada(3, "2020-08-11") + _jornada(4, "2019-08-18"))
    avisos = validar.anios_bien_asignados(ps)
    assert [a.detalle[:16] for a in avisos] == ["Zona A: Fecha 2 ", "Zona A: Fecha 4 "]


def test_un_partido_suelto_fuera_de_lugar_no_mueve_a_su_jornada():
    """Se compara el DEL MEDIO: lo que se busca es la jornada entera corrida. Un
    partido adelantado lejos de los suyos -- que los hay, y estan bien -- no puede
    hacer que toda la fecha parezca de otro anio."""
    ps = (_jornada(1, "2019-08-03", equipos=8) + _jornada(2, "2019-08-10", equipos=8))
    ps[4].fecha = "2018-08-10"            # el primero de la Fecha 2, un anio antes
    assert validar.anios_bien_asignados(ps) == []


def test_un_partido_POSTERGADO_lejos_tampoco_mueve_a_su_jornada():
    """El caso de todos los dias es el otro: un partido postergado meses, que la
    pagina deja en su jornada. Mirando el ultimo partido de la jornada en vez del
    del medio, la Fecha 2 parece caer nueve meses antes que la 1."""
    ps = _jornada(1, "2019-08-03", equipos=8) + _jornada(2, "2019-08-10", equipos=8)
    ps[2].fecha = "2020-05-02"            # el tercero de la Fecha 1, nueve meses despues
    assert validar.anios_bien_asignados(ps) == []


def test_un_partido_postergado_siete_meses_no_es_un_anio_mal_puesto():
    """Con uno o dos partidos, "el del medio" es un partido, y un partido se
    posterga. El grupo `Interzonal` de las ligas de dos zonas tiene casi todas sus
    fechas de un partido: un solo interzonal jugado siete meses tarde no puede ser
    un GRAVE, que frena la actualizacion de todas las paginas. Lo mismo una zona de
    cuatro equipos, que juega de a dos: con dos, el del medio es el mas tardio.

    Se comparan igual, pero se les pide ocho meses y no seis."""
    interzonal = dict(z="Interzonal", equipos=2)
    ps = (_jornada(1, "2026-07-25", **interzonal) + _jornada(2, "2027-03-06", **interzonal)
          + _jornada(3, "2026-08-08", **interzonal))
    assert validar.anios_bien_asignados(ps) == []

    de_a_dos = (_jornada(1, "2019-08-03", equipos=4) + _jornada(2, "2019-08-10", equipos=4)
                + _jornada(3, "2019-08-17", equipos=4))
    de_a_dos[3].fecha = "2020-03-14"      # el segundo de la Fecha 2, siete meses despues
    assert validar.anios_bien_asignados(de_a_dos) == []


def test_una_jornada_chica_corrida_UN_ANIO_si_se_ve():
    """La primera idea fue no compararlas, y fue peor: zonas de cuatro equipos y
    el `Interzonal` quedaban sin ninguna comparacion -- 47 grupos de 17 torneos --,
    y dos de los tres errores historicos se avisaban uno y dos dias mas tarde.

    Un anio mal puesto da mas de 280 dias aun entre una fecha de marzo y una de
    diciembre, que es el caso mas apretado."""
    interzonal = dict(z="Interzonal", equipos=2)
    un_anio = (_jornada(5, "2026-08-22", **interzonal) + _jornada(6, "2025-08-29", **interzonal)
               + _jornada(7, "2026-09-05", **interzonal))
    avisos = validar.anios_bien_asignados(un_anio)
    assert [(a.que, a.grave) for a in avisos] == [(QUE_JORNADA, True)], [str(a) for a in avisos]
    assert "Interzonal: Fecha 6 en 2025-08-29 contra Fecha 5 en 2026-08-22" in avisos[0].detalle

    marzo_y_diciembre = (_jornada(1, "2026-12-12", **interzonal)
                         + _jornada(2, "2026-03-07", **interzonal))
    assert [a.que for a in validar.anios_bien_asignados(marzo_y_diciembre)] == [QUE_JORNADA]


def test_la_unica_jornada_grande_de_un_grupo_de_jornadas_chicas_tambien_se_mira():
    """El `Interzonal` no es todo de un partido: tiene UNA fecha en la que cruzan
    todos (15 partidos en el Clausura 2026). Si las chicas no se compararan, esa
    seria la unica de su grupo y no habria contra que mirarla."""
    interzonal = dict(z="Interzonal")
    ps = (_jornada(5, "2026-08-22", equipos=2, **interzonal)
          + _jornada(6, "2025-08-29", equipos=8, **interzonal)
          + _jornada(7, "2026-09-05", equipos=2, **interzonal))
    avisos = validar.anios_bien_asignados(ps)
    assert [a.que for a in avisos] == [QUE_JORNADA], [str(a) for a in avisos]
    assert "Fecha 6 en 2025-08-29 contra Fecha 5 en 2026-08-22" in avisos[0].detalle


def test_una_jornada_a_medio_jugar_no_apaga_al_resto_de_su_grupo():
    """El estado de todas las semanas en un torneo en curso: de la ultima fecha hay
    uno o dos partidos jugados."""
    ps = (_jornada(1, "2020-07-27") + _jornada(2, "2019-08-04") + _jornada(3, "2019-08-11")
          + _jornada(4, "2019-08-18", equipos=2))
    avisos = validar.anios_bien_asignados(ps)
    assert [a.que for a in avisos] == [QUE_JORNADA], [str(a) for a in avisos]
    assert "Fecha 2 en 2019-08-04 contra Fecha 1 en 2020-07-27" in avisos[0].detalle


def test_alcanza_con_que_UNA_de_las_dos_jornadas_sea_chica():
    """De la Fecha 4 hay un solo partido con fecha, postergado siete meses (o
    adelantado siete meses). La 3 y la 5 estan enteras. Ni la 4 contra la 3 ni la 5
    contra la 4 son un anio mal puesto: en las dos comparaciones hay un partido
    suelto de un lado."""
    for suelto in ("2027-03-06", "2026-01-10"):
        ps = (_jornada(1, "2026-07-25") + _jornada(2, "2026-08-01") + _jornada(3, "2026-08-08")
              + _jornada(4, suelto, equipos=2) + _jornada(5, "2026-08-22"))
        assert validar.anios_bien_asignados(ps) == [], suelto


def test_con_tres_partidos_ya_es_una_jornada():
    """El borde de `_JORNADA_CHICA`: tres partidos, 200 dias para atras, avisa. Con
    dos se le pedirian 240."""
    assert [a.que for a in validar.anios_bien_asignados(
        _jornada(1, "2020-02-20") + _jornada(2, "2019-08-04"))] == [QUE_JORNADA]
    assert validar.anios_bien_asignados(
        _jornada(1, "2020-02-20", equipos=4) + _jornada(2, "2019-08-04", equipos=4)) == []


# ---- pista 2: las rondas de cada llave -------------------------------------
def test_una_ronda_de_eliminacion_despues_de_la_que_le_sigue():
    """La Copa Argentina 2011-12: los treintaidosavos, de noviembre de 2011, salian
    fechados en noviembre de 2012 -- despues de la final --. La eliminacion no la
    miraba nadie: el chequeo era solo para la fase de zonas."""
    mal = (_ronda("Treintaidosavos", "2012-11-29", partidos=4)
           + _ronda("Dieciseisavos", "2012-03-20") + _ronda("Final", "2012-08-08", partidos=1))
    avisos = validar.anios_bien_asignados(mal)
    assert [(a.que, a.grave) for a in avisos] == [(QUE_RONDA, True)], [str(a) for a in avisos]
    assert "Dieciseisavos en 2012-03-20 contra Treintaidosavos en 2012-11-29" in avisos[0].detalle

    bien = (_ronda("Treintaidosavos", "2011-11-29", partidos=4)
            + _ronda("Dieciseisavos", "2012-03-20") + _ronda("Final", "2012-08-08", partidos=1))
    assert validar.anios_bien_asignados(bien) == []


def test_el_error_mas_chico_que_una_configuracion_produce_si_avisa():
    """El borde de ARRIBA del 180, que el comentario de `_ATRAS_DE_MAS` cita: en la
    Copa Argentina 2018-19 con un `anio_fin` de mas, los dieciseisavos quedan 189
    dias antes que los treintaidosavos."""
    ps = _ronda("Treintaidosavos", "2019-07-31", partidos=4) + _ronda("Dieciseisavos", "2019-01-23")
    assert [a.que for a in validar.anios_bien_asignados(ps)] == [QUE_RONDA]


def test_un_partido_suelto_tampoco_mueve_a_su_RONDA():
    """Las rondas tambien se comparan por su partido del medio."""
    ps = (_ronda("Treintaidosavos", "2011-11-29", partidos=4)
          + _ronda("Dieciseisavos", "2012-03-20", partidos=4))
    ps[0].fecha = "2012-11-29"            # un treintaidosavo, un anio despues
    ps[4].fecha = "2011-03-20"            # un dieciseisavo, un anio antes
    assert validar.anios_bien_asignados(ps) == []


def test_el_aviso_de_una_ronda_dice_de_que_llave_es():
    """En una pagina con tres reducidos, "Final en ... contra Semifinales en ..."
    no dice cual."""
    ps = (_ronda("Semifinales", "2012-12-01", llave="Reducido")
          + _ronda("Final", "2012-03-20", llave="Reducido", partidos=1))
    avisos = validar.anios_bien_asignados(ps)
    assert [a.que for a in avisos] == [QUE_RONDA]
    assert avisos[0].detalle.startswith(
        "Reducido: Final en 2012-03-20 contra Semifinales en 2012-12-01;")


def test_dos_cuadros_de_llaves_distintas_no_se_comparan_entre_si():
    """Las rondas tienen orden ADENTRO de su cuadro. Una pagina que pone el cuadro
    final (agosto de 2012) y despues la fase preliminar (agosto de 2011): casi un
    anio para atras, y esta perfecto, porque son dos cuadros."""
    ps = (_ronda("Semifinales", "2012-08-01", llave="Fase final")
          + _ronda("Final", "2012-08-08", llave="Fase final", partidos=1)
          + _ronda("Primera fase", "2011-08-31", llave="Fase preliminar"))
    assert validar.anios_bien_asignados(ps) == []


def test_se_miran_TODAS_las_llaves_y_cada_una_ENTERA():
    """La rota es la segunda llave de tres, entre su segunda y su tercera ronda."""
    ps = (_ronda("Semifinales", "2012-06-10", llave="Reducido")
          + _ronda("Final", "2012-06-20", llave="Reducido", partidos=1)
          + _ronda("Cuartos de final", "2012-05-01", llave="Segundo ascenso", partidos=4)
          + _ronda("Semifinales", "2012-05-10", llave="Segundo ascenso")
          + _ronda("Final", "2011-05-20", llave="Segundo ascenso", partidos=1)
          + _ronda("Ida", "2012-06-27", llave="Promoción", partidos=1)
          + _ronda("Vuelta", "2012-06-30", llave="Promoción", partidos=1))
    avisos = validar.anios_bien_asignados(ps)
    assert [a.que for a in avisos] == [QUE_RONDA], [str(a) for a in avisos]
    assert avisos[0].detalle.startswith(
        "Segundo ascenso: Final en 2011-05-20 contra Semifinales en 2012-05-10;")


def test_una_ronda_que_la_pagina_pone_despues_y_se_jugo_seis_dias_antes():
    """El borde de abajo de esta pista, con el caso real. En el Argentino A 2011-12
    la llave "Promociones" lista primero "Partidos" (30 de junio) y despues
    "Promoción 1" (24 de junio): 6 dias para atras, el mayor del dataset."""
    ps = (_ronda("Partidos", "2012-06-30", llave="Promociones")
          + _ronda("Promoción 1", "2012-06-24", llave="Promociones"))
    assert validar.anios_bien_asignados(ps) == []


def test_los_partidos_de_eliminacion_sin_nombre_de_ronda_no_forman_una_ronda():
    """Hay 15 en 9 paginas. Sin nombre no hay orden que mirar."""
    ps = (_ronda("", "2013-03-20", llave="Promoción")
          + _ronda("Final", "2012-06-10", llave="Promoción", partidos=1))
    assert validar.anios_bien_asignados(ps) == []


# ---- pista 3: las secciones entre si ---------------------------------------
def test_una_seccion_ENTERA_corrida_la_delata_la_seccion_de_al_lado():
    """Lo que las pistas de adentro no pueden ver. Si el Apertura completo se va de
    anio, sus fechas siguen en orden entre si; lo que desentona es que el Clausura,
    que viene despues, quede siete meses antes."""
    apertura = dict(llave="Torneo Apertura", z="")
    clausura = dict(llave="Torneo Clausura", z="")
    mal = (_jornada(1, "2020-09-05", **apertura) + _jornada(2, "2020-09-12", **apertura)
           + _jornada(3, "2020-09-19", **apertura)
           + _jornada(1, "2020-02-01", **clausura) + _jornada(2, "2020-02-08", **clausura)
           + _jornada(3, "2020-02-15", **clausura))
    avisos = validar.anios_bien_asignados(mal)
    assert [(a.que, a.grave) for a in avisos] == [(QUE_SECCION, True)]
    assert avisos[0].detalle.startswith(
        "Torneo Clausura en 2020-02-08 contra Torneo Apertura en 2020-09-12;")


def test_el_error_para_el_que_existe_esta_pista_cae_a_180_dias():
    """Un Apertura y un Clausura tienen sus fechas del medio a unos 185 dias. Si uno
    se va de anio, queda unos 180 dias ANTES que el otro: con el umbral comun de 180
    se veia por un dia o no se veia. Por eso esta pista tiene el suyo."""
    apertura = dict(llave="Torneo Apertura", z="")
    clausura = dict(llave="Torneo Clausura", z="")
    ps = (_jornada(1, "2020-09-05", **apertura) + _jornada(2, "2020-09-12", **apertura)
          + _jornada(3, "2020-09-19", **apertura)
          + _jornada(1, "2020-03-09", **clausura) + _jornada(2, "2020-03-16", **clausura)
          + _jornada(3, "2020-03-23", **clausura))
    assert [a.que for a in validar.anios_bien_asignados(ps)] == [QUE_SECCION]


def test_una_seccion_de_dos_partidos_tambien_se_compara():
    """Lo de las jornadas chicas es de las JORNADAS. Una seccion de dos partidos --
    un desempate a ida y vuelta -- se compara como cualquiera."""
    ps = (_jornada(1, "2018-09-02", llave="Primera fase", z="")
          + _jornada(1, "2018-01-10", llave="Desempate", z="", equipos=4))
    assert [a.que for a in validar.anios_bien_asignados(ps)] == [QUE_SECCION]


def test_la_revalida_que_arranca_antes_no_es_una_seccion_corrida():
    """En el Federal A 2018-19 la pagina pone primero la Tercera fase y despues la
    Revalida, que se juega 49 dias antes."""
    ps = (_jornada(1, "2019-04-14", llave="Tercera fase", z="")
          + _jornada(1, "2019-02-24", llave="Reválida", z=""))
    assert validar.anios_bien_asignados(ps) == []


def test_las_secciones_ordenadas_por_RAMA_tampoco():
    """La Primera B 1969 ordena sus secciones por rama y no por fecha: la Etapa
    descenso (julio a octubre) viene despues del Torneo de Reclasificacion
    (diciembre), 103 dias antes. No hay anio que asignar mal -- es un torneo de un
    solo anio --, y con el umbral de 90 que esta pista tuvo al principio daba un
    grave que ninguna configuracion apagaba."""
    ps = (_jornada(1, "1969-09-20", llave="Etapa campeonato", z="")
          + _jornada(1, "1969-12-18", llave="Torneo de Reclasificación", z="")
          + _jornada(1, "1969-09-06", llave="Etapa descenso", z=""))
    assert validar.anios_bien_asignados(ps) == []

    # Y lo mas largo que se midio en una pagina sana: 140 dias, en una liga regional
    # donde el orden en que llegan los partidos no es el de la pagina.
    ps = (_jornada(1, "2022-08-20", llave="Torneo Clausura", z="")
          + _jornada(1, "2022-04-02", llave="Torneo Apertura", z=""))
    assert validar.anios_bien_asignados(ps) == []


def test_las_secciones_van_en_el_orden_en_que_llegan_no_en_el_alfabetico():
    """"Primera fase" (septiembre) y despues "Descenso" (abril). Ordenadas por
    nombre, el Descenso queda adelante y la Primera fase parece caer siete meses
    antes."""
    ps = (_jornada(1, "2018-09-02", llave="Primera fase", z="")
          + _jornada(1, "2019-04-07", llave="Descenso", z=""))
    assert validar.anios_bien_asignados(ps) == []


def test_se_miran_TODAS_las_secciones():
    """La corrida es la tercera."""
    ps = (_jornada(1, "2018-09-02", llave="Primera fase", z="")
          + _jornada(1, "2019-02-03", llave="Segunda fase", z="")
          + _jornada(1, "2018-04-14", llave="Tercera fase", z=""))
    avisos = validar.anios_bien_asignados(ps)
    assert [a.que for a in avisos] == [QUE_SECCION], [str(a) for a in avisos]
    assert avisos[0].detalle.startswith(
        "Tercera fase en 2018-04-14 contra Segunda fase en 2019-02-03;")


def test_la_seccion_que_no_tiene_nombre_se_llama_la_fase_de_zonas():
    """Hay paginas con partidos de zonas sueltos y ademas una seccion con nombre.
    El aviso tiene que poder nombrar a las dos."""
    ps = (_jornada(1, "1989-05-28", z="")
          + _jornada(1, "1988-10-02", llave="Liguilla", z=""))
    avisos = validar.anios_bien_asignados(ps)
    assert [a.que for a in avisos] == [QUE_SECCION]
    assert avisos[0].detalle.startswith(
        "Liguilla en 1988-10-02 contra la fase de zonas en 1989-05-28;")


# ---- pista 4: la fase final contra el arranque ------------------------------
def test_una_fase_final_que_queda_ANTES_de_que_empiece_el_torneo():
    """Una fase final corrida un anio para atras no cae lejos: en una temporada de
    agosto a junio, la final de junio queda mes y medio ANTES del primer partido.
    Las rondas entre si estan en orden y la fase de zonas tambien; lo unico que no
    cierra es que se defina un torneo que todavia no empezo."""
    zonas = _jornada(1, "2019-08-03") + _jornada(2, "2019-08-10")
    avisos = validar.anios_bien_asignados(zonas + _ronda("Final", "2019-06-20", partidos=1))
    assert [(a.que, a.grave) for a in avisos] == [(QUE_FINAL, True)]
    assert "2019-06-20" in avisos[0].detalle

    assert validar.anios_bien_asignados(zonas + _ronda("Final", "2020-06-20", partidos=1)) == []


def test_una_eliminatoria_previa_de_verdad_no_frena_la_corrida_de_todos_los_dias():
    """El Torneo Integracion 2016 de Catamarca: un repechaje el 22 de junio y los
    grupos desde el 28. No hay ningun anio mal puesto.

    Por eso esta pista es la unica que distingue: en un torneo EN CURSO -- lo unico
    que la corrida diaria vuelve a leer -- avisa y no frena, porque un cambio de
    formato no puede dejar sin actualizar a todas las paginas. En uno cerrado, que
    se lee con alguien mirando, frena. Se prueba por `revisar`, que es por donde
    pasa el build."""
    ps = _ronda("Repechaje", "2016-06-22") + _jornada(1, "2016-06-28") + _jornada(2, "2016-07-05")
    en_curso = [a for a in validar.revisar(ps, en_curso=True) if a.que == QUE_FINAL]
    assert len(en_curso) == 1 and not en_curso[0].grave
    assert "eliminatoria previa" in en_curso[0].detalle
    assert "no llevaba jugados mas de 0 de sus 6 partidos con fecha" in en_curso[0].detalle, \
        "con menos de veinte partidos el arranque ES el primero, y el aviso no dice otra cosa"

    cerrado = [a for a in validar.revisar(ps) if a.que == QUE_FINAL]
    assert len(cerrado) == 1 and cerrado[0].grave


def test_las_rondas_regionales_de_meses_antes_tampoco_frenan_un_torneo_en_curso():
    """La otra forma real, el Argentino B 2000-01: rondas regionales desde
    septiembre que el parser lee como eliminacion, y la Ronda final -- lo unico que
    queda como zonas -- en mayo. 224 dias antes."""
    ps = (_ronda("Fecha 1", "2000-09-24", llave="Primera ronda", partidos=4)
          + _jornada(1, "2001-05-06", llave="Ronda final") + _jornada(2, "2001-05-13", llave="Ronda final"))
    avisos = validar.anios_bien_asignados(ps, en_curso=True)
    assert [(a.que, a.grave) for a in avisos] == [(QUE_FINAL, False)]


def test_las_otras_tres_pistas_frenan_tambien_en_un_torneo_en_curso():
    """Lo de avisar sin frenar es de la cuarta sola."""
    ps = (_jornada(1, "2020-07-26") + _jornada(2, "2019-08-02")
          + _jornada(1, "2019-01-06", llave="Torneo Clausura")
          + _ronda("Semifinales", "2020-12-15", llave="Reducido")
          + _ronda("Final", "2019-12-22", llave="Reducido", partidos=1))
    avisos = validar.anios_bien_asignados(ps, en_curso=True)
    assert [(a.que, a.grave) for a in avisos] == [
        (QUE_JORNADA, True), (QUE_RONDA, True), (QUE_SECCION, True)]


def test_el_arranque_es_el_de_TODA_la_pagina_y_no_el_de_una_seccion():
    """Dos formas reales en las que una ronda cae en el medio de la fase de zonas y
    esta perfecta. El Argentino A 2005-06: el Apertura define su campeon en
    diciembre y el Clausura sigue hasta marzo. Y el Federal A 2018-19: la pagina
    pone primero la Tercera fase (abril) y despues la Revalida (febrero), cuya ida
    se juega en marzo."""
    apertura = dict(llave="Torneo Apertura", z="")
    clausura = dict(llave="Torneo Clausura", z="")
    ps = (_jornada(1, "2005-08-14", **apertura) + _jornada(2, "2005-11-06", **apertura)
          + _ronda("Final", "2005-12-18", llave="Torneo Apertura", partidos=1)
          + _jornada(1, "2006-02-05", **clausura) + _jornada(2, "2006-03-26", **clausura))
    assert validar.anios_bien_asignados(ps) == []

    fases = (_jornada(1, "2019-04-14", llave="Tercera fase", z="")
             + _jornada(1, "2019-02-24", llave="Reválida", z=""))
    ida = dict(llave="Reválida", partidos=1)
    assert validar.anios_bien_asignados(fases + _ronda("Partidos de ida", "2019-03-31", **ida)) == []
    avisos = validar.anios_bien_asignados(fases + _ronda("Partidos de ida", "2018-03-31", **ida))
    assert [a.que for a in avisos] == [QUE_FINAL]


def test_la_pista_de_la_fase_final_va_SIN_margen():
    """Corriendo la eliminacion un anio para atras en los torneos reales, la ronda
    que queda mas pegada es la Promocion de la Primera B 2010-11, a 32 dias del
    primer partido. Un colchon del tamanio de los otros umbrales dejaria pasar a
    tres de cada cuatro."""
    zonas = _jornada(1, "2010-08-07") + _jornada(2, "2010-08-14")
    a_32_dias = validar.anios_bien_asignados(zonas + _ronda("Promoción", "2010-07-06", partidos=1))
    assert [a.que for a in a_32_dias] == [QUE_FINAL]
    la_vispera = validar.anios_bien_asignados(zonas + _ronda("Promoción", "2010-08-06", partidos=1))
    assert [a.que for a in la_vispera] == [QUE_FINAL]
    # "antes" es antes: una ronda jugada el mismo dia del primer partido no lo esta.
    assert validar.anios_bien_asignados(zonas + _ronda("Promoción", "2010-08-07", partidos=1)) == []


def test_un_partido_de_liga_corrido_no_se_lleva_el_arranque():
    """La Primera C 2008-09 con el corte dos meses antes: la fase final de junio se
    iba un anio para atras JUNTO con un partido de liga jugado el 1 de junio. Ese
    partido pasaba a ser "el primero de la fase de zonas", la fase final quedaba
    despues de el y la pista se callaba con quince filas mal. Por eso el arranque
    no es el primer partido sino el que deja atras al 5%."""
    liga = [p for n in range(1, 9)
            for p in _jornada(n, f"2008-{8 + (n - 1) // 4:02d}-{2 + 7 * ((n - 1) % 4):02d}")]
    liga[-1].fecha = "2008-06-01"         # uno de la ultima fecha, corrido con la fase final
    avisos = validar.anios_bien_asignados(liga + _ronda("Final", "2008-06-14", partidos=1))
    assert [a.que for a in avisos] == [QUE_FINAL], [str(a) for a in avisos]
    assert "para el 2008-08-02 la fase de zonas" in avisos[0].detalle, \
        "y el aviso dice contra que fecha comparo, que no es la del primer partido"


def test_el_arranque_deja_atras_al_cinco_por_ciento_ni_mas_ni_menos():
    """Con cuarenta partidos de zonas, dos sueltos corridos no se llevan el
    arranque; con treinta y nueve, el segundo si. Es donde se eligio cortar."""
    final = _ronda("Final", "2019-06-14", partidos=1)

    def liga(n):
        ps = [p for j in range(1, 15)
              for p in _jornada(j, f"2019-{8 + (j - 1) // 4:02d}-{3 + 7 * ((j - 1) % 4):02d}")]
        ps = ps[:n]
        ps[0].fecha, ps[1].fecha = "2019-06-01", "2019-06-02"
        return ps
    avisos = validar.anios_bien_asignados(liga(40) + final)
    assert [a.que for a in avisos] == [QUE_FINAL]
    assert "no llevaba jugados mas de 2 de sus 40 partidos con fecha" in avisos[0].detalle
    assert validar.anios_bien_asignados(liga(39) + final) == []


def test_con_la_fase_de_zonas_casi_sin_fechas_la_pista_se_calla():
    """Como llegan las paginas viejas antes de tener segunda fuente: dos partidos
    fechados de diez, salidos de una nota. El "arranque" seria el dia de un
    postergado cualquiera, y la primera llave quedaria "antes" de un torneo que
    empezo meses atras."""
    zonas = _jornada(1, "", equipos=8) + _jornada(2, "", equipos=8) + _jornada(3, "", equipos=4)
    zonas[0].fecha = zonas[1].fecha = "2015-10-07"
    assert validar.anios_bien_asignados(zonas + _ronda("Final", "2015-09-20", partidos=1)) == []


def test_la_guarda_de_la_mitad_en_sus_dos_bordes():
    """Justo la mitad de la fase de zonas con fecha alcanza; un partido sin fecha
    mas, no."""
    final = _ronda("Final", "2019-06-14", partidos=1)
    mitad = _jornada(1, "2019-08-03", equipos=8) + _jornada(2, "", equipos=8)
    avisos = validar.anios_bien_asignados(mitad + final)
    assert [a.que for a in avisos] == [QUE_FINAL]
    assert "de sus 4 partidos con fecha" in avisos[0].detalle, "los que no tienen fecha no cuentan"
    menos = mitad + _jornada(3, "", equipos=2)
    assert validar.anios_bien_asignados(menos + final) == []


def test_alcanza_con_UN_partido_de_la_ronda_antes_del_arranque():
    """La ronda avisa por los partidos que quedaron antes, aunque no sean todos."""
    zonas = _jornada(1, "2019-08-03") + _jornada(2, "2019-08-10")
    promo = _ronda("Promoción", "2019-06-20")
    promo[1].fecha = "2020-06-27"
    avisos = validar.anios_bien_asignados(zonas + promo)
    assert [a.que for a in avisos] == [QUE_FINAL]
    assert avisos[0].detalle.startswith("Promoción: 1 partido desde el 2019-06-20,")


def test_la_eliminacion_sin_llave_ni_ronda_se_nombra_sin_rotulo():
    """Sin esto el detalle arranca con ": 1 partido"."""
    ps = _jornada(1, "2019-08-03") + _ronda("", "2019-06-14", partidos=1)
    avisos = validar.anios_bien_asignados(ps)
    assert [a.que for a in avisos] == [QUE_FINAL]
    assert avisos[0].detalle.startswith("sin rotulo: 1 partido desde el 2019-06-14,")


def test_la_pista_de_la_fase_final_tampoco_cuenta_las_fechas_que_no_existen():
    """Ni como arranque ni como ronda adelantada."""
    zonas = _jornada(1, "2019-08-03") + _jornada(2, "2019-08-10")
    zonas[0].fecha = "2019-06-31"
    avisos = validar.anios_bien_asignados(zonas + _ronda("Final", "2019-07-20", partidos=1))
    assert [a.que for a in avisos] == [QUE_FINAL]
    assert "para el 2019-08-03 la fase de zonas" in avisos[0].detalle

    sanas = _jornada(1, "2019-08-03") + _jornada(2, "2019-08-10")
    assert validar.anios_bien_asignados(sanas + _ronda("Final", "2019-06-31", partidos=1)) == []


def test_cada_ronda_adelantada_es_UN_aviso_y_dice_cual_es():
    zonas = _jornada(1, "2019-08-03") + _jornada(2, "2019-08-10")
    semis = _ronda("Semifinales", "2019-06-10", llave="Reducido")
    semis[1].fecha = "2019-06-12"
    final = _ronda("Final", "2019-06-20", llave="Reducido", partidos=1)
    promo = _ronda("Final", "2019-06-25", llave="Promoción")
    promo[1].fecha = "2019-06-28"
    avisos = validar.anios_bien_asignados(zonas + semis + final + promo)
    assert [a.que for a in avisos] == [QUE_FINAL] * 3, [str(a) for a in avisos]
    for aviso, donde, desde in zip(avisos,
                                   ("Reducido Semifinales: 2 partidos desde",
                                    "Reducido Final: 1 partido desde",
                                    "Promoción Final: 2 partidos desde"),
                                   ("2019-06-10", "2019-06-20", "2019-06-25")):
        assert aviso.detalle.startswith(donde), aviso.detalle
        assert f"desde el {desde}," in aviso.detalle
        assert "para el 2019-08-03 la fase de zonas" in aviso.detalle


def test_lo_que_no_tiene_numero_de_jornada_no_es_una_Fecha_0_pero_cuenta_para_el_arranque():
    """Hoy ningun partido de zonas llega sin numero de jornada, asi que esto no lo
    decide el dataset sino el codigo: no entran a la pista de las jornadas, y si a
    las secciones y al arranque."""
    def sin_numero(fecha, **donde):
        ps = _jornada(1, fecha, **donde)
        for p in ps:
            p.jornada = "Desempate"
        return ps
    ps = sin_numero("2020-06-20") + _jornada(1, "2019-08-03") + _jornada(2, "2019-08-10")
    assert validar.anios_bien_asignados(ps) == []

    ps = (sin_numero("2019-07-20") + _ronda("Final", "2019-07-27", partidos=1)
          + _jornada(1, "2019-08-03"))
    assert validar.anios_bien_asignados(ps) == []

    # A su seccion SI entra: no tiene jornada, pero es de donde es.
    ps = (_jornada(1, "2020-09-05", llave="Torneo Apertura")
          + sin_numero("2020-02-08", llave="Torneo Clausura"))
    assert [a.que for a in validar.anios_bien_asignados(ps)] == [QUE_SECCION]


# ---- pista 4, sobre lo que ya esta publicado ---------------------------------
DATOS = Path(__file__).resolve().parent.parent / "data"


@pytest.fixture(scope="module")
def publicado() -> dict[tuple, list[Partido]]:
    """Las filas del CSV de cada torneo, como las veria la pista 4. El CSV no trae
    la llave, que esa pista usa nada mas que para rotular. Se leen una sola vez:
    el que las vaya a tocar, que las copie."""
    de_cada_uno: dict[tuple, list[Partido]] = {}
    for f in dataset.leer_carpeta(DATOS):
        clave = (dataset.pagina_de(f), f["tournament"], f["season"])
        de_cada_uno.setdefault(clave, []).append(Partido(
            fecha=f["date"], local=f["home_team"], visita=f["away_team"],
            fase=f["phase"], zona=f["group"], jornada=f["matchday"]))
    return de_cada_uno


def _de(t, publicado) -> list[Partido]:
    return publicado.get((t.url, t.torneo, str(t.temporada)), [])


def test_ningun_torneo_CERRADO_del_dataset_tiene_la_fase_final_antes_del_arranque(publicado):
    """La pista 4 sobre lo PUBLICADO. Un torneo que se sigue en vivo pasa por esa
    pista como torneo en curso, donde solo avisa; cuando se lo cierra ya tiene sus
    filas en el CSV y el build no lo vuelve a leer. Sin esto la rama que frena no
    le tocaria nunca: el error se publicaria con un aviso y ahi quedaria.

    La suite corre antes que el build de todos los dias, asi que el dia que alguien
    pasa a `cerrado=True` un torneo con ese error adentro, esto falla. La corrida
    diaria no lo puede hacer fallar: mira solo torneos cerrados, que el bot no toca.
    """
    cerrados = [t for t in torneos.TODOS if t.cerrado]
    sin_filas = [t.pagina for t in cerrados if not _de(t, publicado)]
    assert len(cerrados) > 150 and not sin_filas, \
        f"si no encuentra las filas de un torneo, no lo esta mirando: {sin_filas}"
    malos = {t.pagina: [str(a) for a in avisos] for t in cerrados
             if (avisos := validar._fase_final_antes_del_arranque(_de(t, publicado), False))}
    assert not malos, malos


def test_y_la_veria_si_la_fase_final_publicada_estuviera_un_anio_antes(publicado):
    """El de arriba no dice nada, y un test que no dice nada puede ser un test que
    no mira. Con las filas de verdad de la B Nacional 2017-18 y su fase final un
    anio para atras -- lo que deja un corte de mes mal puesto --, frena."""
    (t,) = [t for t in torneos.TODOS if t.pagina == "Campeonato de Primera B Nacional 2017-18"]
    ps = [dataclasses.replace(p) for p in _de(t, publicado)]
    finales = [p for p in ps if p.fase == "eliminacion" and p.fecha]
    assert len(finales) > 5
    for p in finales:
        p.fecha = f"{int(p.fecha[:4]) - 1}{p.fecha[4:]}"
    avisos = validar._fase_final_antes_del_arranque(ps, False)
    assert avisos and all(a.grave and a.que == QUE_FINAL for a in avisos)


# ---- las pistas se suman, y las fechas raras --------------------------------
def test_las_llaves_sanas_NO_tapan_a_un_grupo_roto():
    """La Copa de la Liga 2020 tiene grupos Y llaves. Si la pista de las rondas
    PISA los avisos de la de jornadas en vez de sumarlos, la pagina que motivo este
    cambio vuelve a salir limpia."""
    ps = (_jornada(3, "2020-12-27", llave="Fase Campeonato", z="Grupo A")
          + _jornada(4, "2020-01-03", llave="Fase Campeonato", z="Grupo A")
          + _ronda("Final", "2021-01-17", partidos=1))
    avisos = validar.anios_bien_asignados(ps)
    assert [a.que for a in avisos] == [QUE_JORNADA], [str(a) for a in avisos]


def test_las_cuatro_pistas_SE_SUMAN():
    """Una pagina con un error en cada pista da los cuatro avisos. No es un caso
    real: es la manera mas corta de decir que ninguna pista pisa, corta ni
    reemplaza a otra. En un torneo cerrado frenan las cuatro; en uno en curso, la
    cuarta avisa."""
    apertura = dict(llave="Torneo Apertura", z="")
    clausura = dict(llave="Torneo Clausura", z="")
    ps = (_jornada(1, "2020-08-04", **apertura)                 # 1: la Fecha 1, un anio despues
          + _jornada(2, "2019-08-11", **apertura) + _jornada(3, "2019-08-18", **apertura)
          + _jornada(1, "2019-01-06", **clausura)               # 3: el Clausura entero, un anio antes
          + _jornada(2, "2019-01-13", **clausura)
          + _ronda("Semifinales", "2020-12-15", llave="Reducido")       # 2: semis despues de la final
          + _ronda("Final", "2019-12-22", llave="Reducido", partidos=1)
          + _ronda("Desempate", "2018-12-20", llave="Desempate", partidos=1))   # 4: antes de todo
    avisos = validar.anios_bien_asignados(ps)
    assert [(a.que, a.grave) for a in avisos] == [
        (QUE_JORNADA, True), (QUE_RONDA, True), (QUE_SECCION, True), (QUE_FINAL, True)], \
        [str(a) for a in avisos]
    assert [a.grave for a in validar.anios_bien_asignados(ps, en_curso=True)] == [
        True, True, True, False]


def test_una_fecha_que_NO_EXISTE_no_tumba_el_chequeo():
    """Hubo un `31 de noviembre` y tres `31 de junio` en el dataset, y el parser los
    arma igual. Si a una fecha asi le tocaba ser la del medio de su jornada, la
    resta levantaba un `ValueError` y este chequeo se llevaba el build entero. No
    paso de casualidad. Se la saltea: decir que no existe es otro chequeo."""
    ps = (_jornada(18, "2014-10-25") + _jornada(19, "2014-11-31") + _jornada(20, "2014-11-08"))
    assert validar.anios_bien_asignados(ps) == []


def test_una_fecha_rara_se_saltea_ELLA_y_el_resto_se_sigue_mirando():
    """El de arriba pide `== []`, y eso lo cumple tambien un chequeo que al ver una
    fecha rara deja de mirar. Aca la pagina tiene una fecha que no existe, un
    partido sin fecha Y un anio mal puesto de verdad: el aviso tiene que salir."""
    ps = (_jornada(1, "2020-07-27", equipos=8) + _jornada(2, "2019-08-04", equipos=8)
          + _jornada(3, "2019-08-11", equipos=8))
    ps[0].fecha = "2019-06-31"            # no existe, y es el primer partido de la pagina
    ps[5].fecha = ""                      # y uno sin fecha
    avisos = validar.anios_bien_asignados(ps)
    assert len(avisos) == 1 and avisos[0].grave, [str(a) for a in avisos]
    assert "Fecha 2 en 2019-08-04 contra Fecha 1 en 2020-07-27" in avisos[0].detalle


def test_un_partido_SIN_FECHA_no_tumba_ni_apaga_nada():
    """Sin fecha no es lo mismo que con una fecha imposible. Si la cadena vacia se
    diera por buena, una jornada entera sin fecha quedaria en el medio y la resta
    explotaria, y un solo partido de zonas sin fecha se volveria el "arranque" del
    torneo -- la cadena vacia es menor que cualquier fecha -- y la pista de la fase
    final no avisaria nunca mas."""
    ps = _jornada(1, "2019-08-03") + _jornada(2, "") + _jornada(3, "2019-08-17")
    assert validar.anios_bien_asignados(ps) == []

    zonas = _jornada(1, "2019-08-03", equipos=8)
    zonas[0].fecha = ""
    avisos = validar.anios_bien_asignados(zonas + _ronda("Final", "2019-06-20", partidos=1))
    assert [a.que for a in avisos] == [QUE_FINAL]


def test_una_ronda_con_fecha_rara_o_sin_fecha_tampoco():
    """Una final que llega sin fecha -- hay paginas que traen el marcador y no el
    dia -- no esta "antes de que empiece la fase de zonas", y una ronda con un 31
    de noviembre no puede tumbar la comparacion entre rondas."""
    zonas = _jornada(1, "2019-08-03") + _jornada(2, "2019-08-10")
    assert validar.anios_bien_asignados(zonas + _ronda("Final", "", partidos=1)) == []

    for rara in ("", "2019-11-31"):
        ps = _ronda("Semifinales", "2019-11-24") + _ronda("Final", rara, partidos=1)
        assert validar.anios_bien_asignados(ps) == []


def test_una_seccion_entera_con_fechas_que_no_existen_no_es_una_seccion():
    ps = (_jornada(1, "2014-10-25", llave="Torneo Inicial", z="")
          + _jornada(1, "2014-11-31", llave="Torneo Final", z=""))
    assert validar.anios_bien_asignados(ps) == []


def test_existe_dice_que_no_a_lo_vacio_a_lo_imposible_y_a_lo_que_no_esta_en_forma_larga():
    """Las dos ultimas son fechas de verdad -- el 5 y el 15 de enero de 2020 --
    escritas como `fromisoformat` tambien acepta. Este modulo ordena y compara las
    fechas como texto, y eso solo vale para `AAAA-MM-DD`."""
    assert validar._existe("2019-08-03")
    assert not validar._existe("")
    assert not validar._existe("2014-11-31")
    assert not validar._existe(None)
    assert not validar._existe("20200105")
    assert not validar._existe("2020-W03-3")


# --------------------------------------------------------------------------
# la cadena de llaves
# --------------------------------------------------------------------------
def _cuadro():
    """Semis y final consistentes: los dos ganadores juegan la final.

    Las semis van en DOS dias a proposito: es lo normal y es lo que rompia la
    version anterior, que agrupaba las rondas por fecha y tomaba el segundo dia
    como una ronda nueva.
    """
    return [llave("Boca", "River", 0, 1, "2026-05-01", ronda="Semifinales"),
            llave("Racing", "Belgrano", 2, 0, "2026-05-02", ronda="Semifinales"),
            llave("River", "Racing", 1, 0, "2026-05-10", ronda="Final")]


def test_cadena_de_llaves_consistente():
    assert validar.cadena_de_llaves(_cuadro()) == []


def test_juega_la_final_sin_haber_ganado_la_semi():
    roto = _cuadro()
    roto[0] = llave("Boca", "River", 1, 0, "2026-05-01", ronda="Semifinales")
    avisos = validar.cadena_de_llaves(roto)     # gana Boca, pero la final la juega River
    assert len(avisos) == 1 and "River" in avisos[0].detalle


def test_la_cadena_sigue_al_ganador_de_los_penales():
    """Si se invierte la comparacion de penales, avanza el que perdio la tanda."""
    cuadro = [llave("Boca", "River", 1, 1, "2026-05-01", pl=2, pv=4, ronda="Semifinales"),
              llave("Racing", "Belgrano", 2, 0, "2026-05-02", ronda="Semifinales"),
              llave("River", "Racing", 1, 0, "2026-05-10", ronda="Final")]
    assert validar.cadena_de_llaves(cuadro) == []


def test_una_ronda_que_todavia_no_se_jugo_no_es_un_error():
    """El caso de la Copa en curso. Los 16 ganadores de dieciseisavos todavia no
    jugaron su octavos: preguntado al reves ("cada ganador reaparece?") eso daba
    14 avisos por dia hasta noviembre, y un chequeo que grita todos los dias deja
    de leerse."""
    cuadro = [llave("Boca", "River", 2, 0, "2026-05-01", ronda="Cuartos"),
              llave("Racing", "Belgrano", 2, 0, "2026-05-02", ronda="Cuartos"),
              llave("Huracán", "Tigre", 1, 0, "2026-05-03", ronda="Cuartos"),
              llave("Platense", "Lanús", 1, 0, "2026-05-03", ronda="Cuartos"),
              llave("Boca", "Racing", 1, 0, "2026-05-10", ronda="Semifinales")]
    assert validar.cadena_de_llaves(cuadro) == []


def test_sin_rondas_reconocidas_avisa_en_vez_de_saltear_calladito():
    """Un chequeo salteado en silencio es peor que uno ausente: parece que algo
    se esta mirando.

    Las rondas van con DOS etiquetas distintas a proposito: con una sola no hay
    cadena que revisar, y entonces no hay nada que saltear -- ese es el caso del
    test de al lado.
    """
    sin_ronda = [llave("Boca", "River", 1, 0, "2026-05-01", ronda="Partidos"),
                 llave("Racing", "Belgrano", 2, 0, "2026-05-02", ronda="Partidos"),
                 llave("Boca", "Racing", 1, 0, "2026-05-10", ronda="Desempate")]
    avisos = validar.cadena_de_llaves(sin_ronda)
    assert len(avisos) == 1 and "salteo" in avisos[0].detalle


def test_un_cuadro_de_una_sola_ronda_no_es_una_cadena_salteada():
    """Con una sola ronda no hay anterior contra la cual preguntar, asi que no se
    saltea nada: no hay nada que saltear.

    Son ocho llaves del corpus -- promociones, permanencias, desempates -- que
    rotulan su unica ronda con algo que no es un nombre de ronda. Avisar ahi manda
    a buscar un problema que no existe, y este chequeo ya tuvo su temporada de
    decir cosas que no eran.
    """
    una = [llave("Boca", "River", 1, 0, "2026-05-01", ronda="Promoción"),
           llave("Racing", "Belgrano", 2, 0, "2026-05-02", ronda="Promoción"),
           llave("Colón", "Tigre", 1, 0, "2026-05-03", ronda="Promoción")]
    assert validar.cadena_de_llaves(una) == []


def test_la_fase_final_de_la_copa_va_antes_que_los_dieciseisavos():
    """La Copa Argentina 2013-14 llama "Fase final I" y "Fase final II" a las dos
    rondas que van ANTES de los dieciseisavos: tiene una fase preliminar regional
    y despues la fase final propiamente dicha, cuyas primeras rondas numera.

    El nombre enga\u00f1a --dice "final" y va primera-- y el orden importa: al reves,
    el que gana la I aparece jugando la II sin haberla ganado. Por eso el testigo
    de este test es que NO haya ninguna acusacion, no solo que se revise.
    """
    ps = [llave("Boca", "River", 2, 0, "2014-03-12", ronda="Fase final i"),
          llave("Boca", "Colón", 1, 0, "2014-04-09", ronda="Fase final ii"),
          llave("Boca", "Tigre", 1, 0, "2014-07-17", ronda="Dieciseisavos")]
    avisos = validar.cadena_de_llaves(ps)

    assert not any("no se pudo revisar" in a.que for a in avisos), "el cuadro tiene que revisarse"
    assert not any("sin haber ganado" in a.que for a in avisos), "Boca gano todo lo que jugo"
    # Los que entran frescos si se nombran, que es el aviso correcto.
    frescos = [a for a in avisos if "entran al cuadro" in a.que]
    assert len(frescos) == 2 and "Colón" in frescos[0].detalle and "Tigre" in frescos[1].detalle


def test_las_dos_semifinales_son_una_ronda_y_no_dos():
    """"Semifinal 1" y "Semifinal 2" son las dos llaves de la MISMA ronda.

    Tomarlas por rondas consecutivas acusa dos veces y las dos mal: al que gana
    una lo pone jugando la otra sin haberla ganado, y al finalista que salio de la
    primera lo pone llegando a la final sin ganar nada. Paso de verdad en el
    reducido de la B Nacional 2015 y en la Primera Division 2015.
    """
    ps = [llave("Boca", "River", 2, 0, "2026-05-01", ronda="Semifinal 1"),
          llave("Colón", "Tigre", 1, 0, "2026-05-01", ronda="Semifinal 2"),
          llave("Boca", "Colón", 1, 0, "2026-05-08", ronda="Final")]
    assert validar.cadena_de_llaves(ps) == []


def test_las_rondas_en_ingles_de_rsssf_se_entienden():
    """Desde que las llaves de RSSSF entran al dataset, sus jornadas llegan hasta
    aca escritas en ingles. La jornada publicada sigue siendo fiel a la fuente
    --su trabajo es ser fiel, no prolijo--, asi que la traduccion vive donde vive
    el resto de la normalizacion."""
    assert validar._ronda("Semifinals") == "semifinales"
    assert validar._ronda("Quarterfinals") == "cuartos"
    assert validar._ronda("1/8 Finals") == "octavos"


def test_la_pata_se_pela_antes_que_la_rama():
    """Y el orden no da igual. El lector escribe "Semifinals - First leg": pelando
    la rama de adelante queda "first leg", que no es ninguna ronda; sacando la pata
    queda "semifinals", que si lo es."""
    assert validar._ronda("Semifinals - First leg") == "semifinales"
    assert validar._ronda("Final - Second leg") == "final"
    assert validar._ronda("1/8 Finals - First leg") == "octavos"


def test_las_dos_patas_de_una_ronda_son_una_sola():
    """Que es el punto de todo esto: la ida y la vuelta de las semifinales son LA
    misma ronda, no dos."""
    assert validar._ronda("Semifinals - First leg") == validar._ronda("Semifinals - Second leg")


def test_instancia_es_lo_mismo_que_fase():
    """La tercera forma de numerar una ronda. El chequeo tiene que poder ordenar
    "Segunda instancia" contra "Semifinales" igual que si dijera "Segunda fase"."""
    assert validar._ronda("Primera instancia") == "primera fase"
    assert validar._ronda("Tercera instancia") == "tercera fase"


@pytest.mark.parametrize("numero", ["Segunda", "Tercera", "Cuarta", "Quinta", "Sexta",
                                    "Séptima"])
def test_etapa_es_lo_mismo_que_fase(numero):
    """La cuarta forma, la de la Revalida del Federal A desde 2016-17, en las seis
    etapas que tiene. Con una que falte, el cuadro de cada pagina que la juega queda
    sin revisar: sin la cuarta, la quinta o la sexta, el de cinco Revalidas."""
    assert validar._ronda(f"{numero} etapa") == f"{numero.lower()} fase"


def test_la_sexta_y_la_septima_van_despues_de_la_quinta():
    """El Argentino A 2013-14 llega a la sexta fase y el Federal A 2015 a la
    septima. Sin esos escalones `_por_ronda` no las ordena y el cuadro entero se
    queda sin revisar."""
    ps = [llave("Boca", "River", 1, 0, "2015-12-06", ronda="Séptima fase"),
          llave("Boca", "Colón", 1, 0, "2015-11-22", ronda="Quinta fase"),
          llave("Boca", "Tigre", 1, 0, "2015-11-29", ronda="Sexta fase")]
    grupos = validar._por_ronda(ps)
    assert grupos is not None, "las tres rondas tienen que reconocerse"
    assert [r for r, _ in grupos] == ["Quinta fase", "Sexta fase", "Séptima fase"]


def test_un_cuadro_por_etapas_se_revisa():
    """Y con las etapas reconocidas, la Revalida se revisa de verdad: Boca pierde
    las dos patas de la segunda etapa y aparece en la tercera."""
    ps = [llave("Boca", "River", 0, 1, "2017-04-01", ronda="Segunda etapa"),
          llave("River", "Boca", 1, 0, "2017-04-08", ronda="Segunda etapa"),
          llave("Boca", "Colón", 1, 0, "2017-04-15", ronda="Tercera etapa"),
          llave("Colón", "Boca", 0, 1, "2017-04-22", ronda="Tercera etapa")]
    avisos = validar.cadena_de_llaves(ps)
    assert any("sin haber ganado" in a.que and "Boca" in a.detalle for a in avisos), avisos


def test_la_ronda_se_despega_de_la_rama_del_torneo():
    """El Argentino A numera las rondas de su revalida con la rama adelante."""
    assert validar._ronda("Revalida - Segunda ronda") == "segunda fase"
    assert validar._ronda("Semifinal 2") == "semifinales"


def test_pelar_la_etiqueta_solo_vale_si_abajo_hay_una_ronda():
    """La condicion que hace segura a la regla de al lado. "Llave" y "Partido" no
    son rondas, asi que "Llave 1" y "Partido 2" no se tocan -- y ese es justo el
    caso donde colapsarlas estaria mal: son llaves distintas, no una ronda."""
    assert validar._ronda("Llave 1") == "llave 1"
    assert validar._ronda("Partido 2") == "partido 2"
    assert validar._ronda("Promoción - Algo raro") == "promoción - algo raro"


def _cuadro_rotulado_por_pata():
    """Un cuadro que rotula la PATA en vez de la ronda.

    Cuatro rotulos para dos rondas. "Partidos de ida" y "Partidos de vuelta"
    tienen el mismo plantel exacto --son la misma ronda jugada dos veces-- y lo
    mismo el par en singular, que es la final. Es como salian la Revalida del
    Federal A y otras ocho paginas antes de que el parser les leyera la ronda del
    titulo; hoy no sale asi ninguna, y la rama queda para la que no tenga titulo.
    """
    return [llave("Boca", "River", 2, 0, "2026-05-01", ronda="Partidos de ida"),
            llave("Racing", "Colón", 1, 0, "2026-05-01", ronda="Partidos de ida"),
            llave("River", "Boca", 0, 1, "2026-05-08", ronda="Partidos de vuelta"),
            llave("Colón", "Racing", 0, 2, "2026-05-08", ronda="Partidos de vuelta"),
            llave("Boca", "Racing", 1, 0, "2026-05-15", ronda="Partido de ida"),
            llave("Racing", "Boca", 0, 1, "2026-05-22", ronda="Partido de vuelta")]


def test_las_rondas_se_reconstruyen_por_el_plantel():
    """Si un cuadro rotula la pata y nada dice que ronda es, el dato no esta en
    ningun campo. Pero se puede deducir: dos rotulos con el MISMO plantel exacto
    no son dos rondas, son la misma jugada dos veces."""
    avisos = validar.cadena_de_llaves(_cuadro_rotulado_por_pata())
    assert avisos == [], f"el cuadro esta bien jugado, no deberia decir nada: {avisos}"


def test_el_cuadro_reconstruido_igual_acusa():
    """EL TEST QUE IMPORTA. Que un chequeo no diga nada puede querer decir que
    esta todo bien o que no esta mirando, y las dos se ven igual desde afuera.

    Aca Boca pierde las dos patas de su llave y aparece en la final igual. Si el
    cuadro reconstruido fuera decorativo, esto pasaria en silencio.
    """
    ps = _cuadro_rotulado_por_pata()
    for p in ps:
        if "Partidos de" in p.jornada and "Boca" in (p.local, p.visita):
            p.goles_local, p.goles_visita = ((0, 3) if p.local == "Boca" else (3, 0))

    avisos = validar.cadena_de_llaves(ps)
    assert avisos, "Boca no gano nada y jugo la final: tiene que aparecer"
    assert all("sin haber ganado" in a.que for a in avisos)
    assert all("Boca" in a.detalle for a in avisos)


def test_si_el_plantel_no_junta_nada_se_sigue_avisando():
    """El limite de la regla. Si cada rotulo tiene su propio plantel no se
    aprendio nada, y entonces hay que decir que no se reviso en vez de inventar un
    orden por fecha -- que es justo lo que este modulo tiene prohibido."""
    ps = [llave("Boca", "River", 1, 0, "2026-05-01", ronda="Llave 1"),
          llave("Boca", "Racing", 1, 0, "2026-05-08", ronda="Llave 2"),
          llave("Boca", "Colón", 1, 0, "2026-05-15", ronda="Llave 3")]
    avisos = validar.cadena_de_llaves(ps)
    assert len(avisos) == 1 and "salteo" in avisos[0].detalle


def test_llaves_en_paralelo_se_nombran_en_vez_de_llamarse_cuadro():
    """"Promocion 1" y "Promocion 2" son dos promociones distintas, no dos rondas
    de un cuadro. Se sabe sin mirar el titulo: no comparten ningun club, o sea que
    nadie avanzo de una a la otra.

    Va con aviso y no callado -- al reves que el cuadro de una sola ronda -- porque
    aca la falta de cadena se midio en vez de saberse de antemano: el dia que el
    parser parta mal un cuadro de verdad, se va a ver exactamente asi.
    """
    aparte = [llave("Boca", "River", 1, 0, "2026-05-01", ronda="Promoción 1"),
              llave("Boca", "River", 2, 0, "2026-05-08", ronda="Promoción 1"),
              llave("Colón", "Tigre", 1, 0, "2026-05-02", ronda="Promoción 2"),
              llave("Colón", "Tigre", 0, 3, "2026-05-09", ronda="Promoción 2")]
    avisos = validar.cadena_de_llaves(aparte)
    assert len(avisos) == 1
    assert "no es una cadena" in avisos[0].que
    assert not avisos[0].grave


def test_un_club_repetido_alcanza_para_que_sea_cadena():
    """El testigo de la regla de al lado: si una ronda comparte aunque sea UN club
    con otra, alguien avanzo y la cadena existe -- lo que no se puede es ordenarla,
    y eso ya tiene su propio aviso."""
    encadenadas = [llave("Boca", "River", 1, 0, "2026-05-01", ronda="Promoción 1"),
                   llave("Boca", "River", 2, 0, "2026-05-08", ronda="Promoción 1"),
                   llave("Boca", "Tigre", 1, 0, "2026-05-02", ronda="Promoción 2"),
                   llave("Boca", "Tigre", 0, 3, "2026-05-09", ronda="Promoción 2")]
    avisos = validar.cadena_de_llaves(encadenadas)
    assert len(avisos) == 1 and "salteo" in avisos[0].detalle


def test_cadena_con_muy_pocos_partidos_no_dice_nada():
    assert validar.cadena_de_llaves([llave("Boca", "River", 1, 0, "2026-05-01")]) == []


# --------------------------------------------------------------------------
def test_revisar_pone_los_graves_primero():
    ps = [zona("A", "B", z=""),                       # grave
          zona("A", "C"), zona("A", "D")]             # zona despareja: aviso
    avisos = validar.revisar(ps)
    assert [a.grave for a in avisos] == sorted([a.grave for a in avisos], reverse=True)


# --------------------------------------------------------------------------
# localias_repartidas
# --------------------------------------------------------------------------
def ida_y_vuelta(local, visita, *, local_de_vuelta=None):
    """Los dos cruces de un par en un torneo de ida y vuelta."""
    return [zona(local, visita, j="Fecha 1"),
            zona(local_de_vuelta or visita,
                 local if not local_de_vuelta or local_de_vuelta == visita else visita,
                 j="Fecha 10")]


def test_la_vuelta_se_juega_en_la_otra_cancha():
    """El caso sano: nadie se queja de un fixture normal."""
    assert validar.localias_repartidas(ida_y_vuelta("Boca Juniors", "River Plate")) == []


def test_el_mismo_local_las_dos_veces_no_puede_ser():
    """Wikipedia da a Ferro de local contra Union en las fechas 6 y 25 de la B
    Nacional 2009-10. En un ida y vuelta eso es imposible: una de las dos tiene
    la localia al reves."""
    ps = [zona("Boca Juniors", "River Plate", j="Fecha 1"),
          zona("Boca Juniors", "River Plate", j="Fecha 10")]
    avisos = validar.localias_repartidas(ps)
    assert len(avisos) == 1
    assert "Boca Juniors de local 2" in avisos[0].detalle
    assert not avisos[0].grave, "es un error de la fuente, no frena el build"


def test_una_rueda_y_media_no_se_reparte_y_esta_bien():
    """Con un numero impar de cruces el reparto no puede ser parejo. Quejarse
    seria inventar un problema en todos los torneos de tres ruedas."""
    ps = [zona("Boca Juniors", "River Plate", j=f"Fecha {i}") for i in (1, 10)]
    ps.append(zona("River Plate", "Boca Juniors", j="Fecha 20"))
    assert validar.localias_repartidas(ps) == []


def test_cuatro_cruces_van_dos_y_dos():
    """El Federal A 2016-17 jugaba cuadruple rueda: dos de local cada uno."""
    sano = [zona("Boca Juniors", "River Plate", j="Fecha 4"),
            zona("River Plate", "Boca Juniors", j="Fecha 9"),
            zona("Boca Juniors", "River Plate", j="Fecha 14"),
            zona("River Plate", "Boca Juniors", j="Fecha 19")]
    assert validar.localias_repartidas(sano) == []
    roto = sano[:3] + [zona("Boca Juniors", "River Plate", j="Fecha 19")]
    assert len(validar.localias_repartidas(roto)) == 1


def test_el_reducido_no_cuenta():
    """Arsenal y Sarmiento se cruzaron dos veces en 2018 con el mismo local, y
    esta bien: una fue por la fecha 10 y la otra un desempate del Reducido, en
    cancha neutral. Los del todos-contra-todos tienen jornada y esos no."""
    ps = [zona("Boca Juniors", "River Plate", j="Fecha 10"),
          zona("Boca Juniors", "River Plate", j="")]
    assert validar.localias_repartidas(ps) == []


def test_cada_zona_se_mira_aparte():
    """Dos zonas distintas no arman un par: la Zona A y la Zona B tienen cada
    una su fixture, y un club puede jugar en las dos (pasa en el Federal)."""
    ps = [zona("Boca Juniors", "River Plate", z="Zona A", j="Fecha 1"),
          zona("Boca Juniors", "River Plate", z="Zona B", j="Fecha 1")]
    assert validar.localias_repartidas(ps) == []


def test_esta_en_la_lista_de_chequeos():
    assert validar.localias_repartidas in validar.CHEQUEOS


def test_un_partido_sin_fecha_no_duplica_a_otro():
    """Los partidos sin fecha se descartan antes de llegar al CSV, asi que no
    pueden duplicar nada. Contandolos, comparten la clave vacia y cualquier par
    que la fuente escriba dos veces con el mismo local colapsa en "duplicado":
    eso convertia la caida de la segunda fuente -- un aviso leve -- en tres
    errores GRAVES que frenaban el build entero."""
    ps = [zona("Boca Juniors", "River Plate", fecha=""),
          zona("Boca Juniors", "River Plate", fecha="", j="Fecha 20")]
    assert validar.sin_duplicados(ps) == []


def test_el_duplicado_de_verdad_se_sigue_viendo():
    ps = [zona("Boca Juniors", "River Plate", fecha="2026-03-01"),
          zona("Boca Juniors", "River Plate", fecha="2026-03-01")]
    assert len(validar.sin_duplicados(ps)) == 1


# --------------------------------------------------------------------------
# los penales de una serie a dos partidos
# --------------------------------------------------------------------------
def pata(local, visita, gl, gv, pl=None, pv=None):
    return llave(local, visita, gl, gv, "2021-12-13", pl, pv, ronda="Final")


def test_la_tanda_de_una_serie_igualada_no_es_un_error():
    """La final de la Primera C 2021: Argentino de Merlo 2-0 Ituzaingo y despues
    Ituzaingo 2-0 Argentino de Merlo, 2-2 global, penales 4-2. La tanda es de la
    SERIE y la plantilla la cuelga de la pata donde se pateo, que no tiene por
    que haber empatado."""
    ps = [pata("Boca Juniors", "River Plate", 2, 0),
          pata("River Plate", "Boca Juniors", 2, 0, 4, 2)]
    assert validar.penales_solo_en_empates(ps) == []


def test_una_serie_que_no_esta_igualada_si_es_un_error():
    """La excepcion es estrecha a proposito: si el global no empata, la tanda no
    se explica y vuelve a ser la firma del entretiempo leido como penales."""
    ps = [pata("Boca Juniors", "River Plate", 3, 0),
          pata("River Plate", "Boca Juniors", 1, 0, 4, 2)]
    assert len(validar.penales_solo_en_empates(ps)) == 1


def test_un_partido_unico_con_penales_sigue_siendo_grave():
    ps = [pata("Boca Juniors", "River Plate", 2, 0, 4, 2)]
    avisos = validar.penales_solo_en_empates(ps)
    assert len(avisos) == 1 and avisos[0].grave


# --------------------------------------------------------------------------
# un club juega en una sola zona
# --------------------------------------------------------------------------
def test_un_club_en_dos_zonas_es_imposible():
    """El unico chequeo que ve un nombre VALIDO pero equivocado. En el Argentino A
    2010-11 hay cuatro partidos de Union de Mar del Plata escritos "Union (S)",
    que es Union de Sunchales: un club real, enlazado, que jugaba ese mismo torneo
    en otra zona. El padron no puede verlo; el reparto de zonas si."""
    ps = ([zona("Boca Juniors", "River Plate", z="Zona A") for _ in range(3)]
          + [zona("Boca Juniors", "Racing Club", z="Zona B")])
    avisos = validar.una_zona_por_club(ps)
    assert any("Boca Juniors" in a.que for a in avisos)
    assert any("Zona A (3)" in a.detalle and "Zona B (1)" in a.detalle for a in avisos)


def test_un_club_en_una_sola_zona_no_dice_nada():
    ps = [zona("Boca Juniors", "River Plate", z="Zona A"),
          zona("Racing Club", "Huracán", z="Zona B")]
    assert validar.una_zona_por_club(ps) == []


def test_una_fecha_interzonal_no_cuenta():
    """Primera juega una fecha CRUZADA por rueda, contra el clasico de la otra
    zona. Contandola, cada club de cada torneo con interzonales daba un aviso:
    fueron 344 falsos."""
    ps = [zona("Boca Juniors", "River Plate", z="Zona A"),
          zona("Boca Juniors", "Racing Club", z="Interzonal")]
    assert validar.una_zona_por_club(ps) == []


def test_las_zonas_de_llaves_distintas_no_se_mezclan():
    """La Copa de la Liga 2020 tuvo Fase Campeon y Fase Complementacion, cada una
    con su Grupo A y los mismos equipos en las dos."""
    a = zona("Boca Juniors", "River Plate", z="Grupo A")
    b = zona("Boca Juniors", "River Plate", z="Grupo B")
    a.llave, b.llave = "Fase Campeón", "Fase Complementación"
    assert validar.una_zona_por_club([a, b]) == []


def test_esta_en_la_lista_de_chequeos_tambien():
    assert validar.una_zona_por_club in validar.CHEQUEOS


def test_una_fase_con_grupos_y_otra_sin_es_normal():
    """La mezcla se mira DENTRO de cada fase. La Primera B 2020 reparte la "Fase
    segundo ascenso" en Grupo A y Grupo B, y la "Fase primer ascenso" es un solo
    grupo. Comparando las dos juntas, la segunda parecia quince partidos sin zona
    entre treinta con zona, y frenaba el build."""
    con = zona("Boca Juniors", "River Plate", z="Grupo A")
    con.llave = "Fase segundo ascenso"
    sin = zona("Racing Club", "Huracán", z="")
    sin.llave = "Fase primer ascenso"
    assert validar.todos_tienen_zona([con, sin]) == []


def test_la_mezcla_dentro_de_una_fase_sigue_saltando():
    """Que es el caso para el que se escribio: un encabezado no reconocido deja
    unos partidos con la zona anterior y otros sin."""
    con = zona("Boca Juniors", "River Plate", z="Grupo A")
    sin = zona("Racing Club", "Huracán", z="")
    con.llave = sin.llave = "Etapa clasificatoria"
    avisos = validar.todos_tienen_zona([con, sin])
    assert len(avisos) == 1 and "Etapa clasificatoria" in avisos[0].detalle


def test_una_zona_calificada_con_su_fase_sigue_siendo_una_zona():
    """La regresion que casi se cuela con el arreglo del choque de rotulos.

    `una_zona_por_club` solo mira las zonas de verdad, y las reconocia por el
    arranque del nombre. Cuando el parser paso a escribir "Primera fase - Zona 1"
    para desambiguar, esas dejaron de contar y el chequeo se callo justo en la
    pagina que lo motivo -- los cuatro partidos de Union de Mar del Plata
    escritos "Union (S)", que su propio docstring cuenta."""
    ps = [Partido(fecha="2010-08-22", local="Unión (S)", visita="Villa Mitre",
                  goles_local=1, goles_visita=0, fase="zonas",
                  zona="Primera fase - Zona 1", jornada="Fecha 1", llave="Primera fase"),
          Partido(fecha="2010-08-29", local="Unión (S)", visita="Libertad (S)",
                  goles_local=1, goles_visita=0, fase="zonas",
                  zona="Primera fase - Zona 3", jornada="Fecha 2", llave="Primera fase")]
    avisos = validar.una_zona_por_club(ps)
    assert len(avisos) == 1 and "Unión (S)" in avisos[0].que


def test_interzonal_sigue_sin_contar_como_zona():
    """Y el arreglo no puede aflojar eso: "Interzonal" es una fecha cruzada a
    proposito, y contarla daba 344 avisos falsos."""
    ps = [Partido(fecha="2026-01-01", local="Boca Juniors", visita="River Plate",
                  goles_local=1, goles_visita=0, fase="zonas", zona="Zona A",
                  jornada="Fecha 1", llave=""),
          Partido(fecha="2026-01-08", local="Boca Juniors", visita="Platense",
                  goles_local=1, goles_visita=0, fase="zonas", zona="Interzonal",
                  jornada="Fecha 2", llave="")]
    assert validar.una_zona_por_club(ps) == []


def test_el_que_nunca_jugo_no_perdio_nada():
    """Un club que aparece por primera vez en una ronda no viene de la anterior, y
    eso NO es un error: los cuadros reciben gente de afuera por diseño.

    En un reducido, el que termina mejor en la tabla entra directo en semifinales;
    en una Reválida entran los que perdieron en la otra llave -- el Argentino A
    2004-05 lo dice en su propia fuente, "losers enter Round 2 Zona Revalida".
    Acusarlos daba 30 avisos falsos sobre datos correctos.

    Lo que SI es un error es el que jugó antes y sigue jugando sin haber ganado.
    """
    from fad.dataset import Partido

    def p(ronda, local, visita, gl, gv, fecha):
        return Partido(fecha=fecha, hora="", local=local, visita=visita,
                       goles_local=gl, goles_visita=gv, penales_local=None,
                       penales_visita=None, torneo="T", fase="eliminacion", zona="",
                       jornada=ronda, llave="Reducido", estadio="", status="")

    ps = [p("Primera fase", "A", "B", 2, 0, "2024-11-01"),
          # C nunca jugó la primera fase: entró sembrado en semifinales.
          p("Semifinales", "A", "C", 1, 0, "2024-11-08"),
          # Y D entra sembrado en la final, que es lo que hace un torneo cuando el
          # campeón de la otra mitad ya estaba clasificado.
          p("Final", "A", "D", 1, 0, "2024-11-15")]
    avisos = [str(a) for a in validar.cadena_de_llaves(ps)]
    assert not any("sin haber ganado la anterior" in a for a in avisos), avisos
    assert any("entran al cuadro sin venir de la ronda anterior" in a for a in avisos)

    # Y B, que jugó y perdió, sí se denuncia si reaparece.
    ps.append(p("Semifinales", "B", "C", 0, 1, "2024-11-08"))
    avisos = [str(a) for a in validar.cadena_de_llaves(ps)]
    assert any("sin haber ganado la anterior" in a and "B" in a for a in avisos), avisos


def test_un_empate_sin_penales_no_dice_quien_paso_y_no_se_acusa_a_ninguno():
    """`_ganador` devuelve "" en un empate sin penales, asi que los DOS clubes
    quedan afuera de los ganadores y el que avanzo se denuncia solo.

    Y avanzo de verdad: en el reducido argentino, si el partido único termina
    igualado pasa el mejor ubicado de la tabla — una regla que vive FUERA del
    partido y que ninguna columna trae. Pasaba en 44 avisos, entre ellos los tres
    últimos del Federal A 2023 y el Talleres (C) de la Copa Argentina 2019-20,
    cuyo 0-0 de treintaidosavos quedó sin penales en la página.

    Pero no se pierde todo: de una llave igualada pasa UNO. Si aparecen los DOS en
    la ronda siguiente, eso sigue siendo un error y se sigue diciendo.
    """
    from fad.dataset import Partido

    def p(ronda, local, visita, gl, gv, fecha, pl=None, pv=None):
        return Partido(fecha=fecha, hora="", local=local, visita=visita,
                       goles_local=gl, goles_visita=gv, penales_local=pl,
                       penales_visita=pv, torneo="T", fase="eliminacion", zona="",
                       jornada=ronda, llave="Reducido", estadio="", status="")

    # A y B empatan sin penales; A avanza por ventaja deportiva.
    ps = [p("Primera fase", "A", "B", 1, 1, "2024-11-01"),
          p("Primera fase", "C", "D", 2, 0, "2024-11-01"),
          p("Semifinales", "A", "C", 1, 0, "2024-11-08")]
    avisos = [str(a) for a in validar.cadena_de_llaves(ps)]
    assert not any("sin haber ganado la anterior" in a for a in avisos), avisos

    # Pero si avanzan LOS DOS de la llave igualada, uno sobra y hay que decirlo.
    ps.append(p("Semifinales", "B", "D", 1, 0, "2024-11-08"))
    avisos = [str(a) for a in validar.cadena_de_llaves(ps)]
    acusa = [a for a in avisos if "sin haber ganado la anterior" in a]
    assert acusa, avisos
    assert any("A" in a for a in acusa) and any("B" in a for a in acusa), acusa

    # Y con penales, el ganador se conoce: el perdedor sigue siendo un error.
    # Van tres partidos porque con menos el chequeo se abstiene de entrada.
    ps = [p("Primera fase", "A", "B", 1, 1, "2024-11-01", pl=5, pv=3),
          p("Primera fase", "C", "D", 2, 0, "2024-11-01"),
          p("Semifinales", "B", "C", 1, 0, "2024-11-08")]
    avisos = [str(a) for a in validar.cadena_de_llaves(ps)]
    assert any("sin haber ganado la anterior" in a and "B" in a for a in avisos), avisos


def test_una_zona_despareja_no_se_avisa_mientras_se_juega():
    """Mientras la fecha se esta jugando es NORMAL que unos lleven un partido mas
    que otros -- postergados, fechas escalonadas, el partido del domingo --, y
    avisarlo todos los dias durante ocho meses no informa nada: entrena a saltear
    el reporte. Recien con el torneo cerrado una zona despareja significa que falta
    un partido."""
    ps = [zona("A", "B", z="Zona A"), zona("A", "C", z="Zona A")]
    assert validar.zonas_completas(ps, en_curso=True) == []
    assert validar.zonas_completas(ps, en_curso=False), "terminado, si es un aviso"


def test_revisar_le_pasa_el_en_curso_al_chequeo_que_lo_mira():
    """El testigo de arriba a traves de `revisar`, que es como lo llama el build."""
    ps = [zona("A", "B", z="Zona A"), zona("A", "C", z="Zona A")]
    assert not [a for a in validar.revisar(ps, en_curso=True)
                if "no todos jugaron" in a.que]
    assert [a for a in validar.revisar(ps, en_curso=False)
            if "no todos jugaron" in a.que]


# --------------------------------------------------------------------------
# La zona de una fase no es la zona de la otra, y un dividido se jugo
# --------------------------------------------------------------------------
def _zf(local, visita, z, llave=""):
    from fad.parser import Partido
    return Partido(fecha="2010-01-01", local=local, visita=visita, goles_local=1,
                   goles_visita=0, fase="zonas", zona=z, llave=llave,
                   jornada="Fecha 1")


def _rueda(clubes, z, llave="", saltear=()):
    """Ida y vuelta entre todos, menos los partidos (local, visita) de `saltear`.

    Se saltea UNA pata y no las dos: a un club al que le falta un partido tiene
    que quedarle uno menos, no dos.
    """
    import itertools
    return [_zf(a, b, z, llave) for a, b in itertools.permutations(clubes, 2)
            if (a, b) not in set(saltear)]


def _desparejas(ps, **kw):
    return [a for a in validar.zonas_completas(ps, **kw)
            if "no todos jugaron" in a.que]


def test_dos_fases_que_repiten_el_nombre_de_la_zona_son_dos_zonas():
    """Una temporada con fases repite los nombres de sus zonas: el Torneo Federal
    A 2018-19 tiene una "Zona B" en la Primera fase, otra en la Segunda y otra en
    la Revalida. Juntandolas por el nombre, los partidos de tres torneos caen en
    una bolsa y la cuenta sale despareja siempre.

    Medido sobre el corpus: agrupar por (llave, zona) baja este aviso de 15 a 1,
    y el unico que sobrevive es cierto -- la Primera Nacional 2019-20, que la
    pandemia corto con cuatro clubes debiendo un partido.
    """
    dos = _rueda("ABCD", "Zona B", "Primera fase") + _rueda("ABCD", "Zona B", "Revalida")
    assert _desparejas(dos) == [], "cada fase cierra sola"
    # y si de verdad falta uno en una de las dos, se sigue diciendo
    assert _desparejas(dos[:-1]), "un agujero en una fase se sigue viendo"


def test_un_partido_dividido_se_jugo_aunque_no_tenga_fila():
    """El fallo le dio a cada club un resultado distinto y el esquema no puede
    escribir eso, asi que la fila no entra -- pero el partido existio y los dos
    clubes lo jugaron. Sin contarlo, los dos escandalos de arreglo del Argentino
    A 2006-07 dejaban dos zonas desparejas y nada decia por que."""
    falta = _rueda("ABCD", "Zona B", saltear=[("C", "B")])
    assert _desparejas(falta), "sin declararlo, la zona esta despareja"
    assert _desparejas(falta, divididos=[("C", "B", "")]) == []


def test_el_dividido_tambien_cuenta_para_el_todos_contra_todos():
    """Sumarlo en una cuenta y no en la otra deja la zona pareja y el
    todos-contra-todos incompleto: el mismo agujero denunciado por la otra
    puerta."""
    falta = _rueda("ABCD", "Zona B", saltear=[("C", "B")])
    assert validar.zonas_completas(falta, divididos=[("C", "B", "")]) == []


def test_el_dividido_solo_cuenta_en_la_fase_que_declara():
    """El alcance viaja con el par. El del Torneo Federal A 2018-19 es de la
    Revalida, y sus dos clubes tambien juegan la Primera fase: sin el alcance se
    lo cuenta en las dos y arreglar un chequeo rompe el otro."""
    ps = (_rueda("ABCD", "Zona B", "Primera fase")
          + _rueda("ABCD", "Zona B", "Revalida", saltear=[("C", "B")]))
    assert _desparejas(ps, divididos=[("C", "B", "Revalida")]) == []
    assert _desparejas(ps, divididos=[("C", "B", "")]), \
        "sin alcance se cuenta en las dos y rompe la Primera fase"


def test_revisar_le_pasa_los_divididos_al_chequeo():
    falta = _rueda("ABCD", "Zona B", saltear=[("C", "B")])
    assert not any("no todos jugaron" in a.que
                   for a in validar.revisar(falta, divididos=[("C", "B", "")]))


# --------------------------------------------------------------------------
# cada chequeo, por el camino que lo corre el build
# --------------------------------------------------------------------------
# El build no llama a ningun chequeo por su nombre: llama a `revisar`, que recorre
# `CHEQUEOS`. Casi todos los tests de arriba los llaman a mano, asi que sacar uno
# de la lista dejaba la suite verde -- pasaba con siete de los catorce -- y el
# build dejaba de mirarlo sin que nadie se enterara.
#
# Un caso por chequeo, con lo minimo que lo dispara. Lo que dice el chequeo
# llamado a mano tiene que llegar entero por `revisar`: asi el caso queda atado a
# SU chequeo, y no pasa porque otro diga algo parecido.
POR_REVISAR = {
    "campos_completos": lambda: [zona("Boca Juniors", "River Plate", gl=None)],
    "fechas_presentes": lambda: [zona("Boca Juniors", "River Plate", fecha="")],
    "nombres_en_el_padron": lambda: [zona("Boca Juniors", "Club Inventado")],
    "penales_solo_en_empates": lambda: [
        llave("River Plate", "San Lorenzo", 2, 0, "2026-05-17", pl=4, pv=3)],
    "sin_duplicados": lambda: [zona("Boca Juniors", "River Plate"),
                               zona("Boca Juniors", "River Plate")],
    "nadie_juega_contra_si_mismo": lambda: [zona("Boca Juniors", "Boca Juniors")],
    "todos_tienen_zona": lambda: [zona("Boca Juniors", "River Plate"),
                                  zona("Racing Club", "Independiente", z="")],
    "zonas_completas": lambda: torneo_de(4),
    "una_vez_por_jornada": lambda: [zona("Boca Juniors", "River Plate"),
                                    zona("Boca Juniors", "Racing Club")],
    "jornadas_sin_huecos": lambda: torneo_de(4, "Fecha 1") + torneo_de(4, "Fecha 3"),
    "anios_bien_asignados": lambda: _jornada(1, "2020-07-26") + _jornada(2, "2019-08-02"),
    "una_zona_por_club": lambda: [zona("Boca Juniors", "River Plate", z="Zona A"),
                                  zona("Boca Juniors", "Racing Club", z="Zona B")],
    "localias_repartidas": lambda: [
        zona("Boca Juniors", "River Plate", j="Fecha 1"),
        zona("Boca Juniors", "River Plate", fecha="2026-03-08", j="Fecha 2")],
    # Gana Boca la semi, y la final la juega River.
    "cadena_de_llaves": lambda: [
        llave("Boca Juniors", "River Plate", 1, 0, "2026-05-01", ronda="Semifinales"),
        llave("Racing Club", "Platense", 2, 0, "2026-05-02", ronda="Semifinales"),
        llave("River Plate", "Racing Club", 1, 0, "2026-05-10", ronda="Final")],
}


def _dichos(avisos) -> list[tuple]:
    return [(a.que, a.detalle, a.grave) for a in avisos]


@pytest.mark.parametrize("nombre", list(POR_REVISAR))
def test_cada_chequeo_avisa_por_revisar(nombre):
    ps = POR_REVISAR[nombre]()
    suyos = _dichos(getattr(validar, nombre)(ps))
    assert suyos, f"el caso de {nombre} no lo dispara"
    llegan = _dichos(validar.revisar(ps))
    assert [d for d in suyos if d not in llegan] == [], \
        f"{nombre} avisa llamado a mano y no por revisar: ¿salio de CHEQUEOS?"


def test_cada_chequeo_de_la_lista_tiene_su_caso():
    """Los nombres de arriba van escritos a mano, y no sacados de `CHEQUEOS`: si
    salieran de ahi, el que se cae de la lista se llevaria su caso con el. Y al
    reves, un chequeo nuevo en la lista sin su caso tambien se ve."""
    assert sorted(c.__name__ for c in validar.CHEQUEOS) == sorted(POR_REVISAR)

#!/usr/bin/env python3
"""Tests del validador.

Un chequeo que nunca dispara es peor que no tenerlo: da la sensacion de que algo
se esta mirando. Asi que cada uno se prueba de los dos lados -- que se queje con
datos rotos y que se calle con datos sanos.
"""
from __future__ import annotations

import pytest

from fad import validar
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


def test_una_jornada_un_anio_fuera_de_lugar():
    """El caso de la 2019-20 con el corte en el mes equivocado: la Fecha 1 entera
    fechada doce meses adelante, coherente consigo misma y con el marcador bien."""
    ps = ([zona(p.local, p.visita, fecha="2020-07-26", j="Fecha 1") for p in torneo_de(4)]
          + [zona(p.local, p.visita, fecha="2019-08-02", j="Fecha 2") for p in torneo_de(4)])
    avisos = validar.anios_bien_asignados(ps)
    assert len(avisos) == 1 and avisos[0].grave


def test_una_postergacion_de_dos_meses_no_es_un_anio_mal_puesto():
    """La Fecha 9 del Apertura 2026 se jugo entera dos meses despues de la 10 y
    esta perfecta. El umbral es generoso justamente por esto."""
    ps = ([zona(p.local, p.visita, fecha="2026-05-02", j="Fecha 9") for p in torneo_de(4)]
          + [zona(p.local, p.visita, fecha="2026-03-10", j="Fecha 10") for p in torneo_de(4)])
    assert validar.anios_bien_asignados(ps) == []


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
    se esta mirando."""
    sin_ronda = [llave("Boca", "River", 1, 0, "2026-05-01", ronda=""),
                 llave("Racing", "Belgrano", 2, 0, "2026-05-02", ronda=""),
                 llave("Boca", "Racing", 1, 0, "2026-05-10", ronda="")]
    avisos = validar.cadena_de_llaves(sin_ronda)
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

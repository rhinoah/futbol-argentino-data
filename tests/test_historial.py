"""El testigo del historial: que el delta entre dos revisiones aisle un partido.

SIN RED. `arbitrar` recibe la funcion que devuelve la tabla de cada revision, asi
que la logica entera se prueba con tablas escritas a mano. La red vive en
`revisiones` y `tabla_en`, que son dos llamadas a la API y no tienen logica.
"""
from __future__ import annotations

from datetime import date

import pytest

from fad import historial
from fad.historial import Revision

# Los datos del caso que lo motivo, en chiquito: las dos revisiones que rodean
# Platense vs Estudiantes (BA) de la Fecha 6 de la Primera B 2010-11.
ANTES = {"Platense": (5, 2, 4), "Estudiantes (BA)": (5, 7, 2)}
DESPUES = {"Platense": (6, 2, 4), "Estudiantes (BA)": (6, 7, 2)}

R1, R2 = Revision(1, "2010-08-30T03:30:38Z"), Revision(2, "2010-08-31T05:29:54Z")


def _de(mapa):
    """`tabla_de` a partir de {revid: tabla}."""
    return lambda revid: mapa[revid]


def test_los_goles_que_no_se_mueven_son_un_cero_a_cero():
    """El caso que motivo el modulo. Los dos clubes suman un partido y NINGUNO suma
    un gol: el que estaba mirando anoto un 0-0 esa noche. No hay que inferir nada de
    una suma acumulada -- el delta es cero y el partido es el unico que entro."""
    v = historial.arbitrar("Platense", "Estudiantes (BA)", [R1, R2],
                           _de({1: ANTES, 2: DESPUES}))
    assert v.marcador == (0, 0)
    assert (v.antes, v.despues) == (R1, R2)


def test_el_delta_de_goles_ES_el_marcador():
    """Y con goles, lo mismo: el local suma dos a favor y uno en contra, el visitante
    al reves. 2-1."""
    despues = {"Platense": (6, 4, 5), "Estudiantes (BA)": (6, 8, 4)}
    v = historial.arbitrar("Platense", "Estudiantes (BA)", [R1, R2],
                           _de({1: ANTES, 2: despues}))
    assert v.marcador == (2, 1)


def test_los_dos_lados_tienen_que_ser_ESPEJO():
    """El delta del local -- a favor, en contra -- tiene que ser el del visitante
    dado vuelta. Si no lo es, en el medio entro algo mas que este partido, y ahi no
    hay veredicto: es la misma cardinalidad que el repo le exige a cualquier
    emparejamiento."""
    despues = {"Platense": (6, 4, 5), "Estudiantes (BA)": (6, 9, 4)}
    v = historial.arbitrar("Platense", "Estudiantes (BA)", [R1, R2],
                           _de({1: ANTES, 2: despues}))
    assert v.marcador is None
    assert "no coinciden" in v.porque


@pytest.mark.parametrize("pj_local,pj_visita,pedazo", [
    (5, 5, "no entro"),                 # la ventana no alcanza al partido
    (7, 7, "mas de un partido"),        # entraron dos fechas
    (6, 5, "no entro"),                 # solo se movio uno: no es este partido
])
def test_sin_exactamente_un_partido_de_cada_lado_no_hay_veredicto(pj_local, pj_visita,
                                                                  pedazo):
    """Lo que aisla el partido es el PJ, que es lo unico que no admite
    interpretacion. Si los dos clubes no suman exactamente uno cada uno, lo que haya
    en el medio no es este partido solo."""
    despues = {"Platense": (pj_local, 2, 4), "Estudiantes (BA)": (pj_visita, 7, 2)}
    v = historial.arbitrar("Platense", "Estudiantes (BA)", [R1, R2],
                           _de({1: ANTES, 2: despues}))
    assert v.marcador is None and pedazo in v.porque


def test_un_club_que_no_esta_en_la_tabla_no_es_un_veredicto_vacio():
    """Una pagina de copa no tiene tabla de posiciones, asi que este testigo no
    aplica y hay que DECIRLO. Callar y devolver `None` a secas manda a buscar un
    problema que no existe."""
    v = historial.arbitrar("Almagro", "Atlético de Rafaela", [R1, R2],
                           _de({1: ANTES, 2: DESPUES}))
    assert v.marcador is None
    assert "'Almagro' no esta en la tabla" in v.porque


def test_con_una_sola_revision_no_hay_delta():
    v = historial.arbitrar("Platense", "Estudiantes (BA)", [R1], _de({1: ANTES}))
    assert v.marcador is None and "dos revisiones" in v.porque


def test_la_binaria_aisla_el_par_aunque_la_ventana_traiga_muchas():
    """La ventana de un dia trae decenas de revisiones y bajarlas todas seria caro.
    PJ solo crece, asi que la condicion "la tabla ya cuenta este partido" es monotona
    y se puede partir al medio: el caso real se resolvio con seis descargas de trece
    revisiones.

    Lo que se exige no es el ahorro sino el resultado: el par devuelto tiene que ser
    el que ENCIERRA el cambio, no uno cualquiera de la ventana."""
    revs = [Revision(i, f"2010-08-30T0{i}:00:00Z") for i in range(1, 9)]
    tablas = {i: (ANTES if i <= 5 else DESPUES) for i in range(1, 9)}
    bajadas = []

    def tabla_de(revid):
        bajadas.append(revid)
        return tablas[revid]

    v = historial.arbitrar("Platense", "Estudiantes (BA)", revs, tabla_de)
    assert v.marcador == (0, 0)
    assert (v.antes.revid, v.despues.revid) == (5, 6), "el par que encierra el cambio"
    assert len(set(bajadas)) < len(revs), "no baja la ventana entera"


def test_una_revision_intermedia_ilegible_no_rompe_el_arbitraje():
    """Una revision a medio guardar --la tabla rota, el club sin fila-- no puede tirar
    abajo el veredicto NI QUEDAR DE BORDE: los dos bordes se leen al final para sacar
    el delta. Se corre el punto medio hacia `bajo`, que es el unico que ya se sabe
    legible; si no hay ninguna legible en el tramo, el corte queda donde estaba y la
    ventana sale mas grande, nunca mas chica."""
    revs = [Revision(i, f"2010-08-30T0{i}:00:00Z") for i in range(1, 6)]
    # La rota va en el indice que la binaria visita PRIMERO -- (0+4)//2 --, que es la
    # unica manera de ejercitar la rama. Con la rota en otro lado el test pasa sin
    # mirarla, que fue lo que dejo vivo al mutante.
    tablas = {1: ANTES, 2: ANTES, 3: {}, 4: DESPUES, 5: DESPUES}
    v = historial.arbitrar("Platense", "Estudiantes (BA)", revs, _de(tablas))
    assert v.marcador == (0, 0)
    assert {} not in (tablas[v.antes.revid], tablas[v.despues.revid]), (
        "una revision ilegible no puede quedar de borde: el borde se lee al final")


def test_un_delta_negativo_no_es_un_marcador():
    """Si los goles BAJAN, la edicion corrigio otra cosa ademas de cargar el partido,
    y el delta ya no es el marcador. Devolver `(0, -1)` seria escribir un imposible."""
    despues = {"Platense": (6, 2, 3), "Estudiantes (BA)": (6, 6, 2)}
    v = historial.arbitrar("Platense", "Estudiantes (BA)", [R1, R2],
                           _de({1: ANTES, 2: despues}))
    assert v.marcador is None and "negativo" in v.porque


# --------------------------------------------------------------------------
# La lectura del veredicto, que es la mitad que contesta el pendiente.

def test_si_difiere_de_la_grilla_de_hoy_la_pagina_DERIVO():
    """El caso Platense: 0-0 esa noche, 1-1 hoy. El gol entro despues, y el par de
    revisiones fecha desde cuando. Ahi el marcador de esa noche gana."""
    v = historial.arbitrar("Platense", "Estudiantes (BA)", [R1, R2],
                           _de({1: ANTES, 2: DESPUES}))
    dicho = v.contra((1, 1))
    assert "DERIVO" in dicho and "2010-08-31T05:29:54Z" in dicho


def test_si_COINCIDE_con_la_grilla_de_hoy_el_error_es_original():
    """Y este es el que se lee mal. Huracan vs Defensa y Justicia 2011-12 esta
    declarado 2-3 con el timeline de ESPN y el archivo del club, y el historial dice
    1-3. NO lo contradice: dice que ese 1-3 se cargo asi la primera noche, o sea que
    del historial no se recupera nada y hace falta una fuente de afuera.

    Tomar ese 1-3 como si desmintiera la conclusion es el error facil, y por eso el
    veredicto lo dice con todas las letras en vez de devolver un numero pelado."""
    v = historial.arbitrar("Platense", "Estudiantes (BA)", [R1, R2],
                           _de({1: ANTES, 2: DESPUES}))
    dicho = v.contra((0, 0))
    assert "NO CAMBIO DE OPINION" in dicho and "ORIGINAL" in dicho
    assert "DERIVO" not in dicho


def test_sin_veredicto_no_se_opina_sobre_la_grilla():
    v = historial.arbitrar("Platense", "Estudiantes (BA)", [R1], _de({1: ANTES}))
    assert v.contra((1, 1)).startswith("sin veredicto")


# --------------------------------------------------------------------------

def test_la_ventana_se_abre_un_dia_mas_para_atras():
    """El borde de abajo tiene que caer ANTES de que el partido entre en la tabla, y
    la tabla se edita a la noche -- que en UTC ya es el dia siguiente --, asi que un
    borde simetrico cae del lado equivocado."""
    desde, hasta = historial.ventana("2010-08-30", dias=2)
    assert (desde, hasta) == (date(2010, 8, 27), date(2010, 9, 1))
    assert (date(2010, 8, 30) - desde).days > (hasta - date(2010, 8, 30)).days

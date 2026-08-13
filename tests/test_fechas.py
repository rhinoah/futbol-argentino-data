#!/usr/bin/env python3
"""Tests del modulo que completa fechas desde una segunda fuente.

Este modulo toca datos que ya estan bien, asi que lo que hay que probar no es
tanto que complete como que **se niegue a completar** cuando no esta seguro. Una
fecha importada de mas es peor que una fecha faltante: la faltante se ve, la
importada de mas se parece a un dato.

Ninguno sale a la red: se le pasa el HTML.
"""
from __future__ import annotations

import pytest

from fad import fechas
from fad.parser import Partido


def bloque(id_m, cuando, local, id_local, visita, id_visita, gl, gv, estado="finished"):
    return (f'<div data-match_id="{id_m}" data-datetime="{cuando}" '
            f'class="odd {estado} match">'
            f'<div class="team-name team-name-home">'
            f'<a href="/teams/{id_local}/x/">{local}</a></div>'
            f'<div class="team-shortname team-shortname-home">'
            f'<a href="/teams/{id_local}/x/">{local[:4]}</a></div>'
            f'<div class="resultado"><a href="/report/x/">{gl}:{gv}</a></div>'
            f'<div class="team-name team-name-away">'
            f'<a href="/teams/{id_visita}/y/">{visita}</a></div></div>')


def pagina(*bloques, jornada=1):
    return (f'<div class="hs-head round-head">Matchday {jornada}</div>'
            + "".join(bloques))


# --------------------------------------------------------------------------
# la conversion de hora
# --------------------------------------------------------------------------
@pytest.mark.parametrize("utc, dia", [
    ("2007-08-09T22:00:00Z", "2007-08-09"),   # 19:00 en Argentina, mismo dia
    ("2007-08-10T01:00:00Z", "2007-08-09"),   # 22:00 del dia ANTERIOR
    ("2007-08-10T14:00:00Z", "2007-08-10"),
])
def test_la_hora_viene_en_utc(utc, dia):
    """`data-datetime` es UTC y Argentina esta tres horas atras.

    Sin convertir, todo partido que empiece despues de las 21:00 local figura al
    dia siguiente -- o sea la mayoria de los partidos nocturnos. El encabezado
    visible de la pagina muestra el dia local, asi que ni siquiera coincide con
    lo que la propia fuente dice.
    """
    assert fechas._a_hora_local(utc) == dia


def test_una_hora_ilegible_no_inventa_fecha():
    assert fechas._a_hora_local("cuando sea") == ""


# --------------------------------------------------------------------------
# leer la fuente
# --------------------------------------------------------------------------
def test_lee_un_partido():
    ps = fechas.partidos_de(pagina(
        bloque("1", "2007-08-09T22:00:00Z", "Instituto de Córdoba", "te17568",
               "Chacarita Juniors", "te17957", 1, 1)))
    assert len(ps) == 1
    p = ps[0]
    assert (p.fecha, p.jornada) == ("2007-08-09", 1)
    assert (p.local, p.visita) == ("Instituto de Córdoba", "Chacarita Juniors")
    assert (p.goles_local, p.goles_visita) == (1, 1)
    assert (p.id_local, p.id_visita) == ("te17568", "te17957")


def test_el_mismo_equipo_enlazado_dos_veces_es_uno_solo():
    """Cada equipo aparece con su nombre largo y su nombre corto, los dos
    enlazando al mismo id. Tomando los dos primeros ENLACES sin deduplicar, el
    local salia como local y como visitante."""
    ps = fechas.partidos_de(pagina(
        bloque("1", "2007-08-09T22:00:00Z", "Aldosivi", "te21683",
               "Almagro", "te18976", 2, 0)))
    assert (ps[0].local, ps[0].visita) == ("Aldosivi", "Almagro")


def test_un_partido_que_no_se_jugo_no_entra():
    """Suspendido, aplazado o por jugarse: la clase lo dice."""
    assert fechas.partidos_de(pagina(
        bloque("1", "2007-08-09T22:00:00Z", "Aldosivi", "te1",
               "Almagro", "te2", 0, 0, estado="postponed"))) == []


def test_la_jornada_sale_del_encabezado():
    p = pagina(bloque("1", "2007-08-09T22:00:00Z", "A", "te1", "B", "te2", 1, 0),
               jornada=25)
    assert fechas.partidos_de(p)[0].jornada == 25


# --------------------------------------------------------------------------
# deducir el padron sin mirar los nombres
# --------------------------------------------------------------------------
def nuestro(local, visita, gl, gv, jornada, fecha=""):
    return Partido(fecha=fecha, local=local, visita=visita, goles_local=gl,
                   goles_visita=gv, fase="zonas", jornada=f"Fecha {jornada}")


def ajeno(local, visita, gl, gv, jornada, fecha="2007-08-09"):
    return fechas.Ajeno(fecha=fecha, jornada=jornada, local=local, visita=visita,
                        goles_local=gl, goles_visita=gv,
                        id_local=f"te{local}", id_visita=f"te{visita}")


def test_deduce_el_padron_por_marcadores_unicos():
    """La idea: dentro de una jornada, un marcador que aparece UNA sola vez de
    cada lado identifica el partido sin ambiguedad -- y de paso dice quien es
    cada uno de los dos equipos, sin depender de como los escriba cada fuente."""
    nuestros = [nuestro("Aldosivi", "Almagro", 3, 1, 1),
                nuestro("Aldosivi", "Almagro", 2, 0, 2)]
    ajenos = [ajeno("A", "B", 3, 1, 1), ajeno("A", "B", 2, 0, 2)]
    mapa, avisos = fechas.derivar_padron(nuestros, ajenos)
    assert mapa == {"teA": "Aldosivi", "teB": "Almagro"}
    assert avisos == []


def test_un_marcador_repetido_no_identifica_nada():
    """Dos 1-0 en la misma fecha no dicen cual es cual. Forzarlo seria adivinar,
    y un id mal fijado se arrastra a toda la temporada."""
    nuestros = [nuestro("Aldosivi", "Almagro", 1, 0, 1),
                nuestro("Belgrano", "Banfield", 1, 0, 1)]
    ajenos = [ajeno("A", "B", 1, 0, 1), ajeno("C", "D", 1, 0, 1)]
    mapa, _ = fechas.derivar_padron(nuestros, ajenos)
    assert mapa == {}


def test_hace_falta_mas_de_un_voto():
    """Con un solo cruce casual alcanzaria para fijar un club equivocado para
    siempre; pidiendo dos, el error tendria que repetirse en dos jornadas."""
    nuestros = [nuestro("Aldosivi", "Almagro", 3, 1, 1)]
    ajenos = [ajeno("A", "B", 3, 1, 1)]
    mapa, avisos = fechas.derivar_padron(nuestros, ajenos)
    assert mapa == {}
    assert any("menos de 2 votos" in a for a in avisos)


def test_un_id_con_votos_contradictorios_queda_afuera():
    nuestros = [nuestro("Aldosivi", "Almagro", 3, 1, 1),
                nuestro("Belgrano", "Almagro", 2, 0, 2)]
    ajenos = [ajeno("A", "B", 3, 1, 1), ajeno("A", "B", 2, 0, 2)]
    mapa, avisos = fechas.derivar_padron(nuestros, ajenos, minimo=1)
    assert "teA" not in mapa, "un id que voto a dos clubes no puede entrar"
    assert any("contradictorios" in a for a in avisos)


# --------------------------------------------------------------------------
# completar: lo que importa es cuando NO completa
# --------------------------------------------------------------------------
def test_completa_cuando_coincide_todo():
    p = nuestro("Aldosivi", "Almagro", 3, 1, 1)
    n, avisos = fechas.completar([p], [ajeno("A", "B", 3, 1, 1, fecha="2007-08-09")],
                                 {"teA": "Aldosivi", "teB": "Almagro"})
    assert n == 1 and p.fecha == "2007-08-09"


def test_NO_completa_si_el_marcador_no_coincide():
    """EL test del modulo. Paso de verdad: en la Fecha 1 de la B Nacional
    2007-08, Wikipedia dice que Independiente Rivadavia le gano 1-0 a Tiro
    Federal y la otra fuente dice lo contrario. Que las dos fuentes se
    contradigan es informacion; ponerle la fecha igual seria decidir en silencio
    cual tiene razon.
    """
    p = nuestro("Aldosivi", "Almagro", 0, 1, 1)
    n, avisos = fechas.completar([p], [ajeno("A", "B", 1, 0, 1)],
                                 {"teA": "Aldosivi", "teB": "Almagro"})
    assert n == 0 and p.fecha == ""
    assert any("marcador distinto" in a for a in avisos)


def test_no_toca_a_los_que_ya_tienen_fecha():
    p = nuestro("Aldosivi", "Almagro", 3, 1, 1, fecha="2007-01-01")
    n, _ = fechas.completar([p], [ajeno("A", "B", 3, 1, 1, fecha="2007-08-09")],
                            {"teA": "Aldosivi", "teB": "Almagro"})
    assert n == 0 and p.fecha == "2007-01-01", "piso una fecha que ya estaba"


def test_la_jornada_tambien_tiene_que_coincidir():
    """Los mismos dos equipos se cruzan dos veces por temporada, ida y vuelta.
    Sin la jornada, el partido de la primera rueda se llevaria la fecha de la
    segunda."""
    p = nuestro("Aldosivi", "Almagro", 3, 1, 1)
    n, _ = fechas.completar([p], [ajeno("A", "B", 3, 1, 20)],
                            {"teA": "Aldosivi", "teB": "Almagro"})
    assert n == 0 and p.fecha == ""


def test_avisa_de_los_nombres_que_no_reconoce():
    p = nuestro("Aldosivi", "Almagro", 3, 1, 1)
    n, avisos = fechas.completar([p], [ajeno("Rarisimo", "Otro", 3, 1, 1)])
    assert n == 0
    assert any("padron no conoce" in a for a in avisos)


def test_un_marcador_repetido_puede_dar_un_mapeo_consistente_y_FALSO():
    """El caso que de verdad justifica exigir marcadores unicos.

    Aca el 1-0 se repite del lado de la otra fuente, y el equivocado va siempre
    primero. Sin el filtro, el cruce elige ese en las dos jornadas: el mapeo sale
    consistente -- dos votos, ninguna contradiccion -- y por lo tanto ACEPTADO,
    apuntando al club que no es. Ningun chequeo posterior lo agarraria, porque
    para todos los demas se ve perfecto.

    Es la diferencia entre un cruce que no identifica y uno que identifica mal.
    """
    nuestros = [nuestro("Aldosivi", "Almagro", 1, 0, 1),
                nuestro("Aldosivi", "Almagro", 1, 0, 2)]
    ajenos = [ajeno("Falso", "Otro", 1, 0, 1), ajeno("A", "B", 1, 0, 1),
              ajeno("Falso", "Otro", 1, 0, 2), ajeno("A", "B", 1, 0, 2)]
    mapa, _ = fechas.derivar_padron(nuestros, ajenos)
    assert mapa == {}, f"acepto un mapeo sacado de un marcador repetido: {mapa}"


# --------------------------------------------------------------------------
# descubrir competencias y temporadas en el indice del propio sitio
# --------------------------------------------------------------------------
SELECTOR = """
<select>
<option value="/competition/co103/">Primera División</option>
<option value="/competition/co1787/">Primera Nacional</option>
<option value="/competition/co5199/">Primera B Metropolitana</option>
</select>
<select>
<option value="/competition/co1787/argentina-primera-nacional/se112408/2026/all-matches/">2026</option>
<option value="/competition/co1787/argentina-primera-nacional/se107027/2025-playoffs/all-matches/">2025 Playoffs</option>
<option value="/competition/co1787/argentina-primera-nacional/se6101/2010-2011/all-matches/">2010/2011</option>
</select>
"""


def test_las_temporadas_salen_del_selector_del_sitio():
    """Bajando UNA temporada, su selector lista todas las demas: cinco pedidos
    alcanzan para catalogar el sitio entero.

    La alternativa que probamos primero -- adivinar slugs legibles del estilo
    `arg-primera-b-nacional-2010-2011` -- daba 404 en casi todos, porque son
    atajos que a veces existen y a veces no. La 2010/2011 es justo una de las que
    no: por slug es 404, por id existe.
    """
    t = fechas.temporadas_de(SELECTOR)
    assert t["2026"] == ("co1787", "se112408")
    assert t["2010/2011"] == ("co1787", "se6101")


def test_aparecen_temporadas_que_uno_no_imaginaria():
    """"2025 Playoffs", "2024 Relegation", "2025 Gran Final": adivinando nombres
    no se encuentran, y son partidos igual."""
    assert fechas.temporadas_de(SELECTOR)["2025 Playoffs"] == ("co1787", "se107027")


def test_las_competencias_tambien():
    assert fechas.competencias_de(SELECTOR) == {
        "Primera División": "co103",
        "Primera Nacional": "co1787",
        "Primera B Metropolitana": "co5199"}


def test_una_opcion_que_no_es_competencia_no_entra():
    """El mismo `<select>` trae paises y federaciones."""
    otras = '<option value="/matches-today/cy12/">Argentina</option>'
    assert fechas.competencias_de(otras) == {}
    assert fechas.temporadas_de(otras) == {}


def test_la_url_lleva_competencia_y_temporada():
    assert fechas.BASE.format(co="co1787", se="se19981").endswith(
        "/competition/co1787/se19981/all-matches/")

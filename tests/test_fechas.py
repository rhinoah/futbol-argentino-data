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


def bloque(id_m, cuando, local, id_local, visita, id_visita, gl, gv, estado="finished",
           hora="20:30"):
    """Un partido con la estructura REAL de la fuente, no una parecida.

    La version anterior de este helper inventaba `<div class="resultado">` y no
    ponia el horario. Los tests pasaban y el parser estaba roto: leia el `20:30`
    del `match-time` como si fuera el marcador, y devolvia partidos 20-30.
    Ninguno de los tests podia verlo, porque en la fixture ese div no existia.

    Una fixture escrita de memoria prueba el parser contra lo que uno cree que
    manda la fuente. Esta esta copiada de un bloque de verdad -- Aldosivi 0:1
    C.A.I., B Nacional 2010-11 -- con el `match-time` ANTES del `match-result`,
    que es el orden que causaba el problema.
    """
    return (f'<div data-match_id="{id_m}" data-datetime="{cuando}" '
            f'class="odd {estado} match">'
            f'<div class="team-name team-name-home">'
            f'<a href="/teams/{id_local}/x/">{local}</a></div>'
            f'<div class="team-shortname team-shortname-home">'
            f'<a href="/teams/{id_local}/x/">{local[:4]}</a></div>'
            f'<div class="match-time">{hora}</div>'
            f'<div class="match-result match-result-0">'
            f'<a href="/match-report/x/">{gl}:{gv}</a></div>'
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


# --------------------------------------------------------------------------
# el credito
# --------------------------------------------------------------------------
def test_la_fila_dice_de_donde_salio_la_fecha():
    """El credito va fila por fila, no en una nota al pie del README.

    Una fila cuya fecha vino de otra fuente lo dice en `source`, junto a la
    pagina de Wikipedia de la que salio todo lo demas. Un dataset que atribuye
    mal es un dataset que miente sobre si mismo, y eso es un problema de datos
    antes que de licencia.
    """
    from fad import dataset
    p = nuestro("Aldosivi", "Almagro", 3, 1, 1)
    fechas.completar([p], [ajeno("A", "B", 3, 1, 1, fecha="2007-08-09")],
                     {"teA": "Aldosivi", "teB": "Almagro"})
    fila = dataset.a_fila(p, "Primera Nacional", 2007, "https://es.wikipedia.org/wiki/X")
    assert fila["date"] == "2007-08-09"
    assert "es.wikipedia.org" in fila["source"]
    assert "worldfootball" in fila["source"]


def test_la_fila_que_no_uso_la_segunda_fuente_no_la_nombra():
    """La atribucion tiene que ser precisa: nombrar a worldfootball en filas que
    no lo usaron seria tan incorrecto como no nombrarlo en las que si."""
    from fad import dataset
    p = nuestro("Aldosivi", "Almagro", 3, 1, 1, fecha="2007-08-09")
    fila = dataset.a_fila(p, "Primera Nacional", 2007, "https://es.wikipedia.org/wiki/X")
    assert fila["source"] == "https://es.wikipedia.org/wiki/X"


def test_el_credito_no_se_pone_si_no_se_completo():
    """Si el marcador no coincide no se completa la fecha, asi que tampoco hay
    nada que acreditar."""
    p = nuestro("Aldosivi", "Almagro", 0, 1, 1)
    fechas.completar([p], [ajeno("A", "B", 1, 0, 1)],
                     {"teA": "Aldosivi", "teB": "Almagro"})
    assert p.fuente_fecha == ""


# --------------------------------------------------------------------------
# el marcador y el horario tienen la misma forma
# --------------------------------------------------------------------------
def test_el_horario_no_es_el_marcador():
    """`20:30` y `2:0` se escriben igual, y el horario viene primero.

    Este es el bug que las fixtures inventadas no podian ver. El parser tomaba
    el primer `N:N` del bloque, que es la hora de comienzo, y cargaba partidos
    terminados 20 a 30. Lo peor no era el dato absurdo: era que el cruce contra
    Wikipedia reportaba "las dos fuentes dicen marcadores distintos" en 800
    partidos, y la que decia cualquier cosa era esta.
    """
    p, = fechas.partidos_de(pagina(bloque(
        "1", "2010-08-07T18:30:00Z", "Aldosivi", "te21683",
        "CAI", "te20759", 0, 1, hora="20:30")))
    assert (p.goles_local, p.goles_visita) == (0, 1)


def test_sin_marcador_no_hay_partido():
    """Un partido sin `match-result` no se inventa: se saltea.

    Los que todavia no se jugaron traen el div del horario y no el del
    resultado. Si el parser cayera de vuelta en el primer `N:N` del bloque, un
    partido a jugarse el sabado a las 20:30 entraria como 20-30."""
    sin = bloque("1", "2026-08-15T23:30:00Z", "A", "te1", "B", "te2", 0, 0)
    sin = sin.replace('<div class="match-result match-result-0">'
                      '<a href="/match-report/x/">0:0</a></div>', "")
    assert fechas.partidos_de(pagina(sin)) == []


# --------------------------------------------------------------------------
# la derivacion del padron tolera un voto suelto en contra
# --------------------------------------------------------------------------
def _cruce(jornada, gl, gv, local, visita, id_local, id_visita):
    mio = Partido(jornada=f"Fecha {jornada}", local=local, visita=visita,
                  goles_local=gl, goles_visita=gv, fase="zonas")
    suyo = fechas.Ajeno(jornada=jornada, fecha="2010-01-01", goles_local=gl,
                        goles_visita=gv, local=local, visita=visita,
                        id_local=id_local, id_visita=id_visita)
    return mio, suyo


def test_una_localia_al_reves_no_tira_abajo_al_club():
    """Un voto en contra entre muchos a favor no invalida el id.

    En la B Nacional 2009-10 Wikipedia anota Ferro 2-2 Union en la fecha 25 y la
    otra fuente lo da Union 2-2 Ferro. Como el marcador es simetrico, el cruce
    empareja bien el partido y mal los equipos, y quedaba un voto contradictorio
    para cada uno de los dos ids. Exigiendo unanimidad, los dos clubes se caian
    del mapa y con ellos 22 fechas que estaban perfectas.
    """
    mios, suyos = [], []
    for j in range(1, 11):                      # diez votos limpios de cada uno
        m, s = _cruce(j, j, 0, "Ferro", f"Rival {j}", "teF", f"te{j}")
        mios.append(m); suyos.append(s)
    m, s = _cruce(11, 2, 2, "Ferro", "Unión", "teU", "teF")   # el cruzado
    mios.append(m); suyos.append(s)

    mapa, avisos = fechas.derivar_padron(mios, suyos)
    assert mapa["teF"] == "Ferro"
    assert any("minoria" in a for a in avisos)


def test_una_mayoria_ajustada_no_alcanza():
    """Diez a nueve no es un club identificado, es una moneda al aire."""
    mios, suyos = [], []
    for j in range(1, 21):
        quien = "Ferro" if j % 2 else "Unión"
        m, s = _cruce(j, j, 0, quien, f"Rival {j}", "teX", f"te{j}")
        mios.append(m); suyos.append(s)
    mapa, avisos = fechas.derivar_padron(mios, suyos)
    assert "teX" not in mapa
    assert any("contradictorios" in a for a in avisos)


# --------------------------------------------------------------------------
# el huso depende de si el sitio sabe la hora
# --------------------------------------------------------------------------
def _sin_hora(bloque_html: str) -> str:
    return bloque_html.replace('<div class="match-time">20:30</div>',
                               '<div class="match-time match-time-unknown"></div>')


def test_cuando_hay_hora_vale_la_fecha_argentina():
    """`18:30Z` son las 15:30 de Buenos Aires: un sabado a la tarde. El sitio lo
    muestra como 20:30 porque es aleman, pero la hora que se ve no es la del
    partido."""
    p, = fechas.partidos_de(pagina(bloque(
        "1", "2010-08-07T18:30:00Z", "A", "te1", "B", "te2", 1, 0)))
    assert p.fecha == "2010-08-07"


def test_un_partido_de_noche_no_se_va_al_dia_siguiente():
    """22:10Z del 7 son las 19:10 del 7, no del 8."""
    p, = fechas.partidos_de(pagina(bloque(
        "1", "2010-08-07T22:10:00Z", "A", "te1", "B", "te2", 1, 0)))
    assert p.fecha == "2010-08-07"


def test_sin_hora_el_instante_es_un_relleno_y_no_se_convierte():
    """Cuando el sitio no sabe la hora, `data-datetime` no es un instante: es la
    medianoche de ese dia en Berlin. Se nota porque toma DOS valores en toda la
    temporada, 22:00Z y 23:00Z. Restarle tres horas cae en el dia anterior, y asi
    quedaron corridos los 760 partidos de 2007-08 y 2008-09 -- cada uno un dia
    antes del que el propio sitio publica al lado."""
    p, = fechas.partidos_de(pagina(_sin_hora(bloque(
        "1", "2007-08-09T22:00:00Z", "A", "te1", "B", "te2", 1, 0))))
    assert p.fecha == "2007-08-10", "22:00Z es medianoche del 10 en Berlin"


def test_sin_hora_en_invierno_europeo_tambien():
    """En invierno el relleno es 23:00Z, porque Berlin pasa a UTC+1."""
    p, = fechas.partidos_de(pagina(_sin_hora(bloque(
        "1", "2007-12-09T23:00:00Z", "A", "te1", "B", "te2", 1, 0))))
    assert p.fecha == "2007-12-10"


def test_el_horario_de_verano_argentino_se_respeta():
    """Argentina tuvo horario de verano hasta 2009 -- justo en las temporadas que
    se cargan, al reves de lo que decia el comentario que justificaba el UTC-3
    fijo. En enero de 2008 el pais estaba en UTC-2.

    El instante esta elegido para que los dos husos den DIAS distintos, que es lo
    unico que se ve en el dataset: 02:30Z son las 00:30 del 15 en UTC-2 y las
    23:30 del 14 en UTC-3. Con cualquier otro horario los dos dan el mismo dia y
    el test no distingue nada."""
    p, = fechas.partidos_de(pagina(bloque(
        "1", "2008-01-15T02:30:00Z", "A", "te1", "B", "te2", 1, 0)))
    assert p.fecha == "2008-01-15", "UTC-2 en enero de 2008: 00:30 del 15"


def test_fuera_del_horario_de_verano_vale_el_UTC_menos_3():
    """En julio de 2008 Argentina estaba en UTC-3: el mismo instante cae el 14."""
    p, = fechas.partidos_de(pagina(bloque(
        "1", "2008-07-15T02:30:00Z", "A", "te1", "B", "te2", 1, 0)))
    assert p.fecha == "2008-07-14"


# --------------------------------------------------------------------------
# la cache no se envenena
# --------------------------------------------------------------------------
def test_no_se_cachea_una_respuesta_que_no_es_la_pagina(monkeypatch, tmp_path):
    """Un interstitial de firewall o un "access denied" se sirven con status 200
    igual que la pagina buena. Guardado, queda para siempre: todas las corridas
    siguientes leen ESE archivo y devuelven cero partidos sin dar ningun error.
    """
    import urllib.request

    class Respuesta:
        headers = {"Content-Type": "text/html; charset=utf-8"}
        def read(self): return b"<html>Access denied</html>"
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(fechas, "CACHE", tmp_path)
    monkeypatch.setattr(fechas, "PAUSA_MIN", 0)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Respuesta())
    with pytest.raises(OSError, match="no parece una pagina"):
        fechas.descargar("co1", "se1")
    assert list(tmp_path.glob("*.html")) == [], "no tiene que quedar nada guardado"


def test_la_pausa_cuenta_tambien_los_pedidos_que_fallan(monkeypatch, tmp_path):
    """La autolimitacion se desactivaba justo cuando el sitio dice que no: el
    reloj se tocaba despues del pedido exitoso, asi que cuatro 403 salian uno
    atras del otro sin esperar nada."""
    import urllib.request
    monkeypatch.setattr(fechas, "CACHE", tmp_path)
    monkeypatch.setattr(fechas, "_ULTIMO", 0.0)

    def bloqueado(*a, **k):
        raise OSError("HTTP Error 403: Forbidden")

    monkeypatch.setattr(urllib.request, "urlopen", bloqueado)
    with pytest.raises(OSError):
        fechas.descargar("co1", "se1")
    assert fechas._ULTIMO > 0, "un pedido que fallo tambien es un pedido"


# --------------------------------------------------------------------------
# dos partidos indistinguibles no identifican a ninguno
# --------------------------------------------------------------------------
def test_dos_ajenos_con_la_misma_clave_se_descartan_los_dos():
    """Si dos partidos de la otra fuente comparten jornada y los dos equipos, no
    hay forma de saber cual es cual. Antes el segundo pisaba al primero en
    silencio y se importaba la fecha del partido equivocado."""
    p = nuestro("Aldosivi", "Almagro", 3, 1, 1)
    ajenos = [ajeno("Aldosivi", "Almagro", 3, 1, 1, fecha="2007-08-09"),
              ajeno("Aldosivi", "Almagro", 3, 1, 1, fecha="2007-11-30")]
    n, avisos = fechas.completar([p], ajenos)
    assert (n, p.fecha) == (0, "")
    assert any("no identifican nada" in a for a in avisos)


def test_un_partido_arbitrado_toma_la_fecha_igual():
    """`completar` usa el marcador para verificar que las dos fuentes hablan del
    mismo partido. Cuando el emparejamiento ya se confirmo por otro lado -- la
    tabla de posiciones de la propia pagina -- el marcador ya no hace falta como
    verificacion, y la fecha se toma. Es el caso de Talleres 0-4 Atlético
    Tucumán, donde la tabla le da la razon a Wikipedia y no a la otra fuente."""
    p = nuestro("Aldosivi", "Almagro", 0, 4, 36)
    ajenos = [ajeno("Aldosivi", "Almagro", 1, 4, 36, fecha="2009-06-06")]
    n, avisos = fechas.completar([p], ajenos,
                                 arbitrados={("Fecha 36", "Aldosivi", "Almagro")})
    assert (n, p.fecha) == (1, "2009-06-06")
    assert (p.goles_local, p.goles_visita) == (0, 4), "el marcador nuestro no se toca"
    assert any("ya esta arbitrado" in a for a in avisos)


def test_sin_arbitrar_el_marcador_distinto_sigue_frenando():
    """La excepcion se nombra partido por partido. Sin la lista, la regla vale."""
    p = nuestro("Aldosivi", "Almagro", 0, 4, 36)
    ajenos = [ajeno("Aldosivi", "Almagro", 1, 4, 36, fecha="2009-06-06")]
    n, avisos = fechas.completar([p], ajenos)
    assert (n, p.fecha) == (0, "")
    assert any("no se completo" in a for a in avisos)

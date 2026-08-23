#!/usr/bin/env python3
"""Tests del lector del feed de ESPN.

Dos cosas cargan casi todo el riesgo de este adaptador, y ninguna rompe nada
cuando falla: el huso -- una fecha corrida un dia sigue siendo una fecha valida --
y el mapa de nombres -- un club mal traducido sigue siendo un club que existe.
"""
from __future__ import annotations

from fad import espn


class _Eq:
    def __init__(self, nombre): self.nombre = nombre


PADRON = {"Excursionistas", "Villa Dálmine", "Sacachispas", "San Miguel"}


def padron(nombre):
    return _Eq(nombre) if nombre in PADRON else None


MAPA = {"CADU": "Defensores Unidos", "L.N. Alem": "Leandro N. Alem"}


def evento(fecha, local, visita, gl, gv):
    return {"date": fecha, "competitions": [{"competitors": [
        {"homeAway": "home", "team": {"displayName": local}, "score": gl},
        {"homeAway": "away", "team": {"displayName": visita}, "score": gv}]}]}


def leer(*eventos):
    return espn.leer(list(eventos), MAPA, padron_ok=padron)


def test_lee_un_partido():
    aj, avisos = leer(evento("2009-08-22T17:00Z", "San Miguel", "Sacachispas", "0", "1"))
    assert avisos == []
    a = aj[0]
    assert (a.fecha, a.local, a.visita) == ("2009-08-22", "San Miguel", "Sacachispas")
    assert (a.goles_local, a.goles_visita) == (0, 1)


def test_la_fecha_se_convierte_a_hora_argentina():
    """`date` viene en UTC. Un partido de las 21:00 en Argentina es de las 00:00
    UTC del dia siguiente, y sin convertir todos los nocturnos quedan corridos.

    Es la misma trampa que `fad/fechas.py` documenta para worldfootball, y una
    fecha corrida un dia no rompe nada: sigue siendo una fecha valida."""
    aj, _ = leer(evento("2009-08-23T00:30Z", "San Miguel", "Sacachispas", "1", "0"))
    assert aj[0].fecha == "2009-08-22", "00:30 UTC son las 21:30 del dia anterior"


def test_el_mapa_traduce_lo_que_el_padron_no_conoce():
    aj, avisos = leer(evento("2009-08-22T17:00Z", "CADU", "L.N. Alem", "2", "2"))
    assert avisos == []
    assert (aj[0].local, aj[0].visita) == ("Defensores Unidos", "Leandro N. Alem")


def test_un_nombre_que_ni_el_padron_ni_el_mapa_conocen_se_denuncia():
    aj, avisos = leer(evento("2009-08-22T17:00Z", "Club Inventado", "San Miguel", "1", "0"))
    assert aj == []
    assert len(avisos) == 1 and "Club Inventado" in avisos[0]


def test_un_partido_sin_marcador_no_entra():
    """Sin marcador no hay con que verificar el emparejamiento, y emparejar sin
    verificar es lo unico que este modulo no puede hacer."""
    aj, _ = leer(evento("2009-08-22T17:00Z", "San Miguel", "Sacachispas", None, None))
    assert aj == []


def test_la_jornada_va_en_cero_a_proposito():
    """El feed no publica la jornada. El identificador pasa a ser el par
    (local, visita), que en una liga de ida y vuelta ya identifica el partido:
    cada par se cruza una vez en cada cancha. `completar` lo detecta por el cero."""
    aj, _ = leer(evento("2009-08-22T17:00Z", "San Miguel", "Sacachispas", "0", "1"))
    assert aj[0].jornada == 0


# --------------------------------------------------------------------------
# la guarda que el marcador no da
# --------------------------------------------------------------------------
class _Partido:
    def __init__(self, local, visita): self.local, self.visita = local, visita


def test_si_los_planteles_coinciden_no_dice_nada():
    aj, _ = leer(evento("2009-08-22T17:00Z", "San Miguel", "Sacachispas", "0", "1"))
    assert espn.contrastar_plantel(aj, [_Partido("San Miguel", "Sacachispas")]) == []


def test_un_club_que_no_jugo_esa_temporada_se_denuncia():
    """Esta es la guarda que el marcador NO da. Un nombre mal traducido manda el
    partido al club equivocado, y el marcador no lo agarra: dos partidos de la
    misma temporada pueden coincidir en resultado por casualidad, y ahi se
    importa una fecha ajena sin que nada se queje."""
    aj, _ = leer(evento("2009-08-22T17:00Z", "San Miguel", "Sacachispas", "0", "1"))
    avisos = espn.contrastar_plantel(aj, [_Partido("San Miguel", "Excursionistas")])
    assert len(avisos) == 1 and "Sacachispas" in avisos[0]


def test_un_club_nuestro_que_ESPN_no_trae_no_es_un_error():
    """El reciproco no se denuncia: el feed puede no cubrir los playoffs, y que
    le falte un club nuestro no dice nada malo del mapa."""
    aj, _ = leer(evento("2009-08-22T17:00Z", "San Miguel", "Sacachispas", "0", "1"))
    nuestros = [_Partido("San Miguel", "Sacachispas"), _Partido("Excursionistas", "Villa Dálmine")]
    assert espn.contrastar_plantel(aj, nuestros) == []


def test_cada_torneo_con_marca_espn_tiene_liga_rangos_y_mapa():
    for pagina, (liga, rangos, mapa) in espn.FUENTES.items():
        assert liga.startswith("arg."), pagina
        assert rangos and all("-" in r for r in rangos), pagina
        assert isinstance(mapa, dict), pagina


# --------------------------------------------------------------------------
# leer_llaves: el Reducido que Wikipedia solo dibuja
# --------------------------------------------------------------------------
def _evento(slug, fecha, local, visita, gl, gv):
    return {"date": fecha, "season": {"slug": slug},
            "competitions": [{"competitors": [
                {"homeAway": "home", "team": {"displayName": local}, "score": str(gl)},
                {"homeAway": "away", "team": {"displayName": visita}, "score": str(gv)}]}]}


def _ok(n):
    return n


def test_la_fase_regular_no_entra_como_llave():
    """El feed trae la temporada entera y lo unico que dice de que instancia es un
    partido es `season.slug`: un partido de cuartos se ve igual que uno de la fase
    regular en todo lo demas."""
    ev = [_evento("temporada-regular-201112", "2012-03-04T18:00Z", "Dock Sud", "Luján", 1, 0),
          _evento("cuartos-de-final", "2012-05-28T18:00Z", "Dock Sud", "Luján", 1, 0)]
    ps, raros = espn.leer_llaves(ev, {}, "Primera C", padron_ok=_ok)
    assert raros == [] and len(ps) == 1
    assert ps[0].fase == "eliminacion" and ps[0].jornada == "Cuartos de final"


def test_la_fecha_va_en_hora_argentina():
    """LA TRAMPA DEL FEED. La vuelta de la final de la Primera C 2011-12 es
    `2012-06-22T00:00Z`, que en hora argentina es el 21: usar la fecha cruda mete
    un dia de mas en ese partido."""
    ev = [_evento("final", "2012-06-22T00:00Z", "Central Córdoba (R)", "Ferrocarril Midland", 0, 0)]
    ps, _ = espn.leer_llaves(ev, {}, "Primera C", padron_ok=_ok)
    assert ps[0].fecha == "2012-06-21"


def test_la_localia_sale_de_homeaway():
    """Y no del orden en que vengan los competidores: el feed los lista como se le
    da la gana y lo que afirma la localia es `homeAway`."""
    e = _evento("semifinal", "2012-06-06T18:00Z", "Ferrocarril Midland", "Dock Sud", 1, 0)
    e["competitions"][0]["competitors"].reverse()      # ahora el visitante va primero
    ps, _ = espn.leer_llaves([e], {}, "Primera C", padron_ok=_ok)
    assert (ps[0].local, ps[0].goles_local) == ("Ferrocarril Midland", 1)
    assert (ps[0].visita, ps[0].goles_visita) == ("Dock Sud", 0)


def test_un_partido_sin_marcador_se_dice_en_vez_de_entrar_en_cero():
    """Cero no es un error, es un cero: una llave sin marcador no puede entrar con
    0-0, porque despues se lee como un empate."""
    e = _evento("final", "2012-06-17T18:00Z", "Ferrocarril Midland", "Central Córdoba (R)", 1, 2)
    e["competitions"][0]["competitors"][0]["score"] = ""
    ps, raros = espn.leer_llaves([e], {}, "Primera C", padron_ok=_ok)
    assert ps == [] and raros and "sin marcador" in raros[0]

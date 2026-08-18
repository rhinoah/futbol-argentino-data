#!/usr/bin/env python3
"""Tests de las correcciones a mano.

Este modulo es el unico lugar del proyecto donde se sobrescribe lo que dice la
fuente, asi que lo que hay que probar no es que corrija -- eso es una asignacion
-- sino que **se niegue a corregir** cuando no esta parada sobre el partido que
cree. Una correccion que engancha donde no debe no falla: cambia un club por otro
y el dataset queda mintiendo con toda confianza.
"""
from __future__ import annotations

from fad import correcciones
from fad.correcciones import Correccion
from fad.parser import Partido


def partido(local, visita, gl=0, gv=0, jornada="Fecha 12"):
    return Partido(fecha="2009-10-29", local=local, visita=visita, goles_local=gl,
                   goles_visita=gv, fase="zonas", jornada=jornada)


UNA = Correccion(pagina="Una Pagina", jornada="Fecha 12",
                 dice=("All Boys", "Belgrano", 0, 0),
                 debe=("All Boys", "Gimnasia y Esgrima (J)"),
                 porque="de prueba")


def con(monkeypatch, *cs):
    monkeypatch.setattr(correcciones, "CORRECCIONES", cs)


def test_corrige_el_partido_que_identifica(monkeypatch):
    con(monkeypatch, UNA)
    ps = [partido("All Boys", "Belgrano")]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert (n, avisos) == (1, [])
    assert (ps[0].local, ps[0].visita) == ("All Boys", "Gimnasia y Esgrima (J)")


def test_no_toca_los_partidos_de_otra_pagina(monkeypatch):
    con(monkeypatch, UNA)
    ps = [partido("All Boys", "Belgrano")]
    n, _ = correcciones.aplicar(ps, "Otra Pagina")
    assert (n, ps[0].visita) == (0, "Belgrano")


def test_el_marcador_es_parte_de_la_identificacion(monkeypatch):
    """All Boys y Belgrano se cruzan dos veces por temporada. Sin el marcador, la
    correccion podria caer sobre el otro partido."""
    con(monkeypatch, UNA)
    ps = [partido("All Boys", "Belgrano", 2, 1)]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0
    assert ps[0].visita == "Belgrano"
    assert any("ya no engancha" in a for a in avisos)


def test_la_jornada_tambien(monkeypatch):
    con(monkeypatch, UNA)
    ps = [partido("All Boys", "Belgrano", jornada="Fecha 31")]
    n, _ = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0


def test_una_correccion_que_ya_no_aplica_avisa(monkeypatch):
    """Cuando alguien arregle la pagina en Wikipedia, esta entrada queda al pedo.
    Si se callara, quedaria ahi para siempre esperando enganchar con algo."""
    con(monkeypatch, UNA)
    ps = [partido("All Boys", "Gimnasia y Esgrima (J)")]   # ya corregido en la fuente
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0
    assert any("sacala de fad/correcciones.py" in a for a in avisos)


def test_si_engancha_con_dos_no_corrige_ninguno(monkeypatch):
    """Ante la duda, no se toca nada: elegir uno de los dos seria adivinar."""
    con(monkeypatch, UNA)
    ps = [partido("All Boys", "Belgrano"), partido("All Boys", "Belgrano")]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0
    assert all(p.visita == "Belgrano" for p in ps)
    assert any("2 partidos" in a for a in avisos)


# --------------------------------------------------------------------------
# la tabla de verdad
# --------------------------------------------------------------------------
def test_todas_las_correcciones_estan_justificadas():
    """Sin evidencia escrita no entra: es la unica defensa contra que esto se
    convierta en el lugar donde se arregla cualquier dato molesto."""
    for c in correcciones.CORRECCIONES:
        assert len(c.porque) > 80, f"{c.pagina} {c.jornada}: la evidencia es muy flaca"
        assert c.dice[:2] != c.debe, "una correccion que no cambia nada"


def test_las_correcciones_usan_nombres_del_padron():
    """`debe` va en canonico. Un nombre que el padron no conoce dejaria el
    partido peor de lo que estaba, y `nombres_en_el_padron` recien lo agarraria
    despues."""
    from fad import equipos
    for c in correcciones.CORRECCIONES:
        for n in c.debe:
            assert equipos.buscar(n) is not None, f"{n!r} no esta en el padron"


def test_un_marcador_arbitrado_que_ya_no_engancha_avisa(monkeypatch):
    """Si Wikipedia corrige el marcador, el arbitraje queda sin efecto. Tiene que
    decirlo en vez de reventar o de tocar el partido que no es."""
    from fad.correcciones import Marcador
    monkeypatch.setattr(correcciones, "MARCADORES", (
        Marcador(pagina="Una Pagina", jornada="Fecha 1", local="All Boys",
                 visita="Belgrano", dice=(0, 1), debe=(1, 0), porque="x" * 90),))
    ps = [partido("All Boys", "Belgrano", 1, 0, jornada="Fecha 1")]   # ya esta bien
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0
    assert any("no se aplica" in a for a in avisos)


def test_un_marcador_arbitrado_se_aplica(monkeypatch):
    from fad.correcciones import Marcador
    monkeypatch.setattr(correcciones, "MARCADORES", (
        Marcador(pagina="Una Pagina", jornada="Fecha 1", local="All Boys",
                 visita="Belgrano", dice=(0, 1), debe=(1, 0), porque="x" * 90),))
    ps = [partido("All Boys", "Belgrano", 0, 1, jornada="Fecha 1")]
    n, _ = correcciones.aplicar(ps, "Una Pagina")
    assert n == 1 and (ps[0].goles_local, ps[0].goles_visita) == (1, 0)


# --------------------------------------------------------------------------
# la cancha: la tercera forma que tiene la fuente de contradecirse
# --------------------------------------------------------------------------
from fad.correcciones import Cancha

UNA_CANCHA = Cancha(pagina="Una Pagina", jornada="Fecha 36",
                    local="Gimnasia y Esgrima (J)", visita="San Martín (T)",
                    dice="Víctor Antonio Legrotaglie", debe="23 de Agosto",
                    porque="de prueba")


def _con_cancha(estadio, jornada="Fecha 36", local="Gimnasia y Esgrima (J)"):
    p = partido(local, "San Martín (T)", jornada=jornada)
    p.estadio = estadio
    return p


def test_corrige_la_cancha(monkeypatch):
    monkeypatch.setattr(correcciones, "CANCHAS", (UNA_CANCHA,))
    ps = [_con_cancha("Víctor Antonio Legrotaglie")]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert (n, avisos) == (1, [])
    assert ps[0].estadio == "23 de Agosto"


def test_la_cancha_vieja_es_parte_de_la_identificacion(monkeypatch):
    """Si la pagina ya dice otra cosa, la correccion no se aplica a ciegas: o la
    arreglaron, o esta parada sobre un partido que no es."""
    monkeypatch.setattr(correcciones, "CANCHAS", (UNA_CANCHA,))
    ps = [_con_cancha("23 de Agosto")]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0 and len(avisos) == 1 and "engancha con 0" in avisos[0]


def test_una_cancha_corregida_que_ya_no_engancha_avisa(monkeypatch):
    """Cuando alguien arregle la pagina, esta entrada queda sin efecto y el build
    lo dice. Una correccion vieja que nadie saco es una mentira dormida."""
    monkeypatch.setattr(correcciones, "CANCHAS", (UNA_CANCHA,))
    n, avisos = correcciones.aplicar([_con_cancha("Otra", jornada="Fecha 1")], "Una Pagina")
    assert n == 0 and avisos and "sacala de fad/correcciones.py" in avisos[0]


def test_no_toca_las_canchas_de_otra_pagina(monkeypatch):
    monkeypatch.setattr(correcciones, "CANCHAS", (UNA_CANCHA,))
    ps = [_con_cancha("Víctor Antonio Legrotaglie")]
    assert correcciones.aplicar(ps, "Otra Pagina") == (0, [])
    assert ps[0].estadio == "Víctor Antonio Legrotaglie"


def test_las_canchas_corregidas_estan_justificadas():
    """La condicion del modulo: la fuente se contradice sola y se dice donde. Las
    dos que hay salen de la tabla de participantes de la propia pagina."""
    for c in correcciones.CANCHAS:
        assert len(c.porque) > 80, f"{c.jornada} {c.local}: la evidencia es muy flaca"
        assert "participantes" in c.porque, "hay que nombrar al testigo"
        assert c.dice != c.debe


# --------------------------------------------------------------------------
# Reemplazo: la fila que no era una version equivocada del partido sino OTRO
# --------------------------------------------------------------------------
def _fila(llave, jornada, local, visita, gl, gv):
    p = Partido(fecha="", local=local, visita=visita, goles_local=gl, goles_visita=gv,
                fase="zonas", jornada=jornada)
    p.llave = llave
    return p


def test_un_reemplazo_cambia_el_partido_entero():
    """No es un campo mal: la fila describia otro partido. Cambian los dos clubes
    y el marcador de una."""
    p = _fila("Torneo Apertura", "Fecha 5", "Douglas Haig", "Cipolletti", 5, 3)
    _, avisos = correcciones.aplicar([p], "Torneo Argentino A 2005-06")
    assert (p.local, p.visita, p.goles_local, p.goles_visita) == ("Cipolletti", "Douglas Haig", 1, 2)
    # Las demas correcciones de la pagina avisan que no enganchan, y esta bien:
    # la lista tiene un solo partido. Lo que importa es que ESTA no avise.
    assert not [a for a in avisos if "Douglas Haig vs Cipolletti" in a]


def test_la_llave_es_lo_que_hace_posible_el_reemplazo():
    """Sin ella no se puede: la pagina del Argentino A 2005-06 copio dos jornadas
    del Clausura dentro del Apertura, asi que las filas son IDENTICAS en
    (jornada, local, visita, marcador) de los dos lados.

    Este test pone las dos y exige que se toque UNA. Con la clave vieja la
    correccion enganchaba con dos partidos y no se aplicaba -- que era la
    conducta correcta, y por eso hubo que agregar el campo en vez de forzarla."""
    ap = _fila("Torneo Apertura", "Fecha 5", "Douglas Haig", "Cipolletti", 5, 3)
    cl = _fila("Torneo Clausura", "Fecha 5", "Douglas Haig", "Cipolletti", 5, 3)
    _, avisos = correcciones.aplicar([ap, cl], "Torneo Argentino A 2005-06")
    assert not [a for a in avisos if "Douglas Haig vs Cipolletti" in a]
    assert (ap.local, ap.goles_local, ap.goles_visita) == ("Cipolletti", 1, 2), "el del Apertura"
    assert (cl.local, cl.goles_local, cl.goles_visita) == ("Douglas Haig", 5, 3), "el del Clausura no se toca"


def test_un_reemplazo_que_ya_no_engancha_avisa():
    """Si alguien arregla la pagina de Wikipedia, la correccion sobra y hay que
    sacarla. Callarse dejaria una correccion muerta pudriendose en el modulo."""
    p = _fila("Torneo Apertura", "Fecha 5", "Cipolletti", "Douglas Haig", 1, 2)
    n, avisos = correcciones.aplicar([p], "Torneo Argentino A 2005-06")
    assert any("Douglas Haig" in a and "no se aplica" in a for a in avisos)


def test_los_reemplazos_nombran_su_testigo():
    """Cambiar un partido entero es lo mas fuerte que hace este modulo, asi que
    cada uno tiene que decir con que evidencia. La de estos es la tabla de
    posiciones de la propia pagina, que el copy-paste no toco."""
    for r in correcciones.REEMPLAZOS:
        assert len(r.porque) > 120, f"{r.jornada} {r.dice}: la evidencia es muy flaca"
        assert "tabla" in r.porque.lower(), f"{r.jornada} {r.dice}: no nombra el testigo"
        assert r.llave, f"{r.jornada} {r.dice}: sin llave no identifica"


def test_ningun_reemplazo_deja_el_partido_igual():
    for r in correcciones.REEMPLAZOS:
        assert r.dice != r.debe, f"{r.jornada}: reemplazo que no reemplaza nada"


# --------------------------------------------------------------------------
# homonimos: el club mal escrito en TODA la pagina
# --------------------------------------------------------------------------
UN_HOMONIMO = correcciones.Homonimo(
    pagina="Una Pagina", dice="Juventud Unida", debe="Juventud Unida Universitario",
    porque="de prueba")


def test_un_homonimo_renombra_al_club_de_los_dos_lados(monkeypatch):
    monkeypatch.setattr(correcciones, "HOMONIMOS", (UN_HOMONIMO,))
    ps = [partido("Juventud Unida", "Belgrano"), partido("All Boys", "Juventud Unida")]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert avisos == []
    assert [(p.local, p.visita) for p in ps] == [
        ("Juventud Unida Universitario", "Belgrano"),
        ("All Boys", "Juventud Unida Universitario")]


def test_un_homonimo_no_toca_al_club_que_se_llama_parecido(monkeypatch):
    """Es todo el punto: `Juventud Unida` y `Juventud Unida Universitario` son
    dos clubes, y el segundo ya esta bien escrito."""
    monkeypatch.setattr(correcciones, "HOMONIMOS", (UN_HOMONIMO,))
    ps = [partido("Juventud Unida Universitario", "Belgrano")]
    correcciones.aplicar(ps, "Una Pagina")
    assert ps[0].local == "Juventud Unida Universitario"


def test_un_homonimo_no_sale_de_su_pagina(monkeypatch):
    """Un alias global arreglaria una pagina y romperia las otras seis, donde
    `Juventud Unida` es de verdad el club de Primera C."""
    monkeypatch.setattr(correcciones, "HOMONIMOS", (UN_HOMONIMO,))
    ps = [partido("Juventud Unida", "Belgrano")]
    assert correcciones.aplicar(ps, "Otra Pagina") == (0, [])
    assert ps[0].local == "Juventud Unida"


def test_un_homonimo_que_ya_no_engancha_avisa(monkeypatch):
    """Cuando alguien arregle la pagina esto queda sin efecto, y hay que sacarlo.
    Este aviso es el que descubrio que cinco homonimos que se habian escrito ya
    estaban resueltos como `Correccion`."""
    monkeypatch.setattr(correcciones, "HOMONIMOS", (UN_HOMONIMO,))
    avisos = correcciones.homonimos_huerfanos("Una Pagina", {"All Boys", "Belgrano"})
    assert avisos and "sacalo de fad/correcciones.py" in avisos[0]


def test_un_homonimo_que_solo_arregla_la_tabla_no_se_denuncia_solo(monkeypatch):
    """El control mira los dos lados juntos. Adentro de `aplicar`, que solo ve los
    partidos, un homonimo que corrige unicamente la tabla de posiciones se
    declaraba vencido a si mismo -- y el aviso decia lo contrario de la verdad."""
    monkeypatch.setattr(correcciones, "HOMONIMOS", (UN_HOMONIMO,))
    ps = [partido("Juventud Unida Universitario", "Belgrano")]   # la grilla ya esta bien
    assert correcciones.aplicar(ps, "Una Pagina") == (0, [])
    # el nombre corto lo escribe la tabla, y por eso el homonimo sigue haciendo falta
    escritos = {"Juventud Unida Universitario", "Belgrano", "Juventud Unida"}
    assert correcciones.homonimos_huerfanos("Una Pagina", escritos) == []


def test_un_homonimo_vale_para_la_tabla_igual_que_para_los_partidos(monkeypatch):
    """Las dos puertas tienen que dar el mismo nombre. Si la tabla resolviera por
    su cuenta, el cruce no encontraria al club en las dos partes y se saltearia
    la fila -- que es exactamente lo que el homonimo vino a arreglar."""
    monkeypatch.setattr(correcciones, "HOMONIMOS", (UN_HOMONIMO,))
    assert correcciones.homonimo("Una Pagina", "Juventud Unida") == "Juventud Unida Universitario"
    assert correcciones.homonimo("Otra Pagina", "Juventud Unida") == "Juventud Unida"


def test_los_homonimos_corren_despues_de_las_correcciones():
    """El orden no es indistinto: una `Correccion` se identifica por el nombre
    EQUIVOCADO. Si el homonimo renombrara antes, la correccion se apagaria sola
    y nadie se enteraria."""
    dice = correcciones.HOMONIMOS[0].dice
    assert not any(dice in (c.dice[0], c.dice[1])
                   for c in correcciones.CORRECCIONES
                   if c.pagina == correcciones.HOMONIMOS[0].pagina), (
        "hay una Correccion escrita sobre el nombre que el homonimo pisa")


def test_los_homonimos_nombran_su_testigo():
    for h in correcciones.HOMONIMOS:
        assert len(h.porque) > 40, f"{h.dice}: falta la evidencia"
        assert h.dice != h.debe


# --------------------------------------------------------------------------
# el partido que la pagina tiene y no se puede leer
# --------------------------------------------------------------------------
UN_FALTANTE = correcciones.Faltante(
    pagina="Una Pagina", jornada="Fecha 1", local="Defensores de Cambaceres",
    visita="Sportivo Barracas", goles=(0, 0), fecha="2016-02-05", hora="17:00",
    estadio="12 de Octubre", porque="de prueba")


def _hermano():
    p = partido("San Miguel", "Deportivo Laferrere", 1, 3, jornada="Fecha 1")
    p.torneo, p.zona = "Primera C", "Zona Unica"
    return p


def test_un_faltante_agrega_el_partido(monkeypatch):
    monkeypatch.setattr(correcciones, "FALTANTES", (UN_FALTANTE,))
    ps = [_hermano()]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert (n, avisos) == (1, [])
    nuevo = ps[-1]
    assert (nuevo.local, nuevo.visita) == ("Defensores de Cambaceres", "Sportivo Barracas")
    assert (nuevo.goles_local, nuevo.goles_visita) == (0, 0)
    assert nuevo.fecha == "2016-02-05" and nuevo.estadio == "12 de Octubre"


def test_el_faltante_hereda_el_contexto_de_su_jornada(monkeypatch):
    """Torneo, fase y zona son de la RONDA, no del partido. Escribirlos a mano en
    la correccion haria que esta fila sea la unica del torneo que dice otra cosa,
    y eso no falla: sale al CSV con un `group` distinto y el que lo consuma cuenta
    dos zonas donde hay una."""
    monkeypatch.setattr(correcciones, "FALTANTES", (UN_FALTANTE,))
    ps = [_hermano()]
    correcciones.aplicar(ps, "Una Pagina")
    assert (ps[-1].torneo, ps[-1].fase, ps[-1].zona) == ("Primera C", "zonas", "Zona Unica")


def test_un_faltante_no_duplica_si_arreglaron_la_pagina(monkeypatch):
    """El dia que alguien complete la celda en Wikipedia, el parser va a leer la
    fila y esta entrada sobra. Sin la guarda, el partido entraria dos veces."""
    monkeypatch.setattr(correcciones, "FALTANTES", (UN_FALTANTE,))
    ya = partido("Defensores de Cambaceres", "Sportivo Barracas", 0, 0, jornada="Fecha 1")
    ps = [_hermano(), ya]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0 and len(ps) == 2
    assert avisos and "sacalo de fad/correcciones.py" in avisos[0]


def test_un_faltante_sin_hermano_en_su_jornada_no_se_agrega(monkeypatch):
    """Sin hermano no hay de donde heredar la fase ni la zona, y una fila colgada
    de la nada es peor que una fila que falta: la primera miente en silencio."""
    monkeypatch.setattr(correcciones, "FALTANTES", (UN_FALTANTE,))
    ps = [partido("San Miguel", "Deportivo Laferrere", 1, 3, jornada="Fecha 9")]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert n == 0 and len(ps) == 1 and avisos


def test_un_faltante_no_sale_de_su_pagina(monkeypatch):
    monkeypatch.setattr(correcciones, "FALTANTES", (UN_FALTANTE,))
    ps = [_hermano()]
    assert correcciones.aplicar(ps, "Otra Pagina") == (0, [])
    assert len(ps) == 1


def test_los_faltantes_nombran_sus_dos_testigos():
    """Es el unico tipo que AGREGA una fila, asi que la vara es mas alta: el
    marcador tiene que salir de la pagina misma y con dos testigos que no
    dependan uno del otro. Si hay que buscarlo afuera, no entra."""
    for f in correcciones.FALTANTES:
        assert len(f.porque) > 200, f"{f.local}: la evidencia es muy flaca"
        assert "tabla" in f.porque, f"{f.local}: falta el testigo de la tabla"
        assert "resaltado" in f.porque, f"{f.local}: falta el segundo testigo"


# --------------------------------------------------------------------------
# el partido con dos resultados, uno por club
# --------------------------------------------------------------------------
UN_DIVIDIDO = correcciones.Dividido(
    pagina="Una Pagina", local="Almagro", visita="Boca Juniors", dice=(0, 2),
    porque="de prueba: el tribunal se lo dio por perdido a los dos, con marcadores "
           "distintos para cada uno")


def test_un_dividido_sale_del_dataset(monkeypatch):
    """Una fila tiene un `home_score` y un `away_score`: cualquier par de numeros
    afirma UN resultado, y aca hay dos. Publicar el de un club como si fuera el de
    los dos es peor que no publicar la fila."""
    monkeypatch.setattr(correcciones, "DIVIDIDOS", (UN_DIVIDIDO,))
    ps = [partido("Almagro", "Boca Juniors", 0, 2), partido("All Boys", "Belgrano", 1, 1)]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert [(p.local, p.visita) for p in ps] == [("All Boys", "Belgrano")]
    assert avisos == []


def test_el_marcador_identifica_a_cual_de_los_cruces_sacar(monkeypatch):
    """Los mismos dos clubes juegan varias veces en la misma pagina. Sin el
    marcador, sacar 'Almagro vs Boca' saca tambien la ida."""
    monkeypatch.setattr(correcciones, "DIVIDIDOS", (UN_DIVIDIDO,))
    ps = [partido("Almagro", "Boca Juniors", 1, 1)]
    correcciones.aplicar(ps, "Una Pagina")
    assert len(ps) == 1, "saco un partido que no era"


def test_un_dividido_sin_marcador_no_saca_nada(monkeypatch):
    """`dice=None` quiere decir que esa fila NUNCA llega hasta aca, porque su
    celda no se puede leer como marcador (`PP - PP`). No es 'sacar cualquiera':
    leerlo asi borro un Independiente (N) - Deportivo Roca de otra fase."""
    monkeypatch.setattr(correcciones, "DIVIDIDOS", (
        correcciones.Dividido(pagina="Una Pagina", local="Almagro", visita="Boca Juniors",
                              dice=None, porque="de prueba"),))
    ps = [partido("Almagro", "Boca Juniors", 0, 2)]
    n, avisos = correcciones.aplicar(ps, "Una Pagina")
    assert len(ps) == 1 and n == 0 and avisos == []


def test_un_dividido_que_ya_no_esta_avisa(monkeypatch):
    monkeypatch.setattr(correcciones, "DIVIDIDOS", (UN_DIVIDIDO,))
    n, avisos = correcciones.aplicar([partido("All Boys", "Belgrano")], "Una Pagina")
    assert avisos and "sacalo de fad/correcciones.py" in avisos[0]


def test_los_divididos_se_nombran_uno_por_uno():
    """Sacarlos en silencio seria perder el partido. El build los nombra."""
    for d in correcciones.DIVIDIDOS:
        assert d.local in "".join(correcciones.divididos_de(d.pagina))
        assert len(d.porque) > 80, f"{d.local}: falta la evidencia"


def test_los_divididos_no_salen_de_su_pagina(monkeypatch):
    monkeypatch.setattr(correcciones, "DIVIDIDOS", (UN_DIVIDIDO,))
    ps = [partido("Almagro", "Boca Juniors", 0, 2)]
    correcciones.aplicar(ps, "Otra Pagina")
    assert len(ps) == 1

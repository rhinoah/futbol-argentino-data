#!/usr/bin/env python3
"""Tests de las fechas copiadas a mano de una fuente citada.

Es el unico lugar del repo donde un dato se copia a mano, asi que lo que hay que
probar no es tanto el codigo -- son tres lineas -- como las promesas del
docstring: que el marcador verifica, que solo se toma la fecha, y que la tabla no
se desincroniza del resto del repo.
"""
from __future__ import annotations

import build
from fad import citadas, fechas, torneos
from fad.parser import Partido


def test_las_citas_apuntan_a_paginas_que_existen():
    """Una pagina mal escrita en la tabla no rompe nada: simplemente no se aplica
    nunca, en silencio. Es la forma en que este tipo de tabla se muere sola."""
    paginas = {t.pagina for t in torneos.TODOS}
    for pagina in citadas.FECHAS:
        assert pagina in paginas, f"{pagina!r} no es una pagina del catalogo"


def test_los_clubes_de_las_citas_estan_en_el_padron():
    """Van en canonico porque `fechas.completar` compara contra nuestros nombres
    ya canonizados. Uno mal escrito no emparejaria nunca."""
    from fad import equipos

    for citas in citadas.FECHAS.values():
        for c in citas:
            for club in (c.local, c.visita):
                assert equipos.canonizar(club) == club, f"{club!r} no es canonico"


def test_ninguna_cita_esta_repetida():
    """Dos citas del mismo partido son dos fechas para una fila. La regla de
    colision de `completar` las tiraria a las dos, asi que el efecto seria perder
    la fecha en vez de duplicarla -- pero igual es un error de tipeo que conviene
    que salte aca."""
    for pagina, citas in citadas.FECHAS.items():
        pares = [(c.local, c.visita, c.goles_local, c.goles_visita) for c in citas]
        assert len(pares) == len(set(pares)), f"{pagina}: hay citas repetidas"


def test_las_citas_van_como_ajeno_sin_jornada():
    """`jornada=0` a proposito, igual que el feed de ESPN: la fuente rotula sus
    fechas de otra manera que la pagina -- "1ra. Fase" contra "Fecha 1" -- asi que
    el identificador es el par de clubes."""
    a = citadas.ajenos("Torneo Argentino A 2004-05")
    assert a and all(x.jornada == 0 for x in a)
    assert all(x.fecha and x.local and x.visita for x in a)


def test_el_marcador_verifica_la_fecha():
    """EL CONTRATO, que es el mismo que el de cualquier otro completador: los
    clubes identifican el partido y el marcador lo verifica. Una linea mal copiada
    no se cuela -- no empareja, y se avisa."""
    nuestro = Partido(local="Atlético Tucumán", visita="La Florida", goles_local=2,
                      goles_visita=0, fase="zonas", jornada="Fecha 1")
    puestas, _ = fechas.completar(
        [nuestro], [fechas.Ajeno(fecha="2004-09-12", jornada=0,
                                 local="Atlético Tucumán", visita="La Florida",
                                 goles_local=2, goles_visita=0)],
        credito=citadas.CREDITO)
    assert (puestas, nuestro.fecha) == (1, "2004-09-12")

    otro = Partido(local="Atlético Tucumán", visita="La Florida", goles_local=9,
                   goles_visita=9, fase="zonas", jornada="Fecha 1")
    puestas, avisos = fechas.completar(
        [otro], [fechas.Ajeno(fecha="2004-09-12", jornada=0,
                              local="Atlético Tucumán", visita="La Florida",
                              goles_local=2, goles_visita=0)],
        credito=citadas.CREDITO)
    assert puestas == 0 and otro.fecha == ""
    assert any("marcador distinto" in a for a in avisos)


def test_de_la_cita_sale_la_fecha_y_nada_mas():
    """SOLO LA FECHA. La fuente es un blog, de otra categoria que RSSSF o ESPN, y
    lo que la hace aceptable para este uso puntual es justamente que de aca no
    sale ni un marcador, ni una localia, ni un club. Y queda el credito puesto en
    la fila, que es como el dataset dice de donde salio cada fecha."""
    nuestro = Partido(local="Aldosivi", visita="Luján de Cuyo", goles_local=0,
                      goles_visita=1, fase="eliminacion",
                      jornada="Zona Campeonato - Quarterfinals",
                      llave="Torneo Apertura - Zona Campeonato")
    antes = (nuestro.local, nuestro.visita, nuestro.goles_local, nuestro.goles_visita)
    fechas.completar([nuestro], citadas.ajenos("Torneo Argentino A 2004-05"),
                     credito=citadas.CREDITO)
    assert nuestro.fecha == "2004-11-20"
    assert (nuestro.local, nuestro.visita,
            nuestro.goles_local, nuestro.goles_visita) == antes
    assert nuestro.fuente_fecha == citadas.CREDITO


def test_la_llave_separa_al_apertura_del_clausura():
    """EL MISMO PAR DE CLUBES, DOS VECES, Y CADA UNO CON SU FECHA.

    En una temporada con Apertura y Clausura los playoffs vuelven a cruzar a los
    mismos dos: Aldosivi y Lujan de Cuyo juegan los cuartos del Apertura y despues
    las semis del Clausura. El marcador VERIFICA pero no IDENTIFICA -- la clave de
    `completar` es (llave, jornada, local, visita) --, asi que sin la llave las dos
    citas caen en la misma casilla, la regla de colision se lleva puestas a las DOS
    y ninguna de las dos filas queda fechada.

    Este test mira eso desde el CALLER y con las citas de verdad, no con un
    ejemplo armado: si alguien le saca la llave a `Cita` o deja de pasarla en
    `ajenos`, aca se ve como cero fechas puestas y no como un test que hay que
    actualizar."""
    apertura = Partido(local="Aldosivi", visita="Luján de Cuyo", goles_local=0,
                       goles_visita=1, fase="eliminacion",
                       jornada="Zona Campeonato - Quarterfinals",
                       llave="Torneo Apertura - Zona Campeonato")
    clausura = Partido(local="Aldosivi", visita="Luján de Cuyo", goles_local=3,
                       goles_visita=1, fase="eliminacion",
                       jornada="Zona Campeonato - Semifinals",
                       llave="Torneo Clausura - Zona Campeonato")
    puestas, avisos = fechas.completar(
        [apertura, clausura], citadas.ajenos("Torneo Argentino A 2004-05"),
        credito=citadas.CREDITO)
    assert puestas == 2, avisos
    assert (apertura.fecha, clausura.fecha) == ("2004-11-20", "2005-04-17")
    assert not any("cruces" in a for a in avisos), avisos


def test_la_cita_de_otra_fuente_dice_de_cual():
    """Una cita con `fuente` propia entra al `Ajeno` con ella, que es lo que despues
    va a `source`. Si se perdiera en el camino, la fila quedaria atribuida al blog
    que NO publico esa fecha -- y justamente esa fecha existe porque el otro la
    publica rota."""
    from fad import citadas
    con = [a for a in citadas.ajenos("Torneo Argentino A 2004-05") if a.fuente]
    assert len(con) == 1
    assert con[0].fuente == citadas.CREDITO_SOYBH
    assert (con[0].local, con[0].visita, con[0].fecha) == (
        "Ben Hur", "Atlético Tucumán", "2004-12-01")


def test_las_demas_citas_no_inventan_una_fuente():
    """El default es la del modulo, y tiene que quedar vacio para que `completar`
    use esa. Ponerle el credito del modulo a cada cita seria lo mismo escrito dos
    veces, y lo mismo escrito dos veces se escribe distinto."""
    from fad import citadas
    sin = [a for a in citadas.ajenos("Torneo Argentino A 2004-05") if not a.fuente]
    assert len(sin) >= 30


def test_ninguna_cita_cae_fuera_de_su_temporada():
    """EL MARCADOR VERIFICA QUE ES EL PARTIDO; NADA VERIFICABA LA FECHA.

    El contrato de este modulo dice que los clubes identifican y el marcador
    verifica, y eso alcanza para saber que la linea copiada habla del partido que
    creemos. No alcanza para saber que el DIA esta bien: la fuente puede tener una
    errata ahi y el marcador seguiria coincidiendo.

    Y la tiene. Buscando las patas que faltan, el mismo blog escribe
    `01/02/2004 en Rafaela: Ben Hur de Rafaela 2, Atlético Tucumán 1` -- entre un
    partido del 01/12/2004 y otro del 05/12/2004, en las semifinales de un torneo
    que empezo en septiembre --. Los clubes y el marcador son los correctos; el
    dia esta diez meses afuera. Copiada tal cual, esa fecha entraba al dataset y
    ningun chequeo la miraba.

    La ventana de la temporada la cierra: arranca el `mes_inicio` del ano de la
    temporada y termina doce meses despues."""
    from datetime import date

    from fad import torneos

    for pagina, citas in citadas.FECHAS.items():
        t = next(x for x in torneos.TODOS if x.pagina == pagina)
        desde = date(t.temporada, t.mes_inicio, 1)
        hasta = date((t.anio_fin or t.temporada) + (0 if t.anio_fin else 1),
                     t.mes_inicio, 1)
        for c in citas:
            cuando = date.fromisoformat(c.fecha)
            assert desde <= cuando < hasta, (
                f"{pagina}: la cita {c.fecha} de {c.local} vs {c.visita} cae fuera "
                f"de la temporada ({desde} a {hasta})")


def test_cada_cita_engancha_una_sola_fila_y_del_cuadro_que_dice():
    """LO QUE SE MIDIO ANTES DE ESCRIBIRLAS, PUESTO COMO TEST.

    Dos propiedades de la tabla, que es donde puede entrar el error humano:
    ninguna cita repite (llave, local, visita) -- si repitiera, la colision de
    `completar` tiraria las dos y la fecha se perderia en silencio --, y toda
    fecha cae dentro del cuadro que la cita declara, que es el post del que se
    copio. Una fecha del Clausura pegada sobre una llave del Apertura se ve aca."""
    citas = citadas.FECHAS["Torneo Argentino A 2004-05"]
    claves = [(c.llave, c.local, c.visita) for c in citas]
    assert len(set(claves)) == len(claves), "hay citas que no identifican una sola"

    # El Apertura se jugo en 2004 y el Clausura en 2005: es la unica temporada del
    # repo donde un mismo par se cruza en los dos, y por eso alcanza con el anio.
    for c in citas:
        anio = "2004" if "Clausura" not in c.llave else "2005"
        assert c.fecha.startswith(anio), f"{c.fecha} no es del {c.llave}"


_PAGINA = """
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
|
|
|}

== Otra cosa ==
"""


def test_el_build_las_aplica(monkeypatch):
    """El punto de llamada, que es lo que un test sobre la funcion no cubre."""
    from fad.torneos import Torneo

    t = Torneo("Anexo:Prueba", "Prueba", 2004, anio_fin=2005)
    monkeypatch.setitem(
        citadas.FECHAS, "Anexo:Prueba",
        (citadas.Cita("2004-09-12", "Boca Juniors", "River Plate", 2, 1),))
    ps, _ = build.procesar(_PAGINA, t)
    assert [p.fecha for p in ps] == ["2004-09-12"]


def test_sin_citas_no_se_llama_al_completador(monkeypatch):
    """Llamarlo en las 149 paginas cuando una sola tiene citas emitia un "sin
    pareja" en cada una: trece avisos nuevos por una tabla de veinticuatro
    filas."""
    from fad.torneos import Torneo

    def explotar(*a, **k):
        raise AssertionError("no se tiene que llamar")

    monkeypatch.setattr(citadas, "ajenos", explotar)
    build.procesar(_PAGINA, Torneo("Anexo:Otra", "Prueba", 2004, anio_fin=2005))

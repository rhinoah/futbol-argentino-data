#!/usr/bin/env python3
"""Tests del catalogo: que los anios de cada torneo digan lo mismo que su titulo.

`validar.anios_bien_asignados` mira adentro de la pagina, y adentro de la pagina
hay errores de anio que no se pueden ver: si el torneo ENTERO queda un anio
corrido, todas sus fechas siguen en orden entre si; si la segunda mitad queda
catorce meses despues de la primera, nada cae antes de nada. Medido el 10/10/2026
rompiendo a proposito la configuracion de los 168 torneos: de 1015 maneras de
fecharlos mal, 566 pasaban ese chequeo sin un aviso, y 406 de ellas eran el
torneo entero.

Pero hay un testigo que no sale de la configuracion: EL TITULO DE LA PAGINA. No
depende de `temporada` ni de `anio_inicio`, y si no existiera la pagina no se
bajaria. Estas reglas no miran una sola fecha, asi que no dependen de lo que
escriba un editor de Wikipedia: fallan solamente cuando alguien toca el catalogo,
y la suite corre antes que el build de todos los dias.

EL TESTIGO TIENE UN PUNTO CIEGO: un titulo que es una REDIRECCION si se baja --
`wiki.wikitexto` las sigue --, y ahi lo que estas reglas miran es el alias y no
el titulo de verdad. `Copa Argentina 2012` lleva a la 2011-12. El catalogo tiene
uno, `Anexo:Torneo Clausura 1991 (Argentina)`.

LO QUE NO VEN: una copa corrida adentro de los dos anios que nombra su titulo --
son siete, y es el unico error de anio que pasa con un solo campo mal --, y
cualquier error que no sea del anio: un `mes_inicio` mal puesto es del chequeo de
pagina, no de aca.
"""
from __future__ import annotations

import dataclasses
import re

from fad import torneos
from fad.torneos import Torneo

# LOS TORNEOS CUYO TITULO NOMBRA UN SOLO ANIO Y LLEVAN `anio_fin`: terminan en el
# siguiente y la pagina no les escribe el anio. Cruzar el calendario no alcanza:
# el Apertura 2001 cerro el 5 de febrero de 2002 y no va aca, porque su pagina lo
# dice con todas las letras. Van declarados uno por uno porque desde el titulo no
# se pueden distinguir de un `anio_fin` que SOBRA, y ese error es de los que no
# avisan: con un `anio_fin`
# puesto de mas en un torneo de anio calendario, todo lo que se juega antes del mes
# de corte queda fechado un anio despues. Un Apertura -- febrero a junio -- queda
# ENTERO en el anio siguiente, en orden perfecto y sin que nada desentone.
CRUZAN_CON_TITULO_DE_UN_ANIO = {
    "Anexo:Torneo Apertura 1993 (Argentina)":             # termino en marzo de 1994
        1994,
    "Copa de la Liga Profesional 2020":                   # de octubre de 2020 a enero de
        2021,                                             # 2021, y un partido en marzo
    "Campeonato Transición de Primera Nacional 2020":     # los cuatro de la pandemia: de
        2021,                                             # fines de 2020 a enero o febrero
    "Campeonato Transición de Primera B 2020 (Argentina)":
        2021,
    "Campeonato Transición de Primera C 2020 (Argentina)":
        2021,
    "Torneo Transición Federal A 2020":
        2021,
}


def anios_del_titulo(pagina: str) -> tuple[int, ...]:
    """`... 2019-20 (Argentina)` -> (2019, 2020); `... 2026` -> (2026,); sin anio, ()."""
    m = re.search(r"(?<!\d)(\d{4})(?:\s*[-/–—]\s*(\d{4}|\d{2}))?(?!\d)", pagina)
    if not m:
        return ()
    primero = int(m.group(1))
    if not m.group(2):
        return (primero,)
    segundo = int(m.group(2))
    if segundo < 100:
        segundo += primero // 100 * 100
        if segundo < primero:                  # 1999-00
            segundo += 100
    return (primero, segundo)


def faltas(t: Torneo) -> list[str]:
    """Lo que la configuracion de `t` dice distinto de su titulo."""
    del_titulo = anios_del_titulo(t.pagina)
    if not del_titulo:
        return ["el titulo no nombra ningun anio: no hay contra que mirar la entrada"]
    fuera = []
    # 1. El anio con que se fecha. Una liga se fecha desde el primer anio de su
    # titulo. Una copa puede rotularse por el anio en que se definio -- la Copa
    # Argentina 2012-13 es `season=2013`, y lo que el dataset lee de ella se jugo
    # entero en 2013 --, asi que ahi vale cualquiera de los que nombra.
    if t.formato == "copa":
        if t.primer_anio not in del_titulo:
            fuera.append(f"se fecha desde {t.primer_anio} y el titulo dice {del_titulo}")
    elif t.primer_anio != del_titulo[0]:
        fuera.append(f"se fecha desde {t.primer_anio} y el titulo arranca en {del_titulo[0]}")
    # 2. Una temporada que cruza el calendario cruza UN anio.
    if t.anio_fin is not None and t.anio_fin != t.primer_anio + 1:
        fuera.append(f"va de {t.primer_anio} a {t.anio_fin}")
    # 3. Si el titulo nombra dos anios, la liga termina en el segundo. La salvedad
    # es una entrada que lee UNA seccion de la pagina y se juega en un solo anio:
    # el Apertura 1990 vive en la pagina de la 1990-91 y termino en diciembre.
    if len(del_titulo) == 2 and t.formato != "copa" and t.anio_fin != del_titulo[1]:
        if not (t.seccion and t.anio_fin is None):
            fuera.append(f"el titulo llega a {del_titulo[1]} y `anio_fin` es {t.anio_fin}")
    # 4. Si el titulo nombra UN anio, el torneo no lleva `anio_fin` -- salvo los
    # declarados arriba, con el anio en que terminaron.
    if len(del_titulo) == 1 and t.anio_fin != CRUZAN_CON_TITULO_DE_UN_ANIO.get(t.pagina):
        fuera.append(f"el titulo nombra solo {del_titulo[0]} y `anio_fin` es {t.anio_fin}; "
                     f"si de verdad lo necesita, va en CRUZAN_CON_TITULO_DE_UN_ANIO")
    # 5. LA ETIQUETA tambien sale del titulo. `temporada` es la columna `season` y
    # el archivo donde caen las filas, y en las paginas que se fechan con RSSSF
    # ademas fecha. Con `anio_inicio` puesto, la regla 1 ya no la mira.
    if t.formato == "copa":
        if t.temporada not in del_titulo:
            fuera.append(f"se rotula {t.temporada} y el titulo dice {del_titulo}")
    elif t.temporada != del_titulo[0]:
        fuera.append(f"se rotula {t.temporada} y el titulo arranca en {del_titulo[0]}")
    # 6. Una copa de titulo de dos anios, si lleva `anio_fin`, termina en el segundo.
    # Las reglas 3 y 4 no la miran, y la 2 sola deja pasar a la copa fechada desde
    # su segundo anio hasta el siguiente: entera, un anio despues.
    if len(del_titulo) == 2 and t.formato == "copa" and t.anio_fin not in (None, del_titulo[1]):
        fuera.append(f"el titulo llega a {del_titulo[1]} y la copa termina en {t.anio_fin}")
    return fuera


def test_el_titulo_se_lee_en_todas_sus_formas():
    assert anios_del_titulo("Campeonato de Primera B 2026 (Argentina)") == (2026,)
    assert anios_del_titulo("Campeonato de Primera División 1990-91 (Argentina)") == (1990, 1991)
    assert anios_del_titulo("Torneo Argentino A 1999-00") == (1999, 2000)
    assert anios_del_titulo("Copa Argentina 2011-2012") == (2011, 2012)
    assert anios_del_titulo("Torneo Federal A 2016–17") == (2016, 2017), "con raya y no guion"
    assert anios_del_titulo("Torneo Federal A 2016—17") == (2016, 2017), "y con la raya larga"
    assert anios_del_titulo("Torneo del Interior 2010/11") == (2010, 2011)
    assert anios_del_titulo("Copa Suecia") == ()
    assert anios_del_titulo("Ley 12345 del futbol") == (), "cuatro digitos de un numero mas largo"


def test_ningun_torneo_del_catalogo_contradice_a_su_titulo():
    malos = {f"{t.pagina} [{t.torneo} {t.temporada}]": faltas(t)
             for t in torneos.TODOS if faltas(t)}
    assert not malos, malos


def test_los_declarados_que_cruzan_estan_en_el_catalogo():
    """Una declaracion que quedo de una entrada que ya no esta es una excepcion
    esperando a quien no la merece."""
    paginas = {t.pagina for t in torneos.TODOS}
    assert set(CRUZAN_CON_TITULO_DE_UN_ANIO) <= paginas


def _uno(pagina: str) -> Torneo:
    (t,) = [t for t in torneos.TODOS if t.pagina == pagina]
    return t


def test_el_torneo_ENTERO_corrido_un_anio_lo_delata_el_titulo():
    """Lo que ningun chequeo de pagina puede ver, y la forma en que entra mal un
    torneo nuevo: copiar el renglon del anio anterior y cambiarle el titulo. Las
    fechas salen todas un anio antes, en orden perfecto."""
    t = _uno("Campeonato de Primera B 2026 (Argentina)")
    assert faltas(dataclasses.replace(t, temporada=2025))
    assert faltas(dataclasses.replace(t, temporada=2027))
    assert faltas(dataclasses.replace(t, anio_inicio=2025))


def test_una_liga_se_fecha_desde_el_PRIMER_anio_de_su_titulo():
    """No desde cualquiera de los dos: con `temporada=2019` la 2018-19 queda entera
    un anio despues, y 2019 tambien esta en el titulo."""
    t = _uno("Campeonato de Primera División 2018-19 (Argentina)")
    corrida = faltas(dataclasses.replace(t, temporada=2019, anio_fin=2020))
    assert any("arranca en 2018" in f for f in corrida), corrida


def test_una_copa_puede_rotularse_por_cualquiera_de_los_anios_de_su_titulo():
    """Y por ninguno mas. La Copa Argentina 2011-12 se rotula 2012 y se fecha desde
    2011: los dos estan en el titulo. La 2026 es de un solo anio."""
    copa = _uno("Copa Argentina 2011-12")
    assert not faltas(copa)
    assert faltas(dataclasses.replace(copa, anio_inicio=2010, anio_fin=2011))

    abierta = _uno("Copa Argentina 2026")
    assert not faltas(abierta)
    assert faltas(dataclasses.replace(abierta, temporada=2025))
    assert faltas(dataclasses.replace(abierta, temporada=2027))
    desde_antes = faltas(dataclasses.replace(abierta, anio_inicio=2025))
    assert desde_antes == ["se fecha desde 2025 y el titulo dice (2026,)"], desde_antes


def test_un_anio_fin_mas_grande_de_lo_que_va_abre_un_hueco_y_se_ve():
    """La otra clase que el chequeo de pagina no ve: con `anio_fin` un anio de mas
    la segunda mitad queda catorce meses DESPUES de la primera. Nada cae antes de
    nada."""
    t = _uno("Campeonato de Primera División 2018-19 (Argentina)")
    assert not faltas(t)
    assert faltas(dataclasses.replace(t, anio_fin=2020))
    assert faltas(dataclasses.replace(_uno("Copa de la Liga Profesional 2020"), anio_fin=2022))


def test_un_anio_fin_que_SOBRA_en_un_torneo_de_un_solo_anio_tambien():
    """El que no avisa nunca. Un Apertura va de febrero a junio: con un `anio_fin`
    puesto de mas y el corte en agosto, TODO el torneo queda en el anio siguiente,
    con sus fechas en orden. Cumple las otras tres reglas."""
    apertura = _uno("Anexo:Torneo Apertura 2026 (Argentina)")
    assert not faltas(apertura)
    assert faltas(dataclasses.replace(apertura, anio_fin=2027))
    assert faltas(dataclasses.replace(_uno("Campeonato de Primera B 2026 (Argentina)"),
                                      anio_fin=2027))
    assert faltas(dataclasses.replace(_uno("Copa Argentina 2026"), anio_fin=2027)), \
        "y una copa de un solo anio, igual"

    # Y los que si cruzan lo tienen que decir: sin el `anio_fin`, enero de 2021 se
    # fecha en 2020. Es el error que tuvo la Copa de la Liga 2020 durante dos meses.
    copa_de_la_liga = _uno("Copa de la Liga Profesional 2020")
    assert not faltas(copa_de_la_liga)
    assert faltas(dataclasses.replace(copa_de_la_liga, anio_fin=None))


def test_una_temporada_de_dos_anios_sin_anio_fin_no_pasa():
    """El olvido mas natural: sin `anio_fin` todo se fecha en el primer anio y la
    segunda rueda queda antes que la primera. Ese SI lo ve el chequeo de pagina --
    cuando la pagina ya tiene las dos mitades --; esto lo ve el primer dia."""
    t = _uno("Campeonato de Primera División 2018-19 (Argentina)")
    assert faltas(dataclasses.replace(t, anio_fin=None))

    apertura_1990 = _uno("Campeonato de Primera División 1990-91 (Argentina)")
    assert apertura_1990.seccion and apertura_1990.anio_fin is None
    assert not faltas(apertura_1990), "lee una seccion que se jugo entera en 1990"
    assert faltas(dataclasses.replace(apertura_1990, seccion=""))


def test_la_etiqueta_tambien_sale_del_titulo():
    """El arreglo apurado. El test dice "se fecha desde 2025 y el titulo arranca en
    2026", alguien pone `anio_inicio=2026` en vez de corregir `temporada`, y queda
    verde: no cambia una sola fecha y todas las filas se van a otra temporada. En
    una pagina fechada con RSSSF es peor, porque ahi `temporada` tambien fecha."""
    t = _uno("Campeonato de Primera B 2026 (Argentina)")
    apurado = faltas(dataclasses.replace(t, temporada=2025, anio_inicio=2026))
    assert apurado == ["se rotula 2025 y el titulo arranca en 2026"], apurado

    # Una copa puede rotularse por cualquiera de los dos, y por ninguno mas.
    copa = _uno("Copa Argentina 2011-12")
    assert copa.temporada == 2012 and copa.primer_anio == 2011 and not faltas(copa)
    otra = faltas(dataclasses.replace(copa, temporada=2013))
    assert otra == ["se rotula 2013 y el titulo dice (2011, 2012)"], otra

    # Y en una liga es el PRIMERO: 2019 tambien esta en el titulo de la 2018-19.
    liga = _uno("Campeonato de Primera División 2018-19 (Argentina)")
    por_el_segundo = faltas(dataclasses.replace(liga, temporada=2019, anio_inicio=2018))
    assert por_el_segundo == ["se rotula 2019 y el titulo arranca en 2018"], por_el_segundo


def test_ni_la_lista_de_los_declarados_puede_cruzar_dos_anios(monkeypatch):
    """La regla 4 le cree a la lista. Si la lista dijera 2022 para un torneo de
    2020, lo unico que queda para decir que no es la regla 2."""
    monkeypatch.setitem(CRUZAN_CON_TITULO_DE_UN_ANIO, "Copa de la Liga Profesional 2020", 2022)
    t = dataclasses.replace(_uno("Copa de la Liga Profesional 2020"), anio_fin=2022)
    assert faltas(t) == ["va de 2020 a 2022"]


def test_una_copa_de_dos_anios_cruza_UNO_y_termina_en_el_segundo():
    """Para una copa las reglas 3 y 4 no corren, asi que a su `anio_fin` lo miran
    otras dos, y cada una ve algo que la otra no.

    Fechada desde el segundo anio de su titulo y hasta el siguiente cruza un anio,
    como pide la regla 2, y queda ENTERA un anio despues: lo dice la 6. Fechada
    desde el segundo y hasta el segundo termina donde dice el titulo, como pide la
    6, y lo que se jugo en 2011 sale en 2012: lo dice la 2."""
    copa = _uno("Copa Argentina 2011-12")
    un_anio_despues = faltas(dataclasses.replace(copa, anio_inicio=None, anio_fin=2013))
    assert un_anio_despues == ["el titulo llega a 2012 y la copa termina en 2013"], un_anio_despues

    sin_cruzar = faltas(dataclasses.replace(copa, anio_inicio=None, anio_fin=2012))
    assert sin_cruzar == ["va de 2012 a 2012"], sin_cruzar


def test_un_titulo_sin_anio_no_pasa_callado():
    """Hay paginas asi -- `Copa Suecia`, `Copa Centenario de la AFA` --. El dia que
    entre una, estas reglas no tienen contra que mirarla: que lo digan."""
    sin_anio = dataclasses.replace(_uno("Copa Argentina 2026"), pagina="Copa Suecia")
    assert faltas(sin_anio)

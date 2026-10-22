#!/usr/bin/env python3
"""Tests del parser.

Casi todos apuntan a lo mismo: que el parser falle en vez de mentir. Cada uno de
los de mas abajo con nombre `test_bug_*` corresponde a un error que efectivamente
estuvo en el codigo y que ninguna excepcion delataba.
"""
from __future__ import annotations

import re

import pytest

from fad import equipos, parser
from tests.conftest import LLAVES, TABLA


# --------------------------------------------------------------------------
# limpieza
# --------------------------------------------------------------------------
@pytest.mark.parametrize("crudo, limpio", [
    ("[[Club Atlético Unión|Unión]]", "Unión"),
    ("[[Boca Juniors]]", "Boca Juniors"),
    ("'''River Plate'''", "River Plate"),
    ("Talleres<ref name=x>nota</ref>", "Talleres"),
    ("Lanús<ref name=y/>", "Lanús"),
    ("{{bandera|ARG}} Racing", "Racing"),
    ("Vélez<br/>Sarsfield", "Vélez Sarsfield"),
    ("  Huracán   ", "Huracán"),
])
def test_limpiar(crudo, limpio):
    assert parser.limpiar(crudo) == limpio


# --------------------------------------------------------------------------
# la pagina sin comentarios
# --------------------------------------------------------------------------
def test_un_comentario_termina_en_el_primer_cierre():
    """De un `<!--` al ultimo `-->` se iria lo que hay entre dos comentarios: aca, el
    titulo de la seccion que si se ve."""
    assert parser.sin_comentarios("a<!-- x -->b<!-- y -->c") == "abc"
    assert parser.sin_comentarios("<!--== Final ==\n-->== Final ==\n<!-- -->{{Partido\n") == (
        "== Final ==\n{{Partido\n")


def test_los_comentarios_no_se_anidan():
    """El primer `-->` cierra, aunque adentro haya otro `<!--`: lo que sigue se ve en
    la pagina, `-->` incluido. Y un `-->` sin `<!--` es texto."""
    assert parser.sin_comentarios("a<!-- b <!-- c --> d -->e") == "a d -->e"
    assert parser.sin_comentarios("a --> b") == "a --> b"


def test_un_comentario_sin_cerrar_tapa_todo_lo_que_sigue():
    """Es lo que hace MediaWiki: la pagina no muestra nada despues del `<!--`."""
    texto = "a<!-- x -->b<!-- sin cerrar\n== Final ==\n{{Partido\n"
    assert parser.sin_comentarios(texto) == "ab"
    assert parser.comentario_sin_cerrar(texto) == texto.index("<!-- sin")
    assert parser.comentario_sin_cerrar("a<!-- x -->b<!-- y -->") == -1
    assert parser.comentario_sin_cerrar("sin comentarios") == -1


@pytest.mark.parametrize("abre, cierra", [
    ("<nowiki>", "</nowiki>"), ("<NoWiki>", "</nowiki >"), ("<pre>", "</pre>"),
    ('<pre style="x">', "</PRE>"), ("<pre\n>", "</pre>"),
])
def test_adentro_de_nowiki_y_pre_un_comentario_es_texto(abre, cierra):
    """MediaWiki muestra el `<!--` tal cual, y lo que sigue al cierre se limpia."""
    crudo = f"a{abre}b <!-- c{cierra} d<!-- e -->f"
    assert parser.sin_comentarios(crudo) == f"a{abre}b <!-- c{cierra} df"
    assert parser.comentario_sin_cerrar(crudo) == -1


@pytest.mark.parametrize("crudo, limpio", [
    # Autocerrada no tiene adentro: el comentario que sigue es un comentario, aunque
    # mas abajo cierre otra.
    ("a<nowiki/>b<!-- c -->d<nowiki>e</nowiki>", "a<nowiki/>bd<nowiki>e</nowiki>"),
    ("a<nowiki />b<!-- c -->d", "a<nowiki />bd"),
    # Una que no cierra es texto y nada mas.
    ("a<nowiki>b<!-- c -->d", "a<nowiki>bd"),
    # Una etiqueta que empieza como `pre` no es `pre`, aunque mas abajo cierre una.
    ("a<prefacio>b<!-- c -->d<pre>e</pre>", "a<prefacio>bd<pre>e</pre>"),
    # Y una <nowiki> adentro de un comentario esta comentada.
    ("a<!-- <nowiki> -->b</nowiki><!-- c -->d", "ab</nowiki>d"),
])
def test_cuando_una_nowiki_no_protege_nada(crudo, limpio):
    assert parser.sin_comentarios(crudo) == limpio


# --------------------------------------------------------------------------
# celdas y rowspan
# --------------------------------------------------------------------------
@pytest.mark.parametrize("celda, filas, valor", [
    ("Boca Juniors", 1, "Boca Juniors"),
    ("rowspan=3|22 de enero", 3, "22 de enero"),
    ('rowspan="2"|21:00', 2, "21:00"),
    ("bgcolor=#d0e7ff|'''River Plate", 1, "River Plate"),
    ("width=21%|Local", 1, "Local"),
])

def test_celda(celda, filas, valor):
    assert parser._celda(celda) == (filas, valor)


def test_celda_no_confunde_contenido_con_atributos():
    """Un `|` dentro del contenido no es el separador de atributos.

    `[[Club Atlético Unión|Unión]]` tiene una barra y no lleva atributos: si se
    corta ahi, el equipo pasa a llamarse "Unión]]".
    """
    assert parser._celda("[[Club Atlético Unión|Unión]]") == (1, "Unión")


# --------------------------------------------------------------------------
# fechas
# --------------------------------------------------------------------------
@pytest.mark.parametrize("texto, iso", [
    ("22 de enero", "2026-01-22"),
    ("3 de marzo", "2026-03-03"),
    ("17 de Mayo", "2026-05-17"),
    ("9 de setiembre", "2026-09-09"),
    ("9 de septiembre", "2026-09-09"),
    ("1 de diciembre", "2026-12-01"),
])
def test_a_iso(texto, iso):
    assert parser.a_iso(texto, 2026) == iso


@pytest.mark.parametrize("basura", ["", "a confirmar", "32 de tarzo", "manana"])
def test_a_iso_no_inventa(basura):
    assert parser.a_iso(basura, 2026) == ""


# La celda que escribe el dia y el mes sin el «de». Es una sola en todo el corpus
# y esta en la Fecha 35 de la Zona A de la Primera Nacional 2023; el recorte es el
# de la pagina (revision 175069047), con la fila de arriba y la de abajo para que
# se vea que el `rowspan=4` cubre a las cuatro y a ninguna mas.
_FECHA_35_DE_LA_PN_2023 = """
== Resultados ==
{|class="wikitable collapsible collapsed" style="font-size: 95%; margin: 5px auto; text-align: center; width:100%;"
!colspan=6|Fecha 35
|-
! width="20%" |Local
! width="10%" |Resultado
! width="20%" |Visitante
! width="28%" |Estadio
! width="14%" |Fecha
! width="8%" |Hora
|-
|San Martín (T)
|bgcolor=#D0E7FF|'''1 - 1
|Güemes (SdE)
|La Ciudadela
|23 de septiembre
|18:00
|-
|bgcolor=#D0E7FF|'''Guillermo Brown
|1 - 0
|San Martín (SJ)
|Raúl Conti
|rowspan=4|24 septiembre
|rowspan=2|15:30
|-
|Almagro
|bgcolor=#D0E7FF|'''1 - 1
|Alvarado
|Tres de Febrero
|-
|Nueva Chicago
|bgcolor=#D0E7FF|'''0 - 0
|Deportivo Morón
|Nueva Chicago
|15:50
|-
|bgcolor=#D0E7FF|'''Estudiantes (RC)
|1 - 0
|Defensores de Belgrano
|Antonio Candini
|18:00
|-
|bgcolor=#D0E7FF|'''All Boys
|2 - 1
|Almirante Brown
|Islas Malvinas
|25 de septiembre
|21:10
|}

== Otra cosa ==
"""


def test_el_dia_y_el_mes_sin_el_de_tambien_son_una_fecha():
    """`|rowspan=4|24 septiembre`: la pagina tiene el dia y `a_iso` devolvia vacio
    porque pide «de». Los cuatro partidos salian sin fecha y se la ponia otra fuente.

    El testigo de afuera es RSSSF, que no lee este test y lo puede contradecir:
    `arg2023`, Round 35 de la Zona A, pone los cuatro bajo `[Sep 24, Sun]` --
    `CSyA Guillermo Brown 1- 0 CA San Martín (San Juan)`, `Club Almagro 1- 1 CA
    Alvarado`, `CA Nueva Chicago 0- 0 CD Morón` y `AA Estudiantes 1- 0 CA Defensores
    de Belgrano`--. El 24 de septiembre de 2023 fue domingo.

    Las HORAS son de la pagina y siempre lo fueron: lo que faltaba era el dia."""
    ps = parser.partidos(_FECHA_35_DE_LA_PN_2023, 2023, "Primera Nacional")
    assert [(p.fecha, p.hora, p.local, p.goles_local, p.goles_visita, p.visita)
            for p in ps] == [
        ("2023-09-23", "18:00", "San Martín (T)", 1, 1, "Güemes (SdE)"),
        ("2023-09-24", "15:30", "Guillermo Brown", 1, 0, "San Martín (SJ)"),
        ("2023-09-24", "15:30", "Almagro", 1, 1, "Alvarado"),
        ("2023-09-24", "15:50", "Nueva Chicago", 0, 0, "Deportivo Morón"),
        ("2023-09-24", "18:00", "Estudiantes (RC)", 1, 0, "Defensores de Belgrano"),
        ("2023-09-25", "21:10", "All Boys", 2, 1, "Almirante Brown")]
    import datetime
    assert datetime.date(2023, 9, 24).weekday() == 6, "domingo, como dice RSSSF"


@pytest.mark.parametrize("texto, iso", [
    ("24 septiembre", "2026-09-24"),
    ("24 Septiembre", "2026-09-24"),
    ("3 marzo de 2027", "2027-03-03"),
])
def test_a_iso_sin_el_de(texto, iso):
    assert parser.a_iso(texto, 2026) == iso


@pytest.mark.parametrize("texto", [
    "2023 septiembre",          # los dos ultimos digitos de un anio
    "Temporada 2024 marzo",
    "15:30 marzo",              # los minutos de una hora
    "24 septiembres",           # el mes termina ahi
    "3 mayores",
    "24 tarzo",                 # el mes es de la lista, no cualquier palabra
])
def test_a_iso_sin_el_de_no_inventa(texto):
    """Sin el «de», lo unico que separa una fecha de un numero y una palabra es lo
    que tienen alrededor. Cada uno de estos devolvia vacio antes de la segunda regla
    y tiene que seguir devolviendolo."""
    assert parser.a_iso(texto, 2026) == ""


def test_la_regla_sin_el_de_no_le_gana_a_la_de_siempre():
    """Se prueba SOLO cuando la primera no encontro nada. En una nota que trae las
    dos formas manda la que el corpus ya leia: sin ese orden, agregar la segunda
    regla podria cambiarle el dia a una fila que hoy esta bien."""
    assert parser.a_iso("previsto 3 marzo, se jugo el 17 de abril", 2026) == "2026-04-17"


# --------------------------------------------------------------------------
# temporadas que cruzan el anio
# --------------------------------------------------------------------------
@pytest.mark.parametrize("texto, iso", [
    ("26 de agosto", "2016-08-26"),      # arranque: primer anio
    ("13 de diciembre", "2016-12-13"),
    ("19 de enero", "2017-01-19"),       # ya cruzo: segundo anio
    ("27 de junio", "2017-06-27"),
])
def test_temporada_que_cruza_el_calendario(texto, iso):
    """El campeonato 2016-17 fue de agosto de 2016 a junio de 2017, y la pagina
    escribe el dia y el mes pero nunca el anio."""
    assert parser.a_iso(texto, 2016, anio_fin=2017) == iso


def test_bug_el_mes_de_arranque_no_es_siempre_agosto():
    """La 2019-20 arrancó el 26 de JULIO de 2019.

    Con el corte habitual en agosto, sus doce partidos de la Fecha 1 quedaban
    fechados en julio de 2020 -- la primera jornada del torneo, un anio adelante,
    al final de la temporada. Coherentes entre si, con el marcador bien, y a
    doce meses de donde iban.
    """
    assert parser.a_iso("26 de julio", 2019, anio_fin=2020) == "2020-07-26"
    assert parser.a_iso("26 de julio", 2019, anio_fin=2020, mes_inicio=7) == "2019-07-26"


def test_sin_anio_fin_el_mes_no_cambia_nada():
    assert parser.a_iso("26 de julio", 2026, mes_inicio=7) == "2026-07-26"


# --------------------------------------------------------------------------
# la fecha en plantilla
# --------------------------------------------------------------------------
def test_bug_la_fecha_puede_venir_en_una_plantilla():
    """`|fecha = {{fecha|17|1|2021}}, 22:10 ([[UTC-3]])`.

    Hay que leerla ANTES de limpiar: limpiar borra las plantillas y deja la celda
    en ', 22:10 (UTC-3)', o sea un partido sin fecha.
    """
    assert parser._fecha_de_plantilla("{{fecha|17|1|2021}}, 22:10 ([[UTC-3]])") == "2021-01-17"
    assert parser.limpiar("{{fecha|17|1|2021}}, 22:10 ([[UTC-3]])") == ", 22:10 (UTC-3)"


def test_la_plantilla_trae_el_anio_y_manda():
    """La final de la Copa de la Liga 2020 se jugo el 17 de enero de 2021.
    Cualquier anio deducido del torneo la pondria un anio antes."""
    texto = """{{Partido
|local = Boca Juniors
|resultado = 1:1
|visita = Banfield
|fecha = {{fecha|17|1|2021}}, 22:10 ([[UTC-3]])
}}"""
    p = parser.partidos_de_plantillas(texto, 2020, "Copa de la Liga")[0]
    assert p.fecha == "2021-01-17"


@pytest.mark.parametrize("crudo", ["{{fecha|17|13|2021}}", "{{fecha|17|1}}", "17 de enero", ""])
def test_plantilla_de_fecha_no_inventa(crudo):
    assert parser._fecha_de_plantilla(crudo) == ""


# --------------------------------------------------------------------------
# enlaces a archivos
# --------------------------------------------------------------------------
def test_bug_un_enlace_a_archivo_no_es_texto():
    """`[[Archivo:Copa.svg|15px|Campeón]]` es una imagen, no un nombre.

    Tratandola como un wikilink comun deja el ultimo parametro pegado, y el
    equipo pasa a llamarse "Boca Juniors 15px|Campeón matemático". Van veinte
    nombres asi en las temporadas 2016-2024, donde marcaban al campeon y a los
    descendidos con un iconito.
    """
    crudo = "'''Boca Juniors [[Archivo:Trophy.svg|15px|Campeón matemático]]"
    assert parser.limpiar(crudo) == "Boca Juniors"


@pytest.mark.parametrize("etiqueta", ["Archivo", "File", "Imagen", "Image"])
def test_los_cuatro_nombres_de_archivo(etiqueta):
    assert parser.limpiar(f"Aldosivi [[{etiqueta}:X.svg|12px|Descendió]]") == "Aldosivi"


def test_un_wikilink_comun_sigue_andando():
    assert parser.limpiar("[[Club Atlético Boca Juniors|Boca Juniors]]") == "Boca Juniors"


def test_una_plantilla_adentro_de_otra_se_pela_entera():
    """UNA PASADA NO ALCANZA CUANDO LAS PLANTILLAS SE ANIDAN.

    `{{ ... }}` sin llaves adentro no puede describir a una plantilla que tiene
    otra adentro: el barrido de una sola pasada se lleva la de ADENTRO y deja la
    de AFUERA entera. Lo que quedaba no era una celda vacia --que se nota-- sino
    una celda con wikitexto crudo, que se publica tal cual.

    El caso real: la fecha 13 del Torneo Federal A 2024, donde la celda del
    estadio dice `Sin disputar` y cuelga un `refn` que adentro tiene otro `refn`.
    La columna `venue` de esa fila salia con la plantilla puesta."""
    crudo = ("Sin disputar{{refn|name=Sansinena1|group=n.|Sansinena fue eliminado "
             "del torneo por deserción.{{refn|name=Sansinena}}}}")
    assert parser.limpiar(crudo) == "Sin disputar"

    # Y tres niveles, para que el test no dependa de que sean exactamente dos.
    assert parser.limpiar("Hermanos Francani{{a|{{b|{{c|x}}}}}}") == "Hermanos Francani"


# --------------------------------------------------------------------------
# el titulo Resultados, en nivel 2 o 3
# --------------------------------------------------------------------------
@pytest.mark.parametrize("titulo", ["== Resultados ==", "=== Resultados ==="])
def test_bug_la_seccion_resultados_puede_ser_de_nivel_2_o_3(titulo):
    """Las temporadas 2016-2024 lo ponen en nivel 2 y las de 2025-26 en nivel 3.
    Pidiendo tres `=` o mas, nueve temporadas devolvian CERO partidos -- que no se
    distingue de "todavia no empezo el torneo"."""
    pagina = f"""
{titulo}
{TABLA}

== Otra cosa ==
"""
    assert len(parser.partidos(pagina, 2026, "X")) == 4


# --------------------------------------------------------------------------
# marcadores
# --------------------------------------------------------------------------
@pytest.mark.parametrize("texto, goles", [
    ("2 - 1", (2, 1)), ("0-0", (0, 0)), ("1:1", (1, 1)), ("10 - 0", (10, 0)),
])
def test_marcador(texto, goles):
    assert parser._marcador(texto) == goles


@pytest.mark.parametrize("texto", ["", "vs", "a jugarse", "- 1", "Susp."])
def test_marcador_sin_partido(texto):
    assert parser._marcador(texto) is None


# --------------------------------------------------------------------------
# la tabla de la fase de grupos
# --------------------------------------------------------------------------
def test_tabla_completa():
    ps = parser.partidos_de_tabla(TABLA, 2026, "Apertura")
    assert len(ps) == 4
    assert all(p.fase == "zonas" for p in ps)


def test_tabla_lee_los_campos():
    union = parser.partidos_de_tabla(TABLA, 2026, "Apertura")[0]
    assert (union.local, union.visita) == ("Unión", "Platense")
    assert (union.goles_local, union.goles_visita) == (0, 0)
    assert union.fecha == "2026-01-23"
    assert union.hora == "20:00"
    assert union.estadio == "15 de Abril"
    assert (union.zona, union.jornada) == ("Zona A", "Fecha 1")


def test_bug_rowspan_no_corre_las_columnas():
    """La 2a fila trae 5 celdas porque hereda la fecha por `rowspan`.

    Un parser que asuma 6 celdas por fila lee el estadio como fecha y la hora
    como estadio, sin fallar. Boca-Instituto es esa fila.
    """
    boca = parser.partidos_de_tabla(TABLA, 2026, "Apertura")[1]
    assert boca.local == "Boca Juniors"
    assert boca.estadio == "La Bombonera"
    assert boca.fecha == "2026-01-23"       # heredada de la fila de arriba
    assert boca.hora == "22:00"


def test_bug_etiqueta_no_se_corre_entre_tablas():
    """El interzonal esta en la Fecha 1, aunque el `!colspan=6|Fecha 2` de la
    tabla siguiente aparezca sin un `|-` que lo separe de su ultima fila.

    Este fue el bug: los 30 interzonales del Apertura 2026 quedaron anotados una
    fecha adelante. Todo lo demas de la fila estaba bien.
    """
    ps = parser.partidos_de_tabla(TABLA, 2026, "Apertura")
    inter = [p for p in ps if p.zona == "Interzonal"]
    assert len(inter) == 1
    assert inter[0].local == "Aldosivi"
    assert inter[0].jornada == "Fecha 1"

    siguiente = [p for p in ps if p.jornada == "Fecha 2"]
    assert [p.local for p in siguiente] == ["Platense"]


TABLA_SIN_HORA = """
{|class="wikitable"
!colspan=5|Fecha 1
|-
!colspan=5|Zona A
|-
!Local
!Resultado
!Visitante
!Estadio
!Fecha
|-
|Boca Juniors
|2 - 1
|Instituto
|La Bombonera
|23 de enero
|}
"""


def test_el_cierre_de_tabla_no_se_cuela_como_dato():
    """El `|}` que cierra la tabla no es una celda.

    En las tablas de hoy sobra siempre, porque la fila tiene las seis columnas y
    el `}` queda de mas. Pero las temporadas viejas se publicaron SIN la columna
    Hora, y ahi ese `}` cae justo en la primera columna que nadie lleno. No
    falla: escribe un partido que se jugo a las `}`.
    """
    p = parser.partidos_de_tabla(TABLA_SIN_HORA, 2026, "Apertura")[0]
    assert p.estadio == "La Bombonera"
    assert p.fecha == "2026-01-23"
    assert p.hora == "", f"se colo el cierre de tabla: {p.hora!r}"


TABLA_ROWSPAN_PASADO = """
{|class="wikitable"
!colspan=6|Fecha 1
|-
!colspan=6|Zona A
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
|Instituto
|La Bombonera
|rowspan=4|23 de enero
|20:00
|-
!colspan=6|Zona B
|-
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Racing Club
|0 - 0
|Tigre
|Cilindro
|26 de enero
|18:00
|}
"""


def test_un_rowspan_no_cruza_de_una_seccion_a_otra():
    """Un `rowspan=4` con dos filas debajo es markup roto, y Wikipedia lo tiene.

    Sin cortar el arrastre en cada encabezado, esa fecha pendiente le gana a la
    celda que la fila siguiente SI trae, y toda la Zona B queda fechada con el
    dia de la Zona A. El marcador y los equipos, bien; solo la fecha, mal.
    """
    ps = parser.partidos_de_tabla(TABLA_ROWSPAN_PASADO, 2026, "Apertura")
    racing = [p for p in ps if p.local == "Racing Club"][0]
    assert racing.fecha == "2026-01-26", "arrastro la fecha de la seccion anterior"
    assert racing.hora == "18:00"


def test_bloque_interzonal_no_hereda_la_zona():
    """"Interzonal" no empieza con "Zona": la primera version del parser no lo
    reconocia como etiqueta y esos partidos heredaban la zona anterior."""
    ps = parser.partidos_de_tabla(TABLA, 2026, "Apertura")
    assert {p.zona for p in ps} == {"Zona A", "Interzonal"}


@pytest.mark.parametrize("crudo", ["Interzonal", "Interzonales", "interzonal"])
def test_interzonal_es_una_sola_etiqueta(crudo):
    """La misma pagina lo escribe en singular y en plural."""
    assert parser._seccion(crudo) == "Interzonal"


def test_encabezados_no_son_partidos():
    """Las filas `!width=21%|Local ...` no tienen que entrar como partido."""
    ps = parser.partidos_de_tabla(TABLA, 2026, "Apertura")
    assert not any(p.local == "Local" for p in ps)


# --------------------------------------------------------------------------
# las llaves: plantillas {{Partido}}
# --------------------------------------------------------------------------
def test_plantillas():
    ps = parser.partidos_de_plantillas(LLAVES, 2026, "Apertura")
    assert len(ps) == 2
    assert all(p.fase == "eliminacion" for p in ps)
    assert ps[0].local == "River Plate"
    assert ps[0].fecha == "2026-05-17"
    assert ps[0].estadio == "Monumental"


def test_bug_los_parentesis_son_el_entretiempo_no_los_penales():
    """EL error a no cometer.

    `|resultado = 2:0''' (1:0)` -- el (1:0) es el ENTRETIEMPO. Los penales tienen
    su propio parametro. Leerlos de los parentesis no falla: inventa tandas de
    penales en partidos que se ganaron en los 90, y despues alguien arma el
    cuadro de eliminacion al reves.
    """
    river, belgrano = parser.partidos_de_plantillas(LLAVES, 2026, "Apertura")

    # este SI fue a penales, y estan en `resultado penalti`
    assert (river.goles_local, river.goles_visita) == (1, 1)
    assert (river.penales_local, river.penales_visita) == (4, 3)

    # este NO: gano 2-0 en los 90, el (1:0) es el entretiempo
    assert (belgrano.goles_local, belgrano.goles_visita) == (2, 0)
    assert belgrano.penales_local is None
    assert belgrano.penales_visita is None


# --------------------------------------------------------------------------
# la pagina entera
# --------------------------------------------------------------------------
def test_pagina_junta_las_dos_fases(pagina):
    ps = parser.partidos(pagina, 2026, "Apertura")
    assert len(ps) == 6
    assert sum(p.fase == "zonas" for p in ps) == 4
    assert sum(p.fase == "eliminacion" for p in ps) == 2


def test_pagina_sin_resultados_no_explota():
    assert parser.partidos("== Nada ==\ntexto suelto\n", 2026, "X") == []


# --------------------------------------------------------------------------
# un titulo corta la jornada
# --------------------------------------------------------------------------
TABLA_CON_DESEMPATE = """
{|class="wikitable"
!colspan=6|Fecha 25
|-
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Aldosivi
|2 - 0
|Sportivo Estudiantes (SL)
|José María Minella
|rowspan=2|30 de abril
|15:35
|-
|Guillermo Brown
|0 - 0
|Almagro
|Raul Conti
|17:00
|}

=== Partido de desempate del primer puesto ===
{|class="wikitable"
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Almagro
|1 - 3
|Aldosivi
|Ciudad de Vicente López
|4 de mayo
|21:00
|}
"""


def test_bug_un_titulo_corta_la_jornada():
    """El desempate por el titulo NO es un partido de la ultima fecha.

    Cuando dos equipos terminan igualados en el primer puesto juegan una final,
    y esa final vive bajo su propio titulo despues de la tabla de la ultima
    jornada. Sin cortar, se quedaba con la etiqueta de arriba: la Fecha 25 de la
    B Nacional 2017-18 terminaba con TRECE partidos y con Aldosivi y Almagro
    jugando dos veces la misma fecha, que es imposible.
    """
    ps = parser.partidos_de_tabla(TABLA_CON_DESEMPATE, 2018, "X")
    assert len(ps) == 3
    de_la_25 = [p for p in ps if p.jornada == "Fecha 25"]
    assert len(de_la_25) == 2, "el desempate se colo en la jornada"
    desempate = [p for p in ps if p.jornada != "Fecha 25"][0]
    assert (desempate.local, desempate.visita) == ("Almagro", "Aldosivi")
    assert desempate.fecha == "2018-05-04"


def test_el_titulo_no_solo_corta_la_jornada_sino_que_dice_cual_es_la_ronda():
    """Cortar la jornada era media solucion. El desempate no es un partido de la
    ultima fecha, pero TAMPOCO es fase regular: es una llave, y quedaba como
    fase de zonas. Se notaba desde afuera -- Aldosivi y Almagro tenian 25 partidos
    donde su tabla les contaba 24 --, y lo agarro el chequeo de PJ.

    El titulo de Wikipedia dentro del cuerpo es una etiqueta de seccion igual que
    un `!colspan|...`, asi que ahora se lee igual."""
    ps = parser.partidos_de_tabla(TABLA_CON_DESEMPATE, 2018, "X")
    desempate = [p for p in ps if p.jornada != "Fecha 25"][0]
    assert desempate.fase == "eliminacion"
    assert desempate.jornada == "Partido de desempate del primer puesto"
    assert desempate.zona == ""
    for p in [p for p in ps if p.jornada == "Fecha 25"]:
        assert p.fase == "zonas", "la fase regular no se tiene que mover"


def test_un_titulo_que_no_nombra_una_ronda_solo_corta():
    """La lista de rondas es corta y explicita a proposito. Un titulo cualquiera
    cierra la jornada y nada mas: convertir en llave a todo lo que tenga titulo
    propio sacaria de la fase de zonas a paginas enteras del ascenso, que cuelgan
    su fase regular de titulos propios."""
    tabla = TABLA_CON_DESEMPATE.replace("=== Partido de desempate del primer puesto ===",
                                        "=== Otra cosa cualquiera ===")
    desempate = [p for p in parser.partidos_de_tabla(tabla, 2018, "X")
                 if p.jornada != "Fecha 25"][0]
    assert desempate.fase == "zonas" and desempate.jornada == ""


def test_el_titulo_tampoco_arrastra_el_rowspan():
    """El `rowspan=2` de la fecha muere con la tabla: el partido de despues tiene
    la suya, y heredarla lo fecharia cuatro dias antes."""
    ps = parser.partidos_de_tabla(TABLA_CON_DESEMPATE, 2018, "X")
    assert [p.fecha for p in ps] == ["2018-04-30", "2018-04-30", "2018-05-04"]


def test_sin_titulo_de_por_medio_la_jornada_sigue():
    """No romper lo de siempre: dentro de una misma tabla la jornada se arrastra
    de fila en fila, que es como funcionan todas las demas paginas."""
    ps = parser.partidos_de_tabla(TABLA, 2026, "Apertura")
    assert [p.jornada for p in ps].count("Fecha 1") == 3


@pytest.mark.parametrize("crudo, limpio", [
    ("Atlético Tucumán¹", "Atlético Tucumán"),      # B Nacional 2008-09
    ("Boca Juniors²", "Boca Juniors"),
    ("River Plate ³", "River Plate"),
])
def test_el_superindice_de_una_nota_no_es_parte_del_nombre(crudo, limpio):
    """Wikipedia marca con un superindice a los equipos que tienen una aclaracion
    al pie. Como cadena, "Atlético Tucumán¹" es otro club: entra al padron como
    desconocido y se lleva un partido del verdadero."""
    assert parser.limpiar(crudo) == limpio


def test_un_numero_pegado_al_final_si_es_parte_del_nombre():
    """Se borran los superindices, no los digitos: hay clubes con numero."""
    assert parser.limpiar("Douglas Haig 9") == "Douglas Haig 9"


@pytest.mark.parametrize("crudo, limpio", [
    ("Unión (Sunchales) <sup>1</sup>", "Unión (Sunchales)"),    # Argentino A 2011-12
    ("Deportivo Merlo<sup>2</sup>", "Deportivo Merlo"),
    ("Cipolletti (*)", "Cipolletti"),                           # Argentino A 2005-06
    ("Gimnasia y Esgrima (CdU) (**)", "Gimnasia y Esgrima (CdU)"),
])
def test_la_llamada_a_una_nota_al_pie_tampoco_es_parte_del_nombre(crudo, limpio):
    """El mismo problema que el superindice unicode, pero escrito en ASCII. El
    barrido general de tags saca el `<sup>` y deja el numero suelto, asi que el
    club terminaba llamandose "Unión (Sunchales) 1" y quedaba fuera del padron:
    diez de los 44 nombres que la tabla tenia sin arbitro eran esto."""
    assert parser.limpiar(crudo) == limpio


def test_una_celda_que_es_solo_el_marcador_no_queda_vacia():
    """El asterisco se saca si queda nombre atras. Vaciar una celda es peor que
    dejarla rara: `dataset` no puede avisar de lo que no existe."""
    assert parser.limpiar("(*)") == "(*)"


# --------------------------------------------------------------------------
# donde termina una {{Partido}}
# --------------------------------------------------------------------------
def _plantilla(local, visita, resultado, cierre="\n}}", pen=""):
    """Una plantilla como las escribe Wikipedia. `cierre` es lo que la termina."""
    penal = f"\n|resultado penalti = {pen}" if pen else ""
    return (f"{{{{Partido\n|local = {local}\n|resultado = {resultado}"
            f"\n|visita = {visita}\n|fecha = 12 de diciembre, 17:00{penal}"
            f"\n|árbitro=[[Alguien]]{cierre}")


def test_una_plantilla_que_cierra_pegada_al_ultimo_parametro():
    """`|árbitro=[[Fulano]]}}` es la forma mas comun en es.wikipedia. Pidiendo
    que el `}}` este solo en su renglon, esta plantilla no cerraba nunca."""
    ps = parser.partidos_de_plantillas(
        _plantilla("Boca Juniors", "River Plate", "2:1", cierre="}}"), 2021, "x")
    assert len(ps) == 1
    assert (ps[0].local, ps[0].goles_local, ps[0].goles_visita) == ("Boca Juniors", 2, 1)


def test_una_plantilla_que_cierra_asi_no_se_come_a_la_siguiente():
    """El bug que dejo afuera a la Primera B 2021. Cuando la primera no cierra
    donde el regex espera, el `.*?` sigue hasta el proximo `}}` que si este solo
    y se traga las del medio. Como los campos van a un dict, el ultimo `local`
    pisa al primero y el `resultado penalti` del primero sobrevive pegado al
    marcador del ultimo: un partido que nunca se jugo, con todo lleno."""
    texto = (_plantilla("Racing Club", "Huracán", "1:1", cierre="}}", pen="4:2")
             + "\n\n" + _plantilla("Boca Juniors", "River Plate", "2:4", cierre="}}"))
    ps = parser.partidos_de_plantillas(texto, 2021, "x")
    assert len(ps) == 2, "se comio una"
    assert [(p.local, p.visita) for p in ps] == [
        ("Racing Club", "Huracán"), ("Boca Juniors", "River Plate")]
    assert (ps[0].penales_local, ps[0].penales_visita) == (4, 2)
    assert ps[1].penales_local is None, "los penales del primero se pegaron al segundo"


def test_la_plantilla_en_plural_es_la_misma():
    """`{{Partidos}}` es `#REDIRECCION [[Plantilla:Partido]]`: misma plantilla,
    mismos parametros. Pidiendo el singular la `s` no matchea -- no es
    whitespace -- y no se veia: 27 paginas del catalogo y 284 partidos de
    eliminacion se caian en silencio, la mayoria con la fase ENTERA afuera."""
    texto = _plantilla("Boca Juniors", "River Plate", "2:1").replace("{{Partido", "{{Partidos")
    ps = parser.partidos_de_plantillas(texto, 2021, "x")
    assert len(ps) == 1 and ps[0].local == "Boca Juniors"


def test_una_plantilla_adentro_no_corta_el_partido():
    """El cuerpo trae `{{sin negrita|(0:0)}}` y `{{gol|43}}`. Frenando en el
    primer `}}` el partido queda sin visitante."""
    texto = _plantilla("Boca Juniors", "River Plate", "1:1 {{sin negrita|(0:0)}}")
    ps = parser.partidos_de_plantillas(texto, 2021, "x")
    assert len(ps) == 1 and ps[0].visita == "River Plate"


def test_una_plantilla_sin_cerrar_se_descarta():
    """Adivinar donde termina es exactamente lo que hacia el regex."""
    texto = "{{Partido\n|local = Boca Juniors\n|resultado = 2:1\n|visita = River Plate\n"
    assert parser.partidos_de_plantillas(texto, 2021, "x") == []


# --------------------------------------------------------------------------
# una ronda no es una zona
# --------------------------------------------------------------------------
def _tabla_con(encabezado, local="Boca Juniors", visita="River Plate"):
    return f"""
== Resultados ==
{{|class="wikitable"
!colspan=6|{encabezado}
|-
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|{local}
|2 - 1
|{visita}
|Un Estadio
|23 de enero
|20:00
|}}
"""


def test_una_fecha_del_calendario_va_a_la_jornada():
    p, = parser.partidos(_tabla_con("Fecha 7"), 2018, "x")
    assert (p.fase, p.zona, p.jornada) == ("zonas", "", "Fecha 7")


def test_una_zona_va_a_la_zona():
    p, = parser.partidos(_tabla_con("Zona A"), 2018, "x")
    assert (p.fase, p.zona) == ("zonas", "Zona A")


@pytest.mark.parametrize("ronda", [
    "Desempate", "Octavos de final", "Cuartos", "Semifinales", "Final",
    "Ronda de desempate", "Partidos de ida", "Primera ronda", "Reducido"])
def test_una_ronda_no_es_una_zona(ronda):
    """La tabla de una fecha y la de una llave se escriben igual; el encabezado
    es lo unico que las distingue. Tratando la ronda como zona pasan dos cosas:
    la etiqueta va a parar a la columna `group` del CSV, que promete una zona y
    dice "Octavos de final", y el partido queda como fase de grupos. Eso ultimo
    dejo a la Primera B 2017-18 entera afuera del dataset: 306 partidos sin zona
    y uno -- el desempate que definio el campeonato -- con "Desempate"."""
    p, = parser.partidos(_tabla_con(ronda), 2018, "x")
    assert p.zona == "", f"{ronda!r} quedo como zona"
    assert p.fase == "eliminacion"
    assert p.jornada == ronda


def test_una_fase_de_grupos_del_federal_sigue_siendo_zona():
    """La lista de rondas es corta a proposito. En el Federal A, "Primera fase" y
    "Nonagonal final" son fases de GRUPOS: meterlas las sacaria de donde van."""
    for etiqueta in ("Primera fase", "Nonagonal final"):
        p, = parser.partidos(_tabla_con(etiqueta), 2018, "x")
        assert p.fase == "zonas", f"{etiqueta!r} se fue a eliminacion"


# --------------------------------------------------------------------------
# la pata no es la ronda
# --------------------------------------------------------------------------
def _patas(ida="Partidos de ida", vuelta="Partidos de vuelta", arriba=""):
    """Una serie en una tabla que rotula la pata: Boca-River a la ida, River-Boca a
    la vuelta. `arriba` va antes del primer encabezado."""
    cols = "!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n"
    return ('{|class="wikitable"\n' + arriba
            + f"!colspan=6|{ida}\n|-\n{cols}"
            + "|-\n|Boca Juniors\n|2 - 1\n|River Plate\n|Un Estadio\n|23 de enero\n|20:00\n"
            + f"|-\n!colspan=6|{vuelta}\n|-\n{cols}"
            + "|-\n|River Plate\n|1 - 0\n|Boca Juniors\n|Otro Estadio\n|30 de enero\n|20:00\n|}\n")


def _rondas_de(texto):
    return [(p.fase, p.zona, p.jornada) for p in parser.partidos(texto, 2014, "x")]


def test_la_pata_se_lleva_la_ronda_del_titulo():
    """Como lo escribe el Federal A 2014: la fase en el titulo y la pata en el
    encabezado. El encabezado la pisaba y las tres fases quedaban con los mismos dos
    rotulos, que `cadena_de_llaves` no podia separar. El titulo de al lado
    (`Tabla de ordenamiento`) no contiene a los resultados y no cuenta."""
    texto = ("== Segunda a cuarta fase ==\n=== Segunda fase ===\n"
             "==== Tabla de ordenamiento ====\nLos dieciseis.\n"
             "==== Resultados ====\n" + _patas())
    assert _rondas_de(texto) == [("eliminacion", "", "Segunda fase")] * 2


def test_la_pata_saltea_los_titulos_de_relleno():
    """El Federal A 2024 cuelga los resultados de `Enfrentamientos`, que no nombra
    nada: la ronda es el titulo de arriba."""
    texto = ("== Reválida ==\n=== Segunda etapa ===\n==== Enfrentamientos ====\n"
             "===== Resultados =====\n" + _patas())
    assert _rondas_de(texto) == [("eliminacion", "", "Segunda etapa")] * 2


def test_la_pata_se_lleva_una_ronda_que_no_sirve_de_zona():
    """`Octavos de final` no es una zona y `_como_zona` lo vacia, pero como ronda es
    lo que hace falta. Sin el, quedaba la fase entera: `Etapa Eliminatoria`."""
    texto = ("== Etapa Eliminatoria ==\n=== Octavos de final ===\n"
             "==== Resultados ====\n" + _patas())
    assert _rondas_de(texto) == [("eliminacion", "", "Octavos de final")] * 2


def test_la_pata_se_lleva_la_ronda_del_encabezado_de_arriba():
    """El reducido de la Primera B 2011-12 no tiene titulo por ronda: pone la ronda
    en un encabezado y debajo, en la misma tabla, la pata."""
    texto = "== Torneo reducido ==\n" + _patas(arriba="!colspan=6|Semifinales\n|-\n")
    assert _rondas_de(texto) == [("eliminacion", "", "Semifinales")] * 2


def test_la_pata_de_una_tabla_suelta_se_lleva_su_titulo():
    """La sexta fase del Argentino A 2013-14 no tiene `Resultados`: la tabla cuelga
    del titulo de la fase, y la lee el camino de las tablas sueltas."""
    texto = ("== Tercera a sexta fase ==\n=== Sexta fase ===\n"
             + _patas("Partido de ida", "Partido de vuelta"))
    assert _rondas_de(texto) == [("eliminacion", "", "Sexta fase")] * 2


def test_un_titulo_corta_la_ronda_del_encabezado():
    """Lo que dijo un encabezado vale hasta el proximo titulo, igual que la jornada:
    la pata que viene despues de `Revancha` es de la `Final`, no del `Desempate`."""
    cols = "!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n"
    texto = ("== Final ==\n==== Resultados ====\n"
             '{|class="wikitable"\n!colspan=6|Desempate\n|-\n' + cols
             + "|-\n|Racing Club\n|1 - 0\n|Huracán\n|Cancha\n|16 de enero\n|20:00\n|}\n"
             + "===== Revancha =====\n" + _patas())
    rondas = {p.local: p.jornada for p in parser.partidos(texto, 2014, "x")}
    assert rondas == {"Racing Club": "Desempate", "Boca Juniors": "Final",
                      "River Plate": "Final"}


def test_la_pata_no_se_lleva_el_titulo_hermano():
    """Como lo escribe el Federal A 2024: `Tabla de ordenamiento` y `Enfrentamientos`
    son hermanos y los resultados cuelgan del segundo, un nivel mas abajo. El
    hermano de al lado no contiene a los resultados: sin sacarlo de la ruta, las 62
    filas de la Revalida de 2024 y 2025 salian `Tabla de ordenamiento`."""
    texto = ("== Reválida ==\n=== Segunda etapa ===\n==== Tabla de ordenamiento ====\n"
             "Los dieciseis.\n==== Enfrentamientos ====\nLas llaves.\n"
             "===== Resultados =====\n" + _patas())
    assert _rondas_de(texto) == [("eliminacion", "", "Segunda etapa")] * 2


def test_la_final_saltea_el_enfrentamiento_en_singular():
    """La ultima etapa de la Revalida es una serie sola, y su titulo de relleno va en
    singular: `==== Enfrentamiento ====`. Asi las finales del Federal A 2024 y 2025."""
    texto = ("== Reválida ==\n=== Sexta etapa ===\n==== Tabla de ordenamiento ====\n"
             "Los dos.\n==== Enfrentamiento ====\nLa llave.\n===== Resultados =====\n"
             + _patas("Partido de ida", "Partido de vuelta"))
    assert _rondas_de(texto) == [("eliminacion", "", "Sexta etapa")] * 2


def test_la_pata_saltea_un_titulo_que_solo_dice_partidos():
    """`=== Partidos ===` es relleno igual que `Resultados`: la tabla suelta de una
    final colgada de ahi es de la `Final`, no de los `Partidos`."""
    texto = ("== Final ==\n=== Partidos ===\n"
             + _patas("Partido de ida", "Partido de vuelta"))
    assert _rondas_de(texto) == [("eliminacion", "", "Final")] * 2


def test_un_encabezado_que_dice_mas_que_la_pata_no_se_pisa():
    """Solo la pata a secas se cambia por la ronda. `Partido de ida de la final` ya
    dice la ronda, y la seccion de arriba (`Torneo reducido`) dice menos: queda como
    lo escribe la pagina."""
    texto = "== Torneo reducido ==\n" + _patas("Partido de ida de la final",
                                               "Partido de vuelta de la final")
    assert [j for _, _, j in _rondas_de(texto)] == [
        "Partido de ida de la final", "Partido de vuelta de la final"]


def test_un_titulo_de_ronda_adentro_de_los_resultados_vale_para_su_pata():
    """Dos rondas como titulos ADENTRO del `Resultados`, cada una con su tabla que
    rotula solo la pata. Cada pata es de la ronda de su titulo, no de la seccion de
    afuera: con la ronda del titulo sin recordar, las cuatro salian `Fase final`."""
    texto = ("== Fase final ==\n==== Resultados ====\n===== Cuartos de final =====\n"
             + _patas() + "===== Semifinales =====\n"
             + _patas().replace("Boca Juniors", "Racing Club").replace("River Plate", "Huracán"))
    rondas = {p.local: p.jornada for p in parser.partidos(texto, 2014, "x")}
    assert rondas == {"Boca Juniors": "Cuartos de final", "River Plate": "Cuartos de final",
                      "Racing Club": "Semifinales", "Huracán": "Semifinales"}


def test_un_titulo_que_nombra_solo_la_pata_no_es_la_ronda():
    """Un titulo `Partidos de ida` no le deja la pata como ronda a la tabla de abajo:
    la tabla que repite la pata en su encabezado se lleva la de la seccion."""
    texto = ("== Final ==\n==== Resultados ====\n===== Partidos de ida =====\n"
             + _patas())
    assert _rondas_de(texto) == [("eliminacion", "", "Final")] * 2


# --------------------------------------------------------------------------
# tablas que no cuelgan de un "Resultados"
# --------------------------------------------------------------------------
def test_una_tabla_fuera_de_resultados_se_lee():
    """Los reducidos, las promociones y las finales de ascenso viven bajo titulos
    propios, asi que la busqueda por seccion nunca se las pasaba al parser y se
    perdian enteras aunque tuvieran fecha y estadio."""
    texto = _tabla_con("Fecha 1") + """
== Final por el primer ascenso ==
{|class="wikitable"
!colspan=6|Partido 1
|-
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Racing Club
|1 - 0
|Huracán
|Otro Estadio
|22 de junio
|19:00
|}
"""
    ps = parser.partidos(texto, 2018, "x")
    assert len(ps) == 2
    final = [p for p in ps if p.local == "Racing Club"][0]
    assert final.fecha == "2018-06-22" and final.estadio == "Otro Estadio"
    assert final.fase == "eliminacion", "afuera de la liga no hay fechas del calendario"
    assert final.zona == "", "'Partido 1' no es una zona"


def test_una_lista_de_goleadores_no_es_una_tabla_de_partidos():
    """La guarda que hace seguro leer fuera de la seccion. Corriendo el parser
    sobre la pagina entera se miden 34 paginas alteradas y 117 filas nuevas, y
    una es un partido que NO existe: la caja de detalle trae
    `44'|| Elías Torres|| 2 - 0` y el encabezado de las tarjetas dice
    `Amonestaciones`, asi que salia un `Talleres 2-1 Rafaela` inventado."""
    texto = _tabla_con("Fecha 1") + """
== Detalle ==
{|class="wikitable"
!colspan=3|Amonestaciones
|-
!Minuto
!Jugador
!Parcial
|-
|44'
|Elías Torres
|2 - 0
|}
"""
    assert len(parser.partidos(texto, 2018, "x")) == 1


def test_un_partido_publicado_dos_veces_entra_una():
    """La final suele estar en la ultima fecha de los resultados Y en su seccion
    propia. Entrando por las dos, `validar.sin_duplicados` frena el build."""
    texto = _tabla_con("Fecha 19", local="Racing Club", visita="Huracán") + """
== Final ==
{|class="wikitable"
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Racing Club
|2 - 1
|Huracán
|Un Estadio
|23 de enero
|20:00
|}
"""
    ps = parser.partidos(texto, 2018, "x")
    assert len(ps) == 1


def test_una_tabla_adentro_de_otra_no_corta_la_de_afuera():
    """Las paginas del ascenso arman dos columnas de resultados con un
    `{| width=100%` que envuelve a las tablas de cada fecha. Buscando el `|}`
    mas cercano, la de afuera se cierra en el primer cierre de una de adentro y
    la mitad de los partidos queda fuera de la tabla."""
    texto = """
== Final por el primer ascenso ==
{| width=100%
| valign=top width=50% |
{|class="wikitable"
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Racing Club
|1 - 0
|Huracán
|Un Estadio
|22 de junio
|19:00
|}
| valign=top width=50% |
{|class="wikitable"
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Huracán
|2 - 2
|Racing Club
|Otro Estadio
|29 de junio
|19:00
|}
|}
"""
    ps = parser.partidos(texto, 2018, "x")
    assert len(ps) == 2, "se perdio la tabla de la segunda columna"


def test_el_titulo_de_una_tabla_de_posiciones_no_es_una_zona():
    """Varias paginas ponen el calendario DEBAJO de la tabla, asi que el
    `===== Resultados =====` cuelga de `==== Tabla de posiciones ====` y ese
    nombre terminaba en la columna `group` del CSV. Eran 44 filas."""
    for titulo in ("Tabla de posiciones", "Tabla de posiciones final", "Tabla de promedios"):
        assert parser._como_zona(titulo) == "", f"{titulo!r} quedo como zona"
    assert parser._como_zona("Nonagonal final") == "Nonagonal final", (
        "'Nonagonal final' SI es una zona: nueve equipos todos contra todos")


def test_una_seccion_bajo_etapa_eliminatoria_es_una_llave():
    """El mismo rotulo significa cosas distintas segun donde este. "Primera fase"
    es una fase de grupos en el Federal A 2017 -- con sus Fecha 1, Fecha 2 -- y
    una llave en el Transicion 2020, donde es hermana de "Semifinales" y "Final"
    bajo `== Etapa eliminatoria ==`. El nombre no distingue; el lugar si."""
    texto = """
== Etapa eliminatoria ==
=== Primera fase ===
==== Resultados ====
{|class="wikitable"
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
|23 de enero
|20:00
|}
"""
    p, = parser.partidos(texto, 2021, "x")
    assert p.fase == "eliminacion" and p.zona == "" and p.jornada == "Primera fase"


def test_una_fase_de_grupos_con_el_mismo_nombre_sigue_siendo_zona():
    texto = """
== Etapa clasificatoria ==
=== Primera fase ===
==== Resultados ====
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
|23 de enero
|20:00
|}
"""
    p, = parser.partidos(texto, 2021, "x")
    assert p.fase == "zonas" and p.jornada == "Fecha 1"


# --------------------------------------------------------------------------
# cancha neutral: la pagina lo dice rotulando la columna
# --------------------------------------------------------------------------
def _tabla(rotulo, **kw):
    return (f'{{|class="wikitable"\n'
            f'|-\n!width="150"|{rotulo}\n!Resultado\n!{"Equipo 2" if rotulo != "Local" else "Visitante"}\n'
            f'!Estadio\n!Fecha\n!Hora\n'
            f'|-\n|Huracán\n|4 - 1\n|Atlético Tucumán\n|Malvinas Argentinas\n'
            f'|14 de diciembre\n|17:15\n|}}')


def _pagina_con_zonas(rotulo="Fecha 1"):
    """Una fase con dos zonas y una tabla de partidos en cada una, SIN una seccion
    `Resultados` -- que es como estan escritos los `Torneo Argentino A` de 2011-12 y
    2012-13, y por eso caen en el camino de respaldo."""
    def bloque(local, visita):
        return ('{|class="wikitable"\n'
                f'|-\n!colspan=6|{rotulo}\n'
                '|-\n!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n'
                f'|-\n|{local}\n|2 - 1\n|{visita}\n|Cancha\n|14 de diciembre\n|17:15\n|}}')
    return ("== Primera fase ==\n"
            "=== Zona Norte ===\n" + bloque("Talleres (C)", "Racing (C)") + "\n"
            "=== Zona Sur ===\n" + bloque("Cipolletti", "Douglas Haig") + "\n")


def test_la_tabla_QUE_NO_CUELGA_DE_RESULTADOS_igual_tiene_su_zona():
    """El camino de respaldo --el que lee las tablas que no cuelgan de un
    `Resultados`-- pedia la LLAVE, que es el titulo de nivel 2 que las contiene, y no
    pedia la ZONA, que es el de nivel 3. El otro camino si la pedia.

    No es un matiz de dos paginas: la zona viaja a la columna `group` del CSV, asi que
    esas filas se publicaban sin un dato que la fuente tiene escrito. Son 673 entre el
    Argentino A 2011-12 y el 2012-13.
    """
    ps = parser.partidos(_pagina_con_zonas(), 2012, "Argentino A")
    assert {p.zona for p in ps} == {"Zona Norte", "Zona Sur"}
    assert {p.llave for p in ps} == {"Primera fase"}


def test_y_la_zona_no_se_inventa_cuando_el_titulo_no_es_una():
    """`_como_zona` vacia los titulos que nombran una RONDA. Sin eso, una tabla
    colgada de `=== Semifinales ===` saldria con la zona "Semifinales", que promete un
    grupo que no existe."""
    pagina = _pagina_con_zonas().replace("=== Zona Norte ===", "=== Semifinales ===")
    ps = parser.partidos(pagina, 2012, "Argentino A")
    assert {p.zona for p in ps} == {"", "Zona Sur"}


def _pagina_de_dos_zonas():
    """Una seccion `Resultados` con las zonas ADENTRO, que es como la escribe el
    Argentino A 2005-06: `==== Resultados ====` y colgando de el
    `===== Zona Sur =====` y `===== Zona Norte =====`."""
    def bloque(local, visita):
        return ('{|class="wikitable"\n'
                '|-\n!colspan=6|Fecha 1\n'
                '|-\n!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n'
                f'|-\n|{local}\n|2 - 1\n|{visita}\n|Cancha\n'
                '|14 de diciembre\n|17:15\n|}')
    return ("== Torneo Apertura ==\n=== Primera fase ===\n==== Resultados ====\n"
            "===== Zona Sur =====\n" + bloque("Cipolletti", "Douglas Haig") + "\n"
            "===== Zona Norte =====\n" + bloque("Talleres (C)", "Racing (C)") + "\n")


def test_la_seccion_QUE_TRAE_SUS_ZONAS_ADENTRO_se_parte():
    """El Argentino A 2005-06 cuelga las dos zonas ADENTRO del `Resultados`. Sin
    partirla llegan al lector en un solo cuerpo con una sola etiqueta, y sus 263
    partidos salian con la del padre --`Primera fase`--, que no es una zona sino una
    fase. Peor que quedar vacia: una zona equivocada parece un dato."""
    ps = parser.partidos(_pagina_de_dos_zonas(), 2005, "Argentino A")
    assert {p.zona for p in ps} == {"Zona Sur", "Zona Norte"}


def test_pero_NO_se_parte_por_un_subtitulo_que_no_es_una_zona():
    """Partir por cualquier subtitulo mueve 13 781 filas del corpus, medido: hay
    paginas que cuelgan del `Resultados` una `Primera rueda` y una `Segunda rueda`,
    que son mitades de la temporada y no zonas. La regla se estrecha a lo que se puede
    defender: se parte cuando ALGUNA subseccion se llama como una zona."""
    pagina = (_pagina_de_dos_zonas().replace("===== Zona Sur =====", "===== Primera rueda =====")
              .replace("===== Zona Norte =====", "===== Segunda rueda ====="))
    ps = parser.partidos(pagina, 2005, "Argentino A")
    assert {p.zona for p in ps} == {"Primera fase"}, "queda la etiqueta de afuera"


def test_y_la_que_no_es_zona_conserva_la_etiqueta_de_afuera():
    """Cuando conviven las dos, la que no nombra una zona no se queda con su propio
    titulo: no se sabe que zona es, y escribirlo en `group` seria inventarlo."""
    pagina = _pagina_de_dos_zonas().replace("===== Zona Norte =====", "===== Desempate =====")
    ps = parser.partidos(pagina, 2005, "Argentino A")
    assert {p.zona for p in ps} == {"Zona Sur", "Primera fase"}


def test_no_partir_TAMBIEN_protege_a_la_ronda_que_cuelga_de_la_seccion():
    """La guarda no es solo cosmetica. Partir por cualquier subtitulo cambia que texto
    ve `_rotula_fechas`, y con eso se da vuelta `fuera_de_la_liga`: el
    `Partido de desempate del primer puesto` de la B Nacional 2017-18 y el de la
    2018-19 se mudaban de `eliminacion` a `zonas` y perdian su jornada entera.

    Medido: sin la guarda son dos filas mas del corpus, y las dos empeoran."""
    tabla = ('{|class="wikitable"\n'
             '|-\n!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n'
             '|-\n|Talleres (C)\n|2 - 1\n|Racing (C)\n|Cancha\n'
             '|14 de diciembre\n|17:15\n|}')
    con_fecha = tabla.replace('|-\n!Local', '|-\n!colspan=6|Fecha 1\n|-\n!Local')
    pagina = ("== Resultados ==\n" + con_fecha + "\n"
              "=== Partido de desempate del primer puesto ===\n" + tabla + "\n")
    ps = parser.partidos(pagina, 2018, "Primera Nacional")
    desempate = [p for p in ps if p.fase == "eliminacion"]
    assert len(desempate) == 1, "el desempate sigue siendo una llave"
    assert desempate[0].jornada == "Partido de desempate del primer puesto"


def test_el_corte_va_por_el_nivel_MAS_ALTO_que_aparezca():
    """Una subseccion con sub-subsecciones entra ENTERA. Cortando por cualquier nivel,
    la `Ficha` que cuelga del desempate lo parte al medio y la segunda mitad se queda
    con la etiqueta de la ficha, que no es ni una zona ni una ronda.

    Es el mismo criterio que usa `_secciones_con_span` un nivel mas arriba."""
    tabla = ('{|class="wikitable"\n'
             '|-\n!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n'
             '|-\n|Talleres (C)\n|2 - 1\n|Racing (C)\n|Cancha\n'
             '|14 de diciembre\n|17:15\n|}')
    pagina = ("== Resultados ==\n"
              "=== Zona Sur ===\n" + tabla + "\n"
              "==== Ficha ====\n" + tabla.replace("Talleres (C)", "Cipolletti") + "\n")
    ps = parser.partidos(pagina, 2018, "Primera Nacional")
    assert {p.zona for p in ps} == {"Zona Sur"}, (
        "la sub-subseccion entra en su zona, no se lleva una etiqueta propia")


def test_a_la_tabla_de_ELIMINACION_no_se_le_pasa_la_zona():
    """`partidos_de_tabla` REUSA `zona_defecto` como nombre de la ronda cuando la
    tabla esta fuera de la liga -- a proposito, y el otro llamador depende de eso --,
    asi que pasarsela ahi no llena la zona: le pisa la jornada.

    El playoff de descenso del Federal A 2024 pasaba de `Régimen de descenso` a
    `Zona B`, que es el titulo de su subseccion y no la ronda. Lo agarro el build y no
    el arnes de equivalencia, porque el arnes miraba fase, llave y zona y NO la
    jornada: una magnitud que no se captura no se protege."""
    tabla = ('{|class="wikitable"\n'
             '|-\n!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n'
             '|-\n|Talleres (C)\n|2 - 1\n|Racing (C)\n|Cancha\n'
             '|14 de diciembre\n|17:15\n|}')
    pagina = "== Régimen de descenso ==\n=== Zona B ===\n" + tabla + "\n"
    ps = parser.partidos(pagina, 2024, "Federal A")
    assert len(ps) == 1
    assert ps[0].jornada == "Régimen de descenso", "la ronda no la nombra su subseccion"
    assert ps[0].zona == ""


def test_una_tabla_sin_local_marca_el_partido_neutral():
    """Cuando no hay local, la tabla rotula "Equipo 1 / Equipo 2" en vez de
    "Local / Visitante". No es una interpretacion nuestra: es la unica forma que
    tiene una tabla de decir que los dos son visitantes, y la usa siempre para lo
    mismo -- desempates, reducidos y definiciones, en cancha de un tercero.

    El testigo es el Desempate por el ascenso de 2014: Huracan 4-1 Atletico
    Tucuman en el Malvinas Argentinas de Mendoza, que no es de ninguno."""
    ps = parser.partidos_de_tabla(_tabla("Equipo 1"), 2014, "Primera Nacional")
    assert len(ps) == 1 and ps[0].neutral is True


def test_una_tabla_con_local_no_opina():
    """`None` y no `False`: la tabla no esta diciendo que la cancha NO sea
    neutral, solo esta rotulando su columna. Quien decide entonces es el torneo,
    que es el que sabe si es una liga o una copa."""
    ps = parser.partidos_de_tabla(_tabla("Local"), 2014, "Primera Nacional")
    assert len(ps) == 1 and ps[0].neutral is None


def test_el_rotulo_vale_por_tabla_y_no_por_pagina():
    """Un bloque puede traer la fecha 38 con "Local" y abajo el desempate con
    "Equipo 1". Si el rotulo se leyera una vez por bloque, o se perderia el
    desempate o se marcaria neutral media temporada."""
    ida = parser.partidos_de_tabla(_tabla("Local") + "\n" + _tabla("Equipo 1"),
                                   2014, "Primera Nacional")
    assert [p.neutral for p in ida] == [None, True]
    # Y sobre todo AL REVES, que es el orden que discrimina: si el rotulo no se
    # RESETEA al ver "Local", el desempate de arriba deja marcada como neutral a
    # la tabla de abajo, que no lo es. En el otro orden el bug no se ve, porque
    # `sin_local` ya arranca en False.
    vuelta = parser.partidos_de_tabla(_tabla("Equipo 1") + "\n" + _tabla("Local"),
                                      2014, "Primera Nacional")
    assert [p.neutral for p in vuelta] == [True, None]


# --------------------------------------------------------------------------
# el mismo rotulo de zona en dos fases distintas
# --------------------------------------------------------------------------
def _fase(titulo, zona, local, visita):
    return (f"== {titulo} ==\n=== Resultados ===\n"
            f'{{|class="wikitable"\n'
            f'!colspan="6"|Fecha 1\n|-\n!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n'
            f'|-\n!colspan="6"|{zona}\n'
            f'|-\n|{local}\n|1 - 0\n|{visita}\n|Cancha\n|1 de marzo\n|17:00\n|}}\n')


def test_una_zona_reusada_en_dos_fases_se_califica():
    """Un torneo multifase puede llamar "Zona 1" a dos cosas distintas: la de la
    Primera fase y la del Reducido, con otros equipos. El rotulo sale de un
    encabezado de la tabla, que no sabe de que seccion cuelga, asi que los
    partidos de las dos caian en el mismo balde -- el Argentino A 2010-11 quedaba
    con 132 partidos en su Zona 1 cuando son 112 mas 20."""
    texto = (_fase("Primera fase", "Zona 1", "Boca Juniors", "River Plate")
             + _fase("Revélida", "Zona 1", "Platense", "Banfield"))
    zonas = {p.zona for p in parser.partidos(texto, 2010, "Primera Division")}
    assert zonas == {"Primera fase - Zona 1", "Revélida - Zona 1"}


def test_una_zona_que_no_se_repite_queda_como_esta():
    """La calificacion es CONDICIONAL. Ponerle la fase a toda zona cambiaria el
    `group` de las 38109 filas del dataset para arreglar tres paginas que ni
    siquiera estan en el catalogo."""
    texto = (_fase("Primera fase", "Zona 1", "Boca Juniors", "River Plate")
             + _fase("Revélida", "Zona 2", "Platense", "Banfield"))
    zonas = {p.zona for p in parser.partidos(texto, 2010, "Primera Division")}
    assert zonas == {"Zona 1", "Zona 2"}


def test_una_jornada_repetida_entre_fases_no_es_una_zona_ambigua():
    """"Fecha 1" esta en TODAS las fases de casi todos los torneos, y no es una
    zona: la rama de la jornada corre antes. Contandola, 34 paginas del catalogo
    parecian tener el problema y ninguna lo tiene."""
    texto = (_fase("Primera fase", "Zona 1", "Boca Juniors", "River Plate")
             + _fase("Revélida", "Zona 2", "Platense", "Banfield"))
    assert parser._zonas_ambiguas(texto) == frozenset()


def test_una_celda_vacia_no_corre_las_columnas():
    """La posicion ES el dato. Si se descarta una celda vacia, todas las columnas
    que vienen despues se corren un lugar, y el resultado no es un hueco sino un
    valor equivocado en la columna de al lado.

    Es la forma exacta del Argentino A 2010-11: de la Fecha 18 en adelante la
    pagina deja el estadio en blanco y pone la fecha con `rowspan`. Con la celda
    vacia descartada, la fecha caia en `estadio` -- 373 partidos salian sin fecha
    y con `venue = "2 de febrero"`. El diagnostico que habia en el catalogo decia
    "no es el parser, la fuente no la trae", y era el parser."""
    tabla = ("{|class=\"wikitable\"\n"
             "!colspan=6|Fecha 20\n"
             "|-\n"
             "!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n"
             "|-align=center\n"
             "|Villa Mitre\n|1 - 2\n|Huracán (TA)\n|\n|rowspan=2|2 de febrero\n|\n"
             "|-align=center\n"
             "|Cipolletti\n|2 - 2\n|Unión (S)\n|\n|\n"
             "|}\n")
    ps = parser.partidos(tabla, 2010, "Prueba", anio_fin=2011)
    assert len(ps) == 2
    assert [p.fecha for p in ps] == ["2011-02-02", "2011-02-02"]
    assert [p.estadio for p in ps] == ["", ""], "la fecha se corrio a la cancha"


def test_el_rowspan_de_la_fecha_alcanza_a_las_filas_de_abajo():
    """Con estadio presente, que es el caso que ya andaba. Va como testigo de que
    el arreglo de las celdas vacias no rompio el camino feliz."""
    tabla = ("{|class=\"wikitable\"\n"
             "!colspan=6|Fecha 1\n"
             "|-\n"
             "!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n"
             "|-align=center\n"
             "|Unión (MdP)\n|2 - 0\n|Villa Mitre\n|José María Minella\n"
             "|rowspan=2|22 de agosto\n|11:00\n"
             "|-align=center\n"
             "|Rivadavia (L)\n|1 - 1\n|Cipolletti\n|Municipal\n|15:30\n"
             "|}\n")
    ps = parser.partidos(tabla, 2010, "Prueba", anio_fin=2011)
    assert [p.fecha for p in ps] == ["2010-08-22", "2010-08-22"]
    assert [p.estadio for p in ps] == ["José María Minella", "Municipal"]
    assert [p.hora for p in ps] == ["11:00", "15:30"]


def test_una_fase_regular_bajo_titulo_propio_no_es_eliminacion():
    """La fase de grupos no siempre cuelga de un `=== Resultados ===`. El Torneo
    Argentino A 2011-12 y el 2012-13 la ponen bajo `== Primera fase ==` con una
    subseccion por zona, y esas tablas caen al camino de respaldo -- el que
    recoge reducidos y promociones, y que daba `fase="eliminacion"` a todo.

    El sintoma no era que faltaran partidos: estaban los 385, con su "Fecha 1" y
    su marcador. Era que `posiciones.sumar` solo cuenta la fase de zonas, asi que
    la pagina tenia sus tablas leidas y CERO partidos con que cruzarlas. Tenia
    arbitro y grilla, y no se hablaban."""
    texto = ("== Primera fase ==\n=== Zona Norte ===\n"
             "{|class=\"wikitable\"\n"
             "!colspan=6|Fecha 1\n"
             "|-\n!Local\n!Resultado\n!Visitante\n"
             "|-\n|Boca Juniors\n|2 - 1\n|River Plate\n"
             "|}\n")
    ps = parser.partidos(texto, 2011, "Prueba", anio_fin=2012)
    assert len(ps) == 1
    assert ps[0].fase == "zonas", "una tabla que rotula 'Fecha N' es fase regular"
    assert ps[0].jornada == "Fecha 1"


def test_una_tabla_de_reducido_bajo_titulo_propio_sigue_siendo_eliminacion():
    """El reciproco, que es lo que el camino de respaldo vino a resolver: sin
    rotulos de fecha, la tabla es una llave y no una fase."""
    texto = ("== Torneo reducido ==\n"
             "{|class=\"wikitable\"\n"
             "!colspan=6|Semifinales\n"
             "|-\n!Local\n!Resultado\n!Visitante\n"
             "|-\n|Boca Juniors\n|2 - 1\n|River Plate\n"
             "|}\n")
    ps = parser.partidos(texto, 2011, "Prueba", anio_fin=2012)
    assert len(ps) == 1 and ps[0].fase == "eliminacion"


def test_la_seccion_manda_sobre_el_rotulo_de_fecha():
    """La salvedad que sostiene el caso que motivo el flag: un bloque numerado
    'Fecha N' colgado de una ronda eliminatoria no trae fechas de liga."""
    texto = ("== Ronda de desempate ==\n"
             "{|class=\"wikitable\"\n"
             "!colspan=6|Fecha 1\n"
             "|-\n!Local\n!Resultado\n!Visitante\n"
             "|-\n|Boca Juniors\n|2 - 1\n|River Plate\n"
             "|}\n")
    ps = parser.partidos(texto, 2011, "Prueba", anio_fin=2012)
    assert len(ps) == 1 and ps[0].fase == "eliminacion"


def test_la_columna_fecha_no_convierte_una_llave_en_fase_regular():
    """`Fecha` tambien es el nombre de una COLUMNA -- la del dia --, y contarla
    haria pasar por fase regular a cualquier tabla que publique el dia de sus
    partidos. Por eso se miran solo los encabezados con `colspan`.

    El titulo de la seccion tiene que ser NEUTRO para que este test pruebe algo.
    La primera version usaba "== Promocion ==", que `_ES_RONDA` ya reconoce como
    ronda: la tabla quedaba en eliminacion por el titulo y el test pasaba igual
    aunque el criterio de la columna estuviera roto. Lo delato el mutante."""
    texto = ("== Definiciones ==\n"
             "{|class=\"wikitable\"\n"
             "|-\n!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n"
             "|-\n|Boca Juniors\n|2 - 1\n|River Plate\n|Un Estadio\n|3 de junio\n|20:00\n"
             "|}\n")
    ps = parser.partidos(texto, 2011, "Prueba", anio_fin=2012)
    assert len(ps) == 1 and ps[0].fase == "eliminacion"


# --------------------------------------------------------------------------
# el anio y la nota al pie de la fecha
# --------------------------------------------------------------------------
def test_el_anio_que_escribe_la_celda_le_gana_a_la_regla():
    """El Apertura 2007 se jugo entre agosto y diciembre, pero un partido quedo
    postergado hasta abril y la pagina escribe el anio: '23 de abril de 2008'.
    Deducirlo por el mes lo mandaba a abril de 2007, cuando el torneo ni existia."""
    assert parser.a_iso("23 de abril de 2008", 2007) == "2008-04-23"
    assert parser.a_iso("23 de abril", 2007) == "2007-04-23"


def test_sin_anio_escrito_la_regla_de_la_temporada_sigue_valiendo():
    assert parser.a_iso("22 de enero", 2016, 2017, 8) == "2017-01-22"
    assert parser.a_iso("22 de septiembre", 2016, 2017, 8) == "2016-09-22"


def test_la_nota_dice_cuando_se_jugo_de_verdad():
    """La celda de un partido postergado guarda el dia para el que ESTABA
    previsto. El dataset dice cuando se jugo."""
    fila = ("|Villa Dálmine\n|1 - 3\n|Ferro Carril Oeste\n"
            "|28 de junio<ref group=\"n.\">Suspendido por lluvia. "
            "Se jugó el 29 de julio, a partir de las 15:00.</ref>\n|21:30")
    assert parser._fecha_de_la_nota(fila, 2015, None, 8) == "2015-07-29"


def test_completar_un_partido_no_es_jugarlo_otro_dia():
    """`se completó` es el partido que EMPEZO ese dia y se termino despues: la
    fecha buena sigue siendo la primera. Son 105 casos, y meterlos en la misma
    bolsa que los 296 de `se jugó` los mandaria al dia equivocado."""
    fila = "|2 de marzo<ref>Suspendido. Se completó el 4 de marzo, a las 20:00.</ref>"
    assert parser._fecha_de_la_nota(fila, 2025, None, 8) == ""


def test_la_fecha_jugada_nunca_cae_antes_de_la_programada():
    """Un partido no se juega antes del dia para el que estaba previsto, asi que
    si la regla de la temporada lo pone antes, el anio es el que sigue. El caso
    real es de la pandemia: previsto para el 14 de marzo de 2020 y jugado el 29
    de noviembre, que por el mes la regla contesta 2019."""
    fila = "|14 de marzo<ref>Suspendido. Se jugó el 29 de noviembre, a las 17:10.</ref>"
    assert parser._fecha_de_la_nota(fila, 2019, 2020, 8, "2020-03-14") == "2020-11-29"
    assert parser._fecha_de_la_nota(fila, 2019, 2020, 8) == "2019-11-29"


def test_los_pipes_de_una_nota_no_crean_celdas():
    """Una `{{Cita web |url=...|fechaacceso=...}}` mete tres celdas falsas y corre
    todo lo que viene despues. El Apertura 2025 publicaba partidos cuya HORA era
    el titulo de la nota."""
    fila = ("|Banfield\n|1 - 1\n|Independiente\n|Florencio Sola\n|2 de marzo"
            "<ref>{{Cita web |url=http://x |título=Se suspendió |sitioweb=TyC}}</ref>\n|21:30")
    assert [parser._celda(c)[1] for c in parser._partir(fila)][-1] == "21:30"


def test_la_nota_se_conserva_aunque_se_le_saquen_los_pipes():
    """No se borra: adentro esta la fecha en que se jugo el partido postergado.
    Sin pipes queda pegada a su celda, que es la de la fecha."""
    fila = "|28 de junio{{refn|group=n.|Suspendido. Se jugó el 29 de julio.}}"
    assert "29 de julio" in parser._partir(fila)[0]


# la nota, de punta a punta y con la forma que de verdad tiene en Wikipedia:
# un `<ref>` de varias lineas, que es lo unico que llega a partir la fila.
_FILA_CON_NOTA = """{|class="wikitable"
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Villa Dálmine
|1 - 3
|Ferro Carril Oeste
|El Coliseo
|28 de junio<ref>{{Cita web
|url=http://x
|título=Suspendido por lluvia. Se jugó el 29 de julio, a partir de las 15:00.
|fechaacceso=26 de enero de 2022}}</ref>
|21:30
|}"""


def test_la_fecha_del_partido_sale_de_la_nota_y_no_de_la_celda():
    """De punta a punta: no alcanza con que `_fecha_de_la_nota` sepa leerla, la
    tiene que USAR el que arma el partido."""
    p = parser.partidos_de_tabla(_FILA_CON_NOTA, 2015, "X")[0]
    assert p.fecha == "2015-07-29"


def test_una_nota_de_varias_lineas_no_corre_las_columnas():
    """Los `\n|url=`, `\n|título=` y `\n|fechaacceso=` de una cita son tres
    celdas falsas. Con ellas adentro, la HORA del partido pasa a ser el titulo de
    la nota, y la fecha, la de consulta de la cita.

    La nota dice "a la misma hora" para que la hora salga de la CELDA: si dijera
    otra, la hora saldria de la nota y una columna corrida no se notaria aca."""
    fila = _FILA_CON_NOTA.replace("a partir de las 15:00", "a la misma hora")
    p = parser.partidos_de_tabla(fila, 2015, "X")[0]
    assert p.hora == "21:30"
    assert p.estadio == "El Coliseo"
    assert not p.fecha.startswith("2022")


def test_y_si_la_nota_da_la_hora_sale_de_ahi_con_el_dia():
    """De punta a punta, como la fecha: el 29 a las 15:00, no el 29 a las 21:30."""
    p = parser.partidos_de_tabla(_FILA_CON_NOTA, 2015, "X")[0]
    assert (p.fecha, p.hora) == ("2015-07-29", "15:00")


_SIN_DISPUTAR = """{|class="wikitable"
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Sansinena
|0 - 1
|Germinal
|colspan=3|Sin disputar{{refn|name=S1|group=n.|Sansinena fue eliminado del \
torneo por deserción y se le dieron por perdidos los partidos que debía \
disputar entre la 13.ª y la 18.ª fecha.{{refn|name=S}}}}
|-
|Kimberley
|1 - 1
|Ramón Santamarina
|José Alberto Valle
|9 de junio
|11:00
|}"""


def test_el_partido_que_no_se_jugo_no_tiene_estadio_ni_espera_fecha():
    """"SIN DISPUTAR" NO ES UNA CANCHA, Y NO HAY FECHA QUE BUSCARLE.

    La pagina no lo dice en una nota al pie sino en la ESTRUCTURA: donde van
    Estadio, Fecha y Hora pone UNA sola celda con `colspan=3`, porque no hay
    ninguna de las tres cosas que poner. Publicar eso en `venue` seria afirmar
    que el partido se jugo en un lugar llamado "Sin disputar"; dejar `status`
    vacio seria decir que la pagina no dijo nada, cuando dijo lo mas importante
    que se puede decir de un partido.

    Son los seis que el Torneo Federal A 2024 le dio por perdidos a Sansinena
    cuando desertó, y son los unicos del corpus."""
    ps = parser.partidos_de_tabla(_SIN_DISPUTAR, 2024, "Torneo Federal A")
    por = {(x.local, x.visita): x for x in ps}
    no_jugado = por[("Sansinena", "Germinal")]
    assert no_jugado.status == "no disputado"
    assert no_jugado.estadio == ""
    assert no_jugado.fecha == ""
    # El marcador queda: cuenta para la tabla aunque no salga de una cancha.
    assert (no_jugado.goles_local, no_jugado.goles_visita) == (0, 1)

    # Y la fila de al lado, que si se jugo, no se contagia.
    jugado = por[("Kimberley", "Ramón Santamarina")]
    assert (jugado.status, jugado.estadio) == ("", "José Alberto Valle")


def test_sin_disputar_fuera_de_la_celda_del_estadio_no_dice_nada():
    """SE MIRA LA CELDA DEL ESTADIO, NO LA FILA ENTERA.

    Una nota al pie que menciona otro partido sin disputar no convierte a ESTA
    fila en un partido sin disputar. Si se preguntara sobre el texto completo,
    una nota ajena alcanzaria para borrarle el estadio a un partido jugado."""
    assert parser.status_de_la_fila(
        "|A|0 - 1|B|Cancha{{refn|el de la fecha 13 quedó sin disputar}}|hoy|15:00",
        estadio="Cancha") == ""


# --------------------------------------------------------------------------
# el partido que existe y no se puede escribir
# --------------------------------------------------------------------------
_ANULADO_LIGA = """{|class="wikitable"
!Local
!Resultado
!Visitante
!Estadio
|-align=center
|Independiente (N)
|PP - PP<ref group="n.">Se le dio por perdido a ambos equipos.</ref>
|Deportivo Roca
|La Nueva Caldera
|-align=center
|Cipolletti
|1 - 1
|Villa Mitre
|La Visera
|}"""


def test_denuncia_el_partido_que_el_esquema_no_puede_escribir():
    """`PP - PP` es partido perdido para LOS DOS. No hay par de goles que lo diga:
    una fila tiene un `home_score` y un `away_score`, y cualquier cosa que se
    ponga ahi afirma que alguien gano.

    El parser descarta la fila, que es correcto. Lo que faltaba era decirlo: sin
    el aviso el hueco aparece como un partido que falta -- la tabla SI lo cuenta,
    asi que el chequeo de PJ lo denuncia -- y manda a buscar un error de lectura
    que no existe."""
    avisos = parser.partidos_anulados(_ANULADO_LIGA)
    assert len(avisos) == 1
    assert "Independiente (N)" in avisos[0] and "Deportivo Roca" in avisos[0]


def test_el_partido_anulado_no_entra_al_dataset():
    """Se avisa, no se inventa. La otra fila de la misma tabla sigue entrando."""
    ps = parser.partidos_de_tabla(_ANULADO_LIGA, 2019, "X")
    assert [(p.local, p.visita) for p in ps] == [("Cipolletti", "Villa Mitre")]


def test_lo_encuentra_tambien_en_el_formato_de_copa():
    """La columna del resultado no esta siempre en el mismo lugar: la liga ordena
    Local-Resultado-Visitante y la copa Fecha-Estadio-Equipo 1-Partido-Equipo 2.
    Buscando en una posicion fija, la Copa Argentina 2013-14 no se veia."""
    copa = ("{|class=\"wikitable\"\n|-\n|align=center| 20 de marzo || Sin sede "
            "||align=right| Estudiantes Unidos || align=center|PP  - PP<ref>Los dos "
            "abandonaron el torneo.</ref> ||align=left| Belgrano (E)\n|}")
    avisos = parser.partidos_anulados(copa)
    assert len(avisos) == 1
    assert "Estudiantes Unidos" in avisos[0] and "Belgrano (E)" in avisos[0]


@pytest.mark.parametrize("celda", ["1 - 1", "-", "", "a jugarse", "PP"])
def test_no_denuncia_lo_que_no_es_un_partido_anulado(celda):
    """La sigla tiene que estar de los DOS lados. `PP` sola es el equipo al que se
    lo dieron por perdido, y ese caso SI se puede escribir: la pagina trae el
    marcador que otorgo el tribunal."""
    tabla = _ANULADO_LIGA.replace("PP - PP<ref group=\"n.\">Se le dio por perdido a ambos equipos.</ref>", celda)
    assert parser.partidos_anulados(tabla) == []


# --------------------------------------------------------------------------
# status: de donde salio el marcador
# --------------------------------------------------------------------------
def test_una_fila_sin_nota_no_dice_nada():
    """Vacio NO certifica que se hayan jugado los 90: dice que nadie dijo lo
    contrario. Esa lectura es lo que hace que el default no sea una afirmacion
    inventada sobre 39 mil filas."""
    assert parser.status_de_la_fila("|Boca Juniors\n|2 - 1\n|River Plate") == ""


def test_el_partido_que_se_suspendio_y_se_termino_de_jugar_no_lleva_status():
    """Llego al final igual, aunque en dos dias. Son 356 de las 409 filas que
    mencionan una suspension: meterlas en `suspendido` seria decir que su
    marcador no es de la cancha."""
    fila = "|Aldosivi\n|2 - 0\n|Argentinos Juniors\n|20 de mayo<ref>Suspendido por lluvia. Se jugó el 15 de noviembre.</ref>"
    assert parser.status_de_la_fila(fila) == ""


def test_el_partido_que_no_llego_al_final_lleva_suspendido():
    fila = "|San Telmo\n|0 - 1\n|Sportivo Italiano<ref>Suspendido a los 89 minutos por incidentes.</ref>"
    assert parser.status_de_la_fila(fila) == "suspendido"


def test_el_partido_que_termino_y_lo_cambio_un_fallo_lleva_escritorio():
    """El caso que ninguna busqueda por 'suspension' encuentra: se jugaron los
    noventa minutos y el numero publicado igual es de oficina."""
    fila = ("|Atlanta\n|1 - 0<ref>Finalizado 0 a 0, se le dio por ganado a Atlanta "
            "por 1 a 0, por mala inclusión de un jugador de Colegiales.</ref>\n|Colegiales")
    assert parser.status_de_la_fila(fila) == "escritorio"


def test_si_hubo_suspension_manda_la_suspension():
    """El orden es la regla entera. Un partido suspendido Y fallado no llego al
    final, y eso es lo unico que la fuente dice sin ambiguedad: si se mira primero
    el fallo, la mitad de los suspendidos pasan a `escritorio` por una palabra.

    Es el `Cañuelas 0-1 San Martín (B)` de la Primera C 2019-20."""
    fila = ("|Cañuelas\n|0 - 1\n|San Martín (B){{refn|group=\"n.\"|Suspendido a los 40 "
            "minutos del primer tiempo por incidentes, con el resultado 0 a 0. Se le dio por "
            "ganado a San Martín (B) por 1 a 0.}}")
    assert parser.status_de_la_fila(fila) == "suspendido"


def test_una_fila_que_habla_de_un_fallo_y_no_se_supo_leer_se_denuncia():
    """La guarda del default. Vacio significa "la pagina no dijo nada"; el dia que
    signifique tambien "dijo algo que no supe leer", las 39 mil filas vacias dejan
    de ser una ausencia y pasan a ser una afirmacion sin verificar."""
    fila = "|Boca Juniors\n|2 - 1\n|River Plate<ref>El Tribunal resolvió algo raro.</ref>"
    assert parser.status_de_la_fila(fila) == ""
    assert parser.sin_clasificar(fila)


def test_lo_que_ya_se_clasifico_no_se_denuncia():
    for fila in ("|A\n|1 - 0\n|B<ref>Suspendido a los 10'.</ref>",
                 "|A\n|1 - 0\n|B<ref>Suspendido por lluvia. Se jugó el 3 de mayo.</ref>",
                 "|A\n|1 - 0\n|B"):
        assert not parser.sin_clasificar(fila), fila


# --------------------------------------------------------------------------
# la tanda escrita adentro de la celda del resultado
# --------------------------------------------------------------------------
@pytest.mark.parametrize("celda, pen", [
    # las dos notaciones que usa Wikipedia
    ("{{small|(5)}} 1 - 1 {{small|(4)}}", (5, 4)),
    ("1 - 1<br><hr><small>[[Penaltis|Pen.]]<br>3 - 4</small>", (3, 4)),
    ("1 – 0<br><hr><small>[[Penaltis|Pen.]]<br>3 - 2</small>", (3, 2)),
])
def test_las_dos_formas_de_escribir_la_tanda(celda, pen):
    assert parser._penales(celda) == pen


@pytest.mark.parametrize("celda", ["2 - 1", "0:1 (0:0)", "1 - 1 (0-0)", ""])
def test_lo_que_no_es_una_tanda(celda):
    """`0:1 (0:0)` es el ENTRETIEMPO, no los penales -- es el error que el
    docstring del modulo pone como ejemplo de parser que miente en vez de fallar.
    Por eso la segunda notacion pide la palabra escrita y no solo dos numeros."""
    assert parser._penales(celda) is None


def test_la_tanda_llega_al_partido_en_una_tabla_de_liga():
    """No alcanza con saber leerla: la tabla de liga no la miraba. Son doce
    partidos, y son finales y definiciones de ascenso -- justo donde la tanda es
    la que dice quien subio."""
    tabla = """{|class="wikitable"
!Local
!Resultado
!Visitante
!Estadio
!Fecha
|-align=center
|San Martín (T)
|'''1 - 1'''<br><hr><small>[[Penaltis|Pen.]]<br>3 - 4</small>
|Villa Mitre
|La Ciudadela
|28 de mayo de 2006
|}"""
    p = parser.partidos_de_tabla(tabla, 2005, "X")[0]
    assert (p.goles_local, p.goles_visita) == (1, 1)
    assert (p.penales_local, p.penales_visita) == (3, 4)


def test_la_raya_larga_tambien_separa_un_marcador():
    """`1 – 0` con raya media se ve igual que `1 - 0` y no lo es. La fila no tenia
    marcador y el partido se descartaba entero: asi se perdia el desempate por el
    descenso del Argentino A 2005-06."""
    assert parser._marcador("1 – 0") == (1, 0)
    assert parser._marcador("1 — 0") == (1, 0)
    assert parser._marcador("1 - 0") == (1, 0)


def test_la_tanda_sobrevive_a_un_rowspan():
    """La celda cruda se lleva por COLUMNA y no por indice.

    Un `rowspan` en una columna TEMPRANA corre todos los indices de las filas que
    siguen: la segunda fila de abajo no trae su `Local`, asi que su segunda celda
    cruda es el VISITANTE y no el resultado. Buscar la tanda en `celdas[1]` la
    leeria de la columna de al lado, en silencio."""
    tabla = """{|class="wikitable"
!Local
!Resultado
!Visitante
!Estadio
!Fecha
|-align=center
|rowspan=2|San Martín (T)
|2 - 0
|River Plate
|La Ciudadela
|27 de mayo
|-align=center
|1 - 1<br><small>[[Penaltis|Pen.]]<br>3 - 4</small>
|Villa Mitre
|La Ciudadela
|28 de mayo
|}"""
    ps = parser.partidos_de_tabla(tabla, 2005, "X")
    assert [p.local for p in ps] == ["San Martín (T)", "San Martín (T)"], "el rowspan se rompio"
    assert (ps[0].penales_local, ps[0].penales_visita) == (None, None)
    assert (ps[1].penales_local, ps[1].penales_visita) == (3, 4)


# --------------------------------------------------------------------------
# la tanda de una serie, en la tabla del global
# --------------------------------------------------------------------------
# La tercera etapa de la Revalida del Federal A 2016-17, recortada: la primera llave
# se definio por penales y la tanda esta SOLO aca, pegada al global y adentro de un
# `{{nowrap}}`; la segunda no tuvo tanda.
_ENFRENTAMIENTOS = """== Reválida ==
=== Tercera etapa ===
==== Enfrentamientos ====
{| class="wikitable" style="margin: 0 auto; text-align: center;" width="85%"
|- style="background:#dddddd;"
|-
!width=40|Llave
!width=160|Equipo 1
!width=30|Global
!width=160|Equipo 2
|-align=center
|'''1
|bgcolor=#ccffcc|'''Defensores de Belgrano (Villa Ramallo)
|{{nowrap|{{small|(4)}} 1 - 1 {{small|(3)}}}}
|Guaraní Antonio Franco
|-align=center
|'''2
|Sportivo Patria
|2 - 3
|bgcolor=#ccffcc|'''Gutiérrez SC
|}
"""


def test_la_tanda_de_la_tabla_del_global_se_lee():
    """Con los clubes en el orden de las columnas, el global y la tanda en ese mismo
    orden, y la seccion de nivel 2 como llave. La fila sin tanda no aporta nada."""
    assert parser.tandas_de_las_series(_ENFRENTAMIENTOS) == [parser.Tanda(
        "Defensores de Belgrano (Villa Ramallo)", "Guaraní Antonio Franco", 1, 1, 4, 3,
        "Reválida")]


def test_la_tabla_del_global_sin_columna_de_llave():
    """El Federal A 2014 no numera las llaves: la columna `Global` es la segunda."""
    texto = """== Segunda a cuarta fase ==
=== Segunda fase ===
==== Enfrentamientos ====
{| class="wikitable" style="text-align: center;" width="70%"
|- style="background:#dddddd;"
!width="100"|Equipo 1
!width="30"|Global
!width="100"|Equipo 2
|-align=center
|bgcolor=#CCFFCC|'''CAI
|{{small|(4)}} 2 - 2 {{small|(3)}}
|Juventud Unida Universitario
|}
"""
    assert parser.tandas_de_las_series(texto) == [parser.Tanda(
        "CAI", "Juventud Unida Universitario", 2, 2, 4, 3, "Segunda a cuarta fase")]


@pytest.mark.parametrize("tabla", [
    # La fase regional de la Copa Argentina: tiene `Global` y tandas, pero las
    # columnas de club dicen quien fue local en cada pata.
    """{| class="wikitable"
!Fecha !! Estadio !! Local en la ida !! !! Global !! !! Local en la vuelta
|-
| 10 de febrero || El Fortín || Villa Mitre || 2 || <small>(5)</small> 2 - 2 <small>(4)</small> || 0 || Juventud Unida Universitario
|}""",
    # Un desempate a partido unico: `Equipo 1` y `Equipo 2` sin `Global`.
    """{| class="wikitable"
!Equipo 1
!Resultado
!Equipo 2
|-
|Boca Juniors
|{{small|(4)}} 1 - 1 {{small|(3)}}
|River Plate
|}""",
])
def test_una_tabla_que_no_es_de_series_no_da_tandas(tabla):
    assert parser.tandas_de_las_series(tabla) == []


def test_la_tabla_del_global_que_cierra_con_la_leyenda():
    """El Federal A 2025 y el 2026 cierran la tabla del global con la plantilla de la
    leyenda, `{{Tabla de posiciones fin|...}}`, y no con `|}`. Sin contarla como
    cierre la tabla no termina nunca y su tanda no se lee. La fila de la tanda va
    ULTIMA a proposito: la plantilla no se le pega al `Equipo 2`."""
    texto = _ENFRENTAMIENTOS.replace(
        "|-align=center\n|'''2\n|Sportivo Patria\n|2 - 3\n|bgcolor=#ccffcc|'''Gutiérrez SC\n", "")
    texto = texto.replace("|'''1\n", "|'''2\n|Sportivo Patria\n|2 - 3\n"
                          "|bgcolor=#ccffcc|'''Gutiérrez SC\n|-align=center\n|'''1\n")
    texto = texto.replace("|}\n", "{{Tabla de posiciones fin\n|color1= #cfc|texto1="
                          "Clasificados a la [[#Cuarta etapa|Cuarta etapa]].\n}}\n")
    assert "|}" not in texto
    assert parser.tandas_de_las_series(texto) == [parser.Tanda(
        "Defensores de Belgrano (Villa Ramallo)", "Guaraní Antonio Franco", 1, 1, 4, 3,
        "Reválida")]


@pytest.mark.parametrize("fila", [
    "|Sportivo Patria\n|{{small|(4)}} - {{small|(3)}}\n|Gutiérrez SC",
    "|\n|{{small|(4)}} 1 - 1 {{small|(3)}}\n|Gutiérrez SC",
    "|Sportivo Patria\n|{{small|(4)}} 1 - 1 {{small|(3)}}\n|",
], ids=["sin global", "sin equipo 1", "sin equipo 2"])
def test_una_fila_a_medio_llenar_no_da_tanda(fila):
    """Una serie que todavia no se jugo, o que la pagina dejo a medias: la tanda sin el
    global o sin uno de los dos clubes no se puede colgar de ninguna vuelta."""
    texto = ("== Reválida ==\n{| class=\"wikitable\"\n!Llave\n!Equipo 1\n!Global\n"
             "!Equipo 2\n|-\n|'''1\n" + fila + "\n|}\n")
    assert parser.tandas_de_las_series(texto) == []


def _pata(local, visita, gl, gv, fecha, jornada, llave="Reválida", pl=None, pv=None):
    return parser.Partido(fecha=fecha, local=local, visita=visita, goles_local=gl,
                          goles_visita=gv, penales_local=pl, penales_visita=pv,
                          fase="eliminacion", jornada=jornada, llave=llave)


DDB, GAF = "Defensores de Belgrano (VR)", "Guaraní Antonio Franco"
# Como la escribe la tabla del global: el nombre largo, que no es el de la grilla.
TANDA_DDB = parser.Tanda("Defensores de Belgrano (Villa Ramallo)", GAF, 1, 1, 4, 3, "Reválida")


def test_la_tanda_va_a_la_vuelta_y_se_da_vuelta_si_hace_falta():
    """La vuelta es la del dia mas tarde, no la del rotulo, y su local es el
    `Equipo 2` de la tabla: los penales se escriben al reves que en la tabla. Con la
    pata en la jornada y la vuelta empatada, la tanda entra igual: se explica sola."""
    ida = _pata(DDB, GAF, 1, 1, "2017-05-15", "Partidos de ida")
    vuelta = _pata(GAF, DDB, 0, 0, "2017-05-20", "Partidos de vuelta")
    assert parser.colgar_tandas([vuelta, ida], [TANDA_DDB]) == []
    assert (vuelta.penales_local, vuelta.penales_visita) == (3, 4)
    assert (ida.penales_local, ida.penales_visita) == (None, None)


def test_una_vuelta_que_no_empato_lleva_la_tanda_si_las_patas_son_una_serie():
    """Defensores de Belgrano 1-0 Guarani Antonio Franco despues de perder la ida
    1-0: la tanda se pateo al final de una vuelta que no empato."""
    ida = _pata(GAF, DDB, 1, 0, "2017-05-15", "Tercera etapa")
    vuelta = _pata(DDB, GAF, 1, 0, "2017-05-20", "Tercera etapa")
    assert parser.colgar_tandas([ida, vuelta], [TANDA_DDB]) == []
    assert (vuelta.penales_local, vuelta.penales_visita) == (4, 3)


def test_si_la_jornada_no_junta_a_las_patas_la_tanda_espera():
    """Una tabla que rotula solo la pata y no tiene ninguna ronda arriba deja
    `Partidos de ida` y `Partidos de vuelta` en la jornada (ver `_ES_PATA`), y con
    eso `serie_igualada` no ve una serie: escribirla igual frenaria el build con un
    `penales en un partido que no fue empate`. Queda afuera, y lo dice."""
    from fad import validar

    ps = [_pata(GAF, DDB, 1, 0, "2017-05-15", "Partidos de ida"),
          _pata(DDB, GAF, 1, 0, "2017-05-20", "Partidos de vuelta")]
    avisos = parser.colgar_tandas(ps, [TANDA_DDB])
    assert len(avisos) == 1 and "serie_igualada" in avisos[0]
    assert all(p.penales_local is None for p in ps)
    assert validar.penales_solo_en_empates(ps) == []


@pytest.mark.parametrize("ps, tanda, dice", [
    # las patas suman otro global
    ([_pata(GAF, DDB, 1, 0, "2017-05-15", "Tercera etapa"),
      _pata(DDB, GAF, 2, 0, "2017-05-20", "Tercera etapa")], TANDA_DDB, "suman"),
    # la tabla publica una tanda sobre un global que no empato
    ([_pata(GAF, DDB, 1, 0, "2017-05-15", "Tercera etapa"),
      _pata(DDB, GAF, 1, 1, "2017-05-20", "Tercera etapa")],
     parser.Tanda(DDB, GAF, 1, 2, 4, 3, "Reválida"), "igualado"),
    # una sola pata en la grilla
    ([_pata(DDB, GAF, 1, 1, "2017-05-20", "Tercera etapa")], TANDA_DDB, "tiene 1"),
    # el mismo par tres veces en la llave
    ([_pata(GAF, DDB, 0, 0, "2017-05-15", "Tercera etapa"),
      _pata(DDB, GAF, 1, 1, "2017-05-20", "Tercera etapa"),
      _pata(DDB, GAF, 0, 0, "2017-06-20", "Sexta etapa")], TANDA_DDB, "tiene 3"),
    # las dos patas el mismo dia
    ([_pata(GAF, DDB, 0, 0, "2017-05-20", "Tercera etapa"),
      _pata(DDB, GAF, 1, 1, "2017-05-20", "Tercera etapa")], TANDA_DDB, "dias distintos"),
    # una pata sin fecha: ordenada por fecha queda primera, y no se sabe si es la ida
    ([_pata(GAF, DDB, 0, 0, "", "Tercera etapa"),
      _pata(DDB, GAF, 1, 1, "2017-05-20", "Tercera etapa")], TANDA_DDB, "dias distintos"),
    # la serie es de otra llave de la pagina
    ([_pata(GAF, DDB, 0, 0, "2017-05-15", "Tercera etapa", llave="Primera fase"),
      _pata(DDB, GAF, 1, 1, "2017-05-20", "Tercera etapa", llave="Primera fase")],
     TANDA_DDB, "tiene 0"),
])
def test_una_serie_que_no_cierra_no_se_lleva_la_tanda(ps, tanda, dice):
    avisos = parser.colgar_tandas(ps, [tanda])
    assert len(avisos) == 1 and dice in avisos[0]
    assert all(p.penales_local is None for p in ps)


def test_un_partido_de_zonas_entre_los_dos_no_es_una_pata():
    """La Revalida del Federal A arranca con una etapa de zonas y sigue con las
    series, todo bajo `== Reválida ==`: dos clubes que se cruzaron en la zona y
    despues en una serie tienen tres partidos en la misma llave. La serie son los
    dos de eliminacion."""
    zona = _pata(DDB, GAF, 2, 0, "2017-03-12", "Fecha 3")
    zona.fase = "zonas"
    ida = _pata(DDB, GAF, 1, 1, "2017-05-15", "Tercera etapa")
    vuelta = _pata(GAF, DDB, 0, 0, "2017-05-20", "Tercera etapa")
    assert parser.colgar_tandas([zona, ida, vuelta], [TANDA_DDB]) == []
    assert (vuelta.penales_local, vuelta.penales_visita) == (3, 4)
    assert zona.penales_local is None and ida.penales_local is None


@pytest.mark.parametrize("trae, avisa", [((4, 3), False), ((5, 4), True)])
def test_la_vuelta_que_ya_trae_su_tanda_no_se_toca(trae, avisa):
    """Si es la misma no hay nada que decir; si es otra, la pagina se contradice y no
    hay como saber cual de las dos tablas tiene razon."""
    vuelta = _pata(DDB, GAF, 1, 1, "2017-05-20", "Tercera etapa", pl=trae[0], pv=trae[1])
    ps = [_pata(GAF, DDB, 0, 0, "2017-05-15", "Tercera etapa"), vuelta]
    assert bool(parser.colgar_tandas(ps, [TANDA_DDB])) == avisa
    assert (vuelta.penales_local, vuelta.penales_visita) == trae


# --------------------------------------------------------------------------
# una mini-liga que se llama como una llave
# --------------------------------------------------------------------------
def _seccion_ronda(rotula):
    """Un `Resultados` colgado de una seccion con nombre de ronda."""
    bloque = ("!colspan=6|Fecha 1\n|-\n" if rotula else "")
    return f"""== Descenso ==
=== Ronda de desempate ===
==== Resultados ====
{{|class="wikitable"
{bloque}!Equipo 1
!Resultado
!Equipo 2
!Estadio
!Fecha
|-align=center
|San Martín (F)
|2 - 2
|Gimnasia y Tiro
|Miguel Sancho
|3 de abril
|}}
"""


def test_una_mini_liga_no_es_una_llave_aunque_la_seccion_se_llame_ronda():
    """La `Ronda de desempate` del Federal A 2018-19 son tres clubes empatados en
    la tabla de descenso jugando un triangular de tres fechas, con su propia tabla
    de posiciones. No es una llave, y quedaba en `eliminacion`.

    Lo que decide es la TABLA: si rotula sus bloques `Fecha N`, es fase regular
    aunque la seccion se llame como una ronda."""
    p = parser.partidos(_seccion_ronda(rotula=True), 2018, "X")[0]
    assert p.fase == "zonas"
    assert p.jornada == "Fecha 1"


def test_una_llave_de_verdad_sigue_siendo_una_llave():
    """La salvedad no puede tragarse a las llaves. De las dieciseis secciones del
    corpus cuyo titulo parece una ronda, quince NO rotulan fechas -- octavos,
    cuartos, semis, finales, primera/segunda/tercera ronda -- y tienen que seguir
    en eliminacion."""
    p = parser.partidos(_seccion_ronda(rotula=False), 2018, "X")[0]
    assert p.fase == "eliminacion"


# --------------------------------------------------------------------------
# los 240 partidos que las copas no entregaban
# --------------------------------------------------------------------------
def test_la_tanda_pegada_adelante_no_tapa_el_marcador():
    """Las copas viejas escriben la tanda con un tag -- `<small>(4)</small> 0 - 0
    <small>(5)</small>` -- y `limpiar` saca el tag pero deja el contenido, asi que
    la celda queda en `(4) 0 - 0 (5)`. Las nuevas la escriben con plantilla y la
    plantilla se borra entera, por eso la 2025 parseaba 63 de 63 y la 2013-14, 20.

    El ancla al principio de `_marcador` es a proposito y no se toca: sin ella
    cualquier par de numeros de la celda pasaria por marcador. Lo que se agrega es
    un segundo intento."""
    assert parser._marcador("(4) 0 - 0 (5)") == (0, 0)
    assert parser._marcador("(3) 1 - 1 (1)") == (1, 1)


def test_el_entretiempo_sigue_sin_ser_penales():
    """`0:1 (0:0)` lleva los parentesis DESPUES y es el entretiempo. Es el error
    que el docstring del modulo pone como ejemplo de parser que miente, y el
    arreglo de arriba no lo puede resucitar: el grupo que saca va adelante."""
    assert parser._marcador("0:1 (0:0)") == (0, 1)
    assert parser._penales("0:1 (0:0)") is None


def test_el_nowrap_con_una_plantilla_adentro_no_se_come_al_club():
    """El no-goloso cerraba en el primer `}}`, que aca es el de la bandera: el
    desenvuelto quedaba mal armado, el barrido general de plantillas se llevaba al
    club y la celda quedaba VACIA. El partido se descartaba sin que nada fallara."""
    assert parser.limpiar("{{nowrap|{{bandera|Santa Fe}} Colón}}") == "Colón"
    assert parser.limpiar("{{nowrap|Gimnasia y Esgrima (LP)}}") == "Gimnasia y Esgrima (LP)"
    assert parser.limpiar("{{nowrap|A}} y {{nowrap|B}}") == "A y B"


def test_un_nowrap_sin_cerrar_sigue_andando():
    """Ya pasaba antes y hay que conservarlo: la plantilla SIN cerrar existe, y
    como no cierra no la agarra ni el desenvuelto ni el barrido general."""
    assert parser.limpiar("{{nowrap|Defensores de Cambaceres") == "Defensores de Cambaceres"


@pytest.mark.parametrize("titulo", ["Preclasificatorio", "Ronda previa",
                                    "Fase final I", "Fase final II"])
def test_las_rondas_de_entrada_de_las_copas_viejas_se_reconocen(titulo):
    """Las ediciones viejas tienen rondas de entrada que las nuevas no. Sin
    reconocer el titulo, esas secciones no se miran NUNCA: eran 35 partidos, en
    tablas del mismo formato que las demas."""
    assert parser._TITULO_RONDA.match(f"=== {titulo} ===")


def test_una_ronda_anidada_en_otra_no_se_lee_dos_veces():
    """Las copas viejas parten `=== Semifinales ===` en `==== Semifinal 1 ====` y
    `==== Semifinal 2 ====`, y los dos titulos matchean el mismo regex. Sin
    saltear los de adentro, cada semi entra dos veces y `validar.sin_duplicados`
    frena el build."""
    texto = """=== Semifinales ===
==== Semifinal 1 ====
{|class="wikitable"
|-
|align=center|3 de junio ||align=center| Bicentenario ||align=right| Boca Juniors || align=center| <small>(5)</small> 1 - 1 <small>(4)</small> ||align=left| Deportivo Merlo
|}
"""
    ps = parser.partidos_de_rondas(texto, 2012, "Copa Argentina")
    assert len(ps) == 1, "la semifinal entro dos veces"
    assert (ps[0].local, ps[0].visita) == ("Boca Juniors", "Deportivo Merlo")
    assert (ps[0].penales_local, ps[0].penales_visita) == (5, 4)


# --------------------------------------------------------------------------
# el resaltado contra sus propios digitos
# --------------------------------------------------------------------------
def _grilla(*filas: str) -> str:
    """Una grilla con la forma Local | Resultado | Visitante."""
    return '{| class="wikitable"\n' + "\n".join(filas) + "\n|}"


FILA_SANA = ('|-\n|bgcolor=#D0E7FF|\'\'\'Banfield\n|2 - 0\n|Aldosivi')
FILA_QUE_DESMIENTE = ('|-\n|bgcolor=#D0E7FF|\'\'\'Platense\n|1 - 4\n|Belgrano')


def test_el_resaltado_que_acompania_no_dice_nada():
    """La mitad del chequeo es lo que NO hace. Cuando el color va sobre el que
    los digitos dan por ganador no esta confirmando nada: es el mismo dato
    escrito dos veces por la misma mano. Medido contra los 33 marcadores ya
    arbitrados, ese acuerdo banco al digito FALSO 12 de 12 veces."""
    assert parser.resaltado_que_desmiente(_grilla(FILA_SANA)) == []


def test_el_resaltado_que_contradice_acusa():
    avisos = parser.resaltado_que_desmiente(_grilla(FILA_QUE_DESMIENTE))
    assert len(avisos) == 1
    assert "Platense 1-4 Belgrano" in avisos[0]
    assert "gano Belgrano" in avisos[0] and "marca a Platense" in avisos[0]


def test_el_empate_resaltado_sobre_el_marcador_es_la_convencion():
    """Cuando el partido termino empatado la pagina pinta la celda del MARCADOR
    en vez de un club. Es la convencion, no una contradiccion."""
    fila = '|-\n|Banfield\n|bgcolor=#D0E7FF|\'\'\'1 - 1\n|Aldosivi'
    assert parser.resaltado_que_desmiente(_grilla(fila)) == []


def test_el_marcador_pintado_sobre_un_no_empate_acusa():
    """Y al reves: la celda del marcador pintada cuando los digitos NO empatan.
    Es el caso Deportivo Moron 1-3 Belgrano, donde la verdad era 1-1."""
    fila = '|-\n|Deportivo Morón\n|bgcolor=#D0E7FF|\'\'\'1 - 3\n|Belgrano'
    avisos = parser.resaltado_que_desmiente(_grilla(fila))
    assert len(avisos) == 1 and "marca un empate" in avisos[0]


def test_el_aviso_no_propone_un_marcador():
    """El color da la DIRECCION, no los goles: no distingue un 2-1 de un 3-0.
    Un aviso que propusiera un marcador estaria inventando la magnitud, que es
    justo el error que el modulo entero trata de no cometer."""
    aviso = parser.resaltado_que_desmiente(_grilla(FILA_QUE_DESMIENTE))[0]
    assert "no propone un marcador" in aviso
    assert not re.search(r"deberia|tendria que|corregir a", aviso)


def test_dos_celdas_pintadas_no_acusan():
    """Con el azul en las DOS celdas no se sabe cual habla del partido, y el
    chequeo se calla: su modo de fallar tiene que ser el silencio y no una
    acusacion falsa. Sin la guarda tomaria la primera y acusaria al visitante.

    Hoy no pasa -- son 0 filas en las 131 paginas -- y va igual porque es lo que
    la condicion afirma: UNA marca, no al menos una."""
    fila = "|-\n|bgcolor=#D0E7FF|Platense\n|0 - 1\n|bgcolor=#D0E7FF|Colegiales"
    assert parser.resaltado_que_desmiente(_grilla(fila)) == []


def test_el_rojo_del_descenso_no_tapa_al_azul():
    """El caso real de dos colores es este: azul sobre el ganador y rojo sobre el
    que desciende. Como el rojo no entra en `_AZUL_DEL_GANADOR` queda UNA marca y
    la fila se sigue leyendo, en vez de perderse por ambigua."""
    fila = ("|-\n|bgcolor=#D0E7FF|'''Rosario Central\n|1 - 0\n"
            "|bgcolor=#FFCCCC|Deportivo Merlo [[Archivo:1downarrow red.svg|12px]]")
    assert parser.resaltado_que_desmiente(_grilla(fila)) == []
    assert len(parser.resaltado_que_desmiente(
        _grilla(fila.replace("|1 - 0", "|0 - 1")))) == 1


def test_el_verde_no_es_el_azul_del_ganador():
    """Los verdes quieren decir clasifica/asciende/avanza, y se ponen sobre el
    que PASA, que puede haber empatado o perdido ese partido. Tomarlos por
    "gano" convierte 88 filas legitimas en acusaciones falsas."""
    fila = '|-\n|bgcolor=#cfc|Kimberley\n|1 - 2\n|Sarmiento (R)'
    assert parser.resaltado_que_desmiente(_grilla(fila)) == []


def test_la_fila_con_tanda_no_acusa():
    """En una llave el color marca a QUIEN AVANZO, no quien gano los noventa
    minutos, asi que un 0-0 con un lado pintado es exactamente lo correcto."""
    fila = ('|-\n|bgcolor=#D0E7FF|\'\'\'Sarmiento (R)\n'
            '|{{small|(5)}} 0 - 0 {{small|(4)}}\n|Ciudad de Bolívar')
    assert parser.resaltado_que_desmiente(_grilla(fila)) == []


def test_la_fila_con_nota_al_pie_no_acusa():
    """Ahi no hay error de nadie: hay dos marcadores legitimos, el que se jugo y
    el que puso el tribunal, y el color puede estar sobre cualquiera sin mentir."""
    fila = ('|-\n|bgcolor=#D0E7FF|\'\'\'Sarmiento (R)\n|0 - 1\n|Unión (S)\n'
            '|14 de julio{{refn|group=n.|Se le dio por perdido al equipo local.}}')
    assert parser.resaltado_que_desmiente(_grilla(fila)) == []


def test_la_hora_no_es_un_marcador():
    """`21:30` entra como un 21-30 si el separador acepta dos puntos, y entonces
    las celdas de al lado -- la fecha, el estadio -- pasan por clubes. Son 239
    filas del corpus, y por eso este chequeo busca con guion solo."""
    fila = '|-\n|bgcolor=#D0E7FF|Malvinas Argentinas\n|21:30\n|Colegiales'
    assert parser.resaltado_que_desmiente(_grilla(fila)) == []


def test_el_corte_de_fila_tolera_el_espacio():
    """`\\n |-` con un espacio adelante aparece 386 veces en 8 paginas. Sin
    tolerarlo el bloque se traga la tabla siguiente y su bgcolor termina
    contando como resaltado de un partido que no es."""
    grilla = '{| class="wikitable"\n |-\n|Deportivo Morón\n|bgcolor=#D0E7FF|\'\'\'1 - 3\n|Belgrano\n|}'
    assert len(parser.resaltado_que_desmiente(grilla)) == 1


def test_lo_ya_arbitrado_no_se_acusa_de_nuevo():
    """El chequeo lee el wikitexto crudo, asi que sin esta puerta seguiria
    acusando para siempre a las filas que el repo ya arreglo -- justamente las
    cuatro en que acerto --, y un aviso que no se puede cerrar nunca es un aviso
    que se aprende a ignorar."""
    ya = {("Platense", "Belgrano", 1, 4)}
    assert parser.resaltado_que_desmiente(_grilla(FILA_QUE_DESMIENTE), ya) == []
    # y no tapa a las demas
    assert len(parser.resaltado_que_desmiente(
        _grilla(FILA_QUE_DESMIENTE, '|-\n|bgcolor=#D0E7FF|\'\'\'Agropecuario\n|1 - 3\n|Belgrano'),
        ya)) == 1


def test_el_arbitrado_se_identifica_por_lo_que_dice_la_pagina():
    """La clave es el marcador que la pagina ESCRIBE, no el arreglado. Con el
    arreglado nunca engancharia: la fila del wikitexto sigue teniendo el falso."""
    assert parser.resaltado_que_desmiente(
        _grilla(FILA_QUE_DESMIENTE), {("Platense", "Belgrano", 1, 0)}) != []


# --------------------------------------------------------------------------
# el cuadro: la siembra, las marcas con enlace y los nombres que no resuelven
# --------------------------------------------------------------------------
def _cuadro(*equipos_: str) -> str:
    filas = "\n".join(f"| RD1-team{i + 1:02d}={e}" for i, e in enumerate(equipos_))
    return "{{Cuadro de 4\n" + filas + "\n}}"


def test_la_siembra_se_despega_del_nombre():
    """`1: Gimnasia y Tiro (S)` es el club con su orden de siembra pegado. Sin
    sacarlo el nombre no resuelve contra el padron y el cuadro se queda sin
    cruzar a sus clubes: eran trece en el corpus."""
    leidos = parser.clubes_del_cuadro(_cuadro("1: Gimnasia y Tiro (S)", "8: Cipolletti"))
    assert set(leidos) == {"Gimnasia y Tiro (S)", "Cipolletti"}


def test_las_marcas_con_wikilink_se_descartan_por_su_articulo():
    """`(p)` y `t. s.` llevan wikilink, asi que por su FORMA no se distinguen de
    un club al que el padron no llegue. Lo que las delata es a donde apuntan."""
    cuadro = _cuadro("[[Club Atlético Banfield|Banfield]]",
                     "[[Tiros desde el punto penal|(p)]]",
                     "[[Prórroga (deporte)|t. s.]]")
    assert set(parser.clubes_del_cuadro(cuadro)) == {"Banfield"}


def test_el_articulo_del_cuadro_llega_al_padron():
    """El cuadro escribe mas corto que la grilla -- `Sarmiento (Junín)` --, y lo
    que resuelve la identidad es el articulo, no el nombre."""
    cuadro = _cuadro("[[Club Atlético Sarmiento (Junín)|Sarmiento (Junín)]]")
    leidos = parser.clubes_del_cuadro(cuadro)
    assert leidos == {"Sarmiento (Junín)": "Club Atlético Sarmiento (Junín)"}
    assert equipos.buscar("Sarmiento (Junín)",
                          "Club Atlético Sarmiento (Junín)").nombre == "Sarmiento (J)"


def test_los_cuatro_alias_que_solo_usa_el_cuadro():
    """Cada uno se confirmo contra la grilla de su propia pagina: es el unico club
    del padron que juega ahi con ese nombre."""
    assert equipos.buscar("Def. de Belgrano (VR)", "").nombre == "Defensores de Belgrano (VR)"
    assert equipos.buscar("Atl. de Rafaela", "").nombre == "Atlético de Rafaela"
    assert equipos.buscar("Independiente Riv.", "").nombre == "Independiente Rivadavia"
    assert equipos.buscar("Güemes", "").nombre == "Güemes (SdE)"


def test_el_nombre_corto_lo_desata_la_pagina_que_lo_usa():
    """`Def. de Belgrano` a secas parecia irresoluble -- hay dos Defensores de
    Belgrano -- y este test afirmaba que no se resolvia. Se resolvio, y no por
    parecido sino leyendo a la pagina: el cuadro de la Copa Argentina 2011-12, que
    es la unica que lo escribe sin enlace, le pone la bandera de la CIUDAD de
    Buenos Aires, mientras que al de Villa Ramallo le pone la de la PROVINCIA. Y
    la Copa 2015-16 usa el mismo nombre corto pero enlazado, al articulo del de
    Villa Crespo.

    El de Villa Ramallo nunca aparece pelado: siempre lleva su `(VR)`, que ya es
    su alias. Por eso el nombre corto puede entrar sin tapar al otro."""
    assert equipos.buscar("Def. de Belgrano", "").nombre == "Defensores de Belgrano"
    assert equipos.buscar("Def. de Belgrano (VR)", "").nombre == "Defensores de Belgrano (VR)"

def test_una_plantilla_con_los_parametros_indentados_no_se_pierde():
    """`{{Partido}}` se escribe de las dos formas y las dos son validas.

    El corte era `cuerpo.split("\\n|")`, que no corta nada cuando la pagina
    indenta: el cuerpo entero quedaba como UN campo llamado `local`, no habia
    `resultado`, y la plantilla se descartaba en silencio. Eran quince en tres
    paginas -- las Copas de la Liga 2021, 2022 y 2023 -- y con ellas se caian sus
    fases finales enteras.
    """
    indentada = ("=== Cuartos de final ===\n"
                 "{{Partido\n"
                 "  |local= Boca Juniors\n"
                 "  |resultado= 2:0\n"
                 "  |visita= River Plate\n"
                 "  |fecha= 11 de mayo, 18:30\n"
                 "  |estadio= La Bombonera\n"
                 "}}\n")
    ps = parser.partidos_de_plantillas(indentada, 2021, "Prueba")
    assert len(ps) == 1, "la plantilla indentada tiene que entrar"
    assert (ps[0].local, ps[0].goles_local, ps[0].goles_visita, ps[0].visita) == \
        ("Boca Juniors", 2, 0, "River Plate")
    assert ps[0].estadio == "La Bombonera", "y con todos sus campos, no solo el marcador"

    pegada = indentada.replace("\n  |", "\n|")
    assert len(parser.partidos_de_plantillas(pegada, 2021, "Prueba")) == 1, \
        "y la forma sin indentar tiene que seguir andando"


def test_un_parametro_en_el_mismo_renglon_que_otro_se_lee():
    """Asi escribe la Primera B 2021 dos llaves del reducido: el `estadio` arranca
    en el renglon de la `fecha`. Cortando por renglon no se veia -- el partido
    salia sin `venue` y con la cancha pegada a la fecha cruda --, y el `|` de un
    enlace en el mismo renglon tampoco puede cortar."""
    texto = ("{{Partido\n"
             "|local = '''J. J. de Urquiza\n"
             "|resultado = 2:0''' (2:0)\n"
             "|visita = [[Club Defensores Unidos|Defensores Unidos]] |ciudad = [[Zárate]]\n"
             "|fecha =21 de noviembre, 17:00 |estadio = Estadio Ramón Roque Martín \n"
             "|árbitro=[[Mariano Negrete]]}}")
    (p,) = parser.partidos_de_plantillas(texto, 2021, "x")
    assert p.estadio == "Estadio Ramón Roque Martín"
    assert (p.fecha, p.fecha_cruda, p.hora) == ("2021-11-21", "21 de noviembre, 17:00",
                                                "17:00")
    assert p.visita == "Defensores Unidos", "el `|` del enlace no es un parametro"


def test_un_parametro_comentado_no_existe():
    """La Primera C 2025 deja comentadas las patadas de dos tandas, con el `|` de
    cada parametro adentro del comentario. MediaWiki no lo renderiza, asi que un
    parametro comentado no puede pisar al de verdad."""
    texto = ("{{Partido\n|local = Boca Juniors\n|resultado = 0:0\n|visita = River Plate\n"
             "|fecha = 12 de diciembre, 17:00\n|estadio = La Bombonera\n"
             "|resultado penalti = 4:5\n"
             "<!--|estadio = Estadio Monumental\n|resultado penalti = 9:8-->\n"
             "|árbitro=[[Alguien]]}}")
    (p,) = parser.partidos_de_plantillas(texto, 2021, "x")
    assert p.estadio == "La Bombonera"
    assert (p.penales_local, p.penales_visita) == (4, 5)


def test_una_nota_comentada_no_dice_que_se_jugo_otro_dia():
    """Lo comentado no lo dice la pagina, tampoco para la nota: un `suceso` que un
    editor dejo comentado no puede vaciar la hora de `fecha`."""
    texto = ("{{Partido\n|local = Boca Juniors\n|resultado = 1:0\n|visita = River Plate\n"
             "|fecha = 15 de junio, 15:00\n"
             "<!--|suceso = Suspendido. Se jugó el 22 de junio.-->\n"
             "|árbitro=[[Alguien]]}}")
    (p,) = parser.partidos_de_plantillas(texto, 2019, "x")
    assert (p.fecha, p.hora) == ("2019-06-15", "15:00")


def test_dos_comentarios_no_se_llevan_lo_que_hay_entre_ellos():
    """Un comentario termina en el PRIMER `-->`. De un `<!--` al ultimo `-->` se iban
    `resultado` y la plantilla entera con el."""
    texto = ("{{Partido\n|local = Boca Juniors <!-- el local -->\n|resultado = 2:1\n"
             "|visita = River Plate <!-- la visita -->\n|fecha = 21 de diciembre, 17:00\n}}")
    (p,) = parser.partidos_de_plantillas(texto, 2021, "x")
    assert (p.local, p.goles_local, p.goles_visita, p.visita) == (
        "Boca Juniors", 2, 1, "River Plate")


def test_un_enlace_sin_cerrar_no_se_traga_los_parametros_que_siguen():
    """Partir por `|` a nivel cero cuenta los `[[`, y uno que no cierra dejaba todo lo
    que venia despues pegado a su parametro. Antes de `resultado`, el partido se
    descartaba sin aviso; despues, se perdian la fecha y la cancha. Partiendo por
    renglon los dos se leian, y un wikilink no cruza un renglon de parametro."""
    antes = ("{{Partido\n|local = Boca Juniors\n|árbitro = [[Fulano\n|resultado = 2:1\n"
             "|visita = River Plate\n|fecha = 21 de diciembre, 17:00\n|estadio = La Bombonera\n}}")
    (p,) = parser.partidos_de_plantillas(antes, 2021, "x")
    assert (p.local, p.goles_local, p.goles_visita, p.visita) == (
        "Boca Juniors", 2, 1, "River Plate")
    assert (p.fecha, p.hora, p.estadio) == ("2021-12-21", "17:00", "La Bombonera")
    despues = ("{{Partido\n|local = Boca Juniors\n|resultado = 2:1\n|visita = River Plate\n"
               "|goleslocal = [[Fulano {{gol|3}}\n|fecha = 21 de diciembre, 17:00\n"
               "|estadio = La Bombonera\n}}")
    (p,) = parser.partidos_de_plantillas(despues, 2021, "x")
    assert (p.fecha, p.hora, p.estadio) == ("2021-12-21", "17:00", "La Bombonera")


def test_el_respaldo_tambien_vale_con_los_parametros_indentados():
    """Las Copas de la Liga 2021 a 2023 indentan los parametros (`\\n  |local=`): el
    renglon de parametro se reconoce igual con espacios antes del `|`."""
    texto = ("{{Partido\n  |local = Boca Juniors\n  |árbitro = [[Fulano\n  |resultado = 2:1\n"
             "  |visita = River Plate\n  |fecha = 21 de diciembre, 17:00\n}}")
    (p,) = parser.partidos_de_plantillas(texto, 2021, "x")
    assert (p.local, p.goles_local, p.goles_visita, p.visita, p.hora) == (
        "Boca Juniors", 2, 1, "River Plate", "17:00")


def test_una_cita_en_varios_renglones_no_parte_la_plantilla():
    """El respaldo de arriba reinicia los `[[` y NO las llaves: una `{{Cita web}}` en
    varias lineas trae su propio `|fecha=`, y cortando ahi pisaba la del partido."""
    texto = ("{{Partido\n|local = Boca Juniors\n|resultado = 2:1\n|visita = River Plate\n"
             "|fecha = 21 de diciembre, 17:00\n"
             "|suceso = Postergado.<ref>{{Cita web\n|url=http://x.com/nota\n"
             "|fecha=1 de enero de 2020\n|título=La nota}}</ref>\n}}")
    (p,) = parser.partidos_de_plantillas(texto, 2021, "x")
    assert (p.fecha, p.hora) == ("2021-12-21", "17:00")


def test_una_seccion_que_no_es_del_torneo_no_puede_ser_la_llave():
    """El Campeonato Transicion de Primera Nacional 2020 abre `== Entrenadores ==`
    y cuelga de ahi su `=== Etapa eliminatoria ===`, asi que sus 18 partidos de
    eliminacion salian con la llave "Entrenadores". No rompe el CSV -- `llave` no
    se exporta -- pero `validar` agrupa por ella y arma un cuadro que no existe.
    """
    texto = ("== Fase segundo ascenso ==\n\ntexto\n\n"
             "== Entrenadores ==\n\nuna tabla de DT\n\n"
             "=== Etapa eliminatoria ==\n\nAQUI\n")
    assert parser._contexto(texto.index("AQUI"), 3, texto) == "Fase segundo ascenso"


def test_y_si_no_hay_seccion_de_torneo_antes_la_llave_queda_vacia():
    """Vacio es lo honesto: mejor sin llave que con una inventada."""
    texto = "== Goleadores ==\n\n=== Etapa eliminatoria ==\n\nAQUI\n"
    assert parser._contexto(texto.index("AQUI"), 3, texto) == ""


# --- la tabla de llaves de dos patas -------------------------------------

_LLAVE_2004 = """{| cellspacing="0" width=100%
|+ align="center" style="background: #006699"|'''Tercera ronda 8/12 - 12/12'''
|- bgcolor=#006699
!width=24%|Local - Ida
!width=24%|Local - Vuelta
!Ida
!Vuelta
|- align=center
| Gimnasia y Tiro (S)
|  '''Atlético (T)'''
|4 - 0
|2<small>(2)</small> - 6<small>(4)</small>
|}"""

# El mismo formato con OTRO orden y una columna de mas, que es como lo escriben
# el Argentino A 2011-12 y el 2012-13.
_LLAVE_2011 = """{| cellspacing="0" width=70%
|+ align="center" style="background: #dcdcdc"|'''Reválida - Segunda ronda - 22 al 29 de abril'''
|- bgcolor=#dcdcdc
!width=22%|Local - Vuelta
!width=10%|Global
!width=22%|Local - Ida
!width=10%|Ida
!width=10%|Vuelta
|- align=center
|align=right| Cipolletti
|2 - 4
|align=left| '''Libertad (Sunchales)'''
|0 - 2
|2 - 2
|}"""


def test_una_llave_de_dos_patas_da_dos_partidos_con_su_localia_cruzada():
    """La localia no esta en la celda: esta en el SIGNIFICADO de la columna.

    Una columna dice quien fue local en la ida y otra quien lo fue en la vuelta,
    asi que los dos partidos salen de la misma fila cruzados. Leerla como una
    tabla comun le daria la localia al mismo club las dos veces, que es un error
    que no rompe nada y miente en silencio.
    """
    ps = parser.partidos_de_llave(_LLAVE_2004, 2004, "Torneo Argentino A",
                                  anio_fin=2005)
    assert [(p.local, p.visita) for p in ps] == [
        ("Gimnasia y Tiro (S)", "Atlético (T)"),
        ("Atlético (T)", "Gimnasia y Tiro (S)")]
    assert [p.fecha for p in ps] == ["2004-12-08", "2004-12-12"]
    assert [p.jornada for p in ps] == ["Tercera ronda"] * 2


def test_el_marcador_va_en_el_orden_de_las_columnas_y_no_local_visitante():
    """Las dos celdas dicen "goles del club de la izquierda - goles del otro".

    En la pata donde ese club es VISITANTE hay que darlas vuelta, y no es un
    detalle: sin eso, esta misma llave entra como "Atletico Tucuman 2-6 con
    penales 2-4", un partido con penales que no fue empate. Dada vuelta cierra
    sola -- la vuelta fue 6-2, el global 6-6 -- y ademas coincide con quien la
    pagina pone en negrita, que es el que paso.
    """
    ida, vuelta = parser.partidos_de_llave(_LLAVE_2004, 2004, "Torneo Argentino A",
                                           anio_fin=2005)
    assert (ida.goles_local, ida.goles_visita) == (4, 0)
    assert (vuelta.goles_local, vuelta.goles_visita) == (6, 2)
    assert (vuelta.penales_local, vuelta.penales_visita) == (4, 2)
    assert ida.penales_local is None


def test_las_columnas_se_leen_del_encabezado_y_no_por_su_posicion():
    """El 2004-05 ordena `Local - Ida | Local - Vuelta | Ida | Vuelta` y el
    2011-12 pone cinco columnas al reves. Leyendo por posicion, los marcadores
    entraban como nombres de club y tres temporadas se llenaban de clubes que no
    existen."""
    ps = parser.partidos_de_llave(_LLAVE_2011, 2011, "Torneo Argentino A",
                                  anio_fin=2012)
    assert [(p.local, p.visita, p.goles_local, p.goles_visita) for p in ps] == [
        ("Libertad (Sunchales)", "Cipolletti", 2, 0),
        ("Cipolletti", "Libertad (Sunchales)", 2, 2)]
    # El global que publica la propia tabla, 2-4 a favor de Libertad, tiene que
    # salir de sumar las dos patas.
    assert sum(p.goles_visita if p.local == "Libertad (Sunchales)" else p.goles_local
               for p in ps) == 2
    # Y SIN FECHA, porque el titulo de esa tabla es "Revalida - Segunda ronda -
    # 22 al 29 de abril": un RANGO. Que en esta llave los dos extremos resulten
    # ser los dias buenos es una casualidad que la pagina no afirma -- en la
    # Cuarta fase de la misma pagina, "26 al 31 de mayo", de ocho patas solo tres
    # caian bien --. La fecha de verdad la pone despues la fuente que publica
    # partido por partido. Ver `test_un_rango_en_el_titulo_no_fecha_nada`.
    assert [p.fecha for p in ps] == ["", ""]


def _tabla_con_notas(*filas: str) -> str:
    """Una tabla de resultados con las seis columnas de siempre."""
    return ('{| class="wikitable"\n!Local\n!Resultado\n!Visitante\n!Estadio\n'
            "!Fecha\n!Hora\n|-\n" + "\n|-\n".join(filas) + "\n|}")


_ARMENIO = ("|Deportivo Armenio\n|1 - 1\n|Cañuelas\n|Armenia\n"
            '|11 de noviembre{{refn|group="n."|name="susp"}}\n|15:30')
_QUILMES = ("|Argentino de Quilmes\n|1 - 0\n|Sportivo Italiano\n|Argentino de Quilmes\n"
            '|11 de noviembre{{refn|group="n."|name="susp"|Suspendido por las '
            "condiciones climáticas. Se jugó el 28 de noviembre, a partir de las "
            '17:00.}}\n|12:00')


def test_una_nota_definida_una_vez_alcanza_a_las_filas_que_la_REFERENCIAN():
    """MediaWiki deja definir una nota una vez y despues referenciarla sola por
    nombre. Al renderizar las dos filas muestran el mismo texto; en el wikitexto
    crudo, la segunda trae `{{refn|group="n."|name="susp"}}` y no dice nada.

    Es la MISMA FORMA que el `rowspan` --una nota, varias filas, una sola con el
    texto-- por otro mecanismo. La Primera C 2018-19 fechaba a Deportivo Armenio
    el 11 de noviembre y a Argentino de Quilmes el 28, con la misma nota y en la
    misma jornada, diecisiete dias de diferencia.
    """
    ps = parser.partidos(_tabla_con_notas(_QUILMES, _ARMENIO), 2018, "Primera C")
    assert [p.fecha for p in ps] == ["2018-11-28"] * 2,         "las dos filas comparten la nota, asi que comparten el dia"


def test_la_REFERENCIA_puede_venir_antes_que_la_definicion():
    """El orden de las filas no puede decidir la fecha. Se juntan las notas de la
    pagina entera ANTES de leer ninguna fila, justamente para eso."""
    ps = parser.partidos(_tabla_con_notas(_ARMENIO, _QUILMES), 2018, "Primera C")
    assert [p.fecha for p in ps] == ["2018-11-28"] * 2, ps


def test_las_notas_se_juntan_de_la_PAGINA_y_no_de_la_tabla():
    """Definicion y referencia no tienen por que caer en la misma tabla, y desde
    adentro de una tabla la nota referenciada es indistinguible de una que no
    existe. Es la misma razon por la que `_zonas_ambiguas` se calcula una vez."""
    pagina = (_tabla_con_notas(_QUILMES) + "\n\n== Otra fecha ==\n"
              + _tabla_con_notas(_ARMENIO))
    ps = parser.partidos(pagina, 2018, "Primera C")
    assert sorted(p.fecha for p in ps) == ["2018-11-28"] * 2, ps


def test_una_referencia_que_la_pagina_NO_define_se_deja_como_esta():
    """No se inventa. Son 3 de las 31 referencias por nombre del corpus, y apuntan
    a notas de OTRO articulo: lo unico honesto es dejar la fila con su dia."""
    solo = '|11 de noviembre{{refn|group="n."|name="no-existe"}}'
    assert parser._con_notas(solo, {"otra": "Se jugó el 28 de noviembre"}) == solo
    ps = parser.partidos(_tabla_con_notas(_ARMENIO), 2018, "Primera C")
    assert [p.fecha for p in ps] == ["2018-11-11"], "sin cuerpo, manda la celda"


def test_una_nota_que_es_SOLO_referencia_no_se_toma_por_definicion():
    """Si una referencia pelada entrara al diccionario, su cuerpo vacio taparia a
    la definicion de verdad -- y con `setdefault`, si ademas viene primero, la
    tapa para siempre. Por eso se exige que tenga cuerpo."""
    texto = _tabla_con_notas(_ARMENIO, _QUILMES)
    assert parser.notas_con_nombre(texto) == {
        "susp": "Suspendido por las condiciones climáticas. Se jugó el 28 de "
                "noviembre, a partir de las 17:00."}


def test_si_la_pagina_define_dos_veces_el_mismo_nombre_manda_la_PRIMERA():
    """Que es lo que hace MediaWiki. Importa poco cual gane y mucho que no
    dependa del orden en que el parser recorra la pagina."""
    doble = ('{{refn|group=n.|name=x|Se jugó el 3 de mayo.}} '
             '{{refn|group=n.|name=x|Se jugó el 9 de mayo.}}')
    assert "3 de mayo" in parser.notas_con_nombre(doble)["x"]


_COLEGIALES = ("|Colegiales\n|0 - 1\n|Deportivo Merlo\n|Colegiales\n"
               '|6 de septiembre<ref name="suspendido">Suspendido debido a la lluvia. '
               "Se jugó el 24 de septiembre.</ref>\n|11:00")
_VILLA_SAN_CARLOS = ("|Villa San Carlos\n|2 - 0\n|UAI Urquiza\n|Genacio Sálice\n"
                     '|6 de septiembre<ref name="suspendido" />\n|11:00')


def test_la_nota_escrita_con_la_etiqueta_tambien_se_referencia_por_nombre():
    """La otra forma de MediaWiki: `<ref name="x">...</ref>` una vez y `<ref name="x" />`
    despues. La Fecha 8 de la Primera B 2014 la define en `Colegiales - Deportivo Merlo`
    y `Villa San Carlos - UAI Urquiza` la referencia: quedaba el 6, el dia de la lluvia,
    y se jugo el 24 (Diario Hoy, 25/09/2014: «el encuentro pendiente de la fecha
    ocho»)."""
    for orden in ((_COLEGIALES, _VILLA_SAN_CARLOS), (_VILLA_SAN_CARLOS, _COLEGIALES)):
        ps = parser.partidos(_tabla_con_notas(*orden), 2014, "Primera B")
        assert [p.fecha for p in ps] == ["2014-09-24"] * 2, orden


@pytest.mark.parametrize("referencia", [
    '<ref name="susp" />', "<ref name=susp/>", "<ref name='susp' />",
    '<ref group="n." name="susp" />', '<ref name="susp" group="n."/>'])
def test_la_referencia_con_etiqueta_se_lee_en_todas_sus_formas(referencia):
    notas = {"susp": "Se jugó el 24 de septiembre."}
    assert "Se jugó el 24 de septiembre." in parser._con_notas(referencia, notas)


def test_la_referencia_con_etiqueta_que_la_pagina_no_define_se_deja_como_esta():
    sola = '|6 de septiembre<ref name="otra" />'
    assert parser._con_notas(sola, {"susp": "Se jugó el 24 de septiembre."}) == sola


def test_la_etiqueta_pelada_no_tapa_a_la_definicion_que_viene_despues():
    """Igual que con `{{refn}}`: la referencia no tiene cuerpo, y si entrara al
    diccionario le ganaria a la definicion por venir antes."""
    texto = ('<ref name="x" /> y despues <ref name="x">Se jugó el 3 de mayo.</ref>')
    assert parser.notas_con_nombre(texto) == {"x": "Se jugó el 3 de mayo."}


def test_entre_las_dos_formas_manda_la_primera_DE_LA_PAGINA():
    """El mismo nombre definido con la etiqueta y con `{{refn}}`: manda el que aparece
    antes, como en MediaWiki, y no el de la forma que se junte primero."""
    texto = ('<ref name="x">Se jugó el 3 de mayo.</ref> '
             '{{refn|group=n.|name=x|Se jugó el 9 de mayo.}}')
    assert "3 de mayo" in parser.notas_con_nombre(texto)["x"]


def test_la_nota_de_una_celda_con_rowspan_alcanza_a_todas_sus_filas():
    """Cuando se suspende una tanda entera, la nota cuelga de UNA celda que abarca
    a las tres filas -- y por eso habla en plural.

    El lector la buscaba solo en el texto de la fila, asi que la PRIMERA del grupo
    quedaba con el dia que se jugo y las otras dos con el programado: el mismo
    partido de la misma tanda, fechado con diez dias de diferencia segun donde
    cayera. Es el caso de la fecha 7 de la Primera C 2024, suspendida por el
    temporal del 12 de marzo y jugada el 22.

    Se midio sobre el corpus: son 65 filas, y las 65 tienen una nota de la propia
    pagina que dice exactamente el dia al que se movieron.
    """
    tabla = """{| class="wikitable"
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Juventud Unida
|1 - 2
|Defensores de Cambaceres
|Ciudad de San Miguel
|rowspan=3|12 de marzo {{refn|group=n.|Suspendidos por el temporal. Se jugaron el 22 de marzo, desde las 15:30.}}
|rowspan=3|17:00
|-
|Lugano
|0 - 2
|Argentino de Rosario
|José María Moraños
|-
|Puerto Nuevo
|2 - 2
|Real Pilar
|Rubén Carlos Vallejos
|}"""
    ps = parser.partidos_de_tabla(tabla, 2024, "Primera C")
    assert len(ps) == 3
    assert [p.fecha for p in ps] == ["2024-03-22"] * 3, \
        "las tres filas son de la misma celda y de la misma nota"


def test_sin_nota_la_celda_con_rowspan_manda_igual():
    """La contracara: sin nota, la fecha de la celda sigue siendo la de las tres.
    El arreglo no puede convertirse en 'buscar cualquier fecha en cualquier lado'."""
    tabla = """{| class="wikitable"
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
|-
|Juventud Unida
|1 - 2
|Defensores de Cambaceres
|Ciudad de San Miguel
|rowspan=2|12 de marzo
|rowspan=2|17:00
|-
|Lugano
|0 - 2
|Argentino de Rosario
|José María Moraños
|}"""
    ps = parser.partidos_de_tabla(tabla, 2024, "Primera C")
    assert [p.fecha for p in ps] == ["2024-03-12", "2024-03-12"]


def test_un_rango_en_el_titulo_no_fecha_nada():
    """`X al Y` es una VENTANA, no dos dias de partido.

    El lector pedia "exactamente dos dias" y un rango nombra exactamente dos, asi
    que pasaba: a "Cuarta fase - 26 al 31 de mayo" le ponia el 26 a las cuatro
    idas y el 31 a las cuatro vueltas. Los dias reales de esas cuatro llaves
    fueron 26, 26, 27 y 28 las idas y 30, 30, 30 y 31 las vueltas -- el blog de
    Jose Carluccio las publica una por una, con sede y goleadores --, o sea que
    tres de ocho caian bien y cinco llevaban un dia que nadie observo.

    La preposicion es lo unico que los separa y los separa sin ambiguedad: `al`
    abre un rango, `y` enumera. Medido sobre el corpus: de los 13 titulos de
    llave que fechaban, los 7 que enumeran son del Argentino A 2004-05, cuya
    pagina no tiene ni un desacuerdo de fecha contra las otras fuentes; los 6 que
    dicen `al` son de donde salian casi todos.
    """
    def tabla(titulo):
        return ("""{| cellspacing="0"
|+ align="center"|'''%s'''
|- bgcolor=#dcdcdc
!Local - Vuelta
!Global
!Local - Ida
!Ida
!Vuelta
|- align=center
|align=right| Cipolletti
|2 - 4
|align=left| Libertad (Sunchales)
|0 - 2
|2 - 2
|}""" % titulo)

    con_rango = parser.partidos_de_llave(tabla("Cuarta fase - 26 al 31 de mayo"),
                                         2011, "Torneo Argentino A", anio_fin=2012)
    assert len(con_rango) == 2
    assert [p.fecha for p in con_rango] == ["", ""], "un rango no se reparte"

    # y la forma que SI enumera dos dias se sigue leyendo
    enumerados = parser.partidos_de_llave(tabla("Cuarta fase - 2 y 9 de junio"),
                                          2011, "Torneo Argentino A", anio_fin=2012)
    assert [p.fecha for p in enumerados] == ["2012-06-02", "2012-06-09"]


def test_el_rango_se_saca_del_nombre_de_la_ronda_igual():
    """Que no se pueda fechar no quiere decir que se pierda la ronda: sin limpiar
    el rango, `Cuarta fase - 26 al 31 de mayo` no la reconoce nadie y la pagina
    entera se queda sin revisar la cadena de llaves."""
    assert parser._sin_el_rango("Cuarta fase - 26 al 31 de mayo") == "Cuarta fase"
    assert parser._sin_el_rango("Reválida - Segunda ronda - 22 al 29 de abril") \
        == "Reválida - Segunda ronda"


def test_una_tabla_comun_con_columna_global_no_se_desvia_al_lector_de_llaves():
    """`Ida`, `Vuelta` y `Global` son nombres de columna que aparecen tambien en
    tablas normales. Si el desvio se decidiera por el encabezado y no por lo que
    el lector devuelve, un `continue` de mas se llevaria sus partidos sin avisar."""
    tabla = """{| class="wikitable"
!Local
!Global
!Visitante
|-
|Boca Juniors
|1 - 0
|River Plate
|}"""
    assert parser.partidos_de_llave(tabla, 2024, "Primera") == []


# --------------------------------------------------------------------------
# Las tres formas en que una pagina numera sus rondas
# --------------------------------------------------------------------------
def _rondas(texto):
    return [n for _, n in parser._titulos_de_ronda(texto)]


def test_la_ronda_se_lee_escrita_fase_ronda_o_instancia():
    """Tres formas para lo mismo, y las tres tienen que entrar POR EL PARSER.

    Que `validar` supiera que "primera ronda" es "primera fase" no alcanzaba: si
    el parser no reconoce el titulo, el partido sale con la jornada vacia y no
    hay nada que normalizar despues. Asi salia el Campeonato Transicion de
    Primera B 2020, que escribe `==== Primera ronda ====` y publicaba sus tres
    partidos sin ronda ninguna.
    """
    assert _rondas("== Primera fase ==") == ["Primera fase"]
    assert _rondas("== Primera ronda ==") == ["Primera ronda"]
    assert _rondas("==== Primera instancia ====") == ["Primera instancia"]


def test_las_cuatro_instancias_del_transicion_2020():
    """El Transicion de Primera Nacional 2020 numera asi la fase por el segundo
    ascenso. Eran 15 partidos con el `matchday` vacio en el CSV."""
    tx = ("==== Primera instancia ====\n==== Segunda instancia ====\n"
          "==== Tercera instancia ====\n==== Semifinales ====\n==== Final ====\n")
    assert _rondas(tx) == ["Primera instancia", "Segunda instancia",
                           "Tercera instancia", "Semifinales", "Final"]


def test_la_cuarta_y_la_quinta_fase_tambien_son_rondas():
    """Estaban en `RONDAS` pero no en los titulos que el parser mira, asi que el
    Federal A 2024 y 2025 publicaban esos partidos sin ronda."""
    assert _rondas("== Cuarta fase ==\n== Quinta fase ==") == ["Cuarta fase", "Quinta fase"]


def test_un_titulo_que_no_es_una_ronda_no_entra():
    """El testigo: si el vocabulario se abriera de mas, cualquier seccion pasaria
    a ser una ronda y el cuadro se llenaria de rondas inventadas."""
    assert _rondas("== Entrenadores ==\n== Goleadores ==\n== Equipos participantes ==") == []

def test_el_fallo_se_lee_con_el_le_y_SIN_el_le():
    """`se le dio por perdido` y `se dio por perdido` son la misma cosa, y el segundo
    no se leia: `_HABLA_DE_FALLO` lo detectaba y `_HUBO_FALLO` no lo clasificaba, asi
    que la fila caia en `sin_clasificar` -- que es el aviso de "la pagina dijo algo y
    no se supo que", el unico caso en que el vacio seria una afirmacion inventada.

    Es una sola fila en el dataset: el Velez-Boca del Clausura 1993, que la pagina
    anota `Originalmente el partido finalizo 1-1. Sin embargo, se dio por perdido el
    partido a Boca Juniors por no presentarse un jugador al control antidoping`.
    Llego al final, asi que es `escritorio` y no `suspendido`."""
    con_le = "|1 - 0 se le dio por perdido el partido a Boca Juniors"
    sin_le = "|1 - 0 se dio por perdido el partido a Boca Juniors"
    assert parser.status_de_la_fila(con_le) == "escritorio"
    assert parser.status_de_la_fila(sin_le) == "escritorio"
    assert not parser.sin_clasificar(sin_le), "la pagina dijo algo y se supo que"


def test_una_suspension_le_gana_al_fallo_aunque_el_fallo_se_lea():
    """El contraste que sostiene al de arriba. Las otras tres filas del dataset que
    dicen `dio por ganado/perdido` sin `le` mencionan ademas una suspension, y tienen
    que seguir siendo `suspendido`: el eje de esta columna es si el partido LLEGO AL
    FINAL, y eso manda sobre quien se quedo con los puntos."""
    fila = ("|7 de abril Suspendido a los 46' del segundo tiempo con el resultado "
            "2 a 2, por invasion del campo. Se dio por ganado a Central Cordoba")
    assert parser.status_de_la_fila(fila) == "suspendido"


def test_el_fallo_se_lee_con_el_objeto_en_el_medio():
    """`le dio el partido perdido a Central Córdoba`: el mismo fallo de siempre con el
    objeto metido entre el verbo y el participio, y sin el `por`. `_HABLA_DE_FALLO` lo
    detectaba --dice "Tribunal"-- y `_HUBO_FALLO` no lo clasificaba, asi que la fila
    caia en `sin_clasificar`.

    Es una fila: el `Central Córdoba (SdE) 0-1 San Martín (T)` del Torneo Federal A
    2014. Se jugo entero y termino 1-1 --RSSSF: `originally 1-1, awd on Oct 16`--, asi
    que es `escritorio`."""
    fila = ('|Central Córdoba (SdE)\n|0 - 1<ref group="n.">El Tribunal de Disciplina le '
            'dio el partido perdido a Central Córdoba por estar inhabilitado un jugador '
            'del local.</ref>\n|San Martín (T)')
    assert parser.status_de_la_fila(fila) == "escritorio"
    assert not parser.sin_clasificar(fila), "la pagina dijo algo y se supo que"
    # El contraste: la misma frase detras de una suspension sigue siendo `suspendido`.
    # Es el Deportivo Laferrere - Dock Sud de la Primera C 2015.
    suspendido = ("|Deportivo Laferrere\n|2 - 2{{refn|group=n.|Suspendido por incidentes "
                  "fuera del estadio. El Tribunal de Disciplina le dio el partido perdido "
                  "a Deportivo Laferrere por 1 a 0 y mantuvo el resultado para Dock "
                  "Sud.}}\n|Dock Sud")
    assert parser.status_de_la_fila(suspendido) == "suspendido"


_REPROGRAMADO_2014 = (
    '|General Belgrano (SR)\n|1 - 2\n|CAI\n|Nuevo Rancho Grande\n|6 de octubre'
    '<ref group="n.">Suspendido debido a la lluvia. Fue reprogramado para el 6 de '
    'octubre a partir de las 14:00.</ref>')


def test_el_partido_reprogramado_no_lleva_status_si_la_fila_esta_fechada_ese_dia():
    """`Fue reprogramado para el 6 de octubre` es un plan, y vale como «se jugo» porque
    la celda de la fecha dice ese mismo dia: la fila ya esta puesta donde la nota dice
    que se paso. Sin esto salia `suspendido`, que afirma que no llego al final. Es el
    `General Belgrano (SR) 1-2 CAI` del Torneo Federal A 2014, que RSSSF da jugado el
    06/10/2014 sin ninguna nota."""
    assert parser.status_de_la_fila(_REPROGRAMADO_2014) == ""
    assert not parser.sin_clasificar(_REPROGRAMADO_2014)
    # La conjugacion no importa: lo que vale es que el dia sea el de la fila.
    otra = _REPROGRAMADO_2014.replace("Fue reprogramado", "Se reprogramó")
    assert parser.status_de_la_fila(otra) == ""


def test_un_plan_que_no_es_el_dia_de_la_fila_no_alcanza():
    """El `Villa Mitre 2-1 Guillermo Brown` del Federal A 2025: la celda dice 11, la
    nota "reprogramado para el 12", y el 12 se volvio a suspender. La nota real sigue
    con `Se jugó el 13`, y eso es lo unico que le saca el `suspendido`: cortada antes,
    el plan solo no alcanza."""
    cortada = ('|Villa Mitre\n|2 - 1\n|Guillermo Brown\n|El Fortín (BB)\n|11 de octubre'
               '{{refn|group=n.|Suspendido por las condiciones climáticas. Fue reprogramado '
               'para el 12 de octubre, a partir de las 11:00, y se volvió a suspender por el '
               'estado del campo de juego.}}')
    assert parser.status_de_la_fila(cortada) == "suspendido"
    entera = cortada.replace("de juego.}}", "de juego. Se jugó el 13 de octubre, desde las 11:00.}}")
    assert parser.status_de_la_fila(entera) == ""
    # Y el dia tiene que ser el mismo entero: 6 no es 16.
    el_16 = _REPROGRAMADO_2014.replace("para el 6 de octubre", "para el 16 de octubre")
    assert parser.status_de_la_fila(el_16) == "suspendido"


def test_un_plan_cumplido_que_termino_de_otra_manera_no_alcanza():
    """La fila esta fechada el dia del plan, pero la nota sigue y cuenta otro final. Ahi
    no se puede decir que llego al final: vuelve a mandar lo que la nota dice primero."""
    con_cola = _REPROGRAMADO_2014.replace(
        "a partir de las 14:00.",
        "pero el equipo visitante no se presentó y el Tribunal le dio el partido por perdido.")
    assert parser.status_de_la_fila(con_cola) == "suspendido"


def test_la_url_de_una_cita_no_es_texto_de_la_nota():
    """El slug de un enlace externo trae la palabra y la nota dice otra cosa: el
    `Sportivo Estudiantes (SL) 2-0 Juventud Unida Universitario` del Torneo Federal A
    2014 fue POSTERGADO, y el `suspendido` salia de la direccion de la cita."""
    fila = ("|Sportivo Estudiantes (SL)\n|2 - 0\n|Juventud U. U.\n|Juan Gilberto Funes\n"
            "|6 de octubre<ref>[http://www.ascensodelinterior.com.ar/noticias/10541/"
            "el-clsico-puntano-fue-suspendido/ Postergado por falta de acuerdo para jugar "
            "con ambas parcialidades.]</ref>")
    assert parser.status_de_la_fila(fila) == ""
    assert not parser.sin_clasificar(fila), "y tampoco es un fallo sin leer"
    # El contraste: la misma palabra en el TEXTO de la nota si cuenta.
    en_el_texto = fila.replace("Postergado por falta", "Suspendido a los 10' por falta")
    assert parser.status_de_la_fila(en_el_texto) == "suspendido"


def test_el_detector_lee_el_mismo_texto_que_el_status():
    """`sin_clasificar` pregunta sobre el texto de la nota, igual que `status_de_la_fila`.
    Si leyera la fila cruda, una palabra que solo esta en una direccion --aca
    `tribunal`, en el slug-- haria sonar el aviso de "la pagina hablo de un fallo"
    sobre una nota que solo enlaza una cronica."""
    fila = ("|A\n|1 - 0\n|B<ref>[http://www.ascensodelinterior.com.ar/noticias/1/"
            "el-tribunal-de-disciplina/ Crónica del partido]</ref>")
    assert parser.status_de_la_fila(fila) == ""
    assert not parser.sin_clasificar(fila)


# --------------------------------------------------------------------------
# status: las formas que se leen
# --------------------------------------------------------------------------
# Una nota por cada forma que aceptan los regex del status, con el status que tiene
# que salir. Sacarle una alternativa a cualquiera de los cuatro --`_NO_LLEGO_AL_FINAL`,
# `_HUBO_FALLO`, `_SE_COMPLETO` y `_HABLA_DE_FALLO`-- cambia al menos una de estas
# filas: es lo que fija sus formas. Antes no habia nada asi, y de 35 mutantes que les
# sacaban una alternativa sobrevivian 33.
#
# Van con tilde donde la pagina la pone: los regex estan escritos sin tildes y se
# preguntan sobre el texto sin tildes, asi que estas mismas notas fijan eso tambien.
_FORMAS = [
    # no llego al final
    ("Suspendido a los 37' del segundo tiempo.", "suspendido"),
    ("El visitante abandonó la cancha a los 30'.", "suspendido"),
    ("El visitante no se presentó a jugar el segundo tiempo.", "suspendido"),
    ("Interrumpido a los 80' por la lluvia.", "suspendido"),
    # llego al final y el numero lo puso un fallo
    ("Finalizó 1 a 1. Se le dio por perdido a Boca Juniors.", "escritorio"),
    ("Finalizó 1 a 1. Se dio por ganado a Atlanta.", "escritorio"),
    ("Finalizó 1 a 1. Se dio por perdido a Colegiales.", "escritorio"),
    ("El resultado fue 1 a 1 pero se lo dio por ganado a Sarmiento.", "escritorio"),
    ("El resultado fue 1 a 1 pero se lo dio ganado a Sarmiento.", "escritorio"),
    ("Finalizó 1 a 1. El Tribunal le dio por ganado a Sarmiento.", "escritorio"),
    ("Finalizó 1 a 1. Le dio la victoria a Huracán, otorgándole los puntos.", "escritorio"),
    ("Independiente le ganó los puntos a Alianza.", "escritorio"),
    ("Finalizó 1 a 1, por mala inclusión de un jugador.", "escritorio"),
    ("Finalizó 1 a 1, por indebida inclusión de un jugador.", "escritorio"),
    ("Finalizó 1 a 1, por inclusión indebida de un jugador.", "escritorio"),
    ("El Tribunal le dio el partido perdido a Central Córdoba.", "escritorio"),
    ("El Tribunal le dio el partido por ganado a San Martín.", "escritorio"),
    # se suspendio y se termino de jugar otro dia
    ("Suspendido por lluvia. Se jugó el 15 de noviembre.", ""),
    ("Suspendidos por lluvia. Se jugaron el 17 de abril.", ""),
    ("Suspendido por lluvia. Se juega el 3 de octubre.", ""),
    ("Suspendidos por lluvia. Se juegan el 3 de octubre.", ""),
    ("Suspendido por lluvia. Se jugará el 2 de diciembre.", ""),
    ("Suspendidos por lluvia. Se jugarán el 2 de diciembre.", ""),
    ("Suspendido por lluvia. Se disputó el 15 de noviembre.", ""),
    ("Suspendidos por lluvia. Se disputaron el 15 de noviembre.", ""),
    ("Suspendido a los 20'. Se completó el 5 de marzo.", ""),
    ("Suspendido a los 20'. Se reanudó el 5 de marzo.", ""),
    ("Suspendido a los 20'. Se finalizó el 5 de marzo.", ""),
    ("Suspendido a los 20'. Se completó 5 de marzo.", ""),
    # «Se compĺetó», con una `ĺ`: el `Brown de Adrogué 0-0 Agropecuario` de la Primera B
    # Nacional 2018-19. InfoRegion, 27/11/2018: «disputará los 41 minutos restantes».
    ("Suspendido por las condiciones climáticas a los 4' del segundo tiempo, con el "
     "resultado 0-0. Se compĺetó el 28 de noviembre, a partir de las 17:00.", ""),
    # «Se le dió», con tilde: el `Real Arroyo Seco 0-1 Gimnasia y Esgrima (CdU)` del
    # Argentino A 2004-05. RSSSF: `originally 3-0 but Real Arroyo Seco used ineligible
    # players`.
    ("El partido terminó 3 a 0, pero fue anulado por la inclusión por parte de Arroyo "
     "Seco de jugadores no elegibles. Se le dió por ganado a Gimnasia y Esgrima por 1 a 0",
     "escritorio"),
]


@pytest.mark.parametrize("nota, status", _FORMAS)
def test_cada_forma_del_status_se_lee(nota, status):
    fila = "|A\n|1 - 0\n|B<ref>" + nota + "</ref>"
    assert parser.status_de_la_fila(fila) == status
    assert not parser.sin_clasificar(fila), "se leyo, asi que no se avisa"


# Lo que el detector tiene que ver aunque el status no sepa que poner: cada una es una
# forma de `_HABLA_DE_FALLO` que ninguna otra pregunta lee.
@pytest.mark.parametrize("nota", [
    "Los jugadores abandonaron la cancha.",
    "Los dos equipos no se presentan desde la fecha 3.",
    "El Tribunal resolvió algo raro.",
    "Se le dio por concluido.",
    "Lo dio por ganado a Atlanta.",
    "Lo dio por perdido a Colón.",
    "Se dio por terminado.",
    "Se dio por finalizado.",
    "Quedó así, dándolo por bueno.",
    "AFA decide darle por perdido 0-2 a San Martín de Tucumán frente a Alumni",
])
def test_cada_forma_del_detector_avisa(nota):
    fila = "|A\n|1 - 0\n|B<ref>" + nota + "</ref>"
    assert parser.status_de_la_fila(fila) == ""
    assert parser.sin_clasificar(fila)


@pytest.mark.parametrize("nota", [
    # `Acassuso 1-0 Estudiantes (BA)`, Primera B 2012-13
    "Partido suspendido por intensas lluvias y falta de luz a los 26 minutos del ST. Se "
    "completo el miércoles 27 de marzo a las 11:00 horas.",
    # `Guillermo Brown 4-2 Juventud Unida Universitario`, Argentino A 2012-13
    "Partido suspendido por intensas lluvias en el entrtiempo.Se completo el lunes 11 de "
    "febrero a las 10 horas.",
    # `Central Norte (S) 3-0 Juventud Antoniana`, Argentino A 2012-13
    "Suspendido por incidentes entre la tribuna visitante.Se juega el miércoles 3 de "
    "octubre a las 21:35 horas.",
] + [f"Suspendido a los 20'. Se completó el {dia} 5 de marzo." for dia in
     ("lunes", "martes", "miércoles", "jueves", "viernes", "sábado", "domingo")])
def test_el_dia_de_la_semana_entre_el_verbo_y_el_dia(nota):
    """Las tres salian `suspendido`: el dia de la semana cortaba la frase entre el verbo
    y la fecha. Del Central Norte - Juventud Antoniana, Ascenso del Interior publico la
    cronica con los tres goles, bajo «Postergado de la 5ª fecha»."""
    assert parser.status_de_la_fila("|A\n|1 - 0\n|B<ref>" + nota + "</ref>") == ""


def test_donde_se_jugo_puede_ir_entre_el_verbo_y_el_dia():
    """El `Deportivo Español 1-0 Excursionistas` de la Primera C 2021: le clausuraron la
    cancha la vispera --Solo Ascenso, 17/08/2021-- y se jugo el 19 en otra."""
    fila = ('|Deportivo Español\n|1 - 0\n|Excursionistas\n|Nueva España\n|18 de agosto'
            '{{refn|group="n."|Suspendido debido a la clausura del estadio.<ref>'
            '[https://www.soloascenso.com.ar/notas/afa/el-gobierno-de-la-ciudad-clausuro-la-'
            'cancha-de-espanol/165777 El Gobierno de la Ciudad clausuró la cancha de '
            'Español]</ref> Se jugó en el estadio Enrique Sexto, el 19 de agosto a partir de '
            'las 13:30.}}')
    assert parser.status_de_la_fila(fila) == ""
    # Sin pasar de la frase: un lugar que termina en punto no se pega a la fecha que
    # viene en la frase siguiente.
    otra = ("|A\n|1 - 0\n|B<ref>Suspendido a los 30'. Se jugó en el Gigante. El 5 de mayo "
            "el Tribunal lo dio por terminado.</ref>")
    assert parser.status_de_la_fila(otra) == "suspendido"


@pytest.mark.parametrize("nota", [
    # `Alumni 0-0 Juventud Unida Universitario`, Argentino A 2010-11. RSSSF: `abandoned at
    # 0-0 in 33' due to rain` el 7 de noviembre y `remaining 57'` el 8.
    "Suspendido por lluvia a los 33', completado al día siguiente.",
    # `Villa Dálmine 0-0 Ferrocarril Midland`, Primera C 2009-10. RSSSF: `abandoned at 0-0
    # in 69'` y `remaining 21'`.
    "Suspendido a los 69´ por incidentes y jugados los 21´ dos días después",
])
def test_el_resto_que_se_jugo_despues_aunque_la_nota_no_diga_el_dia(nota):
    fila = "|A\n|0 - 0\n|B<ref>" + nota + "</ref>"
    assert parser.status_de_la_fila(fila) == ""
    assert not parser.sin_clasificar(fila)
    # El contraste: «completado» solo no dice que se haya jugado lo que faltaba.
    otra = "|A\n|0 - 0\n|B<ref>Suspendido por lluvia a los 33', completado el informe.</ref>"
    assert parser.status_de_la_fila(otra) == "suspendido"


def test_el_nombre_de_una_nota_no_es_su_texto():
    """Las tres salian `suspendido` por el `name=`. Las dos primeras son referencias
    peladas a una nota que dice «Se jugó el...»; la tercera nombra `suspendidos` a una
    que dice «postergados». RSSSF da jugados sin nota el `Villa San Carlos 2-0 UAI
    Urquiza` (24/09/2014) y el `San Martín (B) 1-0 Ferrocarril Midland` (10/06/2015)."""
    vsc = ("|Villa San Carlos\n|2 - 0\n|UAI Urquiza\n|Genacio Sálice\n|6 de septiembre"
           "<ref name=suspendido />")
    arm = ('|Deportivo Armenio\n|1 - 1\n|Cañuelas\n|Armenia\n|11 de noviembre'
           '{{refn|group="n."|name="suspendido"}}')
    smb = ("|San Martín (B)\n|1 - 0\n|Ferrocarril Midland{{refn|group=n.|name=suspendidos|"
           "Los partidos fueron postergados debido al fallecimiento del futbolista Cristian "
           "Gómez.}}")
    for fila in (vsc, arm, smb):
        assert parser.status_de_la_fila(fila) == "", fila
        assert not parser.sin_clasificar(fila), fila
    # Las tres maneras de escribir el nombre, y el texto de la nota sigue contando.
    for nombre in ("suspendido", '"suspendido"', "'suspendido'"):
        assert parser.status_de_la_fila("|A\n|1 - 0\n|B<ref name=" + nombre + " />") == ""
    con_texto = "|A\n|1 - 0\n|B<ref name=suspendido>Suspendido a los 10'.</ref>"
    assert parser.status_de_la_fila(con_texto) == "suspendido"


def test_una_cita_no_es_la_nota_cuando_la_nota_tiene_texto_propio():
    """La palabra salia del `cita=` o del rotulo de la fuente, y la nota dice
    «Postergado». RSSSF da los dos jugados sin nota: el `Racing Club 1-0 Rosario Central`
    del Clausura 2002 el 6 de marzo, y el `Unión (MdP) 0-0 Alvarado` del Argentino A
    2013-14 el 5 de marzo de 2014."""
    rac = ("|Racing Club\n|1 - 0\n|Rosario Central\n|El Cilindro\n|6 de marzo{{refn|"
           "group=n.|Postergado por motivos de seguridad.<ref>{{cita web |url=https://www."
           "lanacion.com.ar/deportes/futbol/tirando-paredes-nid377509/ |título=Tirando "
           "paredes |fecha=1 de marzo de 2002 |editor=[[La Nación (Argentina)|lanacion]]"
           ".com.ar |cita= [...] El encuentro entre Racing y Central, [...] que fue "
           "suspendido por razones de seguridad, se jugará el miércoles próximo (6 de "
           "marzo), a las 17. [...]}}</ref> }}")
    uni = ("|Unión (MdP)\n|0 - 0\n|Alvarado\n|José María Minella\n|5 de marzo<ref>"
           "Postergado por disposición del ApreViDe, fue sucesivamente reprogramado.</ref>"
           "<ref>[http://ascensodelinterior.com.ar/noticias/7668/union-vs.-alvarado-"
           "suspendido-por-disposicion-de-aprevide/ Unión - Alvarado suspendido por "
           "disposición del ApreViDe]</ref><ref>[http://ascensodelinterior.com.ar/noticias/"
           "8451/otro-papeln-y-van...-se-suspendi-unin-alvarado/ Otro papelón y van... Se "
           "suspendió Unión - Alvarado]</ref>")
    en_la_misma = ("|A\n|1 - 0\n|B<ref>Postergado por la lluvia. [http://x.com/y Se "
                   "suspendió el partido]</ref>")
    for fila in (rac, uni, en_la_misma):
        assert parser.status_de_la_fila(fila) == "", fila
        assert not parser.sin_clasificar(fila), fila


def test_si_la_cita_es_toda_la_nota_la_cita_es_la_nota():
    """El contraste del de arriba. El `Defensores de Pronunciamiento 0-2 Sol de América`
    del Federal A 2016-17 no tiene mas nota que un enlace, y el rotulo tiene razon."""
    dpr = ("|Defensores de Pronunciamiento\n|0 - 2<ref>[https://www.ascensodelinterior.com"
           ".ar/noticias/18628/fallo-del-tribunal-sol-de-amrica-le-gan-los-puntos-a-"
           "defensores-de-pronunciamiento/ Fallo del Tribunal: Sol de América le ganó los "
           "puntos a Defensores de Pronunciamiento]</ref>\n|Sol de América")
    assert parser.status_de_la_fila(dpr) == "escritorio"
    sola = ("|A\n|1 - 0\n|B<ref>{{cita web|url=http://x.com/y|título=Suspendido a los 20' "
            "por incidentes}}</ref>")
    assert parser.status_de_la_fila(sola) == "suspendido"


def test_darle_por_perdido_avisa_y_no_clasifica():
    """El `San Martín (T) 0-2 Alumni (VM)` del Argentino A 2011-12. La cita dice que hubo
    un fallo y no si el partido llego al final, y no llego: el blog de Jose Carluccio lo
    da «Suspendido a los 40', con el marcador 0-2 [...]. No continuó ni se modificó el
    resultado». Leido como fallo saldria `escritorio`, que es falso; lo que se puede
    decir es que la pagina hablo y no se supo que."""
    fila = ("|San Martín (T)\n|bgcolor=#D0E7FF|0 - 2<ref>{{cita web |url= http://www."
            "eldiario24.com/nota.php?id=246935|título= AFA decide darle por perdido 0-2 a "
            "San Martín de Tucuman frente a Alumni|fechaacceso=23 de febrero de 2012|autor= "
            "Eldiario24.com|idioma= español}}</ref>\n|'''Alumni (VM)'''")
    assert parser.status_de_la_fila(fila) == ""
    assert parser.sin_clasificar(fila)


@pytest.mark.parametrize("nota", [
    # `Colón 0-1 Atlético de Rafaela`, Inicial 2013. RSSSF: `Colón dns`.
    "Suspendido porque Colón no se presentó.",
    # `Independiente (Ch) 1-0 Alianza (CC)`, Federal A 2015. RSSSF: `not played`.
    "El equipo visitante no se presentó a disputar el partido. Se le dio por perdido por "
    "1-0, y se le descontaron 3 puntos.",
    # `San Jorge (T) 0-1 Unión Aconquija`, Federal A 2015. RSSSF: `not played`.
    "Suspendido por falta de cuerpo médico. El Tribunal se lo dio ganado al equipo "
    "visitante.",
    # `Central Ballester 0-3 Juventud Unida`, Primera C 2025. Solo Ascenso, 05/06/2025:
    # el partido «quedó aplazado».
    "Suspendido por falta de personal médico. Se le dio por perdido al equipo local.",
])
def test_el_partido_que_no_empezo_es_no_disputado(nota):
    fila = "|A\n|0 - 1\n|B<ref>" + nota + "</ref>"
    assert parser.status_de_la_fila(fila) == "no disputado"
    assert not parser.sin_clasificar(fila)


@pytest.mark.parametrize("nota, status", [
    # Se jugo otro dia, y eso se pregunta antes: `Juventud Unida 0-1 Central Córdoba
    # (R)` de la Primera C 2015.
    ("Suspendido por falta de personal médico. Se jugó el 23 de septiembre.", ""),
    # Si la frase dice que ya se jugaba, el partido empezo.
    ("Suspendido a los 20' porque el visitante no se presentó.", "suspendido"),
    ("Suspendido faltando 7 minutos porque el visitante no se presentó.", "suspendido"),
    ("Suspendido en el entretiempo porque el visitante no se presentó.", "suspendido"),
    # Y se mira la frase de la PRIMERA suspension: la lluvia pudo cortar un partido
    # empezado, y lo que vino despues no lo borra.
    ("Suspendido por lluvia. El visitante no se presentó a la reprogramación.", "suspendido"),
])
def test_lo_que_no_alcanza_para_decir_que_no_empezo(nota, status):
    assert parser.status_de_la_fila("|A\n|0 - 1\n|B<ref>" + nota + "</ref>") == status


def test_el_no_disputado_por_la_nota_llega_al_partido_con_su_dia():
    """La fila conserva el dia para el que estaba programado, como el `Instituto 0-1 San
    Lorenzo` de la 1987-88 que trae RSSSF: no es la celda «Sin disputar», que no trae
    ninguno."""
    tabla = ('{|class="wikitable"\n!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n'
             '|-\n|Colón\n|0 - 1\n|Atlético de Rafaela\n|Brigadier López\n|18 de noviembre'
             '{{refn|group=n.|Suspendido porque Colón no se presentó.}}\n|18:00\n|}')
    p, = parser.partidos_de_tabla(tabla, 2013, "Primera Division")
    assert (p.status, p.fecha) == ("no disputado", "2013-11-18")


# --------------------------------------------------------------------------
# la hora con el canal pegado
# --------------------------------------------------------------------------
def _con_hora(celda: str) -> str:
    return (TABLA_SIN_HORA.replace("!Fecha\n", "!Fecha\n!Hora\n")
            .replace("|23 de enero\n", f"|23 de enero\n|{celda}\n"))


@pytest.mark.parametrize("celda, hora", [
    ("15:30 [[TyC Sports|(TV)]]", "15:30"),     # Primera C 2010-11, la vuelta de la promocion
    ("17:30 ([[Fútbol para todos|TV]])", "17:30"),   # Argentino A 2011-12
    ("18:00 )", "18:00"),                        # Primera C 2011-12, lo que dejo una edicion
    ("21:30 hs.", "21:30"),
    ("9:30 (TV)", "9:30"),                       # la hora de un digito tambien
])
def test_la_hora_con_el_canal_pegado_queda_en_la_hora(celda, hora):
    """Dos paginas publicaban el mismo partido a las `21:00` y a las `21:00 (TV)`:
    la misma hora, y dos copias que no decian lo mismo."""
    assert parser.partidos_de_tabla(_con_hora(celda), 2026, "Apertura")[0].hora == hora


@pytest.mark.parametrize("celda", ["20:00", "9:00", "15::00", "18:5", "14.00", "123:45",
                                   "15:300"])
def test_la_hora_que_no_empieza_bien_queda_como_figura(celda):
    """Lo que no empieza con una hora valida no se adivina, y tampoco se borra."""
    assert parser.partidos_de_tabla(_con_hora(celda), 2026, "Apertura")[0].hora == celda


# --------------------------------------------------------------------------
# la hora de una {{Partido}}
# --------------------------------------------------------------------------
def _con_fecha(fecha: str, mas: str = "") -> str:
    return (f"{{{{Partido\n|local = Boca Juniors\n|resultado = 2:1\n|visita = River Plate"
            f"\n|fecha = {fecha}{mas}\n|árbitro=[[Alguien]]}}}}")


@pytest.mark.parametrize("fecha, hora", [
    ("21 de diciembre, 17:00", "17:00"),                     # 484 de las 514
    ("9 de junio de 2013 - 15:00 hs.", "15:00"),             # Primera B y C 2012-13
    ("28 de mayo 15:10 hs.", "15:10"),                       # Primera B 2013-14
    ("27 de mayo 15:30", "15:30"),                           # Primera C 2013-14
    ("{{fecha|17|1|2021}}, 22:10 ([[UTC-3]])", "22:10"),     # final de la Copa de la Liga 2020
    ("31 de marzo de 2021, 20:15 ([[UTC-3]])", "20:15"),     # y el clasificatorio, misma pagina
])
def test_la_plantilla_trae_la_hora_pegada_a_la_fecha(fecha, hora):
    """511 de las 514 plantillas con resultado escriben la hora adentro de `fecha`, y el
    lector solo sacaba el dia: la fase final de 46 paginas salia sin hora."""
    assert parser.partidos_de_plantillas(_con_fecha(fecha), 2021, "x")[0].hora == hora


@pytest.mark.parametrize("fecha, hora", [
    ("21 de diciembre, 17:00:00", ""),                # con segundos no es la forma que se lee
    ("21 de diciembre, 17:00 (UTC-03:00)", "17:00"),  # el huso no es una hora
    ("21 de diciembre ([[UTC−03:00]])", ""),          # ni aunque este solo
])
def test_la_hora_de_la_fecha_es_un_hh_mm_suelto(fecha, hora):
    """Sin la guarda de adelante, `17:00:00` daba `17:00`; sin la de atras, `00:00`. Y
    con el signo del huso como una hora mas, `17:00 (UTC-03:00)` traia dos y quedaba
    vacia, y un huso solo se publicaba como si fuera la hora."""
    assert parser.partidos_de_plantillas(_con_fecha(fecha), 2021, "x")[0].hora == hora


def test_la_plantilla_con_campo_hora_lo_usa():
    """Las tres del triangular del Apertura 2008: `fecha = {{fecha|23|12|2008}}` y la
    hora aparte."""
    p, = parser.partidos_de_plantillas(
        _con_fecha("{{fecha|23|12|2008}}", "\n|hora = 20:30"), 2008, "x")
    assert (p.fecha, p.hora) == ("2008-12-23", "20:30")


def test_el_campo_hora_se_lee_como_la_celda_de_las_tablas():
    """Con `_hora`: la hora valida y no lo que venga pegado, como el canal."""
    p, = parser.partidos_de_plantillas(
        _con_fecha("{{fecha|23|12|2008}}", "\n|hora = 20:30 ([[TyC Sports]])"), 2008, "x")
    assert p.hora == "20:30"


@pytest.mark.parametrize("fecha", [
    "21 de diciembre",                  # sin hora
    "21 de diciembre, --:--",           # el relleno de un partido que no tiene horario
    "21 de diciembre, 15.30",           # con punto no es una hora valida
    "21 de diciembre, 15:00 o 17:00",   # con dos no se sabe cual es
])
def test_lo_que_no_es_una_hora_en_la_fecha_queda_vacio(fecha):
    """Adentro de `fecha` lo que sobra no es una celda de hora mal escrita: es un
    pedazo de la fecha. Publicarlo en `time` seria decir que esa es la hora."""
    assert parser.partidos_de_plantillas(_con_fecha(fecha), 2021, "x")[0].hora == ""


def test_la_hora_de_una_nota_al_pie_no_es_la_del_partido():
    fecha = "31 de mayo, 15:00<ref>Estaba programado para el 23 de mayo a las 19:00.</ref>"
    assert parser.partidos_de_plantillas(_con_fecha(fecha), 2021, "x")[0].hora == "15:00"


def test_si_se_jugo_otro_dia_el_dia_y_la_hora_son_los_de_la_nota():
    """La final de la Primera C 2018-19: `fecha = 15 de junio, 15:00` y la nota dice
    que se jugo el 22 a las 14:30. Revista Ascenso: «Jugado el sábado 22 de junio».
    Salen juntos: el 22 a las 15:00 o el 15 a las 14:30 serian instantes que no
    existieron."""
    suceso = ("\n|suceso = Suspendido por las condiciones climáticas. Se jugó el 22 de "
              "junio, a partir de las 14:30.")
    texto = _con_fecha("15 de junio, 15:00", suceso)
    assert parser._dia_y_hora_de_la_nota(texto, 2019, None, 8, "2019-06-15",
                                         "15:00") == ("2019-06-22", "14:30")
    p, = parser.partidos_de_plantillas(texto, 2019, "x")
    assert (p.fecha, p.hora) == ("2019-06-22", "14:30")


def test_si_la_nota_repite_el_dia_de_la_fecha_la_hora_queda():
    """San Telmo-All Boys, Primera B 2018-19: la pagina ya paso `fecha` al dia en que
    se jugo, y la nota dice ese mismo dia."""
    suceso = ("\n|suceso = Suspendido por las condiciones climáticas. Se jugó el 20 de "
              "junio, a partir de las 14:10.")
    p, = parser.partidos_de_plantillas(_con_fecha("20 de junio, 14:10", suceso), 2019, "x")
    assert (p.fecha, p.hora) == ("2019-06-20", "14:10")


def test_si_la_nota_dice_que_se_jugara_otro_dia_la_hora_tambien_es_del_programado():
    """Acassuso-Villa San Carlos, cuartos de la Primera B 2025: la pagina escribio la
    nota antes del partido y la dejo en futuro. El 29 de noviembre se suspendio antes
    de empezar y se jugo el martes 2, asi que las 17:00 de `fecha` son las de un dia
    sin partido. Solo Ascenso, 29/11/2025: «el encuentro fue reprogramado para el
    próximo martes 2 de diciembre». El dia no se mueve: un plan no fecha nada."""
    suceso = ("\n|suceso = Suspendido por las condiciones climáticas. Se jugará el 2 de "
              "diciembre, a la misma hora.")
    p, = parser.partidos_de_plantillas(_con_fecha("29 de noviembre, 17:00", suceso), 2025, "x")
    assert (p.fecha, p.hora) == ("2025-11-29", "")


@pytest.mark.parametrize("frase", [
    "Se jugarán el 2 de diciembre",      # el plural, cuando la nota habla de la llave
    "Se disputará el 2 de diciembre",
    "Se jugara el 2 de diciembre",       # sin la tilde
])
def test_la_nota_en_futuro_se_reconoce_en_sus_formas(frase):
    suceso = f"\n|suceso = Suspendido por lluvia. {frase}, a la misma hora."
    p, = parser.partidos_de_plantillas(_con_fecha("29 de noviembre, 17:00", suceso), 2025, "x")
    assert p.hora == "", frase


def test_la_nota_en_futuro_que_repite_el_dia_en_el_anio_que_sigue_no_vacia_la_hora():
    """El gemelo en futuro del test de abajo: la nota que repite el dia de `fecha` no
    habla de otro dia, aunque la regla del mes la ponga en el otro anio."""
    suceso = "\n|suceso = Postergado. Se jugará el 29 de noviembre, a las 15:00."
    p, = parser.partidos_de_plantillas(_con_fecha("{{fecha|29|11|2020}}, 15:00", suceso),
                                       2019, "x", 2020)
    assert (p.fecha, p.hora) == ("2020-11-29", "15:00")


def test_la_nota_que_repite_el_dia_de_fecha_en_el_anio_que_sigue_no_vacia_la_hora():
    """En una temporada que cruza el anio la regla del mes pone el "29 de noviembre" de
    la nota en el primero, y `fecha` lo escribe con el segundo: es el mismo dia, y
    `_fecha_de_la_nota` lo corrige con el dia programado. Sin el, la hora se vaciaba
    como si la nota hablara de otro dia."""
    suceso = "\n|suceso = Suspendido por lluvia. Se jugó el 29 de noviembre, a las 15:00."
    p, = parser.partidos_de_plantillas(_con_fecha("{{fecha|29|11|2020}}, 15:00", suceso),
                                       2019, "x", 2020)
    assert (p.fecha, p.hora) == ("2020-11-29", "15:00")


def test_un_partido_completado_otro_dia_conserva_la_hora_en_que_empezo():
    """Quilmes-Gimnasia (M), Primera Nacional 2023: empezo el 28 de octubre a las 21:30
    y se completo el 4 de noviembre. "Se completo" no mueve el dia, y tampoco la hora."""
    suceso = ("\n|suceso = Suspendido en el entretiempo. Se completó el 4 de noviembre, a "
              "partir de las 13:00.")
    p, = parser.partidos_de_plantillas(_con_fecha("28 de octubre, 21:30", suceso), 2023, "x")
    assert (p.fecha, p.hora) == ("2023-10-28", "21:30")


# --------------------------------------------------------------------------
# la hora del dia en que se jugo: la de la misma oracion que dice el dia
# --------------------------------------------------------------------------
def _reprogramado(nota: str, fecha: str = "28 de junio", hora: str = "21:30"):
    """Una fila de tabla cuya nota dice cuando se jugo. La celda trae el programado."""
    fila = ("|Villa Dálmine\n|1 - 3\n|Ferro Carril Oeste\n|El Coliseo\n"
            f"|{fecha}{{{{refn|group=n.|Suspendido por lluvia. {nota}}}}}\n|{hora}")
    (p,) = parser.partidos(_tabla_con_notas(fila), 2015, "X")
    return p


@pytest.mark.parametrize("nota, hora", [
    ("Se jugó el 29 de julio, a partir de las 15:00.", "15:00"),        # 287 de las 316
    ("Se jugó el 29 de julio, desde las 15:30.", "15:30"),              # Primera C 2024
    ("Se jugó el 29 de julio a las 15:30.", "15:30"),                   # Primera B 2016-17
    ("Se jugó el 29 de julio, a partir de las 15.30, a puertas cerradas.", "15:30"),
    ("Se jugó el 29 de julio, a partir de las 14.", "14:00"),           # B Nacional 2015
    ("Se jugó el 29 de julio, a partir de las 9:15.", "09:15"),         # Federal A 2018-19
    ("Se jugó el 29 de julio, a partir de las 17 horas.", "17:00"),
    ("Se jugó el 29 de julio en el estadio Ciudad Evita, a partir de las 19:00.", "19:00"),
    ("Se jugaron el 29 de julio, a la misma hora.", "21:30"),           # la de la celda
    ("Se jugaron el 29 de julio, en el mismo horario.", "21:30"),       # Primera C 2015
    ("Se jugó el 29 de julio.", ""),                                     # no la dice
])
def test_la_hora_del_dia_jugado_sale_de_la_oracion_del_dia(nota, hora):
    """La celda de la hora es la del programado, igual que la de la fecha: si el dia
    sale de la nota y la hora de la celda, la fila publica un instante que no
    existio. La regla es del dueño del dataset: la hora a la que se jugo ESE dia, de
    la nota; "a la misma hora" es la de la celda; y si la nota no la da, vacia."""
    p = _reprogramado(nota)
    assert (p.fecha, p.hora) == ("2015-07-29", hora)


@pytest.mark.parametrize("nota", [
    "Se jugó el 29 de julio, a las 2 semanas de la suspensión.",    # no es una hora
    "Se jugó el 29 de julio, a las 48 horas de la suspensión.",     # no existe
    "Se jugó el 29 de julio, a las 15:75.",                         # tampoco
    "Se jugó el 29 de julio, a las 15:30:00.",                      # no es la forma que se lee
    "Se jugó el 29 de julio, a las 15:00 o a las 17:00.",           # dos: no se sabe cual
])
def test_lo_que_no_es_una_hora_del_partido_deja_la_hora_vacia(nota):
    p = _reprogramado(nota)
    assert (p.fecha, p.hora) == ("2015-07-29", ""), nota


def test_la_hora_de_otra_oracion_no_es_la_del_dia_jugado():
    """Antes de la frase la nota cuenta lo que NO fue: es la forma de la Primera B 2024
    y del Federal A 2025, con la hora de un plan que se volvio a suspender."""
    p = _reprogramado("Se reprogramó para el 10 de julio, a partir de las 15:00, y se "
                      "volvió a suspender. Se jugó el 29 de julio.")
    assert (p.fecha, p.hora) == ("2015-07-29", "")


@pytest.mark.parametrize("nota", [
    # el titulo de una cita: "jugarán mañana a las 17", y era el plan
    "Se jugó el 29 de julio<ref>[http://x Juegan mañana a las 17:00]</ref>",
    # otra nota de la misma celda
    "Se jugó el 29 de julio}}{{refn|Estaba programado a las 17:00",
])
def test_lo_que_sigue_a_la_nota_no_es_la_hora_del_partido(nota):
    assert _reprogramado(nota).hora == ""


def test_la_nota_de_una_plantilla_termina_con_su_parametro():
    """El `reporte` que sigue al `suceso` no es parte de la nota."""
    texto = ("\n|fecha = 15 de junio, 15:00\n|suceso = Suspendido. Se jugó el 22 de junio"
             "\n|reporte = [http://x Se juega el sábado a las 14:30]")
    assert parser._dia_y_hora_de_la_nota(texto, 2019, None, 8, "2019-06-15",
                                         "15:00") == ("2019-06-22", "")


def test_si_la_nota_repite_el_dia_de_la_celda_la_hora_es_la_de_la_nota():
    """La pagina ya paso la fila al dia en que se jugo, pero no siempre la hora:
    `Crucero del Norte 0-1 Rosario Central` (B Nacional 2012-13) dice `21 de
    noviembre` y `11:00` --la hora del dia de la lluvia-- y la nota "se disputó el 21
    de noviembre, a partir de las 18:30"."""
    p = _reprogramado("Se jugó el 28 de junio, a partir de las 15:00.")
    assert (p.fecha, p.hora) == ("2015-06-28", "15:00")


@pytest.mark.parametrize("nota", [
    "Se jugó el 28 de junio.",                              # la nota no da la hora
    "Se jugó el 28 de junio, a la misma hora.",
])
def test_si_la_nota_repite_el_dia_y_no_da_otra_hora_queda_la_de_la_celda(nota):
    """Con el dia de la celda, la celda ya es la del dia en que se jugo."""
    p = _reprogramado(nota)
    assert (p.fecha, p.hora) == ("2015-06-28", "21:30")


def test_un_partido_completado_conserva_la_hora_de_la_celda():
    """Empezo el dia y a la hora de la celda; "se completó" no mueve ninguno de los dos."""
    p = _reprogramado("Se completó el 4 de julio, a partir de las 13:00.")
    assert (p.fecha, p.hora) == ("2015-06-28", "21:30")


def test_la_nota_en_futuro_de_una_tabla_vacia_la_hora():
    """`Cañuelas 0-2 Colegiales`, Primera B 2024: la celda dice `31 de agosto` y
    `12:05`, y la nota "Se jugará el 2 de septiembre, a partir de las 15:00". El dia
    no se mueve -- un plan no fecha nada --, pero el 31 no hubo partido a las 12:05."""
    p = _reprogramado("Se jugará el 2 de julio, a partir de las 15:00.")
    assert (p.fecha, p.hora) == ("2015-06-28", "")


def test_la_nota_en_futuro_que_repite_el_dia_deja_la_hora_de_la_celda():
    """`Gimnasia y Esgrima (J) 4-0 Nueva Chicago`, Primera Nacional 2026: la celda ya
    dice el dia nuevo y la nota "se disputará el 17 de junio a las 15:00"."""
    p = _reprogramado("Se disputará el 28 de junio a las 15:00.")
    assert (p.fecha, p.hora) == ("2015-06-28", "21:30")


@pytest.mark.parametrize("nota, hora", [
    # `Deportivo Español 1-0 Excursionistas`, Primera C 2021: le clausuraron la cancha
    ("Se jugó en el estadio Enrique Sexto, el 29 de julio a partir de las 13:30.", "13:30"),
    ("Se jugó el miércoles 29 de julio, a partir de las 15:00.", "15:00"),
    ("Se jugó el miercoles 29 de julio.", ""),                       # sin la tilde
    ("Se jugaron en Sarandí el sábado 29 de julio, a la misma hora.", "21:30"),
])
def test_entre_el_verbo_y_el_dia_van_donde_se_jugo_y_el_dia_de_la_semana(nota, hora):
    """Las dos piezas que `_SE_COMPLETO` ya aceptaba para el status. Sin ellas el status
    decia que el partido se habia jugado otro dia y la fila seguia en el programado,
    con la hora de ese dia: la del `Deportivo Español` era el 18 a las 15:00."""
    p = _reprogramado(nota)
    assert (p.fecha, p.hora) == ("2015-07-29", hora), nota


def test_donde_se_jugo_no_se_pega_con_el_dia_de_la_oracion_siguiente():
    """El lugar termina con la frase: el 29 de julio de aca es un plan, no el dia en que
    se jugo, y la fila queda como esta."""
    p = _reprogramado("Se jugó en Sarandí. Se reprogramó para el 29 de julio.")
    assert (p.fecha, p.hora) == ("2015-06-28", "21:30")


@pytest.mark.parametrize("nota", [
    # `Central Norte (S) 3-0 Juventud Antoniana`, Argentino A 2012-13
    "Se juega el miércoles 2 de julio a las 21:35 horas.",
    "Se juegan el 2 de julio, a la misma hora.",
    "Se jugará en el estadio Enrique Sexto, el 2 de julio a partir de las 13:30.",
    "Se jugará el jueves 2 de julio, a partir de las 15:00.",
])
def test_el_plan_en_presente_o_con_la_cancha_o_el_dia_de_la_semana_vacia_la_hora(nota):
    """El mismo plan que «se jugará»: no fecha nada, y dice que la hora de la celda es
    la de un dia en que el partido no se jugo."""
    p = _reprogramado(nota)
    assert (p.fecha, p.hora) == ("2015-06-28", ""), nota


def test_la_nota_de_una_tanda_vale_para_cada_fila_con_su_hora():
    """La nota de una celda con `rowspan` cubre varias filas, cada una con la suya:
    "a la misma hora" es la de cada fila, no la de la primera."""
    filas = ("|Atlas\n|1 - 0\n|Berazategui\n|Atlas\n|rowspan=2|29 de mayo{{refn|group=n.|"
             "Suspendidos. Se jugaron el 30 de mayo, a la misma hora.}}\n|14:00",
             "|Luján\n|0 - 0\n|Leandro N. Alem\n|Luján\n|16:00")
    ps = parser.partidos(_tabla_con_notas(*filas), 2023, "Primera C")
    assert [(p.fecha, p.hora) for p in ps] == [("2023-05-30", "14:00"),
                                                ("2023-05-30", "16:00")]


# --------------------------------------------------------------------------
# cancha neutral en una {{Partido}}: lo dice la prosa de su seccion
# --------------------------------------------------------------------------
def _un_partido(local: str = "Sarmiento (LB)", visita: str = "Los Andes") -> str:
    return (f"{{{{Partidos\n|local = {local}\n|resultado = 0:1\n|visita = {visita}\n"
            f"|fecha = 21 de diciembre, 17:00\n|estadio = [[Estadio Julio César Villagra]]\n}}}}")


def _neutrales(texto: str) -> list:
    return [p.neutral for p in parser.partidos_de_plantillas(texto, 2024, "x")]


def test_la_frase_de_la_seccion_marca_la_plantilla_neutral():
    """El tercer ascenso 2024, como lo escriben la Primera B y el Federal A: la frase va
    en la entradilla de `== Definicion ==` y la plantilla cuelga de `==== Partido ====`,
    un titulo de relleno. Salia `false` en las dos copias."""
    texto = ("== Definición del tercer ascenso a la Primera Nacional ==\n"
             "La disputaron Los Andes y Sarmiento, en estadio neutral, a un solo partido."
             "{{refn|{{Cita web|título=Reglamento}}}}\n\n==== Partido ====\n" + _un_partido())
    assert _neutrales(texto) == [True]


def test_la_frase_justo_arriba_de_la_plantilla_tambien():
    texto = ("== Final ==\nLa disputaron los dos ganadores, a un solo partido, en sede "
             "neutral.\n" + _un_partido())
    assert _neutrales(texto) == [True]


def test_sin_frase_la_plantilla_no_dice_nada():
    """`None` y no `False`: una seccion que no dice nada no afirma que el partido fue
    en la cancha del local. Decide el torneo, como en las tablas."""
    assert _neutrales("== Final ==\nLa disputaron los dos ganadores.\n" + _un_partido()) == [None]


def test_no_se_sube_a_la_entradilla_de_una_fase_entera():
    """El Apertura y el Clausura 2025 y el Apertura 2026: la entradilla de la fase
    habla de cuatro rondas y dice que la FINAL fue neutral. Subiendo hasta ahi se
    marcaban los octavos, los cuartos y las semis, jugados en la cancha del local."""
    texto = ("== Octavos y cuartos de final, semifinales y final ==\n"
             "Se jugaron en la sede del mejor ubicado. El partido final se jugó en campo "
             "neutral.\n=== Octavos de final ===\n" + _un_partido("Boca Juniors", "Tigre"))
    assert _neutrales(texto) == [None]


def test_de_un_titulo_de_relleno_se_sube_solo_a_la_seccion_que_lo_contiene():
    """El padre es el titulo de nivel MENOR, no el anterior. La vuelta cuelga de
    `==== Partido de vuelta ====`, y lo que dice la seccion de la ida no es de ella."""
    texto = ("=== Final ===\nSe jugó a dos partidos.\n"
             "==== Partido de ida ====\nLa ida se jugó en cancha neutral.\n"
             + _un_partido("Boca Juniors", "Tigre") +
             "\n==== Partido de vuelta ====\n" + _un_partido("Tigre", "Boca Juniors"))
    assert _neutrales(texto) == [True, None]


def test_la_entradilla_del_padre_termina_en_el_proximo_titulo():
    """Lo que hay debajo de OTRO titulo hijo del mismo padre no es la entradilla."""
    texto = ("== Fase final ==\nSe jugó por eliminación directa.\n"
             "=== Formato de la final ===\nLa final se jugó en cancha neutral.\n"
             "=== Partidos ===\n" + _un_partido())
    assert _neutrales(texto) == [None]


def test_una_seccion_comentada_no_dice_nada():
    """Las paginas en curso dejan comentada la seccion de la final que todavia no se
    jugo, con la frase y sus subtitulos adentro: asi la escribe hoy el Federal A 2026,
    `<!--== Quinta fase ==` ... `==== Partido ====`. Ni el subtitulo comentado es un
    titulo ni la frase comentada la dice la pagina."""
    seccion = ("== Cuarta fase ==\nA partido único, en la cancha del mejor ubicado.\n"
               "<!--== Quinta fase ==\nLa disputarán los dos ganadores, en sede neutral.\n"
               "==== Partido ====\n-->\n")
    assert _neutrales(seccion + _un_partido()) == [None]
    prosa = "== Cuarta fase ==\nA partido único.<!-- la final, en sede neutral -->\n"
    assert _neutrales(prosa + _un_partido()) == [None]


def test_la_frase_adentro_de_una_nota_no_cuenta():
    for nota in ("{{refn|Estaba previsto en cancha neutral.}}",
                 "<ref>Estaba previsto en cancha neutral.</ref>"):
        texto = "== Cuarta fase ==\nA partido único." + nota + "\n" + _un_partido()
        assert _neutrales(texto) == [None], nota


def test_una_nota_autocerrada_no_se_lleva_la_prosa_que_sigue():
    """`<ref name=a />` es una nota entera. Leida como apertura, la prosa hasta el
    proximo `</ref>` -- la frase de la cancha -- se iba con ella."""
    texto = ("== Final ==\nLa disputaron los dos ganadores<ref name=a />, a un solo partido, "
             "en sede neutral.<ref>Reglamento.</ref>\n" + _un_partido())
    assert _neutrales(texto) == [True]


def test_neutral_es_una_palabra_entera():
    """"El arquero neutralizó dos penales" no habla de la cancha. El plural si."""
    texto = "== Final ==\nEl arquero neutralizó dos penales.\n" + _un_partido()
    assert _neutrales(texto) == [None]
    plural = "== Final ==\nSe jugaron en sedes neutrales.\n" + _un_partido()
    assert _neutrales(plural) == [True]


def test_de_partido_de_ida_y_de_vuelta_tambien_se_sube():
    """`Partido de ida` y `Partido de vuelta` son de relleno como `Partido`: la frase de
    la llave esta en la entradilla de la seccion que los contiene, y vale para las dos."""
    texto = ("=== Final ===\nSe jugó a dos partidos, los dos en cancha neutral.\n"
             "==== Partido de ida ====\n" + _un_partido("Boca Juniors", "Tigre") +
             "\n==== Partido de vuelta ====\n" + _un_partido("Tigre", "Boca Juniors"))
    assert _neutrales(texto) == [True, True]


def test_un_titulo_que_solo_empieza_con_partido_no_es_de_relleno():
    """`Partido por la permanencia` nombra OTRO partido: la entradilla de la seccion que
    lo contiene habla del de la final."""
    texto = ("== Definiciones ==\nLa final por el ascenso se jugó en cancha neutral.\n"
             "=== Partido por la permanencia ===\n" + _un_partido("Boca Juniors", "Tigre"))
    assert _neutrales(texto) == [None]


def test_sin_titulo_arriba_no_hay_seccion_que_lo_diga():
    """Lo que esta antes del primer titulo es la entradilla del articulo, que habla del
    torneo entero."""
    assert _neutrales("Se jugó en cancha neutral.\n" + _un_partido()) == [None]


# --------------------------------------------------------------------------
# el dia y el status de una {{Partido}}: los dice su nota, como en las tablas
# --------------------------------------------------------------------------
def test_la_plantilla_que_se_jugo_otro_dia_va_al_dia_en_que_se_jugo():
    """La final de la Primera C 2018-19: `fecha = 15 de junio, 15:00` y la nota dice
    que se jugo el 22. Doble Amarilla, sabado 22/06/2019: «Villa San Carlos venció
    por 3-2 a Excursionistas»."""
    suceso = ("\n|suceso = Suspendido por las condiciones climáticas. Se jugó el 22 de "
              "junio, a partir de las 14:30.")
    p, = parser.partidos_de_plantillas(_con_fecha("15 de junio, 15:00", suceso), 2019, "x")
    assert p.fecha == "2019-06-22"


def test_la_plantilla_que_se_completo_otro_dia_no_se_mueve():
    """Empezo el dia de `fecha`: "se completo" no es "se jugo"."""
    suceso = "\n|suceso = Suspendido en el entretiempo. Se completó el 4 de noviembre."
    p, = parser.partidos_de_plantillas(_con_fecha("28 de octubre, 21:30", suceso), 2023, "x")
    assert p.fecha == "2023-10-28"


def test_la_plantilla_lee_el_dia_de_una_nota_definida_en_otra_parte():
    """La plantilla puede referenciar una nota que la pagina define en una tabla."""
    otra = "{{refn|group=n.|name=susp|Suspendido por lluvia. Se jugó el 22 de junio.}}\n"
    plantilla = _con_fecha("15 de junio, 15:00", "{{refn|group=n.|name=susp}}")
    p, = parser.partidos_de_plantillas(otra + plantilla, 2019, "x")
    assert p.fecha == "2019-06-22"


@pytest.mark.parametrize("nota, status", [
    # Estudiantes (BA) - Almagro, Primera B 2015, en `suceso`
    ("\n|suceso = Suspendido a los 32' del segundo tiempo, por disturbios provocados por "
     "la parcialidad local. Se lo dio por finalizado.", "suspendido"),
    # Argentino de Quilmes - Defensores de Cambaceres, Primera C 2013-14: el titulo de la
    # cita es toda la nota
    ("<ref>{{Cita web |url= |título=El partido terminó igualado 0:0 pero se lo dieron "
     "como ganado a Defensores de Cambaceres por la mala inclusión de un jugador de "
     "Argentino de Quilmes.}}</ref>", "escritorio"),
    # Deportivo Riestra - Comunicaciones, Primera B 2016-17: se completo, y en plural
    ("{{refn|group=n.|Suspendido a los 45' del segundo tiempo. Se completaron los 5 "
     "minutos adicionales el 3 de agosto, a partir de las 15:00.}}", ""),
    ("", ""),
], ids=["suspendido", "escritorio", "completado", "sin nota"])
def test_la_plantilla_escribe_el_status_que_dice_su_nota(nota, status):
    p, = parser.partidos_de_plantillas(_con_fecha("24 de noviembre, 17:05", nota), 2015, "x")
    assert p.status == status


@pytest.mark.parametrize("nota", [
    "Se completaron los 5 minutos adicionales el 3 de agosto",
    "Se completaron el 3 de agosto",
    "Se jugaron los 10 minutos restantes el 3 de agosto",
])
def test_se_completo_tambien_en_plural_y_con_los_minutos_en_el_medio(nota):
    assert parser.status_de_la_fila(f"Suspendido a los 45'. {nota}.") == ""


def test_la_guarda_de_los_fallos_sin_leer_mira_tambien_las_plantillas():
    """Desde que la plantilla escribe `status`, la guarda tiene que cubrirla: una nota
    que habla de un fallo y no se sabe leer no puede quedar en vacio callada."""
    texto = _con_fecha("21 de diciembre, 17:00",
                       "\n|suceso = El Tribunal de Disciplina resolvió el caso.")
    avisos = parser.fallos_sin_leer(texto)
    assert len(avisos) == 1 and "Boca Juniors vs River Plate" in avisos[0], avisos


# --------------------------------------------------------------------------
# los bordes de las reglas de la nota
# --------------------------------------------------------------------------
def _fila_con_nota(nota: str) -> str:
    return ("|Sportivo Estudiantes (SL)\n|2 - 0\n|Juventud U. U.\n|Juan Gilberto Funes\n"
            f"|6 de octubre<ref>{nota}</ref>")


@pytest.mark.parametrize("nota", [
    "En: [http://x.com/nota Suspendido por lluvia.]",             # dos letras no son texto
    "<small>[http://x.com/nota Suspendido por lluvia.]</small>",  # ni el marcado
])
def test_una_nota_que_es_solo_la_cita_sigue_contando(nota):
    """El rotulo de la cita se saca solo cuando la nota dice algo con palabras suyas:
    tres letras seguidas que no son marcado. Si no, la cita ES la nota."""
    assert parser.status_de_la_fila(_fila_con_nota(nota)) == "suspendido"


def test_lo_que_dice_otra_frase_no_dice_que_el_partido_no_empezo():
    """Se mira la frase de la suspension, no la nota entera: que el inicio se demorara
    por falta de medico no dice que el partido no empezo, y la suspension vino
    despues."""
    nota = ("Se demoró el inicio por falta de personal médico. Suspendido por incidentes "
            "en las tribunas.")
    assert parser.status_de_la_fila(_fila_con_nota(nota)) == "suspendido"


def test_la_cancha_de_la_frase_del_dia_es_corta():
    """«en <lugar>» se acepta hasta 60 letras y sin cruzar un punto: mas largo, la
    fecha es de otra cosa. Aca el 29 de julio es lo que habia fijado la AFA."""
    p = _reprogramado("Se jugó en la cancha del local y no en la sede neutral que había "
                      "fijado la AFA para el 29 de julio.")
    assert p.fecha == "2015-06-28"


def test_una_hora_que_no_existe_en_la_nota_no_es_una_hora():
    p = _reprogramado("Se jugó el 29 de julio, a partir de las 24:30.")
    assert (p.fecha, p.hora) == ("2015-07-29", "")

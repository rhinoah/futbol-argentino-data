#!/usr/bin/env python3
"""Tests del parser.

Casi todos apuntan a lo mismo: que el parser falle en vez de mentir. Cada uno de
los de mas abajo con nombre `test_bug_*` corresponde a un error que efectivamente
estuvo en el codigo y que ninguna excepcion delataba.
"""
from __future__ import annotations

import pytest

from fad import parser
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
    desempate = [p for p in ps if p.jornada == ""][0]
    assert (desempate.local, desempate.visita) == ("Almagro", "Aldosivi")
    assert desempate.fecha == "2018-05-04"


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

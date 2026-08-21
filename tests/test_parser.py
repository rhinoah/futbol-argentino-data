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
    la nota, y la fecha, la de consulta de la cita."""
    p = parser.partidos_de_tabla(_FILA_CON_NOTA, 2015, "X")[0]
    assert p.hora == "21:30"
    assert p.estadio == "El Coliseo"
    assert not p.fecha.startswith("2022")


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
    el fallo, la mitad de los suspendidos pasan a `escritorio` por una palabra."""
    fila = ("|Central Ballester\n|0 - 3\n|Juventud Unida<ref>Suspendido por falta de "
            "personal médico. Se le dio por perdido al equipo local.</ref>")
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
    assert [p.fecha for p in ps] == ["2012-04-22", "2012-04-29"]


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

#!/usr/bin/env python3
"""Tests del cruce contra la tabla de posiciones.

Este chequeo es el unico del repo que puede decidir cual de dos fuentes tiene
razon sobre un marcador. Por eso lo que mas importa probar es CUANDO SE CALLA:
un arbitro que opina de mas es peor que no tener arbitro.
"""
from __future__ import annotations

import re
from unittest import mock

from fad import correcciones, parser, posiciones
from fad.parser import Partido


def fila(pos, club, pts, pj, pg, pe, pp, gf, gc):
    return (f"|- style=\"text-align:center\"\n"
            f"||'''{pos}º'''||align=\"left\"|[[{club}]]\n"
            f"||'''{pts}'''||{pj}||{pg}||{pe}||{pp}||{gf}||{gc}||{gf - gc}")


def pagina(*filas, titulo="Tabla de posiciones"):
    return (f"== {titulo} ==\n<center>\n"
            "{| class=\"wikitable sortable\"\n"
            "|- style=\"background:#dddddd;\"\n"
            "! Pos\n! Equipo\n! Pts\n! PJ\n! PG\n! PE\n! PP\n! GF\n! GC\n! DIF\n"
            + "\n".join(filas) + "\n|}")


def zona(local, visita, gl, gv, z=""):
    return Partido(fecha="2010-01-01", local=local, visita=visita, goles_local=gl,
                   goles_visita=gv, fase="zonas", jornada="Fecha 1", zona=z)


# --------------------------------------------------------------------------
# leer la tabla
# --------------------------------------------------------------------------
def test_lee_la_tabla():
    t = posiciones.tabla(pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1)))
    assert t == {"Boca Juniors": (2, 3, 1)}


def test_el_center_entre_el_titulo_y_la_tabla_no_molesta():
    """Varias paginas meten un `<center>` en el medio. Pidiendo la tabla pegada
    al titulo, la de la B Nacional 2007-08 no se encontraba."""
    assert posiciones.tabla(pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1)))


def test_el_titulo_puede_decir_final():
    t = posiciones.tabla(pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1),
                                titulo="Tabla de posiciones final"))
    assert t == {"Boca Juniors": (2, 3, 1)}


def test_una_fila_que_no_cierra_sola_no_se_usa():
    """Una tabla mal tipeada no puede desmentir a nadie. `GF - GC == DIF` y
    `PG + PE + PP == PJ` la delatan sin costo."""
    rota = (f"|-\n||'''1º'''||align=\"left\"|[[Boca Juniors]]\n"
            f"||'''4'''||2||1||1||0||3||1||99")          # DIF dice 99 y es 2
    assert posiciones.tabla(pagina(rota)) == {}


def test_una_pagina_sin_tabla_no_devuelve_nada():
    assert posiciones.tabla("== Resultados ==\nnada por aca") == {}


def test_una_wikitabla_que_cierra_con_la_plantilla_de_leyenda():
    """La Primera C 2010-11 escribe sus veinte filas en una wikitabla comun pero
    abajo, en vez del `|}`, pone `{{Tabla de posiciones fin}}` con los colores.
    Buscando solo `\\n|}` esa tabla no termina nunca: el codigo viejo la encontraba
    igual porque escaneaba la pagina entera y cerraba en la tabla de promedios,
    dos secciones mas abajo -- funcionaba de casualidad, y acotar la busqueda a la
    seccion la habria perdido entera."""
    texto = ("== Tabla de posiciones ==\n<center>\n"
             "{| class=\"wikitable sortable\"\n"
             "|- style=\"background:#dddddd;\"\n"
             "! Pos\n! Equipo\n! Pts\n! PJ\n! PG\n! PE\n! PP\n! GF\n! GC\n! DIF\n"
             + fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1) + "\n"
             "{{Tabla de posiciones fin\n|color1=#90EE90| texto1=Campeón.\n}}\n"
             "</center>\n\n== Tabla de promedios ==\nlo que sea\n")
    assert posiciones.tabla(texto) == {"Boca Juniors": (2, 3, 1)}


# --------------------------------------------------------------------------
# contrastar: sobre todo, cuando se calla
# --------------------------------------------------------------------------
def test_cuando_los_goles_cierran_no_dice_nada():
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1),
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 3))
    assert posiciones.contrastar(ps, p) == []


def test_un_gol_de_diferencia_se_denuncia():
    """La contradiccion de verdad: los mismos partidos, distintos goles."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 4, 1),      # dice 4, suman 3
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 3))
    avisos = posiciones.contrastar(ps, p)
    assert len(avisos) == 1 and "Boca Juniors" in avisos[0]


def test_si_no_coinciden_los_partidos_jugados_se_calla():
    """La tabla cuenta la fase regular; la pagina trae ademas el reducido y la
    promocion. Comparando goles sobre conjuntos distintos salian 38 avisos
    falsos, uno por cada club de un torneo con reducido."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 9, 9))       # PJ2 contra PJ1
    assert posiciones.contrastar(ps, p) == []


def test_los_partidos_de_eliminacion_no_cuentan():
    """Los del reducido estan en la misma pagina y no en la tabla.

    El caso esta armado para que se note: la tabla dice DOS partidos, y hay uno
    de zona y uno de eliminacion. Sumando los dos, el PJ coincide y la
    comparacion de goles se hace -- y denuncia. Contando solo el de zona, el PJ
    no coincide y el modulo se calla, que es lo correcto."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1),
          Partido(fecha="2010-06-01", local="Boca Juniors", visita="River Plate",
                  goles_local=5, goles_visita=0, fase="eliminacion", jornada="Final")]
    p = pagina(fila(1, "Boca Juniors", 6, 2, 2, 0, 0, 8, 0))
    assert posiciones.contrastar(ps, p) == []


def test_un_club_de_la_tabla_que_no_jugo_no_se_denuncia():
    """Puede ser la tabla de otra zona. No opinar es lo correcto."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1)]
    p = pagina(fila(1, "Racing Club", 4, 2, 1, 1, 0, 3, 1))
    assert posiciones.contrastar(ps, p) == []


# --------------------------------------------------------------------------
# los marcadores arbitrados
# --------------------------------------------------------------------------
def _prueba_de_no_copia(porque: str) -> bool:
    """Si la entrada invoca la divergencia selectiva, escrita como se escriba.

    Es una sola idea -- la fuente coincide con la pagina en los OTROS cruces entre
    los mismos clubes y difiere solo en el discutido, cosa que una fuente derivada
    no puede hacer -- y las entradas la redactan distinto. Buscar una frase
    literal hacia que el test dependiera de como quedo escrita la primera.
    """
    b = porque.lower()
    return ("no copia a wikipedia" in b or "no copian a wikipedia" in b
            or "no la esta copiando" in b or "no esta copiando" in b)


def test_los_marcadores_arbitrados_estan_justificados():
    """Cada correccion tiene que nombrar a su testigo.

    Antes el testigo era siempre la tabla de posiciones y el test pedia esa
    frase. Ya no alcanza: la tabla LOCALIZA el partido y no lo arbitra, y de los
    seis casos que se probaron contra la prensa, en dos la equivocada era ella.
    Asi que el testigo puede ser la tabla o una cronica -- pero tiene que estar
    nombrado, y una cronica solo vale si dice quien hizo los goles.

    LA TERCERA FORMA, y por que se agrego. La regla de los goleadores es un PROXY
    de lo que de verdad importa, que esta escrito en su propio motivo: "un
    marcador suelto en un sitio de estadisticas puede venir de la misma fuente
    que estamos tratando de verificar". Los goleadores valen porque no se copian
    de una tabla. Pero hay otra forma de mostrar que una fuente no esta copiando,
    y es mas directa: que COINCIDA con la pagina en los partidos de al lado y
    difiera solo en el que esta en discusion. Una fuente derivada coincidiria en
    todos.

    Esa prueba entro con el Argentino A 2010-11 Fecha 21, donde no hay cronica
    con goleadores al alcance -- la de La Capital solo existe en el Web Archive,
    que las herramientas no alcanzan -- y si hay dos archivos de resultados que
    dan el partido al reves que Wikipedia mientras reproducen su vecino tal cual.
    Se la acepta, pero hay que ESCRIBIRLA: el `porque` tiene que nombrar el
    partido en que la fuente coincide, para que se pueda auditar."""
    from fad import correcciones
    for m in correcciones.MARCADORES:
        assert len(m.porque) > 80, f"{m.jornada} {m.local}: la evidencia es muy flaca"
        tabla_ = "tabla de posiciones" in m.porque
        prensa = any(p in m.porque for p in ("gol", "Boletin"))
        # la tercera forma pide DOS cosas: que la fuente diverja, y que se diga
        # en que otro partido coincide. Sin lo segundo no se puede auditar.
        assert tabla_ or prensa or _prueba_de_no_copia(m.porque), (
            f"{m.jornada} {m.local}: el testigo no queda nombrado")


def test_la_prensa_arbitro_los_que_la_tabla_no_podia():
    """La tabla dice DONDE mirar y no QUIEN tiene razon. Cuando un torneo tiene
    dos partidos candidatos entre los mismos dos clubes -- la ida y la vuelta --
    la aritmetica no puede elegir, y ahi solo sirve una cronica."""
    from fad import correcciones
    por_prensa = [m for m in correcciones.MARCADORES
                  if "tabla de posiciones" not in m.porque]
    assert por_prensa, "ninguna correccion se apoya en la prensa: se perdio el metodo"
    for m in por_prensa:
        assert "gol" in m.porque or "Boletin" in m.porque or _prueba_de_no_copia(m.porque), (
            f"{m.jornada} {m.local}: sin tabla, sin goleadores y sin la prueba de "
            f"que la fuente no copia a la pagina, no hay evidencia")


def test_el_arbitraje_no_le_da_siempre_la_razon_al_mismo():
    """Que el metodo mide algo se ve en que no contesta siempre lo mismo. Si
    todos dijeran worldfootball, seria indistinguible de haberla elegido."""
    from fad import correcciones
    sin_cambio = [m for m in correcciones.MARCADORES if m.debe == m.dice]
    assert sin_cambio, "ninguno le da la razon a Wikipedia: sospechoso"


def test_los_arbitrados_se_pueden_buscar_por_pagina():
    from fad import correcciones
    clave = correcciones.arbitrados("Campeonato de Primera B Nacional 2010-11")
    assert ("Fecha 22", "San Martín (T)", "Patronato") in clave
    assert correcciones.arbitrados("Una Pagina Cualquiera") == set()


# --------------------------------------------------------------------------
# de que lado esta el error
# --------------------------------------------------------------------------
def test_un_club_solo_desviado_acusa_a_la_tabla():
    """Un marcador mal leido toca siempre a DOS clubes: al que hizo el gol de mas
    y al que lo recibio. Un club solo, sin pareja, no puede venir de un partido.

    Es el caso de Platense en la B Nacional 2009-10, y el error de tipeo es doble
    -- los dos numeros bajos por uno --, asi que deja intactos la diferencia de
    gol, los puntos y el ganados-empatados-perdidos."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 2, 0),      # los DOS bajos por uno
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 3))
    avisos = posiciones.contrastar(ps, p)
    assert len(avisos) == 1
    assert "la fila de la tabla este mal transcripta" in avisos[0]


def test_dos_clubes_desviados_no_acusan_a_la_tabla():
    """Con dos, la explicacion del partido mal leido vuelve a estar sobre la mesa
    y el aviso no se pronuncia."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 4, 1),
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 4))
    avisos = posiciones.contrastar(ps, p)
    assert len(avisos) == 2
    assert all("puede venir de un partido mal leido" in a for a in avisos)


# --------------------------------------------------------------------------
# la tabla escrita con plantillas
# --------------------------------------------------------------------------
def _plantillas(*equipos_, titulo="Tabla de posiciones final"):
    filas = "\n".join(
        "{{Tabla de posiciones equipo|pos=%02d|g=%d|e=%d|p=%d|gf=%d|gc=%d|eq=[[%s|%s]]}}"
        % (i + 1, g, e, pe, gf, gc, f"Club Atlético {n}", n)
        for i, (n, g, e, pe, gf, gc) in enumerate(equipos_))
    return f"== {titulo} ==\n{{{{Tabla de posiciones inicio}}}}\n{filas}\n{{{{Tabla de posiciones fin}}}}\n"


def test_lee_la_tabla_escrita_con_plantillas():
    """Varias paginas no usan una wikitable sino una lista de plantillas, una por
    club. Buscando solo `{|` se perdian enteras, y con ellas el arbitro."""
    t = posiciones.tabla(_plantillas(("Boca Juniors", 1, 1, 0, 3, 1)))
    assert t == {"Boca Juniors": (2, 3, 1)}


def test_el_wikilink_del_equipo_no_parte_el_nombre():
    """`eq=[[Club Atlético San Telmo|San Telmo]]` lleva un `|` adentro. Partiendo
    los parametros por `|` a secas, el club queda llamandose
    "[[Club Atlético San Telmo" y no lo reconoce nadie."""
    t = posiciones.tabla(_plantillas(("San Telmo", 1, 0, 1, 2, 2)))
    assert list(t) == ["San Telmo"]


def test_solo_la_tabla_final_y_no_la_de_la_primera_rueda():
    """Varias paginas publican tambien la parcial de la primera rueda, con los
    mismos clubes y la mitad de los partidos. Si esa pisa a la final, los clubes
    quedan con la mitad del PJ y el cruce se calla por PJ distinto.

    Las dos tablas van una atras de la otra y con su propio titulo: es la forma
    en que aparecen en la pagina, y es lo que obliga a que decida la regla de mas
    partidos y no el orden."""
    texto = (_plantillas(("Boca Juniors", 10, 5, 4, 30, 20))
             + _plantillas(("Boca Juniors", 5, 2, 2, 15, 10),
                           titulo="Tabla de posiciones parcial de la primera rueda"))
    assert posiciones.tabla(texto)["Boca Juniors"] == (19, 30, 20)


def test_la_parcial_tampoco_gana_si_viene_primero():
    """El orden no puede ser lo que decide. Antes se leia la primera seccion y
    nada mas, asi que una pagina que publicara la parcial arriba habria dado el
    PJ de la mitad de la temporada sin que se notara."""
    texto = (_plantillas(("Boca Juniors", 5, 2, 2, 15, 10),
                         titulo="Tabla de posiciones parcial de la primera rueda")
             + _plantillas(("Boca Juniors", 10, 5, 4, 30, 20)))
    assert posiciones.tabla(texto)["Boca Juniors"] == (19, 30, 20)


# --------------------------------------------------------------------------
# torneos por zonas: una tabla por zona, y todas se llaman igual
# --------------------------------------------------------------------------
def test_lee_las_tablas_de_todas_las_zonas():
    """El titulo NO distingue las zonas: las dos se llaman "Tabla de posiciones
    final" y lo que cambia es el `== Zona A ==` de arriba. Leyendo solo la
    primera, la mitad de la pagina se cruzaba contra nada -- en el Federal A
    2019-20 los quince clubes de la Zona B volvian sin tabla, y en la Primera C
    2026 la Zona B escondia dos contradicciones que el aviso nunca denuncio.
    Son 91 de las 279 paginas del catalogo."""
    texto = ("== Zona A ==\n"
             + _plantillas(("Boca Juniors", 1, 1, 0, 3, 1), titulo="Tabla de posiciones final")
             + "== Zona B ==\n"
             + _plantillas(("River Plate", 2, 0, 0, 5, 0), titulo="Tabla de posiciones final"))
    assert posiciones.tabla(texto) == {"Boca Juniors": (2, 3, 1), "River Plate": (2, 5, 0)}


def test_una_zona_sin_tabla_no_tapa_a_la_otra():
    """La Zona B puede no tener tabla y la Zona A si. Nada obliga a que la pagina
    sea simetrica."""
    texto = ("== Zona A ==\n"
             + _plantillas(("Boca Juniors", 1, 1, 0, 3, 1), titulo="Tabla de posiciones")
             + "== Zona B ==\n== Resultados ==\nnada por aca\n")
    assert posiciones.tabla(texto) == {"Boca Juniors": (2, 3, 1)}


def test_un_desvio_en_la_segunda_zona_se_denuncia():
    """El punto del arreglo, medido donde importa: el aviso tiene que salir aunque
    el club este en la zona que antes no se leia."""
    texto = ("== Zona A ==\n"
             + pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1), titulo="Tabla de posiciones final")
             + "\n== Zona B ==\n"
             + pagina(fila(1, "River Plate", 4, 2, 1, 1, 0, 9, 9), titulo="Tabla de posiciones final"))
    ps = [zona("Boca Juniors", "Talleres (C)", 3, 1), zona("Talleres (C)", "Boca Juniors", 0, 0),
          zona("River Plate", "Newell's Old Boys", 1, 1), zona("Newell's Old Boys", "River Plate", 1, 1)]
    avisos = posiciones.contrastar(ps, texto)
    assert len(avisos) == 1 and avisos[0].startswith("River Plate:")


def test_una_nota_al_pie_pegada_al_nombre_no_tira_al_club():
    """`eq=[[Club Atlético Colón|Colón]]{{refn|group="n."|Se le descontaron 6
    puntos...}}`. La nota queda pegada al nombre, `canonizar` no lo reconoce y el
    club se cae del cruce -- calladito, porque `contrastar` saltea a los clubes
    que no estan en las dos partes.

    Y no es cualquier club: el que tiene quita de puntos es justo el que hay que
    mirar. Eran doce, entre quitas y clasificaciones a copas."""
    texto = ("== Tabla de posiciones ==\n"
             "{{Tabla de posiciones equipo|pos=20|g=3|e=3|p=13|gf=8|gc=25|desc=6"
             "|eq=[[Club Atlético Colón|Colón]]{{refn|group=\"n.\"|name=\"descol\""
             "|Se le descontaron 6 puntos por una sanción impuesta por [[FIFA]]."
             "{{cita publicación|autores=AFA|título=Boletín N.º 4838}}}}}}\n")
    assert posiciones.tabla(texto) == {"Colón": (19, 8, 25)}


def test_un_pipe_de_mas_antes_del_color_no_queda_en_el_nombre():
    """`eq=[[...|Boca Juniors]]||color=#cfc` y `eq=[[...|Rosario Central]]|#color=#cfc`
    son las dos formas que aparecen en las Copas de la Liga. Cortando en `|color=`
    a secas, el club terminaba llamandose "Boca Juniors|"."""
    doble = ("== Tabla de posiciones ==\n"
             "{{Tabla de posiciones equipo|pos=2|g=7|e=6|p=1|gf=19|gc=11"
             "|eq=[[Club Atlético Boca Juniors|Boca Juniors]]||color=#cfc}}\n")
    numeral = ("== Tabla de posiciones ==\n"
               "{{Tabla de posiciones equipo|pos=4|g=6|e=5|p=3|gf=17|gc=13"
               "|eq=[[Club Atlético Rosario Central|Rosario Central]]|#color=#cfc|color=#cfc}}\n")
    assert posiciones.tabla(doble) == {"Boca Juniors": (14, 19, 11)}
    assert posiciones.tabla(numeral) == {"Rosario Central": (14, 17, 13)}


def test_la_basura_del_eq_se_limpia_aunque_el_padron_no_conozca_al_club():
    """Los dos tests de arriba pasan igual si no se limpia nada, porque el club
    lo resuelve `canonizar` POR EL ARTICULO y el nombre sucio ni se mira. La
    limpieza recien se nota cuando el padron no conoce al club: ahi `canonizar`
    devuelve el nombre tal cual, y si viene sucio entra sucio.

    Es el caso que hay que cubrir, porque es el unico en que la suciedad
    sobrevive hasta el dato. Un club nuevo o mal linkeado cae siempre aca."""
    con_nota = ("== Tabla de posiciones ==\n"
                "{{Tabla de posiciones equipo|pos=1|g=1|e=1|p=0|gf=3|gc=1"
                "|eq=[[Club Deportivo Inexistente de Prueba|Inexistente de Prueba]]"
                "{{refn|group=\"n.\"|Se le descontaron 3 puntos.}}}}\n")
    sin_enlace = ("== Tabla de posiciones ==\n"
                  "{{Tabla de posiciones equipo|pos=1|g=1|e=1|p=0|gf=3|gc=1"
                  "|eq=Inexistente de Prueba|#color=#cfc}}\n")
    assert list(posiciones.tabla(con_nota)) == ["Inexistente de Prueba"]
    assert list(posiciones.tabla(sin_enlace)) == ["Inexistente de Prueba"]


def test_el_articulo_sale_del_wikilink_y_no_del_nombre_visible():
    """El articulo desambigua, y en el `eq=` esta ahi mismo. Antes se resolvia por
    un mapa de nombres visibles de toda la pagina, que falla justo cuando la tabla
    y los partidos escriben distinto al mismo club.

    El testigo es un club al que el nombre visible manda al lugar equivocado:
    "Gimnasia" sola es el de La Plata o el de Mendoza segun el articulo."""
    mendoza = ("== Tabla de posiciones ==\n"
               "{{Tabla de posiciones equipo|pos=1|g=1|e=1|p=0|gf=3|gc=1"
               "|eq=[[Club Atlético Gimnasia y Esgrima (Mendoza)|Gimnasia]]}}\n")
    plata = ("== Tabla de posiciones ==\n"
             "{{Tabla de posiciones equipo|pos=1|g=1|e=1|p=0|gf=3|gc=1"
             "|eq=[[Club de Gimnasia y Esgrima La Plata|Gimnasia]]}}\n")
    assert list(posiciones.tabla(mendoza)) != list(posiciones.tabla(plata))
    assert list(posiciones.tabla(plata)) == ["Gimnasia y Esgrima (LP)"]


def test_el_color_no_se_lee_como_nombre():
    texto = ("== Tabla de posiciones ==\n"
             "{{Tabla de posiciones equipo|pos=01|g=1|e=1|p=0|gf=3|gc=1"
             "|eq=[[Club Atlético Boca Juniors|Boca Juniors]]|color=#cfc}}\n")
    assert posiciones.tabla(texto) == {"Boca Juniors": (2, 3, 1)}


def test_una_plantilla_a_la_que_le_faltan_campos_no_entra():
    texto = ("== Tabla de posiciones ==\n"
             "{{Tabla de posiciones equipo|pos=01|g=1|eq=[[Boca Juniors]]}}\n")
    assert posiciones.tabla(texto) == {}


# --------------------------------------------------------------------------
# desbalance: la tabla contra si misma
# --------------------------------------------------------------------------
def test_una_tabla_que_balancea_no_dice_nada():
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1),
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 3))
    assert posiciones.desbalance(ps, p) == []


def test_una_tabla_que_no_balancea_se_denuncia_sin_mirar_la_grilla():
    """Todo gol convertido es un gol recibido. Si las dos columnas no suman lo
    mismo, la tabla se contradice sola y no hay nada que arbitrar.

    Aca River declara haber recibido 4 y Boca declara haber convertido 3. El gol
    que sobra no lo hizo nadie."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1),
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 4))
    avisos = posiciones.desbalance(ps, p)
    assert len(avisos) == 1
    assert "GF4" in avisos[0] and "GC5" in avisos[0]
    assert "sobra 1 gol en contra" in avisos[0]


def test_el_desbalance_no_repite_una_conclusion_ya_escrita(monkeypatch):
    """LOS DOS CHEQUEOS MIRAN LA MISMA TABLA DESDE DOS LADOS.

    Cuando un club se desvia solo y su desvio cuadra la tabla, `contrastar` ya
    concluyo que la fila esta mal, y esa conclusion se escribe UNA vez en
    `correcciones`. El aviso de desbalance la repetia en otras palabras: pasaba en
    tres paginas --Union en el Torneo Final 2013, Racing Club en la Copa de la
    Liga 2023 y J. J. de Urquiza en el Clausura de la Primera C 2024-- y decir dos
    veces lo mismo convierte un archivo de conclusiones en ruido."""
    from fad import correcciones

    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    # River declara 4 en contra y sus partidos dan 3: se desvia solo, y con nuestro
    # numero la tabla cierra.
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1),
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 4))
    assert len(posiciones.desbalance(ps, p, pagina="una pagina")) == 1, (
        "sin declarar, el aviso tiene que salir")

    monkeypatch.setattr(correcciones, "REVISADOS", (correcciones.Revisado(
        pagina="una pagina", club="River Plate", porque="de prueba"),))
    assert posiciones.desbalance(ps, p, pagina="una pagina") == []


def test_una_declaracion_que_no_explica_el_desbalance_no_lo_calla(monkeypatch):
    """LA DECLARACION SOLA NO ALCANZA, y es lo que evita que esto sea un
    interruptor. Se piden las tres cosas: un solo club desviado, que ese club este
    declarado, y que poner nuestro numero en su fila deje la tabla balanceada. Si
    el desbalance no lo explica esa fila, el aviso habla de otra cosa y sale."""
    from fad import correcciones

    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    # Se desvian DOS clubes --Boca en los goles a favor y River en los en contra--,
    # asi que arreglar la fila declarada no cuadra la tabla: falta la otra.
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 4, 1),
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 5))
    monkeypatch.setattr(correcciones, "REVISADOS", (correcciones.Revisado(
        pagina="una pagina", club="River Plate", porque="de prueba"),))
    assert len(posiciones.desbalance(ps, p, pagina="una pagina")) == 1


def test_un_club_declarado_que_desvia_de_los_dos_lados_no_calla_el_desbalance(monkeypatch):
    """LA TERCERA CONDICION, Y ES LA QUE MAS SE PARECE A UN ATAJO.

    No alcanza con que el club declarado sea el unico desviado: se pide que su
    arreglo sea DE UN SOLO LADO. Un club cuya fila esta mal en las dos columnas por
    montos distintos es el punto ciego del balance --el caso Platense de la B
    Nacional 2009-10--, y ahi el desbalance esta diciendo algo que la declaracion
    no dice."""
    from fad import correcciones

    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    # River: la tabla le pone GF3 (sus partidos dan 1) y GC4 (dan 3). Se desvia
    # solo, pero de los dos lados y por montos distintos.
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1),
               fila(2, "River Plate", 1, 2, 0, 1, 1, 3, 4))
    monkeypatch.setattr(correcciones, "REVISADOS", (correcciones.Revisado(
        pagina="una pagina", club="River Plate", porque="de prueba"),))
    assert len(posiciones.desbalance(ps, p, pagina="una pagina")) == 1


def test_el_aviso_dice_de_que_lado_sobran_los_goles():
    """La direccion es la mitad util: goles a favor que nadie declara haber
    recibido es un problema distinto al reciproco."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 5, 1),
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 3))
    avisos = posiciones.desbalance(ps, p)
    assert "sobran 2 goles a favor" in avisos[0]


def test_el_error_que_baja_las_dos_columnas_de_una_fila_es_invisible_al_balance():
    """El punto ciego, y es deliberado. Es el caso Platense de la B Nacional
    2009-10: la tabla le pone GF39 GC40 y sus partidos dan 40 y 41. Al estar los
    dos numeros bajos por uno, la resta se cancela y el total de la liga sigue
    cerrando.

    Este chequeo no lo ve, y esta bien: el que lo ve es `contrastar`. Que los dos
    miren cosas distintas es justamente para lo que sirven los dos."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 2, 0),     # los dos bajos por uno
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 3))
    assert posiciones.desbalance(ps, p) == []
    assert len(posiciones.contrastar(ps, p)) == 1


def test_si_la_tabla_lista_un_club_que_no_jugo_se_calla():
    """Sin los partidos de ese club sus goles no estan del otro lado, y el total
    no tendria por que cerrar. Puede ser la tabla de otra zona."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1),
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 4),
               fila(3, "Racing Club", 0, 2, 0, 0, 2, 0, 7))
    assert posiciones.desbalance(ps, p) == []


def test_si_hay_partidos_de_un_club_que_la_tabla_no_lista_se_calla():
    """El reciproco: un interzonal contra un club de la otra zona reparte goles
    afuera de la tabla. La Copa de la Liga 2023 es justo asi."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0),
          zona("Boca Juniors", "Racing Club", 2, 0)]
    p = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1),
               fila(2, "River Plate", 1, 2, 0, 1, 1, 1, 4))
    assert posiciones.desbalance(ps, p) == []


def test_el_desbalance_se_calla_si_no_coinciden_los_partidos_jugados():
    """Mismo motivo que en `contrastar`: si las dos partes no cuentan los mismos
    partidos, comparar sus goles no significa nada."""
    ps = [zona("Boca Juniors", "River Plate", 3, 1), zona("River Plate", "Boca Juniors", 0, 0)]
    p = pagina(fila(1, "Boca Juniors", 8, 4, 2, 2, 0, 3, 1),      # dice 4 partidos, jugaron 2
               fila(2, "River Plate", 2, 4, 0, 2, 2, 1, 4))
    assert posiciones.desbalance(ps, p) == []


def test_una_pagina_sin_tabla_no_desbalancea():
    ps = [zona("Boca Juniors", "River Plate", 3, 1)]
    assert posiciones.desbalance(ps, "== Resultados ==\nnada por aca") == []


# --------------------------------------------------------------------------
# fuera_del_padron: la fila que se caia sin decir nada
# --------------------------------------------------------------------------
def test_un_club_conocido_no_se_denuncia():
    assert posiciones.fuera_del_padron(pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1))) == []


def test_un_club_que_el_padron_no_conoce_se_denuncia():
    """El nombre de la tabla no pasaba por ningun control. El del padron mira los
    clubes de los PARTIDOS; la tabla entra por otra puerta y `canonizar` devuelve
    intacto lo que no reconoce, asi que la fila quedaba a nombre de un club que no
    existe y se caia del cruce en silencio."""
    avisos = posiciones.fuera_del_padron(
        pagina(fila(1, "Club Inexistente de Prueba", 4, 2, 1, 1, 0, 3, 1)))
    assert len(avisos) == 1 and "Club Inexistente de Prueba" in avisos[0]


def test_el_sup_de_la_llamada_al_pie_no_se_pega_al_nombre():
    """La Primera B 2015 escribe `[[Club Social y Deportivo Merlo|Deportivo Merlo]]
    <sup>1</sup>`, y el club terminaba llamandose "Deportivo Merlo 1" -- que no
    esta en el padron, asi que su fila se caia del cruce.

    El arreglo es sacar el articulo del wikilink de la celda cruda, igual que en
    las plantillas: la llamada al pie queda afuera sola."""
    sucia = ("|- style=\"text-align:center\"\n"
             "||'''1º'''||align=\"left\"|[[Club Social y Deportivo Merlo|Deportivo Merlo]] <sup>1</sup>\n"
             "||'''4'''||2||1||1||0||3||1||2")
    assert posiciones.tabla(pagina(sucia)) == {"Deportivo Merlo": (2, 3, 1)}
    assert posiciones.fuera_del_padron(pagina(sucia)) == []


def test_solo_el_wikilink_de_la_fila_separa_a_dos_clubes_que_se_ven_igual():
    """El testigo del wikilink de la wikitabla, cuando NADA MAS puede resolverlo.

    Los otros dos tests de esta parte pasan igual si la celda se resuelve por el
    nombre visible, porque `articulos_de_la_pagina` termina dando el mismo
    articulo por otro camino. Aca no: si la pagina escribe dos clubes distintos
    con el mismo nombre visible, ese indice se abstiene a proposito -- devuelve
    {} -- y el unico dato que queda es el enlace de la propia fila.

    Va con su historia porque es la segunda vez que pasa lo mismo en el repo: a
    este mutante lo mataba el test del `<sup>` de "Deportivo Merlo 1", y cuando
    `limpiar` aprendio a sacar la llamada al pie sola, el wikilink dejo de hacer
    falta ALLI y el mutante quedo vivo sin que ningun test se pusiera rojo. Un
    arreglo en un lado apaga el testigo del otro."""
    dos = pagina("|- style=\"text-align:center\"\n"
                 "||'''1º'''||align=\"left\"|"
                 "[[Club Atlético Gimnasia y Esgrima (Mendoza)|Gimnasia]]\n"
                 "||'''4'''||2||1||1||0||3||1||2",
                 "|- style=\"text-align:center\"\n"
                 "||'''2º'''||align=\"left\"|"
                 "[[Club de Gimnasia y Esgrima La Plata|Gimnasia]]\n"
                 "||'''1'''||2||0||1||1||1||3||-2")
    assert posiciones.tabla(dos) == {"Gimnasia y Esgrima (M)": (2, 3, 1),
                                     "Gimnasia y Esgrima (LP)": (2, 1, 3)}


def test_el_wikilink_de_la_wikitabla_desambigua_igual_que_en_la_plantilla():
    """El articulo manda sobre el nombre visible en los dos formatos, no en uno."""
    mendoza = ("|-\n||'''1º'''||align=\"left\"|"
               "[[Club Atlético Gimnasia y Esgrima (Mendoza)|Gimnasia]]\n"
               "||'''4'''||2||1||1||0||3||1||2")
    plata = ("|-\n||'''1º'''||align=\"left\"|"
             "[[Club de Gimnasia y Esgrima La Plata|Gimnasia]]\n"
             "||'''4'''||2||1||1||0||3||1||2")
    assert list(posiciones.tabla(pagina(mendoza))) != list(posiciones.tabla(pagina(plata)))
    assert list(posiciones.tabla(pagina(plata))) == ["Gimnasia y Esgrima (LP)"]


def test_la_nota_al_pie_pegada_al_eq_sin_wikilink_no_se_lee_como_nombre():
    """El Federal A 2022 escribe `eq=Huracán Las Heras{{refn|group=n.|Se le
    descontaron 3 puntos...`. La rama del wikilink ya estaba a salvo; la del club
    escrito a mano no, y justo el que lleva nota al pie es el de la quita de
    puntos. Con esa fila afuera, el cruce de la pagina entera se debilitaba."""
    texto = ("== Tabla de posiciones ==\n"
             "{{Tabla de posiciones equipo|pos=14|g=8|e=14|p=10|gf=23|gc=26|desc=3"
             "|eq=Huracán Las Heras{{refn|group=n.|Se le descontaron 3 puntos.}}\n")
    assert posiciones.tabla(texto) == {"Huracán Las Heras": (32, 23, 26)}
    assert posiciones.fuera_del_padron(texto) == []


def test_si_la_plantilla_va_adelante_el_nombre_queda_ilegible_pero_DENUNCIADO():
    """Este caso no tiene arreglo por este lado y el test esta para decirlo.

    Si el `eq=` arranca con una plantilla (`eq={{bandera|Mendoza}} Huracán Las
    Heras`), `_FILA_PLANTILLA` corta la fila entera en el primer `}}` -- que es el
    de la bandera -- y el nombre se pierde antes de que este codigo lo vea.
    Cortar en el `{{` dejaria la celda vacia y la fila se saltearia en silencio.

    Por eso el fallback devuelve el crudo aunque venga sucio: un nombre ilegible
    queda como club desconocido y `fuera_del_padron` lo denuncia, mientras que una
    celda vacia hace desaparecer la fila sin que nadie se entere. Vacio no es lo
    mismo que ilegible, y entre los dos males este proyecto ya eligio una vez.

    No pasa en ninguna de las 131 paginas de hoy; el test fija la conducta para
    cuando pase."""
    texto = ("== Tabla de posiciones ==\n"
             "{{Tabla de posiciones equipo|pos=1|g=1|e=1|p=0|gf=3|gc=1"
             "|eq={{bandera|Mendoza}} Huracán Las Heras}}\n")
    assert posiciones.tabla(texto), "la fila no puede desaparecer"
    assert len(posiciones.fuera_del_padron(texto)) == 1


def test_el_bloque_termina_en_el_proximo_encabezado_y_la_de_promedios_no_se_cuela():
    """La tabla de PROMEDIOS se escribe con la misma plantilla que la de
    posiciones, y vive dos secciones mas abajo en la misma pagina.

    Si el bloque no se corta en el proximo encabezado, esas filas entran como si
    fueran de la tabla de posiciones. Y ganan: el promedio se calcula sobre tres
    temporadas, asi que su PJ es siempre mayor y se lleva puesto el desempate por
    max-PJ. El club termina con los partidos de tres años donde tenia que tener
    los de uno, y el cruce contra los partidos parseados pasa a comparar cualquier
    cosa.

    Este test existe porque el mutante `sig = None` sobrevivio: el acotado estaba
    escrito y explicado, pero no habia nada que lo probara."""
    texto = ("== Tabla de posiciones ==\n"
             "{{Tabla de posiciones equipo|pos=1|g=1|e=1|p=0|gf=3|gc=1"
             "|eq=[[Club Atlético Boca Juniors|Boca Juniors]]}}\n"
             "\n== Tabla de promedios ==\n"
             "{{Tabla de posiciones equipo|pos=1|g=40|e=20|p=54|gf=99|gc=98"
             "|eq=[[Club Atlético Boca Juniors|Boca Juniors]]}}\n")
    assert posiciones.tabla(texto) == {"Boca Juniors": (2, 3, 1)}


# --------------------------------------------------------------------------
# la tabla que no vive bajo "Tabla de posiciones"
# --------------------------------------------------------------------------
def _wikitabla(*filas, ancho=""):
    return ("{| class=\"wikitable\"\n"
            "|- style=\"background:#dddddd;\"\n"
            f"!{ancho} Pos\n!{ancho} Equipo\n!{ancho} Pts\n!{ancho} PJ\n!{ancho} PG\n"
            f"!{ancho} PE\n!{ancho} PP\n!{ancho} GF\n!{ancho} GC\n!{ancho} DIF\n"
            + "\n".join(filas) + "\n|}")


def test_una_tabla_bajo_cualquier_titulo_se_encuentra_por_sus_columnas():
    """El Torneo Argentino A pone sus tablas bajo `=== Primera fase ===`, sin la
    frase "Tabla de posiciones" en ningun lado. La pagina tenia arbitro y el
    arbitro no lo encontraba, y eso importo: cuando aparecio que esa misma pagina
    se habia copiado dos jornadas a si misma, fueron sus tablas las que dijeron
    cual version era la buena.

    Una tabla de posiciones SE DECLARA: su encabezado nombra las columnas."""
    texto = "== Primera fase ==\n" + _wikitabla(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1))
    assert posiciones.tabla(texto) == {"Boca Juniors": (2, 3, 1)}


def test_la_de_promedios_no_entra_aunque_tenga_las_mismas_columnas():
    """Su PJ es de tres temporadas, asi que si entra se lleva puesto el desempate
    por max-PJ: el club termina con los partidos de tres anios donde tenia que
    tener los de uno."""
    texto = ("== Tabla de promedios ==\n"
             + _wikitabla(fila(1, "Boca Juniors", 90, 114, 60, 30, 24, 180, 100).replace(
                 "! DIF", "! Prom")))
    assert posiciones.tabla("== Tabla de promedios ==\n"
                            + _wikitabla(fila(1, "Boca Juniors", 90, 114, 60, 30, 24, 180, 100))) == {}


def test_la_de_descenso_tampoco_aunque_sea_una_tabla_de_posiciones_valida():
    """Y este es el caso medido, no el hipotetico. La tabla de descenso del
    Argentino A 2005-06 es la SUMA de las cuatro de zona -- coincide con ellas en
    17 de 23 clubes --, asi que no aporta nada; pero trae el doble de partidos y
    por max-PJ las desplaza. Encima trae su propio error: a 9 de Julio (R) le
    pone GF29 donde las de zona suman 39."""
    texto = ("== Tablas de descenso ==\n"
             + _wikitabla(fila(1, "Boca Juniors", 40, 22, 12, 4, 6, 29, 32)))
    assert posiciones.tabla(texto) == {}


def test_la_de_posiciones_gana_aunque_la_de_descenso_traiga_mas_partidos():
    """Las dos juntas, que es como estan en la pagina real."""
    texto = ("== Torneo Apertura ==\n"
             + _wikitabla(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1))
             + "\n== Tablas de descenso ==\n"
             + _wikitabla(fila(1, "Boca Juniors", 40, 22, 12, 4, 6, 29, 32)))
    assert posiciones.tabla(texto) == {"Boca Juniors": (2, 3, 1)}, (
        "la de descenso trae mas partidos y no puede ganar el desempate por max-PJ")


# --------------------------------------------------------------------------
# el alcance: cada tabla contra los partidos de SU fase
# --------------------------------------------------------------------------
def _de_llave(llave, local, visita, gl, gv):
    p = zona(local, visita, gl, gv)
    p.llave = llave
    return p


def test_cada_tabla_se_compara_contra_los_partidos_de_su_fase():
    """Una pagina con Apertura y Clausura tiene una tabla por torneo, cada una de
    once fechas, mientras que la suma del torneo entero da veintidos. Comparando
    contra el total, el PJ no coincide en NINGUN club y el cruce se saltea a
    todos: la pagina tiene tabla y no tiene arbitro igual.

    Aca la del Apertura dice 4 goles y su partido tiene 3."""
    texto = ("== Torneo Apertura ==\n"
             + _wikitabla(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 4, 1))
             + "\n== Torneo Clausura ==\n"
             + _wikitabla(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 2, 0)))
    ps = [_de_llave("Torneo Apertura", "Boca Juniors", "River Plate", 3, 1),
          _de_llave("Torneo Clausura", "Boca Juniors", "River Plate", 2, 0)]
    avisos = posiciones.contrastar(ps, texto)
    assert len(avisos) == 1
    assert "Boca Juniors" in avisos[0] and "GF4" in avisos[0]


def test_el_alcance_solo_se_usa_si_la_seccion_es_una_llave_de_los_partidos():
    """La condicion que lo hace seguro. En una pagina normal la tabla cuelga de
    `== Tabla de posiciones ==`, que no es la llave de ningun partido, asi que el
    alcance queda vacio y se compara contra el torneo entero, como siempre."""
    texto = "== Tabla de posiciones ==\n" + _wikitabla(fila(1, "Boca Juniors", 6, 2, 2, 0, 0, 5, 1))
    ps = [_de_llave("Torneo Apertura", "Boca Juniors", "River Plate", 3, 1),
          _de_llave("Torneo Clausura", "Boca Juniors", "River Plate", 2, 0)]
    assert posiciones.contrastar(ps, texto) == [], "los dos partidos suman 5-1, como dice la tabla"


def test_una_wikitabla_que_no_declara_las_columnas_no_es_una_tabla_de_posiciones():
    """El filtro por columnas tiene que rechazar, no solo aceptar.

    Sus filas cierran solas -- `GF - GC == DIF` y `PG + PE + PP == PJ` -- asi que
    la guarda numerica de `_por_wikitabla` las deja pasar sin chistar. Lo unico
    que la separa de una tabla de posiciones es que su encabezado no nombra las
    columnas, y eso es exactamente lo que se prueba aca."""
    texto = ("== Equipos participantes ==\n"
             "{| class=\"wikitable\"\n"
             "|- style=\"background:#dddddd;\"\n"
             "! A\n! Equipo\n! B\n! C\n! D\n! E\n! F\n! G\n! H\n! I\n"
             "|-\n||'''1º'''||align=\"left\"|[[Boca Juniors]]\n"
             "||'''4'''||2||1||1||0||3||1||2\n|}")
    assert posiciones.tabla(texto) == {}


def test_las_zonas_en_formato_plantilla_se_leen_todas():
    """El otro formato -- `{{Tabla de posiciones equipo}}` -- no tiene fila de
    encabezado, asi que no puede entrar por el camino de las columnas: entra solo
    por el titulo de la seccion. Leyendo una sola de esas secciones, la mitad de
    una pagina por zonas se cruza contra nada.

    Este test existe porque el mutante que trunca `_bloques` a la primera seccion
    dejo de morir: el camino nuevo tapaba al viejo en las paginas de wikitablas,
    y en estas no hay nada que lo tape."""
    texto = ("== Zona A ==\n=== Tabla de posiciones ===\n"
             "{{Tabla de posiciones equipo|pos=1|g=1|e=1|p=0|gf=3|gc=1"
             "|eq=[[Club Atlético Boca Juniors|Boca Juniors]]}}\n"
             "\n== Zona B ==\n=== Tabla de posiciones ===\n"
             "{{Tabla de posiciones equipo|pos=1|g=2|e=0|p=0|gf=5|gc=2"
             "|eq=[[Club Atlético River Plate|River Plate]]}}\n")
    assert posiciones.tabla(texto) == {"Boca Juniors": (2, 3, 1), "River Plate": (2, 5, 2)}


def test_el_detector_de_padron_mira_las_mismas_tablas_que_el_cruce():
    """`tabla` y `fuera_del_padron` no pueden mirar cosas distintas.

    Miraban: `tabla` leia los dos caminos -- el titulo de la seccion y las
    columnas declaradas -- y `fuera_del_padron` solo el primero. En una pagina
    cuyas tablas no dicen "Tabla de posiciones", el detector de padron devolvia
    cero aunque la tabla tuviera nombres que el padron no conoce. Y son justo los
    que hay que agregar para que esas filas entren al cruce."""
    texto = "== Primera fase ==\n" + _wikitabla(fila(1, "Club Inexistente de Prueba", 4, 2, 1, 1, 0, 3, 1))
    assert posiciones.tabla(texto), "la tabla se encuentra por sus columnas"
    avisos = posiciones.fuera_del_padron(texto)
    assert len(avisos) == 1 and "Club Inexistente de Prueba" in avisos[0]


def test_el_dif_positivo_se_escribe_con_signo_y_hay_que_leerlo():
    r"""`||+2` es como muchas paginas escriben la diferencia de gol cuando es
    positiva. Con un regex de `-?\d+` esa celda no cuenta como numero: la fila
    pierde una, el corte de las ultimas ocho columnas se corre, y la guarda de
    coherencia (`gf - gc == dif`) la descarta entera.

    Y descarta JUSTO A LOS PUNTEROS -- caen todas y solo las filas con diferencia
    positiva --, que es lo que lo hace dificil de ver: la tabla sigue existiendo,
    con la mitad de arriba faltando. En el Argentino A 2010-11 se perdian 8 de 24
    filas y el cruce inventaba un huerfano que no existia; en la Primera C
    2008-09, 10 de 20."""
    con_signo = ("|- style=\"text-align:center\"\n"
                 "||'''1º'''||align=\"left\"|[[Boca Juniors]]\n"
                 "||'''4'''||2||1||1||0||3||1||+2")
    assert posiciones.tabla(pagina(con_signo)) == {"Boca Juniors": (2, 3, 1)}


def test_el_dif_negativo_sigue_leyendose():
    """El reciproco, para que el arreglo no se lleve puesto el caso que ya andaba."""
    negativo = ("|- style=\"text-align:center\"\n"
                "||'''1º'''||align=\"left\"|[[Boca Juniors]]\n"
                "||'''1'''||2||0||1||1||1||3||-2")
    assert posiciones.tabla(pagina(negativo)) == {"Boca Juniors": (2, 1, 3)}


# --------------------------------------------------------------------------
# la fila que no tiene contra que cruzarse
# --------------------------------------------------------------------------
def test_denuncia_la_fila_de_un_club_que_no_jugo():
    """El hermano general de `fuera_del_padron`, y agarra mas que el: aquel pide
    que el nombre sea ilegible, y a este le alcanza con que la fila no enganche.

    El caso real es el Argentino A 2005-06: la tabla escribe "Juventud Unida" y
    la grilla "Juventud Unida Universitario". Los dos existen en el padron y son
    dos clubes de verdad, asi que nadie se quejaba y la fila se caia del cruce
    -- que ademas apagaba el chequeo de balance de esa tabla entera."""
    texto = pagina(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 3, 1),
                   fila(2, "River Plate", 0, 1, 0, 0, 1, 1, 3))
    ps = [zona("Boca Juniors", "Racing Club", 3, 1)]
    avisos = posiciones.sin_partidos(ps, texto)
    assert len(avisos) == 1 and "River Plate" in avisos[0]


def test_un_club_que_jugo_y_no_tiene_fila_no_se_denuncia():
    """La otra direccion no es un error: en toda revalida la tabla cubre a la
    mitad del torneo. Avisar por eso seria opinar de mas."""
    texto = pagina(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 3, 1))
    ps = [zona("Boca Juniors", "River Plate", 3, 1)]
    assert posiciones.sin_partidos(ps, texto) == []


def test_la_fila_se_mide_contra_su_alcance_y_no_contra_el_torneo():
    """Una tabla de zona tiene que cruzarse con los partidos de SU zona. Contra
    el torneo entero, un club que jugo en la otra fase alcanzaria para tapar el
    aviso, y la tabla del Apertura podria nombrar a cualquiera."""
    texto = ("== Torneo Apertura ==\n"
             + _wikitabla(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 3, 1),
                          fila(2, "River Plate", 0, 1, 0, 0, 1, 1, 3))
             + "\n== Torneo Clausura ==\n"
             + _wikitabla(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 2, 0)))
    ps = [_de_llave("Torneo Apertura", "Boca Juniors", "Racing Club", 3, 1),
          _de_llave("Torneo Clausura", "River Plate", "Boca Juniors", 0, 2)]
    avisos = posiciones.sin_partidos(ps, texto)
    assert len(avisos) == 1 and "River Plate" in avisos[0] and "Torneo Apertura" in avisos[0]


def test_el_homonimo_de_la_pagina_vale_tambien_para_la_tabla():
    """Las dos puertas -- partidos y tabla -- tienen que dar el mismo nombre. Si
    la tabla resolviera por su cuenta, el cruce no encontraria al club en las dos
    partes y se saltearia la fila, que es justo lo que el homonimo vino a
    arreglar. Se prueba con el caso real, no con uno inventado."""
    texto = pagina(fila(1, "Juventud Unida", 3, 1, 1, 0, 0, 3, 1))
    assert list(posiciones.tabla(texto)) == ["Juventud Unida"]
    assert list(posiciones.tabla(texto, pagina="Torneo Argentino A 2005-06")) == \
        ["Juventud Unida Universitario"]


# --------------------------------------------------------------------------
# la grilla: el nombre pelado que resuelve al club equivocado
# --------------------------------------------------------------------------
def _pagina_con_homonimo(enlace_del_pelado="", en_tabla="Juventud Unida Universitario"):
    """Una pagina cuya GRILLA escribe 'Juventud Unida' a secas y cuya TABLA
    nombra y enlaza a Juventud Unida Universitario, que es otro club."""
    return (f"Participantes: [[Club Atlético Juventud Unida Universitario|{en_tabla}]] "
            f"y [[Club Atlético Boca Juniors|Boca Juniors]]. {enlace_del_pelado}\n"
            + pagina(fila(1, "Club Atlético Juventud Unida Universitario", 3, 1, 1, 0, 0, 3, 1),
                     fila(2, "Boca Juniors", 0, 1, 0, 0, 1, 1, 3)))


def test_denuncia_el_nombre_pelado_que_la_pagina_nunca_enlaza():
    """El error que no falla nunca: la grilla escribe un nombre sin desambiguar,
    el padron lo resuelve solo, y lo resuelve al club equivocado. El partido
    queda prolijo -- con fecha, marcador y cancha -- a nombre de otro.

    Es el unico de los cuatro chequeos del cruce que mira la GRILLA."""
    ps = [zona("Juventud Unida", "Boca Juniors", 3, 1)]
    avisos = posiciones.homonimo_de_la_pagina(ps, _pagina_con_homonimo())
    assert len(avisos) == 1
    assert "Juventud Unida" in avisos[0] and "Universitario" in avisos[0]


def test_si_la_pagina_enlaza_al_club_pelado_no_hay_nada_que_denunciar():
    """Un wikilink no se adivina: con el articulo puesto la resolucion es segura.
    Callarse es lo correcto."""
    ps = [zona("Juventud Unida", "Boca Juniors", 3, 1)]
    texto = _pagina_con_homonimo("[[Club Deportivo y Social Juventud Unida|Juventud Unida]]")
    assert posiciones.homonimo_de_la_pagina(ps, texto) == []


def test_no_alcanza_con_que_el_homonimo_este_enlazado():
    """La tercera condicion, y la que hace el trabajo. Pedir solo que el homonimo
    aparezca enlazado deja catorce falsos de la Copa Argentina, donde
    'Independiente' pelado es el de Avellaneda. Que ademas tenga FILA DE TABLA los
    apaga a los catorce, porque la Copa es eliminacion directa y no publica
    tabla."""
    ps = [zona("Juventud Unida", "Boca Juniors", 3, 1)]
    texto = ("Participantes: [[Club Atlético Juventud Unida Universitario|"
             "Juventud Unida Universitario]] y [[Club Atlético Boca Juniors|Boca Juniors]].")
    assert posiciones.homonimo_de_la_pagina(ps, texto) == []


def test_un_club_desambiguado_no_se_denuncia():
    ps = [zona("Juventud Unida Universitario", "Boca Juniors", 3, 1)]
    assert posiciones.homonimo_de_la_pagina(ps, _pagina_con_homonimo()) == []


# --------------------------------------------------------------------------
# las filas que la guarda descarta en silencio
# --------------------------------------------------------------------------
def test_una_fila_que_no_cierra_se_denuncia_en_vez_de_desaparecer():
    """La guarda hace bien en no usarla -- una fila mal tipeada no puede
    desmentir a nadie --, pero descartarla callada deja al club sin arbitro. Y no
    lo puede suplir ningun otro chequeo: ni `contrastar` ni `desbalance` opinan
    sobre una fila que no llego a parsearse."""
    mala = ("|- style=\"text-align:center\"\n"
            "||'''1º'''||align=\"left\"|[[Almirante Brown]]\n"
            "||'''55'''||38||14||13||10||36||30||6")       # 14+13+10 = 37, no 38
    avisos = posiciones.filas_que_no_cierran(pagina(mala))
    assert len(avisos) == 1
    assert "Almirante Brown" in avisos[0] and "PJ38" in avisos[0] and "37" in avisos[0]


def test_dice_cual_de_las_dos_cuentas_falla():
    """Son dos guardas distintas y el que lo lea tiene que saber donde mirar."""
    mala = ("|- style=\"text-align:center\"\n"
            "||'''1º'''||align=\"left\"|[[Leandro N. Alem]]\n"
            "||'''32'''||38||6||14||18||32||48||-15")      # 32-48 = -16, no -15
    avisos = posiciones.filas_que_no_cierran(pagina(mala))
    assert len(avisos) == 1 and "DIF-15" in avisos[0] and "-16" in avisos[0]


def test_una_tabla_sana_no_denuncia_nada():
    assert posiciones.filas_que_no_cierran(
        pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1))) == []


# --------------------------------------------------------------------------
# el PJ: lo que `contrastar` mira para callarse
# --------------------------------------------------------------------------
def test_dos_clubes_corridos_lo_mismo_son_un_partido_entre_ellos():
    """Un partido toca a DOS clubes. Si dos se corren lo mismo y para el mismo
    lado, lo que hay es un partido entre esos dos, y el aviso los nombra a los
    dos en vez de mandar a buscar dos cosas."""
    texto = pagina(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 3, 1),
                   fila(2, "River Plate", 0, 1, 0, 0, 1, 1, 3),
                   fila(3, "Racing Club", 3, 1, 1, 0, 0, 2, 0),
                   fila(4, "Independiente", 0, 1, 0, 0, 1, 0, 2))
    ps = [zona("Boca Juniors", "River Plate", 3, 1),
          zona("Racing Club", "Independiente", 2, 0),
          zona("Racing Club", "Independiente", 1, 0)]      # uno de mas en la grilla
    avisos = posiciones.pj_que_no_coincide(ps, texto)
    assert len(avisos) == 1
    assert "Racing Club" in avisos[0] and "Independiente" in avisos[0]


# --------------------------------------------------------------------------
# el cuadro de llaves como arbitro de la fase final
# --------------------------------------------------------------------------
def _cuadro(*lineas: str) -> str:
    return "{{Copa de 4 clubes\n" + "\n".join(lineas) + "\n}}"


def test_el_tercer_numero_del_cuadro_no_es_una_tercera_pata():
    """Es el GLOBAL, y se lo reconoce por lo que es -- la suma de las dos patas,
    de los dos lados -- y no por su posicion: la misma plantilla se usa tambien
    para llaves a partido unico. Sobre el corpus separa 133 globales de 887 patas
    de verdad, y sin la regla cada uno entraba como un partido que nadie jugo."""
    texto = _cuadro("| RD1-team1 = [[Boca Juniors]]",
                    "| RD1-team2 = [[River Plate]]",
                    "| RD1-score1-1 = 2", "| RD1-score1-2 = 1", "| RD1-score1-3 = 3",
                    "| RD1-score2-1 = 0", "| RD1-score2-2 = 1", "| RD1-score2-3 = 1")
    cruces = parser.cruces_del_cuadro(texto)
    assert len(cruces) == 1
    assert cruces[0][4] == [(2, 0), (1, 1)], "el 3-1 es el global, no un partido"


def test_un_tercer_numero_que_no_es_la_suma_si_es_una_pata():
    """La regla mira la aritmetica y no la posicion. Si los tres numeros no
    cierran como global, son tres partidos y hay que decirlo."""
    texto = _cuadro("| RD1-team1 = [[Boca Juniors]]",
                    "| RD1-team2 = [[River Plate]]",
                    "| RD1-score1-1 = 2", "| RD1-score1-2 = 1", "| RD1-score1-3 = 5",
                    "| RD1-score2-1 = 0", "| RD1-score2-2 = 1", "| RD1-score2-3 = 0")
    assert parser.cruces_del_cuadro(texto)[0][4] == [(2, 0), (1, 1), (5, 0)]


def test_el_cuadro_no_dice_quien_fue_local():
    """Y por eso `cruces_del_cuadro` no lo devuelve. Contra las 761 patas que la
    grilla tambien tiene, la convencion "arriba es local en la ida" acierta el
    55.6%: una moneda. Sin esto, leer el cuadro como fuente le inventaria la
    localia a la mitad de las filas."""
    cruce = parser.cruces_del_cuadro(
        _cuadro("| RD1-team1 = [[Boca Juniors]]", "| RD1-team2 = [[River Plate]]",
                "| RD1-score1 = 1", "| RD1-score2 = 0"))[0]
    assert cruce[0] == "Boca Juniors" and cruce[2] == "River Plate"
    assert len(cruce) == 5, "no hay un campo de localia y no tiene que haberlo"


def test_el_cuadro_arbitra_la_fase_final():
    """Es el unico testigo que esa fase tiene: los otros chequeos cruzan contra la
    tabla de posiciones, y la tabla habla de las zonas."""
    texto = _cuadro("| RD1-team1 = [[Boca Juniors]]", "| RD1-team2 = [[River Plate]]",
                    "| RD1-score1 = 1", "| RD1-score2 = 0")
    assert posiciones.marcadores_del_cuadro(
        [zona("Boca Juniors", "River Plate", 1, 0)], texto) == []
    # y da igual quien figure de local, porque el cuadro no lo sabe
    assert posiciones.marcadores_del_cuadro(
        [zona("River Plate", "Boca Juniors", 0, 1)], texto) == []


def test_un_revisado_de_club_NO_calla_una_llave():
    """El alcance importa y se aprendio probando lo contrario.

    Dandole al chequeo del cuadro la puerta de `Revisado` por club, se callaron
    cinco avisos que nadie habia arbitrado: llaves del Argentino A 2005-06 que
    compartian UN club con el `Revisado` del partido dividido del Clausura, que
    habla de otra cosa. Un desvio de tabla es una afirmacion sobre un club; una
    llave lo es sobre dos.
    """
    texto = _cuadro("| RD1-team1 = [[Boca Juniors]]", "| RD1-team2 = [[River Plate]]",
                    "| RD1-score1 = 1", "| RD1-score2 = 0")
    ps = [Partido(fecha="2010-01-01", local="Boca Juniors", visita="River Plate",
                  goles_local=3, goles_visita=3, fase="eliminacion", jornada="Final")]
    assert posiciones.marcadores_del_cuadro(ps, texto, "Una Pagina")

    porclub = correcciones.Revisado(pagina="Una Pagina", club="Boca Juniors", porque="x")
    with mock.patch.object(correcciones, "REVISADOS", (porclub,)):
        assert posiciones.marcadores_del_cuadro(ps, texto, "Una Pagina"), \
            "un revisado de club no puede callar una llave"

    porpar = correcciones.Revisado(pagina="Una Pagina", club="River Plate",
                                   contra="Boca Juniors", porque="x")
    with mock.patch.object(correcciones, "REVISADOS", (porpar,)):
        assert posiciones.marcadores_del_cuadro(ps, texto, "Una Pagina") == [], \
            "y el de par si, en cualquier orden"


def test_un_revisado_de_llave_no_contesta_por_la_tabla():
    """Al reves tambien: el que verifica una llave no explica el desvio de una
    fila de posiciones, asi que `revisado()` no lo devuelve."""
    porpar = correcciones.Revisado(pagina="Una Pagina", club="Boca Juniors",
                                   contra="River Plate", porque="x")
    with mock.patch.object(correcciones, "REVISADOS", (porpar,)):
        assert correcciones.revisado("Una Pagina", "Boca Juniors") is None
        assert correcciones.revisado_llave("Una Pagina", "River Plate",
                                           "Boca Juniors") is porpar


def test_el_aviso_distingue_los_tres_estados():
    """Son TRES cosas distintas y el dato las separa solo. La pregunta no es si
    los dos clubes aparecen juntos en la pagina -- en una liga se cruzaron en la
    zona y eso no dice nada del cuadro -- sino si aparecen en la FASE FINAL.
    Con la pregunta mal hecha, 37 de los 42 avisos se llamaban "desacuerdo"
    cuando lo que pasa es que esas paginas no tienen fase final en la grilla."""
    texto = _cuadro("| RD1-team1 = [[Boca Juniors]]", "| RD1-team2 = [[River Plate]]",
                    "| RD1-score1 = 1", "| RD1-score2 = 0")
    solo = posiciones.marcadores_del_cuadro([zona("Racing Club", "Independiente", 0, 0)],
                                            texto)
    assert solo and "falta el partido" in solo[0]

    # cruzados en la fase regular, pero sin fase final entre ellos
    liga = posiciones.marcadores_del_cuadro([zona("Boca Juniors", "River Plate", 3, 3)],
                                            texto)
    assert liga and "no tiene fase final entre estos dos" in liga[0]

    # y el desacuerdo de verdad: hay llave entre los dos, con otro numero
    llave = Partido(fecha="2010-01-01", local="Boca Juniors", visita="River Plate",
                    goles_local=3, goles_visita=3, fase="eliminacion", jornada="Final")
    hay = posiciones.marcadores_del_cuadro([llave], texto)
    assert hay and "desacuerdo que arbitrar" in hay[0]


def test_el_revisado_tambien_calla_el_aviso_de_PJ():
    """De los tres cruces contra la tabla, este era el unico que no los miraba.

    El hueco tenia consecuencia: un desvio de PJ con la explicacion ya escrita no
    tenia forma de callarse. Pasa cuando la tabla cuenta un partido que el esquema
    no puede escribir -- los dos partidos arreglados de la ultima fecha del
    Clausura 2007 en el Argentino A 2006-07, que terminaron con un resultado
    distinto para cada club.
    """
    texto = pagina(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 3, 1),
                   fila(2, "River Plate", 0, 1, 0, 0, 1, 1, 3),
                   fila(3, "Racing Club", 3, 2, 1, 0, 1, 2, 1),
                   fila(4, "Independiente", 0, 2, 0, 0, 2, 0, 3))
    ps = [zona("Boca Juniors", "River Plate", 3, 1),
          zona("Racing Club", "Independiente", 2, 0)]      # a los dos les falta uno
    assert posiciones.pj_que_no_coincide(ps, texto, pagina="Una Pagina")

    revisados = tuple(correcciones.Revisado(pagina="Una Pagina", club=c, porque="x")
                      for c in ("Racing Club", "Independiente"))
    with mock.patch.object(correcciones, "REVISADOS", revisados):
        assert posiciones.pj_que_no_coincide(ps, texto, pagina="Una Pagina") == []


def test_el_revisado_de_PJ_vale_solo_en_su_pagina():
    """Como los otros dos: una verificacion se hizo sobre una tabla concreta."""
    texto = pagina(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 3, 1),
                   fila(2, "River Plate", 0, 1, 0, 0, 1, 1, 3),
                   fila(3, "Racing Club", 3, 2, 1, 0, 1, 2, 1),
                   fila(4, "Independiente", 0, 2, 0, 0, 2, 0, 3))
    ps = [zona("Boca Juniors", "River Plate", 3, 1),
          zona("Racing Club", "Independiente", 2, 0)]
    ajena = tuple(correcciones.Revisado(pagina="Otra Pagina", club=c, porque="x")
                  for c in ("Racing Club", "Independiente"))
    with mock.patch.object(correcciones, "REVISADOS", ajena):
        assert posiciones.pj_que_no_coincide(ps, texto, pagina="Una Pagina")


def test_un_desvio_de_PJ_tambien_es_un_desvio_para_los_huerfanos():
    """`clubes_desviados` se salteaba a los clubes con el PJ distinto, porque su
    unico consumidor comparaba goles. Con `Revisado` cerrando tambien desvios de
    PJ, esa omision hacia que la entrada que lo explica no enganchara con nada y
    `revisados_huerfanos` la denunciara por no existir un problema que si existe."""
    texto = pagina(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 3, 1),
                   fila(2, "River Plate", 0, 1, 0, 0, 1, 1, 3),
                   fila(3, "Racing Club", 3, 2, 1, 0, 1, 2, 1),
                   fila(4, "Independiente", 0, 2, 0, 0, 2, 0, 3))
    ps = [zona("Boca Juniors", "River Plate", 3, 1),
          zona("Racing Club", "Independiente", 2, 0)]
    crudos = posiciones.clubes_desviados(ps, texto, pagina="Una Pagina")
    assert {"Racing Club", "Independiente"} <= crudos

    r = correcciones.Revisado(pagina="Una Pagina", club="Racing Club", porque="x")
    with mock.patch.object(correcciones, "REVISADOS", (r,)):
        assert correcciones.revisados_huerfanos("Una Pagina", crudos) == []


def test_si_se_mueve_mas_de_media_tabla_no_opina():
    """La guarda no es un umbral sobre la diferencia sino sobre CUANTA TABLA SE
    MUEVE. Un club mal atribuido corre uno o dos de veinte; una tabla que cuenta
    otra cosa -- la fase regular contra una grilla que ademas trae el reducido --
    se mueve entera. Sin esta guarda son 67 avisos; con ella, 11."""
    texto = pagina(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 3, 1),
                   fila(2, "River Plate", 0, 1, 0, 0, 1, 1, 3))
    ps = [zona("Boca Juniors", "River Plate", 3, 1),
          zona("River Plate", "Boca Juniors", 0, 0)]       # los dos con uno de mas
    assert posiciones.pj_que_no_coincide(ps, texto) == []


def test_el_chequeo_se_calla_si_una_zona_explica_el_desvio():
    """El de arriba a traves del chequeo, que es lo que importa: probar la funcion
    sola no alcanza si el que la llama puede ignorarla.

    Tres clubes de una zona con dos partidos cada uno, y uno de ellos juega ademas
    un interzonal que la tabla no cuenta. Se mueve UN club de tres -- por debajo de
    la guarda de media tabla --, asi que sin esta regla el aviso sale.
    """
    texto = pagina(fila(1, "Boca Juniors", 4, 2, 1, 1, 0, 3, 1),
                   fila(2, "River Plate", 2, 2, 0, 2, 0, 1, 1),
                   fila(3, "Racing Club", 1, 2, 0, 1, 1, 1, 3))
    ps = [zona("Boca Juniors", "River Plate", 3, 1, z="Zona A"),
          zona("Boca Juniors", "Racing Club", 0, 0, z="Zona A"),
          zona("River Plate", "Racing Club", 1, 1, z="Zona A"),
          # el interzonal: solo lo juega Boca, y la tabla de la zona no lo cuenta
          zona("Boca Juniors", "Independiente", 2, 0, z="Interzonal")]
    assert posiciones.pj_que_no_coincide(ps, texto) == []


def test_cuando_el_pj_coincide_se_calla():
    texto = pagina(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 3, 1),
                   fila(2, "River Plate", 0, 1, 0, 0, 1, 1, 3))
    assert posiciones.pj_que_no_coincide([zona("Boca Juniors", "River Plate", 3, 1)], texto) == []


# --------------------------------------------------------------------------
# el cuadro de llaves: el segundo testigo de una copa
# --------------------------------------------------------------------------
def _con_cuadro(*equipos_):
    filas = "\n".join(f"| RD1-team{i:02d} = {e}" for i, e in enumerate(equipos_, 1))
    return "{{Copa de 4 clubes\n" + filas + "\n}}"


def test_denuncia_al_club_del_cuadro_cuyo_homonimo_es_el_que_juega():
    """La firma de una mala atribucion vista desde el cuadro. La Primera B 2014,
    2015 y 2017-18 escriben "Estudiantes" a secas ahi -- que el padron resuelve al
    de La Plata, un club de Primera -- mientras la grilla juega Estudiantes (BA).

    Importa donde importa: una copa no publica tabla de posiciones, asi que sus
    paginas son casi toda la region donde ningun otro chequeo puede opinar."""
    texto = _con_cuadro("[[Club Estudiantes de La Plata|Estudiantes]]", "Boca Juniors")
    ps = [zona("Estudiantes (BA)", "Boca Juniors", 1, 0)]
    avisos = posiciones.fuera_del_cuadro(ps, texto)
    assert len(avisos) == 1
    assert "Estudiantes (LP)" in avisos[0] and "Estudiantes (BA)" in avisos[0]


def test_el_cuadro_sin_enlace_se_desata_con_los_enlaces_de_su_pagina():
    """UN CUADRO CASI NUNCA ENLAZA, PERO SU PAGINA SI.

    Los seis clubes del cuadro de la Primera B 2014 estan a secas, y `Estudiantes`
    a secas lo resuelve el padron al de La Plata --un club de Primera--. Pero el
    MISMO documento enlaza `Club Atlético Estudiantes` en otro renglon: en su lista
    de participantes, en su tabla, en la grilla. Ese mapa ya lo junta
    `articulos_de_la_pagina`; lo que faltaba era usarlo aca.

    Sin esto hacia falta una declaracion a mano por pagina, y con esto la del 2014
    quedo sin uso."""
    texto = (_con_cuadro("Estudiantes", "Boca Juniors") +
             "\n[[Club Atlético Estudiantes|Estudiantes]] juega esta temporada.")
    ps = [zona("Estudiantes (BA)", "Boca Juniors", 1, 0)]
    assert posiciones.fuera_del_cuadro(ps, texto) == []

    # Y sin ese enlace en la pagina, el aviso sale: lo que resuelve es el enlace,
    # no el nombre.
    assert len(posiciones.fuera_del_cuadro(ps, _con_cuadro("Estudiantes", "Boca Juniors"))) == 1


def test_si_el_cuadro_y_la_grilla_coinciden_se_calla():
    texto = _con_cuadro("Boca Juniors", "River Plate")
    assert posiciones.fuera_del_cuadro([zona("Boca Juniors", "River Plate", 1, 0)], texto) == []


def test_los_que_faltan_sin_homonimo_van_en_UN_aviso():
    """Ahi lo que falta no es un nombre sino los PARTIDOS: la Copa Argentina
    2019-20 tiene un cuadro de 64 y la grilla trae 42. Es un hueco conocido y se
    dice en una linea, no en una por club."""
    texto = _con_cuadro("Boca Juniors", "River Plate", "Racing Club", "Independiente")
    avisos = posiciones.fuera_del_cuadro([zona("Boca Juniors", "River Plate", 1, 0)], texto)
    assert len(avisos) == 1
    assert "2 clubes" in avisos[0] and "Racing Club" in avisos[0] and "Independiente" in avisos[0]


def test_una_pagina_sin_cuadro_no_dice_nada():
    assert posiciones.fuera_del_cuadro([zona("Boca Juniors", "River Plate", 1, 0)],
                                       "== Resultados ==\nnada por aca") == []


def test_las_marcas_del_cuadro_no_son_clubes():
    """Un cuadro trae, mezcladas con los clubes, marcas que no lo son: `w/o` por
    walkover, `p.` por penales, `t. s.` por tiempo suplementario. Contarlas como
    clubes que faltan llenaria el aviso de basura."""
    texto = _con_cuadro("Boca Juniors", "w/o", "p.", "3")
    assert posiciones.fuera_del_cuadro([zona("Boca Juniors", "River Plate", 1, 0)], texto) == []


def test_el_wikilink_del_cuadro_no_se_parte_en_el_pipe():
    """Partir los parametros por cualquier `|` rompe el wikilink y el club pasa a
    llamarse "[[Arsenal Fútbol Club". Se parte a nivel cero."""
    from fad import parser as _p
    assert "Arsenal" in _p.clubes_del_cuadro(_con_cuadro("[[Arsenal Fútbol Club|Arsenal]]"))


def test_denuncia_el_nombre_del_cuadro_que_el_padron_no_reconoce():
    """Antes esto se salteaba en silencio, y el motivo era bueno: el cuadro trae
    marcas mezcladas con los clubes y avisar por cada una era peor que callarse.
    El costo era que las grafias que SOLO viven en el cuadro no las denunciaba
    nadie -- no entran por ningun partido, asi que `nombres_en_el_padron` tampoco
    las ve --. Se resolvio sacando el ruido en `clubes_del_cuadro`, no
    tolerandolo: de 26 nombres desconocidos quedo uno, y ese uno es real."""
    texto = _con_cuadro("Deportivo Inventado", "Boca Juniors")
    avisos = posiciones.fuera_del_cuadro([zona("Boca Juniors", "River Plate", 1, 0)], texto)
    assert any("Deportivo Inventado" in a and "no lo reconoce" in a for a in avisos)


def test_el_aviso_del_desconocido_dice_si_la_pagina_lo_enlaza():
    """Con enlace hay con que resolverlo -- se le agrega el articulo al padron --;
    sin enlace puede no haber forma, que es el caso de `Def. de Belgrano` en la
    Copa Argentina 2015-16, donde juegan los dos Defensores de Belgrano."""
    sin = posiciones.fuera_del_cuadro(
        [zona("Boca Juniors", "River Plate", 1, 0)], _con_cuadro("Deportivo Inventado"))
    assert "no lo enlaza" in sin[0]
    con = posiciones.fuera_del_cuadro(
        [zona("Boca Juniors", "River Plate", 1, 0)],
        _con_cuadro("[[Club Atlético Inventado|Deportivo Inventado]]"))
    assert "Club Atlético Inventado" in con[0] and "no lo enlaza" not in con[0]


def test_el_desconocido_no_tapa_a_los_otros_avisos():
    """Van los dos: el nombre que no resuelve es un problema del padron y el club
    que no juega es uno del cruce. Juntarlos perdiendo uno deja media pagina sin
    denunciar."""
    texto = _con_cuadro("Deportivo Inventado", "Racing Club", "Independiente", "Boca Juniors")
    avisos = posiciones.fuera_del_cuadro([zona("Boca Juniors", "River Plate", 1, 0)], texto)
    assert any("no lo reconoce" in a for a in avisos)
    assert any("no juegan ningun partido" in a for a in avisos)


def test_el_cuadro_se_cierra_por_balance_y_no_en_el_primer_cierre():
    """Adentro del cuadro hay otras plantillas -- `{{small}}`, `{{bandera}}` --,
    asi que el primer `}}` no es el del cuadro. Cerrando ahi, todo lo que sigue
    queda afuera y el cuadro pierde la mitad de sus clubes."""
    from fad import parser as _p
    texto = ("{{Copa de 4 clubes\n"
             "| RD1-team01 = {{bandera|Santa Fe}} Boca Juniors\n"
             "| RD1-team02 = River Plate\n"
             "| RD1-team03 = Racing Club\n"
             "}}")
    assert set(_p.clubes_del_cuadro(texto)) == {"Boca Juniors", "River Plate", "Racing Club"}


def test_las_marcas_no_entran_ni_al_leer_el_cuadro():
    """El filtro va en el LECTOR y no solo en el chequeo: `clubes_del_cuadro` es
    publico y lo puede usar otro. Ademas el chequeo descarta lo que el padron no
    conoce, asi que sin este test la guarda del lector no la prueba nadie."""
    from fad import parser as _p
    texto = "{{Copa de 2 clubes\n| RD1-team01 = w/o\n| RD1-team02 = p.\n| RD1-team03 = 3\n}}"
    assert _p.clubes_del_cuadro(texto) == {}


# --------------------------------------------------------------------------
def _tabla_gep(*filas: str) -> str:
    """Una tabla con las ocho columnas: PTS PJ G E P GF GC DIF."""
    cab = ('{| class="wikitable"\n'
           "! Pos !! Equipo !! Pts !! PJ !! G !! E !! P !! GF !! GC !! Dif\n")
    return "== Tabla de posiciones ==\n" + cab + "\n".join(filas) + "\n|}"


def _fila_gep(club, pts, pj, g, e, p, gf, gc):
    return (f"|-\n| 1 || {club} || {pts} || {pj} || {g} || {e} || {p} || "
            f"{gf} || {gc} || {gf - gc:+d}")


def test_si_el_gep_coincide_no_avisa():
    """Aunque los goles no cierren. Son dos preguntas distintas sobre la misma
    tabla, y esta funcion solo contesta la de quien gano."""
    ps = [zona("Boca Juniors", "River Plate", 3, 0),
          zona("River Plate", "Boca Juniors", 1, 1)]
    # Boca: 1 ganado 1 empatado; la tabla dice lo mismo pero le pone un gol de mas
    texto = _tabla_gep(_fila_gep("Boca Juniors", 4, 2, 1, 1, 0, 5, 1),
                       _fila_gep("River Plate", 1, 2, 0, 1, 1, 1, 5))
    assert posiciones.resultados_que_no_coinciden(ps, texto) == []


def test_avisa_cuando_la_tabla_le_da_el_partido_al_otro():
    ps = [zona("Boca Juniors", "River Plate", 0, 1),
          zona("River Plate", "Boca Juniors", 1, 1)]
    # la tabla le da a Boca una victoria que la grilla le da a River
    texto = _tabla_gep(_fila_gep("Boca Juniors", 4, 2, 1, 1, 0, 2, 2),
                       _fila_gep("River Plate", 1, 2, 0, 1, 1, 2, 2))
    avisos = posiciones.resultados_que_no_coinciden(ps, texto)
    assert len(avisos) == 2
    assert any("Boca Juniors" in a and "1-1-0" in a and "0-1-1" in a for a in avisos)


def test_el_aviso_no_propone_un_marcador():
    """Es un testigo de DIRECCION: dice quien gano, nunca cuantos goles. Un 2-1 y
    un 3-0 le dan lo mismo, asi que proponer marcador seria inventar la magnitud."""
    ps = [zona("Boca Juniors", "River Plate", 0, 1)]
    texto = _tabla_gep(_fila_gep("Boca Juniors", 3, 1, 1, 0, 0, 1, 1),
                       _fila_gep("River Plate", 0, 1, 0, 0, 1, 1, 1))
    aviso = posiciones.resultados_que_no_coinciden(ps, texto)[0]
    assert "PARTIDO ENTERO" in aviso
    # los unicos numeros que trae son G-E-P y PJ; no hay marcador propuesto
    assert not re.search(r"deber[ií]a|tendr[ií]a que|corregir a|marcador", aviso)


def test_con_distinto_PJ_no_opina():
    """Misma guarda que `contrastar` y por el mismo motivo: si las dos partes no
    cuentan los mismos partidos, comparar no significa nada."""
    ps = [zona("Boca Juniors", "River Plate", 0, 1)]
    texto = _tabla_gep(_fila_gep("Boca Juniors", 3, 2, 1, 1, 0, 1, 1),
                       _fila_gep("River Plate", 0, 2, 0, 1, 1, 1, 1))
    assert posiciones.resultados_que_no_coinciden(ps, texto) == []


def test_sumar_cuenta_los_resultados_junto_con_los_goles():
    """Van juntos y no en dos recorridos: son las dos mitades de la misma
    pregunta y tienen que salir del MISMO conjunto de partidos."""
    ps = [zona("Boca Juniors", "River Plate", 2, 0),
          zona("River Plate", "Boca Juniors", 1, 1)]
    assert posiciones.sumar(ps)["Boca Juniors"] == (2, 3, 1, 1, 1, 0)
    assert posiciones.sumar(ps)["River Plate"] == (2, 1, 3, 0, 1, 1)


def test_la_tabla_publica_sigue_devolviendo_tres():
    """`tabla` es la vieja y publica. Ensancharle la tupla obligaria a cada
    llamador a saber de una columna que no le importa."""
    texto = _tabla_gep(_fila_gep("Boca Juniors", 4, 2, 1, 1, 0, 3, 1))
    assert posiciones.tabla(texto)["Boca Juniors"] == (2, 3, 1)


def test_si_los_goles_coinciden_no_hay_partido_que_buscar():
    """Un marcador mal leido mueve SIEMPRE los goles: cambiarle un digito le toca
    el GF o el GC a los dos clubes. Asi que un resultado corrido con los goles
    intactos no lo puede explicar ningun partido, y el aviso tiene que decir que
    no hay nada que ir a buscar -- que es tan util como decir donde buscar.

    Es uno en el corpus: Defensores de Belgrano en la Primera Nacional 2025, con
    la tabla en 12-13-9 y la grilla en 12-12-10 sobre los mismos goles."""
    ps = [zona("Boca Juniors", "River Plate", 1, 1),
          zona("River Plate", "Boca Juniors", 2, 0)]
    # Boca: grilla 0-1-1 con GF1 GC3; la tabla le pone 0-2-0 y los MISMOS goles
    texto = _tabla_gep(_fila_gep("Boca Juniors", 2, 2, 0, 2, 0, 1, 3),
                       _fila_gep("River Plate", 4, 2, 1, 1, 0, 3, 1))
    avisos = posiciones.resultados_que_no_coinciden(ps, texto)
    boca = [a for a in avisos if a.startswith("Boca Juniors")]
    assert len(boca) == 1
    assert "los GOLES coinciden exacto" in boca[0]
    assert "la que esta mal es la fila de la tabla" in boca[0]
    assert "PARTIDO ENTERO" not in boca[0]


def test_si_los_goles_tambien_se_desvian_manda_a_buscar_el_partido():
    """La otra forma: ahi si hay un partido posible y el aviso dice como
    localizarlo."""
    ps = [zona("Boca Juniors", "River Plate", 0, 1)]
    texto = _tabla_gep(_fila_gep("Boca Juniors", 3, 1, 1, 0, 0, 1, 0),
                       _fila_gep("River Plate", 0, 1, 0, 0, 1, 0, 1))
    aviso = [a for a in posiciones.resultados_que_no_coinciden(ps, texto)
             if a.startswith("Boca Juniors")][0]
    assert "PARTIDO ENTERO" in aviso
    assert "el cruce entre los dos" in aviso
    assert "no hay nada que ir a buscar" not in aviso


# --------------------------------------------------------------------------
# el desvio que se verifico y no era nuestro
# --------------------------------------------------------------------------
def test_un_revisado_calla_el_aviso_de_ese_club():
    """Los otros seis tipos arreglan algo; este no arregla nada y esa es su
    funcion. Cuando la equivocada es la TABLA no hay marcador que corregir, y sin
    donde anotarlo el aviso volvia en cada corrida para siempre."""
    ps = [zona("Boca Juniors", "River Plate", 0, 1)]
    texto = _tabla_gep(_fila_gep("Boca Juniors", 3, 1, 1, 0, 0, 1, 0),
                       _fila_gep("River Plate", 0, 1, 0, 0, 1, 0, 1))
    assert posiciones.resultados_que_no_coinciden(ps, texto, pagina="Una Pagina")
    r = correcciones.Revisado(pagina="Una Pagina", club="Boca Juniors", porque="x")
    with mock.patch.object(correcciones, "REVISADOS", (r,)):
        quedan = posiciones.resultados_que_no_coinciden(ps, texto, pagina="Una Pagina")
    assert not [a for a in quedan if a.startswith("Boca Juniors")]


def test_un_revisado_no_calla_a_otra_pagina():
    """Una verificacion vale para la pagina en que se hizo. Aplicarla en todas
    silenciaria desvios que nadie miro."""
    ps = [zona("Boca Juniors", "River Plate", 0, 1)]
    texto = _tabla_gep(_fila_gep("Boca Juniors", 3, 1, 1, 0, 0, 1, 0),
                       _fila_gep("River Plate", 0, 1, 0, 0, 1, 0, 1))
    r = correcciones.Revisado(pagina="Otra Pagina", club="Boca Juniors", porque="x")
    with mock.patch.object(correcciones, "REVISADOS", (r,)):
        quedan = posiciones.resultados_que_no_coinciden(ps, texto, pagina="Una Pagina")
    assert [a for a in quedan if a.startswith("Boca Juniors")]


def test_un_revisado_que_ya_no_engancha_se_denuncia():
    """Caduca solo. Si la pagina se arreglo, la verificacion hablaba de otra cosa
    y mientras siga ahi puede tapar un desvio nuevo del mismo club."""
    r = correcciones.Revisado(pagina="Una Pagina", club="Boca Juniors", porque="x")
    with mock.patch.object(correcciones, "REVISADOS", (r,)):
        assert correcciones.revisados_huerfanos("Una Pagina", {"Boca Juniors"}) == []
        huerfanos = correcciones.revisados_huerfanos("Una Pagina", {"River Plate"})
    assert len(huerfanos) == 1 and "Boca Juniors" in huerfanos[0]


def test_los_huerfanos_se_preguntan_sobre_los_desvios_CRUDOS():
    """`clubes_desviados` no filtra por revisado, y no es un detalle: si filtrara,
    cada `Revisado` se justificaria a si mismo -- tapa el desvio, el desvio
    desaparece, y por lo tanto nunca aparece como huerfano."""
    ps = [zona("Boca Juniors", "River Plate", 0, 1)]
    texto = _tabla_gep(_fila_gep("Boca Juniors", 3, 1, 1, 0, 0, 1, 0),
                       _fila_gep("River Plate", 0, 1, 0, 0, 1, 0, 1))
    r = correcciones.Revisado(pagina="Una Pagina", club="Boca Juniors", porque="x")
    with mock.patch.object(correcciones, "REVISADOS", (r,)):
        crudos = posiciones.clubes_desviados(ps, texto, pagina="Una Pagina")
    assert "Boca Juniors" in crudos, "el revisado se tapo a si mismo"


def test_cada_revisado_dice_contra_que_se_verifico():
    """La vara es la misma que para corregir: silenciar un aviso sin mirar es peor
    que dejarlo abierto. O nombra una fuente de afuera, o la prueba es INTERNA y
    cerrada -- el caso de los goles que coinciden exacto, donde ningun partido
    puede explicar el desvio y no hay a donde ir a buscar."""
    for r in correcciones.REVISADOS:
        assert len(r.porque) > 120, f"{r.pagina} {r.club}: la evidencia es muy flaca"
        # "La " estuvo en esta lista y habia que sacarlo: matchea "La tabla", "La
        # grilla" y "La Fecha 5", o sea prosa comun de cualquier entrada. Siete de
        # las 33 pasaban SOLO por ahi, y ninguna de las siete nombraba una fuente
        # de afuera -- lo que tenian era una prueba de la TERCERA familia, que
        # abajo por fin se reconoce. Un marcador que se cumple sin querer no
        # guarda nada.
        externa = any(f in r.porque for f in
                       ("RSSSF", "rsssf", "cronica", "diario", "compilado",
                        "historial", "Web Archive"))
        # La prueba INTERNA de este modulo es una sola y siempre la misma: el club
        # se desvia solo, y un marcador mal leido toca a dos. Se la reconoce por la
        # idea y no por como quedo redactada la primera entrada, que es el error
        # que ya se cometio con la prueba de no-copia.
        # La prueba interna tiene una sola idea con varias formas de escribirse:
        # NO EXISTE PAREJA POSIBLE. Un marcador mal leido mueve a dos clubes con
        # deltas espejados, asi que un desvio sin su espejo no lo puede explicar
        # ningun partido. Se la reconoce por la idea, no por la redaccion de la
        # primera entrada -- el error que ya se cometio dos veces en este archivo.
        interna = any(f in r.porque.lower() for f in
                      ("prueba es interna", "prueba interna", "se desvia solo",
                       "otra mitad del par", "que lo aparee", "sin pareja",
                       "unico club desviado", "auto-espejado"))
        # LA TERCERA FAMILIA: el desvio no viene de un dato mal leido sino de un
        # FALLO. El partido existe y se conoce entero; lo que no se puede es
        # escribirlo, porque el tribunal le dio un resultado distinto a cada club,
        # o porque la fuente publica el homologado y no lo jugado. Tampoco hay a
        # donde ir a buscar, y por eso cierra igual que las otras dos.
        #
        # Ya habia tres entradas de esta familia antes de que se la nombrara --
        # Camioneros, Talleres (RdE) y Ramon Santamarina --, y las tres pasaban de
        # rebote por el "La " de la lista de arriba. Es la tercera vez en este
        # archivo que un marcador se queda corto porque se lo escribio mirando
        # una sola entrada.
        fallo = any(f in r.porque.lower() for f in
                    ("dividido", "dos resultados", "resultado distinto para cada club",
                     "homolog", "publica el fallo", "fuera del cruce"))
        # LA CUARTA: la pagina se desmiente a si misma. No hace falta razonar sobre
        # lo que un partido puede o no puede hacer -- que es lo que sostiene a la
        # familia "interna" -- porque hay OTRA tabla de la MISMA pagina diciendo lo
        # contrario. Varias paginas publican tres juegos de tablas (cada mitad del
        # torneo y una acumulada), y ahi la acumulada que no es la suma de sus
        # mitades queda desmentida por las dos que la componen.
        #
        # Es la mas fuerte de las internas y por eso vale distinguirla: las otras
        # concluyen "ningun partido puede explicarlo", esta muestra el desmentido.
        sola = any(f in r.porque.lower() for f in
                   ("se contradice sola", "se desmiente", "la desmienten",
                    "no es la suma de sus mitades", "otra tabla de la misma pagina"))
        assert externa or interna or fallo or sola, \
            f"{r.pagina} {r.club}: no dice contra que se verifico"


def test_el_revisado_tambien_calla_el_aviso_de_goles_y_solo_en_su_pagina():
    """El desvio de un club sale por DOS puertas -- `contrastar` mira los goles y
    `resultados_que_no_coinciden` los resultados -- y una verificacion cierra las
    dos: es el mismo desvio visto de dos maneras. Pero en las dos la entrada vale
    para SU pagina, porque una verificacion se hizo sobre una tabla concreta."""
    ps = [zona("Boca Juniors", "River Plate", 0, 1)]
    texto = _tabla_gep(_fila_gep("Boca Juniors", 3, 1, 1, 0, 0, 5, 0),
                       _fila_gep("River Plate", 0, 1, 0, 0, 1, 0, 5))
    assert [a for a in posiciones.contrastar(ps, texto, pagina="Una Pagina")
            if a.startswith("Boca Juniors")]

    suya = correcciones.Revisado(pagina="Una Pagina", club="Boca Juniors", porque="x")
    with mock.patch.object(correcciones, "REVISADOS", (suya,)):
        assert not [a for a in posiciones.contrastar(ps, texto, pagina="Una Pagina")
                    if a.startswith("Boca Juniors")]

    ajena = correcciones.Revisado(pagina="Otra Pagina", club="Boca Juniors", porque="x")
    with mock.patch.object(correcciones, "REVISADOS", (ajena,)):
        assert [a for a in posiciones.contrastar(ps, texto, pagina="Una Pagina")
                if a.startswith("Boca Juniors")], "una verificacion ajena no puede callar"


# --------------------------------------------------------------------------
# el resaltado contra la tabla: quien contesta a quien
# --------------------------------------------------------------------------
def _fila_resaltada(local, gl, gv, visita, pinta):
    """Una fila de grilla con el azul sobre `pinta`: 'L', 'E' o 'V'."""
    c = "bgcolor=#D0E7FF|'''"
    return ("|-\n|" + (c if pinta == "L" else "") + local
            + "\n|" + (c if pinta == "E" else "") + f"{gl} - {gv}"
            + "\n|" + (c if pinta == "V" else "") + visita)


def _pagina(grilla_filas, tabla_filas):
    return ('{| class="wikitable"\n' + "\n".join(grilla_filas) + "\n|}\n"
            + _tabla_gep(*tabla_filas))


def test_si_la_tabla_banca_a_los_digitos_la_acusacion_queda_contestada():
    """El color acusa y la tabla absuelve. Para que el color tuviera razon
    tendrian que estar mal la grilla Y la tabla, las dos del mismo lado; es mas
    barato que se haya pintado la celda equivocada, que es un error de una tecla
    y no toca ningun numero. Las 19 que habia se contestaban todas asi."""
    ps = [zona("Boca Juniors", "River Plate", 0, 1)]
    texto = _pagina([_fila_resaltada("Boca Juniors", 0, 1, "River Plate", "L")],
                    [_fila_gep("Boca Juniors", 0, 1, 0, 0, 1, 0, 1),
                     _fila_gep("River Plate", 3, 1, 1, 0, 0, 1, 0)])
    assert parser.resaltado_que_desmiente(texto), "el acusador tiene que acusar"
    assert posiciones.resaltado_sin_respuesta(ps, texto, pagina="Una Pagina") == []


def test_si_la_tabla_acompania_al_color_la_acusacion_sobrevive():
    """Es el caso que le dio credibilidad al metodo: en los cuatro aciertos
    conocidos el arreglo CAMBIABA la direccion, asi que la tabla se desviaba
    tambien y los dos testigos decian lo mismo. El filtro no puede comerse eso."""
    ps = [zona("Boca Juniors", "River Plate", 0, 1)]
    # la tabla le da la victoria a Boca, igual que el color y al reves que los digitos
    texto = _pagina([_fila_resaltada("Boca Juniors", 0, 1, "River Plate", "L")],
                    [_fila_gep("Boca Juniors", 3, 1, 1, 0, 0, 1, 0),
                     _fila_gep("River Plate", 0, 1, 0, 0, 1, 0, 1)])
    quedan = posiciones.resaltado_sin_respuesta(ps, texto, pagina="Una Pagina")
    assert len(quedan) == 1
    assert "la tabla no lo contesta" in quedan[0]


def test_si_la_tabla_no_puede_opinar_la_acusacion_sobrevive():
    """Con distinto PJ la tabla no habla del mismo conjunto de partidos, asi que
    no contesta nada y la acusacion sigue abierta."""
    ps = [zona("Boca Juniors", "River Plate", 0, 1)]
    texto = _pagina([_fila_resaltada("Boca Juniors", 0, 1, "River Plate", "L")],
                    [_fila_gep("Boca Juniors", 0, 5, 0, 0, 5, 0, 5),
                     _fila_gep("River Plate", 15, 5, 5, 0, 0, 5, 0)])
    quedan = posiciones.resaltado_sin_respuesta(ps, texto, pagina="Una Pagina")
    assert len(quedan) == 1 and "le cuenta distinto" in quedan[0]


def test_sin_acusacion_no_hay_nada_que_arbitrar():
    ps = [zona("Boca Juniors", "River Plate", 0, 1)]
    texto = _pagina([_fila_resaltada("Boca Juniors", 0, 1, "River Plate", "V")],
                    [_fila_gep("Boca Juniors", 0, 1, 0, 0, 1, 0, 1),
                     _fila_gep("River Plate", 3, 1, 1, 0, 0, 1, 0)])
    assert posiciones.resaltado_sin_respuesta(ps, texto, pagina="Una Pagina") == []


def test_alcanza_con_que_la_tabla_no_conteste_por_UNO_de_los_dos():
    """La acusacion es sobre un PARTIDO, y un partido tiene dos clubes. Si la
    tabla contesta por uno y del otro no puede opinar, no contesto: los goles del
    que no mira son justamente los que estan en discusion. Por eso la condicion
    es que los conteste a LOS DOS."""
    ps = [zona("Boca Juniors", "River Plate", 0, 1)]
    # Boca: la tabla coincide con la grilla (perdio). River: PJ distinto, no opina.
    texto = _pagina([_fila_resaltada("Boca Juniors", 0, 1, "River Plate", "L")],
                    [_fila_gep("Boca Juniors", 0, 1, 0, 0, 1, 0, 1),
                     _fila_gep("River Plate", 15, 5, 5, 0, 0, 5, 0)])
    quedan = posiciones.resaltado_sin_respuesta(ps, texto, pagina="Una Pagina")
    assert len(quedan) == 1
    assert "River Plate" in quedan[0] and "le cuenta distinto" in quedan[0]
    assert "a Boca Juniors le cuenta distinto" not in quedan[0]


# --------------------------------------------------------------------------
# Una zona que la tabla no cuenta no es un desvio
# --------------------------------------------------------------------------
def _pz(local, visita, zona, gl=1, gv=0):
    from fad.parser import Partido
    return Partido(local=local, visita=visita, goles_local=gl, goles_visita=gv,
                   fase="zonas", zona=zona)


def test_una_zona_que_la_tabla_no_cuenta_no_es_un_desvio():
    """La tabla de una ZONA contra una grilla que ademas trae el interzonal. Ahi no
    se mueve la tabla entera --solo los clubes que jugaron el interzonal-- pero
    tampoco hay nada mal: las dos partes cuentan bien, cosas distintas.

    Es el Argentino A 2009-10: sus 25 clubes juegan 16 de zona y diez de ellos
    juegan 4 mas en los grupos interzonales. Salian diez avisos que no eran un
    error de nadie.
    """
    dentro = [_pz("A", "B", "Zone 1"), _pz("A", "C", "Zone 1"), _pz("B", "C", "Zone 1"),
              _pz("A", "D", "Group A")]          # el interzonal, que la tabla no cuenta
    publicada = {"A": (2, 0, 0), "B": (2, 0, 0), "C": (2, 0, 0)}
    assert posiciones._una_zona_lo_explica(dentro, publicada, ["A", "B", "C"])


def test_se_prueban_conjuntos_y_no_zonas_sueltas():
    """El interzonal son DOS grupos y cada club juega en uno solo, asi que sacando
    uno el otro sigue desviado. Probando de a una, este caso se escapa."""
    dentro = [_pz("A", "B", "Zone 1"), _pz("A", "C", "Zone 1"), _pz("B", "C", "Zone 1"),
              _pz("A", "D", "Group A"), _pz("B", "E", "Group B")]
    publicada = {"A": (2, 0, 0), "B": (2, 0, 0), "C": (2, 0, 0)}
    assert posiciones._una_zona_lo_explica(dentro, publicada, ["A", "B", "C"])


def test_si_ninguna_zona_lo_explica_el_desvio_sigue_siendo_un_desvio():
    """El limite de la regla, y el que la hace util: no es un permiso para callar
    cualquier diferencia. Si al sacar zonas nunca cierra, el desvio se dice."""
    dentro = [_pz("A", "B", "Zone 1"), _pz("A", "C", "Zone 1")]
    publicada = {"A": (5, 0, 0), "B": (1, 0, 0), "C": (1, 0, 0)}
    assert not posiciones._una_zona_lo_explica(dentro, publicada, ["A", "B", "C"])


def test_sin_zonas_no_hay_nada_que_sacar():
    """Una pagina de una sola zona --o sin zonas-- no puede explicar nada asi, y la
    regla no se aplica."""
    dentro = [_pz("A", "B", ""), _pz("A", "C", "")]
    assert not posiciones._una_zona_lo_explica(dentro, {"A": (5, 0, 0)}, ["A"])


# --------------------------------------------------------------------------
# Un partido dividido se jugo aunque no tenga fila
# --------------------------------------------------------------------------
def test_un_dividido_explica_el_desvio_de_sus_dos_clubes():
    """El fallo le dio un marcador distinto a cada club, asi que la fila no entra
    --el esquema no puede escribir dos resultados-- pero la tabla de la pagina SI
    lo cuenta. Los dos clubes quedan desviados en uno, y eso no es un hallazgo:
    es la consecuencia aritmetica de una decision que ya esta escrita en
    `DIVIDIDOS`, con su evidencia.

    Se usa un dividido de verdad, no uno inventado: si alguien lo saca, este test
    lo dice.
    """
    # Van CUATRO clubes y no dos: con dos, los dos desviados son toda la tabla y la
    # guarda de media tabla se dispara sola, o sea que el test pasaria sin probar
    # nada. Asi se desvian dos de cuatro y la guarda no opina.
    texto = pagina(fila(1, "Chacarita Juniors", 3, 2, 1, 0, 1, 3, 1),
                   fila(2, "Atlanta", 3, 2, 1, 0, 1, 1, 3),
                   fila(3, "Colegiales", 3, 1, 1, 0, 0, 2, 0),
                   fila(4, "Almirante Brown", 0, 1, 0, 0, 1, 0, 2))
    ps = [zona("Chacarita Juniors", "Atlanta", 3, 1),      # el dividido no tiene fila
          zona("Colegiales", "Almirante Brown", 2, 0)]
    assert posiciones.pj_que_no_coincide(
        ps, texto, pagina="Campeonato de Primera B Nacional 2011-12") == []


def test_sin_la_pagina_el_dividido_no_se_puede_derivar():
    """El testigo: el mismo caso sin decir de que pagina es. `DIVIDIDOS` esta
    indexado por pagina, asi que sin ella no hay nada que derivar y el desvio se
    dice, que es lo correcto."""
    texto = pagina(fila(1, "Chacarita Juniors", 3, 2, 1, 0, 1, 3, 1),
                   fila(2, "Atlanta", 3, 2, 1, 0, 1, 1, 3),
                   fila(3, "Colegiales", 3, 1, 1, 0, 0, 2, 0),
                   fila(4, "Almirante Brown", 0, 1, 0, 0, 1, 0, 2))
    ps = [zona("Chacarita Juniors", "Atlanta", 3, 1),
          zona("Colegiales", "Almirante Brown", 2, 0)]
    assert posiciones.pj_que_no_coincide(ps, texto) != []


def test_el_dividido_solo_cuenta_para_su_seccion():
    """Cuando la pagina publica una tabla por seccion, el dividido suma en la
    suya y en ninguna otra. Sumandolo en todas, el Torneo Federal A 2018-19
    cerraba la Revalida y pasaba a contar uno de mas en la Primera fase."""
    assert correcciones.clubes_divididos("Torneo Federal A 2018-19", "Reválida")
    assert not correcciones.clubes_divididos("Torneo Federal A 2018-19", "Primera fase")
    assert not correcciones.clubes_divididos("Torneo Federal A 2018-19")


def test_un_dividido_sin_seccion_vale_para_la_tabla_general():
    """La mayoria de las paginas tienen una sola tabla y su dividido no declara
    seccion: ahi vale para la comparacion general, que es la de alcance vacio."""
    assert correcciones.clubes_divididos("Campeonato de Primera B Nacional 2011-12")


# --------------------------------------------------------------------------
# Lo que el respaldo de la fuente le cambia al aviso
# --------------------------------------------------------------------------
def _dos_desviados():
    """Dos clubes desviados contra la tabla, que es el caso en que el aviso
    manda a buscar un partido mal leido."""
    ps = [zona("Boca Juniors", "River Plate", 2, 0),
          zona("River Plate", "Boca Juniors", 1, 0)]
    texto = pagina(fila(1, "Boca Juniors", 3, 2, 1, 0, 1, 3, 1),
                   fila(2, "River Plate", 3, 2, 1, 0, 1, 1, 3))
    return ps, texto


def test_sin_respaldo_el_aviso_manda_a_releer_el_partido():
    salio = posiciones.contrastar(*_dos_desviados())
    assert salio and "puede venir de un partido mal leido" in salio[0]


def test_la_foja_de_la_fuente_cambia_el_aviso():
    """Cuando los partidos no salen de la pagina sino de una fuente externa, y
    la tabla que esa fuente publica al lado de ellos coincide EXACTA con nuestra
    suma, no hay nada que releer: el desacuerdo es entre las dos fuentes.

    No es un matiz. El Argentino A 2008-09 tiene diez clubes asi, y a los diez
    los mandaba a buscar un partido mal leido que no existe.
    """
    ps, texto = _dos_desviados()
    salio = posiciones.contrastar(ps, texto, respaldados={"Boca Juniors"})
    boca = next(d for d in salio if d.startswith("Boca"))
    river = next(d for d in salio if d.startswith("River"))
    assert "las dos fuentes no coinciden" in boca
    assert "mal leido" not in boca
    assert "puede venir de un partido mal leido" in river, "el otro no esta respaldado"


# --------------------------------------------------------------------------
# El desbalance de la propia tabla convierte un "probable" en una prueba
# --------------------------------------------------------------------------
def test_el_desbalance_de_la_tabla_prueba_que_la_fila_esta_mal():
    """Un club solo desviado ya sugeria que la fila de la tabla estaba mal --un
    marcador mal leido tocaria a DOS clubes--, pero era una sugerencia. Cuando la
    tabla ademas no cierra CONSIGO MISMA y le falta exactamente lo que a esa fila,
    deja de serlo: poniendo nuestro numero, sus dos columnas pasan a sumar igual.

    Pasa dos veces en el corpus y las dos con el mismo dibujo: el Clausura 1999
    suma GF488 GC489 con Union como unica fila discutida, y la Primera Nacional
    2026 suma GF884 GC885 con San Miguel.
    """
    ps = [zona("Boca Juniors", "River Plate", 2, 1)]
    texto = pagina(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 1, 1),
                   fila(2, "River Plate", 0, 1, 0, 0, 1, 1, 2))
    salio = posiciones.contrastar(ps, texto)
    assert len(salio) == 1 and salio[0].startswith("Boca")
    assert "la propia tabla lo demuestra" in salio[0]
    assert "lo mas probable" not in salio[0]


def test_sin_desbalance_sigue_siendo_un_probable():
    """El testigo del de arriba, sobre la funcion que decide."""
    assert not posiciones._lo_prueba_el_desbalance(1, 0, 1, 0), "tabla que cierra sola"


def test_con_dos_clubes_desviados_el_desbalance_no_prueba_nada():
    """Dos filas discutidas y un desbalance de uno: no se sabe cual de las dos lo
    causa, asi que arreglar ESTA no esta demostrado."""
    assert not posiciones._lo_prueba_el_desbalance(2, 1, 1, 0)


def test_el_desbalance_tiene_que_ir_para_el_lado_correcto():
    """Que las magnitudes coincidan no alcanza: si a la tabla le sobra un gol EN
    CONTRA, lo que falta es un gol A FAVOR. Un arreglo del otro lado la desbalancea
    mas, no menos."""
    assert posiciones._lo_prueba_el_desbalance(1, 1, 1, 0), "le falta un GF: cierra"
    assert not posiciones._lo_prueba_el_desbalance(1, 1, 0, 1), "sumarle un GC la aleja"
    assert posiciones._lo_prueba_el_desbalance(1, -1, 0, 1), "al reves, tambien vale"


def test_un_arreglo_de_los_dos_lados_no_lo_prueba():
    """Se pide que el arreglo sea de UN solo lado. Si la fila esta mal en las dos
    columnas, el desbalance no dice cuanto de cada una."""
    assert not posiciones._lo_prueba_el_desbalance(1, 1, 1, 1)


def test_con_varias_tablas_el_desbalance_no_prueba_nada():
    """SUMAR FILAS DE DOS TABLAS DISTINTAS NO DA UN TOTAL QUE SIGNIFIQUE ALGO.
    Cada tabla cubre su propio conjunto de partidos, asi que el "desbalance" de la
    suma no es el de ninguna, y un club puede ademas aparecer en las dos.

    El caso que lo muestra: la tabla de la Zona A no cierra y el unico club
    discutido esta en la Zona B. Sumando las dos, el sobrante de una se empareja
    de casualidad con el desvio de la otra y el aviso afirmaria una prueba que no
    tiene. Con el guard, sigue diciendo "lo mas probable", que es lo que
    corresponde cuando no se puede demostrar.

    Sobre el corpus de hoy el guard no cambia ni un aviso -- se midio --, pero a
    diferencia de otros defensivos que se sacaron por inobservables, este SI tiene
    un caso construible, y lo que evita es afirmar de mas. Ese es el error caro
    de este chequeo: todo su valor es que cuando dice "probado", esta probado.
    """
    texto = ("== Zona A ==\n"
             + pagina(fila(1, "Boca Juniors", 3, 2, 1, 0, 1, 3, 1),
                      titulo="Tabla de posiciones final")
             + "\n== Zona B ==\n"
             + pagina(fila(1, "River Plate", 0, 2, 0, 0, 2, 1, 4),
                      titulo="Tabla de posiciones final"))
    ps = [zona("Boca Juniors", "Talleres (C)", 3, 0),
          zona("Talleres (C)", "Boca Juniors", 1, 0),
          zona("River Plate", "Newell's Old Boys", 1, 2),
          zona("Newell's Old Boys", "River Plate", 2, 1)]

    salio = posiciones.contrastar(ps, texto)
    assert len(salio) == 1 and salio[0].startswith("River Plate:"), salio
    assert "lo mas probable" in salio[0]
    assert "la propia tabla lo demuestra" not in salio[0], (
        "la Zona A es la que no cierra, y el club discutido es de la Zona B")

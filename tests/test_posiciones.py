#!/usr/bin/env python3
"""Tests del cruce contra la tabla de posiciones.

Este chequeo es el unico del repo que puede decidir cual de dos fuentes tiene
razon sobre un marcador. Por eso lo que mas importa probar es CUANDO SE CALLA:
un arbitro que opina de mas es peor que no tener arbitro.
"""
from __future__ import annotations

from fad import posiciones
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


def zona(local, visita, gl, gv):
    return Partido(fecha="2010-01-01", local=local, visita=visita, goles_local=gl,
                   goles_visita=gv, fase="zonas", jornada="Fecha 1")


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
def test_los_marcadores_arbitrados_estan_justificados():
    """Cada correccion tiene que nombrar a su testigo.

    Antes el testigo era siempre la tabla de posiciones y el test pedia esa
    frase. Ya no alcanza: la tabla LOCALIZA el partido y no lo arbitra, y de los
    seis casos que se probaron contra la prensa, en dos la equivocada era ella.
    Asi que ahora el testigo puede ser la tabla o una cronica -- pero tiene que
    estar nombrado, y una cronica solo vale si dice quien hizo los goles. Un
    marcador suelto en un sitio de estadisticas puede venir de la misma fuente
    que estamos tratando de verificar."""
    from fad import correcciones
    for m in correcciones.MARCADORES:
        assert len(m.porque) > 80, f"{m.jornada} {m.local}: la evidencia es muy flaca"
        tabla_ = "tabla de posiciones" in m.porque
        prensa = any(p in m.porque for p in ("gol", "Boletin"))
        assert tabla_ or prensa, f"{m.jornada} {m.local}: el testigo no queda nombrado"


def test_la_prensa_arbitro_los_que_la_tabla_no_podia():
    """La tabla dice DONDE mirar y no QUIEN tiene razon. Cuando un torneo tiene
    dos partidos candidatos entre los mismos dos clubes -- la ida y la vuelta --
    la aritmetica no puede elegir, y ahi solo sirve una cronica."""
    from fad import correcciones
    por_prensa = [m for m in correcciones.MARCADORES
                  if "tabla de posiciones" not in m.porque]
    assert por_prensa, "ninguna correccion se apoya en la prensa: se perdio el metodo"
    for m in por_prensa:
        assert "gol" in m.porque or "Boletin" in m.porque, (
            f"{m.jornada} {m.local}: sin tabla y sin goleadores no hay evidencia")


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

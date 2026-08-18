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


def test_cuando_el_pj_coincide_se_calla():
    texto = pagina(fila(1, "Boca Juniors", 3, 1, 1, 0, 0, 3, 1),
                   fila(2, "River Plate", 0, 1, 0, 0, 1, 1, 3))
    assert posiciones.pj_que_no_coincide([zona("Boca Juniors", "River Plate", 3, 1)], texto) == []

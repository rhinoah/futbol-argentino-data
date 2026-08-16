#!/usr/bin/env python3
"""
fad/correcciones.py
===================
Errores de la fuente que se corrigen a mano, uno por uno y con la evidencia.

ESTE MODULO ES PELIGROSO Y POR ESO ES ASI DE ESTRICTO
-----------------------------------------------------
Todo el dataset sale de Wikipedia. Un lugar donde se puede escribir "este partido
en realidad fue asi" es exactamente la puerta por la que se cuela un dataset que
dice lo que a uno le gustaria que dijera. La regla del proyecto es que el parser
no adivine; esto es lo mas cerca que se esta de romperla.

Las condiciones para que una correccion entre son estas:

1. **La fuente se contradice sola.** No alcanza con que un dato parezca raro:
   tiene que ser imposible. La unica que hay hoy la agarro `una_vez_por_jornada`,
   que es un chequeo del fixture, no una opinion.
2. **Hay un testigo externo que dice cual es el valor correcto**, y se cita.
3. **La correccion identifica el partido por completo** -- jornada, los dos
   equipos y el marcador. Si algo de eso no coincide, no se aplica.
4. **Si deja de enganchar, se avisa.** Cuando alguien corrija la pagina en
   Wikipedia esta entrada queda sin efecto, y el build lo dice para que se
   borre. Una correccion vieja que nadie saco es una mentira dormida.

Lo que NO va aca: variantes de nombre (eso es un alias en `equipos.py`),
etiquetas de jornada mal puestas (eso lo limpia `_borrar_jornadas_falsas`) y
discrepancias de marcador entre fuentes (esas se informan y no se tocan: no
sabemos cual de las dos tiene razon).
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Correccion:
    pagina: str                      # titulo exacto de la pagina de Wikipedia
    jornada: str
    # El partido tal como queda DESPUES de canonizar los nombres, con marcador.
    # Va completo a proposito: con los cuatro campos no hay forma de que la
    # correccion caiga sobre otro partido.
    dice: tuple[str, str, int, int]
    debe: tuple[str, str]            # (local, visitante) correctos, canonicos
    porque: str                      # la evidencia, para que se pueda auditar


def _localia_al_reves(jornada: str, local: str, visita: str, g: int,
                      otra_jornada: str) -> Correccion:
    """Un partido que la pagina anota con los equipos cambiados de lado.

    Los tres que hay son de la B Nacional 2009-10 y salen del mismo invariante:
    en un torneo de ida y vuelta cada par juega UNA vez en cada cancha, y estos
    tres figuran con el mismo local en las dos ruedas. Eso no es raro, es
    imposible, y no hace falta ninguna fuente externa para verlo.

    Los tres son EMPATES, y ahi esta la gracia: como el marcador es simetrico,
    las dos fuentes coinciden en todo salvo en quien jugaba en su casa. Por eso
    `fechas.completar` no los emparejaba -- busca (jornada, local, visitante) y
    del otro lado estan al reves --, se quedaban sin fecha y se caian del
    dataset. O sea que el error no producia un dato malo: producia tres partidos
    que no existian.

    Cual de las dos ruedas esta mal lo dice worldfootball, que da la otra
    orientacion para esta y coincide con Wikipedia en la otra.
    """
    return Correccion(
        pagina="Campeonato de Primera B Nacional 2009-10",
        jornada=jornada,
        dice=(local, visita, g, g),
        debe=(visita, local),
        porque=(f"La pagina pone a {local} de local contra {visita} en la {otra_jornada} "
                f"Y en la {jornada}. En un torneo de ida y vuelta cada par juega una vez "
                f"en cada cancha, asi que una de las dos esta al reves; lo agarra "
                f"`validar.localias_repartidas` sin mirar ninguna fuente externa. "
                f"Cual es la mala la dice worldfootball, que para la {jornada} da "
                f"{visita} {g}-{g} {local} y para la {otra_jornada} coincide con "
                f"Wikipedia. Como el marcador es un empate, las dos fuentes dicen "
                f"exactamente lo mismo salvo la localia."))


CORRECCIONES: tuple[Correccion, ...] = (
    _localia_al_reves("Fecha 25", "Belgrano", "Instituto", 1, "Fecha 6"),
    _localia_al_reves("Fecha 25", "Ferro Carril Oeste", "Unión", 2, "Fecha 6"),
    _localia_al_reves("Fecha 35", "Deportivo Merlo", "Platense", 2, "Fecha 16"),

    # ------------------------------------------------------------------
    # Torneo Argentino A 2010-11: nueve nombres, todos arbitrados por la GRILLA
    # DE LA ZONA y no por parecido de cadenas. En la fecha donde aparece el
    # nombre raro, el club que falta de esa zona es exactamente ese.
    #
    # Los cuatro de Union tienen ademas prueba aritmetica: con ellos, Union (MdP)
    # llega a los 28 PJ que publica la tabla de la Primera fase, y los ocho
    # clubes de la Zona 1 quedan en 28. Sin ellos queda en 24 y sobra un
    # "Union (S)" con 4 en una zona que no es la suya.
    # ------------------------------------------------------------------
    Correccion(
        pagina="Torneo Argentino A 2010-11",
        jornada="Fecha 4",
        dice=("Ramón Santamarina", "Unión (S)", 0, 0),
        debe=("Ramón Santamarina", "Unión (MdP)"),
        porque=(
            "Zona 1 de la Primera fase, donde juega Union de MAR DEL PLATA. "
            "Union (S) es el de Sunchales y juega la Zona 3, con 27 partidos ahi. "
            "Con este y los otros tres, Union (MdP) llega a los 28 partidos que "
            "publica la tabla de posiciones de su zona; sin ellos queda en 24 y "
            "los otros siete clubes tambien fallan. Ningun otro reparto da 28."),
    ),
    Correccion(
        pagina="Torneo Argentino A 2010-11",
        jornada="Fecha 17",
        dice=("Unión (S)", "Guillermo Brown", 1, 1),
        debe=("Unión (MdP)", "Guillermo Brown"),
        porque=(
            "Zona 1 de la Primera fase, donde juega Union de MAR DEL PLATA. "
            "Union (S) es el de Sunchales y juega la Zona 3, con 27 partidos ahi. "
            "Con este y los otros tres, Union (MdP) llega a los 28 partidos que "
            "publica la tabla de posiciones de su zona; sin ellos queda en 24 y "
            "los otros siete clubes tambien fallan. Ningun otro reparto da 28."),
    ),
    Correccion(
        pagina="Torneo Argentino A 2010-11",
        jornada="Fecha 20",
        dice=("Cipolletti", "Unión (S)", 2, 2),
        debe=("Cipolletti", "Unión (MdP)"),
        porque=(
            "Zona 1 de la Primera fase, donde juega Union de MAR DEL PLATA. "
            "Union (S) es el de Sunchales y juega la Zona 3, con 27 partidos ahi. "
            "Con este y los otros tres, Union (MdP) llega a los 28 partidos que "
            "publica la tabla de posiciones de su zona; sin ellos queda en 24 y "
            "los otros siete clubes tambien fallan. Ningun otro reparto da 28."),
    ),
    Correccion(
        pagina="Torneo Argentino A 2010-11",
        jornada="Fecha 22",
        dice=("Villa Mitre", "Unión (S)", 0, 1),
        debe=("Villa Mitre", "Unión (MdP)"),
        porque=(
            "Zona 1 de la Primera fase, donde juega Union de MAR DEL PLATA. "
            "Union (S) es el de Sunchales y juega la Zona 3, con 27 partidos ahi. "
            "Con este y los otros tres, Union (MdP) llega a los 28 partidos que "
            "publica la tabla de posiciones de su zona; sin ellos queda en 24 y "
            "los otros siete clubes tambien fallan. Ningun otro reparto da 28."),
    ),
    Correccion(
        pagina="Torneo Argentino A 2010-11",
        jornada="Fecha 21",
        dice=("Unión (MdP)", "Douglas Haig", 2, 0),
        debe=("Unión (MdP)", "Huracán (TA)"),
        porque=(
            "En esa misma Fecha 21 de la Zona 1 ya juega Douglas Haig contra "
            "Cipolletti, y en una fecha de ocho clubes nadie juega dos veces. El "
            "unico que falta es Huracan (TA). Con el cambio, Douglas Haig cierra "
            "en los 28 partidos que publica la tabla y Huracan tambien."),
    ),
    Correccion(
        pagina="Torneo Argentino A 2010-11",
        jornada="Fecha 11",
        dice=("Unión", "9 de Julio (R)", 1, 1),
        debe=("Unión (S)", "9 de Julio (R)"),
        porque=(
            "Zona 3 de la Primera fase. \"Union\" a secas SI esta en el padron -- es "
            "Union de Santa Fe --, asi que este no se caia como desconocido: "
            "resolvia calladito a un club de Primera que nunca jugo el Argentino "
            "A. En esa fecha el que falta de la Zona 3 es Union de Sunchales."),
    ),
    Correccion(
        pagina="Torneo Argentino A 2010-11",
        jornada="Fecha 22",
        dice=("Gimnasia y Esgrima", "Unión (S)", 1, 1),
        debe=("Gimnasia y Esgrima (CdU)", "Unión (S)"),
        porque=(
            "Zona 3. \"Gimnasia y Esgrima\" a secas tiene seis candidatos en el "
            "padron, asi que no puede ser un alias. En esa fecha el que falta de "
            "la zona es el de Concepcion del Uruguay, que juega las otras 25."),
    ),
    Correccion(
        pagina="Torneo Argentino A 2010-11",
        jornada="Fecha 28",
        dice=("Central Norte (S)", "Gimnasia y Esgrima", 2, 0),
        debe=("Central Norte (S)", "Gimnasia y Esgrima (CdU)"),
        porque=(
            "El mismo caso que la Fecha 22, en la otra rueda: en esa fecha el "
            "unico que falta de la Zona 3 es Gimnasia y Esgrima (CdU)."),
    ),
    Correccion(
        pagina="Torneo Argentino A 2010-11",
        jornada="Fecha 22",
        dice=("Juventud Antoniana", "Central Norte (SE)", 1, 1),
        debe=("Juventud Antoniana", "Central Norte (S)"),
        porque=(
            "No es un typo de escritura sino un desambiguador equivocado, y por "
            "eso no puede ser un alias: en esta MISMA pagina \"(SE)\" significa "
            "Santiago del Estero -- ahi esta \"Central Cordoba (SE)\", que resuelve "
            "bien --, asi que darselo al de Salta seria escribir en el padron algo "
            "que la fuente no dice. En esa fecha el que falta de la Zona 3 es el "
            "de SALTA, que juega las otras 26."),
    ),

    # ------------------------------------------------------------------
    # Torneo Argentino A 2005-06.
    # ------------------------------------------------------------------
    Correccion(
        pagina="Torneo Argentino A 2005-06",
        jornada="Fecha 6",
        dice=("Desamparados", "Racing (O)", 3, 1),
        debe=("Desamparados", "Cipolletti"),
        porque=(
            "El Apertura es una sola rueda: 11 fechas, 132 partidos, y 130 de sus "
            "131 pares se cruzan exactamente una vez. El unico que se cruza DOS es "
            "Desamparados-Racing (O), en la Fecha 6 y en la 10; y el unico par que "
            "no se cruza nunca es Desamparados-Cipolletti. Ademas Racing (O) juega "
            "dos veces la Fecha 6 y Cipolletti ninguna. Las cuatro cosas se "
            "arreglan con este cambio y con ningun otro, sin salir de la pagina."),
    ),
    Correccion(
        pagina="Torneo Argentino A 2005-06",
        jornada="Fecha 6",
        dice=("9 de Julio", "La Florida", 0, 2),
        debe=("9 de Julio (R)", "La Florida"),
        porque=(
            "El de Rafaela, que juega las otras 21 fechas del torneo escrito con el "
            "(R). No va como alias del padron porque \"9 de Julio\" a secas es un "
            "nombre de club muy repetido en el pais -- hay uno en Morteros, otro en "
            "Rio Tercero -- y darselo al de Rafaela para siempre por una fila seria "
            "justo el alias mal puesto que este modulo existe para evitar."),
    ),
    Correccion(
        pagina="Torneo Argentino A 2005-06",
        jornada="Promoción",
        dice=("Alumni", "General Paz Juniors", 5, 0),
        debe=("Alumni (VM)", "General Paz Juniors"),
        porque=(
            "Alumni de Villa Maria, que venia del Argentino B y jugo la promocion "
            "contra General Paz Juniors. Mismo criterio que el de arriba: "
            "\"Alumni\" a secas no va como alias -- es el nombre de varios clubes "
            "argentinos -- y aca son dos filas."),
    ),
    Correccion(
        pagina="Torneo Argentino A 2005-06",
        jornada="Promoción",
        dice=("General Paz Juniors", "Alumni", 2, 0),
        debe=("General Paz Juniors", "Alumni (VM)"),
        porque=(
            "La vuelta de la promocion. Alumni de Villa Maria gano la serie 5-2 y "
            "ascendio; General Paz Juniors bajo al Argentino B, que es lo que dice "
            "el infobox de la pagina y tambien el articulo del club."),
    ),

    Correccion(
        pagina="Torneo Federal A 2016-17",
        jornada="Fecha 5",
        dice=("Ferro Carril Oeste", "Deportivo Roca", 2, 1),
        debe=("Ferro Carril Oeste (GP)", "Deportivo Roca"),
        porque=(
            "Es el de General Pico, y la pagina se olvida el (GP) en esta fila y "
            "solo en esta: las otras nueve veces que ese club aparece lo escribe "
            "'Ferro Carril Oeste (GP)'. El de Caballito jugaba la Primera Nacional "
            "ese anio, no el Federal A. "
            "Lo delato la CANCHA, que es el testigo que el dataset ya traia: el "
            "partido se juega en El Coloso del Barrio Talleres, que la propia "
            "pagina declara como estadio de Ferro Carril Oeste (General Pico) en "
            "su tabla de participantes, y donde el de Caballito no jugo nunca. "
            "Ver `dataset.casas_compartidas`."),
    ),

    Correccion(
        pagina="Campeonato de Primera Nacional 2022",
        jornada="Fecha 5",
        dice=("Alvarado", "San Martín", 3, 1),
        debe=("Alvarado", "San Martín (T)"),
        porque=(
            "La pagina escribe 'San Martin' a secas, sin enlace, y en ese torneo "
            "juegan el de San Juan y el de Tucuman. No se resolvio por parecido ni "
            "con una fuente externa: en la Fecha 5, San Martin (SJ) ya juega contra "
            "Belgrano y San Martin (T) no juega ninguna vez, y cada club juega una "
            "vez por fecha. Ademas (T) queda con 35 partidos contra los 36 de (SJ) "
            "-- exactamente el que falta -- y Alvarado contra (T) no aparece en "
            "ninguna otra jornada."),
    ),

    Correccion(
        pagina="Campeonato de Primera B Nacional 2009-10",
        jornada="Fecha 12",
        dice=("All Boys", "Belgrano", 0, 0),
        debe=("All Boys", "Gimnasia y Esgrima (J)"),
        porque=(
            "La pagina pone a Belgrano DOS veces en la Fecha 12 (contra All Boys "
            "y contra CAI) y deja a Gimnasia y Esgrima (J) sin jugar. En una "
            "fecha de veinte equipos eso no puede pasar, y lo agarra "
            "`validar.una_vez_por_jornada` sin mirar ninguna fuente externa. "
            "Cual de los dos esta mal lo dice worldfootball, que para esa fecha "
            "trae los mismos diez partidos con los mismos diez marcadores y el "
            "primero como All Boys 0-0 GyE Jujuy."),
    ),
)


@dataclass(frozen=True)
class Marcador:
    """Un partido que las dos fuentes cuentan distinto, arbitrado por la tabla.

    No se elige "la fuente que suele tener razon". Se le pregunta a la TABLA DE
    POSICIONES de la propia pagina de Wikipedia, que publica los partidos jugados
    y los goles a favor y en contra de cada club: sumar los marcadores tiene que
    dar exactamente eso. Uno de los dos candidatos hace cerrar la tabla y el otro
    no, y ahi termina la discusion sin traer una tercera fuente.

    Que el metodo mide algo se ve en que no contesta siempre lo mismo: de los
    nueve, ocho le dan la razon a worldfootball y uno a Wikipedia.

    `debe` puede ser igual a `dice`. Eso quiere decir que la pagina ya tenia
    razon y que lo unico que se toma de la otra fuente es la FECHA.
    """
    pagina: str
    jornada: str
    local: str
    visita: str
    dice: tuple[int, int]
    debe: tuple[int, int]
    porque: str


def _arbitrado(jornada, local, visita, dice, debe, quien, detalle):
    return Marcador(
        pagina={"2007": "Campeonato de Primera B Nacional 2007-08",
                "2008": "Campeonato de Primera B Nacional 2008-09",
                "2009": "Campeonato de Primera B Nacional 2009-10",
                "2010": "Campeonato de Primera B Nacional 2010-11"}[jornada[:4]],
        jornada=jornada[5:], local=local, visita=visita, dice=dice, debe=debe,
        porque=(f"Wikipedia dice {dice[0]}-{dice[1]} y worldfootball "
                f"{debe[0]}-{debe[1]}. La tabla de posiciones de la propia pagina "
                f"le da la razon a {quien}: {detalle}."))


MARCADORES: tuple[Marcador, ...] = (
    Marcador(
        pagina="Torneo Federal A 2019-20",
        jornada="Fecha 14", local="San Martín (F)", visita="Unión (S)",
        dice=(2, 0), debe=(3, 0),
        porque=(
            "La tabla de posiciones de la propia pagina le pone a San Martin (F) un "
            "gol a favor mas y a Union (S) uno en contra mas de los que dan sus "
            "partidos, y el unico ajuste de un gol que hace cerrar el torneo entero "
            "es este. Como la tabla sola no alcanza -- se equivoca, ver Platense en "
            "la B Nacional 2009-10 --, se busco afuera: varias fuentes dan "
            "San Martin (Formosa) 3-0 Union (Sunchales) el 1 de diciembre de 2019, "
            "misma fecha que tiene el partido aca, incluido un video de los goles."),
    ),
    Marcador(
        pagina="Campeonato de Primera B 2018-19 (Argentina)",
        jornada="Fecha 15", local="San Telmo", visita="UAI Urquiza",
        dice=(1, 0), debe=(0, 1),
        porque=(
            "Wikipedia dice 1-0 y worldfootball 0-1. La tabla de posiciones de la "
            "propia pagina le da la razon a worldfootball: con el 0-1 los veinte "
            "clubes cierran, y con el 1-0 fallan San Telmo (45/33 publicados contra "
            "46/32 sumados) y UAI Urquiza (26/33 contra 25/34). Aparecio cruzando la "
            "temporada contra la pagina de worldfootball, que coincide en los otros "
            "379 partidos."),
    ),
    # ------------------------------------------------------------------
    # Los cuatro que arbitro la prensa, no la tabla.
    #
    # La tabla localiza el partido y no lo arbitra: dice ENTRE QUE DOS CLUBES
    # esta la diferencia, y ahi termina. Que exista un unico ajuste de un gol que
    # haga cerrar el torneo no prueba nada -- se probo en seis casos y la tabla
    # tenia razon en cuatro; en los otros dos la equivocada era ella (ver la
    # Primera C 2026 y la B Nacional 2012-13 en `posiciones.py`).
    #
    # Asi que para cada uno se busco una cronica que nombre a los goleadores. Un
    # marcador suelto en un sitio de estadisticas no alcanza: puede venir de la
    # misma fuente que estamos tratando de verificar.
    # ------------------------------------------------------------------
    Marcador(
        pagina="Campeonato de Primera Nacional 2023",
        jornada="Fecha 31", local="Aldosivi", visita="Villa Dálmine",
        dice=(0, 0), debe=(1, 1),
        porque=(
            "A los dos clubes les falta un gol a favor y uno en contra contra la "
            "tabla, y el G-E-P coincide exacto en los dos (8-11-15 y 5-5-24): la "
            "tabla ya computa empate, solo discrepa en los goles. De los dos cruces "
            "posibles, la Fecha 14 queda descartada -- La Capital de Mar del Plata "
            "publica su cronica con el 1-0 y el gol de Tobias Cervera a los 21', "
            "igual que la grilla. "
            "Noticias MDP da 1-1 en la Fecha 31 con los dos goles: Britez a los 11' "
            "del segundo tiempo y Barberini en menos de diez minutos. Contradice a "
            "Wikipedia, que publica 0-0, asi que no puede venir de ahi. 0223 narra "
            "el empate parcial en directo con la misma jugada."),
    ),
    Marcador(
        pagina="Campeonato de Primera C 2015 (Argentina)",
        jornada="Fecha 32", local="Argentino de Merlo", visita="Cañuelas",
        dice=(0, 2), debe=(1, 2),
        porque=(
            "A Merlo le falta un gol a favor contra la tabla y a Canuelas uno en "
            "contra. De los dos cruces, la Fecha 13 queda confirmada como esta "
            "(Canuelas 0-1 Merlo, gol de Damian Villalba). "
            "historiayfutbol publica las 38 fechas partido por partido CON "
            "GOLEADORES, dato que Wikipedia no trae para este torneo, asi que no "
            "puede ser copia: '28/09/2015 en Merlo: Argentino de Merlo 1 (Fernando "
            "Maldonado), Canuelas FC 2 (Guido Saiz y Mauro Boaglio)'. "
            "OJO, y por eso queda escrito: es UNA SOLA fuente calificada. Los "
            "blogs de los dos clubes no publicaron nada ese mes y lo demas son "
            "agregadores. Se aplica porque contradice a Wikipedia con goleadores "
            "nombrados, pero es la evidencia mas flaca de las quince."),
    ),
    Marcador(
        pagina="Campeonato de Primera C 2026 (Argentina)",
        jornada="Fecha 14", local="Claypole", visita="Central Córdoba (R)",
        dice=(0, 0), debe=(2, 2),
        porque=(
            "A los dos clubes les faltan exactamente 2 goles a favor y 2 en contra "
            "contra la tabla, que es la firma de un partido entre ellos, y el G-E-P "
            "ya coincide: las dos partes de la pagina acuerdan en que fue empate y "
            "discrepan solo en los goles. "
            "La Capital de Rosario, el mismo dia del partido, da 2-2 con los cuatro "
            "goles y su club: Gallucci 9' y Marcos Cordoba 74' para Central Cordoba, "
            "Godoy 11' y Llodra 19' para Claypole. Y aca la sospecha de siempre -- "
            "que la prensa haya copiado de Wikipedia -- esta muerta por "
            "construccion: Wikipedia publica 0-0, asi que un medio que diga 2-2 no "
            "puede venir de ahi. Lo confirma De Brown con reporteo propio."),
    ),
    Marcador(
        pagina="Campeonato de Primera Nacional 2022",
        jornada="Fecha 19", local="Estudiantes (RC)", visita="Deportivo Riestra",
        dice=(2, 1), debe=(2, 0),
        porque=(
            "El G-E-P publicado coincide EXACTO con los partidos para los dos "
            "clubes (14-16-6 y 12-18-6), asi que la tabla ya computa este partido "
            "como victoria de Estudiantes: lo unico que sobra es un gol de Riestra. "
            "LV16 publica la ficha cerrada -- estadio Candini, arbitro Rodrigo "
            "Rivero, las dos formaciones -- con una lista de goles de dos entradas, "
            "las dos de Estudiantes: Luis Silba 13' ST y Fernando Belluschi 50' ST. "
            "Puntal coincide en marcador y goleadores. Ninguna registra gol de "
            "Riestra, y esos nombres no pueden salir de Wikipedia: la pagina no "
            "trae goleadores de la fase regular en ningun lado."),
    ),
    Marcador(
        pagina="Campeonato de Primera Nacional 2022",
        jornada="Fecha 26", local="Ramón Santamarina", visita="Chacarita Juniors",
        dice=(1, 1), debe=(2, 1),
        porque=(
            "Aca el G-E-P NO coincide, y esa es la prueba: la tabla le da a "
            "Santamarina 6 ganados y 11 empatados donde los partidos dan 5 y 12, y "
            "a Chacarita 12 perdidos donde dan 11. O sea que la propia pagina "
            "computa una VICTORIA de Santamarina donde su grilla pone empate. "
            "Que Pasa Web narra los tres goles: Alustiza de penal a los 8', empate "
            "de Formica a los 22' y el 2-1 de Gagliardi. "
            "Y hay un testigo independiente y ANTERIOR: El Eco de Tandil, en la "
            "previa de la fecha siguiente, publica cuatro cifras de posiciones -- a "
            "quien supera, a quien alcanza y cuantos puntos lo separan de Rafaela -- "
            "que cierran las cuatro con el 2-1 y fallan las cuatro con el 1-1."),
    ),
    Marcador(
        pagina="Anexo:Torneo Clausura 2007 (Argentina)",
        jornada="Fecha 2", local="Newell's Old Boys", visita="River Plate",
        dice=(1, 2), debe=(0, 2),
        porque=(
            "No es un error de transcripcion: es la diferencia entre el marcador de "
            "cancha y el oficial. El partido se suspendio a los 90' por incidentes en "
            "las tribunas con River ganando 2-1, y el 16/03/2007 el Tribunal de "
            "Disciplina de la AFA se lo dio ganado a River por 2 a 0. "
            "El testigo es la PROPIA PAGINA, que se contradice: la celda del fixture "
            "dice 1-2 y la nota al pie de esa misma celda dice que el Tribunal "
            "otorgo el 2 a 0, citando el Boletin N 3980 de la AFA. La tabla de "
            "posiciones esta calculada con el 0-2. Se guarda el resultado oficial "
            "-- es el que homologo la AFA y con el que esta armada la tabla --, y "
            "queda asentado aca que el 1-2 no es un invento sino lo que estaba en el "
            "marcador cuando se suspendio. "
            "La quita de 3 puntos a Newell's fue de la tabla anual, no de la del "
            "Clausura: por eso conserva sus 22 puntos."),
    ),
    Marcador(
        pagina="Campeonato de Primera Nacional 2024",
        jornada="Fecha 15", local="Alvarado", visita="Talleres (RdE)",
        dice=(1, 0), debe=(2, 0),
        porque=(
            "La tabla le pone a Alvarado un gol a favor mas y a Talleres uno en "
            "contra mas de los que dan sus partidos. La cronica de La Capital de Mar "
            "del Plata del 12 de mayo de 2024, misma fecha que tiene el partido aca, "
            "da 2-0 con los dos goles: Guillermo Sanchez a los 34' y Guido Vadala a "
            "los 48'."),
    ),
    Marcador(
        pagina="Campeonato de Primera C 2023 (Argentina)",
        jornada="Fecha 33", local="Deportivo Laferrere", visita="Excursionistas",
        dice=(1, 0), debe=(1, 1),
        porque=(
            "Habia dos partidos candidatos entre estos dos clubes y la prensa "
            "desempata cual: Solo Ascenso publica la cronica de la Fecha 33 con el "
            "1-1 y los dos goles -- Mateo Figueroa (Excursionistas) a los 14' del "
            "segundo tiempo y Alejandro Gomez (Laferrere) sobre la hora. "
            "El otro candidato, el 0-0 de la Fecha 14, queda descartado."),
    ),
    Marcador(
        pagina="Torneo Federal A 2022",
        jornada="Fecha 14", local="Ciudad de Bolívar", visita="Juventud Unida Universitario",
        dice=(1, 1), debe=(2, 1),
        porque=(
            "Ascenso del Interior publica la cronica de la 14a jornada con el 2-1 y "
            "los tres goles: Sebastian Balmaceda para Juventud a los 30' del primer "
            "tiempo, y Facundo Quiroga y Nahuel Yeri de penal para Ciudad de Bolivar "
            "en el segundo. El empate que dice la pagina no explica ningun gol."),
    ),
    _arbitrado("2007 Fecha 1", "Independiente Rivadavia", "Tiro Federal", (0, 1), (1, 0),
               "worldfootball",
               "con 0-1 los dos clubes quedan fuera de sus totales publicados y con 1-0 cierran"),
    # El unico donde gana Wikipedia. `debe` == `dice`: no se cambia el marcador,
    # solo se acepta la fecha de la otra fuente.
    _arbitrado("2008 Fecha 36 (6/06/2009)", "Talleres (C)", "Atlético Tucumán", (0, 4), (0, 4),
               "Wikipedia",
               "con el 0-4 de Wikipedia los veinte clubes cierran, y con el 1-4 de "
               "worldfootball se rompen Talleres y Atlético Tucumán"),
    _arbitrado("2009 Fecha 1", "Defensa y Justicia", "Tiro Federal", (2, 2), (2, 0),
               "worldfootball",
               "Defensa y Justicia figura con GC53 y sumando los partidos daba 55; "
               "Tiro Federal con GF52 y daba 54"),
    _arbitrado("2009 Fecha 17", "Platense", "Aldosivi", (1, 0), (0, 0),
               "worldfootball",
               "junto con la Fecha 38, es lo que le deja a Aldosivi los GC54 que publica "
               "la tabla en vez de los 58 que daban"),
    _arbitrado("2009 Fecha 23", "Gimnasia y Esgrima (J)", "Quilmes", (0, 1), (1, 2),
               "worldfootball",
               "a los cuatro totales de los dos clubes les faltaba exactamente un gol"),
    _arbitrado("2009 Fecha 38", "San Martín (SJ)", "Ferro Carril Oeste", (1, 0), (1, 1),
               "worldfootball",
               "a San Martín le faltaba un gol en contra y a Ferro uno a favor"),
    _arbitrado("2009 Fecha 38", "Aldosivi", "Boca Unidos", (3, 4), (3, 1),
               "worldfootball",
               "Boca Unidos publica GF42 y sumando daba 45; con este marcador cierra"),
    _arbitrado("2010 Fecha 22", "Ferro Carril Oeste", "Defensa y Justicia", (0, 3), (0, 0),
               "worldfootball",
               "Defensa y Justicia publica GF37 y daba 40; Ferro publica GC47 y daba 50"),
    _arbitrado("2010 Fecha 22", "San Martín (T)", "Patronato", (1, 3), (1, 2),
               "worldfootball",
               "a Patronato le sobraba un gol a favor y a San Martín uno en contra"),
)


@dataclass(frozen=True)
class Cancha:
    """Un partido al que la pagina le pone el estadio de otro club.

    Es la tercera forma de contradecirse que tiene la fuente, y la encontro
    `dataset.casas_compartidas` buscando otra cosa: fue a buscar clubes mal
    atribuidos y aparecieron partidos bien atribuidos con la cancha del vecino.

    El testigo es la MISMA PAGINA. Las dos que hay salen de su tabla de
    participantes, que dice en que estadio juega cada club -- o sea que la
    pagina se contradice sola, sin traer nada de afuera. Cuando no se resuelve
    asi, no entra: el aviso queda abierto y listo.
    """
    pagina: str
    jornada: str
    local: str
    visita: str
    dice: str
    debe: str
    porque: str


CANCHAS: tuple[Cancha, ...] = (
    Cancha(
        pagina="Campeonato de Primera Nacional 2022",
        jornada="Fecha 36", local="Gimnasia y Esgrima (J)", visita="San Martín (T)",
        dice="Víctor Antonio Legrotaglie", debe="23 de Agosto",
        porque=(
            "El Legrotaglie es de Gimnasia y Esgrima de MENDOZA -- la tabla de "
            "participantes de la misma pagina lo dice, y las otras diecinueve veces "
            "que ese estadio aparece en el fixture el local es el de Mendoza. "
            "Que el equivocado sea el estadio y no el club lo decide el fixture: "
            "San Martin (T) ya habia jugado contra el de Mendoza en la Fecha 29, y "
            "en un torneo de una sola rueda no se cruzan dos veces. Asi que el de "
            "la Fecha 36 es el de Jujuy, en su cancha, el 23 de Agosto."),
    ),
    Cancha(
        pagina="Torneo Federal A 2025",
        jornada="Partidos de vuelta", local="Sarmiento (LB)", visita="San Martín (SM)",
        dice="Centenario", debe="Ciudad de La Banda",
        porque=(
            "El Centenario es de Sarmiento de RESISTENCIA. La tabla de participantes "
            "de la misma pagina pone a los dos clubes con sus canchas: Sarmiento de "
            "La Banda en el Ciudad de La Banda y Sarmiento de Resistencia en el "
            "Estadio Centenario (Resistencia). "
            "Que el local sea Sarmiento (LB) esta bien: la ida fue San Martin (SM) "
            "0-0 Sarmiento (LB) en el Libertador General San Martin, asi que la "
            "vuelta le toca de local, y el cuadro de la llave lo confirma."),
    ),
)


def arbitrados(pagina: str) -> set[tuple[str, str, str]]:
    """(jornada, local, visitante) de los partidos ya arbitrados de `pagina`.

    `fechas.completar` usa el marcador para VERIFICAR que las dos fuentes hablan
    del mismo partido, y se niega a completar cuando no coincide. Para estos el
    emparejamiento ya se confirmo por otro lado, asi que una diferencia que
    quede no tiene que frenar la fecha.
    """
    return {(m.jornada, m.local, m.visita) for m in MARCADORES if m.pagina == pagina}


def aplicar(ps: list, pagina: str) -> tuple[int, list[str]]:
    """Corrige los partidos de `pagina`. Devuelve (cuantas se aplicaron, avisos).

    Se llama DESPUES de canonizar los nombres: `dice` y `debe` estan en canonico,
    asi que una correccion no se rompe porque la pagina cambie como escribe un
    club -- para eso estan los alias.
    """
    aplicadas, avisos = 0, []
    for c in CORRECCIONES:
        if c.pagina != pagina:
            continue
        local, visita, gl, gv = c.dice
        candidatos = [p for p in ps
                      if p.jornada == c.jornada and p.local == local
                      and p.visita == visita
                      and (p.goles_local, p.goles_visita) == (gl, gv)]
        if not candidatos:
            avisos.append(f"la correccion de {c.jornada} ({local} vs {visita}) ya no "
                          f"engancha con ningun partido: si la fuente se arreglo, "
                          f"sacala de fad/correcciones.py")
            continue
        if len(candidatos) > 1:
            avisos.append(f"la correccion de {c.jornada} ({local} vs {visita}) "
                          f"engancha con {len(candidatos)} partidos y no se aplica: "
                          f"no identifica uno solo")
            continue
        candidatos[0].local, candidatos[0].visita = c.debe
        aplicadas += 1

    for m in MARCADORES:
        if m.pagina != pagina or m.debe == m.dice:
            continue                      # `debe == dice`: la pagina ya esta bien
        candidatos = [p for p in ps
                      if p.jornada == m.jornada and p.local == m.local
                      and p.visita == m.visita
                      and (p.goles_local, p.goles_visita) == m.dice]
        if len(candidatos) != 1:
            avisos.append(f"el marcador arbitrado de {m.jornada} ({m.local} vs "
                          f"{m.visita}) engancha con {len(candidatos)} partidos y no se "
                          f"aplica: si la fuente se corrigio, sacalo de fad/correcciones.py")
            continue
        candidatos[0].goles_local, candidatos[0].goles_visita = m.debe
        aplicadas += 1

    for c in CANCHAS:
        if c.pagina != pagina:
            continue
        candidatos = [p for p in ps
                      if p.jornada == c.jornada and p.local == c.local
                      and p.visita == c.visita and p.estadio == c.dice]
        if len(candidatos) != 1:
            avisos.append(f"la cancha corregida de {c.jornada} ({c.local} vs "
                          f"{c.visita}) engancha con {len(candidatos)} partidos y no "
                          f"se aplica: si la fuente se corrigio, sacala de "
                          f"fad/correcciones.py")
            continue
        candidatos[0].estadio = c.debe
        aplicadas += 1
    return aplicadas, avisos

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
    # ------------------------------------------------------------------
    # Los dos del Clausura 2008, que no son un error de nadie sino DANO DE
    # EDICION, y se puede seguir en el historial de la propia Wikipedia.
    #
    #   2021-10-09 (oldid 138916082)  |0 - 2   |0 - 5   |0 - 2
    #   2021-11-19 (oldid 139838699)  | - 2    | - 5    | - 2     <- Butoro
    #   2022-09-15 (oldid 145987834)  |1 - 2   |1 - 5   |1 - 2    <- "Mantenimiento"
    #
    # La edicion del 19/11/2021 normaliza ceros a la izquierda en toda la pagina
    # ("01.º" -> "1.º", "pos=01" -> "pos=1") y de paso se come el 0 del local en
    # las lineas de marcador donde el local no habia convertido. Diez meses
    # despues, otra edicion rellena los huecos y en estos escribe 1 en vez de 0.
    #
    # El tercero de la lista, Lanus 0-5 Banfield, ya lo arreglo alguien en
    # Wikipedia y hoy vuelve a decir 0-5. Por eso solo desviaban tres clubes y no
    # cinco. Los otros dos siguen rotos y son estos.
    # ------------------------------------------------------------------
    Marcador(
        pagina="Anexo:Torneo Clausura 2008 (Argentina)",
        jornada="Fecha 2", local="Gimnasia y Esgrima (J)", visita="Estudiantes (LP)",
        dice=(1, 2), debe=(0, 2),
        porque=(
            "ESPN publica la ficha con el 0-2 y los dos goles de Estudiantes: Enzo "
            "Perez a los 11' y Pablo Luguercio a los 50', arbitro Alejandro Sabino. "
            "Lo corrobora el compendio historiayfutbol, que da 'Gimnasia y Esgrima "
            "de Jujuy 0, Estudiantes de La Plata 2 (Enzo Perez y Pablo Luguercio)'. "
            "Pero el testigo decisivo es INTERNO y esta en el historial de la propia "
            "pagina: hasta el 2021-10-09 decia '0 - 2'. El 2021-11-19 una edicion de "
            "normalizacion de ceros a la izquierda le borro el digito del local y "
            "dejo '| - 2', y el 2022-09-15 otra edicion, comentada 'Mantenimiento', "
            "relleno el hueco con un 1. O sea que el 1 no viene de ninguna fuente: "
            "es un digito repuesto a ojo sobre un dato que la propia Wikipedia habia "
            "roto."),
    ),
    Marcador(
        pagina="Anexo:Torneo Clausura 2008 (Argentina)",
        jornada="Fecha 7", local="Racing Club", visita="Estudiantes (LP)",
        dice=(1, 2), debe=(0, 2),
        porque=(
            "Mismo dano de edicion que el de la Fecha 2, en la misma pagina y en la "
            "misma tanda: '0 - 2' hasta 2021-10-09, '| - 2' despues de la "
            "normalizacion de ceros del 2021-11-19, y '1 - 2' desde el "
            "'Mantenimiento' del 2022-09-15. "
            "Y aca ademas el 0-2 es el resultado OFICIAL, no una lectura: el partido "
            "se suspendio a los 78' por incidentes y el Tribunal de Disciplina lo dio "
            "por ganado a Estudiantes 2 a 0. Lo dice la nota al pie de esa misma "
            "celda de la pagina, citando a Clarin, y lo repite historiayfutbol "
            "('Suspendido a los 77'... posteriormente se dio por ganado a Estudiantes "
            "de La Plata por 2-0'). Se guarda el homologado, que es con el que esta "
            "armada la tabla de posiciones, igual que en el Newell's-River del "
            "Clausura 2007. El 1-2 era el marcador de cancha al momento de la "
            "suspension, y queda asentado aca."),
    ),
    # ------------------------------------------------------------------
    # Los tres de la Primera Nacional 2019-20: un mismo club, tres partidos.
    #
    # Es el caso que el apareo de a dos no ve. Belgrano tenia GF+9 y tres clubes
    # tenian solo GC de mas (Platense +4, Agropecuario +3, Moron +2), sumando
    # exactamente 9: no son cuatro huerfanos sino UN club con tres partidos mal
    # leidos, los tres de visitante y los tres de la primera rueda.
    #
    # Lo que hace unico a cada uno es un testigo interno que esta en la misma
    # pagina: la TABLA PARCIAL DE LA PRIMERA RUEDA. Contra la tabla final sola,
    # la aritmetica admitiria repartir el ajuste entre la ida y la vuelta; la
    # parcial confina los tres desvios a la primera rueda y deja un solo cruce
    # posible por club. Los cruces de la segunda rueda tienen ademas su propio
    # testigo, que los confirma como estan.
    # ------------------------------------------------------------------
    Marcador(
        pagina="Campeonato de Primera Nacional 2019-20",
        jornada="Fecha 2", local="Agropecuario", visita="Belgrano",
        dice=(1, 3), debe=(1, 0),
        porque=(
            "Cadena 3 publica la cronica del 25/08/2019 con el 1-0 y el gol: Mariano "
            "Mino a los 5' del segundo tiempo, tras que Alejandro Gagliardi la bajara "
            "de pecho y le cediera el pase. La misma nota dice que Agropecuario quedo "
            "con 6 puntos y Belgrano con 1, dos cifras que solo cierran con el 1-0. "
            "La tabla parcial de la primera rueda de la propia pagina confina todo el "
            "desvio de Agropecuario a esta rueda, y este es su unico cruce con "
            "Belgrano ahi, asi que el partido queda determinado."),
    ),
    Marcador(
        pagina="Campeonato de Primera Nacional 2019-20",
        jornada="Fecha 4", local="Deportivo Morón", visita="Belgrano",
        dice=(1, 3), debe=(1, 1),
        porque=(
            "Solo Ascenso publica la sintesis completa del 06/09/2019 en el Nuevo "
            "Francisco Urbano con el 1-1 y los dos goles: Lucas Perez Godoy a los 30' "
            "para Moron y Pablo Vegetti a los 80' para Belgrano, arbitro Bruno Bocca. "
            "Igual que en la Fecha 2, la tabla parcial de la primera rueda deja este "
            "como unico cruce posible entre los dos."),
    ),
    Marcador(
        pagina="Campeonato de Primera Nacional 2019-20",
        jornada="Fecha 6", local="Platense", visita="Belgrano",
        dice=(1, 4), debe=(1, 0),
        porque=(
            "ESPN publica la ficha del 23/09/2019 en el Ciudad de Vicente Lopez con "
            "el 1-0 y el gol de Javier Rossi a los 22'. Lo respalda el video de los "
            "goles titulado 'Platense 1 VS. Belgrano 0 | Fecha 6 | Primera Nacional "
            "2019/2020'. "
            "El otro cruce, el 1-1 de la Fecha 21, queda descartado por su propio "
            "testigo: Solo Ascenso publica su sintesis con los goles de Matias "
            "Tissera a los 16' y Pablo Vegetti a los 40', o sea que la grilla lo "
            "tiene bien y no hay que tocarlo."),
    ),
    Marcador(
        pagina="Campeonato de Primera C 2011-12 (Argentina)",
        jornada="Fecha 1", local="Villa Dálmine", visita="Defensores de Cambaceres",
        dice=(1, 0), debe=(0, 1),
        porque=(
            "Cuatro cronicas narrativas, de tres redacciones que no se conocen entre "
            "si, y todas nombran al goleador. La Autentica Defensa de Campana "
            "('Ni el triunfo de Cambaceres pudo aguar la fiesta de Dalmine', edicion "
            "del 07/08/2011) da el gol de Enzo Pelosi a los 15' del primer tiempo, "
            "con formaciones, cambios, amonestados y el arbitro Sebastian Bresba. "
            "La Revista Tribuna Roja, el fanzine de Cambaceres, publica su cronica el "
            "mismo 06/08/2011 a las 21:17: 'Iban 16 minutos, cuando Burgos habilito "
            "al unico delantero que presento el Rojo, Enzo Pelosi'. Las Voces del "
            "Ascenso e historiayfutbol coinciden, y Solo Ascenso publica al dia "
            "siguiente al arquero Arias Navarro hablando del triunfo de visitante. "
            "Divergen entre si justo como divergen las planillas escritas a mano por "
            "separado -- 15 contra 16 minutos, 'Jendrulek' contra 'Gendrolec' --, que "
            "es lo contrario de copiarse. "
            "Y el reloj explica el error sin necesidad de vandalismo: la celda de "
            "Wikipedia se cargo el 06/08/2011 a las 19:15 de Argentina, menos de dos "
            "horas despues del final y ANTES de que se publicara una sola cronica. "
            "Una IP la tipeo de un marcador en vivo y la puso al reves. Desde "
            "entonces la pagina dijo '1 - 0' y nunca otra cosa en catorce anios. "
            "OJO CON LA ARITMETICA: aca NO senala este partido. Hay siete arreglos de "
            "dos partidos que reproducen las mismas columnas, asi que la unicidad es "
            "falsa y la correccion se apoya enteramente en las cronicas."),
    ),
    Marcador(
        pagina="Torneo Federal A 2021",
        jornada="Fecha 22", local="Juventud Unida Universitario", visita="Olimpo",
        dice=(2, 2), debe=(0, 0),
        porque=(
            "Tres cronicas del dia del partido, de tres ciudades, y ninguna citada "
            "por la pagina. El Diario de la Republica de San Luis -- el diario del "
            "club local -- publica 'Ni Juventud ni Olimpo pudieron y empataron en El "
            "Bajo' a las 17:37 del 10/09/2021, con reporteo propio (fotografo "
            "Nicolas Varvara en la cancha) y el texto 'ni Juventud ni Olimpo de Bahia "
            "Blanca pudieron quebrar al rival y empataron cero a cero este viernes'. "
            "La Brujula 24 lo transmite en vivo ('Todos empatan sin goles en el "
            "primer tiempo', 16:31) y publica los resultados finales. La Nueva de "
            "Bahia Blanca da 'igualaron sin goles'. "
            "Sobre La Nueva hubo una objecion que valia la pena y quedo resuelta: el "
            "slug de su URL dice 'ven accion esta tarde', o sea que la nota nacio "
            "como previa. Las capturas de Wayback lo demuestran -- la temprana tiene "
            "datePublished igual a dateModified (09:00) y titulo de previa; la "
            "posterior tiene dateModified 22:32 del mismo dia y el titulo reescrito "
            "como cronica --, asi que el diario reutilizo la nota y dejo el slug. "
            "Wikipedia cargo el 2-2 recien el 11/09 a las 03:27, o sea que las tres "
            "fuentes estan aguas arriba y no pueden descender de ella. "
            "La aritmetica ademas lo fuerza: el excedente de Olimpo solo puede caer "
            "en partidos contra Juventud Unida, y en la Fecha 7 (Olimpo 2-0 JUU) "
            "Juventud hizo 0 goles y no se le puede restar nada."),
    ),
    Marcador(
        pagina="Torneo Federal A 2021",
        jornada="Fecha 30", local="Juventud Unida Universitario", visita="Desamparados",
        dice=(2, 1), debe=(2, 0),
        porque=(
            "Dos cronicas de dos provincias y dos redacciones. El Diario de Cuyo de "
            "San Juan -- el diario de Desamparados, o sea el del club perjudicado, "
            "que no tiene ningun motivo para restarle un gol -- publica 'Sportivo "
            "pago caro su error y se despidio' el 31/10/2021 y narra los dos goles: "
            "a los 23' desborde de Eggel por izquierda, centro de De Hoyos y Zuliani "
            "la mete en contra; en el descuento, tras una serie de rebotes, Gatica "
            "empuja el 2 a 0. Dice explicitamente que Desamparados no convirtio. "
            "El Diario de la Republica de San Luis lo confirma independientemente: "
            "'Fue 2-0 a Desamparados por los goles de Hernan Zuliani -en contra- y "
            "Nicolas Gatica'. "
            "La aritmetica tambien lo fuerza: en la Fecha 15 Desamparados hizo 0 "
            "goles, asi que su gol de mas sale si o si de este partido."),
    ),
    Marcador(
        pagina="Torneo Federal A 2022",
        jornada="Fecha 26", local="Crucero del Norte", visita="San Martín (F)",
        dice=(1, 0), debe=(3, 1),
        porque=(
            "Misiones Online publica la cronica el mismo 24/08/2022 a las 17:37, con "
            "los cuatro goles: Cristian Campozano a los 19' y Ernesto Alvarez cerca "
            "de los 30' del primer tiempo para Crucero, Brian Peralta para San Martin "
            "al inicio del segundo, y Emanuel Sosa a los 33' del segundo. Es "
            "redaccion propia y los otros resultados que trae de esa fecha coinciden "
            "uno por uno con la grilla. La celda de Wikipedia se tipeo el 25/08 a las "
            "02:48, o sea NUEVE HORAS DESPUES de la cronica: no puede ser su ancestro. "
            "Lo corrobora la ficha de Transfermarkt (3-1, 2-0 al entretiempo, mismos "
            "goleadores). "
            "SE APLICA SOLA, Y ESO DEJA LA PAGINA SIN CERRAR A PROPOSITO. El desvio "
            "que queda -- San Martin (F) y Central Norte (S), los dos +2 GF +2 GC -- "
            "apunta al San Martin-Central Norte, y ESE no se toca: su unico testigo "
            "es Ascenso del Interior, que resulto ser el ANCESTRO de la tabla de "
            "posiciones de esta misma pagina. ADI publica sus tablas como imagenes de "
            "imgur, y la captura de Wayback del 07/11/2022 muestra su Zona B identica "
            "digito por digito a la tabla del articulo. O sea que ahi la cronica, la "
            "tabla y la aritmetica son un solo testigo contado tres veces. Es la "
            "trampa del Clausura 2005 dada vuelta, y hasta que aparezca un relato del "
            "03/04/2022 ajeno a ADI, ese partido queda abierto."),
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


@dataclass(frozen=True)
class Reemplazo:
    """Una fila que no es una version equivocada de un partido: es OTRO partido.

    Los otros tres tipos arreglan un campo -- el nombre de un club, el marcador,
    la cancha -- sobre una fila que por lo demas describe el partido que dice
    describir. Este es para cuando eso no se sostiene: la fila entera esta de mas
    y el partido que iba ahi falta.

    Existe por un caso, y conviene contarlo entero porque es el unico del repo en
    que la fuente no se equivoca sino que se DUPLICA. La pagina del Torneo
    Argentino A 2005-06 copio las tablas de las Fechas 5 y 6 de la Zona Sur del
    CLAUSURA dentro del APERTURA. No parecido: los mismos doce cruces, los mismos
    locales y los mismos marcadores. Dos rondas de dos torneos distintos no
    pueden ser identicas, asi que la pagina se contradice sola -- eso solo ya
    prueba que esta mal, sin traer nada de afuera.

    Lo que decide QUE iba ahi es la propia pagina otra vez, y esta es la parte
    que vale: sus cuatro tablas de posiciones (Apertura y Clausura por zona) NO
    las toco el copy-paste. Contrastadas contra las dos versiones:

        Apertura Zona Sur     nuestra grilla  0/12    RSSSF  12/12
        Apertura Zona Norte   nuestra grilla  9/12    RSSSF  12/12
        Clausura Zona Sur     nuestra grilla 12/12    RSSSF  12/12

    O sea que la tabla le da la razon a RSSSF en cada club donde el nombre
    resuelve, y se la quita a la grilla. Aplicadas las catorce, las tres tablas
    cierran EXACTO. La cuarta queda en 9/12 por dos rotulos con asterisco y por
    La Florida, que es otra cosa: su partido con Sportivo Patria se abandono y se
    dio "0-1 en contra de los dos", un resultado que un marcador no puede
    expresar. Ese no se toca.

    POR QUE HACE FALTA LA LLAVE. Los otros tipos emparejan por (jornada, local,
    visita) y aca eso no alcanza: Apertura y Clausura numeran los dos del 1 al
    11, y las filas copiadas son identicas en los dos lados. Una correccion sin
    llave enganchaba con dos partidos y no se aplicaba -- que es la conducta
    correcta, y por eso hubo que agregar el campo en vez de forzarla.
    """
    pagina: str
    llave: str                          # la seccion de nivel 2 de la pagina
    jornada: str
    dice: tuple[str, str, int, int]     # local, visita, goles local, goles visita
    debe: tuple[str, str, int, int]
    porque: str


_ARGENTINO_A_2005 = (
    "La pagina copio las Fechas 5 y 6 de la Zona Sur del Clausura dentro del "
    "Apertura -- mismos cruces, mismos locales, mismos marcadores --, y dos "
    "rondas de dos torneos distintos no pueden ser identicas. Lo que iba ahi lo "
    "dice la TABLA DE POSICIONES DE LA MISMA PAGINA, que el copy-paste no toco: "
    "con la grilla como esta, la del Apertura Zona Sur no cierra en ninguno de "
    "sus doce clubes; con estos marcadores cierra en los doce, y la del Apertura "
    "Zona Norte tambien. Los valores salen de RSSSF."
)


def _copiado(jornada: str, dice, debe, detalle: str = "") -> Reemplazo:
    return Reemplazo(pagina="Torneo Argentino A 2005-06", llave="Torneo Apertura",
                     jornada=jornada, dice=dice, debe=debe,
                     porque=_ARGENTINO_A_2005 + (" " + detalle if detalle else ""))


# Diez filas del copy-paste y cuatro marcadores sueltos de la misma pagina. Los
# cuatro van por el mismo camino porque tambien necesitan la llave: sin ella, la
# correccion del Apertura engancharia tambien con la fila gemela del Clausura.
REEMPLAZOS: tuple[Reemplazo, ...] = (
    # --- Fecha 5, Zona Sur: la ronda entera es del Clausura
    _copiado("Fecha 5", ("Douglas Haig", "Cipolletti", 5, 3),
             ("Cipolletti", "Douglas Haig", 1, 2)),
    _copiado("Fecha 5", ("Juventud Unida Universitario", "Desamparados", 2, 2),
             ("Desamparados", "Juventud Unida Universitario", 1, 1)),
    _copiado("Fecha 5", ("La Plata FC", "Villa Mitre", 1, 1),
             ("Villa Mitre", "La Plata FC", 2, 1)),
    _copiado("Fecha 5", ("Luján de Cuyo", "Juventud (P)", 1, 1),
             ("Juventud (P)", "Luján de Cuyo", 1, 0)),
    _copiado("Fecha 5", ("Guillermo Brown", "Independiente Rivadavia", 1, 0),
             ("Independiente Rivadavia", "Guillermo Brown", 1, 0)),
    # Este quedo con el local bien y el marcador del Clausura (0-0 en vez de 1-0):
    # la copia no fue perfecta, y por eso conviene no suponer que lo es.
    _copiado("Fecha 5", ("Racing (O)", "Huracán (CR)", 0, 0),
             ("Racing (O)", "Huracán (CR)", 1, 0),
             "Aca la copia dejo el local bien y se llevo solo el marcador."),
    # --- Fecha 6, Zona Sur: idem, salvo Huracan (CR) vs Villa Mitre, que quedo bien
    _copiado("Fecha 6", ("Racing (O)", "Guillermo Brown", 0, 1),
             ("Guillermo Brown", "Racing (O)", 2, 0)),
    _copiado("Fecha 6", ("Juventud (P)", "La Plata FC", 1, 2),
             ("La Plata FC", "Juventud (P)", 1, 0)),
    _copiado("Fecha 6", ("Juventud Unida Universitario", "Luján de Cuyo", 2, 1),
             ("Luján de Cuyo", "Juventud Unida Universitario", 5, 2)),
    _copiado("Fecha 6", ("Independiente Rivadavia", "Douglas Haig", 1, 1),
             ("Douglas Haig", "Independiente Rivadavia", 0, 1)),
    _copiado("Fecha 6", ("Desamparados", "Cipolletti", 3, 1),
             ("Cipolletti", "Desamparados", 3, 0)),
    # --- Cuatro marcadores de la Zona Norte y uno de la Sur, ajenos al copy-paste
    # pero que la misma tabla arbitra: sin ellos, La Florida, Talleres (P) y
    # Union (S) no cierran.
    _copiado("Fecha 1", ("Unión (S)", "La Florida", 2, 0),
             ("Unión (S)", "La Florida", 2, 1),
             "Este no es del copy-paste: es un gol de menos de La Florida, y "
             "salta en la misma tabla."),
    _copiado("Fecha 4", ("Guillermo Brown", "Cipolletti", 3, 0),
             ("Guillermo Brown", "Cipolletti", 3, 1),
             "Tampoco es del copy-paste; lo arbitra la misma tabla."),
    _copiado("Fecha 5", ("Unión (S)", "Talleres (P)", 2, 0),
             ("Unión (S)", "Talleres (P)", 1, 0),
             "Tampoco es del copy-paste; lo arbitra la misma tabla."),
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

    for r in REEMPLAZOS:
        if r.pagina != pagina:
            continue
        local, visita, gl, gv = r.dice
        # La LLAVE entra en la identificacion, y es lo que distingue este tipo de
        # los otros tres: sin ella, la fila copiada del Apertura y su gemela del
        # Clausura son indistinguibles y la correccion engancha con las dos.
        candidatos = [p for p in ps
                      if p.llave == r.llave and p.jornada == r.jornada
                      and p.local == local and p.visita == visita
                      and (p.goles_local, p.goles_visita) == (gl, gv)]
        if len(candidatos) != 1:
            avisos.append(f"el reemplazo de {r.llave} {r.jornada} ({local} vs "
                          f"{visita}) engancha con {len(candidatos)} partidos y no se "
                          f"aplica: si la fuente se corrigio, sacalo de "
                          f"fad/correcciones.py")
            continue
        p = candidatos[0]
        p.local, p.visita, p.goles_local, p.goles_visita = r.debe
        aplicadas += 1
    return aplicadas, avisos

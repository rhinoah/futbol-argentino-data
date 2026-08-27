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

from dataclasses import dataclass, replace


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


# Las veinte llaves del Argentino A 2011-12 comparten explicacion porque comparten
# causa: la pagina tiene CAMBIADOS los rotulos de dos columnas.
_LLAVES_2011_12 = (
    "LA PAGINA ROTULA `Local - Vuelta` A LA COLUMNA DE LA IDA. Sus tablas de "
    "eliminacion son `Local - Vuelta | Global | Local - Ida | Ida | Vuelta`, y el "
    "lector las lee por NOMBRE de columna y no por posicion --eso ya estaba "
    "resuelto--, asi que toma al pie de la letra un encabezado que esta mal.\n"
    "SE MIDIO, Y ES UNIFORME. De los 34 partidos de eliminacion de esta pagina, "
    "26 se identifican contra RSSSF por par y marcador: 20 vienen con la localia "
    "al reves y 6 no. Los 20 son TODOS de las tablas con esa forma --Tercera "
    "fase, Cuarta fase, Revalida segunda y tercera ronda-- y los 6 que coinciden "
    "son de tablas de otra forma (`Partidos`, `Promoción`). No hay una sola "
    "excepcion adentro de esas cuatro tablas.\n"
    "SE ESPEJAN LAS 28, no las 20. Las otras ocho filas de esas mismas tablas no "
    "se pudieron identificar por marcador --cuatro son llaves donde las DOS patas "
    "terminaron igual, y las otras cuatro tienen ademas un desacuerdo de marcador "
    "con RSSSF-- pero la fecha las empareja igual y RSSSF las da al reves lo mismo. "
    "Corregir 20 y dejar 8 de la misma tabla seria tratar como fila lo que es un "
    "encabezado. El desacuerdo de MARCADOR de esas cuatro no lo toca el espejo "
    "--son dos cosas distintas-- y se arbitro aparte: son los cuatro `Marcador` de esta pagina.\n"
    "Y EL CONTROL ES LA TEMPORADA SIGUIENTE. El Argentino A 2012-13 usa EL MISMO "
    "orden de columnas y el mismo lector, y ahi son 30 identificados con CERO al "
    "reves. Su `Local - Ida` de la tercera ronda de la Revalida dice Libertad (S) "
    "y RSSSF escribe `First leg [May 13] Libertad (Sunchales) 3-0 Guaraní`. O sea "
    "que el orden de columnas no es el problema: el problema es esta pagina.\n"
    "LA SEDE LO CONFIRMA, y es lo que ninguna de las dos tablas puede discutir. El "
    "blog de Jose Carluccio publica cada partido con su CIUDAD, y las cuatro idas "
    "de la Revalida - Segunda ronda se jugaron en la ciudad del club que la pagina "
    "pone a la IZQUIERDA: \"22/04/2012 en Cipolletti: Cipolletti 0, Libertad de "
    "Sunchales 2\", \"en Concepcion del Uruguay: Gimnasia y Esgrima 0, Central "
    "Norte 0\", \"en Salta: Gimnasia y Tiro 0, Rivadavia de Lincoln 1\" y \"en "
    "Salta: Juventud Antoniana 1, Juventud Unida Universitario 1\". Las dos de la "
    "Tercera ronda, igual: \"en Lincoln\" y \"en Salta\".\n"
    "LO QUE NO CAMBIA es el resultado ni el dia: espejar una llave deja los mismos "
    "goles para cada club y la misma fecha en cada fila. RSSSF coincide con "
    "nuestra fecha en 18 de las 20. Lo unico que estaba mal era quien jugaba en su "
    "casa -- y, por arrastre, que `fechas.completar` emparejaba nuestra ida con su "
    "vuelta y denunciaba veintiocho desacuerdos de dia que no existian.")


def _llave_espejada(jornada: str, local: str, visita: str, gl: int, gv: int) -> Correccion:
    """Una llave del Argentino A 2011-12 con los dos clubes del lado equivocado."""
    return Correccion(
        pagina="Torneo Argentino A 2011-12", jornada=jornada,
        dice=(local, visita, gl, gv), debe=(visita, local),
        porque=_LLAVES_2011_12)


CORRECCIONES: tuple[Correccion, ...] = (
    _localia_al_reves("Fecha 25", "Belgrano", "Instituto", 1, "Fecha 6"),
    _localia_al_reves("Fecha 25", "Ferro Carril Oeste", "Unión", 2, "Fecha 6"),
    _localia_al_reves("Fecha 35", "Deportivo Merlo", "Platense", 2, "Fecha 16"),

    # Las veinte de la eliminacion del Argentino A 2011-12; ver
    # `_LLAVES_2011_12` para la evidencia, que es una sola para las veinte.
    _llave_espejada("Reválida - Segunda ronda", "Libertad (S)", "Cipolletti", 2, 0),
    _llave_espejada("Reválida - Segunda ronda", "Cipolletti", "Libertad (S)", 2, 2),
    _llave_espejada("Reválida - Segunda ronda", "Central Norte (S)", "Gimnasia y Esgrima (CdU)", 0, 0),
    _llave_espejada("Reválida - Segunda ronda", "Gimnasia y Esgrima (CdU)", "Central Norte (S)", 1, 3),
    _llave_espejada("Reválida - Segunda ronda", "Rivadavia (L)", "Gimnasia y Tiro (S)", 1, 0),
    _llave_espejada("Reválida - Segunda ronda", "Gimnasia y Tiro (S)", "Rivadavia (L)", 0, 2),
    _llave_espejada("Reválida - Tercera ronda", "Juventud Unida Universitario", "Rivadavia (L)", 0, 1),
    _llave_espejada("Reválida - Tercera ronda", "Rivadavia (L)", "Juventud Unida Universitario", 0, 3),
    _llave_espejada("Tercera fase", "San Martín (T)", "Central Norte (S)", 0, 2),
    _llave_espejada("Tercera fase", "Central Norte (S)", "San Martín (T)", 2, 1),
    _llave_espejada("Tercera fase", "Defensores de Belgrano (VR)", "Juventud Unida Universitario", 1, 4),
    _llave_espejada("Tercera fase", "Juventud Unida Universitario", "Defensores de Belgrano (VR)", 0, 2),
    _llave_espejada("Tercera fase", "Racing (O)", "Central Córdoba (SdE)", 0, 2),
    _llave_espejada("Tercera fase", "Central Córdoba (SdE)", "Racing (O)", 1, 3),
    _llave_espejada("Tercera fase", "Unión (MdP)", "Racing (C)", 1, 1),
    _llave_espejada("Tercera fase", "Racing (C)", "Unión (MdP)", 2, 0),
    _llave_espejada("Cuarta fase", "Sportivo Belgrano", "Central Norte (S)", 2, 3),
    _llave_espejada("Cuarta fase", "Central Norte (S)", "Sportivo Belgrano", 1, 2),
    _llave_espejada("Cuarta fase", "Crucero del Norte", "Juventud Unida Universitario", 1, 0),
    _llave_espejada("Cuarta fase", "Juventud Unida Universitario", "Crucero del Norte", 1, 2),
    _llave_espejada("Reválida - Segunda ronda", "Juventud Unida Universitario", "Juventud Antoniana", 0, 1),
    _llave_espejada("Reválida - Segunda ronda", "Juventud Antoniana", "Juventud Unida Universitario", 0, 1),
    _llave_espejada("Reválida - Tercera ronda", "Libertad (S)", "Central Norte (S)", 1, 2),
    _llave_espejada("Reválida - Tercera ronda", "Central Norte (S)", "Libertad (S)", 0, 1),
    _llave_espejada("Cuarta fase", "Ramón Santamarina", "Racing (O)", 2, 2),
    _llave_espejada("Cuarta fase", "Racing (O)", "Ramón Santamarina", 2, 2),
    _llave_espejada("Cuarta fase", "Talleres (C)", "Racing (C)", 1, 1),
    _llave_espejada("Cuarta fase", "Racing (C)", "Talleres (C)", 1, 1),

    # ------------------------------------------------------------------
    # La Tercera Fase del Argentino A 2010-11: la pagina tiene las dos patas del
    # lado equivocado, y es la unica de las cuatro llaves de esa tabla que no
    # coincide con RSSSF.
    #
    # LA PAGINA SI AFIRMA LA LOCALIA -- no es un cuadro dibujado, es una tabla con
    # una columna rotulada `Local - Ida` y otra `Local - Vuelta` --, asi que hace
    # falta evidencia para contradecirla. Hay tres capas, y ninguna sola alcanza:
    #
    # 1. LA PROPIA TABLA. Sus cuatro filas se leen igual y las otras TRES
    #    coinciden exacto con RSSSF en quien fue local en la ida: Talleres (Cba),
    #    Union (S) y Huracan (TA). La unica que discrepa es esta.
    # 2. RSSSF. `First Legs [May 18] ... Svo Desamparados 3-2 Union (MdP)` y
    #    `Second Legs [May 22] ... Union (MdP) 1-1 Svo Desamparados`. Los dos
    #    marcadores coinciden EXACTO con los nuestros bajo el espejo, en las dos
    #    patas, que ya es mas de lo que explicaria una casualidad. Y el testigo de
    #    localia de esta pagina aprobo a esta fuente: ocho partidos en comun y
    #    estos dos son los unicos al reves, asi que el repo YA importa catorce
    #    partidos suyos confiando en ese orden.
    # 3. UN DIARIO DE SAN JUAN, contemporaneo. Diario de Cuyo del 19/05/2011
    #    cuenta el 3-2 de Sportivo como local en San Juan y anuncia "la revancha
    #    que se disputaria el fin de semana siguiente EN MAR DEL PLATA". Y el del
    #    22/05/2011, sobre el 1-1: "Desamparados empezo ganando ... Luego, en la
    #    segunda etapa llego el empate DEL LOCAL. Collantes ... puso el 1 a 1",
    #    y Collantes es jugador de Union de Mar del Plata. El "San Juan, 22 de
    #    mayo.-" del arranque es el fechado del diario, que es sanjuanino, y no la
    #    sede: leerlo como sede es el error facil.
    #
    # POR QUE NO LO AGARRA NINGUN CHEQUEO INTERNO: el global que publica la propia
    # pagina, 3-4, es el mismo con las dos orientaciones. El error es invisible
    # desde adentro y por eso sobrevivio.
    # ------------------------------------------------------------------
    Correccion(
        pagina="Torneo Argentino A 2010-11", jornada="Tercera Fase",
        dice=("Unión (MdP)", "Desamparados", 2, 3),
        debe=("Desamparados", "Unión (MdP)"),
        porque="La ida se jugo en San Juan y la gano Desamparados 3-2. RSSSF la "
               "escribe asi bajo `First Legs [May 18]`, y el Diario de Cuyo del "
               "19/05/2011 la cuenta como local y anuncia la revancha en Mar del "
               "Plata. En la misma tabla de la pagina, las otras tres llaves "
               "coinciden con RSSSF en quien fue local en la ida."),
    Correccion(
        pagina="Torneo Argentino A 2010-11", jornada="Tercera Fase",
        dice=("Desamparados", "Unión (MdP)", 1, 1),
        debe=("Unión (MdP)", "Desamparados"),
        porque="La vuelta se jugo en Mar del Plata. RSSSF la escribe `Unión (MdP) "
               "1-1 Svo Desamparados` bajo `Second Legs [May 22]`, y el Diario de "
               "Cuyo del 22/05/2011 dice que el empate fue `del local` y que lo "
               "hizo Collantes, que es jugador de Union de Mar del Plata."),

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
    nueve que arbitro worldfootball, ocho le dan la razon a worldfootball y uno
    a Wikipedia.

    UNA LLAVE NO TIENE TABLA DE POSICIONES, y ahi ese arbitro no existe. Quedan
    dos, los dos ya usados en este archivo: que LA PAGINA SE DESMIENTA A SI
    MISMA --su regla de desempate escrita, su tabla de la ronda anterior y a
    quien pone en negrita tienen que cerrar entre ellos-- y UNA FUENTE
    CONTEMPORANEA que no dependa de Wikipedia. Los cuatro de la Revalida del
    Argentino A 2011-12 son de esa clase, dos por cada arbitro, y llevan la
    evidencia escrita en su `porque`.

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

    # Los penales, cuando lo que esta mal son ELLOS y no los goles. Hizo falta al
    # llegar el primero de esa clase: la Copa Argentina 2018-19 publica
    # "Almagro 1-1 Atletico de Rafaela" con los penales 3-4, y el 1-1 es correcto
    # -- lo que esta dado vuelta es la tanda --. Sin esto la correccion no existia
    # como idea: `debe == dice` la salteaba entera y no habia donde escribirla.
    #
    # `penales_debe` en None quiere decir "no los toques". Para BORRARLOS no hace
    # falta decirlo: si `debe` deja de ser empate, la tanda no pudo existir, y
    # `penales_solo_en_empates` lo denunciaria acto seguido.
    penales_dice: tuple[int, int] | None = None
    penales_debe: tuple[int, int] | None = None


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
    # --- Copa Argentina 2018-19: seis filas mal en una sola ronda ---
    #
    # No las encontro nadie leyendo la pagina. Empezo el chequeo de la cadena de
    # llaves, que pregunta si el que juega una ronda gano la anterior: dos clubes
    # seguian jugando -- y ganando -- despues de un partido que, segun la grilla,
    # habian perdido. Al ir a buscar el testigo de afuera aparecieron las otras
    # cuatro, que ningun chequeo ve porque el que pasa es el mismo en las dos
    # versiones y solo cambia el marcador.
    #
    # Que la grilla de un articulo pueda estar mal mientras su anexo esta bien es
    # lo que deja este caso: son dos partes de la MISMA fuente y no se hablan.
    Marcador(
        pagina="Copa Argentina 2018-19",
        jornada="Treintaidosavos", local="Almagro",
        visita="Atlético de Rafaela",
        dice=(1, 1), debe=(1, 1), penales_dice=(3, 4), penales_debe=(4, 2),
        porque="7 de marzo de 2019, Centenario Ciudad de Quilmes. El 1-1 esta bien; "
               "lo que esta dado vuelta es la TANDA. La grilla publica los penales "
               "3-4, o sea que paso Rafaela.\nLA PROPIA PAGINA SE DESMIENTE: Almagro "
               "juega los dieciseisavos seis dias despues, le gana a Boca Juniors por "
               "penales y llega a cuartos, donde pierde con River. Un club eliminado "
               "no juega tres rondas mas.\nRSSSF corrige tambien el numero: `Club "
               "Almagro [4] 1-1 [2] AMSyD Atletico de Rafaela`, misma fecha y mismo "
               "estadio. La tanda fue 4-2 y no 4-3.\nLA RONDA ENTERA, MEDIDA. De los "
               "27 cruces de estos treintaidosavos que se pueden comparar contra "
               "RSSSF, la grilla coincide en 20 y difiere en 7. Eso ya dice que RSSSF "
               "no esta copiando a Wikipedia -- una fuente derivada coincidiria en "
               "los 27 --, y ademas deja repartir la culpa: de esas 7, SEIS son "
               "errores de la grilla, cada uno confirmado ademas por el anexo de la "
               "propia Wikipedia, y UNA es de RSSSF, que escribe 1-2 en el Patronato "
               "- Dock Sud cuando fue 1-1 definido por penales. Ahi la grilla tiene "
               "razon y no se toca. No se elige una fuente: se arbitra partido por "
               "partido. "),
    Marcador(
        pagina="Copa Argentina 2018-19",
        jornada="Treintaidosavos", local="Newell's Old Boys",
        visita="Villa Mitre",
        dice=(0, 0), debe=(1, 2), penales_dice=(5, 3),
        porque="24 de marzo de 2019, 15 de Abril de Santa Fe. La grilla publica un "
               "0-0 con penales 5-3 para Newell's, de donde saldria que paso "
               "Newell's. Pero Villa Mitre juega los dieciseisavos, le gana a San "
               "Martin (SJ) y llega a octavos.\nEl cuadro de la misma pagina ya decia "
               "otra cosa: le pone 1 a Newell's y 2 a Villa Mitre, y marca a Villa "
               "Mitre como el que pasa.\nRSSSF cierra la discusion y explica de donde "
               "sale el lio: `CA Newell's Old Boys 1-2 Club Villa Mitre`, con la nota "
               "`abandoned in 90+1, score stood on Apr 5`. El partido se abandono a "
               "los 90+1 y el resultado quedo firme recien el 5 de abril; el 0-0 con "
               "penales no describe ningun partido que se haya jugado.\nLos penales "
               "se borran solos: un 1-2 no es empate.\nLA RONDA ENTERA, MEDIDA. De "
               "los 27 cruces de estos treintaidosavos que se pueden comparar contra "
               "RSSSF, la grilla coincide en 20 y difiere en 7. Eso ya dice que RSSSF "
               "no esta copiando a Wikipedia -- una fuente derivada coincidiria en "
               "los 27 --, y ademas deja repartir la culpa: de esas 7, SEIS son "
               "errores de la grilla, cada uno confirmado ademas por el anexo de la "
               "propia Wikipedia, y UNA es de RSSSF, que escribe 1-2 en el Patronato "
               "- Dock Sud cuando fue 1-1 definido por penales. Ahi la grilla tiene "
               "razon y no se toca. No se elige una fuente: se arbitra partido por "
               "partido. "),
    Marcador(
        pagina="Copa Argentina 2018-19",
        jornada="Treintaidosavos", local="Nueva Chicago",
        visita="Central Córdoba (SdE)",
        dice=(1, 2), debe=(0, 1),
        porque="3 de abril de 2019, Brigadier General Estanislao Lopez, Santa Fe. La "
               "grilla publica 1-2. Fue 0-1, y es el que mas testigos junto.\nUN SOLO "
               "GOL, Y TRES FUENTES QUE LO CUENTAN IGUAL. El sitio oficial del torneo "
               "titula su nota `Nueva Chicago 0 - Central Cordoba (SdE) 1` y le "
               "adjudica el gol a Facundo Melivilo. Diario Panorama, de Santiago del "
               "Estero, lo ubica a los 23 segundos del segundo tiempo: Melivilo quedo "
               "mano a mano con Minaglia y definio con un zurdazo. El Litoral, de la "
               "ciudad donde se jugo, cuenta la misma jugada con otras palabras y "
               "agrega el error -- una larga cesion y un mal cruce de Enzo Lettieri "
               "--. Ninguna le da un segundo gol a Central ni ninguno a Chicago: para "
               "el 1-2 harian falta tres goleadores y no aparece mas que uno.\nLa "
               "ficha oficial del partido (copaargentina.org, partido 3209) trae las "
               "dos formaciones completas y el arbitro, Pablo Gimenez. Y la Wikipedia "
               "en INGLES publica el partido con `score=0-1`, `goals2=Melivilo 46'` y "
               "ese mismo informe como referencia: es la version en castellano la que "
               "quedo sola.\nEL ANEXO DE LA PROPIA WIKIPEDIA YA DECIA OTRA COSA. "
               "`Anexo:Treintaidosavos de final de la Copa Argentina 2018-19` trae "
               "una plantilla por partido con el marcador, el entretiempo, el "
               "arbitro, los goleadores con su minuto y el link al informe oficial de "
               "copaargentina.org. Contra la grilla del articulo principal coincide "
               "en 28 de 32 y difiere justo en estos. La grilla es una fila pelada, "
               "sin goleadores y sin referencia; el anexo tiene con que "
               "sostenerse.\nLA RONDA ENTERA, MEDIDA. De los 27 cruces de estos "
               "treintaidosavos que se pueden comparar contra RSSSF, la grilla "
               "coincide en 20 y difiere en 7. Eso ya dice que RSSSF no esta copiando "
               "a Wikipedia -- una fuente derivada coincidiria en los 27 --, y ademas "
               "deja repartir la culpa: de esas 7, SEIS son errores de la grilla, "
               "cada uno confirmado ademas por el anexo de la propia Wikipedia, y UNA "
               "es de RSSSF, que escribe 1-2 en el Patronato - Dock Sud cuando fue "
               "1-1 definido por penales. Ahi la grilla tiene razon y no se toca. No "
               "se elige una fuente: se arbitra partido por partido. "),
    Marcador(
        pagina="Copa Argentina 2018-19",
        jornada="Treintaidosavos", local="Defensa y Justicia",
        visita="Gimnasia y Tiro (S)",
        dice=(2, 1), debe=(1, 0),
        porque="16 de abril de 2019, Florencio Sola, Banfield. La grilla publica 2-1. "
               "Fue 1-0.\nUN SOLO GOL: Nicolas Fernandez a los 26 del primer tiempo. "
               "Lo dan Infobae y El Tribuno de Salta, los dos con las 22 formaciones, "
               "los dos entrenadores -- Beccacece y Ramasco -- y el arbitro, Andres "
               "Merlos. Nada de eso esta en la grilla, asi que no salio de "
               "ahi.\nCUIDADO CON CONTARLOS COMO DOS: Infobae acredita `Con "
               "informacion de Telam` y El Tribuno publica la version larga del mismo "
               "cable. Es UN testigo periodistico servido por dos diarios. Alcanza "
               "igual -- un cable con goleador, minuto, 22 nombres y arbitro no se "
               "deriva de una fila de tabla --, pero conviene que quede "
               "escrito.\nRSSSF, por afuera: `CSyD Defensa y Justicia 1-0 Cd Gimnasia "
               "y Tiro`, mismo dia y mismo estadio.\nEL ANEXO DE LA PROPIA WIKIPEDIA "
               "YA DECIA OTRA COSA. `Anexo:Treintaidosavos de final de la Copa "
               "Argentina 2018-19` trae una plantilla por partido con el marcador, el "
               "entretiempo, el arbitro, los goleadores con su minuto y el link al "
               "informe oficial de copaargentina.org. Contra la grilla del articulo "
               "principal coincide en 28 de 32 y difiere justo en estos. La grilla es "
               "una fila pelada, sin goleadores y sin referencia; el anexo tiene con "
               "que sostenerse.\nLA RONDA ENTERA, MEDIDA. De los 27 cruces de estos "
               "treintaidosavos que se pueden comparar contra RSSSF, la grilla "
               "coincide en 20 y difiere en 7. Eso ya dice que RSSSF no esta copiando "
               "a Wikipedia -- una fuente derivada coincidiria en los 27 --, y ademas "
               "deja repartir la culpa: de esas 7, SEIS son errores de la grilla, "
               "cada uno confirmado ademas por el anexo de la propia Wikipedia, y UNA "
               "es de RSSSF, que escribe 1-2 en el Patronato - Dock Sud cuando fue "
               "1-1 definido por penales. Ahi la grilla tiene razon y no se toca. No "
               "se elige una fuente: se arbitra partido por partido. "),
    Marcador(
        pagina="Copa Argentina 2018-19",
        jornada="Treintaidosavos", local="Mitre (SdE)",
        visita="Deportivo Roca",
        dice=(2, 1), debe=(1, 0),
        porque="17 de abril de 2019, Centenario Ciudad de Quilmes. La grilla publica "
               "2-1. Fue 1-0.\nEl anexo lo da con un solo gol y sobre la hora: `Mitre "
               "(SdE) 1:0 (0:0) Deportivo Roca`, gol de Cadenazzi a los 90, arbitro "
               "Pablo Echavarria. El entretiempo 0:0 lo confirma.\nRSSSF, por afuera: "
               "`CA Mitre 1-0 CSyD General Roca`, mismo estadio.\nA este NO se le "
               "busco prensa: el anexo ya nombra al goleador y el minuto, que es la "
               "vara, y RSSSF coincide desde afuera. De los seis es el que menos "
               "testigos tiene, y corresponde decirlo.\nEL ANEXO DE LA PROPIA "
               "WIKIPEDIA YA DECIA OTRA COSA. `Anexo:Treintaidosavos de final de la "
               "Copa Argentina 2018-19` trae una plantilla por partido con el "
               "marcador, el entretiempo, el arbitro, los goleadores con su minuto y "
               "el link al informe oficial de copaargentina.org. Contra la grilla del "
               "articulo principal coincide en 28 de 32 y difiere justo en estos. La "
               "grilla es una fila pelada, sin goleadores y sin referencia; el anexo "
               "tiene con que sostenerse.\nLA RONDA ENTERA, MEDIDA. De los 27 cruces "
               "de estos treintaidosavos que se pueden comparar contra RSSSF, la "
               "grilla coincide en 20 y difiere en 7. Eso ya dice que RSSSF no esta "
               "copiando a Wikipedia -- una fuente derivada coincidiria en los 27 --, "
               "y ademas deja repartir la culpa: de esas 7, SEIS son errores de la "
               "grilla, cada uno confirmado ademas por el anexo de la propia "
               "Wikipedia, y UNA es de RSSSF, que escribe 1-2 en el Patronato - Dock "
               "Sud cuando fue 1-1 definido por penales. Ahi la grilla tiene razon y "
               "no se toca. No se elige una fuente: se arbitra partido por partido. "),
    Marcador(
        pagina="Campeonato de Primera C 2025 (Argentina)",
        jornada="Primera fase", local="J. J. de Urquiza", visita="Sportivo Barracas",
        dice=(0, 3), debe=(0, 2),
        porque="Vuelta de los octavos del reducido, 5 de octubre de 2025. Lo destapo "
               "el cuadro de llaves, que es el unico arbitro que la fase final tiene: "
               "publica 0-2 con un global de 5-0, y la grilla 0-3, que daria 6-0.\n"
               "LA PAGINA SE CONTRADICE SOLA Y DE DOS MANERAS. La plantilla del "
               "partido trae `resultado = 0:3` y, tres lineas mas abajo, "
               "`global = 0:5`; con el 3-0 de la ida, 3+3 da 6 y no 5. Y el cuadro "
               "de llaves de la misma pagina dice 0-2, que si cierra.\n"
               "Afuera no aparece un solo 0-3. La cronica del propio J. J. de "
               "Urquiza (jjurquiza.com.ar, 6/10/2025, por Gustavo Aroldo) titula "
               "\"J.J.Urquiza 0 vs Sportivo Barracas 2\" y da \"Goles: 62m Facundo "
               "Figueroa y 68m Julio Barrionuevo (SPB)\", con las dos formaciones "
               "completas, el expulsado, el arbitro y los dos jueces de linea, mas "
               "el partido entero en video. DOS goles nombrados, no tres: para un "
               "0-3 falta un gol que nadie escribio.\n"
               "Lo confirman por su cuenta Sofascore -- mismos dos goleadores, a los "
               "63 y 69, un minuto corridos, que es senal de recoleccion propia y no "
               "de copia -- y ESPN en tres paginas distintas, con "
               "\"Sportivo Barracas advance 5-0 on aggregate\".",
    ),
    Marcador(
        pagina="Campeonato de Primera B Nacional 2011-12", jornada="Fecha 17",
        local="Huracán", visita="Defensa y Justicia", dice=(1, 3), debe=(2, 3),
        porque="Falta el gol de Gaston Machin a los 43. El timeline de ESPN da los "
               "cinco goles con minuto y autor -- Piriz Alvez 5 y 51 y Ricci 82 para "
               "Defensa; Pablo Lopez 35 y Machin 43 para Huracan -- y ademas el "
               "entretiempo 2-1 a favor de Huracan, que es incompatible con un 1-3: "
               "con un solo gol no se puede ir ganando al descanso. El archivo del "
               "propio club dice \"termino perdiendo 3 a 2\" y lista dos goleadores "
               "quemeros.\n"
               "NO COPIA A WIKIPEDIA: ESPN, el archivo del club y Transfermarkt "
               "coinciden con la pagina en la otra rueda -- el 4-2 de la Fecha 36, y "
               "ESPN hasta con sus seis goleadores -- y difieren solo en esta. Ademas "
               "sumando los 38 partidos de Huracan en cualquiera de esas dos fuentes "
               "da GF43 GC50, que es exactamente lo que dice la tabla; con el 1-3 da "
               "42.\n"
               "OJO CON RSSSF: arrastra el mismo 1-3 y la misma tabla, asi que su "
               "grilla no cierra con su propia tabla. No sirve de arbitro aca."),
    Marcador(
        pagina="Torneo Argentino A 2011-12", jornada="Fecha 1",
        local="Crucero del Norte", visita="Tiro Federal", dice=(0, 0), debe=(1, 1),
        porque="Una cronica del 23/08/2011, dos dias despues del partido y con fuente "
               "atribuida a afa.org.ar, resume la fecha entera: \"Crucero del Norte de "
               "Posadas, con gol de Gabriel Mosevich, empato con Tiro Federal de "
               "Rosario 1-1. Igualo, Bernardo Cuesta\". Es contemporanea y nombra a "
               "los dos goleadores.\n"
               "Y LA FILA DE ESA FECHA TIENE OTRA CELDA CORROMPIDA, que sirve de "
               "testigo: en el mismo renglon, Talleres (C) - Libertad (S) figura hoy "
               "como 2-0, pero la revision de Wikipedia de agosto de 2011 "
               "(oldid=49189384) lo escribia 1-1 CON DOS REFERENCIAS, Soccerway y La "
               "Voz del Interior. Alguien lo degrado despues. O sea que el que "
               "escribio esta fila se comio goles en mas de un partido, y en el caso "
               "que se puede auditar por historial la tabla tenia razon.\n"
               "OJO CON RSSSF: su tabla es la oficial pero su grilla suma 30/20 y "
               "25/27, o sea que falla su propia aritmetica igual que Wikipedia."),
    Marcador(
        pagina="Campeonato de Primera Nacional 2021", jornada="Fecha 19",
        local="Almirante Brown", visita="Mitre (SdE)", dice=(1, 1), debe=(0, 0),
        porque="La sintesis de Solo Ascenso trae las dos formaciones completas, el "
               "arbitro (Hernan Mastrangelo), la hora de inicio y NINGUN gol. Un 1-1 "
               "tendria dos goleadores que nadie nombra.\n"
               "NO COPIA A WIKIPEDIA: coincide con la pagina en la otra rueda -- el "
               "3-2 de la Fecha 2, con sus cinco goles y sus asistencias -- y difiere "
               "solo en esta."),
    Marcador(
        pagina="Torneo Federal A 2017-18", jornada="Fecha 15",
        local="Guaraní Antonio Franco", visita="Deportivo Mandiyú",
        dice=(2, 1), debe=(4, 1),
        porque="La cronica da los cinco goles: Alan Almiron a los 4 y a los 12, "
               "Nicolas Monje a los 30, y los demas. Un 2-1 se come dos.\n"
               "NO COPIA A WIKIPEDIA: la misma fuente coincide con la pagina en la "
               "otra rueda entre estos clubes -- el 0-1 de la Fecha 6, con el gol de "
               "Ostrowski sobre el final -- y difiere solo en esta."),
    Marcador(
        pagina="Torneo Federal A 2022", jornada="Fecha 2",
        local="San Martín (F)", visita="Central Norte (S)", dice=(2, 2), debe=(0, 0),
        porque="El Tribuno de Salta publico la cronica del partido esa misma noche: "
               "\"igualo 0 a 0 con San Martin, por la segunda fecha de la zona 2 del "
               "Federal A\", con los dos tiempos narrados sin goles. Ascenso del "
               "Interior da el mismo 0-0 con las dos formaciones, escritas aparte "
               "(difieren en un nombre de pila). Transfermarkt coincide.\n"
               "NO COPIA A WIKIPEDIA: el mismo diario cubrio las dos ruedas y coincide "
               "con la pagina en la otra, el 3-3 de la Fecha 19.\n"
               "OJO, Y ES IMPORTANTE: esta correccion NO hace cerrar la pagina, y no "
               "tiene por que. Los tres clubes desviados de esa zona -- San Martin (F), "
               "Central Norte (S) y Crucero del Norte -- NO se desvian en espejo, asi "
               "que ningun arreglo a un solo partido entre dos de ellos puede "
               "reconciliar las tres filas: hay mas de un error. Con este arreglo la "
               "fila de Central Norte cierra y la de San Martin se corre para el otro "
               "lado. Se carga igual porque el marcador es el que se jugo, que es lo "
               "que el dataset guarda; que la tabla siga sin cerrar es un problema de "
               "la tabla."),
    Marcador(
        pagina="Campeonato de Primera B 2024 (Argentina)", jornada="Fecha 8",
        local="Deportivo Armenio", visita="Argentino de Quilmes",
        dice=(3, 1), debe=(2, 1),
        porque="La cronica da los dos goles con su minuto y no hay un tercero: Tomas "
               "Jerez Sayago a los 51 para Armenio y Alejo Osella en contra a los 84, "
               "que es el gol de Argentino de Quilmes. Un 3-1 no tiene donde poner el "
               "que falta.\n"
               "NO COPIA A WIKIPEDIA: la misma fuente reproduce el resto de la fecha "
               "igual que la pagina y difiere solo en este."),
    Marcador(
        pagina="Torneo Federal A 2024", jornada="Fecha 10",
        local="Atenas (RC)", visita="Ferro Carril Oeste (GP)", dice=(2, 0), debe=(1, 0),
        porque="Un solo gol, de Ezequiel Bardin de penal sobre el cierre del segundo "
               "tiempo, y las cronicas lo cuentan como el unico del partido. El 2-0 "
               "de la grilla le agrega uno que nadie convirtio.\n"
               "NO COPIA A WIKIPEDIA: las fuentes coinciden con la pagina en los otros "
               "partidos de la fecha."),
    Marcador(
        pagina="Campeonato de Primera B 2021 (Argentina)", jornada="Fecha 5",
        local="Defensores Unidos", visita="Los Andes", dice=(0, 1), debe=(0, 2),
        porque="El historial del propio club visitante da dos goles, de Facundo "
               "Quintana y E. Lopez. El 0-1 se come uno.\n"
               "NO COPIA A WIKIPEDIA: es un historial de club, armado partido por "
               "partido desde su propio archivo, y coincide con la pagina en el resto "
               "del torneo."),
    Marcador(
        pagina="Torneo Argentino A 2011-12", jornada="Fecha 1",
        local="Talleres (C)", visita="Libertad (S)", dice=(2, 0), debe=(1, 1),
        porque="Soccerway contemporaneo, rescatado del Web Archive con capturas de "
               "2011: la ficha de la fecha 1 da \"Talleres Cordoba vs. Libertad "
               "1 - 1\" con entretiempo 0-0, y los goles de Claudio Riano a los 49 "
               "para Talleres y Paolo Berardi a los 56 para Libertad. Un 2-0 no "
               "tiene donde poner el gol de Libertad.\n"
               "NO COPIA A WIKIPEDIA: la ficha archivada de la fecha 14, del mismo "
               "sitio y del mismo mes, da el 1-2 igual que la pagina. Coincide en "
               "una rueda y difiere en la otra.\n"
               "Y OJO CON RSSSF, que aca vuelve a ser la trampa: su grilla copia el "
               "mismo 2-0 que Wikipedia. Mirarle solo la grilla habria confirmado "
               "el error."),
    Marcador(
        pagina="Torneo Federal A 2024", jornada="Fecha 11",
        local="Independiente (C)", visita="El Linqueño", dice=(0, 0), debe=(0, 1),
        porque="Dos sitios de ascenso con cronica propia dan Independiente de "
               "Chivilcoy 0 - El Linqueño 1, con el gol de Andres Mc Cormick sobre "
               "el final: Solo Ascenso (sintesis 41178, estadio Raul Lungarzo, "
               "arbitro Cristian Rubiano) y Ascenso del Interior (nota 33058, que "
               "ademas cuenta un penal errado). Un 0-0 no tiene donde ponerlo.\n"
               "NO COPIAN A WIKIPEDIA: los dos coinciden con la pagina en la fecha 2 "
               "(0-0 en Lincoln, estadio Leonardo Costa, arbitro Billone) y en un "
               "tercer cruce. Difieren solo en este."),
    Marcador(
        pagina="Torneo Federal A 2023", jornada="Fecha 11",
        local="Douglas Haig", visita="Independiente (C)", dice=(1, 0), debe=(0, 1),
        porque="La prensa de las DOS ciudades cuenta el mismo partido desde lados "
               "opuestos y coincide: La Razon de Chivilcoy titula \"Enorme triunfo "
               "de Independiente en Pergamino\" y La Opinion de Pergamino, "
               "\"Douglas Haig perdio su invicto como local\". Los dos diarios "
               "narran una derrota del local. RSSSF ademas lo publica en su grilla "
               "de la Zona 3: \"CA Douglas Haig 0- 1 CA Independiente\".\n"
               "NO COPIA A WIKIPEDIA: en 2023 estos dos se cruzaron CUATRO veces "
               "(zona de 9 clubes, cuadruple rueda) y las fuentes coinciden con la "
               "pagina en las otras tres. Difieren solo en esta."),
    Marcador(
        pagina="Torneo Federal A 2023", jornada="Fecha 11",
        local="Unión (S)", visita="Sportivo Las Parejas", dice=(0, 1), debe=(1, 0),
        porque="Ascenso del Interior publica una cronica propia de cada rueda, con "
               "formaciones, cuerpo arbitral y estadio. La de esta (nota 31594) "
               "titula \"Union (Sunchales) 1 - 0 Sportivo A.C. (L. Parejas)\" y "
               "cuenta que \"Alexandro Ponce hizo estallar el festejo Albiverde en "
               "tiempo de descuento\". RSSSF coincide.\n"
               "NO COPIA A WIKIPEDIA: su cronica de la fecha 2 (nota 31240) da "
               "\"Sportivo A.C. 1 - 0 Union\" con gol de Jonatan Font a los 67, "
               "igual que la pagina. Coincide en una rueda y difiere en esta."),
    Marcador(
        pagina="Torneo Federal A 2023", jornada="Fecha 34",
        local="Crucero del Norte", visita="Central Norte (S)", dice=(1, 2), debe=(1, 1),
        porque="La pagina publica la fecha 34 con el MISMO marcador que la fecha 16, "
               "y no es casualidad: le copio el resultado. Ascenso del Interior tiene "
               "las dos ruedas en notas separadas, con sintesis propia cada una -- la "
               "31733 da la fecha 16 como Crucero 1-2 Central Norte (Reyes a los 5, "
               "Rostagno a los 37), y la 32136 da la fecha 34, en el Comandante "
               "Andres Guacurari, como Crucero 1-1 Central Norte, con Ivan Benitez a "
               "los 44 y el empate de Central Norte.\n"
               "NO COPIA A WIKIPEDIA: coincide con la pagina en las otras ruedas, "
               "incluido el 1-1 de Salta de la fecha 25 que confirma tambien el sitio "
               "oficial de Crucero del Norte."),
    Marcador(
        pagina="Torneo Argentino A 2011-12", jornada="Fecha 14",
        local="Defensores de Belgrano (VR)", visita="Racing (O)",
        dice=(1, 0), debe=(0, 1),
        porque="El G-E-P de la tabla decia que un partido entero estaba al reves "
               "en este par, y de los dos cruces la aritmetica dejaba vivo solo "
               "este. Lo confirma la prensa de Olavarria, dos veces y con dos "
               "manos distintas. Infoeme del 28/11/2011, el dia despues, cita al "
               "zaguero de Racing hablando de \"este triunfo en Villa Ramallo\" y "
               "publica las posiciones tras la 14a fecha; recalculadas desde la "
               "grilla, esas posiciones solo salen con el 0-1. Y una nota de "
               "Infoeme del 10/10/2012 repasa los cuatro cruces de 2011 entre los "
               "dos clubes y nombra \"la victoria 1-0 en Ramallo con gol de "
               "Baroni\" -- Gonzalo Baroni era delantero de Racing (O), lo "
               "confirma su ficha en bdfa.com.ar --, o sea 0-1 para el visitante. "
               "Un tercer testigo da el gol a los 53 de penal.\n"
               "NO COPIA A WIKIPEDIA: esa misma nota de 2012 coincide con la "
               "pagina en los otros TRES cruces de ese anio (el 0-0 de la fecha 3 "
               "en el Buglione Martinese, el 1-0 de Racing por Copa Argentina y el "
               "0-0 del Endecagonal) y difiere solo en este.\n"
               "OJO CON RSSSF, que es la trampa de este caso: su GRILLA copia el "
               "1-0 igual que Wikipedia, pero su propia TABLA da a Racing 34 "
               "puntos y a Defensores 36, y esos totales solo cierran con el 0-1. "
               "Arrastra la misma inconsistencia. Leer solo su grilla y darla por "
               "verificacion fue un error que se cometio aca antes de corregirlo."),

    # --- Argentino A 2011-12: las cuatro patas de la Revalida que no cerraban ---
    #
    # La Revalida es eliminacion directa y no tiene tabla, asi que el arbitro de
    # siempre no esta. Lo reemplazan dos testigos que la pagina no controla, y las
    # dos llaves se resolvieron por caminos distintos.
    #
    # LA TERCERA RONDA LA DESMIENTE LA PROPIA PAGINA. Escribe su regla con todas
    # las letras: "En caso de empate en puntos y diferencia de goles al finalizar
    # la Ronda clasificaran a la Tercera Fase las posiciones 1. Actuaran de local
    # en el primer partido las posiciones 2". Su propia tabla de la Primera ronda
    # de la Revalida Zona Norte pone a Libertad 1o con 13 puntos y a Central Norte
    # 2o con 9 --RSSSF publica esa tabla identica--. Con los marcadores que la
    # pagina publica la serie termina 2-2, y entonces su regla manda pasar a
    # Libertad; sin embargo la pagina pone a CENTRAL NORTE en negrita, y es Central
    # Norte el que juega la Tercera Fase seis dias despues. Con el 2-0 de RSSSF la
    # serie da 3-1 y no hay desempate que aplicar: no se contradice nada.
    #
    # Esa misma regla confirma ademas el espejo de la localia --el 2o es local en
    # la ida, y el 2o es Central Norte--, que es lo que dicen las 28 `Correccion`
    # de esta pagina: rotula al reves sus dos columnas.
    #
    # LA SEGUNDA RONDA LA DESMIENTE EL BLOG DEL PROPIO CLUB. Ahi la pagina NO se
    # contradice: las dos versiones dan la serie 1-1 y las dos dejan pasar a
    # Juventud Unida por ventaja deportiva, o sea que la aritmetica no discrimina y
    # habia que ir a buscar afuera. `juveantoniana.blogspot.com` --el mismo que ya
    # cerro el abandono del Clausura 2009-10; ver `rsssf._SIN_DESENLACE`-- publica
    # las dos patas la semana que se jugaron, con goleadores y formaciones.
    #
    # Y NO COPIAN A WIKIPEDIA, que es lo que hay que probar antes de creerles: de
    # las SEIS llaves de la Segunda y la Tercera ronda, RSSSF coincide con la
    # pagina --ya espejada-- en CUATRO, dato por dato, y difiere solo en estas dos.
    # Una fuente derivada coincidiria en las seis.
    #
    # Los cuatro `dice` van en la orientacion ESPEJADA, que es como esta la fila
    # cuando les toca el turno: `aplicar` corre las `Correccion` primero.
    Marcador(
        pagina="Torneo Argentino A 2011-12", jornada="Reválida - Segunda ronda",
        local="Juventud Antoniana", visita="Juventud Unida Universitario",
        dice=(1, 0), debe=(1, 1),
        porque="22 de abril de 2012, Padre Ernesto Martearena. El blog del propio "
               "club lo publica el mismo dia, en el post \"EL EMPATE NO SIRVE\": "
               "\"Juventud empato con Juv.universitaria de San Luis 1a1\", con el gol "
               "antoniano de Claudio Acosta a los 4 y el de la visita de Seltzer a "
               "los 43, y cierra con la ficha: \"Juventud Antoniana 1 / JUV Univ "
               "DE SAN LUIS 1 / GOLES ACOSTA (CJA) SELTSER (JUUSL)\".\n"
               "EL TITULO SOLO TIENE SENTIDO CON EL 1-1. Juventud Unida iba con "
               "ventaja deportiva --lo dice el previo del mismo blog, \"ante "
               "igualdad de puntos y goles frente a Antoniana, avanzara al "
               "siguiente cruce\"--, asi que con el 1-0 de la pagina a Antoniana el "
               "empate SI le servia. RSSSF da lo mismo que el blog.\n"
               "Y HAY UN TERCERO, que ya estaba citado en este archivo sin que "
               "nadie lo leyera para esto: el blog de Jose Carluccio, el que fija "
               "la sede de las cuatro idas de esta ronda en `_LLAVES_2011_12`, "
               "escribe \"en Salta: Juventud Antoniana 1, Juventud Unida "
               "Universitario 1\". Tres fuentes independientes dan 1-1 y ninguna "
               "da el 1-0. http://juveantoniana.blogspot.com/2012/04/"),
    Marcador(
        pagina="Torneo Argentino A 2011-12", jornada="Reválida - Segunda ronda",
        local="Juventud Unida Universitario", visita="Juventud Antoniana",
        dice=(1, 0), debe=(0, 0),
        porque="29 de abril de 2012, Mario Sebastian Diez. El mismo blog, post "
               "\"NUEVO FRACAZO\": \"Juventud empato en el Bajo con Juventud "
               "Antoniana de salta sin abrir el marcador y paso a una nueva "
               "fase\". No es una frase suelta: publica las dos formaciones enteras "
               "con el cero al lado del nombre, \"Juventud Unida Universitario "
               "(San Luis) (0)\" y \"Juventud Antoniana (0)\", once por once y los "
               "cambios.\n"
               "Y explica el desenlace con la misma cuenta: \"El equipo puntano "
               "tenia ventaja deportiva (termino mejor posicionado que su rival) y "
               "con el empate le alcanzaba para pasar de ronda\". RSSSF da lo "
               "mismo. El 1-0 de la pagina no lo dice ninguna otra fuente. "
               "http://juveantoniana.blogspot.com/2012/05/\n"
               "NO COPIA A WIKIPEDIA, y aca hace falta decirlo porque un 0-0 no "
               "tiene goleadores que lo prueben solos. De las CUATRO llaves de "
               "esta Segunda ronda, RSSSF reproduce las otras tres tal cual las "
               "da la pagina ya espejada --Cipolletti-Libertad 0-2 y 2-2, "
               "Gimnasia y Esgrima (CdU)-Central Norte 0-0 y 3-1, Gimnasia y "
               "Tiro (S)-Rivadavia (L) 0-1 y 2-0-- y difiere solo en esta. Una "
               "fuente derivada coincidiria en las cuatro."),
    Marcador(
        pagina="Torneo Argentino A 2011-12", jornada="Reválida - Tercera ronda",
        local="Central Norte (S)", visita="Libertad (S)", dice=(2, 1), debe=(2, 0),
        porque="6 de mayo de 2012. Con este 2-1 la serie termina 2-2, y entonces la "
               "regla de desempate que la PROPIA PAGINA escribe manda pasar al que "
               "fue 1o de la ronda anterior, que en su propia tabla es Libertad con "
               "13 puntos contra los 9 de Central Norte. Pasa Central Norte: la "
               "pagina lo pone en negrita y lo hace jugar la Tercera Fase. Con el "
               "2-0 de RSSSF la serie da 3-1 y no hay desempate que aplicar. Ver el "
               "comentario de arriba.\n"
               "NO COPIA A WIKIPEDIA: la otra llave de esta Tercera ronda, "
               "Rivadavia (L)-Juventud Unida, RSSSF la da identica a la pagina ya "
               "espejada --1-0 la ida y 3-0 la vuelta--, igual que las tres llaves "
               "de la Segunda ronda que no estan en discusion. Coincide en cuatro "
               "de las seis y difiere en esta y su vuelta."),
    Marcador(
        pagina="Torneo Argentino A 2011-12", jornada="Reválida - Tercera ronda",
        local="Libertad (S)", visita="Central Norte (S)", dice=(1, 0), debe=(1, 1),
        porque="13 de mayo de 2012. La otra pata de la misma serie, y las dos se "
               "mueven juntas: es la SUMA la que tiene que cerrar con quien paso, "
               "asi que el argumento de arriba las arbitra a las dos o a ninguna. "
               "RSSSF escribe `Libertad (Sunchales) 1-1 Central Norte (Salta)`.\n"
               "NO COPIA A WIKIPEDIA: en la otra llave de esta misma Tercera "
               "ronda, Rivadavia (L)-Juventud Unida, RSSSF reproduce la pagina ya "
               "espejada dato por dato (1-0 y 3-0), y lo mismo en tres de las "
               "cuatro llaves de la Segunda ronda. Difiere solo en esta serie."),

    # --- La vuelta de la final de la Revalida del Apertura 2004-05 ---
    #
    # La pagina dice 2-0 y lo dice DOS VECES --la grilla y el `{{Copa}}` de mas
    # abajo, que anota `RD2-score1-2= 0` y `RD2-score2-2= 2`--, pero las dos son la
    # misma fuente y no se controlan entre ellas. La fuente citada del repo, el
    # blog de Jose Carluccio, publica otra cosa y la publica con NOMBRE Y APELLIDO:
    #
    #   "28/12/2004 en Lujan de Cuyo: Lujan de Cuyo 4 (Emiliano Romay 2, Alfredo
    #    Molina y Santiago Sandoval), Atletico Candelaria 1 (Richard Nunez)"
    #
    # CINCO GOLEADORES NOMBRADOS. Es exactamente la vara que este archivo se puso
    # para creerle a una cronica, y un 2-0 no tiene donde meter cinco goles.
    #
    # Y NO COPIA A WIKIPEDIA, medido sobre esta misma pagina: de esa temporada el
    # blog fecha 55 partidos, y el contrato de `citadas` es que el MARCADOR
    # verifica el emparejamiento, o sea que en los 55 coincide con la pagina al
    # gol. Coincide en 55 y difiere en este. Una fuente derivada coincidiria en 56.
    # La ida lo muestra en chico: "22/12/2004 en Posadas: Atletico Candelaria de
    # Misiones 1 (Manuel Sanchez Ocana), Lujan de Cuyo de Mendoza 0" es, dato por
    # dato, la fila que ya teniamos.
    #
    # EL DIA VA APARTE, en `citadas`: 28/12/2004. El `{{Copa}}` de la pagina dice
    # `RD2-date= 22/12 y 26/12`, o sea el 26, pero es el mismo cuadro cuyo marcador
    # queda refutado aca; su dia no pesa mas que el de la fuente que sabe quien
    # hizo los goles.
    Marcador(
        pagina="Torneo Argentino A 2004-05", jornada="Zona Reválida - Final",
        local="Luján de Cuyo", visita="Atlético Candelaria", dice=(2, 0), debe=(4, 1),
        porque="28 de diciembre de 2004, en Lujan de Cuyo. La fuente citada del repo "
               "lo publica con los CINCO GOLEADORES: `28/12/2004 en Lujan de Cuyo: "
               "Lujan de Cuyo 4 (Emiliano Romay 2, Alfredo Molina y Santiago "
               "Sandoval), Atletico Candelaria 1 (Richard Nunez)`. Un 2-0 no tiene "
               "donde meter cinco goles.\n"
               "LA PAGINA LO DICE DOS VECES Y ES UNA SOLA FUENTE: la grilla y el "
               "`{{Copa}}` de la misma seccion, que anota la vuelta como Candelaria "
               "0 - Lujan 2. Que dos partes de un articulo coincidan no las "
               "convierte en dos testigos.\n"
               "NO COPIA A WIKIPEDIA, y se puede medir sobre esta misma pagina: el "
               "blog fecha 55 partidos de esta temporada, y el contrato de "
               "`citadas` es que el marcador VERIFICA el emparejamiento -- o sea "
               "que en esos 55 coincide con la pagina al gol. Coincide en 55 y "
               "difiere en este. La ida lo muestra en chico: `22/12/2004 en "
               "Posadas: Atletico Candelaria de Misiones 1 (Manuel Sanchez Ocana), "
               "Lujan de Cuyo de Mendoza 0` es dato por dato la fila que ya "
               "teniamos.\n"
               "http://josecarluccio.blogspot.com/2013/09/argentina-consejo-federal-afa-torneo_422.html"),
    # --- El ultimo marcador en disputa del dataset, y lo arbitro la propia
    # --- pagina contra si misma, doce anios despues ---
    #
    # EL ARBITRO DE SIEMPRE NO ARBITRA ACA, y conviene decirlo antes que nada
    # porque parece que si. La tabla de hoy cierra con el 1-1 en los 22 clubes,
    # al gol. Pero RSSSF tambien cierra consigo misma con el 0-0: su tabla da
    # `Platense 42 11 20 11 30-33` y `Estudiantes (Buenos Aires) 42 21 10 11
    # 53-42`, que es exactamente su grilla. LAS DOS FUENTES SON COHERENTES, asi
    # que la aritmetica no elige. El G-E-P tampoco: el partido es empate en las
    # dos versiones -- 11-20-11 y 21-10-11 en las dos tablas --, y lo unico que
    # se mueve son dos goles.
    #
    # LO QUE DECIDE ES EL DELTA DE LA PAGINA DE 2010. El articulo se editaba EN
    # VIVO, fecha por fecha. Dos revisiones a veintiseis horas de distancia:
    #
    #   30/08 03:30 UTC   Platense Pts 4, PJ 5, G0 E4 P1, 2-4
    #                     Estudiantes Pts 13, PJ 5, G4 E1 P0, 7-2
    #   31/08 05:29 UTC   Platense Pts 5, PJ 6, G0 E5 P1, 2-4
    #                     Estudiantes Pts 14, PJ 6, G4 E2 P0, 7-2
    #
    # Entre las dos, los dos clubes suman un partido, un empate y un punto -- y
    # LOS GOLES NO SE MUEVEN. Eso es un 0-0 anotado por el que estaba mirando, la
    # misma noche. No hay que inferir nada de una suma acumulada: el delta es cero
    # y el partido es el unico que entro.
    #
    # DE PASO FECHA EL PARTIDO EL 30, no el 31. A las 00:30 del 30 (hora
    # argentina) la tabla todavia no lo tenia y a las 02:29 del 31 ya si, asi que
    # se jugo el lunes 30 de agosto. Ese es el dia que da ESPN; RSSSF lo pone bajo
    # `[Aug 31]` y de ahi sale la fecha que escribimos. El desacuerdo de dia queda
    # AVISADO y sin resolver a proposito: corregir un dia pediria un noveno tipo
    # de correccion, y no se agrega uno por una fila.
    #
    # El gol de mas entro en la pagina entre el 4 y el 16 de septiembre de 2010
    # --la revision 40295378 ya lo tiene-- y se quedo. La tabla final de hoy lo
    # arrastra, que es POR QUE la pagina cierra consigo misma: las dos mitades
    # derivaron juntas. Al corregir la grilla la tabla deja de cerrar, y eso queda
    # declarado abajo en dos `Revisado`.
    #
    # AFUERA COINCIDEN TRES, y ninguno puede venir de la Wikipedia de hoy: la
    # grilla de RSSSF (`Round 6 [Aug 31] Platense 0-0 Estudiantes`) con su tabla
    # final, ESPN --`Platense 0 - Estudiantes de Buenos Aires 0`, 30/08/2010-- y
    # la tabla de la Wikipedia EN INGLES, que publica `42 11 20 11 30 33` y
    # `42 21 10 11 53 42`, los numeros de RSSSF y no los de la pagina en
    # castellano.
    Marcador(
        pagina="Campeonato de Primera B 2010-11 (Argentina)", jornada="Fecha 6",
        local="Platense", visita="Estudiantes (BA)", dice=(1, 1), debe=(0, 0),
        porque="Lo arbitra la TABLA DE POSICIONES de la propia pagina, pero no la "
               "de hoy: la de 2010, cuando el articulo se editaba en vivo. Entre la "
               "revision del 30/08 03:30 UTC y la del 31/08 05:29 UTC --veintiseis "
               "horas-- Platense pasa de `Pts 4, PJ 5, G0 E4 P1, 2-4` a `Pts 5, "
               "PJ 6, G0 E5 P1, 2-4` y Estudiantes de `Pts 13, PJ 5, G4 E1 P0, 7-2` "
               "a `Pts 14, PJ 6, G4 E2 P0, 7-2`. Los dos suman un partido, un "
               "empate y un punto Y LOS GOLES NO SE MUEVEN. Eso es un 0-0, anotado "
               "la misma noche por el que estaba mirando.\n"
               "LA TABLA DE HOY NO ARBITRA, y por eso hubo que ir al historial: "
               "cierra con el 1-1 en los 22 clubes, pero RSSSF tambien cierra "
               "consigo misma con el 0-0. Las dos fuentes son coherentes; el gol de "
               "mas entro en la pagina entre el 4 y el 16 de septiembre de 2010 y se "
               "llevo a las dos mitades. Al corregir la grilla la tabla deja de "
               "cerrar: va declarado en dos `Revisado`.\n"
               "AFUERA COINCIDEN TRES y ninguno copia a la Wikipedia de hoy: la "
               "grilla de RSSSF (`Round 6 [Aug 31] Platense 0-0 Estudiantes`) con su "
               "tabla final (`Platense 30-33`, `Estudiantes 53-42`), ESPN con el "
               "mismo 0-0, y la tabla de la Wikipedia EN INGLES, que publica los "
               "numeros de RSSSF y no los de la pagina en castellano.\n"
               "OJO CON EL DIA: el mismo delta lo fecha el 30 y no el 31. A las "
               "00:30 del 30 la tabla no lo tenia y a las 02:29 del 31 ya si. ESPN "
               "da el 30; RSSSF, de donde sale nuestra fecha, lo pone bajo "
               "`[Aug 31]`. Queda como desacuerdo de dia, avisado."),
    Marcador(
        pagina="Campeonato de Primera Nacional 2021", jornada="Fecha 17",
        local="Gimnasia y Esgrima (J)", visita="Defensores de Belgrano",
        dice=(3, 1), debe=(1, 3),
        porque="El G-E-P de la tabla pedia un resultado invertido entre estos dos "
               "y el otro cruce era imposible por aritmetica: quedaba este solo. "
               "La cronica da los goles con su minuto -- Facundo Suarez a los 60 "
               "para Gimnasia (J); Ivan Sandoval a los 43, Juan Manuel Olivares a "
               "los 72 de penal y un tercero para Defensores --, que es "
               "exactamente lo que no se puede copiar de una tabla.\n"
               "NO COPIA A WIKIPEDIA: el archivo de ESPN reproduce el OTRO cruce "
               "entre los mismos clubes en la misma temporada, la fecha 34 del "
               "15/11/2021 en el Juan Pasquale, igual que la pagina, y difiere "
               "solo en este."),
    Marcador(
        pagina="Campeonato de Primera B 2022 (Argentina)", jornada="Fecha 12",
        local="Cañuelas", visita="Ituzaingó", dice=(2, 2), debe=(3, 2),
        porque="Es el unico par de la pagina con el G-E-P corrido y tenia un solo "
               "cruce posible. La cronica da los tres goles de Cañuelas con su "
               "minuto: Lautaro Suarez Costa a los 40 y a los 80, y Gabriel "
               "Mendoza a los 87. Un 2-2 no tiene donde poner el tercero.\n"
               "NO COPIA A WIKIPEDIA, por partida doble: ESPN y RSSSF coinciden "
               "con la pagina en el otro Cañuelas-Ituzaingó de 2022 -- el 1-1 del "
               "Apertura, fecha 12, del 30/04/2022 -- y difieren solo en este."),
    Marcador(
        pagina="Torneo Argentino A 2010-11", jornada="Fecha 7",
        local="Gimnasia y Esgrima (CdU)", visita="Central Norte (S)",
        dice=(2, 0), debe=(1, 0),
        porque="La tabla de la Primera fase le pone a Gimnasia un gol a favor de "
               "mas y a Central Norte uno en contra de mas, espejados, asi que el "
               "error esta en un cruce entre ellos. De los cuatro, dos pedirian "
               "goles negativos y el tercero cambiaria un empate en victoria, que "
               "el G-E-P de la propia tabla prohibe. Queda este.\n"
               "Lo confirman dos fuentes contemporaneas de autores distintos. El "
               "blog de Central Norte de Salta, el 6/10/2010: \"El conjunto "
               "dirigido por Gustavo Coleoni perdio 1 a 0 en su visita a Gimnasia "
               "y Esgrima de Concepcion del Uruguay\", con el gol de Conrado Besel "
               "a los 25 del primer tiempo y las dos formaciones completas "
               "(central-norte-salta.blogspot.com/2010/10/un-paso-para-atras.html). "
               "Y el blog misionero metagoles, del 4/10/2010 -- la noche del "
               "partido --, que publica los cuatro resultados de la Zona 3: "
               "\"Gimnasia CdU 1-0 Central Norte\". Los otros tres de esa lista "
               "coinciden exactamente con Wikipedia, asi que no la esta copiando: "
               "difiere solo en este.\n"
               "El renglon del 2-0 es de los pocos de la Fecha 7 que la pagina "
               "carga SIN referencia: sus tres refs de esa fecha son todas de la "
               "Zona 1."),
    Marcador(
        pagina="Torneo Argentino A 2010-11", jornada="Fecha 21",
        local="Unión (MdP)", visita="Huracán (TA)", dice=(2, 0), debe=(0, 1),
        porque="Este par es el unico de la pagina donde el G-E-P de la tabla NO "
               "coincide con la grilla, y no coincide en espejo: la tabla le da a "
               "Huracan una victoria que la grilla le da a Union. O sea que no es "
               "un digito sino un partido entero al reves, y tiene que ser uno de "
               "los dos cruces que el arreglo da vuelta -- la Fecha 7 o esta --.\n"
               "Es esta. RSSSF publica la Zona 1 fecha por fecha y da, textual, "
               "\"Union 2-1 Huracan\" en la ronda 7 del 3 de octubre y \"Union 0-1 "
               "Huracan\" en la ronda 21 del 6 de febrero "
               "(rsssf.org/tablesa/arg2011.html). Futbol24 coincide: Union Mar del "
               "Plata 0-1 Huracan Tres Arroyos, Argentino A Zona 1. Y La Capital "
               "de Mar del Plata cubrio la derrota local en su edicion del "
               "7/2/2011.\n"
               "NINGUNA DE LAS DOS COPIA A WIKIPEDIA, y eso se puede auditar: "
               "RSSSF da el cruce de la ronda 7 entre estos mismos clubes como "
               "2-1, igual que la pagina, y difiere solo en este. Una fuente "
               "derivada coincidiria en los dos. Cronica con goleadores no hay al "
               "alcance: la de La Capital del 7/2/2011 solo existe en el Web "
               "Archive, que las herramientas no alcanzan." + chr(10) +
               "Que la Fecha 7 quede confirmada COMO ESTA es la otra mitad del "
               "resultado: con el par cerrado por un lado, el otro cruce deja de "
               "ser candidato. Los dos testigos, el interno y el externo, "
               "coincidieron en cual de los dos era."),
    Marcador(
        pagina="Torneo Argentino A 2010-11", jornada="Fecha 28",
        local="Villa Mitre", visita="Ramón Santamarina", dice=(0, 2), debe=(0, 1),
        porque="La tabla de la Primera fase le pone a Santamarina un gol a favor "
               "de mas y a Villa Mitre uno en contra de mas, y los dos se desvian "
               "en espejo, asi que el error esta en un partido entre ellos. De los "
               "cuatro cruces, tres quedan descartados sin salir de la pagina: uno "
               "pediria goles negativos y los otros dos cambiarian el resultado, "
               "cosa que el G-E-P de la propia tabla prohibe -- coincide exacto "
               "con la grilla para los dos clubes. Queda este solo.\n"
               "Y lo confirman dos fuentes independientes. La Nueva de Bahia "
               "Blanca, al dia siguiente del partido: \"La derrota 1-0 ante Ramon "
               "Santamarina no hizo mas que profundizar una herida que no "
               "cicatriza\", con el gol de Brittes a los 2 minutos "
               "(lanueva.com/nota/2011-3-21-9-0-0-santamarina-profundizo-la-herida"
               "-de-villa-mitre). Y el historial de BeSoccer entre los dos clubes, "
               "que da \"Villa Mitre 0-1 Dep. Santamarina\" y ademas reproduce los "
               "otros tres cruces igual que la grilla -- 0-0, 1-1 y 1-1 --, o sea "
               "que no esta copiando de Wikipedia, que en este difiere.\n"
               "De yapa, La Nueva confirma tambien la Fecha 21 (Santamarina 1-1 "
               "Villa Mitre, Gucci a los 26 y Carrillo a los 37), que es justo uno "
               "de los candidatos que el G-E-P habia refutado. El testigo interno "
               "y la prensa dijeron lo mismo."),
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
    # ------------------------------------------------------------------
    # Primera C 2024. Cuatro marcadores, y la pagina entro al cruce recien
    # ahora: sus tablas viven bajo `== Torneo Apertura ==` y `== Torneo
    # Clausura ==`, no bajo "Tabla de posiciones", asi que el arbitro no las
    # encontraba. Con las dos visibles aparecieron seis desviados en el Apertura
    # y tres en el Clausura.
    #
    # Lo que los volvio unicos NO fue la aritmetica de goles sino que esta tabla
    # publica tambien G-E-P. Con PJ/GF/GC solos, cuatro de los seis quedaban
    # degenerados -- dos clubes con (0,-1) y dos con (-1,0), cuatro maneras de
    # aparearlos --. Mirando ademas ganados/empatados/perdidos, el sistema tiene
    # una sola solucion: se verifico por enumeracion exhaustiva de las seis
    # biyecciones posibles y por busqueda con poda sobre los quince cruces.
    # ------------------------------------------------------------------
    Marcador(
        pagina="Campeonato de Primera C 2024 (Argentina)",
        jornada="Fecha 9", local="Leandro N. Alem", visita="Atlas",
        dice=(1, 2), debe=(2, 1),
        porque=(
            "Solo Ascenso publica la sintesis con los tres goles y sus minutos: "
            "Fernando Maldonado a los 23' de penal y a los 40' para Alem, y "
            "Anriquez a los 90+1' para Atlas, con el arbitro Nestor Barrios y las "
            "dos formaciones. Lo corrobora Cronica del 29/03/2024 con una nota "
            "sobre la 'ley del ex' de Maldonado, que venia de Atlas -- y Cronica "
            "NO esta citada por la pagina de Wikipedia, asi que no puede ser el "
            "ancestro del dato. El feed de ESPN de la temporada tambien da 2-1. "
            "La tabla ademas dice que Alem gano ese partido y Atlas lo perdio, "
            "que es lo que la grilla tiene al reves."),
    ),
    Marcador(
        pagina="Campeonato de Primera C 2024 (Argentina)",
        jornada="Fecha 19", local="Juventud Unida", visita="Muñiz",
        dice=(1, 1), debe=(1, 2),
        porque=(
            "Solo Ascenso publica la sintesis con los tres goles: Diego Guex a los "
            "48' para Muniz, Nicolas Slimmens a los 60' de penal para Juventud "
            "Unida y Ezequiel Ponce a los 90+16' de penal para Muniz. La tabla "
            "coincide: le da a Muniz un ganado mas y a Juventud Unida un empate "
            "menos. "
            "CON UN TESTIGO EN CONTRA, y conviene que quede escrito: ESPN publica "
            "1-1 para este partido. Se toma igual el 1-2 porque una sintesis con "
            "tres goleadores, sus minutos y el detalle de dos penales no se "
            "compara con un marcador suelto en un sitio de estadisticas, que es "
            "justamente lo que este proyecto no acepta como testigo. Es el unico "
            "de los tres del Apertura que tiene una fuente discrepando."),
    ),
    Marcador(
        pagina="Campeonato de Primera C 2024 (Argentina)",
        jornada="Fecha 20", local="Yupanqui", visita="Defensores de Cambaceres",
        dice=(0, 3), debe=(1, 3),
        porque=(
            "Solo Ascenso publica la sintesis con los cuatro goles: Tomas Bravo a "
            "los 23' y a los 70' y Fernando Pasquale a los 55' para Cambaceres, y "
            "William Gimenez a los 52' para Yupanqui. ESPN corrobora el 1-3. El "
            "resultado no cambia -- gana Cambaceres igual --, lo que falta es el "
            "gol de Yupanqui, y por eso la tabla le da un gol a favor mas del que "
            "suma la grilla."),
    ),
    Marcador(
        pagina="Campeonato de Primera C 2024 (Argentina)",
        jornada="Fecha 11", local="Yupanqui", visita="Lugano",
        dice=(0, 0), debe=(1, 1),
        porque=(
            "Del Torneo Clausura, no del Apertura: Lugano y Yupanqui se cruzan una "
            "sola vez en cada uno. Solo Ascenso publica la sintesis con los dos "
            "goles -- German Videla a los 28' para Yupanqui y Alan Seguel a los "
            "81' para Lugano --, el arbitro Sebastian Habib y las dos "
            "formaciones. El1 Digital de La Matanza lo confirma al dia siguiente "
            "identificando la fecha 11 del Clausura y el estadio Ciudad Evita. "
            "Los dos dominios estan citados por la pagina para otros asuntos, asi "
            "que valen menos; pero los dos CONTRADICEN la grilla, y una fuente "
            "que contradice no puede ser el ancestro del dato. "
            "Y hay una huella aritmetica que no se puede copiar: El1 Digital dice "
            "que despues del partido Yupanqui quedo con 9 puntos y Lugano con 11, "
            "y sumando la grilla hasta esa fecha dan exactamente 9 y 11."),
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


@dataclass(frozen=True)
class Dividido:
    """Un partido en el que cada club quedo con un resultado DISTINTO.

    Pasa cuando el tribunal falla en contra de los dos, o de uno solo dejando al
    otro como estaba. Una fila del CSV tiene un `home_score` y un `away_score`:
    cualquier par de numeros que se ponga ahi afirma un solo resultado, y aca hay
    dos. No es una limitacion del parser sino del esquema, asi que estas filas NO
    entran, y el build las nombra una por una.

    La columna `status` no los resuelve y por eso no tienen un valor propio: un
    `status="dividido"` con el marcador puesto seguiria publicando el numero
    equivocado, y con el marcador vacio rompe a cualquiera que haga
    `int(fila["home_score"])`. Sacarlos y decirlo es lo unico honesto.

    Son cinco en las 131 paginas, y los cinco estaban entrando MAL salvo uno:

      * El Clausura 2005 publicaba `Almagro 0-2 Boca Juniors`, o sea a Boca
        GANANDO un partido que Boca tambien perdio. La celda trae los dos
        marcadores (`0 - 2<br>3 - 2`) y el parser se quedaba con el primero.
      * La Primera C 2015 publicaba el 2-2 de Laferrere-Dock Sud, que es cierto
        para Dock Sud y falso para Laferrere.
      * El B Nacional 2016-17 y la Primera B 2017-18 publicaban 0-0 en partidos
        donde el fallo le dio el punto a uno solo.
      * El Federal A 2018-19 ya no entraba, porque su celda dice `PP - PP` y no
        se puede leer como marcador.
    """
    pagina: str
    local: str
    visita: str
    dice: tuple[int, int] | None      # como sale publicado hoy; None si no entra
    porque: str
    # En que SECCION vivia el partido, cuando la pagina publica una tabla por
    # seccion. Vacio = la pagina tiene una sola tabla y no hace falta.
    #
    # Hace falta para el cruce de PJ: el partido se jugo y la tabla lo cuenta, asi
    # que hay que sumarlo al PJ contado -- pero SOLO en la tabla que corresponde.
    # El Torneo Federal A 2018-19 lo enseño: sumandolo en todas, la Revalida cerraba
    # y la Primera fase pasaba a contar uno de mas.
    llave: str = ""



DIVIDIDOS: tuple[Dividido, ...] = (
    Dividido(
        pagina="Campeonato de Primera B Nacional 2011-12",
        local="Chacarita Juniors", visita="Atlanta", dice=(0, 1),
        porque="El clasico del 11/03/2012 termino 1-1 en la cancha -- Lucas "
               "Mancinelli a los 53 para Atlanta y Sebastian Pena en el descuento "
               "para Chacarita, lo dan ESPN y la cronica de La Nacion \"Pena se "
               "vistio de heroe para Chacarita\" --, y despues el Tribunal de "
               "Disciplina fallo por los incidentes de la parcialidad local.\n"
               "Y fallo ASIMETRICO, que es lo que lo trae a esta familia: a "
               "Chacarita le dio el partido por perdido y ademas le quito un punto; "
               "Atlanta conservo el punto del empate. La aritmetica lo confirma sin "
               "ambiguedad en la tabla final, que es la misma en Wikipedia y en "
               "RSSSF: Atlanta 6-16-16 y 34 puntos, que exige EMPATE aca (con la "
               "victoria serian 36), y Chacarita 6-15-17 y 32, que es una derrota "
               "mas la quita. El mismo partido con dos resultados segun de que lado "
               "se lo mire.\n"
               "La grilla lo publica como 0-1, o sea afirmando que Atlanta GANO un "
               "partido que Atlanta empato. Sale, como los otros: una fila tiene un "
               "home_score y un away_score y aca hay dos resultados.\n"
               "RSSSF lo escribe explicito y vale citarlo: \"Chacarita Juniors 1-1 "
               "Atlanta [Later Atlanta won points 0-1]\"."),
    Dividido(
        pagina="Anexo:Torneo Clausura 2005 (Argentina)",
        local="Almagro", visita="Boca Juniors", dice=(0, 2),
        porque="la nota dice: Suspendido por invasion de campo [...] a los 64', con "
               "el resultado 3-2. El 21 de julio, el Tribunal de Disciplina le dio "
               "por perdido el partido a ambos, con un marcador de 0-2 para Almagro, "
               "y de 2-3 para Boca Juniors. O sea que los dos perdieron, y el CSV "
               "publicaba a Boca ganando 2-0",
    ),
    Dividido(
        pagina="Campeonato de Primera C 2015 (Argentina)",
        local="Deportivo Laferrere", visita="Dock Sud", dice=(2, 2),
        porque="la nota dice: El Tribunal de Disciplina le dio el partido perdido a "
               "Deportivo Laferrere por 1 a 0 y mantuvo el resultado para Dock Sud. "
               "El empate publicado es cierto para Dock Sud y falso para Laferrere",
    ),
    Dividido(
        pagina="Campeonato de Primera B Nacional 2016-17",
        local="Atlético Paraná", visita="All Boys", dice=(0, 0),
        porque="la nota dice: lo dio por finalizado, otorgandole un punto a All Boys "
               "y ninguno a Atletico Parana. Un empate le da un punto a cada uno, "
               "asi que el 0-0 publicado no es lo que computo el torneo",
    ),
    Dividido(
        pagina="Campeonato de Primera B 2017-18 (Argentina)",
        local="Deportivo Español", visita="Sacachispas", dice=(0, 0),
        porque="la nota dice: Se dio por finalizado, dandolo por perdido a Deportivo "
               "Español y empatado a Sacachispas. Uno pierde y el otro empata el "
               "mismo partido",
    ),
    Dividido(
        pagina="Torneo Argentino A 2005-06",
        local="La Florida", visita="Sportivo Patria", dice=(2, 2),
        # LA SECCION, y hace falta declararla aunque el tipo la deje opcional. Sin
        # ella `clubes_divididos` la lee como "la pagina tiene una sola tabla" y le
        # aplica la consecuencia a las DOS: al Apertura y al Clausura. El anulado es
        # el del Clausura --lo dicen la nota de la pagina y RSSSF-- y en el Apertura
        # estos mismos dos clubes juegan OTRO partido, que esta escrito y cierra.
        # Sin acotarlo, el chequeo de PJ esperaba en el Apertura un hueco que no
        # existe y denunciaba a los dos clubes.
        llave="Torneo Clausura",
        porque="la nota, que cuelga de la tabla y no de la fila, dice: El partido "
               "se interrumpio en el minuto 90 cuando empataban 2 a 2. Luego se "
               "resolvio darles por perdido el encuentro a ambos equipos por 1 a 0. "
               "Los dos perdieron, y una fila tiene que tener un ganador o un "
               "empate. Salia en sin-fecha/ publicando el 2-2 de la cancha, que no "
               "es el resultado de ninguno de los dos.\n"
               "SON TRES TESTIGOS Y NO UNO, y conviene anotarlo porque esta "
               "familia SACA una fila del dataset. La pagina lo cuenta DOS VECES, "
               "en dos lugares y con palabras distintas: la nota de arriba, que "
               "cuelga de la grilla, y otra bajo la tabla de posiciones -- \"El "
               "partido La Florida-Sportivo Patria correspondiente a la fecha 10 "
               "termino 2-2, pero fue anulado; se considero como 0-1 para "
               "ambos\" --. Dos redacciones que no se copian una a la otra.\n"
               "Y el tercero es de afuera: RSSSF, en la ronda 10 del Clausura, "
               "escribe `La Florida awd Sportivo Patria [abandoned at 2-2 in "
               "90', awarded 0-1 against both]`, y lo repite en su NB al pie de "
               "la zona. Coincide en el minuto, en el 2-2 y en el fallo contra "
               "los dos.",
    ),
    Dividido(
        pagina="Anexo:Torneo Apertura 1997 (Argentina)",
        local="San Lorenzo", visita="Huracán", dice=None,
        porque="La celda dice PP - PP. La nota cuenta que se suspendio a los 21' con "
               "el resultado 0-0 por incidentes entre las dos barras --murio un "
               "hincha, y la pagina cita a Clarin y a El Pais-- y que "
               "\"Posteriormente, el Tribunal de Disciplina le dio por perdido el "
               "partido a ambos, SIN CONSIGNAR GOLES\".\n"
               "POR QUE NO ES UN `suspendido` CON 0-0, que es lo primero que uno "
               "piensa: porque la TABLA de la propia pagina dice otra cosa, y lo dice "
               "con numeros. San Lorenzo figura g=9 e=5 p=5 con gf=42 gc=32, y "
               "nuestra grilla le suma 9-5-4 con los MISMOS 42 y 32. Huracan figura "
               "3-3-13 con 20 y 32, y la grilla le da 3-3-12 con los mismos 20 y 32. "
               "O sea que la tabla le cuenta a cada uno una DERROTA mas, y cero goles "
               "de las dos partes.\n"
               "Una derrota para los dos, sin goles, no se puede escribir en una fila: "
               "un 0-0 seria empate para ambos --que es justo lo que la tabla NO "
               "dice-- y cualquier otro par de numeros le da la victoria a alguien. "
               "Por eso va aca y no como suspendido. Es el mismo caso que "
               "Independiente (N) vs Deportivo Roca del Federal A 2018-19.\n"
               "El desvio de PJ que sale de esto se deriva de esta declaracion en vez "
               "de anotarse aparte.",
    ),
    Dividido(
        pagina="Torneo Federal A 2018-19", llave="Reválida",
        local="Independiente (N)", visita="Deportivo Roca", dice=None,
        porque="la celda dice PP - PP y la nota que el partido finalizo 4 a 1 y se le "
               "dio por perdido a ambos equipos. Es el unico de los cinco que no "
               "entraba ya, porque su celda no se puede leer como marcador",
    ),
    Dividido(
        pagina="Torneo Argentino A 2006-07", llave="Torneo Clausura",
        local="Central Norte (S)", visita="9 de Julio (R)", dice=None,
        porque="Ultima fecha del Clausura 2007, y el primero de los dos escandalos de "
               "arreglo que cuenta la propia pagina: Central Norte, ya descendido, le "
               "concedio a 9 de Julio un penal sobre el final para que clasificara a "
               "la fase final y de paso quedara afuera su clasico rival, Juventud "
               "Antoniana. En la cancha termino 1-0.\n"
               "Lo que lo trae a esta familia es como quedo anotado. En la tabla del "
               "Clausura los DOS clubes figuran con un partido mas que la grilla y "
               "con un PERDIDO de mas: Central Norte 3-5-6 contra 3-5-5, y 9 de Julio "
               "7-2-5 contra 7-2-4. O sea que hasta 9 de Julio, que gano en la "
               "cancha, esta anotado perdiendo. La columna de goles lo dice por su "
               "cuenta y sin que se lo pregunten: los dos con cero a favor y uno en "
               "contra, los dos perdiendo 0-1. Un partido, dos derrotas.\n"
               "RSSSF lo llama por su nombre y ademas lo usa para explicar una "
               "anomalia: \"2 more losses than wins and overall goal difference -1 "
               "due to award Central Norte-9 de Julio in round 14 Clausura\".\n"
               "Y RSSSF, que es de donde salen las filas de esta pagina, lo dice con "
               "todas las letras en la linea del partido: `Central Norte awd 9 de "
               "Julio [awarded 0-1 loss to both; originally 1-1; both teams to start "
               "with -6 points 2007/08]`. LOSS TO BOTH, textual.\n"
               "OJO con una discrepancia que conviene dejar escrita en vez de "
               "elegir: sobre el marcador JUGADO, Wikipedia dice 1-0 y RSSSF dice "
               "1-1. Como ninguno de los dos entra al dataset, la diferencia no "
               "cambia una fila, pero cambia el relato y no hay que taparla.\n"
               "No entra: la fila no existe y no tiene que existir.",
    ),
    Dividido(
        pagina="Torneo Argentino A 2006-07", llave="Torneo Clausura",
        local="San Martín (SM)", visita="Desamparados", dice=None,
        porque="Tres dias despues del otro y con el mismo desenlace. San Martin de "
               "Mendoza de local y Desamparados de visitante -- lo dice la pagina, "
               "que Desamparados \"actuaba como visitante\", y coincide con lo que "
               "exige el fixture: dentro de cada llave la Fecha 14 es el reverso de "
               "la Fecha 7, y en la Fecha 7 el local fue Desamparados --. Termino 0-0 "
               "en la cancha, que era lo que les servia a los dos.\n"
               "Juventud Unida denuncio, y despues aparecio un video de Leon Bustos, "
               "jugador de San Martin, admitiendo que le habian ofrecido treinta mil "
               "pesos al plantel para no ganar. El Consejo Federal les dio el partido "
               "por perdido 1 a 0 A LOS DOS y les quito nueve puntos a cada uno.\n"
               "La tabla del Clausura lo confirma sin que haya que creerle al relato: "
               "Desamparados 4-0-10 contra 4-0-9 en la grilla y San Martin 3-4-7 "
               "contra 3-4-6, los dos con un perdido de mas, y los dos con cero goles "
               "a favor y uno en contra.\n"
               "OJO con la tabla acumulada, que aca se contradice con la del "
               "Clausura: a San Martin le falta ese gol en contra -- da 24-26 donde "
               "la suma de sus dos mitades da 24-27 --. Es uno de los tres clubes de "
               "la pagina donde la acumulada no es la suma de sus mitades, asi que "
               "para este caso vale la del Clausura, que es la que aparea con el "
               "rival.\n"
               "Y RSSSF lo dice textual en la linea del partido: `San Martin awd Sp. "
               "Desamparados [awarded 0-1 loss to both; originally 0-0; both teams "
               "have 9 points deducted in the aggregate table]`. Confirma las tres "
               "cosas de una: el fallo contra los dos, el 0-0 de la cancha y los "
               "nueve puntos -- y no diez, como dice el relato de Wikipedia en otro "
               "parrafo de la misma pagina.\n"
               "No entra, por lo mismo que el otro.",
    ),
)


@dataclass(frozen=True)
class Faltante:
    """Un partido que la pagina TIENE y que no se puede leer.

    Es el unico tipo que AGREGA una fila en vez de arreglar una. Los otros cuatro
    se paran sobre un partido que ya existe; este existe en el wikitexto y muere
    en el parser, porque la celda del marcador esta rota. Y romperse asi no es lo
    mismo que faltar: el partido esta, con sus dos clubes, su cancha y su fecha,
    y lo unico que se perdio es un digito.

    La condicion para entrar es la de siempre y aca es mas exigente todavia,
    porque no se corrige un dato sino que se agrega una fila entera: el marcador
    tiene que salir de la pagina misma, con dos testigos que no dependan uno del
    otro. Si hay que ir a buscarlo afuera, no entra: queda el aviso abierto.

    Por eso `testigos` es un campo y no un parrafo. Hay mas de una forma de
    romperse -- a una fila se le perdio un digito, a otra se le perdio el salto
    de linea -- y cada una se apoya en testigos distintos, asi que pedirle al
    texto de `porque` una palabra fija solo servia mientras hubo un caso. Lo que
    NO cambia entre casos es que tienen que ser dos y tienen que ser
    independientes; eso es lo que se enumera y lo que el test cuenta.

    El resto de la fila -- fecha, hora, cancha -- se lee del wikitexto como
    cualquier otra, y no hay nada que decidir ahi.
    """
    pagina: str
    jornada: str
    local: str
    visita: str
    goles: tuple[int, int]
    fecha: str
    hora: str
    estadio: str
    porque: str
    # Los dos testigos, uno por entrada, cada uno nombrando DE DONDE sale y que
    # dice. Van sueltos y no dentro de `porque` para que se puedan contar: la
    # regla es que sean dos y que no dependan uno del otro.
    testigos: tuple[str, ...]
    # La tanda, cuando la hubo. Va aparte de `goles` porque una eliminatoria que
    # termina empatada NO tiene ganador en el marcador, y sin esto el partido
    # entraria como un empate cualquiera.
    penales: tuple[int, int] | None = None


FALTANTES: tuple[Faltante, ...] = (
    Faltante(
        pagina="Campeonato de Primera C 2016 (Argentina)", jornada="Fecha 1",
        local="Defensores de Cambaceres", visita="Sportivo Barracas",
        goles=(0, 0), fecha="2016-02-05", hora="17:00", estadio="12 de Octubre",
        porque="la celda del marcador dice `''' - 0`: se perdio el gol del local en "
               "alguna edicion. Que el partido es este no se elige: el torneo es "
               "todos contra todos de 20 clubes y 19 fechas, los 20 juegan 19 "
               "partidos salvo estos dos que juegan 18, la Fecha 1 tiene nueve "
               "partidos en vez de diez, y el unico par que no se cruza nunca es "
               "este. El 0-0 lo dicen dos testigos de la pagina: la tabla, donde "
               "el partido que les falta aporta GF+0 y GC+0 a los dos y la cuenta "
               "cierra leida desde cualquiera de los dos clubes; y el resaltado de "
               "la fila, que en esta pagina significa empate en sus 189 filas "
               "legibles sin una excepcion. El 0 del visitante ademas sobrevivio",
        testigos=(
            "LA TABLA DE POSICIONES: es el unico partido que les falta a los dos "
            "clubes, asi que la resta contra la grilla da sus goles exactos y se "
            "puede leer dos veces, una por club. Las dos dan 0-0, y la tabla "
            "ademas cierra sola (SGF = SGC = 457)",
            "EL RESALTADO DE LA PROPIA FILA: la pagina pinta la celda del "
            "resultado cuando el partido termino empatado, y el nombre del "
            "ganador cuando no. Se verifico en sus 189 filas legibles sin una "
            "sola excepcion -- 54 empates, los 54 pintados; 135 con ganador, "
            "ninguno --. La fila rota esta pintada",
        ),
    ),
    Faltante(
        pagina="Copa Argentina 2018-19", jornada="Treintaidosavos",
        local="Godoy Cruz", visita="Deportivo Armenio", goles=(2, 1),
        penales=None, fecha="2019-03-23", hora="", estadio="Juan Domingo Perón",
        porque="la fila esta entera y mal escrita: le sobra una llave y le falta el "
               "salto de linea, `|-bgcolor=#F5FAFF}|align=center| 23 de marzo ||...`. "
               "Con los cinco campos en el mismo renglon, la primera celda -- la "
               "fecha -- se pierde adentro de lo que `_partir` descarta como "
               "atributos de la fila, quedan cuatro y la fila no llega al minimo. Sus "
               "vecinas de la misma tabla son identicas y con el salto puesto. "
               "Aflojar el corte de filas para todo el corpus por una sola es peor el "
               "remedio: es el ultimo de los 240 partidos que faltaban en las copas y "
               "el unico que ningun arreglo de parser alcanza.\nEL MARCADOR DE ESTA "
               "ENTRADA ESTUVO MAL DOS ANIOS Y SE CORRIGIO. Decia 0-0 con penales "
               "6-5, tomando los numeros de la celda rota y dando vuelta el orden "
               "porque el cuadro y las rondas siguientes muestran a Godoy Cruz "
               "avanzando. El razonamiento del orden era bueno; la premisa no. "
               "Aquella version cerraba diciendo que el 0-0 de los noventa minutos no "
               "lo discutia nadie, y hoy lo discuten dos fuentes.\nFUE 2-1, Y SIN "
               "TANDA. El `Anexo:Treintaidosavos de final de la Copa Argentina "
               "2018-19` -- la propia Wikipedia, otra pagina -- lo publica como "
               "`Godoy Cruz 2:1 (0:1) Deportivo Armenio`, arbitro Hector Paletta, con "
               "los tres goles nombrados: Ramis a los 90 y a los 90+2 para Godoy "
               "Cruz, Ortiz a los 26 para Armenio. El entretiempo 0:1 encaja solo -- "
               "Ortiz convierte a los 26 y los dos de Ramis caen en el descuento --. "
               "Fue una remontada sobre la hora, no una tanda. RSSSF lo confirma por "
               "afuera: `CD Godoy Cruz Antonio Tomba 2-1 CD Armenio`, mismo "
               "estadio.\nLo unico que sobrevive de la celda rota es que Godoy Cruz "
               "paso, que era lo que aquella version habia deducido bien. El `(5) 0 - "
               "0 (6)` no describe este partido: es una fila cuyo markup roto "
               "arrastro tambien los numeros ",
        testigos=(
            "EL ANEXO DE LA PROPIA WIKIPEDIA, que es otra pagina y trae lo que la "
            "fila rota no puede: marcador, entretiempo, arbitro y los TRES "
            "goleadores con su minuto. Para un 0-0 no habria ninguno ",
            "RSSSF, desde afuera: `CD Godoy Cruz Antonio Tomba 2-1 CD Armenio`. Y "
            "no esta copiando a Wikipedia -- sobre los 27 cruces comparables de "
            "esta ronda coincide con la grilla en 20 --, asi que su 2-1 es un "
            "testigo y no un eco ",
            "EL CUADRO Y LAS RONDAS SIGUIENTES, que es lo que ya sostenia la "
            "version anterior: la grilla tiene a Godoy Cruz jugando dieciseisavos "
            "(14/07 vs Huracan) y octavos (18/09 vs River). Un club que perdio la "
            "serie no juega las dos rondas que siguen. Eso decidia el orden de la "
            "tanda; ahora decide que el ganador es el mismo aunque la tanda no "
            "haya existido ",
        ),
    ),
)


@dataclass(frozen=True)
class Homonimo:
    """Un club que la pagina escribe pelado y que en el padron son varios.

    `fad/equipos.py` avisa desde su docstring que los alias sin desambiguar
    ("Sarmiento", "Gimnasia y Esgrima") son ambiguos fuera de Primera, y que si
    alguna vez se parseaba una fuente de ascenso que los usara habia que
    resolverlos POR CONTEXTO. Esto es ese contexto: la pagina, y nada mas.

    Por que no puede ser un alias global: el Argentino A 2010-11 escribe
    "Juventud Unida" a secas y son 36 partidos que hoy caen en el club de
    Primera C que se llama igual. Poner el alias en el padron arreglaria esta
    pagina y romperia las otras seis, que son ese club de verdad. Y no falla
    ruidosamente: los partidos quedan prolijos, en el club equivocado.

    Cada uno se decide con la pagina misma, no por parecido. Sirven dos testigos:
    el WIKILINK cuando existe -- 2011-12 escribe
    `[[Club Atlético Juventud Unida Universitario|Juventud Unida (SL)]]` y ahi
    no hay nada que adivinar -- y la FECHA LIBRE cuando no: en una jornada cada
    club juega una sola vez, asi que si el rival de ese partido esta en la fecha
    N y de los cinco San Martin del padron cuatro ya juegan esa fecha, el quinto
    es ese. Sin uno de los dos, no entra.

    CUANDO NO USAR ESTO
    -------------------
    Cuando son uno o dos partidos sueltos, va `Correccion`, que identifica la
    fila entera y deja el resto del club en paz. Hay cinco casos asi resueltos
    ahi arriba -- "Gimnasia y Esgrima" y "Central Norte (SE)" del Argentino A
    2010-11, "9 de Julio" y "Alumni" del 2005-06, "San Martín" de la Primera
    Nacional 2022 -- y se probo pasarlos a homonimo: no aporta nada y encima
    pisa el testigo, porque el `dice` de la correccion es justamente el nombre
    equivocado. Esto es para cuando la pagina llama mal al club en TODOS sus
    partidos y una correccion por fila serian treinta y seis.
    """
    pagina: str
    dice: str
    debe: str
    porque: str


# Las paginas cuya LOCALIA ya se resolvio por afuera del testigo del solapamiento.
#
# El testigo compara a la fuente externa contra la pagina y bloquea la
# importacion cuando la mayoria no coincide. Es la guarda correcta y se queda,
# pero tiene un supuesto: que la pagina es el patron. Cuando la pagina resulta
# estar mal en esa region, el testigo mide contra un patron torcido y da un falso
# negativo -- rechaza a la fuente por tener razon.
#
# Esto no afloja la regla: la nombra. Entrar aca pide que la localia se haya
# establecido con evidencia que NO dependa de la fuente que se quiere importar;
# si no, el testigo se estaria validando a si mismo.
LOCALIA_RESUELTA: dict[str, str] = {
    "Torneo Argentino A 2011-12": (
        "Sus cuatro tablas de eliminacion tienen CAMBIADOS los rotulos de dos "
        "columnas -- lo que llaman `Local - Vuelta` es el local de la ida --, y por "
        "eso el testigo daba 6 de 31. Las 28 filas ya estan espejadas; ver "
        "`_LLAVES_2011_12`.\n"
        "LA EVIDENCIA NO DEPENDE DE RSSSF, que es lo que hace legitimo levantar el "
        "bloqueo: el blog de Jose Carluccio publica cada partido con su CIUDAD, y el "
        "Argentino A 2012-13 --misma forma de tabla, mismo lector-- da 30 de 30 sin "
        "una sola al reves, o sea que el lector no es el problema.\n"
        "LO QUE DESTRABA son los seis partidos que la pagina publica SOLO en el "
        "cuadro: las dos semifinales y la final. El blog los confirma uno por uno "
        "con la sede, y coincide con RSSSF en los seis: 03/06 en Cordoba, 05/06 en "
        "Tandil, 10/06 en Garupa, 11/06 en San Francisco, 17/06 en Garupa y 22/06 "
        "en San Francisco."),
}


HOMONIMOS: tuple[Homonimo, ...] = (
    Homonimo(
        pagina="Copa Argentina 2015-16", dice="Juventud Unida",
        debe="Juventud Unida (G)",
        porque="El de Gualeguaychu, y aca la pagina SE CONTRADICE A SI MISMA: enlaza "
               "al mismo club a DOS articulos distintos. La grilla y la primera "
               "ronda del cuadro dicen `[[Club Deportivo Juventud Unida]]`, que es "
               "el de Gualeguaychu; de la segunda ronda en adelante el cuadro dice "
               "`[[Club Social y Deportivo Juventud Unida]]`, que el padron resuelve "
               "a otro club. Las dos veces la pagina le pone la bandera de Entre "
               "Rios.\n"
               "LA GRILLA MANDA Y ES UNANIME: sus cuatro partidos son de "
               "`Juventud Unida (G)` y no hay ni uno del otro. Y el otro tiene "
               "coartada: en 2015 juega sus 38 partidos en la Primera C, sin pisar "
               "esta copa.\n"
               "Sin esto el cruce entre el cuadro y la grilla no se puede hacer: el "
               "chequeo avisa que el cuadro nombra un club que en la grilla no juega "
               "ni un partido -- y no lo juega porque ese club no estuvo aca."),
    Homonimo(
        # `dice` es el nombre YA CANONIZADO, no el crudo de la pagina: `homonimo()`
        # se llama despues de `equipos.canonizar`. El crudo aca es `Talleres` a
        # secas y el padron lo resuelve al de Cordoba, asi que lo que hay que
        # nombrar es ESE. Declararlo con el crudo no falla: no engancha nunca.
        pagina="Torneo Argentino A 2004-05", dice="Talleres (C)",
        debe="Talleres (P)",
        porque="El de Perico, Jujuy, y la pagina lo dice ella sola. Escribe "
               "`Talleres (P)` en TODAS partes -- las veinte filas de la Zona "
               "Norte, la tabla de posiciones, el cuadro de la Revalida -- salvo "
               "en UNA: la plantilla del cuadro del Zona Campeonato, donde pone "
               "`RD1-equipo05 = Talleres` pelado. Ahi el padron lo resuelve al de "
               "Cordoba, que es el otro Talleres.\n"
               "Y SU PROPIA LISTA DE PARTICIPANTES LO ENLAZA: "
               "`[[Club Atlético Talleres (Perico)|Club Atlético Talleres]] || "
               "[[Perico (Jujuy)|Perico]] || [[Jujuy]]`. No hace falta salir de la "
               "pagina.\n"
               "Afuera lo confirman los otros dos que ya se habian mirado por el "
               "mismo motivo: el Talleres de Cordoba jugaba la Primera Division esa "
               "temporada -- tiene sus 19 partidos en `Primera Division - Clausura "
               "2004` -- y la tabla de RSSSF nombra a este "
               "`Talleres (Perico) ... (Jujuy)`.\n"
               "Sin esto, el cuadro y la grilla no se pueden comparar: el chequeo "
               "avisa que `Talleres (C) vs Ben Hur` esta en el cuadro y no hay "
               "NINGUN partido entre esos dos en la grilla -- y no lo hay porque "
               "ese club no jugo este torneo."),
    Homonimo(
        pagina="Torneo Argentino A 2004-05", dice="Juventud Unida",
        debe="Juventud Unida Universitario",
        porque="El de San Luis. La pagina escribe \"Juventud Unida\" a secas en el "
               "cuadro y en las tablas, y el padron lo resuelve al club de Primera C "
               "que se llama igual.\n"
               "LA FOJA LO ZANJA SIN MARGEN, que es el testigo mas fuerte que hay "
               "aca. La fila de \"Juventud Unida\" en la tabla acumulada de la pagina "
               "dice PJ 20, 6 ganados, 7 empatados, 7 perdidos, 22 a favor y 24 en "
               "contra. RSSSF, que numera el torneo por su cuenta, publica para "
               "Juventud Unida Universitario (San Luis) exactamente 20 6 7 7 22-24. "
               "Los SEIS numeros, no dos ni tres.\n"
               "Y hay dos testigos mas en la propia pagina: su tabla de participantes "
               "enlaza [[Club Atletico Juventud Unida Universitario]] de San Luis y "
               "no menciona ningun otro Juventud Unida, y una de sus tablas de "
               "posiciones escribe el nombre entero, `eq=Juventud Unida "
               "Universitario`. El unico otro Juventud del torneo es el de "
               "Pergamino, que la pagina y RSSSF escriben siempre distinto.\n"
               "Se veia como un desacuerdo del cuadro contra la grilla -- \"Juventud "
               "Unida vs Aldosivi: el cuadro publica 1-0, 2-5 y la grilla no tiene "
               "NINGUN partido entre los dos\" -- y no lo era: la grilla SI los tiene, "
               "con esos marcadores, pero bajo el otro nombre."),
    Homonimo(
        pagina="Campeonato de Primera B 2015 (Argentina)", dice="Estudiantes (LP)",
        debe="Estudiantes (BA)",
        porque="El de Caseros. El cuadro de llaves escribe \"Estudiantes\" a secas "
               "y el padron lo resuelve al de La Plata, que es un club de Primera: "
               "en esta pagina el UNICO Estudiantes que juega es el (BA), en todos "
               "sus partidos.\n"
               "Y no es un nombre suelto que haya que interpretar: los partidos que "
               "el cuadro anuncia estan en la grilla con el marcador exacto -- Estudiantes (BA) 1-3 Almagro en las Semifinales, y el cuadro dice 1-3 --. "
               "O sea que el cuadro y la grilla hablan del mismo partido y lo unico "
               "que los separaba era a que club apuntaba el nombre.\n"
               "Es el caso que `fuera_del_cuadro` ya describia en su docstring y "
               "que nadie habia escrito: la Primera B 2014, 2015 y 2017-18 lo tienen "
               "igual."),
    Homonimo(
        pagina="Campeonato de Primera B 2017-18 (Argentina)", dice="Estudiantes (LP)",
        debe="Estudiantes (BA)",
        porque="El de Caseros. El cuadro de llaves escribe \"Estudiantes\" a secas "
               "y el padron lo resuelve al de La Plata, que es un club de Primera: "
               "en esta pagina el UNICO Estudiantes que juega es el (BA), en todos "
               "sus partidos.\n"
               "Y no es un nombre suelto que haya que interpretar: los partidos que "
               "el cuadro anuncia estan en la grilla con el marcador exacto -- Estudiantes (BA) 4-1 Talleres (RdE) en Cuartos y el 3-1 y el 2-1 con UAI Urquiza en Semifinales, todos con el numero que dice el cuadro --. "
               "O sea que el cuadro y la grilla hablan del mismo partido y lo unico "
               "que los separaba era a que club apuntaba el nombre.\n"
               "Es el caso que `fuera_del_cuadro` ya describia en su docstring y "
               "que nadie habia escrito: la Primera B 2014, 2015 y 2017-18 lo tienen "
               "igual."),
    Homonimo(
        pagina="Torneo Argentino A 2005-06", dice="Talleres (C)", debe="Talleres (P)",
        porque="El de Perico, Jujuy. \"Talleres (C)\" aparece UNA SOLA VEZ en toda "
               "la pagina y es adentro del cuadro de llaves, pegado a un "
               "\"Racing (C)\" que si es de Cordoba: el parentesis se contagio del "
               "vecino. Las otras 28 menciones de Talleres en la pagina dicen (P) o "
               "Perico.\n"
               "La tabla de participantes de la propia pagina lo desata sola: "
               "[[Club Atlético Talleres (Perico)]], Perico, Jujuy, Liga Jujeña de "
               "Futbol. Y RSSSF lo confirma desde afuera -- en sus tres tablas el "
               "unico Talleres del torneo es \"Talleres (Perico) ... (Jujuy)\", y no "
               "hay ningun Talleres de Cordoba --.\n"
               "Sin esto, el cuadro nombraba un club que en la grilla no juega ni un "
               "partido, que es la firma de una mala atribucion. Aca no lo era: era "
               "un nombre mal escrito en un solo lugar."),
    Homonimo(
        pagina="Torneo Argentino A 2010-11", dice="Juventud Unida",
        debe="Juventud Unida Universitario",
        porque="es el de San Luis: la pagina lo lista en participantes como "
               "[[Club Atlético Juventud Unida Universitario]] y no hay otro "
               "Juventud Unida en el torneo. El del padron sin parentesis es el "
               "Club Deportivo y Social Juventud Unida, de Primera C, que se "
               "estaba quedando con estos 36 partidos sin que nada avisara",
    ),
    Homonimo(
        pagina="Torneo Argentino A 2005-06", dice="Juventud Unida",
        debe="Juventud Unida Universitario",
        porque="al reves que el de arriba: aca los partidos lo escriben entero y "
               "la que abrevia es la TABLA. Las dos tablas tienen 24 filas y el "
               "torneo 24 clubes, sobra este de un lado y falta Universitario del "
               "otro, y el unico Juventud Unida que la pagina enlaza es "
               "[[Club Atlético Juventud Unida Universitario]]",
    ),
)


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


def clubes_divididos(pagina: str, llave: str = "") -> dict[str, int]:
    """Cuantos partidos divididos jugo cada club en `pagina`.

    Existe para que el cruce de PJ pueda derivar una consecuencia en vez de que
    haya que anotarla a mano. Un `Dividido` dice que el partido SE JUGO y que el
    esquema no puede escribir su resultado; entonces la tabla de la pagina lo
    cuenta y nuestra grilla no, y los dos clubes aparecen desviados en uno.

    Eso no es un hallazgo: es la consecuencia aritmetica de una decision que ya
    esta escrita mas arriba, con su evidencia. Anotarla ademas como `Revisado`
    para cada club serian catorce notas repitiendo lo que `DIVIDIDOS` ya dice, y
    la segunda copia de un hecho es la que se desactualiza.
    """
    cuenta: dict[str, int] = {}
    for d in DIVIDIDOS:
        # Si el dividido declara seccion, solo cuenta para ESA tabla. Si no la
        # declara, la pagina tiene una sola tabla y vale para la comparacion
        # general, que es la que va con `llave` vacia.
        if d.pagina != pagina or (d.llave or llave) != llave:
            continue
        cuenta[d.local] = cuenta.get(d.local, 0) + 1
        cuenta[d.visita] = cuenta.get(d.visita, 0) + 1
    return cuenta


def pares_divididos(pagina: str) -> list[tuple[str, str, str]]:
    """Los (local, visita, llave) de `pagina` que quedan afuera por tener dos
    resultados.

    Existe para que el chequeo de zonas parejas pueda contarlos SIN importar este
    modulo: un partido dividido se jugo, y el club que lo jugo tiene un partido
    mas de los que tiene fila. Sin esto, los dos escandalos de arreglo del
    Argentino A 2006-07 -- declarados hace rato, con su evidencia -- dejaban dos
    zonas desparejas y nada decia por que.

    La `llave` VIAJA CON EL PAR y no se descarta. Es el alcance del dividido, y
    sin el, el del Torneo Federal A 2018-19 se cuenta en la Primera fase ademas
    de en la Revalida: sus dos clubes juegan en las dos, asi que buscarlos por
    nombre los encuentra dos veces. Arreglar un chequeo rompiendo otro es lo que
    pasa cuando el alcance se pierde en el camino.
    """
    return [(d.local, d.visita, d.llave) for d in DIVIDIDOS if d.pagina == pagina]


def divididos_de(pagina: str) -> list[str]:
    """Los partidos de `pagina` que quedan afuera por tener dos resultados.

    Va por su propio canal y no por los avisos de `aplicar`, que son los de una
    correccion que NO engancho -- esos son graves, y esto no es un problema sino
    una decision: el partido existe, se sabe todo de el salvo como escribir su
    resultado en una fila, y sacarlo diciendolo es mejor que publicar el numero de
    uno de los dos clubes como si fuera el de los dos.
    """
    return [f"{d.local} vs {d.visita} queda AFUERA del dataset: cada club termino "
            f"con un resultado distinto y una fila con un solo marcador no puede "
            f"decir eso. {d.porque}"
            for d in DIVIDIDOS if d.pagina == pagina]


def homonimo(pagina: str, club: str) -> str:
    """Como se llama de verdad `club` en `pagina`.

    Un homonimo es una afirmacion sobre la PAGINA, no sobre los partidos, asi
    que vale para los dos lados: los partidos lo aplican en `aplicar` y las
    tablas de posiciones por aca. Tienen que ser el mismo mapa o el arbitro se
    apaga solo -- si la tabla dice "Juventud Unida" y los partidos, ya
    corregidos, dicen "Juventud Unida Universitario", el cruce no encuentra al
    club en las dos partes y se saltea la fila sin avisar.
    """
    for h in HOMONIMOS:
        if h.pagina == pagina and h.dice == club:
            return h.debe
    return club


def homonimos_huerfanos(pagina: str, escritos: set[str]) -> list[str]:
    """Los homonimos de `pagina` cuyo nombre ya no aparece en ningun lado.

    `escritos` son todos los nombres que la pagina produjo antes de resolverlos:
    los de los partidos y los de las filas de la tabla. Van juntos a proposito.
    Cuando esto vivia adentro de `aplicar`, que solo ve los partidos, un homonimo
    que arreglaba unicamente la tabla se denunciaba a si mismo como vencido.

    Vale la pena tenerlo: este aviso fue el que descubrio que cinco de los seis
    homonimos que se habian escrito ya estaban resueltos como `Correccion`.
    """
    # EL MENSAJE NOMBRA LAS DOS CAUSAS, y la segunda es la que se cometio. Decir
    # solo "la pagina ya no escribe ese nombre" da por sentado que el homonimo
    # alguna vez engancho, y manda a mirar Wikipedia. Pero un homonimo RECIEN
    # escrito puede no haber enganchado nunca: `dice` es el nombre YA CANONIZADO
    # --`homonimo()` corre despues de `equipos.canonizar`-- y escribirlo con el
    # crudo de la pagina no falla, no hace nada. Paso con el `Talleres` del
    # Argentino A 2004-05, que el padron canoniza a `Talleres (C)`.
    return [f"el homonimo {h.dice!r} -> {h.debe!r} no engancha con nada. O la "
            f"pagina ya no escribe ese nombre --ni en los partidos, ni en la "
            f"tabla, ni en el cuadro-- y hay que sacarlo de fad/correcciones.py; "
            f"o `dice` esta escrito con el nombre CRUDO de la pagina en vez del "
            f"canonico, y entonces nunca engancho"
            for h in HOMONIMOS if h.pagina == pagina and h.dice not in escritos]


def arbitrados(pagina: str) -> set[tuple[str, str, str]]:
    """(jornada, local, visitante) de los partidos ya arbitrados de `pagina`.

    `fechas.completar` usa el marcador para VERIFICAR que las dos fuentes hablan
    del mismo partido, y se niega a completar cuando no coincide. Para estos el
    emparejamiento ya se confirmo por otro lado, asi que una diferencia que
    quede no tiene que frenar la fecha.
    """
    return {(m.jornada, m.local, m.visita) for m in MARCADORES if m.pagina == pagina}


@dataclass(frozen=True)
class Revisado:
    """Un desvio que se fue a verificar y resulto NO ser un error del dataset.

    Es el tipo que le faltaba a este modulo, y su ausencia se notaba en el unico
    lugar donde se nota de verdad: la lista de avisos no bajaba nunca. Los otros
    seis tipos arreglan algo; este no arregla nada, y esa es exactamente su
    funcion. Cuando la tabla de una pagina no cierra con su grilla, hay dos
    desenlaces posibles y hasta ahora solo uno se podia anotar:

      * la grilla esta mal -> entra un `Marcador` y el aviso desaparece porque el
        dato cambio;
      * la TABLA esta mal -> no hay nada que corregir, el aviso queda abierto, y
        vuelve a aparecer en cada corrida hasta el fin de los tiempos.

    El segundo desenlace es tan legitimo como el primero -- de seis casos que se
    contrastaron contra la prensa, en dos la equivocada era la tabla -- y era el
    que no tenia donde escribirse. Sin eso, verificar un aviso y no encontrarle
    error se parece demasiado a no haberlo mirado: el proximo que pase lo va a
    volver a investigar desde cero.

    LA VARA ES LA MISMA QUE PARA CORREGIR, y tiene que serlo: silenciar un aviso
    sin mirar es peor que dejarlo abierto. Asi que `porque` tiene que decir que
    se verifico y contra que, con la fuente nombrada. Un `Revisado` sin fuente
    externa solo vale cuando la prueba es INTERNA y cerrada -- el caso de los
    goles que coinciden exacto, donde ningun partido puede explicar el desvio y
    no hay a donde ir a buscar.

    Y no se acumula en silencio: `revisados_huerfanos` denuncia al que ya no
    engancha con ningun desvio, porque eso quiere decir que la pagina cambio y
    que la verificacion que sostiene esta entrada quedo vieja.
    """
    pagina: str
    club: str
    porque: str

    # LA FIRMA DEL DESVIO QUE SE VERIFICO. Es lo que le faltaba a este tipo y lo
    # que `Fechado` y `Dia` ya piden a su manera: la declaracion tiene que decir
    # de QUE estado habla, para dejar de enganchar cuando el estado cambia.
    #
    # Sin esto, un `Revisado` se identifica por (pagina, club) y nada mas: si la
    # pagina corrige su tabla, `revisados_huerfanos` avisa -- el club deja de
    # desviarse --, pero si le aparece un desvio DISTINTO al mismo club, la
    # entrada vieja lo tapa en silencio. Con temporadas cerradas no pasaba nunca
    # y por eso el hueco vivio tranquilo; con las cuatro tablas de 2026 --las
    # primeras sobre paginas todavia en juego-- pasa a ser posible.
    #
    # ES UNA DIFERENCIA Y NO UN NUMERO ABSOLUTO, y ahi esta todo el asunto. En
    # una pagina viva la fila entera cambia cada fecha --sube el PJ, suben los
    # goles-- asi que fijar la fila haria caducar la declaracion todas las
    # semanas. Lo que NO cambia mientras la errata siga ahi es cuanto y en que se
    # aparta la tabla de nuestra grilla: `GF-2` sigue siendo `GF-2` la fecha que
    # viene. Ver `firma_del_desvio`.
    desvio: str = ""

    # El rival, cuando lo que se verifico es una LLAVE y no una fila de tabla.
    #
    # Hace falta y se aprendio probando lo contrario: dejar que el chequeo del
    # cuadro mirara los `Revisado` por club calló cinco avisos que nadie habia
    # arbitrado -- llaves del Argentino A 2005-06 que compartian un club con el
    # `Revisado` del partido dividido del Clausura, que habla de otra cosa --. Un
    # desvio de tabla es una afirmacion sobre UN club; una llave lo es sobre DOS,
    # y reusar el alcance chico para el problema grande suprime de mas.
    contra: str = ""


# Los dos clubes del partido dado por perdido del Argentino A 2007-08
# comparten la explicacion porque comparten el partido: escribirla dos
# veces serian dos textos que se pueden desincronizar.
_AWD_2007 = (
    "El desvio es de UN gol y lo explica entero un solo partido, el Lujan "
    "de Cuyo vs Juventud Unida Universitario de la fecha 26 (16/03/2008), "
    "que se abandono y se fallo en escritorio.\n"
    "LAS DOS FUENTES DAN FALLOS DISTINTOS. RSSSF lo publica con la nota "
    "textual `(awarded 0-2, abandoned at 1-1 in 86')` y de ahi sale la "
    "fila del dataset, 0-2. La tabla de la pagina lo conto 0-1, que es la "
    "forma habitual de la perdida de puntos en Argentina.\n"
    "Y LA CONTRADICCION ES ADENTRO DE RSSSF, no entre las dos fuentes. La "
    "tabla final que la propia RSSSF publica debajo de esos mismos "
    "partidos da 28-57 para Lujan de Cuyo y 48 GF para Juventud Unida: los "
    "mismos numeros que Wikipedia, o sea 0-1 tambien. Asi que la unica "
    "linea del mundo que dice 0-2 es la del partido, y las dos tablas que "
    "existen dicen 0-1. Se supo recien cuando el cruce contra la foja de la "
    "fuente se automatizo, y lo primero que hizo fue redescubrir este caso "
    "solo.\n"
    "LA ARITMETICA LO FUERZA, y no deja lugar a otra lectura: si la "
    "diferencia fuera un partido mal leido moveria cuatro celdas. Mueve "
    "DOS, y son exactamente las dos que separan un 0-1 de un 0-2. Nuestro "
    "GF de Juventud Unida da 49 contra los 48 de la tabla, y nuestro GC "
    "de Lujan de Cuyo da 58 contra 57; las otras dos celdas del mismo "
    "partido -- el GF de Lujan y el GC de Juventud Unida, cero con "
    "cualquiera de los dos fallos -- coinciden exacto, igual que los 32 "
    "PJ de los dos.\n"
    "Aun asi no hay nada que corregir, y el dato nuevo no lo cambia: la "
    "fila dice lo que su fuente afirma con todas las letras, que es la "
    "nota `awarded 0-2`. Una tabla es una suma y una nota es una "
    "afirmacion; preferir la suma seria elegir el resultado que mas se "
    "repite, que no es lo mismo que el que esta dicho. Se anota el "
    "desacuerdo -- ahora con los tres numeros a la vista -- y no se "
    "inventa un tercer marcador. "
)

# Los diez clubes del Argentino A 2008-09 comparten explicacion porque comparten
# causa: no son diez desvios sino una tabla.
_TABLA_2008_09 = (
    "La tabla de la pagina en espanol dice mas goles que nuestra suma en DIEZ "
    "clubes de los veinticinco, y siempre para el mismo lado: a cinco les sobran "
    "goles a favor y a cinco en contra, ocho de cada lado. Que sumen igual no es "
    "casualidad -- es la firma de partidos contados con OTRO marcador, no de "
    "celdas mal tipeadas, que moverian un club solo.\n"
    "LOS PARTIDOS EN DISPUTA SE PUEDEN NOMBRAR, y son cinco. Los desvios se "
    "emparejan dentro de su zona: Santamarina +3 con Alvarado, Villa Mitre +2 "
    "con Rivadavia (L), Gimnasia (M) y Juventud Unida +1 cada uno con Central "
    "Cordoba (SdE) y Deportivo Maipu. El quinto es el unico que cruza zonas y por "
    "eso queda forzado: la Zone 1 tiene seis goles a favor contra cinco en contra "
    "y la Zone 2 tiene uno en contra con cero a favor, asi que ese gol es de un "
    "INTERZONAL, y el unico posible es Cipolletti contra Real Arroyo Seco.\n"
    "DOS TESTIGOS CONTRA UNO. Esta pagina no publica resultados: sus filas salen "
    "de RSSSF. Y la tabla que la propia RSSSF publica al lado de esos partidos "
    "coincide EXACTA con nuestra suma en los veinticinco clubes, las seis cifras "
    "cada uno. La tabla de la Wikipedia en INGLES tambien coincide con nuestra "
    "suma, en los diez clubes discutidos, uno por uno. La unica que dice otra "
    "cosa es la pagina en espanol.\n"
    "OJO CON LA FUERZA DE ESE ARGUMENTO. Nuestra suma y la tabla de RSSSF no son "
    "dos testigos sino uno: las dos salen del mismo documento. Y no se pudo "
    "verificar que la pagina en ingles no derive de RSSSF, asi que en el peor de "
    "los casos esto es un testigo contra otro. Lo que si esta medido es que "
    "ninguna de las tres coincide con la espanola, y que la espanola es la unica "
    "que no publica el partido que sostiene su numero.\n"
    "No se corrige nada: las filas dicen lo que dice su fuente. Se anota el "
    "desacuerdo. Cerrarlo del todo pide una fuente que publique esos cinco "
    "partidos uno por uno, y no se encontro ninguna. "
)

# Los tres clubes de la Primera C 2011-12 comparten explicacion porque comparten
# causa: no son tres desvios sino una tabla.
_CUADRO_REVA_2004 = (
    "EL CUADRO ARRASTRA EL MARCADOR QUE LA GRILLA YA NO TIENE, y es la misma "
    "mano. El `{{Copa}}` de esa seccion anota la vuelta de la final como "
    "`RD2-score1-2= 0` y `RD2-score2-2= 2`, o sea Candelaria 0 - Lujan 2, "
    "identico al 2-0 que la grilla decia antes de arbitrarse. Que dos partes del "
    "mismo articulo coincidan no las convierte en dos testigos: coincidir es lo "
    "que se espera cuando derivan juntas.\n"
    "LO QUE LAS SEPARA es la fuente citada, que publica `28/12/2004 en Lujan de "
    "Cuyo: Lujan de Cuyo 4 (Emiliano Romay 2, Alfredo Molina y Santiago Sandoval), "
    "Atletico Candelaria 1 (Richard Nunez)` -- cinco goleadores con nombre, que "
    "en un 2-0 no entran -- y que coincide con esta pagina al gol en los otros 55 "
    "partidos que le fecha. Ver el `Marcador` de la `Zona Revalida - Final`.\n"
    "Asi que no hay nada que corregir del lado de la grilla: el que quedo mal es "
    "el cuadro, y un cuadro no se edita desde aca.\n"
    "http://josecarluccio.blogspot.com/2013/09/argentina-consejo-federal-afa-torneo_422.html")


_TABLA_B_2010_11 = (
    "LA TABLA ARRASTRA EL MISMO GOL DE MAS QUE ARRASTRABA LA GRILLA. Hasta que "
    "se corrigio la fecha 6, esta pagina cerraba consigo misma en los 22 clubes: "
    "su `Platense 1-1 Estudiantes (BA)` y su tabla decian lo mismo. Eso no era "
    "una verificacion sino la firma de que las dos mitades derivaron juntas -- "
    "RSSSF tambien cierra consigo misma, con el 0-0 --.\n"
    "LO DEMUESTRA EL HISTORIAL DE LA PROPIA PAGINA. Entre la revision del "
    "30/08/2010 03:30 UTC y la del 31/08 05:29, con el partido jugado en el "
    "medio, Platense y Estudiantes suman cada uno un partido, un empate y un "
    "punto, y sus goles NO se mueven: `2-4` y `7-2` antes y despues. El gol de "
    "mas aparecio entre el 4 y el 16 de septiembre de 2010 y se quedo en las dos "
    "mitades del articulo.\n"
    "Asi que no hay nada que corregirle a la grilla: la corregida es ella, y la "
    "que quedo mal es la tabla. Ver el `Marcador` de la Fecha 6, que trae los "
    "numeros y las otras tres fuentes que coinciden.")


_TABLA_C_2011_12 = (
    "NO ES UN PARTIDO MAL LEIDO, Y LOS PROPIOS DESVIOS LO DICEN. Un marcador mal "
    "leido toca SIEMPRE a dos clubes con deltas espejados: lo que le sobra de "
    "goles a favor a uno le sobra de goles en contra al otro. Aca la tabla dice, "
    "contra nuestra suma, J. J. de Urquiza +2 a favor y -3 en contra, San Miguel "
    "-2 y +2, y Sacachispas -1 a favor y CERO en contra. Ese ultimo no puede "
    "venir de un partido: un partido que le cambia un gol a favor a un club se lo "
    "cambia en contra a otro, y no hay otro. Y el par de San Miguel (-2/+2) pediria "
    "un socio de +2/-2, pero Urquiza es +2/-3, que no cierra.\n"
    "DOS TESTIGOS CONTRA UNO, Y EL TERCERO ES UNA COPIA. Nuestra suma sale de la "
    "GRILLA DE RESULTADOS DE LA PROPIA PAGINA, asi que la pagina ya se contradice "
    "sola. El blog de Jose Carluccio, que publica las 38 fechas partido por "
    "partido, da exactamente nuestras cifras en los tres: 45-30, 37-54 y 28-33. "
    "Se leyeron sus 380 partidos: dos renglones le salen mal formados --uno se "
    "come el nombre del local porque colisiona con la sede, `en Gregorio de "
    "Laferrere 3, San Miguel 0`, y otro corta antes del visitante-- y los seis "
    "desvios que quedan contra nuestra suma son EXACTAMENTE lo que aportan esos "
    "dos partidos. La Wikipedia en INGLES no sirve de segunda opinion: trae las "
    "mismas cifras erradas, las tres. Y RSSSF no publica tabla de Primera C esa "
    "temporada.\n"
    "EL TOTAL NO DISCRIMINA, y conviene decirlo. La tabla de la pagina suma 792 "
    "goles a favor y 792 en contra; nuestra suma da 793 y 793. Las dos CIERRAN, "
    "porque los desvios se compensan entre si. O sea que la tabla esta "
    "internamente balanceada y aun asi no es la de su propia grilla: quien la "
    "tipeo tipeo un conjunto coherente y equivocado, y la columna Dif --que en el "
    "wikitexto esta escrita a mano, no calculada-- acompana a los goles errados en "
    "las tres filas. Por eso tampoco es \"una celda mal tipeada\".")


# LAS CUATRO DE LA TEMPORADA EN CURSO. Son las primeras `Revisado` sobre paginas
# VIVAS: las 56 anteriores son de temporadas cerradas, donde la tabla ya no se
# mueve. Conviene tenerlo presente al leerlas, y hay una consecuencia escrita al
# pie de este bloque.
#
# Las arbitra Promiedos, que para la temporada en curso es la fuente natural --y
# la unica que sirve: se probo su archivo historico y solo guarda la temporada
# que se esta jugando--. Publica PJ, goles y G-E-P por club, y en los cuatro
# casos coincide EXACTO con nuestra grilla y no con la tabla de Wikipedia.
#
# Se comparan clubes con el MISMO PJ en las tres partes. No es un detalle: al
# momento de mirar, Promiedos ya tenia jugada una fecha que la pagina todavia no
# cargaba para seis clubes, y comparar goles acumulados entre dos cortes
# distintos del calendario da una diferencia que no es un error de nadie.
_PROMIEDOS_B = "https://www.promiedos.com.ar/league/primera-b-metropolitana/fahh"
_PROMIEDOS_BN = "https://www.promiedos.com.ar/league/primera-nacional/ebj"
_PROMIEDOS_C = "https://www.promiedos.com.ar/league/primera-c/ffjb"


REVISADOS: tuple[Revisado, ...] = (
    Revisado(
        pagina="Campeonato de Primera Nacional 2026", club="San Miguel", desvio="GF-1",
        porque="La tabla le da GF19 GC28 en 26 partidos y nuestra grilla GF20 "
               "GC28: le falta UN gol a favor.\n"
               "LA PROPIA TABLA LO DEMUESTRA, sin salir de la pagina: sus dos "
               "columnas de goles suman GF905 y GC906 sobre los mismos partidos, "
               "y tienen que dar igual. Sobra un gol en contra que ningun club "
               "declara haber convertido, y es exactamente el que le falta a esta "
               "fila: poniendo nuestro numero, la tabla cierra.\n"
               "Y LO CONFIRMA PROMIEDOS, que le da `PJ 26, goles 20:28, 6-11-9`. "
               "El PJ y el G-E-P coinciden en las tres partes, asi que se estan "
               "comparando los mismos 26 partidos.\n"
               + _PROMIEDOS_BN),
    Revisado(
        pagina="Campeonato de Primera B 2026 (Argentina)", club="Real Pilar", desvio="GF-2",
        porque="La tabla le da GF34 GC31 en 32 partidos y nuestra grilla GF36 "
               "GC31: le faltan DOS goles a favor.\n"
               "NINGUN PARTIDO PUEDE EXPLICARLO, y eso se puede razonar antes de "
               "ir a buscar nada. Un marcador mal leido mueve a los DOS clubes "
               "del partido, y aca solo se desvian Real Pilar (en GF) y San "
               "Martin (B) (en GC): el unico cruce posible seria entre ellos. "
               "Pero la tabla publica tambien el G-E-P y coincide con el nuestro "
               "--14-9-9 y 9-13-10--, asi que ningun resultado cambia de ganador; "
               "y los dos partidos entre ellos son `San Martin (B) 1-2 Real "
               "Pilar` y un 0-0. Quitarle dos goles a Real Pilar en el primero lo "
               "convierte en derrota, que contradice el G-E-P de la propia tabla, "
               "y del segundo no hay dos goles que quitar.\n"
               "Y LO CONFIRMA PROMIEDOS: `GamePlayed 32, Goals 36:31, Points 51, "
               "GamesWon 14, GamesEven 9, GamesLost 9`. Los 51 puntos cierran con "
               "14 ganados y 9 empatados, que es lo que decimos nosotros.\n"
               + _PROMIEDOS_B),
    Revisado(
        pagina="Campeonato de Primera B 2026 (Argentina)", club="San Mart\u00edn (B)", desvio="GC-2",
        porque="La tabla le da GF31 GC32 en 32 partidos y nuestra grilla GF31 "
               "GC34: le faltan DOS goles en contra. Es la otra mitad del desvio "
               "de Real Pilar, y por el mismo razonamiento ningun partido lo "
               "explica: ver la entrada de Real Pilar en este mismo archivo.\n"
               "Lo que hace INVISIBLE a este par es que las dos tablas cierran "
               "consigo mismas. Bajar dos goles a favor de un club y dos en "
               "contra de otro deja los totales iguales --688 y 688 en la tabla, "
               "690 y 690 en la grilla--, asi que la suma no denuncia nada. Hay "
               "que mirar fila por fila.\n"
               "LO CONFIRMA PROMIEDOS: `GamePlayed 32, Goals 31:34, Points 40, "
               "GamesWon 9, GamesEven 13, GamesLost 10`.\n"
               + _PROMIEDOS_B),
    Revisado(
        pagina="Campeonato de Primera C 2026 (Argentina)", club="Mu\u00f1iz", desvio="E+1 P-1",
        porque="Aca no se desvian los goles sino el G-E-P: la tabla dice 4-11-10 "
               "en 25 partidos y la grilla da 4-10-11, con los GOLES coincidiendo "
               "exacto en 17:26.\n"
               "ESO SOLO YA LO PRUEBA. Un marcador mal leido mueve siempre los "
               "goles; si los goles coinciden y el reparto de ganados, empatados "
               "y perdidos no, ningun partido puede explicarlo. No hay a donde ir "
               "a buscar.\n"
               "Y HAY UN SEGUNDO TESTIGO, que ademas es aritmetico: la plantilla "
               "de la tabla calcula los puntos sola, y con `g=4|e=11|p=10` "
               "muestra 23. Promiedos publica `PJ 25, goles 17:26, pts 22, "
               "4-10-11`, y 22 es lo que sale de 4 ganados y 10 empatados: los "
               "nuestros. La tabla se contradice con el marcador que ella misma "
               "publica.\n"
               + _PROMIEDOS_C),
    Revisado(
        pagina="Torneo Argentino A 2004-05", club="Luján de Cuyo",
        contra="Atlético Candelaria", porque=_CUADRO_REVA_2004),
    Revisado(
        pagina="Campeonato de Primera B 2010-11 (Argentina)", club="Platense", desvio="GF+1 GC+1",
        porque=_TABLA_B_2010_11),
    Revisado(
        pagina="Campeonato de Primera B 2010-11 (Argentina)", club="Estudiantes (BA)", desvio="GF+1 GC+1",
        porque=_TABLA_B_2010_11),
    Revisado(
        pagina="Campeonato de Primera C 2011-12 (Argentina)", club="J. J. de Urquiza", desvio="GF+2 GC-3",
        porque=_TABLA_C_2011_12),
    Revisado(
        pagina="Campeonato de Primera C 2011-12 (Argentina)", club="Sacachispas", desvio="GF-1",
        porque=_TABLA_C_2011_12),
    Revisado(
        pagina="Campeonato de Primera C 2011-12 (Argentina)", club="San Miguel", desvio="GF-2 GC+2",
        porque=_TABLA_C_2011_12),
    Revisado(
        pagina="Torneo Argentino A 2008-09", club="Ramón Santamarina", desvio="GF+3 G+1 P-1",
        porque=_TABLA_2008_09),
    Revisado(
        pagina="Torneo Argentino A 2008-09", club="Alvarado", desvio="GC+3 G-1 P+1",
        porque=_TABLA_2008_09),
    Revisado(
        pagina="Torneo Argentino A 2008-09", club="Villa Mitre", desvio="GF+2",
        porque=_TABLA_2008_09),
    Revisado(
        pagina="Torneo Argentino A 2008-09", club="Rivadavia (L)", desvio="GC+2",
        porque=_TABLA_2008_09),
    Revisado(
        pagina="Torneo Argentino A 2008-09", club="Cipolletti", desvio="GF+1",
        porque=_TABLA_2008_09),
    Revisado(
        pagina="Torneo Argentino A 2008-09", club="Real Arroyo Seco", desvio="GC+1",
        porque=_TABLA_2008_09),
    Revisado(
        pagina="Torneo Argentino A 2008-09", club="Gimnasia y Esgrima (M)", desvio="GF+1",
        porque=_TABLA_2008_09),
    Revisado(
        pagina="Torneo Argentino A 2008-09", club="Juventud Unida Universitario", desvio="GF+1 E+1 P-1",
        porque=_TABLA_2008_09),
    Revisado(
        pagina="Torneo Argentino A 2008-09", club="Central Córdoba (SdE)", desvio="GC+1 G-1 E+1",
        porque=_TABLA_2008_09),
    Revisado(
        pagina="Torneo Argentino A 2008-09", club="Deportivo Maipú", desvio="GC+1",
        porque=_TABLA_2008_09),

    Revisado(
        pagina="Torneo Argentino A 2007-08", club="Juventud Unida Universitario", desvio="GF-1",
        porque=_AWD_2007),
    Revisado(
        pagina="Torneo Argentino A 2007-08", club="Luján de Cuyo", desvio="GC-1",
        porque=_AWD_2007),
    Revisado(
        pagina="Torneo Federal A 2025", club="9 de Julio (R)", contra="Germinal",
        porque="La vuelta del 12/10/2025 termino 5-0, que es lo que dice la grilla. "
               "El que esta mal es el CUADRO DE LLAVES, que publica 4-0 con un "
               "global de 5-1. No hay nada que corregir en el dataset: la fila ya "
               "esta bien.\n"
               "LA PAGINA SE CONTRADICE SOLA y se desmiente a si misma sin ayuda. "
               "Ademas del cuadro trae una tabla resumen de las llaves con los "
               "GLOBALES, y ahi dice \"9 de Julio (R) 6 - 1 Germinal\": con el 1-1 "
               "de la ida, eso exige 5-0. Esa tabla es confiable en su propio "
               "contexto -- la llave de al lado, \"Atenas (RC) 5 - 0 Sarmiento (R)\", "
               "cierra exacto con su cuadro --.\n"
               "Y la prensa lo decide sin margen. Diario Jornada (Trelew) publico la "
               "cronica la misma noche del partido, 12/10/2025 18:16, con CINCO "
               "goleadores y sus minutos -- Ibanez y Peralta en el primer tiempo, "
               "Abondetto, Del Sole y Bonilla en el segundo --, las dos formaciones "
               "y el arbitro. Cinco goles con cinco autores distintos no se "
               "reconcilian con un 4-0: sobraria un gol y un goleador.\n"
               "El global lo confirma por otra via y desde los dos lados de la "
               "serie: Canal 12 de Chubut (12/10/2025 19:57, el lado de Germinal) y "
               "Diario Castellanos de Rafaela (18/10/2025, el lado de 9 de Julio) "
               "dicen los dos \"global 6-1\". El 5-1 del cuadro no aparece en "
               "ninguna fuente.\n"
               "Es 9 de Julio de RAFAELA y no el de Morteros: las cronicas ubican "
               "el partido en el German Soltermam."),
    Revisado(
        pagina="Torneo Federal A 2024", club="Círculo Deportivo", desvio="GC-1",
        porque="Se desvia en (0, +1) y no hay ningun club que lo aparee: para que un "
               "partido lo explicara haria falta otro desviado en (+1, 0), y el unico "
               "otro club desviado de la fase es Deportivo Camioneros, que va en "
               "(0, -1). Ademas no se cruzan entre si en la grilla, y ninguno de sus "
               "rivales quedo fuera del cruce. Sin pareja posible no hay marcador que "
               "corregir: la equivocada es la fila de la tabla."),
    Revisado(
        pagina="Torneo Federal A 2024", club="Deportivo Camioneros", desvio="GC+1",
        porque="Mismo caso que Circulo Deportivo en la misma fase y por el mismo "
               "motivo: su delta (0, -1) pediria una pareja en (-1, 0) que no existe, "
               "los dos desviados no se cruzan, y ninguno de sus rivales quedo fuera "
               "del cruce. La fila de la tabla es la que esta mal."),
    Revisado(
        pagina="Campeonato de Primera Nacional 2021", club="Deportivo Maipú", desvio="GF-1 GC-1",
        porque="Es el unico club desviado de su zona una vez resueltos los otros dos "
               "-- Almirante Brown y Mitre (SdE), que se cerraron con el 0-0 de la "
               "Fecha 19 --, y ninguno de sus rivales quedo fuera del cruce. Un "
               "marcador mal leido toca siempre a dos clubes; aca se mueve uno solo, "
               "asi que ningun partido puede explicarlo y la equivocada es la fila de "
               "la tabla."),
    Revisado(
        pagina="Campeonato de Primera C 2015 (Argentina)", club="Talleres (RdE)", desvio="GF+2 GC+1",
        porque="Las dos ruedas con Argentino de Quilmes estan bien y la equivocada es "
               "la tabla. La segunda tiene ademas una explicacion que la aritmetica no "
               "podia adivinar: el 0-1 de la Fecha 36 es un resultado ADMINISTRATIVO. "
               "En la cancha gano Argentino de Quilmes 1-0 y el Tribunal de Disciplina "
               "se lo dio ganado a Talleres el 20/11/2015 por mala inclusion de un "
               "jugador. La grilla publica el fallo, que es lo que corresponde.\n"
               "El arreglo que pedia la aritmetica -- tres goles mas repartidos -- era "
               "la senal de que el problema estaba del otro lado: una grilla no pierde "
               "tres goles por un tipeo."),
    Revisado(
        pagina="Campeonato de Primera C 2015 (Argentina)", club="Argentino de Quilmes", desvio="GF+1 GC+2",
        porque="La otra mitad del par con Talleres (RdE), incluido el partido que el "
               "Tribunal le dio por perdido. Mismas fuentes, mismo desenlace: la grilla "
               "tiene razon. Entrada propia porque el aviso se emite por club."),
    Revisado(
        pagina="Torneo Argentino A 2012-13", club="Ramón Santamarina", desvio="GF+2 GC+2",
        porque="Las dos ruedas con Deportivo Maipu estan bien. La Fecha 5 fue 2-0 con "
               "los goles de Roman Strada a los 33 segundos y Arnaldo Gonzalez a los 34 "
               "del segundo tiempo. Y la Fecha 16 es otro resultado por fallo: iba 1-2 "
               "cuando se suspendio a los 37 del segundo tiempo por incidentes de la "
               "barra local con la policia, y se homologo 0-2. La grilla publica el "
               "homologado.\n"
               "Por eso el arreglo de cuatro goles que pedia la aritmetica no podia "
               "existir: la tabla esta contando ese partido con una mezcla del marcador "
               "de cancha y el de escritorio."
               "\n"
               "Y hay una corroboracion de afuera, encontrada despues al cruzar la "
               "foja de RSSSF: su LISTA DE PARTIDOS coincide con nuestra grilla marcador "
               "por marcador en los cuatro partidos de los dos pares en disputa -- 2-0, "
               "3-0, 0-2 y 4-2 --, pero su TABLA trae el mismo desvio que la de Wikipedia. "
               "O sea que la fuente independiente le da la razon a la grilla y se "
               "contradice a si misma en la tabla, igual que la pagina."),
    Revisado(
        pagina="Torneo Argentino A 2012-13", club="Deportivo Maipú", desvio="GF+2 GC+2",
        porque="La otra mitad del par con Ramon Santamarina, incluido el partido "
               "suspendido y homologado 0-2. Misma cronica, mismo desenlace. Entrada "
               "propia porque el aviso es por club."
               "\n"
               "Y hay una corroboracion de afuera, encontrada despues al cruzar la "
               "foja de RSSSF: su LISTA DE PARTIDOS coincide con nuestra grilla marcador "
               "por marcador en los cuatro partidos de los dos pares en disputa -- 2-0, "
               "3-0, 0-2 y 4-2 --, pero su TABLA trae el mismo desvio que la de Wikipedia. "
               "O sea que la fuente independiente le da la razon a la grilla y se "
               "contradice a si misma en la tabla, igual que la pagina."),
    Revisado(
        pagina="Torneo Argentino A 2012-13", club="Juventud Unida Universitario", desvio="GF-1",
        porque="Las dos ruedas con Guillermo Brown estan bien. El 3-0 de la Fecha 8 lo "
               "confirma una cronica con los goleadores y las jugadas. Y el 4-2 de la "
               "Fecha 19 tiene una particularidad que explica el desvio: el partido se "
               "jugo en DOS DIAS -- se suspendio 1-1 el 10/02 y se completo el 11/02 --, "
               "asi que hay fuentes que lo cuentan partido y otras entero.\n"
               "Ademas una tabla de Superdepor del 31/10/2012, contemporanea y anterior "
               "a la fecha 19, ya trae los totales del torneo, o sea que no puede "
               "derivar de la Wikipedia de hoy."
               "\n"
               "Y hay una corroboracion de afuera, encontrada despues al cruzar la "
               "foja de RSSSF: su LISTA DE PARTIDOS coincide con nuestra grilla marcador "
               "por marcador en los cuatro partidos de los dos pares en disputa -- 2-0, "
               "3-0, 0-2 y 4-2 --, pero su TABLA trae el mismo desvio que la de Wikipedia. "
               "O sea que la fuente independiente le da la razon a la grilla y se "
               "contradice a si misma en la tabla, igual que la pagina."),
    Revisado(
        pagina="Torneo Argentino A 2012-13", club="Guillermo Brown", desvio="GC-1",
        porque="La otra mitad del par con Juventud Unida Universitario, incluido el "
               "partido que se jugo en dos dias. Mismas fuentes, mismo desenlace. "
               "Entrada propia porque el aviso es por club."
               "\n"
               "Y hay una corroboracion de afuera, encontrada despues al cruzar la "
               "foja de RSSSF: su LISTA DE PARTIDOS coincide con nuestra grilla marcador "
               "por marcador en los cuatro partidos de los dos pares en disputa -- 2-0, "
               "3-0, 0-2 y 4-2 --, pero su TABLA trae el mismo desvio que la de Wikipedia. "
               "O sea que la fuente independiente le da la razon a la grilla y se "
               "contradice a si misma en la tabla, igual que la pagina."),
    Revisado(
        pagina="Campeonato de Primera B Nacional 2012-13", club="Atlético Tucumán", desvio="GF+1",
        porque="El 2-0 de la grilla es el correcto y la tabla es la equivocada. La "
               "Gaceta de Tucuman, en una nota sobre el gol de Gabriel Mendez desde "
               "mitad de cancha, dice textual que \"Atletico ya ganaba 1-0 y se jugaba "
               "tiempo de descuento\": eso CUENTA los goles y excluye cualquier otro "
               "entre el 1-0 y el descuento. El compilado historiayfutbol lista los "
               "goleadores de esa fecha y en este partido nombra exactamente dos, Luis "
               "Rodriguez y Gabriel Mendez. La unica fuente que da 3-0 es ESPN, que "
               "agrega un gol en contra a los 76 que no aparece en ninguna otra parte "
               "-- un gol fantasma en su feed, no uno que se le escapo a la cronica."),
    Revisado(
        pagina="Campeonato de Primera B Nacional 2012-13", club="Olimpo", desvio="GC+1",
        porque="La otra mitad del par con Atletico Tucuman. Mismo partido verificado "
               "con La Gaceta y el compilado de goleadores, mismo desenlace: la grilla "
               "tiene razon. Entrada propia porque el aviso se emite por club."),
    Revisado(
        pagina="Campeonato de Primera B Nacional 2013-14", club="Talleres (C)", desvio="GC+4",
        porque="El 1-4 de la grilla esta bien y el arreglo que pedia la aritmetica "
               "(1-8) era la senal de que el problema estaba del otro lado: cuatro "
               "goles de diferencia no son un digito mal transcripto. La cronica da "
               "los cinco goles con su minuto -- Juan Sanchez Sotelo de penal a los 35 "
               "para Talleres; Sproat a los 32, Guerrero y los demas para Brown --. La "
               "equivocada es la fila de la tabla."),
    Revisado(
        pagina="Campeonato de Primera B Nacional 2013-14", club="Brown de Adrogué", desvio="GF+4",
        porque="La otra mitad del par con Talleres (C): mismo partido, misma cronica "
               "con los cinco goleadores, mismo desenlace. Entrada propia porque el "
               "aviso es por club."),
    Revisado(
        pagina="Campeonato de Primera B Nacional 2014", club="Instituto", desvio="GC-1",
        porque="El 1-2 de la grilla esta bien. La cronica da los tres goles con su "
               "minuto: Gotti a los 30 y Bernardi a los 61 para Instituto, Pinero da "
               "Silva a los 66 para Guarani. El 0-2 que pedia la tabla borraria un gol "
               "que la cronica nombra con su autor. La equivocada es la tabla."),
    Revisado(
        pagina="Campeonato de Primera B Nacional 2014", club="Guaraní Antonio Franco", desvio="GF-1",
        porque="La otra mitad del par con Instituto: el gol que la tabla querria "
               "borrar es justamente el suyo, el de Pinero da Silva a los 66. Entrada "
               "propia porque el aviso es por club."),
    Revisado(
        pagina="Campeonato de Primera C 2015 (Argentina)", club="Central Córdoba (R)", desvio="GF-1",
        porque="El 0-2 de la grilla esta bien: los dos goles son de Central Cordoba de "
               "Rosario, Cristian Vella a los 7 y Federico Ferrari a los 87, los dos "
               "con su minuto en la cronica. El 0-1 que pedia la tabla tendria que "
               "borrar uno de esos dos. La equivocada es la tabla."),
    Revisado(
        pagina="Campeonato de Primera C 2015 (Argentina)", club="Sacachispas", desvio="GC-1",
        porque="La otra mitad del par con Central Cordoba (R): mismo partido, misma "
               "cronica con los dos goleadores. Entrada propia porque el aviso es por "
               "club."),
    Revisado(
        pagina="Torneo Argentino A 2010-11", club="Sportivo Belgrano", desvio="GF+1 GC+2",
        porque="Este es el mas interesante de los cinco: el 0-2 de la grilla es un "
               "resultado HOMOLOGADO, no el que quedo en la cancha. La cronica de La "
               "Voz del Interior del 25/04/2011, rescatada del Web Archive, da el "
               "partido 1-2 -- Perez a los 27 del primer tiempo para Sportivo "
               "Belgrano; Oga a los 5 y Serrizuela a los 39 del segundo para Central "
               "Norte -- y cuenta que a los 43 del segundo tiempo expulsaron al arquero "
               "Barucco, la hinchada local desbordo y el arbitro Ariel Montero "
               "suspendio el partido a los 44. Se homologo 0-2.\n"
               "Por eso el arreglo de 1-4 que pedia la aritmetica es un artefacto: la "
               "tabla no esta contando este partido con el marcador de la cancha ni "
               "con el homologado, sino con una mezcla. La grilla publica el "
               "homologado, que es lo que corresponde. No hay nada que corregir."),
    Revisado(
        pagina="Torneo Argentino A 2010-11", club="Central Norte (S)", desvio="GF+2 GC+1",
        porque="La otra mitad del par con Sportivo Belgrano, en el partido suspendido "
               "y homologado 0-2. Misma cronica de La Voz del Interior, mismo "
               "desenlace. Entrada propia porque el aviso es por club."),
    Revisado(
        pagina="Campeonato de Primera B Nacional 2009-10", club="Platense", desvio="GF-1 GC-1",
        porque="Se desvia SOLO, y eso alcanza para cerrarlo sin fuente de afuera. Un "
               "marcador mal leido toca siempre a dos clubes, con deltas espejados; "
               "aca ningun otro club de la tabla se desvia y ninguno de los rivales de "
               "Platense quedo fuera del cruce -- la tabla y la grilla les cuentan a "
               "todos los mismos partidos --, asi que no hay ningun partido que pueda "
               "explicarlo. La equivocada es la fila de la tabla."),
    Revisado(
        pagina="Anexo:Torneo Final 2013 (Argentina)", club="Unión", desvio="GC+1",
        porque="Se desvia solo y ninguno de sus rivales quedo fuera del cruce, asi que "
               "ningun partido puede explicarlo: un marcador mal leido movería a dos "
               "clubes y aca se mueve uno. La equivocada es la fila de la tabla, no la "
               "grilla. Es la misma prueba interna que cierra a Platense en el B "
               "Nacional 2009-10."),
    Revisado(
        pagina="Copa de la Liga Profesional 2023", club="Racing Club", desvio="GF-1",
        porque="Se desvia solo en su zona y ninguno de sus rivales quedo fuera del "
               "cruce. Sin un segundo club desviado en espejo no hay partido que "
               "explique la diferencia, asi que la fila de la tabla es la que esta "
               "mal. Prueba interna, no hace falta fuente externa."),
    Revisado(
        pagina="Campeonato de Primera C 2024 (Argentina)", club="J. J. de Urquiza", desvio="GC-1",
        porque="Se desvia solo en el Torneo Clausura y todos sus rivales son "
               "comparables. Ningun marcador mal leido puede mover a un club sin mover "
               "a otro, asi que la equivocada es la fila de la tabla."),
    Revisado(
        pagina="Torneo Federal A 2016-17", club="Gutiérrez", desvio="GF+2 GC+2",
        porque="Se desvia solo en la primera fase y ninguno de sus rivales quedo fuera "
               "del cruce. Su delta es ademas de dos goles en cada columna, que "
               "necesitaria dos partidos mal leidos y por lo tanto hasta cuatro clubes "
               "desviados; no hay ninguno mas. La equivocada es la fila de la tabla."),
    Revisado(
        pagina="Torneo Federal A 2025", club="Cipolletti", desvio="GF+2 GC-1 G+1 P-1",
        porque="Las dos ruedas con Villa Mitre se fueron a verificar y las dos "
               "estan bien: la fecha 4 (Villa Mitre 0-2 Cipolletti, goles de "
               "Cristian Ibarra a los 23 de chilena y de Gonzalo Crespo) la cuentan "
               "La Nueva de Bahia Blanca y LM Cipolletti, o sea la prensa de las dos "
               "ciudades desde lados opuestos; y la fecha 13 (Cipolletti 1-1 Villa "
               "Mitre, Enzo Gonzalez 37 PT y Matias Paez 41) la publica Ascenso del "
               "Interior. Ademas las cronicas traen los puntajes acumulados que "
               "calcula el periodista, y esos totales solo cierran con estos "
               "marcadores. No hay nada que corregir en la grilla: la equivocada es "
               "la tabla de posiciones."),
    Revisado(
        pagina="Torneo Federal A 2025", club="Villa Mitre", desvio="GF+1 GC-2 G+1 P-1",
        porque="La otra mitad del par con Cipolletti: sus deltas son los de aquel. "
               "Las mismas dos ruedas verificadas con la prensa de Bahia Blanca y de "
               "Cipolletti, mismo desenlace. Va como entrada propia porque el aviso "
               "se emite POR CLUB, y callar uno solo dejaria el par denunciado a "
               "medias."),
    Revisado(
        pagina="Torneo Federal A 2025", club="Círculo Deportivo", desvio="GF-1 GC+2 G-1 P+1",
        porque="Las dos ruedas con Sol de Mayo verificadas y las dos estan bien. La "
               "fecha 6 (Circulo Deportivo 1-0, gol de Imanol Iriberri de penal a "
               "los 31) la cuentan TRES diarios de las dos puntas -- Rio Negro y "
               "NoticiasNet desde Viedma, El Marplatense desde Otamendi --, cada uno "
               "con el goleador y su minuto. La fecha 15 (Sol de Mayo 4-1) tambien "
               "queda confirmada. La equivocada es la tabla."),
    Revisado(
        pagina="Torneo Federal A 2025", club="Sol de Mayo (V)", desvio="GF-2 GC+1 G-1 P+1",
        porque="La otra mitad del par con Circulo Deportivo: mismas dos ruedas, "
               "mismas fuentes de las dos ciudades, mismo desenlace. Entrada propia "
               "porque el aviso es por club."),
    Revisado(
        pagina="Campeonato de Primera Nacional 2025", club="Defensores de Belgrano", desvio="E+1 P-1",
        porque="Este no necesita fuente de afuera porque la prueba es interna y "
               "cierra sola. La tabla dice 12-13-9 y la grilla da 12-12-10 -- un "
               "empate menos y una derrota mas -- pero los GOLES coinciden exacto, "
               "GF y GC. Un marcador mal leido mueve siempre los goles: cambiarle "
               "un digito a un partido le toca el GF o el GC a los dos clubes. Un "
               "resultado corrido con los goles intactos no lo puede explicar "
               "ningun partido, asi que lo que esta mal es el G-E-P de la fila y "
               "no hay a donde ir a buscar. Ademas no aparea con nadie: es el "
               "unico club desviado de su zona."),
    # Los cuatro clubes de los dos partidos arreglados. El desvio es real y esta
    # explicado: ver los `Dividido` de esta misma pagina.
    Revisado(
        pagina="Torneo Argentino A 2006-07", club="Central Norte (S)", desvio="PJ+1 GC+1 P+1",
        porque="La tabla le cuenta un partido que la grilla no tiene, y el partido no "
               "falta: es el del penal regalado, contra 9 de Julio (R), uno de los dos que la ultima fecha "
               "del Clausura 2007 termino con UN RESULTADO DISTINTO PARA CADA CLUB. "
               "El fallo del Consejo Federal les dio derrota a los dos, y una fila "
               "tiene un solo marcador, asi que queda afuera -- esta en `DIVIDIDOS` "
               "con toda la evidencia.\n"
               "Lo confirma la propia tabla del Clausura por dos columnas que no "
               "dependen una de la otra: Central Norte (S) figura con un PERDIDO de mas que la "
               "grilla, y ademas con cero goles a favor y uno en contra de mas. Las "
               "dos columnas dicen la misma derrota.\n"
               "No hay nada que ir a buscar: del partido se sabe todo salvo como "
               "escribir su resultado, que es precisamente lo que no se puede."),
    Revisado(
        pagina="Torneo Argentino A 2006-07", club="9 de Julio (R)", desvio="PJ+1 GC+1 P+1",
        porque="La tabla le cuenta un partido que la grilla no tiene, y el partido no "
               "falta: es el del penal regalado, contra Central Norte (S), uno de los dos que la ultima fecha "
               "del Clausura 2007 termino con UN RESULTADO DISTINTO PARA CADA CLUB. "
               "El fallo del Consejo Federal les dio derrota a los dos, y una fila "
               "tiene un solo marcador, asi que queda afuera -- esta en `DIVIDIDOS` "
               "con toda la evidencia.\n"
               "Lo confirma la propia tabla del Clausura por dos columnas que no "
               "dependen una de la otra: 9 de Julio (R) figura con un PERDIDO de mas que la "
               "grilla, y ademas con cero goles a favor y uno en contra de mas. Las "
               "dos columnas dicen la misma derrota. Y es el mas contundente de los cuatro: 9 de Julio GANO 1-0 en la cancha y la tabla lo anota perdiendo.\n"
               "No hay nada que ir a buscar: del partido se sabe todo salvo como "
               "escribir su resultado, que es precisamente lo que no se puede."),
    Revisado(
        pagina="Torneo Argentino A 2006-07", club="San Martín (SM)", desvio="PJ+1 P+1",
        porque="La tabla le cuenta un partido que la grilla no tiene, y el partido no "
               "falta: es el del soborno denunciado, contra Desamparados, uno de los dos que la ultima fecha "
               "del Clausura 2007 termino con UN RESULTADO DISTINTO PARA CADA CLUB. "
               "El fallo del Consejo Federal les dio derrota a los dos, y una fila "
               "tiene un solo marcador, asi que queda afuera -- esta en `DIVIDIDOS` "
               "con toda la evidencia.\n"
               "Lo confirma la propia tabla del Clausura por dos columnas que no "
               "dependen una de la otra: San Martín (SM) figura con un PERDIDO de mas que la "
               "grilla, y ademas con cero goles a favor y uno en contra de mas. Las "
               "dos columnas dicen la misma derrota.\n"
               "No hay nada que ir a buscar: del partido se sabe todo salvo como "
               "escribir su resultado, que es precisamente lo que no se puede."),
    Revisado(
        pagina="Torneo Argentino A 2006-07", club="Desamparados", desvio="PJ+1 GC+1 P+1",
        porque="La tabla le cuenta un partido que la grilla no tiene, y el partido no "
               "falta: es el del soborno denunciado, contra San Martín (SM), uno de los dos que la ultima fecha "
               "del Clausura 2007 termino con UN RESULTADO DISTINTO PARA CADA CLUB. "
               "El fallo del Consejo Federal les dio derrota a los dos, y una fila "
               "tiene un solo marcador, asi que queda afuera -- esta en `DIVIDIDOS` "
               "con toda la evidencia.\n"
               "Lo confirma la propia tabla del Clausura por dos columnas que no "
               "dependen una de la otra: Desamparados figura con un PERDIDO de mas que la "
               "grilla, y ademas con cero goles a favor y uno en contra de mas. Las "
               "dos columnas dicen la misma derrota.\n"
               "No hay nada que ir a buscar: del partido se sabe todo salvo como "
               "escribir su resultado, que es precisamente lo que no se puede."),
    Revisado(
        pagina="Torneo Argentino A 2006-07", club="Sportivo Patria", desvio="E+1 P-1",
        porque="La tabla acumulada le da 12-5-11 (G-E-P) y la grilla 12-4-12: un "
               "empate donde va una derrota. Los GOLES coinciden exacto, 32-38 de "
               "los dos lados, y un marcador mal leido mueve siempre los goles, asi "
               "que ningun partido puede explicarlo.\n"
               "Y hay algo mejor que ese argumento, porque no hace falta razonar "
               "sobre lo que un partido puede o no puede hacer: LA PAGINA SE "
               "CONTRADICE SOLA. Publica tres juegos de tablas -- Apertura, Clausura "
               "y la acumulada de las de descenso -- y las dos mitades de Patria "
               "suman 9-2-3 mas 3-2-9, o sea 12-4-12, que es exactamente lo que dice "
               "la grilla. La equivocada es la fila acumulada, y las otras dos tablas "
               "de la misma pagina la desmienten.\n"
               "Es uno de los tres clubes de las 24 filas donde la acumulada no es la "
               "suma de sus mitades. Los otros dos son San Martin (SM) y Atletico "
               "Tucuman, los dos tocados por partidos que no estan en la grilla; "
               "Patria no tiene ninguno, asi que aca no queda ni esa excusa. No hay "
               "a donde ir a buscar."),
    Revisado(
        pagina="Torneo Argentino A 2006-07", club="Atlético Tucumán", desvio="G+1 P-1",
        porque="La tabla acumulada le da 14-7-7 (G-E-P) y la grilla 13-7-8: un ganado "
               "donde va un perdido. Los GOLES coinciden exacto, 42-30 de los dos "
               "lados.\n"
               "LA PAGINA SE CONTRADICE SOLA, igual que con Sportivo Patria: sus dos "
               "mitades suman 5-3-6 mas 8-4-2, o sea 13-7-8, que es lo que dice la "
               "grilla. La fila acumulada es la equivocada y las otras dos tablas de la "
               "misma pagina la desmienten.\n"
               "Y se sabe de que partido se trata, que es lo lindo del caso: el "
               "Atletico Tucuman-Talleres de la Fecha 14 del Apertura se abandono con "
               "Atletico Tucuman ganando 3-0 a los 72' y despues se lo dieron perdido "
               "0-1 -- RSSSF: `awarded 0-1; abandoned at 3-0 in 72'`. La acumulada "
               "anota la CANCHA y las mitades anotan el FALLO. No hay a donde ir a "
               "buscar: las dos versiones estan en la pagina."),
    Revisado(
        pagina="Torneo Argentino A 2005-06", club="La Florida", desvio="PJ+1 GC+1 P+1",
        porque="La tabla del Clausura le cuenta un partido que la grilla no "
               "tiene, y no falta: es el La Florida-Sportivo Patria de la "
               "Fecha 10, que termino 2-2 en la cancha, se anulo y se "
               "considero 0-1 PARA LOS DOS. Dos resultados para un partido no "
               "entran en una fila, asi que la fila sale -- esta en "
               "`DIVIDIDOS` con sus tres testigos, dos de la propia pagina y "
               "uno de RSSSF.\n"
               "No hay nada que ir a buscar: del partido se sabe todo, hasta "
               "el minuto en que se interrumpio. Lo unico que no se puede es "
               "escribirlo."),
    Revisado(
        pagina="Torneo Argentino A 2005-06", club="Sportivo Patria", desvio="PJ+1 GC+1 P+1",
        porque="La tabla del Clausura le cuenta un partido que la grilla no "
               "tiene, y no falta: es el Sportivo Patria-La Florida de la "
               "Fecha 10, que termino 2-2 en la cancha, se anulo y se "
               "considero 0-1 PARA LOS DOS. Dos resultados para un partido no "
               "entran en una fila, asi que la fila sale -- esta en "
               "`DIVIDIDOS` con sus tres testigos, dos de la propia pagina y "
               "uno de RSSSF.\n"
               "No hay nada que ir a buscar: del partido se sabe todo, hasta "
               "el minuto en que se interrumpio. Lo unico que no se puede es "
               "escribirlo."),
)




# Los seis campos de una fila de tabla, en el orden en que vienen. Los nombra
# `firma_del_desvio` y son los mismos que devuelven `posiciones.sumar` y la
# lectura de la tabla, que es lo que hace comparable una cosa con la otra.
_CAMPOS_DE_LA_FILA = ("PJ", "GF", "GC", "G", "E", "P")


def firma_del_desvio(publicada, contada) -> str:
    """En que y cuanto se aparta la fila de la TABLA de la de nuestra grilla.

    `tabla menos grilla`, campo por campo, y solo los que difieren: `GF-2` quiere
    decir que la tabla le da dos goles a favor MENOS que los que suman nuestros
    partidos. Cadena vacia si no se aparta en nada.

    ES EL DELTA Y NO LOS NUMEROS, por lo que dice el comentario de `Revisado`:
    en una pagina viva los absolutos se mueven cada fecha y el delta no.

    SE CALCULA CRUDO, sin mirar `DIVIDIDOS` ni ninguna otra explicacion. Quien
    decide si un desvio se denuncia es cada chequeo, y cada uno lo decide a su
    manera --`pj_que_no_coincide` le suma los partidos divididos, `contrastar` no
    mira el PJ--; si la firma dependiera de eso, el mismo club tendria firmas
    distintas segun quien preguntara y la declaracion engancharia en un chequeo y
    en el otro no.

    Compara el prefijo comun: la tabla de algunas paginas trae tres columnas y no
    seis, y una fila corta no es un desvio en los campos que no publica.
    """
    n = min(len(publicada), len(contada), len(_CAMPOS_DE_LA_FILA))
    return " ".join(f"{_CAMPOS_DE_LA_FILA[i]}{publicada[i] - contada[i]:+d}"
                    for i in range(n) if publicada[i] != contada[i])


def revisado(pagina: str, club: str, desvio: str | None = None) -> Revisado | None:
    """La verificacion que cierra ESE desvio de ese club, si alguien la hizo.

    Si la declaracion trae `desvio` y se le pregunta por uno, tienen que ser el
    mismo: una verificacion habla de un estado concreto y deja de valer cuando el
    estado cambia.

    `desvio=None` PREGUNTA OTRA COSA -- "¿este club tiene alguna verificacion
    escrita?" -- y lo usa el unico llamador al que la firma no le sirve:
    `build.la_fuente_se_respalda` compara la tabla de RSSSF contra los partidos
    de RSSSF, que es otra tabla y otro conjunto, asi que la firma de nuestro
    desvio contra Wikipedia no dice nada ahi. Distinguirlo hace falta: al ponerle
    firma a las 58 entradas viejas, ese llamador dejo de enganchar y volvio un
    aviso que ya estaba explicado.

    Las declaraciones sin `desvio` contestan a cualquiera, que es como se
    comportaba esto antes de que el campo existiera. Hoy no queda ninguna de
    tabla asi -- ver el test que lo exige -- pero el caso sigue definido.
    """
    for r in REVISADOS:
        # Los que nombran rival NO contestan aca: verifican una llave, no la fila
        # de un club en la tabla.
        if r.pagina == pagina and r.club == club and not r.contra:
            if desvio is None or not r.desvio or r.desvio == desvio:
                return r
            return None
    return None


def revisado_llave(pagina: str, uno: str, otro: str) -> "Revisado | None":
    """La verificacion que cierra el desacuerdo de esa LLAVE, si alguien la hizo.

    Pide los dos clubes y en cualquier orden, porque una llave no tiene local.
    """
    for r in REVISADOS:
        if r.pagina == pagina and r.contra and {r.club, r.contra} == {uno, otro}:
            return r
    return None


def revisados_huerfanos(pagina: str, desviados, llaves: set | None = None) -> list[str]:
    """Los `Revisado` de esta pagina que ya no enganchan con el desvio que dicen.

    Un `Revisado` silencia un aviso, asi que tiene que caducar solo. Si la pagina
    se corrigio -- o si le cambiaron la tabla --, la verificacion que sostiene
    esta entrada hablaba de otra cosa y hay que rehacerla. Sin esto, una entrada
    vieja sigue tapando un desvio nuevo del mismo club y nadie se entera.

    SON DOS FORMAS DE CADUCAR Y NO UNA, y hasta que `desvio` existio solo se veia
    la primera:

      * el club ya no se desvia -- la pagina se arreglo, o le cambiaron la fila --
        y entonces la entrada no tiene nada que silenciar;
      * el club SIGUE desviandose pero de otra manera. Esta es la peligrosa: la
        entrada engancha igual y calla un problema que nadie miro. Se ve
        comparando la firma declarada contra la de hoy.

    `desviados` es {club: firma}; se acepta tambien un conjunto pelado, y ahi
    solo se puede mirar la primera forma.
    """
    firmas = desviados if isinstance(desviados, dict) else {}
    fuera = []
    for r in REVISADOS:
        if r.pagina != pagina:
            continue
        # Los de llave se preguntan contra los pares acusados por el cuadro;
        # los de club, contra los desvios de tabla. Son dos chequeos distintos
        # y cada uno tiene que mirar SU conjunto o la guarda no guarda.
        if r.contra:
            if llaves is None or frozenset((r.club, r.contra)) in llaves:
                continue
            fuera.append(
                f"la verificacion de {r.club} ya no engancha con ningun desvio: o "
                f"la pagina se arreglo, o le cambiaron la tabla. Sacala de "
                f"fad/correcciones.py, porque mientras siga ahi puede estar "
                f"tapando un desvio nuevo del mismo club")
            continue
        if r.club not in desviados:
            fuera.append(
                f"la verificacion de {r.club} ya no engancha con ningun desvio: o "
                f"la pagina se arreglo, o le cambiaron la tabla. Sacala de "
                f"fad/correcciones.py, porque mientras siga ahi puede estar "
                f"tapando un desvio nuevo del mismo club")
        elif r.desvio and r.club in firmas and firmas[r.club] != r.desvio:
            fuera.append(
                f"la verificacion de {r.club} hablaba de un desvio `{r.desvio}` y "
                f"hoy el desvio es `{firmas[r.club]}`: el club se sigue apartando, "
                f"pero de otra manera. Lo que se verifico ya no es lo que pasa, "
                f"asi que hay que rehacerlo y actualizar `desvio` en "
                f"fad/correcciones.py")
    return fuera


def renombrado(pagina: str, jornada: str, local: str, visita: str,
               gl, gv) -> tuple[str, str]:
    """Los nombres que ese partido VA A TENER despues de `aplicar`.

    Existe para que la deduplicacion de una fuente externa pueda preguntarlo
    ANTES. Es el mismo modo de falla que `sin_repetir` ya documenta para los
    homonimos, con otra familia de correcciones: `aplicar` corre mas abajo en el
    pipeline, asi que cuando se deduplica la pagina todavia dice "Alumni" a secas
    mientras que la fila de la otra fuente ya viene con "Alumni (VM)". Sin esto,
    el cruce no las reconoce como el mismo partido y entra dos veces.

    Y entraba: los dos partidos de la promocion del Argentino A 2005-06 se
    duplicaron apenas el lector de RSSSF aprendio a resolver esos nombres. Los
    agarro `sin_duplicados` como GRAVE, que es el sistema funcionando -- pero
    frenar el build es peor que no duplicar.
    """
    for c in CORRECCIONES:
        if (c.pagina == pagina and c.jornada == jornada
                and c.dice == (local, visita, gl, gv)):
            return c.debe
    return local, visita


# La regla que zanja los tres desacuerdos de abajo. Va aparte porque es UNA
# regla y no tres hallazgos: repetirla entera en cada entrada invita a leerla por
# arriba, que es exactamente como se cuela una entrada que no la cumple.
#
# Y ojo con lo contrario, que ya paso: compartir el `porque` COMPLETO entre varias
# entradas esconde a la que no describe. Cada una guarda su evidencia propia --que
# partido fue, a que minuto se suspendio, quien lo publica-- y comparte solo esto.
_CONVENCION = (
    "NUESTRA FECHA ES LA BUENA POR LA REGLA QUE YA TIENE EL REPO: un partido que "
    "empezo un dia y se completo otro lleva el PRIMERO, y por eso `_SE_JUGO` deja "
    "`completo`, `reanudo` y `termino` afuera a proposito -- son 105 partidos. La "
    "otra fuente fecha por el dia en que se completo; no es un error suyo, es otra "
    "convencion. Y CONTAR CUANTAS FUENTES DICEN CADA COSA NO SIRVE cuando no estan "
    "midiendo lo mismo.")


@dataclass(frozen=True)
class Fechado:
    """Un desacuerdo de DIA que se fue a verificar, y la fecha nuestra estaba bien.

    Es a `discrepan` lo que `Revisado` es a la tabla de posiciones: no corrige
    nada, y esa es exactamente su funcion. Cuando dos fuentes dan un partido en
    dias distintos hay dos desenlaces y hasta ahora solo uno se podia anotar:

      * la nuestra esta mal -> habria que corregirla, y para eso hace falta un
        mecanismo que este modulo no tiene;
      * LA NUESTRA ESTA BIEN -> no hay nada que tocar, el aviso queda abierto, y
        vuelve a aparecer en cada corrida hasta el fin de los tiempos.

    El segundo es el que se verifico y el que no tenia donde escribirse. Sin
    esto, mirar un desacuerdo y no encontrarle error se parece demasiado a no
    haberlo mirado: el proximo que pase lo investiga de cero.

    LA VARA ES LA MISMA QUE PARA CORREGIR. `porque` tiene que nombrar la fuente
    que se consulto, y tiene que ser una TERCERA -- si el arbitro fuera una de
    las dos que discuten, esto seria elegir y no verificar.

    Y no se acumula en silencio: `fechados_huerfanos` denuncia al que ya no
    engancha con ningun desacuerdo, porque eso quiere decir que alguna de las dos
    fuentes cambio y la verificacion que sostiene esta entrada quedo vieja.
    """
    pagina: str
    jornada: str
    local: str
    visita: str
    nuestra: str          # ISO, la que quedo escrita
    otra: str             # ISO, la que da la otra fuente
    porque: str


# Y las otras dos categorias donde el mismo compendio zanja un desacuerdo
# suelto. Se llego a ellas por el mismo camino: la fuente ya estaba adentro.
_CARL_B_1011 = "http://josecarluccio.blogspot.com/2015/03/argentina-1ra-b-afa-201011.html"
_CARL_BN_0708 = ("http://josecarluccio.blogspot.com/2014/05/"
                 "argentina-1ra-b-nacional-afa-200708.html")


# La 17a fecha de la Zona Sur y la vuelta de la Cuarta fase del Argentino A
# 2012-13. RSSSF corre las cinco un dia para atras; el blog de Jose Carluccio
# --que es una TERCERA fuente y publica cada partido con su ciudad y sus
# goleadores-- coincide con la pagina en las cinco.
#
# Y ESTE COMENTARIO YA DECIA CINCO CUANDO ABAJO HABIA CUATRO. La quinta
# --Cipolletti vs Gimnasia y Esgrima (CdU)-- siguio denunciandose en cada corrida
# hasta que se la fue a buscar. El numero escrito al lado de una lista es un
# invariante gratis: si no coincide con lo que la lista tiene, algo falta.
_BLOG_2012_13 = (
    "Lo verifica una TERCERA fuente, que no es ninguna de las dos que discuten: "
    "el blog de Jose Carluccio, que publica cada partido con su ciudad y sus "
    "goleadores y que este repo ya cita para el Argentino A 2004-05. La pagina y "
    "el blog coinciden; RSSSF corre esta jornada un dia para atras.\n"
    "http://josecarluccio.blogspot.com/2016/01/argentina-consejo-federal-afa-torneo_24.html")

_BLOG_2012_13_CUARTA = (
    "Lo verifica una TERCERA fuente: el blog de Jose Carluccio publica "
    "`09/06/2013 en San Miguel de Tucuman: San Jorge de Tucuman 1, San Martin de "
    "Tucuman 3`, con ciudad y goleadores. La pagina dice lo mismo; RSSSF lo corre "
    "un dia para atras.\n"
    "http://josecarluccio.blogspot.com/2016/02/argentina-consejo-federal-afa-torneo_18.html")


FECHADOS: tuple[Fechado, ...] = (
    Fechado(pagina="Torneo Argentino A 2012-13", jornada="Fecha 17",
            local="Cipolletti", visita="Gimnasia y Esgrima (CdU)",
            nuestra="2013-01-27", otra="2013-01-26", porque=_BLOG_2012_13),
    Fechado(pagina="Torneo Argentino A 2012-13", jornada="Fecha 17",
            local="Ramón Santamarina", visita="Alvarado",
            nuestra="2013-01-27", otra="2013-01-26", porque=_BLOG_2012_13),
    Fechado(pagina="Torneo Argentino A 2012-13", jornada="Fecha 17",
            local="Guillermo Brown", visita="Deportivo Maipú",
            nuestra="2013-01-27", otra="2013-01-26", porque=_BLOG_2012_13),
    Fechado(pagina="Torneo Argentino A 2012-13", jornada="Fecha 17",
            local="Defensores de Belgrano (VR)", visita="Juventud Unida Universitario",
            nuestra="2013-01-27", otra="2013-01-26", porque=_BLOG_2012_13),
    Fechado(pagina="Torneo Argentino A 2012-13", jornada="Fecha 17",
            local="Unión (MdP)", visita="Rivadavia (L)",
            nuestra="2013-01-27", otra="2013-01-26", porque=_BLOG_2012_13),
    Fechado(pagina="Torneo Argentino A 2012-13", jornada="Cuarta fase",
            local="San Jorge (T)", visita="San Martín (T)",
            nuestra="2013-06-09", otra="2013-06-08", porque=_BLOG_2012_13_CUARTA),
    # LOS CUATRO DE ABAJO SON EL MISMO CHOQUE, no cuatro hallazgos sueltos:
    # partidos que empezaron un dia y se completaron otro. Los tres primeros
    # aparecieron juntos al preguntarle al corpus cuantos desacuerdos de dia
    # tenian una nota de completado que nombrara justo la fecha de la otra
    # fuente; eran 3 de 34. El cuarto aparecio por otro camino y eso vale la
    # pena: su pagina NO trae la nota, asi que ese chequeo no lo veia. Lo
    # delato el TAMANIO del desacuerdo -- 16 dias, demasiado para una
    # postergacion de fin de semana -- y lo confirmo la prensa de la epoca.
    # EL UNICO DE LOS VEINTE QUE CAE PARA ESTE LADO, y por eso vale escribirlo:
    # si el compendio le diera la razon a ESPN en los veinte seria
    # indistinguible de una copia suya. Le da la razon a ESPN en dieciocho y a
    # RSSSF --que es de donde sale la nuestra-- en este.
    Fechado(pagina="Campeonato de Primera B Nacional 2007-08", jornada="Fecha 19",
            local="Ferro Carril Oeste", visita="Independiente Rivadavia",
            nuestra="2008-02-28", otra="2008-02-29",
            porque="Aca la que discute es worldfootball y nuestra fecha es la que "
                   "publica la propia pagina, asi que el compendio de Jose Carluccio "
                   "es un TERCERO: `28/02/2008 en Caballito: Ferro Carril Oeste 1 "
                   "(Santiago Rodriguez), Independiente Rivadavia de Mendoza 1 (Oscar "
                   "Negri)`. El 1-1 es el marcador de nuestra fila.\n"
                   "EL 29 DE FEBRERO EXISTE EN ESA JORNADA, pero para OTRO partido: el "
                   "compendio pone dos encuentros el 28 --este y Quilmes vs Platense-- "
                   "y uno el 29, que es Ben Hur vs Almagro. O sea que worldfootball no "
                   "invento un dia: corrio este partido al de al lado.\n"
                   "2008 fue bisiesto, asi que el 29 de febrero es una fecha real y no "
                   "un error de calendario. Vale decirlo porque es lo primero que uno "
                   "sospecha al ver un 29/02.\n"
                   + _CARL_BN_0708),
    Fechado(pagina="Campeonato de Primera C 2010-11 (Argentina)", jornada="Fecha 20",
            local="Defensores de Cambaceres", visita="Argentino de Merlo",
            nuestra="2010-12-07", otra="2010-12-08",
            porque="El compendio de Jose Carluccio, que arbitra los otros dieciocho "
                   "desacuerdos de estas tres temporadas, en este dice lo mismo que "
                   "nosotros: `07/12/2010 en Caniuelas: Defensores de Cambaceres 0, "
                   "Argentino de Merlo 0`, con la nota `Se jugo en cancha de Caniuelas "
                   "FC a puertas cerradas`. El 0-0 es el marcador de nuestra fila.\n"
                   "No hay nada que corregir. Se anota igual porque el aviso volvia en "
                   "cada corrida y el proximo que pasara lo investigaba de cero.\n"
                   "http://josecarluccio.blogspot.com/2015/04/argentina-1ra-c-afa-201011.html"),
    Fechado(pagina="Campeonato de Primera C 2008-09 (Argentina)", jornada="Fecha 3",
            local="Excursionistas", visita="Argentino de Merlo",
            nuestra="2008-08-18", otra="2008-09-03",
            porque="Empezo el lunes 18 de agosto de 2008, se suspendio a los 25 "
                   "minutos y se completo el miercoles 3 de septiembre, 0-0. La "
                   "pagina no lo dice --de esta temporada no publica ni el dia--, "
                   "asi que aca no hubo nota que leer: lo delato el TAMANIO del "
                   "desacuerdo. Dieciseis dias no es una postergacion de fin de "
                   "semana, que es lo que son los otros diecinueve de estas tres "
                   "temporadas.\n"
                   "LO CONFIRMA EL BLOG DE EXCURSIONISTAS, escrito EN EL MOMENTO y "
                   "por lo tanto anterior a cualquier compilacion posterior. En "
                   "agosto de 2008: `El miercoles 3/9 se continuara el partido "
                   "suspendio con Argentino de Merlo, a partir de las 15:30 hs, los "
                   "no socios tendran que tener la entrada de los 25 minutos jugados "
                   "el 18/8`. Y en septiembre, la cronica: `Excursio 0 - Arg. de "
                   "Merlo 0 / En la continuacion del partido suspendido el 18/8 "
                   "Excursionistas no pudo con Argentino de Merlo`. El 0-0 es el "
                   "marcador que tiene nuestra fila, que es lo que verifica que "
                   "hablan del mismo partido.\n" + _CONVENCION + "\n"
                   "https://excursio.blogspot.com/2008/09/"),
    Fechado(pagina="Campeonato de Primera C 2024 (Argentina)", jornada="Fecha 14",
            local="Claypole", visita="Berazategui",
            nuestra="2024-09-24", otra="2024-11-06",
            porque="Suspendido a los 36 minutos del primer tiempo, 0-0, por "
                   "incidentes de la barra local, y completado seis semanas "
                   "despues. La celda lo dice entera: `24 de septiembre{{refn|"
                   "group=n.|Suspendido por incidentes provocados por "
                   "simpatizantes locales, a los 36' del primer tiempo, con el "
                   "resultado 0-0. Se completo el 6 de noviembre, desde las "
                   "14:15.}}`, con cita a Perfil.\n"
                   "RSSSF lo publica en DOS renglones, que es la lectura mas "
                   "clara que hay: `[Sep 24, Tue] CA Claypole - AD Berazategui "
                   "abandoned at 0-0 in 35m` y `[Nov 6, Wed] CA Claypole 0-2 AD "
                   "Berazategui remaining 55m`.\n" + _CONVENCION + "\n"
                   "https://www.rsssf.org/tablesa/arg2024.html"),
    Fechado(pagina="Campeonato de Primera Nacional 2023", jornada="Fecha 6",
            local="Gimnasia y Esgrima (J)", visita="Atl\u00e9tico de Rafaela",
            nuestra="2023-03-17", otra="2023-03-18",
            porque="Suspendido a los 15 minutos del primer tiempo por un corte "
                   "del suministro electrico. La celda lo dice: `17 de marzo"
                   "{{refn|group=n.|Suspendido a los 15 minutos del primer "
                   "tiempo, por corte del suministro electrico. Se completo el "
                   "18 de marzo, a partir de las 15:00.}}`, con cita a Rafaela "
                   "Noticias.\n"
                   "ESTA ENTRADA ESTUVO A PUNTO DE IRSE PARA EL OTRO LADO, como "
                   "una correccion de fecha: Transfermarkt publica la ficha con "
                   "`Sat, 18/03/23` y betexplorer da lo mismo, asi que parecian "
                   "tres fuentes contra una. Las tres fechan por el dia en que "
                   "se completo.\n" + _CONVENCION + "\n"
                   "https://es.wikipedia.org/wiki/"
                   "Campeonato_de_Primera_Nacional_2023"),
    Fechado(pagina="Campeonato de Primera Nacional 2023", jornada="Primera fase",
            local="Quilmes", visita="Gimnasia y Esgrima (M)",
            nuestra="2023-10-28", otra="2023-11-04",
            porque="Suspendido en el entretiempo, 0-0, por una agresion al "
                   "arquero visitante desde la parcialidad local, y completado a "
                   "puertas cerradas en cancha de Platense. La ficha lo dice en "
                   "su campo `suceso`, con citas a TyC Sports y a Diario "
                   "Popular: `Se completo el 4 de noviembre, a partir de las "
                   "13:00, en el estadio Ciudad de Vicente Lopez, a puertas "
                   "cerradas`.\n" + _CONVENCION + "\n"
                   "https://es.wikipedia.org/wiki/"
                   "Campeonato_de_Primera_Nacional_2023"),
    Fechado(pagina="Campeonato de Primera Nacional 2023", jornada="Fecha 11",
            local="Deportivo Madryn", visita="Atlético de Rafaela",
            nuestra="2023-04-23", otra="2023-04-22",
            porque="La previa de La Nacion, publicada el sabado 22 de abril de "
                   "2023, dice `este domingo a las 15:30` en el Coliseo del Golfo. "
                   "El domingo era el 23, asi que ESPN esta dando el dia en que se "
                   "anuncio y no en el que se jugo.\n"
                   "Ambito lo confirma del otro lado: publica la cronica el 23 a "
                   "las 13:40 con el partido ya terminado --`At. Rafaela se lleva "
                   "un triunfo`, gol de Mauro Osores a los 8 minutos--. Las dos "
                   "son independientes de ESPN.\n"
                   "https://www.lanacion.com.ar/deportes/futbol/deportivo-madryn-"
                   "atletico-rafaela-primera-nacional-el-partido-de-la-jornada-11-"
                   "nid22042023/"),
)


# EL COMPENDIO DE JOSE CARLUCCIO, que arbitra los 18 desacuerdos de dia de la
# Primera C 2008-2011. Va aparte porque es UNA fuente y una sola medicion; lo que
# NO se comparte es el porque de cada partido, que lleva su propio renglon.
_CARL_0809 = "http://josecarluccio.blogspot.com/2014/08/argentina-1ra-c-afa-200809.html"
_CARL_0910 = "http://josecarluccio.blogspot.com/2014/11/argentina-1ra-c-afa-200910.html"
_CARL_1011 = "http://josecarluccio.blogspot.com/2015/04/argentina-1ra-c-afa-201011.html"

_PC_CARLUCCIO = (
    "LO ARBITRA UNA TERCERA FUENTE, que no es ninguna de las dos que discuten: "
    "nuestra fecha viene de RSSSF y quien discrepa es ESPN. Es el compendio "
    "`historiayfutbol` de Jose Carluccio, que este repo YA acredita para el "
    "Argentino A --ver `fad/citadas.py`-- y que nadie habia mirado para Primera "
    "C. Publica las tres temporadas partido por partido, con dia, sede y "
    "goleadores.\n"
    "SE MIDIO ANTES DE CREERLE. De sus 1.132 partidos, 1.035 de 1.038 marcadores "
    "coinciden con los que publica Wikipedia (99,71%), que es lo que verifica que "
    "habla de los mismos partidos. Y NO ES UN ESPEJO de ninguna de las dos: tiene "
    "tres errores de marcador propios --que una copia no tendria-- y en los 21 "
    "desacuerdos de estas temporadas le da la razon a ESPN en 19 y a RSSSF en 2. "
    "Un espejo de ESPN daria 21 a 0.\n"
    "Y HAY UN LIMITE, dicho: es una compilacion de 2014-2015, o sea posterior a "
    "RSSSF y a ESPN. Se probo que no las copia; no se puede probar que nunca las "
    "miro. Por eso las cuatro entradas que ademas tienen un testigo CONTEMPORANEO "
    "lo nombran, y son las mas firmes del grupo.\n"
    "http://josecarluccio.blogspot.com/")


@dataclass(frozen=True)
class Dia:
    """Un partido cuya FECHA estaba mal, corregida contra una fuente de afuera.

    El hermano de `Fechado` que SI toca el dato. Los dos salen del mismo aviso
    --dos fuentes que dan un partido en dias distintos-- y se reparten los dos
    desenlaces: si la nuestra estaba bien va un `Fechado` y no se toca nada; si
    estaba mal va uno de estos.

    LA VARA ES LA DE SIEMPRE, con un requisito extra por tocar el dato: la fuente
    que arbitra tiene que ser una TERCERA. Un desacuerdo de dia es entre dos, y si
    el arbitro fuera una de ellas esto seria elegir y no verificar. Va con su URL
    en `fuente`, que ademas es lo que queda en el credito de la fila: si la fecha
    la puso esta declaracion, el `source` tiene que decirlo y no seguir
    acreditando a quien la tenia mal.

    SE APLICA AL FINAL, despues de los completadores, y no en `aplicar` como las
    otras correcciones. No es un capricho: la fecha que hay que pisar muchas veces
    todavia no existe cuando `aplicar` corre -- la escribe RSSSF o ESPN un rato
    despues --, asi que declarar `dice` contra una fila vacia no engancharia nada.

    Y `dice` se exige: es la verificacion de que la declaracion sigue hablando del
    mismo estado. Si la fuente que fechaba mal se corrige sola, esta entrada deja
    de enganchar y el aviso lo dice, en vez de pisar en silencio una fecha que ya
    estaba bien.
    """
    pagina: str
    jornada: str
    local: str
    visita: str
    dice: str             # ISO, la que escribia el repo
    debe: str             # ISO, la verificada
    fuente: str           # la URL de quien lo verifico; va al credito de la fila
    porque: str


DIAS: tuple[Dia, ...] = (
    # NO HAY NINGUNA DE LA PRIMERA C 2024, y ese hueco vale la pena.
    # Hubo tres, hasta que se leyo la pagina: sus notas estaban definidas
    # una vez y referenciadas por NOMBRE, asi que el dia bueno ya estaba
    # escrito y no lo leiamos. Un desacuerdo de dia en una pagina con notas
    # con nombre es una pregunta para el parser, no para este archivo.
    # Ver `notas_con_nombre` en fad/parser.py.

    # Las dos de la Primera B 2010-11 las arbitra el HISTORIAL de la propia pagina,
    # que es un tercero: nuestra fecha viene de RSSSF y quien discute es ESPN.
    Dia(pagina="Campeonato de Primera B 2010-11 (Argentina)", jornada="Fecha 6",
        local="Platense", visita="Estudiantes (BA)",
        dice="2010-08-31", debe="2010-08-30",
        fuente="https://es.wikipedia.org/w/index.php?oldid=39894064",
        porque="EL HISTORIAL DE LA PROPIA PAGINA, que aca es un TERCERO: la fecha "
               "nuestra viene de RSSSF y quien discute es ESPN, asi que Wikipedia no "
               "es parte. El articulo se editaba en vivo y su tabla de posiciones va "
               "contando partidos.\nLa revision 39865552, del 30/08/2010 a las "
               "03:30 UTC, da a los dos clubes 5 partidos jugados; la 39894064, del "
               "31/08 a las 05:29 UTC --02:29 de la madrugada en la Argentina--, les "
               "da 6 a los dos en la misma edicion. Un partido no termina antes del "
               "mediodia, asi que no se jugo la tarde del 31: se jugo el 30.\n"
               "ESPN da el 30 por su lado. Es el mismo delta que arbitro el marcador "
               "de este partido; ver el `Marcador` de la Fecha 6.\n"
               "https://es.wikipedia.org/w/index.php?oldid=39894064"),
    Dia(pagina="Campeonato de Primera B 2010-11 (Argentina)", jornada="Fecha 35",
        local="Estudiantes (BA)", visita="Sarmiento (J)",
        dice="2011-04-16", debe="2011-04-15",
        fuente="https://es.wikipedia.org/w/index.php?oldid=45663491",
        porque="EL HISTORIAL DE LA PROPIA PAGINA, igual que el de la Fecha 6 y por el "
               "mismo motivo: nuestra fecha viene de RSSSF, discute ESPN, y Wikipedia "
               "no es ninguna de las dos.\nAca el corchete es de TREINTA Y NUEVE "
               "SEGUNDOS: la revision 45663480 del 16/04/2011 a las 13:22:09 UTC da a "
               "los dos clubes 34 partidos y la 45663491, a las 13:22:48, les da 35 en "
               "una sola edicion. Las 13:22 UTC son las 10:22 de la maniana en la "
               "Argentina: la tabla ya lo contaba antes del mediodia del 16, asi que "
               "no se jugo ese dia. Se jugo el 15, que es lo que da ESPN.\n"
               "https://es.wikipedia.org/w/index.php?oldid=45663491"),

    # ---- Primera B 2010-11 -------------------------------------------------
    # Los dos que quedaban de esta pagina, y los dos con el mismo argumento:
    # el compendio NO USA nuestro dia en toda la jornada.
    Dia(pagina="Campeonato de Primera B 2010-11 (Argentina)", jornada="Fecha 14",
        local="Flandria", visita="Colegiales",
        dice="2010-10-17", debe="2010-10-18", fuente=_CARL_B_1011,
        porque="Carluccio: `18/10/2010 en Jauregui: Flandria 2 (Mariano Barbieri "
               "y Alejandro Noriega), Colegiales 0`. El 2-0 es el marcador de "
               "nuestra fila.\n"
               "Y LA JORNADA ENTERA LO RESPALDA: el compendio parte la Fecha 14 en "
               "cuatro dias --15, 16, 18 y 19 de octubre-- y NO USA EL 17 para "
               "ningun partido. Nuestra fecha viene de RSSSF; quien discute es "
               "ESPN, que dice 18. Este partido es uno de los cuatro que el "
               "compendio pone ese dia.\n"
               "La fuente es la misma que arbitro los dieciocho de la Primera C "
               "2008-2011, donde se midio: 99,71% de sus marcadores coinciden con "
               "los que publica Wikipedia.\n" + _CARL_B_1011),
    Dia(pagina="Campeonato de Primera B 2010-11 (Argentina)", jornada="Fecha 36",
        local="Almagro", visita="Barracas Central",
        dice="2011-04-25", debe="2011-04-26", fuente=_CARL_B_1011,
        porque="Carluccio: `26/04/2011 en Jose Ingenieros: Almagro 1 (Humberto "
               "Vega), Barracas Central 0`. El 1-0 es el marcador de nuestra "
               "fila.\n"
               "Mismo argumento que el de la Fecha 14 y con la misma forma: el "
               "compendio parte la Fecha 36 en 22, 23, 24 y 26 de abril, y NO USA "
               "EL 25. Este partido queda solo el 26, que es lo que dice ESPN.\n"
               "Que el dia que damos nosotros no aparezca en ninguna otra fila de "
               "la jornada es lo que distingue este caso de un simple desacuerdo "
               "de asignacion: no es que la fuente ponga el partido en otro de los "
               "dias de la fecha, es que ese dia no es de la fecha.\n"
               + _CARL_B_1011),

    # ---- Primera C 2008-09 -------------------------------------------------
    # La Fecha 26 es la UNICA de las 38 que RSSSF no parte: pone los diez
    # partidos el 7 de marzo. Su propia costumbre en esta temporada es partir en
    # tres o cuatro dias, y Carluccio la parte en 7, 8 y 9. Los tres de abajo son
    # los que caen del lado del 8.
    Dia(pagina="Campeonato de Primera C 2008-09 (Argentina)", jornada="Fecha 26",
        local="Villa D\u00e1lmine", visita="Argentino de Rosario",
        dice="2009-03-07", debe="2009-03-08", fuente=_CARL_0809,
        porque="Carluccio: `08/03/2009 en Campana: Villa Dalmine 2 (Cristian "
               "Jeandet y Nestor Correa), Argentino de Rosario 1 (Cesar "
               "Basualdo)`. El 2-1 es el marcador de nuestra fila.\n"
               "Y TIENE TESTIGO CONTEMPORANEO, que es el mas firme de los cuatro: "
               "El Viola, el sitio de Villa Dalmine, publica la tabla de la "
               "temporada con la fecha DECLARADA de cada partido --no deducida de "
               "un `maniana` ni de la fecha de publicacion-- y ahi figura `26 | "
               "08/03/2009 | Villa Dalmine | 2 | 1 | Argentino de Rosario`. En los "
               "otros 40 partidos de Villa Dalmine de esa temporada El Viola "
               "coincide con RSSSF; se aparta SOLO en este.\n"
               "http://www.elviola.com.ar/2009/06/temporada-200809.html" + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2008-09 (Argentina)", jornada="Fecha 26",
        local="Deportivo Laferrere", visita="Luj\u00e1n",
        dice="2009-03-07", debe="2009-03-08", fuente=_CARL_0809,
        porque="Carluccio: `08/03/2009 en Gregorio de Laferrere: Deportivo "
               "Laferrere 0, Lujan 1 (Martin Repetto)`. El 0-1 es el marcador de "
               "nuestra fila.\n"
               "Es uno de los tres de la Fecha 26, la unica jornada de las 38 que "
               "RSSSF no parte en varios dias. De los tres, el de Villa Dalmine "
               "tiene ademas testigo contemporaneo, y los tres se mueven al mismo "
               "dia por la misma lectura." + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2008-09 (Argentina)", jornada="Fecha 26",
        local="F\u00e9nix", visita="Villa San Carlos",
        dice="2009-03-07", debe="2009-03-08", fuente=_CARL_0809,
        porque="Carluccio: `08/03/2009 en Pilar: Fenix 1 (Fabio Lapenna), Villa "
               "San Carlos 3 (Pablo Miranda, Ignacio Orona y Manuel Madrid)`. El "
               "1-3 es el marcador de nuestra fila.\n"
               "El tercero de la Fecha 26, la unica jornada de las 38 que RSSSF "
               "pone entera en un solo dia." + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2008-09 (Argentina)", jornada="Fecha 28",
        local="Excursionistas", visita="Luj\u00e1n",
        dice="2009-03-22", debe="2009-03-21", fuente=_CARL_0809,
        porque="Carluccio: `21/03/2009 en Belgrano: Excursionistas 2 (Tomas De "
               "Vicenti y Lucas Del Rio), Lujan 0`. El 2-0 es el marcador de "
               "nuestra fila.\n"
               "TESTIGO CONTEMPORANEO, y por partida doble. Los dos blogs de "
               "Excursionistas publicaron la programacion ANTES del partido: "
               "`Programacion confirmada / Fecha 28 / Excursionistas vs. Lujan / "
               "Sabado 21/3 - 15:00h. / Arbitro: Ramiro Lopez` en pampayminones, y "
               "`Fecha 28 / Excursionistas - Lujan / Estadio: Coliseo del Bajo "
               "Belgrano / Sabado 21/3 15:00 hs / Arbitro: Ramiro Lopez` en "
               "excursio. El dia esta ESCRITO --`Sabado 21/3`--, no deducido de la "
               "fecha de publicacion. El 21 de marzo de 2009 fue sabado.\n"
               "http://pampayminones.blogspot.com/2009/03/" + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2008-09 (Argentina)", jornada="Fecha 30",
        local="Villa San Carlos", visita="Luj\u00e1n",
        dice="2009-04-04", debe="2009-04-06", fuente=_CARL_0809,
        porque="Carluccio: `06/04/2009 en La Plata: Villa San Carlos 3 (Gonzalo "
               "Raverta, Federico Slezack y Rodrigo Salinas), Lujan 1 (Horacio "
               "Zacardo)`. El 3-1 es el marcador de nuestra fila.\n"
               "RSSSF fecha esta jornada el sabado 4; el 6 de abril de 2009 fue "
               "lunes, y la Primera C de esos anios jugaba de viernes a lunes, asi "
               "que un lunes no es una rareza." + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2008-09 (Argentina)", jornada="Fecha 38",
        local="Excursionistas", visita="Barracas Bol\u00edvar",
        dice="2009-05-30", debe="2009-06-01", fuente=_CARL_0809,
        porque="Carluccio: `01/06/2009 en Belgrano: Excursionistas 4 (Marcelo "
               "Pacor, Federico Rizzo, Diego Jaime y Patricio Roldan), Barracas "
               "Bolivar 0`. El 4-0 es el marcador de nuestra fila.\n"
               "TESTIGO CONTEMPORANEO, y este ademas EXPLICA el desacuerdo. El "
               "blog de Excursionistas publica primero `Ultima fecha: programacion "
               "confirmada / Fecha 38 / Excursionistas vs. Barracas Bolivar / "
               "Sabado 30/5 - 14:00 hs.`; despues `:: PARTIDO SUSPENDIDO` con "
               "`todavia no hay reprogramacion oficial del encuentro con "
               "Bolivar`; y despues `Fecha 38 - REPROGRAMADO POR SUBSEF / "
               "Excursionistas vs. Barracas Bolivar / Lunes 1/6 - 15:00 hs.`\n"
               "RSSSF SE QUEDO CON EL DIA PROGRAMADO. Y ojo con la palabra "
               "`suspendido`: aca el partido NO se jugo el 30 --se posterga "
               "entero--, asi que no es el caso de los que empiezan un dia y se "
               "completan otro, donde la fecha buena es la primera. Son dos cosas "
               "distintas y se resuelven al reves.\n"
               "http://pampayminones.blogspot.com/2009/05/" + "\n" + _PC_CARLUCCIO),

    # ---- Primera C 2009-10 -------------------------------------------------
    Dia(pagina="Campeonato de Primera C 2009-10 (Argentina)", jornada="Fecha 3",
        local="Luj\u00e1n", visita="Defensores de Cambaceres",
        dice="2009-09-07", debe="2009-09-08", fuente=_CARL_0910,
        porque="Carluccio: `08/09/2009 en Lujan: Lujan 1 (Mauro Rubira), "
               "Defensores de Cambaceres 3 (Damian Manes, Leonardo Kees y Diego "
               "Jaime)`, con la nota `Se jugo en el estadio Municipal de Lujan`. "
               "El 1-3 es el marcador de nuestra fila.\n"
               "Uno de los dos de la Fecha 3 que se corren del lunes 7 al martes "
               "8; el otro es Berazategui vs Leandro N. Alem." + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2009-10 (Argentina)", jornada="Fecha 3",
        local="Berazategui", visita="Leandro N. Alem",
        dice="2009-09-07", debe="2009-09-08", fuente=_CARL_0910,
        porque="Carluccio: `08/09/2009 en Gerli: Berazategui 1 (Gustavo Pastor), "
               "Leandro N. Alem 0`, con la nota `Se jugo en cancha de El "
               "Porvenir`. El 1-0 es el marcador de nuestra fila.\n"
               "El otro de la Fecha 3 que se corre del lunes 7 al martes 8." + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2009-10 (Argentina)", jornada="Fecha 8",
        local="Ferrocarril Midland", visita="Villa D\u00e1lmine",
        dice="2009-10-03", debe="2009-10-05", fuente=_CARL_0910,
        porque="Carluccio: `05/10/2009 en Libertad: Ferrocarril Midland 0, Villa "
               "Dalmine 1 (Alberto Meinecke)`. El 0-1 es el marcador de nuestra "
               "fila.\n"
               "RSSSF lo pone el sabado 3 junto a otros siete; el 5 de octubre de "
               "2009 fue lunes." + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2009-10 (Argentina)", jornada="Fecha 9",
        local="Luj\u00e1n", visita="Barracas Bol\u00edvar",
        dice="2009-10-11", debe="2009-10-09", fuente=_CARL_0910,
        porque="Carluccio: `09/10/2009 en Lujan: Lujan 1 (Federico Quintana), "
               "Barracas Bolivar 0`, con la nota `Se jugo en el estadio Municipal "
               "de Lujan`. El 1-0 es el marcador de nuestra fila.\n"
               "TESTIGO CONTEMPORANEO. El blog Rumores del Ascenso publica el 11 "
               "de octubre de 2009 el post `ESTO YA FUE HISTORIA` con los "
               "resultados agrupados por dia: `PRIMERA C: VIERNES: SACACHISPAS 0 "
               "EXCURSIONISTAS 2 / TALLERES (RE) 0 BARRACAS CENTRAL 0 / LUJAN 1 "
               "BARRACAS BOLIVAR 0`. Los otros dos de esa lista YA los tenemos "
               "fechados el viernes 9, asi que el tercero es del mismo dia.\n"
               "Y ES EL UNICO DE LOS DIECIOCHO CON UNA FUENTE EN CONTRA: la "
               "fixture de AFA capturada el 8 de octubre lo anunciaba para el 11. "
               "Una fixture es un PLAN publicado antes; el listado de resultados "
               "es de despues, y ademas encaja con dos partidos que ya sabiamos "
               "del viernes.\n"
               "http://rumoresdelascenso.blogspot.com/2009/10/esto-ya-fue-historia.html" + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2009-10 (Argentina)", jornada="Fecha 11",
        local="General Lamadrid", visita="Barracas Bol\u00edvar",
        dice="2009-10-18", debe="2009-10-17", fuente=_CARL_0910,
        porque="Carluccio: `17/10/2009 en Villa Devoto: General Lamadrid 3 "
               "(Gaston Lezcano, Damian Gimenez y Lucas Tiedemann), Barracas "
               "Bolivar 0`. El 3-0 es el marcador de nuestra fila.\n"
               "RSSSF lo pone el domingo 18; el 17 de octubre de 2009 fue sabado, "
               "y RSSSF ya usa ese sabado para otros cinco partidos de la misma "
               "jornada." + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2009-10 (Argentina)", jornada="Fecha 12",
        local="El Porvenir", visita="Defensores Unidos",
        dice="2009-10-24", debe="2009-10-23", fuente=_CARL_0910,
        porque="Carluccio: `23/10/2009 en Gerli: El Porvenir 1 (Heber Leanios), "
               "Defensores Unidos 2 (Santiago Davio 2)`. El 1-2 es el marcador de "
               "nuestra fila.\n"
               "RSSSF lo pone el sabado 24 junto a otros seis; el 23 de octubre de "
               "2009 fue viernes, dia en que la Primera C abria la jornada." + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2009-10 (Argentina)", jornada="Fecha 13",
        local="San Miguel", visita="Leandro N. Alem",
        dice="2009-11-01", debe="2009-11-02", fuente=_CARL_0910,
        porque="Carluccio: `02/11/2009 en Los Polvorines: San Miguel 1 (Alejandro "
               "Maldonado), Leandro N. Alem 1 (Gustavo Romero)`. El 1-1 es el "
               "marcador de nuestra fila.\n"
               "Uno de los tres de la Fecha 13 que pasan del domingo 1 al lunes 2. "
               "RSSSF ya usa ese lunes para un partido de la misma jornada, asi "
               "que no esta inventando un dia: le faltan estos tres." + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2009-10 (Argentina)", jornada="Fecha 13",
        local="Deportivo Laferrere", visita="J. J. de Urquiza",
        dice="2009-11-01", debe="2009-11-02", fuente=_CARL_0910,
        porque="Carluccio: `02/11/2009 en Gregorio de Laferrere: Deportivo "
               "Laferrere 1 (Walter Garcete), Justo Jose de Urquiza 0`. El 1-0 es "
               "el marcador de nuestra fila.\n"
               "El segundo de los tres de la Fecha 13 que pasan al lunes 2." + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2009-10 (Argentina)", jornada="Fecha 13",
        local="Sacachispas", visita="Ferrocarril Midland",
        dice="2009-11-01", debe="2009-11-02", fuente=_CARL_0910,
        porque="Carluccio: `02/11/2009 en Villa Soldati: Sacachispas FC 1 (Javier "
               "Vargas), Ferrocarril Midland 1 (Miguel Mendoza)`. El 1-1 es el "
               "marcador de nuestra fila.\n"
               "El tercero de los tres de la Fecha 13 que pasan al lunes 2." + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2009-10 (Argentina)", jornada="Fecha 25",
        local="Argentino de Merlo", visita="Deportivo Laferrere",
        dice="2010-02-06", debe="2010-02-08", fuente=_CARL_0910,
        porque="Carluccio: `08/02/2010 en Merlo Norte: Argentino de Merlo 2 "
               "(Gonzalo Pavone 2), Deportivo Laferrere 1 (Jonathan Saban)`. El "
               "2-1 es el marcador de nuestra fila.\n"
               "RSSSF lo pone el sabado 6; el 8 de febrero de 2010 fue lunes, y "
               "RSSSF ya usa ese lunes para otros seis partidos de la jornada." + "\n" + _PC_CARLUCCIO),

    # ---- Primera C 2010-11 -------------------------------------------------
    Dia(pagina="Campeonato de Primera C 2010-11 (Argentina)", jornada="Fecha 13",
        local="Deportivo Laferrere", visita="Berazategui",
        dice="2010-10-18", debe="2010-10-19", fuente=_CARL_1011,
        porque="Carluccio: `19/10/2010 en Gregorio de Laferrere: Deportivo "
               "Laferrere 2 (Cristian Jeandet 2), Berazategui 1 (Juan C. "
               "Horvat)`. El 2-1 es el marcador de nuestra fila.\n"
               "RSSSF lo pone el lunes 18 junto a otros cinco; el 19 de octubre de "
               "2010 fue martes." + "\n" + _PC_CARLUCCIO),
    Dia(pagina="Campeonato de Primera C 2010-11 (Argentina)", jornada="Fecha 16",
        local="San Miguel", visita="Leandro N. Alem",
        dice="2011-02-23", debe="2011-02-22", fuente=_CARL_1011,
        porque="Carluccio: `22/02/2011 en Los Polvorines: San Miguel 1 (Francisco "
               "Luna), Leandro N. Alem 0`. El 1-0 es el marcador de nuestra "
               "fila.\n"
               "ES UN POSTERGADO, y eso lo hace mas facil de creer y no menos: los "
               "otros nueve partidos de la Fecha 16 se jugaron entre el 6 y el 8 "
               "de noviembre de 2010, y este quedo solo, ciento siete dias "
               "despues. Una fuente que copiara la fecha de la jornada nunca "
               "produciria eso; hay que tener el dato del partido." + "\n" + _PC_CARLUCCIO),
)


def dias(pagina: str) -> tuple:
    """Las correcciones de fecha declaradas para esa pagina."""
    return tuple(d for d in DIAS if d.pagina == pagina)


def corregir_fechas(ps: list, pagina: str) -> list[str]:
    """Aplica las `Dia` de esa pagina. Devuelve los avisos.

    Se llama DESPUES de todos los completadores: ver el docstring de `Dia`.
    """
    avisos = []
    for d in dias(pagina):
        candidatos = [p for p in ps if p.jornada == d.jornada and p.local == d.local
                      and p.visita == d.visita]
        if len(candidatos) != 1:
            avisos.append(f"la fecha corregida de {d.jornada} ({d.local} vs "
                          f"{d.visita}) engancha con {len(candidatos)} partidos y no "
                          f"se aplica: no identifica uno solo")
            continue
        p = candidatos[0]
        if p.fecha != d.dice:
            avisos.append(f"la fecha corregida de {d.jornada} ({d.local} vs "
                          f"{d.visita}) esperaba encontrar {d.dice} y la fila dice "
                          f"{p.fecha or 'nada'}: si la fuente se arreglo, sacala de "
                          f"fad/correcciones.py")
            continue
        p.fecha, p.fuente_fecha = d.debe, d.fuente
    return avisos


def fechados(pagina: str) -> set[tuple[str, str, str, str, str]]:
    """(jornada, local, visita, nuestra, otra) de los desacuerdos ya verificados.

    Se le pasa a `fechas.completar` igual que `arbitrados`, y por el mismo motivo:
    la funcion que arma el aviso no sabe de que pagina viene.
    """
    # Y las `Dia` entran con TRES campos y no con cinco. Un `Fechado` dice "de
    # este desacuerdo puntual ya sabemos"; una `Dia` dice algo mas fuerte, "la
    # fecha de este partido esta zanjada a mano", asi que calla cualquier
    # desacuerdo sobre esa fila y no solo el que la motivo. Tiene que ser asi: al
    # corregir la fecha, la fuente que la tenia mal pasa a discrepar con la nueva,
    # y ese aviso lo generaria la misma correccion que lo resuelve.
    return ({(f.jornada, f.local, f.visita, f.nuestra, f.otra) for f in FECHADOS
             if f.pagina == pagina}
            | {(d.jornada, d.local, d.visita) for d in DIAS if d.pagina == pagina})


def arbitrado(pagina: str, jornada: str, local: str, visita: str,
              gl: int, gv: int) -> tuple[int, int]:
    """El marcador que ese partido VA A TENER despues de `aplicar`.

    El gemelo de `renombrado` para la otra familia de correcciones, y existe
    por el mismo motivo: `sin_repetir` corre ANTES que `aplicar` --y tiene que
    correr antes, porque decide que se importa--, asi que sin esto el build
    sigue enfrentando "la pagina dice X y la otra fuente dice Y" sobre una fila
    que dos pasos mas abajo pasa a decir Y. Una notificacion que se vuelve
    falsa sola es peor que no tenerla.

    LOS NOMBRES QUE ENTRAN SON LOS DE DESPUES DEL ESPEJO, porque `aplicar`
    corre las `Correccion` primero y los `Marcador` despues, y por eso un
    `Marcador` se declara contra la fila ya dada vuelta. Llamarlo con los
    nombres crudos no engancha nada y devuelve el marcador sin tocar, que es
    lo correcto: no hay nada declarado para esa fila.

    No mira los penales a proposito. Los dos `Marcador` que existen para
    arreglar una tanda dejan `debe == dice` --el marcador no se mueve-- y esta
    funcion contesta sobre el marcador; quien la usa compara marcadores.
    """
    for m in MARCADORES:
        if (m.pagina == pagina and m.jornada == jornada
                and (m.local, m.visita) == (local, visita)
                and m.dice == (gl, gv)):
            return m.debe
    return gl, gv


def aplicar(ps: list, pagina: str) -> tuple[int, list[str]]:
    """Corrige los partidos de `pagina`. Devuelve (cuantas se aplicaron, avisos).

    Se llama DESPUES de canonizar los nombres: `dice` y `debe` estan en canonico,
    asi que una correccion no se rompe porque la pagina cambie como escribe un
    club -- para eso estan los alias.
    """
    aplicadas, avisos = 0, []
    # UNA CORRECCION NO PUEDE CAER SOBRE UNA FILA QUE OTRA YA CAMBIO. Sin esto, dos
    # espejos de la misma llave se pisan: al dar vuelta la IDA queda escrita igual
    # que la vuelta --mismo par, mismo marcador, y en una llave que termino empatada
    # las dos patas son identicas--, asi que la correccion de la vuelta encuentra
    # DOS candidatos y se niega a aplicarse, con razon. Es el caso de
    # `Ramón Santamarina 2-2 Racing (O)` y de `Talleres (C) 1-1 Racing (C)` en la
    # Cuarta fase del Argentino A 2011-12.
    #
    # No se afloja la regla de "uno solo": se le saca de la vista lo que ya no es
    # candidato. Cada correccion consume una fila y ninguna otra la vuelve a mirar.
    tocadas: set[int] = set()
    for c in CORRECCIONES:
        if c.pagina != pagina:
            continue
        local, visita, gl, gv = c.dice
        candidatos = [p for p in ps
                      if id(p) not in tocadas
                      and p.jornada == c.jornada and p.local == local
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
        # SI LA CORRECCION ES UN ESPEJO, LOS GOLES VAN CON LOS CLUBES. `Correccion`
        # sirve para dos cosas distintas y solo una de ellas mueve el marcador:
        #
        #   * ARREGLAR LA IDENTIDAD de un club --"Unión" era el de Mar del Plata y
        #     no el de Sunchales--: el partido es el mismo, quien jugo en su casa
        #     es el mismo, y los goles NO se tocan. Son dieciseis de las
        #     diecinueve que hay.
        #   * ESPEJAR LA LOCALIA: los dos clubes estan del lado equivocado. Ahi el
        #     resultado no cambia, cambia como se escribe, y `2-3` visto desde el
        #     otro lado es `3-2`. Mover los nombres y dejar los goles convertiria
        #     una victoria en una derrota.
        #
        # No se notaba porque los tres espejos que habia son EMPATES, donde dar
        # vuelta el marcador no hace nada. El primero que no lo es --la ida de la
        # Tercera Fase del Argentino A 2010-11, que la pagina anota `Unión (MdP)
        # 2-3 Desamparados`-- habria quedado como `Desamparados 2-3 Unión (MdP)`,
        # o sea con el ganador cambiado.
        #
        # Los dos casos se distinguen sin ambiguedad: si `debe` es exactamente el
        # par de `dice` dado vuelta, es un espejo.
        if c.debe == (visita, local):
            candidatos[0].goles_local, candidatos[0].goles_visita = gv, gl
        candidatos[0].local, candidatos[0].visita = c.debe
        tocadas.add(id(candidatos[0]))
        aplicadas += 1

    for m in MARCADORES:
        # `debe == dice` y sin penales que tocar: la pagina ya esta bien y de la
        # otra fuente se toma solo la FECHA.
        if m.pagina != pagina or (m.debe == m.dice and m.penales_debe is None
                                  and m.penales_dice is None):
            continue
        candidatos = [p for p in ps
                      if p.jornada == m.jornada and p.local == m.local
                      and p.visita == m.visita
                      and (p.goles_local, p.goles_visita) == m.dice
                      and (m.penales_dice is None
                           or (p.penales_local, p.penales_visita) == m.penales_dice)]
        if len(candidatos) != 1:
            avisos.append(f"el marcador arbitrado de {m.jornada} ({m.local} vs "
                          f"{m.visita}) engancha con {len(candidatos)} partidos y no se "
                          f"aplica: si la fuente se corrigio, sacalo de fad/correcciones.py")
            continue
        candidatos[0].goles_local, candidatos[0].goles_visita = m.debe
        if m.penales_debe is not None:
            candidatos[0].penales_local, candidatos[0].penales_visita = m.penales_debe
        elif m.debe[0] != m.debe[1]:
            # El marcador corregido no es empate: la tanda no pudo existir.
            candidatos[0].penales_local = candidatos[0].penales_visita = None
        aplicadas += 1

    # Los divididos se SACAN. Antes que todo lo demas, porque una fila que no
    # deberia existir no tiene por que pasar por los otros arreglos.
    for div in DIVIDIDOS:
        if div.pagina != pagina:
            continue
        # `dice=None` quiere decir que la fila NO llega hasta aca -- su celda no se
        # puede leer como marcador --, asi que no hay nada que sacar. No es "sacar
        # cualquiera": leerlo asi borro un Independiente (N) - Deportivo Roca de la
        # Primera fase que no tenia nada que ver, porque los mismos dos clubes
        # juegan varias veces en la misma pagina.
        if div.dice is None:
            continue
        sobran = [p for p in ps if p.local == div.local and p.visita == div.visita
                  and (p.goles_local, p.goles_visita) == div.dice]
        if not sobran:
            avisos.append(f"el partido dividido {div.local} vs {div.visita} ya no "
                          f"esta en la grilla: si arreglaron la pagina, sacalo de "
                          f"fad/correcciones.py")
            continue
        for p in sobran:
            ps.remove(p)
        aplicadas += len(sobran)

    # Los faltantes van al final de todo: no arreglan una fila, agregan una, y
    # lo que agregan tiene que estar ya en canonico y ya sin homonimos que
    # resolver. Antes de las otras correcciones, ademas, se expondria a que una
    # de ellas lo enganche sin querer.
    for fal in FALTANTES:
        if fal.pagina != pagina:
            continue
        if any(p.jornada == fal.jornada and p.local == fal.local
               and p.visita == fal.visita for p in ps):
            avisos.append(f"el partido faltante de {fal.jornada} ({fal.local} vs "
                          f"{fal.visita}) ya se lee de la pagina: la arreglaron, "
                          f"sacalo de fad/correcciones.py antes de que quede "
                          f"duplicado")
            continue
        # El contexto se hereda de un hermano de la MISMA jornada en vez de
        # escribirse a mano: torneo, fase y zona son de la ronda, no del partido,
        # y copiarlos evita que esta fila sea la unica del torneo que dice otra
        # cosa. Sin hermano no se agrega: seria una fila colgada de la nada.
        hermanos = [p for p in ps if p.jornada == fal.jornada]
        if not hermanos:
            avisos.append(f"el partido faltante de {fal.jornada} ({fal.local} vs "
                          f"{fal.visita}) no tiene ningun hermano en su jornada de "
                          f"donde heredar fase y zona, asi que no se agrega")
            continue
        h = hermanos[0]
        ps.append(replace(h, fecha=fal.fecha, hora=fal.hora, local=fal.local,
                          visita=fal.visita, goles_local=fal.goles[0],
                          goles_visita=fal.goles[1], estadio=fal.estadio,
                          penales_local=(fal.penales or (None, None))[0],
                          penales_visita=(fal.penales or (None, None))[1],
                          local_art="", visita_art="", fecha_cruda=""))
        aplicadas += 1

    # Los homonimos van DESPUES de `CORRECCIONES`, y no es indistinto: una
    # correccion se identifica por como escribe la pagina, o sea por el nombre
    # equivocado. Si el homonimo lo renombrara antes, la correccion ya no
    # engancharia con su fila y se apagaria sola.
    for h in HOMONIMOS:
        if h.pagina != pagina:
            continue
        for p in ps:
            if p.local == h.dice:
                p.local = h.debe
                aplicadas += 1
            if p.visita == h.dice:
                p.visita = h.debe
                aplicadas += 1
    # Aca NO va el aviso de "ya no engancha", que los otros tres tipos si tienen:
    # un homonimo puede tocar solo la tabla de posiciones -- el Argentino A
    # 2005-06 escribe "Juventud Unida" en la tabla y el nombre entero en la
    # grilla -- y desde aca los partidos se ven pero la tabla no. El control de
    # vigencia es `homonimos_huerfanos`, que se llama con los dos lados juntos.

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

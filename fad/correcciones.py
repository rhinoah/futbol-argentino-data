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
        porque="la nota, que cuelga de la tabla y no de la fila, dice: El partido "
               "se interrumpio en el minuto 90 cuando empataban 2 a 2. Luego se "
               "resolvio darles por perdido el encuentro a ambos equipos por 1 a 0. "
               "Los dos perdieron, y una fila tiene que tener un ganador o un "
               "empate. Salia en sin-fecha/ publicando el 2-2 de la cancha, que no "
               "es el resultado de ninguno de los dos",
    ),
    Dividido(
        pagina="Torneo Federal A 2018-19",
        local="Independiente (N)", visita="Deportivo Roca", dice=None,
        porque="la celda dice PP - PP y la nota que el partido finalizo 4 a 1 y se le "
               "dio por perdido a ambos equipos. Es el unico de los cinco que no "
               "entraba ya, porque su celda no se puede leer como marcador",
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
        local="Godoy Cruz", visita="Deportivo Armenio", goles=(0, 0),
        penales=(6, 5), fecha="2019-03-23", hora="", estadio="Juan Domingo Perón",
        porque="la fila esta entera y mal escrita: le sobra una llave y le falta "
               "el salto de linea, `|-bgcolor=#F5FAFF}|align=center| 23 de marzo "
               "||...`. Con los cinco campos en el mismo renglon, la primera celda "
               "-- la fecha -- se pierde adentro de lo que `_partir` descarta como "
               "atributos de la fila, quedan cuatro y la fila no llega al minimo. "
               "Sus vecinas de la misma tabla son identicas y con el salto puesto. "
               "Aflojar el corte de filas para todo el corpus por una sola es peor "
               "el remedio: es el ultimo de los 240 partidos que faltaban en las "
               "copas y el unico que ningun arreglo de parser alcanza. "
               "LA TANDA VA AL REVES QUE LA FILA, y es una decision: la fila pone "
               "en negrita a Armenio y escribe (5) 0 - 0 (6), o sea que Armenio "
               "gano -- la pagina usa esa convencion en sus 18 filas legibles sin "
               "excepcion --, pero el cuadro marca a Godoy Cruz con su (p) de "
               "penales en RD2 y RD3, y la grilla lo tiene JUGANDO dieciseisavos "
               "(14/07 vs Huracan) y octavos (18/09 vs River). Tres testigos "
               "independientes contra la negrita de la unica fila de la pagina que "
               "esta mal escrita. Se toman los numeros de la fila y el orden de los "
               "otros tres. El 0-0 de los noventa minutos no lo discute nadie",
        testigos=(
            "LA CELDA MISMA: el 0-0 y los numeros de la tanda estan escritos en "
            "la fila, intactos y sin ambiguedad (`(5) 0 - 0 (6)`). Lo que la fila "
            "no puede sostener es a QUIEN le toca cada numero, porque es la unica "
            "de la pagina con el markup roto",
            "EL CUADRO Y LAS RONDAS SIGUIENTES: el bracket marca a Godoy Cruz con "
            "su `(p)` de penales en RD2 y RD3, y la grilla lo tiene jugando "
            "dieciseisavos (14/07 vs Huracan) y octavos (18/09 vs River). Un club "
            "que perdio la serie no juega las dos rondas que siguen",
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


HOMONIMOS: tuple[Homonimo, ...] = (
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
    return [f"el homonimo {h.dice!r} -> {h.debe!r} no engancha con nada: la "
            f"pagina ya no escribe ese nombre, ni en los partidos ni en la "
            f"tabla. Si la arreglaron, sacalo de fad/correcciones.py"
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


REVISADOS: tuple[Revisado, ...] = (
    Revisado(
        pagina="Campeonato de Primera B Nacional 2012-13", club="Atlético Tucumán",
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
        pagina="Campeonato de Primera B Nacional 2012-13", club="Olimpo",
        porque="La otra mitad del par con Atletico Tucuman. Mismo partido verificado "
               "con La Gaceta y el compilado de goleadores, mismo desenlace: la grilla "
               "tiene razon. Entrada propia porque el aviso se emite por club."),
    Revisado(
        pagina="Campeonato de Primera B Nacional 2013-14", club="Talleres (C)",
        porque="El 1-4 de la grilla esta bien y el arreglo que pedia la aritmetica "
               "(1-8) era la senal de que el problema estaba del otro lado: cuatro "
               "goles de diferencia no son un digito mal transcripto. La cronica da "
               "los cinco goles con su minuto -- Juan Sanchez Sotelo de penal a los 35 "
               "para Talleres; Sproat a los 32, Guerrero y los demas para Brown --. La "
               "equivocada es la fila de la tabla."),
    Revisado(
        pagina="Campeonato de Primera B Nacional 2013-14", club="Brown de Adrogué",
        porque="La otra mitad del par con Talleres (C): mismo partido, misma cronica "
               "con los cinco goleadores, mismo desenlace. Entrada propia porque el "
               "aviso es por club."),
    Revisado(
        pagina="Campeonato de Primera B Nacional 2014", club="Instituto",
        porque="El 1-2 de la grilla esta bien. La cronica da los tres goles con su "
               "minuto: Gotti a los 30 y Bernardi a los 61 para Instituto, Pinero da "
               "Silva a los 66 para Guarani. El 0-2 que pedia la tabla borraria un gol "
               "que la cronica nombra con su autor. La equivocada es la tabla."),
    Revisado(
        pagina="Campeonato de Primera B Nacional 2014", club="Guaraní Antonio Franco",
        porque="La otra mitad del par con Instituto: el gol que la tabla querria "
               "borrar es justamente el suyo, el de Pinero da Silva a los 66. Entrada "
               "propia porque el aviso es por club."),
    Revisado(
        pagina="Campeonato de Primera C 2015 (Argentina)", club="Central Córdoba (R)",
        porque="El 0-2 de la grilla esta bien: los dos goles son de Central Cordoba de "
               "Rosario, Cristian Vella a los 7 y Federico Ferrari a los 87, los dos "
               "con su minuto en la cronica. El 0-1 que pedia la tabla tendria que "
               "borrar uno de esos dos. La equivocada es la tabla."),
    Revisado(
        pagina="Campeonato de Primera C 2015 (Argentina)", club="Sacachispas",
        porque="La otra mitad del par con Central Cordoba (R): mismo partido, misma "
               "cronica con los dos goleadores. Entrada propia porque el aviso es por "
               "club."),
    Revisado(
        pagina="Torneo Argentino A 2010-11", club="Sportivo Belgrano",
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
        pagina="Torneo Argentino A 2010-11", club="Central Norte (S)",
        porque="La otra mitad del par con Sportivo Belgrano, en el partido suspendido "
               "y homologado 0-2. Misma cronica de La Voz del Interior, mismo "
               "desenlace. Entrada propia porque el aviso es por club."),
    Revisado(
        pagina="Campeonato de Primera B Nacional 2009-10", club="Platense",
        porque="Se desvia SOLO, y eso alcanza para cerrarlo sin fuente de afuera. Un "
               "marcador mal leido toca siempre a dos clubes, con deltas espejados; "
               "aca ningun otro club de la tabla se desvia y ninguno de los rivales de "
               "Platense quedo fuera del cruce -- la tabla y la grilla les cuentan a "
               "todos los mismos partidos --, asi que no hay ningun partido que pueda "
               "explicarlo. La equivocada es la fila de la tabla."),
    Revisado(
        pagina="Anexo:Torneo Final 2013 (Argentina)", club="Unión",
        porque="Se desvia solo y ninguno de sus rivales quedo fuera del cruce, asi que "
               "ningun partido puede explicarlo: un marcador mal leido movería a dos "
               "clubes y aca se mueve uno. La equivocada es la fila de la tabla, no la "
               "grilla. Es la misma prueba interna que cierra a Platense en el B "
               "Nacional 2009-10."),
    Revisado(
        pagina="Copa de la Liga Profesional 2023", club="Racing Club",
        porque="Se desvia solo en su zona y ninguno de sus rivales quedo fuera del "
               "cruce. Sin un segundo club desviado en espejo no hay partido que "
               "explique la diferencia, asi que la fila de la tabla es la que esta "
               "mal. Prueba interna, no hace falta fuente externa."),
    Revisado(
        pagina="Campeonato de Primera C 2024 (Argentina)", club="J. J. de Urquiza",
        porque="Se desvia solo en el Torneo Clausura y todos sus rivales son "
               "comparables. Ningun marcador mal leido puede mover a un club sin mover "
               "a otro, asi que la equivocada es la fila de la tabla."),
    Revisado(
        pagina="Torneo Federal A 2016-17", club="Gutiérrez",
        porque="Se desvia solo en la primera fase y ninguno de sus rivales quedo fuera "
               "del cruce. Su delta es ademas de dos goles en cada columna, que "
               "necesitaria dos partidos mal leidos y por lo tanto hasta cuatro clubes "
               "desviados; no hay ninguno mas. La equivocada es la fila de la tabla."),
    Revisado(
        pagina="Torneo Federal A 2025", club="Cipolletti",
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
        pagina="Torneo Federal A 2025", club="Villa Mitre",
        porque="La otra mitad del par con Cipolletti: sus deltas son los de aquel. "
               "Las mismas dos ruedas verificadas con la prensa de Bahia Blanca y de "
               "Cipolletti, mismo desenlace. Va como entrada propia porque el aviso "
               "se emite POR CLUB, y callar uno solo dejaria el par denunciado a "
               "medias."),
    Revisado(
        pagina="Torneo Federal A 2025", club="Círculo Deportivo",
        porque="Las dos ruedas con Sol de Mayo verificadas y las dos estan bien. La "
               "fecha 6 (Circulo Deportivo 1-0, gol de Imanol Iriberri de penal a "
               "los 31) la cuentan TRES diarios de las dos puntas -- Rio Negro y "
               "NoticiasNet desde Viedma, El Marplatense desde Otamendi --, cada uno "
               "con el goleador y su minuto. La fecha 15 (Sol de Mayo 4-1) tambien "
               "queda confirmada. La equivocada es la tabla."),
    Revisado(
        pagina="Torneo Federal A 2025", club="Sol de Mayo (V)",
        porque="La otra mitad del par con Circulo Deportivo: mismas dos ruedas, "
               "mismas fuentes de las dos ciudades, mismo desenlace. Entrada propia "
               "porque el aviso es por club."),
    Revisado(
        pagina="Campeonato de Primera Nacional 2025", club="Defensores de Belgrano",
        porque="Este no necesita fuente de afuera porque la prueba es interna y "
               "cierra sola. La tabla dice 12-13-9 y la grilla da 12-12-10 -- un "
               "empate menos y una derrota mas -- pero los GOLES coinciden exacto, "
               "GF y GC. Un marcador mal leido mueve siempre los goles: cambiarle "
               "un digito a un partido le toca el GF o el GC a los dos clubes. Un "
               "resultado corrido con los goles intactos no lo puede explicar "
               "ningun partido, asi que lo que esta mal es el G-E-P de la fila y "
               "no hay a donde ir a buscar. Ademas no aparea con nadie: es el "
               "unico club desviado de su zona."),
)


def revisado(pagina: str, club: str) -> Revisado | None:
    """La verificacion que cierra el desvio de ese club, si alguien la hizo."""
    for r in REVISADOS:
        if r.pagina == pagina and r.club == club:
            return r
    return None


def revisados_huerfanos(pagina: str, desviados: set[str]) -> list[str]:
    """Los `Revisado` de esta pagina que ya no enganchan con ningun desvio.

    Un `Revisado` silencia un aviso, asi que tiene que caducar solo. Si la pagina
    se corrigio -- o si le cambiaron la tabla --, la verificacion que sostiene
    esta entrada hablaba de otra cosa y hay que rehacerla. Sin esto, una entrada
    vieja sigue tapando un desvio nuevo del mismo club y nadie se entera.
    """
    fuera = []
    for r in REVISADOS:
        if r.pagina != pagina or r.club in desviados:
            continue
        fuera.append(
            f"la verificacion de {r.club} ya no engancha con ningun desvio: o la "
            f"pagina se arreglo, o le cambiaron la tabla. Sacala de "
            f"fad/correcciones.py, porque mientras siga ahi puede estar tapando "
            f"un desvio nuevo del mismo club")
    return fuera


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

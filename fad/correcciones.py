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
    return aplicadas, avisos

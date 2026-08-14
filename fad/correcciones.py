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


CORRECCIONES: tuple[Correccion, ...] = (
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
    return aplicadas, avisos

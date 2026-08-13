#!/usr/bin/env python3
"""
fad/torneos.py
==============
Que paginas de Wikipedia componen el dataset.

Es una tabla explicita y no un descubrimiento automatico. Se puede adivinar el
titulo de una temporada por patron ("Anexo:Torneo Apertura {anio} (Argentina)"),
pero el futbol argentino le cambio el nombre y el formato al campeonato casi
todos los anios: Inicial/Final, Transicion, Superliga, Copa de la Liga, Apertura
/Clausura otra vez. No hay patron que sobreviva a eso, y una lista escrita a mano
falla al agregar una temporada — no en silencio, que es lo que importa.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Torneo:
    pagina: str          # titulo exacto en es.wikipedia.org
    torneo: str          # va a la columna `tournament`
    temporada: int       # va a la columna `season`

    @property
    def url(self) -> str:
        return "https://es.wikipedia.org/wiki/" + self.pagina.replace(" ", "_")


PRIMERA = [
    Torneo("Anexo:Torneo Apertura 2026 (Argentina)", "Primera Division - Apertura", 2026),
    Torneo("Anexo:Torneo Clausura 2026 (Argentina)", "Primera Division - Clausura", 2026),
]

TODOS = PRIMERA

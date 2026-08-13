#!/usr/bin/env python3
"""
fad/dataset.py
==============
El CSV: esquema, escritura y lectura.

El esquema sigue de cerca al de martj42/international_results, que es el que ya
usa medio mundo para selecciones — `date, home_team, away_team, home_score,
away_score, tournament` estan igual a proposito, para que el codigo que ya lee
aquel dataset lea este con cambios minimos. Lo agregado es lo que el futbol de
clubes necesita y aquel no tiene: penales, zona, jornada y temporada.

DOS DECISIONES QUE PARECEN DETALLES Y NO LO SON
-----------------------------------------------
1. **Las filas salen ordenadas.** Este archivo se va a regenerar solo todos los
   dias y a commitear. Si el orden depende de como Wikipedia acomodo las tablas,
   cada commit es un diff ilegible de miles de lineas movidas y no se ve que
   cambio de verdad. Ordenado por fecha, el diff de un dia son las filas de ese
   dia.
2. **No hay columna `neutral`.** El modelo la quiere (la localia vale), pero de
   esta fuente no se puede deducir sin un padron de estadios, y una columna
   booleana inventada es peor que una columna ausente: quien la consuma no tiene
   como saber que esta mal. Se emite `venue`, que es el dato que si esta, y
   `neutral` se derivara cuando exista el padron.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path

from fad.parser import Partido

COLUMNAS = [
    "date", "time", "home_team", "away_team", "home_score", "away_score",
    "home_pens", "away_pens", "tournament", "season", "phase", "group",
    "matchday", "venue", "source",
]


def a_fila(p: Partido, torneo: str, temporada: int, fuente: str) -> dict:
    return {
        "date": p.fecha, "time": p.hora,
        "home_team": p.local, "away_team": p.visita,
        "home_score": p.goles_local, "away_score": p.goles_visita,
        # los penales van tal cual: el modulo csv escribe None como campo vacio
        "home_pens": p.penales_local,
        "away_pens": p.penales_visita,
        "tournament": torneo, "season": temporada,
        "phase": p.fase, "group": p.zona, "matchday": p.jornada,
        "venue": p.estadio, "source": fuente,
    }


def _orden(fila: dict) -> tuple:
    return (fila["date"], fila["time"], fila["home_team"], fila["away_team"])


def escribir(filas: list[dict], destino: Path) -> int:
    """Escribe el CSV ordenado, de forma atomica. Devuelve cuantas filas."""
    filas = sorted(filas, key=_orden)
    destino.parent.mkdir(parents=True, exist_ok=True)
    tmp = destino.with_suffix(destino.suffix + ".tmp")
    # newline="" es obligatorio en Windows: sin eso el modulo csv escribe \r\r\n
    with tmp.open("w", encoding="utf-8", newline="") as f:
        w = csv.DictWriter(f, fieldnames=COLUMNAS, extrasaction="raise")
        w.writeheader()
        w.writerows(filas)
    os.replace(tmp, destino)          # o esta el viejo entero o el nuevo entero
    return len(filas)


def leer(origen: Path) -> list[dict]:
    with origen.open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    if filas and list(filas[0]) != COLUMNAS:
        raise ValueError(f"{origen.name}: el encabezado no es el esperado.\n"
                         f"  esperado: {COLUMNAS}\n  encontrado: {list(filas[0])}")
    return filas

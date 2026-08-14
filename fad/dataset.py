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
2. **`neutral` sale del reglamento de la competencia, no del estadio.** La Copa
   Argentina se juega a partido unico en cancha neutral y su pagina lo dice ronda
   por ronda, asi que ahi el dato se afirma con fundamento. En las ligas es
   `false` con el alcance que declara el README: el partido se jugo donde dice el
   fixture. NO detecta mudanzas puntuales -- un partido de liga que se muda de
   cancha sigue figurando `false`. Se prefirio decir eso y documentarlo antes que
   deducir la localia comparando el estadio contra un padron que todavia no
   existe.
"""
from __future__ import annotations

import csv
import os
from pathlib import Path

from fad.parser import Partido

COLUMNAS = [
    "date", "time", "home_team", "away_team", "home_score", "away_score",
    "home_pens", "away_pens", "tournament", "season", "phase", "group",
    "matchday", "venue", "neutral", "source",
]


def a_fila(p: Partido, torneo: str, temporada: int, fuente: str,
           neutral: bool = False) -> dict:
    return {
        "date": p.fecha, "time": p.hora,
        "home_team": p.local, "away_team": p.visita,
        "home_score": p.goles_local, "away_score": p.goles_visita,
        # los penales van tal cual: el modulo csv escribe None como campo vacio
        "home_pens": p.penales_local,
        "away_pens": p.penales_visita,
        "tournament": torneo, "season": temporada,
        "phase": p.fase, "group": p.zona, "matchday": p.jornada,
        "venue": p.estadio, "neutral": str(neutral).lower(),
        # Si la fecha vino de otra fuente, las DOS quedan nombradas. La fila es
        # de Wikipedia salvo ese campo, y asi se lee.
        "source": f"{fuente} + {p.fuente_fecha}" if p.fuente_fecha else fuente,
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
        # Final de linea EXPLICITO, y no el que csv elige por defecto (CRLF).
        # Este archivo lo escriben DOS maquinas -- la de quien desarrolla y el
        # runner de Linux que corre todos los dias -- y si cada una usa uno
        # distinto, git ve las 26 000 filas cambiadas aunque no haya cambiado un
        # solo dato. El primer commit automatico fue exactamente eso:
        # "+22271 -22271" y ninguna diferencia real.
        w = csv.DictWriter(f, fieldnames=COLUMNAS, extrasaction="raise",
                           lineterminator="\n")
        w.writeheader()
        w.writerows(filas)
    os.replace(tmp, destino)          # o esta el viejo entero o el nuevo entero
    return len(filas)


def regresiones(nuevas: list[dict], anteriores: list[dict]) -> list[str]:
    """Torneos que perdieron partidos respecto del CSV que ya estaba.

    Existe por el modo de fallar de una tarea automatica, que no es explotar. Si
    manana Wikipedia reordena una pagina y el parser saca 40 partidos donde habia
    240, los 40 pueden ser correctos y coherentes entre si: ningun chequeo de
    `validar` los ve mal, porque mirados solos estan bien. Lo unico que delata
    esa perdida es compararla contra lo de ayer.

    Se cuenta POR TORNEO y no por partido: durante un torneo en curso los
    partidos se reprograman todo el tiempo y cambian de fecha, asi que
    compararlos uno a uno da bajas y altas todos los dias. La cantidad, en
    cambio, solo baja cuando se perdio algo de verdad.
    """
    def por_torneo(filas):
        cuenta: dict[tuple, int] = {}
        for f in filas:
            # `str(...)` no es decorativo: las filas recien armadas traen
            # `season` como entero y las leidas del CSV como texto, asi que
            # ("Primera Division", 2016) y ("Primera Division", "2016") no se
            # cruzaban. Con eso, TODOS los torneos figuraban desaparecidos y la
            # guarda frenaba cada build. Un chequeo que salta siempre es igual de
            # inutil que uno que no salta nunca, y encima parece que anda.
            clave = (f["tournament"], str(f["season"]))
            cuenta[clave] = cuenta.get(clave, 0) + 1
        return cuenta

    antes, ahora = por_torneo(anteriores), por_torneo(nuevas)
    avisos = []
    for clave, cuantos in sorted(antes.items()):
        tenia_ahora = ahora.get(clave, 0)
        if tenia_ahora < cuantos:
            torneo, temporada = clave
            avisos.append(f"{torneo} {temporada}: tenia {cuantos} partidos y ahora "
                          f"{tenia_ahora}" + ("  (DESAPARECIO)" if not tenia_ahora else ""))
    return avisos


PATRON = "partidos-*.csv"


def archivo_de(temporada) -> str:
    return f"partidos-{temporada}.csv"


def escribir_por_temporada(filas: list[dict], carpeta: Path) -> dict[str, int]:
    """Un archivo por temporada. Devuelve {archivo: filas} de los que CAMBIARON.

    Partido en varios archivos y no en uno solo porque una temporada terminada no
    se toca nunca mas: 2004 quedo como quedo. Un archivo que no se reescribe no
    se puede corromper -- hoy, un bug al escribir se llevaba puesto el historico
    entero aunque nadie lo hubiera reparseado -- y el diff diario pasa a tocar un
    solo archivo, el del anio en curso, en vez de las 27 000 filas.

    Se reescribe solo el que cambio de contenido. Eso es lo que hace que git no
    vea nada cuando no paso nada.
    """
    por_anio: dict[str, list[dict]] = {}
    for f in filas:
        por_anio.setdefault(str(f["season"]), []).append(f)

    cambiados = {}
    for temporada, suyas in sorted(por_anio.items()):
        destino = carpeta / archivo_de(temporada)
        nuevo = _serializar(sorted(suyas, key=_orden))
        if destino.exists() and destino.read_bytes() == nuevo:
            continue
        carpeta.mkdir(parents=True, exist_ok=True)
        tmp = destino.with_suffix(destino.suffix + ".tmp")
        tmp.write_bytes(nuevo)
        os.replace(tmp, destino)
        cambiados[destino.name] = len(suyas)
    return cambiados


def leer_carpeta(carpeta: Path) -> list[dict]:
    """Todas las temporadas juntas, en orden."""
    filas = [f for archivo in sorted(carpeta.glob(PATRON)) for f in leer(archivo)]
    return sorted(filas, key=_orden)


def _serializar(filas: list[dict]) -> bytes:
    import io
    buf = io.StringIO(newline="")
    w = csv.DictWriter(buf, fieldnames=COLUMNAS, extrasaction="raise",
                       lineterminator="\n")
    w.writeheader()
    w.writerows(filas)
    return buf.getvalue().encode("utf-8")


def read_anterior(origen: Path) -> list[dict]:
    """El CSV que ya estaba, o vacio si es la primera vez.

    Un clon nuevo no tiene contra que comparar, y eso no es un error.
    """
    return leer(origen) if origen.exists() else []


def leer(origen: Path) -> list[dict]:
    with origen.open(encoding="utf-8", newline="") as f:
        filas = list(csv.DictReader(f))
    if filas and list(filas[0]) != COLUMNAS:
        raise ValueError(f"{origen.name}: el encabezado no es el esperado.\n"
                         f"  esperado: {COLUMNAS}\n  encontrado: {list(filas[0])}")
    return filas

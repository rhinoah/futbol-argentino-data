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
import re
import unicodedata
from collections import Counter
from pathlib import Path

from fad.parser import Partido

COLUMNAS = [
    "date", "time", "home_team", "away_team", "home_score", "away_score",
    "home_pens", "away_pens", "tournament", "season", "phase", "group",
    "matchday", "venue", "neutral", "source",
]


# Lo que separa las dos fuentes en `source` cuando la fila usa las dos. Es una
# constante y no un literal suelto porque hay que ESCRIBIRLO y despues volver a
# LEERLO: `build.py` agrupa las filas guardadas por su pagina para reusar los
# torneos ya terminados, y si lee la cadena entera no encuentra ninguna.
SEPARADOR = " + "


def pagina_de(fila) -> str:
    """La URL de Wikipedia de una fila, sin el credito de la segunda fuente.

    Existe por un bug que no rompia nada visible: los cuatro torneos cuya fecha
    viene de una segunda fuente llevan un `source` compuesto, y el reuso los
    buscaba por la URL pelada. No los encontraba NUNCA, asi que se reparseaban
    todos los dias y se le volvia a pedir la pagina al sitio de terceros -- justo
    lo que el `cerrado=True` estaba puesto para evitar. Y como el sitio hoy
    contesta 403, el build terminaba con esas cuatro temporadas en cero.
    """
    return fila["source"].split(SEPARADOR, 1)[0]


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
        "source": fuente + SEPARADOR + p.fuente_fecha if p.fuente_fecha else fuente,
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


_RUIDO_CLUB = {"club", "atletico", "atlantico", "social", "deportivo", "sportivo",
               "asociacion", "de", "del", "la", "el", "y", "los", "las"}


def _nucleo(nombre: str) -> str:
    """El nombre sin el desambiguador, que es lo que dos clubes confundibles comparten.

    "Estudiantes (LP)" y "Estudiantes (BA)" son el mismo nucleo; "Racing Club" y
    "Racing (C)" tambien, porque uno arranca con el otro.
    """
    s = unicodedata.normalize("NFKD", nombre).encode("ascii", "ignore").decode().lower()
    s = re.sub(r"\(.*?\)", " ", s)
    s = re.sub(r"[^a-z0-9 ]+", " ", s)
    return " ".join(s.split())


def _confundibles(a: str, b: str) -> bool:
    """Si los dos nombres podrian ser el mismo club escrito de dos formas."""
    x, y = _nucleo(a), _nucleo(b)
    if not x or not y:
        return False
    if x == y:
        return True
    return (x.startswith(y + " ") or y.startswith(x + " ")
            or x.endswith(" " + y) or y.endswith(" " + x))


def casas_compartidas(filas: list[dict]) -> list[str]:
    """Dos clubes de nombre confundible que juegan de local en la misma cancha.

    Es la contracara de `regresiones`: los dos miran el dataset ENTERO porque lo
    que buscan es invisible desde una pagina sola. Un club mal atribuido no rompe
    ninguna regla del fixture -- juega sus partidos, gana y pierde, no se repite
    en una fecha --, asi que ningun chequeo de `validar` lo puede ver. Y adentro
    de su pagina es perfectamente coherente: el falso "Estudiantes (LP)" de la
    Primera B 2015 jugaba SIEMPRE en Ciudad de Caseros. La mentira solo se ve
    comparando contra el resto.

    La cancha es el testigo, y el dataset ya la traia. Los dos errores de
    atribucion que apareceron en este repo se ven de una:

        Ciudad de Caseros   Estudiantes (BA) (248)  vs  Estudiantes (LP) (21)
        Miguel Sancho       Racing Club (119)       vs  Racing (C) (19)

    Se compara la cancha por cadena EXACTA a proposito. Intentar unificar
    "Coloso Marcelo Bielsa" con "Coloso del Parque", o las tres grafias de
    Kolbowsky, es un pozo sin fondo y no hace falta: dos clubes distintos que
    aparecen bajo el MISMO string son sospechosos justamente porque comparten la
    grafia, que es lo que pasa cuando en realidad son uno.

    Lo que deja el aviso casi sin ruido es la condicion de los nombres.
    Compartir estadio es normal -- Argentinos y Chacarita, los municipales de
    provincia --, pero compartirlo ADEMAS de llamarse igual es la firma del
    error. Medido sobre el dataset: 8 avisos sin esa condicion, 2 con ella, y los
    2 eran los dos bugs.

    No es grave y no frena el build: un club puede alquilar la cancha de otro, y
    de hecho pasa. Lo que dice el aviso es "mira esto", no "esto esta mal".
    """
    de_local: dict[str, Counter] = {}
    for f in filas:
        if str(f.get("neutral", "")).lower() == "true" or not str(f.get("venue", "")).strip():
            continue
        de_local.setdefault(str(f["venue"]).strip(), Counter())[f["home_team"]] += 1
    avisos = []
    for cancha, clubes in sorted(de_local.items()):
        nombres = sorted(clubes)
        for i, a in enumerate(nombres):
            for b in nombres[i + 1:]:
                if _confundibles(a, b):
                    na, nb = clubes[a], clubes[b]
                    avisos.append(
                        f"{cancha}: juegan de local {a} ({na} partido"
                        f"{'' if na == 1 else 's'}) y {b} ({nb}). Se llaman parecido "
                        f"y comparten cancha: puede ser un alquiler, o puede ser el "
                        f"mismo club escrito de dos formas")
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

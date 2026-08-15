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


# Clubes que jugaron de local en la cancha de otro, verificado con prensa.
#
# Un chequeo que grita todos los dias por algo que ya se miro deja de leerse, y
# ahi se pierde el unico aviso que importaba. Pero silenciar es peligroso, asi que
# se pide lo mismo que en `correcciones.py`: la evidencia escrita y citada. La
# regla que se uso en los dos es la misma -- una cronica ANTERIOR al partido que
# nombre el estadio, porque una nota previa no puede haber copiado de Wikipedia.
#
# Un alquiler verificado no cuenta como casa del club: no se lo silencia despues,
# directamente no entra al recuento. Es lo correcto y ademas es lo mas conservador
# -- si ese club tuviera OTRO problema en esa cancha, seguiria apareciendo.
ALQUILERES = {
    ("Centenario", "Argentino de Quilmes"):
        "Primera C 2018-19, Fecha 19 contra Berazategui. El Centenario es de "
        "Quilmes AC, que en 2018 jugaba la Primera Nacional. Solo Ascenso, cuatro "
        "dias ANTES del partido: 'El Mate sera local en un estadio de primer nivel "
        "como el Centenario, la cancha de Quilmes'. Y el presidente de Argentino, "
        "Cesar Sosa, en El Sol de Quilmes: 'Hemos hecho un esfuerzo enorme para "
        "poder llevar el partido al estadio de Quilmes'. "
        "https://www.soloascenso.com.ar/notas/berazategui/clasico-con-visitantes/128095",
    ("Malvinas Argentinas", "Huracán Las Heras"):
        "Federal A 2023, Fecha 1 contra San Martin (SM). El Malvinas Argentinas es "
        "el municipal de Mendoza donde juega Godoy Cruz. Los Andes, cuatro dias "
        "ANTES: 'Se jugara el domingo desde las 16 en el estadio Malvinas "
        "Argentinas, con ambos publicos'. Ademas la revancha del mismo cruce, en "
        "la misma temporada, figura en General San Martin: la pagina distingue las "
        "dos canchas, asi que no es un error de transcripcion. "
        "https://www.losandes.com.ar/mas-deportes/federal-a-todo-lo-que-hay-que-saber-para-el-partido-entre-huracan-las-heras-y-san-martin",
}


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
        cancha = str(f["venue"]).strip()
        if (cancha, f["home_team"]) in ALQUILERES:
            continue        # verificado con prensa: no dice nada sobre su casa
        de_local.setdefault(cancha, Counter())[f["home_team"]] += 1
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


# En que division juega cada torneo. Dos torneos del MISMO nivel en una temporada
# son normales -- el Apertura y el Clausura son los dos de Primera --, y un salto
# de UN nivel tambien: la temporada argentina cruza dos anios calendario, asi que
# un club que asciende en junio figura en las dos categorias del mismo anio.
#
# Las copas quedan afuera a proposito: la Copa Argentina cruza divisiones por
# diseno y ahi un club de Primera C contra uno de Primera no dice nada raro.
_NIVEL = {
    "Primera Division": 1, "Primera Division - Apertura": 1,
    "Primera Division - Clausura": 1, "Primera Division - Inicial": 1,
    "Primera Division - Final": 1, "Copa de la Liga": 1,
    "Primera Nacional": 2,
    "Primera B": 3, "Torneo Argentino A": 3, "Torneo Federal A": 3,
    "Primera C": 4,
    "Primera D": 5,
}


def categorias_incompatibles(filas: list[dict]) -> list[str]:
    """Un club en dos divisiones que no se pueden encadenar, la misma temporada.

    El otro chequeo de dataset entero que no mira nombres ni canchas: mira DONDE
    juega cada club. Un club mal atribuido termina jugando torneos que su club de
    verdad nunca jugo, y eso se ve sin saber nada de futbol.

    Lo que hace que esto no sea ruido es el SALTO. Un club aparece en dos
    categorias el mismo anio todo el tiempo, porque la temporada argentina cruza
    dos anios calendario: el que desciende en junio juega el Clausura en Primera
    y desde agosto la Primera Nacional, y las dos filas dicen el mismo anio. Eso
    es un salto de uno y es normal -- son 45 de los 46 casos del dataset.

    Dos niveles no se puede. Para ir de Primera a Primera B en un anio calendario
    habria que descender dos veces, y no hay calendario donde eso entre. El unico
    caso que aparecio fue Estudiantes de La Plata en la Primera B 2015, que era
    Estudiantes de Caseros mal atribuido por una tilde.
    """
    por_club: dict[str, dict[str, set]] = {}
    for f in filas:
        n = _NIVEL.get(f["tournament"])
        if n is None:
            continue
        for lado in ("home_team", "away_team"):
            por_club.setdefault(f[lado], {}).setdefault(str(f["season"]), set()).add(
                (n, f["tournament"]))
    avisos = []
    for club, temporadas in sorted(por_club.items()):
        for temporada, tors in sorted(temporadas.items()):
            niveles = {n for n, _ in tors}
            if max(niveles) - min(niveles) < 2:
                continue
            cuales = ", ".join(t for _, t in sorted(tors))
            avisos.append(
                f"{club} figura en {temporada} jugando {cuales}. Entre esas hay "
                f"{max(niveles) - min(niveles)} divisiones de diferencia, y en un "
                f"anio calendario no se baja ni se sube mas de una: casi seguro "
                f"que uno de los dos es otro club con el mismo nombre")
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

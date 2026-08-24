#!/usr/bin/env python3
"""
fad/espn.py
===========
Sacar del feed de ESPN la FECHA de partidos que ya tenemos. Tercer adaptador,
mismo contrato que `fad/fechas.py` (worldfootball) y `fad/rsssf.py`: entra un
partido que ya existe y sale con fecha, o sin ella. Nada mas.

POR QUE ESTE Y NO OTRO
----------------------
Las tres temporadas de Primera C 2008-2011 publican los resultados en tablas de
TRES columnas -- `Local | Resultado | Visitante` -- y no hay columna de fecha que
el parser este leyendo mal: no existe. worldfootball tampoco sirve, porque su
Primera B Metropolitana arranca en 2018/19 y Primera C no figura.

El feed de ESPN devuelve la temporada entera en una sola llamada, con fecha por
partido. La consulta es por RANGO DE FECHAS y no por temporada, asi que arrastra
lo que se haya jugado en ese rango: partidos de promocion contra Primera D, por
ejemplo. Eso no molesta -- lo que no empareja, no empareja -- pero explica por
que el feed trae mas partidos que nuestra grilla.

LA TRAMPA DEL HUSO, QUE YA MORDIO UNA VEZ
-----------------------------------------
`date` viene en **UTC**. Es la misma trampa que documenta `fad/fechas.py` para
worldfootball: un partido de las 21:00 en Argentina es de las 00:00 UTC del dia
siguiente, y tomando el UTC sin convertir todos los nocturnos quedan corridos un
dia. Se convierte a hora argentina antes de quedarse con la fecha.

SIN NUMERO DE JORNADA, Y QUE SE HACE CON ESO
--------------------------------------------
El feed NO trae la jornada. La regla del proyecto es "los equipos y la jornada
IDENTIFICAN el partido, el marcador lo VERIFICA", asi que no se puede aplicar tal
cual. Lo que se hace en su lugar no es aflojarla sino cambiarle el identificador,
y se midio antes de decidirlo:

    en una liga de ida y vuelta cada par se cruza UNA VEZ EN CADA CANCHA, asi que
    (local, visita) ya identifica el partido sin ayuda de la jornada.

Medido sobre nuestros propios datos: 384 pares distintos sobre 384 partidos en la
2008-09, y 384 sobre 385 en la 2009-10. Del lado de ESPN hay una decena de pares
repetidos -- los playoffs vuelven a cruzar a los mismos --, y esos se caen solos
por la regla de colision que `completar` ya tenia: lo que no identifica uno solo,
no identifica nada.

El marcador sigue verificando igual que siempre. Y hay una guarda mas, que el
marcador no da: `contrastar_plantel` exige que los clubes que ESPN pone en la
temporada sean LOS MISMOS que los nuestros. Un mapa de nombres mal escrito manda
un partido al club equivocado, y eso el marcador no lo agarra -- dos partidos
pueden coincidir en resultado por casualidad. La comparacion de planteles si.
"""
from __future__ import annotations

import json
import urllib.request
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from fad import wiki
from fad.fechas import Ajeno

CREDITO = "https://www.espn.com.ar/"

_CACHE = Path(__file__).resolve().parent.parent / ".cache" / "espn"
_ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")
_API = ("https://site.api.espn.com/apis/site/v2/sports/soccer/"
        "{liga}/scoreboard?dates={rango}&limit=1000")


def descargar(liga: str, rangos: tuple[str, ...], usar_cache: bool = True) -> list[dict]:
    """Los eventos del feed para esos rangos de fechas.

    Van en varios rangos porque el endpoint contesta 400 si se le pide mas de un
    anio de una: la temporada 2010-11 se pide en dos mitades.
    """
    destino = _CACHE / f"{liga}-{'_'.join(rangos)}.json"
    if usar_cache and destino.exists():
        return json.loads(destino.read_text(encoding="utf-8"))
    eventos: list[dict] = []
    for rango in rangos:
        req = urllib.request.Request(_API.format(liga=liga, rango=rango),
                                     headers={"User-Agent": wiki.UA})
        with urllib.request.urlopen(req, timeout=90) as r:
            eventos += json.loads(r.read().decode("utf-8")).get("events", [])
    destino.parent.mkdir(parents=True, exist_ok=True)
    destino.write_text(json.dumps(eventos, ensure_ascii=False), encoding="utf-8")
    return eventos


def _fecha_argentina(iso: str) -> str:
    """`2009-08-22T17:00Z` -> `2009-08-22`, ya en hora argentina."""
    return (datetime.fromisoformat(iso.replace("Z", "+00:00"))
            .astimezone(_ARGENTINA).date().isoformat())


def leer(eventos: list[dict], mapa: dict[str, str],
         padron_ok=None) -> tuple[list[Ajeno], list[str]]:
    """Los partidos del feed, ya con el club canonico.

    `mapa` traduce los nombres que el padron no reconoce. Los que el padron SI
    reconoce pasan derecho, y `padron_ok` es la funcion que lo decide (se inyecta
    para no importar `equipos` aca y poder testear sin el padron entero).

    `jornada=0` en todos a proposito: el feed no la trae y el identificador pasa a
    ser el par (local, visita). Ver el docstring del modulo.
    """
    from fad import equipos
    padron_ok = padron_ok or (lambda n: equipos.buscar(n))

    fuera: list[Ajeno] = []
    desconocidos: set[str] = set()
    for e in eventos:
        comp = e.get("competitions", [{}])[0]
        # UN PARTIDO PROGRAMADO CON MARCADOR CERO NO ES UN 0-0. El feed publica
        # seis eventos en `STATUS_SCHEDULED` que nunca se actualizaron, y los seis
        # traen "0" en las dos columnas. Leidos como resultado, contradecian a la
        # pagina en seis partidos que la pagina tenia bien, y de paso le negaban
        # la fecha a esas filas: el completador no toma una fecha cuando los
        # marcadores no coinciden, porque podrian no ser el mismo partido.
        #
        # Es el mismo caso que "sin marcador no se puede verificar", tres lineas
        # mas abajo, escrito de otra manera. Se descarta SOLO cuando el feed dice
        # que no: si el campo no esta, no se sabe y se lee como antes.
        if ((comp.get("status") or {}).get("type") or {}).get("completed") is False:
            continue
        lados = {c.get("homeAway"): c for c in comp.get("competitors", [])}
        if "home" not in lados or "away" not in lados:
            continue
        nombres, goles = {}, {}
        for lado in ("home", "away"):
            crudo = lados[lado].get("team", {}).get("displayName") or ""
            if crudo in mapa:
                nombres[lado] = mapa[crudo]
            else:
                eq = padron_ok(crudo)
                if eq is None:
                    desconocidos.add(crudo)
                    nombres[lado] = None
                else:
                    nombres[lado] = eq.nombre if hasattr(eq, "nombre") else eq
            marcador = lados[lado].get("score")
            goles[lado] = int(marcador) if marcador not in (None, "") else None
        if not nombres["home"] or not nombres["away"]:
            continue
        if goles["home"] is None or goles["away"] is None:
            continue                      # sin marcador no se puede verificar
        fuera.append(Ajeno(fecha=_fecha_argentina(e["date"]), jornada=0,
                           local=nombres["home"], visita=nombres["away"],
                           goles_local=goles["home"], goles_visita=goles["away"]))
    avisos = ([f"{len(desconocidos)} nombres de ESPN que el mapa no traduce: "
               + ", ".join(sorted(desconocidos))] if desconocidos else [])
    return fuera, avisos


def contrastar_plantel(ajenos: list[Ajeno], nuestros: list) -> list[str]:
    """Que ESPN y nosotros hablemos de LOS MISMOS clubes.

    Esta es la guarda que el marcador no da. Un nombre mal traducido en el mapa
    manda el partido al club equivocado, y el marcador no lo agarra: dos partidos
    de la misma temporada pueden coincidir en resultado por casualidad, y ahi se
    importa una fecha ajena sin que nada se queje. La comparacion de planteles si
    lo agarra, porque un club que no jugo esa temporada no puede aparecer.

    Solo denuncia lo que ESPN pone y nosotros no. El reciproco -- clubes nuestros
    que ESPN no tiene -- no es un error: el feed puede no cubrir todo, y de hecho
    no cubre los playoffs de todas las temporadas.
    """
    suyos = {c for a in ajenos for c in (a.local, a.visita)}
    mios = {c for p in nuestros for c in (p.local, p.visita)}
    sobran = sorted(suyos - mios)
    if not sobran:
        return []
    return [f"ESPN trae clubes que no jugaron esta temporada segun nuestra grilla: "
            f"{', '.join(sobran)}. Puede ser un partido de promocion contra otra "
            f"categoria (inocuo) o un nombre mal traducido en el mapa (no inocuo)"]


# --------------------------------------------------------------------------
# Los mapas. Solo lo que el padron NO resuelve solo.
#
# `FC Urquiza` es el que obliga a mirar dos veces: ESPN tiene ADEMAS un
# `J. J. de Urquiza` con otro id (10104 contra 10056), o sea que para ESPN son
# dos clubes distintos, y lo son. En la 2010-11 nuestro plantel trae los dos --
# J. J. de Urquiza y UAI Urquiza -- asi que `FC Urquiza` es UAI. En la 2009-10 no
# jugo UAI Urquiza, asi que ahi NO se traduce y sus partidos no emparejan, que es
# lo correcto: son de la promocion contra otra categoria.
# --------------------------------------------------------------------------
_COMUNES = {
    "CADU": "Defensores Unidos",
    "L.N. Alem": "Leandro N. Alem",
    "Lamadrid": "General Lamadrid",
    "Argentino (Rosario)": "Argentino de Rosario",
    "Central Córdoba (Rosario)": "Central Córdoba (R)",
    "Talleres de Remedios": "Talleres (RdE)",
}

PRIMERA_C_2008 = dict(_COMUNES)
PRIMERA_C_2009 = dict(_COMUNES)
PRIMERA_C_2010 = {**_COMUNES, "FC Urquiza": "UAI Urquiza"}

# Primera C 2011-12. `Social Español` se fuerza por CARDINALIDAD y no por
# parecido, igual que en la Primera B 2010-11 de mas abajo, y la cuenta se
# rehizo para ESTA temporada en vez de heredarla: nuestro plantel tiene
# exactamente UN Español -- Deportivo -- y el de ESPN tambien, en la misma
# competencia y la misma temporada. Y los dos Urquiza estan separados, que es
# la trampa de esta categoria: `FC Urquiza` es UAI y `J. J. de Urquiza` es otro
# club, los dos jugando el mismo torneo.
PRIMERA_C_2011 = {**_COMUNES,
                  "FC Urquiza": "UAI Urquiza",
                  "Social Español": "Deportivo Español"}

# Primera B 2010-11, que va por `arg.3`. `Social Español` es el unico que hace
# dudar, porque en el ascenso argentino hay dos Espanoles y no son el mismo club.
# Queda forzado por cardinalidad y no por parecido: nuestro plantel de esa
# temporada tiene exactamente UN Espanol -- Deportivo -- y el de ESPN tambien, en
# la misma competencia y la misma temporada. Si estuviera mal, `contrastar_plantel`
# no lo agarraria (Deportivo Espanol si jugo), pero el marcador fallaria en sus
# 42 partidos y el aviso lo diria a los gritos.
PRIMERA_B_2010 = {
    **_COMUNES,
    "Estudiantes de Buenos Aires": "Estudiantes (BA)",
    "Sarmiento (Junín)": "Sarmiento (J)",
    "Social Español": "Deportivo Español",
}

# {pagina de Wikipedia: (liga, rangos de fecha, mapa)}
FUENTES: dict[str, tuple[str, tuple[str, ...], dict]] = {
    "Campeonato de Primera C 2008-09 (Argentina)":
        ("arg.4", ("20080801-20090731",), PRIMERA_C_2008),
    "Campeonato de Primera C 2009-10 (Argentina)":
        ("arg.4", ("20090801-20100731",), PRIMERA_C_2009),
    "Campeonato de Primera C 2010-11 (Argentina)":
        ("arg.4", ("20100701-20101231", "20110101-20110731"), PRIMERA_C_2010),
    "Campeonato de Primera B 2010-11 (Argentina)":
        ("arg.3", ("20100701-20101231", "20110101-20110731"), PRIMERA_B_2010),
    "Campeonato de Primera C 2011-12 (Argentina)":
        ("arg.4", ("20110801-20111231", "20120101-20120731"), PRIMERA_C_2011),
}

# Como llama ESPN a cada ronda del Reducido, y como se escribe en el dataset. El
# feed las distingue en `season.slug`, que es el unico lugar donde dice de que
# instancia es el partido: todo lo demas de un partido de cuartos se ve igual que
# uno de la fase regular.
_RONDAS = {
    "cuartos-de-final": "Cuartos de final",
    "semifinal": "Semifinal",
    "final": "Final",
    "promocion": "Promoción",
}


def leer_llaves(eventos: list[dict], mapa: dict[str, str], torneo: str,
                padron_ok=None) -> tuple[list, list[str]]:
    """Los partidos de eliminacion del feed, listos para entrar al dataset.

    Devuelve `Partido` y no `Ajeno` porque estas filas ENTRAN -- `Ajeno` existe
    para completarle la fecha a una fila de Wikipedia, que es otra cosa.

    LA LOCALIA SALE DE `homeAway` Y NO DE `venue`. Se midio: en la Primera C
    2011-12 hay dos partidos cuyo `venue` nombra una cancha que no es de ninguno
    de los dos clubes, asi que deducir la localia del estadio daria el club
    equivocado en esos dos. `homeAway` es lo que el feed afirma, y ademas se
    verifica solo: en las siete llaves la localia ALTERNA entre ida y vuelta sin
    una excepcion, que es lo que un valor por defecto no produce.

    LA FECHA VA EN HORA ARGENTINA. El feed la da en UTC y la vuelta de la final es
    `2012-06-22T00:00Z`, que aca es el 21: usar la fecha cruda mete un dia de mas
    en ese partido. `_fecha_argentina` ya lo hacia para las fechas y vale igual
    aca.
    """
    from fad import equipos
    from fad.parser import Partido

    padron_ok = padron_ok or (lambda n: equipos.buscar(n))
    fuera, raros = [], []
    desconocidos: set[str] = set()
    for e in eventos:
        ronda = _RONDAS.get((e.get("season") or {}).get("slug", ""))
        if not ronda:
            continue                      # la fase regular no es una llave
        comp = (e.get("competitions") or [{}])[0]
        lados = {c.get("homeAway"): c for c in comp.get("competitors", [])}
        if "home" not in lados or "away" not in lados:
            continue
        nombres, goles = {}, {}
        for lado in ("home", "away"):
            crudo = lados[lado].get("team", {}).get("displayName") or ""
            if crudo in mapa:
                nombres[lado] = mapa[crudo]
            else:
                eq = padron_ok(crudo)
                if eq is None:
                    desconocidos.add(crudo)
                    nombres[lado] = None
                else:
                    nombres[lado] = eq.nombre if hasattr(eq, "nombre") else eq
            m = lados[lado].get("score")
            goles[lado] = int(m) if m not in (None, "") else None
        if not nombres["home"] or not nombres["away"]:
            continue
        if goles["home"] is None or goles["away"] is None:
            raros.append(f"{ronda}: {nombres['home']} vs {nombres['away']} viene "
                         f"sin marcador; queda afuera")
            continue
        fuera.append(Partido(
            fecha=_fecha_argentina(e["date"]),
            local=nombres["home"], visita=nombres["away"],
            goles_local=goles["home"], goles_visita=goles["away"],
            torneo=torneo, fase="eliminacion", jornada=ronda,
            llave="Reducido" if ronda != "Promoción" else "Promociones",
            fuente_fecha=CREDITO))
    if desconocidos:
        raros.append(f"{len(desconocidos)} nombres de ESPN que el mapa no traduce: "
                     + ", ".join(sorted(desconocidos)))
    return fuera, raros

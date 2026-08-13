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
    formato: str = "liga"    # "liga" (zonas + llaves) o "copa" (tabla por ronda)
    neutral: bool = False    # si TODA la competencia se juega en cancha neutral
    anio_fin: int | None = None   # si la temporada cruza el calendario (2016-17)
    mes_inicio: int = 8           # mes en que arranca; solo importa si cruza

    @property
    def url(self) -> str:
        return "https://es.wikipedia.org/wiki/" + self.pagina.replace(" ", "_")


# `formato` va escrito y no se detecta solo. Una pagina de copa y una de liga se
# parecen lo bastante como para que una deteccion automatica devuelva cero
# partidos en vez de fallar, y cero partidos se parece mucho a "todavia no
# empezo el torneo".
PRIMERA = [
    Torneo("Anexo:Torneo Apertura 2026 (Argentina)", "Primera Division - Apertura", 2026),
    Torneo("Anexo:Torneo Clausura 2026 (Argentina)", "Primera Division - Clausura", 2026),
]

# El historico. Diez temporadas y siete nombres distintos para el mismo
# campeonato -- por eso el catalogo va a mano: no hay patron de titulo que
# sobreviva a Campeonato / Superliga / Copa de la Liga / Apertura-Clausura.
#
# `anio_fin` marca las que cruzan el calendario. Ojo con `mes_inicio`: la 2019-20
# arranco el 26 de JULIO, y con el corte habitual de agosto su Fecha 1 entera
# quedaba fechada en julio de 2020, al final de la temporada.
#
# En 2020-2024 conviven dos torneos por anio (la Copa de la Liga y el campeonato
# largo) y los dos son de Primera: dejar uno afuera deja medio calendario sin
# cubrir, que para estimar forma reciente es peor que no tener el anio.
HISTORICO = [
    Torneo("Campeonato de Primera División 2016 (Argentina)",
           "Primera Division", 2016),
    Torneo("Campeonato de Primera División 2016-17 (Argentina)",
           "Primera Division", 2016, anio_fin=2017),
    Torneo("Campeonato de Primera División 2017-18 (Argentina)",
           "Primera Division", 2017, anio_fin=2018),
    Torneo("Campeonato de Primera División 2018-19 (Argentina)",
           "Primera Division", 2018, anio_fin=2019),
    Torneo("Campeonato de Primera División 2019-20 (Argentina)",
           "Primera Division", 2019, anio_fin=2020, mes_inicio=7),

    Torneo("Copa de la Liga Profesional 2020", "Copa de la Liga", 2020),
    Torneo("Copa de la Liga Profesional 2021", "Copa de la Liga", 2021),
    Torneo("Campeonato de Primera División 2021 (Argentina)",
           "Primera Division", 2021),
    Torneo("Copa de la Liga Profesional 2022", "Copa de la Liga", 2022),
    Torneo("Campeonato de Primera División 2022 (Argentina)",
           "Primera Division", 2022),
    Torneo("Copa de la Liga Profesional 2023", "Copa de la Liga", 2023),
    Torneo("Campeonato de Primera División 2023 (Argentina)",
           "Primera Division", 2023),
    Torneo("Copa de la Liga Profesional 2024", "Copa de la Liga", 2024),
    Torneo("Campeonato de Primera División 2024 (Argentina)",
           "Primera Division", 2024),

    Torneo("Anexo:Torneo Apertura 2025 (Argentina)",
           "Primera Division - Apertura", 2025),
    Torneo("Anexo:Torneo Clausura 2025 (Argentina)",
           "Primera Division - Clausura", 2025),
]

# `neutral=True` no es una suposicion: la Copa Argentina se juega a partido unico
# en cancha neutral por reglamento, y la propia pagina lo dice ronda por ronda
# ("se enfrentaron a partido unico en estadio neutral"). Es el unico caso hasta
# ahora en que el dato se puede afirmar sin mirar donde queda cada estadio.
COPAS = [
    Torneo("Copa Argentina 2026", "Copa Argentina", 2026,
           formato="copa", neutral=True),
]

TODOS = HISTORICO + PRIMERA + COPAS

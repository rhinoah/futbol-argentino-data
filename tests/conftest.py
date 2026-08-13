#!/usr/bin/env python3
"""Fixtures de wikitexto. Los tests no salen a la red: lo que se prueba es el
parseo, y un test que depende de que Wikipedia este arriba y diga hoy lo mismo
que ayer no prueba el parseo, prueba internet."""
from __future__ import annotations

import pytest

# Reproduce la estructura real, con lo que la hace dificil:
#   * una tabla POR JORNADA, y entre el `|}` de una y el `{|` de la siguiente no
#     hay `|-`  (el bug de las etiquetas corridas)
#   * `rowspan` en fecha y hora
#   * bgcolor y negritas en la celda del ganador
#   * un bloque "Interzonal", que no es "Zona X"
TABLA = """
{|class="wikitable" style="text-align: center;"
!colspan=6|Fecha 1
|-
!colspan=6|Zona A
|-
!width=21%|Local
!width=10%|Resultado
!width=21%|Visitante
!width=26%|Estadio
!width=14%|Fecha
!width=8%|Hora
|-
|[[Club Atlético Unión|Unión]]
|0 - 0
|[[Club Atlético Platense|Platense]]
|15 de Abril
|rowspan=2|23 de enero
|20:00
|-
|bgcolor=#d0e7ff|'''Boca Juniors
|2 - 1
|Instituto
|La Bombonera
|22:00
|-
!colspan=6|Interzonal
|-
!width=21%|Local
!width=10%|Resultado
!width=21%|Visitante
!width=26%|Estadio
!width=14%|Fecha
!width=8%|Hora
|-
|Aldosivi
|bgcolor=#d0e7ff|'''0 - 0
|Defensa y Justicia<ref name=x>algo</ref>
|José María Minella
|22 de enero
|17:00
|}
{|class="wikitable" style="text-align: center;"
!colspan=6|Fecha 2
|-
!colspan=6|Zona A
|-
!width=21%|Local
!width=10%|Resultado
!width=21%|Visitante
!width=26%|Estadio
!width=14%|Fecha
!width=8%|Hora
|-
|Platense
|1 - 3
|Boca Juniors
|Vicente Lopez
|26 de enero
|19:00
|}
"""

LLAVES = """
{{Partido
|local = River Plate
|resultado = 1:1''' (0:0)
|visita = San Lorenzo
|resultado penalti = 4:3
|fecha = 17 de mayo
|estadio = [[Estadio Monumental|Monumental]]
}}

{{Partido
|local = Belgrano
|resultado = 2:0''' (1:0)
|visita = Racing Club
|fecha = 18 de mayo
|estadio = Gigante de Alberdi
}}
"""


# La Copa: una tabla por ronda, y todo distinto.
#   * las celdas van en UN renglon separadas por `||`, no una por linea
#   * las filas alternan sombreado, y ese `bgcolor` va pegado al `|-`
#   * los penales son `{{small|(N)}}` a los costados del marcador -- al reves
#     que en {{Partido}}, donde el parentesis es el entretiempo
#   * hay filas sin marcador: la ronda esta en curso
#   * despues de la ultima ronda sigue la pagina, con mas tablas
COPA = """
== Fase final ==

=== Treintaidosavos de final ===
Se enfrentaron a partido unico en estadio neutral.
{| cellspacing="0" width="80%"
|- bgcolor="#006699"
!Fecha
!Estadio
!Equipo 1
!Partido
!Equipo 2
|-
|align=center|18 de enero||align=center|Ciudad de Caseros||align=right|[[Club Atlético Lanús|Lanús]] {{bandera|Provincia de Buenos Aires}}||align=center|4 - 1||{{bandera|Santiago del Estero}} [[Sarmiento (La Banda)|Sarmiento (LB)]]

|- bgcolor="#F5FAFF"
|align=center|21 de enero||align=center|Ciudad de Lanús||align=right|[[Argentinos Juniors]] {{bandera|Buenos Aires}}||align=center| {{small|(5)}} 1 - 1 {{small|(6)}} ||{{bandera|Provincia de Buenos Aires}} '''[[Ferrocarril Midland]]'''

|- bgcolor="#F5FAFF"
|align=center|22 de enero||align=center|Once Unidos||align=right|'''{{nowrap|[[Gimnasia y Esgrima (LP)]]}}''' {{bandera|Provincia de Buenos Aires}}||align=center|2 - 0||{{bandera|Provincia de Chubut}} [[Deportivo Madryn]]
|}

=== Dieciseisavos de final ===
{| cellspacing="0" width="80%"
|- bgcolor="#006699"
!Fecha
!Estadio
!Equipo 1
!Partido
!Equipo 2
|-
|align=center|17 de julio||align=center|Ciudad de Caseros||align=right|'''[[Ferrocarril Midland]]''' {{bandera|Provincia de Buenos Aires}}||align=center|2 - 0||{{bandera|Provincia de Buenos Aires}} [[Club Atlético Lanús|Lanús]]

|- bgcolor="#F5FAFF"
|align=center| || ||align=right|[[Gimnasia y Esgrima (LP)]] {{bandera|Provincia de Buenos Aires}}||align=center| ||{{bandera|Provincia de Chubut}} [[Deportivo Madryn]]
|}

== Goleadores ==
{| class="wikitable"
!Jugador
!Equipo
!Goles
|-
|Fulano||[[Club Atlético Lanús|Lanús]]||7 - 0
|}
"""


@pytest.fixture
def pagina() -> str:
    """Una pagina de temporada entera, como la devuelve la API."""
    return f"== Desarrollo ==\n=== Resultados ===\n{TABLA}\n== Eliminacion ==\n{LLAVES}\n"

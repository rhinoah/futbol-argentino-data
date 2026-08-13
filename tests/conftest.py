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


@pytest.fixture
def pagina() -> str:
    """Una pagina de temporada entera, como la devuelve la API."""
    return f"== Desarrollo ==\n=== Resultados ===\n{TABLA}\n== Eliminacion ==\n{LLAVES}\n"

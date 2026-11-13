#!/usr/bin/env python3
"""
fad/canchas.py
==============
El padron de canchas: como se publica cada una en `venue`.

`venue` sale de la pagina de cada torneo, y cada pagina escribe la cancha a su
manera. Medido el 13/11/2026 sobre las 40 265 filas con cancha: 630 grafias, y
177 canchas que difieren solo en tildes, mayusculas, comillas o un "Estadio"
adelante -- `15 de abril` y `15 de Abril`, `Raúl Conti` y `Raul Conti`. Quien
agrupaba por cancha las contaba como dos.

ESTA ES LA PRIMERA ETAPA, LA TIPOGRAFICA
----------------------------------------
Dos grafias son la misma si coinciden despues de `clave`, y se publica la que
dice este padron. No pide fuente: no afirma que dos nombres distintos sean la
misma cancha, solo que es el mismo nombre escrito de dos formas. Por eso una
grafia como `El Fortín` puede seguir nombrando dos canchas distintas: ya las
nombraba antes, con o sin el "Estadio".

Lo que NO resuelve, y queda para las etapas que siguen, cada alias con su fuente:
  * un apellido mal escrito: `Don León Kolbovsky` y `Don León Kolbowsky`;
  * un nombre largo y uno corto: `Tomás A. Ducó` y `Tomás Adolfo Ducó`;
  * un apodo: `La Doble Visera`, que es el Libertadores de América.
Por eso hay pares que parecen repetidos en `PADRON`: son dos grafias que la clave
no junta, y juntarlas es decir que son la misma cancha.

POR QUE EL NOMBRE SE ESCRIBE ACA Y NO SE ELIGE SOLO
---------------------------------------------------
Elegir en cada build la grafia mas comun ahorraba la lista, pero el nombre de una
cancha cambiaba el dia que una pagina nueva diera vuelta la mayoria, y nadie se
enteraba. Escrito aca, cambiarlo es un commit. Cada nombre es la grafia mas comun
de su cancha sin el "Estadio" adelante, medida el 13/11/2026; en los empates, la
que lleva tildes.

Una grafia nueva que choca con otra y no esta en el padron no se elige sola:
`sueltas` la avisa en el build, y se agrega aca.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter

# Las palabras que no distinguen una cancha de otra. `Estadio Del Bosque`,
# `Estadio del Bosque` y `Del Bosque` son la misma; `Héctor Odicino y Pedro
# Benoza` y `Héctor Odicino - Pedro Benoza`, tambien.
_SIN_PESO = frozenset({"estadio", "cancha", "de", "del", "la", "el", "los", "las", "y",
                       "stadium", "club", "campo", "deportes"})


def clave(nombre: str) -> str:
    """El nombre sin tildes, mayusculas, puntuacion ni palabras sin peso."""
    s = "".join(c for c in unicodedata.normalize("NFKD", nombre)
                if not unicodedata.combining(c))
    s = re.sub(r"[^\w\s]", " ", s.lower())
    return " ".join(t for t in s.split() if t not in _SIN_PESO)


# Ordenado por la clave, que es como se busca a ojo: `La Bombonera` va en la B.
PADRON: tuple[str, ...] = (
    "1 de Abril",
    "1.º de Abril",
    "12 de Octubre",
    "15 de abril",
    "17 de Octubre",
    "20 de Octubre",
    "23 de Agosto",
    "9 de Julio",
    "Abel Sastre",
    "Alfredo Beranger",
    "Alfredo Ramos",
    "Alfredo Terrera",
    "Antonio Candini",
    "Argentino de Merlo",
    "Argentino de Quilmes",
    "Armenia",
    "Arquitecto Ricardo Echeverri",
    "Arquitecto Ricardo Etcheverri",
    "Club Atlético Atlanta",
    "Club Atlético Belgrano",
    "Club Atlético Unión",
    "De la Avenida",
    "Bautista Gargantini",
    "Beto Larrosa",
    "Bicentenario",
    "Bicentenario Ciudad de Catamarca",
    "La Bombonera",
    "Del Bosque",
    "Brigadier General Estanislao López",
    "Carlos Alberto Sacaan",
    "Carlos Barraza",
    "Carlos Sacaan",
    "Carlos V",
    "Centenario Ciudad de Quilmes",
    "Centenario de Resistencia",
    "Centro Siderúrgico",
    "Chacarita Juniors",
    "El Cilindro",
    "Ciudad de La Banda",
    "Ciudad de Caseros",
    "Ciudad de Córdoba",
    "Ciudad Evita",
    "Ciudad de Laferrere",
    "Ciudad de Lanús",
    "Ciudad de Libertad",
    "Ciudad de La Plata",
    "Ciudad de Río Cuarto",
    "Ciudad de San Miguel",
    "Ciudad de San Vicente",
    "Ciudad de Vicente López",
    "La Ciudadela",
    "Claudio Chiqui Tapia",
    "Clemente Fernández de Oliveira",
    "Colegiales",
    "Coliseo del Golfo",
    "El Coliseo de Mitre y Puccini",
    "El Coloso del Barrio Talleres",
    "Coloso del Parque",
    "Coloso de Ruca Quimey",
    "Comandante Andrés Guacurarí",
    "Deportivo Paraguayo",
    "Diego Armando Maradona",
    "La Doble Visera",
    "Doctor Luis Güemes",
    "Doctor Osvaldo Baletto",
    "Don León Kolbovsky",
    "Don León Kolbowsky",
    "Dr. Osvaldo Baletto",
    "Eduardo Gallardón",
    "Elías Moisés Gómez",
    "Emilio Fabrizzi",
    "Enrique Sexto",
    "De los Eucaliptos",
    "De Los Eucaliptus",
    "Eva Perón",
    "Excursionistas",
    "Félix Oriola",
    "Ferro Carril Oeste",
    "Florencio Sola",
    "Fortaleza del Bicho",
    "El Fortín",
    "Fragata Presidente Sarmiento",
    "Fragata Sarmiento",
    "Fray Honorato Pistoia",
    "Gabino Sosa",
    "Genacio Sálice",
    "General San Martín",
    "Gigante de Alberdi",
    "Gigante de Arroyito",
    "Gigante del Barrio Sarmiento",
    "El Gigante del Norte",
    "Gigante de Villa Fox",
    "Gildo Francisco Ghersinich",
    "Guillermo Laza",
    "Héctor Odicino y Pedro Benoza",
    "Hugo Moyano",
    "Ingeniero Hilario Sánchez",
    "De los Inmigrantes",
    "Islas Malvinas",
    "Jorge Alfredo Arín",
    "Jorge Arin",
    "Jorge Luis Hirschi",
    "José Alfredo Arín",
    "José Amalfitani",
    "José Dellagiovanna",
    "José Luis Sánchez",
    "José Manuel Moreno",
    "José María Minella",
    "José María Moraños",
    "José María Paz",
    "José Martín Olaeta",
    "José Moraños",
    "Juan Antonio Arias",
    "Juan Carlos Brieva",
    "Juan Carmelo Zerillo",
    "Juan D. Perón",
    "Juan Domingo Perón",
    "Juan Pablo Francia",
    "Juan Pasquale",
    "Julio César Villagra",
    "Julio Humberto Grondona",
    "Leandro N. Alem",
    "Libertadores de América",
    "Libertarios Unidos",
    "Liga Mercedina",
    "Lorenzo Arandilla",
    "Malvinas Argentinas",
    "Manuel y Ramón Núñez",
    "Marcelo Bielsa",
    "Mario Alberto Kempes",
    "Merlo",
    "Miguel Sancho",
    "Modesto Marrone",
    "Monumental",
    "Monumental José Fierro",
    "Monumental de Villa Lynch",
    "Municipal de la Ciudad de Luján",
    "Municipal de Comodoro Rivadavia",
    "Municipal Eva Perón",
    "Municipal General San Martín",
    "Municipal Gral. San Martín",
    "Norman Lee",
    "Nueva Chicago",
    "Nueva España",
    "Nuevo Francisco Urbano",
    "Nuevo Gasómetro",
    "Nuevo Monumental",
    "Ofelia Rosenzuaig",
    "Omar Higinio Sperdutti",
    "Oscar C. Boero",
    "Padre Ernesto Martearena",
    "La Pedrera",
    "Presbítero Bartolomé Grella",
    "Presidente Perón",
    "La Quema",
    "Ramón Roque Martín",
    "Raúl Conti",
    "República de Italia",
    "Ricardo Puga",
    "Roberto Larrosa",
    "Roberto N. Carminatti",
    "Rodolfo Capocasa",
    "Rubén Carlos Vallejos",
    "Salomón Boeseldín",
    "San Juan del Bicentenario",
    "Saturnino Moure",
    "Sol de América",
    "Talleres",
    "Talleres (RdE)",
    "Tomás A. Ducó",
    "Tomás Adolfo Ducó",
    "Tres de Febrero",
    "Único Diego Armando Maradona",
    "Único Madre de Ciudades",
    "Único de San Nicolás",
    "Víctor Antonio Legrotaglie",
    "La Visera de Cemento",
)

_INDICE = {clave(n): n for n in PADRON}


def canonica(nombre: str) -> str:
    """Como se publica la cancha `nombre`: la del padron si es una de sus grafias,
    y si no, tal cual vino."""
    return _INDICE.get(clave(nombre), nombre)


def unificar(filas: list[dict]) -> int:
    """Escribe el `venue` de cada fila como dice el padron. Devuelve cuantas cambio."""
    cambiadas = 0
    for f in filas:
        antes = f.get("venue") or ""
        despues = canonica(antes)
        if despues != antes:
            f["venue"] = despues
            cambiadas += 1
    return cambiadas


def sueltas(filas: list[dict]) -> list[str]:
    """Las canchas escritas de mas de una forma que el padron no unifica.

    Pasa cuando una pagina trae una grafia nueva de una cancha que hasta hoy se
    escribia de una sola: ninguna de las dos esta en `PADRON`, asi que `unificar`
    no las toca. No se elige sola, por lo mismo que el padron se escribe a mano.
    """
    por_clave: dict[str, Counter] = {}
    for f in filas:
        cancha = (f.get("venue") or "").strip()
        if cancha:
            por_clave.setdefault(clave(cancha), Counter())[cancha] += 1
    return [f"una cancha escrita de {len(c)} formas: "
            + " / ".join(f"{g!r} ({n})" for g, n in sorted(c.items()))
            + ". Va en fad/canchas.py, con la que se publica"
            for _, c in sorted(por_clave.items()) if len(c) > 1]

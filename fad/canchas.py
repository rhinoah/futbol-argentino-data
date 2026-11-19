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

UNA SOLA ESTRUCTURA, `PADRON`, como el de clubes: el nombre con que se publica
cada cancha y, si tiene, sus alias. El indice de busqueda se deriva de ella al
importar, y una clave que reclaman dos canchas revienta ahi y no en el CSV.

LA PRIMERA ETAPA: LA GRAFIA
---------------------------
Dos grafias son la misma si coinciden despues de `clave`, y se publica el nombre
del padron. No pide fuente: no afirma que dos nombres distintos sean la misma
cancha, solo que es el mismo nombre escrito de dos formas. Por eso una grafia
como `El Fortín` puede seguir nombrando dos canchas distintas: ya las nombraba
antes, con o sin el "Estadio". Cada nombre es la grafia mas comun de su cancha sin
el "Estadio" adelante, medida el 13/11/2026; en los empates, la que lleva tildes.
Escrito aca y no elegido en cada build, para que no cambie solo el dia que una
pagina nueva de vuelta la mayoria.

LA SEGUNDA ETAPA: LOS ALIAS, CON SU TESTIGO
-------------------------------------------
Un alias SI afirma que dos nombres distintos son la misma cancha -- `Chateau
Carreras` y `Mario Alberto Kempes`, `El Viaducto` y `Julio Humberto Grondona`, un
apellido mal escrito --, asi que va con fuente: las paginas enlazan la celda de la
cancha a un articulo de Wikipedia, y si los enlaces del nombre y del alias llevan,
redirecciones mediante, al MISMO articulo de estadio, son la misma cancha para
Wikipedia. Ese articulo va en `articulo`, y un enlace de ejemplo por grafia, con
su pagina, en `tests/testigos_canchas.txt`. Medido el 19/11/2026: 36 canchas, 40
alias. El nombre que se publica es, como en la primera etapa, la grafia mas comun
del grupo, aunque sea el apodo -- `Del Bosque` y no `Juan Carmelo Zerillo`, `El
Viaducto` y no `Julio Humberto Grondona` --: decidido el 19/11/2026. El titulo del
articulo daba nombres que no escribe ninguna pagina, como `León Kolbowski`.

Tres cosas que la medicion enseño y que la regla cuida:
  * El texto del enlace se compara con la grafia SIN sacar palabras del medio. Con
    la clave de la primera etapa, `[[Estadio 15 de Abril|La Avenida]]` -- el apodo
    de la cancha de Unión -- quedaba igual que `De la Avenida`, que es la de Unión
    de Sunchales, y las juntaba.
  * Una grafia que enlaza a dos estadios no se junta con nada: `Malvinas
    Argentinas` es el de Mendoza y el de Los Polvorines, `El Fortín` es tres.
  * Wikipedia separa lo que la tradicion junta, y manda Wikipedia: `La Doble
    Visera` (1985-2006 en el dataset) tiene articulo propio y no es el
    `Libertadores de América` (desde 2009), que se construyo en su lugar.

Una grafia nueva que choca con otra y no esta en el padron no se elige sola:
`sueltas` la avisa en el build, y se agrega aca.
"""
from __future__ import annotations

import re
import unicodedata
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache

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


@dataclass(frozen=True)
class Cancha:
    nombre: str                       # como se publica
    alias: tuple[str, ...] = ()       # otros nombres de la MISMA cancha
    # El articulo de Wikipedia al que llevan los enlaces del nombre y de cada alias.
    # Es el testigo: sin el, un alias no entra (ver `tests/testigos_canchas.txt`).
    articulo: str = ""


# Ordenado por la clave del nombre, que es como se busca a ojo: `La Bombonera` va
# en la B.
PADRON: tuple[Cancha, ...] = (
    Cancha("1 de Abril"),
    Cancha("1.º de Abril"),
    Cancha("12 de Octubre"),
    Cancha("15 de abril"),
    Cancha("17 de Octubre"),
    Cancha("20 de Octubre"),
    Cancha("23 de Agosto"),
    Cancha("9 de Julio"),
    Cancha("Abel Sastre", alias=("Coliseo del Golfo",),
           articulo="Estadio Abel Sastre"),
    Cancha("Alfredo Beranger"),
    Cancha("Alfredo Ramos"),
    Cancha("Alfredo Terrera"),
    Cancha("Antonio Candini", alias=("Ciudad de Río Cuarto", "Ciudad de Río Cuarto Antonio Candini"),
           articulo="Estadio Ciudad de Río Cuarto Antonio Candini"),
    Cancha("Argentino de Merlo"),
    Cancha("Argentino de Quilmes"),
    Cancha("Armenia"),
    Cancha("Arquitecto Ricardo Echeverri"),
    Cancha("Arquitecto Ricardo Etcheverri"),
    Cancha("Club Atlético Atlanta"),
    Cancha("Club Atlético Belgrano"),
    Cancha("Club Atlético Unión"),
    Cancha("De la Avenida"),
    Cancha("Bautista Gargantini"),
    Cancha("Beto Larrosa", alias=("Roberto Larrosa",),
           articulo="Estadio Roberto Larrosa"),
    Cancha("Bicentenario"),
    Cancha("Bicentenario Ciudad de Catamarca"),
    Cancha("La Bombonera", alias=("Alberto J. Armando",),
           articulo="Estadio Alberto J. Armando"),
    Cancha("Del Bosque", alias=("Juan Carmelo Zerillo", "Juan Carmelo Zerrillo"),
           articulo="Estadio Juan Carmelo Zerillo"),
    Cancha("La Boutique", alias=("Boutique de Barrio Jardín",),
           articulo="Estadio Francisco Cabasés"),
    Cancha("Brigadier Estanislao López", alias=("Brigadier General Estanislao López",),
           articulo="Estadio Brigadier General Estanislao López"),
    Cancha("Carlos Alberto Sacaan"),
    Cancha("Carlos Barraza", alias=("Municipal de Pilar",),
           articulo="Estadio Municipal de Pilar-Carlos Barraza"),
    Cancha("Carlos Sacaan"),
    Cancha("Carlos V"),
    Cancha("Centenario Ciudad de Quilmes", alias=("Centenario Dr. José Luis Meiszner",),
           articulo="Estadio Centenario Ciudad de Quilmes"),
    Cancha("Centenario de Resistencia"),
    Cancha("Centro Siderúrgico"),
    Cancha("Chacarita Juniors"),
    Cancha("El Cilindro", alias=("Presidente Perón",),
           articulo="Estadio Presidente Perón"),
    Cancha("Ciudad de La Banda"),
    Cancha("Ciudad de Caseros"),
    Cancha("Ciudad de Córdoba"),
    Cancha("Ciudad Evita"),
    Cancha("Ciudad de Laferrere"),
    Cancha("Ciudad de Lanús"),
    Cancha("Ciudad de Libertad"),
    Cancha("Ciudad de La Plata", alias=("Único Diego Armando Maradona",),
           articulo="Estadio Único Diego Armando Maradona"),
    Cancha("Ciudad de San Miguel"),
    Cancha("Ciudad de San Vicente"),
    Cancha("Ciudad de Vicente López"),
    Cancha("La Ciudadela"),
    Cancha("Claudio Chiqui Tapia"),
    Cancha("Clemente Fernández de Oliveira"),
    Cancha("Colegiales", alias=("Libertarios Unidos",),
           articulo="Estadio Libertarios Unidos"),
    Cancha("El Coliseo de Mitre y Puccini"),
    Cancha("El Coloso del Barrio Talleres"),
    Cancha("Coloso de Ruca Quimey", alias=("Álvaro Pedro Ducás",),
           articulo="Estadio Alvaro Pedro Ducás"),
    Cancha("Comandante Andrés Guacurarí", alias=("Comandante A. Guacurarí", "Cte. Andrés Guacurarí"),
           articulo="Estadio Comandante Andrés Guacurarí"),
    Cancha("Deportivo Paraguayo"),
    Cancha("Diego Armando Maradona", alias=("Diego A. Maradona",),
           articulo="Estadio Diego Armando Maradona (Argentina)"),
    Cancha("La Doble Visera"),
    Cancha("Doctor Luis Güemes", alias=("Dr. Luis Güemes",),
           articulo="Estadio Doctor Luis Güemes"),
    Cancha("Don León Kolbowsky", alias=("Don León Kolbovsky",),
           articulo="Estadio León Kolbowski"),
    Cancha("Dr. Osvaldo Baletto", alias=("Doctor Osvaldo Baletto",),
           articulo="Estadio Doctor Osvaldo Baletto"),
    Cancha("Eduardo Gallardón"),
    Cancha("Elías Moisés Gómez"),
    Cancha("Emilio Fabrizzi"),
    Cancha("Enrique Sexto"),
    Cancha("De los Eucaliptos"),
    Cancha("De Los Eucaliptus"),
    Cancha("Eva Perón"),
    Cancha("Excursionistas"),
    Cancha("Félix Oriola"),
    Cancha("Ferro Carril Oeste"),
    Cancha("Florencio Sola"),
    Cancha("Fortaleza del Bicho"),
    Cancha("El Fortín"),
    Cancha("Fragata Presidente Sarmiento"),
    Cancha("Fragata Sarmiento"),
    Cancha("Fray Honorato Pistoia"),
    Cancha("Gabino Sosa"),
    Cancha("Genacio Sálice"),
    Cancha("General San Martín"),
    Cancha("Gigante de Alberdi", alias=("Julio César Villagra",),
           articulo="Estadio Julio César Villagra"),
    Cancha("Gigante de Arroyito"),
    Cancha("Gigante del Barrio Sarmiento"),
    Cancha("El Gigante del Norte"),
    Cancha("Gigante de Villa Fox", alias=("Mario Losinno",),
           articulo="Estadio Mario Losinno"),
    Cancha("Gildo Francisco Ghersinich"),
    Cancha("Guillermo Laza"),
    Cancha("Héctor Odicino y Pedro Benoza"),
    Cancha("Hugo Moyano"),
    Cancha("Ingeniero Hilario Sánchez"),
    Cancha("De los Inmigrantes"),
    Cancha("Islas Malvinas"),
    Cancha("Jorge Alfredo Arín"),
    Cancha("Jorge Arin"),
    Cancha("Jorge Luis Hirschi"),
    Cancha("José Alfredo Arín"),
    Cancha("José Amalfitani"),
    Cancha("José Antonio Romero Feris", alias=("José Antonio Romero",),
           articulo="Estadio José Antonio Romero Feris"),
    Cancha("José Dellagiovanna"),
    Cancha("José Luis Sánchez"),
    Cancha("José Manuel Moreno"),
    Cancha("José María Minella"),
    Cancha("José María Moraños"),
    Cancha("José María Paz"),
    Cancha("José Martín Olaeta", alias=("José María Olaeta",),
           articulo="Estadio José Martín Olaeta"),
    Cancha("José Moraños"),
    Cancha("Juan Antonio Arias"),
    Cancha("Juan Carlos Brieva"),
    Cancha("Juan D. Perón"),
    Cancha("Juan Domingo Perón", alias=("Monumental Presidente Perón",),
           articulo="Estadio Monumental Presidente Perón"),
    Cancha("Juan Pablo Francia"),
    Cancha("Juan Pasquale", alias=("Juan Pasquele",),
           articulo="Estadio Juan Pasquale"),
    Cancha("Leandro N. Alem"),
    Cancha("Libertadores de América"),
    Cancha("Liga Mercedina"),
    Cancha("Lorenzo Arandilla"),
    Cancha("Malvinas Argentinas"),
    Cancha("Manuel y Ramón Núñez"),
    Cancha("Marcelo Bielsa", alias=("Coloso del Parque", "Coloso Marcelo Bielsa"),
           articulo="Estadio Marcelo Bielsa"),
    Cancha("Mario Alberto Kempes", alias=("Chateau Carreras",),
           articulo="Estadio Mario Alberto Kempes"),
    Cancha("Merlo"),
    Cancha("Miguel Sancho"),
    Cancha("Modesto Marrone"),
    Cancha("Monumental"),
    Cancha("Monumental José Fierro"),
    Cancha("Monumental de Villa Lynch"),
    Cancha("Municipal de la Ciudad de Luján"),
    Cancha("Municipal de Comodoro Rivadavia"),
    Cancha("Municipal Eva Perón"),
    Cancha("Municipal General San Martín"),
    Cancha("Municipal Gral. San Martín"),
    Cancha("Norman Lee"),
    Cancha("Nueva Chicago", alias=("República de Mataderos",),
           articulo="Estadio Nueva Chicago"),
    Cancha("Nueva España", alias=("España",),
           articulo="Estadio Nueva España"),
    Cancha("Nuevo Francisco Urbano"),
    Cancha("Nuevo Gasómetro", alias=("Pedro Bidegain",),
           articulo="Estadio Pedro Bidegain"),
    Cancha("Nuevo Monumental"),
    Cancha("Ofelia Rosenzuaig"),
    Cancha("Omar Higinio Sperdutti"),
    Cancha("Oscar C. Boero"),
    Cancha("Pablo Comelli", alias=("Talleres de Remedios de Escalada",),
           articulo="Estadio Pablo Comelli"),
    Cancha("Padre Ernesto Martearena"),
    Cancha("La Pedrera", alias=("Único La Pedrera", "Único de Villa Mercedes"),
           articulo="Estadio Único de Villa Mercedes"),
    Cancha("Plaza Manuel Anselmo Ocampo", alias=("Plaza Ocampo",),
           articulo="Estadio Plaza Manuel Anselmo Ocampo"),
    Cancha("Presbítero Bartolomé Grella", alias=("Bartolomé Grella",),
           articulo="Estadio Presbítero Bartolomé Grella"),
    Cancha("La Quema"),
    Cancha("Ramón Roque Martín"),
    Cancha("Raúl Conti"),
    Cancha("República de Italia"),
    Cancha("Ricardo Puga"),
    Cancha("Roberto N. Carminatti", alias=("Roberto Natalio Carminatti",),
           articulo="Estadio Roberto Nicolás Carminatti"),
    Cancha("Rodolfo Capocasa"),
    Cancha("Rubén Carlos Vallejos"),
    Cancha("Salomón Boeseldín"),
    Cancha("San Juan del Bicentenario"),
    Cancha("Saturnino Moure"),
    Cancha("Sol de América"),
    Cancha("Talleres"),
    Cancha("Talleres (RdE)"),
    Cancha("Tomás A. Ducó", alias=("Tomás Adolfo Ducó",),
           articulo="Estadio Tomás Adolfo Ducó"),
    Cancha("Tres de Febrero"),
    Cancha("Único Madre de Ciudades"),
    Cancha("Único de San Nicolás"),
    Cancha("El Viaducto", alias=("Julio Humberto Grondona",),
           articulo="Estadio Julio Humberto Grondona"),
    Cancha("Víctor Antonio Legrotaglie"),
    Cancha("La Visera de Cemento"),
)


def _armar_indice() -> dict[str, str]:
    indice: dict[str, str] = {}
    for c in PADRON:
        for n in (c.nombre,) + c.alias:
            ya = indice.setdefault(clave(n), c.nombre)
            if ya != c.nombre:
                raise ValueError(f"{n!r} lo reclaman dos canchas del padron: "
                                 f"{ya!r} y {c.nombre!r}")
    return indice


# Se arma la primera vez que se usa, y no al importar. Un padron con dos canchas que
# reclaman la misma clave revienta igual -- en el build, que unifica todas las filas,
# y en los tests --, pero no tumba la importacion de todo lo que importa este modulo.
# Armado al importar, un cambio en `clave` que juntara dos canchas cortaba pytest en
# la colecta: ningun test llegaba a mirarlo, y mutar.py lo contaba, con razon, como
# un mutante que nadie mato.
@lru_cache(maxsize=1)
def _indice() -> dict[str, str]:
    return _armar_indice()


def canonica(nombre: str) -> str:
    """Como se publica la cancha `nombre`: la del padron si es una de sus grafias,
    y si no, tal cual vino."""
    return _indice().get(clave(nombre), nombre)


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

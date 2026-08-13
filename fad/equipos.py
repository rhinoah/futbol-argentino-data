#!/usr/bin/env python3
"""
fad/equipos.py
==============
El padron de clubes: un nombre canonico por club y todos sus alias.

UNA sola estructura, `PADRON`. Los indices de busqueda se derivan de ella al
importar el modulo. La tentacion es tener "un dict para AFA, otro para Wikipedia,
otro para los nombres cortos": no. Cuando esos diccionarios se desincronizan
nadie se entera, porque cada uno anda bien por su cuenta.

POR QUE NO ALCANZA CON PARECERSE
--------------------------------
Adivinar por similitud de texto se probo y falla justo donde importa:

  * "Gimnasia" a secas es Gimnasia y Esgrima **La Plata** para AFA, pero Mendoza
    aparece como "Gimnasia (Mendoza)" contra "Gimnasia y Esgrima (M)" de
    Wikipedia. La palabra que comparten no decide cual es.
  * "Estudiantes" solo es el de La Plata; el de Rio Cuarto siempre lleva "(RC)".
  * "Independiente" e "Independiente Rivadavia" son dos clubes distintos y uno es
    prefijo del otro.

Emparejando por similitud, 26 de 60 partidos del Clausura 2026 quedaron sin
pareja. Con el padron escrito a mano, 60 de 60. Por eso va a mano.

UN RIESGO CONOCIDO: LOS ALIAS PELADOS
-------------------------------------
Varios alias son el nombre a secas -- "Sarmiento", "Talleres", "Gimnasia",
"Estudiantes" -- y salen del feed de la AFA, donde el contexto es Primera y ahi
hay uno solo de cada uno. Fuera de ese contexto son ambiguos: en la Copa
Argentina juegan tambien Sarmiento (LB), Gimnasia y Esgrima (C) y (J), y
Estudiantes (BA).

Por que no molesta hoy: la unica fuente que se PARSEA es Wikipedia, que siempre
los escribe desambiguados, y el CSV sale siempre con el nombre canonico. Los
alias pelados se usan nada mas para cruzar contra la AFA, que es Primera.

Si algun dia se parsea una fuente de ascenso que escriba "Sarmiento" a secas, hay
que resolver el alias por contexto y no globalmente. Queda anotado porque es la
clase de cosa que no falla: le da los partidos al club equivocado.

EL ID DE AFA
------------
`afa` es el numero con el que la AFA identifica al club en su propio feed
(`class="local e_124"`). No lo usamos para buscar, pero es una clave externa e
independiente de como se escriba el nombre, y sirve de testigo: si dos clubes del
padron terminan con el mismo id, o un id con dos clubes, algo se mezclo.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field


@dataclass(frozen=True)
class Equipo:
    nombre: str                              # el canonico: el que va al CSV
    afa: int | None = None                   # id en el feed de la AFA
    alias: tuple[str, ...] = field(default=())


# Los alias salen de fuentes reales, no de la imaginacion: el nombre largo y el
# corto del feed de la AFA, mas las variantes con las que Wikipedia titula.
PADRON: tuple[Equipo, ...] = (
    Equipo("Aldosivi", 122),
    Equipo("Argentinos Juniors", 2, ("Argentinos",)),
    Equipo("Atlético Tucumán", 815, ("Atl. Tucumán",)),
    Equipo("Banfield", 4, ("Club Atlético Banfield",)),
    Equipo("Barracas Central", 685, ("Barracas C.",)),
    Equipo("Belgrano", 124, ("Belgrano (C)", "Belgrano de Córdoba")),
    Equipo("Boca Juniors", 5, ("Boca",)),
    Equipo("Central Córdoba (SdE)", 1485,
           ("Central Córdoba (SE)", "C.Córdoba (SE)", "Central Córdoba")),
    Equipo("Defensa y Justicia", 129, ("Defensa",)),
    Equipo("Deportivo Riestra", 788, ("Dep. Riestra", "Riestra")),
    Equipo("Estudiantes (LP)", 7, ("Estudiantes", "Estudiantes de La Plata")),
    Equipo("Estudiantes (RC)", 834, ("Estudiantes RC", "Estudiantes de Río Cuarto")),
    Equipo("Gimnasia y Esgrima (LP)", 8,
           ("Gimnasia", "Gimnasia y Esgrima La Plata", "Gimnasia (LP)")),
    Equipo("Gimnasia y Esgrima (M)", 816,
           ("Gimnasia (Mendoza)", "Gimnasia (M)", "Gimnasia y Esgrima de Mendoza")),
    Equipo("Huracán", 100),
    Equipo("Independiente", 10),
    Equipo("Independiente Rivadavia", 664,
           ("Independiente Riv. (M)", "Indep.Mza.", "Independiente Rivadavia (M)")),
    Equipo("Instituto", 11, ("Instituto (C)",)),
    Equipo("Lanús", 12),
    Equipo("Newell's Old Boys", 13, ("Newell`s", "Newell's", "Newells Old Boys")),
    Equipo("Platense", 489),
    Equipo("Racing Club", 16, ("Racing",)),
    Equipo("River Plate", 17, ("River",)),
    Equipo("Rosario Central", 18, ("R. Central",)),
    Equipo("San Lorenzo", 19, ("San Lorenzo de Almagro",)),
    Equipo("Sarmiento (J)", 142, ("Sarmiento", "Sarmiento de Junín")),
    # "Tallleres", con tres eles, es un error de tipeo en la pagina de la Copa de
    # la Liga 2022 (juega contra Union). Va como alias porque el alias existe
    # justo para esto: la alternativa era que el build se frene todos los dias
    # por una letra de mas en una fuente que no controlamos. Si algun dia lo
    # corrigen, este alias no molesta a nadie.
    Equipo("Talleres (C)", 135, ("Talleres", "Talleres de Córdoba", "Tallleres (C)")),
    Equipo("Tigre", 136),
    Equipo("Unión", 137, ("Unión (SF)", "Unión de Santa Fe")),
    Equipo("Vélez Sarsfield", 20, ("Vélez", "Vélez Sársfield")),

    # --- clubes de otras divisiones, que entran por la Copa Argentina ---
    # Van SIN alias y sin id de AFA a proposito. El feed del que salieron los ids
    # y los nombres cortos es el de Primera y no los tiene, y un alias sin una
    # fuente que lo respalde es exactamente el error que este modulo trata de
    # evitar. Se agregan cuando alguna fuente los escriba distinto, no antes.
    #
    # Aca se ve para que sirve todo esto: hay CUATRO Gimnasia y Esgrima (LP, M,
    # C, J) mas un Gimnasia y Tiro que es otro club; TRES San Martin (F, SJ, T);
    # TRES Estudiantes (LP, RC, BA); DOS Sarmiento (J, LB).
    # Clubes que jugaron Primera entre 2016 y 2025 y hoy no estan. Sin ellos, el
    # historico no entra: Arsenal, Colon y Patronato solos son ~670 partidos.
    Equipo("Arsenal", alias=("Arsenal de Sarandí",)),
    Equipo("Chacarita Juniors"),
    Equipo("Colón", alias=("Colón (SF)", "Colón de Santa Fe")),
    Equipo("Patronato", alias=("Patronato (P)",)),
    Equipo("Quilmes"),

    Equipo("Acassuso"),
    Equipo("Agropecuario"),
    Equipo("Argentino (MM)"),
    Equipo("Argentino de Merlo"),
    Equipo("Atenas (RC)"),
    Equipo("Atlanta"),
    Equipo("Atlético de Rafaela"),
    Equipo("Chaco For Ever"),
    Equipo("Ciudad de Bolívar"),
    Equipo("Claypole"),
    Equipo("Deportivo Armenio"),
    Equipo("Deportivo Camioneros"),
    Equipo("Deportivo Madryn"),
    Equipo("Deportivo Maipú"),
    Equipo("Deportivo Morón"),
    Equipo("Deportivo Rincón"),
    Equipo("Estudiantes (BA)"),
    Equipo("Ferrocarril Midland"),
    Equipo("Gimnasia y Esgrima (C)"),
    Equipo("Gimnasia y Esgrima (J)"),
    Equipo("Gimnasia y Tiro (S)"),
    Equipo("Godoy Cruz"),
    Equipo("Ituzaingó"),
    Equipo("Olimpo"),
    Equipo("Real Pilar"),
    Equipo("San Martín (F)"),
    Equipo("San Martín (SJ)"),
    Equipo("San Martín (T)"),
    Equipo("San Miguel"),
    Equipo("Sarmiento (LB)"),
    Equipo("Sportivo Barracas"),
    Equipo("Sportivo Belgrano"),
    Equipo("Temperley"),
    Equipo("Tristán Suárez"),
)


class EquipoDesconocido(LookupError):
    """Un nombre que el padron no tiene. Se levanta a proposito en vez de dejarlo
    pasar: un club nuevo (un ascenso, un torneo que se suma) tiene que hacer
    ruido una vez, no colarse como un equipo distinto para siempre."""


def normalizar(nombre: str) -> str:
    """La forma en la que se comparan dos nombres.

    Saca acentos, mayusculas, puntos y las comillas raras -- la AFA escribe
    "Newell`s" con acento grave y Wikipedia "Newell's" con apostrofe, que para
    una comparacion literal son dos clubes.
    """
    # las comillas se unifican ANTES de tirar lo que no es ASCII: el apostrofe
    # tipografico (U+2019) no tiene equivalente ASCII, asi que si se limpia
    # primero desaparece en vez de convertirse, y "Newell's" queda "newells"
    # mientras que "Newell`s" -- con acento grave, que si es ASCII -- queda
    # "newell's". Dos claves distintas para el mismo club.
    s = nombre.replace("`", "'").replace("’", "'").replace("´", "'")
    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()
    s = s.lower().replace(".", " ")
    s = re.sub(r"\s*\(\s*", " (", s)
    s = re.sub(r"\s*\)", ")", s)
    return " ".join(s.split())


def _armar_indice() -> dict[str, Equipo]:
    """El indice se DERIVA del padron; no se escribe al lado.

    Si dos clubes se pelean un alias, se levanta aca y no en produccion: un alias
    ambiguo no da error, da un partido atribuido al club equivocado.
    """
    indice: dict[str, Equipo] = {}
    for eq in PADRON:
        for nombre in (eq.nombre, *eq.alias):
            clave = normalizar(nombre)
            if clave in indice and indice[clave] is not eq:
                raise ValueError(
                    f"el alias {nombre!r} lo reclaman dos clubes: "
                    f"{indice[clave].nombre!r} y {eq.nombre!r}")
            indice[clave] = eq
    return indice


_INDICE = _armar_indice()


def buscar(nombre: str) -> Equipo | None:
    """El club, o None si el padron no lo conoce."""
    return _INDICE.get(normalizar(nombre))


def canonical(nombre: str) -> str:
    """El nombre canonico. Levanta si no lo conoce -- es el default seguro."""
    eq = buscar(nombre)
    if eq is None:
        raise EquipoDesconocido(nombre)
    return eq.nombre


def conocido(nombre: str) -> bool:
    return buscar(nombre) is not None


def canonizar(nombre: str) -> str:
    """El canonico si lo conoce; el mismo nombre, intacto, si no.

    No levanta: se usa en el pipeline ANTES de validar, y el que no se pudo
    traducir tiene que llegar entero a `validar.nombres_en_el_padron` para que el
    aviso diga como vino escrito de la fuente. Devolver "" o inventar un nombre
    ahi seria esconder justo el dato que hace falta para arreglarlo.
    """
    eq = buscar(nombre)
    return eq.nombre if eq else nombre


def por_afa(id_afa: int) -> Equipo | None:
    return next((e for e in PADRON if e.afa == id_afa), None)

#!/usr/bin/env python3
"""
Testigo externo del padron: como nombra la AFA a los 30 clubes de Primera.

Capturado el 12/08/2026 del feed oficial
https://info.afa.org.ar/deposito/html/v3/htmlCenter/data/deportes/futbol/primeraa/pages/es/fixture.html
donde cada equipo viene como `class="local e_124"` con su nombre largo en el
`alt` del escudo y el corto en `.equipo`.

QUE HACE ACA
------------
Los tests de un padron unificado tienden a volverse tautologicos: si el caso de
prueba sale de la misma estructura que se esta probando, pasa siempre. Ya paso en
el proyecto hermano, donde un refactor de unificacion dejo ~49 tests comparando
una estructura consigo misma.

Esto es data de AFUERA. La AFA numera sus clubes con un sistema propio que no
sabe nada de como los escribe Wikipedia, asi que exigir que las dos numeraciones
se correspondan es una restriccion real: si un alias se le asigna al club
equivocado, el id deja de coincidir y el test cae.

Es una foto, no una fuente: no se actualiza sola y no debe hacerlo. Si el dia de
manana AFA renombra un club, este archivo sigue diciendo lo que decia el dia que
se escribio el padron, que es exactamente lo que un testigo tiene que hacer.
"""

# (id de AFA, nombre largo, nombre corto)
AFA = [
    (2, "Argentinos Juniors", "Argentinos"),
    (4, "Banfield", "Banfield"),
    (5, "Boca Juniors", "Boca"),
    (7, "Estudiantes", "Estudiantes"),
    (8, "Gimnasia", "Gimnasia"),
    (10, "Independiente", "Independiente"),
    (11, "Instituto", "Instituto"),
    (12, "Lanús", "Lanús"),
    (13, "Newell`s", "Newell`s"),
    (16, "Racing Club", "Racing"),
    (17, "River Plate", "River"),
    (18, "Rosario Central", "R. Central"),
    (19, "San Lorenzo", "San Lorenzo"),
    (20, "Vélez", "Vélez"),
    (100, "Huracán", "Huracán"),
    (122, "Aldosivi", "Aldosivi"),
    (124, "Belgrano", "Belgrano"),
    (129, "Defensa y Justicia", "Defensa"),
    (135, "Talleres", "Talleres"),
    (136, "Tigre", "Tigre"),
    (137, "Unión", "Unión"),
    (142, "Sarmiento", "Sarmiento"),
    (489, "Platense", "Platense"),
    (664, "Independiente Riv. (M)", "Indep.Mza."),
    (685, "Barracas Central", "Barracas C."),
    (788, "Dep. Riestra", "Riestra"),
    (815, "Atlético Tucumán", "Atl. Tucumán"),
    (816, "Gimnasia (Mendoza)", "Gimnasia (M)"),
    (834, "Estudiantes (RC)", "Estudiantes RC"),
    (1485, "Central Córdoba (SE)", "C.Córdoba (SE)"),
]

# Los 30 nombres tal como los titula Wikipedia en español, sacados de las paginas
# del Apertura y el Clausura 2026. La otra punta del padron.
WIKIPEDIA = [
    "Aldosivi", "Argentinos Juniors", "Atlético Tucumán", "Banfield",
    "Barracas Central", "Belgrano", "Boca Juniors", "Central Córdoba (SdE)",
    "Defensa y Justicia", "Deportivo Riestra", "Estudiantes (LP)",
    "Estudiantes (RC)", "Gimnasia y Esgrima (LP)", "Gimnasia y Esgrima (M)",
    "Huracán", "Independiente", "Independiente Rivadavia", "Instituto", "Lanús",
    "Newell's Old Boys", "Platense", "Racing Club", "River Plate",
    "Rosario Central", "San Lorenzo", "Sarmiento (J)", "Talleres (C)", "Tigre",
    "Unión", "Vélez Sarsfield",
]

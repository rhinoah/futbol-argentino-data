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

Ya paso: el Argentino A 2010-11 escribe los partidos con el nombre pelado y sus
36 partidos de "Juventud Unida" caian en el club de Primera C que se llama asi.
Se resuelve por pagina en `correcciones.HOMONIMOS`, no aca.

LOS ALIAS CON EL DESAMBIGUADOR DESPLEGADO
-----------------------------------------
La misma pagina escribe el club de dos maneras: los partidos usan la sigla
("Central Córdoba (SdE)") y la TABLA DE POSICIONES despliega el nombre entero
("Central Córdoba (Santiago del Estero)"). La celda de la tabla no lleva
wikilink, asi que no hay articulo con que resolverla y el club se queda sin
arbitro -- la tabla no se puede comparar contra los partidos de un club que el
padron no reconoce.

Son 34 nombres, todos del Argentino A y el Federal A, que es donde los clubes
comparten nombre. No se emparejaron por parecido sino por cardinalidad: la tabla
tiene tantas filas como clubes el plantel, asi que si en una zona sobra un solo
nombre desconocido y falta un solo club, la identidad esta forzada. Los tres que
no cerraban asi se resolvieron uno por uno, y uno de ellos ("Juventud Unida (SL)")
resulto ser Universitario y no el homonimo, que es exactamente el error que este
archivo viene avisando desde arriba.

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
    # "Aldovisi" es un error de tipeo de Wikipedia en la B Nacional 2008-09, con
    # la `s` y la `v` cambiadas de lugar. No lo encontro nadie leyendo: el padron
    # derivado del cruce con la segunda fuente vio 17 partidos de un id llamados
    # "Aldosivi" y uno "Aldovisi", y avisó que el id tenia votos contradictorios.
    Equipo("Aldosivi", 122, ("Aldovisi", "CA Aldosivi")),
    Equipo("Argentinos Juniors", 2, ("Argentinos",)),
    # Abreviaturas del Torneo Argentino A 2005-06. Cada una confirmada contra la
    # tabla de participantes de esa misma pagina, que da el articulo y la ciudad.
    Equipo("Atlético Tucumán", 815, ("Atl. Tucumán", "Atlético (T)")),
    Equipo("Banfield", 4, ("Club Atlético Banfield",)),
    # "Barracs Centreal" es un error de tipeo de la fuente, con DOS letras
    # cambiadas de lugar en la misma palabra.
    Equipo("Barracas Central", 685, ("Barracas C.", "Barracs Centreal", "B. Central")),
    Equipo("Belgrano", 124, ("Belgrano (C)", "Belgrano de Córdoba", "Belgrano (Cba)")),
    Equipo("Boca Juniors", 5, ("Boca",)),
    Equipo("Central Córdoba (SdE)", 1485,
           ("Central Córdoba (SE)", "C.Córdoba (SE)", "Central Córdoba",
            "Central Córdoba (Santiago del Estero)")),
    Equipo("Defensa y Justicia", 129, alias=("Defensa", "Def. Y Justicia", "Def. y Justicia",)),
    Equipo("Deportivo Riestra", 788, ("Dep. Riestra", "Riestra")),
    Equipo("Estudiantes (LP)", 7, ("Estudiantes", "Estudiantes de La Plata")),
    Equipo("Estudiantes (RC)", 834, ("Estudiantes RC", "Estudiantes de Río Cuarto",
                                     "Estudiantes (Río Cuarto)")),
    Equipo("Gimnasia y Esgrima (LP)", 8,
           ("Gimnasia", "Gimnasia y Esgrima La Plata", "Gimnasia (LP)")),
    Equipo("Gimnasia y Esgrima (M)", 816,
           ("Gimnasia (Mendoza)", "Gimnasia (M)", "Gimnasia y Esgrima de Mendoza",
            "Gimnasia y Esgrima (Mendoza)")),
    Equipo("Huracán", 100),
    Equipo("Independiente", 10),
    # "Independiente M." es Independiente de MENDOZA, y hay que tener cuidado:
    # "Independiente" a secas es otro club. Que sean el mismo no se dedujo por
    # parecido, que es justo lo que este modulo no hace. Lo confirmo la segunda
    # fuente, que le da a los 19 partidos un unico id llamado "CSIR" = Club
    # Sportivo Independiente Rivadavia, el titulo exacto del articulo.
    Equipo("Independiente Rivadavia", 664,
           ("Independiente Riv. (M)", "Indep.Mza.", "Independiente Rivadavia (M)",
            "Independiente M.", "Independiente M", "CSIR",
            # el cuadro de la Copa Argentina 2011-12 lo abrevia asi, sin enlazarlo
            "Independiente Riv.")),
    Equipo("Instituto", 11, ("Instituto (C)",)),
    Equipo("Lanús", 12),
    Equipo("Newell's Old Boys", 13, ("Newell`s", "Newell's", "Newells Old Boys")),
    Equipo("Platense", 489),
    Equipo("Racing Club", 16, ("Racing",)),
    Equipo("River Plate", 17, ("River",)),
    Equipo("Rosario Central", 18, ("R. Central",)),
    Equipo("San Lorenzo", 19, ("San Lorenzo de Almagro",)),
    Equipo("Sarmiento (J)", 142, ("Sarmiento", "Sarmiento de Junín", "Samiento")),
    # "Tallleres", con tres eles, es un error de tipeo en la pagina de la Copa de
    # la Liga 2022 (juega contra Union). Va como alias porque el alias existe
    # justo para esto: la alternativa era que el build se frene todos los dias
    # por una letra de mas en una fuente que no controlamos. Si algun dia lo
    # corrigen, este alias no molesta a nadie.
    Equipo("Talleres (C)", 135, ("Talleres", "Talleres de Córdoba", "Tallleres (C)",
                                "Talleres (Cba)")),
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
    Equipo("Chacarita Juniors", alias=("Chacarita", "Chacarita",)),
    Equipo("Colón", alias=("Colón (SF)", "Colón de Santa Fe")),
    Equipo("Patronato", alias=("Patronato (P)",)),
    Equipo("Quilmes"),

    # la pagina de Primera B 2024 escribe las DOS formas, 24 y 31 veces
    Equipo("Acassuso", alias=("Acasusso", "Accasuso", "Acasuso")),
    Equipo("Agropecuario"),
    Equipo("Argentino (MM)"),
    Equipo("Argentino de Merlo", alias=("Argentino (M)",)),
    Equipo("Atenas (RC)"),
    Equipo("Alumni (VM)", alias=("Alumni (Villa María)",)),      # Villa María, Córdoba
    Equipo("Atlanta"),
    Equipo("Atlético de Rafaela", alias=("Atlético Rafaela", "Atlético de Rafela",
                                        "Alético de Rafaela", "Atl. Rafaela",
                                        "Atl. de Rafaela")),
    Equipo("Chaco For Ever"),
    Equipo("Ciudad de Bolívar"),
    Equipo("Claypole"),
    Equipo("Deportivo Armenio", alias=("Dep. Armenio",)),
    # Primera C lo escribe de TRES formas en dos temporadas: con acento agudo,
    # sin acento, y con acento grave -- "Bolìvar", que en castellano no existe.
    Equipo("Barracas Bolívar", alias=("Barracas Bolivar", "Barracas Bolìvar")),
    Equipo("Deportivo Camioneros"),
    Equipo("Deportivo Madryn"),
    Equipo("Deportivo Maipú"),
    # Entro con la fase eliminatoria de la Primera C 2025, que estaba
    # invisible: su pagina usa `{{Partidos}}` y el parser solo miraba el
    # singular.
    Equipo("Deportivo Metalúrgico"),
    Equipo("Deportivo Morón", alias=("Deporitvo Morón", "Dep. Morón",)),   # typo en la fuente
    Equipo("Deportivo Rincón"),
    Equipo("Estudiantes (BA)"),
    Equipo("Ferrocarril Midland", alias=("Midland", "FC Midland")),
    Equipo("Gimnasia y Esgrima (C)"),
    # La B Nacional 2007-2011 lo escribe "Gimnasia (J)", sin enlace. Lo
    # confirma la segunda fuente: el id te930 es "Gimnasia de Jujuy".
    Equipo("Gimnasia y Esgrima (J)", alias=("Gimnasia (J)",)),
    Equipo("Gimnasia y Tiro (S)", alias=("Gimnasia y Tiro", "Gimnasia y Tiro (Salta)")),
    Equipo("Godoy Cruz"),
    Equipo("Ituzaingó"),
    Equipo("Olimpo"),
    Equipo("Real Pilar"),
    Equipo("San Martín (F)", alias=("San Martín (Formosa)",)),
    Equipo("San Martín (SJ)"),
    Equipo("San Martín (T)", alias=("San Martín (Tucumán)",)),
    Equipo("San Miguel"),
    Equipo("Sarmiento (LB)"),
    Equipo("Sportivo Barracas"),
    Equipo("Sportivo Belgrano", alias=("Sportivo Belgrano (SF)",
                                       "Sportivo Belgrano (San Francisco)",
                                       "Sp. Belgrano")),
    Equipo("Temperley"),
    Equipo("Tristán Suárez", alias=("T. Suárez",)),

    # entran por las ediciones viejas de la Copa Argentina, que mezclan mas
    # divisiones todavia.
    #
    # Aca vivia un "Liniers (SJ)" que NO era un tercer club sino el mismo de mas
    # abajo escrito de otra forma: los dos salen del articulo
    # `Club Social y Deportivo Liniers`, y por eso ahora es su alias. El otro,
    # `Liniers (BB)`, si es otro club y tiene otro articulo
    # (`Club Atlético Liniers`, de Bahia Blanca). Partido en dos, el mismo club
    # salia al CSV como "Liniers" en sus 360 partidos de Primera B y C y como
    # "Liniers (SJ)" en su unico partido de la Copa Argentina 2022.
    Equipo("Pacífico"),
    # entran por las primeras ediciones de la Copa Argentina
    Equipo("Alianza de Moldes"),      # Alianza Coronel Moldes, Córdoba
    Equipo("Andino"),
    Equipo("Jorge Gibson Brown"),    # Posadas, Misiones
    Equipo("Villa Cubas"),           # Catamarca
    # verificados por el articulo al que enlaza la pagina
    Equipo("CAI", alias=("C.A.I.", "Comisión de Actividades Infantiles")),
    Equipo("Unión (MdP)", alias=("Unión (Mar del Plata)",)),
    Equipo("Atlético Policial"),
    Equipo("Guaymallén"),
    Equipo("Racing (O)", alias=("Racing (Olavarría)",)),
    Equipo("Racing (T)"),
    Equipo("La Emilia"),
    Equipo("Viale FBC"),
    # jugaron Primera en la era Apertura/Clausura y hoy no estan
    Equipo("Huracán (TA)", alias=("Huracán (Tres Arroyos)",)),
    Equipo("Tiro Federal", alias=("Tiro Federal (R)", "Tiro Federal (Rosario)")),
    Equipo("Sportivo Rivadavia (VT)"),

    # --- historico del ascenso 2016-2023 ---
    # "Mitre" a secas va a Mitre (SdE) porque en TODOS los Federal A donde
    # aparece pelado, el unico Mitre del torneo es ese. El resto son erratas de
    # la fuente o el nombre acortado.
    Equipo("Altos Hornos Zapla"),
    Equipo("Atlético Paraná"),
    Equipo("Concepción FC"),
    Equipo("Deportivo Mandiyú"),
    Equipo("Deportivo Roca"),
    # "Desamprados", sin la segunda A, en un partido del Argentino A 2010-11.
    Equipo("Desamparados", alias=("Desamprados", "Sp. Desamparados")),
    Equipo("General Belgrano (SR)", alias=("General Belgrano (Santa Rosa)",)),
    # "Anotonio" es un typo del Argentino A 2012-13, en un solo partido.
    Equipo("Guaraní Antonio Franco", alias=("Guaraní Anotonio Franco",)),
    Equipo("Independiente (N)", alias=("Independiente (Neuquén)",)),
    Equipo("Juventud Unida (G)", alias=("Juventud Unida (Gualeguaychú)",)),
    # La pagina omite el desambiguador a veces, igual que con Sol de America.
    # Es el unico Libertad del padron.
    Equipo("Libertad (S)", alias=("Libertad", "Libertad (Sunchales)")),
    Equipo("Liniers (BB)"),
    Equipo("Rivadavia (L)", alias=("Rivadavia (Lincoln)",)),
    # "San Jorge (S)" NO es un club: es "San Jorge (T)" con la letra equivocada en
    # 2 de sus 16 partidos del Federal A 2016-17 (la pagina enlaza un solo
    # articulo, [[Club Social y Deportivo San Jorge]], de Tucuman).
    #
    # Estuvo un tiempo aca arriba como club propio, y vale la pena decir por que:
    # el nombre no estaba en el padron, `nombres_en_el_padron` lo marcaba, y
    # agregarlo callaba el aviso. Se agrego. Asi es como un typo de la fuente se
    # convierte en un club fantasma con dos partidos, y ningun chequeo protesta
    # porque el padron es justamente el que dice que clubes existen.
    # Lo encontro `localias_repartidas`, que no le pregunta al padron nada.
    Equipo("San Jorge (T)", alias=("San Jorge (S)", "San Jorge (Tucumán)")),
    Equipo("San Lorenzo de Alem"),
    Equipo("Sportivo Patria", alias=("Sp. Patria",)),
    Equipo("Sportivo Peñarol (C)"),
    Equipo("Tiro Federal (BB)", alias=("Tiro Federal (Bahía Blanca)",)),
    Equipo("Unión (VK)", alias=("Unión (Villa Krause)",)),
    Equipo("Unión Aconquija"),

    # --- los del Argentino A 2005-06, todos del interior ---
    # Diez clubes que el padron no tenia. Cada uno sale del ARTICULO que enlaza la
    # tabla de participantes de esa pagina, que ademas da la ciudad; el canonico es
    # como lo escriben las TABLAS de los torneos, no el titulo del articulo.
    #
    # Los alias son SOLO los que aparecen de verdad como celda de equipo en las 293
    # paginas de la cache. Se probaron veintisiete y quedaron cinco: los otros
    # veintidos no resolvian una sola fila, y un alias que no sostiene nada es un
    # choque esperando.
    #
    # Y tres que NO van, medidos:
    #   "Candelaria"             7 de 8 veces apunta a la LOCALIDAD (Misiones)
    #   "La Plata"               1 de 8 a la ciudad y 1 al partido
    #   "Club Atlético Juventud" es pagina de DESAMBIGUACION: hay otros cuatro
    # Los tres resuelven igual, por el articulo, que es donde tienen que resolver.
    Equipo("Atlético Candelaria",
           alias=("At. Candelaria", "Atl. Candelaria", "At: Candelaria")),
    Equipo("General Paz Juniors", alias=("General Paz Junior",)),
    # "(CR)" es Comodoro Rivadavia. Convive con Huracan (Parque Patricios),
    # Huracan (TA) de Tres Arroyos y Huracan Las Heras: son cuatro clubes.
    Equipo("Huracán (CR)"),
    # "(P)" ya significa cuatro ciudades en este padron -- Parana, Posadas, Perico
    # y Pergamino --. No choca porque la base difiere en los cuatro, pero a ojo la
    # letra sola ya no dice nada.
    Equipo("Juventud (P)"),
    Equipo("La Florida"),
    # El punto importa: `normalizar` lo cambia por espacio, asi que "La Plata F.C."
    # y "La Plata FC" son dos claves distintas y hacen falta las dos.
    Equipo("La Plata FC", alias=("La Plata F.C.",)),
    Equipo("Luján de Cuyo"),
    Equipo("Ñuñorco"),
    Equipo("Real Arroyo Seco"),
    # El cuarto Talleres del corpus, con Cordoba, Remedios de Escalada y Frias.
    Equipo("Talleres (P)"),

    # --- el ascenso: Primera Nacional, Primera B, Primera C y Federal A ---
    # Sin id de AFA: el feed del que salieron los ids es el de Primera y no los
    # tiene. Casi todos sin alias tampoco -- solo llevan los que hicieron falta,
    # y cada uno dice por que.
    #
    # Ojo con los que se parecen y NO son: Ferro Carril Oeste (Caballito) y Ferro
    # Carril Oeste (GP) (General Pico); Defensores de Belgrano y Defensores de
    # Belgrano (VR); Central Cordoba (R) de Rosario y el (SdE) de Santiago;
    # Juventud Unida y Juventud Unida Universitario; Union (S) de Sunchales y el
    # Union de Santa Fe. Son diez clubes distintos, no cinco.

    Equipo('9 de Julio (R)'),
    Equipo('All Boys'),
    Equipo('Almagro'),
    Equipo('Almirante Brown'),
    Equipo('Alvarado'),
    Equipo('Argentino de Quilmes'),
    Equipo('Atlas'),
    Equipo('Atlético Escobar'),
    Equipo('Bartolomé Mitre (P)'),
    Equipo('Ben Hur'),
    Equipo('Berazategui'),
    Equipo('Boca Unidos'),
    # Abreviaturas del Campeonato de Primera B 2010-11, que escribe la mitad
    # de sus fechas con el nombre cortado. Cada una se verifico contra el
    # plantel del propio torneo: la forma larga esta ahi y los partidos suman.
    Equipo('Brown de Adrogué', alias=("Brown (A)",)),
    Equipo('Cañuelas'),
    Equipo('Central Ballester'),
    Equipo('Central Córdoba (R)'),
    # "Centrl Norte", sin la A, en un partido del Argentino A 2010-11. Es el
    # unico Central Norte del padron, asi que el typo no puede apuntar a otro.
    Equipo('Central Norte (S)', alias=('Centrl Norte', 'Central Norte (Salta)')),
    Equipo('Centro Español'),
    # "Cipoletti", con una L, en dos partidos del Argentino A 2010-11.
    Equipo('Cipolletti', alias=('Cipoletti',)),
    Equipo('Colegiales'),
    Equipo('Comunicaciones'),
    Equipo('Costa Brava'),
    Equipo('Crucero del Norte'),
    Equipo('Círculo Deportivo'),
    Equipo('Defensores Unidos'),
    Equipo('Defensores de Belgrano',
           # `Def. de Belgrano` a secas es ESTE, el de Villa Crespo, y no el de
           # Villa Ramallo. Lo dice la pagina que lo usa sin enlazar: el cuadro de
           # la Copa Argentina 2011-12 le pone `{{bandera|Buenos Aires}}`, la de la
           # ciudad, mientras que al de Ramallo le pone `Provincia de Buenos
           # Aires`. Y en la Copa 2015-16 el mismo nombre corto SI va enlazado, a
           # `Club Atlético Defensores de Belgrano`, que es el de Villa Crespo.
           # El otro nunca aparece pelado: siempre lleva su `(VR)`, que ya es su
           # alias. Sin esto, el unico nombre del cuadro que el padron no
           # reconocia quedaba abierto para siempre.
           alias=("D. de Belgrano", "Def. de Belgrano")),
    Equipo('Defensores de Belgrano (VR)',
           # `Def. de Belgrano (VR)` es del cuadro y va con el sufijo puesto: es lo
           # unico que lo separa de `Defensores de Belgrano`, que en la Copa
           # Argentina 2015-16 juega en la MISMA pagina.
           alias=('Defensores de Belgrano (Villa Ramallo)', 'Def. de Belgrano (VR)')),
    Equipo("Defensores de Cambaceres", alias=("Cambaceres",)),
    Equipo("Defensores de Pronunciamiento",
           alias=("Defensores de Pronunciamento", "Def. de Pronunciamiento", "DEPRO")),
    Equipo('Defensores de Vilelas'),
    Equipo('Deportivo Español', alias=("Dep. Español",)),
    Equipo('Deportivo Merlo'),
    Equipo('Deportivo Paraguayo'),
    Equipo('Dock Sud'),
    Equipo('Douglas Haig'),
    Equipo('El Linqueño'),
    Equipo('El Porvenir'),
    Equipo('Estrella del Sur'),
    Equipo('Excursionistas'),
    Equipo('FADEP'),
    # "Ferro" a secas es un alias PELADO, de los que este modulo dice arriba que
    # hay que mirar con desconfianza: hay dos Ferro Carril Oeste. Antes de
    # ponerlo se midio donde aparece, y por eso esta:
    #   * pelado sale en UNA sola pagina de las 96 del catalogo -- la B Nacional
    #     2008-09 -- y son sus 38 partidos.
    #   * el de General Pico se escribe "Ferro Carril Oeste (GP)" en las 235
    #     veces que juega. Pelado, nunca.
    #   * y aunque algun dia lo escribieran asi, `buscar` resuelve primero por el
    #     ARTICULO, y el de General Pico tiene el suyo en ARTICULOS. El alias
    #     solo decide cuando el nombre viene sin enlace, que es el caso de esta
    #     pagina: no enlaza ningun equipo.
    # "Ferro CO" es el nombre corto de la segunda fuente, y el usuario confirmo
    # que es el de Caballito.
    Equipo('Ferro Carril Oeste', alias=("Ferro", "Ferro CO")),
    Equipo('Ferro Carril Oeste (GP)',
           alias=('Ferro Carril Oeste (General Pico)',)),
    Equipo('Flandria'),
    Equipo('Fénix'),
    Equipo('General Lamadrid'),
    Equipo('Germinal'),
    Equipo("Guillermo Brown", alias=("Guillermon Brown", "Guillermo Brown (PM)")),
    Equipo("Gutiérrez", alias=("Gutiérrez SC",)),
    Equipo('Güemes (SdE)', alias=('Güemes (Santiago del Estero)', 'Güemes')),
    Equipo('Huracán Las Heras'),
    Equipo('Independiente (C)'),
    Equipo("J. J. de Urquiza", alias=("J. J. Urquiza",)),
    Equipo('Juventud Antoniana'),
    Equipo('Juventud Unida'),
    # "Juventud Unida (SL)" es ESTE y no el `Juventud Unida` de arriba: el
    # Argentino A 2011-12 lo escribe con el wikilink puesto,
    # `[[Club Atlético Juventud Unida Universitario|Juventud Unida (SL)]]`.
    Equipo("Juventud Unida Universitario", alias=("Juventud U. U.", "Juventud Unida U.",
                                                  "Juv. U. Universitario",
                                                  "Juventud Unida (SL)")),
    Equipo('Kimberley'),
    Equipo('Leandro N. Alem'),
    Equipo('Leones de Rosario'),
    Equipo('Liniers', alias=('Liniers (SJ)',)),
    Equipo('Los Andes'),
    Equipo('Lugano'),
    Equipo('Luján'),
    Equipo('Mercedes'),
    Equipo("Mitre (SdE)", alias=("Mitre", "Mitre (Santiago del Estero)")),
    Equipo('Muñiz'),
    Equipo('Nueva Chicago'),
    Equipo('Puerto Nuevo'),
    Equipo('Racing (C)', alias=('Racing (Córdoba)',)),
    Equipo("Ramón Santamarina", alias=("Santamarina",)),
    Equipo('Sacachispas'),
    Equipo('San Martín (B)'),
    Equipo('San Telmo'),
    Equipo('Sansinena'),
    Equipo('Sarmiento (R)', alias=('Sarmiento (Resistencia)',)),
    Equipo("Sol de Mayo (V)", alias=("Sol de Mayo",)),
    Equipo('Sportivo Estudiantes (SL)', alias=('Sportivo Estudiantes (San Luis)',)),
    Equipo("Sportivo Italiano", alias=("Deportivo Italiano", "Sp. Italiano")),
    # "Sportivo AC" es Sportivo Atlético Club, el nombre formal de este. No sale
    # del parecido: la fila de la Reválida del Federal A 2017-18 dice
    # G=5 E=2 P=3 GF=13 GC=8 y esos son sus numeros exactos, contra 3-2-3 y 12:11
    # de Sportivo Belgrano, que era el otro Sportivo de esa tabla.
    Equipo('Sportivo Las Parejas', alias=('Sportivo AC',)),
    # Remedios de Escalada. La Primera C 2009-10 lo abrevia "(RE)" y el resto del
    # catalogo "(RdE)"; es el mismo club y el mismo articulo.
    Equipo('Talleres (RdE)', alias=("Talleres (RE)",)),
    Equipo('Tucumán Central'),
    Equipo('UAI Urquiza'),
    Equipo("Unión (S)", alias=("Unión (Sunchales)",)),
    Equipo('Victoriano Arenas'),
    Equipo('Villa Dálmine'),
    Equipo('Villa Mitre', alias=("Villa Mitre (BB)",)),
    Equipo('Villa San Carlos', alias=("V. San Carlos",)),
    Equipo('Yupanqui'),

    # la pagina lo escribe de las dos formas
    Equipo('Deportivo Laferrere', alias=('Laferrere',)),
    # idem
    Equipo('Argentino de Rosario', alias=('Argentino (R)',)),
    # una sola aparicion contra 37 de "(SM)" en la MISMA pagina del Federal A 2024
    Equipo('San Martín (SM)', alias=('San Martín (M)',)),
    # error de tipeo en la fuente
    # "Gimnasia (CdU)" -- sin el "y Esgrima" -- en un partido del Argentino A
    # 2010-11. El desambiguador alcanza: es el unico CdU.
    Equipo("Gimnasia y Esgrima (CdU)",
           alias=("Gimnasia y Esgrisma (CDU)", "Gimmasia y Esgrima (CdU)",
                  "Gimnasia (CdU)", "Gimnasia y Esgrima (CU)",
                  "Gimnasia y Esgrima (Concepción del Uruguay)")),
    # la pagina omite la provincia a veces
    Equipo('Sol de América (F)', alias=('Sol de América',)),
)


# Titulo de articulo de Wikipedia -> club. Es el testigo por temporada: la
# pagina de cada torneo enlaza a sus clubes, y ese enlace dice CUAL es sin
# depender de la division ni del anio. "Estudiantes" a secas apunta a tres
# articulos distintos segun la pagina; el articulo, a uno solo.
#
# Se genero recorriendo el catalogo y quedandose SOLO con los nombres visibles
# que apuntan a un unico articulo en todo el corpus -- los que apuntan a varios
# no sirven de testigo y quedaron afuera a proposito.
ARTICULOS: dict[str, str] = {
    # Los cuatro que solo aparecen en el CUADRO DE LLAVES, donde la pagina los
    # escribe mas corto que en la grilla -- `Def. de Belgrano (VR)`,
    # `Estudiantes (SL)`, `Sarmiento (Junín)`, `Sportivo Rivadavia` --. Entran
    # por el ARTICULO y no por el nombre a proposito: `Def. de Belgrano` a secas
    # es ambiguo entre dos clubes del padron, y el articulo es identidad y no
    # parecido. Las cuatro identidades las confirma la grilla de su propia
    # pagina, que juega esos mismos partidos con el mismo articulo.
    'Club Atlético y Social Defensores de Belgrano': 'Defensores de Belgrano (VR)',
    'Club Sportivo Estudiantes (San Luis)': 'Sportivo Estudiantes (SL)',
    'Club Atlético Sarmiento (Junín)': 'Sarmiento (J)',
    'Club Sportivo Bernardino Rivadavia': 'Sportivo Rivadavia (VT)',
    'Arsenal Fútbol Club': 'Arsenal',
    'Asociación Cultural y Deportiva Altos Hornos Zapla': 'Altos Hornos Zapla',
    'Asociación Civil Leones de Rosario Fútbol Club': 'Leones de Rosario',
    'Asociación Mutual Social y Deportiva Atlético de Rafaela': 'Atlético de Rafaela',
    'Asociación Social y Deportiva Justo José de Urquiza': 'J. J. de Urquiza',
    'Atlético Club San Martín': 'San Martín (SM)',
    'Atlético Escobar Fútbol Club': 'Atlético Escobar',
    'Cañuelas Fútbol Club': 'Cañuelas',
    'Centro Juventud Antoniana': 'Juventud Antoniana',
    'Centro Social y Recreativo Español': 'Centro Español',
    'Club Agropecuario Argentino': 'Agropecuario',
    'Club Almagro': 'Almagro',
    'Club Almirante Brown': 'Almirante Brown',
    'Club Atlético 9 de Julio (Rafaela)': '9 de Julio (R)',
    'Club Atlético Acassuso': 'Acassuso',
    'Club Atlético Aldosivi': 'Aldosivi',
    'Club Atlético All Boys': 'All Boys',
    'Club Atlético Alvarado': 'Alvarado',
    'Club Atlético Argentino (Rosario)': 'Argentino de Rosario',
    'Club Atlético Argentino de Quilmes': 'Argentino de Quilmes',
    'Club Atlético Atlanta': 'Atlanta',
    'Club Atlético Atlas': 'Atlas',
    'Club Atlético Banfield': 'Banfield',
    'Club Atlético Barracas Central': 'Barracas Central',
    'Club Atlético Bartolomé Mitre (Posadas)': 'Bartolomé Mitre (P)',
    'Club Atlético Belgrano': 'Belgrano',
    'Club Atlético Boca Juniors': 'Boca Juniors',
    'Club Atlético Boca Unidos': 'Boca Unidos',
    'Club Atlético Brown': 'Brown de Adrogué',
    'Club Atlético Central Córdoba (Rosario)': 'Central Córdoba (R)',
    'Club Atlético Central Córdoba (Santiago del Estero)': 'Central Córdoba (SdE)',
    'Club Atlético Central Norte (Salta)': 'Central Norte (S)',
    'Club Atlético Chacarita Juniors': 'Chacarita Juniors',
    'Club Atlético Chaco For Ever': 'Chaco For Ever',
    'Club Atlético Claypole': 'Claypole',
    'Club Atlético Colegiales (Munro)': 'Colegiales',
    'Club Atlético Colón': 'Colón',
    'Club Atlético Defensores Unidos': 'Defensores Unidos',
    'Club Atlético Defensores de Vilelas': 'Defensores de Vilelas',
    'Club Atlético Deportivo Paraguayo': 'Deportivo Paraguayo',
    'Club Atlético Douglas Haig': 'Douglas Haig',
    'Club Atlético El Linqueño': 'El Linqueño',
    'Club Atlético Estudiantes': 'Estudiantes (BA)',
    'Club Atlético Ferrocarril Midland': 'Ferrocarril Midland',
    'Club Atlético Fénix': 'Fénix',
    'Club Atlético General Lamadrid': 'General Lamadrid',
    'Club Atlético Germinal': 'Germinal',
    'Club Atlético Gimnasia y Esgrima (Jujuy)': 'Gimnasia y Esgrima (J)',
    'Club Atlético Gimnasia y Esgrima (Mendoza)': 'Gimnasia y Esgrima (M)',
    'Club Atlético Güemes': 'Güemes (SdE)',
    'Club Atlético Huracán': 'Huracán',
    'Club Atlético Huracán Las Heras': 'Huracán Las Heras',
    'Club Atlético Independiente (Chivilcoy)': 'Independiente (C)',
    'Club Atlético Independiente (Neuquén)': 'Independiente (N)',
    'Club Atlético Juventud Unida Universitario': 'Juventud Unida Universitario',
    'Club Atlético Kimberley': 'Kimberley',
    'Club Atlético Lanús': 'Lanús',
    'Alianza Coronel Moldes': 'Alianza de Moldes',
    'Club Jorge Gibson Brown': 'Jorge Gibson Brown',
    'Club Sportivo Villa Cubas (Catamarca)': 'Villa Cubas',
    'Club Atlético Liniers': 'Liniers (BB)',
    # Los siete de abajo no cambian ningun partido de hoy: los siete resuelven ya
    # por su nombre pelado, que es justo el problema. Son los articulos de los
    # clubes cuyo nombre canonico NO lleva desambiguador teniendo homonimos que
    # si -- Independiente e Independiente (C), Union y Union (S), Ferro Carril
    # Oeste y el (GP) --, y sobre 4307 lados de partido que llevan uno de esos
    # nombres, el articulo hoy desambigua en el 16%: en el resto `buscar` cae al
    # nombre y el enlace queda de adorno. Entran para que el dia que una pagina
    # escriba el nombre pelado del club equivocado, el articulo lo desmienta.
    'Club Atlético Independiente': 'Independiente',
    'Club Ferro Carril Oeste': 'Ferro Carril Oeste',
    'Club Atlético Unión (Santa Fe)': 'Unión',
    'Club Atlético Defensores de Belgrano': 'Defensores de Belgrano',
    'Club Social y Deportivo Liniers': 'Liniers',
    'Club Atlético Tiro Federal Argentino': 'Tiro Federal',
    'Club Deportivo y Social Juventud Unida': 'Juventud Unida',
    'Club Atlético Los Andes': 'Los Andes',
    'Club Atlético Lugano': 'Lugano',
    'Club Atlético Mitre (Santiago del Estero)': 'Mitre (SdE)',
    'Club Atlético Nueva Chicago': 'Nueva Chicago',
    'Club Atlético Paraná': 'Atlético Paraná',
    'Club Atlético Patronato de la Juventud Católica': 'Patronato',
    'Club Atlético Platense': 'Platense',
    'Club Atlético Puerto Nuevo': 'Puerto Nuevo',
    # Racing de CORDOBA, no el de Avellaneda. El de Avellaneda se llama "Racing
    # Club" a secas y su articulo es ese; "Club Atlético Racing" es el cordobes.
    # Mientras esto apunto a Avellaneda, 248 partidos de Racing de Cordoba
    # quedaron a nombre suyo -- en Primera Nacional 2007/2023/2025/2026,
    # Argentino A 2011/2012 y Federal A 2018/2021/2022, torneos que Avellaneda no
    # jugo nunca. Medido: las 22 paginas de la cache que enlazan este articulo lo
    # muestran como "Racing", "Racing (C)", "Racing (Cba.)" o "Racing (Córdoba)",
    # y ninguna como el de Avellaneda.
    'Club Atlético Racing': 'Racing (C)',
    'Club Atlético River Plate': 'River Plate',
    'Club Atlético Rosario Central': 'Rosario Central',
    'Club Atlético San Lorenzo de Alem': 'San Lorenzo de Alem',
    'Club Atlético San Lorenzo de Almagro': 'San Lorenzo',
    'Club Atlético San Martín (San Juan)': 'San Martín (SJ)',
    'Club Atlético San Martín (Tucumán)': 'San Martín (T)',
    'Club Atlético San Telmo': 'San Telmo',
    'Club Atlético Sansinena Social y Deportivo': 'Sansinena',
    'Club Atlético Sarmiento (La Banda)': 'Sarmiento (LB)',
    'Club Atlético Social y Deportivo Camioneros': 'Deportivo Camioneros',
    'Club Atlético Talleres (Córdoba)': 'Talleres (C)',
    'Club Atlético Talleres (Remedios de Escalada)': 'Talleres (RdE)',
    'Club Atlético Temperley': 'Temperley',
    'Club Atlético Tigre': 'Tigre',
    'Club Atlético Tucumán': 'Atlético Tucumán',
    'Club Atlético Tucumán Central': 'Tucumán Central',
    'Club Atlético Unión (Sunchales)': 'Unión (S)',
    'Club Atlético Unión (Villa Krause)': 'Unión (VK)',
    'Club Atlético Victoriano Arenas': 'Victoriano Arenas',
    'Club Atlético Villa San Carlos': 'Villa San Carlos',
    'Club Atlético Vélez Sarsfield': 'Vélez Sarsfield',
    'Club Cipolletti': 'Cipolletti',
    'Club Ciudad de Bolívar': 'Ciudad de Bolívar',
    'Club Defensores de Cambaceres': 'Defensores de Cambaceres',
    'Club Defensores de Pronunciamiento': 'Defensores de Pronunciamiento',
    'Club Deportivo Argentino (Monte Maíz)': 'Argentino (MM)',
    'Club Deportivo Armenio': 'Deportivo Armenio',
    'Club Deportivo Español de Buenos Aires': 'Deportivo Español',
    'Club Deportivo Godoy Cruz Antonio Tomba': 'Godoy Cruz',
    'Club Atlético Alumni': 'Alumni (VM)',
    'Club Deportivo Guaraní Antonio Franco': 'Guaraní Antonio Franco',
    'Club Deportivo Juventud Unida': 'Juventud Unida (G)',
    'Club Deportivo Libertad': 'Libertad (S)',
    'Club Deportivo Maipú': 'Deportivo Maipú',
    'Club Deportivo Mandiyú': 'Deportivo Mandiyú',
    'Club Deportivo Metalúrgico': 'Deportivo Metalúrgico',
    'Club Deportivo Morón': 'Deportivo Morón',
    'Club Deportivo Riestra': 'Deportivo Riestra',
    'Club Deportivo UAI Urquiza': 'UAI Urquiza',
    'Club Deportivo y Mutual Leandro N. Alem': 'Leandro N. Alem',
    'Club El Porvenir': 'El Porvenir',
    'Club Estudiantes de La Plata': 'Estudiantes (LP)',
    'Club Ferro Carril Oeste (General Pico)': 'Ferro Carril Oeste (GP)',
    'Club General Belgrano': 'General Belgrano (SR)',
    'Club Gimnasia y Esgrima (Concepción del Uruguay)': 'Gimnasia y Esgrima (CdU)',
    'Club Mutual Crucero del Norte': 'Crucero del Norte',
    'Club Rivadavia': 'Rivadavia (L)',
    # Los diez del Argentino A 2005-06. Dos tienen dos titulos: uno es redireccion
    # del otro, y las paginas usan los dos.
    'Club Atlético Candelaria': 'Atlético Candelaria',
    'Club Atlético General Paz Juniors': 'General Paz Juniors',
    'Club Atlético Huracán (Comodoro Rivadavia)': 'Huracán (CR)',
    'Huracán de Comodoro Rivadavia': 'Huracán (CR)',
    'Club Atlético Juventud (Pergamino)': 'Juventud (P)',
    'Club Atlético Ñuñorco': 'Ñuñorco',
    'Club Atlético Talleres (Perico)': 'Talleres (P)',
    'Club Social y Deportivo La Florida': 'La Florida',
    'Club Social y Deportivo Real Arroyo Seco': 'Real Arroyo Seco',
    'La Plata Fútbol Club': 'La Plata FC',
    'Asociación Atlética Luján de Cuyo': 'Luján de Cuyo',
    'Asociación Atlético Luján de Cuyo': 'Luján de Cuyo',
    # El Argentino A 2010-11 lo enlaza asi y escribe "Rivadavia" a secas, que
    # el padron no resuelve -- hay tres. El articulo si.
    'Rivadavia de Lincoln': 'Rivadavia (L)',
    'Club Social y Atlético Guillermo Brown': 'Guillermo Brown',
    'Club Social y Cultural Deportivo Laferrere': 'Deportivo Laferrere',
    'Club Social y Deportivo Central Ballester': 'Central Ballester',
    'Club Social y Deportivo Defensa y Justicia': 'Defensa y Justicia',
    'Club Social y Deportivo Flandria': 'Flandria',
    'Club Social y Deportivo General Roca': 'Deportivo Roca',
    'Club Social y Deportivo Madryn': 'Deportivo Madryn',
    'Club Social y Deportivo Merlo': 'Deportivo Merlo',
    'Club Social y Deportivo San Jorge': 'San Jorge (T)',
    'Club Social y Deportivo San Martín': 'San Martín (B)',
    'Club Social y Deportivo Sol de Mayo': 'Sol de Mayo (V)',
    'Club Social y Deportivo Yupanqui': 'Yupanqui',
    'Club Sol de América (Formosa)': 'Sol de América (F)',
    'Club Sportivo Barracas': 'Sportivo Barracas',
    'Club Sportivo Ben Hur': 'Ben Hur',
    'Club Sportivo Desamparados': 'Desamparados',
    'Club Sportivo Dock Sud': 'Dock Sud',
    'Club Sportivo General San Martín': 'San Martín (F)',
    'Club Sportivo Independiente Rivadavia': 'Independiente Rivadavia',
    'Club Sportivo Italiano': 'Sportivo Italiano',
    'Club Sportivo Patria': 'Sportivo Patria',
    'Club Sportivo y Biblioteca Atenas': 'Atenas (RC)',
    'Club Tiro Federal': 'Tiro Federal (BB)',
    'Club Unión Aconquija': 'Unión Aconquija',
    'Club Villa Dálmine': 'Villa Dálmine',
    'Club Villa Mitre': 'Villa Mitre',
    'Club de Gimnasia y Esgrima de La Plata': 'Gimnasia y Esgrima (LP)',
    'Club de Gimnasia y Tiro': 'Gimnasia y Tiro (S)',
    'Club y Biblioteca Ramón Santamarina': 'Ramón Santamarina',
    'Concepción Fútbol Club': 'Concepción FC',
    'Círculo Deportivo de Comandante Nicanor Otamendi': 'Círculo Deportivo',
    'Fundación Amigos por el Deporte': 'FADEP',
    'Gregorio de Laferrere (Buenos Aires)': 'Deportivo Laferrere',
    'Gutiérrez Sport Club': 'Gutiérrez',
    'Instituto Atlético Central Córdoba': 'Instituto',
    'Racing Club (Trelew)': 'Racing Club',
    'Real Pilar Fútbol Club': 'Real Pilar',
    'Sacachispas Fútbol Club': 'Sacachispas',
}


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


def _armar_indice_de_articulos() -> dict[str, Equipo]:
    """Igual que el de nombres, derivado y con la misma guarda: si un articulo
    apunta a un club que el padron no tiene, revienta al importar."""
    indice = {}
    for articulo, nombre in ARTICULOS.items():
        eq = _INDICE.get(normalizar(nombre))
        if eq is None:
            raise ValueError(f"el articulo {articulo!r} apunta a {nombre!r}, "
                             "que no esta en el padron")
        indice[normalizar(articulo)] = eq
    return indice


_POR_ARTICULO = _armar_indice_de_articulos()


def buscar(nombre: str, articulo: str = "") -> Equipo | None:
    """El club, o None si el padron no lo conoce.

    El ARTICULO manda sobre el nombre visible, y esa prioridad es todo el punto.
    "Estudiantes" a secas apunta a tres articulos distintos segun la pagina: en
    Primera es el de La Plata, en Primera B el de Caseros. Resolviendo por el
    nombre, media division termina en la historia del club equivocado -- y no
    falla, solo miente. Resolviendo por el articulo, cada temporada dice cual es
    la suya, y los ascensos y descensos dejan de importar: el enlace de la pagina
    del anio que viene apunta al mismo lugar.
    """
    if articulo:
        eq = _POR_ARTICULO.get(normalizar(articulo))
        if eq is not None:
            return eq
    return _INDICE.get(normalizar(nombre))


def canonical(nombre: str) -> str:
    """El nombre canonico. Levanta si no lo conoce -- es el default seguro."""
    eq = buscar(nombre)
    if eq is None:
        raise EquipoDesconocido(nombre)
    return eq.nombre


def conocido(nombre: str, articulo: str = "") -> bool:
    return buscar(nombre, articulo) is not None


def canonizar(nombre: str, articulo: str = "") -> str:
    """El canonico si lo conoce; el mismo nombre, intacto, si no.

    No levanta: se usa en el pipeline ANTES de validar, y el que no se pudo
    traducir tiene que llegar entero a `validar.nombres_en_el_padron` para que el
    aviso diga como vino escrito de la fuente. Devolver "" o inventar un nombre
    ahi seria esconder justo el dato que hace falta para arreglarlo.
    """
    eq = buscar(nombre, articulo)
    return eq.nombre if eq else nombre


def por_afa(id_afa: int) -> Equipo | None:
    return next((e for e in PADRON if e.afa == id_afa), None)


# `[[Articulo|Nombre visible]]`, que es la unica forma que importa aca: si el
# enlace no tiene nombre visible, no hay dos testigos que puedan contradecirse.
_ENLACE_CON_NOMBRE = re.compile(r"\[\[\s*([^\]|#]+?)\s*\|\s*([^\]]+?)\s*\]\]")
_CALIFICADOR = re.compile(r"\(")


def articulos_que_contradicen(texto: str) -> list[str]:
    """Enlaces donde el nombre visible y el articulo apuntan a clubes distintos.

    El indice de articulos existe para desambiguar un nombre pelado, asi que que
    los dos testigos difieran es lo NORMAL: `[[Club Atlético Estudiantes|Estudiantes]]`
    dice "de los tres Estudiantes, este". No hay nada que avisar ahi.

    Lo que si es un error es cuando el nombre visible YA viene desambiguado y aun
    asi difiere. `[[Club Atlético Racing|Racing (C)]]`: ese "(C)" lo escribio un
    editor a proposito para decir Cordoba, y el indice contestaba Avellaneda. Uno
    de los dos esta mal, y mientras nadie mirara, 248 partidos de Racing de
    Cordoba quedaron a nombre del otro.

    Las tres condiciones juntas son lo que lo deja casi sin ruido, y hacen falta
    las tres:
      - el nombre visible trae su propio parentesis (desambiguacion explicita)
      - el articulo esta en el indice
      - el nombre SOLO tambien resuelve a un club del padron
    Sin la tercera entran 8 casos donde el nombre no lo conoce nadie y el
    articulo lo esta traduciendo, que es justo para lo que el indice existe.

    Sobre las 279 paginas de la cache queda UN caso, y es real: la Copa Argentina
    2019-20 escribe `[[Club Atlético San Martín (Tucumán)|San Martín (SJ)]]` con
    la bandera de San Juan al lado. Ahi el equivocado es el enlace. No ensucia el
    dataset porque la misma pagina usa tambien el correcto y
    `parser.articulos_de_la_pagina` se abstiene, pero el aviso corresponde igual.
    """
    fuera = []
    for m in _ENLACE_CON_NOMBRE.finditer(texto):
        articulo, visible = m.group(1), m.group(2)
        if not _CALIFICADOR.search(visible) or articulo not in ARTICULOS:
            continue
        solo = buscar(visible, "")
        if solo is None:
            continue
        con = canonizar(visible, articulo)
        if con != solo.nombre:
            fuera.append(f"[[{articulo}|{visible}]]: el articulo dice {con} y el "
                         f"nombre dice {solo.nombre}. El nombre ya viene "
                         f"desambiguado, asi que uno de los dos esta mal")
    return sorted(set(fuera))

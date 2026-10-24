#!/usr/bin/env python3
"""Tests del padron.

El riesgo especifico de un padron no es que falte un club: es que un alias se le
asigne al club equivocado. Eso no rompe nada -- reparte los partidos de Gimnasia
de La Plata entre los dos Gimnasia y sigue andando. Casi todo lo de abajo apunta
ahi, y se apoya en `afa_snapshot`, que es data de afuera.
"""
from __future__ import annotations

from pathlib import Path

import pytest

from fad import dataset, equipos
from tests.afa_snapshot import AFA, WIKIPEDIA

DATOS = Path(__file__).resolve().parent.parent / "data"


# --------------------------------------------------------------------------
# normalizacion
# --------------------------------------------------------------------------
@pytest.mark.parametrize("a, b", [
    ("Vélez Sarsfield", "velez sarsfield"),
    ("BOCA JUNIORS", "boca juniors"),
    ("  Racing   Club  ", "racing club"),
    ("Dep. Riestra", "dep riestra"),
    ("Indep.Mza.", "indep mza"),
    ("Central Córdoba ( SdE )", "central cordoba (sde)"),
])
def test_normalizar(a, b):
    assert equipos.normalizar(a) == b


def test_las_comillas_raras_son_la_misma_comilla():
    """AFA escribe "Newell`s" con acento grave y Wikipedia con apostrofe. Para
    una comparacion literal son dos clubes distintos."""
    assert equipos.normalizar("Newell`s") == equipos.normalizar("Newell's")
    assert equipos.normalizar("Newell’s") == equipos.normalizar("Newell's")


# --------------------------------------------------------------------------
# el testigo externo: las dos numeraciones tienen que corresponderse
# --------------------------------------------------------------------------
@pytest.mark.parametrize("id_afa, largo, corto", AFA)
def test_los_nombres_de_afa_resuelven(id_afa, largo, corto):
    assert equipos.conocido(largo), f"el padron no conoce {largo!r}"
    assert equipos.conocido(corto), f"el padron no conoce {corto!r}"


@pytest.mark.parametrize("id_afa, largo, corto", AFA)
def test_cada_alias_de_afa_cae_en_el_club_de_ese_id(id_afa, largo, corto):
    """EL test que importa.

    La AFA numera sus clubes con un sistema propio, que no sabe nada de como los
    escribe Wikipedia. Si el alias "Gimnasia" se le asigna por error al de
    Mendoza, resolverlo devuelve un club con `afa=816` y este test cae contra el
    8 que dice el feed. Ninguna otra verificacion lo notaria: los dos clubes
    existen, los dos nombres son plausibles y el dataset se arma igual.
    """
    for nombre in (largo, corto):
        eq = equipos.buscar(nombre)
        assert eq is not None and eq.afa == id_afa, (
            f"{nombre!r} resuelve a {eq.nombre if eq else None!r} "
            f"(afa={eq.afa if eq else None}), pero el feed dice que es el {id_afa}")


@pytest.mark.parametrize("nombre", WIKIPEDIA)
def test_los_nombres_de_wikipedia_resuelven(nombre):
    assert equipos.canonical(nombre) == nombre, "el canonico es el de Wikipedia"


def test_el_padron_cubre_a_los_30_de_primera():
    """Los 30 son el piso, no el total: la Copa Argentina mezcla divisiones y
    trae clubes que no juegan Primera."""
    assert set(WIKIPEDIA) <= {e.nombre for e in equipos.PADRON}


def test_no_hay_dos_clubes_con_el_mismo_nombre():
    nombres = [e.nombre for e in equipos.PADRON]
    assert len(nombres) == len(set(nombres))


def test_los_ids_de_afa_no_se_repiten():
    ids = [e.afa for e in equipos.PADRON if e.afa is not None]
    assert len(ids) == len(set(ids))
    assert set(ids) == {i for i, _, _ in AFA}


# --------------------------------------------------------------------------
# los que se parecen y no son
# --------------------------------------------------------------------------
@pytest.mark.parametrize("nombre, canonico", [
    ("Gimnasia", "Gimnasia y Esgrima (LP)"),
    ("Gimnasia (Mendoza)", "Gimnasia y Esgrima (M)"),
    ("Gimnasia (M)", "Gimnasia y Esgrima (M)"),
    ("Estudiantes", "Estudiantes (LP)"),
    ("Estudiantes RC", "Estudiantes (RC)"),
    ("Independiente", "Independiente"),
    ("Independiente Riv. (M)", "Independiente Rivadavia"),
    ("Indep.Mza.", "Independiente Rivadavia"),
    ("Talleres", "Talleres (C)"),
    ("Sarmiento", "Sarmiento (J)"),
])
def test_los_homonimos_no_se_mezclan(nombre, canonico):
    """"Gimnasia" a secas es el de La Plata; "Estudiantes" a secas es el de La
    Plata; "Independiente" NO es Independiente Rivadavia aunque sea prefijo.
    Emparejar por similitud fallaba justo en estos: 26 de 60 partidos sin par."""
    assert equipos.canonical(nombre) == canonico


def test_los_CINCO_huracan_son_cinco_clubes():
    """El padron tiene cinco: el de Parque Patricios, el de Tres Arroyos, el de
    Comodoro Rivadavia, Las Heras y Corrientes. El ultimo entro para la capa
    1991-1996 --juga en Primera hasta el Clausura 1997-- y el riesgo de agregarlo no
    es que no resuelva sino que se coma al que ya estaba: `Huracán` a secas tiene que
    seguir siendo el de Parque Patricios."""
    cinco = ["Huracán", "Huracán (TA)", "Huracán (CR)",
             "Huracán Las Heras", "Huracán Corrientes"]
    assert len({equipos.canonical(n) for n in cinco}) == 5
    assert equipos.canonical("Huracán") == "Huracán"


def test_huracan_corrientes_resuelve_tambien_por_su_articulo():
    """Las paginas de esos anios lo enlazan como `[[Club Atlético Huracán
    Corrientes|Huracán Corrientes]]`, asi que el articulo tiene que traducir igual que
    el display: es por donde resuelven los clubes cuando el nombre corto es ambiguo."""
    assert equipos.canonizar("Huracán Corrientes",
                             "Club Atlético Huracán Corrientes") == "Huracán Corrientes"


def test_los_dos_gimnasia_son_dos_clubes():
    assert equipos.canonical("Gimnasia") != equipos.canonical("Gimnasia (Mendoza)")


def test_los_dos_estudiantes_son_dos_clubes():
    assert equipos.canonical("Estudiantes") != equipos.canonical("Estudiantes (RC)")


def test_independiente_no_es_independiente_rivadavia():
    assert equipos.canonical("Independiente") != equipos.canonical("Independiente Rivadavia")


# --------------------------------------------------------------------------
# el indice no se escribe al lado del padron: se deriva
# --------------------------------------------------------------------------
def test_un_alias_peleado_por_dos_clubes_no_arranca(monkeypatch):
    """Si dos clubes reclaman el mismo alias, tiene que reventar al construir el
    indice. Un alias ambiguo no da error en produccion: le da los partidos al
    club equivocado, calladito."""
    monkeypatch.setattr(equipos, "PADRON", (
        equipos.Equipo("Gimnasia y Esgrima (LP)", 8, ("Gimnasia",)),
        equipos.Equipo("Gimnasia y Esgrima (M)", 816, ("Gimnasia",)),
    ))
    with pytest.raises(ValueError, match="dos clubes"):
        equipos._armar_indice()


def test_el_indice_sale_del_padron_y_no_de_otro_lado(monkeypatch):
    monkeypatch.setattr(equipos, "PADRON", (equipos.Equipo("Inventado FC", 999, ("IFC",)),))
    indice = equipos._armar_indice()
    assert set(indice) == {"inventado fc", "ifc"}


# --------------------------------------------------------------------------
# desconocidos: ruido una vez, no silencio para siempre
# --------------------------------------------------------------------------
def test_un_club_que_no_esta_levanta():
    with pytest.raises(equipos.EquipoDesconocido):
        equipos.canonical("Deportivo Wanderers de Pehuajó")


def test_canonizar_deja_pasar_al_desconocido_tal_cual():
    """`canonizar` corre ANTES de validar. El que no se pudo traducir tiene que
    llegar entero al aviso, porque el aviso existe para decir como venia escrito."""
    raro = "Deportivo Wanderers de Pehuajó"
    assert equipos.canonizar(raro) == raro
    assert not equipos.conocido(raro)


def test_canonizar_traduce_al_que_si_conoce():
    assert equipos.canonizar("Newell`s") == "Newell's Old Boys"


def test_por_afa():
    assert equipos.por_afa(124).nombre == "Belgrano"
    assert equipos.por_afa(999999) is None


# --------------------------------------------------------------------------
# el dataset que se publica
# --------------------------------------------------------------------------
@pytest.mark.skipif(not list(DATOS.glob("partidos-*.csv")),
                    reason="hay que correr build.py primero")
def test_el_csv_publicado_usa_nombres_canonicos():
    nombres = {f[c] for f in dataset.leer_carpeta(DATOS) for c in ("home_team", "away_team")}
    canonicos = {e.nombre for e in equipos.PADRON}
    assert nombres <= canonicos, f"nombres fuera del padron: {sorted(nombres - canonicos)}"


# --------------------------------------------------------------------------
# el articulo manda sobre el nombre visible
# --------------------------------------------------------------------------
def test_el_articulo_desempata_lo_que_el_nombre_no_puede():
    """"Estudiantes" a secas apunta a TRES articulos distintos segun la pagina:
    en Primera es el de La Plata, en Primera B el de Caseros. El nombre no
    alcanza; el articulo si, y ademas no depende de la division ni del anio, asi
    que los ascensos y descensos dejan de importar."""
    assert equipos.canonizar("Estudiantes") == "Estudiantes (LP)"
    assert equipos.canonizar("Estudiantes", "Club Atlético Estudiantes") == "Estudiantes (BA)"
    assert equipos.canonizar("Talleres", "Club Atlético Talleres (Remedios de Escalada)") \
        == "Talleres (RdE)"


def test_sin_articulo_se_cae_al_nombre():
    assert equipos.canonizar("Newell`s", "") == "Newell's Old Boys"


def test_un_articulo_desconocido_no_pisa_al_nombre():
    assert equipos.canonizar("Boca Juniors", "Club Inventado") == "Boca Juniors"


def test_todo_articulo_apunta_a_un_club_del_padron():
    """La guarda que evita la desincronizacion: `ARTICULOS` es una segunda
    estructura, y si apunta a un club que no existe revienta al importar."""
    nombres = {e.nombre for e in equipos.PADRON}
    assert set(equipos.ARTICULOS.values()) <= nombres


def test_el_mapa_de_la_pagina_no_adivina():
    """Si dentro de UNA pagina el mismo nombre visible apunta a dos articulos, no
    hay testigo y no se devuelve ninguno."""
    from fad import parser
    texto = "[[Club A|Equipo]] y [[Club B|Equipo]] y [[Club C|Otro]]"
    assert parser.articulos_de_la_pagina(texto) == {"Otro": "Club C"}


def test_una_tilde_de_menos_no_es_un_desacuerdo():
    """La Primera B 2015 enlaza a Estudiantes de Caseros ocho veces bien y dos
    veces como "Club Atletico Estudiantes", sin la tilde. Es el mismo articulo y
    un typo, pero comparando por igualdad de cadena la guarda lo tomaba por un
    desacuerdo: "Estudiantes" pelado se quedaba sin testigo y caia al nombre
    solo, que en Primera es el de La Plata. Cuarenta y cuatro partidos de Caseros
    quedaron en la historia de un club que nunca jugo esa categoria.

    O sea que la guarda contra adivinar terminaba forzando la adivinanza."""
    from fad import parser
    texto = ("[[Club Atlético Estudiantes|Estudiantes]] "
             "[[Club Atletico Estudiantes|Estudiantes]]")
    assert parser.articulos_de_la_pagina(texto)["Estudiantes"] in (
        "Club Atlético Estudiantes", "Club Atletico Estudiantes")
    # y el club sale bien con cualquiera de las dos grafias
    mapa = parser.articulos_de_la_pagina(texto)
    assert equipos.canonizar("Estudiantes", mapa["Estudiantes"]) == "Estudiantes (BA)"


def test_dos_articulos_de_verdad_distintos_siguen_sin_testigo():
    """El arreglo de arriba no puede aflojar la guarda. La Copa Argentina 2019-20
    tiene un enlace mal puesto -- `[[Club Atlético San Martín (Tucumán)|San Martín
    (SJ)]]`, con la bandera de San Juan al lado -- junto con el correcto. Son dos
    articulos genuinamente distintos, asi que el mapa se tiene que seguir
    callando y dejar que resuelva el nombre, que ahi es el que tiene razon."""
    from fad import parser
    texto = ("[[Club Atlético San Martín (Tucumán)|San Martín (SJ)]] "
             "[[Club Atlético San Martín (San Juan)|San Martín (SJ)]]")
    assert "San Martín (SJ)" not in parser.articulos_de_la_pagina(texto)


# --------------------------------------------------------------------------
# cuando el enlace se contradice con el nombre que muestra
# --------------------------------------------------------------------------
def test_un_nombre_ya_desambiguado_que_no_coincide_con_el_articulo():
    """`[[Club Atlético San Martín (Tucumán)|San Martín (SJ)]]`, tal cual esta en
    la Copa Argentina 2019-20 y con la bandera de San Juan al lado. El "(SJ)" lo
    escribio alguien a proposito, asi que no hay ambiguedad que el articulo venga
    a resolver: uno de los dos esta mal.

    Es la firma del bug de Racing, que costo 248 partidos."""
    texto = "algo [[Club Atlético San Martín (Tucumán)|San Martín (SJ)]] mas"
    avisos = equipos.articulos_que_contradicen(texto)
    assert len(avisos) == 1
    assert "San Martín (T)" in avisos[0] and "San Martín (SJ)" in avisos[0]


def test_el_articulo_desambiguando_un_nombre_pelado_no_es_aviso():
    """Que los dos testigos difieran es lo NORMAL y es para lo que el indice
    existe: "Estudiantes" a secas apunta al de La Plata y el articulo dice que
    este es el de Caseros. Avisar ahi seria avisar en cada pagina del ascenso."""
    texto = "[[Club Atlético Estudiantes|Estudiantes]]"
    assert equipos.articulos_que_contradicen(texto) == []


def test_un_nombre_que_el_padron_no_conoce_no_es_una_contradiccion():
    """Sin esta condicion entran casos donde el nombre visible no lo conoce nadie:
    ahi el articulo no lo esta contradiciendo, lo esta traduciendo.

    El ejemplo era `[[Club Atlético Brown|Brown (A)]]`, y dejo de servir cuando
    "Brown (A)" entro al padron como alias -- el test seguia pasando, pero por el
    motivo equivocado, y el mutante que lo cuidaba sobrevivio. Lo agarro
    `mutar.py`, no la suite. Ahora el nombre es uno que el padron no puede
    conocer nunca, y el test lo exige antes de probar nada."""
    visible = "Deportivo Inexistente (XX)"
    assert equipos.buscar(visible, "") is None, "el ejemplo dejo de ser desconocido"
    assert equipos.articulos_que_contradicen(f"[[Club Atlético Brown|{visible}]]") == []


def test_un_articulo_desconocido_no_es_una_contradiccion():
    texto = "[[Club Inventado de Prueba|San Martín (SJ)]]"
    assert equipos.articulos_que_contradicen(texto) == []


def test_el_enlace_sin_nombre_visible_no_tiene_dos_testigos():
    texto = "[[Club Atlético San Martín (Tucumán)]]"
    assert equipos.articulos_que_contradicen(texto) == []


# --------------------------------------------------------------------------
# los typos del Argentino A 2010-11
# --------------------------------------------------------------------------
@pytest.mark.parametrize("typo, club", [
    ("Cipoletti", "Cipolletti"),              # una L
    ("Desamprados", "Desamparados"),          # sin la segunda A
    ("Centrl Norte", "Central Norte (S)"),    # sin la A
    ("Gimnasia (CdU)", "Gimnasia y Esgrima (CdU)"),   # sin el "y Esgrima"
    ("Libertad", "Libertad (S)"),             # sin el desambiguador
])
def test_los_typos_de_una_pagina_resuelven_al_club(typo, club):
    """Todos verificados contra la grilla de la zona: en la fecha donde aparece
    el nombre raro, el club que falta es exactamente ese. No se dedujeron por
    parecido de cadenas."""
    assert equipos.canonizar(typo, "") == club


def test_el_articulo_de_rivadavia_de_lincoln():
    """La pagina escribe "Rivadavia" a secas, que el padron no resuelve -- hay
    tres. Pero enlaza el articulo, y el articulo si desambigua."""
    assert equipos.canonizar("Rivadavia", "") == "Rivadavia"
    assert equipos.canonizar("Rivadavia", "Rivadavia de Lincoln") == "Rivadavia (L)"


@pytest.mark.parametrize("ambiguo", ["Gimnasia y Esgrima", "Central Norte (SE)"])
def test_los_nombres_ambiguos_NO_se_agregaron_como_alias(ambiguo):
    """Y esto es lo que hay que sostener, no lo de arriba.

    "Gimnasia y Esgrima" a secas tiene CINCO candidatos en el padron. Y
    "Central Norte (SE)" no es un typo de escritura sino un desambiguador
    equivocado: en esa misma pagina "(SE)" significa Santiago del Estero -- ahi
    esta "Central Córdoba (SE)", que resuelve bien -- asi que darselo al de
    SALTA seria escribir en el padron algo que la fuente no dice.

    Los dos quedan como club desconocido, que frena el build. Es lo correcto:
    un alias mal puesto no falla, le da partidos al club equivocado."""
    assert equipos.buscar(ambiguo, "") is None


def test_la_pagina_usa_SE_para_santiago_del_estero():
    """El testigo de que "(SE)" no puede ser Salta: la misma pagina lo usa para
    Santiago del Estero y el padron ya lo resuelve asi."""
    assert equipos.canonizar("Central Córdoba (SE)", "") == "Central Córdoba (SdE)"


# --------------------------------------------------------------------------
# Un nombre con hermanos no se puede pelar
# --------------------------------------------------------------------------
def test_un_nombre_con_hermanos_no_tiene_un_solo_dueno():
    """Es lo unico que separa un acierto de un error grave cuando hay que pelarle
    la ciudad a un nombre. `Racing (Olavarria)` pelado da `Racing`, que el padron
    resuelve a Racing Club de Avellaneda -- un club de Primera que no jugo nunca
    el Argentino A."""
    assert not equipos.unico_dueno("Racing")
    assert not equipos.unico_dueno("San Martín")


def test_un_nombre_sin_hermanos_si():
    """`Real Arroyo Seco (Arroyo Seco)` y `General Paz Juniors (Cordoba)` traen la
    ciudad aunque sea redundante, y ahi pelarla es lo unico que los hace
    reconocibles."""
    assert equipos.unico_dueno("Real Arroyo Seco")
    assert equipos.unico_dueno("General Paz Juniors")
    assert equipos.unico_dueno("Atlético Candelaria")


def test_la_provincia_entera_tambien_nombra_al_de_mendoza():
    """Sus dos hermanos ya la traian -- `San Martín (Formosa)`, `San Martín
    (Tucumán)` --; a este le faltaba, y sin ella se perdian dos partidos de la
    promocion del Argentino A 2005-06."""
    assert equipos.canonizar("San Martín (Mendoza)") == "San Martín (SM)"


# --------------------------------------------------------------------------
# Los del Federal A 2014 y 2015
# --------------------------------------------------------------------------
@pytest.mark.parametrize("escrito, club", [
    ("Alianza (CC)", "Alianza (CC)"),
    ("Alianza de Cutral Có", "Alianza (CC)"),                  # la tabla
    ("Américo Tesorieri (LR)", "Américo Tesorieri (LR)"),
    ("Americo Tesorieri (LR)", "Américo Tesorieri (LR)"),      # sin tilde: 2014, Fecha 11
    ("Américo Tesorieri", "Américo Tesorieri (LR)"),           # pelado: 2014, Fecha 13
    ("Américo Tesorieri (La Rioja)", "Américo Tesorieri (LR)"),
    ("Independiente (Ch)", "Independiente (C)"),               # la grilla de las dos
    ("Independiente (Chivilcoy)", "Independiente (C)"),        # sus tablas
    ("Textil Mandiyú", "Textil Mandiyú"),
    ("9 de Julio (M)", "9 de Julio (M)"),
    ("9 de Julio (Morteros)", "9 de Julio (M)"),
    ("Vélez Sarsfield (SR)", "Vélez Sarsfield (SR)"),
    ("Vélez Sarsfield (San Ramón)", "Vélez Sarsfield (SR)"),
    ("Talleres (Córdoba)", "Talleres (C)"),
])
def test_las_grafias_del_federal_a_2014_y_2015_resuelven(escrito, club):
    """Cada una aparece de verdad en la grilla o en una tabla de esas dos paginas,
    y ninguna lleva enlace: resuelven por el nombre o no resuelven.

    Con `canonical` y no con `canonizar`, a proposito: `canonizar` devuelve intacto
    lo que no conoce, asi que para el club que se llama igual que su canonico
    --"Alianza (CC)", "Textil Mandiyú"-- el test pasaria tambien sin el club en el
    padron."""
    assert equipos.canonical(escrito) == club


@pytest.mark.parametrize("ambiguo", ["Mitre (S)", "San Jorge", "Alianza", "9 de Julio"])
def test_los_nombres_con_dos_duenos_del_federal_a_2014_NO_son_alias(ambiguo):
    """Los cuatro tienen otro dueno, y los dos primeros lo tienen EN EL CORPUS.

    "Mitre (S)" es Mitre de SALTA en las Copa Argentina 2012-13, 2013-14, 2014-15 y
    2016-17, que lo enlazan dieciseis veces a [[Club Atlético Mitre (Salta)]]; el
    Federal A 2014 se lo escribe a Mitre de Santiago del Estero en diez partidos, y
    eso se resuelve con un `Homonimo` de esa pagina. "San Jorge" es tambien el nombre
    base del de la provincia de Santa Fe, [[Club Atlético San Jorge]], que cinco Copa
    Argentina escriben 'Atlético San Jorge' y 'San Jorge (SF)', nunca pelado.
    "Alianza" es tambien Alianza de Moldes y "9 de Julio" el de Rafaela.

    Los cuatro quedan como club desconocido, que frena el build. Es lo correcto: un
    alias mal puesto no falla, le da partidos al club equivocado."""
    assert equipos.buscar(ambiguo, "") is None


def test_los_dos_mandiyu_son_dos_clubes():
    """Textil Mandiyu no es Deportivo Mandiyu con otro nombre. Convivieron de 2010 a
    2016 y JUGARON ENTRE ELLOS: la Copa Argentina 2012-13 publica
    `[[Club Deportivo Mandiyú|Deportivo Mandiyú]] (3) 0 - 0 (1)
    [[Club Social y Deportivo Textil Mandiyú|Textil Mandiyú]]`. Si uno fuera alias
    del otro, ese partido seria un club contra si mismo."""
    assert equipos.canonical("Textil Mandiyú") != equipos.canonical("Deportivo Mandiyú")
    assert equipos.canonizar("Mandiyú", "Club Social y Deportivo Textil Mandiyú") == "Textil Mandiyú"
    assert equipos.canonizar("Mandiyú", "Club Deportivo Mandiyú") == "Deportivo Mandiyú"


def test_el_velez_de_san_ramon_no_se_come_al_de_liniers():
    """El riesgo de agregar un segundo Velez no es que no resuelva sino que se quede
    con el nombre del que ya estaba: `Vélez Sarsfield` a secas, `Vélez` y el
    articulo sin parentesis tienen que seguir siendo el de Liniers, con su id de
    AFA. El de San Ramon entra solo por su "(SR)" o por su articulo."""
    assert equipos.canonical("Vélez Sarsfield") == "Vélez Sarsfield"
    assert equipos.canonical("Vélez") == "Vélez Sarsfield"
    assert equipos.por_afa(20).nombre == "Vélez Sarsfield"
    assert equipos.canonizar("Vélez Sarsfield",
                             "Club Atlético Vélez Sarsfield") == "Vélez Sarsfield"
    assert equipos.canonizar("Club Atlético Vélez Sarsfield",
                             "Club Atlético Vélez Sarsfield (San Ramón)") == "Vélez Sarsfield (SR)"


def test_el_9_de_julio_de_morteros_no_es_el_de_rafaela():
    """Y resuelve por sus DOS titulos: el Federal A 2015 enlaza el largo en la
    grilla y el corto, que es redireccion, en la tabla de participantes."""
    assert equipos.canonical("9 de Julio (M)") != equipos.canonical("9 de Julio (R)")
    for titulo in ("Asociación Deportiva 9 de Julio (Morteros)",
                   "Asociación Deportiva 9 de Julio"):
        assert equipos.canonizar("9 de Julio", titulo) == "9 de Julio (M)"
    assert equipos.canonizar("9 de Julio",
                             "Club Atlético 9 de Julio (Rafaela)") == "9 de Julio (R)"


def test_el_articulo_de_alianza_resuelve_con_tilde_y_sin_tilde():
    """Wikipedia titula `(Cutral Co)` y las paginas enlazan `(Cutral Có)`. Es una
    sola clave porque el indice normaliza; este test es para que siga siendolo."""
    for titulo in ("Club Social y Deportivo Alianza (Cutral Có)",
                   "Club Social y Deportivo Alianza (Cutral Co)"):
        assert equipos.canonizar("Club Social y Deportivo Alianza", titulo) == "Alianza (CC)"


def test_los_dos_de_la_rioja_no_se_cruzan_por_el_articulo():
    """Andino y Américo Tesorieri son de la misma ciudad, juegan en la misma cancha y
    en 2015 compartieron zona, y los 30 lados de cada uno entran por el ARTICULO, que
    manda sobre el nombre visible. Con las dos claves cruzadas el build escribia la
    temporada entera de uno a nombre del otro sin un solo grave: se midio, y lo unico
    que saltaba era un aviso de tabla. El testigo es RSSSF, que los lista con ciudad
    y con fojas distintas en el Federal A 2015 --Tesorieri 9:28 en 18 partidos de la
    zona, Andino 12:38--, y con cada articulo en su club esas fojas cierran."""
    assert equipos.canonizar("Andino", "Andino Sport Club") == "Andino"
    assert equipos.canonizar("Américo Tesorieri (LR)",
                             "Club Atlético Américo Tesorieri") == "Américo Tesorieri (LR)"
    # Manda el articulo: con el nombre visible del otro, sigue siendo el del articulo.
    assert equipos.canonizar("Américo Tesorieri (LR)", "Andino Sport Club") == "Andino"
    assert equipos.canonizar("Andino",
                             "Club Atlético Américo Tesorieri") == "Américo Tesorieri (LR)"


# --------------------------------------------------------------------------
# Los del Nacional 1985
# --------------------------------------------------------------------------
@pytest.mark.parametrize("escrito, club", [
    ("Argentino (F)", "Argentino (F)"),
    ("Juventud Alianza", "Juventud Alianza"),
])
def test_las_grafias_del_nacional_1985_resuelven(escrito, club):
    """Las dos aparecen asi, sin enlace, en la grilla de la Zona G y en las llaves:
    resuelven por el nombre o no resuelven. Con `canonical` por lo mismo que el test
    del Federal A: `canonizar` devuelve intacto al que no conoce."""
    assert equipos.canonical(escrito) == club


def test_el_argentino_de_firmat_resuelve_por_sus_dos_titulos():
    """La tabla de participantes muestra "Argentino" a secas, enlazado a la
    redireccion; la de posiciones, "Argentino (F)" enlazado al articulo."""
    for titulo in ("Club Atlético Argentino (Firmat)", "Club Atlético Argentino de Firmat"):
        assert equipos.canonizar("Argentino", titulo) == "Argentino (F)"


def test_el_argentino_de_firmat_no_se_come_a_los_otros_cuatro():
    """Cinco Argentino, y "Argentino" a secas no es de ninguno. El "(F)" es Firmat
    aunque en este padron tambien quiera decir Formosa: la base difiere."""
    otros = {"Argentino de Merlo", "Argentino (MM)", "Argentino de Quilmes",
             "Argentino de Rosario"}
    assert equipos.canonical("Argentino (F)") not in otros
    assert {equipos.canonical(n) for n in ("Argentino (M)", "Argentino (MM)",
                                           "Argentino de Quilmes", "Argentino (R)")} == otros
    assert equipos.buscar("Argentino", "") is None
    # Manda el articulo: el de Rosario sigue siendo el de Rosario.
    assert equipos.canonizar("Argentino (F)",
                             "Club Atlético Argentino (Rosario)") == "Argentino de Rosario"
    assert equipos.canonical("San Martín (F)") == "San Martín (F)"
    assert equipos.canonizar("San Martín (F)",
                             "Club Sportivo General San Martín") == "San Martín (F)"


def test_juventud_alianza_no_es_otro_juventud_ni_otro_alianza():
    """Y el "(SJ)" de las Copa Argentina entra por el articulo, sin alias."""
    otros = {"Juventud Antoniana", "Juventud Unida", "Juventud Unida (G)",
             "Juventud Unida Universitario", "Juventud (P)", "Alianza (CC)",
             "Alianza de Moldes"}
    assert equipos.canonical("Juventud Alianza") not in otros
    assert equipos.canonizar("Juventud Alianza (SJ)",
                             "Club Atlético de la Juventud Alianza") == "Juventud Alianza"

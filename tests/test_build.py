#!/usr/bin/env python3
"""Tests del pipeline: parsear -> normalizar nombres -> validar.

El pegamento tambien se rompe, y calladito: sacar el paso de normalizacion no
hace fallar nada, solo escribe "Newell`s" en el CSV publicado y al mes hay dos
clubes con media historia cada uno.
"""
from __future__ import annotations

import build
from fad import posiciones
from fad.torneos import Torneo

# `cerrado=False`: estos tests reconstruyen el torneo en cada corrida. Uno
# cerrado se reusaria del CSV anterior y la mitad de lo que se prueba aca --
# volver a parsear, la guarda contra achicarse -- no llegaria a correr.
T = Torneo("Anexo:Prueba", "Prueba", 2026, cerrado=False)


def tabla(*cruces: tuple[str, str]) -> str:
    filas = "".join(
        f"|-\n|{local}\n|2 - 1\n|{visita}\n|Un Estadio\n|{23 + i} de enero\n|20:00\n"
        for i, (local, visita) in enumerate(cruces))
    return f"""
=== Resultados ===
{{|class="wikitable"
!colspan=6|Fecha 1
|-
!colspan=6|Zona A
|-
!Local
!Resultado
!Visitante
!Estadio
!Fecha
!Hora
{filas}|}}

== Otra cosa ==
"""


def test_los_nombres_llegan_al_canonico():
    """Como los escribe la AFA -> como los titula Wikipedia."""
    ps, _ = build.procesar(tabla(("Newell`s", "Gimnasia")), T)
    assert len(ps) == 1
    assert ps[0].local == "Newell's Old Boys"
    assert ps[0].visita == "Gimnasia y Esgrima (LP)"


def test_un_nombre_que_ya_es_canonico_no_se_toca():
    ps, _ = build.procesar(tabla(("Boca Juniors", "River Plate")), T)
    assert (ps[0].local, ps[0].visita) == ("Boca Juniors", "River Plate")


def test_un_club_desconocido_frena_el_build():
    """Grave: `main` no escribe el CSV y queda el dataset de ayer, que estaba
    bien. Es el caso de un ascenso o de un torneo que se suma."""
    ps, avisos = build.procesar(tabla(("Boca Juniors", "Deportivo Inventado")), T)
    graves = [a for a in avisos if a.grave]
    assert graves, "un club fuera del padron tiene que ser un aviso grave"
    assert any("padron" in a.que for a in graves)


def test_el_aviso_dice_como_venia_escrito():
    """Sin el nombre crudo el aviso no sirve: hay que poder buscarlo en la
    pagina para saber que alias agregar."""
    _, avisos = build.procesar(tabla(("Boca Juniors", "Deportivo Inventado")), T)
    assert any("Deportivo Inventado" in a.detalle for a in avisos)


def test_un_alias_no_frena_el_build():
    _, avisos = build.procesar(tabla(("Newell`s", "Gimnasia")), T)
    assert not any("padron" in a.que for a in avisos)


# --------------------------------------------------------------------------
# la pagina se lee sin comentarios
# --------------------------------------------------------------------------
def test_una_fecha_comentada_no_es_un_partido():
    """Las paginas en curso dejan comentado lo que todavia no se jugo. El control
    es la misma pagina sin los `<!--`: ahi el partido si esta."""
    visible = tabla(("Boca Juniors", "River Plate"))
    comentada = tabla(("Racing Club", "Independiente"))
    ps, avisos = build.procesar(visible + "<!--" + comentada + "-->", T)
    assert [(p.local, p.visita) for p in ps] == [("Boca Juniors", "River Plate")]
    assert not any("sin cerrar" in a.que for a in avisos)
    ps, _ = build.procesar(visible + comentada, T)
    assert len(ps) == 2


def test_un_enlace_comentado_no_desambigua():
    """El Argentino A 2010-11 escribe "Rivadavia" a secas, y el unico enlace que lo
    desambigua esta adentro de una seccion que un editor dejo comentada. Lo
    comentado no lo dice la pagina: el nombre queda sin resolver, y eso es grave."""
    enlace = "Ante [[Rivadavia de Lincoln|Rivadavia]] de Lincoln.\n"
    pagina = tabla(("Douglas Haig", "Rivadavia"))
    ps, avisos = build.procesar(pagina + "<!--\n" + enlace + "-->\n", T)
    assert ps[0].visita == "Rivadavia"
    assert any("padron" in a.que for a in avisos if a.grave)
    ps, avisos = build.procesar(pagina + enlace, T)
    assert ps[0].visita == "Rivadavia (L)"
    assert not any(a.grave for a in avisos)


def test_un_comentario_sin_cerrar_tapa_el_resto_y_lo_avisa():
    """MediaWiki no muestra nada despues de un `<!--` que no cierra, y el build
    tampoco lo lee. Lo que se deja de leer no avisa solo, asi que se avisa aca, sin
    frenar: si tapaba partidos, lo frena la guarda contra achicarse."""
    antes = tabla(("Boca Juniors", "River Plate"))
    ps, avisos = build.procesar(antes + "<!-- sin cerrar" + tabla(
        ("Racing Club", "Independiente")), T)
    assert [(p.local, p.visita) for p in ps] == [("Boca Juniors", "River Plate")]
    (aviso,) = [a for a in avisos if "sin cerrar" in a.que]
    assert not aviso.grave
    assert f"caracter {len(antes)} " in aviso.detalle
    assert "'<!-- sin cerrar\\n=== Resultados" in aviso.detalle


# --------------------------------------------------------------------------
# el build entero, que es lo que va a correr solo todos los dias
# --------------------------------------------------------------------------
def correr(monkeypatch, tmp_path, pagina: str, argv=()):
    """`build.main` contra una pagina de mentira y un CSV temporal."""
    monkeypatch.setattr(build.torneos, "TODOS", [T])
    monkeypatch.setattr(build.wiki, "wikitexto", lambda *a, **k: pagina)
    monkeypatch.setattr(build, "SALIDA", tmp_path / "data")
    return build.main(list(argv))


def test_el_build_escribe(monkeypatch, tmp_path):
    assert correr(monkeypatch, tmp_path,
                  tabla(("Boca Juniors", "River Plate"), ("Racing Club", "Huracán"))) == 0
    assert len(build.dataset.leer_carpeta(tmp_path / "data")) == 2


def test_un_club_desconocido_no_escribe_nada(monkeypatch, tmp_path):
    assert correr(monkeypatch, tmp_path, tabla(("Boca Juniors", "Deportivo Inventado"))) == 1
    assert not list((tmp_path / "data").glob("*.csv")) if (tmp_path / "data").exists() else True


def test_si_el_dataset_se_achica_no_pisa_el_anterior(monkeypatch, tmp_path):
    """La guarda que importa cuando esto corre solo. Los 1 partido que quedan
    pueden estar perfectos: ningun chequeo de `validar` los ve mal, porque
    mirados solos estan bien. Lo unico que delata la perdida es lo de ayer."""
    correr(monkeypatch, tmp_path,
           tabla(("Boca Juniors", "River Plate"), ("Racing Club", "Huracán")))
    assert correr(monkeypatch, tmp_path, tabla(("Boca Juniors", "River Plate"))) == 1
    assert len(build.dataset.leer_carpeta(tmp_path / "data")) == 2, \
        "pisó el dataset bueno con el achicado"


def test_forzar_deja_pasar_el_achicamiento(monkeypatch, tmp_path):
    """Para cuando la baja es real: Wikipedia saco un partido que no iba."""
    correr(monkeypatch, tmp_path,
           tabla(("Boca Juniors", "River Plate"), ("Racing Club", "Huracán")))
    assert correr(monkeypatch, tmp_path,
                  tabla(("Boca Juniors", "River Plate")), argv=["--forzar"]) == 0
    assert len(build.dataset.leer_carpeta(tmp_path / "data")) == 1


def test_dry_run_no_escribe(monkeypatch, tmp_path):
    assert correr(monkeypatch, tmp_path, tabla(("Boca Juniors", "River Plate")),
                  argv=["--dry-run"]) == 0
    assert not list((tmp_path / "data").glob("*.csv")) if (tmp_path / "data").exists() else True


def test_una_pagina_que_no_se_puede_bajar_no_escribe(monkeypatch, tmp_path):
    def explota(*a, **k):
        raise LookupError("no existe")
    monkeypatch.setattr(build.torneos, "TODOS", [T])
    monkeypatch.setattr(build.wiki, "wikitexto", explota)
    monkeypatch.setattr(build, "SALIDA", tmp_path / "data")
    assert build.main([]) == 1
    assert not list((tmp_path / "data").glob("*.csv")) if (tmp_path / "data").exists() else True


def test_se_normaliza_ANTES_de_validar():
    """El orden de los dos pasos, y por que no da igual.

    Los chequeos que comparan nombres entre si lo hacen por igualdad de cadena.
    Aca Newell's juega dos veces en la Fecha 1, una escrita como la AFA y otra
    como Wikipedia. Normalizando primero son el mismo club y salta el aviso;
    validando primero son dos clubes distintos y no salta nada.

    No es hipotetico: las llaves salen de plantillas y las zonas de tablas, asi
    que en la misma pagina conviven dos maneras de escribir al mismo club.
    """
    _, avisos = build.procesar(
        tabla(("Newell`s", "Boca Juniors"), ("River Plate", "Newell's Old Boys")), T)
    assert any("dos veces" in a.que for a in avisos), (
        "sin normalizar antes, las dos grafias pasan por dos clubes distintos")


# --------------------------------------------------------------------------
# lo que ya termino no se vuelve a bajar
# --------------------------------------------------------------------------
CERRADO_A = Torneo("Anexo:Prueba A", "Prueba", 2016)
CERRADO_B = Torneo("Anexo:Prueba B", "Prueba", 2016)   # MISMO torneo y temporada


def test_un_homonimo_que_arregla_solo_el_cuadro_no_queda_huerfano():
    """`escritos` es contra lo que se chequea si un homonimo sigue haciendo falta,
    y tiene que incluir los nombres del CUADRO DE LLAVES.

    Ya paso una vez con la tabla de posiciones: mientras `escritos` eran solo los
    partidos, un homonimo que arreglaba unicamente una fila de la tabla se
    denunciaba a si mismo como vencido. El cuadro es el tercer lugar donde una
    pagina escribe un nombre, y hay nombres que viven SOLO ahi -- el "Talleres (C)"
    del Argentino A 2005-06 aparece una unica vez en toda la pagina y es adentro
    del cuadro.
    """
    from unittest import mock
    from fad import correcciones

    texto = tabla(("Boca Juniors", "River Plate")) + """
=== Segunda fase ===
{{Copa de 4 clubes
| RD1-equipo1 = Racing Club
| RD1-equipo2 = Independiente
| RD1-goles1 = 1
| RD1-goles2 = 0
}}
"""
    h = correcciones.Homonimo(pagina="Anexo:Prueba", dice="Racing Club",
                              debe="Boca Juniors", porque="de prueba")
    with mock.patch.object(correcciones, "HOMONIMOS", (h,)):
        _, avisos = build.procesar(texto, T)
    assert not [a for a in avisos if "homonimo" in a.que], \
        "el nombre esta en el cuadro, asi que el homonimo hace falta"


def test_un_torneo_cerrado_no_se_vuelve_a_bajar(monkeypatch, tmp_path):
    """El Apertura 2004 no va a cambiar nunca. Volver a bajarlo todos los dias no
    solo gasta pedidos: le da a una pagina de hace veinte anios la posibilidad de
    cambiar un dato que ya esta bien."""
    salida = tmp_path / "data"
    bajadas = []

    def espiar(pag, *a, **k):
        bajadas.append(pag)
        return tabla(("Boca Juniors", "River Plate"))

    monkeypatch.setattr(build.torneos, "TODOS", [CERRADO_A])
    monkeypatch.setattr(build.wiki, "wikitexto", espiar)
    monkeypatch.setattr(build, "SALIDA", salida)

    assert build.main([]) == 0
    assert len(bajadas) == 1, "la primera vez si hay que bajarla"
    assert build.main([]) == 0
    assert len(bajadas) == 1, "la segunda la volvio a bajar"
    assert len(build.dataset.leer_carpeta(salida)) == 1

    assert build.main(["--rehacer"]) == 0
    assert len(bajadas) == 2, "--rehacer tiene que volver a parsear"


def test_dos_paginas_del_mismo_torneo_no_se_pisan(monkeypatch, tmp_path):
    """Varias entradas del catalogo comparten torneo y temporada -- la 2016 y la
    2016-17 son las dos "Primera Division 2016". Si las filas guardadas se
    agrupan por (torneo, temporada) en vez de por pagina, cada entrada se lleva
    las de las DOS y el dataset crece solo: fueron 3284 partidos de la nada."""
    salida = tmp_path / "data"
    monkeypatch.setattr(build.torneos, "TODOS", [CERRADO_A, CERRADO_B])
    monkeypatch.setattr(build.wiki, "wikitexto",
                        lambda *a, **k: tabla(("Boca Juniors", "River Plate")))
    monkeypatch.setattr(build, "SALIDA", salida)

    assert build.main([]) == 0
    assert len(build.dataset.leer_carpeta(salida)) == 2
    assert build.main([]) == 0
    assert len(build.dataset.leer_carpeta(salida)) == 2, "se duplicaron al reusar"


# --------------------------------------------------------------------------
# la segunda fuente, enchufada al pipeline
# --------------------------------------------------------------------------
def _sin_fecha() -> str:
    """Una pagina como las de la B Nacional 2007-2011: tres columnas, sin fecha."""
    return """
== Resultados ==
{|class="wikitable"
!colspan=3|Fecha 1
|-
!Equipo Local
!Resultado
!Equipo Visitante
|-align=center
|Boca Juniors
|2 - 1
|River Plate
|}
"""


def _la_otra_fuente(gl=2, gv=1) -> str:
    return ('<div class="hs-head round-head">Matchday 1</div>'
            '<div data-match_id="1" data-datetime="2007-08-09T22:00:00Z" '
            'class="odd finished match">'
            '<div class="team-name team-name-home">'
            '<a href="/teams/te1/x/">Boca Juniors</a></div>'
            '<div class="match-time">19:00</div>'
            f'<div class="match-result match-result-0"><a href="/x/">{gl}:{gv}</a></div>'
            '<div class="team-name team-name-away">'
            '<a href="/teams/te2/y/">River Plate</a></div></div>')


CON_WF = Torneo("Anexo:Prueba", "Prueba", 2007, cerrado=False, wf=("co1", "se1"))


def test_sin_la_segunda_fuente_el_partido_no_entra(monkeypatch):
    """El estado sin este paso: la pagina no trae fecha y el partido no puede
    entrar al dataset principal, que promete una fecha en cada fila. Es la linea
    de base contra la que se mide.

    Ojo con lo que NO dice: el partido no se tira. `_repartir` lo manda a
    `sin-fecha/`, porque que falte la fecha no es lo mismo que no tener el
    partido. Lo que se prueba aca es que no tiene fecha."""
    T_SIN = Torneo("Anexo:Prueba", "Prueba", 2007, cerrado=False)
    ps, _ = build.procesar(_sin_fecha(), T_SIN)
    assert [p for p in ps if p.fecha] == []


def test_la_segunda_fuente_le_pone_la_fecha(monkeypatch):
    from fad import fechas
    monkeypatch.setattr(fechas, "descargar", lambda *a, **k: _la_otra_fuente())
    ps, avisos = build.procesar(_sin_fecha(), CON_WF)
    assert len(ps) == 1
    assert ps[0].fecha == "2007-08-09"
    assert ps[0].fuente_fecha == fechas.CREDITO, "el credito viaja con el dato"
    assert not any(a.grave for a in avisos)


def test_el_credito_llega_hasta_la_fila_del_csv(monkeypatch):
    """De nada sirve completar la fecha si despues el CSV dice que salio de
    Wikipedia: la fila estaria mintiendo sobre su propio origen."""
    from fad import dataset, fechas
    monkeypatch.setattr(fechas, "descargar", lambda *a, **k: _la_otra_fuente())
    ps, _ = build.procesar(_sin_fecha(), CON_WF)
    fila = dataset.a_fila(ps[0], CON_WF.torneo, CON_WF.temporada, CON_WF.url, False)
    assert "wikipedia" in fila["source"] and "worldfootball" in fila["source"]


def test_si_la_segunda_fuente_no_esta_el_build_sigue(monkeypatch):
    """El sitio es de terceros y hoy nos devuelve 403. Que se caiga no puede
    frenar el build de todos los dias: se avisa, los partidos quedan sin fecha y
    van a `sin-fecha/`, que es exactamente lo que pasaba antes de que existiera
    la segunda fuente."""
    from fad import fechas

    def explota(*a, **k):
        raise OSError("HTTP Error 403: Forbidden")

    monkeypatch.setattr(fechas, "descargar", explota)
    ps, avisos = build.procesar(_sin_fecha(), CON_WF)
    assert [p for p in ps if p.fecha] == []
    assert not any(a.grave for a in avisos), "un sitio caido no es un error grave"
    assert any("segunda fuente" in a.que for a in avisos)


def test_no_se_consulta_a_la_segunda_fuente_sin_wf(monkeypatch):
    """Los otros 92 torneos del catalogo no la tocan ni de casualidad."""
    from fad import fechas

    def explota(*a, **k):
        raise AssertionError("no se tenia que llamar")

    monkeypatch.setattr(fechas, "descargar", explota)
    build.procesar(tabla(("Boca Juniors", "River Plate")), T)


def test_un_marcador_distinto_no_trae_la_fecha(monkeypatch):
    """La regla de `completar`: los equipos identifican y el marcador verifica.
    Si las dos fuentes no coinciden en el resultado, no se completa nada."""
    from fad import fechas
    monkeypatch.setattr(fechas, "descargar", lambda *a, **k: _la_otra_fuente(3, 0))
    ps, avisos = build.procesar(_sin_fecha(), CON_WF)
    assert [p for p in ps if p.fecha] == []
    assert any("marcador distinto" in a.detalle for a in avisos)


# --------------------------------------------------------------------------
# el catalogo
# --------------------------------------------------------------------------
def test_solo_las_paginas_sin_fecha_llevan_wf():
    """`wf` es una dependencia de un sitio de terceros: va donde hace falta y en
    ningun otro lado. Hoy son las cuatro B Nacional de 2007-2011."""
    from fad import torneos
    con_wf = [t for t in torneos.TODOS if t.wf]
    assert len(con_wf) == 4
    assert all(t.torneo == "Primera Nacional" for t in con_wf)
    assert {t.temporada for t in con_wf} == {2007, 2008, 2009, 2010}
    assert len({t.wf for t in con_wf}) == 4, "cada temporada con su id"
    assert all(t.cerrado for t in con_wf), \
        "si no fueran cerrados se consultaria el sitio todos los dias"


# --------------------------------------------------------------------------
# las correcciones a mano, enchufadas al pipeline
# --------------------------------------------------------------------------
def _tabla_con_error() -> str:
    """La Fecha 12 de la B Nacional 2009-10 en chiquito: un club repetido en la
    misma jornada, que es lo que la hace imposible."""
    return tabla(("Boca Juniors", "River Plate"), ("Racing Club", "River Plate"))


def _correccion(monkeypatch, dice, debe=("Racing Club", "Independiente")):
    from fad import correcciones
    from fad.correcciones import Correccion
    monkeypatch.setattr(correcciones, "CORRECCIONES", (
        Correccion(pagina=T.pagina, jornada="Fecha 1", dice=dice, debe=debe,
                   porque="x" * 90),))


def test_una_correccion_arregla_lo_que_el_chequeo_agarro(monkeypatch):
    """Sin la correccion, `una_vez_por_jornada` marca grave y el torneo entero se
    queda afuera. Con ella entra, y el aviso dice que se toco algo."""
    ps, avisos = build.procesar(_tabla_con_error(), T)
    assert any(a.grave for a in avisos), "sin corregir, tiene que ser grave"

    _correccion(monkeypatch, ("Racing Club", "River Plate", 2, 1))
    ps, avisos = build.procesar(_tabla_con_error(), T)
    assert not any(a.grave for a in avisos)
    assert {p.visita for p in ps} == {"River Plate", "Independiente"}
    assert any("corregidos a mano" in a.que for a in avisos), \
        "corregir en silencio seria peor que no corregir"


def test_una_correccion_que_quedo_sin_efecto_frena_el_build(monkeypatch):
    """Si Wikipedia arregla la pagina, esta entrada deja de enganchar. Eso es
    GRAVE: o se saca, o esta apuntando a otra cosa. Las dos se miran a mano."""
    _correccion(monkeypatch, ("Racing Club", "Boca Juniors", 9, 9))
    _, avisos = build.procesar(_tabla_con_error(), T)
    graves = [a for a in avisos if a.grave]
    assert any("correccion que no aplica" in a.que for a in graves)


# --------------------------------------------------------------------------
# un torneo que comparte la pagina de la temporada con otro
# --------------------------------------------------------------------------
_TEMPORADA = """== Equipos ==
los veinte de siempre

== Torneo Apertura ==
=== Tabla de posiciones final ===
la tabla del Apertura

== Torneo Clausura ==
=== Tabla de posiciones final ===
la tabla del Clausura

== Tabla de posiciones final del campeonato ==
la combinada, de 38 partidos
"""


def test_el_recorte_se_queda_con_su_seccion_y_entera():
    """Una pagina de TEMPORADA publica dos torneos, con una tabla cada uno y una
    combinada. Sin recortar, los chequeos de tabla se quedan con la combinada
    --gana por PJ-- y despues se callan porque 38 no es 19."""
    apertura = build._sola_su_seccion(_TEMPORADA, "Torneo Apertura")
    assert "la tabla del Apertura" in apertura
    assert "la tabla del Clausura" not in apertura
    assert "la combinada" not in apertura
    assert "los veinte de siempre" not in apertura


def test_el_recorte_no_corta_en_un_subtitulo():
    """LA GUARDA QUE IMPORTA. La tabla cuelga de un `=== Tabla de posiciones final
    ===`, que esta ADENTRO de la seccion. Si el corte tomara cualquier renglon de
    `=`, cortaria ahi y devolveria una seccion vacia: el torneo se quedaria sin
    arbitro y el build no diria nada, que es exactamente el modo de falla que este
    recorte vino a cerrar."""
    apertura = build._sola_su_seccion(_TEMPORADA, "Torneo Apertura")
    assert "Tabla de posiciones final" in apertura, "se comio el subtitulo"
    assert apertura.strip(), "recorte vacio"


_CON_PLANTILLAS = """== Equipos ==
los de siempre

== Tabla de posiciones final ==
{{Tabla de posiciones inicio}}
{{Tabla de posiciones equipo|pos=1|g=1|e=0|p=0|gf=2|gc=0|eq=[[Boca Juniors]]}}
{{Tabla de posiciones equipo|pos=2|g=0|e=0|p=1|gf=0|gc=2|eq=[[River Plate]]}}
{{Tabla de posiciones fin}}

== Goleadores ==
nadie
"""


def test_el_recorte_conserva_su_propio_encabezado():
    """EL INTERRUPTOR MUDO. Las tablas escritas con plantillas se reconocen por el
    TITULO de la seccion que las contiene. Si esa seccion es justo la que se pide y
    el recorte la devuelve sin su `== ... ==`, quedan cero filas: el torneo se queda
    sin arbitro, entra igual y no avisa.

    Lo encontro la medicion de la 1985-86, no un test: pidiendo `Tabla de posiciones
    final` salian 2987 caracteres y ninguna fila, y ensuciando un marcador a
    proposito no saltaba nada. La primera version del recorte solo se habia probado
    con la 1990-91, donde la tabla cuelga de un subtitulo de ADENTRO de la seccion y
    el encabezado de afuera no hacia falta."""
    recorte = build._sola_su_seccion(_CON_PLANTILLAS, "Tabla de posiciones final")
    assert "== Tabla de posiciones final ==" in recorte
    assert "Goleadores" not in recorte and "los de siempre" not in recorte
    assert set(posiciones.tabla(recorte)) == {"Boca Juniors", "River Plate"}, \
        "sin el encabezado el lector de plantillas no reconoce la tabla"


# --------------------------------------------------------------------------
# la capa 1985-1990: campeonatos unicos, todos contra todos a dos ruedas
# --------------------------------------------------------------------------
import pytest  # noqa: E402

# temporada -> (clubes, partidos que NO se pueden escribir)
_CAPA_1985 = {1985: (19, 0), 1986: (20, 0), 1987: (20, 0), 1988: (20, 1), 1989: (20, 1)}


@pytest.mark.parametrize("temporada", sorted(_CAPA_1985))
def test_la_capa_1985_1990_trae_el_torneo_entero(temporada):
    """Un todos contra todos a dos ruedas son N*(N-1) partidos, y cada club juega
    2*(N-1). Con eso alcanza para ver si falta una fecha, que es el modo de falla de
    esta capa: los partidos salen de un ARCHIVO de RSSSF recortado entre dos anclas,
    y un ancla puesta un renglon mas abajo se come la primera jornada entera.

    Paso de verdad en el Apertura 1990 y volvia a estar a un paso en la 1985-86:
    anclando en `[Jul 6]`, que es unico, quedaban 333 partidos en las rondas 2 a 38
    y NINGUN chequeo del build avisaba, porque los de tabla comparan solo a los
    clubes cuyo PJ ya coincide.

    Mira el CSV y no el lector a proposito: el lector necesita el archivo de RSSSF,
    que no esta en el repo. Lo que el repo si tiene es el resultado."""
    import csv
    import pathlib
    datos = pathlib.Path(__file__).resolve().parent.parent / "data" / f"partidos-{temporada}.csv"
    if not datos.exists():
        pytest.skip("hace falta el dataset")
    clubes, fuera = _CAPA_1985[temporada]
    with datos.open(encoding="utf-8") as fh:
        filas = [f for f in csv.DictReader(fh)
                 if f["tournament"] == "Primera Division" and f["season"] == str(temporada)]
    assert len(filas) == clubes * (clubes - 1) - fuera, len(filas)
    jugados = {}
    for f in filas:
        for c in (f["home_team"], f["away_team"]):
            jugados[c] = jugados.get(c, 0) + 1
    assert len(jugados) == clubes, sorted(jugados)
    if not fuera:
        assert set(jugados.values()) == {2 * (clubes - 1)}, jugados
    jornadas = {f["matchday"] for f in filas}
    esperadas = 2 * clubes if clubes % 2 else 2 * (clubes - 1)
    assert len(jornadas) == esperadas, f"{len(jornadas)} jornadas, van {esperadas}"
    assert all(f["date"] for f in filas), "un partido sin dia no se escribe"


# --------------------------------------------------------------------------
# la 1988-89: la temporada que se definia por penales
# --------------------------------------------------------------------------
# La tabla final tal como la publica RSSSF en `arg89`: PJ, G, E, P, GF, GC.
_FINAL_1988 = {
    'Independiente': (38, 22, 11, 5, 58, 32),
    'Boca Juniors': (38, 20, 9, 9, 56, 38),
    'Deportivo Español': (38, 16, 14, 8, 45, 31),
    'River Plate': (38, 16, 13, 9, 61, 36),
    'San Lorenzo': (38, 16, 10, 12, 58, 44),
    'Talleres (C)': (38, 16, 12, 10, 48, 43),
    'Argentinos Juniors': (38, 13, 16, 9, 55, 39),
    'Estudiantes (LP)': (38, 15, 12, 11, 53, 41),
    'Racing Club': (38, 13, 16, 9, 47, 41),
    'Gimnasia y Esgrima (LP)': (38, 10, 16, 12, 31, 30),
    'Vélez Sarsfield': (38, 8, 17, 13, 37, 54),
    "Newell's Old Boys": (38, 11, 13, 14, 42, 44),
    'Rosario Central': (38, 10, 16, 12, 49, 55),
    'Deportivo Mandiyú': (38, 7, 19, 12, 35, 44),
    'Platense': (38, 11, 11, 16, 36, 51),
    'Racing (C)': (38, 11, 11, 16, 38, 54),
    'San Martín (T)': (38, 12, 10, 16, 38, 49),
    'Ferro Carril Oeste': (38, 8, 14, 16, 35, 43),
    'Deportivo Armenio': (38, 5, 15, 18, 29, 57),
    'Instituto': (38, 7, 9, 22, 38, 65),
}


def _filas_de_la_1988():
    import csv
    import pathlib
    datos = pathlib.Path(__file__).resolve().parent.parent / "data" / "partidos-1988.csv"
    if not datos.exists():
        pytest.skip("hace falta el dataset")
    with datos.open(encoding="utf-8") as fh:
        return [f for f in csv.DictReader(fh)
                if f["tournament"] == "Primera Division" and f["season"] == "1988"]


def test_la_1988_89_cierra_contra_la_tabla_final_de_su_fuente():
    """EL TESTIGO DE LAS FECHAS 20 A 38, que no tienen otro. La tabla del campeonato
    que publica Wikipedia tiene mal los goles de 14 clubes y no se usa; la del
    Apertura arbitra la primera rueda. Para la segunda queda esto: la tabla final
    de la propia fuente, contra la suma de los partidos.

    No es un testigo independiente --son la tabla y los partidos del mismo
    archivo--, pero dice que el archivo se leyo entero y bien, que es lo que mas
    fallo en esta temporada: leyendo 249 partidos de 380 no cierra ni un club.

    Dieciocho cierran en las seis cifras. Los otros dos son Newell's y Rosario
    Central, a los que les falta lo mismo: un partido, una derrota y un gol en
    contra. Es el clasico que perdieron los dos, que no tiene fila."""
    suma = {}
    for f in _filas_de_la_1988():
        gl, gv = int(f["home_score"]), int(f["away_score"])
        for club, gf, gc in ((f["home_team"], gl, gv), (f["away_team"], gv, gl)):
            r = suma.setdefault(club, [0, 0, 0, 0, 0, 0])
            r[0] += 1
            r[1 + (0 if gf > gc else 1 if gf == gc else 2)] += 1
            r[4] += gf
            r[5] += gc
    assert set(suma) == set(_FINAL_1988)
    for club, (pj, g, e, p, gf, gc) in _FINAL_1988.items():
        if club in ("Newell's Old Boys", "Rosario Central"):
            pj, p, gc = pj - 1, p - 1, gc - 1
        assert tuple(suma[club]) == (pj, g, e, p, gf, gc), club


# La tabla de penales que `arg89` publica aparte de los partidos: por club, los
# partidos empatados, las tandas ganadas y las perdidas.
_PENALES_1988 = {
    'Vélez Sarsfield': (17, 12, 5),
    'Gimnasia y Esgrima (LP)': (16, 11, 5),
    'Deportivo Mandiyú': (19, 11, 8),
    'San Lorenzo': (10, 8, 2),
    'Boca Juniors': (9, 7, 2),
    'Independiente': (11, 7, 4),
    "Newell's Old Boys": (13, 7, 6),
    'Ferro Carril Oeste': (14, 7, 7),
    'Deportivo Armenio': (15, 7, 8),
    'Rosario Central': (16, 7, 9),
    'Platense': (11, 6, 5),
    'Racing (C)': (11, 6, 5),
    'River Plate': (13, 6, 7),
    'Deportivo Español': (14, 6, 8),
    'Racing Club': (16, 6, 10),
    'Argentinos Juniors': (16, 6, 10),
    'Talleres (C)': (12, 5, 7),
    'Estudiantes (LP)': (12, 4, 8),
    'San Martín (T)': (10, 2, 8),
    'Instituto': (9, 1, 8),
}


def test_en_la_1988_89_las_tandas_cierran_contra_la_tabla_de_penales():
    """Tres puntos al que ganaba, dos al que empataba y ganaba la tanda, uno al que
    la perdia. La fuente publica las tandas dos veces y por separado: pegadas al
    marcador de cada partido, y en una tabla que cuenta, por club, cuantas gano y
    cuantas perdio. Contar las primeras tiene que dar la segunda.

    Y da, en los veinte clubes, salvo por UN PARTIDO: `Rosario Central 1-1
    Instituto`, fecha 12. Es el unico de los 132 empates que la fuente escribe sin
    su tanda. La tabla dice que existio y quien la gano --a Central le falta una
    ganada y a Instituto una perdida-- pero no por cuanto, asi que la fila queda con
    los penales vacios: se sabe el ganador y no hay columna para eso."""
    filas = _filas_de_la_1988()
    empates = [f for f in filas if f["home_score"] == f["away_score"]]
    con_tanda = [f for f in filas if f["home_pens"] != ""]
    assert len(empates) == 132 and len(con_tanda) == 131
    assert all(f["home_score"] == f["away_score"] for f in con_tanda), \
        "una tanda sobre un partido con ganador"
    assert all(f["home_pens"] != f["away_pens"] for f in con_tanda), "una tanda tiene ganador"
    assert [(f["home_team"], f["away_team"], f["matchday"]) for f in empates
            if f["home_pens"] == ""] == [("Rosario Central", "Instituto", "Fecha 12")]

    cuenta = {}
    for f in empates:
        for club, mios, suyos in ((f["home_team"], f["home_pens"], f["away_pens"]),
                                  (f["away_team"], f["away_pens"], f["home_pens"])):
            r = cuenta.setdefault(club, [0, 0, 0])
            r[0] += 1
            if mios != "":
                r[1 if int(mios) > int(suyos) else 2] += 1
    falta = {"Rosario Central": (0, 1, 0), "Instituto": (0, 0, 1)}
    for club, tabla_de_la_fuente in _PENALES_1988.items():
        esperado = tuple(a - b for a, b in zip(tabla_de_la_fuente, falta.get(club, (0, 0, 0))))
        assert tuple(cuenta[club]) == esperado, club


# --------------------------------------------------------------------------
# el Nacional 1985: ocho zonas y doble eliminacion
# --------------------------------------------------------------------------
# Las ocho tablas de zona tal como las publica la pagina: G, E, P, GF, GC. Son el
# testigo de los 96 partidos de la fase, y la de la Zona C es ademas la que arbitra
# el `Guarani Antonio Franco - Talleres (C)` de la fecha 5; ver el `Marcador` en
# fad/correcciones.py. Copiadas de la revision 175539170, la de las filas.
_ZONAS_1985 = {
    "Zona A": {
        "Estudiantes (LP)": (4, 1, 1, 12, 4),
        "Ramón Santamarina": (2, 1, 3, 5, 6),
        "Racing (C)": (2, 1, 3, 5, 8),
        "Platense": (2, 1, 3, 5, 9),
    },
    "Zona B": {
        "Boca Juniors": (3, 2, 1, 13, 6),
        "Estudiantes (RC)": (3, 1, 2, 12, 12),
        "Temperley": (2, 1, 3, 8, 11),
        "Altos Hornos Zapla": (2, 0, 4, 5, 9),
    },
    "Zona C": {
        "Independiente": (3, 1, 2, 11, 6),
        "Talleres (C)": (3, 1, 2, 6, 6),
        "Guaraní Antonio Franco": (3, 1, 2, 6, 8),
        "Huracán": (0, 3, 3, 7, 10),
    },
    "Zona D": {
        "River Plate": (4, 2, 0, 10, 4),
        "Unión": (1, 3, 2, 9, 6),
        "Gimnasia y Esgrima (LP)": (1, 3, 2, 4, 10),
        "Cipolletti": (0, 4, 2, 5, 8),
    },
    "Zona E": {
        "Newell's Old Boys": (2, 4, 0, 9, 6),
        "San Lorenzo": (2, 3, 1, 10, 5),
        "Huracán Las Heras": (2, 3, 1, 8, 8),
        "Círculo Deportivo": (1, 0, 5, 6, 14),
    },
    "Zona F": {
        "Argentinos Juniors": (3, 3, 0, 16, 5),
        "Chacarita Juniors": (3, 1, 2, 11, 6),
        "Central Norte (S)": (1, 3, 2, 4, 14),
        "Belgrano": (0, 3, 3, 8, 14),
    },
    "Zona G": {
        "San Martín (T)": (3, 2, 1, 12, 4),
        "Vélez Sarsfield": (3, 2, 1, 11, 6),
        "Argentino (F)": (2, 1, 3, 5, 10),
        "Juventud Alianza": (1, 1, 4, 4, 12),
    },
    "Zona H": {
        "Ferro Carril Oeste": (4, 1, 1, 8, 2),
        "Deportivo Español": (3, 1, 2, 9, 6),
        "Instituto": (3, 0, 3, 9, 9),
        "Juventud Antoniana": (1, 0, 5, 4, 13),
    },
}

# El dia de cada fecha de zonas, y los cinco partidos que se jugaron otro. Salen de
# "Futbol Argentino: Cronicas y Estadisticas", que encabeza cada fecha con su dia
# --"1a FECHA (17 de febrero)"-- y anota "(Se jugo el ...)" arriba de la ficha del
# partido que no fue ese dia. RSSSF da los mismos seis dias, por ronda.
_DIA_DE_LA_FECHA_1985 = {"Fecha 1": "1985-02-17", "Fecha 2": "1985-02-24",
                         "Fecha 3": "1985-03-03", "Fecha 4": "1985-03-06",
                         "Fecha 5": "1985-03-10", "Fecha 6": "1985-03-17"}
_JUGADOS_OTRO_DIA_1985 = {
    ("Cipolletti", "Gimnasia y Esgrima (LP)"): "1985-02-23",
    ("Círculo Deportivo", "Newell's Old Boys"): "1985-02-23",
    ("Newell's Old Boys", "San Lorenzo"): "1985-03-01",
    ("Unión", "Cipolletti"): "1985-03-02",
    ("Newell's Old Boys", "Círculo Deportivo"): "1985-03-07",
}

# Las tres finales del torneo, fila por fila: fecha, local, goles, penales, visitante,
# cancha y `neutral`. En el CSV las cinco dicen `matchday=Final`, y lo unico que las
# separa es la fecha. Las da la obra --"RONDA DE GANADORES / FINAL - IDA" y "- VUELTA",
# "RONDA DE PERDEDORES / FINAL - PARTIDO UNICO" y "FINAL GANADORES - PERDEDORES"--, y
# RSSSF las mismas, con "Champion: Asociacion Atletica Argentinos Juniors".
_FINALES_1985 = {
    "ganadores": [
        ("1985-07-09", "Argentinos Juniors", "2", "0", "", "", "Vélez Sarsfield",
         "Estadio La Bombonera", "false"),
        ("1985-07-17", "Vélez Sarsfield", "2", "0", "2", "4", "Argentinos Juniors",
         "Estadio José Amalfitani", "false"),
    ],
    "perdedores": [
        ("1985-08-07", "Vélez Sarsfield", "2", "1", "", "", "River Plate",
         "Estadio Tomás Adolfo Ducó", "true"),
    ],
    "campeonato": [
        ("1985-08-28", "Argentinos Juniors", "1", "1", "3", "4", "Vélez Sarsfield",
         "Estadio Monumental", "true"),
        ("1985-09-04", "Vélez Sarsfield", "1", "2", "", "", "Argentinos Juniors",
         "Estadio Monumental", "true"),
    ],
}


def _filas_del_nacional_1985():
    import csv
    import pathlib
    datos = pathlib.Path(__file__).resolve().parent.parent / "data" / "partidos-1985.csv"
    if not datos.exists():
        pytest.skip("hace falta el dataset")
    with datos.open(encoding="utf-8") as fh:
        return [f for f in csv.DictReader(fh)
                if f["tournament"] == "Primera Division - Nacional"]


def _posiciones_por_zona(filas):
    """{club: (zona, puesto)} con 2 puntos por triunfo y, a igual puntaje, la
    diferencia de gol. En 1985 no hacia falta mas: ningun primero ni segundo empata
    en las dos cosas."""
    suma = {}
    for f in filas:
        if f["phase"] != "zonas":
            continue
        gl, gv = int(f["home_score"]), int(f["away_score"])
        for club, gf, gc in ((f["home_team"], gl, gv), (f["away_team"], gv, gl)):
            zona, pts, dif = suma.get(club, (f["group"], 0, 0))
            suma[club] = (zona, pts + (2 if gf > gc else 1 if gf == gc else 0), dif + gf - gc)
    puesto = {}
    for zona in {z for z, _, _ in suma.values()}:
        orden = sorted((c for c in suma if suma[c][0] == zona),
                       key=lambda c: suma[c][1:], reverse=True)
        assert suma[orden[1]][1:] != suma[orden[2]][1:], f"{zona}: empate en el corte"
        puesto.update({c: (zona, i + 1) for i, c in enumerate(orden)})
    return puesto


def test_el_nacional_1985_esta_entero():
    """160 partidos, que es lo que publican la pagina y `arg85`: 8 zonas de 4 a dos
    ruedas, y 64 de eliminacion entre las dos rondas y la final. Sin la Sexta fase en
    el vocabulario del parser, el `River 2-0 Newell's` del 31 de julio salia en la
    Quinta y nada lo decia."""
    filas = _filas_del_nacional_1985()
    assert len(filas) == 160
    zonas = [f for f in filas if f["phase"] == "zonas"]
    assert sorted({(f["group"], sum(g["group"] == f["group"] for g in zonas))
                   for f in zonas}) == [(f"Zona {z}", 12) for z in "ABCDEFGH"]
    rondas = {}
    for f in filas:
        if f["phase"] == "eliminacion":
            rondas[f["matchday"]] = rondas.get(f["matchday"], 0) + 1
    assert rondas == {"Octavos": 16, "Cuartos": 4, "Semifinales": 2, "Primera fase": 16,
                      "Segunda fase": 8, "Tercera fase": 6, "Cuarta fase": 4,
                      "Quinta fase": 2, "Sexta fase": 1, "Final": 5}
    assert all("1985-02-17" <= f["date"] <= "1985-09-04" for f in filas)
    clubes = {}
    for f in filas:
        for c in (f["home_team"], f["away_team"]):
            clubes[c] = clubes.get(c, 0) + 1
    assert len(clubes) == 32
    # Los dos que el padron no tenia: seis de zona y los dos de la primera fase.
    assert clubes["Argentino (F)"] == clubes["Juventud Alianza"] == 8


def test_las_ocho_zonas_del_nacional_1985_cierran_contra_su_tabla():
    """LAS TABLAS DE LA PAGINA CONTRA LOS PARTIDOS PUBLICADOS, club por club: cierran
    los 32 en las cinco cifras, asi que un marcador cualquiera de los 96 que se mueva
    descuadra a sus dos clubes. En la Zona C, con el 2-2 que publica la grilla
    cerraban 30 de 32: a Guarani y a Talleres les sobraba un empate, y ademas a Guarani
    dos goles en contra y a Talleres dos a favor."""
    suma = {}
    for f in _filas_del_nacional_1985():
        if f["phase"] != "zonas":
            continue
        gl, gv = int(f["home_score"]), int(f["away_score"])
        for club, gf, gc in ((f["home_team"], gl, gv), (f["away_team"], gv, gl)):
            r = suma.setdefault(f["group"], {}).setdefault(club, [0, 0, 0, 0, 0])
            r[0 if gf > gc else 1 if gf == gc else 2] += 1
            r[3] += gf
            r[4] += gc
    assert {z: {c: tuple(r) for c, r in cs.items()} for z, cs in suma.items()} == _ZONAS_1985


def test_los_dias_de_las_zonas_del_nacional_1985():
    """El dia de su fecha, salvo los cinco que la obra anota jugados otro dia; los 96
    lo cumplen. Que la grilla los fechara asi es una de las cosas que dicen que copia a
    la obra y no a RSSSF: a esos cinco RSSSF les da el dia de la ronda."""
    for f in _filas_del_nacional_1985():
        if f["phase"] != "zonas":
            continue
        esperado = _JUGADOS_OTRO_DIA_1985.get((f["home_team"], f["away_team"]),
                                             _DIA_DE_LA_FECHA_1985[f["matchday"]])
        assert f["date"] == esperado, (f["matchday"], f["home_team"], f["away_team"])


def test_en_las_zonas_del_nacional_1985_cada_club_es_local_en_una_cancha():
    """Los tres partidos de local de cada club, en la misma cancha. Tres usaron dos, y
    la obra lo dice en la ficha del que se mudo: 'CANCHA: Centro Siderurgico Palpala.'
    para Altos Hornos Zapla, 'CANCHA: Villa Dalmine (Campana).' para dos de Chacarita y
    'CANCHA: Central Norte (Salta).' para Juventud Antoniana. Una cancha cambiada en
    cualquier otra fila deja a su club con dos."""
    canchas = {}
    for f in _filas_del_nacional_1985():
        if f["phase"] == "zonas":
            c = canchas.setdefault(f["home_team"], {})
            c[f["venue"]] = c.get(f["venue"], 0) + 1
    assert len(canchas) == 32
    assert {club: c for club, c in canchas.items() if len(c) != 1} == {
        "Altos Hornos Zapla": {"Emilio Fabrizzi": 2, "Centro Siderúrgico": 1},
        "Chacarita Juniors": {"El Coliseo de Mitre y Puccini": 2, "Chacarita Juniors": 1},
        "Juventud Antoniana": {"Fray Honorato Pistoia": 2, "Doctor Luis Güemes": 1},
    }


def test_las_tres_finales_del_nacional_1985_y_su_campeon():
    """LA DE GANADORES, ida y vuelta: 2-0 y 0-2, y la ganaron los penales de Argentinos.
    LA DE PERDEDORES, a partido unico: la gano Velez. Y LA DEL CAMPEONATO: el que venia
    de perdedores tenia que ganar dos veces, gano la primera por penales, y Argentinos
    fue campeon en el desempate. Las dos ultimas, en cancha neutral; la de ganadores no,
    porque fue de ida y vuelta: la ida la jugo Argentinos de local en la Bombonera."""
    filas = [(f["date"], f["home_team"], f["home_score"], f["away_score"], f["home_pens"],
              f["away_pens"], f["away_team"], f["venue"], f["neutral"])
             for f in _filas_del_nacional_1985() if f["matchday"] == "Final"]
    assert sorted(filas) == sorted(sum(_FINALES_1985.values(), []))

    def ganador(fila):
        _, local, gl, gv, pl, pv, visita, _, _ = fila
        a, b = (int(gl), int(gv)) if gl != gv else (int(pl), int(pv))
        return local if a > b else visita

    ida, vuelta = _FINALES_1985["ganadores"]
    assert int(ida[2]) + int(vuelta[3]) == int(ida[3]) + int(vuelta[2]), "quedo igualada"
    # La tanda, despues del 2-2 global, es de la serie y no del partido de vuelta.
    assert int(vuelta[4]) < int(vuelta[5]) and vuelta[6] == "Argentinos Juniors"
    assert ganador(_FINALES_1985["perdedores"][0]) == "Vélez Sarsfield"
    primera, desempate = _FINALES_1985["campeonato"]
    assert ganador(primera) == "Vélez Sarsfield" and ganador(desempate) == "Argentinos Juniors"


def test_las_zonas_del_nacional_1985_no_son_neutrales():
    """La fase de zonas se jugo en la cancha de cada local: la pagina no dice neutral en
    ninguna de sus secciones, y la regla de la seccion no tiene que marcar ninguna."""
    zonas = [f for f in _filas_del_nacional_1985() if f["phase"] == "zonas"]
    assert len(zonas) == 96
    assert [f for f in zonas if f["neutral"] != "false"] == []


def test_el_neutral_de_la_eliminacion_del_nacional_1985():
    """CADA FILA DE LA ELIMINACION CON EL `neutral` QUE DICE EL REGLAMENTO, como lo
    cuentan la pagina y la obra. Ida y vuelta, `false`: los octavos, la primera fase de
    perdedores y la final de ganadores. Partido unico en cancha neutral, `true`, salvo
    en la tercera y la cuarta fase de perdedores, donde los que llegaban de la ronda de
    ganadores --los perdedores de cuartos y de semifinales-- jugaron de local. Diez de
    estas filas salian `false` y seis `true` hasta que se declararon; ver los `Neutral`
    del Nacional 1985 en fad/correcciones.py."""
    filas = _filas_del_nacional_1985()

    def perdedor(f):
        gl, gv = int(f["home_score"]), int(f["away_score"])
        if gl == gv:
            gl, gv = int(f["home_pens"]), int(f["away_pens"])
        return f["away_team"] if gl > gv else f["home_team"]

    de_ganadores = {"Tercera fase": {perdedor(f) for f in filas if f["matchday"] == "Cuartos"},
                    "Cuarta fase": {perdedor(f) for f in filas
                                    if f["matchday"] == "Semifinales"}}
    ida_y_vuelta = {"Octavos", "Primera fase"}
    final_de_ganadores = {fila[0] for fila in _FINALES_1985["ganadores"]}
    neutrales = 0
    for f in filas:
        if f["phase"] != "eliminacion":
            continue
        neutral = not (f["matchday"] in ida_y_vuelta
                       or (f["matchday"] == "Final" and f["date"] in final_de_ganadores)
                       or f["home_team"] in de_ganadores.get(f["matchday"], ()))
        assert f["neutral"] == str(neutral).lower(), (f["date"], f["matchday"],
                                                       f["home_team"], f["away_team"])
        neutrales += neutral
    assert len(de_ganadores["Tercera fase"]) == 4 and len(de_ganadores["Cuarta fase"]) == 2
    assert neutrales == 24


def test_los_octavos_del_nacional_1985_cruzan_primero_contra_segundo():
    """EL TESTIGO QUE NO ES NINGUNA TABLA: el cuadro. La pagina y RSSSF publican los
    mismos cruces de octavos, y los seis que no tocan la Zona C son del primero de
    una zona contra el segundo de su pareja. Los otros dos cumplen solo si la Zona C
    la termina primera Independiente, y eso pasa con el 2-0 --tres clubes en 7
    puntos, Independiente con +5 y Talleres con 0--: con el 2-2 Talleres seria
    primero con 8, y quedarian un primero contra primero y un segundo contra segundo."""
    filas = _filas_del_nacional_1985()
    puesto = _posiciones_por_zona(filas)
    cruces = {frozenset((f["home_team"], f["away_team"])) for f in filas
              if f["matchday"] == "Octavos"}
    assert len(cruces) == 8
    parejas = set()
    for cruce in cruces:
        a, b = sorted(cruce, key=lambda c: puesto[c][1])
        assert (puesto[a][1], puesto[b][1]) == (1, 2), (a, puesto[a], b, puesto[b])
        parejas.add(frozenset((puesto[a][0][-1], puesto[b][0][-1])))
    assert parejas == {frozenset(p) for p in ("AC", "BG", "DH", "EF")}
    assert puesto["Independiente"] == ("Zona C", 1) and puesto["Talleres (C)"] == ("Zona C", 2)


def test_el_independiente_boca_del_nacional_1985_sale_suspendido():
    """Tercera fase de la ronda de perdedores, 7 de abril. La plantilla trae el suceso
    --suspendido a los 40 minutos del segundo tiempo, 1-0, y la AFA lo dio por
    terminado con ese resultado-- y el parser lo lee: sale `suspendido` con el 1-0, sin
    ninguna correccion a mano. RSSSF dice lo mismo, `(Abandoned at 85')`.

    Es lo que dice la pagina y nada mas: si esa fila tiene que decir otra cosa es una
    decision sobre el `status`, no sobre este partido. Y es el unico de los 160 con
    `status`."""
    filas = _filas_del_nacional_1985()
    con_status = [(f["date"], f["matchday"], f["home_team"], f["home_score"],
                   f["away_score"], f["away_team"], f["status"])
                  for f in filas if f["status"]]
    assert con_status == [("1985-04-07", "Tercera fase", "Independiente", "1", "0",
                           "Boca Juniors", "suspendido")]


def test_las_rondas_declaradas_como_torneo_aparte_SALEN_CON_SU_LLAVE(monkeypatch):
    """El cableado de `rsssf.con_llaves`. La llave no va al CSV, asi que si
    `procesar` deja de pedirla ninguna fila cambia y ningun otro test se entera: lo
    unico que se pierde es el arbitro de esas rondas, que es justo lo que no avisa."""
    from fad import rsssf
    t = Torneo("Anexo:Prueba", "Prueba", 1988, anio_fin=1989, cerrado=False,
               sin_grilla=True)
    crudo = ("Round 1@N@[Sep 11]@N@Boca Juniors            1-0 River Plate@N@"
             "Round 2@N@[Sep 18]@N@River Plate             2-2 Boca Juniors@N@"
             ).replace("@N@", chr(10))
    monkeypatch.setattr(rsssf, "FUENTES", {t.pagina: ("archivo", {"": {
        "Boca Juniors": "Boca Juniors", "River Plate": "River Plate"}})})
    monkeypatch.setattr(rsssf, "descargar", lambda *a, **k: crudo)
    monkeypatch.setattr(rsssf, "LLAVES_POR_RONDA", {t.pagina: ((1, 1, "Torneo Apertura"),)})
    ps, _ = build.procesar("", t)
    assert {p.jornada: p.llave for p in ps} == {"Fecha 1": "Torneo Apertura", "Fecha 2": ""}


def test_la_llave_declarada_es_la_seccion_que_el_torneo_recorta():
    """Las dos declaraciones tienen que decir lo mismo y viven en archivos
    distintos: `torneos.py` dice que tabla de la pagina se lee (`seccion`) y
    `rsssf.py` dice que rondas le tocan (`LLAVES_POR_RONDA`). Si una cambia sola, la
    tabla y los partidos dejan de encontrarse y los chequeos se callan."""
    from fad import rsssf, torneos
    for pagina, tramos in rsssf.LLAVES_POR_RONDA.items():
        (t,) = [x for x in torneos.TODOS if x.pagina == pagina]
        assert t.seccion in {llave for _, _, llave in tramos}, pagina


def test_si_la_seccion_no_esta_devuelve_la_pagina_entera():
    """Un nombre mal escrito no puede dejar al torneo mudo. Devolver vacio seria
    sacarle el arbitro sin que nada lo denuncie; devolver todo lo deja como estaba
    antes del recorte, y de ahi en mas hablan los chequeos de tabla."""
    assert build._sola_su_seccion(_TEMPORADA, "Torneo Que No Existe") == _TEMPORADA
    assert build._sola_su_seccion(_TEMPORADA, "") == _TEMPORADA


def test_los_dos_torneos_de_1990_91_miran_tablas_distintas():
    """El caso real que lo motivo: el Apertura 1990 y el Clausura 1991 comparten
    pagina, porque la del Clausura es una redireccion a la de la temporada y la del
    Apertura directamente no existe."""
    from fad import torneos
    pagina_clausura = "Anexo:Torneo Clausura 1991 (Argentina)"
    pagina_temporada = "Campeonato de Primera División 1990-91 (Argentina)"
    de = {t.pagina: t for t in torneos.TODOS
          if t.pagina in (pagina_clausura, pagina_temporada)}
    assert set(de) == {pagina_clausura, pagina_temporada}, sorted(de)
    assert de[pagina_clausura].seccion == "Torneo Clausura"
    assert de[pagina_temporada].seccion == "Torneo Apertura"
    assert de[pagina_clausura].rsssf == de[pagina_temporada].rsssf == "arg91"
    # y los dos sin grilla: la pagina publica tablas, no partidos
    assert de[pagina_clausura].sin_grilla and de[pagina_temporada].sin_grilla


def test_un_arbitraje_que_la_fuente_alcanzo_NO_frena_el_build(monkeypatch):
    """La otra mitad del de arriba, y la que se pago cara.

    Una correccion que deja de enganchar es grave porque puede estar apuntando a
    otra cosa. Pero hay un caso en que se sabe que no: cuando la pagina publica
    EXACTAMENTE lo que la correccion pedia. Ahi la fuente nos dio la razon, el dato
    sale bien con la entrada o sin ella, y frenar el build es frenarlo por acertar.

    Paso de verdad: el 26/09/2026 el bot aborto porque Wikipedia habia corregido el
    `Claypole 2-2 Sacachispas` a 2-0, que es lo que el arbitraje decia desde el 19.
    El dataset se quedo sin actualizar por haber tenido razon."""
    from fad import correcciones
    from fad.correcciones import Marcador
    monkeypatch.setattr(correcciones, "MARCADORES", (
        Marcador(pagina=T.pagina, jornada="Fecha 1", local="Racing Club",
                 visita="Boca Juniors", dice=(9, 9), debe=(2, 1),
                 porque="x" * 90),))
    _, avisos = build.procesar(tabla(("Racing Club", "Boca Juniors")), T)
    alcanzados = [a for a in avisos if "arbitraje que la fuente alcanzo" in a.que]
    assert len(alcanzados) == 1, [a.que for a in avisos]
    assert not alcanzados[0].grave, "el build no se puede frenar por haber acertado"
    assert not [a for a in avisos if a.grave], [a.que for a in avisos if a.grave]


def test_una_Dia_en_una_pagina_SIN_segunda_fuente_se_aplica_y_no_revienta(monkeypatch):
    """Corregir un dia a mano en una pagina que no tiene con quien cruzarse tiraba un
    `ValueError` y se llevaba el build entero.

    Las `Dia` entran a `correcciones.fechados` con tres campos y los `Fechado` con
    cinco. A las primeras las saca de la lista el completador que discrepa con ellas;
    sin completador se quedaban, y el aviso de los `Fechado` huerfanos desempaqueta
    cinco. Las 22 que habia vivian todas en paginas con segunda fuente, asi que el
    camino roto nunca se habia pisado."""
    from fad import correcciones
    from fad.correcciones import Dia
    monkeypatch.setattr(correcciones, "DIAS", (
        Dia(pagina=T.pagina, jornada="Fecha 1", local="Racing Club",
            visita="Boca Juniors", dice="2026-01-23", debe="2026-01-25",
            fuente="https://ejemplo.invalid/cronica", porque="x" * 90),))
    ps, avisos = build.procesar(tabla(("Racing Club", "Boca Juniors")), T)
    assert [p.fecha for p in ps] == ["2026-01-25"], "la correccion se aplica"
    assert not [a for a in avisos if "ya no enganchan" in a.que], \
        "una `Dia` no es un `Fechado` huerfano"
    assert not [a for a in avisos if a.grave], [a.que for a in avisos if a.grave]


def test_un_Fechado_que_ya_no_engancha_se_sigue_avisando(monkeypatch):
    """La otra mitad, que no tenia test: el aviso para el que SI fue escrito. Un
    `Fechado` declara verificado un desacuerdo de dia entre dos fuentes; si ninguna
    de las dos lo sigue teniendo, la verificacion quedo vieja y hay que decirlo."""
    from fad import correcciones
    from fad.correcciones import Fechado
    monkeypatch.setattr(correcciones, "FECHADOS", (
        Fechado(pagina=T.pagina, jornada="Fecha 1", local="Racing Club",
                visita="Boca Juniors", nuestra="2026-01-23", otra="2026-01-24",
                porque="x" * 90),))
    _, avisos = build.procesar(tabla(("Racing Club", "Boca Juniors")), T)
    huerfanos = [a for a in avisos if "ya no enganchan" in a.que]
    assert len(huerfanos) == 1, [a.que for a in avisos]
    assert "Racing Club vs Boca Juniors" in huerfanos[0].detalle
    assert not huerfanos[0].grave


def test_el_anio_en_que_arranca_un_torneo_NO_es_siempre_el_de_su_etiqueta():
    """`temporada` rotula la fila; `anio_inicio`, cuando esta, es el anio con que se
    fechan los partidos anteriores al corte. Eran el mismo campo, y la Copa
    Argentina 2011-12 --rotulada 2012, arrancada en 2011-- tenia que elegir entre
    fechar bien y rotular como las demas: sus 26 partidos de noviembre y diciembre
    de 2011 figuraban a fines de 2012, despues de la final."""
    pagina = (tabla(("Racing Club", "Boca Juniors"), ("River Plate", "Independiente"))
              .replace("23 de enero", "22 de noviembre").replace("24 de enero", "2 de febrero"))
    cruza = Torneo("Anexo:Prueba", "Prueba", 2012, anio_inicio=2011, anio_fin=2012,
                   mes_inicio=9, cerrado=False)
    ps, _ = build.procesar(pagina, cruza)
    assert sorted(p.fecha for p in ps) == ["2011-11-22", "2012-02-02"]
    assert cruza.temporada == 2012, "la etiqueta no se toca"

    # Y sin el campo todo sigue como siempre: el primer anio es el de la etiqueta.
    comun = Torneo("Anexo:Prueba", "Prueba", 2012, cerrado=False)
    ps, _ = build.procesar(pagina, comun)
    assert sorted(p.fecha for p in ps) == ["2012-02-02", "2012-11-22"]


def test_en_una_copa_ninguna_ronda_se_juega_despues_de_la_final():
    """La regla que habria frenado ese error el primer dia. No hace falta saber nada
    del calendario: en una eliminacion directa la final es lo ultimo, asi que una
    ronda fechada despues tiene el anio mal. Mira el CSV entero, que es donde viven
    las temporadas cerradas -- el build de todos los dias no las vuelve a leer."""
    import csv
    import pathlib
    import pytest
    datos = pathlib.Path(__file__).resolve().parent.parent / "data"
    if not list(datos.glob("partidos-*.csv")):
        pytest.skip("hace falta el dataset")
    rondas = {}
    for archivo in datos.glob("partidos-*.csv"):
        with archivo.open(encoding="utf-8") as fh:
            for f in csv.DictReader(fh):
                if f["tournament"] == "Copa Argentina" and f["date"]:
                    rondas.setdefault(f["season"], {}).setdefault(f["matchday"], []).append(f["date"])
    assert len(rondas) >= 13, sorted(rondas)
    for temporada, por_ronda in rondas.items():
        if "Final" not in por_ronda:
            continue                       # la edicion en curso
        final = max(por_ronda["Final"])
        tarde = {r: max(fs) for r, fs in por_ronda.items() if max(fs) > final}
        assert not tarde, f"Copa Argentina {temporada}: la final fue el {final} y {tarde}"


def test_un_torneo_con_segunda_fuente_no_se_le_pide_dos_veces(monkeypatch, tmp_path):
    """El test que faltaba, y el que habria agarrado el bug.

    `a_fila` escribe `source` con las DOS fuentes cuando la fecha vino de afuera,
    y `main` buscaba las filas guardadas por la URL pelada: no las encontraba
    nunca. Los cuatro torneos con `wf` se reparseaban todos los dias y se le
    volvia a pedir la pagina a un sitio de terceros -- lo unico que `cerrado=True`
    esta puesto para evitar. Y como ese sitio hoy contesta 403, el build
    terminaba con esas cuatro temporadas en cero y frenaba por regresion.

    Los dos asserts de una sola corrida no alcanzaban: `cerrado=True` en el
    catalogo y "el sitio se consulta una sola vez" parecen la misma afirmacion y
    no lo son. Hace falta pasar dos veces.
    """
    from fad import fechas
    salida = tmp_path / "data"
    pedidos = []

    def espiar(co, se, **k):
        pedidos.append((co, se))
        return _la_otra_fuente()

    CERRADO_WF = Torneo("Anexo:Prueba", "Prueba", 2007, cerrado=True, wf=("co1", "se1"))
    monkeypatch.setattr(build.torneos, "TODOS", [CERRADO_WF])
    monkeypatch.setattr(build.wiki, "wikitexto", lambda *a, **k: _sin_fecha())
    monkeypatch.setattr(fechas, "descargar", espiar)
    monkeypatch.setattr(build, "SALIDA", salida)

    assert build.main([]) == 0
    assert len(pedidos) == 1, "la primera vez si hay que pedirla"
    filas = build.dataset.leer_carpeta(salida)
    assert len(filas) == 1 and "worldfootball" in filas[0]["source"]

    assert build.main([]) == 0
    assert pedidos == [("co1", "se1")], \
        "la segunda corrida volvio a pedirle la pagina al sitio de terceros"
    assert len(build.dataset.leer_carpeta(salida)) == 1


def test_si_el_sitio_se_cae_las_filas_guardadas_no_se_pierden(monkeypatch, tmp_path):
    """Una vez que las fechas estan en el CSV, que el sitio deje de contestar no
    puede borrarlas. Con el reuso funcionando el torneo ni se procesa, asi que el
    403 no llega a tocar nada."""
    from fad import fechas
    salida = tmp_path / "data"
    CERRADO_WF = Torneo("Anexo:Prueba", "Prueba", 2007, cerrado=True, wf=("co1", "se1"))
    monkeypatch.setattr(build.torneos, "TODOS", [CERRADO_WF])
    monkeypatch.setattr(build.wiki, "wikitexto", lambda *a, **k: _sin_fecha())
    monkeypatch.setattr(build, "SALIDA", salida)

    monkeypatch.setattr(fechas, "descargar", lambda *a, **k: _la_otra_fuente())
    assert build.main([]) == 0

    def bloqueado(*a, **k):
        raise OSError("HTTP Error 403: Forbidden")

    monkeypatch.setattr(fechas, "descargar", bloqueado)
    assert build.main([]) == 0, "el 403 no tiene que frenar el build"
    filas = build.dataset.leer_carpeta(salida)
    # 22:00Z con la hora conocida son las 19:00 del 9 en Buenos Aires.
    assert len(filas) == 1 and filas[0]["date"] == "2007-08-09"


def test_un_mapa_declarado_inservible_no_se_usa(monkeypatch):
    """`derivar_padron` puede terminar diciendo que su propio mapa no sirve --
    dos ids apuntando al mismo club. Antes ese aviso se emitia y el mapa se usaba
    igual en la linea siguiente, que es la peor combinacion: queda dicho que el
    dato no es confiable y se lo usa lo mismo."""
    from fad import fechas
    visto = {}

    # `**k` y no la firma copiada: este doble solo mira `mapa`, y clavarle los
    # parametros de `completar` lo rompe cada vez que la funcion crece -- paso al
    # agregarle `verificadas`, y el test fallaba por el doble y no por el codigo.
    def espiar(nuestros, ajenos, mapa=None, arbitrados=None, **k):
        visto["mapa"] = mapa
        return 0, []

    monkeypatch.setattr(fechas, "descargar", lambda *a, **k: _la_otra_fuente())
    monkeypatch.setattr(fechas, "derivar_padron",
                        lambda *a, **k: ({"te1": "Boca Juniors", "te2": "Boca Juniors"},
                                         ["HAY DOS IDS APUNTANDO AL MISMO CLUB: el mapa no sirve"]))
    monkeypatch.setattr(fechas, "completar", espiar)
    _, avisos = build.procesar(_sin_fecha(), CON_WF)
    assert visto["mapa"] == {}, "se cruzo con un mapa que la propia derivacion descarto"
    assert any("no sirve" in a.que for a in avisos)


def test_una_pagina_SIN_GRILLA_recorta_su_seccion(monkeypatch):
    """Los cuatro torneos que estrenaron este camino tenian archivo propio en RSSSF,
    asi que leer el archivo entero alcanzaba. El Clausura 1991 comparte `arg91` con el
    Apertura 1990 y LOS DOS LOS JUEGAN LOS MISMOS VEINTE CLUBES: el mapa no puede
    desempatarlos, asi que sin recorte entran los 381 partidos de los dos torneos bajo
    el rotulo de uno -- y encima fechados, porque cada seccion trae sus dias.
    """
    from fad import rsssf, torneos
    visto = {}

    def espiar(texto, mapa, anio, anio_fin, mes_inicio=8, desde="", hasta=""):
        visto["desde"], visto["hasta"] = desde, hasta
        return [], []

    monkeypatch.setattr(rsssf, "descargar", lambda *a, **k: "")
    monkeypatch.setattr(rsssf, "leer", espiar)
    pagina = "Anexo:Torneo Clausura 1991 (Argentina)"
    t = [x for x in torneos.TODOS if x.pagina == pagina][0]
    assert t.sin_grilla, "este test solo tiene sentido sobre una pagina sin grilla"
    build.procesar("", t)

    assert visto.get("desde"), "se leyo el archivo entero, sin recortar la seccion"
    assert visto["desde"] == rsssf.SECCION_LIGA[pagina][0]
    assert visto["hasta"] == rsssf.SECCION_LIGA[pagina][1]


def test_la_rama_de_RSSSF_tambien_pasa_los_arbitrados(monkeypatch):
    """Un partido que termino en un escritorio tiene DOS marcadores ciertos -- el de
    la cancha y el que homologo el tribunal -- y cada fuente publica uno. `completar`
    usa el marcador para VERIFICAR el emparejamiento, asi que sin `arbitrados` lee
    ese caso como desacuerdo y no lo fecha.

    El mecanismo ya existia pero solo lo usaba la rama de worldfootball; la de RSSSF
    llamaba a `completar` sin el, y los partidos de escritorio de la capa 1991-1996 se
    quedaban sin fecha aunque estuvieran escritos y justificados en
    `correcciones.MARCADORES`.

    Dos de aquellos tres ya no necesitan arbitraje --el lector aprendio a leer la nota
    del fallo y las fuentes coinciden solas--, pero el permiso sigue haciendo falta
    para el que quedo: en el `Talleres (C) 2-2 River Plate` del Clausura 1993 la que
    publica el marcador de la cancha es LA PAGINA y RSSSF el del fallo.
    """
    from fad import fechas, rsssf, torneos
    visto = {}

    def espiar(nuestros, ajenos, mapa=None, arbitrados=None, **k):
        visto["arbitrados"] = arbitrados
        return 0, []

    monkeypatch.setattr(rsssf, "descargar", lambda *a, **k: "")
    monkeypatch.setattr(fechas, "completar", espiar)
    pagina = "Anexo:Torneo Clausura 1993 (Argentina)"
    t = [x for x in torneos.TODOS if x.pagina == pagina][0]
    build._completar_fechas_rsssf([], t)

    assert visto["arbitrados"] is not None, "se llamo a `completar` sin `arbitrados`"
    assert ("Fecha 16", "Talleres (C)", "River Plate") in visto["arbitrados"], (
        "el Talleres-River del Clausura 1993 esta arbitrado y no llego a `completar`")


def test_una_fecha_fuera_de_la_temporada_no_entra(monkeypatch):
    """Nadie mas lo mira: `anios_bien_asignados` compara la MEDIANA de cada
    jornada, asi que un partido suelto tres anios afuera lo absorbe sin quejarse.
    Aca esta el Torneo a mano, que es lo que hace falta para saber el rango."""
    from fad import fechas
    monkeypatch.setattr(fechas, "descargar", lambda *a, **k: _la_otra_fuente().replace(
        "2007-08-09T22:00:00Z", "2013-08-09T22:00:00Z"))
    ps, avisos = build.procesar(_sin_fecha(), CON_WF)
    assert [p for p in ps if p.fecha] == [], "tiene que quedar sin fecha"
    assert any("caen fuera" in a.que for a in avisos)


def test_se_vacian_todas_las_fechas_fuera_de_la_temporada(monkeypatch):
    """El aviso dice que se descartan, y se vaciaban las tres primeras: con cuatro,
    la cuarta seguia con su fecha y su credito. El aviso es grave y el build no
    escribe nada, asi que no llegaba a ningun dato; lo que no cerraba era el
    mensaje con lo que se hacia."""
    from fad import fechas
    from fad.parser import Partido

    ps = [Partido(local=f"Local {i}", visita=f"Visita {i}", goles_local=1,
                  goles_visita=0, fase="zonas", jornada="Fecha 1") for i in range(4)]

    def completar(nuestros, *a, **k):
        for p in nuestros:
            p.fecha, p.fuente_fecha = "2013-08-09", "la otra fuente"
        return len(nuestros), []

    monkeypatch.setattr(fechas, "descargar", lambda *a, **k: "")
    monkeypatch.setattr(fechas, "partidos_de", lambda *a, **k: ["un partido"])
    monkeypatch.setattr(fechas, "derivar_padron", lambda *a, **k: ({}, []))
    monkeypatch.setattr(fechas, "completar", completar)
    avisos = build._completar_fechas(ps, CON_WF)
    assert [(p.fecha, p.fuente_fecha) for p in ps] == [("", "")] * 4
    assert any("4 fechas importadas caen fuera" in a.que for a in avisos)


def test_una_fecha_del_anio_siguiente_si_entra(monkeypatch):
    """La temporada 2007-08 cruza el calendario: junio de 2008 es de esa
    temporada y tiene que pasar. El rango sale de `anio_fin`, no del anio a secas
    -- si no, la mitad de cada temporada del ascenso quedaria afuera."""
    from fad import fechas
    cruzado = Torneo("Anexo:Prueba", "Prueba", 2007, cerrado=False,
                     anio_fin=2008, wf=("co1", "se1"))
    monkeypatch.setattr(fechas, "descargar", lambda *a, **k: _la_otra_fuente().replace(
        "2007-08-09T22:00:00Z", "2008-06-13T22:00:00Z"))
    ps, _ = build.procesar(_sin_fecha(), cruzado)
    assert len(ps) == 1 and ps[0].fecha == "2008-06-13"


def test_el_build_cruza_contra_la_tabla_de_posiciones():
    """La pagina dice que Boca hizo 5 goles y su unico partido tiene 2. Es una
    contradiccion de la fuente consigo misma, asi que avisa sin frenar nada."""
    pagina = tabla(("Boca Juniors", "River Plate")) + """
== Tabla de posiciones ==
{| class="wikitable"
|- style="background:#dddddd;"
! Pos
! Equipo
! Pts
! PJ
! PG
! PE
! PP
! GF
! GC
! DIF
|-
||'''1º'''||align="left"|[[Boca Juniors]]
||'''3'''||1||1||0||0||5||1||4
|}
"""
    _, avisos = build.procesar(pagina, T)
    tabla_avisos = [a for a in avisos if "tabla de posiciones" in a.que]
    assert len(tabla_avisos) == 1
    assert not tabla_avisos[0].grave, "es un error de la fuente, no frena el build"


def test_el_build_avisa_cuando_la_tabla_no_cierra_consigo_misma():
    """El unico partido es Boca 2-1 River, y la tabla le pone a River 3 en
    contra. Entonces la columna GF suma 3 y la GC suma 4: hay un gol recibido
    que nadie declara haber convertido.

    Es un aviso distinto al del cruce, y por eso se filtra por su propio texto:
    aquel compara la tabla contra nuestra grilla y tiene que razonar de quien es
    la culpa, este la agarra contradiciendose sola y no deja lugar a discusion."""
    pagina = tabla(("Boca Juniors", "River Plate")) + """
== Tabla de posiciones ==
{| class="wikitable"
|- style="background:#dddddd;"
! Pos
! Equipo
! Pts
! PJ
! PG
! PE
! PP
! GF
! GC
! DIF
|-
||'''1º'''||align="left"|[[Boca Juniors]]
||'''3'''||1||1||0||0||2||1||1
|-
||'''2º'''||align="left"|[[River Plate]]
||'''0'''||1||0||0||1||1||3||-2
|}
"""
    _, avisos = build.procesar(pagina, T)
    solos = [a for a in avisos if "no cierra sola" in a.que]
    assert len(solos) == 1
    assert "GF3" in solos[0].detalle and "GC4" in solos[0].detalle
    assert not solos[0].grave, "es un error de la fuente, no frena el build"


# --------------------------------------------------------------------------
# los partidos sin fecha, guardados aparte
# --------------------------------------------------------------------------
SIN_FECHA = Torneo("Anexo:Prueba", "Prueba", 2008, cerrado=False)


def _tres_columnas() -> str:
    """Una pagina como las de Primera C 2008-2011: sin columna de fecha."""
    return """
== Resultados ==
{|class="wikitable"
!colspan=3|Fecha 1
|-
!Equipo Local
!Resultado
!Equipo Visitante
|-align=center
|Boca Juniors
|2 - 1
|River Plate
|}
"""


def test_un_torneo_sin_fecha_conserva_sus_partidos():
    """El dataset principal descarta los partidos sin fecha, y esta bien: el
    esquema promete una. Pero que falte la fecha no es lo mismo que no tener el
    partido, y tirar mil partidos reales por un campo seria peor."""
    ps, avisos = build.procesar(_tres_columnas(), SIN_FECHA)
    assert len(ps) == 1
    assert ps[0].fecha == "" and ps[0].local == "Boca Juniors"
    assert not any(a.grave for a in avisos)
    assert any("sin fecha" in a.que for a in avisos), (
        "y se avisa: sacada la marca del catalogo, una fila sin fecha siempre es "
        "algo que mirar. Donde va esa fila es cosa de `_repartir`, no de aca")


def test_sin_la_marca_el_mismo_partido_se_descarta():
    """La marca va en el catalogo y no se adivina: en cualquier otro torneo, un
    partido sin fecha sigue siendo algo que hay que mirar."""
    normal = Torneo("Anexo:Prueba", "Prueba", 2008, cerrado=False)
    ps, avisos = build.procesar(_tres_columnas(), normal)
    assert [p for p in ps if p.fecha] == []
    assert any("sin fecha" in a.que for a in avisos), (
        "sin la marca, que un partido no tenga fecha sigue siendo algo que avisar")


def test_van_a_su_propia_carpeta(monkeypatch, tmp_path):
    """Y NO al dataset principal, que no puede tener filas sin fecha."""
    salida = tmp_path / "data"
    monkeypatch.setattr(build.torneos, "TODOS", [SIN_FECHA])
    monkeypatch.setattr(build.wiki, "wikitexto", lambda *a, **k: _tres_columnas())
    monkeypatch.setattr(build, "SALIDA", salida)

    assert build.main([]) == 0
    assert build.dataset.leer_carpeta(salida) == [], "no puede haber entrado al principal"
    guardados = build.dataset.leer_carpeta(build.sin_fecha_en(salida))
    assert len(guardados) == 1 and guardados[0]["date"] == ""
    assert guardados[0]["home_team"] == "Boca Juniors"


def test_no_se_vuelven_a_parsear(monkeypatch, tmp_path):
    """El punto de guardarlos: probar una fuente de fechas no obliga a releer
    tres temporadas enteras desde Wikipedia."""
    salida = tmp_path / "data"
    bajadas = []
    cerrado = Torneo("Anexo:Prueba", "Prueba", 2008)
    monkeypatch.setattr(build.torneos, "TODOS", [cerrado])
    monkeypatch.setattr(build.wiki, "wikitexto",
                        lambda *a, **k: (bajadas.append(1), _tres_columnas())[1])
    monkeypatch.setattr(build, "SALIDA", salida)

    assert build.main([]) == 0 and len(bajadas) == 1
    assert build.main([]) == 0 and len(bajadas) == 1, "lo volvio a bajar"
    assert len(build.dataset.leer_carpeta(build.sin_fecha_en(salida))) == 1


def test_cada_marca_de_fuente_de_fecha_apunta_a_algo():
    """Reemplaza a `test_cada_torneo_sin_fecha_esta_justificado_en_el_catalogo`,
    que se quedo sin sujeto.

    Aquel exigia que cada torneo marcado `sin_fecha` estuviera explicado en el
    catalogo, y traia escrita su propia condicion de muerte: "si no queda
    ninguno, sobra la carpeta y sobra el flag". Eso paso. Las cinco temporadas
    que no tenian fecha consiguieron fuente -- RSSSF para el Argentino A 2005-06
    y, en aquel momento, el feed de ESPN para las tres de Primera C y la Primera B
    2010-11 -- y el flag quedo sin un solo usuario, asi que se saco.

    Despues las cuatro pasaron a fecharse desde RSSSF y el feed de ESPN se saco
    del repo, con sus dos marcas. Las cinco siguen marcadas, todas con `rsssf`.

    Lo que queda por sostener es la otra mitad: una marca de fuente que apunte a
    una entrada que no existe revienta el build a mitad de camino, con el CSV
    anterior ya leido."""
    from fad import rsssf, torneos
    assert "sin_fecha" not in Torneo.__dataclass_fields__, "el flag volvio sin querer"
    assert not {"espn", "espn_llaves"} & set(Torneo.__dataclass_fields__), (
        "ESPN se saco: sus condiciones no autorizan a armar una base con su contenido")
    con_fuente = 0
    for t in torneos.TODOS:
        if t.rsssf:
            assert t.pagina in rsssf.FUENTES, f"{t.pagina}: `rsssf` sin entrada en FUENTES"
            con_fuente += 1
    assert con_fuente >= 5, "las cinco temporadas rescatadas tienen que seguir marcadas"


def test_ninguna_fila_del_dataset_principal_esta_sin_fecha(tmp_path):
    """La promesa de `data/`, dicha por lo que de verdad promete.

    Este test PEDIA otra cosa: que ningun torneo marcado `sin_fecha` tuviera
    filas en `data/`. Era un proxy, y dejo de valer cuando el reparto paso a ser
    por fila. Hoy el Argentino A 2005-06 tiene 264 partidos fechados desde RSSSF
    y 15 sin fechar: los primeros van a `data/` y los segundos a `sin-fecha/`, y
    eso esta bien aunque el torneo siga teniendo filas en las dos carpetas.

    Lo que nunca puede pasar es que una fila SIN fecha entre al dataset
    principal, y eso es lo que se chequea ahora. Es mas fuerte que el proxy: no
    depende de como este marcado el catalogo."""
    from pathlib import Path
    from fad import dataset
    principal = Path(__file__).resolve().parent.parent / "data"
    if not list(principal.glob("partidos-*.csv")):
        pytest.skip("hay que correr build.py primero")
    sin = [f for f in dataset.leer_carpeta(principal) if not (f.get("date") or "").strip()]
    assert not sin, f"{len(sin)} filas sin fecha en data/: {sin[:2]}"


def test_el_build_avisa_del_club_de_la_tabla_que_no_esta_en_el_padron():
    """Los nombres de la TABLA no pasaban por ningun control. El del padron mira
    los clubes de los partidos -- ahi un desconocido frena el build -- pero la
    tabla entra por otra puerta, y la fila terminaba a nombre de un club que no
    existe: no engancha con nada y el cruce la descarta sin decir palabra.

    No es grave, porque los datos no se tocan. Es un aviso porque apaga el arbitro
    justo donde nadie mira."""
    pagina = tabla(("Boca Juniors", "River Plate")) + """
== Tabla de posiciones ==
{{Tabla de posiciones equipo|pos=1|g=1|e=0|p=0|gf=2|gc=1|eq=[[Club Inexistente de Prueba]]}}
"""
    _, avisos = build.procesar(pagina, T)
    padron = [a for a in avisos if "no esta en el padron" in a.que]
    assert len(padron) == 1
    assert "Club Inexistente de Prueba" in padron[0].detalle
    assert not padron[0].grave, "los datos no se tocan; el aviso es porque debilita el cruce"


def test_el_partido_que_no_se_puede_escribir_llega_al_aviso():
    """No alcanza con que el parser lo sepa: lo tiene que decir el build. Sin
    este aviso el hueco aparece como un partido que falta -- la tabla si lo
    cuenta, asi que el chequeo de PJ lo denuncia -- y manda a buscar un error de
    lectura que no existe."""
    texto = tabla(("Boca Juniors", "River Plate"), ("Racing Club", "Independiente"))
    texto = texto.replace("|Racing Club" + chr(10) + "|2 - 1",
                          "|Racing Club" + chr(10) + "|PP - PP")
    ps, avisos = build.procesar(texto, T)
    assert [(x.local, x.visita) for x in ps] == [("Boca Juniors", "River Plate")]
    anulado = [a for a in avisos if "no se puede escribir" in a.que]
    assert anulado and not anulado[0].grave
    assert "Racing Club" in anulado[0].detalle and "Independiente" in anulado[0].detalle


def test_el_cruce_contra_el_cuadro_llega_al_aviso():
    """El cuadro es el segundo testigo de una copa, que no publica tabla. De nada
    sirve saber leerlo si el build no lo mira."""
    texto = tabla(("Boca Juniors", "River Plate")) + """
{{Copa de 2 clubes
| RD1-team01 = [[Club Estudiantes de La Plata|Estudiantes]]
| RD1-team02 = Boca Juniors
}}
"""
    _, avisos = build.procesar(texto, T)
    cuadro = [a for a in avisos if "cuadro" in a.que]
    assert cuadro and not cuadro[0].grave
    assert "Estudiantes" in cuadro[0].detalle


# --------------------------------------------------------------------------
# sin_repetir: importar sobre una pagina que ya trae parte de las llaves
# --------------------------------------------------------------------------
def _p(local, visita, fecha, gl=1, gv=0, fase="eliminacion"):
    from fad.parser import Partido
    return Partido(fecha=fecha, local=local, visita=visita, goles_local=gl,
                   goles_visita=gv, fase=fase)


def test_no_se_duplica_lo_que_la_pagina_ya_trae():
    """El par de clubes MAS la fecha. El par solo no alcanza: las dos patas de una
    llave son el mismo par y se distinguen por el dia."""
    pagina = [_p("Racing (C)", "Talleres (C)", "2012-06-03"),
              _p("Talleres (C)", "Racing (C)", "2012-06-10")]
    rsssf_ = [_p("Racing (C)", "Talleres (C)", "2012-06-03"),
              _p("Talleres (C)", "Racing (C)", "2012-06-10"),
              _p("Racing (C)", "Boca Juniors", "2012-06-17")]

    nuevas, repetidas, discuten, _ = build.sin_repetir(rsssf_, pagina, "una pagina")
    assert repetidas == 2 and discuten == []
    assert [x.visita for x in nuevas] == ["Boca Juniors"]


def test_la_comparacion_va_canonizada():
    """LA QUE IMPORTA. La canonizacion corre despues, asi que la pagina todavia trae
    los nombres crudos y RSSSF ya los trae canonicos. Comparando en crudo el cruce
    falla y entran duplicados -- paso: reconocia 8 de 34."""
    # Como escribe la pagina (crudo) contra como sale del mapa de RSSSF (canonico).
    pagina = [_p("Talleres de Córdoba", "Libertad (Sunchales)", "2012-06-03")]
    rsssf_ = [_p("Talleres (C)", "Libertad (S)", "2012-06-03")]

    nuevas, repetidas, _, _r = build.sin_repetir(rsssf_, pagina, "una pagina")
    assert repetidas == 1 and nuevas == [], (
        "si esto falla, la pagina y RSSSF no se reconocen y el partido entra dos veces")


def test_la_localia_al_reves_no_pasa_por_repetido():
    """Que el par y el dia coincidan hace que sea el MISMO partido, no que las dos
    fuentes digan lo mismo. En la Primera C 2011-12 la pagina pone "Deportivo
    Español 1-0 Luján" y el feed del que entonces salia su Reducido ponia "Luján
    0-1 Deportivo Español", el mismo 30 de mayo. Contarlo como repetido y callarse
    tapa un desacuerdo real."""
    pagina = [_p("Deportivo Español", "Luján", "2012-05-30", 1, 0)]
    otra = [_p("Luján", "Deportivo Español", "2012-05-30", 0, 1)]

    nuevas, repetidas, discuten, _ = build.sin_repetir(otra, pagina, "una pagina")
    assert nuevas == [] and repetidas == 1, "es el mismo partido: no se duplica"
    assert len(discuten) == 1 and "localia al reves" in discuten[0]


def test_no_se_denuncia_el_desacuerdo_que_una_correccion_ya_resuelve():
    """UNA NOTIFICACION QUE SE VUELVE FALSA SOLA ES PEOR QUE NO TENERLA.

    `sin_repetir` corre ANTES que `correcciones.aplicar` --y tiene que correr
    antes, porque decide que se importa--, asi que sin mirar las correcciones el
    build dice "la pagina dice X y la otra fuente dice Y; se conserva el de la
    pagina" sobre una fila que dos pasos mas abajo pasa a decir exactamente Y.

    Lo que NO cambia es `alreves`: ese contador alimenta al testigo que decide si
    le creemos la localia a la fuente, y un testigo que se alimenta de nuestras
    propias correcciones se valida a si mismo."""
    from fad import correcciones
    from fad.correcciones import Correccion

    pagina = [_p("Unión (MdP)", "Desamparados", "", 2, 3)]
    rsssf_ = [_p("Desamparados", "Unión (MdP)", "2011-05-18", 3, 2)]
    espejo = Correccion(pagina="una pagina", jornada="",
                        dice=("Unión (MdP)", "Desamparados", 2, 3),
                        debe=("Desamparados", "Unión (MdP)"), porque="de prueba")

    viejas = correcciones.CORRECCIONES
    try:
        correcciones.CORRECCIONES = (espejo,)
        nuevas, repetidas, discuten, alreves = build.sin_repetir(
            rsssf_, pagina, "una pagina")
    finally:
        correcciones.CORRECCIONES = viejas
    assert nuevas == [], "no es un partido que falte"
    assert discuten == [], discuten
    # El contador SI lo cuenta: es lo que mide el testigo de la localia.
    assert (repetidas, alreves) == (1, 1)


def test_la_fecha_que_falta_no_es_un_desacuerdo():
    """LO UNICO DISTINTO ES EL DIA, Y EL DIA ES LO QUE VINIMOS A BUSCAR.

    La pagina publica la llave sin fecha; RSSSF la trae con fecha, mismo par,
    mismo marcador y misma localia. Eso no es que las fuentes se contradigan: es
    exactamente el caso para el que se lee RSSSF. Avisarlo hacia que el mismo
    build dijera las dos cosas sobre los mismos cuatro partidos de la promocion
    de la B Nacional 2007-08 -- "ya estaban en la grilla y no se duplicaron" y
    "no coinciden" --, y el aviso ademas nombraba mal al contraparte."""
    pagina = [_p("Los Andes", "Nueva Chicago", "", 1, 0)]
    rsssf_ = [_p("Los Andes", "Nueva Chicago", "2008-06-21", 1, 0)]

    nuevas, repetidas, discuten, alreves = build.sin_repetir(rsssf_, pagina, "una pagina")
    assert (nuevas, repetidas, alreves) == ([], 1, 0)
    assert discuten == [], discuten


def test_sin_fecha_pero_con_la_localia_al_reves_si_se_avisa():
    """LA OTRA MITAD DE LA CONDICION. Que la pagina no tenga fecha no vuelve
    callable a un desacuerdo de LOCALIA: ahi las dos versiones se enfrentan y el
    aviso las muestra, que es lo que deja verlo. Es el caso de los dos partidos
    de la Tercera Fase del Argentino A 2010-11."""
    pagina = [_p("Unión (MdP)", "Desamparados", "", 1, 1)]
    rsssf_ = [_p("Desamparados", "Unión (MdP)", "2011-05-22", 1, 1)]

    nuevas, repetidas, discuten, alreves = build.sin_repetir(rsssf_, pagina, "una pagina")
    assert (nuevas, repetidas, alreves) == ([], 1, 1)
    assert len(discuten) == 1 and "Desamparados" in discuten[0]


def test_cuando_las_dos_fuentes_se_contradicen_gana_la_pagina_y_se_avisa():
    """Mismo par, otra fila: no es un partido que falte, es un desacuerdo. Se
    conserva el de la pagina --Wikipedia es la fuente primaria-- y se dice.

    Y cuenta para el testigo de la localia, porque es el MISMO partido: mismo par
    y mismo marcador, dado vuelta."""
    pagina = [_p("Racing (O)", "Central Córdoba (SdE)", "2012-05-19", 0, 2)]
    rsssf_ = [_p("Central Córdoba (SdE)", "Racing (O)", "2012-05-18", 2, 0)]

    nuevas, repetidas, discuten, alreves = build.sin_repetir(rsssf_, pagina, "una pagina")
    assert nuevas == [], "no es un partido que falte"
    # Y CUENTA COMO TESTIGO DE LA LOCALIA. Antes daba `repetidas == 0`, que era
    # decir que las dos fuentes no traen este partido en comun -- y lo traen: es el
    # mismo par con el mismo marcador. Lo que cambia es quien fue local, que es
    # justo lo que el testigo tiene que medir. Contarlo como "no comun" dejaba sin
    # examinar a las paginas que publican sus llaves sin dia: el Argentino A
    # 2010-11 tiene ocho asi, y el guard decia "0 partidos en comun".
    assert (repetidas, alreves) == (1, 1)
    assert len(discuten) == 1
    # las dos versiones enfrentadas, que es lo que deja ver que ademas de la fecha
    # discuten la LOCALIA
    assert "2012-05-19" in discuten[0] and "2012-05-18" in discuten[0]


def test_sin_fecha_la_casilla_es_el_partido_entero():
    """Sin fecha, la casilla de `sin_repetir` no cruza nunca y entrarian todas las
    patas, la mitad duplicando lo que la pagina ya tiene. La casilla pasa a ser
    local, visita y marcador, EN ESE ORDEN -- el orden es lo que separa las dos
    patas de una misma llave."""
    pagina = [_p("Aldosivi", "Luján de Cuyo", "2004-11-20", 0, 1),
              _p("Luján de Cuyo", "Aldosivi", "2004-11-28", 3, 1)]
    rsssf_ = [_p("Aldosivi", "Luján de Cuyo", "", 0, 1),
              _p("Luján de Cuyo", "Aldosivi", "", 3, 1),
              _p("Ben Hur", "Talleres (C)", "", 2, 0)]

    nuevas, repetidas, discuten = build.sin_repetir_sin_fecha(rsssf_, pagina, "una pagina")
    assert repetidas == 2 and discuten == []
    assert [x.local for x in nuevas] == ["Ben Hur"]


def test_sin_fecha_el_partido_al_reves_es_un_desacuerdo_y_no_uno_nuevo():
    """Mismo marcador, local y visitante cambiados: no falta el partido, discrepan
    sobre quien jugo en casa. Pasa de verdad en el Argentino A 2004-05, con la
    llave Villa Mitre - General Paz Juniors."""
    pagina = [_p("General Paz Juniors", "Villa Mitre", "2004-11-21", 4, 1)]
    rsssf_ = [_p("Villa Mitre", "General Paz Juniors", "", 1, 4)]

    nuevas, repetidas, discuten = build.sin_repetir_sin_fecha(rsssf_, pagina, "una pagina")
    assert nuevas == [] and repetidas == 0, "no es un partido que falte"
    assert len(discuten) == 1 and "al reves" in discuten[0]


def test_el_cruce_aplica_el_homonimo_de_la_pagina():
    """La correccion de homonimos corre MAS ABAJO en el pipeline, asi que en el
    momento del cruce la pagina todavia dice "Juventud Unida" mientras que las
    filas de la otra fuente ya vienen con el nombre entero. Sin aplicarlo aca, el
    cruce no las reconoce y el mismo partido entra dos veces -- paso, y son dos
    filas duplicadas en el Argentino A 2004-05.

    Se usa el homonimo de verdad, no uno inventado: si alguien lo saca de
    `correcciones`, este test lo dice.
    """
    pagina = [_p("General Paz Juniors", "Juventud Unida", "2005-04-10", 0, 1)]
    otra = [_p("General Paz Juniors", "Juventud Unida Universitario", "2005-04-10", 0, 1)]

    nuevas, repetidas, _, _r = build.sin_repetir(otra, pagina, "Torneo Argentino A 2004-05")
    assert repetidas == 1 and nuevas == [], (
        "sin el homonimo la pagina y la otra fuente no se reconocen y el partido se duplica")


# --------------------------------------------------------------------------
# El solapamiento como testigo de la localia de la fuente
# --------------------------------------------------------------------------
def test_si_la_fuente_le_lleva_la_contra_a_la_pagina_no_se_le_cree():
    """Donde las dos traen el MISMO partido, la pagina dice quien fue local con
    una columna rotulada. Si la fuente le lleva la contra en la mayoria de esos,
    su orden no es la localia -- y tampoco lo seria en los partidos que la pagina
    NO trae, que son justo los que se querian importar.

    Medido: el Argentino A 2011-12 coincide en 6 de 28. Veintiuno por ciento, peor
    que el 55.6% de la convencion que este repo ya rechazo por inventar.
    """
    que_decir, frenar = build.le_creemos_la_localia(repetidas=28, alreves=22)
    assert frenar and "no coinciden en quien jugo de local" in que_decir


def test_si_la_fuente_coincide_no_se_dice_nada():
    """El Argentino A 2004-05: 40 de 45. La fuente paso el examen y no hay nada que
    contar."""
    assert build.le_creemos_la_localia(repetidas=45, alreves=5) == ("", False)


def test_sin_testigo_no_se_bloquea_pero_se_dice():
    """SON TRES ESTADOS Y NO DOS. Que no haya solapamiento no es que la fuente
    aprobo: es que no se la pudo examinar, y en un reporte que solo habla cuando
    algo falla los dos se ven igual. El Argentino A 2012-13 importa seis partidos
    con CERO en comun."""
    que_decir, frenar = build.le_creemos_la_localia(repetidas=0, alreves=0)
    assert not frenar, "sin testigo no se bloquea"
    assert "no tiene testigo" in que_decir, "pero se dice"


def test_una_mayoria_sobre_dos_partidos_no_es_una_mayoria():
    """El limite de abajo. Con dos en comun y los dos al reves, la cuenta da 100%
    pero no significa nada: por eso pide un solapamiento minimo antes de juzgar."""
    _, frenar = build.le_creemos_la_localia(repetidas=2, alreves=2)
    assert not frenar


def test_cuando_el_patron_es_el_torcido_el_testigo_se_puede_nombrar():
    """EL TESTIGO SUPONE QUE LA PAGINA ES EL PATRON, Y A VECES NO LO ES.

    Mide a la fuente contra la pagina, asi que cuando la pagina esta mal en esa
    region rechaza a la fuente POR TENER RAZON -- y ahi se pierden los partidos
    que solo la fuente trae. Le paso al Argentino A 2011-12: daba 6 de 31 porque
    la pagina rotula `Local - Vuelta` a la columna de la ida, y con el bloqueo
    puesto quedaban afuera seis partidos que Wikipedia publica solo como dibujo.

    La salida no afloja la regla, la nombra: sin evidencia sigue bloqueando."""
    sin_evidencia = build.le_creemos_la_localia(repetidas=31, alreves=25)
    assert sin_evidencia[1] is True, "sin evidencia tiene que seguir frenando"

    que_decir, frenar = build.le_creemos_la_localia(
        repetidas=31, alreves=25, resuelta="la evidencia, medida aparte")
    assert frenar is False
    assert "no se le hace caso" in que_decir
    # Y lo sigue DICIENDO: levantar el bloqueo no es callarse.
    assert "25 de 31" in que_decir


def test_la_localia_resuelta_nombra_paginas_que_existen():
    """UN TITULO MAL TIPEADO NO FALLA: NO HACE NADA.

    `LOCALIA_RESUELTA` se consulta con `.get(pagina, "")`, asi que una clave que
    no corresponde a ninguna pagina del catalogo deja el bloqueo puesto en
    silencio -- que es justo lo contrario de lo que quien la escribio quiso."""
    from fad import correcciones, torneos

    paginas = {t.pagina for t in torneos.TODOS}
    for clave in correcciones.LOCALIA_RESUELTA:
        assert clave in paginas, f"{clave!r} no es ninguna pagina del catalogo"


# --------------------------------------------------------------------------
# La foja de la fuente como testigo de nuestra propia lectura
# --------------------------------------------------------------------------
_MAPA_2 = {"Zone 1": {"A": "A", "B": "B"}, "Zone 2": {"C": "C", "D": "D"}}


def _zp(local, visita, gl, gv, zona):
    from fad.parser import Partido
    return Partido(fecha="2010-01-01", local=local, visita=visita, goles_local=gl,
                   goles_visita=gv, fase="zonas", zona=zona)


def _tabla(zona, filas):
    """Un documento con una tabla rotulada. `filas` son (PJ, G, E, P, GF, GC),
    que es el orden en que la fuente las imprime."""
    dentro = "".join(
        f" {i}.Club{i} (Ciudad)   {pj:>3} {g:>3} {e:>3} {pp:>3}  {gf}-{gc}  0\n"
        for i, (pj, g, e, pp, gf, gc) in enumerate(filas, 1))
    return f"{zona}\nFinal Table:\n\n{dentro}"


def test_la_foja_de_la_fuente_respalda_nuestra_lectura():
    """Dos clubes, un partido, y la tabla de la fuente diciendo lo mismo que
    nuestra suma. NO SE EMPAREJA NI UN NOMBRE: la fuente escribe `Club1` y
    `Club2` y nosotros `A` y `B`. Se comparan los CONJUNTOS de fojas, y para
    saber si dos conjuntos son el mismo no hace falta saber cual fila es cual."""
    ps = [_zp("A", "B", 2, 0, "Zone 1")]
    respaldados, avisos = build.la_fuente_se_respalda(
        ps, _tabla("Zone 1", [(1, 1, 0, 0, 2, 0), (1, 0, 0, 1, 0, 2)]), _MAPA_2)
    assert respaldados == {"A", "B"} and avisos == []


def test_si_la_foja_no_coincide_se_avisa_sin_acusar_a_nadie():
    """EL AVISO NO DICE DE QUIEN ES LA CULPA PORQUE NO LA SABE. Lo tentador es
    leerlo como "la leimos mal", y es una de las dos explicaciones: la otra es
    que la fuente se contradiga sola, que es textualmente lo que hace el
    Argentino A 2007-08 con su partido dado por perdido."""
    ps = [_zp("A", "B", 2, 0, "Zone 1")]
    respaldados, avisos = build.la_fuente_se_respalda(
        ps, _tabla("Zone 1", [(1, 1, 0, 0, 3, 0), (1, 0, 0, 1, 0, 3)]), _MAPA_2)
    assert respaldados == set()
    assert len(avisos) == 1 and "o los leimos mal o la fuente se contradice" in avisos[0]
    assert "error de lectura nuestro" not in avisos[0]


def test_el_club_del_interzonal_vuelve_a_su_zona():
    """Las rondas interzonales se imprimen bajo UNA de las dos zonas, asi que un
    club aparece con partidos en la zona ajena. La zona de cada club sale de
    donde juega la MAYORIA de los suyos; sin eso, la Zone 1 del Argentino A
    2008-09 se cruzaba con dieciseis clubes contra ocho filas y no cruzaba
    nunca."""
    ps = [_zp("A", "B", 1, 0, "Zone 1"), _zp("B", "A", 1, 0, "Zone 1"),
          _zp("C", "D", 1, 0, "Zone 2"), _zp("D", "C", 1, 0, "Zone 2"),
          # el interzonal, impreso bajo la Zone 1: mete a C y D ahi
          _zp("A", "C", 1, 0, "Zone 1"), _zp("B", "D", 1, 0, "Zone 1")]
    # La tabla de la zona cuenta los TRES partidos de cada uno, interzonal
    # incluido, que es lo que hace la fuente de verdad.
    respaldados, avisos = build.la_fuente_se_respalda(
        ps, _tabla("Zone 2", [(3, 1, 0, 2, 1, 2), (3, 1, 0, 2, 1, 2)]), _MAPA_2)
    assert respaldados == {"C", "D"}, "C y D son de la Zone 2 aunque jueguen en la 1"


def _fp(local, visita, gl, gv, zona, llave):
    """Un partido de zona con su FASE, para las paginas que corren dos torneos."""
    from fad.parser import Partido
    return Partido(fecha="2010-01-01", local=local, visita=visita, goles_local=gl,
                   goles_visita=gv, fase="zonas", zona=zona, llave=llave)


def test_con_fases_declaradas_cada_etapa_suma_por_su_cuenta(monkeypatch):
    """ADENTRO DE UN APERTURA HAY DOS ETAPAS, y la tabla de una zona NO cuenta los
    partidos de la otra.

    La fuente corre primero las zonas y despues los pentagonales. Sin separarlos, un
    club de la `Zone 1` llega a la comparacion con sus partidos de zona MAS los del
    grupo, y la tabla de la zona --que solo cuenta los primeros-- no cierra nunca.
    Es lo que dejaba al Argentino A 2009-10 sin ningun respaldo."""
    from fad import rsssf

    ps = [_fp("A", "B", 2, 0, "Zone 1", "Torneo Apertura"),
          # el pentagonal de la MISMA fase: no tiene que contar en la tabla de zona
          _fp("A", "C", 5, 0, "Group A", "Torneo Apertura")]
    tabla = ("Apertura\n\nZone 1\nFinal Table:\n\n"
             " 1.Club1 (Ciudad)     1   1  0  0  2-0  3\n"
             " 2.Club2 (Otra)       1   0  0  1  0-2  0\n")
    monkeypatch.setitem(rsssf.FASES, "una pagina", {"Apertura": "Torneo Apertura"})
    respaldados, avisos = build.la_fuente_se_respalda(ps, tabla, _MAPA_2, "una pagina")
    assert (respaldados, avisos) == ({"A", "B"}, []), avisos


def test_sin_fases_declaradas_todo_suma_junto():
    """Y LA SEPARACION ES OPT-IN, que no es un detalle. En el Argentino A 2007-08 no
    hay fases y sus `Group A` y `Group B` SON las zonas, con el interzonal impreso
    bajo una de ellas: separar por prefijo ahi se lleva puestos ocho clubes de los
    diecisiete que respalda. Sin fases declaradas, todo suma junto, que es como
    venia."""
    ps = [_zp("A", "B", 2, 0, "Zone 1"),
          _zp("A", "C", 5, 0, "Group A")]     # el interzonal, impreso bajo el grupo
    # La tabla de la zona cuenta los DOS partidos de A, que es lo que hace la fuente.
    tabla = _tabla("Zone 1", [(2, 2, 0, 0, 7, 0), (1, 0, 0, 1, 0, 2)])
    respaldados, _ = build.la_fuente_se_respalda(ps, tabla, _MAPA_2, "otra pagina")
    assert respaldados == {"A", "B"}


def test_una_zona_con_un_partido_dividido_no_se_cruza(monkeypatch):
    """SE ABSTIENE, Y EN SILENCIO. Un partido dividido se JUGO -- la tabla de la
    fuente lo cuenta -- y su fila no se puede escribir, porque cada club termino
    con un resultado distinto. Asi que a esos clubes les falta un partido contra
    la tabla y siempre les va a faltar: es la misma razon por la que se abstiene
    ante un club ya revisado a mano, y denunciarlo de nuevo convierte un archivo
    de conclusiones en ruido.

    En el Argentino A 2006-07 son cuatro clubes, dos pares, y desvian exactamente
    `+1 PJ, +1 en contra, +1 perdido`. Sin esta rama, habilitar sus tablas
    acumuladas producia dos alarmas perfectamente falsas."""
    from fad import correcciones

    ps = [_zp("A", "B", 2, 0, "Zone 1")]
    # La fuente le cuenta a los dos un partido mas: el dividido.
    tabla = _tabla("Zone 1", [(2, 1, 0, 1, 2, 1), (2, 0, 0, 2, 0, 3)])
    monkeypatch.setattr(correcciones, "pares_divididos",
                        lambda pagina: [("A", "B", "")])
    respaldados, avisos = build.la_fuente_se_respalda(ps, tabla, _MAPA_2, "una pagina")
    assert (respaldados, avisos) == (set(), []), avisos

    # Y sin el dividido declarado, la MISMA tabla si avisa: la abstencion es por
    # la declaracion, no por el desvio.
    monkeypatch.setattr(correcciones, "pares_divididos", lambda pagina: [])
    _, avisos = build.la_fuente_se_respalda(ps, tabla, _MAPA_2, "una pagina")
    assert len(avisos) == 1


def test_una_tabla_que_no_cubre_la_zona_no_se_cruza():
    """Distinta cantidad de filas que de clubes quiere decir que las dos partes
    no estan hablando del mismo conjunto de partidos --las tablas de playoff son
    asi-- y comparar dos conjuntos distintos no responde nada."""
    ps = [_zp("A", "B", 2, 0, "Zone 1")]
    respaldados, avisos = build.la_fuente_se_respalda(
        ps, _tabla("Zone 1", [(1, 1, 0, 0, 2, 0)]), _MAPA_2)
    assert (respaldados, avisos) == (set(), [])


def test_la_zona_se_traduce_cuando_los_dos_lados_la_nombran_distinto(monkeypatch):
    """EL MAPA DE ZONAS. La fuente dice `Zone 1` y nuestra pagina dice
    `Primera fase - Zona 1`: es la misma zona con dos nombres, y el cruce los
    comparaba literalmente. Sin traduccion no cruza ni un club y la tabla se descarta
    por cardinalidad -- en silencio, y pareciendose a "la fuente no publica tablas".

    Es el hermano de `FASES`, que ya existia para el otro rotulo."""
    from fad import rsssf

    ps = [_zp("A", "B", 2, 0, "Nuestra Zona")]
    una = _tabla("Zone 1", [(1, 1, 0, 0, 2, 0), (1, 0, 0, 1, 0, 2)])
    mapa = {"Zone 1": {"A": "A", "B": "B"}}
    assert build.la_fuente_se_respalda(ps, una, mapa, "P")[0] == set(), "sin traducir"
    monkeypatch.setattr(rsssf, "ZONAS", {"P": {("", "Zone 1"): "Nuestra Zona"}})
    assert build.la_fuente_se_respalda(ps, una, mapa, "P")[0] == {"A", "B"}


def test_sin_mapa_la_zona_se_compara_CONTRA_SI_MISMA(monkeypatch):
    """Y el default tiene que ser la IDENTIDAD, no un error. En las paginas sin
    grilla nuestras filas salen de RSSSF y ya traen su rotulo puesto: ahi los dos
    lados dicen `Zone 1` y no hay nada que traducir. Un mapa obligatorio se llevaria
    puestas las cuatro temporadas que ya cruzan."""
    from fad import rsssf

    monkeypatch.setattr(rsssf, "ZONAS", {})
    ps = [_zp("A", "B", 2, 0, "Zone 1")]
    una = _tabla("Zone 1", [(1, 1, 0, 0, 2, 0), (1, 0, 0, 1, 0, 2)])
    assert build.la_fuente_se_respalda(ps, una, _MAPA_2, "P")[0] == {"A", "B"}


def test_la_traduccion_va_POR_FASE_porque_la_zona_se_repite(monkeypatch):
    """Un archivo repite los nombres de zona entre fases: el Argentino A 2010-11
    rotula `Zone 1` en la fase regular y otra vez en la final, y son zonas distintas
    con clubes distintos. Traducir por el nombre solo mandaria las dos a la misma."""
    from fad import rsssf

    monkeypatch.setattr(rsssf, "ZONAS",
                        {"P": {("Uno", "Zone 1"): "La de la fase Uno",
                               ("Dos", "Zone 1"): "La de la fase Dos"}})
    monkeypatch.setattr(rsssf, "FASES", {"P": {"Fase Uno": "Uno", "Fase Dos": "Dos"}})
    ps = [_zp("A", "B", 2, 0, "La de la fase Uno"),
          _zp("C", "D", 1, 0, "La de la fase Dos")]
    for p_, llave in zip(ps, ("Uno", "Dos")):
        p_.llave = llave
    mapa = {"Zone 1": {"A": "A", "B": "B", "C": "C", "D": "D"}}
    crudo = ("Fase Uno\n" + _tabla("Zone 1", [(1, 1, 0, 0, 2, 0), (1, 0, 0, 1, 0, 2)])
             + "\nFase Dos\n" + _tabla("Zone 1", [(1, 1, 0, 0, 1, 0), (1, 0, 0, 1, 0, 1)]))
    assert build.la_fuente_se_respalda(ps, crudo, mapa, "P")[0] == {"A", "B", "C", "D"}


def test_una_zona_con_dos_tablas_no_se_cruza():
    """Cardinalidad: si la zona trae dos tablas DISTINTAS no se sabe cual cubre que.
    Es el Argentino A 2009-10, que corre dos fases rotulando las dos `Zone 1`."""
    ps = [_zp("A", "B", 2, 0, "Zone 1")]
    una = _tabla("Zone 1", [(1, 1, 0, 0, 2, 0), (1, 0, 0, 1, 0, 2)])
    otra = _tabla("Zone 1", [(3, 3, 0, 0, 9, 0), (3, 0, 0, 3, 0, 9)])
    respaldados, avisos = build.la_fuente_se_respalda(ps, una + "\n" + otra, _MAPA_2)
    assert (respaldados, avisos) == (set(), [])


def test_la_foja_se_queda_con_LA_SECCION_de_su_pagina():
    """El recorte no alcanza con que `leer_tabla` sepa hacerlo: hay que pedirselo.

    Desde 2010-11 RSSSF mete siete divisiones en un archivo por ano, y la seccion que
    le toca a cada pagina la declara `SECCION_LIGA` -- la misma que usan los partidos.
    Sin pasarla, la foja ve las tablas de las siete: dos bajo la misma clave, el cruce
    no puede elegir, y se abstiene en la temporada entera.

    Se usa una pagina REAL y su recorte real, porque el que se puede escribir mal es
    justamente ese: un test con anclas inventadas prueba el mecanismo y no el dato.
    """
    from fad import rsssf

    pagina = "Campeonato de Primera B 2010-11 (Argentina)"
    desde, hasta = rsssf.SECCION_LIGA[pagina]
    ps = [_zp("A", "B", 2, 0, "Zone 1")]
    mia = _tabla("Zone 1", [(1, 1, 0, 0, 2, 0), (1, 0, 0, 1, 0, 2)])
    ajena = _tabla("Zone 1", [(9, 9, 0, 0, 99, 0), (9, 0, 0, 9, 0, 99)])
    crudo = f"{ajena}\n{desde}\n{mia}\n{hasta}\n{ajena}"
    respaldados, avisos = build.la_fuente_se_respalda(ps, crudo, _MAPA_2, pagina)
    assert (respaldados, avisos) == ({"A", "B"}, []), (
        "sin el recorte se ven dos tablas distintas bajo la misma clave y se abstiene")


def test_el_aviso_se_entera_de_que_la_pagina_TIENE_grilla(monkeypatch):
    """Y la otra mitad del cableado: de donde salen los partidos decide cual de las
    dos conclusiones se escribe, y eso lo sabe `build` y no `contrastar`.

    Con grilla los partidos salen de la propia pagina, asi que el aviso NO puede
    decir que vienen de una fuente externa. `contrastar` ya sabe redactar las dos; lo
    que se prueba aca es que reciba cual.
    """
    visto = {}
    real = posiciones.contrastar

    def espiar(*a, **k):
        visto.update(k)
        return real(*a, **k)

    monkeypatch.setattr(posiciones, "contrastar", espiar)
    build.procesar(tabla(("Boca Juniors", "River Plate")), T)
    assert visto["de_afuera"] is False


def test_y_de_que_NO_la_tiene_cuando_los_partidos_son_de_RSSSF(monkeypatch):
    """El mismo cableado del otro lado. Es el camino por el que un torneo entero no
    viene de Wikipedia, y el aviso que le corresponde es el otro: ahi el
    respaldo deja un desacuerdo ENTRE FUENTES, que pide una tercera para arbitrar.

    La fuente se monkeypatchea vacia a proposito -- lo que se mira es el cableado,
    no los partidos --, que es lo mismo que hacen los tests del completador de
    fechas con `descargar`.
    """
    from fad import rsssf

    visto = {}
    real = posiciones.contrastar

    def espiar(*a, **k):
        visto.update(k)
        return real(*a, **k)

    t = Torneo("Anexo:Prueba", "Prueba", 2026, cerrado=False, sin_grilla=True)
    monkeypatch.setattr(rsssf, "FUENTES", {t.pagina: ("archivo", {})})
    monkeypatch.setattr(rsssf, "descargar", lambda *a, **k: "")
    monkeypatch.setattr(posiciones, "contrastar", espiar)
    build.procesar("", t)
    assert visto["de_afuera"] is True


def test_la_misma_tabla_dos_veces_SI_alcanza():
    """Y esta es la otra mitad, que hasta hoy caia del lado equivocado. RSSSF
    publica su tabla final arriba del archivo y de nuevo abajo: son dos apariciones
    de una tabla, no dos tablas, y ahi no hay ninguna ambiguedad que cuidar.

    Abstenerse igual costaba caro y en silencio -- la B Nacional 2007-08 y las
    Primera C 2008-09 y 2009-10, sesenta clubes sin respaldo por una copia --. La
    guarda queda entera: lo de arriba sigue sin cruzar."""
    ps = [_zp("A", "B", 2, 0, "Zone 1")]
    una = _tabla("Zone 1", [(1, 1, 0, 0, 2, 0), (1, 0, 0, 1, 0, 2)])
    respaldados, avisos = build.la_fuente_se_respalda(ps, una + "\n" + una, _MAPA_2)
    assert (respaldados, avisos) == ({"A", "B"}, [])


def test_un_club_ya_revisado_a_mano_calla_el_aviso_pero_no_el_cruce():
    """SOLO CUANDO EL CRUCE FALLA. Ahi el desvio ya tiene su explicacion escrita y
    repetirla convierte un archivo de conclusiones en ruido.

    Pero cuando el cruce PASA no hay nada que repetir, y abstenerse igual apagaba
    el chequeo justo en la pagina que lo motivo: el Argentino A 2008-09 tiene sus
    veinticinco clubes revisados -- la tabla de la pagina en espanol dice mas
    goles que las otras dos -- y sus tres zonas cierran perfecto contra la foja de
    la fuente. Callarlas ahi era perder el guard sin ganar nada.
    """
    pagina = "Torneo Argentino A 2007-08"
    ps = [_zp("Luján de Cuyo", "Juventud Unida Universitario", 2, 0, "Zone 1")]
    mapa = {"Zone 1": {"L": "Luján de Cuyo", "J": "Juventud Unida Universitario"}}

    falla = _tabla("Zone 1", [(1, 1, 0, 0, 9, 0), (1, 0, 0, 1, 0, 9)])
    assert build.la_fuente_se_respalda(ps, falla, mapa)[1], "sin la pagina, avisa"
    assert build.la_fuente_se_respalda(ps, falla, mapa, pagina) == (set(), []), \
        "con la pagina, calla"

    pasa = _tabla("Zone 1", [(1, 1, 0, 0, 2, 0), (1, 0, 0, 1, 0, 2)])
    respaldados, avisos = build.la_fuente_se_respalda(ps, pasa, mapa, pagina)
    assert avisos == [] and respaldados == {"Luján de Cuyo",
                                            "Juventud Unida Universitario"}, \
        "si cierra, el respaldo vale aunque el club este revisado"


def test_la_deduplicacion_ve_el_renombre_que_corre_despues():
    """`correcciones.aplicar` corre mas abajo en el pipeline, asi que cuando se
    deduplica la pagina todavia dice "Alumni" a secas -- que en el padron es OTRO
    club -- mientras que la fila de RSSSF ya viene con "Alumni (VM)". Sin mirar el
    renombre, el cruce no las reconoce como el mismo partido.

    Y no las reconocia: los dos partidos de la promocion del Argentino A 2005-06
    entraron duplicados apenas el lector de RSSSF aprendio a resolver esos
    nombres. Los agarro `sin_duplicados` como GRAVE, que es el sistema
    funcionando -- pero frenar el build es peor que no duplicar.

    Va sobre `sin_repetir` y no sobre `correcciones.renombrado`: preguntandole a
    la funcion directamente, este error no se ve. Lo destapo un mutante que
    sobrevivio.
    """
    from fad.parser import Partido
    pagina = [Partido(fecha="2006-06-18", local="Alumni",
                      visita="General Paz Juniors", goles_local=5, goles_visita=0,
                      fase="eliminacion", jornada="Promoción")]
    rsssf_ = [_p("Alumni (VM)", "General Paz Juniors", "2006-06-18", 5, 0)]

    nuevas, repetidas, _, _r = build.sin_repetir(
        rsssf_, pagina, "Torneo Argentino A 2005-06")
    assert (repetidas, nuevas) == (1, []), "es el mismo partido"

    # y en otra pagina, donde ese renombre no existe, sigue siendo otro club
    nuevas, repetidas, _, _r = build.sin_repetir(rsssf_, pagina, "Otra Pagina")
    assert repetidas == 0 and len(nuevas) == 1


def test_el_desacuerdo_que_un_marcador_ya_resuelve_no_se_denuncia():
    """El mismo modo de falla que el renombre, con la otra familia.

    `sin_repetir` corre antes que `correcciones.aplicar` -- y tiene que correr
    antes, porque decide que se importa --, asi que sin mirar los `Marcador` el
    build seguia diciendo "la pagina dice 2012-05-06 Libertad (S) 1-2 Central
    Norte (S) y la otra fuente Central Norte (S) 2-0 Libertad (S); se conserva el
    de la pagina" sobre una fila que dos pasos mas abajo pasa a decir exactamente
    lo de la otra fuente. Eran cuatro de las siete que denunciaba esa pagina.

    La fila entra CRUDA, como la lee la pagina, y tiene que atravesar las dos
    correcciones: primero el espejo de la localia --que la deja `Central Norte
    (S) 2-1 Libertad (S)`-- y recien despues el marcador arbitrado, que la deja
    en 2-0. Preguntar el arbitraje antes del espejo no engancha nada.
    """
    from fad.parser import Partido
    pagina = [Partido(fecha="2012-05-06", local="Libertad (S)",
                      visita="Central Norte (S)", goles_local=1, goles_visita=2,
                      fase="eliminacion", jornada="Reválida - Tercera ronda")]
    rsssf_ = [_p("Central Norte (S)", "Libertad (S)", "2012-05-06", 2, 0)]

    nuevas, repetidas, discuten, alreves = build.sin_repetir(
        rsssf_, pagina, "Torneo Argentino A 2011-12")
    assert (repetidas, nuevas) == (1, []), "es el mismo partido"
    assert discuten == [], "el desacuerdo esta resuelto y declarado: no se denuncia"

    # PERO SE SIGUE CONTANDO COMO AL REVES, y es a proposito: ese contador
    # alimenta al testigo que decide si le creemos la localia a la fuente, y un
    # testigo que se alimenta de nuestras propias correcciones se valida solo.
    assert alreves == 1, "apaga el mensaje, no el testigo"


def test_un_desacuerdo_que_nadie_declaro_se_sigue_denunciando():
    """La contracara del anterior. Si el marcador de la fuente no es el que
    ningun `Marcador` declara, el desacuerdo es real y hay que decirlo -- si no,
    mirar los `Marcador` seria una forma de callar todo."""
    from fad.parser import Partido
    pagina = [Partido(fecha="2012-05-06", local="Libertad (S)",
                      visita="Central Norte (S)", goles_local=1, goles_visita=2,
                      fase="eliminacion", jornada="Reválida - Tercera ronda")]
    rsssf_ = [_p("Central Norte (S)", "Libertad (S)", "2012-05-06", 5, 0)]

    _n, _r, discuten, _a = build.sin_repetir(
        rsssf_, pagina, "Torneo Argentino A 2011-12")
    assert len(discuten) == 1 and "5-0" in discuten[0]


def test_sin_fecha_la_fila_se_identifica_por_el_marcador_CORREGIDO():
    """Cuando la fila no trae dia, lo que la identifica es el marcador -- y tiene
    que ser el que va a tener, no el que la pagina escribio.

    Las dos cosas se cruzaron de verdad y por eso hace falta el test. Los cuatro
    partidos de la Revalida del Argentino A 2011-12 tienen su marcador arbitrado
    --la pagina dice 1-0 y el dataset escribe 1-1-- y ademas se quedaron sin fecha,
    porque su tabla la publica como rango y un rango no se reparte. Sin fecha esta
    es la rama que empareja, y comparando el marcador CRUDO no encontraba la fila:
    `{0,1}` no es `{1,1}`. El build volvia a denunciar, uno por uno, los cuatro
    desacuerdos que dos pasos mas abajo estan resueltos y declarados.

    Si no identifica, `resuelto` ni siquiera llega a correr: por eso el arreglo va
    un renglon antes y no adentro de `resuelto`.
    """
    from fad.parser import Partido
    # la fila CRUDA de la pagina: sin fecha, con la localia al reves y el marcador
    # que un `Marcador` declarado corrige a 1-1
    pagina = [Partido(fecha="", local="Juventud Unida Universitario",
                      visita="Juventud Antoniana", goles_local=0, goles_visita=1,
                      fase="eliminacion", jornada="Reválida - Segunda ronda")]
    rsssf_ = [_p("Juventud Antoniana", "Juventud Unida Universitario",
                 "2012-04-22", 1, 1)]

    nuevas, repetidas, discuten, _a = build.sin_repetir(
        rsssf_, pagina, "Torneo Argentino A 2011-12")
    assert (repetidas, nuevas) == (1, []), "es el mismo partido"
    assert discuten == [], "esta arbitrado y declarado: no se vuelve a denunciar"


def test_una_fila_sin_fecha_y_espejada_es_un_desacuerdo_de_verdad():
    """Acá vivía una guarda muerta, y su único efecto posible era el equivocado.

    Preguntaba `if not iguales[0].fecha and mismo_local: continue`, o sea: si la
    fila de la página no trae día y el local coincide, entre las dos versiones lo
    único distinto es el día. Eso es cierto casi siempre -- y por eso `resuelto`,
    que llego despues, ya lo contesta --, pero no siempre: `iguales` empareja
    comparando el marcador como CONJUNTO, asi que ahi adentro cae tambien la fila
    ESPEJADA. La pagina diciendo `2-1` y la fuente `1-2` con el mismo local es el
    mismo partido con el ganador cambiado, y la guarda lo callaba por no tener
    fecha.

    Lo destapo un mutante que sobrevivia: anular la guarda entera no cambiaba un
    byte del reporte del build -- 182 avisos identicos en 149 paginas --, que es
    la definicion de codigo muerto.
    """
    from fad.parser import Partido
    pagina = [Partido(fecha="", local="Alumni (VM)", visita="General Paz Juniors",
                      goles_local=2, goles_visita=1,
                      fase="eliminacion", jornada="Promoción")]
    rsssf_ = [_p("Alumni (VM)", "General Paz Juniors", "2006-06-18", 1, 2)]

    _n, repetidas, discuten, alreves = build.sin_repetir(
        rsssf_, pagina, "Torneo Argentino A 2005-06")
    assert (repetidas, alreves) == (1, 0), "mismo partido y mismo local"
    assert len(discuten) == 1, "el resultado esta al reves: hay que decirlo"
    assert "2-1" in discuten[0] and "1-2" in discuten[0]


def test_una_fila_sin_fecha_que_coincide_en_todo_no_se_denuncia():
    """La contracara, y es el caso comun: si lo unico que la pagina no tiene es el
    dia, no hay desacuerdo que contar. Sin esto el build decia las dos cosas sobre
    los mismos cuatro partidos de la promocion de la B Nacional 2007-08."""
    from fad.parser import Partido
    pagina = [Partido(fecha="", local="Alumni (VM)", visita="General Paz Juniors",
                      goles_local=2, goles_visita=1,
                      fase="eliminacion", jornada="Promoción")]
    rsssf_ = [_p("Alumni (VM)", "General Paz Juniors", "2006-06-18", 2, 1)]

    _n, repetidas, discuten, _a = build.sin_repetir(
        rsssf_, pagina, "Torneo Argentino A 2005-06")
    assert (repetidas, discuten) == (1, []), "lo unico distinto es el dia"


def test_el_completador_acota_la_seccion_del_archivo_del_anio(monkeypatch):
    """Desde 2010-11 RSSSF mete todas las divisiones en la pagina del anio, una
    atras de otra y todas con sus `Round N`. El corte no alcanza con tenerlo en
    `rsssf.leer`: hay que PASARSELO, y este es el unico lugar que lo hace.

    Sin el corte no hay error ni aviso: hay partidos de otro torneo en el indice
    de fechas, y el completador le pone a la fecha 1 de la Primera C el dia en que
    jugo la Primera B. Lo destapo un mutante que sobrevivio -- el corte estaba
    probado en el lector y no en su llamador.
    """
    from fad import rsssf
    from fad.parser import Partido

    documento = ("Primera B Metropolitano\n"
                 "Round 1\n"
                 "[Jul 24]\n"
                 "Racing                       2-1 Talleres\n"
                 "Topscorers\n"
                 "Fulano  9\n"
                 "Primera C Metropolitano\n"
                 "Round 1\n"
                 "[Aug 2]\n"
                 "Racing                       3-0 Talleres\n"
                 "Topscorers\n")
    mapa = {"": {"Racing": "Racing (C)", "Talleres": "Talleres (C)"}}
    t = Torneo("Anexo:Prueba", "Prueba", 2010, anio_fin=2011, mes_inicio=7)

    monkeypatch.setattr(rsssf, "descargar", lambda *a, **k: documento)
    monkeypatch.setitem(rsssf.FUENTES, "Anexo:Prueba", ("cualquiera", mapa))
    monkeypatch.setitem(rsssf.SECCION_LIGA, "Anexo:Prueba",
                        ("Primera C Metropolitano", "Topscorers"))

    ps = [Partido(local="Racing (C)", visita="Talleres (C)", goles_local=3,
                  goles_visita=0, fase="zonas", jornada="Fecha 1")]
    build._completar_fechas_rsssf(ps, t)
    assert ps[0].fecha == "2010-08-02", (
        "sin el corte toma el 24/07, que es cuando jugo la OTRA division")


def test_las_llaves_le_ponen_fecha_a_lo_que_la_pagina_trae_sin_dia():
    """LO QUE LA PAGINA YA TIENE PUEDE TENERLO SIN FECHA. El bloque que importa
    llaves solo sabia agregar lo que faltaba y descartar lo repetido, y "repetido"
    incluye al partido que la pagina publica sin dia: el cruce lo reconocia y se
    iba igual a `sin-fecha/` porque nadie miraba la fecha. Eran los ocho de la
    Tercera fase del Argentino A 2012-13.

    El identificador es el PAR ORDENADO: las dos patas de una serie son (A,B) y
    (B,A), asi que se distinguen sin la ronda -- que ademas no cruzaria, porque la
    pagina rotula "Tercera fase" y la fuente "Third Phase - First leg".
    """
    from fad.parser import Partido

    ida = Partido(local="Racing (C)", visita="Talleres (C)", goles_local=1,
                  goles_visita=1, fase="eliminacion", jornada="Tercera fase")
    vuelta = Partido(local="Talleres (C)", visita="Racing (C)", goles_local=2,
                     goles_visita=0, fase="eliminacion", jornada="Tercera fase")
    llaves = [
        Partido(fecha="2013-05-22", local="Racing (C)", visita="Talleres (C)",
                goles_local=1, goles_visita=1, fase="eliminacion",
                jornada="Third Phase - First leg"),
        Partido(fecha="2013-05-26", local="Talleres (C)", visita="Racing (C)",
                goles_local=2, goles_visita=0, fase="eliminacion",
                jornada="Third Phase - Second leg"),
    ]
    build.fechar_con_las_llaves([ida, vuelta], llaves)
    assert (ida.fecha, vuelta.fecha) == ("2013-05-22", "2013-05-26")


def test_no_le_pone_la_fecha_de_una_llave_a_un_partido_de_liga():
    """SOLO SOBRE LA ELIMINACION. Esto corre en la etapa de parseo, antes de que
    el completador de la fase regular haga lo suyo, asi que la pagina entera puede
    estar sin fechas. Sin acotarlo daba trescientos setenta y siete "sin pareja"
    en la Primera C 2008-09, un grave, y le ofrecia a un partido de liga la fecha
    de una llave."""
    from fad.parser import Partido

    liga = Partido(local="Racing (C)", visita="Talleres (C)", goles_local=1,
                   goles_visita=1, fase="zonas", jornada="Fecha 7")
    llave = Partido(fecha="2013-05-22", local="Racing (C)", visita="Talleres (C)",
                    goles_local=1, goles_visita=1, fase="eliminacion",
                    jornada="Third Phase - First leg")
    build.fechar_con_las_llaves([liga], [llave])
    assert liga.fecha == "", "el mismo cruce en la liga no es el de la llave"


def test_si_el_marcador_no_coincide_no_se_fecha():
    """El par identifica y el marcador VERIFICA, que es la regla de
    `fechas.completar` y sigue puesta acá."""
    from fad.parser import Partido

    nuestro = Partido(local="Racing (C)", visita="Talleres (C)", goles_local=3,
                      goles_visita=0, fase="eliminacion", jornada="Tercera fase")
    llave = Partido(fecha="2013-05-22", local="Racing (C)", visita="Talleres (C)",
                    goles_local=1, goles_visita=1, fase="eliminacion",
                    jornada="Third Phase - First leg")
    avisos = build.fechar_con_las_llaves([nuestro], [llave])
    assert nuestro.fecha == "" and any("marcador distinto" in a for a in avisos)


def _cuadro(*cruces, ronda="Tercera fase"):
    """Una pagina con una fase de eliminacion y la columna de fecha VACIA, que es
    como la publica el Argentino A 2012-13."""
    filas = "".join(f"|-\n|{a}\n|{gl} - {gv}\n|{b}\n|Un Estadio\n|\n|\n"
                    for a, b, gl, gv in cruces)
    return (f"\n== Fase final ==\n=== {ronda} ===\n"
            '{|class="wikitable"\n'
            f"!colspan=6|{ronda}\n|-\n"
            "!Local\n!Resultado\n!Visitante\n!Estadio\n!Fecha\n!Hora\n"
            + filas + "|}\n\n== Otra cosa ==\n")


def test_el_build_fecha_las_llaves_de_la_pagina_que_vienen_sin_dia(monkeypatch):
    """EL PUNTO DE LLAMADA, no la funcion. Los tres tests de arriba prueban
    `fechar_con_las_llaves`, y con eso un mutante que le saca la llamada al bloque
    de importacion sobrevive: la funcion anda perfecto y no la usa nadie.

    Es el mismo agujero que este repo ya se hizo dos veces -- probar la funcion y
    no a quien la llama --, y lo destapo un mutante que sobrevivio.
    """
    from fad import rsssf

    documento = ("Zona Unica\n"
                 "Third Phase Reválida\n"
                 "First leg [May 22]\n"
                 "Racing                       1-1 Talleres\n"
                 "Second leg [May 26]\n"
                 "Talleres                     2-0 Racing\n")
    mapa = {"Zona Unica": {"Racing": "Racing (C)", "Talleres": "Talleres (C)"}}
    t = Torneo("Anexo:Prueba", "Prueba", 2012, anio_fin=2013, rsssf_llaves=True)

    monkeypatch.setattr(rsssf, "descargar", lambda *a, **k: documento)
    monkeypatch.setitem(rsssf.FUENTES, "Anexo:Prueba", ("cualquiera", mapa))

    ps, _ = build.procesar(_cuadro(("Racing (C)", "Talleres (C)", 1, 1),
                                   ("Talleres (C)", "Racing (C)", 2, 0)), t)
    assert sorted(p.fecha for p in ps) == ["2013-05-22", "2013-05-26"]


# EL ANIO DE CIERRE QUE SE LE PASA A RSSSF. Un torneo que arranca en un anio que no
# es el de su etiqueta y no cruza el calendario: el parser le pone `primer_anio` a
# todo, y RSSSF tiene que hacer lo mismo con lo que cae antes de `mes_inicio` (el 8
# de siempre). Se le pasaba `anio_fin or temporada`, que es la ETIQUETA, y un partido
# de marzo salia 2012 de RSSSF y 2011 de la pagina. Hoy no lo pisa ningun torneo del
# catalogo: el unico con `anio_inicio` tiene `anio_fin`. Son tres llamadas y van tres.
_ARRANCA_ANTES = {"anio_inicio": 2011}


def test_el_completador_de_rsssf_fecha_con_el_anio_de_la_pagina(monkeypatch):
    from fad import rsssf
    from fad.parser import Partido

    documento = "Round 1\n[Mar 2]\nRacing                       3-0 Talleres\n"
    mapa = {"": {"Racing": "Racing (C)", "Talleres": "Talleres (C)"}}
    t = Torneo("Anexo:Prueba", "Prueba", 2012, **_ARRANCA_ANTES)
    monkeypatch.setattr(rsssf, "descargar", lambda *a, **k: documento)
    monkeypatch.setitem(rsssf.FUENTES, "Anexo:Prueba", ("cualquiera", mapa))

    ps = [Partido(local="Racing (C)", visita="Talleres (C)", goles_local=3,
                  goles_visita=0, fase="zonas", jornada="Fecha 1")]
    build._completar_fechas_rsssf(ps, t)
    assert ps[0].fecha == "2011-03-02", "no el anio de la etiqueta"


def test_la_rama_sin_grilla_fecha_con_el_anio_de_la_pagina(monkeypatch):
    from fad import rsssf

    documento = "Round 1\n[Mar 2]\nBoca Juniors            1-0 River Plate\n"
    t = Torneo("Anexo:Prueba", "Prueba", 2012, cerrado=False, sin_grilla=True,
               **_ARRANCA_ANTES)
    monkeypatch.setattr(rsssf, "FUENTES", {t.pagina: ("archivo", {"": {
        "Boca Juniors": "Boca Juniors", "River Plate": "River Plate"}})})
    monkeypatch.setattr(rsssf, "descargar", lambda *a, **k: documento)
    ps, _ = build.procesar("", t)
    assert [p.fecha for p in ps] == ["2011-03-02"], "no el anio de la etiqueta"


def test_las_llaves_de_rsssf_fechan_con_el_anio_de_la_pagina(monkeypatch):
    from fad import rsssf

    documento = ("Zona Unica\n"
                 "Third Phase Reválida\n"
                 "First leg [Mar 2]\n"
                 "Racing                       1-1 Talleres\n"
                 "Second leg [Mar 6]\n"
                 "Talleres                     2-0 Racing\n")
    mapa = {"Zona Unica": {"Racing": "Racing (C)", "Talleres": "Talleres (C)"}}
    t = Torneo("Anexo:Prueba", "Prueba", 2012, rsssf_llaves=True, **_ARRANCA_ANTES)
    monkeypatch.setattr(rsssf, "descargar", lambda *a, **k: documento)
    monkeypatch.setitem(rsssf.FUENTES, "Anexo:Prueba", ("cualquiera", mapa))

    ps, _ = build.procesar(_cuadro(("Racing (C)", "Talleres (C)", 1, 1),
                                   ("Talleres (C)", "Racing (C)", 2, 0)), t)
    assert sorted(p.fecha for p in ps) == ["2011-03-02", "2011-03-06"], (
        "no el anio de la etiqueta")


def test_procesar_le_dice_a_los_chequeos_si_el_torneo_esta_en_curso(monkeypatch):
    """EL CABLE. `en_curso` sale de `Torneo.cerrado` y de ningun otro lado, por una
    sola linea. Los tests del validador prueban de `revisar` para adentro: si esa
    linea dijera siempre "en curso" no fallaba ninguno, y dos chequeos quedaban
    apagados justo donde importan -- un torneo cerrado al que le faltan partidos
    dejaba de frenar, y una fase final antes del arranque era un aviso para siempre.
    """
    from dataclasses import replace

    visto = []
    real = build.validar.revisar

    def espia(ps, en_curso=False, **k):
        visto.append(en_curso)
        return real(ps, en_curso=en_curso, **k)

    monkeypatch.setattr(build.validar, "revisar", espia)
    pagina = tabla(("Boca Juniors", "River Plate"))
    build.procesar(pagina, T)
    build.procesar(pagina, replace(T, cerrado=True))
    assert visto == [True, False]


# --------------------------------------------------------------------------
# El credito de la fila que nace de RSSSF y a la que el dia se lo pone otro
# --------------------------------------------------------------------------
# Los renglones de `arg3-int05` tal cual los publica RSSSF, con su relleno:
# https://www.rsssf.org/tablesa/arg3-int05.html
_ARG3_INT05 = ("Torneo Apertura\n"
               "\n"
               "Zona Campeonato\n"
               "\n"
               "Quarterfinals\n"
               "[Nov 20-28]\n"
               "Aldosivi                 0-1 1-3 Luján de Cuyo \n"
               "\n"
               "Semifinals [Dec 1-5]\n"
               "Ben Hur                  2-1 2-2 Atlético Tucumán\n")

# Y las filas de `data/partidos-2004.csv` que salen de esos dos renglones. La ida
# de la primera llave es la que el blog escribe «20/11/2004 en Mar del Plata:
# Aldosivi de Mar del Plata 0, Luján de Cuyo de Mendoza 1»; la ida de la segunda es
# la unica que fecha la otra pagina citada, porque el blog le pone un dia de febrero.
_PAGINA_04 = "https://es.wikipedia.org/wiki/Torneo_Argentino_A_2004-05"
_FILAS_DE_ARG3_INT05 = [
    "2004-11-20,,Aldosivi,Luján de Cuyo,0,1,,,Torneo Argentino A,2004,eliminacion,,"
    "Zona Campeonato - Quarterfinals,,false,"
    + _PAGINA_04 + " + https://www.rsssf.org/ + http://josecarluccio.blogspot.com/,",
    "2004-11-28,,Luján de Cuyo,Aldosivi,3,1,,,Torneo Argentino A,2004,eliminacion,,"
    "Zona Campeonato - Quarterfinals,,false,"
    + _PAGINA_04 + " + https://www.rsssf.org/ + http://josecarluccio.blogspot.com/,",
    "2004-12-01,,Ben Hur,Atlético Tucumán,2,1,,,Torneo Argentino A,2004,eliminacion,,"
    "Zona Campeonato - Semifinals,,false,"
    + _PAGINA_04 + " + https://www.rsssf.org/ + http://soybh.blogspot.com/p/argentino-200405.html,",
    "2004-12-05,,Atlético Tucumán,Ben Hur,2,2,,,Torneo Argentino A,2004,eliminacion,,"
    "Zona Campeonato - Semifinals,,false,"
    + _PAGINA_04 + " + https://www.rsssf.org/ + http://josecarluccio.blogspot.com/,",
]


def _publicado_2004():
    import pathlib
    datos = pathlib.Path(__file__).resolve().parent.parent / "data" / "partidos-2004.csv"
    if not datos.exists():
        pytest.skip("hace falta el dataset")
    return datos


def _como_en_el_csv(filas: list[dict]) -> list[str]:
    """Las filas con el texto que tendrian en el archivo, sin el encabezado."""
    from fad import dataset
    return dataset._serializar(sorted(filas, key=dataset._orden)).decode("utf-8").splitlines()[1:]


def test_la_llave_que_sale_de_rsssf_la_nombra_aunque_el_dia_se_lo_ponga_un_blog(monkeypatch):
    """EL PARTIDO SALE DE RSSSF, EL DIA DE UN BLOG, Y LA FILA NOMBRA A LOS DOS.

    Las llaves del Argentino A 2004-05 la pagina las trae solo como cuadro. Las
    filas nacen del archivo compacto de RSSSF, sin dia --su corchete es un rango
    que cubre las dos patas--, y despues las fechan las citas. `fechas.completar`
    se quedaba con el ultimo credito: 37 filas publicadas nombraban al blog, que
    les puso un campo, y no a la fuente de la que salen los clubes, el marcador, la
    localia y la ronda.

    Por `procesar` y con el torneo, el mapa y las citas de verdad, porque el
    credito se perdia ENTRE dos pasos que cada uno por su lado estaba bien. Y
    contra el texto de las filas publicadas, que es lo que un tercero puede ir a
    contradecir: de un lado los renglones de RSSSF, del otro el CSV."""
    from fad import dataset, rsssf, torneos

    t = next(x for x in torneos.TODOS if x.pagina == "Torneo Argentino A 2004-05")
    assert t.rsssf_compacto, "si deja de serlo, este test mira otro camino"
    monkeypatch.setattr(rsssf, "descargar", lambda *a, **k: _ARG3_INT05)

    # La pagina va vacia: lo que se mira son las filas que la pagina NO trae.
    ps, _ = build.procesar("", t)
    filas = [dataset.a_fila(p, t.torneo, t.temporada, t.url, t.neutral) for p in ps]
    assert _como_en_el_csv(filas) == _FILAS_DE_ARG3_INT05

    publicadas = _publicado_2004().read_text(encoding="utf-8").splitlines()
    for fila in _FILAS_DE_ARG3_INT05:
        assert fila in publicadas, f"el CSV publicado no trae esta fila tal cual:\n{fila}"


def test_las_37_llaves_del_argentino_a_2004_05_nombran_a_rsssf():
    """Lo mismo sobre lo PUBLICADO, que es donde vive: el torneo esta cerrado y el
    build de todos los dias reusa sus filas del CSV sin volver a armarlas, asi que
    arreglar el codigo no arregla el dato.

    Las que nacen de RSSSF se reconocen sin mirar `source`: son las unicas de esa
    pagina cuyo `matchday` lleva el cuadro y la ronda como los escribe el archivo
    --`Zona Campeonato - Quarterfinals`--. Las otras 80 son de la pagina, y esas
    NO la nombran: 60 llaves que Wikipedia publica con su dia y 20 partidos de zona
    que publica sin el, a los que el blog les pone la fecha y nada mas."""
    from fad import citadas, dataset, rsssf

    suyas = [f for f in dataset.leer(_publicado_2004())
             if dataset.pagina_de(f) == _PAGINA_04]
    assert len(suyas) == 117
    de_rsssf = [f for f in suyas if f["matchday"].startswith("Zona ")]
    assert len(de_rsssf) == 37 and {f["phase"] for f in de_rsssf} == {"eliminacion"}
    for f in de_rsssf:
        pagina, de_donde, quien_fecho = f["source"].split(dataset.SEPARADOR)
        assert (pagina, de_donde) == (_PAGINA_04, rsssf.CREDITO), f["source"]
        assert quien_fecho in (citadas.CREDITO, citadas.CREDITO_SOYBH), f["source"]
    assert sum(f["source"].endswith(citadas.CREDITO_SOYBH) for f in de_rsssf) == 1
    los_de_la_pagina = [f for f in suyas if not f["matchday"].startswith("Zona ")]
    assert len(los_de_la_pagina) == 80
    assert not [f["source"] for f in los_de_la_pagina if "rsssf" in f["source"]]


# --------------------------------------------------------------------------
# un partido que publican dos paginas
# --------------------------------------------------------------------------
PROMO_B = Torneo("Anexo:Prueba B", "Primera B", 2026)                    # cerrado
PROMO_C = Torneo("Anexo:Prueba C", "Primera C", 2026, cerrado=False)     # en curso


def _promo(hora: str, sin_local: bool) -> str:
    """La misma promocion como la escribe cada division: una con la hora y como
    tabla sin local, la otra sin hora y con "Local / Visitante"."""
    t = tabla(("Boca Juniors", "River Plate")).replace("|20:00\n", f"|{hora}\n")
    return t.replace("!Local\n", "!Equipo 1\n") if sin_local else t


def _dos_paginas(monkeypatch, tmp_path, paginas):
    monkeypatch.setattr(build.torneos, "TODOS", [PROMO_B, PROMO_C])
    monkeypatch.setattr(build.wiki, "wikitexto", lambda pag, *a, **k: paginas[pag])
    monkeypatch.setattr(build, "SALIDA", tmp_path / "data")


def _de_cada_torneo(tmp_path):
    return sorted((f["tournament"], f["time"], f["neutral"])
                  for f in build.dataset.leer_carpeta(tmp_path / "data"))


def test_las_dos_copias_de_un_partido_salen_iguales(monkeypatch, tmp_path, capsys):
    paginas = {PROMO_B.pagina: _promo("", sin_local=False),
               PROMO_C.pagina: _promo("20:00", sin_local=True)}
    _dos_paginas(monkeypatch, tmp_path, paginas)
    assert build.main([]) == 0
    assert _de_cada_torneo(tmp_path) == [
        ("Primera B", "20:00", "true"), ("Primera C", "20:00", "true")]

    # Al dia siguiente la B se reusa del CSV y la C se relee: siguen iguales, y se
    # avisa que no se completan una con la otra.
    capsys.readouterr()
    assert build.main([]) == 0
    assert _de_cada_torneo(tmp_path) == [
        ("Primera B", "20:00", "true"), ("Primera C", "20:00", "true")]
    err = capsys.readouterr().err
    assert "se releyo" in err
    assert "publican distinto" not in err, "la del CSV y la recien armada son la misma tanda"


def test_la_copia_en_curso_sigue_a_su_pagina_y_no_a_la_del_csv(monkeypatch, tmp_path, capsys):
    """La copia cerrada tiene la hora y el `neutral` que se completaron con la otra
    pagina. Si esa otra pagina, todavia en curso, los saca, devolverselos desde el
    CSV la dejaria publicando lo que ya no dice nadie: sigue a su pagina, y se avisa."""
    paginas = {PROMO_B.pagina: _promo("", sin_local=False),
               PROMO_C.pagina: _promo("20:00", sin_local=True)}
    _dos_paginas(monkeypatch, tmp_path, paginas)
    assert build.main([]) == 0
    paginas[PROMO_C.pagina] = _promo("", sin_local=False)
    capsys.readouterr()
    assert build.main([]) == 0
    assert _de_cada_torneo(tmp_path) == [
        ("Primera B", "20:00", "true"), ("Primera C", "", "false")]
    assert "difieren en neutral, time" in capsys.readouterr().err


def test_dos_paginas_que_no_coinciden_avisan_y_no_frenan(monkeypatch, tmp_path, capsys):
    """Un grave en un torneo en curso dejaria sin actualizar a todos los demas por
    un desacuerdo que solo se resuelve con una declaracion a mano."""
    paginas = {PROMO_B.pagina: _promo("15:00", sin_local=False),
               PROMO_C.pagina: _promo("15:30", sin_local=False)}
    _dos_paginas(monkeypatch, tmp_path, paginas)
    assert build.main([]) == 0
    assert sorted(f["time"] for f in build.dataset.leer_carpeta(tmp_path / "data")) == [
        "15:00", "15:30"]
    assert "15:00 / 15:30" in capsys.readouterr().err


def test_un_club_en_dias_seguidos_en_dos_paginas_avisa_y_no_frena(monkeypatch, tmp_path,
                                                                  capsys):
    """Cada pagina ve uno solo de los dos partidos: River juega el 23 la promocion
    que publican las dos, y el 24 la Fecha 2 de la C. Lo ve el chequeo de dataset
    entero, y avisa una vez -- la promocion es UN partido, no dos el mismo dia -- sin
    frenar la escritura."""
    fecha_2 = tabla(("Independiente", "River Plate")).replace(
        "Fecha 1", "Fecha 2").replace("23 de enero", "24 de enero")
    paginas = {PROMO_B.pagina: _promo("20:00", sin_local=False),
               PROMO_C.pagina: _promo("20:00", sin_local=False) + fecha_2}
    _dos_paginas(monkeypatch, tmp_path, paginas)
    assert build.main([]) == 0
    assert len(build.dataset.leer_carpeta(tmp_path / "data")) == 3
    dichos = [ln for ln in capsys.readouterr().err.splitlines() if "juega dos partidos" in ln]
    assert len(dichos) == 1, dichos
    assert dichos[0].startswith("  aviso: River Plate juega dos partidos en dias seguidos: "
                                "2026-01-23 Boca Juniors 2-1 River Plate")


# --------------------------------------------------------------------------
# un partido en cancha neutral declarado a mano
# --------------------------------------------------------------------------
def _neutral(monkeypatch, dice=("Boca Juniors", "River Plate", 2, 1)):
    from fad import correcciones
    from fad.correcciones import Neutral
    monkeypatch.setattr(correcciones, "NEUTRALES", (
        Neutral(pagina=T.pagina, fecha="2026-01-23", dice=dice, porque="x" * 90),))


def test_un_partido_declarado_neutral_sale_neutral(monkeypatch):
    _neutral(monkeypatch)
    ps, avisos = build.procesar(tabla(("Boca Juniors", "River Plate")), T)
    assert [p.neutral for p in ps] == [True]
    assert any("corregidos a mano" in a.que for a in avisos)
    assert not [a for a in avisos if a.grave], [a.que for a in avisos if a.grave]


def test_un_neutral_que_ya_no_engancha_frena_el_build(monkeypatch):
    """Como cualquier correccion: o la fuente cambio y hay que sacarlo, o esta
    apuntando a otro partido."""
    _neutral(monkeypatch, dice=("Boca Juniors", "River Plate", 9, 9))
    ps, avisos = build.procesar(tabla(("Boca Juniors", "River Plate")), T)
    assert [p.neutral for p in ps] == [None]
    assert any(a.grave and "correccion que no aplica" in a.que and "neutral" in a.detalle
               for a in avisos)


def test_un_neutral_que_la_pagina_ya_marca_avisa_sin_frenar(monkeypatch):
    """La pagina paso a rotular la tabla "Equipo 1 / Equipo 2": el dato sale bien con
    la entrada o sin ella, asi que no se frena nada, pero se pide sacarla."""
    _neutral(monkeypatch)
    sin_local = (tabla(("Boca Juniors", "River Plate"))
                 .replace("!Local", "!Equipo 1").replace("!Visitante", "!Equipo 2"))
    ps, avisos = build.procesar(sin_local, T)
    assert [p.neutral for p in ps] == [True]
    sobra = [a for a in avisos if "neutral declarado que la pagina ya da" in a.que]
    assert len(sobra) == 1 and not sobra[0].grave
    assert not [a for a in avisos if a.grave], [a.que for a in avisos if a.grave]


def _de_local(monkeypatch, dice=("Boca Juniors", "River Plate", 2, 1)):
    from fad import correcciones
    from fad.correcciones import Neutral
    monkeypatch.setattr(correcciones, "NEUTRALES", (
        Neutral(pagina=T.pagina, fecha="2026-01-23", dice=dice, porque="x" * 90,
                neutral=False),))


def _sin_local(texto: str) -> str:
    return texto.replace("!Local", "!Equipo 1").replace("!Visitante", "!Equipo 2")


def test_un_partido_declarado_de_local_sale_de_local(monkeypatch):
    """El otro lado: la pagina lo da por neutral -- aca, con "Equipo 1 / Equipo 2" -- y
    la declaracion lo desmarca. Es lo que pasa en la tercera y la cuarta fase de
    perdedores del Nacional 1985."""
    _de_local(monkeypatch)
    ps, avisos = build.procesar(_sin_local(tabla(("Boca Juniors", "River Plate"))), T)
    assert [p.neutral for p in ps] == [False]
    assert any("corregidos a mano" in a.que for a in avisos)
    assert not [a for a in avisos if a.grave], [a.que for a in avisos if a.grave]


def test_un_de_local_que_la_pagina_ya_da_avisa_sin_frenar(monkeypatch):
    """La pagina dejo de darlo por neutral: la fila sale sin marcar con la entrada o
    sin ella, y se pide sacarla."""
    _de_local(monkeypatch)
    ps, avisos = build.procesar(tabla(("Boca Juniors", "River Plate")), T)
    assert [p.neutral for p in ps] == [None]
    sobra = [a for a in avisos if "neutral declarado que la pagina ya da" in a.que]
    assert len(sobra) == 1 and not sobra[0].grave and "de local" in sobra[0].detalle
    assert not [a for a in avisos if a.grave], [a.que for a in avisos if a.grave]


# --------------------------------------------------------------------------
# la tanda que la pagina publica solo en la tabla del global
# --------------------------------------------------------------------------
# Una etapa de la Revalida como la escribe el Federal A 2016-17: arriba la tabla del
# global, con la tanda, y abajo las dos tablas de resultados, rotuladas solo por la
# pata. Los nombres no son los mismos en las dos: la del global escribe el largo.
_REVALIDA = """== Reválida ==
=== Cuarta etapa ===
==== Enfrentamientos ====
{| class="wikitable"
|- style="background:#dddddd;"
|-
!width=40|Llave
!width=160|Equipo 1
!width=30|Global
!width=160|Equipo 2
|-align=center
|'''4
|bgcolor=#ccffcc|'''Cipolletti
|{{small|(3)}} 1 - 1 {{small|(1)}}
|Juventud Antoniana
|}

==== Resultados ====
{|class="wikitable collapsible collapsed"
!colspan="6"|Partidos de ida
|-
!width="150"|Local
!width="65"|Resultado
!width="150"|Visitante
!width="150"|Estadio
!width="75"|Fecha
!width="40"|Hora
|-align=center
|Juventud Antoniana
|1 - 1
|Cipolletti
|Padre Ernesto Martearena
|24 de mayo
|21:30
|}
{|class="wikitable collapsible collapsed"
!colspan="6"|Partidos de vuelta
|-
!width="150"|Local
!width="65"|Resultado
!width="150"|Visitante
!width="150"|Estadio
!width="75"|Fecha
!width="40"|Hora
|-align=center
|Cipolletti
|0 - 0
|Juventud Antoniana
|La Visera de Cemento
|28 de mayo
|16:00
|}
"""
REVALIDA = Torneo("Anexo:Prueba", "Prueba", 2016, anio_fin=2017, cerrado=False)


def test_la_tanda_de_la_tabla_del_global_llega_a_la_vuelta():
    """La vuelta empato, asi que la tanda se explica sola. RSSSF la da igual:
    `Cipolletti [3] 0-0 [1] Juventud Antoniana`, el 28 de mayo de 2017."""
    ps, avisos = build.procesar(_REVALIDA, REVALIDA)
    vuelta = [p for p in ps if p.fecha == "2017-05-28"]
    assert [(p.local, p.penales_local, p.penales_visita) for p in vuelta] == [
        ("Cipolletti", 3, 1)]
    assert [p.penales_local for p in ps if p.fecha == "2017-05-24"] == [None]
    assert not [a for a in avisos if "tabla del global" in a.que]
    assert not [a for a in avisos if a.grave], [a.que for a in avisos if a.grave]


def test_la_tanda_de_una_vuelta_que_no_empato_entra_porque_las_patas_son_una_serie():
    """Cipolletti 1-0 en la vuelta despues de perder 2-1 la ida: 2-2 global, y la
    tanda se pateo al final de una vuelta que no empato. La explica la serie, y
    `serie_igualada` la reconoce porque las dos patas llevan la ronda del titulo,
    `Cuarta etapa`, y no la pata. Con `Partidos de ida` y `Partidos de vuelta` en la
    jornada no la reconocia, y escribirla era un grave: asi esperaban 10 de las 22
    tandas del Federal A."""
    sin_empate = _REVALIDA.replace("|Cipolletti\n|0 - 0\n", "|Cipolletti\n|1 - 0\n").replace(
        "{{small|(3)}} 1 - 1 {{small|(1)}}", "{{small|(3)}} 2 - 2 {{small|(1)}}").replace(
        "|Juventud Antoniana\n|1 - 1\n", "|Juventud Antoniana\n|2 - 1\n")
    ps, avisos = build.procesar(sin_empate, REVALIDA)
    assert sorted((p.fecha, p.jornada, p.penales_local, p.penales_visita) for p in ps) == [
        ("2017-05-24", "Cuarta etapa", None, None), ("2017-05-28", "Cuarta etapa", 3, 1)]
    assert not [a for a in avisos if "tabla del global" in a.que]
    assert not [a for a in avisos if a.grave], [a.que for a in avisos if a.grave]


def test_la_tanda_que_no_cierra_con_la_grilla_se_avisa_y_no_frena():
    """Si las patas de la grilla no suman el global de la tabla, una de las dos tablas
    esta mal y no hay como saber cual: la tanda queda afuera, con un aviso que no
    frena el build."""
    otra = _REVALIDA.replace("|Cipolletti\n|0 - 0\n", "|Cipolletti\n|1 - 0\n")
    ps, avisos = build.procesar(otra, REVALIDA)
    assert all(p.penales_local is None for p in ps)
    espera = [a for a in avisos if "tabla del global" in a.que]
    assert len(espera) == 1 and not espera[0].grave and "suman 2-1" in espera[0].detalle
    assert not [a for a in avisos if a.grave], [a.que for a in avisos if a.grave]

#!/usr/bin/env python3
"""Tests del pipeline: parsear -> normalizar nombres -> validar.

El pegamento tambien se rompe, y calladito: sacar el paso de normalizacion no
hace fallar nada, solo escribe "Newell`s" en el CSV publicado y al mes hay dos
clubes con media historia cada uno.
"""
from __future__ import annotations

import build
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
    """El estado de hoy sin este paso: la pagina no trae fecha, el esquema exige
    una, y el partido se descarta. Es la linea de base contra la que se mide."""
    T_SIN = Torneo("Anexo:Prueba", "Prueba", 2007, cerrado=False)
    ps, _ = build.procesar(_sin_fecha(), T_SIN)
    assert ps == []


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
    no entran, que es exactamente lo que pasaba antes de que existiera."""
    from fad import fechas

    def explota(*a, **k):
        raise OSError("HTTP Error 403: Forbidden")

    monkeypatch.setattr(fechas, "descargar", explota)
    ps, avisos = build.procesar(_sin_fecha(), CON_WF)
    assert ps == []
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
    assert ps == []
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

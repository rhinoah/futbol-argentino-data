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
    y el feed de ESPN para las tres de Primera C y la Primera B 2010-11 -- y el
    flag quedo sin un solo usuario, asi que se saco.

    Lo que queda por sostener es la otra mitad: una marca de fuente que apunte a
    una entrada que no existe revienta el build a mitad de camino, con el CSV
    anterior ya leido."""
    from fad import espn, rsssf, torneos
    assert "sin_fecha" not in Torneo.__dataclass_fields__, "el flag volvio sin querer"
    con_fuente = 0
    for t in torneos.TODOS:
        if t.rsssf:
            assert t.pagina in rsssf.FUENTES, f"{t.pagina}: `rsssf` sin entrada en FUENTES"
            con_fuente += 1
        if t.espn:
            assert t.pagina in espn.FUENTES, f"{t.pagina}: `espn` sin entrada en FUENTES"
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
    Español 1-0 Luján" y ESPN "Luján 0-1 Deportivo Español", el mismo 30 de mayo.
    Contarlo como repetido y callarse tapa un desacuerdo real."""
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


def test_una_zona_con_dos_tablas_no_se_cruza():
    """Cardinalidad: si la zona trae dos tablas no se sabe cual cubre que. Es el
    Argentino A 2009-10, que corre dos fases rotulando las dos `Zone 1`."""
    ps = [_zp("A", "B", 2, 0, "Zone 1")]
    una = _tabla("Zone 1", [(1, 1, 0, 0, 2, 0), (1, 0, 0, 1, 0, 2)])
    respaldados, avisos = build.la_fuente_se_respalda(ps, una + "\n" + una, _MAPA_2)
    assert (respaldados, avisos) == (set(), []), "dos tablas iguales tampoco alcanzan"


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

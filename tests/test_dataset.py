#!/usr/bin/env python3
"""Tests del CSV."""
from __future__ import annotations

import csv

import pytest

from fad import dataset
from fad.parser import Partido


def fila(fecha, local, visita, hora="20:00", **kw):
    p = Partido(fecha=fecha, hora=hora, local=local, visita=visita,
                goles_local=1, goles_visita=0, fase="zonas", zona="Zona A",
                jornada="Fecha 1", estadio="La Bombonera", **kw)
    return dataset.a_fila(p, "Primera", 2026, "https://ejemplo")


def test_ida_y_vuelta(tmp_path):
    destino = tmp_path / "p.csv"
    original = [fila("2026-03-01", "Boca", "River")]
    dataset.escribir(original, destino)
    leido = dataset.leer(destino)
    assert len(leido) == 1
    assert leido[0]["home_team"] == "Boca"
    assert leido[0]["home_score"] == "1"


def test_el_encabezado_es_el_esquema(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    with destino.open(encoding="utf-8", newline="") as f:
        assert next(csv.reader(f)) == dataset.COLUMNAS


def test_las_filas_salen_ordenadas(tmp_path):
    """Este archivo se regenera solo y se commitea. Si el orden dependiera de
    como Wikipedia acomodo las tablas, cada commit seria un diff de miles de
    lineas movidas y no se veria que cambio de verdad."""
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-05-01", "Racing", "Union"),
                      fila("2026-03-01", "Boca", "River"),
                      fila("2026-03-01", "Aldosivi", "Tigre", hora="17:00")], destino)
    fechas = [(f["date"], f["time"]) for f in dataset.leer(destino)]
    assert fechas == sorted(fechas)
    assert fechas[0] == ("2026-03-01", "17:00")


def test_el_mismo_dataset_da_el_mismo_archivo(tmp_path):
    """Sin esto, una tarea diaria commitea un cambio aunque no haya pasado nada."""
    a, b = tmp_path / "a.csv", tmp_path / "b.csv"
    filas = [fila("2026-05-01", "Racing", "Union"), fila("2026-03-01", "Boca", "River")]
    dataset.escribir(filas, a)
    dataset.escribir(list(reversed(filas)), b)
    assert a.read_bytes() == b.read_bytes()


def test_los_penales_vacios_no_dicen_None(tmp_path):
    """`str(None)` en un CSV es la cadena 'None', y quien lo lea despues tiene un
    equipo que convirtio None penales."""
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    assert dataset.leer(destino)[0]["home_pens"] == ""
    assert "None" not in destino.read_text(encoding="utf-8")


def test_los_penales_cuando_los_hay(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River",
                           penales_local=4, penales_visita=3)], destino)
    leido = dataset.leer(destino)[0]
    assert (leido["home_pens"], leido["away_pens"]) == ("4", "3")


def test_no_quedan_saltos_de_linea_de_mas(tmp_path):
    """En Windows, `csv` sin `newline=''` escribe \\r\\r\\n y sale una fila vacia
    entre cada dos."""
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River"),
                      fila("2026-03-02", "Racing", "Union")], destino)
    assert b"\r\r\n" not in destino.read_bytes()
    assert len(destino.read_text(encoding="utf-8").strip().splitlines()) == 3


def test_no_deja_el_archivo_temporal(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    assert [p.name for p in tmp_path.iterdir()] == ["p.csv"]


def test_pisa_el_archivo_anterior(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    dataset.escribir([fila("2026-04-01", "Racing", "Union")], destino)
    leido = dataset.leer(destino)
    assert len(leido) == 1 and leido[0]["home_team"] == "Racing"


def test_crea_la_carpeta_si_no_esta(tmp_path):
    destino = tmp_path / "nueva" / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    assert destino.exists()


def test_un_encabezado_distinto_se_rechaza(tmp_path):
    """Si alguien edito el CSV a mano o cambio el esquema, mejor romper que
    devolver diccionarios con las claves equivocadas."""
    destino = tmp_path / "p.csv"
    destino.write_text("fecha,local,visita\n2026-03-01,Boca,River\n", encoding="utf-8")
    with pytest.raises(ValueError, match="encabezado"):
        dataset.leer(destino)


def test_un_campo_de_mas_no_pasa_desapercibido(tmp_path):
    """`extrasaction='raise'`: si el parser empieza a devolver un campo que el
    esquema no tiene, se entera alguien."""
    mala = fila("2026-03-01", "Boca", "River") | {"inventado": 1}
    with pytest.raises(ValueError):
        dataset.escribir([mala], tmp_path / "p.csv")


def test_neutral_sale_del_torneo(tmp_path):
    """La Copa Argentina se juega toda en cancha neutral por reglamento; las
    ligas son local y visitante. El dato es de la competencia, no del partido."""
    destino = tmp_path / "p.csv"
    p = Partido(fecha="2026-03-01", local="Boca", visita="River", goles_local=1,
                goles_visita=0, fase="eliminacion")
    dataset.escribir([dataset.a_fila(p, "Copa", 2026, "url", neutral=True)], destino)
    assert dataset.leer(destino)[0]["neutral"] == "true"


def test_neutral_por_defecto_es_false(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    assert dataset.leer(destino)[0]["neutral"] == "false"


def test_neutral_no_sale_capitalizado(tmp_path):
    """`str(True)` en Python es "True" con mayuscula, que no es lo que espera
    quien lea el CSV con pandas o R."""
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    texto = destino.read_text(encoding="utf-8")
    assert "True" not in texto and "False" not in texto


# --------------------------------------------------------------------------
# la guarda contra achicarse: la unica que mira lo que YA NO esta
# --------------------------------------------------------------------------
def liga(torneo, temporada, n):
    """`n` partidos de un torneo, para contarlos."""
    return [dataset.a_fila(
        Partido(fecha=f"2026-03-{i + 1:02d}", local="Boca", visita="River",
                goles_local=1, goles_visita=0, fase="zonas"),
        torneo, temporada, "url") for i in range(n)]


def test_si_no_se_perdio_nada_no_dice_nada():
    antes = liga("Primera", 2025, 100)
    assert dataset.regresiones(liga("Primera", 2025, 100), antes) == []


def test_crecer_esta_bien():
    """Lo normal: ayer 100 partidos, hoy 110 porque se jugo una fecha."""
    antes = liga("Primera", 2025, 100)
    assert dataset.regresiones(liga("Primera", 2025, 110), antes) == []


def test_achicarse_avisa():
    """El caso que importa: Wikipedia reordena una pagina y el parser saca 40
    partidos donde habia 240. Los 40 pueden estar perfectos y coherentes entre
    si -- ningun chequeo de `validar` los ve mal, porque mirados solos estan
    bien. Lo unico que delata la perdida es comparar contra lo de ayer."""
    avisos = dataset.regresiones(liga("Primera", 2025, 40), liga("Primera", 2025, 240))
    assert len(avisos) == 1
    assert "240" in avisos[0] and "40" in avisos[0]


def test_un_torneo_que_desaparece_entero():
    avisos = dataset.regresiones([], liga("Primera", 2025, 240))
    assert len(avisos) == 1 and "DESAPARECIO" in avisos[0]


def test_un_torneo_nuevo_no_es_una_regresion():
    antes = liga("Primera", 2025, 100)
    ahora = liga("Primera", 2025, 100) + liga("Copa Argentina", 2026, 49)
    assert dataset.regresiones(ahora, antes) == []


def test_cada_temporada_se_cuenta_aparte():
    """Si 2016 se cae pero 2025 crece, el total puede subir y aun asi haberse
    perdido un anio entero."""
    antes = liga("Primera", 2016, 240) + liga("Primera", 2025, 100)
    ahora = liga("Primera", 2016, 0) + liga("Primera", 2025, 500)
    avisos = dataset.regresiones(ahora, antes)
    assert len(avisos) == 1 and "2016" in avisos[0]


def test_bug_comparar_lo_recien_armado_contra_lo_leido_del_csv(tmp_path):
    """EL caso real, y el que los otros tests de aca no cubrian.

    En produccion no se comparan dos listas armadas igual: se compara lo que
    acaba de salir del parser contra lo que se lee del CSV commiteado. Y ahi
    `season` es un entero de un lado y texto del otro, asi que las claves no se
    cruzaban y TODOS los torneos figuraban desaparecidos. La guarda frenaba cada
    build, todos los dias.

    Los demas tests no lo veian porque usaban `a_fila` de los dos lados. El bug
    vivia justo en la juntura que no se estaba probando.
    """
    destino = tmp_path / "p.csv"
    dataset.escribir(liga("Primera", 2025, 3), destino)
    del_csv = dataset.leer(destino)

    assert isinstance(liga("Primera", 2025, 3)[0]["season"], int)
    assert isinstance(del_csv[0]["season"], str)
    assert dataset.regresiones(liga("Primera", 2025, 3), del_csv) == []


def test_un_clon_nuevo_no_tiene_contra_que_comparar(tmp_path):
    assert dataset.read_anterior(tmp_path / "no-existe.csv") == []


def test_lee_el_anterior_si_esta(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River")], destino)
    assert len(dataset.read_anterior(destino)) == 1


def test_acentos(tmp_path):
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Unión", "Vélez Sarsfield")], destino)
    assert dataset.leer(destino)[0]["home_team"] == "Unión"


def test_el_csv_sale_con_el_mismo_final_de_linea_en_toda_maquina(tmp_path):
    """Lo escriben dos maquinas: la de desarrollo y el runner de Linux del cron.
    Si cada una elige un final de linea distinto, git ve el archivo entero
    cambiado aunque no haya cambiado un dato -- el primer commit automatico salio
    "+22271 -22271" por esto."""
    destino = tmp_path / "p.csv"
    dataset.escribir([fila("2026-03-01", "Boca", "River"),
                      fila("2026-03-02", "Racing", "Union")], destino)
    crudo = destino.read_bytes()
    assert b"\r" not in crudo, "quedo CRLF: el diff diario va a ser el archivo entero"
    assert crudo.count(b"\n") == 3


# --------------------------------------------------------------------------
# un archivo por temporada: lo cerrado no se vuelve a tocar
# --------------------------------------------------------------------------
def test_parte_por_temporada(tmp_path):
    dataset.escribir_por_temporada(
        liga("Primera", 2016, 3) + liga("Primera", 2026, 2), tmp_path)
    assert sorted(p.name for p in tmp_path.glob("*.csv")) == [
        "partidos-2016.csv", "partidos-2026.csv"]
    assert len(dataset.leer(tmp_path / "partidos-2016.csv")) == 3


def test_no_reescribe_el_archivo_que_no_cambio(tmp_path):
    """LO que hace que esto sirva. Una temporada terminada no se toca nunca mas:
    2004 quedo como quedo. Un archivo que no se reescribe no se puede corromper
    -- antes, un bug al escribir se llevaba puesto el historico entero -- y el
    diff diario toca un solo archivo en vez de las 27 000 filas."""
    viejas = liga("Primera", 2016, 3)
    dataset.escribir_por_temporada(viejas, tmp_path)
    antes = (tmp_path / "partidos-2016.csv").stat().st_mtime_ns

    cambiados = dataset.escribir_por_temporada(viejas + liga("Primera", 2026, 1), tmp_path)
    assert set(cambiados) == {"partidos-2026.csv"}, "toco una temporada que no cambio"
    assert (tmp_path / "partidos-2016.csv").stat().st_mtime_ns == antes


def test_leer_carpeta_junta_todo_en_orden(tmp_path):
    dataset.escribir_por_temporada(
        liga("Primera", 2026, 2) + liga("Primera", 2016, 2), tmp_path)
    filas = dataset.leer_carpeta(tmp_path)
    assert len(filas) == 4
    assert [f["date"] for f in filas] == sorted(f["date"] for f in filas)


def test_una_carpeta_vacia_no_es_un_error(tmp_path):
    assert dataset.leer_carpeta(tmp_path) == []


def test_los_archivos_por_temporada_no_llevan_CRLF(tmp_path):
    dataset.escribir_por_temporada(liga("Primera", 2016, 2), tmp_path)
    assert b"\r" not in (tmp_path / "partidos-2016.csv").read_bytes()


# --------------------------------------------------------------------------
# el `source` compuesto y el reuso
# --------------------------------------------------------------------------
def test_la_pagina_se_recupera_de_un_source_compuesto():
    """Es el ida y vuelta que faltaba: `a_fila` ESCRIBE las dos fuentes juntas y
    `build.main` tiene que poder volver a sacar la pagina para reusar el torneo.
    Sin esto, los cuatro torneos con segunda fuente no reusaban NUNCA -- se
    reparseaban todos los dias y le volvian a pedir la pagina al sitio de
    terceros, que es lo unico que `cerrado=True` estaba puesto para evitar."""
    from fad import dataset
    from fad.parser import Partido
    url = "https://es.wikipedia.org/wiki/Campeonato_de_Primera_B_Nacional_2007-08"
    p = Partido(fecha="2007-08-10", local="Aldosivi", visita="Almagro",
                goles_local=1, goles_visita=0, fase="zonas", jornada="Fecha 1")
    p.fuente_fecha = "https://www.worldfootball.net/"
    fila = dataset.a_fila(p, "Primera Nacional", 2007, url, False)
    assert fila["source"] != url, "el credito de la segunda fuente tiene que estar"
    assert dataset.pagina_de(fila) == url


def test_una_fila_de_una_sola_fuente_no_cambia():
    from fad import dataset
    from fad.parser import Partido
    url = "https://es.wikipedia.org/wiki/X"
    p = Partido(fecha="2026-01-01", local="Boca Juniors", visita="River Plate",
                goles_local=1, goles_visita=0, fase="zonas", jornada="Fecha 1")
    fila = dataset.a_fila(p, "Primera Division", 2026, url, False)
    assert fila["source"] == url and dataset.pagina_de(fila) == url


# --------------------------------------------------------------------------
# la cancha como testigo: dos clubes de nombre confundible, misma casa
# --------------------------------------------------------------------------
def _local(club, cancha, n=1, neutral="false"):
    return [{"home_team": club, "venue": cancha, "neutral": neutral} for _ in range(n)]


def test_dos_clubes_confundibles_en_la_misma_cancha():
    """El caso Estudiantes, en chico. Estudiantes de La Plata nunca jugo la
    Primera B: esos 44 partidos eran de Estudiantes de Caseros, y la cancha lo
    decia -- los 23 de local fueron en Ciudad de Caseros."""
    filas = (_local("Estudiantes (BA)", "Ciudad de Caseros", 20)
             + _local("Estudiantes (LP)", "Ciudad de Caseros", 5))
    avisos = dataset.casas_compartidas(filas)
    assert len(avisos) == 1
    assert "Estudiantes (BA)" in avisos[0] and "Estudiantes (LP)" in avisos[0]


def test_el_caso_racing_tambien():
    """Y el otro, donde uno de los dos nombres no lleva parentesis: "Racing Club"
    y "Racing (C)" comparten Miguel Sancho."""
    filas = _local("Racing Club", "Miguel Sancho", 10) + _local("Racing (C)", "Miguel Sancho", 3)
    assert len(dataset.casas_compartidas(filas)) == 1


def test_compartir_cancha_sin_parecerse_no_es_aviso():
    """Compartir estadio es normal -- los municipales de provincia, Argentinos y
    Chacarita. Lo que hace la firma es que ADEMAS se llamen igual, y sin esa
    condicion el chequeo pasa de 2 avisos a 8 y deja de servir."""
    filas = (_local("Argentinos Juniors", "Diego Armando Maradona", 20)
             + _local("Chacarita Juniors", "Diego Armando Maradona", 5))
    assert dataset.casas_compartidas(filas) == []


def test_dos_clubes_que_comparten_una_palabra_suelta_no_alcanzan():
    """"San Jorge (T)" y "San Martin (T)" comparten "San" y no son confundibles:
    el nucleo tiene que ser el mismo o uno tiene que contener al otro."""
    filas = (_local("San Martín (T)", "La Ciudadela", 20)
             + _local("San Jorge (T)", "La Ciudadela", 4))
    assert dataset.casas_compartidas(filas) == []


def test_la_cancha_neutral_no_dice_nada_de_nadie():
    """Una final o un desempate se juegan en cancha de un tercero. Contar eso
    como 'juega de local ahi' inventa parejas que no existen."""
    filas = (_local("Estudiantes (BA)", "Ciudad de Caseros", 20)
             + _local("Estudiantes (LP)", "Ciudad de Caseros", 5, neutral="true"))
    assert dataset.casas_compartidas(filas) == []


def test_sin_cancha_no_opina():
    filas = (_local("Estudiantes (BA)", "", 20) + _local("Estudiantes (LP)", "", 5))
    assert dataset.casas_compartidas(filas) == []


def test_el_mismo_club_en_dos_canchas_no_es_aviso():
    """Un club que se muda, o que alquila, no tiene nada de raro. El aviso es
    sobre DOS clubes en una cancha, no sobre un club en dos canchas."""
    filas = (_local("Boca Juniors", "La Bombonera", 20)
             + _local("Boca Juniors", "El Cilindro", 5))
    assert dataset.casas_compartidas(filas) == []


# --------------------------------------------------------------------------
# donde juega cada club: un salto de dos divisiones no existe
# --------------------------------------------------------------------------
_RIVALES = iter(range(10_000))


def _en(club, torneo, temporada="2015"):
    # Un rival distinto por fila. Reusando el mismo, el rival queda el tambien en
    # las dos categorias y el chequeo lo denuncia -- con razon, pero ensuciando
    # el test.
    return {"home_team": club, "away_team": f"Rival {next(_RIVALES)}",
            "tournament": torneo, "season": temporada}


def test_dos_divisiones_de_salto_es_aviso():
    """Estudiantes de La Plata en la Primera B 2015. Para ir de Primera a Primera
    B en un anio calendario habria que descender dos veces, y no hay calendario
    donde eso entre."""
    filas = [_en("Estudiantes (LP)", "Primera Division"),
             _en("Estudiantes (LP)", "Primera B")]
    avisos = dataset.categorias_incompatibles(filas)
    assert len(avisos) == 1 and "Estudiantes (LP)" in avisos[0]


def test_el_caso_racing_lo_agarra_este_y_no_el_de_la_cancha():
    """Racing de Cordoba a nombre de Avellaneda: Primera y Federal A el mismo
    anio. Los dos chequeos son complementarios -- al de la cancha se le escapaba
    en las temporadas donde las dos grafias no convivian."""
    filas = [_en("Racing Club", "Primera Division", "2018"),
             _en("Racing Club", "Torneo Federal A", "2018")]
    assert len(dataset.categorias_incompatibles(filas)) == 1


def test_un_ascenso_no_es_aviso():
    """El caso normal, y son 45 de los 46 del dataset: la temporada argentina
    cruza dos anios calendario, asi que el que desciende en junio juega el
    Clausura en Primera y desde agosto la Primera Nacional, con el mismo anio en
    las dos filas."""
    filas = [_en("Belgrano", "Primera Division - Clausura", "2007"),
             _en("Belgrano", "Primera Nacional", "2007")]
    assert dataset.categorias_incompatibles(filas) == []


def test_apertura_y_clausura_son_el_mismo_nivel():
    filas = [_en("Boca Juniors", "Primera Division - Apertura", "2010"),
             _en("Boca Juniors", "Primera Division - Clausura", "2010")]
    assert dataset.categorias_incompatibles(filas) == []


def test_la_copa_argentina_no_cuenta():
    """Cruza divisiones por diseno: ahi un club de Primera C contra uno de
    Primera es el torneo funcionando, no un error."""
    filas = [_en("Boca Juniors", "Primera Division"),
             _en("Boca Juniors", "Copa Argentina"),
             _en("Deportivo Armenio", "Primera C"),
             _en("Deportivo Armenio", "Copa Argentina")]
    assert dataset.categorias_incompatibles(filas) == []


def test_el_visitante_tambien_cuenta():
    """Un club mal atribuido puede aparecer solo de visitante en la categoria que
    no le toca."""
    filas = [_en("Estudiantes (LP)", "Primera Division"),
             {"home_team": "Almagro X", "away_team": "Estudiantes (LP)",
              "tournament": "Primera B", "season": "2015"}]
    assert len(dataset.categorias_incompatibles(filas)) == 1


def test_un_alquiler_verificado_no_cuenta_como_casa(monkeypatch):
    """Un chequeo que grita todos los dias por algo que ya se miro deja de
    leerse, y ahi se pierde el aviso que importaba. Pero el alquiler verificado
    no se silencia DESPUES: directamente no entra al recuento, que es lo mismo
    pero mas conservador."""
    monkeypatch.setattr(dataset, "ALQUILERES",
                        {("Ciudad de Caseros", "Estudiantes (LP)"): "verificado"})
    filas = (_local("Estudiantes (BA)", "Ciudad de Caseros", 20)
             + _local("Estudiantes (LP)", "Ciudad de Caseros", 5))
    assert dataset.casas_compartidas(filas) == []


def test_el_alquiler_verificado_es_de_UNA_cancha_y_UN_club(monkeypatch):
    """Silenciar de mas es el riesgo de este mecanismo. La entrada vale para el
    par exacto: el mismo club en otra cancha, o el mismo estadio con otro club,
    siguen avisando."""
    monkeypatch.setattr(dataset, "ALQUILERES",
                        {("Ciudad de Caseros", "Estudiantes (LP)"): "verificado"})
    otra = (_local("Estudiantes (BA)", "Otro Estadio", 20)
            + _local("Estudiantes (LP)", "Otro Estadio", 5))
    assert len(dataset.casas_compartidas(otra)) == 1


def test_los_alquileres_estan_documentados_y_citados():
    """La misma exigencia que `correcciones.py`: sin evidencia escrita y con link,
    esto es una lista de cosas barridas bajo la alfombra."""
    for (cancha, club), porque in dataset.ALQUILERES.items():
        assert len(porque) > 120, f"{cancha}/{club}: la evidencia es muy flaca"
        assert "http" in porque, f"{cancha}/{club}: falta el link a la fuente"
        assert "ANTES" in porque, (
            f"{cancha}/{club}: la regla es una cronica anterior al partido, que no "
            f"puede haber copiado de Wikipedia")


# --------------------------------------------------------------------------
# neutral: el torneo lo dice para todos, el partido para si mismo
# --------------------------------------------------------------------------
def _p(neutral=None):
    p = Partido(fecha="2014-12-14", local="Huracán", visita="Atlético Tucumán",
                goles_local=4, goles_visita=1, fase="eliminacion", jornada="Desempate")
    p.neutral = neutral
    return p


def test_si_el_partido_no_opina_manda_el_torneo():
    assert dataset.a_fila(_p(), "Primera Nacional", 2014, "u", False)["neutral"] == "false"
    assert dataset.a_fila(_p(), "Copa Argentina", 2014, "u", True)["neutral"] == "true"


def test_un_partido_neutral_dentro_de_un_torneo_que_no_lo_es():
    """El caso que abrio esto: el Desempate por el ascenso de 2014 se jugo en el
    Malvinas Argentinas de Mendoza, que no es de ninguno de los dos. El torneo no
    es neutral; ese partido si."""
    assert dataset.a_fila(_p(True), "Primera Nacional", 2014, "u", False)["neutral"] == "true"


def test_el_desempate_neutral_deja_de_contar_como_casa():
    """Y por eso `casas_compartidas` se calla: una cancha neutral no dice nada
    sobre la casa de nadie. Es el mismo motivo por el que el chequeo saltea las
    filas neutrales desde que existe."""
    filas = ([{"home_team": "Huracán", "venue": "Malvinas Argentinas", "neutral": "true"}]
             + _local("Huracán Las Heras", "Malvinas Argentinas", 5))
    assert dataset.casas_compartidas(filas) == []

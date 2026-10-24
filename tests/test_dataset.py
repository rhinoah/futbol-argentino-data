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


def test_la_pagina_se_recupera_tambien_cuando_el_source_nombra_tres():
    """UN `source` PUEDE TRAER DOS ` + `, y la pagina sigue siendo lo que va antes
    del PRIMERO. Son las llaves del Argentino A 2004-05: el partido sale de RSSSF y
    el dia se lo puso un blog, asi que nombran las tres cosas.

    Cortando por el ultimo separador la clave de reuso de esas 37 filas pasa a ser
    `pagina + RSSSF`, que no es la URL de ningun torneo: `build.main` reusa el
    torneo con las otras 80, lo ve achicarse y no escribe nada mas, ningun dia.
    Con dos partes los dos cortes dan lo mismo, y por eso no lo veia ningun test."""
    from fad import dataset
    url = "https://es.wikipedia.org/wiki/Torneo_Argentino_A_2004-05"
    fila = {"source": url + " + https://www.rsssf.org/ + http://josecarluccio.blogspot.com/"}
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


def test_se_puede_leer_un_csv_de_una_version_anterior(tmp_path):
    """El dia que se agrega una columna, los archivos que ya estan en disco no la
    tienen. `build.py` REUSA los torneos terminados leyendo ese mismo archivo, asi
    que rechazarlos dejaria sin dataset hasta que alguien corra un `--rehacer` a
    mano. Se completan vacias y se sigue."""
    viejo = tmp_path / "partidos-2020.csv"
    viejo.write_text(",".join(dataset.COLUMNAS[:-1]) + "\n"
                     + ",".join(["x"] * (len(dataset.COLUMNAS) - 1)) + "\n",
                     encoding="utf-8")
    filas = dataset.leer(viejo)
    assert len(filas) == 1
    assert filas[0][dataset.COLUMNAS[-1]] == ""


def test_un_encabezado_que_no_es_un_prefijo_sigue_siendo_un_error(tmp_path):
    """Se acepta que FALTEN columnas del final, no cualquier cosa: un CSV corrupto
    no se lee 'lo mejor posible', se rechaza."""
    roto = tmp_path / "partidos-2020.csv"
    roto.write_text("fecha,local,visitante\n1,2,3\n", encoding="utf-8")
    with pytest.raises(ValueError):
        dataset.leer(roto)


def test_el_status_del_partido_llega_a_la_fila():
    """De nada sirve detectarlo si no sale publicado: la columna existe para que
    el que consume el CSV pueda saber que ese marcador no salio de la cancha."""
    from fad.parser import Partido
    p = Partido(fecha="2018-05-04", local="Atlanta", visita="Colegiales",
                goles_local=1, goles_visita=0, status="escritorio")
    assert dataset.a_fila(p, "Primera B", 2017, "http://x")["status"] == "escritorio"
    normal = Partido(fecha="2018-05-04", local="A", visita="B", goles_local=1, goles_visita=0)
    assert dataset.a_fila(normal, "Primera B", 2017, "http://x")["status"] == ""


def test_una_temporada_que_se_queda_sin_filas_no_deja_su_archivo_viejo(tmp_path):
    """Sin esto el archivo sobrevive intacto y sigue publicando lo que ya no esta,
    mientras el build informa "sin cambios". Paso de verdad: al sacar
    La Florida - Sportivo Patria, el unico partido sin fecha que le quedaba al
    Argentino A 2005-06, `sin-fecha/` conservaba la fila igual."""
    f1 = fila("2005-10-30", "La Florida", "Sportivo Patria")
    f1["season"] = "2005"
    f2 = fila("2007-03-01", "Boca Juniors", "River Plate")
    f2["season"] = "2007"
    dataset.escribir_por_temporada([f1, f2], tmp_path)
    assert {p.name for p in tmp_path.glob("partidos-*.csv")} == {"partidos-2005.csv", "partidos-2007.csv"}
    cambiados = dataset.escribir_por_temporada([f2], tmp_path)
    assert {p.name for p in tmp_path.glob("partidos-*.csv")} == {"partidos-2007.csv"}
    assert cambiados.get("partidos-2005.csv") == 0, "el que se vacio tiene que aparecer como cambiado"


def test_una_baja_en_sin_fecha_se_puede_excusar():
    """`salvo` existe para un caso y conviene que quede fijado.

    En `sin-fecha/` una baja NO es una pérdida si el dataset principal creció para
    el mismo torneo: esos partidos consiguieron fecha y se mudaron. Sin la excusa,
    la guarda frena por una mejora — y frenar así no escribe NADA, ni siquiera lo
    que estaba bien, con lo cual desde afuera parece que no pasó nada.
    """
    def fila(t, s):
        return {"tournament": t, "season": s}

    antes = [fila("T", 2012)] * 28
    ahora = [fila("T", 2012)] * 8
    assert dataset.regresiones(ahora, antes), "sin excusa tiene que denunciarlo"
    assert not dataset.regresiones(ahora, antes, salvo=frozenset({("T", "2012")}))
    # Y la excusa es de esa clave nada más: otro torneo sigue denunciándose.
    otros = [fila("U", 2012)] * 5
    assert dataset.regresiones([], otros, salvo=frozenset({("T", "2012")}))


# --------------------------------------------------------------------------
# los partidos escritos dos veces
# --------------------------------------------------------------------------
from fad.correcciones import Copia  # noqa: E402

PB = "https://es.wikipedia.org/wiki/Primera_B"
FA = "https://es.wikipedia.org/wiki/Federal_A"


def _copia(fuente, **kw):
    f = {"date": "2021-02-04", "time": "", "home_team": "San Telmo",
         "away_team": "Deportivo Madryn", "home_score": "0", "away_score": "0",
         "home_pens": "3", "away_pens": "1", "tournament": "Primera B", "season": "2020",
         "phase": "eliminacion", "group": "", "matchday": "", "venue": "",
         "neutral": "false", "source": fuente, "status": ""}
    f.update(kw)
    return f


def _declarada(campo, valor):
    return Copia(fecha="2021-02-04", local="San Telmo", visita="Deportivo Madryn",
                 campo=campo, valor=valor, porque="test")


def test_alcanza_con_que_una_copia_diga_que_fue_neutral():
    fs = [_copia(PB), _copia(FA, neutral="true")]
    assert dataset.reconciliar_copias(fs) == []
    assert [f["neutral"] for f in fs] == ["true", "true"]


def test_ninguna_copia_lo_dice_y_queda_como_estaba():
    fs = [_copia(PB), _copia(FA)]
    dataset.reconciliar_copias(fs)
    assert [f["neutral"] for f in fs] == ["false", "false"]


def test_lo_que_una_copia_no_trae_se_toma_de_la_otra():
    fs = [_copia(PB), _copia(FA, time="21:30", venue="Marcelo Bielsa", status="suspendido")]
    assert dataset.reconciliar_copias(fs) == []
    for campo, valor in (("time", "21:30"), ("venue", "Marcelo Bielsa"),
                         ("status", "suspendido")):
        assert [f[campo] for f in fs] == [valor, valor], campo


def test_la_fila_recien_armada_trae_None_y_no_es_un_valor():
    """La copia que se acaba de parsear trae la tanda en None y el marcador en
    enteros; la del CSV, texto. Leidos tal cual, 0 y "0" serian dos marcadores."""
    fs = [_copia(PB, home_score=0, away_score=0, home_pens=3, away_pens=1),
          _copia(FA, time="21:30")]
    assert dataset.reconciliar_copias(fs) == []
    assert [f["time"] for f in fs] == ["21:30", "21:30"]
    sin_tanda = [_copia(PB, home_pens=None, away_pens=None),
                 _copia(FA, home_pens="", away_pens="")]
    assert dataset.reconciliar_copias(sin_tanda) == []


def test_dos_valores_distintos_no_se_eligen_solos():
    """El 2011-06-25 una pagina decia 15:00 y la otra 15:30. Elegir sin testigo es
    inventar: se avisa y cada copia sigue diciendo lo suyo."""
    fs = [_copia(PB, time="15:00"), _copia(FA, time="15:30")]
    avisos = dataset.reconciliar_copias(fs)
    assert [f["time"] for f in fs] == ["15:00", "15:30"]
    assert any("15:00 / 15:30" in a for a in avisos)


def test_la_declaracion_elige_entre_las_dos():
    fs = [_copia(PB, venue="Estadio Marcelo Bielsa"), _copia(FA, venue="Marcelo Bielsa")]
    assert dataset.reconciliar_copias(fs, (_declarada("venue", "Marcelo Bielsa"),)) == []
    assert [f["venue"] for f in fs] == ["Marcelo Bielsa", "Marcelo Bielsa"]


def test_la_declaracion_no_puede_inventar_un_valor():
    """Unificar no es reescribir: el valor tiene que ser uno de los que publican."""
    fs = [_copia(PB, venue="Estadio Marcelo Bielsa"), _copia(FA, venue="Marcelo Bielsa")]
    avisos = dataset.reconciliar_copias(fs, (_declarada("venue", "Coloso del Parque"),))
    assert [f["venue"] for f in fs] == ["Estadio Marcelo Bielsa", "Marcelo Bielsa"]
    assert any("no se aplica" in a for a in avisos)


def test_la_tanda_no_se_toca():
    """Y no frena lo demas: con el mismo marcador es el mismo partido, y que una
    pagina no traiga la tanda no cambia a que hora se jugo."""
    fs = [_copia(PB, home_pens="", away_pens=""), _copia(FA, time="21:30")]
    avisos = dataset.reconciliar_copias(fs)
    assert [(f["home_pens"], f["away_pens"]) for f in fs] == [("", ""), ("3", "1")]
    assert any("home_pens" in a for a in avisos)
    assert [f["time"] for f in fs] == ["21:30", "21:30"]


def test_con_otro_marcador_no_se_unifica_nada():
    """La clave es lo unico que dice que las dos filas son el mismo partido, y el
    marcador el unico control. Unificando igual, una fila con el 1-1 de la cancha
    quedaba rotulada `escritorio` porque la otra publicaba el fallo."""
    fs = [_copia(PB, home_score="1", away_score="1"),
          _copia(FA, home_score="0", away_score="3", status="escritorio", time="17:00",
                 venue="Estadio A", neutral="true")]
    antes = [dict(f) for f in fs]
    avisos = dataset.reconciliar_copias(fs)
    assert fs == antes
    assert any("home_score" in a for a in avisos)
    assert any("No se unifica nada" in a for a in avisos)


def test_lo_que_es_de_cada_torneo_no_se_toca():
    fs = [_copia(PB, tournament="Primera B"),
          _copia(FA, tournament="Torneo Federal A", matchday="Tercer ascenso")]
    dataset.reconciliar_copias(fs)
    assert [(f["tournament"], f["matchday"]) for f in fs] == [
        ("Primera B", ""), ("Torneo Federal A", "Tercer ascenso")]


def test_dos_filas_de_la_misma_pagina_no_son_copias():
    """Eso es un partido leido dos veces, y lo frena `validar.sin_duplicados`."""
    fs = [_copia(PB), _copia(PB, neutral="true", time="21:30")]
    assert dataset.copias(fs) == {}
    dataset.reconciliar_copias(fs)
    assert [(f["neutral"], f["time"]) for f in fs] == [("false", ""), ("true", "21:30")]


def test_la_declaracion_que_sobra_se_dice_solo_con_las_dos_paginas_releidas():
    """Lo reusado del CSV ya viene unificado de ayer: ahi coinciden POR la
    declaracion, y decir que sobra seria mentir."""
    d = (_declarada("venue", "Marcelo Bielsa"),)

    def iguales():
        return [_copia(PB, venue="Marcelo Bielsa"), _copia(FA, venue="Marcelo Bielsa")]

    assert any("sobra" in a for a in dataset.reconciliar_copias(iguales(), d, frozenset({PB, FA})))
    assert dataset.reconciliar_copias(iguales(), d) == []


def test_una_declaracion_sin_sus_dos_copias_avisa():
    avisos = dataset.reconciliar_copias([_copia(PB)], (_declarada("venue", "X"),))
    assert any("no encuentra" in a for a in avisos)


def test_la_declaracion_de_otro_dia_no_es_de_este_partido():
    """Los mismos clubes se cruzan en la ida y en la vuelta: la fecha es parte de la
    clave, y una declaracion de otro dia no elige nada aca."""
    fs = [_copia(PB, venue="Estadio Marcelo Bielsa"), _copia(FA, venue="Marcelo Bielsa")]
    otro_dia = Copia(fecha="2021-02-07", local="San Telmo", visita="Deportivo Madryn",
                     campo="venue", valor="Marcelo Bielsa", porque="test")
    avisos = dataset.reconciliar_copias(fs, (otro_dia,))
    assert [f["venue"] for f in fs] == ["Estadio Marcelo Bielsa", "Marcelo Bielsa"]
    assert any("no encuentra" in a for a in avisos)


def test_una_copia_releida_no_se_completa_con_la_del_csv():
    """Lo de la copia reusada puede haber salido de una version vieja de la pagina
    que hoy se relee: copiarselo de vuelta la dejaria diciendo lo que ya no publica
    nadie. Cada una sigue a su pagina, y se avisa."""
    fs = [_copia(PB, time="21:30", neutral="true"), _copia(FA)]
    avisos = dataset.reconciliar_copias(fs, (), frozenset({FA}))
    assert [(f["time"], f["neutral"]) for f in fs] == [("21:30", "true"), ("", "false")]
    assert any("se releyo" in a and "neutral, time" in a for a in avisos)
    # Releidas las dos, la misma pareja si se unifica.
    assert dataset.reconciliar_copias(fs, (), frozenset({PB, FA})) == []
    assert [(f["time"], f["neutral"]) for f in fs] == [("21:30", "true")] * 2


def test_reconciliar_dos_veces_es_reconciliar_una():
    """Lo que garantiza que el bot no mueva nunca lo cerrado: sobre filas ya
    reconciliadas la regla no cambia nada."""
    fs = [_copia(PB, venue="Estadio Marcelo Bielsa"),
          _copia(FA, time="21:30", venue="Marcelo Bielsa", neutral="true")]
    d = (_declarada("venue", "Marcelo Bielsa"),)
    dataset.reconciliar_copias(fs, d)
    antes = [dict(f) for f in fs]
    assert dataset.reconciliar_copias(fs, d) == []
    assert fs == antes


# --------------------------------------------------------------------------
# nadie juega dos dias seguidos
# --------------------------------------------------------------------------
def _jugado(fecha, local, visita, fuente=PB):
    return _copia(fuente, date=fecha, home_team=local, away_team=visita,
                  tournament="Primera Division - Clausura", season="1994",
                  matchday="Fecha 7")


def test_dos_partidos_en_dias_seguidos_es_aviso():
    """Belgrano en el Clausura 1994: el 5 de mayo contra Velez y el 6 contra River.
    Uno de los dos dias esta mal."""
    filas = [_jugado("1994-05-05", "Belgrano", "Vélez Sarsfield"),
             _jugado("1994-05-06", "River Plate", "Belgrano")]
    (aviso,) = dataset.dias_seguidos(filas)
    assert aviso.startswith(
        "Belgrano juega dos partidos en dias seguidos: 1994-05-05 Belgrano 0-0 Vélez "
        "Sarsfield (Primera Division - Clausura 1994, Fecha 7) y 1994-05-06 River Plate")


def test_dos_partidos_distintos_el_mismo_dia_tambien():
    filas = [_jugado("1994-05-05", "Belgrano", "Vélez Sarsfield"),
             _jugado("1994-05-05", "River Plate", "Belgrano")]
    (aviso,) = dataset.dias_seguidos(filas)
    assert aviso.startswith("Belgrano juega dos partidos el mismo dia")


def test_a_dos_dias_no_es_aviso():
    """A dos dias hay 117 pares en lo publicado; a uno, dos."""
    filas = [_jugado("1994-05-05", "Belgrano", "Vélez Sarsfield"),
             _jugado("1994-05-07", "River Plate", "Belgrano")]
    assert dataset.dias_seguidos(filas) == []


def test_el_partido_que_publican_dos_paginas_es_uno_solo():
    """Las `copias`: una promocion, en la pagina de cada division. Sin saltearla,
    los dos clubes jugaban dos partidos el mismo dia."""
    fs = [_copia(PB), _copia(FA)]
    assert len(dataset.copias(fs)) == 1
    assert dataset.dias_seguidos(fs) == []


def test_y_saltear_la_copia_no_tapa_el_partido_del_dia_siguiente():
    fs = [_copia(PB), _copia(FA), _jugado("2021-02-05", "Atlanta", "San Telmo")]
    (aviso,) = dataset.dias_seguidos(fs)
    assert aviso.startswith("San Telmo juega dos partidos en dias seguidos: 2021-02-04")


def test_una_fila_sin_fecha_o_con_una_que_no_existe_no_se_cuenta():
    """No se pueden restar. Y no tumban el build: corre todos los dias."""
    filas = [_jugado("", "Belgrano", "Vélez Sarsfield"),
             _jugado("1994-06-31", "Belgrano", "Boca Juniors"),
             _jugado("1994-07-01", "River Plate", "Belgrano")]
    assert dataset.dias_seguidos(filas) == []


# ---- sobre lo publicado ------------------------------------------------------
from pathlib import Path  # noqa: E402

DATOS = Path(__file__).resolve().parent.parent / "data"
_DEL_PARTIDO = ("date", "time", "home_score", "away_score", "home_pens", "away_pens",
                "venue", "neutral", "status")


def _desacuerdos(grupos: dict) -> list[str]:
    return [f"{k[0]} {k[1]} - {k[2]}: {c} = {sorted({f[c] for f in fs})}"
            for k, fs in sorted(grupos.items()) for c in _DEL_PARTIDO
            if len({f[c] for f in fs}) > 1]


def _cerradas(filas) -> dict:
    from fad import torneos
    cerradas = {t.url for t in torneos.TODOS if t.cerrado}
    return {k: fs for k, fs in dataset.copias(filas).items()
            if all(dataset.pagina_de(f) in cerradas for f in fs)}


@pytest.fixture(scope="module")
def publicadas():
    filas = dataset.leer_carpeta(DATOS)
    if not filas:
        pytest.skip("hace falta el dataset")
    return _cerradas(filas)


def test_los_partidos_escritos_dos_veces_dicen_lo_mismo_en_los_torneos_cerrados(publicadas):
    """La regla corre todos los dias pero solo AVISA, para que una pagina en curso
    no frene al resto. Esto es lo que frena, y mira solo torneos CERRADOS: el bot no
    los toca --se reusan del CSV y la regla, sobre filas ya reconciliadas, no cambia
    nada--, asi que la corrida diaria no lo puede hacer fallar. Falla el dia que
    alguien cierra un torneo con una copia en desacuerdo, que es cuando hay que
    mirarlo."""
    assert len(publicadas) >= 15, f"son 15 y encontro {len(publicadas)}: no esta mirando"
    assert not _desacuerdos(publicadas)


def test_lo_declarado_es_lo_que_se_publica(publicadas):
    """Una declaracion se aplica al rehacer, y el CSV publicado es lo que queda de
    eso. Si se cambia una sin rehacer, o se rehace sin ella, se nota aca. Mira solo
    las de torneos cerrados, por lo mismo que el test de arriba: las de un torneo en
    curso las aplica el bot DESPUES de correr la suite."""
    from fad import correcciones
    vistas = 0
    for d in correcciones.COPIAS:
        fs = publicadas.get((d.fecha, d.local, d.visita))
        if fs is None:
            continue
        vistas += 1
        assert [f[d.campo] for f in fs] == [d.valor] * len(fs), (d.fecha, d.local, d.campo)
    assert vistas >= 3, "las tres de hoy son de torneos cerrados: si no las ve, no mira"


def test_y_lo_veria_si_una_copia_cerrada_dijera_otra_hora(publicadas):
    k = ("2021-02-04", "San Telmo", "Deportivo Madryn")
    copia = {k: [dict(f) for f in publicadas[k]]}
    copia[k][0]["time"] = "23:59"
    assert _desacuerdos(copia)


@pytest.mark.parametrize("clave, campo, valor", [
    # La AFA, nota del 24/06/2011 «Esta tarde juegan Los Andes y Central Córdoba»:
    # «Sábado 25 de junio 15.00-- Los Andes-Central Córdoba». Ver correcciones.COPIAS.
    (("2011-06-25", "Los Andes", "Central Córdoba (R)"), "time", "15:00"),
    # UNO Santa Fe, 4/02/2021: «se jugará a partir de las 21.30 en el estadio de
    # Newell's Old Boys», que no es la cancha de ninguno de los dos.
    (("2021-02-04", "San Telmo", "Deportivo Madryn"), "time", "21:30"),
    (("2021-02-04", "San Telmo", "Deportivo Madryn"), "venue", "Marcelo Bielsa"),
    (("2021-02-04", "San Telmo", "Deportivo Madryn"), "neutral", "true"),
    # Cadena 3, 18/12/2024: «Se enfrentarán este sábado a las 17 en el estadio Julio
    # César Villagra». Las dos paginas lo escriben con `{{Partidos}}`, en `fecha`.
    (("2024-12-21", "Sarmiento (LB)", "Los Andes"), "time", "17:00"),
    # Sitio Andino: «una final que se desarrolló en el estadio de Belgrano de Córdoba».
    # Las dos paginas lo dicen en la seccion del partido: «en estadio neutral».
    (("2024-12-21", "Sarmiento (LB)", "Los Andes"), "neutral", "true"),
])
def test_lo_que_dicen_las_dos_copias_lo_dice_un_testigo_de_afuera(publicadas, clave, campo,
                                                                   valor):
    """Que coincidan no alcanza: dos copias pueden coincidir en lo equivocado. Estos
    valores los decide un testigo que no es ninguna de las dos paginas, y se los
    escribe aca para que una fuente de afuera los pueda contradecir."""
    assert [f[campo] for f in publicadas[clave]] == [valor, valor]


def test_los_partidos_declarados_neutrales_salen_neutrales():
    """Lo mismo que `test_lo_declarado_es_lo_que_se_publica`, para
    `correcciones.NEUTRALES`: se aplican al rehacer, y el CSV es lo que queda, con el
    valor declarado -- `true`, o `false` para los de local --. Mira solo los torneos
    cerrados; los de uno en curso los aplica el bot despues de la suite."""
    from fad import correcciones, torneos
    filas = dataset.leer_carpeta(DATOS)
    if not filas:
        pytest.skip("hace falta el dataset")
    cerradas = {t.pagina: t.url for t in torneos.TODOS if t.cerrado}
    por_partido: dict[tuple, list] = {}
    for f in filas:
        k = (dataset.pagina_de(f), f["date"], f["home_team"], f["away_team"],
             f["home_score"], f["away_score"])
        por_partido.setdefault(k, []).append(f["neutral"])
    vistas = 0
    for n in correcciones.NEUTRALES:
        if n.pagina not in cerradas:
            continue
        local, visita, gl, gv = n.dice
        k = (cerradas[n.pagina], n.fecha, local, visita, str(gl), str(gv))
        assert por_partido.get(k) == [str(n.neutral).lower()], (n.pagina, n.fecha, local,
                                                                 visita)
        vistas += 1
    assert vistas >= 75, f"son 75 de torneos cerrados y vio {vistas}: no esta mirando"


@pytest.fixture(scope="module")
def todas():
    filas = dataset.leer_carpeta(DATOS)
    if not filas:
        pytest.skip("hace falta el dataset")
    return {(f["date"], f["home_team"], f["away_team"]): f for f in filas}


@pytest.mark.parametrize("clave, campo, valor", [
    # La nota de la fila: «se disputó el 21 de noviembre, a partir de las 18:30». La
    # celda ya decia el 21, con las 11:00 del domingo de la lluvia (La Nueva,
    # 28/10/2012: «debía iniciarse a las 11»).
    (("2012-11-21", "Crucero del Norte", "Rosario Central"), "time", "18:30"),
    # Una `Dia`: «Se juega el miércoles 3 de octubre a las 21:35 horas», y la cronica
    # de Ascenso del Interior del 04/10/2012 lo cuenta jugado «esta noche».
    (("2012-10-03", "Central Norte (S)", "Juventud Antoniana"), "time", "21:35"),
    # Una `Dia`: el comunicado de la Liga, La Capital 01/11/2020, «martes 03.11.2020
    # a las 21»; las 21:15 eran las del domingo programado.
    (("2020-11-03", "River Plate", "Banfield"), "time", "21:00"),
    # Una `Dia`: la programacion de la AFA y La Nueva del 22/06/2013, «consiguió hoy
    # el segundo ascenso». La pagina dice el 23.
    (("2013-06-22", "Almagro", "Brown de Adrogué"), "time", "12:05"),
])
def test_lo_que_fija_un_testigo_de_afuera_esta_publicado(todas, clave, campo, valor):
    """Una correccion a mano que se cae, o una regla que cambia, mueven estas filas
    sin que ningun otro test lo note: el dato correcto lo dice una fuente de afuera."""
    assert clave in todas, f"no esta {clave}: ¿se movio el dia?"
    assert todas[clave][campo] == valor, (clave, campo)


def test_cada_dia_declarado_es_el_que_se_publica(todas):
    """Una `Dia` de un torneo cerrado se aplica al rehacer, y lo publicado es lo que
    queda de eso: la fila esta en el dia que la declaracion dice que es el bueno, y
    con su hora si la declara. Si alguien cambia una sin rehacer, se nota aca."""
    from fad import correcciones, torneos
    cerradas = {t.pagina: t.url for t in torneos.TODOS if t.cerrado}
    vistas = 0
    for d in correcciones.DIAS:
        if d.pagina not in cerradas:
            continue
        f = todas.get((d.debe, d.local, d.visita))
        assert f is not None, f"{d.pagina}: no esta {d.local} - {d.visita} del {d.debe}"
        if d.hora is not None:
            assert f["time"] == d.hora, (d.pagina, d.debe, d.local)
        vistas += 1
    assert vistas >= 20, f"vio {vistas} Dia de torneos cerrados: no esta mirando"

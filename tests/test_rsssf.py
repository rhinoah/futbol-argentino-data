#!/usr/bin/env python3
"""Tests del lector de RSSSF.

Es una fuente de texto plano de columnas fijas, y las tres veces que fallo al
escribirlo fallo en silencio: no rompio nada, solo dejo partidos sin fechar. Por
eso lo que se prueba aca es sobre todo que NO se pierda una fila y que no se
invente un club.
"""
from __future__ import annotations

from fad import rsssf

MAPA = {
    "Zona A - Sur": {
        "Sportivo Desamparados": "Desamparados",
        "Villa Mitre": "Villa Mitre",
        "Juventud Unida Universitario": "Juventud Unida Universitario",
        "Racing": "Racing (O)",
        "La Plata FC": "La Plata FC",
        "Cipolletti": "Cipolletti",
        "Guillermo Brown": "Guillermo Brown",
    },
    "Zona B - Norte": {
        "Racing": "Racing (C)",
        "Talleres": "Talleres (P)",
        "Ñuñorco": "Ñuñorco",
        "Gimnasia y Esgrima": "Gimnasia y Esgrima (CdU)",
    },
}


def leer(texto):
    return rsssf.leer(texto, MAPA, 2005, 2006, 8)


def test_la_fecha_va_en_el_encabezado_de_la_ronda():
    ajenos, avisos = leer("Torneo Apertura\n"
                          "Zona A - Sur\n"
                          "Round 1 [Aug 21]\n"
                          "Sportivo Desamparados        0-1 Villa Mitre\n")
    assert avisos == []
    assert len(ajenos) == 1
    a = ajenos[0]
    assert (a.fecha, a.jornada, a.local, a.visita) == ("2005-08-21", 1, "Desamparados", "Villa Mitre")
    assert (a.goles_local, a.goles_visita) == (0, 1)


def test_una_jornada_partida_en_dos_dias_fecha_cada_partido_por_separado():
    """Es el motivo entero por el que sirve esta fuente. En el ascenso argentino
    solo el 19% de las jornadas se juega en un solo dia, asi que una fecha por
    jornada dejaria mal el 41% de los partidos."""
    ajenos, _ = leer("Torneo Apertura\n"
                     "Zona A - Sur\n"
                     "Round 2\n"
                     "[Aug 27]\n"
                     "La Plata FC                  2-0 Cipolletti\n"
                     "[Aug 28]\n"
                     "Guillermo Brown              2-0 Sportivo Desamparados\n")
    assert [a.fecha for a in ajenos] == ["2005-08-27", "2005-08-28"]


def test_el_club_de_28_letras_no_se_pierde():
    """El marcador arranca en la columna 29 fija y "Juventud Unida Universitario"
    mide 28: le queda UN espacio. Con un separador de dos o mas espacios se
    perdian sus doce partidos de local, todos del mismo club y de a bloques."""
    ajenos, _ = leer("Torneo Apertura\n"
                     "Zona A - Sur\n"
                     "Round 2 [Aug 27]\n"
                     "Juventud Unida Universitario 3-1 Racing\n")
    assert len(ajenos) == 1
    assert ajenos[0].local == "Juventud Unida Universitario"
    assert ajenos[0].visita == "Racing (O)"


def test_la_anotacion_que_se_derrama_sobre_el_partido_de_abajo():
    """La cola de un `[abandoned at ...` cae en la linea siguiente, que es un
    partido de verdad. Sin cortar el visitante en la proxima corrida de dos
    espacios, ese partido se perdia."""
    ajenos, avisos = leer("Torneo Apertura\n"
                          "Zona B - Norte\n"
                          "Round 9 [Oct 30]\n"
                          "Gimnasia y Esgrima           5-2 Ñuñorco                  in 90', awarded\n")
    assert avisos == [], "el visitante tiene que quedar limpio"
    assert len(ajenos) == 1 and ajenos[0].visita == "Ñuñorco"


def test_la_continuacion_entre_corchetes_no_es_un_partido():
    ajenos, _ = leer("Torneo Apertura\n"
                     "Zona B - Norte\n"
                     "Round 9 [Oct 30]\n"
                     "Ñuñorco                      1-2 Talleres     [abandoned at 2-1 in 85',\n"
                     "                                               awarded 0-1 against both]\n")
    assert len(ajenos) == 1
    assert (ajenos[0].local, ajenos[0].visita) == ("Ñuñorco", "Talleres (P)")


def test_el_mismo_nombre_en_dos_zonas_son_dos_clubes():
    """"Racing" es el de Olavarria en la Zona Sur y el de Cordoba en la Norte, en
    el MISMO torneo. Resolverlo por el padron devuelve Racing Club, el de
    Avellaneda, que nunca jugo el Argentino A: no falla, apunta a otro lado."""
    sur, _ = leer("Torneo Apertura\nZona A - Sur\nRound 1 [Aug 21]\n"
                  "Racing                       0-2 Villa Mitre\n")
    norte, _ = leer("Torneo Apertura\nZona B - Norte\nRound 1 [Aug 21]\n"
                    "Racing                       0-2 Talleres\n")
    assert sur[0].local == "Racing (O)"
    assert norte[0].local == "Racing (C)"


def test_un_nombre_que_el_mapa_no_traduce_se_denuncia_y_no_se_empareja():
    """No se empareja por parecido y no se saltea callado: sin el aviso, el
    partido que se derramaba con la anotacion se habria perdido sin dejar rastro."""
    ajenos, avisos = leer("Torneo Apertura\nZona A - Sur\nRound 1 [Aug 21]\n"
                          "Sportivo Desamparados        0-1 Club Inventado\n")
    assert ajenos == []
    assert len(avisos) == 1 and "Club Inventado" in avisos[0]


def test_una_zona_que_no_esta_en_el_mapa_se_ignora_entera():
    """Los playoffs mezclan las dos zonas, y ahi un nombre corto deja de
    identificar a un club."""
    ajenos, avisos = leer("Torneo Apertura\nSecond Phase\nRound 1 [Dec 4]\n"
                          "Racing                       0-2 Villa Mitre\n")
    assert ajenos == [] and avisos == []


def test_la_llave_separa_dos_torneos_con_la_misma_numeracion():
    """El Apertura y el Clausura numeran los dos del 1 al 11. Sin la llave,
    "Fecha 5 Douglas Haig vs Cipolletti" es una casilla para dos partidos."""
    ajenos, _ = leer("Torneo Apertura\nZona A - Sur\nRound 5 [Sep 25]\n"
                     "La Plata FC                  1-1 Villa Mitre\n"
                     "Torneo Clausura\nZona A - Sur\nRound 5 [Feb 12]\n"
                     "La Plata FC                  1-1 Villa Mitre\n")
    assert [a.llave for a in ajenos] == ["Torneo Apertura", "Torneo Clausura"]
    assert [a.fecha for a in ajenos] == ["2005-09-25", "2006-02-12"]


def test_el_anio_sale_del_mes_porque_la_temporada_cruza_el_calendario():
    ajenos, _ = leer("Torneo Clausura\nZona A - Sur\nRound 1 [Feb 12]\n"
                     "La Plata FC                  1-1 Villa Mitre\n")
    assert ajenos[0].fecha == "2006-02-12"


def test_una_fecha_suelta_no_cruza_de_una_seccion_a_la_siguiente():
    """Si `[Aug 27]` sobreviviera al cambio de zona, el primer partido de la zona
    siguiente se llevaria una fecha que no es la suya."""
    ajenos, _ = leer("Torneo Apertura\nZona A - Sur\nRound 2\n[Aug 27]\n"
                     "La Plata FC                  2-0 Cipolletti\n"
                     "Zona B - Norte\n"
                     "Ñuñorco                      1-0 Talleres\n")
    assert len(ajenos) == 1, "el de la Zona Norte no tiene fecha propia y no entra"


def test_la_pagina_se_lee_como_latin1_y_no_como_utf8(monkeypatch, tmp_path):
    """RSSSF no declara charset y NO es UTF-8. Leyendola como UTF-8, "Luján de
    Cuyo" y "Ñuñorco" llegan rotos y no cruzan con el padron: el partido se
    pierde y el aviso denuncia un club que no existe.

    El decode vive dentro de `descargar`, asi que hay que entrar por ahi. Se
    monkeypatchea la red, no se sale a internet: un test que depende de que RSSSF
    este arriba no prueba el parseo, prueba internet."""
    import io as _io
    import urllib.request
    crudo = "Ñuñorco vs Luján de Cuyo".encode("latin-1")

    class Respuesta(_io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    monkeypatch.setattr(rsssf, "_CACHE", tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", lambda *a, **k: Respuesta(crudo))
    assert rsssf.descargar("loquesea") == "Ñuñorco vs Luján de Cuyo"


def test_lo_descargado_queda_cacheado_y_no_se_vuelve_a_pedir(monkeypatch, tmp_path):
    import io as _io
    import urllib.request
    llamadas = []

    class Respuesta(_io.BytesIO):
        def __enter__(self): return self
        def __exit__(self, *a): return False

    def espiar(*a, **k):
        llamadas.append(1)
        return Respuesta("Round 1 [Aug 21]".encode("latin-1"))

    monkeypatch.setattr(rsssf, "_CACHE", tmp_path)
    monkeypatch.setattr(urllib.request, "urlopen", espiar)
    rsssf.descargar("arg3-int06")
    rsssf.descargar("arg3-int06")
    assert len(llamadas) == 1

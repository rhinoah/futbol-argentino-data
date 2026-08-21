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


def test_el_dia_entre_parentesis_es_un_dia():
    """2007-08 escribe TODAS sus fechas asi, y 2006-07 una sola.

    Lo que hace falta probar no es que la reconozca sino que el partido de abajo
    no se quede con la fecha anterior: no reconocerla no lo deja afuera, le pone
    una fecha que no es, que es la unica de las dos formas de fallar que despues
    no se nota.
    """
    ajenos, _ = leer("Torneo Apertura\nZona A - Sur\nRound 10\n[Oct 15]\n"
                     "La Plata FC                  2-0 Cipolletti\n"
                     "(Oct 16)\n"
                     "Villa Mitre                  1-0 Guillermo Brown\n")
    assert [a.fecha for a in ajenos] == ["2005-10-15", "2005-10-16"]


def test_la_ronda_tambien_trae_el_dia_entre_parentesis():
    ajenos, _ = leer("Torneo Apertura\nZona A - Sur\nRound 1 (Aug 24)\n"
                     "La Plata FC                  2-0 Cipolletti\n")
    assert [a.fecha for a in ajenos] == ["2005-08-24"]


# --------------------------------------------------------------------------
# el marcador que no es un marcador
#
# Las lineas de esta seccion estan copiadas TAL CUAL de RSSSF, con su sangria y
# sus columnas, porque lo que se prueba es justamente que se lean columnas.
# --------------------------------------------------------------------------
MAPA_C = {
    "Zona C": {
        "La Florida": "La Florida",
        "Talleres (P)": "Talleres (P)",
        "Atl. Tucumán": "Atlético Tucumán",
        "Sp. Patria": "Sportivo Patria",
        "9 de Julio": "9 de Julio (R)",
        "Central Norte": "Central Norte (S)",
    },
}


def leer_c(texto):
    return rsssf.leer(texto, MAPA_C, 2006, 2007, 8)


def test_un_marcador_que_no_es_un_marcador_no_se_saltea_en_silencio():
    """`abd` con el resultado firme es un partido, y entraba en ninguna parte.

    Se venia salteando en silencio, que es la cuarta vez que este modulo falla de
    la misma forma. Son diez lineas asi en las cuatro temporadas de RSSSF, y dos
    de ellas eran partidos que al dataset le faltaban de verdad.
    """
    ajenos, avisos = leer_c(
        "Zona C\n"
        "Round 11 [Oct 22]\n"
        "La Florida               abd Talleres (P)             [abandoned at 3-2 in 88';\n"
        "Sp. Patria               3-1 9 de Julio                result stood]\n")
    assert len(ajenos) == 2, "tienen que entrar los dos, no uno"
    abd = [a for a in ajenos if a.local == "La Florida"][0]
    assert (abd.goles_local, abd.goles_visita) == (3, 2)
    assert abd.status == "suspendido", "no llego al final, y eso es lo que la fuente dice"
    assert abd.fecha == "2006-10-22"
    assert any("entra 3-2" in a for a in avisos), "y ademas lo tiene que decir"


def test_el_parentesis_del_nombre_de_un_club_no_abre_la_nota():
    """"Talleres (P)" trae un parentesis antes de la nota, y la nota es lo que
    decide si el partido entra y con que marcador. Leyendo desde el primer
    parentesis, la nota resultaba ser "(P)" y el partido se caia."""
    _, avisos = leer_c(
        "Zona C\n"
        "Round 11 [Oct 22]\n"
        "La Florida               abd Talleres (P)             [abandoned at 3-2 in 88';\n"
        "Sp. Patria               3-1 9 de Julio                result stood]\n")
    assert not any("(P)             [" in a for a in avisos), "se comio el nombre"


def test_la_nota_puede_empezar_en_la_linea_de_abajo():
    """Y ahi convive con lo que esa linea tenga por su cuenta."""
    ajenos, avisos = leer_c(
        "Zona C\n"
        "Round 14\n"
        "[Nov 11]\n"
        "Atl. Tucumán             awd Talleres (P)             [awarded 0-1; abandoned\n"
        "[Nov 12]                                                at 3-0 in 72']\n")
    assert len(ajenos) == 1
    a = ajenos[0]
    assert (a.goles_local, a.goles_visita) == (0, 1), "el marcador es el del fallo"
    # Y el status sale del mismo eje que `parser.status_de_la_fila`, con su misma
    # precedencia: NO LLEGAR AL FINAL manda sobre el fallo.
    assert a.status == "suspendido"


def test_el_fallo_contra_los_dos_clubes_no_entra_y_se_dice():
    """Dos resultados para un partido no caben en una fila. La linea no se ignora:
    se nombra, para que la decision quede escrita y no parezca un olvido."""
    ajenos, avisos = leer_c(
        "Zona C\n"
        "Round 14 [Apr 29]\n"
        "Central Norte            awd 9 de Julio\n"
        "  [awarded 0-1 loss to both; originally 1-1; both teams to start with\n"
        "   -6 points 2007/08]\n")
    assert ajenos == []
    assert any("NO entra" in a and "DOS clubes" in a for a in avisos)


def test_un_abandonado_sin_resultado_firme_no_entra():
    """Si no dice que el resultado quedo firme, lo mas probable es que se haya
    completado despues -- y esa fila, la del partido completo, es la que entra."""
    ajenos, avisos = leer_c(
        "Zona C\n"
        "Round 1\n"
        "[Jan 26]\n"
        "Atl. Tucumán             abd La Florida               [abandoned at 1-1 in 42']\n"
        "[Jan 29]\n"
        "Atl. Tucumán             1-1 La Florida               [remaining 48']\n")
    assert len(ajenos) == 1, "entra el completo y no el abandonado"
    assert ajenos[0].fecha == "2007-01-29"
    assert any("NO entra" in a for a in avisos)


def test_la_prosa_con_forma_de_partido_no_es_un_partido():
    """El token va suelto -- cualquier palabra corta -- y lo que hace segura esa
    laxitud es exigir que los DOS flancos traduzcan por el mapa de la zona. RSSSF
    esta lleno de lineas con forma de partido que son prosa."""
    ajenos, avisos = leer_c(
        "Zona C\n"
        "Round 11 [Oct 22]\n"
        "La Florida               and Talleres (P)             to overall semifinals\n"
        "Sp. Patria               vs 9 de Julio                is not a match either\n"
        "Douglas Haig             and Villa Mitre              to overall semifinals\n")
    assert ajenos == []
    assert avisos == [], "y ni siquiera tiene que avisar: no son partidos"


def test_la_cancha_prestada_no_es_parte_del_nombre():
    """RSSSF pone la sede aparte cuando se juega fuera de casa. Con dos espacios
    el separador la deja afuera sola, pero si el club YA termina en parentesis
    queda pegada a uno: `Gimnasia y Esgr. (CdU) (at Huracán-C)`. Sin despegarla el
    mismo club entra como tres, y ninguno de los tres esta en el padron, asi que
    sus partidos se caen del cruce sin ruido."""
    mapa = {"Group A": {"La Plata FC": "La Plata FC",
                        "Gimnasia y Esgr. (CdU)": "Gimnasia y Esgrima (CdU)"}}
    ajenos, _ = rsssf.leer(
        "Group A\nRound 1 (Aug 21)\n"
        "La Plata FC               2-0 Gimnasia y Esgr. (CdU) (at Huracán-C)\n"
        "La Plata FC               1-1 Gimnasia y Esgr. (CdU)   (at Libertad)\n",
        mapa, 2007, 2008, 8)
    assert len(ajenos) == 2, "los dos son del mismo club, con y sin dos espacios"
    assert {a.visita for a in ajenos} == {"Gimnasia y Esgrima (CdU)"}


def test_el_interzonal_tambien_viene_como_encabezado():
    """En 2008-09 el marcador cuelga de la ronda -- `Round 21 [interzonal 1-2]` --
    y en 2007-08 es un encabezado propio, `Interzonal Group A-B`, seguido de su
    ronda. Las dos formas dicen lo mismo: esa ronda pertenece a los dos grupos y
    RSSSF la imprime bajo los dos, asi que se lee una sola vez.

    Y vale para UNA ronda: la que viene despues del bloque es normal, y si el
    marcador sobreviviera se saltearia bajo el segundo grupo del par.
    """
    mapa = {g: {"La Plata FC": "La Plata FC", "Villa Mitre": "Villa Mitre"}
            for g in ("Group A", "Group B")}
    texto = ("Group A\nInterzonal Group A-B\nRound 5 (Sep 15)\n"
             "La Plata FC                  2-0 Villa Mitre\n"
             "Round 6 (Sep 23)\n"
             "Villa Mitre                  1-1 La Plata FC\n"
             "Group B\nInterzonal Group A-B\nRound 5 (Sep 15)\n"
             "La Plata FC                  2-0 Villa Mitre\n")
    ajenos, _ = rsssf.leer(texto, mapa, 2007, 2008, 8)
    assert len(ajenos) == 2, "el interzonal entra una vez, la ronda normal tambien"
    assert sorted(a.jornada for a in ajenos) == [5, 6]
    assert all(a.zona == "Group A" for a in ajenos)


def test_la_zona_tambien_se_escribe_en_ingles():
    """RSSSF pone "Zona" en unas temporadas y "Zone" en otras: el Argentino A
    2008-09 usa `Zone 1`, `Zone 2` y `Zone 3`. Sin reconocerlo no son encabezados
    de nada, y la temporada entera -- 400 partidos -- entra en cero y sin ruido,
    que es como este modulo fallo las cuatro veces anteriores."""
    mapa = {"Zone A": {"La Plata FC": "La Plata FC", "Villa Mitre": "Villa Mitre"}}
    ajenos, _ = rsssf.leer(
        "Zone A\nRound 1 [Aug 21]\n"
        "La Plata FC                  2-0 Villa Mitre\n", mapa, 2005, 2006, 8)
    assert len(ajenos) == 1 and ajenos[0].zona == "Zone A"


def test_la_llave_tambien_viene_escrita_sin_la_palabra_torneo():
    """RSSSF rotula "Torneo Apertura" en una temporada y "Apertura 2006" en otra.

    No es cosmetico: el Argentino A 2006-07 corre las dos mitades sobre LAS MISMAS
    zonas, numerando las dos del 1 al 14. Sin reconocer la forma pelada, las dos
    caen en la misma casilla y cada zona termina con el doble de partidos por
    fecha. Se normaliza al nombre largo porque el cruce contra la tabla de
    Wikipedia agrupa por llave, y dos vocabularios no cruzan.
    """
    ajenos, _ = leer("Apertura 2005\nZona A - Sur\nRound 5 [Sep 25]\n"
                     "La Plata FC                  1-1 Villa Mitre\n"
                     "Clausura 2006\nZona A - Sur\nRound 5 [Feb 12]\n"
                     "La Plata FC                  1-1 Villa Mitre\n")
    assert [a.llave for a in ajenos] == ["Torneo Apertura", "Torneo Clausura"]
    assert [a.fecha for a in ajenos] == ["2005-09-25", "2006-02-12"]


def test_apertura_sin_anio_no_es_un_encabezado():
    """El regex pide el anio, y por eso pide el anio: un encabezado resetea la
    zona, asi que una palabra suelta confundida con uno se lleva puestos en
    silencio todos los partidos que vengan atras."""
    ajenos, _ = leer("Torneo Apertura\nZona A - Sur\nRound 5 [Sep 25]\n"
                     "Apertura\n"
                     "La Plata FC                  1-1 Villa Mitre\n")
    assert len(ajenos) == 1, "la linea suelta no tenia que apagar la zona"


def test_la_zona_del_partido_es_la_zona_y_no_la_llave():
    """`a_partidos` copiaba la llave en los dos campos, asi que la columna `group`
    del dataset decia "Torneo Apertura" donde va "Zona A - Sur"."""
    ajenos, _ = leer("Apertura 2005\nZona A - Sur\nRound 1 [Aug 21]\n"
                     "Sportivo Desamparados        0-1 Villa Mitre\n")
    ps = rsssf.a_partidos(ajenos, "Torneo Argentino A", 2005)
    assert [p.zona for p in ps] == ["Zona A - Sur"]
    assert [p.llave for p in ps] == ["Torneo Apertura"]


def test_dos_zonas_con_la_misma_ronda_no_se_pisan():
    """Cada zona numera sus fechas desde 1. Es lo que separa `validar` para saber
    quien juega dos veces, y sin la zona los tres grupos son una sola casilla."""
    ajenos, _ = leer("Apertura 2005\nZona A - Sur\nRound 1 [Aug 21]\n"
                     "Sportivo Desamparados        0-1 Villa Mitre\n"
                     "Zona B - Norte\nRound 1 [Aug 21]\n"
                     "Ñuñorco                      1-0 Talleres\n")
    ps = rsssf.a_partidos(ajenos, "Torneo Argentino A", 2005)
    assert {p.jornada for p in ps} == {"Fecha 1"}
    assert [p.zona for p in ps] == ["Zona A - Sur", "Zona B - Norte"]


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


def test_2007_08_los_dos_grupos_nombran_los_mismos_clubes():
    """`Group A` y `Group B` son dos zonas de 8 -- la Zona 1 y la Zona 2 --, pero
    cada bloque nombra 16 clubes: los otros 8 son los rivales del interzonal, que
    RSSSF imprime bajo los dos grupos. Por eso los dos dicts tienen que conocer a
    los mismos 16 sin ser el mismo grupo.

    Se prueba sobre los clubes CANONICOS y no sobre las claves porque las claves
    difieren a proposito -- cada grupo trae alguna grafia suelta que el otro no --.
    Lo que no puede diferir es a quien apuntan. Si alguna vez alguien edita un
    grupo y se olvida del otro, los partidos de la segunda etapa se le van a otro
    club, que es la unica falla de este repo que no hace ruido.
    """
    a = rsssf.ARGENTINO_A_2007["Group A"]
    b = rsssf.ARGENTINO_A_2007["Group B"]
    assert set(a.values()) == set(b.values())
    assert len(set(a.values())) == 16
    assert len(set(rsssf.ARGENTINO_A_2007["Group C"].values())) == 9


def test_2007_08_el_talleres_pelado_se_traduce_en_el_mapa_y_no_en_el_padron():
    """RSSSF escribe `Talleres` a secas en UNA linea de 2007-08, y ahi es el de
    Perico. Globalmente NO lo es: "Talleres" pelado es el de Cordoba.

    Por eso la traduccion vive en el mapa de la temporada, que es por zona, y no
    en los alias del padron. Este test es el que se rompe si alguien decide
    "simplificar" moviendo el alias arriba: ese dia Perico se quedaria con las
    temporadas de Cordoba.
    """
    from fad import equipos

    assert rsssf.ARGENTINO_A_2007["Group A"]["Talleres"] == "Talleres (P)"
    pelado = equipos.buscar("Talleres")
    assert pelado is not None and pelado.nombre != "Talleres (P)"


def test_la_ronda_interzonal_tambien_se_escribe_detras_de_un_guion():
    """`Round 5 - Interzonal 1-2` es la tercera forma que usa la fuente, y la que
    estreno el Argentino A 2009-10.

    Importa mas de lo que parece porque falla en silencio a medias: sin reconocer
    la cola, la linea deja de ser una ronda, sus partidos heredan la ronda ANTERIOR
    -- aparecen como si fueran de la fecha 4 -- y ademas entran DOS veces, una bajo
    cada zona, porque tampoco se los reconoce como interzonales. Los partidos estan
    todos; lo que esta mal es cuando se jugaron.
    """
    mapa = {"Zone 1": {"La Plata FC": "La Plata FC", "Villa Mitre": "Villa Mitre"},
            "Zone 2": {"La Plata FC": "La Plata FC", "Villa Mitre": "Villa Mitre"}}
    texto = ("Zone 1\nRound 4 [Sep 12]\n"
             "La Plata FC                  1-0 Villa Mitre\n"
             "Round 5 - Interzonal 1-2\n[Sep 18]\n"
             "Villa Mitre                  2-1 La Plata FC\n"
             "Zone 2\nRound 5 - Interzonal 1-2\n[Sep 18]\n"
             "Villa Mitre                  2-1 La Plata FC\n")
    ajenos, _ = rsssf.leer(texto, mapa, 2009, 2010, 8)
    assert [a.jornada for a in ajenos] == [4, 5], \
        "el interzonal tiene que ser su propia ronda, no la anterior"
    assert len(ajenos) == 2, "el interzonal esta impreso dos veces y entra una"


def test_la_llave_pelada_abre_seccion_pero_repetida_no_cierra_nada():
    """Dos temporadas piden cosas opuestas de la misma linea.

    El 2009-10 rotula sus dos torneos con la palabra sola, y sin leerla las dos
    mitades caen en la misma casilla: la fecha 8 del Apertura choca con la del
    Clausura. Pero una palabra suelta repetida adentro de una zona ya abierta NO es
    un encabezado, y tratarla como tal apaga la zona y se lleva los partidos de
    atras sin decir nada. Lo que concilia las dos es exigir que la llave CAMBIE.
    """
    mapa = {"Zone 1": {"La Plata FC": "La Plata FC", "Villa Mitre": "Villa Mitre"}}
    ajenos, _ = rsssf.leer("Apertura\nZone 1\nRound 8 [Sep 25]\n"
                           "La Plata FC                  1-1 Villa Mitre\n"
                           "Clausura\nZone 1\nRound 8 [Feb 12]\n"
                           "La Plata FC                  2-2 Villa Mitre\n",
                           mapa, 2009, 2010, 8)
    assert [a.llave for a in ajenos] == ["Torneo Apertura", "Torneo Clausura"]

    # Y la repetida, que es contra lo que protege el test de al lado.
    ajenos, _ = rsssf.leer("Apertura\nZone 1\nRound 8 [Sep 25]\n"
                           "Apertura\n"
                           "La Plata FC                  1-1 Villa Mitre\n",
                           mapa, 2009, 2010, 8)
    assert len(ajenos) == 1, "la linea repetida no tenia que apagar la zona"

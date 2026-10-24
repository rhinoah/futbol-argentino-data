#!/usr/bin/env python3
"""Las declaraciones a mano contra dos cosas que no son ellas mismas.

`fad/correcciones.py` y `fad/citadas.py` cambian lo que sale de la fuente, y CI
no tiene las paginas: no puede ver que sin una declaracion la fila saldria
distinta. Lo que si tiene es lo publicado y este directorio, y con eso alcanza
para dos redes que miran para lados opuestos:

* DE IDA, contra `data/`. Cada declaracion de un torneo cerrado promete algo
  sobre una fila publicada, y la fila lo tiene que decir. Si se cambia una sin
  rehacer, o se rehace y deja de aplicarse, se nota aca. Mira solo los torneos
  cerrados, por lo mismo que `test_dataset.py`: los de uno en curso los aplica
  el bot DESPUES de correr la suite. `COPIAS`, `NEUTRALES` y la fecha de `DIAS`
  ya tenian la suya en `test_dataset.py`; aca estan las que faltaban.

* DE VUELTA, contra `huellas_correcciones.txt`. Sacar una declaracion no cambia
  lo publicado --el CSV ya salio con ella--, asi que ningun test de ida lo ve: el
  loop recorre una menos y pasa igual. Lo ve un testigo que NO sale de las
  declaraciones en cada corrida: un renglon por cada una, escrito una vez y
  revisado. Es la leccion del proyecto hermano, donde un refactor de unificacion
  dejo ~49 tests comparando una estructura consigo misma.
"""
from __future__ import annotations

import dataclasses
from collections import Counter, defaultdict
from pathlib import Path

import pytest

from fad import citadas, correcciones, dataset, torneos

DATOS = Path(__file__).resolve().parent.parent / "data"
HUELLAS = Path(__file__).resolve().parent / "huellas_correcciones.txt"


def _en_curso(pagina: str) -> bool:
    """Las de un torneo en curso las aplica el bot DESPUES de la suite. Es una
    funcion y no una constante para que importar este modulo no toque el
    catalogo: un mutante que lo rompa tiene que caer en un test, no en la colecta."""
    return pagina in {t.pagina for t in torneos.TODOS if not t.cerrado}


# ---- de vuelta: el testigo -----------------------------------------------------
# Lo que NO entra en la huella es la evidencia. Corregir la redaccion de un
# `porque` no mueve ningun dato, y pedir un renglon nuevo por eso enseñaria a
# pegar renglones sin mirarlos, que es justo lo que el testigo tiene que evitar.
# Los campos que valen lo que su default tampoco entran: asi un campo nuevo con
# default no cambia las huellas de las declaraciones que ya estaban.
_EVIDENCIA = frozenset({"porque", "testigos"})


def _campos(x) -> str:
    if not dataclasses.is_dataclass(x):
        return ""         # `LOCALIA_RESUELTA`: el valor es el texto de la evidencia
    return "".join(f" | {f.name}={getattr(x, f.name)!r}" for f in dataclasses.fields(x)
                   if f.name not in _EVIDENCIA and getattr(x, f.name) != f.default)


def huellas() -> list[str]:
    """Un renglon por declaracion, en el orden en que estan escritas.

    Las colecciones se buscan solas --toda tupla de dataclasses o dict en
    MAYUSCULAS de los dos modulos-- para que una coleccion nueva entre al testigo
    sin que nadie se acuerde de agregarla aca."""
    out = []
    for mod in (correcciones, citadas):
        for nombre, v in vars(mod).items():
            if not nombre.isupper() or nombre.startswith("_"):
                continue
            if isinstance(v, tuple) and v and all(dataclasses.is_dataclass(x) for x in v):
                out += [f"{nombre}{_campos(x)}" for x in v]
            elif isinstance(v, dict):
                out += [f"{nombre} | {k!r}{_campos(x)}" for k, xs in v.items()
                        for x in (xs if isinstance(xs, tuple) else (xs,))]
    return out


def test_cada_declaracion_es_un_renglon_del_testigo():
    """SACAR UNA DECLARACION DEJA LA SUITE EN ROJO, y cambiarle un campo que llega
    al dato tambien. El archivo NO se regenera: cuando esto falla dice que renglon
    falta y cual sobra, y el renglon se edita a mano en el mismo commit que cambia
    la declaracion. Regenerarlo desde el codigo lo volveria tautologico."""
    escritas = Counter(r for r in HUELLAS.read_text(encoding="utf-8").splitlines()
                       if r.strip() and not r.startswith("#"))
    vivas = Counter(huellas())
    faltan = sorted((escritas - vivas).elements())
    sobran = sorted((vivas - escritas).elements())
    assert not faltan and not sobran, (
        f"las declaraciones no son las de {HUELLAS.name}.\n"
        + "".join(f"\n  en el testigo y no en el codigo (¿se saco o se cambio?):\n    {r}"
                  for r in faltan)
        + "".join(f"\n  en el codigo y no en el testigo (¿es nueva o se cambio?):\n    {r}"
                  for r in sobran))


# ---- de ida: lo publicado -------------------------------------------------------
@pytest.fixture(scope="module")
def de():
    """Las filas publicadas, por titulo de pagina."""
    filas = dataset.leer_carpeta(DATOS)
    if not filas:
        pytest.skip("hace falta el dataset")
    pagina = {t.url: t.pagina for t in torneos.TODOS}
    por = defaultdict(list)
    for f in filas:
        por[pagina.get(dataset.pagina_de(f), "")].append(f)
    return por


def _goles(f):
    return (int(f["home_score"]), int(f["away_score"])) if f["home_score"] else None


def _penales(f):
    return (int(f["home_pens"]), int(f["away_pens"])) if f["home_pens"] else None


def _del_partido(de, pagina, jornada, local, visita) -> list[dict]:
    return [f for f in de[pagina] if f["matchday"] == jornada
            and (f["home_team"], f["away_team"]) == (local, visita)]


def test_cada_correccion_esta_publicada(de):
    """La fila quedo con los clubes de `debe`. Si es un espejo los goles van con los
    clubes, y despues puede pasarle un `Marcador`: es el orden de `aplicar`."""
    vistas = 0
    for c in correcciones.CORRECCIONES:
        if _en_curso(c.pagina):
            continue
        local, visita, gl, gv = c.dice
        goles = (gv, gl) if c.debe == (visita, local) else (gl, gv)
        goles = correcciones.arbitrado(c.pagina, c.jornada, *c.debe, *goles)
        fs = _del_partido(de, c.pagina, c.jornada, *c.debe)
        assert goles in [_goles(f) for f in fs], (c.pagina, c.jornada, c.debe, goles)
        vistas += 1
    assert vistas >= 40, f"son 53 y vio {vistas}: no esta mirando"


def test_cada_marcador_arbitrado_esta_publicado(de):
    vistas = 0
    for m in correcciones.MARCADORES:
        if _en_curso(m.pagina):
            continue
        fs = [f for f in _del_partido(de, m.pagina, m.jornada, m.local, m.visita)
              if _goles(f) == m.debe
              and (m.penales_debe is None or _penales(f) == m.penales_debe)
              and (not m.status_debe or f["status"] == m.status_debe)]
        assert len(fs) == 1, (m.pagina, m.jornada, m.local, m.visita, m.debe)
        vistas += 1
    assert vistas >= 50, f"son 68 y vio {vistas}: no esta mirando"


def test_ningun_partido_dividido_se_publica(de):
    """El que `dice=None` no llega a ser fila, y de ese no hay nada que mirar."""
    vistas = 0
    for d in correcciones.DIVIDIDOS:
        if _en_curso(d.pagina) or d.dice is None:
            continue
        assert not [f for f in de[d.pagina] if _goles(f) == d.dice
                    and (f["home_team"], f["away_team"]) == (d.local, d.visita)], (
            d.pagina, d.local, d.visita, d.dice)
        vistas += 1
    assert vistas >= 5, f"son 9 y vio {vistas}: no esta mirando"


def test_cada_faltante_esta_publicado_entero(de):
    for x in correcciones.FALTANTES:
        if _en_curso(x.pagina):
            continue
        fs = [f for f in _del_partido(de, x.pagina, x.jornada, x.local, x.visita)
              if (_goles(f), _penales(f), f["date"], f["time"], f["venue"])
              == (x.goles, x.penales, x.fecha, x.hora, x.estadio)]
        assert len(fs) == 1, (x.pagina, x.jornada, x.local, x.visita)


def test_cada_homonimo_quedo_resuelto_en_lo_publicado(de):
    """Ninguna fila de la pagina escribe el nombre ambiguo, y alguna el resuelto."""
    for h in correcciones.HOMONIMOS:
        if _en_curso(h.pagina):
            continue
        clubes = Counter(f["home_team"] for f in de[h.pagina])
        clubes.update(f["away_team"] for f in de[h.pagina])
        assert clubes[h.dice] == 0 and clubes[h.debe] > 0, (h.pagina, h.dice, h.debe)


def test_cada_cancha_corregida_esta_publicada(de):
    for c in correcciones.CANCHAS:
        if _en_curso(c.pagina):
            continue
        fs = _del_partido(de, c.pagina, c.jornada, c.local, c.visita)
        assert [f["venue"] for f in fs] == [c.debe], (c.pagina, c.jornada, c.local)


def test_cada_reemplazo_esta_publicado(de):
    vistas = 0
    for r in correcciones.REEMPLAZOS:
        if _en_curso(r.pagina):
            continue
        local, visita, gl, gv = r.debe
        assert (gl, gv) in [_goles(f) for f in _del_partido(de, r.pagina, r.jornada,
                                                             local, visita)], (
            r.pagina, r.llave, r.jornada, r.debe)
        vistas += 1
    assert vistas >= 10, f"son 14 y vio {vistas}: no esta mirando"


def test_cada_desacuerdo_de_fecha_verificado_habla_del_dia_publicado(de):
    """Un `Fechado` calla un desacuerdo puntual: nuestra fecha contra la otra. Si
    la publicada ya es otra, la declaracion habla de una fila que no existe."""
    vistas = 0
    for x in correcciones.FECHADOS:
        if _en_curso(x.pagina):
            continue
        fs = _del_partido(de, x.pagina, x.jornada, x.local, x.visita)
        assert [f["date"] for f in fs] == [x.nuestra], (x.pagina, x.jornada, x.local)
        vistas += 1
    assert vistas >= 5, f"son 7 y vio {vistas}: no esta mirando"


def test_cada_fecha_puesta_a_mano_publica_su_credito(de):
    """`Dia`, `Cita` y `Pata` le ponen el dia a una fila, y su fuente viaja en
    `source`. La fecha de las `Dia` ya la mira `test_dataset.py`; esto es lo que
    no miraba nadie: que la fila exista una sola vez y nombre a quien la fecha."""
    vistas = 0
    for d in correcciones.DIAS:
        if _en_curso(d.pagina):
            continue
        fs = _del_partido(de, d.pagina, d.jornada, d.local, d.visita)
        assert [f["source"].endswith(dataset.SEPARADOR + d.fuente) for f in fs] == [True], (
            d.pagina, d.jornada, d.local, d.fuente)
        vistas += 1
    for pagina, citas in citadas.FECHAS.items():
        if _en_curso(pagina):
            continue
        for c in citas:
            fs = [f for f in de[pagina] if f["date"] == c.fecha
                  and (f["home_team"], f["away_team"]) == (c.local, c.visita)
                  and _goles(f) == (c.goles_local, c.goles_visita)]
            credito = dataset.SEPARADOR + (c.fuente or citadas.CREDITO)
            assert [credito in f["source"] for f in fs] == [True], (pagina, c.fecha, c.local)
            vistas += 1
    for pagina, patas in citadas.LLAVES.items():
        if _en_curso(pagina):
            continue
        for p in patas:
            fs = [f for f in de[pagina] if f["date"] == p.fecha and f["matchday"] == p.ronda
                  and (f["home_team"], f["away_team"]) == (p.local, p.visita)
                  and _goles(f) == (p.goles_local, p.goles_visita)]
            assert [f["source"].endswith(dataset.SEPARADOR + p.fuente) for f in fs] == [True], (
                pagina, p.fecha, p.local)
            vistas += 1
    assert vistas >= 80, f"son 106 y vio {vistas}: no esta mirando"

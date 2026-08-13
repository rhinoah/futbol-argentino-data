#!/usr/bin/env python3
"""Tests del cliente de Wikipedia. Ninguno sale a la red: se reemplaza `_pedir`.

Interesa que la cache y el manejo de errores anden, no que Wikipedia responda.
"""
from __future__ import annotations

import json
import urllib.error

import pytest

from fad import wiki


@pytest.fixture
def cache(tmp_path, monkeypatch):
    """Manda la cache a un directorio temporal. Sin esto los tests escribirian
    (y leerian) la cache de verdad, y el resultado dependeria de que se bajo
    antes."""
    monkeypatch.setattr(wiki, "CACHE", tmp_path / ".cache")
    return tmp_path / ".cache"


def responder(monkeypatch, texto="hola", pedidos=None):
    def falso(url):
        if pedidos is not None:
            pedidos.append(url)
        return json.dumps({"parse": {"wikitext": texto}})
    monkeypatch.setattr(wiki, "_pedir", falso)


def test_trae_el_wikitexto(cache, monkeypatch):
    responder(monkeypatch, "== Hola ==")
    assert wiki.wikitexto("Anexo:X") == "== Hola =="


def test_guarda_en_cache(cache, monkeypatch):
    responder(monkeypatch, "contenido")
    wiki.wikitexto("Anexo:X")
    assert list(cache.iterdir()), "no escribio nada en la cache"


def test_la_segunda_vez_no_pide(cache, monkeypatch):
    pedidos = []
    responder(monkeypatch, "contenido", pedidos)
    wiki.wikitexto("Anexo:X")
    wiki.wikitexto("Anexo:X")
    assert len(pedidos) == 1


def test_sin_cache_pide_igual(cache, monkeypatch):
    pedidos = []
    responder(monkeypatch, "contenido", pedidos)
    wiki.wikitexto("Anexo:X")
    wiki.wikitexto("Anexo:X", usar_cache=False)
    assert len(pedidos) == 2


def test_el_titulo_con_barras_no_arma_subcarpetas(cache, monkeypatch):
    """"Anexo:Torneo Apertura 2026 (Argentina)" tiene dos puntos, espacios y
    parentesis; otros titulos traen barras. El nombre del archivo va escapado,
    si no la cache escribe fuera de su carpeta."""
    responder(monkeypatch, "x")
    wiki.wikitexto("Anexo:Copa/Argentina 2026")
    archivos = list(cache.iterdir())
    assert len(archivos) == 1 and archivos[0].is_file()


def test_dos_paginas_no_comparten_cache(cache, monkeypatch):
    monkeypatch.setattr(wiki, "_pedir",
                        lambda url: json.dumps({"parse": {"wikitext": url}}))
    a = wiki.wikitexto("Anexo:A")
    b = wiki.wikitexto("Anexo:B")
    assert a != b


def test_pagina_inexistente(cache, monkeypatch):
    monkeypatch.setattr(wiki, "_pedir", lambda url: json.dumps(
        {"error": {"code": "missingtitle", "info": "The page you specified doesn't exist."}}))
    with pytest.raises(LookupError, match="doesn't exist"):
        wiki.wikitexto("Anexo:No existe")


def test_una_pagina_que_no_esta_no_queda_cacheada(cache, monkeypatch):
    """Cachear un error convierte un problema de un rato en uno permanente."""
    monkeypatch.setattr(wiki, "_pedir",
                        lambda url: json.dumps({"error": {"info": "nope"}}))
    with pytest.raises(LookupError):
        wiki.wikitexto("Anexo:No existe")
    assert not cache.exists() or not list(cache.iterdir())


def test_existe(cache, monkeypatch):
    responder(monkeypatch, "x")
    assert wiki.existe("Anexo:X")


def test_no_existe(cache, monkeypatch):
    monkeypatch.setattr(wiki, "_pedir",
                        lambda url: json.dumps({"error": {"info": "nope"}}))
    assert not wiki.existe("Anexo:X")


# --------------------------------------------------------------------------
# reintentos: esto corre solo todos los dias
# --------------------------------------------------------------------------
def test_reintenta_si_se_corta_la_red(monkeypatch):
    """Un corte de diez segundos no tiene que volverse un dataset sin actualizar
    y un mail de error."""
    monkeypatch.setattr(wiki.time, "sleep", lambda _: None)
    intentos = []

    def flaky(req, timeout=None):
        intentos.append(1)
        if len(intentos) < 3:
            raise urllib.error.URLError("se cayo la red")
        return _respuesta('{"parse": {"wikitext": "ok"}}')

    monkeypatch.setattr(wiki.urllib.request, "urlopen", flaky)
    assert wiki._pedir("http://x") == '{"parse": {"wikitext": "ok"}}'
    assert len(intentos) == 3


def test_se_rinde_despues_de_varios_intentos(monkeypatch):
    monkeypatch.setattr(wiki.time, "sleep", lambda _: None)
    intentos = []

    def siempre_mal(req, timeout=None):
        intentos.append(1)
        raise urllib.error.URLError("nada")

    monkeypatch.setattr(wiki.urllib.request, "urlopen", siempre_mal)
    with pytest.raises(urllib.error.URLError):
        wiki._pedir("http://x")
    assert len(intentos) == wiki.INTENTOS


def test_un_404_no_se_reintenta(monkeypatch):
    """Una pagina que no existe no va a existir en cinco segundos. Reintentarla
    solo tarda mas en avisar que el titulo cambio."""
    monkeypatch.setattr(wiki.time, "sleep", lambda _: None)
    intentos = []

    def no_esta(req, timeout=None):
        intentos.append(1)
        raise urllib.error.HTTPError("http://x", 404, "Not Found", {}, None)

    monkeypatch.setattr(wiki.urllib.request, "urlopen", no_esta)
    with pytest.raises(urllib.error.HTTPError):
        wiki._pedir("http://x")
    assert len(intentos) == 1


def test_un_500_si_se_reintenta(monkeypatch):
    """Un error del servidor puede ser pasajero."""
    monkeypatch.setattr(wiki.time, "sleep", lambda _: None)
    intentos = []

    def caido(req, timeout=None):
        intentos.append(1)
        if len(intentos) < 2:
            raise urllib.error.HTTPError("http://x", 503, "Unavailable", {}, None)
        return _respuesta("{}")

    monkeypatch.setattr(wiki.urllib.request, "urlopen", caido)
    assert wiki._pedir("http://x") == "{}"
    assert len(intentos) == 2


def _respuesta(cuerpo: str):
    """Un stand-in de lo que devuelve urlopen: context manager con .read()."""
    class R:
        def __enter__(self): return self
        def __exit__(self, *a): return False
        def read(self): return cuerpo.encode("utf-8")
    return R()


def test_se_identifica():
    """Wikipedia le contesta 403 a los User-Agent genericos, y pide que diga
    quien es y como contactarlo."""
    assert "futbol-argentino-data" in wiki.UA
    assert "http" in wiki.UA

#!/usr/bin/env python3
"""Tests del cliente de Wikipedia. Ninguno sale a la red: se reemplaza `_pedir`.

Interesa que la cache y el manejo de errores anden, no que Wikipedia responda.
"""
from __future__ import annotations

import json

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


def test_se_identifica():
    """Wikipedia le contesta 403 a los User-Agent genericos, y pide que diga
    quien es y como contactarlo."""
    assert "futbol-argentino-data" in wiki.UA
    assert "http" in wiki.UA

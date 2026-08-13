#!/usr/bin/env python3
"""
fad/wiki.py
===========
Bajar el wikitexto de Wikipedia en castellano.

Se usa la API de MediaWiki y no el HTML renderizado: el wikitexto es la fuente
que editan las personas, y las plantillas (`{{Partido|local=...}}`) vienen con
sus parametros nombrados en vez de convertidas en `<table>`. Parsear el HTML
seria mas fragil y no daria mas datos.

Hay cache en disco a proposito. Durante el desarrollo la misma pagina se parsea
decenas de veces, y no hay razon para pedirsela a Wikipedia cada vez: son ~80 KB
por torneo y la pagina cambia unas pocas veces por dia.
"""
from __future__ import annotations

import time
import urllib.parse
import urllib.request
from pathlib import Path

API = "https://es.wikipedia.org/w/api.php"

# Wikipedia pide identificarse. Un User-Agent generico puede recibir un 403.
UA = ("futbol-argentino-data/0.1 "
      "(https://github.com/rhinoah/futbol-argentino-data; dataset abierto)")

CACHE = Path(__file__).resolve().parent.parent / ".cache"

_ULTIMO_PEDIDO = 0.0
PAUSA_MIN = 1.0          # segundos entre pedidos, para no golpear la API


def _pedir(url: str) -> str:
    """GET con User-Agent propio y una pausa minima entre llamadas."""
    global _ULTIMO_PEDIDO
    espera = PAUSA_MIN - (time.monotonic() - _ULTIMO_PEDIDO)
    if espera > 0:
        time.sleep(espera)
    req = urllib.request.Request(url, headers={"User-Agent": UA})
    with urllib.request.urlopen(req, timeout=60) as r:
        datos = r.read().decode("utf-8")
    _ULTIMO_PEDIDO = time.monotonic()
    return datos


def wikitexto(titulo: str, usar_cache: bool = True) -> str:
    """El wikitexto crudo de una pagina. Levanta si la pagina no existe."""
    archivo = CACHE / (urllib.parse.quote(titulo, safe="") + ".wiki")
    if usar_cache and archivo.exists():
        return archivo.read_text(encoding="utf-8")

    url = (f"{API}?action=parse&page={urllib.parse.quote(titulo)}"
           "&prop=wikitext&formatversion=2&format=json")
    import json
    datos = json.loads(_pedir(url))
    if "error" in datos:
        raise LookupError(f"{titulo}: {datos['error'].get('info', datos['error'])}")
    texto = datos["parse"]["wikitext"]

    CACHE.mkdir(exist_ok=True)
    archivo.write_text(texto, encoding="utf-8")
    return texto


def existe(titulo: str) -> bool:
    """Si la pagina existe. Sirve para descubrir que temporadas hay cargadas."""
    try:
        wikitexto(titulo)
        return True
    except LookupError:
        return False


def ultima_edicion(titulo: str) -> str:
    """Timestamp ISO de la ultima edicion. Para saber si hay algo nuevo."""
    import json
    url = (f"{API}?action=query&prop=revisions&titles={urllib.parse.quote(titulo)}"
           "&rvlimit=1&rvprop=timestamp&formatversion=2&format=json")
    paginas = json.loads(_pedir(url))["query"]["pages"]
    revs = paginas[0].get("revisions") if paginas else None
    return revs[0]["timestamp"] if revs else ""

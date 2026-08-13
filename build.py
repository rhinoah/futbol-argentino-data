#!/usr/bin/env python3
"""
build.py
========
Arma el dataset: baja las paginas, las parsea, las valida y escribe el CSV.

    python build.py                 # todo, usando la cache si hay
    python build.py --sin-cache     # vuelve a pedirle todo a Wikipedia
    python build.py --dry-run       # parsea y valida, no escribe nada

Un aviso GRAVE no escribe el archivo. Es a proposito: este script se va a correr
solo desde una tarea programada, y el modo de fallar de un scraper no es tirar
una excepcion sino escribir un CSV plausible y equivocado. Si algo no cierra,
preferimos quedarnos con el dataset de ayer, que estaba bien.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

from fad import dataset, parser, torneos, validar, wiki

SALIDA = Path(__file__).resolve().parent / "data" / "partidos.csv"


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sin-cache", action="store_true", help="ignora la cache en disco")
    ap.add_argument("--dry-run", action="store_true", help="no escribe el CSV")
    args = ap.parse_args(argv)

    filas, avisos, fallo = [], [], False
    for t in torneos.TODOS:
        try:
            texto = wiki.wikitexto(t.pagina, usar_cache=not args.sin_cache)
        except Exception as e:                       # red caida, pagina renombrada
            print(f"  !! {t.pagina}: {e}", file=sys.stderr)
            fallo = True
            continue

        ps = parser.partidos(texto, t.temporada, t.torneo)
        propios = validar.revisar(ps)
        avisos += propios
        graves = sum(a.grave for a in propios)
        print(f"  {t.pagina[6:]:<44} {len(ps):>4} partidos"
              f"{'' if not propios else f'   ({len(propios)} avisos, {graves} graves)'}")
        filas += [dataset.a_fila(p, t.torneo, t.temporada, t.url) for p in ps]

    for a in avisos:
        print(f"  {a}", file=sys.stderr)

    if fallo or any(a.grave for a in avisos):
        print("\nNO se escribio el CSV: hay problemas sin resolver.\n"
              "El dataset anterior queda como estaba.", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"\n[dry-run] {len(filas)} filas, sin escribir.")
        return 0

    n = dataset.escribir(filas, SALIDA)
    print(f"\n{n} partidos -> {SALIDA.relative_to(SALIDA.parent.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

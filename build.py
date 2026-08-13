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

from fad import dataset, equipos, parser, torneos, validar, wiki

SALIDA = Path(__file__).resolve().parent / "data" / "partidos.csv"


def procesar(texto: str, t) -> tuple[list, list]:
    """Parsea, lleva los nombres al canonico y valida. Devuelve (partidos, avisos).

    Separado de `main` para poder probarlo: es donde vive el orden de los pasos,
    y el orden importa.

    Normalizar va ANTES de validar, pero no por la razon que parece. No es para
    que `nombres_en_el_padron` no se queje de los alias -- ese chequeo los acepta,
    asi que por ese lado da igual el orden. Es por los OTROS chequeos, que
    comparan nombres entre si: "nadie juega dos veces por fecha", "sin
    duplicados", "cada ganador reaparece en la ronda siguiente". Todos comparan
    por igualdad de cadena, y las llaves vienen de plantillas mientras las zonas
    vienen de tablas, asi que el mismo club perfectamente puede estar escrito de
    dos maneras en la misma pagina. Sin normalizar antes, esas comparaciones
    tratan dos grafias como dos clubes y los chequeos dejan pasar justo lo que
    tenian que agarrar.
    """
    ps = parser.partidos(texto, t.temporada, t.torneo, formato=t.formato,
                         anio_fin=t.anio_fin, mes_inicio=t.mes_inicio)
    for p in ps:
        p.local = equipos.canonizar(p.local)
        p.visita = equipos.canonizar(p.visita)
    return ps, validar.revisar(ps)


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sin-cache", action="store_true", help="ignora la cache en disco")
    ap.add_argument("--dry-run", action="store_true", help="no escribe el CSV")
    ap.add_argument("--forzar", action="store_true",
                    help="escribe aunque el dataset se achique (revisalo antes)")
    args = ap.parse_args(argv)

    filas, avisos, fallo = [], [], False
    for t in torneos.TODOS:
        try:
            texto = wiki.wikitexto(t.pagina, usar_cache=not args.sin_cache)
        except Exception as e:                       # red caida, pagina renombrada
            print(f"  !! {t.pagina}: {e}", file=sys.stderr)
            fallo = True
            continue

        ps, propios = procesar(texto, t)
        avisos += propios
        graves = sum(a.grave for a in propios)
        etiqueta = t.pagina.split(":", 1)[-1]      # saca el "Anexo:" si lo tiene
        print(f"  {etiqueta:<44} {len(ps):>4} partidos"
              f"{'' if not propios else f'   ({len(propios)} avisos, {graves} graves)'}")
        filas += [dataset.a_fila(p, t.torneo, t.temporada, t.url, t.neutral)
                  for p in ps]

    for a in avisos:
        print(f"  {a}", file=sys.stderr)

    if fallo or any(a.grave for a in avisos):
        print("\nNO se escribio el CSV: hay problemas sin resolver.\n"
              "El dataset anterior queda como estaba.", file=sys.stderr)
        return 1

    # Ultima guarda, y la que importa cuando esto corre solo: que no se achique.
    # Un chequeo de `validar` mira los partidos que HAY; este mira los que ya no.
    perdidos = dataset.regresiones(filas, dataset.read_anterior(SALIDA))
    if perdidos and not args.forzar:
        print("\nEl dataset se ACHICO respecto del que ya estaba:", file=sys.stderr)
        for p in perdidos:
            print(f"   {p}", file=sys.stderr)
        print("\nNo se escribio nada. Puede ser real (Wikipedia corrigio algo) o\n"
              "puede ser que una pagina cambio de forma y el parser se quedo sin\n"
              "encontrarla. Mirando el detalle de arriba se distingue; si esta\n"
              "bien, va de nuevo con --forzar.", file=sys.stderr)
        return 1

    if args.dry_run:
        print(f"\n[dry-run] {len(filas)} filas, sin escribir.")
        return 0

    n = dataset.escribir(filas, SALIDA)
    print(f"\n{n} partidos -> {SALIDA.relative_to(SALIDA.parent.parent)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

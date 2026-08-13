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


def _borrar_jornadas_falsas(ps) -> int:
    """Saca la jornada cuando no puede ser una jornada, y devuelve cuantas.

    Una etiqueta bajo la cual un equipo aparece DOS VECES no es una fecha del
    calendario: es un encabezado que el parser tomo por tal. La pagina del Torneo
    Inicial 2012 cuelga sus 190 partidos de un unico "Fecha 1", asi que los 20
    equipos figuran diecinueve veces cada uno ahi adentro.

    Se borra en vez de dejarla, y no es esconder nada: la etiqueta equivocada ES
    la mentira. Sin ella el partido entra completo -- fecha, equipos y marcador --
    con `matchday` vacio, que es exactamente lo que la fuente dice. Queda avisado
    cuantos fueron.
    """
    from collections import Counter
    grupos = {}
    for p in ps:
        if p.fase == "zonas" and p.jornada:
            grupos.setdefault((p.llave, p.zona, p.jornada), []).append(p)
    n = 0
    for partidos in grupos.values():
        c = Counter()
        for p in partidos:
            c[p.local] += 1
            c[p.visita] += 1
        # El umbral importa, y ajustarlo mal desactiva un chequeo. Una jornada
        # real no puede tener MAS partidos que equipos: con 20 equipos son 10
        # como maximo. Los 190 del Inicial 2012 bajo un solo rotulo lo superan
        # por lejos y se limpian. En cambio una jornada con UN partido de mas --
        # la firma de una etiqueta corrida, que es lo que paso con los
        # interzonales del Apertura 2026 -- no lo supera, y sigue siendo el
        # error grave que tiene que ser.
        if len(partidos) > len(c) and any(v > 1 for v in c.values()):
            for p in partidos:
                p.jornada = ""
                n += 1
    return n


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
        p.local = equipos.canonizar(p.local, p.local_art)
        p.visita = equipos.canonizar(p.visita, p.visita_art)
    borradas = _borrar_jornadas_falsas(ps)
    avisos = validar.revisar(ps)
    if borradas:
        avisos.append(validar.Aviso(
            f"{borradas} partidos sin numero de jornada",
            "la pagina no la rotula; el partido entra igual, con `matchday` vacio",
            grave=False))
    # Los sin fecha se van DESPUES de validar, para que el aviso alcance a
    # nombrarlos: el esquema promete una fecha en cada fila.
    return [p for p in ps if p.fecha], avisos


def main(argv=None) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--sin-cache", action="store_true", help="ignora la cache en disco")
    ap.add_argument("--dry-run", action="store_true", help="no escribe el CSV")
    ap.add_argument("--rehacer", action="store_true",
                    help="vuelve a parsear TODO, incluso los torneos terminados")
    ap.add_argument("--forzar", action="store_true",
                    help="escribe aunque el dataset se achique (revisalo antes)")
    args = ap.parse_args(argv)

    anterior = dataset.read_anterior(SALIDA)
    # Lo ya jugado se toma del CSV, no se vuelve a bajar. Ver `Torneo.cerrado`.
    # La clave es `source` -- la URL de la pagina -- y no (torneo, temporada).
    # Varias entradas del catalogo comparten torneo y temporada: la 2016 y la
    # 2016-17 son las dos "Primera Division 2016". Agrupando por ahi, cada una se
    # llevaba las filas de las DOS y el dataset crecia 3284 partidos de la nada.
    guardado: dict[str, list] = {}
    for f in anterior:
        guardado.setdefault(f["source"], []).append(f)

    filas, avisos, fallo, reusados = [], [], False, 0
    for t in torneos.TODOS:
        listas = guardado.get(t.url)
        if t.cerrado and not args.rehacer and listas is not None:
            filas += listas
            reusados += 1
            continue
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

    if reusados:
        print(f"\n  ({reusados} torneos terminados salieron del CSV, sin bajarlos)")

    for a in avisos:
        print(f"  {a}", file=sys.stderr)

    if fallo or any(a.grave for a in avisos):
        print("\nNO se escribio el CSV: hay problemas sin resolver.\n"
              "El dataset anterior queda como estaba.", file=sys.stderr)
        return 1

    # Ultima guarda, y la que importa cuando esto corre solo: que no se achique.
    # Un chequeo de `validar` mira los partidos que HAY; este mira los que ya no.
    perdidos = dataset.regresiones(filas, anterior)
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

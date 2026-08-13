#!/usr/bin/env python3
"""
fad/validar.py
==============
Chequeos de sanidad sobre los partidos parseados.

La razon de ser de este modulo: **un parser de wikitexto no falla, miente**. Si
una columna se corre por un `rowspan` mal manejado, no hay excepcion: hay un
dataset con el estadio en la columna de la fecha. Si los parentesis del
entretiempo se leen como penales, no hay excepcion: hay definiciones por penales
que nunca ocurrieron. Los dos errores pasaron de verdad escribiendo esto.

Asi que no se confia en el parser: se le exige que lo que devuelve cumpla cosas
que solo pueden cumplirse si esta bien. La mas fuerte es la del cuadro de
eliminacion (`cadena_de_llaves`): cada ganador tiene que reaparecer en la ronda
siguiente. Eso se verifica SIN mirar ninguna fuente externa, y si el parseo esta
mal se rompe en el primer eslabon.
"""
from __future__ import annotations

import re
from collections import Counter

from fad import equipos
from fad.parser import Partido

MAX_GOLES = 20          # marcador mas alto plausible en un partido profesional


class Aviso:
    """Un problema encontrado. `grave` corta el build; el resto solo informa."""

    def __init__(self, que: str, detalle: str, grave: bool = True):
        self.que, self.detalle, self.grave = que, detalle, grave

    def __str__(self):
        return f"{'ERROR' if self.grave else 'aviso'}: {self.que} — {self.detalle}"


def campos_completos(ps: list[Partido]) -> list[Aviso]:
    """Ningun partido a medias: sin equipos, sin fecha o sin marcador."""
    avisos = []
    for p in ps:
        falta = [c for c in ("local", "visita") if not getattr(p, c)]
        if falta:
            avisos.append(Aviso("partido sin equipos", f"{p.fecha} {p.local!r} vs {p.visita!r}"))
        if p.goles_local is None or p.goles_visita is None:
            avisos.append(Aviso("partido sin marcador", f"{p.local} vs {p.visita}"))
        elif not (0 <= p.goles_local <= MAX_GOLES and 0 <= p.goles_visita <= MAX_GOLES):
            avisos.append(Aviso("marcador inverosimil",
                                f"{p.local} {p.goles_local}-{p.goles_visita} {p.visita}"))
        if not p.fecha:
            avisos.append(Aviso("partido sin fecha",
                                f"{p.local} vs {p.visita} (crudo: {p.fecha_cruda!r})"))
    return avisos


def nombres_en_el_padron(ps: list[Partido]) -> list[Aviso]:
    """Todo club tiene que estar en `equipos.PADRON`.

    Es grave y corta el build a proposito. Un nombre que el padron no conoce es
    casi siempre un club que asciende o un torneo que se suma, y si se deja pasar
    entra al dataset como un equipo nuevo: "Talleres" y "Talleres (C)" pasan a ser
    dos clubes con media historia cada uno, y nadie lo nota hasta que el modelo
    da cualquier cosa. Cuesta un renglon en el padron; se avisa una vez.
    """
    raros = sorted({n for p in ps for n in (p.local, p.visita)
                    if n and not equipos.conocido(n)})
    return [Aviso("club que no esta en el padron",
                  f"{len(raros)}: {', '.join(raros[:6])}"
                  f"{' ...' if len(raros) > 6 else ''}")] if raros else []


def penales_solo_en_empates(ps: list[Partido]) -> list[Aviso]:
    """Una tanda de penales sobre un partido que no termino empatado es la firma
    de haber leido el entretiempo como si fuera la tanda."""
    return [Aviso("penales en un partido que no fue empate",
                  f"{p.local} {p.goles_local}-{p.goles_visita} {p.visita} "
                  f"(pen {p.penales_local}-{p.penales_visita})")
            for p in ps
            if p.penales_local is not None and p.goles_local != p.goles_visita]


def sin_duplicados(ps: list[Partido]) -> list[Aviso]:
    """El mismo cruce dos veces en la misma fecha es una fila leida dos veces."""
    c = Counter((p.fecha, p.local, p.visita) for p in ps)
    return [Aviso("partido duplicado", f"{f} {l} vs {v} ({n} veces)")
            for (f, l, v), n in c.items() if n > 1]


def nadie_juega_contra_si_mismo(ps: list[Partido]) -> list[Aviso]:
    """Sintoma clasico de columnas corridas."""
    return [Aviso("un equipo contra si mismo", f"{p.fecha} {p.local}")
            for p in ps if p.local and p.local == p.visita]


def todos_tienen_zona(ps: list[Partido]) -> list[Aviso]:
    """Un partido de fase de grupos sin zona quiere decir que su encabezado no se
    reconocio. El riesgo real no es el vacio sino el vecino: la zona se arrastra
    de fila en fila, asi que un encabezado ignorado no deja el campo en blanco,
    lo llena con la etiqueta anterior. Ya paso con los bloques "Interzonal"."""
    sin = [p for p in ps if p.fase == "zonas" and not p.zona]
    return [Aviso("partidos de zona sin zona asignada",
                  f"{len(sin)}, p.ej. {sin[0].fecha} {sin[0].local} vs {sin[0].visita}")] if sin else []


_ZONA = re.compile(r"(?i)^(zona|grupo)\b")


def zonas_completas(ps: list[Partido]) -> list[Aviso]:
    """En una zona todos-contra-todos, cada equipo juega la misma cantidad.

    Solo se le exige a las secciones que son realmente una zona: los bloques
    "Interzonal" cruzan equipos de zonas distintas y no tienen por que cerrar.
    """
    avisos = []
    zonas: dict[str, list[Partido]] = {}
    for p in ps:
        if p.fase == "zonas" and _ZONA.match(p.zona or ""):
            zonas.setdefault(p.zona, []).append(p)
    for zona, partidos in sorted(zonas.items()):
        jugados = Counter()
        for p in partidos:
            jugados[p.local] += 1
            jugados[p.visita] += 1
        if not jugados:
            continue
        if len(set(jugados.values())) > 1:
            raro = sorted(jugados.items(), key=lambda kv: kv[1])
            avisos.append(Aviso(
                f"{zona}: no todos jugaron la misma cantidad",
                f"min {raro[0][0]}={raro[0][1]}, max {raro[-1][0]}={raro[-1][1]}",
                grave=False))          # un torneo en curso lo incumple sin estar mal
        elif len(partidos) != (n := len(jugados)) * (n - 1) // 2:
            avisos.append(Aviso(
                f"{zona}: no es un todos-contra-todos completo",
                f"{n} equipos deberian jugar {n * (n - 1) // 2} partidos, hay {len(partidos)}",
                grave=False))
    return avisos


def una_vez_por_jornada(ps: list[Partido]) -> list[Aviso]:
    """Nadie juega dos veces en la misma fecha del calendario.

    Este es el chequeo que agarra las etiquetas corridas, y hubo que buscarlo un
    poco. El primer intento fue cronologico -- "la Fecha 7 no puede empezar antes
    que la Fecha 6" -- y sirvio de poco por los dos lados: no vio el bug real
    (las dos jornadas empezaban el mismo dia, y un empate no es un `<`) y en
    cambio se quejaba de la Fecha 9 del Apertura 2026, que se posterrgo entera a
    mayo y esta perfecta.

    Este no depende del calendario, solo de como esta armado el torneo, y por eso
    sobrevive a las reprogramaciones: si un partido se anota en la jornada
    equivocada, alguien aparece dos veces ahi y alguien falta en la de al lado.
    """
    porjornada: dict[str, Counter] = {}
    for p in ps:
        if p.fase == "zonas" and p.jornada:
            c = porjornada.setdefault(p.jornada, Counter())
            c[p.local] += 1
            c[p.visita] += 1

    avisos = []
    for jornada, cuenta in sorted(porjornada.items(), key=_nro):
        repiten = [e for e, n in cuenta.items() if n > 1]
        if repiten:
            avisos.append(Aviso(f"{jornada}: alguien juega dos veces",
                                ", ".join(sorted(repiten)[:4])))
    return avisos


def _nro(kv) -> int:
    m = re.search(r"(\d+)", kv[0])
    return int(m.group(1)) if m else 0


def cadena_de_llaves(ps: list[Partido]) -> list[Aviso]:
    """EL chequeo fuerte: cada ganador de la eliminacion reaparece despues.

    Es autocontenido -- no necesita saber cual era el cuadro. Si el parseo corrio
    una columna o invento un marcador, la cadena se corta enseguida. Se saltea el
    ultimo dia (la final no tiene ronda siguiente) y los partidos por el tercer
    puesto, que los juegan los PERDEDORES.
    """
    elim = sorted([p for p in ps if p.fase == "eliminacion" and p.fecha],
                  key=lambda p: p.fecha)
    if len(elim) < 3:
        return []

    por_dia: dict[str, list[Partido]] = {}
    for p in elim:
        por_dia.setdefault(p.fecha, []).append(p)
    dias = sorted(por_dia)

    avisos = []
    for i, dia in enumerate(dias[:-1]):
        siguientes = {e for d in dias[i + 1:] for p in por_dia[d]
                      for e in (p.local, p.visita)}
        if not siguientes:
            continue
        for p in por_dia[dia]:
            gana = _ganador(p)
            if gana and gana not in siguientes:
                # puede ser una final, o un 3er puesto: solo se avisa
                avisos.append(Aviso(
                    "un ganador de eliminacion no reaparece",
                    f"{p.fecha} {p.local} {p.goles_local}-{p.goles_visita} {p.visita} "
                    f"-> gano {gana}, que no juega despues", grave=False))
    return avisos


def _ganador(p: Partido) -> str:
    if p.goles_local > p.goles_visita:
        return p.local
    if p.goles_visita > p.goles_local:
        return p.visita
    if p.penales_local is not None:
        return p.local if p.penales_local > p.penales_visita else p.visita
    return ""


CHEQUEOS = [campos_completos, nombres_en_el_padron,
            penales_solo_en_empates, sin_duplicados,
            nadie_juega_contra_si_mismo, todos_tienen_zona, zonas_completas,
            una_vez_por_jornada, cadena_de_llaves]


def revisar(ps: list[Partido]) -> list[Aviso]:
    """Corre todos los chequeos. Devuelve los avisos, graves primero."""
    avisos = [a for chequeo in CHEQUEOS for a in chequeo(ps)]
    return sorted(avisos, key=lambda a: not a.grave)

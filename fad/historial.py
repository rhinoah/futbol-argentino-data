#!/usr/bin/env python3
"""
fad/historial.py
================
El testigo que faltaba: **la tabla de posiciones de la propia pagina, pero la del
dia del partido**.

EL PROBLEMA QUE RESUELVE. El arbitro de siempre en este repo es la tabla de
posiciones: sumar la grilla tiene que dar sus PJ/GF/GC. Funciona solo si la tabla
es una afirmacion INDEPENDIENTE de la grilla, y cuando una sola mano escribe las
dos, un error se propaga a las dos y el chequeo lo bendice. Ahi la aritmetica deja
de discriminar y no queda testigo: es el pendiente que el TODO llamaba "fechar un
desacuerdo" -- ningun chequeo puede decir CUANDO la pagina cambio de opinion.

QUE LO ARBITRA. Las paginas de temporada se editan EN VIVO, fecha por fecha, asi
que la tabla de hace quince anios no es la de hoy: es lo que un editor cargo la
noche del partido, antes de que nada derivara. El delta entre las dos revisiones
que rodean un partido dice que resultado se anoto esa noche.

Y LO QUE CONTESTA NO ES "CUAL ES EL MARCADOR", sino la pregunta del pendiente:
si la pagina cambio de opinion y cuando. Son dos hallazgos y hay que separarlos,
porque se parecen y no sirven para lo mismo:

  el historial DIFIERE de la grilla de hoy -> LA PAGINA DERIVO, y el par de
      revisiones fecha cuando. El marcador de esa noche gana: la grilla de hoy
      arrastra una edicion posterior. Es el caso Platense -- 0-0 esa noche, 1-1 hoy.
  el historial COINCIDE con la grilla de hoy -> NO derivo. El error, si lo hay, es
      ORIGINAL, y del historial no se recupera nada: hace falta una fuente de
      afuera. Es el caso Huracan vs Defensa y Justicia 2011-12, declarado 2-3 con
      el timeline de ESPN y el archivo del club; el historial dice 1-3 y no lo
      contradice, dice que ese 1-3 se cargo asi la primera noche.

Confundir los dos es el error facil: leer "el historial dice 1-3" como si
desmintiera una conclusion, cuando lo que hace es fecharla.

  30/08 03:30 UTC   Platense PJ 5, 2-4   |   Estudiantes PJ 5, 7-2
  31/08 05:29 UTC   Platense PJ 6, 2-4   |   Estudiantes PJ 6, 7-2

Los dos clubes suman un partido y LOS GOLES NO SE MUEVEN: es un 0-0, anotado por
el que estaba mirando. Y de paso FECHA EL PARTIDO, porque el par de timestamps lo
encierra.

COMO SE ACORRALA. No se piden dos instantes escritos a mano -- la revision de ese
caso esta a las 05:29:54 y pedir "05:29:00" devuelve la anterior, en silencio --.
Se pide la LISTA de revisiones de una ventana alrededor del dia, y se busca el
salto donde los dos clubes suman exactamente un partido. Si en la ventana entraron
varias fechas, se parte al medio hasta aislar una: PJ solo crece, asi que la
busqueda binaria vale y cuesta log(n) descargas en vez de n.

LA LOGICA NO TOCA LA RED. `arbitrar` recibe una funcion `tabla_de(revid)` y no
sabe de donde sale: asi se prueba entera sin internet, que es la regla de los
tests de este repo. La red vive en `revisiones` y `tabla_en`, que son dos llamadas
a la API sin logica adentro.

NO CORRE EN EL BUILD. Es una herramienta para arbitrar UN caso y escribir la
conclusion en `correcciones.py`, no un chequeo diario: son varias descargas por
partido y la respuesta no cambia nunca -- una revision vieja es inmutable.

    python -m fad.historial "Campeonato de Primera B 2010-11 (Argentina)" \
                            "Platense" "Estudiantes (BA)" 2010-08-30 --dice 1-1
"""
from __future__ import annotations

import json
import urllib.parse
from dataclasses import dataclass
from datetime import date, timedelta

from fad import posiciones, wiki


@dataclass(frozen=True)
class Revision:
    """Una revision de la pagina: su numero y cuando se guardo (UTC)."""
    revid: int
    cuando: str          # ISO 8601 con Z, tal como lo da la API


@dataclass(frozen=True)
class Veredicto:
    """Lo que el historial dice de un partido, o por que no dice nada.

    `marcador` es `None` cuando el historial no alcanza. NO es un fracaso del
    mecanismo: una pagina que se escribio entera despues del torneo no tiene la
    tabla del dia, y decirlo es la respuesta correcta. Inventar un marcador
    cuando el delta no aisla un partido seria exactamente el error que este
    modulo viene a evitar.
    """
    marcador: tuple[int, int] | None
    antes: Revision | None
    despues: Revision | None
    porque: str

    def __str__(self) -> str:
        if self.marcador is None:
            return f"sin veredicto: {self.porque}"
        return (f"{self.marcador[0]}-{self.marcador[1]}  "
                f"(entre {self.antes.cuando} y {self.despues.cuando}) — {self.porque}")

    def contra(self, dice: tuple[int, int]) -> str:
        """Que significa el veredicto al lado de lo que la grilla dice HOY.

        Es la mitad que contesta el pendiente. Ver la cabecera del modulo: el mismo
        numero significa una cosa u otra segun coincida o no con la grilla de hoy, y
        leerlo mal --tomar el `1-3` del historial como si desmintiera una conclusion
        de 2-3-- es el error facil.
        """
        if self.marcador is None:
            return f"sin veredicto: {self.porque}"
        if self.marcador == dice:
            return (f"LA PAGINA NO CAMBIO DE OPINION: el {dice[0]}-{dice[1]} se cargo "
                    f"asi la primera noche, entre {self.antes.cuando} y "
                    f"{self.despues.cuando}. Si esta mal, el error es ORIGINAL y del "
                    f"historial no se recupera nada: hace falta una fuente de afuera.")
        return (f"LA PAGINA DERIVO. Esa noche se cargo "
                f"{self.marcador[0]}-{self.marcador[1]} y hoy dice {dice[0]}-{dice[1]}; "
                f"el cambio entro DESPUES del {self.despues.cuando}. El de esa noche lo "
                f"escribio el que estaba mirando, antes de que nada se propagara.")


def revisiones(titulo: str, desde: date, hasta: date) -> list[Revision]:
    """Las revisiones de la pagina entre las dos fechas, de la mas vieja a la mas nueva.

    `rvend` es el borde viejo y `rvstart` el nuevo -- al reves de lo que se lee --
    porque la API va hacia atras. Se piden 500, que es el maximo de un pedido sin
    continuacion: una ventana de dias no llega ni cerca, y si llegara es que la
    ventana esta mal elegida y conviene enterarse.
    """
    url = (f"{wiki.API}?action=query&prop=revisions"
           f"&titles={urllib.parse.quote(titulo)}"
           f"&rvstart={urllib.parse.quote(hasta.isoformat() + 'T23:59:59Z')}"
           f"&rvend={urllib.parse.quote(desde.isoformat() + 'T00:00:00Z')}"
           "&rvdir=older&rvlimit=500&rvprop=ids%7Ctimestamp"
           "&formatversion=2&format=json")
    paginas = json.loads(wiki._pedir(url)).get("query", {}).get("pages", [])
    if not paginas or "revisions" not in paginas[0]:
        return []
    return [Revision(r["revid"], r["timestamp"])
            for r in reversed(paginas[0]["revisions"])]


def tabla_en(titulo: str, revid: int, pagina: str = "") -> dict:
    """La tabla de posiciones tal como estaba en esa revision.

    Se cachea en disco por `revid` y no por fecha: una revision vieja es inmutable,
    asi que el cache nunca queda viejo. Es lo que hace barata la busqueda binaria
    cuando se arbitra mas de un partido de la misma temporada.
    """
    destino = wiki.CACHE / "revisiones" / f"{revid}.wiki"
    if destino.exists():
        texto = destino.read_text(encoding="utf-8")
    else:
        url = (f"{wiki.API}?action=query&prop=revisions&revids={revid}"
               "&rvprop=content&rvslots=main&formatversion=2&format=json")
        paginas = json.loads(wiki._pedir(url))["query"]["pages"]
        texto = paginas[0]["revisions"][0]["slots"]["main"]["content"]
        destino.parent.mkdir(parents=True, exist_ok=True)
        destino.write_text(texto, encoding="utf-8")
    return posiciones.tabla(texto, pagina=pagina or titulo)


def ventana(fecha: str, dias: int = 2) -> tuple[date, date]:
    """El rango de dias a mirar alrededor de un partido.

    Asimetrico a proposito: se abre UN dia mas para atras que para adelante. El
    borde de abajo tiene que caer antes de que el partido entre, y la tabla se
    edita a la noche -- que en UTC ya es el dia siguiente --, asi que un borde
    justo cae del lado equivocado. Hacia adelante alcanza con llegar a la primera
    edicion posterior.
    """
    d = date.fromisoformat(fecha)
    return d - timedelta(days=dias + 1), d + timedelta(days=dias)


def arbitrar(local: str, visita: str, revs: list[Revision], tabla_de) -> Veredicto:
    """Que marcador dice el historial que se cargo para este partido.

    `tabla_de(revid)` devuelve la tabla de esa revision. Va inyectada para que la
    logica se pruebe sin red.

    EL PARTIDO SE AISLA POR PJ, que es lo unico que no admite interpretacion: si
    entre dos revisiones los dos clubes suman EXACTAMENTE un partido, lo unico que
    entro en el medio es este. Ahi el delta de goles es el marcador.

    Y SE EXIGE QUE LOS DOS LADOS COINCIDAN. El delta del local -- goles a favor,
    goles en contra -- tiene que ser el espejo del delta del visitante. Si no lo
    es, en el medio entro algo mas que este partido y no hay veredicto: es la
    misma cardinalidad que el repo le exige a cualquier emparejamiento.
    """
    if len(revs) < 2:
        return Veredicto(None, None, None,
                         "la ventana no tiene dos revisiones que comparar")

    def pj(t, club):
        fila = t.get(club)
        return None if fila is None else fila[0]

    primera, ultima = tabla_de(revs[0].revid), tabla_de(revs[-1].revid)
    for club, t, cual in ((local, primera, "primera"), (visita, primera, "primera"),
                          (local, ultima, "ultima"), (visita, ultima, "ultima")):
        if pj(t, club) is None:
            return Veredicto(None, None, None,
                             f"{club!r} no esta en la tabla de la {cual} revision "
                             f"de la ventana")
    salto = (pj(ultima, local) - pj(primera, local),
             pj(ultima, visita) - pj(primera, visita))
    if salto != (1, 1):
        return Veredicto(None, None, None,
                         f"en la ventana los dos clubes suman {salto[0]} y {salto[1]} "
                         f"partidos, y hace falta exactamente uno cada uno: "
                         f"{'no entro' if 0 in salto else 'entro mas de un partido'}")

    # BUSQUEDA BINARIA sobre "la tabla ya cuenta este partido". PJ solo crece, asi
    # que la condicion es monotona y el corte existe. Cuesta log(n) descargas: una
    # ventana de treinta revisiones se resuelve con cinco.
    bajo, alto = 0, len(revs) - 1
    while alto - bajo > 1:
        medio = (bajo + alto) // 2
        # UNA REVISION ILEGIBLE NO PUEDE QUEDAR DE BORDE. Una a medio guardar --la
        # tabla rota, el club sin fila-- no invalida el arbitraje, pero tampoco sirve
        # de extremo: los dos bordes se leen al final para sacar el delta. Se corre
        # el punto medio HACIA `bajo`, que es el unico que ya se sabe legible.
        #
        # Si no hay ninguna legible en el tramo, el tramo se da por agotado y el
        # corte queda donde estaba: la ventana sale mas grande, nunca mas chica, y
        # los dos bordes siguen siendo los que se verificaron al entrar.
        while medio > bajo and (pj(tabla_de(revs[medio].revid), local) is None
                                or pj(tabla_de(revs[medio].revid), visita) is None):
            medio -= 1
        if medio == bajo:
            break
        t = tabla_de(revs[medio].revid)
        ya = (pj(t, local) > pj(primera, local)
              and pj(t, visita) > pj(primera, visita))
        bajo, alto = (bajo, medio) if ya else (medio, alto)

    antes, despues = tabla_de(revs[bajo].revid), tabla_de(revs[alto].revid)
    dl = (despues[local][1] - antes[local][1], despues[local][2] - antes[local][2])
    dv = (despues[visita][1] - antes[visita][1], despues[visita][2] - antes[visita][2])
    if dl != (dv[1], dv[0]):
        return Veredicto(None, revs[bajo], revs[alto],
                         f"los dos lados no coinciden: el local se mueve {dl} y el "
                         f"visitante {dv}, asi que en el medio entro algo mas")
    if min(dl) < 0:
        return Veredicto(None, revs[bajo], revs[alto],
                         f"el delta de goles es negativo {dl}: la edicion corrigio "
                         f"otra cosa ademas de cargar este partido")
    return Veredicto(dl, revs[bajo], revs[alto],
                     "los dos clubes suman un partido entre esas dos revisiones y "
                     "el delta de goles es el mismo de los dos lados")

# --------------------------------------------------------------------------
# El CLI. Va aca y no en un ejecutable aparte porque es una cascara de veinte
# lineas sobre las tres funciones de arriba, y separarlo obligaria a repetir la
# explicacion de que significa cada veredicto.

def _main(argv=None) -> int:
    import argparse

    ap = argparse.ArgumentParser(
        prog="python -m fad.historial",
        description="Que marcador se cargo la noche de un partido, segun el "
                    "historial de la propia pagina.")
    ap.add_argument("pagina", help="titulo exacto en es.wikipedia.org")
    ap.add_argument("local")
    ap.add_argument("visita")
    ap.add_argument("fecha", help="el dia del partido, YYYY-MM-DD")
    ap.add_argument("--dias", type=int, default=2,
                    help="cuantos dias mirar alrededor (default 2)")
    ap.add_argument("--dice", metavar="A-B",
                    help="lo que la grilla de la pagina dice HOY. Con esto el "
                         "veredicto contesta si la pagina DERIVO o si el marcador es "
                         "el ORIGINAL, que son dos hallazgos distintos")
    args = ap.parse_args(argv)

    desde, hasta = ventana(args.fecha, args.dias)
    revs = revisiones(args.pagina, desde, hasta)
    print(f"  ventana {desde} .. {hasta}: {len(revs)} revisiones")
    if not revs:
        print("  La pagina no se edito en esos dias. Si el torneo es viejo, puede que")
        print("  se haya escrito entera despues: ahi no hay tabla del dia que mirar.")
        return 1

    bajadas: list[int] = []

    def tabla_de(revid: int):
        bajadas.append(revid)
        return tabla_en(args.pagina, revid, args.pagina)

    v = arbitrar(args.local, args.visita, revs, tabla_de)
    print(f"  revisiones descargadas: {len(set(bajadas))}")
    print()
    print(f"  {args.local} vs {args.visita}, {args.fecha}")
    print(f"  {v}")
    if v.marcador is not None:
        print()
        print(f"  Y de paso lo fecha: la tabla no lo tenia el {v.antes.cuando} y ya lo")
        print(f"  tenia el {v.despues.cuando}. Son UTC; Argentina es UTC-3.")
    if args.dice:
        a, b = args.dice.split("-")
        print()
        print(f"  {v.contra((int(a), int(b)))}")
    return 0 if v.marcador is not None else 1


if __name__ == "__main__":
    import io
    import sys

    sys.stdout = io.TextIOWrapper(sys.stdout.buffer, encoding="utf-8", errors="replace")
    raise SystemExit(_main())

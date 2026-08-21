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
    return avisos


def fechas_presentes(ps: list[Partido]) -> list[Aviso]:
    """Los partidos sin fecha, que NO entran al dataset.

    Un partido que no se puede ubicar en el tiempo no sirve para nada -- y el
    esquema promete una fecha en cada fila --, asi que se deja afuera. Pero se
    dice cuales y como venia escrita la celda, porque las dos causas se parecen y
    no son lo mismo: puede ser una rareza de la fuente (Sansinena se retiro del
    Federal A 2024 y sus partidos quedaron sin fecha) o puede ser el parser
    leyendo mal un formato nuevo.

    NO es grave, y es a proposito: ocho filas de cinco mil no justifican frenar
    el build. Si algun dia son ochocientas, el que avisa es otro -- la guarda de
    `dataset.regresiones`, que compara contra lo de ayer y no deja escribir un
    dataset que se achico.
    """
    sin = [p for p in ps if not p.fecha]
    if not sin:
        return []
    muestra = "; ".join(f"{p.local} vs {p.visita} (crudo: {p.fecha_cruda!r})"
                        for p in sin[:3])
    return [Aviso(f"{len(sin)} partidos sin fecha, quedan afuera", muestra, grave=False)]


def nombres_en_el_padron(ps: list[Partido]) -> list[Aviso]:
    """Todo club tiene que estar en `equipos.PADRON`.

    Es grave y corta el build a proposito. Un nombre que el padron no conoce es
    casi siempre un club que asciende o un torneo que se suma, y si se deja pasar
    entra al dataset como un equipo nuevo: "Talleres" y "Talleres (C)" pasan a ser
    dos clubes con media historia cada uno, y nadie lo nota. Cuesta un renglon en
    el padron; se avisa una vez.
    """
    raros = sorted({n for p in ps for n in (p.local, p.visita)
                    if n and not equipos.conocido(n)})
    return [Aviso("club que no esta en el padron",
                  f"{len(raros)}: {', '.join(raros[:6])}"
                  f"{' ...' if len(raros) > 6 else ''}")] if raros else []


def _serie_igualada(p: Partido, ps: list[Partido]) -> bool:
    """Si `p` es una pata de una serie a dos partidos empatada en el global."""
    par = frozenset((p.local, p.visita))
    serie = [q for q in ps
             if q.fase == "eliminacion" and q.llave == p.llave
             and q.jornada == p.jornada and frozenset((q.local, q.visita)) == par]
    if len(serie) != 2:
        return False
    a = sum(q.goles_local if q.local == p.local else q.goles_visita for q in serie)
    b = sum(q.goles_local if q.local == p.visita else q.goles_visita for q in serie)
    return a == b


def penales_solo_en_empates(ps: list[Partido]) -> list[Aviso]:
    """Una tanda de penales sobre un partido que no termino empatado es la firma
    de haber leido el entretiempo como si fuera la tanda.

    SALVO en una serie a dos partidos. Ahi la tanda no es del partido sino de la
    SERIE, y se patea al final de la vuelta, que no tiene por que haber quedado
    empatada: la final de la Primera C 2021 fue Argentino de Merlo 2-0 Ituzaingo
    y despues Ituzaingo 2-0 Argentino de Merlo, 2-2 global, penales 4-2. La
    plantilla cuelga la tanda de la pata donde se pateo, y esta bien.

    El caso no era hipotetico ni nuevo: eran once partidos, y todos aparecieron
    de golpe cuando el parser empezo a leer las plantillas que antes se le
    escapaban. Once de once quedaron explicados por su serie; ninguno era el bug
    del entretiempo. Por eso la excepcion se pide ESTRECHA -- la serie tiene que
    existir, ser de exactamente dos partidos y estar igualada -- en vez de
    aflojar el chequeo para los partidos de eliminacion en general.
    """
    return [Aviso("penales en un partido que no fue empate",
                  f"{p.local} {p.goles_local}-{p.goles_visita} {p.visita} "
                  f"(pen {p.penales_local}-{p.penales_visita})")
            for p in ps
            if p.penales_local is not None and p.goles_local != p.goles_visita
            and not (p.fase == "eliminacion" and _serie_igualada(p, ps))]


def sin_duplicados(ps: list[Partido]) -> list[Aviso]:
    """El mismo cruce dos veces en la misma fecha es una fila leida dos veces."""
    # Solo los que tienen fecha. Los que no la tienen se descartan antes de
    # llegar al CSV, asi que no pueden duplicar nada -- pero comparten la clave
    # vacia, y entonces cualquier par que la fuente escriba dos veces con el
    # mismo local colapsa en "partido duplicado". Eso convertia la caida de la
    # segunda fuente, que es un aviso leve, en tres errores GRAVES que frenaban
    # el build entero: la B Nacional 2009-10 tiene tres pares asi.
    c = Counter((p.fecha, p.local, p.visita) for p in ps if p.fecha)
    return [Aviso("partido duplicado", f"{f} {l} vs {v} ({n} veces)")
            for (f, l, v), n in c.items() if n > 1]


def nadie_juega_contra_si_mismo(ps: list[Partido]) -> list[Aviso]:
    """Sintoma clasico de columnas corridas."""
    return [Aviso("un equipo contra si mismo", f"{p.fecha} {p.local}")
            for p in ps if p.local and p.local == p.visita]


def todos_tienen_zona(ps: list[Partido]) -> list[Aviso]:
    """O TODOS los partidos de grupos tienen zona, o ninguno.

    Un encabezado que no se reconocio no deja el campo en blanco: la zona se
    arrastra de fila en fila, asi que lo llena con la etiqueta anterior. Ya paso
    con los bloques "Interzonal". Lo que delata ese caso es la MEZCLA -- unos
    partidos con zona y otros sin -- y no el vacio.

    Un torneo entero sin zonas es perfectamente normal y no se toca: de 2017 a
    2024 el campeonato fue de zona unica, veintipico de equipos en una sola
    tabla. Exigirle una zona a eso convertia nueve temporadas correctas en nueve
    errores graves que no dejaban escribir el dataset.

    Y la mezcla se mira DENTRO DE CADA FASE, no en toda la pagina. Una pagina
    puede tener una fase con grupos y otra sin, y es normal: la Primera B 2020
    reparte la "Fase segundo ascenso" en Grupo A y Grupo B, y la "Fase primer
    ascenso" es un solo grupo. Comparando las dos juntas, la segunda parecia
    quince partidos sin zona entre treinta con zona.
    """
    porfase: dict[str, list[Partido]] = {}
    for p in ps:
        if p.fase == "zonas":
            porfase.setdefault(p.llave, []).append(p)

    avisos = []
    for llave, zonas in sorted(porfase.items()):
        sin = [p for p in zonas if not p.zona]
        if not sin or len(sin) == len(zonas):
            continue
        avisos.append(Aviso("hay partidos de zona con zona y otros sin",
                            f"{llave + ': ' if llave else ''}{len(sin)} de {len(zonas)} "
                            f"sin zona, p.ej. {sin[0].fecha} {sin[0].local} vs {sin[0].visita}"))
    return avisos


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
        else:
            # Una vuelta o dos: el ascenso juega ida y vuelta, asi que 19 equipos
            # dan 171 partidos o 342, y las dos cosas estan bien. Lo que no puede
            # es quedar en el medio.
            n = len(jugados)
            una_vuelta = n * (n - 1) // 2
            if una_vuelta and len(partidos) % una_vuelta:
                avisos.append(Aviso(
                    f"{zona}: no es un todos-contra-todos completo",
                    f"{n} equipos deberian jugar {una_vuelta} partidos (una vuelta) "
                    f"o {una_vuelta * 2} (ida y vuelta), hay {len(partidos)}",
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
    # La clave es (zona, jornada) y no solo la jornada: la "Fecha 1" de la Zona A
    # no es la misma que la de la Zona B, y la de `== Torneo Apertura ==` no es la
    # misma que la de `== Torneo Clausura ==` -- Primera B y C meten los dos
    # torneos en una pagina. Agrupando solo por el numero, todos los equipos
    # parecian jugar dos veces por fecha, y eran ~90 avisos graves de mentira.
    # La clave incluye tambien `llave` -- la seccion de nivel 2 -- porque el
    # encabezado de tabla pisa a la seccion y sin eso se pierden: la Copa de la
    # Liga 2020 tuvo Fase Campeon y Fase Complementacion, CADA UNA con su Grupo A
    # y su Fecha 1, y los mismos equipos en las dos.
    porjornada: dict[tuple[str, str, str], Counter] = {}
    for p in ps:
        if p.fase == "zonas" and p.jornada:
            c = porjornada.setdefault((p.llave, p.zona, p.jornada), Counter())
            c[p.local] += 1
            c[p.visita] += 1

    avisos = []
    for (llave, zona, jornada), cuenta in sorted(porjornada.items(),
                                                 key=lambda kv: _nro(kv[0])):
        repiten = [e for e, n in cuenta.items() if n > 1]
        if repiten:
            donde = " ".join(x for x in (llave, zona) if x)
            avisos.append(Aviso(f"{donde + ' ' if donde else ''}{jornada}: alguien juega dos veces",
                                ", ".join(sorted(repiten)[:4])))
    return avisos


# La zona puede venir calificada con su fase -- "Primera fase - Zona 1" -- cuando
# la pagina reusa el rotulo en dos fases distintas. Anclando en el arranque, esas
# dejaban de contar como zonas y este chequeo se callaba justo en la pagina que
# lo motivo: los cuatro partidos de Union que cuenta el docstring de abajo.
_ES_ZONA = re.compile(r"(?i)^(.*- )?(zona|grupo)\b")


def una_zona_por_club(ps: list[Partido]) -> list[Aviso]:
    """Un club juega en UNA sola zona de cada fase.

    Es la definicion de zona: los equipos se reparten y cada uno juega contra los
    de la suya. Que un club aparezca en dos no es raro, es imposible.

    ES EL UNICO CHEQUEO QUE VE UN NOMBRE VALIDO PERO EQUIVOCADO. Todos los demas
    controlan que los clubes esten en el padron, y contra este error no sirven:
    en el Torneo Argentino A 2010-11 hay cuatro partidos de Union de Mar del
    Plata escritos "Union (S)", que es Union de SUNCHALES -- un club real, con su
    articulo enlazado, que ademas jugaba ese mismo torneo en otra zona. Pasa por
    el padron sin una queja, y los cuatro partidos quedan asignados al club
    equivocado.

    Lo delata el reparto: a Union (MdP) le quedan 24 partidos en su zona cuando
    los demas tienen 27 o 28, y a Union (S) le sobran exactamente esos cuatro en
    una zona que no es la suya.

    SOLO cuenta las zonas de verdad, las que se llaman "Zona X" o "Grupo X".
    "Interzonal" es una fecha CRUZADA a proposito -- Primera juega una por rueda
    contra el clasico de la otra zona -- y contarla daba 344 avisos falsos, uno
    por cada club de cada torneo con interzonales.
    """
    donde: dict[tuple[str, str], Counter] = {}
    for p in ps:
        if p.fase != "zonas" or not _ES_ZONA.match(p.zona or ""):
            continue
        for club in (p.local, p.visita):
            donde.setdefault((p.llave, club), Counter())[p.zona] += 1

    avisos = []
    for (llave, club), zonas in sorted(donde.items()):
        if len(zonas) > 1:
            donde_dice = " ".join(f"{z} ({n})" for z, n in sorted(zonas.items()))
            avisos.append(Aviso(f"{club} juega en dos zonas de la misma fase",
                                f"{llave + ': ' if llave else ''}{donde_dice}. "
                                f"La zona con menos partidos suele ser el club "
                                f"equivocado, escrito con un nombre que existe"))
    return avisos


def localias_repartidas(ps: list[Partido]) -> list[Aviso]:
    """En un todos-contra-todos, un par que se cruza N veces (N par) juega N/2 de
    local cada uno.

    Es una propiedad del fixture, no de los datos: si Ferro visita a Union, en la
    otra rueda Union visita a Ferro. Que los dos partidos figuren con el mismo
    local es imposible, y por eso el chequeo no necesita ninguna fuente externa.

    Agarra DOS cosas distintas, y la segunda es la que no esperaba:

    1. Una localia dada vuelta en la fuente. Wikipedia pone a Ferro de local
       contra Union en las fechas 6 y 25 de la B Nacional 2009-10; worldfootball
       dice que la 25 la jugo Union en su cancha, y el fixture le da la razon.
    2. Un club escrito de dos formas. Si la mitad de los partidos de un club se
       anotan bajo otro nombre, cada mitad queda con un solo local y las dos
       saltan. Asi aparecio que "San Jorge (S)" era "San Jorge (T)" mal tipeado
       -- y ese estaba EN el padron como club propio, o sea que
       `nombres_en_el_padron` lo daba por bueno. Este chequeo no le pregunta al
       padron nada, y por eso lo vio.

    Va como aviso y no como error: lo que denuncia suele estar mal en la fuente,
    y no es razon para frenar el build de todos los dias. Sobre los 32.960
    partidos ya cargados da 2 avisos, los dos del mismo typo.
    """
    # Solo la fase regular: en el Reducido de la Primera Nacional 2018 Arsenal y
    # Sarmiento se cruzaron dos veces con el mismo local, y esta perfecto -- una
    # fue por la fecha 10 y la otra un desempate en cancha neutral. Se distinguen
    # porque los partidos del todos-contra-todos tienen jornada y esos no.
    locales: dict[tuple, Counter] = {}
    for p in ps:
        if p.fase != "zonas" or not p.jornada or not p.local or not p.visita:
            continue
        k = (p.llave, p.zona, tuple(sorted((p.local, p.visita))))
        locales.setdefault(k, Counter())[p.local] += 1

    avisos = []
    for (llave, zona, par), cuenta in sorted(locales.items(), key=lambda kv: kv[0][2]):
        n = sum(cuenta.values())
        # Con un numero impar de cruces el reparto no puede ser parejo y no hay
        # nada que denunciar: pasa en los torneos de rueda y media.
        if n % 2 or all(v == n // 2 for v in cuenta.values()) and len(cuenta) == 2:
            continue
        donde = " ".join(x for x in (llave, zona) if x)
        avisos.append(Aviso(f"{donde + ': ' if donde else ''}"
                            f"{par[0]} y {par[1]} se cruzan {n} veces y la localia no se reparte",
                            ", ".join(f"{e} de local {v}" for e, v in sorted(cuenta.items())),
                            grave=False))
    return avisos


def _nro(clave) -> tuple:
    llave, zona, jornada = clave
    m = re.search(r"(\d+)", jornada)
    return (llave, zona, int(m.group(1)) if m else 0)


def jornadas_sin_huecos(ps: list[Partido]) -> list[Aviso]:
    """Si estan la Fecha 1 y la 23, tienen que estar todas las del medio.

    No siempre es culpa del parser. La pagina del campeonato 2019-20 no tiene la
    Fecha 4: no esta escrita, faltan sus 12 partidos en la fuente. Igual hay que
    decirlo, porque un hueco en el medio de una temporada es indistinguible de
    "el modelo no vio esos partidos" para quien use el dataset.
    """
    nums = sorted({n for p in ps if p.fase == "zonas" and (n := _numero(p.jornada))})
    if len(nums) < 2:
        return []
    faltan = [i for i in range(nums[0], nums[-1] + 1) if i not in nums]
    return [Aviso("faltan jornadas en el medio",
                  f"hay de la {nums[0]} a la {nums[-1]}, faltan: "
                  f"{', '.join(map(str, faltan))}", grave=False)] if faltan else []


def anios_bien_asignados(ps: list[Partido]) -> list[Aviso]:
    """Una jornada no puede caer medio anio ANTES que la anterior.

    Las paginas escriben el dia y el mes pero no el anio, asi que en una
    temporada que cruza el calendario hay que decidirlo por el mes. Cuando ese
    corte esta mal, una jornada entera se va un anio de lugar: con el corte en
    agosto, la Fecha 1 del campeonato 2019-20 -- que se jugo el 26 de julio de
    2019 -- quedaba fechada en julio de 2020, al final de la temporada. Los 12
    partidos coherentes entre si, el marcador bien, y un anio de diferencia.

    El umbral es generoso a proposito. Una jornada postergada se corre semanas o
    algun mes -- la Fecha 9 del Apertura 2026 se jugo entera dos meses despues de
    la 10 y esta perfecta --, pero medio anio para atras no es una postergacion,
    es un anio mal puesto.
    """
    porjornada: dict[int, list[str]] = {}
    for p in ps:
        if p.fase == "zonas" and p.fecha and (n := _numero(p.jornada)):
            porjornada.setdefault(n, []).append(p.fecha)

    avisos = []
    previo = None
    for n in sorted(porjornada):
        medio = sorted(porjornada[n])[len(porjornada[n]) // 2]
        if previo and _dias(medio, previo[1]) > 180:
            avisos.append(Aviso(
                "una jornada cae medio anio antes que la anterior",
                f"Fecha {n} en {medio} contra Fecha {previo[0]} en {previo[1]}; "
                f"parece un anio mal asignado, no una postergacion"))
        previo = (n, medio)
    return avisos


def _numero(jornada: str) -> int:
    m = re.search(r"(\d+)", jornada or "")
    return int(m.group(1)) if m else 0


def _dias(despues: str, antes: str) -> int:
    """Cuantos dias esta `despues` ANTES de `antes` (positivo = va para atras)."""
    from datetime import date
    return (date.fromisoformat(antes) - date.fromisoformat(despues)).days


def cadena_de_llaves(ps: list[Partido]) -> list[Aviso]:
    """EL chequeo fuerte: el que juega una ronda gano la anterior.

    Es autocontenido -- no necesita saber cual era el cuadro. Sale de como
    funciona una eliminacion directa, y si el parseo corrio una columna, invirtio
    unos penales o invento un marcador, aparece alguien en cuartos que segun los
    datos perdio en octavos.

    LA DIRECCION IMPORTA. La primera version preguntaba lo simetrico -- "cada
    ganador, reaparece despues?" -- y sobre un torneo terminado da igual, pero
    sobre uno en curso no: los 16 ganadores de dieciseisavos de la Copa 2026
    todavia no jugaron su octavos, asi que tiraba 14 avisos por dia hasta
    noviembre. Un chequeo que grita todos los dias deja de leerse, y ahi ya no
    sirve para nada.

    Preguntado al reves valida lo que HAY en vez de exigir lo que todavia no se
    jugo, y no pierde nada: el mismo error que rompia una punta rompe la otra.
    """
    elim = [p for p in ps if p.fase == "eliminacion" and p.fecha]
    if len(elim) < 3:
        return []
    # Cada cuadro por separado. Una pagina del ascenso trae la final del
    # campeonato, el torneo reducido y a veces la definicion de un ascenso: son
    # tres eliminaciones que no se encadenan entre si, y mezclandolas el chequeo
    # tiraba 21 avisos sobre datos correctos.
    porllave: dict[str, list[Partido]] = {}
    for p in elim:
        porllave.setdefault(p.llave, []).append(p)
    if len(porllave) > 1:
        return [a for parte in porllave.values() for a in cadena_de_llaves(parte)]

    grupos = _por_ronda(elim)
    if grupos is None:
        # UN CUADRO DE UNA SOLA RONDA NO TIENE CADENA. No se saltea nada porque no
        # hay nada que saltear: la pregunta de este chequeo es si el que juega una
        # ronda gano la anterior, y con una sola ronda no hay anterior. Decir que
        # se salteo manda a buscar un problema que no existe, y son ocho llaves
        # -- promociones, permanencias, desempates -- que rotulan su unica ronda
        # con algo que no es un nombre de ronda ("Promocion", "Partidos", vacio).
        if len({p.jornada for p in elim}) < 2:
            return []
        # NI TAMPOCO EL QUE SON VARIAS LLAVES EN PARALELO. En una cadena el que gana
        # sigue, asi que dos rondas seguidas comparten por lo menos un club. Si
        # NINGUN par de rondas comparte a nadie, nadie avanzo de una a otra: no se
        # siguen, son eliminatorias independientes bajo un mismo titulo. Pasa en las
        # promociones ("Promocion 1" y "Promocion 2" son dos promociones distintas,
        # no dos rondas) y son diez llaves del corpus.
        #
        # Va con aviso y no callado, al reves que el caso de una sola ronda: aca la
        # falta de cadena es algo que se midio, no algo que se sabe de antemano, y
        # el dia que el parser parta mal un cuadro de verdad se va a ver asi.
        clubes = {}
        for x in elim:
            clubes.setdefault(x.jornada, set()).update({x.local, x.visita} - {""})
        rondas = sorted(clubes)
        if not any(clubes[a] & clubes[b]
                   for i, a in enumerate(rondas) for b in rondas[i + 1:]):
            return [Aviso("el cuadro no es una cadena",
                          f"sus {len(rondas)} rondas no comparten ningun club, asi "
                          "que son llaves independientes y no hay cadena que revisar",
                          grave=False)]
        return [Aviso("no se pudo revisar el cuadro de eliminacion",
                      "hay partidos sin ronda reconocida; el chequeo se salteo",
                      grave=False)]
    avisos = []
    # Los clubes que ya aparecieron en este cuadro, de la primera ronda hasta la
    # anterior. Es lo que separa un error de un repechaje.
    vistos: set[str] = set()
    for (_, previa), (ronda, actual) in zip(grupos, grupos[1:]):
        vistos |= {e for p in previa for e in (p.local, p.visita) if e}
        ganadores = {_ganador(p) for p in previa} - {""}
        if not ganadores:
            continue
        # UN CLUB QUE NUNCA JUGO NO PERDIO NADA. Muchos cuadros reciben gente de
        # afuera por diseno: la Zona Revalida del Argentino A 2004-05 lo dice en
        # su propia fuente -- "losers enter Round 2 Zona Revalida" --, y ahi los
        # cuatro que entran en la segunda ronda no vienen de la primera sino de
        # haber perdido en la otra llave. Acusarlos daba 17 avisos falsos sobre 20.
        #
        # Lo que SI es un error es el que jugo antes y sigue jugando sin haber
        # ganado. Esa distincion calla 30 avisos que eran falsos.
        #
        # UN EMPATE SIN PENALES NO DICE QUIEN PASO. `_ganador` devuelve "" y los
        # DOS clubes quedan afuera de `ganadores`, asi que el que avanzo se
        # denuncia solo. Y avanzo de verdad: en el reducido argentino, si el
        # partido unico termina igualado pasa el mejor ubicado de la tabla, una
        # regla que vive FUERA del partido y que ninguna columna trae. Eran los 3
        # ultimos avisos del Federal A 2023 -- Douglas Haig 0-0, Independiente (C)
        # 1-1 y Ciudad de Bolivar 1-1 --, y los tres estaban bien jugados.
        #
        # Cuando el marcador no alcanza para saberlo, los dos se admiten. Pero no
        # se pierde todo: de una llave igualada pasa UNO, asi que si aparecen LOS
        # DOS en la ronda siguiente sigue siendo un error, y ese se sigue diciendo.
        indecisos: list[frozenset] = [frozenset((p.local, p.visita)) for p in previa
                                      if not _ganador(p) and p.local and p.visita]
        siguen = {e for p in actual for e in (p.local, p.visita) if e}
        excusados = {e for par in indecisos if len(par & siguen) < 2 for e in par}
        frescos = sorted({e for p in actual for e in (p.local, p.visita)
                          if e and e not in vistos})
        if frescos:
            avisos.append(Aviso(
                "entran al cuadro sin venir de la ronda anterior",
                f"{ronda}: {', '.join(frescos)}. No es un error por si mismo -- un "
                f"repechaje recibe a los que perdieron en otra llave --, pero si la "
                f"pagina publicó entera la ronda anterior, entonces falta algo",
                grave=False))
        for p in actual:
            for equipo in (p.local, p.visita):
                if (equipo and equipo not in ganadores and equipo in vistos
                        and equipo not in excusados):
                    avisos.append(Aviso(
                        "juega una ronda sin haber ganado la anterior",
                        f"{ronda}: {equipo} ({p.fecha} vs "
                        f"{p.visita if equipo == p.local else p.local})", grave=False))
    return avisos


# La MISMA ronda escrita de otra manera. Es una lista corta, exacta y cerrada, y
# eso es todo el punto: "Cuartos de final" y "Cuartos" son la misma ronda sin
# ninguna ambiguedad, mientras que "Primera ronda" o "Reválida" NO se pueden
# mapear sin decidir en que escalon de la escalera van, que es justo lo que este
# modulo no hace. Se midio antes de escribirla: de las 51 paginas donde el
# chequeo se apaga, esto destraba UNA -- el Torneo Federal A 2022 --. Las otras
# cincuenta no tienen la ronda escrita en ningun campo, ni en `jornada` ni en
# `llave`, asi que no hay de donde normalizarlas.
#
# Se normaliza SOLO para el chequeo. El dato publicado sigue diciendo lo que dice
# la pagina: `jornada` sale en el CSV y su trabajo es ser fiel, no prolijo.
_SINONIMOS = {
    # Los cuatro ordinales, que unas paginas escriben "fase" y otras "ronda".
    # No es una suposicion: se midio sobre las 136 paginas y NINGUNA usa las dos
    # formas del mismo ordinal, asi que colapsarlas no puede fusionar dos rondas
    # distintas de un mismo torneo -- que seria peor que no revisar, porque
    # compararia contra el conjunto equivocado en vez de abstenerse.
    "primera ronda": "primera fase",
    "segunda ronda": "segunda fase",
    "tercera ronda": "tercera fase",
    "cuarta ronda": "cuarta fase",
    "cuartos de final": "cuartos",
    "octavos de final": "octavos",
    "dieciseisavos de final": "dieciseisavos",
    "treintaidosavos de final": "treintaidosavos",
    "semifinal": "semifinales",
}


def _ronda(jornada: str) -> str:
    """La jornada en el vocabulario de `RONDAS`, para poder ordenarla.

    Ademas de los sinonimos hay dos formas que las paginas le agregan ALREDEDOR
    del nombre de la ronda, y que se sacan siempre que lo que queda sea una ronda
    de verdad. Esa condicion es la que las hace seguras: si al pelarla no queda
    una ronda conocida, no se toca nada y el chequeo se sigue absteniendo.

      - un numero atras, para partir una ronda en sus llaves: "Semifinal 1" y
        "Semifinal 2" son las dos semifinales, no dos rondas. "Llave 1" no se
        toca, porque "Llave" no es una ronda -- y ese es justo el caso donde
        colapsar estaria mal.
      - un prefijo con guion, para decir de que rama del torneo es la ronda:
        "Revalida - Segunda ronda". El Argentino A escribe asi las dos rondas de
        su revalida.

    Destraba cuatro paginas. Se midio que ningun par de jornadas distintas de una
    misma llave cae en el mismo nombre por esto, que seria peor que no revisar:
    compararia contra el conjunto equivocado en vez de abstenerse.
    """
    j = (jornada or "").lower().strip()
    if j in _SINONIMOS:
        return _SINONIMOS[j]
    from fad.parser import RONDAS

    conocidas = {r.lower() for r in RONDAS}

    def pelada(x: str) -> str:
        return _SINONIMOS.get(x, x)

    sin_numero = re.sub(r"\s+\d+$", "", j)
    if sin_numero != j and pelada(sin_numero) in conocidas:
        return pelada(sin_numero)
    sin_rama = re.sub(r"^.+?\s+-\s+", "", j)
    if sin_rama != j and pelada(sin_rama) in conocidas:
        return pelada(sin_rama)
    return j


def _por_ronda(elim: list[Partido]) -> list[tuple[str, list[Partido]]] | None:
    """Agrupa la eliminacion en rondas ordenadas, de la mas lejana a la final.

    Devuelve None si algun partido no trae una ronda reconocida, y NO cae a
    agrupar por fecha. Ese fallback existio y habia que sacarlo: una ronda se
    juega en varios dias -- los octavos del Apertura 2026 se jugaron en dos --, y
    agrupando por dia el segundo dia parece una ronda nueva cuyos participantes
    "no ganaron la anterior". Inventaba errores en datos perfectos.

    Prefiero no revisar y decirlo. Un chequeo salteado en silencio es peor que
    uno ausente: parece que algo se esta mirando.
    """
    from fad.parser import RONDAS

    orden = {r.lower(): i for i, r in enumerate(RONDAS)}
    if not all(_ronda(p.jornada) in orden for p in elim):
        return None
    # Se agrupa por el nombre NORMALIZADO, no por el que trae la pagina. Agrupar
    # por el original dejaba dos grupos distintos con el mismo lugar en el orden
    # -- "Semifinal 1" y "Semifinal 2" --, y entonces el zip de mas abajo los
    # tomaba como rondas consecutivas: el que gana una semifinal aparece jugando
    # la otra sin haberla ganado, y el finalista que salio de la primera aparece
    # llegando a la final sin ganar nada. Cuatro acusaciones falsas en dos
    # paginas, y el bug ya estaba latente para cualquier pagina que escribiera
    # "Cuartos" y "Cuartos de final" en el mismo cuadro.
    grupos: dict[str, list[Partido]] = {}
    nombres: dict[str, set[str]] = {}
    for p in elim:
        r = _ronda(p.jornada)
        grupos.setdefault(r, []).append(p)
        nombres.setdefault(r, set()).add(p.jornada)
    # Para el aviso se muestran los nombres de la pagina, no el normalizado: el
    # que lee tiene que poder encontrar la ronda ahi.
    return sorted(((" / ".join(sorted(nombres[r])), ps) for r, ps in grupos.items()),
                  key=lambda kv: orden[_ronda(kv[0].split(" / ")[0])])


def _ganador(p: Partido) -> str:
    if p.goles_local > p.goles_visita:
        return p.local
    if p.goles_visita > p.goles_local:
        return p.visita
    if p.penales_local is not None:
        return p.local if p.penales_local > p.penales_visita else p.visita
    return ""


CHEQUEOS = [campos_completos, fechas_presentes, nombres_en_el_padron,
            penales_solo_en_empates, sin_duplicados,
            nadie_juega_contra_si_mismo, todos_tienen_zona, zonas_completas,
            una_vez_por_jornada, jornadas_sin_huecos, anios_bien_asignados,
            una_zona_por_club, localias_repartidas, cadena_de_llaves]


def revisar(ps: list[Partido]) -> list[Aviso]:
    """Corre todos los chequeos. Devuelve los avisos, graves primero."""
    avisos = [a for chequeo in CHEQUEOS for a in chequeo(ps)]
    return sorted(avisos, key=lambda a: not a.grave)

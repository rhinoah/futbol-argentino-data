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


def serie_igualada(p: Partido, ps: list[Partido]) -> bool:
    """Si `p` es una pata de una serie a dos partidos empatada en el global.

    Publica porque la usa tambien el lector de RSSSF. Es la MISMA pregunta desde
    los dos lados -- el que escribe la tanda y el que la audita -- y tenerla dos
    veces era tenerla distinta: el lector pedia que la PATA hubiera quedado
    igualada, que es mas estricto y falso, asi que tiraba veintidos tandas que
    este chequeo habria aceptado sin chistar.

    LAS DOS PATAS PUEDEN NO COMPARTIR LA JORNADA. Las plantillas de Wikipedia
    rotulan las dos igual y ahi alcanza con comparar el texto, pero RSSSF escribe
    "Semifinals - First leg" y "Semifinals - Second leg": dos jornadas distintas
    para la misma ronda. Se compara por el nombre normalizado, que es el que ya
    sabe pelar la pata, y solo cuando normalizar da algo -- si no da nada, se cae
    a la comparacion literal de antes y el chequeo se abstiene como siempre.
    """
    par = frozenset((p.local, p.visita))
    suya = _ronda(p.jornada)

    def misma_ronda(q: Partido) -> bool:
        return q.jornada == p.jornada or (bool(suya) and _ronda(q.jornada) == suya)

    serie = [q for q in ps
             if q.fase == "eliminacion" and q.llave == p.llave
             and misma_ronda(q) and frozenset((q.local, q.visita)) == par]
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
            and not (p.fase == "eliminacion" and serie_igualada(p, ps))]


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


def zonas_completas(ps: list[Partido], en_curso: bool = False,
                    divididos: tuple = ()) -> list[Aviso]:
    """En una zona todos-contra-todos, cada equipo juega la misma cantidad.

    Solo se le exige a las secciones que son realmente una zona: los bloques
    "Interzonal" cruzan equipos de zonas distintas y no tienen por que cerrar.

    Y SOLO SE LE EXIGE A UN TORNEO TERMINADO. Mientras la fecha se esta jugando
    es normal que unos lleven un partido mas que otros -- postergados, fechas
    escalonadas, un partido del domingo que todavia no se jugo --, y avisarlo
    todos los dias durante ocho meses no informa nada: solo entrena a saltear el
    reporte. Recien cuando el torneo cerro, una zona despareja significa que
    falta un partido.
    """
    if en_curso:
        return []
    avisos = []
    # Por (llave, zona) y no por zona sola. Una temporada con fases repite los
    # nombres de sus zonas -- el Torneo Federal A 2018-19 tiene una "Zona B" en la
    # Primera fase, otra en la Segunda y otra en la Revalida --, y hace falta
    # distinguirlas para saber en cual cuenta un partido dividido.
    zonas: dict[tuple[str, str], list[Partido]] = {}
    for p in ps:
        if p.fase == "zonas" and _ZONA.match(p.zona or ""):
            zonas.setdefault((p.llave or "", p.zona), []).append(p)
    for (llave, zona), partidos in sorted(zonas.items()):
        jugados = Counter()
        for p in partidos:
            jugados[p.local] += 1
            jugados[p.visita] += 1
        if not jugados:
            continue
        # UN PARTIDO DIVIDIDO SE JUGO AUNQUE NO TENGA FILA. El fallo le dio a cada
        # club un resultado distinto y el esquema no puede escribir eso, asi que
        # la fila no entra -- pero el partido existio y los dos clubes lo jugaron.
        # Sin sumarlo aca, declarar un dividido arregla el cruce de PJ contra la
        # tabla y deja la zona despareja, que es el mismo hecho denunciado dos
        # veces por caminos distintos.
        #
        # La ZONA no hace falta declararla: sale de los clubes. Los dos juegan en
        # una sola, asi que el partido es de la zona donde estan los dos.
        aparte = 0
        for local, visita, suya in divididos:
            if suya and suya != llave:
                continue
            if local in jugados and visita in jugados:
                jugados[local] += 1
                jugados[visita] += 1
                aparte += 1
        if len(set(jugados.values())) > 1:
            # EL QUE QUEDA EN LA ERA 2004-2026 ES CIERTO Y NO SE VA A CERRAR. Es la
            # Primera Nacional 2019-20: su ultimo partido es del 16/03/2020 y el
            # torneo termino sin completar el fixture, asi que 28 clubes jugaron 21
            # y cuatro jugaron 20. No hay partido que falte ni lectura que
            # arreglar; el aviso dice algo verdadero sobre el torneo. Queda escrito
            # aca y no en la lista de pendientes, que es para lo que se puede
            # hacer.
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
            # Los divididos van tambien en ESTA cuenta, por la misma razon: se
            # jugaron. Sumarlos arriba y no aca dejaba la zona pareja y el
            # todos-contra-todos incompleto, o sea el mismo agujero denunciado
            # por la otra puerta.
            if una_vuelta and (len(partidos) + aparte) % una_vuelta:
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


# Cuanto puede caer algo ANTES de lo que lo precede sin que sea un anio mal puesto.
# Son tres numeros y los tres salen de medir, no de una intuicion (10/10/2026: los
# 168 torneos del catalogo, el historial de 72 de sus paginas en Wikipedia --53 mil
# revisiones-- y unas 1300 paginas que todavia no entraron).
#
# ENTRE DOS JORNADAS O DOS RONDAS SEGUIDAS, 180. Lo mas largo que es legitimo son
# 158 dias --la Fecha 7 de la B Nacional 2016-17, que se jugo entera en marzo,
# cinco meses despues de la 8--; entre rondas, 6 en el catalogo y 9 en su historial.
# Los errores de anio que hubo dieron 358 y 359 entre jornadas y 254 entre rondas.
# Queda apretado de los dos lados y conviene saberlo antes de moverlo: 22 dias por
# encima de lo legitimo, y 9 por debajo del error mas chico que una configuracion
# equivocada del catalogo llega a producir (189, simulado).
_ATRAS_DE_MAS = 180

# ENTRE DOS SECCIONES SEGUIDAS, 160, y no 180: el error para el que existe esta
# pista puede caer justo ahi. Si dos mitades de un anio tienen sus fechas del medio
# a D dias y una se va de anio, queda 365 - D ANTES que la otra. En el catalogo D
# va de 140 a 164 y con 180 sobraba; en la Primera B 1967 es 185, y ahi con el
# umbral en 180 se veia por un dia o no se veia. Del otro lado, lo mas largo que
# es legitimo son 49 dias en el catalogo (53 en su historial), 103 en la Primera B
# 1969 --que ordena sus secciones por rama y no por fecha-- y 140 en una liga
# regional donde el orden en que llegan los partidos no es el de la pagina. Empezo
# en 90, y con 90 esas dos daban un grave sobre paginas sanas. Quedan 20 dias de
# cada lado: si un dia esta pista frena en falso, lo que hay que arreglar es el
# orden en que el parser entrega las secciones, no este numero.
_SECCION_ATRAS_DE_MAS = 160

# UNA JORNADA DE UNO O DOS PARTIDOS no tiene "el del medio" que la proteja: el del
# medio ES un partido, y un partido se posterga. Se la compara igual, pero se le
# pide mas: 240 dias, ocho meses. Un anio mal puesto da mas de 280 aun entre una
# fecha de marzo y una de diciembre, y lo mas largo que es legitimo son 157 dias:
# una revision de la B Nacional 2016-17 con un solo partido cargado de una fecha
# postergada cinco meses.
#
# La primera idea fue saltearlas, y fue peor: costaba y no compraba nada. Zonas de
# cuatro equipos y el grupo `Interzonal` se quedaban sin ninguna comparacion (47
# grupos de 17 torneos), una pagina con un error real dejaba de verse --la Copa
# Entre Rios 2021-22, que escribe "enero de 2021" donde va 2022--, y dos de los
# tres errores historicos se avisaban uno y dos dias mas tarde. Y comparandolas
# con el umbral comun no habia un solo aviso de mas en todo lo medido.
#
# Lo que cuesta: una celda sola con el mes mal en una jornada de un partido frena
# si queda a mas de ocho meses. En 11 870 revisiones reales que hacen alguna de
# estas comparaciones no paso nunca, y esa fecha estaria mal de verdad.
_JORNADA_CHICA = 3
_ATRAS_DE_MAS_CHICA = 240


def anios_bien_asignados(ps: list[Partido], en_curso: bool = False) -> list[Aviso]:
    """Nada puede caer medio anio ANTES de lo que lo precede.

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

    SE MIRA POR PISTAS. Una pista es una lista de cosas que tienen un orden
    propio, y son cuatro:

      1. las jornadas de un mismo GRUPO -- (llave, zona) --, por numero;
      2. las rondas de eliminacion de una misma llave, en el orden en que llegan;
      3. las secciones de la fase de zonas, en el orden en que llegan;
      4. y la eliminacion entera contra el arranque de la fase de zonas.

    Las tres primeras son GRAVES siempre. La cuarta es grave en un torneo cerrado
    y solo avisa en uno en curso; por que, en `_fase_final_antes_del_arranque`.

    HASTA EL 10/10/2026 HABIA UNA SOLA, Y MAL ARMADA: se juntaba por NUMERO de
    jornada todo lo que hubiera en la pagina. Una pagina que reusa "Fecha 1" --
    para el Apertura y el Clausura, o para dos fases con sus grupos -- mezclaba
    en una misma bolsa partidos de meses distintos, la fecha del medio de la bolsa
    caia en el medio y no se movia nadie. Asi pasaron 24 partidos de la Copa de la
    Liga 2020 fechados un anio antes y 8 de la Primera C 2019-20 fechados un anio
    despues -- que es EXACTAMENTE el caso que cuenta el parrafo de arriba, en
    otra division --. Y la eliminacion no se miraba: 26 partidos de la Copa
    Argentina 2011-12 figuraban despues de su propia final.

    Las tres las encontro un barrido del CSV, no este chequeo. Repuestas, las
    pistas 1 y 2 dan 6 avisos graves, uno por cada grupo roto. Sobre el dataset
    sano ninguna de las cuatro dice nada: ni al final de cada torneo, ni
    cortandolo en cada uno de los dias en que tuvo partidos (14 571 cortes), ni
    -- que es lo que de verdad veia la corrida diaria -- sobre el historial de
    revisiones de Wikipedia de las seis paginas en curso y de otras 66. Ahi lo
    unico que frena son 18 revisiones de una misma tarde de diciembre de 2014, con
    el fixture de la B Nacional 2015 a medio cargar y una jornada diez meses antes
    que la anterior; el chequeo de antes las frenaba igual.

    "EN EL ORDEN EN QUE LLEGAN" es el orden de `ps`, que es el de la pagina casi
    siempre: el parser entrega primero las tablas que cuelgan de un `Resultados`,
    despues las tablas sueltas y al final las plantillas, y las llaves que vienen
    de otra fuente se agregan atras. En las paginas del catalogo coincide.

    LO QUE SIGUE SIN VERSE, que no es poco y por eso este chequeo no esta solo:

      * El torneo ENTERO corrido un anio. Adentro no desentona nada. La mayor
        parte la frena `tests/test_torneos.py`, que corre antes que el build: el
        anio con que se fecha tiene que ser el del titulo de la pagina.
      * Un bloque que se ALEJA en vez de encimarse: con un `anio_fin` un anio mas
        grande de lo que va, la segunda mitad queda catorce meses despues de la
        primera y nada cae antes de nada. Tambien lo frena ese test.
      * Una llave de una sola ronda: no hay contra que comparar. Si la pagina
        tiene fase de zonas la ve la pista 4, y solo para atras. Son 55 llaves y
        125 partidos.
      * Un grupo ENTERO corrido respecto de los otros grupos de su llave: la
        pista 1 mira adentro de cada grupo, la 3 compara llaves y la 4 solo filas
        de eliminacion. El chequeo de antes lo veia cuando la numeracion seguia
        de un grupo al otro: el `Interzonal` de una sola fecha de la Copa de la
        Liga 2022, 2023 y 2024 (42 partidos) y, con el corte de mes mal puesto,
        siete revisiones de mayo de 2017 de la Primera C 2016-17, que esa semana
        tuvo sus dos ruedas escritas como dos zonas. Con el corte de mes
        equivocado en los 59 torneos que cruzan el anio -- 540 configuraciones,
        al final y dia por dia -- no hay ninguna que el de antes frenara y este no.
      * Al lado de una jornada de uno o dos partidos el umbral sube a 240 para
        LAS DOS comparaciones, la que llega a ella y la que sale: un salto de
        181 a 240 dias ahi no se ve.
      * Un partido suelto. Se mira la fecha del medio de cada tramo a proposito.
      * Dos rondas con el MISMO nombre adentro de una llave se juntan en una.
    """
    grupos: dict[tuple[str, str], dict[int, list[str]]] = {}
    rondas: dict[str, dict[str, list[str]]] = {}
    secciones: dict[str, list[str]] = {}
    for p in ps:
        if not _existe(p.fecha):
            continue
        if p.fase == "zonas":
            secciones.setdefault(p.llave, []).append(p.fecha)
            if n := _numero(p.jornada):
                grupos.setdefault((p.llave, p.zona), {}).setdefault(n, []).append(p.fecha)
        elif p.fase == "eliminacion" and p.jornada:
            rondas.setdefault(p.llave, {}).setdefault(p.jornada, []).append(p.fecha)

    avisos = []
    for (llave, zona), porjornada in grupos.items():
        avisos += _saltos_para_atras(
            [(f"Fecha {n}", porjornada[n]) for n in sorted(porjornada)],
            "una jornada cae medio anio antes que la anterior", _donde(llave, zona),
            chica=_JORNADA_CHICA)
    for llave, porronda in rondas.items():
        avisos += _saltos_para_atras(
            list(porronda.items()),
            "una ronda cae medio anio antes que la anterior", llave)
    avisos += _saltos_para_atras(
        [(llave or "la fase de zonas", fechas) for llave, fechas in secciones.items()],
        "una seccion entera cae medio anio antes que la anterior",
        umbral=_SECCION_ATRAS_DE_MAS)
    return avisos + _fase_final_antes_del_arranque(ps, en_curso)


def _saltos_para_atras(pista: list[tuple[str, list[str]]], que: str, donde: str = "",
                       umbral: int = _ATRAS_DE_MAS, chica: int = 0) -> list[Aviso]:
    """Los tramos de `pista` que caen mas de `umbral` dias antes que el anterior.

    `pista` es [(etiqueta, fechas)] EN EL ORDEN en que las cosas tienen que
    pasar. Se compara la fecha DEL MEDIO de cada tramo y no su primer dia: lo que
    se busca es el tramo entero fuera de lugar.

    `chica` es el tamanio por debajo del cual un tramo no tiene "el del medio" que
    lo proteja de un partido postergado; cuando cualquiera de los dos tramos que se
    comparan es asi, el umbral es `_ATRAS_DE_MAS_CHICA`. Lo piden las jornadas. Las
    rondas y las secciones no: una final es de un partido, y ahi no hay nada mas
    chico contra que cuidarse.
    """
    avisos = []
    previo = None
    for etiqueta, fechas in pista:
        medio = sorted(fechas)[len(fechas) // 2]
        if previo:
            corto = min(len(fechas), previo[2]) < chica
            if _dias(medio, previo[1]) > (_ATRAS_DE_MAS_CHICA if corto else umbral):
                avisos.append(Aviso(
                    que,
                    f"{donde + ': ' if donde else ''}{etiqueta} en {medio} contra "
                    f"{previo[0]} en {previo[1]}; son las fechas del medio de cada una "
                    f"y parece un anio mal asignado"))
        previo = (etiqueta, medio, len(fechas))
    return avisos


def _fase_final_antes_del_arranque(ps: list[Partido], en_curso: bool) -> list[Aviso]:
    """Las rondas de eliminacion que se juegan antes de que empiece la fase de zonas.

    Una fase final corrida un anio para atras NO cae lejos: en una temporada de
    agosto a junio, la de junio queda dos meses antes del primer partido. Las
    rondas entre si siguen en orden y la fase de zonas tambien, asi que ninguna de
    las otras pistas lo ve. Va sin margen por eso mismo: un colchon del tamanio de
    los otros umbrales dejaria pasar a tres de cada cuatro.

    ES GRAVE EN UN TORNEO CERRADO Y SOLO AVISA EN UNO EN CURSO, y es la unica de
    las cuatro que distingue. Hay torneos de verdad en los que la eliminacion va
    primero: una eliminatoria previa que reparte los cupos de los grupos (el
    Torneo Integracion 2016 de Catamarca), o rondas regionales con "Fecha 1, Fecha
    2" que el parser lee como eliminacion por el nombre de su seccion (el Argentino
    B 2000-01). Ninguno esta en el catalogo, pero existen. Los torneos en curso
    son lo que la corrida de todos los dias vuelve a leer: si un anio cambia de
    formato, un grave ahi frena la actualizacion de todas las paginas por una que
    esta sana. Uno cerrado se lee al cargarlo o con `--rehacer`, que es cuando hay
    alguien mirando -- y ahi conviene que frene: es la pista que ve un corte de mes
    que se lleva solamente la fase final.

    Lo que eso cuesta: en un torneo en curso, ese error se publica con un aviso. Y
    cuando se lo pasa a cerrado no se vuelve a leer, porque ya tiene sus filas en
    el CSV. Por eso `tests/test_validar.py` corre esta pista sobre las filas
    PUBLICADAS de cada torneo cerrado: la suite corre antes que el build, y el dia
    que alguien cierra un torneo con ese error adentro, se entera.

    EL ARRANQUE NO ES EL PRIMER PARTIDO sino el que deja atras al 5% de la fase de
    zonas (con menos de veinte partidos fechados, si es el primero). A un minimo
    lo mueve un solo partido, y el error que se busca se lleva justamente partidos
    sueltos: en la Primera C 2008-09 con el corte dos meses antes, la fase final de
    junio se iba un anio para atras JUNTO con un partido de liga jugado el 1 de
    junio, ese partido pasaba a ser "el arranque" y la pista se quedaba muda con
    quince filas mal.

    Y SE CALLA SI MENOS DE LA MITAD DE LA FASE DE ZONAS TIENE FECHA. Con dos fechados
    de cien -- que es como llegan las paginas viejas antes de tener segunda fuente
    --, el "arranque" es el dia de un postergado cualquiera.
    """
    zonas = [p.fecha for p in ps if p.fase == "zonas"]
    fechadas = sorted(f for f in zonas if _existe(f))
    if not fechadas or len(fechadas) * 2 < len(zonas):
        return []
    arranque = fechadas[len(fechadas) // 20]
    antes: dict[tuple[str, str], list[str]] = {}
    for p in ps:
        if p.fase == "eliminacion" and _existe(p.fecha) and p.fecha < arranque:
            antes.setdefault((p.llave, p.jornada), []).append(p.fecha)
    return [Aviso(
        "una ronda de eliminacion antes de que empiece la fase de zonas",
        f"{_donde(llave, ronda) or 'sin rotulo'}: {len(fechas)} "
        f"partido{'s' if len(fechas) != 1 else ''} desde el {min(fechas)}, y para el "
        f"{arranque} la fase de zonas no llevaba jugados mas de {len(fechadas) // 20} de "
        f"sus {len(fechadas)} partidos con fecha; o la pagina trae una eliminatoria "
        f"previa, o se leyo como eliminacion una ronda de grupos, o el anio esta mal "
        f"asignado", grave=not en_curso)
        for (llave, ronda), fechas in antes.items()]


def _donde(*partes: str) -> str:
    """`llave zona`, sin repetir: hay paginas donde la zona se llama igual que la
    llave que la contiene."""
    return " ".join(dict.fromkeys(x for x in partes if x))


def _existe(fecha: str) -> bool:
    """La fecha esta, es un dia del calendario y esta escrita `AAAA-MM-DD`.

    Las paginas a veces escriben uno que no existe -- hubo un `31 de noviembre` y
    tres `31 de junio` en el dataset -- y el parser lo arma igual. Una fecha asi
    no se puede restar: si le tocaba ser la del medio de su jornada, `_dias`
    levantaba un `ValueError` y el chequeo tumbaba el build en vez de avisar. No
    paso de casualidad. Aca se la saltea; decir que no existe es otro chequeo.

    Se le pide ademas que vuelva igual por `isoformat`: `fromisoformat` acepta
    otras formas -- `20200105`, `2020-W03-3` -- y este modulo ordena y compara las
    fechas como texto, que solo vale para la forma larga.
    """
    from datetime import date
    try:
        return date.fromisoformat(fecha).isoformat() == fecha
    except (TypeError, ValueError):
        return False


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
        # ULTIMO INTENTO: RECONSTRUIR LAS RONDAS POR EL PLANTEL. Si dos rotulos
        # tienen el MISMO plantel exacto, no son dos rondas: son la misma ronda
        # jugada dos veces. Es lo que pasa con nueve de las diez paginas que
        # rotulan la PATA en vez de la ronda -- "Partidos de ida" y "Partidos de
        # vuelta" tienen identico plantel, y "Partido de ida" y "Partido de
        # vuelta" tambien --, asi que cuatro rotulos colapsan en las dos rondas de
        # verdad: la de varias llaves y la final. Se midio en las nueve; la decima
        # es el Federal A 2014 y cae en el `else` de abajo.
        #
        # El agrupado es ESTRUCTURAL, no por fecha: solo junta rotulos, nunca
        # parte uno. Por eso no puede repetir el error que este modulo ya cometio
        # -- agrupar por dia hacia que el segundo dia de una misma ronda pareciera
        # una ronda nueva--. La fecha se usa despues y solo para ORDENAR los
        # grupos ya armados, que en una eliminacion avanzan en el tiempo.
        #
        # Solo sirve si el plantel efectivamente junto rotulos. Si cada uno tiene
        # su propio plantel no se aprendio nada y se avisa, como antes.
        porplantel: dict[frozenset, list[str]] = {}
        for j, cs in clubes.items():
            porplantel.setdefault(frozenset(cs), []).append(j)
        if 1 < len(porplantel) < len(clubes):
            armados = [(" / ".join(sorted(rots)),
                        [x for x in elim if x.jornada in set(rots)])
                       for rots in porplantel.values()]
            grupos = sorted(armados, key=lambda kv: min(x.fecha for x in kv[1]))
        else:
            # DE LOS CINCO QUE QUEDAN, CUATRO NO SON CADENAS, y no se puede probar
            # que no lo sean, asi que el chequeo se abstiene en vez de acusar. `Llave 1..6`
            # (Primera Division 2015) y `Partido 1/2/3` (B Nacional 2014) son
            # llaves PARALELAS: cada rotulo es una serie distinta jugandose al
            # mismo tiempo, no una ronda que sigue a la anterior. `Final Reválida`
            # y `Final por la Promoción` (Argentino A 2004-05) son finales sueltas.
            # Y `Tercer ascenso` (Transicion Federal A 2020) marca el limite
            # conceptual: un partido de consolacion lo juegan los que PERDIERON la
            # ronda anterior, y el modelo de este chequeo es "el que juega gano lo
            # anterior" -- meterlo en el vocabulario generaria acusaciones falsas.
            #
            # EL QUINTO SI ES UNA CADENA y aca no se la puede armar: la `Segunda a
            # cuarta fase` del Torneo Federal A 2014, 16 -> 8 -> 4 -> 2 en 28
            # partidos. La pagina rotula solo la pata y su ultima fase son DOS
            # series, asi que no hay un `Partido de ida` en singular que separe
            # nada: quedan dos rotulos con el mismo plantel. Con la abstencion, un
            # club mal atribuido en ese cuadro no se veria. Se reviso a mano al
            # cargarlo --todo el que sigue jugando gano su serie o la empato y paso
            # por penales-- y los 28 marcadores coinciden con los de RSSSF.
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
        # DOS FORMAS DE DESAMBIGUAR ESTO QUE SE MIDIERON Y SON FALSAS. Quedan
        # escritas para que no se vuelvan a intentar: el aviso es ambiguo por
        # naturaleza y no por falta de ganas.
        #
        #   1. "El que entra fresco es el mejor ubicado, o sea un sembrado".
        #      Falso: sobre los 29 avisos del corpus, lo es en 8. Entran
        #      Douglas Haig doceavo de 14, Argentino de Merlo ultimo de 10.
        #   2. "El que entra fresco perdio antes en otra llave de la pagina, y
        #      por eso es un repechaje". Tambien falso como regla general: casi
        #      todos no tienen NINGUN partido anterior en la pagina. Vienen de
        #      la fase de zonas, no de otro cuadro.
        #
        # Y la razon de fondo es que no hay asimetria de donde agarrarse: si a
        # la ronda anterior le falta un partido, sus DOS clubes desaparecen de
        # los datos y solo el ganador reaparece -- exactamente lo mismo que se
        # ve cuando el formato siembra a alguien. Un cuadro completo y uno con
        # un agujero se ven igual desde adentro. Para separarlos hace falta
        # saber cuantos clubes entran al cuadro y en que ronda, que es un dato
        # del reglamento y no de los partidos.
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
# "Semifinals - First leg" / "Final - Second leg", y el typo "Secoond" que la
# fuente trae en una temporada.
_PATA_AL_FINAL = re.compile(r"\s+-\s+(?:first|second|secoond)\s+legs?$", re.I)

_SINONIMOS = {
    # Los ordinales, que cada pagina escribe a su manera: "fase", "ronda" o
    # "instancia".
    #
    # CUIDADO CON COMO SE MIDIO ESTO. La version anterior de este comentario
    # afirmaba que ninguna pagina usa dos formas del mismo ordinal, y es FALSO a
    # nivel de titulos: el Torneo Argentino A 2011-12 y el 2012-13 escriben
    # "Primera fase" y "Primera ronda" en la misma pagina, y lo mismo con segunda
    # y tercera. Lo que si se midio, y es lo que importa, es a nivel de JORNADA
    # dentro de una misma LLAVE: ningun cuadro tiene dos jornadas distintas que
    # caigan en la misma ronda -- en esas dos paginas las dos formas viven en
    # llaves separadas ("Segunda fase" y "Tercera y cuarta fase"), asi que el
    # chequeo nunca las compara entre si. La unica fusion que ocurre es la
    # buscada: "Semifinal 1" y "Semifinal 2" en una sola ronda.
    #
    # La diferencia no es cosmetica: fusionar dos rondas distintas de un mismo
    # cuadro seria PEOR que no revisar, porque compararia contra el conjunto
    # equivocado en vez de abstenerse.
    "primera ronda": "primera fase",
    "segunda ronda": "segunda fase",
    "tercera ronda": "tercera fase",
    "cuarta ronda": "cuarta fase",
    # RSSSF escribe las rondas en INGLES, y desde que sus llaves entran al dataset
    # esas jornadas llegan hasta aca. La jornada publicada sigue siendo fiel a la
    # fuente -- su trabajo es ser fiel, no prolijo --, asi que la traduccion vive
    # donde vive el resto de la normalizacion: aca.
    "semifinals": "semifinales",
    "quarterfinals": "cuartos",
    "1/8 finals": "octavos",
    "third phase": "tercera fase",
    "fourth phase": "cuarta fase",
    "second round": "segunda fase",
    "third round": "tercera fase",
    "primera instancia": "primera fase",
    "segunda instancia": "segunda fase",
    "tercera instancia": "tercera fase",
    "cuarta instancia": "cuarta fase",
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

    # LA PATA SE PELA PRIMERO, y el orden no da igual: el lector de llaves escribe
    # "Semifinals - First leg", y pelando la rama de adelante quedaria "first leg",
    # que no es ninguna ronda. Sacando la pata queda "semifinals", que si lo es.
    sin_pata = _PATA_AL_FINAL.sub("", j)
    if sin_pata != j and pelada(sin_pata) in conocidas:
        return pelada(sin_pata)
    j = sin_pata
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


def revisar(ps: list[Partido], en_curso: bool = False,
            divididos: tuple = ()) -> list[Aviso]:
    """Corre todos los chequeos. Devuelve los avisos, graves primero.

    `en_curso` dice que el torneo todavia se esta jugando. Lo miran dos --
    `zonas_completas` y `anios_bien_asignados` --, y va como parametro y no como
    una deteccion por fecha para que se vea en la lista de torneos quien lo declara.
    """
    avisos = []
    for chequeo in CHEQUEOS:
        if chequeo is zonas_completas:
            avisos += chequeo(ps, en_curso, divididos)
        elif chequeo is anios_bien_asignados:
            avisos += chequeo(ps, en_curso)
        else:
            avisos += chequeo(ps)
    return sorted(avisos, key=lambda a: not a.grave)

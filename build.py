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

from fad import (correcciones, dataset, equipos, parser, posiciones, torneos,
                 validar, wiki)

SALIDA = Path(__file__).resolve().parent / "data"   # una carpeta: un CSV por temporada


def _completar_fechas_rsssf(ps, t) -> list:
    """Igual que `_completar_fechas` pero contra RSSSF, para los torneos que
    worldfootball no tiene -- el Argentino A no figura en su selector.

    Misma tolerancia: si el sitio no responde se avisa y se sigue. Los partidos
    quedan sin fecha y van a `sin-fecha/`, que es donde estaban antes.
    """
    from fad import fechas, rsssf

    archivo, mapa = rsssf.FUENTES[t.pagina]
    try:
        crudo = rsssf.descargar(archivo)
    except OSError as e:
        return [validar.Aviso("no se pudo consultar RSSSF",
                              f"{archivo}: {e}; los partidos quedan sin fecha",
                              grave=False)]
    ajenos, avisos = rsssf.leer(crudo, mapa, t.temporada, t.anio_fin or t.temporada,
                                t.mes_inicio)
    puestas, mas = fechas.completar(ps, ajenos, credito=rsssf.CREDITO)
    return [validar.Aviso(f"{t.pagina}: RSSSF", d, grave=False)
            for d in avisos + mas]


def _completar_fechas_espn(ps, t) -> list:
    """Tercera fuente de fechas, para las tres temporadas de Primera C.

    Sus paginas traen los resultados en tablas de tres columnas y no hay columna
    de fecha; worldfootball no tiene la categoria tan atras y RSSSF tampoco. El
    feed de ESPN devuelve la temporada entera en una llamada.

    Misma tolerancia que las otras dos: si el sitio no responde se avisa y se
    sigue, y los partidos quedan sin fecha en `sin-fecha/`.
    """
    from fad import espn, fechas

    liga, rangos, mapa = espn.FUENTES[t.pagina]
    try:
        eventos = espn.descargar(liga, rangos)
    except OSError as e:
        return [validar.Aviso("no se pudo consultar ESPN",
                              f"{t.pagina}: {e}; los partidos quedan sin fecha",
                              grave=False)]
    ajenos, avisos = espn.leer(eventos, mapa)
    # Antes de completar nada: que las dos partes hablen de los mismos clubes. Un
    # nombre mal traducido manda el partido al club equivocado y el marcador no
    # lo agarra.
    avisos += espn.contrastar_plantel(ajenos, ps)
    _, mas = fechas.completar(ps, ajenos, credito=espn.CREDITO)
    return [validar.Aviso(f"{t.pagina}: ESPN", d, grave=False) for d in avisos + mas]


def _repartir(listas: list[dict], filas: list, sin_fecha: list) -> None:
    """Cada fila va donde le corresponde SEGUN SU FECHA, no segun su torneo.

    Antes esto se decidia por torneo: uno marcado `sin_fecha` iba entero a la
    carpeta aparte, y en cualquier otro las filas sin fecha SE TIRABAN. Las dos
    mitades de esa regla envejecieron mal.

    Por un lado, un torneo `sin_fecha` puede dejar de serlo a medias. El Argentino
    A 2005-06 tiene hoy 264 de sus 279 partidos fechados desde RSSSF: mandarlos a
    todos a `sin-fecha/` seria archivar 264 fechas que ya tenemos, y mandarlos a
    todos a `data/` seria perder 15 partidos reales.

    Por el otro, tirar una fila por no tener fecha contradice lo que dice el LEEME
    de esa misma carpeta: que falte la fecha no es lo mismo que no tener el
    partido. El resto del dato -- equipos, marcador, jornada, estadio -- esta
    completo y validado. Se guarda igual, aparte, y el dataset principal sigue
    prometiendo una fecha en cada fila.
    """
    for f in listas:
        (filas if (f.get("date") or "").strip() else sin_fecha).append(f)


def sin_fecha_en(salida: Path) -> Path:
    """La subcarpeta de los partidos que la fuente publica SIN fecha.

    Van aparte y no al dataset principal, que promete una fecha en cada fila. Que
    falte la fecha no es lo mismo que no tener el partido: el resto del dato --
    equipos, marcador, jornada, estadio -- esta completo y verificado.

    Se deriva de `SALIDA` y NO se guarda en una
    constante: si no, un test que cambia `SALIDA` sigue leyendo la carpeta real y
    se lleva los partidos de verdad adentro de su carpeta temporal."""
    return salida / "sin-fecha"


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


def _completar_fechas(ps, t) -> list:
    """Le pide a la segunda fuente el unico campo que Wikipedia no publica.

    Corre solo para las entradas del catalogo que tienen `wf`, que hoy son las
    cuatro temporadas de B Nacional 2007-2011: sus paginas traen los resultados
    en tablas de tres columnas, sin fecha, y sin este paso los 1520 partidos se
    descartan enteros en el filtro final.

    SI LA FUENTE NO ESTA, NO PASA NADA GRAVE. Se avisa y se sigue: los partidos
    quedan sin fecha y el filtro los deja afuera, que es exactamente lo que pasa
    hoy. Un aviso grave seria peor -- frenaria el build entero de todos los dias
    por un sitio de terceros que no controlamos.

    Y no se consulta todos los dias. Los cuatro torneos son `cerrado=True`: una
    vez que sus filas con fecha estan en `data/`, `main` las reusa por `t.url` y
    no vuelve a pasar por aca. La enriquecida es de una sola vez; despues el dato
    es del CSV. Por eso CI, que no tiene la cache ni puede salir a ese sitio,
    igual arma el dataset completo.
    """
    from fad import fechas

    try:
        pagina = fechas.descargar(*t.wf)
    # `OSError` y no `Exception`: URLError y HTTPError lo heredan, asi que cubre
    # el 403, la red caida y el timeout, que es lo que este `try` viene a
    # tolerar. Atrapando todo se tragaba tambien los errores de programacion --
    # un `wf` mal escrito en el catalogo pasaba como "el sitio no responde" y el
    # torneo se quedaba sin fechas sin que nadie se enterara de por que.
    except OSError as e:                         # 403, sin red, sin cache
        return [validar.Aviso(
            f"{t.pagina}: no se pudo consultar la segunda fuente",
            f"{e}. Los partidos quedan sin fecha y no entran al dataset", grave=False)]

    ajenos = fechas.partidos_de(pagina)
    if not ajenos:
        return [validar.Aviso(f"{t.pagina}: la segunda fuente no devolvio partidos",
                              "la pagina cambio de forma?", grave=False)]

    mapa, avisos = fechas.derivar_padron(ps, ajenos)
    # `derivar_padron` puede terminar diciendo que su propio mapa no sirve --
    # dos ids apuntando al mismo club --. Antes ese aviso se emitia y el mapa se
    # usaba igual en la linea siguiente, que es la peor combinacion: queda dicho
    # que el dato no es confiable y se lo usa lo mismo. Si pasa, se cruza solo
    # con el padron hecho a mano, que no depende de esta derivacion.
    roto = [a for a in avisos if "no sirve" in a]
    puestos, mas = fechas.completar(ps, ajenos, {} if roto else mapa,
                                    correcciones.arbitrados(t.pagina))

    # La fecha importada tiene que caer dentro de la temporada declarada. Es
    # barato y no lo mira nadie mas: `anios_bien_asignados` compara la MEDIANA de
    # cada jornada, asi que un partido suelto tres anios afuera lo absorbe sin
    # una queja. Aca esta el Torneo a mano, que es lo que hace falta para saber
    # cual seria el rango.
    validos = {t.temporada, t.anio_fin or t.temporada}
    fuera = [p for p in ps if p.fuente_fecha and int(p.fecha[:4]) not in validos]
    for p in fuera[:3]:
        p.fecha, p.fuente_fecha = "", ""

    faltan = sum(1 for p in ps if not p.fecha)
    return [validar.Aviso(f"{t.pagina}: el mapa de ids no sirve, se cruzo solo con "
                         f"el padron", "; ".join(roto)) for _ in roto[:1]] +            [validar.Aviso(f"{t.pagina}: {len(fuera)} fechas importadas caen fuera de "
                          f"{sorted(validos)}", "se descartan; el partido queda sin fecha")
            for _ in fuera[:1]] +            [validar.Aviso(f"{t.pagina}: {puestos} fechas de la segunda fuente",
                          f"{len(mapa)} clubes cruzados"
                          + (f"; quedan {faltan} partidos sin fecha" if faltan else ""),
                          grave=False)] + \
           [validar.Aviso(f"{t.pagina}: segunda fuente", a, grave=False)
            for a in avisos + mas]


def _dias(iso: str) -> int:
    """La fecha como numero de dias, para poder decir cual esta mas cerca. Una
    fecha vacia se va lejos en vez de romper: el que la trae ya tiene su aviso."""
    from datetime import date
    try:
        return date.fromisoformat(iso).toordinal()
    except (ValueError, TypeError):
        return 0


def sin_repetir(llaves: list, ps: list) -> tuple[list, int, list[str]]:
    """Las llaves de RSSSF que la pagina NO tiene ya, y las que contradice.

    LO QUE LA PAGINA YA TIENE NO SE VUELVE A ESCRIBIR. En el Argentino A 2005-06 la
    fase final no estaba en la grilla y entraba entera; en el 2011-12 la pagina SI
    publica la Revalida y las fases tercera y cuarta, y solo le faltan las semis y
    la final. Importar sin mirar duplicaria 34 partidos, que es peor que no
    importar ninguno.

    La casilla es el par de clubes MAS la fecha. El par solo no alcanza: las dos
    patas de una llave son el mismo par y se distinguen justamente por el dia.

    SE COMPARA CANONIZADO, y no da lo mismo. La canonizacion corre despues, asi que
    aca `ps` todavia trae los nombres crudos de Wikipedia mientras que los de RSSSF
    ya salen canonicos del mapa. Comparando en crudo el cruce falla casi entero --
    se midio: reconocia 8 de 34 -- y entraban 26 duplicados.

    Si el par esta pero la fila no coincide, las dos fuentes discrepan sobre ESE
    partido y no es uno que falte. Se conserva el de la pagina --Wikipedia es la
    fuente primaria del repo y RSSSF entra a completar, no a pisar-- y se avisa con
    las dos versiones enfrentadas. No es solo la fecha, y por eso se muestran los
    renglones enteros: en el Argentino A 2011-12 las dos fuentes se contradicen
    ademas en la LOCALIA -- la pagina pone "Racing (O) 0-2 Central Cordoba" y RSSSF
    "Central Cordoba 2-0 Racing" --, o sea mismo resultado y cancha al reves. Decir
    "otra fecha" lo tapaba.
    """
    def par(x):
        return frozenset((equipos.canonizar(x.local, x.local_art),
                          equipos.canonizar(x.visita, x.visita_art)))

    ya = {(par(x), x.fecha) for x in ps}
    suyas: dict = {}
    for x in ps:
        if x.fase == "eliminacion":
            suyas.setdefault(par(x), []).append(x)

    nuevas, repetidas, discuten = [], 0, []
    for p_ in llaves:
        suyo = frozenset((p_.local, p_.visita))
        if (suyo, p_.fecha) in ya:
            repetidas += 1
        elif suyo in suyas:
            cerca = min(suyas[suyo], key=lambda x: abs(_dias(x.fecha) - _dias(p_.fecha)))
            discuten.append(
                f"la pagina dice {cerca.fecha} "
                f"{equipos.canonizar(cerca.local, cerca.local_art)} "
                f"{cerca.goles_local}-{cerca.goles_visita} "
                f"{equipos.canonizar(cerca.visita, cerca.visita_art)} y RSSSF "
                f"{p_.fecha} {p_.local} {p_.goles_local}-{p_.goles_visita} {p_.visita}")
        else:
            nuevas.append(p_)
    return nuevas, repetidas, discuten


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
    if t.sin_grilla:
        # La pagina no publica resultados y los partidos salen de RSSSF. Es el
        # unico camino del repo por el que una fila NO viene de Wikipedia, y va
        # detras de un flag escrito a mano -- ver `Torneo.sin_grilla` -- para que
        # nunca se dispare por accidente cuando una grilla real deje de parsearse.
        #
        # Todo lo que sigue -- canonizar, corregir, y los chequeos contra la tabla
        # de posiciones de la propia pagina -- corre igual sobre estas filas. La
        # tabla SI esta en Wikipedia, asi que el cedazo es el mismo que para
        # cualquier otro torneo: entran auditadas o no entran.
        from fad import rsssf
        archivo, mapa = rsssf.FUENTES[t.pagina]
        try:
            crudo = rsssf.descargar(archivo)
        except OSError as e:
            return [], [validar.Aviso(
                f"{t.pagina}: RSSSF no respondio y esta pagina no tiene grilla "
                f"propia, asi que el torneo queda sin partidos", repr(e), grave=True)]
        ajenos, mas = rsssf.leer(crudo, mapa, t.temporada,
                                 t.anio_fin or t.temporada, t.mes_inicio)
        importados = [validar.Aviso(f"{t.pagina}: RSSSF", d, grave=False) for d in mas]
        ps = rsssf.a_partidos(ajenos, t.torneo, t.temporada)
    else:
        importados = []
        ps = parser.partidos(texto, t.temporada, t.torneo, formato=t.formato,
                             anio_fin=t.anio_fin, mes_inicio=t.mes_inicio)
        # La grilla de la pagina cubre los grupos pero no la fase final, que ahi
        # es un dibujo. Las llaves vienen de RSSSF, que si dice quien fue local.
        if t.rsssf_llaves:
            from fad import rsssf
            archivo, mapa = rsssf.FUENTES[t.pagina]
            try:
                crudo = rsssf.descargar(archivo)
            except OSError as e:
                importados.append(validar.Aviso(
                    f"{t.pagina}: RSSSF no respondio, asi que la fase final se "
                    f"queda sin partidos", repr(e), grave=False))
            else:
                llaves, mas = rsssf.leer_llaves(
                    crudo, mapa, t.temporada, t.anio_fin or t.temporada,
                    t.mes_inicio, desde=rsssf.SECCION.get(t.pagina, ""))
                for p_ in llaves:
                    p_.torneo = t.torneo
                nuevas, repetidas, discuten = sin_repetir(llaves, ps)
                ps += nuevas
                if repetidas:
                    mas.append(f"{repetidas} llaves de RSSSF ya estaban en la "
                               f"grilla de la pagina y no se duplicaron")
                if discuten:
                    mas.append(f"{len(discuten)} partidos donde la pagina y RSSSF no "
                               f"coinciden; se conserva el de la pagina: "
                               + " | ".join(discuten[:3]))
                importados += [validar.Aviso(f"{t.pagina}: RSSSF llaves", d,
                                             grave=False) for d in mas]
    for p in ps:
        p.local = equipos.canonizar(p.local, p.local_art)
        p.visita = equipos.canonizar(p.visita, p.visita_art)
    # Las correcciones a mano van despues de canonizar y antes de todo lo demas,
    # porque lo que arreglan -- un club mal escrito -- es justamente lo que los
    # chequeos van a mirar. Ver `fad/correcciones.py`: hay una sola y esta ahi
    # documentada con su evidencia.
    # Como escribe la pagina a cada club, de los dos lados y antes de resolver
    # nada: es contra esto que se chequea si un homonimo sigue haciendo falta.
    # La tabla se pide sin `pagina` justamente para que NO aplique homonimos.
    # El cuadro de llaves va TAMBIEN, y por la misma razon por la que se sumo la
    # tabla en su momento: un homonimo que arregla un nombre que solo vive en el
    # cuadro no engancha con los partidos ni con la tabla, y se denunciaria a si
    # mismo como vencido. Es el caso del "Talleres (C)" del Argentino A 2005-06,
    # que aparece una unica vez en toda la pagina y es adentro del cuadro.
    escritos = ({p.local for p in ps} | {p.visita for p in ps}
                | set(posiciones.tabla(texto))
                | {equipos.canonizar(crudo, art)
                   for crudo, art in parser.clubes_del_cuadro(texto).items()
                   if equipos.conocido(crudo, art)})
    arregladas, dudas = correcciones.aplicar(ps, t.pagina)
    borradas = _borrar_jornadas_falsas(ps)
    # La segunda fuente va DESPUES de borrar las jornadas falsas y ANTES de
    # validar, y las dos mitades del sandwich importan.
    #
    # Despues de borrarlas, porque `fechas.completar` empareja por (jornada,
    # local, visitante). Una etiqueta que el parser tomo por jornada y no lo es
    # -- los 190 partidos del Inicial 2012 colgando de un unico "Fecha 1" --
    # mandaria a buscar la Fecha 1 del otro lado para partidos de cualquier
    # ronda. El marcador tendria que coincidir tambien, asi que la chance es
    # baja, pero no hay ninguna razon para correrla: una vez borradas, esos
    # partidos no emparejan con nada y se quedan sin fecha, que es lo correcto.
    #
    # Antes de validar, porque si no `fechas_presentes` se queja de los mismos
    # partidos que este paso viene a arreglar.
    avisos = list(importados)
    avisos += _completar_fechas(ps, t) if t.wf else []
    # `sin_grilla` no pasa por aca: sus filas YA salieron de RSSSF con su fecha
    # puesta, asi que completarlas es leer la misma pagina dos veces y emitir
    # cada aviso por duplicado.
    avisos += _completar_fechas_rsssf(ps, t) if t.rsssf and not t.sin_grilla else []
    avisos += _completar_fechas_espn(ps, t) if t.espn else []
    avisos += validar.revisar(ps)
    # La tabla de posiciones de la propia pagina, contra la suma de los partidos.
    # Va como aviso: lo que denuncia es una contradiccion DE LA FUENTE consigo
    # misma, y frenar el build de todos los dias por eso seria desproporcionado.
    # Sirve igual, y para algo que ningun otro chequeo puede hacer: decidir cual
    # de dos fuentes tiene razon sobre un marcador, sin traer una tercera.
    avisos += [validar.Aviso(f"{t.pagina}: no cierra con su tabla de posiciones", d,
                             grave=False)
               for d in posiciones.contrastar(ps, texto, pagina=t.pagina)]
    # Y la tabla contra si misma. No compara contra nuestra grilla: suma sus dos
    # columnas de goles y las encuentra distintas, que es imposible. Cuando este
    # salta no hay nada que arbitrar -- la equivocada es la pagina.
    avisos += [validar.Aviso(f"{t.pagina}: su tabla de posiciones no cierra sola", d,
                             grave=False)
               for d in posiciones.desbalance(ps, texto, pagina=t.pagina)]
    # Un club que la tabla nombra y el padron no conoce. No afecta a los datos --
    # por eso no es grave-- pero apaga el arbitro en esa fila sin decir nada, que
    # es peor: el chequeo sigue corriendo y ya no mira todo.
    avisos += [validar.Aviso(f"{t.pagina}: un club de la tabla no esta en el padron", d,
                             grave=False)
               for d in posiciones.fuera_del_padron(texto)]
    # Y su hermano general: la fila cuyo club no jugo ni un partido en ese
    # alcance. El de arriba pide que el nombre sea ilegible; a este le alcanza
    # con que la fila no tenga contra que cruzarse, que es lo que de verdad
    # apaga al arbitro.
    avisos += [validar.Aviso(f"{t.pagina}: un club de la tabla no jugo ahi", d,
                             grave=False)
               for d in posiciones.sin_partidos(ps, texto, pagina=t.pagina)]
    # El cuarto y ultimo del cruce, y el unico que mira la GRILLA. Los otros tres
    # miran la tabla, y ninguno ve el error que no falla nunca: un nombre pelado
    # que el padron resuelve solo, y lo resuelve al club equivocado.
    avisos += [validar.Aviso(f"{t.pagina}: la grilla nombra un club sin desambiguar", d,
                             grave=False)
               for d in posiciones.homonimo_de_la_pagina(ps, texto, pagina=t.pagina)]
    # Las filas que la pagina publica y la guarda de coherencia descarta. Sin
    # esto, ese club se queda sin arbitro y no lo dice nadie: ni contrastar ni
    # desbalance opinan sobre una fila que no llego a parsearse.
    avisos += [validar.Aviso(f"{t.pagina}: una fila de la tabla no cierra sola", d,
                             grave=False)
               for d in posiciones.filas_que_no_cierran(texto, pagina=t.pagina)]
    # Y las verificaciones que caducaron. Un `Revisado` silencia un aviso, asi
    # que tiene que denunciarse solo cuando deja de enganchar: si la pagina
    # cambio, esa verificacion hablaba de otra cosa y puede estar tapando un
    # desvio nuevo del mismo club.
    avisos += [validar.Aviso(f"{t.pagina}: una verificacion que ya no engancha", d,
                             grave=False)
               for d in correcciones.revisados_huerfanos(
                   t.pagina, posiciones.clubes_desviados(ps, texto, pagina=t.pagina),
                   posiciones.marcadores_del_cuadro(ps, texto, t.pagina, crudo=True))]
    # Y los RESULTADOS, que es la otra mitad de la misma tabla: `contrastar`
    # pregunta cuantos goles y este pregunta quien gano. Separa un digito mal
    # leido de un partido entero al reves, y eso cambia que hay que ir a buscar.
    avisos += [validar.Aviso(f"{t.pagina}: la tabla y la grilla dan distinto ganador", d,
                             grave=False)
               for d in posiciones.resultados_que_no_coinciden(ps, texto, pagina=t.pagina)]
    # Y el PJ, que `contrastar` mira para CALLARSE y que aca se mira para hablar.
    avisos += [validar.Aviso(f"{t.pagina}: la tabla y la grilla cuentan distintos partidos", d,
                             grave=False)
               for d in posiciones.pj_que_no_coincide(ps, texto, pagina=t.pagina)]
    # Un partido que la pagina tiene y que el esquema no puede escribir. No se
    # arregla -- no hay par de goles que diga que perdieron los dos --, pero sin
    # avisarlo el hueco aparece como un partido que falta y manda a buscar un
    # error de lectura que no existe.
    avisos += [validar.Aviso(f"{t.pagina}: un partido que no se puede escribir", d,
                             grave=False)
               for d in parser.partidos_anulados(texto)]
    # Y la guarda del default de `status`: una fila que habla de un fallo y que
    # no se supo clasificar no puede quedar en vacio callada, porque vacio
    # significa "la pagina no dijo nada".
    avisos += [validar.Aviso(f"{t.pagina}: un fallo que no se supo leer", d, grave=False)
               for d in parser.fallos_sin_leer(texto)]
    # El resaltado de la grilla contra sus propios digitos. Es el UNICO uso
    # legitimo de ese color: acusa, nunca absuelve. Medido contra los 33
    # marcadores ya arbitrados, cuando el color acompania al numero banco al
    # digito falso 12 de 12; cuando lo contradice acerto 4 de 4.
    avisos += [validar.Aviso(f"{t.pagina}: el resaltado desmiente al marcador", d,
                             grave=False)
               for d in posiciones.resaltado_sin_respuesta(
                   ps, texto, pagina=t.pagina,
                   ya_arbitrados={(m.local, m.visita) + m.dice
                                  for m in correcciones.MARCADORES if m.pagina == t.pagina})]
    # Y los que quedan afuera por tener DOS resultados, uno por club. No es un
    # problema del parseo sino del esquema, y por eso se nombran uno por uno.
    avisos += [validar.Aviso(f"{t.pagina}: un partido con dos resultados", d, grave=False)
               for d in correcciones.divididos_de(t.pagina)]
    # El cuadro de llaves, que es el segundo testigo de una copa. Los otros
    # chequeos cruzan contra la tabla de posiciones y una copa no publica: sus
    # catorce paginas son casi toda la region donde nada puede opinar.
    avisos += [validar.Aviso(f"{t.pagina}: el cuadro y la grilla no coinciden", d,
                             grave=False)
               for d in posiciones.fuera_del_cuadro(ps, texto, t.pagina)]
    # Y el cuadro tambien sabe MARCADORES, que es lo unico que puede arbitrar la
    # fase final: la tabla de posiciones solo habla de las zonas.
    avisos += [validar.Aviso(f"{t.pagina}: el cuadro dice otro marcador", d,
                             grave=False)
               for d in posiciones.marcadores_del_cuadro(ps, texto, t.pagina)]
    # Y si algun homonimo dejo de hacer falta porque arreglaron la pagina.
    avisos += [validar.Aviso(f"{t.pagina}: un homonimo quedo sin uso", d, grave=False)
               for d in correcciones.homonimos_huerfanos(t.pagina, escritos)]
    # Un enlace donde el nombre visible y el articulo se contradicen. Mira el
    # wikitexto y no los partidos, asi que no puede ir en `validar`: lo que
    # denuncia es que la fuente se contradice al NOMBRAR, antes de que eso llegue
    # a ningun partido.
    avisos += [validar.Aviso(f"{t.pagina}: el enlace se contradice", d, grave=False)
               for d in equipos.articulos_que_contradicen(texto)]
    if borradas:
        avisos.append(validar.Aviso(
            f"{borradas} partidos sin numero de jornada",
            "la pagina no la rotula; el partido entra igual, con `matchday` vacio",
            grave=False))
    if arregladas:
        avisos.append(validar.Aviso(
            f"{arregladas} partidos corregidos a mano",
            "ver fad/correcciones.py, que dice cual y con que evidencia", grave=False))
    # Una correccion que ya no engancha es GRAVE: o la fuente cambio y hay que
    # sacarla, o cambio de otra forma y esta tocando lo que no es. Las dos cosas
    # se miran antes de escribir nada.
    avisos += [validar.Aviso("correccion que no aplica", d) for d in dudas]
    return ps, avisos


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

    anterior = dataset.leer_carpeta(SALIDA)
    sf_dir = sin_fecha_en(SALIDA)
    anterior_sf = dataset.leer_carpeta(sf_dir) if sf_dir.exists() else []
    # Lo ya jugado se toma del CSV, no se vuelve a bajar. Ver `Torneo.cerrado`.
    # La clave es `source` -- la URL de la pagina -- y no (torneo, temporada).
    # Varias entradas del catalogo comparten torneo y temporada: la 2016 y la
    # 2016-17 son las dos "Primera Division 2016". Agrupando por ahi, cada una se
    # llevaba las filas de las DOS y el dataset crecia 3284 partidos de la nada.
    guardado: dict[str, list] = {}
    for f in anterior + anterior_sf:
        guardado.setdefault(dataset.pagina_de(f), []).append(f)

    filas, sin_fecha, avisos, fallo, reusados = [], [], [], False, 0
    for t in torneos.TODOS:
        listas = guardado.get(t.url)
        if t.cerrado and not args.rehacer and listas is not None:
            _repartir(listas, filas, sin_fecha)
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
        _repartir([dataset.a_fila(p, t.torneo, t.temporada, t.url, t.neutral) for p in ps],
                  filas, sin_fecha)

    if reusados:
        print(f"\n  ({reusados} torneos terminados salieron del CSV, sin bajarlos)")

    for a in avisos:
        print(f"  {a}", file=sys.stderr)

    if fallo or any(a.grave for a in avisos):
        print("\nNO se escribio el CSV: hay problemas sin resolver.\n"
              "El dataset anterior queda como estaba.", file=sys.stderr)
        return 1

    # Los chequeos que miran el dataset ENTERO, y que por eso van aca y no en
    # `validar`: lo que buscan es invisible desde una pagina sola. Un club mal
    # atribuido no rompe ninguna regla del fixture y adentro de su pagina es
    # perfectamente coherente; se lo ve por donde juega y por donde es local.
    #
    # Los dos van como aviso y no frenan nada: un club puede alquilar la cancha
    # de otro, y una categoria rara puede ser un torneo que el catalogo rotula
    # distinto. Dicen "mira esto", no "esto esta mal".
    for a in dataset.casas_compartidas(filas) + dataset.categorias_incompatibles(filas):
        print(f"  aviso: {a}", file=sys.stderr)

    # Y la que importa cuando esto corre solo: que el dataset no se achique.
    # Un chequeo de `validar` mira los partidos que HAY; este mira los que ya no.
    # Los torneos que perdieron filas en `sin-fecha/` Y ganaron en `data/`: esos
    # partidos consiguieron fecha y se mudaron, que es lo contrario de perderse.
    #
    # Frenar por una mejora sale caro de un modo particular: el build no escribe
    # NADA, ni siquiera lo que estaba bien, y el conteo de `data/` queda igual que
    # ayer -- asi que desde afuera parece que no paso nada. Estuvo frenando cuatro
    # commits de esta sesion sin que lo mirara: veinte partidos del Argentino A
    # 2012 que acababan de conseguir su fecha.
    def _por_torneo(fs):
        c: dict[tuple, int] = {}
        for f in fs:
            k = (f["tournament"], str(f["season"]))
            c[k] = c.get(k, 0) + 1
        return c

    antes_sf, ahora_sf = _por_torneo(anterior_sf), _por_torneo(sin_fecha)
    antes_d, ahora_d = _por_torneo(anterior), _por_torneo(filas)
    # Que `data/` haya crecido no alcanza: tiene que haber crecido con filas QUE
    # TRAEN FECHA. Si alguna llega sin ella, lo que paso no es que se fecharan
    # sino que se volcaron, y ahi la baja de `sin-fecha/` es exactamente la
    # perdida que esta guarda existe para ver. Sin esta condicion, mandar las
    # filas sin fecha al dataset principal se disfraza de mejora.
    todas_fechadas = all((f.get("date") or "").strip() for f in filas)
    fechados = frozenset(k for k, n in antes_sf.items()
                         if todas_fechadas
                         and ahora_sf.get(k, 0) < n
                         and ahora_d.get(k, 0) > antes_d.get(k, 0))
    perdidos = (dataset.regresiones(filas, anterior)
                + dataset.regresiones(sin_fecha, anterior_sf, salvo=fechados))
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

    cambiados = dataset.escribir_por_temporada(filas, SALIDA)
    if sin_fecha:
        cambiados |= {f"sin-fecha/{k}": v
                      for k, v in dataset.escribir_por_temporada(sin_fecha, sf_dir).items()}
    print(f"\n{len(filas)} partidos en {SALIDA.name}/")
    if cambiados:
        for archivo, n in sorted(cambiados.items()):
            print(f"   cambio {archivo} ({n} filas)")
    else:
        print("   sin cambios: ningun archivo se reescribio")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

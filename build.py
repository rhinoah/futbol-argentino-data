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

from fad import (citadas, correcciones, dataset, equipos, fechas, parser,
                 posiciones, torneos,
                 validar, wiki)

SALIDA = Path(__file__).resolve().parent / "data"   # una carpeta: un CSV por temporada


def _foja_de(pagina: str) -> tuple[str, dict] | None:
    """(texto crudo, mapa) de la fuente que publica su tabla al lado de sus partidos.

    Para las paginas CON grilla, que no la traian de antes: las sin grilla ya tienen
    el crudo en la mano de haber leido los partidos y no vuelven a pasar por aca.
    `None` cuando la pagina no tiene mapa escrito, que son la mayoria.

    SI LA FUENTE NO RESPONDE SE SIGUE SIN FOJA. Aca no hay nada que perder: el
    respaldo mejora un aviso, no alimenta el dataset. La pagina sin grilla si frena
    el build cuando RSSSF no contesta, y con razon -- ahi se quedaria sin partidos --,
    pero eso pasa mucho antes que esta llamada.
    """
    from fad import rsssf

    if pagina not in rsssf.FUENTES:
        return None
    archivo, mapa = rsssf.FUENTES[pagina]
    try:
        return rsssf.descargar(archivo), mapa
    except OSError:
        return None


def _completar_fechas_rsssf(ps, t, usadas: set | None = None) -> list:
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
    desde, hasta = rsssf.SECCION_LIGA.get(t.pagina, ("", ""))
    ajenos, avisos = rsssf.leer(crudo, mapa, t.temporada, t.anio_fin or t.temporada,
                                t.mes_inicio, desde=desde, hasta=hasta)
    puestas, mas = fechas.completar(ps, ajenos, credito=rsssf.CREDITO,
                                    verificadas=correcciones.fechados(t.pagina),
                                    usadas=usadas)
    return [validar.Aviso(f"{t.pagina}: RSSSF", d, grave=False)
            for d in avisos + mas]


def _completar_fechas_espn(ps, t, usadas: set | None = None) -> list:
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
    _, mas = fechas.completar(ps, ajenos, credito=espn.CREDITO,
                              verificadas=correcciones.fechados(t.pagina),
                              usadas=usadas)
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


def _completar_fechas(ps, t, usadas: set | None = None) -> list:
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
                                    correcciones.arbitrados(t.pagina),
                                    verificadas=correcciones.fechados(t.pagina),
                                    usadas=usadas)

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


def sin_repetir(llaves: list, ps: list, pagina: str) -> tuple[list, int, list[str]]:
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
    # EL HOMONIMO VA ACA TAMBIEN, y no es un detalle. La correccion de homonimos
    # corre mas abajo en el pipeline, asi que en este punto la pagina todavia dice
    # "Juventud Unida" mientras que las filas de la otra fuente ya vienen con el
    # nombre entero: sin aplicarlo, el cruce no las reconoce y el mismo partido
    # entra dos veces. Paso de verdad, y el docstring de `correcciones.homonimo`
    # ya avisaba de este modo de falla para el otro lado del cruce.
    def uno(nombre, art):
        return correcciones.homonimo(pagina, equipos.canonizar(nombre, art))

    def par(x):
        # Y LAS CORRECCIONES DE NOMBRE TAMBIEN, por la misma razon que el
        # homonimo: corren mas abajo en el pipeline. La pagina del Argentino A
        # 2005-06 escribe "Alumni" a secas en la promocion -- que en el padron es
        # otro club -- y una `Correccion` lo arregla despues; hasta entonces el
        # cruce contra el "Alumni (VM)" de RSSSF no reconoce nada.
        l, v = uno(x.local, x.local_art), uno(x.visita, x.visita_art)
        return frozenset(correcciones.renombrado(pagina, x.jornada, l, v,
                                                 x.goles_local, x.goles_visita))

    def corregida(x):
        """La fila de la pagina como va a quedar DESPUES de `correcciones.aplicar`.

        Sirve para no denunciar un desacuerdo que ya esta resuelto. `sin_repetir`
        corre antes que `aplicar` --y tiene que correr antes, porque decide que se
        importa--, asi que sin esto el build sigue diciendo "la pagina dice X y la
        otra fuente dice Y; se conserva el de la pagina" sobre una fila que dos
        pasos mas abajo pasa a decir Y. Es una notificacion que se vuelve falsa
        sola, que es peor que no tenerla.

        Solo apaga el MENSAJE. `alreves` se sigue contando como estaba, y es a
        proposito: ese contador alimenta al testigo que decide si le creemos la
        localia a la fuente, y un testigo que se alimenta de nuestras propias
        correcciones se termina validando a si mismo.

        Mira las DOS familias de correcciones, porque un desacuerdo puede ser de
        cualquiera de las dos: `renombrado` para los clubes --y el espejo de la
        localia, que es una `Correccion`-- y `arbitrado` para el marcador. Con
        una sola, la Revalida del Argentino A 2011-12 seguia denunciando cuatro
        partidos cuyo marcador ya estaba arbitrado y escrito.
        """
        l, v = uno(x.local, x.local_art), uno(x.visita, x.visita_art)
        gl, gv = x.goles_local, x.goles_visita
        dl, dv = correcciones.renombrado(pagina, x.jornada, l, v, gl, gv)
        # El espejo se lleva los goles con los clubes; ver `correcciones.aplicar`.
        if (dl, dv) == (v, l):
            gl, gv = gv, gl
        # Y RECIEN AHI EL MARCADOR ARBITRADO, en ese orden y no al reves: un
        # `Marcador` se declara contra la fila YA espejada, que es como la
        # encuentra `aplicar`. Preguntarlo antes del espejo no engancha nada.
        return (dl, dv) + correcciones.arbitrado(pagina, x.jornada, dl, dv, gl, gv)

    def resuelto(x, p_):
        return corregida(x) == (p_.local, p_.visita, p_.goles_local, p_.goles_visita)

    ya: dict = {}
    for x in ps:
        ya.setdefault((par(x), x.fecha), []).append(x)
    suyas: dict = {}
    for x in ps:
        if x.fase == "eliminacion":
            suyas.setdefault(par(x), []).append(x)

    nuevas, repetidas, discuten, alreves = [], 0, [], 0
    for p_ in llaves:
        suyo = frozenset((p_.local, p_.visita))
        if (suyo, p_.fecha) in ya:
            repetidas += 1
            # MISMO PARTIDO, LOCALIA AL REVES. Que el par y el dia coincidan hace
            # que sea el mismo partido, no que las dos fuentes digan lo mismo: en
            # la Primera C 2011-12 la pagina pone "Deportivo Español 1-0 Luján" y
            # ESPN "Luján 0-1 Deportivo Español", el mismo 30 de mayo. Contarlo
            # como repetido y callarse tapa un desacuerdo real -- el aviso solo
            # miraba la fecha, y con la fecha igual no decia nada.
            otro = ya[(suyo, p_.fecha)][0]
            if uno(otro.local, otro.local_art) != p_.local:
                alreves += 1
                if resuelto(otro, p_):
                    continue
                discuten.append(
                    f"mismo partido y misma fecha pero la localia al reves: la "
                    f"pagina dice {p_.fecha} "
                    f"{uno(otro.local, otro.local_art)} "
                    f"{otro.goles_local}-{otro.goles_visita} "
                    f"{uno(otro.visita, otro.visita_art)} y la otra "
                    f"fuente {p_.local} {p_.goles_local}-{p_.goles_visita} {p_.visita}")
        elif suyo in suyas:
            # EL TESTIGO DE LA LOCALIA TAMBIEN VIVE ACA. Arriba se cuenta como
            # "repetido" el partido que coincide en par Y FECHA, y eso deja fuera
            # justo a los que la pagina publica sin dia: el Argentino A 2010-11
            # tiene ocho asi, y el guard decia "0 partidos en comun, esa localia no
            # tiene testigo" teniendo ocho.
            #
            # Lo que identifica al partido cuando no hay fecha es el MARCADOR: si
            # el par es el mismo y el marcador es el mismo -- dado vuelta o no --,
            # es el mismo partido, y ahi la pagina si puede decir quien fue local.
            # Se pide que identifique UNO SOLO, como en todo el resto del repo.
            # EL MARCADOR QUE IDENTIFICA ES EL CORREGIDO, no el crudo de la
            # pagina. Se ve cuando las dos cosas se cruzan: los cuatro partidos de
            # la Revalida del Argentino A 2011-12 tienen su marcador arbitrado --
            # la pagina dice 1-0 y va 1-1 -- y ademas dejaron de tener fecha,
            # porque su tabla la publica como rango. Sin fecha, esta rama es la
            # que empareja, y comparando el marcador CRUDO no encuentra la fila:
            # `{0,1}` no es `{1,1}`. El resultado era el peor: el build volvia a
            # denunciar, uno por uno, los cuatro desacuerdos que dos pasos mas
            # abajo estan resueltos y declarados.
            #
            # `corregida` ya sabe como va a quedar la fila -- el espejo y el
            # marcador arbitrado --, asi que se le pregunta a ella. Es la misma
            # razon por la que `resuelto` existe, aplicada un renglon antes: si no
            # identifica, `resuelto` no llega a correr.
            iguales = [x for x in suyas[suyo]
                       if set(corregida(x)[2:]) == {p_.goles_local, p_.goles_visita}]
            if len(iguales) == 1:
                repetidas += 1
                mismo_local = uno(iguales[0].local, iguales[0].local_art) == p_.local
                if not mismo_local:
                    alreves += 1
                # NO HAY DESACUERDO QUE CONTAR si las dos versiones ya dicen lo
                # mismo. Son dos casos y los cubre la misma pregunta:
                #
                #   * LA FILA VIENE SIN FECHA y coincide en todo lo demas. Entre
                #     las dos versiones lo unico distinto es el dia, que es justo
                #     lo que la pagina no publica y lo que vinimos a buscar. Sin
                #     esto el build decia las dos cosas sobre los mismos cuatro
                #     partidos de la promocion de la B Nacional 2007-08: "4 llaves
                #     de RSSSF ya estaban en la grilla" y "4 partidos donde la
                #     pagina y RSSSF no coinciden". Y ademas nombraba mal al
                #     contraparte, porque `cerca` elige por cercania de FECHA y de
                #     este lado no hay: llegaba a contrastar la vuelta de RSSSF
                #     contra la ida de la pagina.
                #   * UNA CORRECCION DECLARADA ya la deja igual que la otra fuente.
                #     El desacuerdo existe en la pagina y no en el dataset, y
                #     `aplicar` lo dice por su cuenta.
                #
                # ACA HUBO UNA SEGUNDA GUARDA Y ERA CODIGO MUERTO. Preguntaba
                # `if not iguales[0].fecha and mismo_local` y salia; la escribio el
                # primer caso, antes de que existiera el segundo. Lo destapo un
                # mutante que sobrevivia: anularla entera no cambiaba un byte del
                # reporte -- 182 avisos identicos en las 149 paginas --, porque
                # coincidir en localia y marcador es exactamente lo que `resuelto`
                # ya contesta.
                #
                # Y no era inofensiva. `iguales` empareja comparando el marcador
                # como CONJUNTO, asi que ahi adentro puede caer una fila espejada:
                # la pagina diciendo `A 2-1 B` y la fuente `A 1-2 B`, mismo local y
                # resultado opuesto. Eso es un desacuerdo de verdad, y la guarda lo
                # callaba por no tener fecha. Su unico efecto posible era el
                # equivocado.
                if resuelto(iguales[0], p_):
                    continue
            cerca = min(suyas[suyo], key=lambda x: abs(_dias(x.fecha) - _dias(p_.fecha)))
            discuten.append(
                f"la pagina dice {cerca.fecha} "
                f"{uno(cerca.local, cerca.local_art)} "
                f"{cerca.goles_local}-{cerca.goles_visita} "
                f"{uno(cerca.visita, cerca.visita_art)} y RSSSF "
                f"{p_.fecha} {p_.local} {p_.goles_local}-{p_.goles_visita} {p_.visita}")
        else:
            nuevas.append(p_)
    return nuevas, repetidas, discuten, alreves


# Con menos partidos en comun, que la mayoria caiga para un lado no dice nada.
_MINIMO_PARA_JUZGAR = 8


def le_creemos_la_localia(repetidas: int, alreves: int,
                          resuelta: str = "") -> tuple[str, bool]:
    """(que decir, si hay que frenar la importacion).

    Devuelve las dos cosas por separado porque son tres estados y no dos: la
    fuente aprobo el examen, la fuente lo reprobo, o NO SE LA PUDO EXAMINAR. El
    tercero no frena nada pero tampoco es un aprobado, y en un reporte que solo
    habla cuando algo falla los dos se ven igual.

    EL SOLAPAMIENTO ES EL TESTIGO, y sale gratis. Donde la pagina y la fuente traen
    el MISMO partido, la pagina dice quien fue local con una columna rotulada
    --"Local - Ida"--; si la fuente le lleva la contra en la mayoria de esos, su
    orden no es la localia, y entonces tampoco lo es en los partidos que la pagina
    NO trae, que son justo los que se querian importar.

    No es una sospecha: se midio pagina por pagina, Y CON ESTA MISMA FUNCION -- que
    no es un detalle, porque contar el solapamiento "a ojo" da otro numero. El
    Argentino A 2004-05 coincide en 43 de 45 y el 2012-13 en 24 de 24. Y la
    alternancia entre ida y vuelta no sirve para distinguirlas: las dos fuentes
    alternan, una es el espejo de la otra. Lo unico que decide es una columna
    rotulada, y esa la tiene la pagina.

    Pide un solapamiento MINIMO porque con dos o tres partidos la mayoria no
    significa nada; sin testigo suficiente no se bloquea, y eso queda dicho aparte.

    Y TIENE UN SUPUESTO, que hay que decir: que la pagina es el patron. El
    Argentino A 2011-12 daba 6 de 31 -- DIECINUEVE por ciento -- y eso se leyo un
    tiempo como "esa fuente no sirve"; era al reves: la pagina rotula
    `Local - Vuelta` a la columna de la ida. Un testigo que mide contra un patron torcido rechaza a la fuente POR TENER
    RAZON, y ahi se pierden los partidos que solo la fuente trae: en esa pagina
    eran seis, las dos semifinales y la final, que Wikipedia publica unicamente
    como dibujo.

    `resuelta` es la salida para eso: la evidencia, cuando la localia de la pagina
    ya se establecio por afuera. No afloja la regla, la nombra, y entrar pide
    evidencia que NO dependa de la fuente que se quiere importar -- si no, el
    testigo se valida a si mismo. Ver `correcciones.LOCALIA_RESUELTA`.
    """
    if resuelta and repetidas >= _MINIMO_PARA_JUZGAR:
        return (f"el testigo dice que {alreves} de {repetidas} van al reves y no se "
                f"le hace caso: la localia de esta pagina ya se resolvio por afuera. "
                f"Ver correcciones.LOCALIA_RESUELTA", False)
    if repetidas < _MINIMO_PARA_JUZGAR:
        # SIN TESTIGO NO SE BLOQUEA, PERO SE DICE. El Argentino A 2012-13 importa
        # seis partidos con CERO en comun con la pagina.
        return (f"ojo: solo {repetidas} partido(s) en comun con la pagina, muy pocos "
                f"para saber si el orden de la fuente es la localia. Se importa "
                f"igual, pero esa localia no tiene testigo", False)
    if alreves * 2 > repetidas:
        return (f"la fuente y la pagina traen {repetidas} partidos en comun y en "
                f"{alreves} no coinciden en quien jugo de local. Ahi la pagina lo "
                f"dice con una columna rotulada, asi que el orden de la fuente NO es "
                f"la localia -- y tampoco lo seria en los que la pagina no trae. No "
                f"se importa nada: seria escribir una localia que el testigo "
                f"desmiente", True)
    return "", False


def la_fuente_se_respalda(ps: list, crudo: str, mapa: dict,
                          pagina: str = "") -> tuple[set[str], list[str]]:
    """(clubes cuya suma respalda la fuente, avisos). LA FOJA, automatizada.

    Es la prueba que en este repo se hace a mano cuando un club no cierra: sumar
    todos sus partidos y exigir las SEIS cifras -- PJ, G, E, P, GF, GC -- contra
    la fila que la fuente publica al lado de esos mismos partidos. Sirve para
    separar dos cosas que el aviso de "no cierra con su tabla" confunde en una:
    que hayamos leido mal a la fuente, o que las dos fuentes no coincidan.

    La diferencia no es academica. El Argentino A 2008-09 no cierra contra la
    tabla de Wikipedia en DIEZ clubes, y el aviso los mandaba a buscar un partido
    mal leido. Pero la tabla que publica la propia RSSSF coincide exactamente con
    nuestra suma en los veinticinco clubes de la temporada: nuestra lectura es
    fiel y lo que hay es un desacuerdo entre fuentes, que se arbitra con una
    tercera y no releyendo la segunda.

    NO SE EMPAREJA NI UN NOMBRE, ni aca ni en `rsssf.leer_tabla`. La foja de una
    zona es un CONJUNTO de filas y se compara contra el conjunto de nuestras
    sumas; a que club corresponde cada fila no hace falta saberlo para saber si
    los dos conjuntos son el mismo. La zona de cada club sale de donde juega la
    MAYORIA de sus partidos: las rondas interzonales se imprimen bajo una sola de
    las dos zonas, asi que un club de la Zone 2 tiene veintiocho partidos bajo su
    zona y cuatro bajo la otra, y la mayoria lo devuelve a la suya.

    SE ABSTIENE ANTE UN CLUB YA REVISADO A MANO. La comparacion es de conjuntos
    y no de filas, asi que no se puede sacar una sola fila de cada lado: si un
    club de la zona tiene su desvio explicado en `correcciones`, la zona entera
    deja de cruzar. Se pierde el respaldo de los otros siete, y esta bien que se
    pierda -- abstenerse deja las cosas como estaban, mientras que denunciar de
    nuevo algo ya resuelto convierte un archivo de conclusiones en ruido. Es lo
    que pasa en el Group A del 2007-08, cuyo partido dado por perdido ya tiene
    escrita su explicacion.

    SE ABSTIENE POR CARDINALIDAD. Una tabla cuya cantidad de filas no es la
    cantidad de clubes de la zona no esta hablando del mismo conjunto de partidos
    -- las de playoff son asi --, y comparar dos conjuntos distintos no responde
    nada. Abstenerse deja el aviso como estaba, que es lo peor que puede pasar;
    cruzar de mas inventaria una acusacion.

    LA FASE SEPARA LAS ZONAS QUE SE LLAMAN IGUAL. El Argentino A 2009-10 corre dos
    torneos adentro del ano y rotula DOS `Zone 1`, una del Apertura y otra del
    Clausura; hasta que la fase se leyo, no se sabia cual tabla cubria que partidos
    y se abstenia en las diez, o sea que esa temporada no tenia ningun cruce. La
    fase la declara `rsssf.FASES` y viaja con cada tabla.

    Y CUANDO HAY FASES, CADA ETAPA SUMA POR SU CUENTA. Adentro de un Apertura la
    fuente corre primero las zonas y despues los pentagonales, y la tabla de una
    zona NO cuenta los partidos del pentagonal. Sin separarlos, un club de la Zone 1
    llega a la comparacion con sus catorce de zona MAS los cinco del grupo. Las
    zonas siguen sumando juntas --el interzonal se imprime bajo una sola de ellas--
    y cada grupo suma solo.

    La separacion es OPT-IN con la fase, y eso importa: en el Argentino A 2007-08 no
    hay fases y sus `Group A` y `Group B` SON las zonas, con el interzonal impreso
    bajo una. Ahi la separacion fina se lleva puestos ocho clubes de los diecisiete
    que hoy respalda. Se midio antes de escribirla, en las cuatro paginas sin
    grilla: 8 / 17 / 25 se quedan iguales y el 2009-10 pasa de 0 a 50.
    """
    from collections import Counter, defaultdict

    from fad import rsssf

    fases = rsssf.FASES.get(pagina, {})
    # El MISMO recorte que se quedan los partidos. Sin el, en la pagina del ano la
    # tabla ve las siete divisiones y no la nuestra. Ver `rsssf._acotar`.
    desde, hasta = rsssf.SECCION_LIGA.get(pagina, ("", ""))
    tablas = rsssf.leer_tabla(crudo, mapa, fases, desde=desde, hasta=hasta)

    def etapa(zona: str) -> str:
        """Que secciones suman juntas. Sin fases declaradas, TODAS -- que es lo que
        hacia antes y es correcto cuando las secciones son las zonas. Con fases, las
        zonas de un lado y cada grupo del suyo."""
        if not fases:
            return ""
        return "Zone" if zona.startswith(("Zone", "Zona")) else zona

    def del_pool(fase: str, zona: str) -> list:
        return [p for p in ps if p.fase == "zonas"
                and (not fase or p.llave == fase) and etapa(p.zona) == etapa(zona)]

    # Los clubes con un partido dividido en esta pagina, sin importar la llave: la
    # foja acumulada cubre la temporada entera, asi que el alcance no acota nada.
    divididos = {c for par in correcciones.pares_divididos(pagina) for c in par[:2]}
    respaldados: set[str] = set()
    avisos: list[str] = []
    repetidas = {(fa, z) for fa, z, _ in tablas
                 if sum(1 for o, w, _ in tablas if (o, w) == (fa, z)) > 1}
    for fase, zona, filas in tablas:
        if (fase, zona) in repetidas:
            continue
        # La zona de cada club, por mayoria de sus partidos DENTRO DE SU POOL.
        pool = del_pool(fase, zona)
        donde: dict[str, Counter] = defaultdict(Counter)
        for p in pool:
            donde[p.local][p.zona] += 1
            donde[p.visita][p.zona] += 1
        sumas = posiciones.sumar(pool)
        clubes = {c for c, cuenta in donde.items()
                  if cuenta.most_common(1)[0][0] == zona and c in sumas}
        if len(clubes) != len(filas):
            continue
        nuestras = sorted(sumas[c] for c in clubes)
        if nuestras == sorted(filas):
            respaldados |= clubes
        elif clubes & divididos:
            # SE ABSTIENE IGUAL ANTE UN PARTIDO DIVIDIDO, y por la misma razon que
            # ante un club revisado: el desvio ya tiene su explicacion escrita. Un
            # dividido se JUGO -- la tabla de la fuente lo cuenta -- y su fila no
            # se puede escribir, porque cada club termino con un resultado
            # distinto, asi que a esos clubes les falta un partido contra la tabla
            # y siempre les va a faltar. En el Argentino A 2006-07 son cuatro
            # clubes, dos pares, y desvian exactamente `+1 PJ, +1 en contra, +1
            # perdido`; sin esta rama, habilitar sus tablas acumuladas producia dos
            # alarmas perfectamente falsas.
            #
            # No se suma el partido de vuelta para poder comparar: seria escribir
            # un marcador que este repo declaro que no puede escribir.
            continue
        elif any(correcciones.revisado(pagina, c) for c in clubes):
            # Callado, no abstenido. La zona con un club ya revisado a mano solo
            # importa cuando el cruce FALLA: ahi el desvio ya tiene su explicacion
            # escrita y repetirla convierte un archivo de conclusiones en ruido.
            # Cuando el cruce PASA no hay nada que repetir, y abstenerse ahi
            # apagaba el chequeo justo en la pagina que lo motivo -- el Argentino
            # A 2008-09, cuyos diez clubes estan revisados y cuyas tres zonas
            # cierran perfecto contra la foja de la fuente.
            continue
        else:
            distintas = sum(1 for a, b in zip(nuestras, sorted(filas)) if a != b)
            # EL AVISO NO DICE DE QUIEN ES LA CULPA PORQUE NO LA SABE. Lo
            # tentador es leer esto como "la leimos mal", y es una de las dos
            # explicaciones, pero no la unica: una fuente tambien puede
            # contradecirse sola. El Argentino A 2007-08 publica un partido
            # abandonado con la nota `(awarded 0-2, ...)` en su lista y lo cuenta
            # 0-1 en su propia tabla. Nombrar al culpable de mas es exactamente
            # el error que este chequeo vino a arreglar en el aviso de al lado.
            avisos.append(
                f"{zona}: la suma de los partidos que trae la fuente no coincide con "
                f"la tabla que publica la fuente misma, en {distintas} de "
                f"{len(filas)} clubes. Las dos cosas salen del MISMO lugar, asi que "
                f"o los leimos mal o la fuente se contradice sola. Mirar el partido "
                f"antes de mirar la otra fuente")
    return respaldados, avisos


def fechar_con_las_llaves(ps: list, llaves: list,
                          verificadas: set | None = None,
                          usadas: set | None = None) -> list[str]:
    """Le pone fecha a los partidos de eliminacion que la pagina trae sin dia.

    LO QUE LA PAGINA YA TIENE PUEDE TENERLO SIN FECHA. El bloque que importa
    llaves solo sabia agregar lo que faltaba y descartar lo repetido, y
    "repetido" incluye al partido que la pagina publica sin dia: el cruce lo
    reconocia y se iba igual a `sin-fecha/` porque nadie miraba la fecha. Eran
    los ocho de la Tercera fase del Argentino A 2012-13.

    EL IDENTIFICADOR ES EL PAR ORDENADO, sin jornada ni llave. No cruzan por
    llave porque los vocabularios son distintos --la pagina rotula "Tercera fase"
    y la fuente "Third Phase - First leg"-- y no hace falta: las dos patas de una
    serie son (A,B) y (B,A), asi que el par ordenado ya las distingue. La regla de
    colision de `fechas.completar` sigue puesta y el marcador sigue verificando.

    SOLO SOBRE LA ELIMINACION, que es de lo que hablan las llaves. Esto corre en
    la etapa de parseo, ANTES de que el completador de la fase regular haga lo
    suyo, asi que en este momento la pagina entera puede estar sin fechas.
    Pasarle todo daba trescientos setenta y siete "sin pareja" en la Primera C
    2008-09, un grave, y le ofrecia a un partido de liga la fecha de una llave.
    """
    from fad import fechas, rsssf

    return fechas.completar(
        [x for x in ps if x.fase == "eliminacion"],
        [fechas.Ajeno(fecha=x.fecha, jornada=0, local=x.local, visita=x.visita,
                      goles_local=x.goles_local, goles_visita=x.goles_visita)
         for x in llaves if x.fecha],
        credito=rsssf.CREDITO, verificadas=verificadas,
        usadas=usadas)[1]


def sin_repetir_sin_fecha(llaves: list, ps: list,
                          pagina: str) -> tuple[list, int, list[str]]:
    """Lo mismo que `sin_repetir` pero para filas que NO traen fecha.

    Hace falta porque el formato compacto de RSSSF -- el del Argentino A 2004-05 --
    da la fecha como RANGO y de ahi no sale un dia. Sin fecha, la casilla de
    `sin_repetir` no cruza NUNCA y entrarian las setenta y ocho patas, la mitad de
    ellas duplicando lo que la pagina ya publica.

    La casilla pasa a ser el partido entero: local, visita y marcador, EN ESE
    ORDEN. Se midio que sirve de identificador en esta pagina -- sus sesenta
    partidos de eliminacion dan sesenta claves distintas, ni una repetida --, y el
    orden es lo que separa las dos patas de una misma llave.

    Y la vuelta de eso: si la pagina tiene el partido AL REVES -- mismo marcador,
    local y visitante cambiados -- no es un partido que falte sino un desacuerdo
    sobre quien jugo en casa. Se conserva el de la pagina y se avisa. Son dos patas
    en esta temporada, la llave Villa Mitre - General Paz Juniors.
    """
    # Mismo cuidado que en `sin_repetir`: el homonimo se aplica aca porque la
    # correccion corre mas abajo, y sin el la pagina y la otra fuente llaman
    # distinto al mismo club y el partido entra dos veces.
    def uno(nombre, art):
        return correcciones.homonimo(pagina, equipos.canonizar(nombre, art))

    suyos = set()
    for x in ps:
        if x.fase == "eliminacion":
            suyos.add((uno(x.local, x.local_art), uno(x.visita, x.visita_art),
                       x.goles_local, x.goles_visita))

    nuevas, repetidas, discuten = [], 0, []
    for p_ in llaves:
        mio = (p_.local, p_.visita, p_.goles_local, p_.goles_visita)
        alreves = (p_.visita, p_.local, p_.goles_visita, p_.goles_local)
        if mio in suyos:
            repetidas += 1
        elif alreves in suyos:
            discuten.append(f"la pagina dice {p_.visita} {p_.goles_visita}-"
                            f"{p_.goles_local} {p_.local} y RSSSF lo tiene al reves, "
                            f"{p_.local} {p_.goles_local}-{p_.goles_visita} {p_.visita}")
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
    # LAS DECLARACIONES DE `Fechado` QUE ENGANCHEN, juntadas entre TODOS los
    # completadores. Una pagina pasa por varios --worldfootball, RSSSF, el de
    # llaves, las citas-- y cada uno ve solo los desacuerdos que a el le
    # tocan, asi que ninguno puede decir por su cuenta que una declaracion
    # quedo huerfana: las cinco del Argentino A 2012-13 se reparten entre
    # dos. El que sabe cuando se termino la pagina es este.
    usadas: set = set()
    # (texto crudo, mapa) de la fuente externa, si los partidos vienen de una.
    foja: tuple[str, dict] | None = None
    # Las llaves que RSSSF publica para esta pagina, para fecharlas mas abajo.
    llaves_rsssf: list = []
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
        # Se guardan para cruzar la foja MAS ABAJO y no aca: la fuente publica
        # su propia tabla al lado de sus propios partidos, y compararla contra
        # nuestra suma dice si la leimos bien. Va despues de canonizar porque
        # `contrastar`, que es quien usa el resultado, habla en nombres
        # canonicos, y dos vocabularios no cruzan.
        foja = (crudo, mapa)
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
                    t.mes_inicio, *rsssf.SECCION.get(t.pagina, ("", "")))
                for p_ in llaves:
                    p_.torneo = t.torneo
                nuevas, repetidas, discuten, alreves = sin_repetir(
                    llaves, ps, t.pagina)
                que_decir, frenar = le_creemos_la_localia(
                    repetidas, alreves,
                    correcciones.LOCALIA_RESUELTA.get(t.pagina, ""))
                if que_decir:
                    mas.append(f"RSSSF: {que_decir}")
                if not frenar:
                    ps += nuevas
                if repetidas:
                    mas.append(f"{repetidas} llaves de RSSSF ya estaban en la "
                               f"grilla de la pagina y no se duplicaron")
                if discuten:
                    mas.append(f"{len(discuten)} partidos donde la pagina y RSSSF no "
                               f"coinciden; se conserva el de la pagina: "
                               + " | ".join(discuten[:3]))
                # NO SE COMPLETA ACA. Ver mas abajo: en esta etapa `ps`
                # todavia trae los nombres crudos de Wikipedia.
                llaves_rsssf = llaves
                importados += [validar.Aviso(f"{t.pagina}: RSSSF llaves", d,
                                             grave=False) for d in mas]
        # El formato compacto va aparte: sus filas salen SIN FECHA -- el archivo
        # da un rango que cubre las dos patas -- y por eso terminan en
        # `data/sin-fecha`, que es la carpeta que existe para esto.
        if t.rsssf_compacto:
            from fad import rsssf
            archivo, mapa = rsssf.FUENTES[t.pagina]
            try:
                crudo = rsssf.descargar(archivo)
            except OSError as e:
                importados.append(validar.Aviso(
                    f"{t.pagina}: RSSSF no respondio, asi que la fase final se "
                    f"queda sin partidos", repr(e), grave=False))
            else:
                llaves, mas = rsssf.leer_llaves_compacto(crudo, mapa)
                for p_ in llaves:
                    p_.torneo = t.torneo
                nuevas, repetidas, discuten = sin_repetir_sin_fecha(llaves, ps, t.pagina)
                ps += nuevas
                if repetidas:
                    mas.append(f"{repetidas} patas de RSSSF ya estaban en la grilla "
                               f"de la pagina y no se duplicaron")
                if discuten:
                    mas.append(f"{len(discuten)} patas donde la pagina y RSSSF no "
                               f"coinciden en quien jugo de local; se conserva el de "
                               f"la pagina: " + " | ".join(discuten[:3]))
                importados += [validar.Aviso(f"{t.pagina}: RSSSF compacto", d,
                                             grave=False) for d in mas]

        # Y lo mismo desde ESPN, para las temporadas que RSSSF no cubre. Mismo
        # criterio: solo entra lo que la pagina no tiene, y por el mismo cedazo.
        if t.espn_llaves:
            from fad import espn
            liga, rangos, mapa = espn.FUENTES[t.pagina]
            try:
                eventos = espn.descargar(liga, rangos)
            except OSError as e:
                importados.append(validar.Aviso(
                    f"{t.pagina}: ESPN no respondio, asi que la fase final se "
                    f"queda sin partidos", repr(e), grave=False))
            else:
                llaves, mas = espn.leer_llaves(eventos, mapa, t.torneo)
                nuevas, repetidas, discuten, alreves = sin_repetir(
                    llaves, ps, t.pagina)
                que_decir, frenar = le_creemos_la_localia(
                    repetidas, alreves,
                    correcciones.LOCALIA_RESUELTA.get(t.pagina, ""))
                if que_decir:
                    mas.append(f"ESPN: {que_decir}")
                if not frenar:
                    ps += nuevas
                if repetidas:
                    mas.append(f"{repetidas} llaves de ESPN ya estaban en la grilla "
                               f"de la pagina y no se duplicaron")
                if discuten:
                    mas.append(f"{len(discuten)} partidos donde la pagina y ESPN no "
                               f"coinciden; se conserva el de la pagina: "
                               + " | ".join(discuten[:3]))
                importados += [validar.Aviso(f"{t.pagina}: ESPN llaves", d,
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
    avisos += _completar_fechas(ps, t, usadas) if t.wf else []
    # `sin_grilla` no pasa por aca: sus filas YA salieron de RSSSF con su fecha
    # puesta, asi que completarlas es leer la misma pagina dos veces y emitir
    # cada aviso por duplicado.
    avisos += _completar_fechas_rsssf(ps, t, usadas) if t.rsssf and not t.sin_grilla else []
    # Las llaves de RSSSF le ponen fecha a lo que la pagina publica sin dia, y
    # va ACA y no en el bloque que las importa: alla `ps` todavia trae los
    # nombres crudos de Wikipedia mientras que las llaves ya vienen canonicas,
    # asi que el par no emparejaba y solo se fechaba lo que casualmente se
    # escribia igual. Eran 2 de 8 en el Argentino A 2010-11.
    if llaves_rsssf:
        avisos += [validar.Aviso(f"{t.pagina}: RSSSF llaves", d, grave=False)
                   for d in fechar_con_las_llaves(
                       ps, llaves_rsssf, correcciones.fechados(t.pagina),
                       usadas)]
    # Y al final, las fechas copiadas a mano de una fuente citada, que van
    # ULTIMAS a proposito: solo tienen que tocar lo que ningun lector pudo
    # fechar. Ver el docstring de `fad/citadas.py`, que dice cuando corresponde
    # y que lo sostiene.
    if citadas.FECHAS.get(t.pagina):
        avisos += [validar.Aviso(f"{t.pagina}: fechas citadas a mano", d, grave=False)
                   for d in fechas.completar(ps, citadas.ajenos(t.pagina),
                                             credito=citadas.CREDITO)[1]]
    avisos += _completar_fechas_espn(ps, t, usadas) if t.espn else []
    # LAS FECHAS CORREGIDAS A MANO VAN AL FINAL, cuando ya paso todo el que
    # sabe fechar. La que hay que pisar muchas veces todavia no existe cuando
    # corren las otras correcciones --la escribe RSSSF o ESPN un rato despues--,
    # asi que declararlas alla no engancharia nada. Ver `correcciones.Dia`.
    avisos += [validar.Aviso(f"{t.pagina}: fecha corregida a mano", d, grave=False)
               for d in correcciones.corregir_fechas(ps, t.pagina)]
    # Y RECIEN AHORA se puede decir cual no engancho con nada. Un `Fechado`
    # huerfano quiere decir que alguna de las dos fuentes cambio de fecha y que
    # la verificacion que lo sostiene quedo vieja: si se lo deja, silencia un
    # desacuerdo que nadie miro. Misma guarda que `revisados_huerfanos`.
    sobran = sorted(correcciones.fechados(t.pagina) - usadas)
    if sobran:
        avisos.append(validar.Aviso(
            f"{t.pagina}: {len(sobran)} desacuerdos de dia declarados como"
            f" verificados que ya no enganchan con ninguno",
            "si la fuente cambio de fecha, sacalos de fad/correcciones.py: "
            + "; ".join(f"{j} {l} vs {v} ({n} contra {o})"
                        for j, l, v, n, o in sobran[:3]), grave=False))
    avisos += validar.revisar(ps, en_curso=not t.cerrado,
                              divididos=correcciones.pares_divididos(t.pagina))
    # La tabla de posiciones de la propia pagina, contra la suma de los partidos.
    # Va como aviso: lo que denuncia es una contradiccion DE LA FUENTE consigo
    # misma, y frenar el build de todos los dias por eso seria desproporcionado.
    # Sirve igual, y para algo que ningun otro chequeo puede hacer: decidir cual
    # de dos fuentes tiene razon sobre un marcador, sin traer una tercera.
    # La foja de la fuente, cuando los partidos vienen de una. Sale antes que el
    # cruce contra Wikipedia porque es lo que le da sentido: sin ella, un club que
    # no cierra manda a buscar un partido mal leido aunque no lo haya.
    respaldados: set[str] = set()
    # Y LA FOJA NO ES SOLO PARA LAS PAGINAS SIN GRILLA. Nacio ahi porque ahi era
    # imprescindible --si los partidos salen de RSSSF, lo primero que hay que
    # descartar es haberla leido mal--, pero en una pagina CON grilla contesta algo
    # distinto y mas fuerte. Ahi los partidos salen de Wikipedia, asi que una
    # coincidencia exacta con la tabla de RSSSF dice que nuestra lectura de la
    # grilla esta respaldada por una fuente independiente: si igual no cierra contra
    # la tabla de la propia Wikipedia, la que se contradice es Wikipedia.
    #
    # Sale gratis: son las paginas que ya tienen mapa escrito -- para las llaves o
    # para las fechas -- y `descargar` cachea el archivo en disco. Cinco de las diez
    # cruzan hoy, con 102 clubes respaldados y cero desacuerdos: la B Nacional
    # 2007-08, las Primera C 2008-09, 2009-10 y 2010-11 y la Primera B 2010-11.
    #
    # Las otras cinco --los Argentino A-- publican una tabla por zona y necesitan el
    # mapa de nombres de cada temporada, que no esta escrito. Se abstienen, que es
    # el caso previsto: cero respaldos y cero avisos, igual que antes.
    foja = foja or _foja_de(t.pagina)
    if foja:
        respaldados, mas = la_fuente_se_respalda(ps, foja[0], foja[1], t.pagina)
        avisos += [validar.Aviso(f"{t.pagina}: RSSSF no cierra consigo misma", d,
                                 grave=False) for d in mas]
    avisos += [validar.Aviso(f"{t.pagina}: no cierra con su tabla de posiciones", d,
                             grave=False)
               for d in posiciones.contrastar(ps, texto, pagina=t.pagina,
                                              respaldados=respaldados,
                                              de_afuera=t.sin_grilla)]
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
        # "salieron del CSV" se leia como "se fueron del CSV", que es justo lo
        # contrario de lo que pasa: sus filas se LEEN de ahi en vez de volver a
        # bajar la pagina. Un mensaje que asusta por como esta escrito cuesta
        # igual que uno que informa mal.
        print(f"\n  ({reusados} torneos ya terminados: sus filas se reusaron "
              f"del CSV en vez de volver a bajar la pagina)")

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

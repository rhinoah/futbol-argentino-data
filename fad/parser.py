#!/usr/bin/env python3
"""
fad/parser.py
=============
Sacar los partidos del wikitexto de una temporada.

Conviven TRES formatos, y el mismo torneo cambia de uno a otro segun el anio:

1. FASE DE GRUPOS -- una `wikitable` con columnas
   `Local | Resultado | Visitante | Estadio | Fecha | Hora`.
   Lo dificil es el `rowspan`: cuando varios partidos comparten fecha u horario,
   la celda aparece UNA sola vez y las filas siguientes vienen con menos celdas.
   Un parser que asuma "6 celdas por fila" corre las columnas y termina leyendo
   el estadio como si fuera la fecha, sin fallar.

2. ELIMINACION -- plantillas `{{Partido|local=...|resultado=...}}` con parametros
   nombrados, practicamente un JSON.

3. COPA -- una tabla por ronda, `Fecha | Estadio | Equipo 1 | Partido | Equipo 2`,
   con las celdas separadas por `||` en un solo renglon. Cual usar lo dice el
   catalogo (`torneos.Torneo.formato`) y no se adivina: el parser equivocado no
   falla, devuelve cero partidos.

EL ERROR QUE HAY QUE NO COMETER
-------------------------------
En `|resultado = 0:1''' (0:0)` lo que esta entre parentesis es el ENTRETIEMPO,
no la tanda de penales. Los penales viven en su propio parametro
(`|resultado penalti = 4:3`). Leer los parentesis como penales no falla: inventa
definiciones por penales en partidos que se ganaron en los 90, y despues el que
consume el dataset arma un cuadro de eliminacion equivocado.

Esa es la forma tipica de fallar de todo esto: un parser mal escrito no explota,
miente. Por eso `validar.py` chequea invariantes en vez de confiar.
"""
from __future__ import annotations

import re
import unicodedata
from dataclasses import dataclass, field

# Solo por `normalizar`, que es una funcion de cadenas y nada mas. El parser no
# traduce nombres -- eso lo hace `build` despues, a proposito --, pero para
# decidir si dos titulos de articulo son el mismo hace falta la MISMA regla que
# usa el padron para buscarlos. Escribir una segunda regla aca es exactamente el
# diccionario paralelo que este proyecto ya pago una vez.
from fad import equipos

MESES = {"enero": 1, "febrero": 2, "marzo": 3, "abril": 4, "mayo": 5, "junio": 6,
         "julio": 7, "agosto": 8, "septiembre": 9, "setiembre": 9, "octubre": 10,
         "noviembre": 11, "diciembre": 12}

COLUMNAS = ["local", "resultado", "visita", "estadio", "fecha", "hora"]

# Nombres de columna que a veces vienen con colspan. NO son etiquetas de seccion.
_COLUMNAS_CONOCIDAS = {"local", "resultado", "visitante", "visita", "estadio",
                       "fecha", "hora", "partido", "equipo 1", "equipo 2",
                       "equipo", "arbitro", "árbitro", "ciudad"}

# El titulo "Resultados" aparece en nivel 2 o en nivel 3 segun la temporada: las
# de Primera de 2016 a 2024 lo ponen como `== Resultados ==` y las de 2025-26
# como `=== Resultados ===`. Pidiendo tres `=` o mas, nueve temporadas devolvian
# CERO partidos -- que no se distingue de "todavia no empezo el torneo".
_TITULO_RESULTADOS = re.compile(r"^(=+)\s*Resultados\s*=+\s*$", re.M)
# Cualquier titulo de Wikipedia. Sirve para cortar la jornada: lo que viene
# despues de un titulo no pertenece a la tabla de arriba.
_TITULO_CUALQUIERA = re.compile(r"^=+[^=\n]+=+\s*$", re.M)

# Un titulo de zona de primer nivel: `== Zona A ==`. En el ascenso la zona no
# viene en un encabezado de tabla sino en el titulo de la seccion que la contiene.
_TITULO_ZONA = re.compile(r"^==\s*((?:Zona|Grupo)\b[^=\n]*?)\s*==\s*$", re.M | re.I)


@dataclass
class Partido:
    fecha: str = ""              # ISO, YYYY-MM-DD
    hora: str = ""
    local: str = ""
    visita: str = ""
    goles_local: int | None = None
    goles_visita: int | None = None
    penales_local: int | None = None
    penales_visita: int | None = None
    torneo: str = ""
    fase: str = ""               # "zonas" / "eliminacion"
    zona: str = ""
    jornada: str = ""
    llave: str = ""              # que cuadro de eliminacion: una pagina tiene varios
    # A que ARTICULO de Wikipedia enlaza cada equipo. Es el unico dato que
    # identifica al club sin ambiguedad: "Estudiantes" a secas es el de La Plata
    # en Primera y el de Caseros en Primera B, pero los articulos son distintos.
    local_art: str = field(default="", repr=False)
    visita_art: str = field(default="", repr=False)
    estadio: str = ""
    # De donde salio el MARCADOR: "" (la pagina no dijo otra cosa),
    # "suspendido" (no llego al final) o "escritorio" (termino y el numero
    # publicado lo puso un fallo). Ver `status_de_la_fila`.
    status: str = ""
    fecha_cruda: str = field(default="", repr=False)   # para diagnosticar
    # De donde salio la FECHA, cuando no salio de la pagina de Wikipedia. El
    # credito viaja con el dato: si una fila usa una segunda fuente, su `source`
    # lo dice. Un dataset que atribuye mal es un dataset que miente sobre si mismo.
    fuente_fecha: str = field(default="", repr=False)
    # Si el partido se jugo en cancha NEUTRAL. `None` quiere decir "la pagina no
    # dijo", y entonces manda lo que diga el torneo -- la Copa Argentina es toda
    # neutral, una liga no.
    #
    # Que una pagina lo diga no es una suposicion: cuando no hay local, la tabla
    # rotula sus columnas "Equipo 1 / Equipo 2" en vez de "Local / Visitante".
    # Son los desempates, los reducidos y las definiciones, que se juegan en
    # cancha de un tercero. Ver `_ENCABEZADO_SIN_LOCAL`.
    neutral: bool | None = field(default=None, repr=False)


# --------------------------------------------------------------------------
# limpieza de wikitexto
# --------------------------------------------------------------------------
_ATRIBUTO = re.compile(r"=|bgcolor|style|align|width|span|scope", re.I)


def limpiar(texto: str) -> str:
    """Deja el contenido visible de una celda: sin plantillas, links ni formato."""
    s = texto.strip()
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S | re.I)
    s = re.sub(r"<ref[^>]*/>", "", s, flags=re.I)
    # `{{nowrap|X}}` se DESENVUELVE, no se borra: es puro formato, pero adentro
    # esta el dato. Borrarla junto con las demas plantillas hacia desaparecer
    # equipos enteros ("{{nowrap|Gimnasia y Esgrima (LP)}}" quedaba en nada).
    s = re.sub(r"\{\{\s*nowrap\s*\|(.*?)\}\}", r"\1", s, flags=re.I | re.S)
    # La misma plantilla SIN cerrar tambien existe, y como no cierra no la agarra
    # ni la de arriba ni el barrido general: un club quedaba llamandose
    # "{{nowrap|Defensores de Cambaceres".
    s = re.sub(r"\{\{\s*nowrap\s*\|", "", s, flags=re.I)
    s = re.sub(r"\{\{[^{}]*\}\}", "", s)
    # Un enlace a un archivo NO es texto: `[[Archivo:Copa.svg|15px|Campeón]]` es
    # una imagen. Tratandolo como un wikilink comun queda "15px|Campeón" pegado
    # al nombre, y el equipo pasa a llamarse "Boca Juniors 15px|Campeón
    # matematico". Van 20 nombres asi en las temporadas 2016-2024, donde se
    # marcaba al campeon y a los descendidos con un iconito.
    s = re.sub(r"\[\[\s*(?:Archivo|File|Imagen|Image)\s*:[^\]]*\]\]", "", s, flags=re.I)
    s = re.sub(r"\[\[([^\]|]*\|)?([^\]]*)\]\]", r"\2", s)    # [[destino|texto]] -> texto
    s = s.replace("'''", "").replace("''", "")
    # `<sup>` se borra CON su contenido, como `<ref>`: en este corpus nunca lleva
    # un dato, siempre es la llamada a una nota al pie. El barrido general de
    # tags de abajo saca el `<sup>` pero deja el numero suelto, y el club pasa a
    # llamarse "Unión (Sunchales) 1". Se reviso una por una las 195 apariciones:
    # digitos, ordinales de infobox ("1<sup>.er</sup> título") y una sola con un
    # wikilink adentro, que es prosa de un articulo de club y no una celda.
    s = re.sub(r"<sup[^>]*>.*?</sup>", "", s, flags=re.S | re.I)
    s = re.sub(r"<[^>]+>", " ", s)
    s = re.sub(r"\s+", " ", s).strip()
    # Un superindice de nota al pie no es parte del nombre: "Atlético Tucumán¹"
    # es el mismo club que "Atlético Tucumán", pero como cadena es otro, y entra
    # al padron como un club nuevo con un solo partido.
    # Va con escapes y no con los caracteres pelados porque `¹²³` viven fuera del
    # bloque ⁰-₟ donde estan los demas superindices, y escritos a mano
    # el rango parece un error de tipeo.
    s = re.sub(r"[\u00b9\u00b2\u00b3\u2070-\u209f]+$", "", s).strip()
    # La misma nota al pie pero en ASCII: `Cipolletti (*)`, `Gimnasia y Esgrima
    # (CdU) (**)`. Se saca solo si queda nombre atras, para no vaciar una celda
    # que sea unicamente el marcador.
    return re.sub(r"^(.+?)\s*\(\*+\)$", r"\1", s).strip()


def _celda(bruta: str) -> tuple[int, str]:
    """Separa atributos de contenido. Devuelve (cuantas filas ocupa, contenido).

    `rowspan=3|22 de enero` -> (3, '22 de enero');  `Boca Juniors` -> (1, 'Boca Juniors')
    """
    m = re.match(r"^\s*([^|]*?)\|(?!\|)(.*)$", bruta, re.S)
    if not m or not _ATRIBUTO.search(m.group(1)):
        return 1, limpiar(bruta)
    n = re.search(r"rowspan\s*=\s*\"?(\d+)", m.group(1), re.I)
    return (int(n.group(1)) if n else 1), limpiar(m.group(2))


def _seccion(cab: str) -> str:
    """Normaliza la etiqueta de una seccion.

    La misma pagina escribe "Interzonal" en 15 fechas e "Interzonales" en una.
    Es lo mismo, pero salen dos valores distintos en la columna `group` y quien
    consuma el CSV los cuenta como dos cosas.
    """
    if re.match(r"(?i)^interzonal", cab):
        return "Interzonal"
    return cab


def articulos_de_la_pagina(texto: str) -> dict[str, str]:
    """{nombre visible: articulo} para toda la pagina, y SOLO cuando es univoco.

    Las tablas de resultados muchas veces escriben el equipo sin enlace, pero la
    seccion de equipos participantes si lo enlaza. Con este mapa, un "Estudiantes"
    pelado en una tabla se resuelve con el enlace que la misma pagina uso en otro
    lado.

    Si dentro de UNA pagina el mismo nombre visible apunta a dos articulos, no se
    devuelve ninguno: ahi no hay testigo, y adivinar es justo lo que no hay que
    hacer.

    Pero "dos articulos" se compara NORMALIZADO, y esa no es una sutileza. La
    Primera B 2015 enlaza a Estudiantes de Caseros ocho veces bien y dos veces
    escrito "Club Atletico Estudiantes", sin la tilde. Son el mismo articulo y un
    typo, no un desacuerdo -- pero comparando por igualdad de cadena la guarda se
    disparaba, "Estudiantes" pelado se quedaba sin testigo, y el fallback lo
    resolvia por el nombre solo: el de La Plata, que nunca jugo la Primera B.
    Cuarenta y cuatro partidos en la historia del club equivocado, por una tilde.
    O sea que la guarda contra adivinar terminaba forzando la adivinanza.
    """
    vistos: dict[str, dict[str, str]] = {}
    for destino, visible in re.findall(r"\[\[([^\]|]+)\|([^\]]+)\]\]", texto):
        d = destino.strip()
        if d.lower().startswith(("estadio", "provincia", "anexo", "archivo", "file")):
            continue
        # La clave es la forma normalizada y el valor una de las grafias. Cual de
        # las dos se devuelve da igual: `equipos.buscar` normaliza el articulo
        # antes de buscarlo, asi que las dos resuelven al mismo club.
        vistos.setdefault(limpiar(visible), {})[equipos.normalizar(d)] = d
    return {v: next(iter(d.values())) for v, d in vistos.items() if len(d) == 1}


_NOTA_AL_PIE = re.compile(r"<ref[^>]*>.*?</ref>|<ref[^>]*/>", re.S | re.I)


def _partir(fila: str) -> list[str]:
    """Las celdas crudas de una fila, en los DOS estilos que usa Wikipedia.

    Las tablas de liga ponen una celda por linea (`\\n|`); las de la Copa meten
    la fila entera en un renglon separando con `||`. Es la misma tabla para
    MediaWiki, pero un parser que solo conozca un estilo lee la fila de la Copa
    como una unica celda gigante y no encuentra ningun partido.

    Lo que va ANTES de la primera celda son atributos de la fila, no un dato:
    `|- bgcolor="#F5FAFF"`. Se descarta. Contarlo como celda corre todas las
    columnas un lugar, y como la Copa sombrea una fila de cada dos, se perdia
    exactamente la mitad de los partidos -- 16 de 32 treintaidosavos, 8 de 16
    dieciseisavos. Nada fallaba: la fila corrida no tenia un marcador donde
    buscarlo y se descartaba sola.

    Y las celdas VACIAS se conservan, aunque no digan nada, porque la posicion es
    el dato. Descartarlas corre todas las columnas que vienen despues, y el
    resultado no es un hueco sino un valor equivocado en la columna de al lado.
    Asi se perdian 373 de las 438 fechas del Argentino A 2010-11: de la Fecha 18
    en adelante la pagina deja el estadio en blanco, la fecha se corria a esa
    columna y `venue` terminaba diciendo "2 de febrero". El partido salia sin
    fecha y con una fecha por cancha, que es peor que salir sin nada.
    """
    # Y la nota al pie se saca ANTES de partir, porque adentro trae pipes: una
    # `{{Cita web\n|url=...\n|fechaacceso=...}}` escrita en varias lineas mete
    # tres celdas falsas y corre todo lo que viene despues. Es la misma forma de
    # fallar que las celdas vacias del parrafo anterior, y tampoco falla
    # ruidosamente: el Apertura 2025 publicaba nueve partidos cuya HORA era
    # "título=Tras muerte del Papa Francisco la AFA suspende partidos del futbol
    # argentino", y dos quedaban con la fecha de consulta de la cita.
    #
    # Se puede borrar sin perder nada aunque la nota traiga el dato de cuando se
    # jugo el partido postergado, porque eso se lee de la FILA CRUDA -- ver
    # `_fecha_de_la_nota` --, antes de llegar aca.
    fila = _NOTA_AL_PIE.sub("", fila)
    partes = re.split(r"\n\|", "\n" + fila.replace("||", "\n|"))
    return partes[1:]


# Mes en que arranca una temporada que cruza el calendario. Los partidos de ese
# mes en adelante son del PRIMER anio; los anteriores, del segundo. Es el valor
# mas comun (agosto), pero NO sirve para todas: la 2019-20 arranco el 26 de julio
# de 2019, y con el corte en agosto su Fecha 1 entera quedaba fechada en julio de
# 2020 -- la primera jornada del torneo, un anio adelante, al final de la
# temporada. Por eso el mes va por temporada en el catalogo.
MES_INICIO_HABITUAL = 8


# "Suspendido por lluvia. Se jugó el 29 de julio, a partir de las 15:00." La
# nota dice CUANDO SE JUGO, y esa es la fecha del partido.
#
# `completó`, `reanudó` y `terminó` quedan afuera A PROPOSITO, y no es un olvido:
# ahi el partido EMPEZO el dia de la celda y se termino despues -- son los 105
# casos de "se completó el 5 de marzo" --, asi que la fecha buena sigue siendo la
# primera. Meterlos en el mismo saco moveria 105 partidos al dia equivocado.
_SE_JUGO = re.compile(
    r"(?i)se\s+(?:jug[oó]|jugaron|disput[oó]|disputaron)\s+(?:el\s+)?"
    r"(\d{1,2}\s*de\s+[a-záéíóúñ]+(?:\s*de\s+\d{4})?)")


def _fecha_de_la_nota(fila: str, anio: int, anio_fin: int | None,
                      mes_inicio: int, programada: str = "") -> str:
    """La fecha en que se jugo de verdad, cuando la nota al pie la dice.

    Se lee de la FILA cruda y no de la celda, por dos motivos. Uno, que para
    cuando la celda esta armada `limpiar` ya borro el `<ref>` con la nota
    adentro. Dos, que la nota es de la fila: puede colgar de la celda de la
    fecha, de la del resultado o de la del estadio, y en las tres esta hablando
    del mismo partido. Sacarla de la fila las agarra a las tres sin que el texto
    de la nota se meta en la columna de la que colgaba.
    """
    m = _SE_JUGO.search(fila)
    if not m:
        return ""
    jugada = a_iso(m.group(1), anio, anio_fin, mes_inicio)
    # Un partido no se juega ANTES del dia para el que estaba programado, asi que
    # si la regla de la temporada lo puso antes, el anio que le toca es el que
    # sigue. Pasa una sola vez en las 296 notas, y es el caso que la regla no
    # puede saber: Acassuso-Argentino de Quilmes de la Primera B 2019-20, previsto
    # para el 14 de marzo de 2020 y jugado el 29 de noviembre, cuando volvio el
    # futbol. Por noviembre la regla contesta 2019, que es medio anio antes de
    # que lo suspendieran.
    if jugada and programada and jugada < programada:
        jugada = f"{int(jugada[:4]) + 1}{jugada[4:]}"
    return jugada


def a_iso(texto: str, anio: int, anio_fin: int | None = None,
          mes_inicio: int = MES_INICIO_HABITUAL) -> str:
    """'22 de enero' -> '2026-01-22'. Cadena vacia si no se entiende.

    Las paginas escriben el dia y el mes pero NO el anio, porque en la pagina se
    sobreentiende. Para un torneo dentro de un mismo anio alcanza con ponerselo;
    para los que cruzan -- 2016-17, 2017-18, 2018-19, 2019-20 -- hay que decidirlo
    por el mes, y equivocarse ahi no falla: fecha media temporada un anio entero
    para atras, el partido queda antes de que el torneo empezara, y cualquiera
    que despues filtre por fecha lo lee donde no corresponde.

    SALVO QUE LA CELDA LO DIGA. Cuando la pagina escribe el anio, gana ella y no
    se deduce nada: es un dato de la fuente contra una regla nuestra. Y no es
    raro ni decorativo -- lo escribe justo cuando la regla se equivocaria, que es
    el partido postergado fuera de su temporada. "23 de abril de 2008{{refn|
    Postergado por la participacion de Arsenal en la final de la Copa
    Sudamericana}}" es del Apertura 2007, y por el mes caia en abril de 2007,
    cuando el torneo todavia no existia. Son 39 partidos en seis paginas, 34 de
    ellos de la Copa Argentina 2019-20, que la pandemia estiro hasta 2021.
    """
    m = re.search(r"(\d{1,2})\s*de\s+([a-záéíóúñ]+)(?:\s*de\s+(\d{4}))?", texto, re.I)
    if not m:
        return ""
    mes_txt = unicodedata.normalize("NFKD", m.group(2).lower()).encode("ascii", "ignore").decode()
    mes = MESES.get(mes_txt)
    if not mes:
        return ""
    y = int(m.group(3)) if m.group(3) else (anio if (anio_fin is None or mes >= mes_inicio) else anio_fin)
    return f"{y}-{mes:02d}-{int(m.group(1)):02d}"


_PLANTILLA_FECHA = re.compile(r"\{\{\s*fecha\s*\|\s*(\d{1,2})\s*\|\s*(\d{1,2})\s*\|\s*(\d{4})\s*\}\}",
                              re.I)


def _fecha_de_plantilla(crudo: str) -> str:
    """`{{fecha|17|1|2021}}` -> '2021-01-17'. Vacio si no es esa forma.

    Hay que leerla ANTES de limpiar, porque limpiar borra las plantillas y deja
    la celda en ', 22:10 (UTC-3)' -- un partido sin fecha.

    Ademas trae el anio EXPLICITO, que acá no es un lujo: la final de la Copa de
    la Liga 2020 se jugo el 17 de enero de 2021. Cualquier anio deducido del
    torneo la habria puesto un anio antes.
    """
    m = _PLANTILLA_FECHA.search(crudo)
    if not m:
        return ""
    dia, mes, anio = (int(g) for g in m.groups())
    return f"{anio}-{mes:02d}-{dia:02d}" if 1 <= mes <= 12 and 1 <= dia <= 31 else ""


# `PP` es "partido perdido": la sigla con que Wikipedia escribe un resultado que
# no salio de la cancha sino de un tribunal.
_ANULADO = re.compile(r"(?i)^\s*PP\s*-\s*PP\s*$")


# El idioma con que la fuente habla de un partido que no salio normal. Es ANCHO
# a proposito: sirve para preguntar "¿aca paso algo?", no para decidir que paso.
_HABLA_DE_FALLO = re.compile(
    r"(?i)suspendid|abandon|no se present|tribunal|se le dio por|dio por (ganado|perdido|"
    r"terminado|finalizado)|d[aá]ndolo por|otorg[aá]ndole|inclusi[oó]n indebida|mala inclusi[oó]n")
# No llego al final. Es lo unico que la fuente dice SIEMPRE y sin ambiguedad.
_NO_LLEGO_AL_FINAL = re.compile(r"(?i)suspendid|abandon[oó]|no se present[oó]|interrumpi")
# Llego al final y despues un fallo cambio el numero.
# Un fallo que cambio el numero. Se pregunta DESPUES de descartar que el partido
# no haya llegado al final, y ese orden es la regla entera: si hubo suspension,
# manda la suspension; si el partido termino y aun asi hubo fallo, es escritorio.
_HUBO_FALLO = re.compile(
    r"(?i)se le dio por (ganado|perdido)|se lo dio (por )?ganado|le dio por ganado"
    r"|otorg[aá]ndole|le gan[oó] los puntos|(mala|indebida) inclusi[oó]n|inclusi[oó]n indebida")
# El partido se suspendio y DESPUES se jugo o se completo: llego al final igual,
# aunque en dos dias. Son 356 de las 409 filas que mencionan una suspension, y
# meterlas en "suspendido" seria decir que su marcador no es de la cancha.
_SE_COMPLETO = re.compile(
    r"(?i)se\s+(?:jug[oó]|jugaron|jugar[aá]n?|disput[oó]|disputaron|complet[oó]|"
    r"reanud[oó]|finaliz[oó])\s+(?:el\s+)?\d{1,2}\s*de\s+[a-záéíóúñ]+")


def status_de_la_fila(fila: str) -> str:
    """De donde salio el marcador de esta fila: "", "suspendido" o "escritorio".

    LO QUE NO HACE, y es la decision de diseño entera: NO trata de leer si el
    tribunal RATIFICO el marcador de la cancha o lo CAMBIO. Se probo y la fuente
    no lo dice de forma decidible -- la misma formula sostiene los dos casos y
    tambien el tercero:

      * "Se dio por finalizado" ratificando: Federal A 2025, "Suspendido a los
        39' [...] con el resultado 1 a 1. Se dio por finalizado."
      * "Se dio por finalizado" CAMBIANDO, y ademas distinto para cada club:
        Primera B 2017-18, "Se dio por finalizado, dandolo por perdido a
        Deportivo Español y empatado a Sacachispas."
      * "darlo por terminado" cambiando el numero: B Nacional 2008-09, "decidio
        darlo por terminado con resultado 4-0" sobre una cancha que iba 4-1.

    Cuando 53 casos se clasificaron a mano con la pagina entera a la vista y sin
    apuro, dos de las tres correcciones que hizo la verificacion cruzaron
    justamente esa frontera. Un parser que corre todos los dias a las 10:00 la
    decidiria por keyword, y una columna cuyo valor significa cosas distintas es
    peor que no tener la columna.

    Asi que el eje es otro, y es el unico que la fuente marca sin ambiguedad:
    ¿el partido LLEGO AL FINAL? Eso lo dice o no lo dice, y no hay que juzgar al
    tribunal para saberlo.

      ""            La fila no trae ninguna nota que diga otra cosa. NO certifica
                    que se hayan jugado los 90: dice que nadie dijo lo contrario.
      "suspendido"  La fuente dice que no llego al final. El marcador publicado
                    puede ser el de la cancha o uno de escritorio; la fila no
                    dice cual, porque la fuente no lo distingue.
      "escritorio"  El partido SI termino y el numero publicado no es el de la
                    cancha: lo puso un fallo. Es el caso que ninguna busqueda por
                    "suspension" encuentra -- Atlanta-Colegiales de la Primera B
                    2017-18 dice "Finalizado 0 a 0, se le dio por ganado a
                    Atlanta por 1 a 0" y se jugaron los noventa minutos.
    """
    if _SE_COMPLETO.search(fila):
        return ""                      # se suspendio y se termino de jugar
    if _NO_LLEGO_AL_FINAL.search(fila):
        return "suspendido"            # no llego al final: manda eso
    if _HUBO_FALLO.search(fila):
        return "escritorio"            # llego al final y el numero es de oficina
    return ""


def sin_clasificar(fila: str) -> bool:
    """La fila habla de un fallo y `status_de_la_fila` no supo que decir.

    Vacio quiere decir "la pagina no dijo nada". NUNCA puede querer decir "dijo
    algo que no supe leer": esa es la unica forma de que el default no se vuelva
    una afirmacion inventada sobre 39 mil filas. Cuando pasa, se avisa.
    """
    if _SE_COMPLETO.search(fila):
        return False           # se suspendio y se termino de jugar: eso SI se leyo
    return bool(_HABLA_DE_FALLO.search(fila)) and not status_de_la_fila(fila)


def fallos_sin_leer(texto: str) -> list[str]:
    """Las filas que hablan de un fallo y a las que no se les supo poner status.

    Es la guarda que sostiene el default. `status` vacio quiere decir "la pagina
    no dijo nada"; si alguna vez pasara a querer decir tambien "dijo algo que no
    supe leer", las 39 mil filas vacias dejarian de ser una ausencia y pasarian a
    ser una afirmacion sin verificar. Hoy son cero, y este aviso existe para que
    se note el dia que Wikipedia escriba el veredicto de otra forma.
    """
    fuera = []
    for bloque in re.finditer(r"\{\|.*?\n\|\}", texto, re.S):
        for fila in re.split(r"\n\|-", bloque.group(0)):
            celdas = [_celda(c)[1] for c in _partir(fila)]
            if len(celdas) < 3 or not _marcador(celdas[1]) or not sin_clasificar(fila):
                continue
            fuera.append(
                f"{celdas[0]} vs {celdas[2]} ({celdas[1]}): la pagina dice algo sobre "
                f"un fallo y no se supo si el partido llego al final. Queda con "
                f"status vacio, que significa \"la pagina no dijo nada\" -- y aca si "
                f"dijo. Mira la nota y ajusta `parser.status_de_la_fila`")
    return list(dict.fromkeys(fuera))


def partidos_anulados(texto: str) -> list[str]:
    """Los partidos que la pagina tiene y que el esquema no puede escribir.

    `PP - PP` quiere decir que el tribunal se lo dio por perdido a LOS DOS. No es
    un marcador y no hay par de numeros que lo diga: una fila tiene un
    `home_score` y un `away_score`, y cualquier cosa que se ponga ahi afirma que
    alguien gano. El parser descarta la fila, que es lo correcto, y hasta ahora lo
    hacia sin decirlo.

    Que no se pueda escribir no quiere decir que no se pueda AVISAR, y la
    diferencia importa: sin este aviso el hueco aparece como un partido que falta
    -- el chequeo de PJ lo denuncia, porque la tabla si lo cuenta -- y manda a
    buscar un error de lectura que no existe. Vacio no es lo mismo que ilegible,
    otra vez.

    Son dos en las 131 paginas. El del Federal A 2018-19 es el mas raro que tiene
    el repo: Independiente (N) - Deportivo Roca termino 4 a 1 y el Tribunal se lo
    dio por perdido a los dos, por incluir a un jugador de manera indebida para
    asegurar un resultado que le convenia al rival. La tabla de esa Revalida le
    pone 0-1 en contra a CADA UNO, y por eso es la unica tabla del corpus que no
    cierra por un motivo legitimo: le sobran dos goles en contra que nadie
    convirtio.
    """
    fuera = []
    for bloque in re.finditer(r"\{\|.*?\n\|\}", texto, re.S):
        for fila in re.split(r"\n\|-", bloque.group(0)):
            celdas = [_celda(c)[1] for c in _partir(fila)]
            # La columna del resultado NO esta siempre en el mismo lugar: la liga
            # ordena Local-Resultado-Visitante y la copa
            # Fecha-Estadio-Equipo 1-Partido-Equipo 2. Se busca la celda anulada
            # donde caiga y los clubes se toman de sus dos vecinas, que es lo que
            # los dos formatos si tienen en comun.
            i = next((k for k, c in enumerate(celdas) if _ANULADO.match(c)), None)
            if i is None or not 0 < i < len(celdas) - 1:
                continue
            fuera.append(
                f"{celdas[i - 1]} vs {celdas[i + 1]}: la pagina lo publica como "
                f"\"{celdas[i].strip()}\" -- partido perdido para los dos --, y eso "
                f"no es un marcador. La fila queda afuera del dataset a proposito: "
                f"con un solo par de goles no se puede decir que perdieron los dos")
    return list(dict.fromkeys(fuera))


def _marcador(texto: str) -> tuple[int, int] | None:
    m = re.match(r"^\s*(\d+)\s*[-:]\s*(\d+)", texto)
    return (int(m.group(1)), int(m.group(2))) if m else None


# --------------------------------------------------------------------------
# fase de grupos: la wikitable con rowspan
# --------------------------------------------------------------------------
def _cortar_en_tablas(bloque: str) -> str:
    """Convierte el cierre y la apertura de tabla en separadores de fila.

    Cada jornada es su propia `wikitable`, y entre el cierre de una y la apertura
    de la siguiente NO hay `|-`:

        |22 de enero
        |17:00
        |}
        {|class="wikitable ..."
        !colspan=6|Fecha 2

    Partiendo solo por `\\n|-`, esa ultima fila y el encabezado de la jornada
    siguiente caen en el mismo pedazo. Como los encabezados se leen antes que las
    celdas, la fila terminaba anotada en la fecha que venia: los 30 interzonales
    (siempre el ultimo bloque de su jornada) quedaron corridos una fecha. No
    rompia nada, solo mentia. Lo mira `validar.una_vez_por_jornada`.
    """
    bloque = re.sub(r"\n\|\}", "\n|-", bloque)          # cierre  |}
    return re.sub(r"\n\{\|[^\n]*", "\n|-", bloque)      # apertura {|class=...


# Un encabezado `colspan` que nombra una RONDA no es una zona. La tabla de
# resultados y la de una llave se escriben igual, y el encabezado es lo unico que
# las distingue: `!colspan=12|Fecha 7` contra `!colspan=12|Desempate`.
#
# Tratando la ronda como zona pasan dos cosas malas a la vez. La etiqueta va a
# parar a la columna `group` del CSV, que promete una zona y termina diciendo
# "Octavos de final"; y el partido queda como fase de grupos, que es lo que hizo
# saltar `todos_tienen_zona` en la Primera B 2017-18 -- 306 partidos sin zona y
# uno, el desempate que definio el campeonato, con "Desempate".
#
# La lista es corta y explicita a proposito. "Primera fase" y "Nonagonal final"
# NO estan: en el Federal A son fases de grupos, no llaves, y meterlas aca las
# sacaria de la fase de zonas que es donde van.
_ES_RONDA = re.compile(
    r"(?i)^(desempate|ronda de desempate|reducido"
    r"|(octavos|cuartos|dieciseisavos|treintaidosavos)( de final)?"
    r"|semifinal(es)?|final\b|primera ronda|segunda ronda|tercera ronda"
    r"|partidos? de (ida|vuelta|desempate)|promoci[oó]n)")


def _zonas_ambiguas(texto: str) -> frozenset[str]:
    """Rotulos de zona que la pagina reusa en MAS DE UNA fase.

    Un torneo multifase puede llamar "Zona 1" a dos cosas distintas: la Zona 1 de
    la Primera fase y la Zona 1 de la Revalida, con otros equipos. El rotulo sale
    de un encabezado de la tabla y la tabla no sabe de que seccion cuelga, asi que
    los partidos de las dos caian en el mismo balde -- el Argentino A 2010-11
    quedaba con 132 partidos en su Zona 1 cuando son 112 mas 20, y ninguna cuenta
    por zona se podia hacer.

    Se calcula sobre la pagina entera y no se supone: son 3 paginas de las 279,
    y NINGUNA del catalogo. Por eso la calificacion es condicional -- ponerle la
    fase a toda zona cambiaria el `group` de las 38109 filas para arreglar tres
    paginas que ni siquiera estan.
    """
    n2 = [(m.start(), m.group(2).strip())
          for m in re.finditer(r"^(==+)([^=\n]+)\1", texto, re.M) if len(m.group(1)) == 2]
    donde: dict[str, set] = {}
    for m in re.finditer(r"^!\s*colspan\s*=\s*\"?\d+\"?[^|\n]*\|\s*(.+)$", texto, re.M):
        cab = limpiar(m.group(1))
        # Las mismas dos guardas, y en el mismo orden, que la rama de abajo: una
        # jornada o una ronda no son zonas y no cuentan para la ambiguedad.
        if (not cab or cab.lower() in _COLUMNAS_CONOCIDAS
                or re.match(r"(?i)fecha\s*\d+", cab) or _ES_RONDA.match(cab)):
            continue
        z = _como_zona(cab)
        if not z:
            continue
        previas = [t for p, t in n2 if p < m.start()]
        donde.setdefault(z, set()).add(previas[-1] if previas else "")
    return frozenset(z for z, s in donde.items() if len(s) > 1)


def partidos_de_tabla(bloque: str, anio: int, torneo: str, anio_fin: int | None = None,
                      mes_inicio: int = MES_INICIO_HABITUAL,
                      zona_defecto: str = "", llave: str = "",
                      arts: dict[str, str] | None = None,
                      fuera_de_la_liga: bool = False,
                      ambiguas: frozenset[str] = frozenset()) -> list[Partido]:
    """`fuera_de_la_liga` marca las tablas que NO cuelgan de un "Resultados".

    Ahi no hay fechas del calendario: son reducidos, promociones, finales y
    desempates. Sus encabezados dicen "Partido 1", "Cuarta ronda", "Tercer
    ascenso" -- etiquetas que no son zonas y que crecen sin fin, asi que en vez
    de irlas agregando a una lista se decide por el lugar: si la tabla esta
    afuera de la seccion de resultados, su encabezado es una ronda y el partido
    es de eliminacion.
    """
    partidos: list[Partido] = []
    pendientes: dict[str, list] = {}        # columna -> [valor, filas restantes]
    # La zona puede venir de un encabezado de tabla (`!colspan=6|Zona A`) o del
    # titulo de la seccion que contiene a esta tabla, que es como lo hace el
    # ascenso. Si aparece un encabezado, pisa al de la seccion.
    jornada, zona, ronda = "", zona_defecto, ""
    sin_local = False       # hasta que un encabezado diga "Equipo 1"
    if fuera_de_la_liga:
        # Sin encabezado propio, la ronda es el titulo de la seccion. Se prefiere
        # el mas cercano (`zona_defecto`, que es el padre inmediato) sobre la fase
        # que lo contiene: bajo `== Etapa eliminatoria ==` lo que identifica al
        # partido es "Primera fase", no "Etapa eliminatoria", que es la llave.
        ronda = jornada = zona_defecto or llave

    for fila in re.split(r"\n\|-", _cortar_en_tablas(bloque)):
        fila = fila.strip()
        if not fila:
            continue

        # Dentro de esta seccion todo encabezado `colspan` es o la jornada
        # ("Fecha 7") o la etiqueta de la seccion que sigue ("Zona A",
        # "Interzonal"). Los nombres de columna no llevan colspan, asi que no
        # entran. Se toma cualquier etiqueta y no una lista cerrada: la primera
        # version solo conocia "Zona|Grupo", los bloques "Interzonal" caian al
        # vacio y heredaban en silencio la zona anterior -- 30 partidos quedaron
        # marcados como Zona B. Lo agarro `validar.zonas_completas`.
        # `[^|\n]*` entre el colspan y la barra: el encabezado puede traer mas
        # atributos, y muchas paginas del ascenso escriben
        # `!colspan=3 align=center|Fecha 1`. Exigiendo la barra pegada al numero,
        # esas jornadas no se leian -- los 380 partidos de una temporada quedaban
        # todos sin `matchday`, sin que nada fallara.
        for cab in re.findall(r"!\s*colspan\s*=\s*\"?\d+\"?[^|\n]*\|\s*(.+)", fila):
            cab = limpiar(cab)
            if not cab:
                continue
            # Un encabezado cuyo texto es el nombre de una COLUMNA no es una
            # seccion: `!colspan=2 ...|Partido` encabeza la columna del marcador.
            # Antes no molestaba porque el regex no los veia; al aflojarlo para
            # leer `!colspan=3 align=center|Fecha 1`, uno de estos se colaba como
            # zona y dejaba una temporada con 1 partido con zona y 300 sin.
            if cab.lower() in _COLUMNAS_CONOCIDAS:
                continue
            pendientes.clear()      # un rowspan no cruza de una seccion a otra
            if re.match(r"(?i)fecha\s*\d+", cab) and not fuera_de_la_liga:
                jornada, ronda = cab, ""
            elif fuera_de_la_liga or _ES_RONDA.match(cab):
                jornada, ronda = cab, cab
            else:
                z = _seccion(cab)
                # Si la pagina usa ese mismo rotulo en otra fase, no alcanza con
                # el rotulo: hay que decir de cual. La fase ya viene hasta aca
                # como `llave`.
                zona = f"{llave} - {z}" if z and llave and z in ambiguas else z
                ronda = ""
        if fila.lstrip().startswith("!"):
            # El encabezado tambien dice si hay local. Se mira aca, en el bucle, y
            # no una vez por bloque, porque un bloque puede traer varias tablas:
            # la de la fecha 38 con "Local" y abajo la del desempate con
            # "Equipo 1". Vale hasta que otra tabla diga otra cosa.
            if _ENCABEZADO_SIN_LOCAL.search(fila):
                sin_local = True
            elif _ENCABEZADO_CON_LOCAL.search(fila):
                sin_local = False
            continue                                   # fila de encabezado

        # Un titulo de Wikipedia cierra la jornada. Dentro de la seccion de
        # resultados puede aparecer `=== Partido de desempate del primer puesto ===`
        # -- la final del campeonato, cuando dos equipos terminan igualados -- y
        # ese partido NO es de la ultima fecha: es otra cosa. Sin cortar, se
        # quedaba con la jornada de la tabla anterior y dejaba a la Fecha 25 con
        # 13 partidos y dos equipos jugando dos veces, que es imposible.
        if (titulo := _TITULO_CUALQUIERA.search(fila)):
            jornada = ""
            pendientes.clear()
            # Y si ese titulo ademas NOMBRA una ronda, lo que sigue no es fase
            # regular: es una llave. Un titulo de Wikipedia dentro del cuerpo es
            # una etiqueta de seccion igual que un `!colspan|...`, asi que se lee
            # igual. Cortar la jornada y no mirar el nombre dejaba al desempate
            # del titulo de la B Nacional 2017-18 como fase de zonas: un partido
            # de mas para Aldosivi y Almagro, que la tabla no les contaba.
            nombre = limpiar(titulo.group(0).strip("=" + chr(32) + chr(10)))
            if _ES_RONDA.match(nombre):
                jornada = ronda = nombre

        celdas = _partir(fila)
        if len(celdas) < 3:
            continue


        valores, i = {}, 0
        for col in COLUMNAS:
            if pendientes.get(col, [None, 0])[1] > 0:
                valores[col] = pendientes[col][0]
                pendientes[col][1] -= 1
                continue
            if i >= len(celdas):
                valores[col] = ""
                continue
            filas, contenido = _celda(celdas[i]); i += 1
            valores[col] = contenido
            if filas > 1:
                pendientes[col] = [contenido, filas - 1]

        goles = _marcador(valores["resultado"])
        if not goles or not valores["local"] or not valores["visita"]:
            continue
        programada = a_iso(valores["fecha"], anio, anio_fin, mes_inicio)
        partidos.append(Partido(
            status=status_de_la_fila(fila),
            fecha=(_fecha_de_la_nota(fila, anio, anio_fin, mes_inicio, programada)
                   or programada),
            hora=valores["hora"],
            local=valores["local"], visita=valores["visita"],
            goles_local=goles[0], goles_visita=goles[1],
            torneo=torneo, fase="eliminacion" if ronda else "zonas",
            zona="" if ronda else zona, jornada=jornada, llave=llave,
            local_art=(arts or {}).get(valores["local"], ""),
            visita_art=(arts or {}).get(valores["visita"], ""),
            estadio=valores["estadio"], fecha_cruda=valores["fecha"],
            # Solo se MARCA neutral, nunca se desmarca. Un torneo declarado
            # neutral entero -- la Copa Argentina -- sigue siendolo aunque alguna
            # de sus tablas rotule "Local", que es una etiqueta de la columna y no
            # una afirmacion sobre la cancha.
            neutral=True if sin_local else None))
    return partidos


# --------------------------------------------------------------------------
# eliminacion: plantillas {{Partido}}
# --------------------------------------------------------------------------
# El arranque de una `{{Partido}}`. `Partidos?` en plural TAMBIEN, porque
# `Plantilla:Partidos` es literalmente `#REDIRECCION [[Plantilla:Partido]]`:
# misma plantilla, mismos parametros, se renderiza igual. Pidiendo el singular
# la `s` no matchea -- no es whitespace -- y la plantilla no se ve. Eran 27
# paginas del catalogo y 284 partidos de eliminacion que se caian en silencio,
# la mayoria de ellas con la fase eliminatoria ENTERA afuera.
_ARRANQUE_PARTIDO = re.compile(r"\{\{\s*Partidos?\s*\n", re.I)


def _plantillas_partido(texto: str):
    r"""(posicion, cuerpo) de cada `{{Partido}}`, cerrando por balance de llaves.

    El cierre NO se puede buscar con un regex. Pidiendo `\n\s*\}\}` se exige
    que el `}}` este solo en su renglon, y la forma mas comun en es.wikipedia es
    cerrarla pegada al ultimo parametro (`|árbitro=[[Fulano]]}}`). Cuando cierra
    asi, el `.*?` no para donde termina la plantilla: sigue hasta el proximo `}}`
    que si este solo, y se COME las plantillas del medio.

    Y no se rompe: como los campos van a un diccionario, el ultimo `local` pisa
    al primero. En la Primera B 2021 las tres plantillas de la fase eliminatoria
    colapsaban en una sola, que salia con los equipos y el marcador de la final
    (Talleres 2-4 Comunicaciones), los penales de la semifinal (4-2, porque ese
    parametro estaba solo en la primera) y el rotulo de ronda de la primera.
    Un partido que nunca existio, con todos los campos llenos.

    Contar llaves ademas es lo unico que sirve con las anidadas: el cuerpo trae
    `{{sin negrita|(0:0)}}` y `{{gol|43}}`, asi que frenar en el primer `}}`
    dejaria el partido sin visitante.
    """
    for m in _ARRANQUE_PARTIDO.finditer(texto):
        i, hondo = m.end(), 1
        while i < len(texto) and hondo:
            if texto.startswith("{{", i):
                hondo, i = hondo + 1, i + 2
            elif texto.startswith("}}", i):
                hondo, i = hondo - 1, i + 2
            else:
                i += 1
        # Una plantilla que no cierra se descarta. Adivinar donde termina es
        # exactamente lo que hacia el regex, y es de donde salio el problema.
        if hondo == 0:
            yield m.start(), texto[m.end():i - 2]


def partidos_de_plantillas(texto: str, anio: int, torneo: str, anio_fin: int | None = None,
                           mes_inicio: int = MES_INICIO_HABITUAL,
                       arts: dict[str, str] | None = None) -> list[Partido]:
    titulos = _titulos_de_ronda(texto)
    arts = arts or articulos_de_la_pagina(texto)
    partidos: list[Partido] = []
    # Una pagina puede traer VARIOS cuadros: la final del campeonato, el torneo
    # reducido y la definicion de un ascenso son tres eliminaciones distintas que
    # no se encadenan entre si. Cual es cual lo dice la seccion de nivel 2.
    for pos, cuerpo in _plantillas_partido(texto):
        campos = {}
        for linea in cuerpo.split("\n|"):
            if "=" not in linea:
                continue
            k, v = linea.split("=", 1)
            campos[k.strip().lstrip("|").lower()] = v.strip()

        goles = _marcador(limpiar(campos.get("resultado", "")))
        if not goles:
            continue
        # OJO: los penales NO salen de los parentesis de `resultado` (eso es el
        # entretiempo). Ver el docstring del modulo.
        pen = _marcador(limpiar(campos.get("resultado penalti", "")))
        partidos.append(Partido(
            fecha=(_fecha_de_plantilla(campos.get("fecha", ""))
                   or a_iso(limpiar(campos.get("fecha", "")), anio, anio_fin, mes_inicio)),
            local=limpiar(campos.get("local", "")),
            visita=limpiar(campos.get("visita", "")),
            goles_local=goles[0], goles_visita=goles[1],
            penales_local=pen[0] if pen else None,
            penales_visita=pen[1] if pen else None,
            torneo=torneo, fase="eliminacion",
            jornada=_ronda_en(pos, titulos, _inicio_de_llave(pos, texto)),
            local_art=arts.get(limpiar(campos.get("local", "")), ""),
            visita_art=arts.get(limpiar(campos.get("visita", "")), ""),
            llave=_contexto(pos, 3, texto),
            estadio=limpiar(campos.get("estadio", "")),
            fecha_cruda=limpiar(campos.get("fecha", ""))))
    return partidos


# --------------------------------------------------------------------------
# copa: una tabla por ronda
# --------------------------------------------------------------------------
# En orden. Sirve para encontrar las secciones y para saber cual va despues de
# cual, que en la Copa no se puede deducir de las fechas: las rondas se solapan
# (los treintaidosavos 2026 se jugaron entre enero y abril, y los dieciseisavos
# entre abril y julio, con dias compartidos).
# En orden, de la mas lejana a la final. El ascenso agrega las "fases" del
# torneo reducido, que van antes de las semis.
RONDAS = ("Primera fase", "Segunda fase", "Tercera fase",
          "Treintaidosavos", "Dieciseisavos", "Octavos", "Cuartos",
          "Semifinales", "Final")

# "Semifinal" y "Semifinales" son la misma ronda escrita de dos maneras; si
# quedan como dos, el orden de las rondas se parte en dos mitades.
_TITULO_RONDA = re.compile(
    r"^=+\s*(Primera fase|Segunda fase|Tercera fase|Treintaidosavos|Dieciseisavos"
    r"|Octavos|Cuartos|Semifinales|Semifinal|Final)[^=\n]*=+\s*$", re.M | re.I)

_COL_COPA = ["fecha", "estadio", "local", "resultado", "visita"]


def _titulos_de_ronda(texto: str) -> list[tuple[int, str]]:
    """(posicion, ronda) de cada titulo de ronda de la pagina."""
    return [(m.start(), _nombre_de_ronda(m.group(1))) for m in _TITULO_RONDA.finditer(texto)]


def _nombre_de_ronda(crudo: str) -> str:
    n = crudo.capitalize()
    return "Semifinales" if n == "Semifinal" else n


def _inicio_de_llave(pos: int, texto: str) -> int:
    """Donde empieza la seccion de nivel 2 que contiene a `pos`."""
    inicio = 0
    for m in _TITULO.finditer(texto[:pos]):
        if len(m.group(1)) <= 2:
            inicio = m.start()
    return inicio


def _ronda_en(pos: int, titulos: list[tuple[int, str]], desde: int = 0) -> str:
    """La ronda a la que pertenece lo que esta en `pos`: la del ultimo titulo
    que quedo atras.

    Las llaves de liga vienen como plantillas `{{Partido}}` que no dicen a que
    ronda pertenecen; lo unico que lo dice es bajo que titulo estan.

    `desde` acota la busqueda al cuadro actual, y hace falta: una pagina del
    ascenso tiene una seccion `== Final ==` (la del campeonato) y despues un
    `== Torneo reducido ==` con sus propias fases. Sin acotar, los partidos de la
    "Primera fase" del reducido se quedaban con el "Final" arrastrado de la
    seccion anterior, y el chequeo del cuadro encadenaba semifinales con finales
    que no tenian nada que ver: 21 avisos sobre datos correctos.
    """
    ronda = ""
    for donde, nombre in titulos:
        if donde > pos:
            break
        if donde >= desde:          # solo las rondas de ESTE cuadro
            ronda = nombre
    return ronda

# Los penales de la Copa: `{{small|(5)}} 1 - 1 {{small|(4)}}`, o con la etiqueta
# HTML `<small>(5)</small>`. OJO que esto es lo OPUESTO a lo que significa un
# parentesis en una plantilla {{Partido}}, donde `1:1 (0:0)` es el entretiempo.
# Se distinguen por lo que hay adentro: un solo numero es la tanda de ese equipo,
# dos numeros separados por `:` son los goles del primer tiempo.
_PENAL = re.compile(r"(?:\{\{\s*small\s*\||<small>)\s*\((\d+)\)", re.I)


def _penales(celda_cruda: str) -> tuple[int, int] | None:
    """Los penales de una celda de marcador, ANTES de limpiarla.

    Tiene que correr sobre el texto crudo: `limpiar` borra las plantillas, y la
    tanda vive adentro de una. Limpiando primero, `{{small|(5)}} 1 - 1
    {{small|(4)}}` queda en `1 - 1` y la definicion desaparece sin que nada falle.
    """
    n = _PENAL.findall(celda_cruda)
    return (int(n[0]), int(n[1])) if len(n) == 2 else None


def partidos_de_rondas(texto: str, anio: int, torneo: str, anio_fin: int | None = None,
                       mes_inicio: int = MES_INICIO_HABITUAL,
                       arts: dict[str, str] | None = None) -> list[Partido]:
    """La Copa Argentina: una tabla por ronda, `Fecha | Estadio | Eq1 | Partido | Eq2`."""
    partidos: list[Partido] = []
    for m in _TITULO_RONDA.finditer(texto):
        # La seccion termina en el proximo titulo, sea del nivel que sea, y no en
        # la proxima ronda: la ultima ronda jugada es la ultima seccion de ronda
        # de la pagina, pero abajo siguen "Goleadores", "Referencias" y sus
        # tablas, que sin este corte entran como si fueran partidos.
        # Corta en el proximo titulo del MISMO nivel o mas alto, no en cualquiera.
        # Las ediciones viejas de la Copa parten cada ronda en subsecciones, y
        # cortando en el primer subtitulo se leia solo la primera tabla: la
        # 2011-12 daba UN partido de sesenta. Los subtitulos entran en la ronda;
        # la ronda siguiente, no.
        nivel = len(re.match(r"=+", m.group(0)).group(0))
        sig = re.search(rf"^={{1,{nivel}}}[^=]", texto[m.end():], re.M)
        fin = m.end() + (sig.start() if sig else len(texto) - m.end())
        ronda = _nombre_de_ronda(m.group(1))
        for fila in re.split(r"\n\|-", texto[m.end():fin]):
            if not fila.strip() or fila.lstrip().startswith("!"):
                continue
            celdas = _partir(fila)
            if len(celdas) < len(_COL_COPA):
                continue
            v = dict(zip(_COL_COPA, (_celda(c)[1] for c in celdas)))
            goles = _marcador(v["resultado"])
            if not goles or not v["local"] or not v["visita"]:
                continue          # ronda en curso: la fila esta pero sin marcador
            pen = _penales(celdas[_COL_COPA.index("resultado")])
            partidos.append(Partido(
                fecha=a_iso(v["fecha"], anio, anio_fin, mes_inicio), local=v["local"], visita=v["visita"],
                goles_local=goles[0], goles_visita=goles[1],
                penales_local=pen[0] if pen else None,
                penales_visita=pen[1] if pen else None,
                torneo=torneo, fase="eliminacion", jornada=ronda,
                local_art=(arts or {}).get(v["local"], ""),
                visita_art=(arts or {}).get(v["visita"], ""),
                estadio=v["estadio"], fecha_cruda=v["fecha"]))
    return partidos


# --------------------------------------------------------------------------
def secciones_de_resultados(texto: str) -> list[tuple[str, str, str]]:
    """(zona, fase, cuerpo) de CADA seccion "Resultados" de la pagina.

    Son varias, no una, y cada una pertenece a algo distinto:

      * en el ascenso, `== Zona A ==` y `== Zona B ==` son secciones de primer
        nivel y cada una trae su propio `=== Resultados ===`;
      * en Primera B y C, lo que hay arriba es `== Torneo Apertura ==` y
        `== Torneo Clausura ==`, o sea DOS torneos en una pagina, cada uno con su
        Fecha 1.

    Buscando una sola seccion se leia la mitad: la Primera Nacional 2025 daba 26
    equipos donde hay 38. Y sin el contexto, las dos "Fecha 1" de Primera B se
    mezclaban en una y todos los equipos parecian jugar dos veces por fecha.

    El corte va hasta el proximo titulo del MISMO nivel o mas alto, asi que una
    seccion con subsecciones entra entera pero no se come a su hermana.
    """
    return [(_como_zona(z), f, c) for _, _, z, f, c in _secciones_con_span(texto)]


def _secciones_con_span(texto: str):
    """Lo mismo que `secciones_de_resultados` pero diciendo tambien DONDE cae cada
    seccion. El span lo necesita `partidos()` para no volver a leer lo mismo."""
    fuera, hasta = [], 0
    for m in _TITULO_RESULTADOS.finditer(texto):
        # Una seccion "Resultados" ADENTRO de otra ya vino en el cuerpo de la de
        # afuera. Tomandola igual, cada partido entra dos veces y todos los
        # equipos parecen jugar dos veces por fecha. Se saltea la de adentro.
        if m.start() < hasta:
            continue
        nivel = len(m.group(1))
        resto = texto[m.end():]
        sig = re.search(rf"^={{1,{nivel}}}[^=]", resto, re.M)
        cuerpo = resto[:sig.start()] if sig else resto
        hasta = m.end() + len(cuerpo)
        # Dos contextos, y hacen falta los dos. El PADRE inmediato es la zona
        # ("Grupo A"); la seccion de nivel 2 es la fase del torneo ("Fase
        # Campeonato"). La Copa de la Liga 2020 tuvo Fase Clasificatoria, Campeonato
        # y Complementacion, y CADA UNA con su Grupo A y su Fecha 1: quedandose solo
        # con el padre, los mismos equipos aparecian jugando dos veces la misma fecha.
        # `min(nivel, 3)`: la fase nunca se busca en un nivel igual o mayor al
        # del propio titulo "Resultados". Cuando este es de nivel 2 -- como en
        # los torneos de 2004-2015 -- pedir nivel 3 devolvia la seccion de nivel 2
        # ANTERIOR, que no lo contiene: los 190 partidos del Inicial 2012
        # quedaban bajo una fase llamada "Tabla de posiciones final".
        fuera.append((m.start(), hasta,
                      _contexto(m.start(), nivel, texto),
                      _contexto(m.start(), min(nivel, 3), texto), cuerpo))
    return fuera


# Una fase que se llama "Etapa eliminatoria" no tiene zonas adentro: tiene
# rondas. Sirve donde la lista de nombres no alcanza, porque el MISMO rotulo
# significa cosas distintas en paginas distintas: "Primera fase" es una fase de
# grupos en el Federal A 2017 -- con sus Fecha 1, Fecha 2 -- y una llave en el
# Transicion 2020, donde es hermana de "Semifinales" y "Final" bajo
# `== Etapa eliminatoria ==`. El nombre no distingue; el lugar si.
_LLAVE_ELIMINATORIA = re.compile(r"(?i)eliminatori")


def _rotula_fechas(tabla: str) -> bool:
    """La tabla numera sus bloques como "Fecha N", o sea que es una fase regular.

    Un reducido rotula "Semifinales", "Final", "Ida"; una fase de liga rotula
    fechas del calendario. Se mira el encabezado con `colspan`, que es el que
    separa bloques dentro de la tabla, y no cualquier celda: "Fecha" tambien es
    el nombre de una COLUMNA -- la del dia -- y contarla haria pasar por fase
    regular a cualquier tabla que publique la fecha de sus partidos.
    """
    return any(re.match(r"(?i)fecha\s*\d+", limpiar(cab))
               for cab in re.findall(r"!\s*colspan\s*=\s*\"?\d+\"?[^|\n]*\|\s*(.+)", tabla))


def _como_zona(titulo: str) -> str:
    """El titulo de la seccion que contiene los resultados, si es una zona.

    No siempre lo es: un `=== Resultados ===` puede colgar de `== Final ==`, y
    entonces "Final" termina en la columna `group`, que promete una zona. Cuando
    el titulo nombra una RONDA esta funcion lo vacia, y `partidos()` manda esa
    seccion por el camino de las llaves, que le pone la ronda en la jornada y la
    marca como eliminacion. El dato no se pierde: se muda a la columna que le
    corresponde.

    QUE NO HACE, Y POR QUE. Tambien hay secciones tituladas `== Tabla de
    posiciones ==` con los resultados adentro, y su nombre queda igual como zona
    en 44 filas. Se probo vaciarlas y no alcanza: a diferencia de una ronda, ahi
    no hay ningun valor correcto con que reemplazarlo, asi que esos partidos
    quedan SIN zona, mezclados con los que si tienen, y `todos_tienen_zona` salta
    -- con razon -- en cuatro torneos. Cambiar una etiqueta equivocada por una
    faltante no es una mejora. Queda como problema conocido.
    """
    if _ES_RONDA.match(titulo) or re.match(r"(?i)^(tabla|posiciones|promedios)\b", titulo):
        return ""
    return titulo


_TITULO = re.compile(r"^(=+)\s*([^=\n]+?)\s*=+\s*$", re.M)


def _contexto(pos: int, nivel: int, texto: str) -> str:
    """El titulo de la seccion que CONTIENE a esta.

    Es el ultimo titulo de nivel MENOR que quedo atras. Que sea menor y no
    "cualquiera" importa: en las paginas de Primera de 2016 a 2024 el propio
    `== Resultados ==` es de nivel 2, y tomando el titulo anterior sin mirar el
    nivel, los 4400 partidos de esas temporadas quedaban agrupados bajo la
    seccion que estuviera arriba.
    """
    ctx = ""
    for m in _TITULO.finditer(texto[:pos]):
        if len(m.group(1)) < nivel:
            ctx = _seccion(limpiar(m.group(2)))
    return ctx


# Una tabla se declara a si misma. Estas tres columnas juntas no aparecen en una
# tabla de posiciones, ni en una de promedios, ni en una lista de goleadores.
_COLUMNAS_DE_PARTIDO = ({"local", "resultado", "visitante"},
                        {"local", "resultado", "visita"},
                        {"equipo 1", "resultado", "equipo 2"})

# Como la pagina dice que un partido NO tiene local: rotulando la columna
# "Equipo 1" en vez de "Local". No es una interpretacion nuestra -- es la unica
# forma que tiene una tabla de decir que los dos son visitantes, y la usa siempre
# para lo mismo: desempates, reducidos y definiciones, que se juegan en cancha de
# un tercero. Van 232 tablas en 51 paginas.
#
#   Desempate B Nacional 2014: Huracan 4-1 Atletico Tucuman en el Malvinas
#   Argentinas de Mendoza, que no es de ninguno de los dos.
_ENCABEZADO_SIN_LOCAL = re.compile(r"(?i)\bequipos?\s*1\b")
_ENCABEZADO_CON_LOCAL = re.compile(r"(?i)\blocal\b")

_ABRE_TABLA = re.compile(r"\{\|")


def _tablas(texto: str):
    """(posicion, cuerpo) de cada tabla de la pagina, cerrando por balance.

    Las tablas se anidan: las paginas del ascenso arman dos columnas de
    resultados con un `{| width=100%` que envuelve a las de cada fecha. Contando
    llaves, la de afuera sale entera; buscando el `|}` mas cercano, sale cortada
    en el primer cierre de una de adentro.

    QUE TANTO IMPORTA, MEDIDO. Cambia que tablas se reconocen en 10 paginas del
    catalogo (38 tablas), y NO cambia ni un partido: cada `{|` se escanea por su
    cuenta, asi que las de adentro se encuentran igual, y las repetidas las
    descarta el filtro de duplicados. O sea que el balance mantiene el cuerpo
    completo -- que es sobre lo que decide `_es_tabla_de_partidos` -- pero hoy
    ninguna pagina depende de eso para que un partido entre. Va escrito porque
    la primera version de este comentario decia que sin balance "se pierde la
    mitad de los partidos", y al medirlo resulto que no.
    """
    for m in _ABRE_TABLA.finditer(texto):
        i, hondo = m.end(), 1
        while i < len(texto) and hondo:
            if texto.startswith("{|", i):
                hondo, i = hondo + 1, i + 2
            elif texto.startswith("|}", i):
                hondo, i = hondo - 1, i + 2
            else:
                i += 1
        if hondo == 0:
            yield m.start(), texto[m.start():i]


def _es_tabla_de_partidos(tabla: str) -> bool:
    """Si el ENCABEZADO de la tabla declara las columnas de un partido.

    Es la guarda que hace seguro leer tablas fuera de la seccion "Resultados".

    MEDIDO, y no es lo que yo creia. Corriendo el parser sobre la pagina entera
    entran 117 filas nuevas; con la guarda, 108. Las 9 de diferencia NO son
    partidos inventados: son partidos reales con el nombre roto -- uno queda como
    `San Martín (F) {{Tabla de posiciones`, con el nombre comiendose el arranque
    de una plantilla -- o sin fecha, o sin canonizar. Un club asi entra al padron
    como desconocido y frena el build; nueve filas rotas alcanzan para justificar
    la guarda, sin necesidad de inventar que se inventan partidos.

    Lo otro que evita, y que no se cuenta en esas nueve, es el ARRASTRE de
    etiquetas: parseando la pagina como un solo bloque, la zona se hereda de una
    tabla a la siguiente, asi que un partido real de la definicion del descenso
    salia con zona "Amonestaciones" -- el ultimo encabezado que el parser habia
    visto, en la caja de goleadores. El partido existe; la etiqueta no.
    """
    columnas = set()
    for linea in re.findall(r"^!(.+)$", tabla, re.M):
        for celda in linea.split("!!"):
            columnas.add(_celda(celda.lstrip("!"))[1].lower())
    return any(pedidas <= columnas for pedidas in _COLUMNAS_DE_PARTIDO)


def partidos(texto: str, anio: int, torneo: str, formato: str = "liga",
             anio_fin: int | None = None,
             mes_inicio: int = MES_INICIO_HABITUAL) -> list[Partido]:
    """Todos los partidos de una pagina.

    `formato` lo dice el catalogo y no se adivina: una pagina de copa y una de
    liga se parecen lo suficiente como para que una deteccion automatica devuelva
    cero partidos en vez de fallar.
    """
    if formato == "copa":
        return partidos_de_rondas(texto, anio, torneo, anio_fin, mes_inicio,
                                  articulos_de_la_pagina(texto))
    arts = articulos_de_la_pagina(texto)
    # Se calcula UNA vez sobre la pagina entera: la ambiguedad de un rotulo es una
    # propiedad de la pagina, y desde adentro de una seccion no se puede ver.
    ambiguas = _zonas_ambiguas(texto)
    zonas, leido = [], []
    for ini, fin, titulo, fase, cuerpo in _secciones_con_span(texto):
        leido.append((ini, fin))
        # Un `=== Resultados ===` que cuelga de `== Ronda de desempate ==` no
        # trae fechas de la liga: trae una definicion. Vaciarle la zona y dejarlo
        # en fase de grupos lo deja mezclado con los demas y hace saltar
        # `todos_tienen_zona`, asi que va por el mismo camino que las tablas de
        # afuera: es una ronda.
        zonas += partidos_de_tabla(cuerpo, anio, torneo, anio_fin, mes_inicio,
                                   zona_defecto=_como_zona(titulo), llave=fase,
                                   arts=arts,
                                   fuera_de_la_liga=bool(_ES_RONDA.match(titulo)
                                                         or _LLAVE_ELIMINATORIA.search(fase)),
                                   ambiguas=ambiguas)

    # Las tablas de partidos que NO cuelgan de un "Resultados". Los reducidos,
    # las promociones y las finales de ascenso viven bajo titulos propios --
    # `== Final por el primer ascenso ==`, `== Permanencia ==` --, asi que la
    # busqueda por seccion nunca se las pasaba y se perdian enteras aunque
    # tuvieran fecha y estadio.
    llaves = partidos_de_plantillas(texto, anio, torneo, anio_fin, mes_inicio)

    # Una final suele estar DOS o TRES veces en la misma pagina: en la ultima
    # fecha de la seccion de resultados, en su seccion propia, y ademas como
    # `{{Partido}}`. Tomandola de todos lados queda duplicada y
    # `validar.sin_duplicados` frena el build -- pasa con la final del
    # Transicion 2020, que esta como tabla y como plantilla, con el estadio
    # escrito distinto en cada una.
    #
    # La copia que se conserva es la de las otras dos vias, que son mas ricas:
    # la plantilla trae la ronda y los penales. Es un partido repetido en la
    # FUENTE, no una fila que se esconde.
    ya = {(p.fecha, p.local, p.visita, p.goles_local, p.goles_visita)
          for p in zonas + llaves}
    for pos, tabla in _tablas(texto):
        if any(ini <= pos < fin for ini, fin in leido) or not _es_tabla_de_partidos(tabla):
            continue
        # `fuera_de_la_liga` no se fuerza: se PREGUNTA. Estas tablas suelen ser
        # de reducidos y promociones, y por eso el default era True -- pero hay
        # paginas que cuelgan su fase regular de un titulo propio en vez de un
        # "Resultados", y ahi el default las mandaba enteras a `eliminacion`.
        #
        # Se notaba en que `posiciones.sumar` solo cuenta la fase de zonas: el
        # Argentino A 2011-12 y el 2012-13 tenian sus tablas leidas, sus 385
        # partidos parseados con "Fecha 1".."Fecha 26" y CERO partidos con que
        # cruzarlas. La pagina tenia arbitro, tenia grilla, y no se hablaban.
        #
        # Lo que decide es la tabla misma: si rotula sus bloques "Fecha N" es una
        # fase regular, salvo que la seccion que la contiene diga lo contrario.
        # Esa salvedad es la que sostiene el caso que motivo el flag -- un
        # `=== Resultados ===` colgado de `== Ronda de desempate ==` no trae
        # fechas de liga aunque las numere.
        llave = _contexto(pos, 3, texto)
        for p in partidos_de_tabla(tabla, anio, torneo, anio_fin, mes_inicio,
                                   llave=llave, arts=arts,
                                   fuera_de_la_liga=not _rotula_fechas(tabla)
                                                    or bool(_ES_RONDA.match(llave))
                                                    or bool(_LLAVE_ELIMINATORIA.search(llave))):
            k = (p.fecha, p.local, p.visita, p.goles_local, p.goles_visita)
            if k in ya:
                continue
            ya.add(k)
            zonas.append(p)
    return zonas + llaves

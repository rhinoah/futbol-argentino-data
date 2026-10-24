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

# Un titulo que NOMBRA una zona. `Interzonal` entra porque lo es: `_seccion` ya lo
# normaliza como etiqueta de zona, y hay paginas que le dan seccion propia.
_NOMBRA_UNA_ZONA = re.compile(r"(?i)^(?:zona|grupo|zone|interzonal)\b")

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
    # "suspendido" (no llego al final), "escritorio" (termino y el numero
    # publicado lo puso un fallo) o "no disputado" (no se jugo nunca).
    # Ver `status_de_la_fila`.
    status: str = ""
    fecha_cruda: str = field(default="", repr=False)   # para diagnosticar
    # De donde salio la FECHA, cuando no salio de la pagina de Wikipedia. El
    # credito viaja con el dato: si una fila usa una segunda fuente, su `source`
    # lo dice. Un dataset que atribuye mal es un dataset que miente sobre si mismo.
    #
    # La fila que nace entera de otra fuente lleva aca el credito de esa fuente
    # desde que nace, tenga fecha o no. Si despues el dia se lo pone una tercera,
    # quedan las dos, separadas como en `source`: ver `fechas.completar`.
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
# la pagina sin comentarios
# --------------------------------------------------------------------------
# Lo que el preprocesador de MediaWiki mira antes que nada: un comentario, o una
# etiqueta cuyo contenido se muestra tal cual. Adentro de <nowiki> y de <pre> un
# `<!--` es texto que se ve, asi que no abre ningun comentario. La etiqueta se
# reconoce como la reconoce MediaWiki: el nombre y despues un blanco, `/>` o `>`,
# para que `<prefacio>` no sea una <pre>.
_COMENTARIO_O_LITERAL = re.compile(r"<!--|<(nowiki|pre)(?=\s|/>|>)[^>]*>", re.I)


def _sin_comentarios(texto: str) -> tuple[str, int]:
    """(texto sin comentarios, donde arranca el que no cierra o -1)."""
    partes, i = [], 0
    while (m := _COMENTARIO_O_LITERAL.search(texto, i)):
        if m.group(1):
            # Autocerrada no tiene adentro. Y una que no cierra es la etiqueta
            # sola, como texto: lo que sigue se lee.
            cierre = (None if m.group(0).endswith("/>") else
                      re.compile(rf"</{m.group(1)}\s*>", re.I).search(texto, m.end()))
            fin = cierre.end() if cierre else m.end()
            partes.append(texto[i:fin])
            i = fin
            continue
        partes.append(texto[i:m.start()])
        cierra = texto.find("-->", m.end())
        if cierra < 0:
            return "".join(partes), m.start()
        i = cierra + 3
    partes.append(texto[i:])
    return "".join(partes), -1


def sin_comentarios(texto: str) -> str:
    """La pagina como la lee MediaWiki: sin los comentarios HTML.

    Lo comentado no lo dice la pagina. El preprocesador lo borra ANTES de buscar
    titulos, tablas, plantillas o enlaces, asi que un `== Final ==` comentado no es
    una seccion, una `{{Partido}}` comentada no es un partido y un enlace comentado
    no desambigua a nadie. Hasta aca solo el lector de `{{Partido}}` lo sabia, y el
    resto del parser leia lo comentado como si estuviera a la vista.

    Medido el 15/10/2026 sobre el catalogo, con las paginas en curso de ese dia: 270
    comentarios en 87 paginas, con 49 titulos y 50 `{{Partido}}` adentro --las
    plantillas, todas de las cuatro paginas de 2026 en curso, que dejan comentadas
    las fases que faltan--, 89 tablas y 162 enlaces. El parser saca los mismos
    partidos con y sin ellos. Lo unico que se movia era el ARTICULO de 335 lados de partido del
    Argentino A 2010-11 y del Federal A 2016, que venia de enlaces de una seccion y
    de una tabla comentadas, y en un solo lado eso cambiaba el club: el `Douglas
    Haig - Rivadavia` de la Fecha 13 del 2010-11, que va en `correcciones`.

    Las reglas son las del preprocesador:
      - un comentario termina en el PRIMER `-->`, sin anidarse, y uno que no cierra
        tapa todo lo que sigue: la pagina no muestra nada despues. Hoy no hay
        ninguno, y si aparece lo avisa `build.procesar`;
      - adentro de <nowiki> y <pre> un `<!--` es texto. Hoy hay dos <nowiki> en el
        catalogo, ninguna <pre> y ningun `<!--` adentro de una.

    Lo que NO se copia, medido sobre las mismas paginas:
      - MediaWiki tambien saltea el contenido de una <ref> y lo limpia aparte, asi
        que a un comentario que abre adentro lo corta el `</ref>`. Hay uno solo
        adentro de una <ref>, y cierra antes: el texto da igual en las 170 paginas;
      - si el renglon queda vacio --solo comentarios y blancos--, MediaWiki se lo
        come entero. Cambia el texto de 82 paginas y ninguna fila ni aviso.

    El lector de `{{Partido}}` los sigue sacando por su cuenta, del cuerpo de la
    plantilla, de la prosa de su seccion y de sus titulos. Desde `build` ya le llega
    la pagina limpia; lo sostienen los que lo llaman directo.
    """
    return _sin_comentarios(texto)[0]


def comentario_sin_cerrar(texto: str) -> int:
    """Donde arranca el `<!--` que no cierra, o -1 si cierran todos."""
    return _sin_comentarios(texto)[1]


# --------------------------------------------------------------------------
# limpieza de wikitexto
# --------------------------------------------------------------------------
_ATRIBUTO = re.compile(r"=|bgcolor|style|align|width|span|scope", re.I)


_ABRE_NOWRAP = re.compile(r"\{\{\s*nowrap\s*\|", re.I)


def _desenvolver_nowrap(s: str) -> str:
    """Saca el `{{nowrap|...}}` y deja lo de adentro, contando llaves."""
    while (m := _ABRE_NOWRAP.search(s)):
        i, hondo = m.start(), 0
        while i < len(s):
            if s.startswith("{{", i):
                hondo += 1
                i += 2
                continue
            if s.startswith("}}", i):
                hondo -= 1
                i += 2
                if hondo == 0:
                    break
                continue
            i += 1
        else:
            # No cierra nunca. Se saca la apertura y se sigue, que es lo mismo
            # que ya hacia la limpieza de abajo con las plantillas sin cerrar.
            return s[:m.start()] + s[m.end():]
        s = s[:m.start()] + s[m.end():i - 2] + s[i:]
    return s


def limpiar(texto: str) -> str:
    """Deja el contenido visible de una celda: sin plantillas, links ni formato."""
    s = texto.strip()
    s = re.sub(r"<ref[^>]*>.*?</ref>", "", s, flags=re.S | re.I)
    s = re.sub(r"<ref[^>]*/>", "", s, flags=re.I)
    # `{{nowrap|X}}` se DESENVUELVE, no se borra: es puro formato, pero adentro
    # esta el dato. Borrarla junto con las demas plantillas hacia desaparecer
    # equipos enteros ("{{nowrap|Gimnasia y Esgrima (LP)}}" quedaba en nada).
    # El no-goloso cerraba en el PRIMER `}}`, que cuando adentro hay otra
    # plantilla es el de ella: en `{{nowrap|{{bandera|Santa Fe}} Colón}}` cerraba
    # en el de la bandera, el desenvuelto quedaba mal armado y el barrido general
    # de plantillas se llevaba puesto al club entero. La celda quedaba VACIA y el
    # partido se descartaba sin que nada fallara: eran 28 filas, casi todas de la
    # Copa Argentina. Ahora se cuentan las llaves.
    s = _desenvolver_nowrap(s)
    # La misma plantilla SIN cerrar tambien existe, y como no cierra no la agarra
    # ni la de arriba ni el barrido general: un club quedaba llamandose
    # "{{nowrap|Defensores de Cambaceres".
    s = re.sub(r"\{\{\s*nowrap\s*\|", "", s, flags=re.I)
    # DE ADENTRO HACIA AFUERA, porque las plantillas se anidan. El barrido no
    # anidado -- una sola pasada de `{{ sin llaves adentro }}` -- no puede tocar a
    # una plantilla que tiene otra adentro, asi que se llevaba la de adentro y
    # dejaba la de AFUERA entera, con su wikitexto crudo, en la celda. Es el mismo
    # error que ya habia estado en `_desenvolver_nowrap` y que ahi se arreglo
    # contando llaves; aca faltaba.
    #
    # Se veia en el dataset publicado: la fecha 13 del Torneo Federal A 2024
    # escribe `Sin disputar{{refn|name=Sansinena1|group=n.|Sansinena fue eliminado
    # del torneo por desercion...{{refn|name=Sansinena}}}}`, un refn adentro de
    # otro, y la columna `venue` de esa fila salia con la plantilla de afuera
    # adentro. Repetir hasta que no cambie las pela de a una y no deja nada.
    while True:
        limpio = re.sub(r"\{\{[^{}]*\}\}", "", s)
        if limpio == s:
            break
        s = limpio
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
#
# Entre el verbo y el dia pueden ir DONDE se jugo, sin pasar de la frase, y el DIA
# DE LA SEMANA, que son las dos cosas que ya acepta `_SE_COMPLETO` para el status:
# «Se jugó en el estadio Enrique Sexto, el 19 de agosto a partir de las 13:30» es el
# `Deportivo Español 1-0 Excursionistas` de la Primera C 2021, que figuraba el 18 --
# el dia que le clausuraron la cancha -- con las 15:00 de ese dia. Solo Ascenso, el
# 19/08/2021 a las 23:52: «el Gallego enfrentó a Excursionistas este jueves en el
# estadio de Lamadrid». Medido el 15/10/2026 sobre las 170 paginas del catalogo: las
# dos piezas mueven UNA fila, esa. Se escriben con tildes porque esta frase se busca
# en la fila cruda y no en el texto sin tildes del status.
_EN_LA_CANCHA = r"(?:en\s+[^.|]{1,60}?,?\s+)?"
_EL_DIA_DE_LA_SEMANA = r"(?:(?:lunes|martes|mi[eé]rcoles|jueves|viernes|s[aá]bado|domingo)\s+)?"
_SE_JUGO = re.compile(
    r"(?i)se\s+(?:jug[oó]|jugaron|disput[oó]|disputaron)\s+(?:el\s+)?"
    + _EN_LA_CANCHA + _EL_DIA_DE_LA_SEMANA
    + r"(\d{1,2}\s*de\s+[a-záéíóúñ]+(?:\s*de\s+\d{4})?)")
# La misma frase EN FUTURO, que es como la escribe una pagina en curso antes de que
# el partido se juegue, y a veces la deja: "Suspendido por las condiciones
# climaticas. Se jugará el 2 de diciembre, a la misma hora". Es un plan y no un
# hecho, asi que NO fecha nada (ver `_FECHADO_EL_DIA_REPROGRAMADO`, que lo midio en
# las tablas) y `_fecha_de_la_nota` no la usa salvo que se la pidan. La pide
# `_dia_y_hora_de_la_nota`, y solo para saber que la hora de la celda -- o la de
# `fecha` en una `{{Partido}}` -- es la de un dia en que el partido no se jugo.
#
# Y EN PRESENTE, que es el mismo plan: «Se juega el miércoles 3 de octubre a las 21:35
# horas» es el `Central Norte (S) 3-0 Juventud Antoniana` del Argentino A 2012-13, que
# figuraba el 16 de septiembre a las 16:45, el dia en que se suspendio sin jugarse un
# minuto. Para el status ya contaba como «se jugo otro dia» (ver `_SE_COMPLETO`); aca
# dice que la hora de la celda es la de un partido que no existio, y queda vacia. El
# dia y la hora buenos los pone una `Dia`, con testigo, en `fad/correcciones.py`.
_SE_JUGARA = re.compile(
    r"(?i)se\s+(?:jugar[aá]n?|juegan?|disputar[aá]n?)\s+(?:el\s+)?"
    + _EN_LA_CANCHA + _EL_DIA_DE_LA_SEMANA
    + r"(\d{1,2}\s*de\s+[a-záéíóúñ]+(?:\s*de\s+\d{4})?)")


def _fecha_de_la_nota(fila: str, anio: int, anio_fin: int | None,
                      mes_inicio: int, programada: str = "",
                      regla: re.Pattern = _SE_JUGO) -> str:
    """La fecha en que se jugo de verdad, cuando la nota al pie la dice.

    Se lee de la FILA cruda y no de la celda, por dos motivos. Uno, que para
    cuando la celda esta armada `limpiar` ya borro el `<ref>` con la nota
    adentro. Dos, que la nota es de la fila: puede colgar de la celda de la
    fecha, de la del resultado o de la del estadio, y en las tres esta hablando
    del mismo partido. Sacarla de la fila las agarra a las tres sin que el texto
    de la nota se meta en la columna de la que colgaba.

    `regla` es la frase que se busca: "se jugo el", salvo que se pida otra.
    """
    m = regla.search(fila)
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


# LA HORA DEL DIA EN QUE SE JUGO. La celda de la hora es la del programado, igual
# que la de la fecha: "28 de junio" y "21:30", con la nota "Suspendido por lluvia.
# Se jugó el 29 de julio, a partir de las 15:00". Si el dia sale de la nota y la
# hora de la celda, la fila publica un instante que no existio: el 29 a las 21:30.
#
# La regla es del dueño del dataset: si el partido se jugo otro dia, `time` es la
# hora a la que se jugo ESE dia. Si la nota la da, se toma de ahi; "a la misma
# hora" es la del programado, que es la de la celda; y si la nota no la da, queda
# vacia. Nunca la del programado sin que la nota lo diga.
#
# Se lee SOLO la oracion de la frase del dia: desde la fecha hasta el punto que la
# cierra o hasta que se termina la nota. Antes de la frase la nota cuenta lo que no
# fue -- "Se reprogramó para el 2 de septiembre, a partir de las 15:00, y se volvió
# a suspender" --, y despues de la nota viene otra cosa: el titulo de una cita
# ("jugarán mañana a las 17"), la celda de la hora o el `fecha` de la plantilla.
# Un punto seguido de un digito no cierra nada: es el de `15.00`.
#
# Las formas son las que escribe la pagina, medidas el 15/10/2026 sobre las 170
# paginas del catalogo: de las 367 filas de tabla cuyo dia sale de la nota, 317
# dan la hora con "a partir de las" (288), "desde las" (25) o "a las" (4) --en 2
# sin los minutos, `a partir de las 14.`, y en 2 con punto, `15.00`--; 45 dicen "a
# la misma hora" (43) o "en el mismo horario" (2), y 5 no dicen ninguna. Una hora
# sola, sin los minutos, se lee si la sigue el final de la oracion o "hs"/"horas":
# `a las 2 semanas` no es una hora. Y una que no existe (`a las 48 horas`) tampoco.
_HORA_DE_LA_NOTA = re.compile(
    r"(?i)\b(?:a\s+partir\s+de\s+las|desde\s+las|a\s+las)\s+(\d{1,2})"
    r"(?:[:.](\d{2})|(?=\s*(?:hs|horas)\b|\s*[.,;)<}]|\s*$))(?![\d:])")
_MISMA_HORA = re.compile(r"(?i)\b(?:a\s+la\s+misma\s+hora|en\s+el\s+mismo\s+horario)\b")
_FIN_DE_LA_ORACION = re.compile(r"\.(?!\d)|<|\}\}|\n")


def _hora_de_la_oracion(oracion: str, hora: str) -> str:
    """La hora que da la oracion de la frase del dia. `hora` es la del programado.

    Con dos horas distintas no se sabe cual es la del partido, y queda vacia: es
    lo mismo que hace `_hora_de_la_plantilla` con dos horas en `fecha`.
    """
    horas = {f"{int(h):02d}:{m or '00'}" for h, m in _HORA_DE_LA_NOTA.findall(oracion)
             if int(h) < 24 and int(m or 0) < 60}
    if horas:
        return horas.pop() if len(horas) == 1 else ""
    return hora if _MISMA_HORA.search(oracion) else ""


def _dia_y_hora_de_la_nota(fila: str, anio: int, anio_fin: int | None,
                           mes_inicio: int, programada: str = "",
                           hora: str = "") -> tuple[str, str]:
    """(dia, hora) del partido: los de la nota si dice que se jugo OTRO dia.

    Salen juntos y de la misma frase, porque son un solo dato: el instante en que
    empezo el partido. `programada` y `hora` son los de la celda, y vuelven tal
    cual cuando la nota no dice otro dia -- no dice ninguno, o repite el
    programado, que es la pagina que ya paso la fila al dia en que se jugo --.
    "Se completó" no cuenta, como para `_fecha_de_la_nota`: ese partido EMPEZO el
    dia y a la hora de la celda.

    LA NOTA EN FUTURO no fecha nada (ver `_SE_JUGARA`), asi que el dia sigue siendo
    el programado; pero dice que ese dia no se jugo, y la hora de la celda es la de
    un partido que no existio. Queda vacia. Son las dos de la Fecha 12 de la Primera
    B 2024 que terminan en "Se jugará el 2 de septiembre, a partir de las ...", que
    publicaban la hora del 31 de agosto, y el `Central Norte (S) - Juventud
    Antoniana` del Argentino A 2012-13, en presente. A las tres las pasa al dia en
    que se jugaron una `Dia`, con su testigo y la hora de la nota.
    """
    jugada = _fecha_de_la_nota(fila, anio, anio_fin, mes_inicio, programada)
    if jugada:
        frase = _SE_JUGO.search(fila)
        fin = _FIN_DE_LA_ORACION.search(fila, frase.end())
        de_la_nota = _hora_de_la_oracion(fila[frase.end():fin.start() if fin else None], hora)
        if jugada != programada:
            return jugada, de_la_nota
        # LA NOTA REPITE EL DIA DE LA CELDA: la pagina ya paso la fila al dia en que
        # se jugo, pero no siempre la hora. `Crucero del Norte 0-1 Rosario Central`, B
        # Nacional 2012-13: la celda dice `21 de noviembre` y `11:00` --la hora del
        # domingo de la lluvia, el 28 de octubre-- y la nota "se disputó el 21 de
        # noviembre, a partir de las 18:30". La hora de la nota es la del partido. Si
        # no da ninguna, queda la de la celda, que ya es la del dia en que se jugo.
        return programada, de_la_nota or hora
    if not jugada and _fecha_de_la_nota(fila, anio, anio_fin, mes_inicio, programada,
                                        regla=_SE_JUGARA) not in ("", programada):
        return programada, ""
    return programada, hora


# UNA NOTA SE DEFINE UNA VEZ Y DESPUES SE REFERENCIA POR NOMBRE. MediaWiki lo
# resuelve al renderizar; el wikitexto crudo no: la fila que la referencia trae
# `{{refn|group=n.|name=tres}}` pelado y no dice nada.
#
# Es la MISMA FORMA que el `rowspan` --una nota, varias filas, una sola con el
# texto-- por otro mecanismo, y con la misma consecuencia. La Primera C 2024
# define `name=tres|Suspendidos por las condiciones climaticas. Se jugaron el 17
# de abril` en una fila y la referencia en las otras dos, que quedaban fechadas el
# 15 y el 16.
#
# Medido sobre el corpus son 31 referencias por nombre, 28 con el cuerpo en la
# misma pagina y 5 cuyo cuerpo dice cuando se jugo. Se resuelve SOLO para la
# fecha: `status_de_la_fila` sigue mirando la fila pelada, igual que con el
# `rowspan`, y esas filas ya salen bien porque el partido se jugo.
_REFN = re.compile(r"\{\{\s*refn\s*\|(?P<args>[^{}]*(?:\{\{[^{}]*\}\}[^{}]*)*)\}\}",
                   re.I)
_NOMBRE_DE_NOTA = re.compile(r"(?:^|\|)\s*name\s*=\s*\"?(?P<n>[^|\"]+?)\"?\s*(?=\||$)",
                             re.I)
# Y LA MISMA NOTA ESCRITA CON LA ETIQUETA, que es la otra forma que tiene MediaWiki:
# `<ref name="suspendido">Suspendido debido a la lluvia. Se jugó el 24 de
# septiembre.</ref>` en una fila y `<ref name="suspendido" />` en otra. Es la Fecha 8
# de la Primera B 2014: la nota se define en `Colegiales - Deportivo Merlo`, que ya
# salia el 24, y `Villa San Carlos 2-0 UAI Urquiza` la referencia y quedaba el 6, el
# dia de la lluvia.
#
# Los atributos van en cualquier orden y con comillas dobles, simples o sin ninguna
# (`<ref group="n." name=x />`). El nombre es uno solo para las dos formas, como ya
# pasaba con `{{refn}}`, que tampoco mira el `group=`: sobre la cache, ningun nombre
# esta definido de las dos maneras ni en dos grupos. Son 1 206 definiciones y 767
# referencias peladas, y resolverlas mueve el dia de UNA fila, esa. 72 nombres se
# definen dos veces con cuerpos distintos, casi todos en las tablas de evolucion de
# posiciones, y ahi manda el primero, como en MediaWiki.
_REF_ETIQUETA = re.compile(r"<ref\b(?P<atr>[^>]*?)(?:/>|>(?P<cuerpo>.*?)</ref\s*>)",
                           re.S | re.I)
_NOMBRE_EN_LA_ETIQUETA = re.compile(
    r"""\bname\s*=\s*(?:"(?P<a>[^"]*)"|'(?P<b>[^']*)'|(?P<c>[^\s"'/>]+))""", re.I)


def _nombre_de_la_etiqueta(atr: str) -> str:
    m = _NOMBRE_EN_LA_ETIQUETA.search(atr)
    return (m.group("a") or m.group("b") or m.group("c") or "").strip() if m else ""


def _cuerpo_de_la_nota(args: str) -> str:
    """Lo que no es `group=` ni `name=`. Vacio cuando la nota es SOLO una
    referencia, que es justamente como se distingue una de la otra."""
    return " ".join(t for t in args.split("|")
                    if t.strip() and not re.match(r"(?i)\s*(group|name)\s*=", t))


def notas_con_nombre(texto: str) -> dict[str, str]:
    """El cuerpo de cada nota que la pagina define una vez y despues referencia.

    Se calcula sobre la PAGINA ENTERA y no sobre la tabla: la definicion y la
    referencia no tienen por que caer en la misma, y desde adentro de una tabla
    la nota referenciada es indistinguible de una que no existe. Es la misma
    razon por la que `_zonas_ambiguas` tambien se calcula una vez.

    Con `setdefault`: si la pagina define el mismo nombre dos veces manda la
    primera, que es lo que hace MediaWiki. La primera DE LA PAGINA, asi que las
    dos formas -- `{{refn}}` y `<ref>` -- se ordenan por donde estan antes de elegir.
    """
    definidas = []
    for m in _REFN.finditer(texto):
        nombre = _NOMBRE_DE_NOTA.search(m.group("args"))
        cuerpo = _cuerpo_de_la_nota(m.group("args"))
        if nombre and cuerpo:
            definidas.append((m.start(), nombre.group("n"), cuerpo))
    for m in _REF_ETIQUETA.finditer(texto):
        nombre = _nombre_de_la_etiqueta(m.group("atr"))
        if nombre and (m.group("cuerpo") or "").strip():
            definidas.append((m.start(), nombre, m.group("cuerpo")))
    notas: dict[str, str] = {}
    for _, nombre, cuerpo in sorted(definidas, key=lambda d: d[0]):
        notas.setdefault(nombre, cuerpo)
    return notas


def _con_notas(texto: str, notas: dict[str, str] | None) -> str:
    """Le devuelve el cuerpo a las referencias por nombre que lo tengan.

    Una referencia cuyo nombre la pagina no define queda como esta: no se
    inventa. Es el caso de las 3 que se midieron sin cuerpo, que son referencias
    a notas de OTRO articulo.
    """
    if not notas:
        return texto

    def reponer(m):
        if _cuerpo_de_la_nota(m.group("args")):
            return m.group(0)
        nombre = _NOMBRE_DE_NOTA.search(m.group("args"))
        cuerpo = notas.get(nombre.group("n")) if nombre else None
        return m.group(0) if cuerpo is None else "{{refn|" + cuerpo + "}}"

    # La etiqueta pelada, `<ref name=x />`. La que trae cuerpo ya dice lo suyo.
    def reponer_etiqueta(m):
        if m.group("cuerpo") is not None:
            return m.group(0)
        cuerpo = notas.get(_nombre_de_la_etiqueta(m.group("atr")))
        return m.group(0) if cuerpo is None else "<ref>" + cuerpo + "</ref>"

    return _REF_ETIQUETA.sub(reponer_etiqueta, _REFN.sub(reponer, texto))


# `24 septiembre`, SIN EL «DE». Lo escribe una sola celda del corpus --la del
# domingo de la Fecha 35 de la Zona A de la Primera Nacional 2023, con `rowspan=4`--
# y con la regla de siempre sus cuatro partidos salian sin fecha teniendo el dia
# escrito en la pagina.
#
# Es una SEGUNDA regla y no un «de» opcional en la primera, y se prueba solo cuando
# la primera no encontro nada: asi ningun texto que hoy se lee puede leerse distinto.
# Y es mas estrecha que la primera en las dos puntas, porque sin el «de» lo unico que
# separa una fecha de dos palabras cualesquiera es lo que tengan alrededor:
#
#   * el mes sale de la lista cerrada de `MESES` y termina ahi (`\b`), no es
#     cualquier palabra que venga despues de un numero;
#   * el dia no puede venir pegado a otro digito ni a dos puntos. Sin eso
#     `2023 septiembre` se lee como el 23 de septiembre y `15:30 marzo` como el 30
#     de marzo: los dos ultimos digitos de un anio o los minutos de una hora.
#
# Medido sobre las 170 paginas del catalogo: una sola lectura nueva, esa celda, y
# cambian cuatro filas.
_DIA_Y_MES_SIN_DE = re.compile(
    r"(?<![\d:])(\d{1,2})\s+(" + "|".join(MESES) + r")\b(?:\s*de\s+(\d{4}))?", re.I)


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
        m = _DIA_Y_MES_SIN_DE.search(texto)
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
#
# ESTE REGEX Y LOS QUE SIGUEN SE PREGUNTAN SOBRE EL TEXTO SIN TILDES, y por eso estan
# escritos sin tildes: ver `_texto_de_la_nota`. Una tilde opcional en cada palabra no
# alcanzaba, porque la pagina no se equivoca solo sacandolas: tambien las pone de mas o
# donde no van. «Se le dió por ganado» (Argentino A 2004-05) salia sin status y sin
# aviso, y «Se compĺetó el 28 de noviembre», con una `ĺ`, salia `suspendido`.
#
# `darle por perdido` va SOLO ACA y no en `_HUBO_FALLO`: es el titulo de la unica cita
# del `San Martín (T) 0-2 Alumni (VM)` del Argentino A 2011-12, «AFA decide darle por
# perdido 0-2 a San Martín de Tucuman frente a Alumni», que es toda la nota de la fila.
# Dice que hubo un fallo y no dice si el partido llego al final, y no llego: el blog de
# Jose Carluccio lo da «Suspendido a los 40', con el marcador 0-2, por agresión a
# Silvestre de Alumni. No continuó ni se modificó el resultado». Leido como fallo
# saldria `escritorio`, que afirma que se jugaron los noventa; leido solo como aviso,
# la fila queda vacia y el build dice que la pagina hablo y no se supo que.
_HABLA_DE_FALLO = re.compile(
    r"(?i)suspendid|abandon|no se present|tribunal|se le dio por|dio por (ganado|perdido|"
    r"terminado|finalizado)|dandolo por|otorgandole|inclusion indebida|mala inclusion"
    r"|darle por perdido")
# NUNCA SE JUGO. La pagina no lo cuenta en una nota al pie sino en la ESTRUCTURA
# de la fila: donde van Estadio, Fecha y Hora pone una sola celda con
# `colspan=3`, porque no hay ninguna de las tres cosas que poner. Son los seis
# que el Torneo Federal A 2024 le dio por perdidos a Sansinena cuando desertó, y
# la propia pagina lo explica: "Sansinena fue eliminado del torneo por desercion
# y se le dieron por perdidos los partidos que debia disputar entre la 13.a y la
# 18.a fecha".
#
# Se pregunta ANTES que todo lo demas. Un partido que no se jugo no puede haber
# sido suspendido ni haber llegado al final, asi que si esto esta, manda.
_NO_SE_JUGO = re.compile(r"(?i)^sin disputar$")

# No llego al final. Es lo unico que la fuente dice SIEMPRE y sin ambiguedad.
_NO_LLEGO_AL_FINAL = re.compile(r"(?i)suspendid|abandono|no se presento|interrumpi")
# NO EMPEZO: el partido se suspendio antes de jugarse, porque no hubo con quien. Es
# `no disputado` y no `suspendido`, que afirmaria que hubo un partido que cortar. La
# pagina lo dice de dos maneras, y son cinco filas del catalogo:
#
#   * un club que no se presento: el `Colón 0-1 Atlético de Rafaela` del Inicial 2013
#     («Suspendido porque Colón no se presentó»; RSSSF: `awarded on Dec 11; Colón
#     dns`), y del Federal A 2015 `Independiente (Ch) 1-0 Alianza (CC)` y `Altos Hornos
#     Zapla 1-0 Andino` («El equipo visitante no se presentó a disputar el partido»;
#     RSSSF: `not played, awd on Oct 29`);
#   * que no habia medico: el `San Jorge (T) 0-1 Unión Aconquija` del Federal A 2015
#     («Suspendido por falta de cuerpo médico»; RSSSF: `not played, awd on Jul 16`) y el
#     `Central Ballester 0-3 Juventud Unida` de la Primera C 2025 («Suspendido por falta
#     de personal médico»; Solo Ascenso, 05/06/2025: el partido «quedó aplazado» y el
#     tribunal lo dio por perdido despues).
#
# Se mira SOLO LA FRASE DE LA PRIMERA SUSPENSION que cuenta la nota, y que en esa frase
# no se hable de minutos: ver `_no_empezo`. Otra fila dice lo mismo y sigue vacia,
# porque despues cuenta que se jugo otro dia, y eso se pregunta antes: el `Juventud
# Unida 0-1 Central Córdoba (R)` de la Primera C 2015.
_NO_EMPEZO = re.compile(r"(?i)no se presento|falta de (?:cuerpo|personal) medico")
# Lo que dice que la pelota ya habia empezado a rodar: «a los 20'», «faltando 7
# minutos», «en el entretiempo», «del segundo tiempo». Si esta, el partido empezo.
_YA_SE_JUGABA = re.compile(r"(?i)a\s+los\s+\d|minuto|tiempo")
# Llego al final y despues un fallo cambio el numero.
# Un fallo que cambio el numero. Se pregunta DESPUES de descartar que el partido
# no haya llegado al final, y ese orden es la regla entera: si hubo suspension,
# manda la suspension; si el partido termino y aun asi hubo fallo, es escritorio.
# EL `le` ES OPCIONAL, y no serlo dejaba una asimetria de una palabra entre este
# regex y `_HABLA_DE_FALLO`: aquel acepta `dio por (ganado|perdido)` sin el `le` y
# este lo exigia, con lo que la fila caia en `sin_clasificar` -- "la pagina dice algo
# sobre un fallo y no se supo que". Era una sola fila en todo el dataset, el
# `Velez Sarsfield 1-0 Boca Juniors` del Clausura 1993, cuya nota dice "Originalmente
# el partido finalizo 1-1. Sin embargo, se dio por perdido el partido a Boca Juniors
# por no presentarse un jugador al control antidoping".
#
# Las otras tres filas del dataset que dicen `dio por ganado/perdido` sin `le` NO
# cambian, y no por suerte: las tres mencionan una suspension, asi que
# `_NO_LLEGO_AL_FINAL` las agarra antes. La precedencia las protege sola.
#
# Y `le dio el partido (ganado|perdido)`, con el objeto EN EL MEDIO: es como lo
# escribe el Torneo Federal A 2014 sobre el `Central Córdoba (SdE) 0-1 San Martín (T)`
# de la Fecha 7 de la Zona 3 --"El Tribunal de Disciplina le dio el partido perdido a
# Central Córdoba por estar inhabilitado un jugador del local"--. La nota no dice si
# el partido se jugo, y se fue a buscar: se jugaron los noventa y termino 1-1. RSSSF
# lo anota `[originally 1-1, awd on Oct 16, at Alfredo Terrera]`; el blog de Jose
# Carluccio da el 1-1 con sus goleadores y "posteriormente, se dio por ganado a San
# Martín de Tucumán por 1-0, debido a mala inclusión de Franco Ledesma"; y La Gaceta
# publico la cronica del empate el mismo 28/09/2014. Llego al final y el numero es de
# oficina: `escritorio`. La tabla de la zona cuenta el 0-1 y no el 1-1 --Central
# Córdoba 9-1-4 con 20:14--, asi que el marcador publicado es el que vale.
#
# Medido sobre las 168 paginas del catalogo mas el Federal A 2014 y el 2015: cambia UNA
# fila, esa, y la lista de fallos sin leer vuelve a cero. La otra fila que usa la frase
# --Deportivo Laferrere - Dock Sud, Primera C 2015-- arranca con "Suspendido por
# incidentes", asi que `_NO_LLEGO_AL_FINAL` la agarra antes, igual que a las de arriba.
_HUBO_FALLO = re.compile(
    r"(?i)se (?:le )?dio por (ganado|perdido)|se lo dio (por )?ganado|le dio por ganado"
    r"|otorgandole|le gano los puntos|(mala|indebida) inclusion|inclusion indebida"
    r"|le dio el partido (?:por )?(?:ganado|perdido)")
# El partido se suspendio y DESPUES se jugo o se completo: llego al final igual,
# aunque en dos dias. Son 356 de las 409 filas que mencionan una suspension, y
# meterlas en "suspendido" seria decir que su marcador no es de la cancha.
#
# Entre el verbo y el dia puede ir el DIA DE LA SEMANA --«Se completo el miércoles 27 de
# marzo» (`Acassuso 1-0 Estudiantes (BA)`, Primera B 2012-13) y «Se completo el lunes 11
# de febrero» (`Guillermo Brown 4-2 Juventud Unida Universitario`, Argentino A
# 2012-13)-- o DONDE se jugo, sin pasar de la frase: «Se jugó en el estadio Enrique
# Sexto, el 19 de agosto» (`Deportivo Español 1-0 Excursionistas`, Primera C 2021,
# programado el 18, el dia que le clausuraron la cancha). Las tres salian
# `suspendido`. Son las dos piezas de `_SE_JUGO`, que llevan la tilde opcional porque
# aquella frase se busca en la fila cruda; sobre este texto, sin tildes, da lo mismo.
#
# Y `juega` en presente, que es el plan escrito como hoy: «Se juega el miércoles 3 de
# octubre a las 21:35 horas» es el `Central Norte (S) 3-0 Juventud Antoniana` del
# Argentino A 2012-13, que se suspendio sin jugarse un minuto y se jugo entero despues:
# Ascenso del Interior publico la cronica, con los goles a los 10' y a los 30' del
# primero y a los 15 segundos del segundo, bajo «Postergado de la 5ª fecha». Vale lo
# mismo que `jugara`, que ya estaba. El dia y la hora de esa fila los pone una `Dia`.
#
# Y EN PLURAL, CON LO QUE FALTABA EN EL MEDIO: "Se completaron los 5 minutos
# adicionales el 3 de agosto". Es la vuelta de la final de la Primera B 2016-17,
# `Deportivo Riestra 2-0 Comunicaciones`, una `{{Partido}}`: mientras su lector no
# escribia `status` no hacia falta, y al escribirlo la fila salia `suspendido` con el
# partido terminado. Sobre la cache, el plural y los minutos estan en esa sola nota.
_LOS_MINUTOS = r"(?:los\s+\d+\s+minutos\s+(?:[a-z]+\s+)?)?"
_SE_COMPLETO = re.compile(
    r"(?i)se\s+(?:jugo|jugaron|juegan?|jugaran?|disputo|disputaron|completo|completaron|"
    r"reanudo|finalizo)\s+" + _EN_LA_CANCHA + _LOS_MINUTOS + r"(?:el\s+)?"
    + _EL_DIA_DE_LA_SEMANA + r"\d{1,2}\s*de\s+[a-z]+")
# Y sin fecha: el resto se jugo «al dia siguiente» o «dos dias despues». Es el `Alumni
# 0-0 Juventud Unida Universitario` del Argentino A 2010-11 («completado al día
# siguiente»; RSSSF: `abandoned at 0-0 in 33' due to rain` el 7 de noviembre y
# `remaining 57'` el 8) y el `Villa Dálmine 0-0 Ferrocarril Midland` de la Primera C
# 2009-10 («jugados los 21´ dos días después»; RSSSF: `abandoned at 0-0 in 69'` el 19
# de febrero y `remaining 21'` el 31 de marzo).
_SE_COMPLETO_DESPUES = re.compile(
    r"(?i)(?:completado|jugados\s+los\s+\d+\S*)\s+(?:al\s+dia\s+siguiente|\S+\s+dias\s+despues)")
# `REPROGRAMADO PARA EL 6 DE OCTUBRE` NO ES LO MISMO: es un plan, no un hecho. De las
# siete filas del corpus que lo dicen, en seis el partido NO se jugo ese dia --se volvio
# a suspender o a postergar-- y la nota lo cuenta despues. Vale como «se jugo» en un
# solo caso: cuando LA FILA ESTA FECHADA ESE MISMO DIA, o sea cuando la celda de la
# fecha ya trae el dia al que la nota dice que se paso, y la nota no cuenta nada mas.
# Es el `General Belgrano (SR) 1-2 CAI` de la Fecha 8 de la Zona 1 del Torneo Federal A
# 2014: la celda dice `6 de octubre` y la nota "Suspendido debido a la lluvia. Fue
# reprogramado para el 6 de octubre a partir de las 14:00". Sin esto la fila salia
# `suspendido`, o sea afirmando que NO llego al final un partido que RSSSF y el blog de
# Jose Carluccio dan jugado el 06/10/2014, 1-2, sin ninguna nota.
#
# El contraejemplo es el `Villa Mitre 2-1 Guillermo Brown` del Federal A 2025: la celda
# dice 11 de octubre, la nota "Fue reprogramado para el 12 de octubre [...] y se volvio
# a suspender", y se jugo el 13. Ahi el plan no coincide con la fila y no vale; lo que
# la salva es el `Se jugó el 13` que sigue. Medido el 11/10/2026 sobre las 170 paginas
# del catalogo: la regla engancha UNA fila, la de General Belgrano.
_FECHADO_EL_DIA_REPROGRAMADO = re.compile(
    r"(?i)\|\s*(\d{1,2}\s*de\s+[a-z]+)\b[^\n]*?"
    r"reprogram\w+\s+para\s+(?:el\s+)?\1(?![a-z])")
# Lo que la nota puede contar DESPUES del plan y que lo desmiente.
_Y_DESPUES_PASO_ALGO = re.compile(
    r"(?i)suspend|posterg|abandon|no se present|interrumpi|tribunal|\bdio\b")


def _se_jugo_el_dia_reprogramado(fila: str) -> bool:
    """La nota dice que el partido se paso a un dia, y la fila esta fechada ese dia."""
    plan = _FECHADO_EL_DIA_REPROGRAMADO.search(fila)
    return bool(plan) and not _Y_DESPUES_PASO_ALGO.search(fila, plan.end())


# LA DIRECCION DE UNA CITA NO ES TEXTO DE LA NOTA. Una celda puede llevar un enlace
# externo cuya URL trae la palabra en el slug, y los regex de arriba la leian como si
# la hubiera escrito la pagina. Es el `Sportivo Estudiantes (SL) 2-0 Juventud Unida
# Universitario` de la Fecha 8 de la Zona 2 del Federal A 2014, cuya celda de fecha
# dice `6 de octubre<ref>[http://www.ascensodelinterior.com.ar/noticias/10541/el-clsico-
# puntano-fue-suspendido/ Postergado por falta de acuerdo para jugar con ambas
# parcialidades.]</ref>`: el texto dice POSTERGADO --se jugo otro dia, entero-- y el
# `suspendido` salia del slug. Se saca la URL antes de preguntar, en el texto que leen
# las dos preguntas --ver `_texto_de_la_nota`--: si se sacara solo para el status,
# `sin_clasificar` seguiria viendo el slug y denunciaria la fila como un fallo sin leer
# (se midio: pasa).
# Medido sobre las mismas 170 paginas: cambia UNA fila, esa.
_URL_DE_CITA = re.compile(r"https?://[^\s\]|}<]+")

# EL NOMBRE DE UNA NOTA TAMPOCO ES TEXTO: es una etiqueta para referenciarla. La
# Primera B 2014 define `<ref name="suspendido">Suspendido debido a la lluvia. Se jugó
# el 24 de septiembre.</ref>` en una fila y la referencia pelada en el `Villa San
# Carlos 2-0 UAI Urquiza`, y la Primera C 2018-19 hace lo mismo con
# `{{refn|group="n."|name="suspendido"}}` en el `Deportivo Armenio 1-1 Cañuelas`: las
# dos salian `suspendido` por el nombre, de dos partidos que la nota que nombran da
# jugados enteros otro dia. Y el `San Martín (B) 1-0 Ferrocarril Midland` de la Primera
# C 2015 salia `suspendido` por `name=suspendidos` con un texto que dice «Los partidos
# fueron postergados». RSSSF da el primero y el ultimo jugados sin nota, el 24/09/2014
# y el 10/06/2015.
_NOMBRE_DE_LA_NOTA = re.compile(r"""(?i)\bname\s*=\s*(?:"[^"]*"|'[^']*'|[^\s|/>}"']+)""")

# UNA CITA ES LA FUENTE DE LA NOTA, NO LA NOTA: su titulo, su rotulo o su `cita=` son
# las palabras de un diario, y un diario escribe «se suspendió» por un partido que se
# postergo antes de empezar. El `Racing Club 1-0 Rosario Central` del Clausura 2002 dice
# «Postergado por motivos de seguridad» y el `suspendido` salia del `cita=` de su
# fuente; el `Unión (MdP) 0-0 Alvarado` del Argentino A 2013-14 dice «Postergado por
# disposición del ApreViDe, fue sucesivamente reprogramado» y salia de los rotulos de
# dos enlaces de Ascenso del Interior, que cuentan que la policia no dio el operativo.
# RSSSF da los dos jugados sin nota, el 6 de marzo de 2002 y el 5 de marzo de 2014.
#
# PERO SOLO CUANDO LA NOTA TIENE TEXTO PROPIO. Si la cita es todo lo que hay, la cita
# es la nota, y sacarla dejaria a la fila sin nada que leer. Son dos filas: el
# `Defensores de Pronunciamiento 0-2 Sol de América` del Federal A 2016-17, cuya nota
# entera es un enlace rotulado «Fallo del Tribunal: Sol de América le ganó los puntos»,
# y el `San Martín (T) 0-2 Alumni (VM)` de `_HABLA_DE_FALLO`. El precio es una tercera,
# el `Excursionistas 0-0 Juventud Unida` de la Primera C 2014, cuya nota entera es un
# enlace rotulado «Suspendido» a una nota de Mundo Ascenso del 15/08/2014 que dice que
# se suspendio «por falta de escenario» --la vispera, sin jugarse-- y que RSSSF da
# jugado el 18 de septiembre, que es el dia de la fila: sigue saliendo `suspendido`.
_CITA = re.compile(r"(?i)\{\{\s*cita\b[^{}]*\}\}|\[https?://[^\]]*\]")
_CUERPO_DE_REF = re.compile(r"(?is)<ref(?:\s[^>]*?)?(?<!/)>(.*?)</ref>")


def _tiene_texto_propio(fila: str) -> bool:
    """Alguna nota de la fila dice algo con palabras suyas: tres letras seguidas que
    no son ni marcado ni el `group=`/`name=` de la nota."""
    cuerpos = ([_cuerpo_de_la_nota(m.group("args")) for m in _REFN.finditer(fila)]
               + _CUERPO_DE_REF.findall(fila))
    return any(re.search(r"[^\W\d_]{3}", re.sub(r"<[^>]*>", " ", c)) for c in cuerpos)


def _texto_de_la_nota(fila: str) -> str:
    """La fila tal como la leen los regex del `status`: sin las citas cuando la nota
    tiene texto propio, sin direcciones, sin el nombre de la nota y sin tildes."""
    sin_citas = _CITA.sub(" ", fila)
    if _tiene_texto_propio(sin_citas):
        fila = sin_citas
    fila = _NOMBRE_DE_LA_NOTA.sub(" ", _URL_DE_CITA.sub(" ", fila))
    return "".join(c for c in unicodedata.normalize("NFD", fila)
                   if not unicodedata.combining(c))


def _llego_al_final_otro_dia(texto: str) -> bool:
    """Se suspendio y se termino de jugar, o se paso al dia de esta fila."""
    return bool(_SE_COMPLETO.search(texto) or _SE_COMPLETO_DESPUES.search(texto)
                or _se_jugo_el_dia_reprogramado(texto))


def _no_empezo(texto: str) -> bool:
    """La PRIMERA suspension que cuenta la nota es que no hubo con quien empezar.

    Se mira la frase de esa suspension y no la nota entera, porque una nota puede
    contar dos cosas: «Suspendido debido a la lluvia. Fue reprogramado para el 6 de
    octubre, pero el equipo visitante no se presentó» no dice si la lluvia corto un
    partido empezado, y ahi lo que se sabe es que no llego al final."""
    m = _NO_LLEGO_AL_FINAL.search(texto)
    if not m:
        return False
    fin = texto.find(".", m.end())
    frase = texto[texto.rfind(".", 0, m.start()) + 1:fin if fin >= 0 else len(texto)]
    return bool(_NO_EMPEZO.search(frase)) and not _YA_SE_JUGABA.search(frase)


def status_de_la_fila(fila: str, estadio: str = "") -> str:
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
      "no disputado" NO SE JUGO NUNCA. Ni empezo. El marcador esta igual porque
                    cuenta para la tabla, pero no salio de una cancha y no hay
                    fecha que buscarle: la pagina no la da porque no existe.

    Los tres primeros hablan de COMO TERMINO un partido que empezo; el cuarto
    dice que no empezo. Por eso se pregunta primero y no compite con los otros.
    La pagina lo dice de dos maneras: con la celda «Sin disputar», que manda sobre
    todo y deja la fila sin dia, o con una nota que cuenta que no hubo con quien
    empezar --ver `_NO_EMPEZO`--, que se pregunta despues de «se jugo otro dia» y
    antes que la suspension, porque esa nota tambien dice «suspendido». En ese caso
    la fila conserva el dia para el que estaba programado, como el `Instituto 0-1
    San Lorenzo` de la 1987-88 que trae RSSSF.

    `estadio` viene YA PARSEADO y no se saca de `fila`, por dos razones: la celda
    trae pegado su `colspan=3|`, que pela `_celda` y no `limpiar`, y con un
    `rowspan` la celda ni siquiera esta en esta fila porque viene arrastrada de
    una anterior. Se mira ESA celda y no la fila entera a proposito: "sin
    disputar" es una afirmacion sobre este partido solo cuando esta ahi.
    """
    if _NO_SE_JUGO.search(estadio.strip()):
        return "no disputado"
    return _status_de_la_nota(_texto_de_la_nota(fila))


def _status_de_la_nota(texto: str) -> str:
    """El orden de las preguntas es la regla: ver `status_de_la_fila`."""
    if _llego_al_final_otro_dia(texto):
        return ""                      # se suspendio y se termino de jugar
    if _no_empezo(texto):
        return "no disputado"          # se suspendio antes de empezar
    if _NO_LLEGO_AL_FINAL.search(texto):
        return "suspendido"            # no llego al final: manda eso
    if _HUBO_FALLO.search(texto):
        return "escritorio"            # llego al final y el numero es de oficina
    return ""


def sin_clasificar(fila: str) -> bool:
    """La fila habla de un fallo y `status_de_la_fila` no supo que decir.

    Vacio quiere decir "la pagina no dijo nada". NUNCA puede querer decir "dijo
    algo que no supe leer": esa es la unica forma de que el default no se vuelva
    una afirmacion inventada sobre 39 mil filas. Cuando pasa, se avisa.
    """
    texto = _texto_de_la_nota(fila)
    if _llego_al_final_otro_dia(texto):
        return False           # se suspendio y se termino de jugar: eso SI se leyo
    return bool(_HABLA_DE_FALLO.search(texto)) and not _status_de_la_nota(texto)


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
            fuera.append(_FALLO_SIN_LEER.format(celdas[0], celdas[2], celdas[1]))
    # Y las `{{Partido}}`, desde que su lector tambien escribe `status`: la guarda
    # tiene que cubrir a todo el que lo escribe. Con el mismo cuerpo que lee el
    # lector, sin los comentarios. Hoy no salta en ninguna.
    for _, crudo in _plantillas_partido(texto):
        visible = _COMENTARIO.sub("", crudo)
        dice = {k.strip().lower(): limpiar(v) for k, v in _parametros(visible, 0, True)}
        if _marcador(dice.get("resultado", "")) and sin_clasificar(visible):
            fuera.append(_FALLO_SIN_LEER.format(dice.get("local", ""), dice.get("visita", ""),
                                                dice.get("resultado", "")))
    return list(dict.fromkeys(fuera))


_FALLO_SIN_LEER = (
    "{} vs {} ({}): la pagina dice algo sobre un fallo y no se supo si el partido "
    "llego al final. Queda con status vacio, que significa \"la pagina no dijo nada\" "
    "-- y aca si dijo. Mira la nota y ajusta `parser.status_de_la_fila`")


_ARRANQUE_CUADRO = re.compile(r"\{\{\s*(?:Copa|Cuadro|Llave)[^\n|}]*", re.I)
_ES_EQUIPO_DEL_CUADRO = re.compile(r"(?i)^\s*RD\d+[- ]?(?:equipo|team)\d*\s*$")
_ENLACE_DEL_CUADRO = re.compile(r"\[\[\s*([^\]|#]+?)\s*(?:\|([^\]]*))?\]\]")
# `w/o` es walkover y `p.` es "por penales": marcas, no clubes.
_NO_ES_CLUB = re.compile(r"(?i)^(w/?o|p\.?|libre|bye)$")

# UN LUGAR RESERVADO, que tampoco es un club: el cuadro de una pagina en curso
# escribe quien VA a ocupar el lugar cuando se juegue lo anterior. Es un lugar
# vacio y se lee como vacio. Las formas son las que hay en los cuadros de la cache:
# "Perdedor Final" (la Primera C 2026, que el build avisaba todos los dias como un
# nombre que el padron no reconoce), "Perdedor de la final 2.º asc." (dos
# revisiones de la Primera C 2025) y "Posición 2" a "Posición 9" (seis revisiones
# de la Primera B 2010-11). "Ganador ..." no aparece y va igual: es la otra mitad
# del mismo cuadro, y ningun club se llama asi.
_LUGAR_RESERVADO = re.compile(r"(?i)^(?:ganador|perdedor)\b|^posici[oó]n\s*\d")

# La SIEMBRA que algunas copas escriben pegada al club: `1: Gimnasia y Tiro (S)`.
# El numero es el orden de la siembra, no parte del nombre, y sin sacarlo esos
# trece nombres no resuelven contra el padron y el cuadro se queda sin cruzar a
# sus clubes.
_SIEMBRA = re.compile(r"^\s*\d+\s*:\s*")

# Las marcas del cuadro que SI llevan wikilink, que es lo que las vuelve
# indistinguibles de un club por su forma. Son dos articulos y no dos nombres
# porque el nombre visible cambia -- `(p)`, `(p.)`, `t. s.` -- y el articulo no.
_ARTICULOS_QUE_NO_SON_CLUB = frozenset({
    "Tiros desde el punto penal",   # la tanda
    "Prórroga (deporte)",           # el tiempo suplementario
})


def _cuerpos_de_cuadro(texto: str):
    """El cuerpo de cada plantilla de cuadro, cortado por llaves BALANCEADAS.

    No alcanza con un regex no-goloso: adentro del cuadro hay otras plantillas
    (`{{small}}`, `{{bandera}}`) y el primer `}}` no es el del cuadro.
    """
    for m in _ARRANQUE_CUADRO.finditer(texto):
        i, hondo = m.start(), 0
        while i < len(texto):
            if texto.startswith("{{", i):
                hondo += 1
                i += 2
                continue
            if texto.startswith("}}", i):
                hondo -= 1
                i += 2
                if hondo == 0:
                    # SIN el `}}` final: si no, se lo queda pegado el ultimo
                    # parametro y ese club se pierde. No es hipotetico y no
                    # falla ruidosamente -- "Independiente }}" no esta en el
                    # padron, asi que el club se saltea callado y el cuadro
                    # queda con uno menos que el que la pagina escribio.
                    yield texto[m.start():i - 2]
                    break
                continue
            i += 1


def _parametros(cuerpo: str, nivel: int = 1, renglones: bool = False) -> list[list[str]]:
    """(nombre, valor) de cada parametro, partiendo por `|` A NIVEL CERO.

    Partir por cualquier `|` rompe los wikilinks: `[[Arsenal Fútbol Club|Arsenal]]`
    queda en dos, y el club pasa a llamarse "[[Arsenal Fútbol Club". Y cortar en el
    fin de linea tampoco sirve, porque la mitad de los cuadros escriben varios
    parametros en el mismo renglon.

    `nivel` es a que profundidad de llaves viven los parametros: 1 si `cuerpo`
    trae la apertura de la plantilla (el cuadro), 0 si ya viene sin ella (la
    `{{Partido}}`, que `_plantillas_partido` entrega pelada).

    `renglones` es el respaldo de la `{{Partido}}` contra un `[[` que no cierra:
    ver `_RENGLON_DE_PARAMETRO`.
    """
    partes, buf, hondo_l, hondo_p, i = [], [], 0, 0, 0
    while i < len(cuerpo):
        if renglones and _RENGLON_DE_PARAMETRO.match(cuerpo, i):
            hondo_l = 0
        for abre, cierra, cual in (("[[", "]]", "l"), ("{{", "}}", "p")):
            if cuerpo.startswith(abre, i):
                if cual == "l":
                    hondo_l += 1
                else:
                    hondo_p += 1
                buf.append(abre)
                i += 2
                break
            if cuerpo.startswith(cierra, i):
                if cual == "l":
                    hondo_l -= 1
                else:
                    hondo_p -= 1
                buf.append(cierra)
                i += 2
                break
        else:
            # El cuadro entero es UNA plantilla, asi que sus propios parametros
            # viven a profundidad 1, no 0. La `{{Partido}}` llega sin su apertura
            # y los suyos viven en 0: eso es `nivel`.
            if cuerpo[i] == "|" and hondo_l <= 0 and hondo_p <= nivel:
                partes.append("".join(buf))
                buf = []
            else:
                buf.append(cuerpo[i])
            i += 1
    partes.append("".join(buf))
    return [x.split("=", 1) for x in partes if "=" in x]


_CU_EQUIPO = re.compile(r"RD(\d+)-(?:team|equipo)(\d+)\s*=\s*([^\n|}]*)")
_CU_GOL = re.compile(
    r"RD(\d+)-(?:score|goles)(\d+)(?:-(\d+)|(ida|vuelta))?\s*=\s*([^\n|}]*)")


def _cu_limpio(v: str) -> str:
    v = re.sub(r"''+", "", v)
    v = re.sub(r"\{\{[^}]*\}\}", "", v)
    return re.sub(r"<[^>]*>", "", v).strip()


def cruces_del_cuadro(texto: str) -> list[tuple[str, str, str, str, list]]:
    """Los cruces del cuadro de llaves: (nombreA, artA, nombreB, artB, patas).

    `patas` son los marcadores de ida y vuelta como (golesA, golesB). NO se
    devuelve quien fue local, y esa ausencia es el resultado de una medicion, no
    un descuido: contra las 761 patas que la grilla tambien tiene -- donde la
    grilla SI dice quien fue local -- la convencion "el equipo de arriba es local
    en la ida" acierta el 55.6%. Una moneda. El cuadro dibuja una llave, no un
    calendario, y quien puso los nombres arriba y abajo no estaba afirmando nada
    sobre la localia.
    #
    Por eso esto NO es una fuente de filas: seria inventarle la localia a la
    mitad. Es un TESTIGO, y es el unico que la fase final tiene -- la tabla de
    posiciones solo habla de las zonas --.

    EL TERCER NUMERO NO ES UNA TERCERA PATA. Muchas plantillas traen el global
    junto a las dos patas, y se lo reconoce por lo que es -- la suma de las dos,
    de los dos lados -- y no por su posicion, que es lo unico honesto cuando la
    misma plantilla se usa tambien para llaves a partido unico. Sobre el corpus
    eso separa 133 globales de 887 patas de verdad; sin la regla, cada uno
    entraba como un partido que nadie jugo.
    """
    fuera = []
    for cuerpo in _cuerpos_de_cuadro(texto):
        eq = {}
        for m in _CU_EQUIPO.finditer(cuerpo):
            crudo = _cu_limpio(m.group(3))
            enlace = re.search(r"\[\[([^\]|]+)(?:\|([^\]]+))?\]\]", crudo)
            if enlace:
                eq[(int(m.group(1)), int(m.group(2)))] = (
                    (enlace.group(2) or enlace.group(1)).strip(),
                    enlace.group(1).strip())
            else:
                eq[(int(m.group(1)), int(m.group(2)))] = (crudo, "")
        goles: dict = {}
        for m in _CU_GOL.finditer(cuerpo):
            pata = m.group(3) or {"ida": "1", "vuelta": "2"}.get(m.group(4), "1")
            v = _cu_limpio(m.group(5)).strip("()").strip()
            if v.isdigit():
                goles.setdefault((int(m.group(1)), int(m.group(2))), {})[pata] = int(v)
        for (rd, slot), (na, aa) in sorted(eq.items()):
            if slot % 2 == 0 or (rd, slot + 1) not in eq:
                continue
            nb, ab = eq[(rd, slot + 1)]
            ga = goles.get((rd, slot), {})
            gb = goles.get((rd, slot + 1), {})
            patas = [(ga[k], gb[k]) for k in sorted(set(ga) & set(gb))]
            if len(patas) == 3 and patas[2] == (patas[0][0] + patas[1][0],
                                                patas[0][1] + patas[1][1]):
                patas = patas[:2]
            if na and nb and patas:
                fuera.append((na, aa, nb, ab, patas))
    return fuera


def clubes_del_cuadro(texto: str) -> dict[str, str]:
    """{club canonico: como lo escribe el cuadro} de las llaves de la pagina.

    El cuadro de eliminacion es el SEGUNDO TESTIGO de una copa. Importa porque
    los cuatro chequeos del cruce comparan la grilla contra la tabla de
    posiciones, y una copa no publica tabla: sus catorce paginas son la mayor
    parte de la region donde ningun chequeo puede opinar. El cuadro lo escribe
    otra mano, con otros nombres, y eso es exactamente lo que hace falta.
    """
    fuera: dict[str, str] = {}
    for cuerpo in _cuerpos_de_cuadro(texto):
        for nombre, valor in _parametros(cuerpo):
            if not _ES_EQUIPO_DEL_CUADRO.match(nombre):
                continue
            enlace = _ENLACE_DEL_CUADRO.search(valor)
            club = limpiar(enlace.group(2) or enlace.group(1)) if enlace else limpiar(valor)
            club = re.sub(r"\{\{.*", "", club).strip()
            club = _SIEMBRA.sub("", club)
            articulo = enlace.group(1) if enlace else ""
            if articulo in _ARTICULOS_QUE_NO_SON_CLUB:
                continue
            if not club or _NO_ES_CLUB.match(club) or re.fullmatch(r"[\d\s.:-]*", club):
                continue
            if _LUGAR_RESERVADO.match(club):
                continue
            fuera[club] = articulo
    return fuera


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


# El azul con que estas paginas pintan la celda del GANADOR. Se acepta tambien
# `#DOE7FF` con la letra O en vez del cero, que es un typo tan comun que en el
# Federal A 2024 son 187 de sus 534 filas -- y que en el navegador ni siquiera
# pinta, asi que nadie lo vio nunca.
#
# Los otros colores NO entran, y no es por prolijidad: significan otra cosa. Los
# verdes (`#cfc`, `#ccffcc`, `#90ee90`, `#81f781`) quieren decir clasifica,
# asciende o avanza la llave -- se ponen sobre el que PASA, que puede haber
# empatado o hasta perdido ese partido --, los rojos (`#fcc`, `#ffcccc`)
# descienden, `#ffa` juega la promocion y `gold` es campeon. Meterlos en la misma
# bolsa convierte 88 filas legitimas en acusaciones falsas.
_AZUL_DEL_GANADOR = re.compile(r"""bgcolor\s*=\s*["']?#?(?:d0e7ff|doe7ff)\b""", re.I)

# Una fila con nota al pie no se mira. Ahi no hay error de nadie: hay DOS
# marcadores legitimos -- el que se jugo y el que puso el tribunal --, y el
# resaltado puede estar sobre cualquiera de los dos sin mentir.
_TIENE_NOTA = re.compile(r"<ref|\{\{\s*refn", re.I)

# Ni una fila con tanda de penales, por el mismo motivo al reves: ahi el color
# marca a QUIEN AVANZO y no quien gano los noventa minutos, asi que un 0-0 con un
# lado pintado es exactamente lo que tiene que ser.
_TIENE_TANDA = re.compile(r"\{\{\s*small|\bpen\.|\(\d+\)")

# Y el marcador se busca con GUION SOLO, sin los dos puntos que acepta
# `_SEPARADOR`. Es la unica diferencia con el resto del modulo y es a proposito:
# con `:` adentro, `21:30` entra como un 21-30 y las celdas de al lado -- la
# fecha, el estadio -- pasan por clubes. Son 239 filas del corpus.
_MARCADOR_SOLO = re.compile(r"^\s*(\d+)\s*-\s*(\d+)\s*$")

# Las filas se cortan tolerando espacios antes del `|-`: con un espacio adelante
# aparece 386 veces en 8 paginas del corpus, y sin tolerarlo el bloque se traga
# la tabla siguiente entera.
#
# MEDIDO: hoy no cambia ninguna de las 19 acusaciones, y no es casualidad. Este
# chequeo corta en el PRIMER marcador de cada bloque, asi que un bloque de mas
# se detiene igual en la primera fila y la basura de la tabla siguiente nunca
# llega a ser vecina de un marcador. Va igual porque es el corte correcto, pero
# no se le atribuye un merito que en esta funcion no tiene.
_CORTE_DE_FILA = re.compile(r"\n\s*\|-")


def resaltado_que_desmiente(
        texto: str,
        ya_arbitrados: set[tuple[str, str, int, int]] = frozenset()) -> list[str]:
    """Las filas de la grilla cuyo resaltado contradice a sus propios digitos.

    Estas paginas pintan de azul al ganador de cada partido, y cuando el partido
    fue empate pintan la celda del MARCADOR en vez de un club. O sea que cada
    fila dice quien gano dos veces: con los numeros y con el color. Cuando las
    dos versiones no coinciden, alguna de las dos esta mal y la fila merece que
    la miren.

    LO QUE ESTA FUNCION NO HACE, Y ES LA MITAD DE POR QUE EXISTE: no absuelve.
    Que el color acompanie a los digitos NO es evidencia de que los digitos esten
    bien, y creer que si lo era fue un error que ya se cometio una vez aca. Se
    midio contra la verdad que el propio repo tiene arbitrada -- los 33
    marcadores de `correcciones.MARCADORES`, cada uno con su fuente -- y da esto:

        el arreglo no cambia la direccion, el color no puede opinar   16
        el color ACOMPANIA a los digitos ... y los digitos son falsos 12
        el color CONTRADICE a los digitos ... y tiene razon            4

    Doce de doce. Cuando el color acompania al numero no confirma nada: es el
    mismo dato escrito dos veces por la misma mano en la misma edicion, y si la
    mano se equivoco, se equivoco en las dos. La unica vez que aporta informacion
    es cuando rompe esa correlacion, y ahi acerto 4 de 4.

    Por eso es un chequeo de TRIAGE y no un veredicto: dice que fila mirar, nunca
    que escribir. La direccion tampoco alcanza para corregir sola -- que el color
    diga "gano el local" no distingue un 2-1 de un 3-0 --, asi que el aviso manda
    a buscar una cronica y no propone marcador.

    `ya_arbitrados` son las filas que `correcciones.MARCADORES` ya resolvio, como
    (local, visita, gol_local, gol_visita) del marcador QUE LA PAGINA ESCRIBE. Se
    saltean, y no es cosmetico: el chequeo lee el wikitexto crudo, asi que sin
    esto seguiria acusando para siempre a las filas que el repo ya arreglo --
    justamente las cuatro donde acerto --, y un aviso que no se puede cerrar
    nunca es un aviso que se aprende a ignorar.

    Dispara 23 veces en las 131 paginas, repartidas en 13. Cuatro son las de
    verdad conocida, que salen por `ya_arbitrados`; quedan 19 abiertas.
    """
    fuera = []
    for bloque in _CORTE_DE_FILA.split(texto):
        if _TIENE_NOTA.search(bloque):
            continue
        celdas = _partir(bloque)
        for k in range(1, max(0, len(celdas) - 1)):
            if _TIENE_TANDA.search(celdas[k]):
                break
            m = _MARCADOR_SOLO.match(_celda(celdas[k])[1])
            if not m:
                continue
            gl, gv = int(m.group(1)), int(m.group(2))
            pintadas = [bool(_AZUL_DEL_GANADOR.search(c))
                        for c in (celdas[k - 1], celdas[k], celdas[k + 1])]
            # Dos celdas pintadas es la fila que ademas marca en rojo al que
            # desciende, o en dorado al campeon: ahi no se sabe cual de los dos
            # colores habla del partido y el chequeo se calla. Cero pintadas es
            # una pagina que no usa la convencion.
            if sum(pintadas) != 1:
                break
            dice = "LEV"[pintadas.index(True)]
            segun_numeros = "L" if gl > gv else ("V" if gv > gl else "E")
            if dice != segun_numeros:
                local, visita = _celda(celdas[k - 1])[1], _celda(celdas[k + 1])[1]
                if (local, visita, gl, gv) in ya_arbitrados:
                    break
                numeros = ("empate" if segun_numeros == "E"
                           else f"gano {local if segun_numeros == 'L' else visita}")
                color = ("un empate" if dice == "E"
                         else f"a {local if dice == 'L' else visita}")
                fuera.append(
                    f"{local} {gl}-{gv} {visita}: los numeros dicen {numeros} y el "
                    f"resaltado de la MISMA fila marca {color}. Uno de los dos "
                    f"esta mal y la fila no dice cual, asi que hay que ir a buscar "
                    f"una cronica. Y OJO: esto no propone un marcador, porque el "
                    f"color da la direccion y no los goles")
            break
    return list(dict.fromkeys(fuera))

# El separador del marcador puede ser un guion, dos puntos, o una RAYA: `1 – 0`
# con raya media (U+2013) en vez de guion. Se ve igual y no lo es, asi que la
# fila no tenia marcador y el partido se descartaba entero -- el desempate por el
# descenso del Argentino A 2005-06, General Paz Juniors - Cipolletti, se perdia
# por eso. Es uno solo en las 131 paginas, y esa es justamente la razon por la
# que no se veia.
_SEPARADOR = r"[-:–—]"


# La tanda pegada ADELANTE del marcador: `(4) 0 - 0 (5)`. Sale de que las copas
# viejas escriben la tanda con un tag -- `<small>(4)</small> 0 - 0 <small>(5)</small>`
# -- y `limpiar` saca el tag pero deja el contenido, mientras que las nuevas la
# escriben con plantilla -- `{{small|(4)}}` -- y la plantilla se borra entera.
#
# No se confunde con el ENTRETIEMPO, que es el error que este modulo pone como
# ejemplo de parser que miente: el entretiempo va DESPUES (`0:1 (0:0)`) y este
# grupo va antes.
_TANDA_ADELANTE = re.compile(r"^\s*\(\d+\)\s*")


def _marcador(texto: str) -> tuple[int, int] | None:
    """El marcador de una celda, o None.

    Se prueba dos veces: como viene, y sacando la tanda de adelante. El ancla al
    principio es a proposito -- sin ella, cualquier par de numeros de la celda
    pasaria por marcador --, y por eso una tanda adelante hacia fallar la fila
    entera. En las copas eso no se veia como un error: `partidos_de_rondas` la
    descartaba con el comentario "ronda en curso: la fila esta pero sin
    marcador", que para un torneo de 2013 es falso. Eran 155 partidos.
    """
    for candidato in (texto, _TANDA_ADELANTE.sub("", texto)):
        m = re.match(r"^\s*(\d+)\s*" + _SEPARADOR + r"\s*(\d+)", candidato)
        if m:
            return int(m.group(1)), int(m.group(2))
    return None





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

# LA PATA NO ES LA RONDA. `Partidos de ida` y `Partido de vuelta` dicen cual de los
# dos partidos de la serie es, y la ronda la dice otro rotulo: el encabezado de
# arriba en la misma tabla (`Semifinales`, en el reducido de la Primera B 2011-12)
# o el titulo de la seccion (`=== Segunda fase ===`, en el Federal A). El
# encabezado de la pata pisaba a los dos: 368 filas de 11 paginas salian con la
# pata en el `matchday`, y las dos patas de cada serie con dos rotulos distintos.
#
# No era solo un rotulo feo. `validar.serie_igualada` arma la serie por la ronda,
# y con la ida y la vuelta rotuladas distinto veia 1 de las 47 series igualadas de
# esas paginas: de las 22 tandas que publica la tabla del global (ver
# `colgar_tandas`), las 10 de una vuelta que no empato salian graves. Y
# `cadena_de_llaves` no podia separar las tres fases del Federal A 2014, que
# rotulaban igual. La pata queda en la fecha: en las 178 series con las dos patas,
# la ida es la primera.
_ES_PATA = re.compile(r"(?i)^partidos? de (ida|vuelta)$")


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



# Una TABLA DE LLAVES DE DOS PATAS declara sus columnas por nombre: `Local - Ida`,
# `Local - Vuelta`, `Ida`, `Vuelta` y a veces `Global`. Se reconoce por el par de
# encabezados de localia, que es lo unico que tienen todas.
_COL_DE_LLAVE = re.compile(r"^!\s*(?:[^|\n]*\|)?\s*"
                           r"(Local\s*-\s*(?:Ida|Vuelta)|Ida|Vuelta|Global)\s*$",
                           re.M | re.I)
_TITULO_DE_LLAVE = re.compile(r"\|\+[^|]*\|\s*'''\s*(.*?)\s*'''")
# "0 (5) - 0 (3)": el marcador de una pata, con los penales si los hubo. Se
# matchea DESPUES de `limpiar`, que deja los parentesis y se lleva el `<small>`:
# mirar el `<small>` crudo perdia justo las llaves definidas por penales.
_PATA = re.compile(r"^(\d+)(?:\((\d+)\))?[-–](\d+)(?:\((\d+)\))?$")
# Las fechas que puede nombrar el titulo de una llave, en las cuatro formas que
# usa el corpus: "21/11", "28 de abril", y las listas "22, 26 y 27 de mayo" donde
# los primeros dias vienen sueltos y el mes aparece una sola vez al final.
_FECHA_BARRAS = re.compile(r"\b(\d{1,2})\s*/\s*(\d{1,2})\b")
# Los dias vienen encadenados por coma, por "y" o por "al" -- "22, 26 y 27 de
# mayo", "22 al 29 de abril" -- con el mes UNA sola vez al final. Sin el "al" se
# pierde el primer dia, que es la forma mas comun del corpus.
_FECHA_DE_MES = re.compile(r"\b\d{1,2}(?:\s*(?:,|y|al)\s*\d{1,2})*\s*de\s+([a-záéíóúñ]+)", re.I)
_DIA_SUELTO = re.compile(r"\b(\d{1,2})\b")


def _columnas_de_llave(bloque: str) -> dict[str, int]:
    """Que columna es cada cosa, LEIDO DEL ENCABEZADO y no supuesto por la posicion.

    Hace falta y se aprendio rompiendolo: el Argentino A 2004-05 ordena
    `Local - Ida | Local - Vuelta | Ida | Vuelta`, pero el 2011-12 y el 2012-13
    ponen cinco columnas y en otro orden -- `Local - Vuelta | Global | Local - Ida |
    Ida | Vuelta` --. Leyendo por posicion, los marcadores entraban como nombres de
    club y las tres temporadas se llenaban de clubes inexistentes.
    """
    orden = {}
    for k, m in enumerate(_COL_DE_LLAVE.finditer(bloque)):
        clave = re.sub(r"\s+", " ", m.group(1).strip().lower())
        orden.setdefault(clave, k)
    return orden


def _fechas_del_titulo(titulo: str) -> list[tuple[int, int]]:
    """Los (dia, mes) que nombra el titulo, en orden y sin repetir.

    Se juntan las dos escrituras porque el corpus usa las dos y a veces mezcla:
    "21/11 - 28/11" y "28 de abril al 9 de mayo". Las listas -- "22, 26 y 27 de
    mayo" -- se expanden a sus tres dias, que es justo lo que hace falta para
    saber que son TRES y no dos.
    """
    fuera: list[tuple[int, int]] = []
    for m in _FECHA_BARRAS.finditer(titulo):
        fuera.append((int(m.group(1)), int(m.group(2))))
    for m in _FECHA_DE_MES.finditer(titulo):
        mes_txt = unicodedata.normalize("NFKD", m.group(1).lower()) \
            .encode("ascii", "ignore").decode()
        mes = MESES.get(mes_txt)
        if not mes:
            continue
        # El trozo entero, para recuperar los dias de la lista que el grupo
        # repetido pisa: re guarda solo la ultima repeticion.
        for d in _DIA_SUELTO.findall(m.group(0).split(" de ")[0]):
            fuera.append((int(d), mes))
    return list(dict.fromkeys(f for f in fuera if 1 <= f[0] <= 31 and 1 <= f[1] <= 12))


# "26 al 31 de mayo" no son dos dias: es una VENTANA. La preposicion es lo unico
# que los separa, y los separa sin ambiguedad -- en castellano `X al Y` abre un
# rango y `X y Y` enumera --.
_ES_RANGO = re.compile(r"\bal\b", re.I)


def _fechas_de_llave(titulo: str, anio: int, anio_fin: int | None,
                     mes_inicio: int) -> tuple[str, str]:
    """La fecha de la ida y la de la vuelta, o dos vacias.

    SOLO cuando el titulo nombra EXACTAMENTE DOS DIAS Y NO UN RANGO.

    Con dos dias enumerados -- "Cuarta fase - 2 y 9 de junio", "Primera ronda
    21/11 - 28/11" -- la pagina esta diciendo en que dia se jugo cada pata y no
    hay nada que deducir. Con tres o mas -- "Tercera fase - 22, 26 y 27 de mayo"
    -- los partidos se repartieron entre esos dias y la tabla no dice cual le toco
    a cada llave.

    Y CON UN RANGO TAMPOCO, que es lo que faltaba. "Cuarta fase - 26 al 31 de
    mayo" nombra exactamente dos dias, asi que pasaba el filtro y les ponia el 26
    a las cuatro idas y el 31 a las cuatro vueltas. No es lo que dice la pagina:
    dice que esa fase se jugo en esa ventana. Los dias reales de esas cuatro
    llaves fueron 26, 26, 27 y 28 las idas y 30, 30, 30 y 31 las vueltas -- lo
    publica el blog de Jose Carluccio partido por partido, con sede y goleadores
    --, o sea que de las ocho filas solo TRES caian bien y cinco llevaban una
    fecha que nadie observo.

    SE MIDIO SOBRE EL CORPUS ENTERO: de los 13 titulos de llave que fechaban, 6
    dicen `al` con ventanas de 4 a 11 dias, y 7 enumeran. Los 7 son del Argentino
    A 2004-05, cuya pagina no tiene NI UN desacuerdo de fecha contra las otras
    fuentes; los 6 con `al` son de donde salen casi todos los desacuerdos de esas
    dos temporadas. El corte no es una intuicion: separa exactamente al grupo que
    discute del que no.

    Este archivo ya tenia la regla escrita en otro lado -- `citadas` dice "un
    rango no es una fecha, asi que no se reparte" -- y aca la rompia.
    """
    if _ES_RANGO.search(titulo):
        return "", ""
    fs = _fechas_del_titulo(titulo)
    if len(fs) != 2:
        return "", ""

    def iso(dia, mes):
        y = anio if (anio_fin is None or mes >= mes_inicio) else anio_fin
        return f"{y}-{mes:02d}-{dia:02d}"

    return iso(*fs[0]), iso(*fs[1])


def _sin_el_rango(titulo: str) -> str:
    """El titulo sin las fechas: lo que queda nombra la ronda.

    Se limpia SIEMPRE, aunque las fechas no se hayan podido usar. Son dos cosas
    distintas y confundirlas cuesta caro: "Tercera fase - 22, 26 y 27 de mayo" no
    se puede fechar, pero su ronda es "Tercera fase", que `parser.RONDAS` conoce
    -- y con el rango pegado no la reconoce nadie y la pagina entera se queda sin
    revisar la cadena de llaves.
    """
    t = _FECHA_DE_MES.sub("", _FECHA_BARRAS.sub("", titulo))
    t = re.sub(r"\s*(?:al|y|,)\s*$", "", t.strip(), flags=re.I)
    return re.sub(r"\s*[-–]\s*$", "", t.strip(" -–")).strip(" -–,").strip()


def partidos_de_llave(bloque: str, anio: int, torneo: str,
                      anio_fin: int | None = None,
                      mes_inicio: int = MES_INICIO_HABITUAL,
                      llave: str = "") -> list[Partido]:
    """Los dos partidos de cada fila de una tabla de llaves de ida y vuelta.

    Es un formato que quedaba entero afuera, y no por un descuido:
    `_es_tabla_de_partidos` mira el encabezado y este no declara `Local`,
    `Resultado` y `Visitante`. La guarda hacia bien su trabajo -- no ES una tabla
    de partidos, es una tabla de LLAVES --, solo que nadie habia escrito el otro
    lector. Son 54 llaves en cuatro paginas del Argentino A (2004-05, 2010-11,
    2011-12 y 2012-13).

    LO QUE LA HACE DISTINTA es que la localia no esta en la celda: esta en el
    SIGNIFICADO de la columna. Una dice quien fue local en la ida y otra quien lo
    fue en la vuelta, asi que los dos partidos de una llave salen de la misma fila
    CRUZADOS. Leerla como una tabla comun le daria la localia al mismo club las dos
    veces y perderia la mitad de las localias, que es la clase de error que no
    rompe nada y miente en silencio.

    Las negritas marcan al que paso, no al local, asi que se limpian y no se usan:
    quien fue local ya lo dice la columna.
    """
    col = _columnas_de_llave(bloque)
    if "local - ida" not in col or "local - vuelta" not in col:
        return []
    salida: list[Partido] = []
    tit = _TITULO_DE_LLAVE.search(bloque)
    titulo = tit.group(1) if tit else ""
    ronda = _sin_el_rango(titulo)
    f_ida, f_vuelta = _fechas_de_llave(titulo, anio, anio_fin, mes_inicio)
    for fila in re.split(r"\n\|-", bloque)[1:]:
        # `_celda` y no `limpiar` a secas: la celda puede traer sus atributos
        # pegados -- `|align=left| Central Norte` --, y sin sacarlos el nombre
        # del club entra con el `align=left|` adelante y no lo reconoce nadie.
        celdas = [_celda(c)[1].replace("'''", "").strip() for c in _partir(fila)]
        if len(celdas) <= max(col.values()):
            continue

        def dame(clave):
            i = col.get(clave)
            return celdas[i] if i is not None and i < len(celdas) else ""

        # LOS DOS MARCADORES VAN EN EL ORDEN DE LAS COLUMNAS DE EQUIPO, no en
        # orden local-visitante. O sea que las dos celdas se leen "goles del club
        # de la columna izquierda - goles del otro", y en la pata donde ese club
        # es visitante hay que darlos vuelta.
        #
        # Se aprendio rompiendolo, y lo delato el propio repo: leyendo las dos
        # patas como local-visitante aparecian cinco partidos "con penales sin
        # haber empatado" -- Atletico Tucuman 2-6 con penales 2-4 --, que es
        # imposible. Dados vuelta cierran solos: la vuelta fue 6-2, el global 6-6
        # y de ahi los penales. Y ademas coincide con quien la pagina pone en
        # negrita, que es el que paso.
        izq = min(col["local - ida"], col["local - vuelta"])
        t1 = celdas[izq]
        a, b = dame("local - ida"), dame("local - vuelta")
        for local, cruda, fecha in ((a, dame("ida"), f_ida),
                                    (b, dame("vuelta"), f_vuelta)):
            visita = b if local == a else a
            m = _PATA.match(re.sub(r"\s+", "", cruda))
            if not m or not local or not visita:
                continue
            g1, p1, g2, p2 = (m.group(1), m.group(2), m.group(3), m.group(4))
            if local != t1:                      # el de la izquierda es el visitante
                g1, p1, g2, p2 = g2, p2, g1, p1
            salida.append(Partido(
                fecha=fecha, hora="", local=local, visita=visita,
                goles_local=int(g1), goles_visita=int(g2),
                penales_local=int(p1) if p1 else None,
                penales_visita=int(p2) if p2 else None,
                torneo=torneo, fase="eliminacion", zona="", jornada=ronda,
                llave=llave, estadio="", status=""))
    return salida


# --------------------------------------------------------------------------
# la tanda de una serie, en la tabla del global
# --------------------------------------------------------------------------
# Las fases a doble partido del Federal A publican cada serie DOS veces: en
# `Enfrentamientos`, un renglon por serie con el global -- `Llave | Equipo 1 |
# Global | Equipo 2` --, y en `Resultados`, un renglon por partido. La tanda vive
# SOLO en la primera, pegada al global (`{{small|(4)}} 2 - 2 {{small|(3)}}`), y la
# fila de la vuelta trae nada mas que los noventa minutos. Sin leerla, la serie
# queda en el CSV como si no se hubiera definido: son las 22 tandas del Federal A
# de 2014 a 2018-19, y RSSSF da las 13 que publica con el mismo numero.
#
# Se reconoce por el encabezado y no por el titulo de la seccion: las dos columnas
# de club rotuladas `Equipo 1` y `Equipo 2`, y `Global` en el medio. MEDIDO SOBRE
# LAS 309 PAGINAS DE LA CACHE: son 47 tablas en 10 paginas, todas del catalogo -- el
# Federal A de 2014 a 2018-19 y de 2024 a 2026, y el Argentino A 2013-14 --, y traen
# tandas solo las de 2014, 2016-17, 2017-18 y 2018-19. Diez de las 47, las cinco del
# Federal A 2025 y las cinco del 2026, no cierran con `|}` sino con la plantilla de
# la leyenda, y salen porque `_tablas` la cuenta como cierre: las de 2025 no tienen
# tandas porque esas series las desempataba la ventaja deportiva, y en 2026 pasa lo
# mismo de la Segunda a la Quinta etapa --el 22/10/2026 la Segunda ya tenia sus 12
# globales, cuatro empatados y sin tanda-- y la pagina dice que solo la Sexta se
# define por penales. Las otras 24 tablas con una columna
# `Global` son de otro tipo: 13 de la fase regional de la Copa Argentina, que rotulan
# `Local en la ida | Global | Local en la vuelta` y cuyas patas no entran al dataset;
# 9 del Argentino A de 2010 a 2013, que lee `partidos_de_llave` con la tanda en la
# celda de la pata, y 2 de una pagina que no esta en el catalogo.
_COLUMNAS_DE_SERIE = frozenset({"equipo 1", "global", "equipo 2"})


@dataclass(frozen=True)
class Tanda:
    """La tanda de una serie como la publica la tabla del global: los dos clubes en
    el orden de las columnas, el global y los penales en ese mismo orden, y la
    seccion de nivel 2 que contiene a la tabla, que es la `llave` de sus partidos."""
    equipo1: str
    equipo2: str
    global1: int
    global2: int
    penales1: int
    penales2: int
    llave: str = ""
    art1: str = field(default="", repr=False)
    art2: str = field(default="", repr=False)


def _columnas_en_orden(tabla: str) -> list[str]:
    """Los nombres de columna del encabezado, en minuscula y en el orden de la tabla."""
    columnas = []
    for linea in re.findall(r"^!(.+)$", tabla, re.M):
        for celda in linea.split("!!"):
            columnas.append(_celda(celda.lstrip("!"))[1].lower())
    return columnas


def tandas_de_las_series(texto: str) -> list[Tanda]:
    """Las tandas que publica la tabla del global de cada fase a doble partido.

    Solo las filas que TRAEN tanda: la que no la trae no tiene nada que agregar a
    los partidos de `Resultados`, que ya dicen el marcador de cada pata. La tanda se
    lee con `_penales`, el mismo lector de la celda del marcador, sobre la celda
    cruda: `limpiar` se lleva las plantillas y con ellas el dato.

    No le pone la tanda a ningun partido: eso lo hace `colgar_tandas`, que necesita
    los nombres ya canonicos. La tabla del global escribe el nombre largo y la
    grilla el corto -- `Defensores de Belgrano (Villa Ramallo)` contra `Defensores de
    Belgrano (VR)`, `Juventud Unida Universitario` contra `Juventud U. U.` --, asi
    que comparadas como cadena no se encuentran nunca.
    """
    arts = articulos_de_la_pagina(texto)
    fuera: list[Tanda] = []
    for pos, tabla in _tablas(texto):
        cols = _columnas_en_orden(tabla)
        if not _COLUMNAS_DE_SERIE <= set(cols):
            continue
        i1, ig, i2 = cols.index("equipo 1"), cols.index("global"), cols.index("equipo 2")
        llave = _contexto(pos, 3, texto)
        for fila in _CORTE_DE_FILA.split(tabla)[1:]:
            if fila.lstrip().startswith("!"):
                continue
            celdas = _partir(fila)
            if len(celdas) <= max(i1, ig, i2):
                continue
            pen = _penales(celdas[ig])
            glob = _marcador(_celda(celdas[ig])[1])
            e1, e2 = _celda(celdas[i1])[1], _celda(celdas[i2])[1]
            if not pen or not glob or not e1 or not e2:
                continue
            fuera.append(Tanda(e1, e2, glob[0], glob[1], pen[0], pen[1], llave,
                               arts.get(e1, ""), arts.get(e2, "")))
    return fuera


def colgar_tandas(ps: list[Partido], tandas: list[Tanda]) -> list[str]:
    """Le pone a la VUELTA de cada serie la tanda que publica la tabla del global.

    Va en la vuelta porque ahi se pateo, y es donde la cuelgan las plantillas de
    Wikipedia y el lector de RSSSF: el dataset guarda los penales por partido. Los
    numeros se dan vuelta si el local de la vuelta es el `Equipo 2` de la tabla.

    LA SERIE SE PIDE ESTRECHA, y cada condicion que falta es un aviso y una tanda
    que no se escribe: exactamente dos partidos de eliminacion entre esos dos clubes
    en la llave de la tabla, en dos dias distintos, cuya suma es el global que la
    tabla publica y que esta igualado. La ida y la vuelta salen de la FECHA, no del
    rotulo: las dos patas llevan la misma ronda en `jornada` (ver `_ES_PATA`).

    Y LA ULTIMA PALABRA LA TIENE `validar.serie_igualada`, la misma que audita la
    tanda despues, como en `rsssf._resolver_tandas`: si este lector y el chequeo
    opinaran distinto sobre la misma fila, el build la escribiria para frenarse
    acto seguido. Una vuelta que quedo empatada no la necesita -- la tanda se
    explica sola --; una que no, si, y la reconoce porque las dos patas comparten
    la ronda. Si no la compartieran -- una tabla que rotula solo la pata y no tiene
    ninguna ronda arriba --, la tanda queda afuera con su aviso. En la cache no hay
    ninguna asi: entran las 22, y 10 son de una vuelta que no empato.

    Corre con los nombres ya canonicos y con las fechas ya puestas por todos los
    completadores: ver `build.procesar`.
    """
    from fad import validar

    avisos: list[str] = []
    for t in tandas:
        a, b = equipos.canonizar(t.equipo1, t.art1), equipos.canonizar(t.equipo2, t.art2)
        cruce = f"{a} {t.global1}-{t.global2} {b} (pen {t.penales1}-{t.penales2})"
        serie = [p for p in ps if p.fase == "eliminacion" and p.llave == t.llave
                 and {p.local, p.visita} == {a, b}]
        if len(serie) != 2:
            avisos.append(f"{cruce}: la tabla del global publica la tanda y la grilla "
                          f"tiene {len(serie)} partidos entre los dos en `{t.llave}`, "
                          f"no 2; queda afuera")
            continue
        ida, vuelta = sorted(serie, key=lambda p: p.fecha)
        if not ida.fecha or ida.fecha == vuelta.fecha:
            avisos.append(f"{cruce}: las dos patas no tienen dos dias distintos y no se "
                          f"sabe cual es la vuelta; queda afuera")
            continue
        suma = tuple(sum(p.goles_local if p.local == c else p.goles_visita for p in serie)
                     for c in (a, b))
        if suma != (t.global1, t.global2):
            avisos.append(f"{cruce}: las dos patas de la grilla suman {suma[0]}-{suma[1]}, "
                          f"no el global de la tabla; queda afuera")
            continue
        if t.global1 != t.global2:
            avisos.append(f"{cruce}: el global no quedo igualado, asi que la tanda no "
                          f"tiene donde vivir; queda afuera")
            continue
        pl, pv = ((t.penales1, t.penales2) if vuelta.local == a
                  else (t.penales2, t.penales1))
        if vuelta.penales_local is not None:
            if (vuelta.penales_local, vuelta.penales_visita) != (pl, pv):
                avisos.append(f"{cruce}: la vuelta ya trae la tanda "
                              f"{vuelta.penales_local}-{vuelta.penales_visita}; no se toca")
            continue
        if vuelta.goles_local != vuelta.goles_visita and not validar.serie_igualada(vuelta, ps):
            avisos.append(f"{cruce}: la vuelta {vuelta.local} {vuelta.goles_local}-"
                          f"{vuelta.goles_visita} {vuelta.visita} no empato y "
                          f"`serie_igualada` no reconoce a las dos patas como una serie "
                          f"({ida.jornada!r} y {vuelta.jornada!r}); queda afuera")
            continue
        vuelta.penales_local, vuelta.penales_visita = pl, pv
    return avisos


# Una hora VALIDA con algo pegado atras. Es el canal que lo transmitio -- la Primera
# B, la C y el Argentino A de 2009 a 2012 escriben `15:30 [[TyC Sports|(TV)]]`, que
# `limpiar` deja en `15:30 (TV)` -- o un parentesis suelto, `18:00 )`, que dejo una
# edicion de 2013 al borrar el enlace al canal. Se toma la hora y se tira la cola.
#
# Lo que no EMPIEZA con una hora valida queda tal como figura: `15::00`, `18:5` o
# `14.00` no se adivinan. Ni se borran: una celda que no se entiende sigue diciendo
# algo, y vaciarla seria decir que la pagina no trae la hora.
_HORA_CON_COLA = re.compile(r"^\s*(\d{1,2}:\d{2})(?!\d)\s*\S")


def _hora(celda: str) -> str:
    m = _HORA_CON_COLA.match(celda)
    return m.group(1) if m else celda


def partidos_de_tabla(bloque: str, anio: int, torneo: str, anio_fin: int | None = None,
                      mes_inicio: int = MES_INICIO_HABITUAL,
                      zona_defecto: str = "", llave: str = "",
                      arts: dict[str, str] | None = None,
                      fuera_de_la_liga: bool = False,
                      ambiguas: frozenset[str] = frozenset(),
                      notas: dict[str, str] | None = None,
                      ronda_de_la_seccion: str = "") -> list[Partido]:
    """`fuera_de_la_liga` marca las tablas que NO cuelgan de un "Resultados".

    Ahi no hay fechas del calendario: son reducidos, promociones, finales y
    desempates. Sus encabezados dicen "Partido 1", "Cuarta ronda", "Tercer
    ascenso" -- etiquetas que no son zonas y que crecen sin fin, asi que en vez
    de irlas agregando a una lista se decide por el lugar: si la tabla esta
    afuera de la seccion de resultados, su encabezado es una ronda y el partido
    es de eliminacion.

    `ronda_de_la_seccion` es la que se le pone a un encabezado que nombra solo la
    pata, si arriba en el bloque no hay otro que nombre la ronda: ver `_ES_PATA`.
    """
    partidos: list[Partido] = []
    pendientes: dict[str, list] = {}        # columna -> [valor, filas restantes]
    # La zona puede venir de un encabezado de tabla (`!colspan=6|Zona A`) o del
    # titulo de la seccion que contiene a esta tabla, que es como lo hace el
    # ascenso. Si aparece un encabezado, pisa al de la seccion.
    jornada, zona, ronda = "", zona_defecto, ""
    ronda_dicha = ""        # la ultima ronda que nombro un encabezado o un titulo
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
            elif _ES_PATA.match(cab):
                # La pata se lleva la ronda de arriba: la del encabezado o el
                # titulo anterior, o la de la seccion. Solo si no hay ninguna queda
                # la pata, que es lo que se hacia antes.
                jornada = ronda = ronda_dicha or ronda_de_la_seccion or cab
            elif fuera_de_la_liga or _ES_RONDA.match(cab):
                jornada = ronda = ronda_dicha = cab
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
            ronda_dicha = ""
            if _ES_RONDA.match(nombre):
                jornada = ronda = nombre
                # Y si nombra la RONDA y no solo la pata, vale tambien para la
                # tabla de abajo cuando esa rotula solo la pata: dos rondas como
                # titulos ADENTRO del `Resultados` (`===== Cuartos de final =====`
                # y `===== Semifinales =====`, cada una con su `Partidos de ida`)
                # salian las dos con la ronda de la seccion de afuera. En la cache
                # no hay ninguna pagina asi: no cambia ninguna fila.
                if not _ES_PATA.match(nombre):
                    ronda_dicha = nombre

        celdas = _partir(fila)
        if len(celdas) < 3:
            continue


        # `crudos` guarda la celda SIN limpiar de cada columna. Hace falta para
        # los penales: `limpiar` borra las plantillas, y en una de las dos
        # notaciones la tanda vive adentro de una. Se lleva junto con `valores` y
        # no por indice, porque con un `rowspan` los indices se corren.
        valores, crudos, i = {}, {}, 0
        for col in COLUMNAS:
            if pendientes.get(col, [None, 0])[1] > 0:
                valores[col], crudos[col] = pendientes[col][0], pendientes[col][2]
                pendientes[col][1] -= 1
                continue
            if i >= len(celdas):
                valores[col], crudos[col] = "", ""
                continue
            crudo = celdas[i]
            filas, contenido = _celda(crudo); i += 1
            valores[col], crudos[col] = contenido, crudo
            if filas > 1:
                pendientes[col] = [contenido, filas - 1, crudo]

        goles = _marcador(valores["resultado"])
        if not goles or not valores["local"] or not valores["visita"]:
            continue
        programada = a_iso(valores["fecha"], anio, anio_fin, mes_inicio)
        # El dia y la hora en que se jugo, que salen JUNTOS de la nota: ver
        # `_dia_y_hora_de_la_nota`, y abajo, en `fecha`, de donde sale el texto.
        fecha, hora = _dia_y_hora_de_la_nota(
            _con_notas(fila + " " + " ".join(crudos.values()), notas),
            anio, anio_fin, mes_inicio, programada, _hora(valores["hora"]))
        pen = _penales(crudos["resultado"])
        partidos.append(Partido(
            status=status_de_la_fila(fila, valores["estadio"]),
            # LA NOTA PUEDE VIVIR EN UNA CELDA CON `rowspan`, y entonces NO esta
            # en el texto de esta fila. Es el caso normal cuando se suspende una
            # tanda entera: la Primera C 2024 pone `rowspan=3|12 de marzo` con la
            # nota "Suspendidos por las condiciones climaticas. Se jugaron el 22
            # de marzo" colgando de esa celda, y por eso la nota habla en PLURAL
            # -- cubre a las tres --. Leyendo solo `fila`, la primera del grupo
            # quedaba con el 22 y las otras dos con el 12: el mismo partido de la
            # misma tanda, fechado con diez dias de diferencia segun donde cayera.
            #
            # `crudos` ya trae la celda original de las filas de continuacion
            # --`pendientes[col][2]`, que se guarda justamente sin limpiar-- asi
            # que alcanza con mirarla. Se midieron 15 partidos asi en el corpus, y
            # los quince coinciden con lo que dicen ESPN y RSSSF por su lado.
            fecha=fecha, hora=hora,
            local=valores["local"], visita=valores["visita"],
            goles_local=goles[0], goles_visita=goles[1],
            # La tanda, cuando la celda del resultado la trae pegada al marcador.
            # Se lee de la celda CRUDA porque `limpiar` borra las plantillas, y en
            # una de las dos notaciones la tanda vive adentro de una.
            penales_local=(pen or (None, None))[0],
            penales_visita=(pen or (None, None))[1],
            torneo=torneo, fase="eliminacion" if ronda else "zonas",
            zona="" if ronda else zona, jornada=jornada, llave=llave,
            local_art=(arts or {}).get(valores["local"], ""),
            visita_art=(arts or {}).get(valores["visita"], ""),
            # "Sin disputar" NO ES UNA CANCHA. La pagina la escribe donde va el
            # estadio porque la celda se come tres columnas, pero publicarla en
            # `venue` seria afirmar que el partido se jugo en un lugar llamado
            # asi. Lo que la celda dice ya quedo en `status`.
            estadio="" if _NO_SE_JUGO.search(valores["estadio"].strip())
                    else valores["estadio"],
            fecha_cruda=valores["fecha"],
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
# Un comentario de wikitexto. No se renderiza, asi que lo que tenga adentro --un
# parametro comentado, por ejemplo-- no es parte de la plantilla.
_COMENTARIO = re.compile(r"<!--.*?-->", re.S)
# EL RESPALDO DEL CORTE A NIVEL CERO. Contar `[[` tiene un costo que partir por
# renglon no tenia: un enlace que no cierra -- `|árbitro = [[Fulano` -- deja la
# profundidad arriba de cero hasta el final del cuerpo, ningun `|` corta, y lo que
# sigue queda pegado a ese parametro. Si `resultado` viene despues, el partido se
# descarta sin aviso, y partiendo por renglon se leia. Por eso cada renglon que
# arranca con `|` cierra los enlaces que quedaron abiertos: un wikilink no cruza un
# renglon de parametro, y el `[[` roto se lleva a lo sumo el resto de SU renglon.
#
# Las llaves `{{` NO se reinician, porque esas si cruzan renglones: una `{{Cita web`
# escrita en varias lineas adentro de una nota trae su propio `|fecha=`, y si cortara
# ahi, la fecha de la cita pisaria a la del partido. Medido sobre las 752 plantillas
# de la cache, con las paginas en curso de hoy: no cambia ningun campo. Ninguna tiene
# hoy un enlace sin cerrar; es un respaldo.
_RENGLON_DE_PARAMETRO = re.compile(r"\n\s*\|")


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


# LA HORA DE UNA `{{Partido}}`. La plantilla tiene un campo `hora` y casi nadie lo
# usa: de las 514 con resultado del catalogo, 511 escriben la hora ADENTRO de `fecha`,
# pegada al dia -- `21 de diciembre, 17:00`, `9 de junio de 2013 - 15:00 hs.`,
# `{{fecha|17|1|2021}}, 22:10 ([[UTC-3]])` -- y solo tres, las del Apertura 2008, usan
# el campo. Sin leerla, la fase final de 46 paginas salia sin hora con la hora a la
# vista: 504 filas. Medido el 15/10/2026, con las paginas en curso de ese dia.
#
# El campo `hora`, cuando esta, es una celda de hora como la de las tablas, y se lee
# igual: con `_hora`, que deja como figura lo que no empieza con una hora valida.
#
# Adentro de `fecha` NO se puede hacer eso. Lo que sobra al sacar el dia no es una
# celda de hora mal escrita: es un pedazo de la fecha (`de 2013 -`, `hs.`,
# `(UTC-3)`) o el `--:--` que la pagina pone mientras el partido no tiene horario.
# Publicarlo en `time` seria decir que eso es la hora. Asi que se toma UNA hora
# valida y nada mas: sin ninguna, o con dos -- no se sabe cual es la del partido --,
# queda vacia, que en el dataset quiere decir "la pagina no la dijo".
#
# Se lee del texto LIMPIO: las notas al pie se van antes de buscar, y una nota que
# cuente "estaba programado a las 15:00" no es la hora del partido.
#
# Y "una hora" quiere decir HH:MM suelta, por los dos lados. Adelante no puede seguir
# otro digito ni otros dos puntos: `17:00:00` no es una hora de la forma que se lee,
# y sin esa guarda daba `17:00`. Atras no puede haber un digito, dos puntos o un
# punto (de `17:00:00` saldria `00:00`), ni un signo: `UTC-03:00` es un huso, no
# una hora, y sin el signo `17:00 (UTC-03:00)` daba dos horas y quedaba vacia. Hoy
# ninguna plantilla del catalogo escribe el huso asi -- todas ponen `UTC-3` --, y
# ninguna cambia.
_HORA_EN_LA_FECHA = re.compile(r"(?<![\d:.+\-−])(\d{1,2}:\d{2})(?![\d:])")


def _hora_de_la_plantilla(campos: dict[str, str]) -> str:
    if campos.get("hora", "").strip():
        return _hora(limpiar(campos["hora"]))
    horas = _HORA_EN_LA_FECHA.findall(limpiar(campos.get("fecha", "")))
    return horas[0] if len(horas) == 1 else ""


# Como dice una plantilla que el partido fue en cancha NEUTRAL. La tabla tiene
# su encabezado -- "Equipo 1 / Equipo 2" --, la plantilla no tiene ninguno: lo
# unico que lo dice es la PROSA de su seccion, y la pagina la escribe siempre
# igual, "La disputaron ... a un solo partido, en sede neutral". Era el
# `Sarmiento (LB) - Los Andes` del tercer ascenso 2024, que salia `false` en las
# dos paginas que lo publican con la frase escrita arriba de la plantilla.
#
# EL ALCANCE ES LA SECCION DEL PARTIDO, Y NADA MAS. Se mira la prosa que va del
# titulo mas cercano hasta la plantilla y, si ese titulo es uno de relleno
# (`==== Partido ====`, `=== Partidos de ida ===`), la entradilla de la seccion
# que lo contiene, que es donde la pagina pone la frase cuando cuelga la
# plantilla de un subtitulo. No se sube mas: la entradilla de una fase entera
# habla de varias rondas a la vez. El Apertura y el Clausura 2025 y el Apertura
# 2026 abren `== Octavos y cuartos de final, semifinales y final ==` con "en la
# sede del mejor ubicado... El partido final se jugo en campo neutral", y subiendo
# hasta ahi se marcaban sus 42 partidos que no son la final -- 14 de cada torneo --,
# jugados todos en la cancha del local. Medido sobre las 514 plantillas con
# resultado: asi marca 14, las 14 en cancha neutral, y deja afuera 60 que tambien
# lo fueron pero cuya frase vive en la seccion de formato o en ninguna parte. Esas
# van declaradas, una por una: ver `correcciones.Neutral`.
#
# Los comentarios HTML se sacan antes de leer, titulos incluidos: las paginas en
# curso dejan comentada la seccion de la final que todavia no se jugo, con la
# frase de la cancha adentro.
_DICE_NEUTRAL = re.compile(r"(?i)\bneutral(es)?\b")
_TITULO_DE_RELLENO = re.compile(r"(?i)^partidos?(\s+de\s+(ida|vuelta))?$")
_REFERENCIA = re.compile(r"<ref[^>/]*/>|<ref[^>]*>.*?</ref>", re.S | re.I)
_PLANTILLA_SIN_ANIDAR = re.compile(r"\{\{[^{}]*\}\}")


def _prosa(trozo: str) -> str:
    """El texto sin comentarios, sin referencias y sin plantillas.

    Las plantillas se sacan de adentro hacia afuera, asi que tambien se van los
    cuerpos de las otras `{{Partido}}` de la seccion: lo que queda es lo que la
    pagina dice con palabras.
    """
    trozo = _REFERENCIA.sub(" ", _COMENTARIO.sub(" ", trozo))
    while (sin := _PLANTILLA_SIN_ANIDAR.sub(" ", trozo)) != trozo:
        trozo = sin
    return trozo


def _la_seccion_dice_neutral(pos: int, texto: str, visible: str) -> bool:
    """Si la seccion de la plantilla que esta en `pos` dice que fue en cancha neutral.

    `visible` es `texto` con los comentarios en blanco, del mismo largo: los
    titulos se buscan ahi para que uno comentado no cuente.
    """
    arriba = list(_TITULO.finditer(visible[:pos]))
    if not arriba:
        return False
    cerca = arriba[-1]
    if _DICE_NEUTRAL.search(_prosa(texto[cerca.end():pos])):
        return True
    if not _TITULO_DE_RELLENO.match(limpiar(cerca.group(2))):
        return False
    padre = next((m for m in reversed(arriba[:-1])
                  if len(m.group(1)) < len(cerca.group(1))), None)
    if padre is None:
        return False
    hasta = next((m.start() for m in arriba if m.start() > padre.start()), pos)
    return bool(_DICE_NEUTRAL.search(_prosa(texto[padre.end():hasta])))


def partidos_de_plantillas(texto: str, anio: int, torneo: str, anio_fin: int | None = None,
                           mes_inicio: int = MES_INICIO_HABITUAL,
                       arts: dict[str, str] | None = None,
                       notas: dict[str, str] | None = None) -> list[Partido]:
    titulos = _titulos_de_ronda(texto)
    arts = arts or articulos_de_la_pagina(texto)
    notas = notas_con_nombre(texto) if notas is None else notas
    visible = _COMENTARIO.sub(lambda m: " " * len(m.group(0)), texto)
    partidos: list[Partido] = []
    # Una pagina puede traer VARIOS cuadros: la final del campeonato, el torneo
    # reducido y la definicion de un ascenso son tres eliminaciones distintas que
    # no se encadenan entre si. Cual es cual lo dice la seccion de nivel 2.
    for pos, cuerpo in _plantillas_partido(texto):
        # Se corta por `|` A NIVEL CERO -- el mismo `_parametros` del cuadro -- y
        # no por renglon. Partir el renglon ya habia fallado una vez: con `\n|`
        # no cortaba nada cuando la pagina INDENTA los parametros (`\n  |local=`),
        # y las 15 plantillas de las Copas de la Liga 2021, 2022 y 2023 se
        # descartaban enteras, con sus fases finales adentro. Con `\n\s*\|` eso
        # se arreglo y quedo el otro lado: un parametro que arranca en el MISMO
        # renglon que el anterior no se ve. La Primera B 2021 escribe
        # `|fecha =21 de noviembre, 17:00 |estadio = Estadio Ramón Roque Martín`,
        # y las dos llaves del reducido de ese dia salian sin `venue`, con la
        # cancha pegada a la fecha cruda. El `|` de nivel cero corta donde sea
        # que este, y el de un `[[destino|texto]]` o un `{{gol|43}}` no corta.
        #
        # Los comentarios se sacan ANTES de cortar, que es lo que hace MediaWiki:
        # no son parte de la plantilla. La Primera C 2025 deja comentadas las
        # patadas de dos tandas (`<!--|penaltis1 = ...-->`), y partiendo por
        # nivel cero esos parametros comentados pasaban a existir. Se sacan del
        # cuerpo entero y no solo para cortar, porque de ese cuerpo se lee mas
        # abajo si el partido se jugo otro dia, y lo que esta comentado tampoco
        # lo dice la pagina.
        #
        # Y con un respaldo que partir por renglon tenia gratis: un `[[` que no
        # cierra no se traga los renglones que siguen. Ver `_RENGLON_DE_PARAMETRO`.
        cuerpo = _COMENTARIO.sub("", cuerpo)
        campos = {k.strip().lower(): v.strip()
                  for k, v in _parametros(cuerpo, nivel=0, renglones=True)}

        goles = _marcador(limpiar(campos.get("resultado", "")))
        if not goles:
            continue
        # OJO: los penales NO salen de los parentesis de `resultado` (eso es el
        # entretiempo). Ver el docstring del modulo.
        pen = _marcador(limpiar(campos.get("resultado penalti", "")))
        programada = (_fecha_de_plantilla(campos.get("fecha", ""))
                      or a_iso(limpiar(campos.get("fecha", "")), anio, anio_fin, mes_inicio))
        # SI LA PLANTILLA DICE QUE SE JUGO OTRO DIA, lo que hay en `fecha` es el
        # programado, hora incluida. La final de la Primera C 2018-19 trae `fecha =
        # 15 de junio, 15:00` y `suceso = Suspendido por las condiciones climaticas.
        # Se jugo el 22 de junio, a partir de las 14:30`: las 15:00 son la hora de un
        # partido que no se jugo. La nota se busca en el cuerpo entero y con la regla
        # de las tablas: "se completo" no cuenta, porque ese partido SI empezo el dia
        # y a la hora de `fecha`. Y si la nota repite el dia de `fecha`, la pagina ya
        # lo corrigio.
        #
        # TAMBIEN EN FUTURO. `Acassuso 1-0 Villa San Carlos`, cuartos de la Primera B
        # 2025, trae `fecha = 29 de noviembre, 17:00` y "Se jugará el 2 de diciembre,
        # a la misma hora": la pagina escribio la nota antes del partido y la dejo
        # asi. El 29 se suspendio antes de empezar, con la cancha anegada, y se jugo el
        # martes 2. Sin la forma en futuro la fila publicaba las 17:00 de un dia en
        # que no hubo partido, mientras `Deportivo Armenio - Sportivo Italiano`, del
        # mismo dia y con la nota en pasado, quedaba vacia.
        #
        # Son 9 plantillas del catalogo: 8 en pasado y esa en futuro. Las 8 en pasado
        # dan la hora -- 4 la escriben, 3 de ellas distinta de la de `fecha`, y 4 dicen
        # "a la misma hora" --; la en futuro tambien, pero es un plan, y queda vacia
        # como la de las tablas (ver `_dia_y_hora_de_la_nota`).
        #
        # EL DIA SALE DE LA NOTA EN PASADO, como en las tablas, y junto con la hora de
        # ese dia; de la nota en futuro no: un plan no fecha nada. Las 8 en pasado pasan
        # al dia en que se jugaron, y a las 8 las confirma la prensa de esos dias.
        # `Acassuso - Villa San Carlos` se jugo el dia del plan, pero eso lo dice Solo
        # Ascenso y no la pagina: va como `Dia`, con su testigo y su hora, en
        # `fad/correcciones.py`.
        #
        # Mover el dia mueve la clave (fecha, local, visitante) de la fila, y con ella
        # lo que engancha por fecha: cuatro de las ocho tenian una `Neutral` declarada
        # con el dia programado, y pasaron al jugado.
        #
        # Con las notas con nombre resueltas, igual que en las tablas: una plantilla
        # puede referenciar una nota que la pagina define en otra parte.
        dia, hora = _dia_y_hora_de_la_nota(_con_notas(cuerpo, notas), anio, anio_fin,
                                           mes_inicio, programada,
                                           _hora_de_la_plantilla(campos))
        partidos.append(Partido(
            # EL STATUS, con la regla de las tablas y sobre el mismo texto que ellas:
            # el cuerpo entero, porque la nota puede colgar de `suceso`, de
            # `resultado` o de `fecha`. Sin esto la plantilla salia siempre vacia, y
            # cuatro dicen otra cosa: tres suspendidas (`Estudiantes (BA) - Almagro`
            # 2015, `Comunicaciones - Estudiantes (BA)` 2016-17 y `Gimnasia y Esgrima
            # (J) - Deportivo Madryn` 2025) y una de escritorio (`Argentino de Quilmes
            # - Defensores de Cambaceres` 2013-14, terminado 0-0 y fallado por mala
            # inclusion).
            status=status_de_la_fila(cuerpo),
            fecha=dia, hora=hora,
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
            fecha_cruda=limpiar(campos.get("fecha", "")),
            # Igual que en las tablas, solo se MARCA: una seccion que no dice
            # nada no afirma que el partido fue en la cancha del local.
            neutral=True if _la_seccion_dice_neutral(pos, texto, visible) else None))
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
# La lista se cortaba en "Tercera fase" y hay torneos con una cuarta: el
# Argentino A 2011-12 y 2012-13 y el Federal A 2021 la juegan. Sin ese escalon
# la pagina entera se queda sin revisar la cadena de llaves, que es lo que
# `_por_ronda` hace -- bien -- apenas una etiqueta no esta.
RONDAS = ("Preclasificatorio", "Ronda previa",
          "Primera fase", "Segunda fase", "Tercera fase", "Cuarta fase",
          "Quinta fase",
          # La sexta y la septima son las del Argentino A 2013-14 y el Federal A
          # 2015, y las de la Revalida del Federal A desde 2016-17 (que dice
          # `etapa`; ver `validar._SINONIMOS`). No hacian falta mientras esas
          # paginas salian con la pata en el `matchday` en vez de la ronda.
          "Sexta fase", "Séptima fase",
          # Van ANTES de los treintaidosavos aunque se llamen "final", y no es
          # un error de tipeo: la Copa Argentina 2013-14 tiene una fase
          # preliminar regional y despues la "Fase final", cuyas dos primeras
          # rondas la pagina numera I y II. Las fechas lo confirman -- marzo y
          # abril, contra julio de los dieciseisavos.
          #
          # Se midio antes de agregarlas: ningun otro torneo del corpus usa un
          # rotulo con "fase final", asi que estas dos lineas no pueden mover a
          # nadie mas de lugar.
          "Fase final i", "Fase final ii",
          "Treintaidosavos", "Dieciseisavos", "Octavos", "Cuartos",
          "Semifinales", "Final")

# "Semifinal" y "Semifinales" son la misma ronda escrita de dos maneras; si
# quedan como dos, el orden de las rondas se parte en dos mitades.
# Los titulos con que una copa nombra sus rondas. Las ediciones viejas tienen dos
# rondas de entrada que las nuevas no -- `Preclasificatorio` y `Ronda previa` en
# la 2012-13, `Fase final I` y `II` en la 2013-14 --, y sin ellas esas secciones
# no se miran nunca: eran 35 partidos, escritos en tablas del mismo formato que
# las demas.
#
# YA NO van solo aca. Estuvieron fuera de `RONDAS` a proposito mientras la cadena
# de llaves no sabia distinguir a un club que perdio de uno que nunca jugo: a la
# Ronda previa de la Copa Argentina entran CUARENTA equipos frescos que no ganaron
# el Preclasificatorio, y pedirle a cada uno que viniera de la ronda anterior daba
# cuarenta y ocho avisos falsos. Salteando la pagina entera se pagaba uno solo.
#
# Ese era el precio de una limitacion, no una propiedad del torneo, y la
# limitacion se levanto: `cadena_de_llaves` ahora dice "entran sin venir de la
# ronda anterior" en vez de acusarlos. Con eso la Copa Argentina 2012-13 se puede
# revisar entera -- 63 partidos que nadie miraba -- y los ocho que SI vienen del
# Preclasificatorio se chequean de verdad.
# `instancia` es como el Campeonato Transicion de Primera Nacional 2020 numera
# las rondas de su fase por el segundo ascenso, y era la unica forma que no
# estaba: sus quince partidos de eliminacion salian con la ronda VACIA, o sea
# con el `matchday` vacio en el CSV. La cuarta y la quinta fase tampoco
# estaban, y son las del Federal A 2024 y 2025.
_TITULO_RONDA = re.compile(
    r"^=+\s*(Primera fase|Segunda fase|Tercera fase|Cuarta fase|Quinta fase"
    r"|Primera ronda|Segunda ronda|Tercera ronda|Cuarta ronda"
    r"|Primera instancia|Segunda instancia|Tercera instancia|Cuarta instancia"
    r"|Treintaidosavos|Dieciseisavos"
    r"|Octavos|Cuartos|Semifinales|Semifinal|Final"
    r"|Preclasificatorio|Ronda previa|Fase final I{1,2})[^=\n]*=+\s*$", re.M | re.I)

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
# Entre la palabra y los numeros hay marcado -- la palabra suele venir dentro de
# un wikilink y la tanda en el renglon de abajo: `[[Penaltis|Pen.]]<br>3 - 4` --,
# asi que se tolera cualquier cosa que NO sea un digito. El limite de 20 es para
# que "pen" no se coma media celda buscando numeros que estan en otra cosa.
_PENAL_ESCRITO = re.compile(r"(?i)pen[^\d]{0,20}(\d+)\s*" + _SEPARADOR + r"\s*(\d+)")


def _penales(celda_cruda: str) -> tuple[int, int] | None:
    """Los penales de una celda de marcador, ANTES de limpiarla.

    Tiene que correr sobre el texto crudo: `limpiar` borra las plantillas, y la
    tanda vive adentro de una. Limpiando primero, `{{small|(5)}} 1 - 1
    {{small|(4)}}` queda en `1 - 1` y la definicion desaparece sin que nada falle.
    """
    n = _PENAL.findall(celda_cruda)
    if len(n) == 2:
        return int(n[0]), int(n[1])
    # La segunda forma de escribirla, que no es una plantilla sino la palabra:
    # `1 - 1<br><hr><small>[[Penaltis|Pen.]]<br>3 - 4</small>`. Pide la palabra
    # EXPLICITA, y por eso no se confunde con el entretiempo -- `0:1 (0:0)` --,
    # que va entre parentesis y que este parser ya sabe que no hay que leer como
    # penales. Son las dos finales del Argentino A 2005-06, que publicaban su
    # marcador de los 90 sin la tanda que decidio el titulo y el descenso.
    m = _PENAL_ESCRITO.search(celda_cruda)
    return (int(m.group(1)), int(m.group(2))) if m else None


def partidos_de_rondas(texto: str, anio: int, torneo: str, anio_fin: int | None = None,
                       mes_inicio: int = MES_INICIO_HABITUAL,
                       arts: dict[str, str] | None = None) -> list[Partido]:
    """La Copa Argentina: una tabla por ronda, `Fecha | Estadio | Eq1 | Partido | Eq2`."""
    partidos: list[Partido] = []
    hasta = 0
    for m in _TITULO_RONDA.finditer(texto):
        # Una ronda ADENTRO de otra ya vino en el cuerpo de la de afuera. Las
        # ediciones viejas de la Copa parten `=== Semifinales ===` en
        # `==== Semifinal 1 ====` y `==== Semifinal 2 ====`, y las dos matchean
        # este mismo regex: sin saltearlas, cada semi entra dos veces y
        # `validar.sin_duplicados` frena el build. Es la misma guarda que ya usa
        # `_secciones_con_span` para un `Resultados` anidado en otro.
        if m.start() < hasta:
            continue
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
        hasta = fin
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


# Titulos de nivel 2 que aparecen en las paginas de torneo y NO son una parte del
# torneo. Es una lista corta y cerrada a proposito: lo que se quiere excluir son
# las secciones de cierre que toda pagina tiene, no adivinar que es una fase.
_NO_SON_FASE = frozenset({
    "entrenadores", "goleadores", "goleadoras", "plantel", "planteles",
    "estadios", "vease tambien", "véase también", "referencias",
    "enlaces externos", "notas", "bibliografia", "bibliografía",
})


def _por_subseccion(titulo: str, cuerpo: str) -> list[tuple[str, str]]:
    """(titulo, cuerpo) de cada subseccion, o el cuerpo entero si no tiene ninguna.

    Una seccion `Resultados` puede traer las zonas ADENTRO en vez de al lado: el
    Argentino A 2005-06 escribe `==== Resultados ====` y cuelga de ahi
    `===== Zona Sur =====` y `===== Zona Norte =====`. Sin partirla, las dos zonas
    llegan al lector en un solo cuerpo con una sola etiqueta, y sus partidos salen
    con la del padre -- `Primera fase` --, que no es una zona sino una fase.

    Es peor que quedar vacia: una zona equivocada parece un dato, y `group` es una
    columna que se publica.

    SE CORTA POR EL NIVEL MAS ALTO QUE APAREZCA, y no por uno fijo: el mismo criterio
    que usa `_secciones_con_span` un nivel mas arriba. Asi una subseccion con
    sub-subsecciones entra entera y no se come a su hermana.

    Y SOLO SI ALGUNA SUBSECCION SE LLAMA COMO UNA ZONA. Partir por cualquier subtitulo
    mueve 13 781 filas del corpus, medido: hay paginas que cuelgan del `Resultados`
    una `Primera rueda` y una `Segunda rueda`, que son mitades de la temporada y no
    zonas, y terminaban escritas en la columna `group`. Cambiar una zona vacia por una
    equivocada es peor que dejarla vacia -- una zona equivocada parece un dato.

    Lo que hay ANTES del primer subtitulo se conserva con la etiqueta de afuera: si
    una pagina pone tablas sueltas arriba de las zonas, tirarlas seria perder
    partidos y ponerles la etiqueta de la primera zona seria mentir.
    """
    cortes = list(_TITULO.finditer(cuerpo))
    if not cortes:
        return [(titulo, cuerpo)]
    arriba = min(len(m.group(1)) for m in cortes)
    cortes = [m for m in cortes if len(m.group(1)) == arriba]
    nombres = [_seccion(limpiar(m.group(2))) for m in cortes]
    if not any(_NOMBRA_UNA_ZONA.match(n) for n in nombres):
        return [(titulo, cuerpo)]
    fuera = []
    if cuerpo[:cortes[0].start()].strip():
        fuera.append((titulo, cuerpo[:cortes[0].start()]))
    for i, (m, n) in enumerate(zip(cortes, nombres)):
        fin = cortes[i + 1].start() if i + 1 < len(cortes) else len(cuerpo)
        # La que NO nombra una zona conserva la etiqueta de afuera: no se sabe que
        # zona es, y ponerle su propio titulo escribiria en `group` algo que no lo es.
        fuera.append((n if _NOMBRA_UNA_ZONA.match(n) else titulo, cuerpo[m.end():fin]))
    return fuera


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
            titulo = _seccion(limpiar(m.group(2)))
            # Una seccion que NO es una parte del torneo no puede ser la llave de
            # un partido, y hay paginas que la meten en el medio. El Campeonato
            # Transicion de Primera Nacional 2020 abre `== Entrenadores ==` y
            # cuelga de ahi su `=== Etapa eliminatoria ===`, asi que sus 18
            # partidos de eliminacion salian con la llave "Entrenadores".
            #
            # No rompe el CSV -- `llave` no se exporta -- pero `validar` agrupa
            # por ella, y una llave inventada arma un cuadro de eliminacion que
            # no existe. Se ignora el titulo y sigue valiendo el anterior, que es
            # la fase de verdad; si no hay anterior, queda vacio, que es lo
            # honesto.
            if titulo.lower() in _NO_SON_FASE:
                continue
            ctx = titulo
    return ctx


# Los titulos que rotulan lo que trae la seccion y no una parte del torneo. El
# Federal A 2024 cuelga los resultados de `==== Enfrentamientos ====`, y la ronda
# es el titulo de arriba, `=== Segunda etapa ===`.
_TITULO_DE_CONTENIDO = re.compile(r"(?i)^(resultados|enfrentamientos?)$")


def _ronda_de_la_seccion(pos: int, texto: str) -> str:
    """El titulo mas cercano que CONTIENE a `pos` y nombra una parte del torneo.

    Lo que le hace falta a un encabezado que nombra solo la pata: ver `_ES_PATA`.
    Si en `pos` empieza un titulo, se miran los de nivel mas alto que el; si no,
    todos los de arriba. Se saltean los de relleno (`Resultados`, `Enfrentamientos`,
    `Partidos de ida`) y los que no son del torneo (`Goleadores`), y no se pasa por
    `_como_zona`: `Octavos de final` es justo lo que hace falta y esa funcion lo
    vacia, porque como ZONA no sirve.
    """
    aca = _TITULO.match(texto, pos)
    nivel = len(aca.group(1)) if aca else 99
    ruta: list[tuple[int, str]] = []
    for m in _TITULO.finditer(texto, 0, pos):
        n = len(m.group(1))
        if n < nivel:
            ruta = [x for x in ruta if x[0] < n] + [(n, _seccion(limpiar(m.group(2))))]
    for _, titulo in reversed(ruta):
        if not (_TITULO_DE_CONTENIDO.match(titulo) or _TITULO_DE_RELLENO.match(titulo)
                or titulo.lower() in _NO_SON_FASE):
            return titulo
    return ""


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
# La plantilla que cierra una tabla con la leyenda de colores abajo,
# `{{Tabla de posiciones fin|color1=...}}`, en vez del `|}`. Es el mismo cierre que
# ya acepta `posiciones._WIKITABLA`.
_CIERRE_CON_LEYENDA = re.compile(r"\{\{\s*Tabla de posiciones fin\b", re.I)


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

    CIERRA TAMBIEN EN `{{Tabla de posiciones fin}}`, la plantilla de la leyenda,
    que hace de `|}`. Sin contarla, una tabla que termina asi no cierra nunca y no
    sale: le pasaba a la tabla del global del Federal A 2025 y del 2026 (ver
    `tandas_de_las_series`). El cuerpo termina ANTES de la plantilla, como en
    `posiciones._WIKITABLA`: adentro, sus parametros quedarian pegados a la ultima
    celda. MEDIDO SOBRE LAS 309 PAGINAS DE LA CACHE: salen 124 tablas mas, en 46
    paginas, y ninguna que ya salia cambia de largo. Son 10 de series y 114 de
    posiciones, promedios y ordenamiento, que ningun lector de partidos acepta: no
    cambia ninguna fila ni ningun aviso.
    """
    for m in _ABRE_TABLA.finditer(texto):
        i, hondo = m.end(), 1
        while i < len(texto) and hondo:
            if texto.startswith("{|", i):
                hondo, i = hondo + 1, i + 2
            elif texto.startswith("|}", i):
                hondo, i = hondo - 1, i + 2
            elif cierre := _CIERRE_CON_LEYENDA.match(texto, i):
                hondo -= 1
                i = cierre.start() if not hondo else cierre.end()
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
    # Por lo mismo: una nota definida en una tabla se referencia en otra.
    notas = notas_con_nombre(texto)
    zonas, leido = [], []
    for ini, fin, titulo, fase, cuerpo in _secciones_con_span(texto):
        leido.append((ini, fin))
        # Un `=== Resultados ===` que cuelga de `== Ronda de desempate ==` no
        # trae fechas de la liga: trae una definicion. Vaciarle la zona y dejarlo
        # en fase de grupos lo deja mezclado con los demas y hace saltar
        # `todos_tienen_zona`, asi que va por el mismo camino que las tablas de
        # afuera: es una ronda.
        # Y SI LA SECCION TRAE SUS ZONAS ADENTRO, se parte: ver
        # `_por_subseccion`. Sin subsecciones devuelve el cuerpo entero con su
        # etiqueta, que es exactamente lo que se hacia antes.
        for titulo, cuerpo in _por_subseccion(titulo, cuerpo):
            zonas += partidos_de_tabla(cuerpo, anio, torneo, anio_fin, mes_inicio,
                                       zona_defecto=_como_zona(titulo), llave=fase,
                                       arts=arts, notas=notas,
                                       # El nombre de la seccion NO decide solo: si la
                                       # tabla rotula sus bloques "Fecha N", es una
                                       # mini-liga aunque la seccion se llame como una
                                       # llave. La `Ronda de desempate` del Federal A
                                       # 2018-19 son tres clubes empatados en la tabla
                                       # de descenso jugando un triangular de tres
                                       # fechas, con su propia tabla de posiciones: no
                                       # es una llave y quedaba en `eliminacion`.
                                       #
                                       # Es la misma pregunta que ya hace el camino de
                                       # respaldo, y ahora los dos coinciden. Se midio
                                       # antes de tocarla: de las dieciseis secciones
                                       # del corpus cuyo titulo parece una ronda, esta
                                       # es la UNICA que rotula fechas. Las otras
                                       # quince -- octavos, cuartos, semis, finales,
                                       # primera/segunda/tercera ronda -- no rotulan
                                       # ninguna, asi que no se mueven.
                                       fuera_de_la_liga=(bool(_ES_RONDA.match(titulo))
                                                         and not _rotula_fechas(cuerpo))
                                                        or bool(_LLAVE_ELIMINATORIA.search(fase)),
                                       ambiguas=ambiguas,
                                       ronda_de_la_seccion=_ronda_de_la_seccion(ini, texto))

    # Las tablas de partidos que NO cuelgan de un "Resultados". Los reducidos,
    # las promociones y las finales de ascenso viven bajo titulos propios --
    # `== Final por el primer ascenso ==`, `== Permanencia ==` --, asi que la
    # busqueda por seccion nunca se las pasaba y se perdian enteras aunque
    # tuvieran fecha y estadio.
    llaves = partidos_de_plantillas(texto, anio, torneo, anio_fin, mes_inicio, notas=notas)

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
        if any(ini <= pos < fin for ini, fin in leido):
            continue
        # Una tabla de llaves de dos patas tiene su propio lector: cada fila son
        # DOS partidos y la localia sale de la columna, no de la celda.
        #
        # Se desvia solo si el lector DEVUELVE algo. Preguntarle al encabezado y
        # cortar ahi seria mas directo y estaria mal: `Ida`, `Vuelta` y `Global`
        # son nombres de columna que aparecen tambien en tablas comunes, y un
        # `continue` de mas se lleva sus partidos sin decir nada.
        de_llave = (partidos_de_llave(tabla, anio, torneo, anio_fin, mes_inicio,
                                      llave=_contexto(pos, 3, texto))
                    if _COL_DE_LLAVE.search(tabla) else [])
        if de_llave:
            for p in de_llave:
                k = (p.fecha, p.local, p.visita, p.goles_local, p.goles_visita)
                if k in ya:
                    continue
                ya.add(k)
                zonas.append(p)
            continue
        if not _es_tabla_de_partidos(tabla):
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
        fuera_de_la_liga = (not _rotula_fechas(tabla)
                            or bool(_ES_RONDA.match(llave))
                            or bool(_LLAVE_ELIMINATORIA.search(llave)))
        # LA ZONA SALE DEL TITULO DE NIVEL 3, que es el que la nombra: `_contexto(pos,
        # 3, ...)` devuelve el de nivel 2, que es la fase. Este camino --el de las
        # tablas que NO cuelgan de un `Resultados`-- pedia la llave y no la zona, y el
        # otro camino si la pedia. Los `Torneo Argentino A` de 2011-12 y 2012-13 no
        # tienen ninguna seccion `Resultados`, asi que caian enteros por aca y sus 673
        # filas se publicaban con la columna `group` vacia.
        #
        # PERO SOLO PARA LAS TABLAS DE LIGA. En una de eliminacion `partidos_de_tabla`
        # REUSA `zona_defecto` como nombre de la ronda --a proposito, y el otro
        # llamador depende de eso--, asi que pasarla ahi no llena la zona: pisa la
        # jornada. El playoff de descenso del Federal A 2024 pasaba de `Régimen de
        # descenso` a `Zona B`, que es el titulo de su subseccion y no la ronda.
        for p in partidos_de_tabla(tabla, anio, torneo, anio_fin, mes_inicio,
                                   llave=llave, arts=arts, notas=notas,
                                   zona_defecto=("" if fuera_de_la_liga else
                                                 _como_zona(_contexto(pos, 4, texto))),
                                   fuera_de_la_liga=fuera_de_la_liga,
                                   ronda_de_la_seccion=_ronda_de_la_seccion(pos, texto)):
            k = (p.fecha, p.local, p.visita, p.goles_local, p.goles_visita)
            if k in ya:
                continue
            ya.add(k)
            zonas.append(p)
    return zonas + llaves

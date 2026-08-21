#!/usr/bin/env python3
"""
fad/torneos.py
==============
Que paginas de Wikipedia componen el dataset.

Es una tabla explicita y no un descubrimiento automatico. Se puede adivinar el
titulo de una temporada por patron ("Anexo:Torneo Apertura {anio} (Argentina)"),
pero el futbol argentino le cambio el nombre y el formato al campeonato casi
todos los anios: Inicial/Final, Transicion, Superliga, Copa de la Liga, Apertura
/Clausura otra vez. No hay patron que sobreviva a eso, y una lista escrita a mano
falla al agregar una temporada — no en silencio, que es lo que importa.
"""
from __future__ import annotations

from dataclasses import dataclass


@dataclass(frozen=True)
class Torneo:
    pagina: str          # titulo exacto en es.wikipedia.org
    torneo: str          # va a la columna `tournament`
    temporada: int       # va a la columna `season`
    formato: str = "liga"    # "liga" (zonas + llaves) o "copa" (tabla por ronda)
    neutral: bool = False    # si TODA la competencia se juega en cancha neutral
    anio_fin: int | None = None   # si la temporada cruza el calendario (2016-17)
    mes_inicio: int = 8           # mes en que arranca; solo importa si cruza
    # Un torneo TERMINADO no se vuelve a bajar: sus filas se toman del CSV que ya
    # esta commiteado. No es solo ahorrar pedidos -- que son 90 de 96 --, es sacar
    # riesgo: si manana alguien reestructura la pagina del Clausura 2007, no hay
    # ninguna razon para que eso toque un dato de hace diecinueve anios. El
    # partido ya se jugo; el dato es duro. `build.py --rehacer` los vuelve a
    # parsear cuando de verdad haga falta.
    cerrado: bool = True
    # ------------------------------------------------------------------
    # De donde sale la FECHA cuando la pagina de Wikipedia no la trae.
    #
    # Son tres fuentes y ninguna cubre todo, que es la razon de que sean tres:
    # worldfootball no tiene Primera C ni el Argentino A, RSSSF tiene el
    # Argentino A viejo, y el feed de ESPN cubre Primera B y C de esos anios.
    # Todo lo demas -- equipos, marcador, jornada -- sigue saliendo de Wikipedia,
    # y `source` dice fila por fila quien puso la fecha.
    # ------------------------------------------------------------------
    # Ids de competencia y temporada en worldfootball. Salen del selector del
    # propio sitio, no de adivinar.
    wf: tuple[str, str] | None = None
    # Archivo de RSSSF (`arg3-int06` -> rsssf.org/tablesa/arg3-int06.html). Ver
    # `fad/rsssf.py`: hace falta ademas un mapa de nombres POR ZONA, porque RSSSF
    # los escribe cortos y resolverlos por el padron da el club equivocado, que
    # es peor que un error.
    rsssf: str | None = None

    # La pagina no tiene grilla y los partidos salen de `rsssf`. Es un flag
    # EXPLICITO y no "si el parser devolvio vacio", y la diferencia importa:
    # una grilla que dejo de parsearse por un bug se ve exactamente igual que
    # una que no existe, y con la regla automatica la importacion taparia la
    # regresion en silencio. Asi, importar es una decision escrita.
    sin_grilla: bool = False
    # El feed de ESPN. La liga, los rangos de fecha y el mapa de nombres viven en
    # `fad/espn.py`, indexados por pagina.
    espn: bool = False

    @property
    def url(self) -> str:
        return "https://es.wikipedia.org/wiki/" + self.pagina.replace(" ", "_")


# `formato` va escrito y no se detecta solo. Una pagina de copa y una de liga se
# parecen lo bastante como para que una deteccion automatica devuelva cero
# partidos en vez de fallar, y cero partidos se parece mucho a "todavia no
# empezo el torneo".
PRIMERA = [
    Torneo("Anexo:Torneo Apertura 2026 (Argentina)", "Primera Division - Apertura", 2026),
    Torneo("Anexo:Torneo Clausura 2026 (Argentina)", "Primera Division - Clausura", 2026, cerrado=False),
]

# El historico. Diez temporadas y siete nombres distintos para el mismo
# campeonato -- por eso el catalogo va a mano: no hay patron de titulo que
# sobreviva a Campeonato / Superliga / Copa de la Liga / Apertura-Clausura.
#
# `anio_fin` marca las que cruzan el calendario. Ojo con `mes_inicio`: la 2019-20
# arranco el 26 de JULIO, y con el corte habitual de agosto su Fecha 1 entera
# quedaba fechada en julio de 2020, al final de la temporada.
#
# En 2020-2024 conviven dos torneos por anio (la Copa de la Liga y el campeonato
# largo) y los dos son de Primera: dejar uno afuera deja medio calendario sin
# cubrir, que para estimar forma reciente es peor que no tener el anio.
HISTORICO = [
    Torneo("Campeonato de Primera División 2016 (Argentina)",
           "Primera Division", 2016),
    Torneo("Campeonato de Primera División 2016-17 (Argentina)",
           "Primera Division", 2016, anio_fin=2017),
    Torneo("Campeonato de Primera División 2017-18 (Argentina)",
           "Primera Division", 2017, anio_fin=2018),
    Torneo("Campeonato de Primera División 2018-19 (Argentina)",
           "Primera Division", 2018, anio_fin=2019),
    Torneo("Campeonato de Primera División 2019-20 (Argentina)",
           "Primera Division", 2019, anio_fin=2020, mes_inicio=7),

    Torneo("Copa de la Liga Profesional 2020", "Copa de la Liga", 2020),
    Torneo("Copa de la Liga Profesional 2021", "Copa de la Liga", 2021),
    Torneo("Campeonato de Primera División 2021 (Argentina)",
           "Primera Division", 2021),
    Torneo("Copa de la Liga Profesional 2022", "Copa de la Liga", 2022),
    Torneo("Campeonato de Primera División 2022 (Argentina)",
           "Primera Division", 2022),
    Torneo("Copa de la Liga Profesional 2023", "Copa de la Liga", 2023),
    Torneo("Campeonato de Primera División 2023 (Argentina)",
           "Primera Division", 2023),
    Torneo("Copa de la Liga Profesional 2024", "Copa de la Liga", 2024),
    Torneo("Campeonato de Primera División 2024 (Argentina)",
           "Primera Division", 2024),

    Torneo("Anexo:Torneo Apertura 2025 (Argentina)",
           "Primera Division - Apertura", 2025),
    Torneo("Anexo:Torneo Clausura 2025 (Argentina)",
           "Primera Division - Clausura", 2025),
]

# `neutral=True` no es una suposicion: la Copa Argentina se juega a partido unico
# en cancha neutral por reglamento, y la propia pagina lo dice ronda por ronda
# ("se enfrentaron a partido unico en estadio neutral"). Es el unico caso hasta
# ahora en que el dato se puede afirmar sin mirar donde queda cada estadio.
# La temporada es el anio en que se JUGARON, que no siempre coincide con el
# titulo: la "2016-17" se disputo entera en 2017. No hay edicion 2021 -- la
# 2019-20 se estiro hasta diciembre de 2020 por la pandemia y la siguiente
# arranco en febrero de 2022.
COPAS = [
    Torneo("Copa Argentina 2011-12", "Copa Argentina", 2012,
           formato="copa", neutral=True),
    Torneo("Copa Argentina 2012-13", "Copa Argentina", 2013,
           formato="copa", neutral=True),
    Torneo("Copa Argentina 2013-14", "Copa Argentina", 2014,
           formato="copa", neutral=True),
    Torneo("Copa Argentina 2014-15", "Copa Argentina", 2015,
           formato="copa", neutral=True),
    Torneo('Copa Argentina 2015-16', "Copa Argentina", 2016,
           formato="copa", neutral=True),
    Torneo('Copa Argentina 2016-17', "Copa Argentina", 2017,
           formato="copa", neutral=True),
    Torneo('Copa Argentina 2017-18', "Copa Argentina", 2018,
           formato="copa", neutral=True),
    Torneo('Copa Argentina 2018-19', "Copa Argentina", 2019,
           formato="copa", neutral=True),
    Torneo('Copa Argentina 2019-20', "Copa Argentina", 2020,
           formato="copa", neutral=True),
    Torneo('Copa Argentina 2022', "Copa Argentina", 2022,
           formato="copa", neutral=True),
    Torneo('Copa Argentina 2023', "Copa Argentina", 2023,
           formato="copa", neutral=True),
    Torneo('Copa Argentina 2024', "Copa Argentina", 2024,
           formato="copa", neutral=True),
    Torneo('Copa Argentina 2025', "Copa Argentina", 2025,
           formato="copa", neutral=True),
    Torneo("Copa Argentina 2026", "Copa Argentina", 2026,
           formato="copa", neutral=True, cerrado=False),
]

# Las divisiones que juegan la Copa Argentina. Sin ellas, la mitad de los cruces
# de la Copa tiene un lado del que no se sabe nada: un club de Primera Nacional
# aparece una vez y desaparece.
#
# Cada una trae su propia forma de estar armada, y por eso el parser tuvo que
# aprender que una pagina puede tener VARIAS secciones "Resultados": el ascenso
# pone `== Zona A ==` y `== Zona B ==` de primer nivel con una adentro de cada
# una, y Primera B y C meten `== Torneo Apertura ==` y `== Torneo Clausura ==`,
# o sea dos torneos en la misma pagina, cada uno con su Fecha 1.
ASCENSO = [
    Torneo("Campeonato de Primera Nacional 2024", "Primera Nacional", 2024),
    Torneo("Campeonato de Primera Nacional 2025", "Primera Nacional", 2025),
    Torneo("Campeonato de Primera Nacional 2026", "Primera Nacional", 2026, cerrado=False),

    Torneo("Campeonato de Primera B 2024 (Argentina)", "Primera B", 2024),
    Torneo("Campeonato de Primera B 2025 (Argentina)", "Primera B", 2025),
    Torneo("Campeonato de Primera B 2026 (Argentina)", "Primera B", 2026, cerrado=False),

    Torneo("Campeonato de Primera C 2024 (Argentina)", "Primera C", 2024),
    Torneo("Campeonato de Primera C 2025 (Argentina)", "Primera C", 2025),
    Torneo("Campeonato de Primera C 2026 (Argentina)", "Primera C", 2026, cerrado=False),

    Torneo("Torneo Federal A 2024", "Torneo Federal A", 2024),
    Torneo("Torneo Federal A 2025", "Torneo Federal A", 2025),
    Torneo("Torneo Federal A 2026", "Torneo Federal A", 2026, cerrado=False),
]

# El ascenso 2011-2015. Las temporadas anteriores a 2011 quedan pendientes: la
# mitad de esas paginas no trae fechas y la otra mitad usa otro formato.
ASCENSO_VIEJO = [
    # Las cuatro mas viejas son las UNICAS del catalogo que necesitan una segunda
    # fuente. Sus paginas publican los resultados en tablas de tres columnas
    # -- Local | Resultado | Visitante -- sin ninguna columna de fecha, asi que
    # el parser saca los 1520 partidos completos y ninguno con dia. Como el
    # esquema promete una fecha en cada fila, sin eso los 1520 se descartan
    # enteros: la diferencia no es "peor calidad", es que el torneo no existe.
    #
    # `wf` son los ids de worldfootball, de donde sale ese unico campo. El resto
    # -- equipos, marcador, jornada -- sigue siendo de Wikipedia, y la columna
    # `source` de esas filas nombra a las dos.
    Torneo("Campeonato de Primera B Nacional 2007-08", "Primera Nacional", 2007,
           anio_fin=2008, wf=("co1787", "se19981")),
    Torneo("Campeonato de Primera B Nacional 2008-09", "Primera Nacional", 2008,
           anio_fin=2009, wf=("co1787", "se19980")),
    Torneo("Campeonato de Primera B Nacional 2009-10", "Primera Nacional", 2009,
           anio_fin=2010, wf=("co1787", "se19979")),
    Torneo("Campeonato de Primera B Nacional 2010-11", "Primera Nacional", 2010,
           anio_fin=2011, wf=("co1787", "se6101")),

    Torneo("Campeonato de Primera B Nacional 2011-12", "Primera Nacional", 2011, anio_fin=2012),
    Torneo("Campeonato de Primera B Nacional 2012-13", "Primera Nacional", 2012, anio_fin=2013),
    Torneo("Campeonato de Primera B Nacional 2013-14", "Primera Nacional", 2013, anio_fin=2014),
    Torneo("Campeonato de Primera B Nacional 2014", "Primera Nacional", 2014),
    Torneo("Campeonato de Primera B Nacional 2015", "Primera Nacional", 2015),

    Torneo("Campeonato de Primera B 2011-12 (Argentina)", "Primera B", 2011, anio_fin=2012),
    Torneo("Campeonato de Primera B 2012-13 (Argentina)", "Primera B", 2012, anio_fin=2013),
    Torneo("Campeonato de Primera B 2013-14 (Argentina)", "Primera B", 2013, anio_fin=2014),
    Torneo("Campeonato de Primera B 2014 (Argentina)", "Primera B", 2014),
    Torneo("Campeonato de Primera B 2015 (Argentina)", "Primera B", 2015),

    Torneo("Campeonato de Primera C 2011-12 (Argentina)", "Primera C", 2011, anio_fin=2012),
    Torneo("Campeonato de Primera C 2012-13 (Argentina)", "Primera C", 2012, anio_fin=2013),
    Torneo("Campeonato de Primera C 2013-14 (Argentina)", "Primera C", 2013, anio_fin=2014),
    Torneo("Campeonato de Primera C 2014 (Argentina)", "Primera C", 2014),
    Torneo("Campeonato de Primera C 2015 (Argentina)", "Primera C", 2015),

    # El Torneo Federal A se llamo "Torneo Argentino A" hasta 2014. Va con su
    # nombre historico: es la misma categoria pero no el mismo torneo.
    Torneo("Torneo Argentino A 2011-12", "Torneo Argentino A", 2011, anio_fin=2012),
    Torneo("Torneo Argentino A 2012-13", "Torneo Argentino A", 2012, anio_fin=2013),
    Torneo("Torneo Argentino A 2013-14", "Torneo Argentino A", 2013, anio_fin=2014),
]

# El historico del ascenso: las mismas cuatro divisiones hacia atras.
ASCENSO_HISTORICO = [
    Torneo('Campeonato de Primera B Nacional 2016', 'Primera Nacional', 2016),
    Torneo('Campeonato de Primera B Nacional 2016-17', 'Primera Nacional', 2016, anio_fin=2017),
    Torneo('Campeonato de Primera B Nacional 2017-18', 'Primera Nacional', 2017, anio_fin=2018),
    Torneo('Campeonato de Primera B Nacional 2018-19', 'Primera Nacional', 2018, anio_fin=2019),
    Torneo('Campeonato de Primera Nacional 2019-20', 'Primera Nacional', 2019, anio_fin=2020),

    Torneo('Campeonato de Primera Nacional 2021', 'Primera Nacional', 2021),
    # Estuvo FUERA por UN partido que dice 'San Martin' a secas, sin enlace,
    # donde juegan el (SJ) y el (T). Se resolvio sin fuentes externas: en esa
    # fecha el (SJ) ya juega y el (T) no. Ver `fad/correcciones.py`.
    Torneo('Campeonato de Primera Nacional 2022', 'Primera Nacional', 2022),
    Torneo('Campeonato de Primera Nacional 2023', 'Primera Nacional', 2023),

    Torneo('Campeonato de Primera B 2016 (Argentina)', 'Primera B', 2016),
    Torneo('Campeonato de Primera B 2016-17 (Argentina)', 'Primera B', 2016, anio_fin=2017),
    # Estuvo FUERA con el cartel "lista dos veces las fechas de la primera rueda",
    # que era falso. Lo que la frenaba era UN partido: el desempate que definio el
    # campeonato colgaba de un encabezado `!colspan=12|Desempate`, el parser lo
    # tomaba por zona, y `todos_tienen_zona` saltaba por la mezcla de 306 partidos
    # sin zona y uno con. Ver `parser._ES_RONDA`.
    Torneo('Campeonato de Primera B 2017-18 (Argentina)', 'Primera B', 2017, anio_fin=2018),
    Torneo('Campeonato de Primera B 2018-19 (Argentina)', 'Primera B', 2018, anio_fin=2019),
    Torneo('Campeonato de Primera B 2019-20 (Argentina)', 'Primera B', 2019, anio_fin=2020),

    # Estuvo FUERA un tiempo, con el cartel "una plantilla {{Partido}} sin cerrar
    # bien mezcla el resultado de dos partidos". La culpa no era de la pagina: sus
    # doce plantillas cierran perfecto. Era el parser, que buscaba el cierre con un
    # regex y se comia las del medio. Ver `_plantillas_partido`.
    Torneo('Campeonato de Primera B 2021 (Argentina)', 'Primera B', 2021),
    Torneo('Campeonato de Primera B 2022 (Argentina)', 'Primera B', 2022),
    Torneo('Campeonato de Primera B 2023 (Argentina)', 'Primera B', 2023),

    # Sin fecha en la fuente: sus tablas son de tres columnas
    # Local | Resultado | Visitante. Los partidos estan completos y verificados
    # -- los goles coinciden con la ficha de cada pagina --, asi que se guardan en
    # `data/sin-fecha/` a la espera de una fuente de fechas. worldfootball no
    # sirve: su selector no lista Primera C para Argentina.
    Torneo('Campeonato de Primera C 2008-09 (Argentina)', 'Primera C', 2008,
           anio_fin=2009, espn=True),
    Torneo('Campeonato de Primera C 2009-10 (Argentina)', 'Primera C', 2009,
           anio_fin=2010, espn=True),
    Torneo('Campeonato de Primera C 2010-11 (Argentina)', 'Primera C', 2010,
           anio_fin=2011, espn=True),
    # Este ESTUVO en `sin-fecha/` por un diagnostico equivocado, y conviene dejar
    # escrito cual. El comentario que habia aca decia: "sus tablas SI tienen
    # columna de fecha, pero la pagina la deja vacia en casi todas las filas...
    # quedan 65 de 438 con fecha, y NO ES EL PARSER: la fuente no la trae".
    #
    # Era el parser. `_partir` descartaba las celdas vacias, asi que en las
    # jornadas donde la pagina deja el ESTADIO en blanco -- de la Fecha 18 en
    # adelante -- las columnas se corrian un lugar y la fecha aterrizaba en la
    # cancha. El partido salia sin fecha y con `venue = "2 de febrero"`, que es
    # peor que salir sin nada: no era un hueco, era un dato falso.
    #
    # Arreglado el corrimiento, la pagina fecha sus 438 partidos, los 438. La
    # leccion es la de siempre en este repo: antes de culpar a la fuente,
    # medirlo. "La fuente no lo trae" es comodo y hay que probarlo.
    Torneo('Torneo Argentino A 2010-11', 'Torneo Argentino A', 2010,
           anio_fin=2011),
    # Igual que la de arriba: tiene columna de fecha y la deja vacia en 462 de
    # sus 474 filas. La mitad de las jornadas ademas escribe los clubes con el
    # nombre cortado ("Sp. Italiano", "T. Suarez"), que estan como alias.
    Torneo('Campeonato de Primera B 2010-11 (Argentina)', 'Primera B', 2010,
           anio_fin=2011, espn=True),
    # Y esta: 12 fechadas de 279. Trajo diez clubes del interior que el padron
    # no tenia -- Lujan de Cuyo, Nunorco, La Plata FC, Atletico Candelaria... --
    # todos sacados del articulo que enlaza su propia tabla de participantes.
    Torneo('Torneo Argentino A 2005-06', 'Torneo Argentino A', 2005,
           anio_fin=2006, rsssf='arg3-int06'),
    # El primer torneo del repo cuyos partidos NO salen de Wikipedia. Su articulo
    # publica los participantes, la tabla final de cada zona y la fase final, y
    # ningun resultado fecha por fecha -- se comprobo catalogandola sin el flag,
    # que dio cero partidos --. RSSSF si los tiene, y `source` lo dice fila por
    # fila. La tabla de posiciones de Wikipedia sigue estando, asi que estas filas
    # pasan por el mismo cruce que todas las demas.
    # La mas flaca del corpus, y a proposito: de su fase de grupos Wikipedia
    # publica los resultados de UNA sola zona -- la Norte del Apertura -- y de las
    # otras siete nada mas que las tablas. RSSSF tampoco los tiene: su archivo trae
    # las tablas finales y las llaves, no la grilla. Asi que lo que entra son las
    # llaves de las dos Revalidas, las dos fases finales, la permanencia y las
    # promociones, mas esa unica zona. No se inventa el resto; queda anotado.
    Torneo('Torneo Argentino A 2004-05', 'Torneo Argentino A', 2004, anio_fin=2005),
    Torneo('Torneo Argentino A 2006-07', 'Torneo Argentino A', 2006,
           anio_fin=2007, rsssf='arg3-int07', sin_grilla=True),
    # La tercera sin grilla, y la que enseño a no dar por buena la analogia con la
    # anterior: sus `Group A` y `Group B` SI son dos zonas de 8 -- la Zona 1 y la
    # Zona 2 --, aunque cada bloque nombre 16 clubes. Los otros 8 son los rivales
    # del interzonal, que RSSSF imprime bajo los dos grupos. Lo zanja la cuenta de
    # partidos, no la de nombres: 112 + 112 + 32 + 144 = 400.
    Torneo('Torneo Argentino A 2007-08', 'Torneo Argentino A', 2007,
           anio_fin=2008, rsssf='arg3-int08', sin_grilla=True),
    # La segunda sin grilla, y la que enseño que la correspondencia de zonas no se
    # da por hecha: RSSSF la parte en `Zone 1`, `Zone 2` y `Zone 3`, pero sus dos
    # primeras son ETAPAS sobre los mismos 16 clubes y la pagina las reparte en dos
    # zonas de 8. Ver el mapa en `fad/rsssf.py`.
    Torneo('Torneo Argentino A 2008-09', 'Torneo Argentino A', 2008,
           anio_fin=2009, rsssf='arg3-int09', sin_grilla=True),
    # La cuarta sin grilla, y la primera con DOS torneos adentro: Apertura y
    # Clausura reparten los clubes distinto, asi que el mapa se forzo por (torneo,
    # zona) y despues se unio. Ver `fad/rsssf.py`.
    Torneo('Torneo Argentino A 2009-10', 'Torneo Argentino A', 2009,
           anio_fin=2010, rsssf='arg3-int2010', sin_grilla=True),

    Torneo('Campeonato de Primera C 2016 (Argentina)', 'Primera C', 2016),
    Torneo('Campeonato de Primera C 2016-17 (Argentina)', 'Primera C', 2016, anio_fin=2017),
    Torneo('Campeonato de Primera C 2017-18 (Argentina)', 'Primera C', 2017, anio_fin=2018),
    Torneo('Campeonato de Primera C 2018-19 (Argentina)', 'Primera C', 2018, anio_fin=2019),
    Torneo('Campeonato de Primera C 2019-20 (Argentina)', 'Primera C', 2019, anio_fin=2020),

    Torneo('Campeonato de Primera C 2021 (Argentina)', 'Primera C', 2021),
    Torneo('Campeonato de Primera C 2022 (Argentina)', 'Primera C', 2022),
    Torneo('Campeonato de Primera C 2023 (Argentina)', 'Primera C', 2023),

    Torneo('Torneo Federal A 2016', 'Torneo Federal A', 2016),
    Torneo('Torneo Federal A 2016-17', 'Torneo Federal A', 2016, anio_fin=2017),
    Torneo('Torneo Federal A 2017-18', 'Torneo Federal A', 2017, anio_fin=2018),
    Torneo('Torneo Federal A 2018-19', 'Torneo Federal A', 2018, anio_fin=2019),
    Torneo('Torneo Federal A 2019-20', 'Torneo Federal A', 2019, anio_fin=2020),

    Torneo('Torneo Federal A 2021', 'Torneo Federal A', 2021),
    Torneo('Torneo Federal A 2022', 'Torneo Federal A', 2022),
    Torneo('Torneo Federal A 2023', 'Torneo Federal A', 2023),

    # Los torneos de la pandemia: arrancaron en noviembre/diciembre de 2020 y
    # terminaron en 2021. Sin `anio_fin`, enero de 2021 quedaba once meses
    # antes del arranque -- lo agarro `validar.anios_bien_asignados`.
    Torneo('Campeonato Transición de Primera Nacional 2020', 'Primera Nacional', 2020, anio_fin=2021, mes_inicio=11),
    Torneo('Campeonato Transición de Primera B 2020 (Argentina)', 'Primera B', 2020, anio_fin=2021, mes_inicio=11),
    Torneo('Campeonato Transición de Primera C 2020 (Argentina)', 'Primera C', 2020, anio_fin=2021, mes_inicio=11),
    Torneo('Torneo Transición Federal A 2020', 'Torneo Federal A', 2020, anio_fin=2021, mes_inicio=11),
]

# La era Apertura/Clausura, 2004-2015. El parser no necesito un solo cambio: el
# formato de tabla es el mismo que el de hoy. Lo unico que crecio fue el padron.
VIEJO = [
    Torneo("Anexo:Torneo Apertura 2004 (Argentina)", "Primera Division - Apertura", 2004),
    Torneo("Anexo:Torneo Apertura 2005 (Argentina)", "Primera Division - Apertura", 2005),
    Torneo("Anexo:Torneo Apertura 2006 (Argentina)", "Primera Division - Apertura", 2006),
    Torneo("Anexo:Torneo Apertura 2007 (Argentina)", "Primera Division - Apertura", 2007),
    Torneo("Anexo:Torneo Apertura 2008 (Argentina)", "Primera Division - Apertura", 2008),
    Torneo("Anexo:Torneo Apertura 2009 (Argentina)", "Primera Division - Apertura", 2009),
    Torneo("Anexo:Torneo Apertura 2010 (Argentina)", "Primera Division - Apertura", 2010),
    Torneo("Anexo:Torneo Apertura 2011 (Argentina)", "Primera Division - Apertura", 2011),
    Torneo("Anexo:Torneo Clausura 2004 (Argentina)", "Primera Division - Clausura", 2004),
    Torneo("Anexo:Torneo Clausura 2005 (Argentina)", "Primera Division - Clausura", 2005),
    Torneo("Anexo:Torneo Clausura 2006 (Argentina)", "Primera Division - Clausura", 2006),
    Torneo("Anexo:Torneo Clausura 2007 (Argentina)", "Primera Division - Clausura", 2007),
    Torneo("Anexo:Torneo Clausura 2008 (Argentina)", "Primera Division - Clausura", 2008),
    Torneo("Anexo:Torneo Clausura 2009 (Argentina)", "Primera Division - Clausura", 2009),
    Torneo("Anexo:Torneo Clausura 2010 (Argentina)", "Primera Division - Clausura", 2010),
    Torneo("Anexo:Torneo Clausura 2011 (Argentina)", "Primera Division - Clausura", 2011),
    Torneo("Anexo:Torneo Clausura 2012 (Argentina)", "Primera Division - Clausura", 2012),

    # 2012-2014: el campeonato se llamo Inicial y Final. Tres de las cuatro
    # paginas rotulan sus 19 jornadas sin problema; la del Inicial 2012 no, y
    # cuelga los 190 partidos de un unico "Fecha 1". Esos entran igual, con
    # `matchday` vacio -- ver `build._borrar_jornadas_falsas`.
    Torneo("Anexo:Torneo Inicial 2012 (Argentina)", "Primera Division - Inicial", 2012),
    Torneo("Anexo:Torneo Final 2013 (Argentina)", "Primera Division - Final", 2013),
    Torneo("Anexo:Torneo Inicial 2013 (Argentina)", "Primera Division - Inicial", 2013),
    Torneo("Anexo:Torneo Final 2014 (Argentina)", "Primera Division - Final", 2014),
    Torneo("Campeonato de Primera División 2014 (Argentina)", "Primera Division", 2014),
    Torneo("Campeonato de Primera División 2015 (Argentina)", "Primera Division", 2015),
]

TODOS = ASCENSO_VIEJO + VIEJO + HISTORICO + PRIMERA + ASCENSO + ASCENSO_HISTORICO + COPAS

#!/usr/bin/env python3
"""Fechas copiadas a mano de una fuente citada, cuando ningun lector puede.

ES EL UNICO LUGAR DEL REPO DONDE UN DATO SE COPIA A MANO, y por eso conviene
decir con precision cuando corresponde y que lo sostiene.

SON DOS TABLAS Y NO PROMETEN LO MISMO. `FECHAS` le pone el dia a un partido que
la pagina ya trae, y de eso habla casi todo este docstring. `LLAVES` es mas: pone
el dia Y LA LOCALIA de los partidos de un cuadro que la pagina solo dibuja. Tiene
su contrato aparte, mas abajo, en `Pata`.

CUANDO CORRESPONDE. Solo cuando ninguna de las fuentes que el repo ya lee puede
dar esa fecha, y se comprobo. El Argentino A 2004-05 es el caso: Wikipedia
publica esos partidos sin dia, y RSSSF -- que es la unica otra fuente que trae
esa temporada -- la escribe en su formato COMPACTO, con las dos patas de cada
llave en un renglon y la fecha como un RANGO que las cubre a las dos. Un rango no
es una fecha. Se probaron los otros archivos de RSSSF para 2004-05 y no existen:
`arg3-int05` es el unico, y sus enlaces confirman que no hay hermano.

QUE LO SOSTIENE. Exactamente el mismo contrato que cualquier otro completador de
este repo: LOS CLUBES Y LA LLAVE IDENTIFICAN EL PARTIDO Y EL MARCADOR LO
VERIFICA. Estas filas entran por `fechas.completar` igual que las de RSSSF o las
de worldfootball, asi que una linea mal copiada no se cuela: no empareja, y se
avisa. Se midio antes de escribirlas -- las cincuenta y cinco identifican UNA sola
de nuestras filas, sin un ambiguo y sin un desacuerdo.

LA FUENTE ES UN BLOG, y eso es de otra categoria que RSSSF. Va igual, con
el credito puesto y con dos salvedades escritas: primero, de `FECHAS` sale la
FECHA y nada mas -- ni un marcador, ni una localia, ni un club --; segundo, si algun dia
una base de datos contradice esto, gana la base de datos. Lo que hace aceptable
al blog para este uso puntual es que publica cada partido con dia, sede y
goleadores, y que sus marcadores coinciden con los nuestros en los cincuenta y
cinco.

Y HAY UN TESTIGO, que es lo mas fuerte que se consiguio a favor de la fuente.
`Ben Hur 5-0 Talleres (P)`, primera ronda de la Revalida del Clausura: el blog lo
fecha el 03/04/2005 y la propia Wikipedia lo fecha el 2005-04-03. Las dos fuentes
llegan al mismo dia por caminos separados. Ese partido NO esta en la lista de
abajo, justamente porque no le falta la fecha; esta escrito aca porque es la
razon medible para creerle al blog en los que si le faltan.

Y HAY UN LIMITE, que conviene dejar escrito con el mismo cuidado. La vuelta de la
final de la Revalida del Apertura el blog la da 28/12 y 4-1; nuestra fila, la
pagina y el articulo del club dicen 26/12 y 2-0. No entra, y no hizo falta
decidirlo a mano: con ese marcador la cita no verifica y `completar` la habria
frenado sola. La ida, que si coincide, entra igual -- la confianza es por
partido y no por post.

EL POST ES LA FASE, y sin eso el par de clubes no identifica. Los mismos dos
clubes con el mismo resultado aparecen en dos torneos distintos: `Desamparados
1-0 Lujan de Cuyo` es la semifinal del Apertura del 01/12/2004 Y la segunda fecha
de la Zona Cuyo del Clausura del 22/01/2005. Buscar por par y marcador en todo el
blog da una fecha que parece unica y es de otro partido. Cada post cubre UNA fase
--`Apertura 2004 - 2da. Fase`, `Apertura 2004 - Reválida`, `Clausura 2005 - 2da.
Fase - Zona Campeonato`, `Clausura 2005 - 2da. Fase - Revalida`-- y se busca en
el de la llave de la fila, nada mas.

Y LA FUENTE PUEDE ERRARLE AL DIA aunque el marcador coincida. El blog escribe
`01/02/2004 en Rafaela: Ben Hur 2, Atletico Tucuman 1` entre un partido del
01/12/2004 y otro del 05/12/2004, en las semifinales de un torneo que empezo en
septiembre: los clubes y el marcador son los correctos y el dia esta diez meses
afuera. Por eso hay un test que exige que toda cita caiga en la ventana de su
temporada; ese partido NO entra, y sigue sin fecha.

LO QUE NO CUBRE. De los 57 partidos sin fecha de esa temporada, esto fecha 55.
Los 2 que quedan estan en `data/sin-fecha/`, que es donde tienen que estar: el de
la errata de arriba, y la vuelta de la final de la Revalida del Apertura, cuyo
marcador el blog da 4-1 contra el 2-0 de la pagina.

Un control mas, que no costo nada y vale: la llave de la fila que cada cita
engancha coincide con el POST del que se copio, en las treinta y seis. Si una
fecha del Clausura se hubiera pegado sobre un partido del Apertura, se veria ahi.

Citas literales, una por post, para que se vea la forma del dato:

    http://josecarluccio.blogspot.com/2013/09/argentina-consejo-federal-afa-torneo_1512.html
    "Argentina: Consejo Federal AFA - Torneo Argentino "A" - Apertura 2004 -
     1ra. Fase - Zona Norte"
    "12/09/2004 en San Miguel de Tucumán: Atlético Tucumán 2 (Martín Seri y
     Roberto Urbina), La Florida de Tucumán 0"

    http://josecarluccio.blogspot.com/2013/09/argentina-consejo-federal-afa-torneo_14.html
    "Argentina: Consejo Federal AFA - Torneo Argentino "A" - Apertura 2004 -
     2da. Fase"
    "20/11/2004 en Mar del Plata: Aldosivi de Mar del Plata 0, Luján de Cuyo de
     Mendoza 1"
"""
from __future__ import annotations

from dataclasses import dataclass

# Lo que se escribe en `source` de las filas cuya fecha salio de aca.
CREDITO = "http://josecarluccio.blogspot.com/"

# LA SEGUNDA FUENTE, para las fechas que la primera no da o da rotas. No se cree por
# ser segunda: se cree porque REPRODUCE A LA PRIMERA donde la primera esta bien. En la
# llave del Apertura 2004 publica las cuatro fechas y tres --05/12, 08/12 y 12/12--
# son exactamente las que ya estaban verificadas; la cuarta es justo donde la primera
# escribe un dia diez meses afuera. Y trae los goleadores de cada partido, que una
# lista de fixtures copiada no tiene.
CREDITO_SOYBH = "http://soybh.blogspot.com/p/argentino-200405.html"

# LA TERCERA, Y ES DE OTRA CATEGORIA: PRENSA DEL DIA. Pagina/12 esta digitalizado
# entero de 1987 a 2009 en la Hemeroteca Digital de la Biblioteca Nacional, con
# acceso libre y los PDF servidos sin login. No tiene OCR ni buscador de texto, asi
# que hay que ubicar el ejemplar por fecha y leer la pagina; por eso se usa sólo
# donde de verdad hace falta y no como fuente de volumen.
#
# ES LA UNICA CITA QUE LE GANA A UNA BASE DE DATOS. El resto de este modulo se
# escribio con la regla "si alguna vez una base de datos contradice esto, gana la
# base de datos", y esa regla vale para un blog. No vale para el diario del dia
# siguiente: ahi la base de datos es la reconstruccion posterior y el diario es el
# hecho. Ver el comentario del Apertura 1993, que es el caso.
CREDITO_P12 = "https://hemerotecadigital.bn.gob.ar/collection/001207768/pagina-12"

# Y UN ARCHIVO DE RSSSF QUE EL REPO NO SABE LEER. `arg2024` esta en el formato nuevo
# de la fuente --`<U>Round 19</U>:`, el club con su sigla adelante y el estadio en
# una tercera columna-- y no tiene ni lector ni mapa de nombres: escribirlos por UNA
# fecha seria el remedio peor que la enfermedad. Va la URL del archivo y no la del
# sitio, como en las `Dia` que citan a `arg2015` o `arg2020`: es lo que lleva a su
# autor, que es a quien el pie del archivo pide reconocer. Ver `LICENSE-DATOS.md`.
CREDITO_RSSSF_2024 = "https://www.rsssf.org/tablesa/arg2024.html"


@dataclass(frozen=True)
class Cita:
    """Un partido con su dia, como lo publica la fuente citada.

    El marcador va aunque no se use como dato: es lo que VERIFICA que la fecha es
    de este partido y no de otro. Sin el, copiar mal un nombre pondria una fecha
    ajena sin que nada lo dijera.
    """
    fecha: str            # ISO
    local: str            # ya en el nombre canonico del padron
    visita: str
    goles_local: int
    goles_visita: int
    llave: str = ""       # el cuadro, cuando hace falta para identificar
    # De que fuente salio ESTA cita. Vacio = la del modulo. Va por cita y no por
    # modulo porque una temporada puede necesitar dos, y el credito de una fecha no
    # se le puede poner a un blog que no la publico.
    fuente: str = ""

    # POR QUE LA LLAVE. El marcador VERIFICA pero no IDENTIFICA: la clave de
    # `fechas.completar` es (llave, jornada, local, visita). En una temporada con
    # Apertura y Clausura los playoffs vuelven a cruzar a los mismos dos clubes, y
    # sin la llave las dos filas caen en la misma casilla: la regla de colision se
    # lleva puestas a las DOS y no se completa ninguna. Aca pasaba con
    # Aldosivi-Lujan de Cuyo y con Atletico Tucuman-Douglas Haig, que se juegan en
    # los cuartos del Apertura y otra vez en los del Clausura. La llave separa los
    # cuadros y las treinta y seis vuelven a identificar una sola fila.


FECHAS: dict[str, tuple[Cita, ...]] = {
    # ------------------------------------------------------------------
    # UN SOLO PARTIDO, Y LO ZANJO EL DIARIO DEL DIA SIGUIENTE.
    #
    # Era el ultimo sin fecha de la capa 1991-1996. Las dos fuentes que el repo lee
    # coinciden en la ronda y en el 1-1 y se pelean en dos cosas: RSSSF lo pone con
    # BOCA DE LOCAL y bajo `[Mar 18, Fri]`, y la pagina lo pone con Gimnasia de local
    # y sin dia.
    #
    # La localia ya estaba probada sin salir de RSSSF: en el mismo archivo, la Round
    # 19 del Apertura 1993 y la del Clausura 1994 son el mismo fixture invertido, y
    # nueve de los diez cruces invierten prolijamente -- el unico que no es este. La
    # fuente se contradice a si misma en esa linea.
    #
    # EL DIA NO SE PODIA CERRAR con fuentes secundarias: tres decian sabado 19 y dos
    # decian viernes 18, y la jornada se jugo PARTIDA entre los dos dias, asi que
    # "la fecha fue el 19" no servia como argumento. Lo cerro Pagina/12:
    #
    #   * El ejemplar del SABADO 19 (Pagina/23) publica las formaciones de los
    #     partidos de ESE dia y ahi estan las dos: "Gimnasia: Lavallen; ... DT:
    #     Roberto Perfumo." y "Boca: Navarro Montoya; ... DT: Cesar Luis Menotti.
    #     Arbitro: Juan Carlos Crespi." En la misma pagina, la cronica del
    #     Huracan-Independiente del viernes dice que Independiente "debia ganar por
    #     una diferencia de tres goles y esperar que HOY perdieran River, Velez y
    #     Boca".
    #
    #   * El del DOMINGO 20 (Pagina/24) lo cuenta jugado: Boca "empatarle a Gimnasia
    #     recien sobre el final", el penal que "Juan Carlos Crespi" cobro y "Sergio
    #     Martinez" convirtio, el cabezazo de "Fabian `Picaro` Fernandez", las
    #     expulsiones de Acosta y Noriega, y el equipo "dirigido por Roberto Perfumo".
    #
    # Los dos goleadores, el arbitro, los dos expulsados y los dos tecnicos coinciden
    # con la ficha del partido. Y el diario lo dice de cuatro maneras en la misma
    # edicion: la cronica del viernes ("esperar que HOY perdieran River, Velez y
    # Boca"), las formaciones con su arbitro, el aviso de que el campeonato "hoy
    # llegara a su fin", y que Canal 13 transmitiria "con conexiones con Liniers y LA
    # PLATA" -- que son las canchas de Velez y de Gimnasia.
    #
    # HAY UNA FUENTE BUENA QUE DICE VIERNES 18, y conviene dejarla anotada para que
    # el que la encuentre no crea que esto se escribio sin verla. `gelp.org`, el
    # archivo estadistico de Gimnasia, publica la ficha mas completa que existe de
    # este partido -- estadio con direccion, arbitro, recaudacion ($ 111.014),
    # publico (8812), formaciones con suplentes, los dos DT, el gol de Fernandez a
    # los 42' CON la asistencia de Stremiz, el penal de Martinez a los 41' del
    # segundo tiempo y los dos expulsados CON MINUTO -- y la fecha con "18-03-1994
    # (Viernes)".
    #
    # No gana, por tres razones y en este orden:
    #
    #   1. Es reconstruccion posterior y el diario es contemporaneo. Un archivo de
    #      club se arma anios despues; el diario del sabado anuncia el partido de esa
    #      tarde y el del domingo lo cuenta jugado.
    #   2. `gelp.org` DECLARA usar material de RSSSF entre sus fuentes, y RSSSF es
    #      justamente quien fecha este partido el 18. Que gelp corrija la localia que
    #      RSSSF tiene mal no prueba que no le haya tomado el dia: el estadio es suyo
    #      y el dia no.
    #   3. Tiene al menos otra discrepancia de fecha con RSSSF en esta misma
    #      temporada -- el Gimnasia-Mandiyu, que gelp fecha 24/06 y RSSSF 24/07 --,
    #      asi que sus dias no son infalibles.
    #
    # Lo que gelp aporta y nadie mas tiene son los DETALLES del partido, y esos no se
    # discuten: coinciden con el diario en todo lo que los dos publican.
    # ------------------------------------------------------------------
    "Anexo:Torneo Apertura 1993 (Argentina)": (
        Cita("1994-03-19", "Gimnasia y Esgrima (LP)", "Boca Juniors", 1, 1,
             fuente=CREDITO_P12),
    ),

    # ------------------------------------------------------------------
    # UN SOLO PARTIDO, Y LA PAGINA NO LE PUSO NUNCA EL DIA. La fila de `Luján 3-1
    # Victoriano Arenas`, Fecha 19 del Clausura, tiene las celdas de fecha y de hora
    # vacias desde la revision que la agrego (oldid 163591579, del 15/11/2024) hasta
    # la ultima: no hay revision vieja de la que sacarlo.
    #
    # RSSSF lo trae, en `arg2024`, seccion de la Primera C, Torneo Clausura:
    #
    #     <U>Round 19</U>:
    #     [Oct 26, Sat]
    #     Club Luján                3- 1      CA Victoriano Arenas      Primero de Abril, Luján, B
    #
    # Mismo local, mismo 3-1 y la misma cancha que publica la pagina (1.º de Abril).
    # El 26 de octubre de 2024 fue sabado.
    #
    # Y HAY UN TESTIGO DEL DIA, que no es RSSSF ni lo copia: la cronica de Solo
    # Ascenso, publicada esa misma noche (26/10/2024, 22:42), cuenta que el partido se
    # jugo «este sábado» en el 1ro de Abril, por la fecha 19 del Clausura, y que
    # Victoriano perdio 3-1.
    # https://www.soloascenso.com.ar/notas/victoriano-arenas/victoriano-no-hizo-pie-como-visitante-ante-lujan/208440
    # No va en el credito: es prensa con todos los derechos reservados, y alcanza con
    # RSSSF, que autoriza la copia reconociendo al autor.
    #
    # La llave no hace falta para identificar --el otro cruce del anio, el del
    # Apertura, es con la localia al reves: `CA Victoriano Arenas 0- 1 Club Luján`-- y
    # va igual, porque dice de que torneo es la cita.
    # ------------------------------------------------------------------
    "Campeonato de Primera C 2024 (Argentina)": (
        Cita("2024-10-26", "Luján", "Victoriano Arenas", 3, 1, "Torneo Clausura",
             fuente=CREDITO_RSSSF_2024),
    ),

    "Torneo Argentino A 2004-05": (
        # La fase regular de la Zona Norte, fecha por fecha. La 7 y la 9 se
        # jugaron partidas en dos dias, y la fuente lo dice asi.
        Cita("2004-09-12", "Atlético Tucumán", "La Florida", 2, 0, "Torneo Apertura"),
        Cita("2004-09-12", "Talleres (P)", "Ñuñorco", 1, 2, "Torneo Apertura"),
        Cita("2004-09-19", "La Florida", "Gimnasia y Tiro (S)", 1, 0, "Torneo Apertura"),
        Cita("2004-09-19", "Ñuñorco", "Atlético Tucumán", 1, 2, "Torneo Apertura"),
        Cita("2004-09-26", "Atlético Tucumán", "Talleres (P)", 2, 3, "Torneo Apertura"),
        Cita("2004-09-26", "Gimnasia y Tiro (S)", "Ñuñorco", 1, 0, "Torneo Apertura"),
        Cita("2004-10-03", "Talleres (P)", "Gimnasia y Tiro (S)", 0, 0, "Torneo Apertura"),
        Cita("2004-10-03", "Ñuñorco", "La Florida", 2, 1, "Torneo Apertura"),
        Cita("2004-10-10", "Gimnasia y Tiro (S)", "Atlético Tucumán", 2, 1, "Torneo Apertura"),
        Cita("2004-10-10", "La Florida", "Talleres (P)", 2, 1, "Torneo Apertura"),
        Cita("2004-10-17", "La Florida", "Atlético Tucumán", 0, 2, "Torneo Apertura"),
        Cita("2004-10-17", "Ñuñorco", "Talleres (P)", 1, 0, "Torneo Apertura"),
        Cita("2004-10-22", "Gimnasia y Tiro (S)", "La Florida", 2, 0, "Torneo Apertura"),
        Cita("2004-10-24", "Atlético Tucumán", "Ñuñorco", 2, 0, "Torneo Apertura"),
        Cita("2004-10-31", "Talleres (P)", "Atlético Tucumán", 0, 0, "Torneo Apertura"),
        Cita("2004-10-31", "Ñuñorco", "Gimnasia y Tiro (S)", 0, 1, "Torneo Apertura"),
        Cita("2004-11-05", "Gimnasia y Tiro (S)", "Talleres (P)", 2, 3, "Torneo Apertura"),
        Cita("2004-11-06", "La Florida", "Ñuñorco", 0, 1, "Torneo Apertura"),
        Cita("2004-11-14", "Atlético Tucumán", "Gimnasia y Tiro (S)", 4, 2, "Torneo Apertura"),
        Cita("2004-11-14", "Talleres (P)", "La Florida", 4, 0, "Torneo Apertura"),
        # El Zona Campeonato del Apertura: los cuatro cuartos de ida del segundo
        # post, y del mismo post las vueltas, las semis y la final.
        Cita("2004-11-20", "Aldosivi", "Luján de Cuyo", 0, 1,
             "Torneo Apertura - Zona Campeonato"),
        Cita("2004-11-21", "Desamparados", "Cipolletti", 2, 0,
             "Torneo Apertura - Zona Campeonato"),
        Cita("2004-11-21", "Douglas Haig", "Atlético Tucumán", 3, 1,
             "Torneo Apertura - Zona Campeonato"),
        Cita("2004-11-27", "Atlético Tucumán", "Douglas Haig", 4, 0,
             "Torneo Apertura - Zona Campeonato"),
        Cita("2004-11-27", "Ben Hur", "Talleres (P)", 3, 1,
             "Torneo Apertura - Zona Campeonato"),
        Cita("2004-11-28", "Cipolletti", "Desamparados", 0, 1,
             "Torneo Apertura - Zona Campeonato"),
        # LA IDA DE ESTA SEMIFINAL NO LA DA LA FUENTE DEL MODULO, que le erra al dia
        # por diez meses --`01/02/2004` en un torneo que empezo en septiembre-- y por
        # eso el test de la ventana de temporada la frenaba, con razon. La segunda
        # fuente publica las cuatro fechas de esta llave y tres coinciden EXACTO con
        # las que ya estaban verificadas: es la de abajo, la del 08/12 y la del 12/12.
        # Discrepa solo donde la primera esta visiblemente rota. Ver `CREDITO_SOYBH`.
        Cita("2004-12-01", "Ben Hur", "Atlético Tucumán", 2, 1,
             "Torneo Apertura - Zona Campeonato", fuente=CREDITO_SOYBH),
        Cita("2004-12-05", "Atlético Tucumán", "Ben Hur", 2, 2,
             "Torneo Apertura - Zona Campeonato"),
        # La final del Apertura la suspendieron a los 41 del segundo tiempo por
        # invasion del publico, con el 3-0 puesto, y el resultado quedo. Eso lo
        # cuenta la fuente; de aca sale la fecha igual que en todas las demas.
        Cita("2004-12-12", "Ben Hur", "Desamparados", 3, 0,
             "Torneo Apertura - Zona Campeonato"),
        # El Zona Revalida del Apertura, del tercer post. Las dos de Candelaria se
        # jugaron en cancha de Guarani Antonio Franco de Posadas, dice la fuente;
        # no se toca `neutral`, que en este repo sale del REGLAMENTO y no del
        # estadio, asi que una mudanza puntual no lo cambia.
        Cita("2004-12-15", "Atlético Candelaria", "Desamparados", 2, 2,
             "Torneo Apertura - Zona Reválida"),
        Cita("2004-12-15", "Atlético Tucumán", "Luján de Cuyo", 0, 0,
             "Torneo Apertura - Zona Reválida"),
        Cita("2004-12-22", "Atlético Candelaria", "Luján de Cuyo", 1, 0,
             "Torneo Apertura - Zona Reválida"),
        # La vuelta, que estuvo en `sin-fecha/` hasta que se arbitro su marcador.
        # El blog la da 4-1 con los cinco goleadores y la pagina 2-0; gano el blog
        # --ver el `Marcador` en `correcciones`-- y recien ahi el marcador pudo
        # VERIFICAR el emparejamiento, que es lo que esta cita necesita para
        # aplicarse. `correcciones.aplicar` corre antes que este completador, asi
        # que cuando le toca el turno la fila ya dice 4-1.
        Cita("2004-12-28", "Luján de Cuyo", "Atlético Candelaria", 4, 1,
             "Torneo Apertura - Zona Reválida"),
        # Y el Zona Campeonato del Clausura, del cuarto post.
        Cita("2005-04-03", "Aldosivi", "Juventud Unida Universitario", 5, 2,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-04-03", "Atlético Tucumán", "Douglas Haig", 3, 0,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-04-10", "Atlético Tucumán", "Unión (S)", 2, 3,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-04-17", "Aldosivi", "Luján de Cuyo", 3, 1,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-04-24", "Aldosivi", "Unión (S)", 3, 0,
             "Torneo Clausura - Zona Campeonato"),

        # Y las diecinueve patas que faltaban, de los MISMOS cuatro posts. Estaban
        # ahi desde el principio: lo que fallaba era el emparejamiento, no la
        # fuente. Ver "EL POST ES LA FASE" arriba.
        Cita("2004-11-21", "Talleres (P)", "Ben Hur", 0, 1,
             "Torneo Apertura - Zona Campeonato"),
        Cita("2004-11-28", "Luján de Cuyo", "Aldosivi", 3, 1,
             "Torneo Apertura - Zona Campeonato"),
        Cita("2004-12-01", "Desamparados", "Luján de Cuyo", 1, 0,
             "Torneo Apertura - Zona Campeonato"),
        Cita("2004-12-08", "Desamparados", "Ben Hur", 0, 1,
             "Torneo Apertura - Zona Campeonato"),
        Cita("2004-12-19", "Desamparados", "Atlético Candelaria", 1, 2,
             "Torneo Apertura - Zona Reválida"),
        Cita("2004-12-19", "Luján de Cuyo", "Atlético Tucumán", 1, 0,
             "Torneo Apertura - Zona Reválida"),
        Cita("2005-03-27", "Douglas Haig", "Atlético Tucumán", 1, 1,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-03-27", "Guillermo Brown", "Luján de Cuyo", 1, 0,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-03-27", "Juventud Unida Universitario", "Aldosivi", 1, 0,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-03-27", "La Florida", "Unión (S)", 3, 1,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-04-03", "Luján de Cuyo", "Guillermo Brown", 3, 1,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-04-03", "Unión (S)", "La Florida", 2, 0,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-04-10", "Luján de Cuyo", "Aldosivi", 1, 2,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-04-17", "Unión (S)", "Atlético Tucumán", 1, 0,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-05-01", "Unión (S)", "Aldosivi", 2, 2,
             "Torneo Clausura - Zona Campeonato"),
        Cita("2005-05-08", "Douglas Haig", "Unión (S)", 3, 0,
             "Torneo Clausura - Zona Reválida"),
        Cita("2005-05-08", "Luján de Cuyo", "Atlético Tucumán", 0, 0,
             "Torneo Clausura - Zona Reválida"),
        Cita("2005-05-15", "Atlético Tucumán", "Luján de Cuyo", 2, 2,
             "Torneo Clausura - Zona Reválida"),
        Cita("2005-05-15", "Unión (S)", "Douglas Haig", 2, 1,
             "Torneo Clausura - Zona Reválida"),
    ),
}


def ajenos(pagina: str) -> list:
    """Las citas de `pagina` como `Ajeno`, para que las coma `fechas.completar`.

    `jornada=0` a proposito: la fuente rotula sus
    fechas de otra manera que la pagina -- "1ra. Fase" contra "Fecha 1" -- asi que
    el identificador es el par de clubes MAS LA LLAVE. En una liga de ida y vuelta
    cada par se cruza una vez en cada cancha, pero una temporada con Apertura y
    Clausura los vuelve a cruzar en los playoffs de las dos; la llave separa los
    cuadros y la regla de colision de `completar` sigue puesta para lo que aun asi
    no identifique uno solo.
    """
    from fad.fechas import Ajeno

    return [Ajeno(fecha=c.fecha, jornada=0, llave=c.llave, fuente=c.fuente,
                  local=c.local, visita=c.visita,
                  goles_local=c.goles_local, goles_visita=c.goles_visita)
            for c in FECHAS.get(pagina, ())]


# --------------------------------------------------------------------------
# LLAVES: el cuadro que la pagina dibuja y ninguna fuente que el repo lee trae.
# --------------------------------------------------------------------------
@dataclass(frozen=True)
class Pata:
    """Un partido de una llave que la pagina publica SOLO COMO CUADRO.

    Un cuadro dice que dos clubes se cruzaron y como salio cada pata. No dice que
    dia ni quien fue local, y sin eso no hay fila: ver `parser.cruces_del_cuadro`,
    que por eso mismo es un testigo y no una fuente de filas. Cuando RSSSF trae la
    llave, la localia y el dia salen de ahi (`Torneo.rsssf_llaves`). Esto es para
    el cuadro que RSSSF no trae.

    DE LA FUENTE CITADA SALEN DOS COSAS: EL DIA Y QUIEN FUE LOCAL. Los clubes y el
    marcador se escriben aca porque una fila los necesita, pero no se le creen a
    la fuente: los tiene que decir el cuadro de la pagina. `segun_el_cuadro` deja
    afuera la llave cuyo cruce el cuadro no publica o publica con otros marcadores,
    pata por pata y en orden --la ida primero--, asi que tampoco pasa una cita con
    las dos fechas cruzadas. Un digito mal copiado no entra: se avisa.

    Es MAS de lo que `FECHAS` se permite --alla sale la fecha y nada mas-- y por eso
    pide mas. Para escribir una pata hace falta, de afuera de la fuente citada:

      * un testigo del DIA que no sea ella, y
      * un testigo de la LOCALIA que no sea ella, o decir en el comentario que no
        lo hay y que la sostiene.

    El credito va por pata y es obligatorio: no hay default. Lo que queda en
    `source` es la URL de donde se copio.
    """
    fecha: str            # ISO
    local: str            # ya en el nombre canonico del padron
    visita: str
    goles_local: int
    goles_visita: int
    ronda: str            # va a `matchday`, escrita como en el resto del dataset
    llave: str            # que cuadro de la pagina es
    fuente: str           # la URL de donde se copio; va a `source`


# El post del blog de Jose Carluccio con el Reducido de la Primera C 2011-12:
# `Argentina: 1ra. "C" AFA 2011/12 - Torneo Reducido por la Promoción`.
_REDUCIDO_C_2011 = ("http://josecarluccio.blogspot.com/2015/07/"
                    "argentina-1ra-c-afa-201112-torneo.html")


def _c2011(fecha: str, local: str, goles_local: int, goles_visita: int,
           visita: str, ronda: str) -> Pata:
    return Pata(fecha, local, visita, goles_local, goles_visita, ronda,
                llave="Reducido", fuente=_REDUCIDO_C_2011)


LLAVES: dict[str, tuple[Pata, ...]] = {
    # ------------------------------------------------------------------
    # EL REDUCIDO DE LA PRIMERA C 2011-12: catorce partidos, siete llaves.
    #
    # La pagina lo trae como `{{Copa de 8 clubes}}` y nunca lo tuvo de otra forma.
    # RSSSF no cubre esta temporada de la categoria: `arg2012` llega hasta la
    # Primera B Metropolitana, y su indice del cuarto nivel deja 2011/12 sin enlace.
    # Estas filas salian del feed de ESPN, que se saco del repo: sus condiciones no
    # autorizan a extraer contenido para armar una base de datos.
    #
    # LO QUE DICE LA PAGINA, que es lo que `segun_el_cuadro` exige: los siete
    # cruces con el marcador de la ida y el de la vuelta, y en la cabecera del
    # cuadro cuando se jugo cada ronda --cuartos del 28 de mayo al 3 de junio,
    # semifinal del 6 al 10 de junio, final el 17 y el 21 de junio--.
    #
    # LO QUE SALE DEL BLOG: el dia de cada partido y quien fue local. El post los
    # publica uno por uno, con la ciudad y los goleadores:
    #
    #     "28/05/2012 en Libertad: Ferrocarril Midland 4 (Diego Figueroa 3 y Néstor
    #      Villalba), Defensores de Cambaceres 1 (Sergio Valenti)"
    #
    # Los catorce marcadores del post son los del cuadro, y los catorce dias caen
    # en la ronda que dice la cabecera.
    #
    # EL TESTIGO DEL DIA es el historial de la propia pagina, que se editaba en vivo:
    # cada marcador entro al cuadro a las pocas horas de jugado. En hora argentina:
    #
    #     28/05 17:54   Midland 4-1 Cambaceres y Dock Sud 1-0 J. J. de Urquiza
    #     28/05 23:22   Central Córdoba 1-1 Laferrere       (rev 56569780)
    #     29/05 17:05   Berazategui 1-1 UAI Urquiza         (rev 56587212)
    #     03/06 16:57   las cuatro vueltas de cuartos       (rev 56718847)
    #     06/06 16:03   Berazategui 0-1 Central Córdoba     (rev 56797455)
    #     06/06 17:33   Midland 1-0 Dock Sud                (rev 56799618)
    #     09/06 14:13   Dock Sud 0-0 Midland                (rev 56870468)
    #     10/06 18:55   Central Córdoba 1-0 Berazategui     (rev 56904602)
    #     17/06 17:04   Midland 1-2 Central Córdoba         (rev 57093286)
    #     22/06 00:35   Central Córdoba 0-0 Midland         (rev 57213538)
    #
    # El ultimo es el del jueves 21 a las 21: se cargo pasada la medianoche.
    #
    # EL UNICO DIA CON UNA FUENTE EN CONTRA es el de Berazategui-UAI Urquiza. El
    # blog `Rumores del Ascenso` publico el 25/05 la programacion de la ida con los
    # cuatro partidos el lunes 28, ese a las 14. Se jugo el martes 29: a las 23:22
    # del 28 el cuadro ya tenia los otros tres marcadores y ese casillero seguia
    # vacio, y se lleno el 29 a las 17:05. Una programacion dice cuando se iba a
    # jugar, no cuando se jugo.
    # http://rumoresdelascenso.blogspot.com/2012/05/reducido-de-primera-c-comienza-el.html
    #
    # LA LOCALIA TIENE TESTIGO EN DOCE DE LAS CATORCE, y son programaciones y
    # previas de esos dias, que escriben al local primero:
    #
    #   * las cuatro idas de cuartos, en la programacion de arriba: `Berazategui-UAI
    #     Urquiza (en Villa San Carlos)`, `Midland-Defensores de Cambaceres`, `Dock
    #     Sud-J.J. Urquiza`, `Central Córdoba-Deportivo Laferrere`;
    #   * las cuatro vueltas, `Domingo 3 de junio`: `UAI Urquiza-Berazategui`,
    #     `Defensores de Cambaceres-Midland (en Talleres R.E.)`, `J.J. Urquiza-Dock
    #     Sud`, `Laferrere-Central Cordoba`.
    #     http://rumoresdelascenso.blogspot.com/2012/05/vuelta-de-4tos-de-final-del-reducido-de.html
    #   * la semifinal de Central Córdoba, en Pagina/12 Rosario del miercoles 6 de
    #     junio: `Cancha: Talleres de Remedios de Escalada (local Berazategui)`, y
    #     la vuelta `en el Gabino Sosa el domingo a las 15`.
    #     https://www.pagina12.com.ar/diario/suplementos/rosario/11-34108-2012-06-06.html
    #   * la final: `Domingo 17 de junio 15.00-- Midland-Central Córdoba` y `Jueves
    #     21 de junio 21.00-- Central Córdoba-Midland`.
    #     http://rumoresdelascenso.blogspot.com/2012/06/finales-reducidas.html
    #
    # LAS DOS QUE NO LO TIENEN son las de la semifinal Midland-Dock Sud, y conviene
    # decirlo: fuera del post no se encontro quien escriba en que cancha se jugo
    # cada una. Las sostiene la regla del torneo, que Pagina/12 enuncia en esa misma
    # nota para la otra semifinal --el que tiene la ventaja deportiva juega la
    # vuelta en su cancha--: Dock Sud termino septimo con 54 puntos y Midland
    # octavo con 53, y la regla se cumple en las otras seis llaves, que si tienen
    # testigo. Hay dos indicios mas, que no llegan a prueba: `Rumores del Ascenso`
    # escribio el 13/06 `Dock Sud-Midland igualaron 0-0`, con Dock Sud primero, que
    # es como ese blog nombra al local en sus programaciones; y en el historial de la
    # pagina el club de arriba del cuadro era el local de la ida en las cinco llaves
    # que si tienen testigo, y en la revision 56799618 Midland va arriba de Dock Sud.
    # Si aparece una cronica que diga lo contrario, gana la cronica.
    #
    # SE MIDIO ANTES DE CREERLE, sobre la fase regular de esta misma temporada, que
    # el blog publica en otro post: de 377 partidos leidos, los 377 marcadores son
    # los de la grilla de la pagina y 375 dias tambien. No es un espejo de la
    # pagina --del Reducido la pagina no tiene ni el dia ni la localia que
    # copiarle-- y tampoco es infalible: es una transcripcion a mano, y en ese otro
    # post hay un partido con el mes mal tipeado (`20/12/2011` por 20/10). Y este
    # mismo post tiene un error propio, que no toca ninguna fila: su lista de
    # `Participantes` nombra a Leandro N. Alem, que ese anio descendio, y se olvida de
    # Ferrocarril Midland, que jugo la final; los renglones de los partidos si dicen
    # Midland. Por eso cada dia de aca tiene su testigo aparte.
    #
    # LO QUE NO SE GANA: el blog da la ciudad y no el estadio, asi que `venue` sigue
    # vacio. Tres partidos se jugaron en cancha ajena y a puertas cerradas --
    # Berazategui-UAI Urquiza en Villa San Carlos; Cambaceres-Midland y
    # Berazategui-Central Córdoba en Talleres de Remedios de Escalada--; el local
    # es el que figura, que es como los programo la AFA.
    # ------------------------------------------------------------------
    "Campeonato de Primera C 2011-12 (Argentina)": (
        _c2011("2012-05-28", "Ferrocarril Midland", 4, 1, "Defensores de Cambaceres",
               "Cuartos de final"),
        _c2011("2012-05-28", "Dock Sud", 1, 0, "J. J. de Urquiza", "Cuartos de final"),
        _c2011("2012-05-28", "Central Córdoba (R)", 1, 1, "Deportivo Laferrere",
               "Cuartos de final"),
        _c2011("2012-05-29", "Berazategui", 1, 1, "UAI Urquiza", "Cuartos de final"),
        _c2011("2012-06-03", "UAI Urquiza", 1, 3, "Berazategui", "Cuartos de final"),
        _c2011("2012-06-03", "Defensores de Cambaceres", 1, 0, "Ferrocarril Midland",
               "Cuartos de final"),
        _c2011("2012-06-03", "J. J. de Urquiza", 0, 1, "Dock Sud", "Cuartos de final"),
        _c2011("2012-06-03", "Deportivo Laferrere", 1, 3, "Central Córdoba (R)",
               "Cuartos de final"),
        _c2011("2012-06-06", "Berazategui", 0, 1, "Central Córdoba (R)", "Semifinal"),
        _c2011("2012-06-06", "Ferrocarril Midland", 1, 0, "Dock Sud", "Semifinal"),
        _c2011("2012-06-09", "Dock Sud", 0, 0, "Ferrocarril Midland", "Semifinal"),
        _c2011("2012-06-10", "Central Córdoba (R)", 1, 0, "Berazategui", "Semifinal"),
        _c2011("2012-06-17", "Ferrocarril Midland", 1, 2, "Central Córdoba (R)", "Final"),
        _c2011("2012-06-21", "Central Córdoba (R)", 0, 0, "Ferrocarril Midland", "Final"),
    ),
}


def llaves(pagina: str, torneo: str) -> list:
    """Las patas citadas de `pagina` como `Partido`, para el cedazo del build.

    Devuelve `Partido` y no `Ajeno` porque estas filas ENTRAN: `Ajeno` existe para
    ponerle la fecha a una fila que la pagina ya trae, que es lo que hace `ajenos`.
    Nacen con el credito puesto, igual que las llaves que salen de RSSSF.
    """
    from fad.parser import Partido

    return [Partido(fecha=p.fecha, local=p.local, visita=p.visita,
                    goles_local=p.goles_local, goles_visita=p.goles_visita,
                    torneo=torneo, fase="eliminacion", jornada=p.ronda,
                    llave=p.llave, fuente_fecha=p.fuente)
            for p in LLAVES.get(pagina, ())]


def segun_el_cuadro(patas: list, cruces: list) -> tuple[list, list[str]]:
    """(las patas que el cuadro de la pagina respalda, por que no entran las demas).

    `cruces` es lo que devuelve `posiciones.llaves_del_cuadro`: (clubA, clubB,
    [(goles de A, goles de B) de la ida, de la vuelta]).

    ES LA CONDICION PARA ENTRAR y va antes que todo lo demas. Una llave citada pone
    el dia y la localia; los clubes y el marcador son de la pagina, y esto es lo
    que hace que esa frase sea cierta y no una intencion. Se compara LA LLAVE
    ENTERA y EN ORDEN: las patas citadas de un cruce, puestas por fecha, tienen que
    ser exactamente las del cuadro, ida y vuelta. Si una no coincide no entra
    ninguna de las dos, porque lo que quedo en duda es la llave.

    Por que hace falta aunque ya exista `posiciones.marcadores_del_cuadro`: aquel
    pregunta si la grilla tiene ALGUN partido entre los dos clubes con el marcador
    que el cuadro publica, sin mirar cual pata es. En una llave que sale 1-0 y 0-1
    las dos patas son el mismo par de numeros, asi que romper una no lo hace
    hablar: la otra le alcanza. Medido sobre estos catorce partidos, sumandole un
    gol al local de a uno por vez: avisa en siete y calla en siete.
    """
    del_cuadro: dict = {}
    for a, b, marcadores in cruces:
        del_cuadro.setdefault(frozenset((a, b)), []).append((a, b, marcadores))
    por_cruce: dict = {}
    for p in patas:
        por_cruce.setdefault(frozenset((p.local, p.visita)), []).append(p)

    afuera, avisos = set(), []
    for cruce, suyas in por_cruce.items():
        nombres = " vs ".join(sorted(cruce))
        publicados = del_cuadro.get(cruce, [])
        if len(publicados) != 1:
            afuera.add(cruce)
            avisos.append(
                f"{nombres}: el cuadro de la pagina "
                + ("no publica ese cruce" if not publicados
                   else f"publica ese cruce {len(publicados)} veces")
                + f"; no entra ninguna de sus {len(suyas)} patas citadas")
            continue
        a, b, marcadores = publicados[0]
        citadas = [(p.goles_local, p.goles_visita) if p.local == a
                   else (p.goles_visita, p.goles_local)
                   for p in sorted(suyas, key=lambda p: p.fecha)]
        if citadas != [tuple(m) for m in marcadores]:
            afuera.add(cruce)
            avisos.append(
                f"{a} vs {b}: el cuadro de la pagina publica "
                + ", ".join(f"{x}-{y}" for x, y in marcadores)
                + " y la cita " + ", ".join(f"{x}-{y}" for x, y in citadas)
                + " (ida y vuelta, en ese orden de clubes); no entra ninguna de las "
                  "dos patas hasta que se mire cual tiene razon")
    return [p for p in patas if frozenset((p.local, p.visita)) not in afuera], avisos

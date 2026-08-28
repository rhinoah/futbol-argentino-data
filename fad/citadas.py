#!/usr/bin/env python3
"""Fechas copiadas a mano de una fuente citada, cuando ningun lector puede.

ES EL UNICO LUGAR DEL REPO DONDE UN DATO SE COPIA A MANO, y por eso conviene
decir con precision cuando corresponde y que lo sostiene.

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
de ESPN, asi que una linea mal copiada no se cuela: no empareja, y se avisa. Se
midio antes de escribirlas -- las cincuenta y cinco identifican UNA sola de
nuestras filas, sin un ambiguo y sin un desacuerdo.

LA FUENTE ES UN BLOG, y eso es de otra categoria que RSSSF o ESPN. Va igual, con
el credito puesto y con dos salvedades escritas: primero, de aca sale la FECHA y
nada mas -- ni un marcador, ni una localia, ni un club --; segundo, si algun dia
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

    `jornada=0` a proposito, igual que el feed de ESPN: la fuente rotula sus
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

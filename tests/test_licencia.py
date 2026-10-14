"""`LICENSE-DATOS.md` contra lo que el dataset usa de verdad.

El pie de cada archivo de RSSSF autoriza a copiarlo «provided that proper
acknowledgement is given to the author», y el autor depende del archivo: el
reconocimiento vive en una tabla de `LICENSE-DATOS.md`, escrita a mano. Lo que estos
tests cuidan es que esa tabla no se quede atras del codigo: un archivo de RSSSF que
se sume al catalogo, o una fuente nueva que aparezca en la columna `source`, tienen
que estar nombrados ahi antes de que el cambio entre.

Lo que NO pueden mirar es que los nombres de los autores sean los del pie: los
archivos de RSSSF no se versionan (`.cache/`), asi que ese cotejo se hace a mano y
el archivo dice con que fecha.
"""
import csv
import re
from pathlib import Path

from fad import citadas, correcciones, dataset, rsssf

RAIZ = Path(__file__).resolve().parent.parent
LICENCIA = (RAIZ / "LICENSE-DATOS.md").read_text(encoding="utf-8")

_ARCHIVO_DE_RSSSF = re.compile(r"rsssf\.org/tablesa/([\w-]+)\.html")


def _archivos_de_rsssf_que_se_usan() -> set[str]:
    """Los del catalogo y los que cita a mano una fecha, corregida o puesta.

    Son dos listas a mano y no una: `correcciones.DIAS` pisa un dia que estaba mal y
    `citadas.FECHAS` le pone uno a la fila que no lo tenia. Las dos escriben la URL
    del archivo en el `source` de la fila, asi que las dos cuentan."""
    del_catalogo = {archivo for archivo, _ in rsssf.FUENTES.values()}
    fuentes = [d.fuente or "" for d in correcciones.DIAS]
    fuentes += [c.fuente for citas in citadas.FECHAS.values() for c in citas]
    citados = {m.group(1) for f in fuentes for m in [_ARCHIVO_DE_RSSSF.search(f)] if m}
    return del_catalogo | citados


def _sitio(url: str) -> str:
    return re.sub(r"^https?://(?:www\.)?([^/]+).*$", r"\1", url)


def test_cada_archivo_de_rsssf_que_se_usa_tiene_su_reconocimiento():
    """El testigo es el catalogo: `rsssf.FUENTES` dice de que archivo sale cada
    torneo, las `Dia` de que archivo salio cada fecha corregida a mano y las `Cita`
    de cual salio cada fecha puesta a mano. Son 28, y los 28 tienen que tener su
    renglon, con la URL que lleva a su autor."""
    usados = _archivos_de_rsssf_que_se_usan()
    assert len(usados) >= 28, "si son menos, este test dejo de mirar el catalogo"
    sin_renglon = sorted(a for a in usados
                         if f"https://www.rsssf.org/tablesa/{a}.html" not in LICENCIA)
    assert not sin_renglon, (
        f"LICENSE-DATOS.md no reconoce al autor de {sin_renglon}: el dataset usa esos "
        "archivos de RSSSF y su pie pide que se nombre a quien los hizo")


def test_la_tabla_no_reconoce_archivos_que_el_dataset_no_usa():
    """Al reves: un renglon por un archivo del que ya no sale nada le atribuye a su
    autor filas que no son suyas."""
    usados = _archivos_de_rsssf_que_se_usan()
    de_mas = sorted(set(_ARCHIVO_DE_RSSSF.findall(LICENCIA)) - usados)
    assert not de_mas, f"LICENSE-DATOS.md nombra {de_mas} y el dataset no los usa"


def test_toda_fuente_que_aparece_en_source_esta_nombrada_en_la_licencia():
    """El testigo es el dato publicado: cada sitio que una fila nombra despues del
    separador tiene que estar en `LICENSE-DATOS.md`, con lo que aporta. Antes de este
    test el archivo nombraba a una sola de las siete."""
    sitios = set()
    # `rglob` y no `glob`: `data/sin-fecha/` tambien es dato publicado -- la licencia
    # la nombra en su primer parrafo -- y ahi una fila puede traer credito sin tener
    # dia, que es como vivieron las llaves del Argentino A 2004-05 hasta fecharse.
    for ruta in sorted((RAIZ / "data").rglob("partidos-*.csv")):
        with open(ruta, encoding="utf-8", newline="") as f:
            for fila in csv.DictReader(f):
                for credito in fila["source"].split(dataset.SEPARADOR)[1:]:
                    sitios.add(_sitio(credito))
    assert "rsssf.org" in sitios, "si no esta, este test no leyo los datos"
    sin_nombrar = sorted(s for s in sitios if s not in LICENCIA)
    assert not sin_nombrar, (
        f"hay filas que nombran a {sin_nombrar} en `source` y LICENSE-DATOS.md no")


def test_cada_archivo_de_rsssf_que_una_fila_nombra_tiene_su_renglon():
    """El mismo cruce que el primero, con OTRO testigo: el dato publicado en vez del
    codigo. Una fila que escribe la URL de un archivo de RSSSF en `source` esta
    diciendo de quien es el dato, y el pie de ese archivo pide que se lo nombre.

    Hace falta porque el de arriba mira las listas que conoce. Cuando la fecha de
    `Luján 3-1 Victoriano Arenas` paso a salir de `arg2024` por una `Cita`, ese test
    seguia pasando sin el renglon: no sabia que `citadas.FECHAS` tambien cita
    archivos. Este no depende de saber por que camino entro."""
    archivos = set()
    for ruta in sorted((RAIZ / "data").rglob("partidos-*.csv")):
        with open(ruta, encoding="utf-8", newline="") as f:
            for fila in csv.DictReader(f):
                for credito in fila["source"].split(dataset.SEPARADOR)[1:]:
                    archivos.update(_ARCHIVO_DE_RSSSF.findall(credito))
    assert "arg2024" in archivos, "si no esta, este test no leyo los datos"
    sin_renglon = sorted(a for a in archivos
                         if f"https://www.rsssf.org/tablesa/{a}.html" not in LICENCIA)
    assert not sin_renglon, (
        f"hay filas que nombran a {sin_renglon} en `source` y LICENSE-DATOS.md no "
        "reconoce a su autor")
    de_otro_lado = sorted(archivos - _archivos_de_rsssf_que_se_usan())
    assert not de_otro_lado, (
        f"hay filas que nombran a {de_otro_lado} y ni el catalogo ni las listas a mano "
        "dicen de donde salen: `_archivos_de_rsssf_que_se_usan` se quedo corto")


def test_la_atribucion_sugerida_nombra_a_wikipedia_y_a_rsssf():
    """La cita que se le sugiere a quien reusa el dataset es lo que se va a copiar:
    si nombra solo a Wikipedia, RSSSF deja de estar reconocida un paso mas alla."""
    sugerida = LICENCIA.split("## Atribución sugerida", 1)[1].split("\n## ", 1)[0]
    cita = "\n".join(r for r in sugerida.splitlines() if r.startswith(">"))
    assert "es.wikipedia.org" in cita
    assert "rsssf.org" in cita

#!/usr/bin/env python3
"""Mutation testing casero: rompe el codigo a proposito y exige que la suite lo note.

Un mutante SOBREVIVIENTE es un cambio que rompe el comportamiento y que ningun
test detecta -- o sea, un agujero en la red.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

RAIZ = Path(__file__).resolve().parent

# (archivo, descripcion, texto original, texto mutado)
MUTANTES = [
    ("fad/parser.py", "no cortar entre tablas (el bug de las fechas corridas)",
     'for fila in re.split(r"\\n\\|-", _cortar_en_tablas(bloque)):',
     'for fila in re.split(r"\\n\\|-", bloque):'),

    ("fad/parser.py", "no ver la plantilla en plural {{Partidos}}",
     'r"\\{\\{\\s*Partidos?\\s*\\n"',
     'r"\\{\\{\\s*Partido\\s*\\n"'),

    ("fad/parser.py", "cerrar la plantilla en el primer cierre y no por balance",
     '            if texto.startswith("{{", i):\n                hondo, i = hondo + 1, i + 2',
     '            if False:\n                hondo, i = hondo + 1, i + 2'),

    ("fad/parser.py", "quedarse con una plantilla que nunca cierra",
     "        if hondo == 0:",
     "        if True:"),

    ("fad/validar.py", "aceptar penales en cualquier partido de eliminacion",
     '            and not (p.fase == "eliminacion" and _serie_igualada(p, ps))]',
     '            and p.fase != "eliminacion"]'),

    ("fad/validar.py", "dar por igualada una serie sin mirar el global",
     "    return a == b",
     "    return True"),

    ("fad/posiciones.py", "no decir de que lado esta el error",
     "    if desviados == 1:",
     "    if False:"),

    ("fad/posiciones.py", "usar filas de la tabla que no cierran solas",
     "        if gf - gc != dif or pg + pe + pp != pj:",
     "        if False:"),

    ("fad/posiciones.py", "comparar goles aunque no coincidan los partidos jugados",
     "        if pj != pj2:",
     "        if False:"),

    ("fad/posiciones.py", "sumar tambien los partidos de eliminacion",
     '        if p.fase != "zonas" or p.goles_local is None or p.goles_visita is None:',
     "        if p.goles_local is None or p.goles_visita is None:"),

    ("fad/posiciones.py", "denunciar a un club de la tabla que no jugo",
     "        if club not in contada:",
     "        if False:"),

    ("fad/fechas.py", "tomar la fecha de cualquier marcador distinto",
     "            if (p.jornada, p.local, p.visita) not in (arbitrados or ()):",
     "            if False:"),

    ("build.py", "no cruzar contra la tabla de posiciones",
     "               for d in posiciones.contrastar(ps, texto)]",
     "               for d in []]"),

    ("fad/correcciones.py", "aplicar un marcador arbitrado que ya no engancha",
     "        if len(candidatos) != 1:",
     "        if False:"),

    ("fad/parser.py", "no cortar en el cierre |} de tabla",
     'bloque = re.sub(r"\\n\\|\\}", "\\n|-", bloque)',
     'bloque = bloque'),

    ("fad/parser.py", "no reconocer 'Interzonal' como etiqueta de seccion",
     '                zona, ronda = _seccion(cab), ""',
     '                zona, ronda = (cab if re.match(r"(?i)(zona|grupo)", cab) else ""), ""'),

    ("fad/parser.py", "no unificar Interzonal/Interzonales",
     '    if re.match(r"(?i)^interzonal", cab):\n        return "Interzonal"',
     '    pass'),

    ("fad/parser.py", "ignorar el rowspan (asumir 6 celdas siempre)",
     "    return (int(n.group(1)) if n else 1), limpiar(m.group(2))",
     "    return 1, limpiar(m.group(2))"),

    ("fad/parser.py", "que un titulo NO corte la jornada",
     "        if _TITULO_CUALQUIERA.search(fila):",
     "        if False:"),

    ("fad/parser.py", "no limpiar el rowspan pendiente entre secciones",
     "            pendientes.clear()      # un rowspan no cruza de una seccion a otra",
     "            pass"),

    ("fad/parser.py", "leer los penales de los parentesis del entretiempo",
     '        pen = _marcador(limpiar(campos.get("resultado penalti", "")))',
     '        import re as _r; _m = _r.search(r"\\((\\d+)\\D+(\\d+)\\)", campos.get("resultado", "")); '
     'pen = (int(_m.group(1)), int(_m.group(2))) if _m else None'),

    ("fad/parser.py", "tomar el mes equivocado en la fecha",
     '    return f"{y}-{mes:02d}-{int(m.group(1)):02d}"',
     '    return f"{y}-{(mes % 12) + 1:02d}-{int(m.group(1)):02d}"'),

    ("fad/validar.py", "que el ganador de los penales sea el que perdio la tanda",
     "        return p.local if p.penales_local > p.penales_visita else p.visita",
     "        return p.local if p.penales_local < p.penales_visita else p.visita"),

    ("fad/validar.py", "no chequear que nadie juegue dos veces por fecha",
     "        repiten = [e for e, n in cuenta.items() if n > 1]",
     "        repiten = []"),

    ("fad/validar.py", "aceptar penales en partidos que no empataron",
     "            if p.penales_local is not None and p.goles_local != p.goles_visita",
     "            if False"),

    ("fad/validar.py", "no mirar si falta la zona",
     '    sin = [p for p in zonas if not p.zona]',
     "    sin = []"),

    # --- correr solo ---
    ("fad/dataset.py", "no mirar si el dataset se achico",
     "        if tenia_ahora < cuantos:",
     "        if False:"),

    ("fad/dataset.py", "comparar season como entero de un lado y texto del otro",
     '            clave = (f["tournament"], str(f["season"]))',
     '            clave = (f["tournament"], f["season"])'),

    ("fad/dataset.py", "no leer el CSV anterior (nunca hay con que comparar)",
     "    return leer(origen) if origen.exists() else []",
     "    return []"),

    ("build.py", "escribir igual aunque el dataset se haya achicado",
     "    if perdidos and not args.forzar:",
     "    if False:"),

    ("fad/wiki.py", "no reintentar cuando se corta la red",
     "        except urllib.error.URLError:\n            if intento == INTENTOS - 1:\n                raise",
     "        except urllib.error.URLError:\n            raise"),

    ("fad/wiki.py", "reintentar tambien los 404 (tarda mas en avisar y no sirve)",
     "            if e.code < 500 or intento == INTENTOS - 1:\n                raise",
     "            if intento == INTENTOS - 1:\n                raise"),

    # --- completar fechas desde la segunda fuente ---
    ("fad/fechas.py", "tomar el UTC sin convertir a hora argentina",
     "    return t.astimezone(ARGENTINA if hora_conocida else BERLIN).date().isoformat()",
     "    return t.date().isoformat()"),

    ("fad/fechas.py", "usar el mismo huso sepa o no sepa la hora",
     "    return t.astimezone(ARGENTINA if hora_conocida else BERLIN).date().isoformat()",
     "    return t.astimezone(ARGENTINA).date().isoformat()"),

    ("fad/fechas.py", "no mirar si el sitio conoce la hora del partido",
     "                                not _HORA_DESCONOCIDA.search(bloque)),",
     "                                True),"),

    ("fad/fechas.py", "volver a UTC-3 fijo, sin horario de verano",
     'ARGENTINA = ZoneInfo("America/Argentina/Buenos_Aires")',
     'from datetime import timedelta, timezone as _tz; ARGENTINA = _tz(timedelta(hours=-3))'),

    ("fad/fechas.py", "dejar que el ultimo ajeno pise al anterior",
     "            if k in indice:\n                chocados.add(k)",
     "            if False:\n                chocados.add(k)"),

    ("fad/fechas.py", "cachear cualquier respuesta, sea o no la pagina",
     '    if "data-match_id" not in texto:',
     "    if False:"),

    ("fad/fechas.py", "no contar el pedido que fallo para la pausa de cortesia",
     "    finally:\n        _ULTIMO = time.monotonic()",
     "    _ULTIMO = time.monotonic()"),

    ("fad/dataset.py", "buscar la pagina sin sacar el credito de la segunda fuente",
     '    return fila["source"].split(SEPARADOR, 1)[0]',
     '    return fila["source"]'),

    ("fad/validar.py", "contar como duplicados los partidos sin fecha",
     "    c = Counter((p.fecha, p.local, p.visita) for p in ps if p.fecha)",
     "    c = Counter((p.fecha, p.local, p.visita) for p in ps)"),

    ("build.py", "usar el mapa que la derivacion declaro inservible",
     "    puestos, mas = fechas.completar(ps, ajenos, {} if roto else mapa,",
     "    puestos, mas = fechas.completar(ps, ajenos, mapa,"),

    ("build.py", "aceptar una fecha importada fuera de la temporada",
     "    fuera = [p for p in ps if p.fuente_fecha and int(p.fecha[:4]) not in validos]",
     "    fuera = []"),

    ("fad/fechas.py", "no deduplicar los enlaces del mismo equipo",
     "        vistos.setdefault(id_eq, html.unescape(nombre).strip())",
     "        vistos[id_eq + str(len(vistos))] = html.unescape(nombre).strip()"),

    ("fad/fechas.py", "usar marcadores repetidos para deducir el padron",
     "            if cuenta_mia[k] != 1 or cuenta_suya[k] != 1:",
     "            if False:"),

    ("fad/fechas.py", "alcanzar con un solo voto para fijar un club",
     "        if favor < minimo:",
     "        if favor < 1:"),

    ("fad/fechas.py", "aceptar un club con una mayoria apenas ajustada",
     "        if contra * 4 > favor:",
     "        if contra > favor:"),

    ("fad/fechas.py", "no avisar cuando hubo votos en minoria",
     "        if contra:",
     "        if False:"),

    ("build.py", "consultar la segunda fuente para todos los torneos",
     "    avisos = _completar_fechas(ps, t) if t.wf else []",
     "    avisos = _completar_fechas(ps, t) if True else []"),

    ("build.py", "no completar las fechas de la segunda fuente",
     "    avisos = _completar_fechas(ps, t) if t.wf else []",
     "    avisos = []"),

    ("build.py", "frenar el build entero si la segunda fuente esta caida",
     '            f"{e}. Los partidos quedan sin fecha y no entran al dataset", grave=False)]',
     '            f"{e}. Los partidos quedan sin fecha y no entran al dataset")]'),

    ("build.py", "aplicar las correcciones a mano DESPUES de validar",
     "    arregladas, dudas = correcciones.aplicar(ps, t.pagina)",
     "    arregladas, dudas = 0, []"),

    ("build.py", "no avisar de una correccion que quedo sin efecto",
     '    avisos += [validar.Aviso("correccion que no aplica", d) for d in dudas]',
     "    avisos += []"),

    ("fad/correcciones.py", "corregir sin mirar el marcador",
     "                      and (p.goles_local, p.goles_visita) == (gl, gv)]",
     "                      ]"),

    ("fad/correcciones.py", "corregir sin mirar de que pagina es",
     "        if c.pagina != pagina:",
     "        if False:"),

    ("fad/correcciones.py", "corregir el primero cuando engancha con varios",
     "        if len(candidatos) > 1:",
     "        if False:"),

    ("fad/fechas.py", "leer el marcador de cualquier lado del bloque",
     "    celda = _CELDA_RESULTADO.search(bloque)",
     "    celda = re.match(r'(.*)', bloque, re.S)"),

    ("fad/validar.py", "no chequear que la localia se reparta",
     "            localias_repartidas, cadena_de_llaves]",
     "            cadena_de_llaves]"),

    ("fad/validar.py", "mirar la localia sin separar por zona",
     "        k = (p.llave, p.zona, tuple(sorted((p.local, p.visita))))",
     "        k = (p.llave, tuple(sorted((p.local, p.visita))))"),

    ("fad/validar.py", "contar tambien los partidos sin jornada",
     "        if p.fase != \"zonas\" or not p.jornada or not p.local or not p.visita:",
     "        if p.fase != \"zonas\" or not p.local or not p.visita:"),

    ("fad/parser.py", "dejar el superindice de la nota al pie pegado al nombre",
     "    return re.sub(r\"[\\u00b9\\u00b2\\u00b3\\u2070-\\u209f]+$\", \"\", s).strip()",
     "    return s"),

    ("fad/fechas.py", "completar aunque el marcador no coincida",
     "        if (a.goles_local, a.goles_visita) != (p.goles_local, p.goles_visita):",
     "        if False:"),

    ("fad/fechas.py", "pisar la fecha de los que ya la tienen",
     "        if p.fecha:\n            continue",
     "        if False:\n            continue"),

    ("fad/fechas.py", "no exigir que coincida la jornada",
     "            k = (a.jornada, el, ev)",
     "            k = (a.jornada, el, ev)\n"
     "            for _j in range(1, 60):\n"
     "                indice.setdefault((_j, el, ev), a)"),

    ("fad/fechas.py", "aceptar como temporada cualquier opcion del selector",
     '        m = _IDS.search(valor)',
     '        m = _IDS.search(valor) or re.search(r"(cy\d+)()", valor)'),

    ("fad/fechas.py", "confundir una competencia con una temporada",
     '        m = re.fullmatch(r"/competition/(co\d+)/", valor)',
     '        m = re.search(r"/(co\d+)/", valor)'),

    ("fad/fechas.py", "completar sin dejar el credito de la fuente",
     "        p.fuente_fecha = CREDITO",
     "        pass"),

    ("fad/dataset.py", "no nombrar la segunda fuente en source",
     '        "source": fuente + SEPARADOR + p.fuente_fecha if p.fuente_fecha else fuente,',
     '        "source": fuente,'),

    # --- el historico ---
    ("fad/parser.py", "pedir tres '=' en el titulo Resultados (9 temporadas en cero)",
     '_TITULO_RESULTADOS = re.compile(r"^(=+)\\s*Resultados\\s*=+\\s*$", re.M)',
     '_TITULO_RESULTADOS = re.compile(r"^(===+)\\s*Resultados\\s*=+\\s*$", re.M)'),

    ("fad/parser.py", "leer una sola seccion Resultados y no todas",
     "    fuera, hasta = [], 0",
     "    fuera, hasta = [], 10**9"),

    ("fad/parser.py", "contar dos veces una seccion Resultados anidada",
     "        if m.start() < hasta:\n            continue",
     "        if False:\n            continue"),

    ("fad/parser.py", "confundir la zona con la fase del torneo",
     "                      _contexto(m.start(), nivel, texto),\n"
     "                      _contexto(m.start(), min(nivel, 3), texto), cuerpo))",
     "                      _contexto(m.start(), nivel, texto),\n"
     "                      _contexto(m.start(), nivel, texto), cuerpo))"),

    ("fad/parser.py", "buscar la fase en un nivel igual o mayor al propio titulo",
     "                      _contexto(m.start(), min(nivel, 3), texto), cuerpo))",
     "                      _contexto(m.start(), 3, texto), cuerpo))"),

    ("fad/parser.py", "arrastrar la ronda de un cuadro al siguiente",
     "        if donde >= desde:          # solo las rondas de ESTE cuadro",
     "        if True:"),

    ("fad/validar.py", "no separar la fase al contar quien juega por fecha",
     "            c = porjornada.setdefault((p.llave, p.zona, p.jornada), Counter())",
     "            c = porjornada.setdefault((p.zona, p.jornada), Counter())"),

    ("fad/parser.py", "ignorar que la temporada cruza de anio",
     "    y = anio if (anio_fin is None or mes >= mes_inicio) else anio_fin",
     "    y = anio"),

    ("fad/parser.py", "corte de temporada fijo en agosto (la 2019-20 arranco en julio)",
     "    y = anio if (anio_fin is None or mes >= mes_inicio) else anio_fin",
     "    y = anio if (anio_fin is None or mes >= 8) else anio_fin"),

    ("fad/parser.py", "no leer la fecha que viene en {{fecha|D|M|Y}}",
     '            fecha=(_fecha_de_plantilla(campos.get("fecha", ""))\n'
     '                   or a_iso(limpiar(campos.get("fecha", "")), anio, anio_fin, mes_inicio)),',
     '            fecha=a_iso(limpiar(campos.get("fecha", "")), anio, anio_fin, mes_inicio),'),

    ("fad/parser.py", "tratar un enlace a archivo como si fuera texto",
     '    s = re.sub(r"\\[\\[\\s*(?:Archivo|File|Imagen|Image)\\s*:[^\\]]*\\]\\]", "", s, flags=re.I)',
     "    s = s"),

    ("fad/validar.py", "no mirar si faltan jornadas en el medio",
     "    faltan = [i for i in range(nums[0], nums[-1] + 1) if i not in nums]",
     "    faltan = []"),

    ("fad/validar.py", "no mirar si una jornada cae un anio fuera de lugar",
     "        if previo and _dias(medio, previo[1]) > 180:",
     "        if False:"),

    ("fad/validar.py", "quejarse de un torneo de zona unica",
     "    if not sin or len(sin) == len(zonas):",
     "    if not sin:"),

    # --- la copa ---
    ("fad/parser.py", "contar el bgcolor de la fila como si fuera una celda",
     "    return [c for c in partes[1:] if c.strip()]",
     "    return [c for c in partes if c.strip()]"),

    ("fad/parser.py", "no reconocer '||' como separador de celdas",
     '    partes = re.split(r"\\n\\|", "\\n" + fila.replace("||", "\\n|"))',
     '    partes = re.split(r"\\n\\|", "\\n" + fila)'),

    ("fad/parser.py", "sacar los penales DESPUES de limpiar la celda",
     '        pen = _penales(celdas[_COL_COPA.index("resultado")])',
     '        pen = _penales(v["resultado"])'),

    ("fad/parser.py", "borrar {{nowrap}} en vez de desenvolverla",
     '    s = re.sub(r"\\{\\{\\s*nowrap\\s*\\|(.*?)\\}\\}", r"\\1", s, flags=re.I | re.S)',
     "    s = s"),

    ("fad/parser.py", "no cortar la ronda en el proximo titulo (entra Goleadores)",
     "        fin = m.end() + (sig.start() if sig else len(texto) - m.end())",
     "        fin = len(texto)"),

    ("fad/parser.py", "que Semifinal y Semifinales sean dos rondas distintas",
     '    return "Semifinales" if n == "Semifinal" else n',
     "    return n"),

    ("fad/parser.py", "tomar la primera ronda de la pagina y no la que corresponde",
     "    ronda = \"\"\n    for donde, nombre in titulos:",
     "    return titulos[0][1] if titulos else \"\"\n    for donde, nombre in titulos:"),

    ("fad/parser.py", "ignorar el formato del catalogo y parsear todo como liga",
     '    if formato == "copa":',
     "    if False:"),

    ("fad/validar.py", "aceptar en una ronda a cualquiera que jugo la anterior",
     "        ganadores = {_ganador(p) for p in previa} - {\"\"}",
     "        ganadores = {p.local for p in previa} | {p.visita for p in previa}"),

    ("fad/validar.py", "saltear el chequeo del cuadro calladito",
     "    if grupos is None:\n        return [Aviso(",
     "    if grupos is None:\n        return []\n    if False:\n        return [Aviso("),

    ("fad/dataset.py", "escribir siempre neutral=false",
     '"neutral": str(neutral).lower()',
     '"neutral": "false"'),

    # --- el padron ---
    ("fad/equipos.py", "darle el alias 'Gimnasia' al club equivocado (el de Mendoza)",
     '    Equipo("Gimnasia y Esgrima (LP)", 8,\n'
     '           ("Gimnasia", "Gimnasia y Esgrima La Plata", "Gimnasia (LP)")),\n'
     '    Equipo("Gimnasia y Esgrima (M)", 816,\n'
     '           ("Gimnasia (Mendoza)", "Gimnasia (M)", "Gimnasia y Esgrima de Mendoza")),',
     '    Equipo("Gimnasia y Esgrima (LP)", 8,\n'
     '           ("Gimnasia y Esgrima La Plata", "Gimnasia (LP)")),\n'
     '    Equipo("Gimnasia y Esgrima (M)", 816,\n'
     '           ("Gimnasia", "Gimnasia (Mendoza)", "Gimnasia (M)", "Gimnasia y Esgrima de Mendoza")),'),

    ("fad/equipos.py", "no detectar un alias peleado por dos clubes",
     "            if clave in indice and indice[clave] is not eq:",
     "            if False:"),

    ("fad/equipos.py", "no unificar las comillas raras (Newell`s vs Newell's)",
     '    s = nombre.replace("`", "\'").replace("’", "\'").replace("´", "\'")',
     "    s = nombre"),

    ("fad/equipos.py", "no sacar los acentos al comparar",
     '    s = unicodedata.normalize("NFKD", s).encode("ascii", "ignore").decode()',
     "    s = s"),

    ("fad/equipos.py", "que un club desconocido pase como cadena vacia",
     "    return eq.nombre if eq else nombre",
     '    return eq.nombre if eq else ""'),

    ("fad/equipos.py", "que canonical devuelva el nombre en vez de levantar",
     "        raise EquipoDesconocido(nombre)",
     "        return nombre"),

    ("fad/validar.py", "no chequear que los clubes esten en el padron",
     "    raros = sorted({n for p in ps for n in (p.local, p.visita)\n"
     "                    if n and not equipos.conocido(n)})",
     "    raros = []"),

    ("fad/equipos.py", "resolver por el nombre visible y no por el articulo",
     "    if articulo:",
     "    if False:"),

    ("fad/parser.py", "aceptar un nombre visible que apunta a dos articulos",
     "    return {v: next(iter(d)) for v, d in vistos.items() if len(d) == 1}",
     "    return {v: next(iter(d)) for v, d in vistos.items()}"),

    ("build.py", "no normalizar los nombres antes de escribir",
     "        p.local = equipos.canonizar(p.local, p.local_art)\n"
     "        p.visita = equipos.canonizar(p.visita, p.visita_art)",
     "        pass"),

    # Simula el orden equivocado sin reordenar medio `procesar`: valida con los
    # nombres crudos y deja `revisar` devolviendo ESE resultado, que es lo que se
    # veria si el paso de normalizar corriera despues.
    ("build.py", "validar ANTES de normalizar (el orden de los pasos)",
     "    for p in ps:\n"
     "        p.local = equipos.canonizar(p.local, p.local_art)\n"
     "        p.visita = equipos.canonizar(p.visita, p.visita_art)\n",
     "    _antes = validar.revisar(ps)\n"
     "    for p in ps:\n"
     "        p.local = equipos.canonizar(p.local, p.local_art)\n"
     "        p.visita = equipos.canonizar(p.visita, p.visita_art)\n"
     "    validar.revisar = lambda _ps, _a=_antes: _a\n"),

    ("fad/dataset.py", "escribir el CSV sin ordenar",
     "    filas = sorted(filas, key=_orden)",
     "    filas = list(filas)"),

    # el mutante "escribir None en vez de cadena vacia" se saco: resulto
    # EQUIVALENTE. El modulo csv ya escribe None como campo vacio, asi que la
    # rama `"" if ... is None` no cambiaba el archivo. Se simplifico el codigo.
    ("build.py", "borrar la jornada de una fecha con solo un partido de mas",
     "        if len(partidos) > len(c) and any(v > 1 for v in c.values()):",
     "        if any(v > 1 for v in c.values()):"),

    ("build.py", "volver a bajar los torneos ya terminados",
     "        if t.cerrado and not args.rehacer and listas is not None:",
     "        if False:"),

    ("build.py", "reusar las filas por (torneo, temporada) y no por pagina",
     '        guardado.setdefault(dataset.pagina_de(f), []).append(f)',
     '        guardado.setdefault(f["tournament"], []).append(f)'),

    ("fad/dataset.py", "reescribir una temporada que no cambio",
     "        if destino.exists() and destino.read_bytes() == nuevo:\n            continue",
     "        if False:\n            continue"),

    ("fad/dataset.py", "meter todas las temporadas en un solo archivo",
     '        por_anio.setdefault(str(f["season"]), []).append(f)',
     '        por_anio.setdefault("todo", []).append(f)'),

    ("fad/dataset.py", "escribir el CSV sin encabezado",
     "        w.writeheader()",
     "        pass"),

    ("fad/dataset.py", "aceptar campos de mas en silencio",
     'extrasaction="raise",\n                           lineterminator',
     'extrasaction="ignore",\n                           lineterminator'),

    ("fad/dataset.py", "dejar que csv elija el final de linea (CRLF en Windows)",
     '                           lineterminator="\\n")',
     '                           )'),

    ("fad/dataset.py", "no validar el encabezado al leer",
     "    if filas and list(filas[0]) != COLUMNAS:",
     "    if False:"),
]


def correr_suite() -> bool:
    r = subprocess.run([sys.executable, "-m", "pytest", "tests/", "-q", "-x", "--no-header"],
                       cwd=RAIZ, capture_output=True, text=True)
    return r.returncode == 0


def main():
    if not correr_suite():
        print("La suite no pasa ANTES de mutar. Abortando.")
        return 1

    sobrevivientes = []
    for archivo, desc, viejo, nuevo in MUTANTES:
        ruta = RAIZ / archivo
        original = ruta.read_text(encoding="utf-8")
        if viejo not in original:
            print(f"  ??  NO APLICA  {desc}")
            print(f"      (no se encontro el texto en {archivo})")
            sobrevivientes.append((desc, "no aplico"))
            continue
        ruta.write_text(original.replace(viejo, nuevo, 1), encoding="utf-8")
        try:
            paso = correr_suite()
        finally:
            ruta.write_text(original, encoding="utf-8")
        if paso:
            print(f"  !!  SOBREVIVE  {desc}")
            sobrevivientes.append((desc, archivo))
        else:
            print(f"  ok  muere      {desc}")

    print()
    if sobrevivientes:
        print(f"{len(sobrevivientes)}/{len(MUTANTES)} mutantes sobrevivieron:")
        for d, a in sobrevivientes:
            print(f"   - {d}  [{a}]")
        return 1        # que CI se entere: un sobreviviente es un agujero
    print(f"Los {len(MUTANTES)} mutantes murieron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

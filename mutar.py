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
     "        # exactamente lo que hacia el regex, y es de donde salio el problema." + chr(10) + "        if hondo == 0:",
     "        # exactamente lo que hacia el regex, y es de donde salio el problema." + chr(10) + "        if True:"),

    ("fad/validar.py", "aceptar penales en cualquier partido de eliminacion",
     '            and not (p.fase == "eliminacion" and serie_igualada(p, ps))]',
     '            and p.fase != "eliminacion"]'),

    ("fad/validar.py", "dar por igualada una serie sin mirar el global",
     "    return a == b",
     "    return True"),

    ("fad/parser.py", "no calificar una zona que se repite en dos fases",
     '                zona = f"{llave} - {z}" if z and llave and z in ambiguas else z',
     '                zona = z'),

    ("fad/parser.py", "calificar TODA zona con su fase, no solo las ambiguas",
     '                zona = f"{llave} - {z}" if z and llave and z in ambiguas else z',
     '                zona = f"{llave} - {z}" if z and llave else z'),

    ("fad/parser.py", "contar la jornada como zona al buscar rotulos ambiguos",
     '                or re.match(r"(?i)fecha\\s*\\d+", cab) or _ES_RONDA.match(cab)):',
     "                or False):"),

    ("fad/validar.py", "no reconocer como zona a la que viene calificada con su fase",
     r'_ES_ZONA = re.compile(r"(?i)^(.*- )?(zona|grupo)\b")',
     r'_ES_ZONA = re.compile(r"(?i)^(zona|grupo)\b")'),

    ("fad/parser.py", "no ver que la tabla no tiene columna de local",
     '            if _ENCABEZADO_SIN_LOCAL.search(fila):\n                sin_local = True',
     '            if False:\n                sin_local = True'),

    ("fad/parser.py", "que el rotulo de una tabla se pegue a las siguientes",
     '            elif _ENCABEZADO_CON_LOCAL.search(fila):\n                sin_local = False',
     '            elif False:\n                sin_local = False'),

    ("fad/dataset.py", "que el torneo pise lo que dice el partido sobre la cancha",
     '        "neutral": str(neutral if p.neutral is None else p.neutral).lower(),',
     '        "neutral": str(neutral).lower(),'),

    ("fad/dataset.py", "silenciar un alquiler verificado en cualquier cancha",
     '        if (cancha, f["home_team"]) in ALQUILERES:',
     '        if f["home_team"] in {c for _, c in ALQUILERES}:'),

    ("build.py", "mandar al dataset principal tambien lo que no tiene fecha",
     '        (filas if (f.get("date") or "").strip() else sin_fecha).append(f)',
     "        filas.append(f)"),

    ("fad/correcciones.py", "corregir la cancha sin mirar cual dice la pagina",
     '                      and p.visita == c.visita and p.estadio == c.dice]',
     '                      and p.visita == c.visita]'),

    ("fad/dataset.py", "avisar por un salto de una sola division (todos los ascensos)",
     '            if max(niveles) - min(niveles) < 2:',
     '            if len(niveles) < 2:'),

    ("fad/dataset.py", "contar las copas, que cruzan divisiones por diseno",
     '        n = _NIVEL.get(f["tournament"])\n        if n is None:\n            continue',
     '        n = _NIVEL.get(f["tournament"], 9)'),

    ("fad/dataset.py", "mirar solo al local y perder al club mal atribuido de visitante",
     '        for lado in ("home_team", "away_team"):',
     '        for lado in ("home_team",):'),

    ("fad/equipos.py", "avisar aunque el nombre visible no venga desambiguado",
     '        if not _CALIFICADOR.search(visible) or articulo not in ARTICULOS:',
     '        if articulo not in ARTICULOS:'),

    ("fad/equipos.py", "avisar cuando el padron no conoce el nombre visible",
     '        solo = buscar(visible, "")\n        if solo is None:\n            continue',
     '        solo = buscar(visible, "") or Equipo(nombre=visible)'),

    ("fad/dataset.py", "avisar por cualquier cancha compartida, se parezcan o no",
     '                if _confundibles(a, b):',
     '                if True:'),

    ("fad/dataset.py", "contar la cancha neutral como casa del local",
     '        if str(f.get("neutral", "")).lower() == "true" or not str(f.get("venue", "")).strip():',
     '        if not str(f.get("venue", "")).strip():'),

    ("fad/dataset.py", "tomar por confundibles dos clubes que comparten una palabra suelta",
     '    return (x.startswith(y + " ") or y.startswith(x + " ")\n'
     '            or x.endswith(" " + y) or y.endswith(" " + x))',
     '    return bool(set(x.split()) & set(y.split()))'),

    ("fad/parser.py", "que una tilde de menos parezca un desacuerdo de articulos",
     '        vistos.setdefault(limpiar(visible), {})[equipos.normalizar(d)] = d',
     '        vistos.setdefault(limpiar(visible), {})[d] = d'),

    ("fad/posiciones.py", "no decir de que lado esta el error",
     "    if desviados == 1:",
     "    if False:"),

    ("fad/posiciones.py", 'no leer la tabla escrita con plantillas',
     '    return _por_plantillas(bloque, arts) or _por_wikitabla(bloque, arts, descartadas)',
     '    return _por_wikitabla(bloque, arts, descartadas)'),

    ("fad/posiciones.py", 'leer una sola tabla y no las de todas las zonas',
     "    for bloque in _bloques(texto):\n        yield from _filas(bloque, arts, descartadas)",
     "    for bloque in list(_bloques(texto))[:1]:\n        yield from _filas(bloque, arts, descartadas)"),

    ("fad/posiciones.py", 'dejar que la parcial de la primera rueda pise a la final',
     '        if canonico not in fuera or datos[0] > fuera[canonico][0]:',
     '        if True:'),

    ("fad/posiciones.py", 'no cortar el bloque en el proximo encabezado',
     '        sig = _CUALQUIER_ENCABEZADO.search(texto, m.end())',
     '        sig = None'),

    ("fad/posiciones.py", 'no cerrar la wikitabla en la plantilla de leyenda',
     r'_WIKITABLA = re.compile(r"\{\|.*?(?=\n\|\}|\{\{\s*Tabla de posiciones fin)", re.S | re.I)',
     r'_WIKITABLA = re.compile(r"\{\|.*?(?=\n\|\})", re.S | re.I)'),

    ("fad/posiciones.py", 'partir los parametros por | y romper el wikilink',
     '        eq = _CAMPO_EQUIPO.search(cuerpo)',
     '        eq = re.match(r"(.*)", cuerpo.split("|")[-1], re.S)'),

    ("fad/posiciones.py", 'resolver el club por el nombre visible y no por el articulo',
     '        enlace = _EQ_WIKILINK.search(eq.group(1))',
     '        enlace = None'),

    ("fad/posiciones.py", 'dejar la nota al pie pegada al nombre del club',
     '            club = parser.limpiar(enlace.group(2) or articulo)',
     '            club = parser.limpiar(eq.group(1))'),

    ("fad/posiciones.py", 'no cortar el eq= en un |#color de mas',
     r'_CAMPO_EQUIPO = re.compile(r"(?<![a-zA-Z])eq\s*=\s*(.*?)(?:\|\s*#?\s*color\s*=|$)", re.S)',
     r'_CAMPO_EQUIPO = re.compile(r"(?<![a-zA-Z])eq\s*=\s*(.*?)(?:\|\s*color\s*=|$)", re.S)'),

    ("fad/posiciones.py", 'aceptar una plantilla a la que le faltan campos',
     '        if len(nums) < 5 or not eq:',
     '        if not eq:'),

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
     "        if club not in contada or correcciones.revisado(pagina, club):" + chr(10) +
     "            continue" + chr(10) + "        pj2, gf2, gc2 = contada[club][:3]",
     "        if correcciones.revisado(pagina, club):" + chr(10) +
     "            continue" + chr(10) + "        pj2, gf2, gc2 = contada[club][:3]"),

    ("fad/fechas.py", "tomar la fecha de cualquier marcador distinto",
     "            if (p.jornada, p.local, p.visita) not in (arbitrados or ()):",
     "            if False:"),

    ("build.py", 'meter los partidos sin fecha en el dataset principal',
     '        _repartir([dataset.a_fila(p, t.torneo, t.temporada, t.url, t.neutral) for p in ps],\n                  filas, sin_fecha)',
     '        filas.extend(dataset.a_fila(p, t.torneo, t.temporada, t.url, t.neutral) for p in ps)'),

    ("build.py", 'reusar los sin fecha desde el dataset principal',
     '            _repartir(listas, filas, sin_fecha)',
     '            filas.extend(listas)'),

    ("build.py", 'guardar la carpeta sin-fecha en una constante',
     '    sf_dir = sin_fecha_en(SALIDA)',
     '    sf_dir = Path(__file__).resolve().parent / "data" / "sin-fecha"'),

    ("build.py", "no cruzar contra la tabla de posiciones",
     "               for d in posiciones.contrastar(ps, texto, pagina=t.pagina,\n"
     "                                              respaldados=respaldados)]",
     "               for d in []]"),

    ("build.py", "no chequear que la tabla cierre consigo misma",
     "               for d in posiciones.desbalance(ps, texto, pagina=t.pagina)]",
     "               for d in []]"),

    ("fad/posiciones.py", "denunciar el desbalance aunque la tabla y la grilla "
                          "no hablen de los mismos clubes",
     "        if not publicada or set(publicada) != set(contada):\n            continue",
     "        if False:\n            continue"),

    ("fad/posiciones.py", "denunciar el desbalance aunque no coincidan los PJ",
     "        if any(publicada[c][0] != contada[c][0] for c in publicada):\n            continue",
     "        if False:\n            continue"),

    ("fad/posiciones.py", "dar por desbalanceada a una tabla que cierra",
     "        if gf != gc:\n            fuera.append(_texto_del_desbalance(gf, gc, alcance))",
     "        if True:\n            fuera.append(_texto_del_desbalance(gf, gc, alcance))"),

    ("fad/posiciones.py", "no leer el DIF positivo escrito con signo (+31)",
     r'        numeros = [c for c in celdas if re.fullmatch(r"[-+]?\d+", c)]',
     r'        numeros = [c for c in celdas if re.fullmatch(r"-?\d+", c)]'),

    ("fad/posiciones.py", "comparar cada tabla suelta en vez de fusionar las del mismo alcance",
     "    for alcance, filas in por_alcance.items():",
     "    for alcance, filas in [(k, {c: d}) for k, v in por_alcance.items() for c, d in v.items()]:"),

    ("build.py", "no avisar del club de la tabla que no esta en el padron",
     "               for d in posiciones.fuera_del_padron(texto)]",
     "               for d in []]"),

    ("fad/posiciones.py", "dar por desconocido a un club que el padron si conoce",
     "        if not equipos.conocido(club, articulo):",
     "        if True:"),

    ("fad/posiciones.py", "dejar la nota al pie pegada al nombre del eq=",
     "            corte = parser.limpiar(_COLA_DE_NOTA.split(eq.group(1), 1)[0])",
     "            corte = parser.limpiar(eq.group(1))"),

    ("fad/posiciones.py", "resolver la wikitabla por el nombre visible y no por el wikilink",
     "        enlace = _EQ_WIKILINK.search(crudas[nombres[-1]])",
     "        enlace = None"),

    ("fad/correcciones.py", "aplicar un marcador arbitrado que ya no engancha",
     "        if len(candidatos) != 1:",
     "        if False:"),

    ("fad/posiciones.py", "buscar la tabla solo por el titulo de la seccion",
     "    for t in _tablas_declaradas(texto):\n        yield from _por_wikitabla(t, arts, descartadas)",
     "    for t in []:\n        yield from _por_wikitabla(t, arts, descartadas)"),

    ("fad/posiciones.py", "dejar entrar la tabla de descenso y que desplace a las de zona",
     '_SECCION_AGREGADA = re.compile(r"(?i)descenso|promedio|anual|acumulad")',
     '_SECCION_AGREGADA = re.compile(r"(?i)no-va-a-matchear-nunca-jamas")'),

    ("fad/posiciones.py", "aceptar como tabla de posiciones a cualquier wikitabla",
     "    return _COLUMNAS_DECLARADAS <= etiquetas",
     "    return True"),

    ("fad/posiciones.py", "comparar cada tabla contra el torneo entero y no contra su fase",
     "    return sumar([p for p in ps if not alcance or p.llave == alcance])",
     "    return sumar(ps)"),

    ("fad/posiciones.py", "usar la seccion como alcance aunque no sea una llave de los partidos",
     "        return previos[-1] if previos and previos[-1] in llaves else \"\"",
     "        return previos[-1] if previos else \"\""),

    ("fad/correcciones.py", "reemplazar el partido sin mirar la llave",
     "                      if p.llave == r.llave and p.jornada == r.jornada",
     "                      if p.jornada == r.jornada"),

    ("fad/correcciones.py", "reemplazar sin exigir que el marcador viejo coincida",
     "                      and (p.goles_local, p.goles_visita) == (gl, gv)]",
     "                      ]"),

    ("fad/correcciones.py", "aplicar un reemplazo que engancha con varios partidos",
     "        if len(candidatos) != 1:\n"
     "            avisos.append(f\"el reemplazo de {r.llave} {r.jornada} ({local} vs \"",
     "        if False:\n"
     "            avisos.append(f\"el reemplazo de {r.llave} {r.jornada} ({local} vs \""),

    ("fad/espn.py", "tomar la fecha de ESPN en UTC sin pasarla a hora argentina",
     "    return (datetime.fromisoformat(iso.replace(\"Z\", \"+00:00\"))\n"
     "            .astimezone(_ARGENTINA).date().isoformat())",
     "    return iso[:10]"),

    ("fad/espn.py", "no chequear que los planteles coincidan",
     "    sobran = sorted(suyos - mios)",
     "    sobran = []"),

    ("fad/espn.py", "importar un partido de ESPN sin marcador",
     "        if goles[\"home\"] is None or goles[\"away\"] is None:\n            continue",
     "        goles = {k: (v if v is not None else 0) for k, v in goles.items()}"),

    ("fad/fechas.py", "exigir jornada aunque la fuente no la publique",
     "    con_jornada = any(a.jornada for a in ajenos)",
     "    con_jornada = True"),

    ("fad/rsssf.py", "exigir dos espacios antes del marcador (pierde al club de 28 letras)",
     r'    r"^([^\[\]]{3,34}?)\s+(\d+)-(\d+)',
     r'    r"^([^\[\]]{3,34}?)\s{2,}(\d+)-(\d+)'),

    ("fad/rsssf.py", "dejar que la anotacion derramada se pegue al visitante",
     r'([^\[\]\s](?:[^\[\]]*?[^\[\]\s])?)(?:\s{2,}.*)?$")',
     r'([^\[\]]+?)\s*$")'),

    ("fad/rsssf.py", "no distinguir Apertura de Clausura",
     '                llave, zona = pelada, ""',
     '                llave, zona = "", ""'),

    ("fad/rsssf.py", "leer la pagina de RSSSF como UTF-8",
     '    texto = crudo.decode("latin-1")',
     '    texto = crudo.decode("utf-8", errors="replace")'),

    ("fad/rsssf.py", "emparejar por parecido lo que el mapa no traduce",
     "        if not cl or not cv:\n            continue",
     "        cl, cl = cl or local, cv or visita"),

    ("fad/fechas.py", "ignorar la llave y mezclar dos torneos de la misma pagina",
     "            k = (a.llave, a.jornada if con_jornada else 0, el, ev)",
     '            k = ("", a.jornada if con_jornada else 0, el, ev)'),

    ("build.py", "tirar las filas sin fecha en vez de guardarlas aparte",
     '        (filas if (f.get("date") or "").strip() else sin_fecha).append(f)',
     '        filas.append(f) if (f.get("date") or "").strip() else None'),

    ("fad/parser.py", "descartar las celdas vacias y correr las columnas",
     "    return partes[1:]",
     "    return [c for c in partes[1:] if c.strip()]"),

    ("fad/parser.py", "mandar a eliminacion toda tabla que no cuelgue de un Resultados",
     "                                   fuera_de_la_liga=not _rotula_fechas(tabla)",
     "                                   fuera_de_la_liga=True or not _rotula_fechas(tabla)"),

    ("fad/parser.py", "ignorar la seccion y creerle solo al rotulo de fecha",
     "                                                    or bool(_ES_RONDA.match(llave))\n"
     "                                                    or bool(_LLAVE_ELIMINATORIA.search(llave))):",
     "                                                    ):"),

    ("fad/parser.py", "contar la COLUMNA Fecha como si fuera un rotulo de jornada",
     r'    return any(re.match(r"(?i)fecha\s*\d+", limpiar(cab))'
     "\n"
     r'               for cab in re.findall(r"!\s*colspan\s*=\s*\"?\d+\"?[^|\n]*\|\s*(.+)", tabla))',
     r'    return bool(re.search(r"(?i)fecha", tabla))'),

    ("fad/parser.py", "no cortar en el cierre |} de tabla",
     'bloque = re.sub(r"\\n\\|\\}", "\\n|-", bloque)',
     'bloque = bloque'),

    ("fad/parser.py", "no reconocer 'Interzonal' como etiqueta de seccion",
     '                z = _seccion(cab)',
     '                z = cab if re.match(r"(?i)(zona|grupo)", cab) else ""'),

    ("fad/parser.py", "no unificar Interzonal/Interzonales",
     '    if re.match(r"(?i)^interzonal", cab):\n        return "Interzonal"',
     '    pass'),

    ("fad/parser.py", "ignorar el rowspan (asumir 6 celdas siempre)",
     "    return (int(n.group(1)) if n else 1), limpiar(m.group(2))",
     "    return 1, limpiar(m.group(2))"),

    ("fad/parser.py", "que un titulo NO corte la jornada",
     "        if (titulo := _TITULO_CUALQUIERA.search(fila)):",
     "        if (titulo := None):"),

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
     "        if tenia_ahora < cuantos and clave not in salvo:",
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
     "    avisos += _completar_fechas(ps, t) if t.wf else []",
     "    avisos += _completar_fechas(ps, t) if True else []"),

    ("build.py", "no completar las fechas de la segunda fuente",
     "    avisos += _completar_fechas(ps, t) if t.wf else []",
     "    avisos += []"),

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

    ("fad/validar.py", "mirar la mezcla de zonas en toda la pagina y no por fase",
     "            porfase.setdefault(p.llave, []).append(p)",
     "            porfase.setdefault('', []).append(p)"),

    ("fad/parser.py", "usar el titulo de una tabla de posiciones como zona",
     '    if _ES_RONDA.match(titulo) or re.match(r"(?i)^(tabla|posiciones|promedios)\\b", titulo):',
     "    if _ES_RONDA.match(titulo):"),

    ("fad/parser.py", "no mirar la fase que contiene a la seccion",
     "                                                    or bool(_LLAVE_ELIMINATORIA.search(fase)),",
     "                                                    or False,"),

    ("fad/parser.py", "tomar la fase en vez de la seccion como nombre de la ronda",
     "        ronda = jornada = zona_defecto or llave",
     "        ronda = jornada = llave or zona_defecto"),

    ("fad/validar.py", "no chequear que un club juegue en una sola zona",
     "            una_zona_por_club, localias_repartidas, cadena_de_llaves]",
     "            localias_repartidas, cadena_de_llaves]"),

    ("fad/validar.py", "contar las fechas interzonales como si fueran una zona",
     '        if p.fase != "zonas" or not _ES_ZONA.match(p.zona or ""):',
     '        if p.fase != "zonas" or not (p.zona or ""):'),

    ("fad/validar.py", "mezclar las zonas de llaves distintas",
     "            donde.setdefault((p.llave, club), Counter())[p.zona] += 1",
     "            donde.setdefault(((), club), Counter())[p.zona] += 1"),

    ("fad/validar.py", "no chequear que la localia se reparta",
     "            una_zona_por_club, localias_repartidas, cadena_de_llaves]",
     "            una_zona_por_club, cadena_de_llaves]"),

    ("fad/validar.py", "mirar la localia sin separar por zona",
     "        k = (p.llave, p.zona, tuple(sorted((p.local, p.visita))))",
     "        k = (p.llave, tuple(sorted((p.local, p.visita))))"),

    ("fad/validar.py", "contar tambien los partidos sin jornada",
     "        if p.fase != \"zonas\" or not p.jornada or not p.local or not p.visita:",
     "        if p.fase != \"zonas\" or not p.local or not p.visita:"),

    ("fad/dataset.py", "dejar el archivo de una temporada que se quedo sin filas",
     "        if viejo.name not in {archivo_de(t) for t in por_anio}:",
     "        if False:"),

    # --- los 240 partidos que las copas no entregaban ---
    ("fad/parser.py", "no tolerar la tanda pegada adelante del marcador",
     "    for candidato in (texto, _TANDA_ADELANTE.sub(\"\", texto)):",
     "    for candidato in (texto,):"),

    ("fad/parser.py", "desenvolver el nowrap con un regex no goloso",
     "    s = _desenvolver_nowrap(s)",
     '    s = re.sub(r"' + chr(92)*2 + '{' + chr(92)*2 + '{' + chr(92)*2 + 's*nowrap' + chr(92)*2 + 's*' + chr(92)*2 + '|(.*?)' + chr(92)*2 + '}' + chr(92)*2 + '}", r"' + chr(92)*2 + '1", s, flags=re.I | re.S)'),

    ("fad/parser.py", "no reconocer las rondas de entrada de las copas viejas",
     '    r"|Preclasificatorio|Ronda previa|Fase final I{1,2})[^=' + chr(92) + 'n]*=+' + chr(92) + 's*$", re.M | re.I)',
     '    r")[^=' + chr(92) + 'n]*=+' + chr(92) + 's*$", re.M | re.I)'),

    ("fad/parser.py", "leer dos veces una ronda anidada dentro de otra",
     "        if m.start() < hasta:" + chr(10) + "            continue",
     "        if False:" + chr(10) + "            continue"),

    # --- la tanda escrita en la celda, y la raya larga ---
    ("fad/parser.py", "no leer la tanda escrita con la palabra Pen.",
     "    m = _PENAL_ESCRITO.search(celda_cruda)",
     "    m = None"),

    ("fad/parser.py", "no pasarle la tanda al partido de una tabla de liga",
     '            penales_local=(pen or (None, None))[0],',
     '            penales_local=None,'),

    ("fad/parser.py", "buscar la tanda por indice en vez de por columna",
     '        pen = _penales(crudos["resultado"])',
     '        pen = _penales(celdas[1]) if len(celdas) > 1 else None'),

    ("fad/parser.py", "no aceptar la raya larga como separador del marcador",
     '_SEPARADOR = r"[-:–—]"',
     '_SEPARADOR = r"[-:]"'),

    ("fad/parser.py", "tomar por tanda dos numeros cualesquiera, sin la palabra",
     '_PENAL_ESCRITO = re.compile(r"(?i)pen[^' + chr(92) + 'd]{0,20}(' + chr(92) + 'd+)' + chr(92) + 's*" + _SEPARADOR + r"' + chr(92) + 's*(' + chr(92) + 'd+)")',
     '_PENAL_ESCRITO = re.compile(r"(' + chr(92) + 'd+)' + chr(92) + 's*" + _SEPARADOR + r"' + chr(92) + 's*(' + chr(92) + 'd+)" + r"' + chr(92) + 's*$")'),

    # --- status: de donde salio el marcador ---
    ("fad/parser.py", "no mirar si el partido se termino de jugar despues",
     '    if _SE_COMPLETO.search(fila):' + chr(10) + '        return ""',
     '    if False:' + chr(10) + '        return ""'),

    ("fad/parser.py", "mirar el fallo ANTES que la suspension",
     '    if _NO_LLEGO_AL_FINAL.search(fila):' + chr(10) + '        return "suspendido"',
     '    if _HUBO_FALLO.search(fila):' + chr(10) + '        return "escritorio"'),

    ("fad/parser.py", "no marcar el fallo que cambio el numero de un partido terminado",
     '    if _HUBO_FALLO.search(fila):' + chr(10) + '        return "escritorio"',
     '    if False:' + chr(10) + '        return "escritorio"'),

    ("fad/parser.py", "dejar en vacio un fallo que no se supo leer, sin avisar",
     "    return bool(_HABLA_DE_FALLO.search(fila)) and not status_de_la_fila(fila)",
     "    return False"),

    ("fad/dataset.py", "no escribir el status en el CSV",
     '        "status": p.status,',
     '        "status": "",'),

    ("fad/dataset.py", "aceptar cualquier encabezado con tal de que falten columnas",
     "        if tiene != COLUMNAS[:len(tiene)]:",
     "        if False:"),

    ("fad/correcciones.py", "dejar en el dataset el partido con dos resultados",
     "        for p in sobran:" + chr(10) + "            ps.remove(p)",
     "        for p in sobran:" + chr(10) + "            pass"),

    ("fad/correcciones.py", "sacar cualquier cruce de esos dos clubes, sin mirar el marcador",
     "        sobran = [p for p in ps if p.local == div.local and p.visita == div.visita" + chr(10) +
     "                  and (p.goles_local, p.goles_visita) == div.dice]",
     "        sobran = [p for p in ps if p.local == div.local and p.visita == div.visita]"),

    ("fad/correcciones.py", "tratar el `dice=None` como si fuera cualquier marcador",
     "        if div.dice is None:" + chr(10) + "            continue",
     "        if False:" + chr(10) + "            continue"),

    # --- el partido que existe y no se puede escribir ---
    ("build.py", "no avisar del partido que el esquema no puede escribir",
     "               for d in parser.partidos_anulados(texto)]",
     "               for d in []]"),

    ("fad/parser.py", "buscar el resultado anulado en una posicion fija",
     "            i = next((k for k, c in enumerate(celdas) if _ANULADO.match(c)), None)",
     "            i = 1 if len(celdas) > 1 and _ANULADO.match(celdas[1]) else None"),

    ("fad/parser.py", "tomar por anulado un PP de un solo lado",
     'r"(?i)^' + chr(92) + 's*PP' + chr(92) + 's*-' + chr(92) + 's*PP' + chr(92) + 's*$"',
     'r"(?i)PP"'),

    ("fad/parser.py", "que el nombre de la seccion pise al rotulo de la tabla",
     "                                   fuera_de_la_liga=(bool(_ES_RONDA.match(titulo))" + chr(10) +
     "                                                     and not _rotula_fechas(cuerpo))",
     "                                   fuera_de_la_liga=(bool(_ES_RONDA.match(titulo))" + chr(10) +
     "                                                     and True)"),

    ("fad/parser.py", "no mirar el nombre de la seccion en el primer camino",
     "                                   fuera_de_la_liga=(bool(_ES_RONDA.match(titulo))",
     "                                   fuera_de_la_liga=(False"),

    # --- el titulo que ademas nombra una ronda ---
    ("fad/parser.py", "que un titulo corte la jornada pero no diga que ronda es",
     "            if _ES_RONDA.match(nombre):" + chr(10) + "                jornada = ronda = nombre",
     "            if False:" + chr(10) + "                jornada = ronda = nombre"),

    ("fad/parser.py", "tomar por ronda a cualquier titulo, no solo a los que la nombran",
     "            if _ES_RONDA.match(nombre):",
     "            if nombre:"),

    ("fad/parser.py", "no reconocer 'Partido de desempate' como una ronda",
     'r"|partidos? de (ida|vuelta|desempate)|promoci[oó]n)")',
     'r"|partidos? de (ida|vuelta)|promoci[oó]n)")'),

    # --- la fecha: el anio y la nota al pie ---
    ("fad/parser.py", "ignorar el anio que escribe la celda y deducirlo igual",
     '    y = int(m.group(3)) if m.group(3) else (anio if (anio_fin is None or mes >= mes_inicio) else anio_fin)',
     '    y = anio if (anio_fin is None or mes >= mes_inicio) else anio_fin'),

    ("fad/parser.py", "no leer la nota que dice cuando se jugo de verdad",
     '            fecha=(_fecha_de_la_nota(fila, anio, anio_fin, mes_inicio, programada)',
     '            fecha=(""'),

    ("fad/parser.py", "tomar tambien `se completo` como si fuera otra fecha",
     'r"(?i)se\s+(?:jug[oó]|jugaron|disput[oó]|disputaron)\s+(?:el\s+)?"',
     'r"(?i)se\s+(?:jug[oó]|jugaron|disput[oó]|disputaron|complet[oó])\s+(?:el\s+)?"'),

    ("fad/parser.py", "dejar que la fecha jugada caiga antes de la programada",
     '    if jugada and programada and jugada < programada:',
     '    if False:'),

    ("fad/parser.py", "dejar que los pipes de la nota partan la fila",
     '    fila = _NOTA_AL_PIE.sub("", fila)',
     '    fila = fila'),

    ("fad/parser.py", "dejar el superindice de la nota al pie pegado al nombre",
     "    s = re.sub(r\"[\\u00b9\\u00b2\\u00b3\\u2070-\\u209f]+$\", \"\", s).strip()",
     "    s = s"),

    ("fad/parser.py", "dejar pegada la llamada al pie escrita en ASCII",
     "    s = re.sub(r\"<sup[^>]*>.*?</sup>\", \"\", s, flags=re.S | re.I)",
     "    s = s"),

    ("fad/parser.py", "leer el asterisco de la nota como parte del nombre",
     "    return re.sub(r\"^(.+?)\\s*\\(\\*+\\)$\", r\"\\1\", s).strip()",
     "    return s"),

    ("fad/fechas.py", "completar aunque el marcador no coincida",
     "        if (a.goles_local, a.goles_visita) != (p.goles_local, p.goles_visita):",
     "        if False:"),

    ("fad/fechas.py", "pisar la fecha de los que ya la tienen",
     "        if p.fecha:\n"
     "            # YA TIENE FECHA, PERO ESTA FUENTE PUEDE DECIR OTRA.",
     "        if False:\n"
     "            # YA TIENE FECHA, PERO ESTA FUENTE PUEDE DECIR OTRA."),

    ("fad/fechas.py", "no exigir que coincida la jornada",
     "            k = (a.llave, a.jornada if con_jornada else 0, el, ev)",
     "            k = (a.llave, a.jornada if con_jornada else 0, el, ev)\n"
     "            for _j in range(1, 60):\n"
     "                indice.setdefault((a.llave, _j, el, ev), a)"),

    ("fad/fechas.py", "aceptar como temporada cualquier opcion del selector",
     '        m = _IDS.search(valor)',
     '        m = _IDS.search(valor) or re.search(r"(cy\d+)()", valor)'),

    ("fad/fechas.py", "confundir una competencia con una temporada",
     '        m = re.fullmatch(r"/competition/(co\d+)/", valor)',
     '        m = re.search(r"/(co\d+)/", valor)'),

    ("fad/fechas.py", "completar sin dejar el credito de la fuente",
     "        p.fuente_fecha = credito",
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
     "    y = int(m.group(3)) if m.group(3) else (anio if (anio_fin is None or mes >= mes_inicio) else anio_fin)",
     "    y = anio"),

    ("fad/parser.py", "corte de temporada fijo en agosto (la 2019-20 arranco en julio)",
     "    y = int(m.group(3)) if m.group(3) else (anio if (anio_fin is None or mes >= mes_inicio) else anio_fin)",
     "    y = int(m.group(3)) if m.group(3) else (anio if (anio_fin is None or mes >= 8) else anio_fin)"),

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
     "    return partes[1:]",
     "    return partes"),

    ("fad/parser.py", "no reconocer '||' como separador de celdas",
     '    partes = re.split(r"\\n\\|", "\\n" + fila.replace("||", "\\n|"))',
     '    partes = re.split(r"\\n\\|", "\\n" + fila)'),

    ("fad/parser.py", "sacar los penales DESPUES de limpiar la celda",
     '        pen = _penales(celdas[_COL_COPA.index("resultado")])',
     '        pen = _penales(v["resultado"])'),

    ("fad/parser.py", "borrar {{nowrap}} en vez de desenvolverla",
     "    s = _desenvolver_nowrap(s)",
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
     '            return [Aviso("no se pudo revisar el cuadro de eliminacion",\n'
     '                          "hay partidos sin ronda reconocida; el chequeo se salteo",\n'
     "                          grave=False)]",
     "            return []"),

    # La regla de al lado tiene su propio mutante porque es una excepcion, y una
    # excepcion mal puesta se come al chequeo entero: con "< 1" no se cumple nunca
    # y vuelve el aviso en las ocho llaves de una sola ronda.
    ("fad/validar.py", "una sola ronda tampoco se libra del aviso",
     "if len({p.jornada for p in elim}) < 2:",
     "if len({p.jornada for p in elim}) < 1:"),

    # El guard de las llaves paralelas, de los dos lados: si nunca se cumple vuelve
    # el aviso equivocado en diez llaves, y si se cumple siempre se come al aviso
    # que si corresponde en las diecinueve que quedan.
    # Los tres de la normalizacion de rondas: agrupar por el nombre de la pagina
    # en vez del normalizado deja dos grupos con el mismo lugar en el orden, y sin
    # cada pelada vuelven a trabarse las paginas que destraban.
    # Las dos rondas raras de la Copa Argentina 2013-14: si no estan, el cuadro
    # entero de 53 partidos vuelve a quedar sin revisar; si estan al reves, el que
    # gana la primera queda acusado de no haberla ganado.
    # Las tres formas de numerar una ronda, cada una con su mutante: sin
    # cualquiera de ellas vuelven a salir partidos con el `matchday` vacio.
    # El lector de llaves de RSSSF, por donde de verdad puede mentir.
    # La temporada que vive dentro de la pagina del ano, con todo lo que trae.
    # Las rondas a partido unico, y la cancha de un tercero.
    ("fad/rsssf.py", "pedirle pata a una ronda a partido unico",
     "        if not m:\n            continue",
     "        if not m or not pata:\n            continue"),

    ("fad/rsssf.py", "no leer la fecha que el titulo trae puesta",
     'pata, fecha = "", _dia_de(m.group(2) or "")',
     'pata, fecha = "", None'),

    ("fad/rsssf.py", "callarse que se jugo en cancha de un tercero",
     "        if _LLAVE_SEDE.search(nota):",
     "        if False:"),

    ("fad/rsssf.py", "quedarse con la primera aparicion de la seccion",
     "        i = texto.find(desde)",
     "        i = 0 if desde else texto.find(desde)"),

    ("fad/rsssf.py", "no tolerar el typo 'Secoond leg' de la fuente",
     "First|Second|Secoond",
     "First|Second"),

    ("fad/rsssf.py", "que una fecha de liga no cierre la eliminacion",
     "        if _LLAVE_CIERRA.match(pelada):",
     "        if False:"),

    ("fad/rsssf.py", "no despegar el marcador del parentesis",
     '_LLAVE_PEGADO = re.compile(r"\\)[ ]?(\\d+\\s*-\\s*\\d+)")',
     '_LLAVE_PEGADO = re.compile(r"(?!x)x()")'),

    ("build.py", "comparar sin canonizar al buscar repetidos",
     "        l, v = uno(x.local, x.local_art), uno(x.visita, x.visita_art)",
     "        l, v = x.local, x.visita"),

    # El lector de llaves de ESPN, y el hueco que destapo en el cedazo.
    # El formato compacto, por donde puede mentir: el marcador de la vuelta y la
    # localia de la vuelta son lo que hay que dar vuelta, y la casilla sin fecha es
    # lo unico que evita duplicar media temporada.
    # Los tres que salieron de la ultima tanda: el separador de un espacio en los
    # dos lectores, el homonimo en el cruce, y la zona despareja mientras se juega.
    ("fad/rsssf.py", "pedir dos espacios de separador en el lector expandido",
     '(?:\\t+|[ ]+)(\\d+)\\s*-\\s*(\\d+)(?:\\t+|[ ]+)',
     '(?:\\t+|[ ]{2,})(\\d+)\\s*-\\s*(\\d+)(?:\\t+|[ ]+)'),

    ("fad/rsssf.py", "pedir dos espacios de separador en el lector compacto",
     'r"^(.+?)[ \\t]+(\\d+)-(\\d+)[ \\t]+(\\d+)-(\\d+)[ \\t]+(.+?)"',
     'r"^(.+?)[ \\t]{2,}(\\d+)-(\\d+)[ \\t]+(\\d+)-(\\d+)[ \\t]+(.+?)"'),

    ("build.py", "no aplicar el homonimo de la pagina al cruzar",
     "        return correcciones.homonimo(pagina, equipos.canonizar(nombre, art))\n"
     "\n"
     "    def par(x):",
     "        return equipos.canonizar(nombre, art)\n"
     "\n"
     "    def par(x):"),

    # La zona que la tabla no cuenta: si se apaga vuelven diez avisos que no son de
    # nadie, y si se prueba de a una zona el interzonal de dos grupos se escapa.
    # El dividido en el cruce de PJ: si no se suma vuelven cinco avisos que son la
    # consecuencia de una decision ya escrita, y si se suma sin mirar la seccion se
    # arregla una tabla y se rompe la de al lado.
    ("fad/posiciones.py", "no contar el dividido como jugado",
     "if publicada[c][0] != contada[c][0] + divididos.get(c, 0)]",
     "if publicada[c][0] != contada[c][0]]"),

    ("fad/correcciones.py", "el dividido cuenta para cualquier seccion",
     "        if d.pagina != pagina or (d.llave or llave) != llave:",
     "        if d.pagina != pagina:"),

    ("fad/posiciones.py", "no ver que una zona explica el desvio",
     "        if desviados and _una_zona_lo_explica(dentro, publicada, comunes):",
     "        if False:"),

    ("fad/posiciones.py", "probar zonas sueltas y no conjuntos",
     "    for cuantas in range(1, len(zonas)):",
     "    for cuantas in range(1, 2):"),

    ("fad/validar.py", "avisar la zona despareja aunque el torneo este en curso",
     "    if en_curso:\n        return []",
     "    if False:\n        return []"),

    # La regresion que metieron las llaves importadas: sus jornadas vienen en
    # ingles y con la pata pegada, y sin esto vuelven dos cuadros sin revisar.
    ("fad/validar.py", "no entender las rondas en ingles de RSSSF",
     '    "semifinals": "semifinales",',
     '    "semifinals": "semifinals",'),

    ("fad/validar.py", "pelar la rama antes que la pata",
     "    sin_pata = _PATA_AL_FINAL.sub(\"\", j)",
     "    sin_pata = j"),

    ("fad/rsssf.py", "la zona del compacto no va en la llave",
     'cuadro = f"{llave} - {zona}" if zona else llave',
     "cuadro = llave"),

    ("fad/rsssf.py", "la zona del compacto no va en la jornada",
     'jornada = f"{zona} - {ronda}" if zona else ronda',
     "jornada = ronda"),

    ("fad/rsssf.py", "no dar vuelta el marcador de la vuelta",
     "                             goles_local=vuelta[1], goles_visita=vuelta[0],",
     "                             goles_local=vuelta[0], goles_visita=vuelta[1],"),

    ("fad/rsssf.py", "no cambiar la localia en la vuelta",
     "        fuera.append(Partido(local=cv, visita=cl,",
     "        fuera.append(Partido(local=cl, visita=cv,"),

    # La seccion de llaves y la fila de tabla que no es un partido.
    ("fad/rsssf.py", "leer llaves mas alla del final de la seccion",
     "        else:\n            texto = texto[:j]\n\n    fuera = []",
     "        else:\n            pass\n\n    fuera = []"),

    ("fad/rsssf.py", "leer una fila de tabla como si abriera una llave",
     "        if _FOJA.match(linea):\n            continue",
     "        if False:\n            continue"),

    ("build.py", "no contar como testigo el partido que la pagina trae sin dia",
     "            if len(iguales) == 1:",
     "            if False:"),

    # Dos fuentes que dan dias distintos.
    ("fad/fechas.py", "callar que la otra fuente da otro dia",
     "            if a is not None and a.fecha and a.fecha != p.fecha:",
     "            if False:"),

    ("fad/fechas.py", "tomar el vacio de la otra fuente como un desacuerdo",
     "            if a is not None and a.fecha and a.fecha != p.fecha:",
     "            if a is not None and a.fecha != p.fecha:"),

    # Las fechas copiadas a mano de una fuente citada.
    ("build.py", "no aplicar las fechas citadas a mano",
     "    if citadas.FECHAS.get(t.pagina):",
     "    if False:"),

    ("build.py", "pedirle las citas a todas las paginas",
     "    if citadas.FECHAS.get(t.pagina):",
     "    if True:"),

    ("fad/citadas.py", "mandar la cita con jornada en vez de sin ella",
     "    return [Ajeno(fecha=c.fecha, jornada=0, llave=c.llave,",
     "    return [Ajeno(fecha=c.fecha, jornada=1, llave=c.llave,"),

    # Sin la llave, las dos veces que un mismo par se cruza en la temporada
    # -- cuartos del Apertura y semis del Clausura -- caen en la misma casilla y
    # la regla de colision de `completar` se lleva puestas a las dos.
    ("fad/citadas.py", "mandar la cita sin la llave que separa los cuadros",
     "    return [Ajeno(fecha=c.fecha, jornada=0, llave=c.llave,",
     '    return [Ajeno(fecha=c.fecha, jornada=0, llave="",'),

    # La cola del titulo, y las llaves completando fechas.
    ("fad/rsssf.py", "no reconocer la cola 'Revalida' en el titulo de la ronda",
     'r"(?:\\s+(?:\\d[^\\[\\]]*|Reválida))?(?:\\s*\\[([^\\]]*)\\])?\\s*$", re.I)',
     'r"(?:\\s+\\d[^\\[\\]]*)?(?:\\s*\\[([^\\]]*)\\])?\\s*$", re.I)'),

    ("build.py", "no fecharle a la pagina lo que la llave si tiene fechado",
     "                   for d in fechar_con_las_llaves(ps, llaves_rsssf)]",
     "                   for d in []]"),

    ("build.py", "darle a un partido de liga la fecha de una llave",
     '        [x for x in ps if x.fase == "eliminacion"],',
     "        list(ps),"),

    # El corte de seccion, cuando el archivo del ano trae varias divisiones.
    ("fad/rsssf.py", "leer mas alla del final de la seccion",
     "        else:\n            texto = texto[:j]",
     "        else:\n            pass"),

    ("fad/rsssf.py", "callar que el final de la seccion no aparecio",
     '            raros.append(f"no se encontro el final de la seccion "',
     '            raros.append("") or raros.pop() or raros.append(f"x "'),

    ("fad/rsssf.py", "leer el archivo entero cuando la seccion no aparece",
     '            return [], [f"no se encontro la seccion {desde.splitlines()[0]!r}"]\n'
     "        texto = texto[i:]",
     "        texto = texto[max(i, 0):]"),

    ("build.py", "no acotar la seccion al completar fechas",
     '    desde, hasta = rsssf.SECCION_LIGA.get(t.pagina, ("", ""))',
     '    desde, hasta = "", ""'),

    # El padron como ultimo recurso, y la deduplicacion viendo los renombres
    # que corren despues.
    ("fad/rsssf.py", "no preguntarle al padron lo que el mapa no tiene",
     "        return _por_el_padron(corto)",
     '        return "", f"el mapa no traduce {corto!r}"'),

    ("fad/rsssf.py", "pelarle la ciudad a un nombre con hermanos",
     "    if pelado != corto and equipos.unico_dueno(pelado):",
     "    if pelado != corto:"),

    ("fad/equipos.py", "decir que cualquier nombre tiene un solo dueno",
     "    return len(duenos) == 1",
     "    return True"),

    ("build.py", "deduplicar sin ver los renombres que corren despues",
     "        return frozenset(correcciones.renombrado(pagina, x.jornada, l, v,\n"
     "                                                 x.goles_local, x.goles_visita))",
     "        return frozenset((l, v))"),

    # El abandonado que se recupera y el que se pierde no son lo mismo.
    ("fad/rsssf.py", "decir lo mismo del que se recupera y del que se pierde",
     "        hay = any(a.jornada == ronda and a.llave == llave and a.zona == zona",
     "        hay = True or any(a.jornada == ronda and a.llave == llave and a.zona == zona"),

    ("fad/rsssf.py", "preguntarle su continuacion a un partido dividido",
     "        if not texto.endswith(_SIN_DESENLACE):",
     "        if False:"),

    # Un partido programado con marcador cero no es un 0-0.
    ("fad/espn.py", "leer como resultado un partido que no se jugo",
     '        if ((comp.get("status") or {}).get("type") or {}).get("completed") is False:',
     "        if False:"),

    ("fad/espn.py", "descartar tambien los 0-0 de verdad",
     '        if ((comp.get("status") or {}).get("type") or {}).get("completed") is False:',
     '        if not ((comp.get("status") or {}).get("type") or {}).get("completed"):'),

    # La tanda vive en la pata donde se pateo, si la serie la explica. Los tres
    # lados: emparejar patas rotuladas distinto, exigir la serie antes de
    # escribir, y mirar el global y no la vuelta en el formato compacto.
    ("fad/validar.py", "no emparejar dos patas rotuladas distinto",
     "        return q.jornada == p.jornada or (bool(suya) and _ronda(q.jornada) == suya)",
     "        return q.jornada == p.jornada"),

    ("fad/rsssf.py", "escribir la tanda sin mirar si la serie quedo igualada",
     "        if validar.serie_igualada(p, fuera):",
     "        if True:"),

    ("fad/rsssf.py", "mirar la vuelta en vez del global en el formato compacto",
     "        if pen and ida[0] + vuelta[0] == ida[1] + vuelta[1]:",
     "        if pen and vuelta[0] == vuelta[1]:"),

    # La zona de una fase no es la zona de la otra, y un partido dividido se jugo
    # aunque no tenga fila. Los cinco lados: el agrupado, las dos cuentas que el
    # dividido toca, su alcance, y que llegue hasta el chequeo.
    ("fad/validar.py", "juntar por nombre las zonas de dos fases distintas",
     '            zonas.setdefault((p.llave or "", p.zona), []).append(p)',
     '            zonas.setdefault(("", p.zona), []).append(p)'),

    ("fad/validar.py", "no contar el partido dividido en la zona",
     "                jugados[local] += 1\n"
     "                jugados[visita] += 1\n"
     "                aparte += 1",
     "                pass"),

    ("fad/validar.py", "no contar el dividido en el todos-contra-todos",
     "            if una_vuelta and (len(partidos) + aparte) % una_vuelta:",
     "            if una_vuelta and len(partidos) % una_vuelta:"),

    ("fad/validar.py", "contar el dividido en una fase que no es la suya",
     "            if suya and suya != llave:\n                continue",
     "            if False:\n                continue"),

    ("fad/validar.py", "no pasarle los divididos al chequeo de zonas",
     "            avisos += chequeo(ps, en_curso, divididos)",
     "            avisos += chequeo(ps, en_curso)"),

    ("fad/correcciones.py", "perder el alcance del dividido en el camino",
     "    return [(d.local, d.visita, d.llave) for d in DIVIDIDOS if d.pagina == pagina]",
     '    return [(d.local, d.visita, "") for d in DIVIDIDOS if d.pagina == pagina]'),

    # El desbalance de la propia tabla convierte un "probable" en una prueba.
    ("fad/posiciones.py", "no mirar si el desbalance prueba la fila",
     "    if lo_prueba_el_desbalance:",
     "    if False:"),

    ("fad/posiciones.py", "afirmar la prueba con dos clubes desviados",
     "    if desviados != 1 or desbalanceada == 0:",
     "    if desbalanceada == 0:"),

    ("fad/posiciones.py", "afirmar la prueba sin mirar para que lado va",
     "    return (dgf == desbalanceada and dgc == 0) or "
     "(dgc == -desbalanceada and dgf == 0)",
     "    return (abs(dgf) == abs(desbalanceada) and dgc == 0) or "
     "(abs(dgc) == abs(desbalanceada) and dgf == 0)"),

    ("fad/posiciones.py", "sumar una tabla que no cubre a todos los que juegan",
     "    if juegan and juegan == set(publicada):",
     "    if True:"),

    # La foja que publica la fuente, como testigo de nuestra propia lectura.
    # Cada pieza del lector por separado, porque cada una falla en silencio: lo
    # que se pierde no da error, solo deja de cruzar.
    ("fad/rsssf.py", "dejar que la linea de guiones cierre la tabla",
     '        if set(pelada) <= {"-", " "}:',
     '        if False:'),

    ("fad/rsssf.py", "leer tambien las tablas sin el rotulo Final Table",
     '        if m := _FOJA.match(linea):\n            if abierta and zona in mapa:',
     '        if m := _FOJA.match(linea):\n            if zona in mapa:'),

    ("fad/rsssf.py", "exigirle dos espacios a la fila de la foja",
     '_FOJA = re.compile(r"^\\s*\\d+\\.(?:.+?)\\s+"',
     '_FOJA = re.compile(r"^\\s*\\d+\\.(?:.+?)\\s{2,}"'),

    ("fad/rsssf.py", "juntar por nombre las dos tablas de una misma zona",
     "    return [(z, f) for z, f in fuera if f]",
     "    j = {}\n"
     "    for z, f in fuera:\n"
     "        j.setdefault(z, []).extend(f)\n"
     "    return [(z, f) for z, f in j.items() if f]"),

    ("build.py", "mandar al club del interzonal a la zona ajena",
     "        de_la_zona[cuenta.most_common(1)[0][0]].add(club)",
     "        de_la_zona[cuenta.most_common()[-1][0]].add(club)"),

    ("build.py", "cruzar una tabla que no cubre la zona",
     "        if len(clubes) != len(filas):\n            continue",
     "        if False:\n            continue"),

    ("build.py", "cruzar una zona que trae dos tablas",
     "        if zona in repetidas:\n            continue",
     "        if False:\n            continue"),

    ("build.py", "volver a denunciar un club ya revisado a mano",
     "        elif any(correcciones.revisado(pagina, c) for c in clubes):",
     "        elif False:"),

    ("fad/posiciones.py", "mandar a releer un partido que la fuente ya respaldo",
     "    if respaldado:",
     "    if False:"),

    # El solapamiento como testigo de la localia, por los tres lados: no juzgar
    # nunca, juzgar con dos partidos, y juzgar al reves.
    ("build.py", "creerle la localia a una fuente que la pagina desmiente",
     "    if alreves * 2 > repetidas:",
     "    if False:"),

    ("build.py", "juzgar la localia con dos partidos en comun",
     "_MINIMO_PARA_JUZGAR = 8",
     "_MINIMO_PARA_JUZGAR = 1"),

    ("build.py", "no decir que la localia importada no tiene testigo",
     '                f"igual, pero esa localia no tiene testigo", False)',
     '                f"igual, pero esa localia no tiene testigo", False) if False else ("", False)'),

    ("build.py", "sin fecha, no ver el partido al reves",
     "        elif alreves in suyos:",
     "        elif False:"),

    ("build.py", "sin fecha, duplicar lo que la pagina ya trae",
     "        if mio in suyos:",
     "        if False:"),

    ("fad/espn.py", "leer la fase regular como si fuera una llave",
     '        if not ronda:\n            continue',
     '        ronda = ronda or "Fecha"\n        if False:\n            continue'),

    ("fad/espn.py", "usar la fecha cruda del feed, en UTC",
     'fecha=_fecha_argentina(e["date"]),',
     'fecha=e["date"][:10],'),

    # OJO CON EL ANCLA. `espn.leer` y `espn.leer_llaves` tienen el mismo bloque casi
    # palabra por palabra, y `leer` viene PRIMERO en el archivo: un snippet que sirva
    # para los dos muta el otro. Lo que los distingue es como llegan a `comp` --
    # `(e.get(...) or [{}])[0]` contra `e.get(..., [{}])[0]` --, asi que el ancla se
    # toma de ahi. Se descubrio porque el mutante sobrevivia: estaba mutando el
    # lector de fechas, donde este test no mira.
    ("fad/espn.py", "tomar la localia del orden y no de homeAway",
     '        comp = (e.get("competitions") or [{}])[0]\n'
     '        lados = {c.get("homeAway"): c for c in comp.get("competitors", [])}',
     '        comp = (e.get("competitions") or [{}])[0]\n'
     '        lados = dict(zip(("home", "away"), comp.get("competitors", [])))'),

    ("build.py", "no ver la localia al reves cuando la fecha coincide",
     "            if uno(otro.local, otro.local_art) != p_.local:",
     "            if False:"),

    ("build.py", "duplicar lo que la pagina ya trae",
     "        if (suyo, p_.fecha) in ya:",
     "        if False:"),

    ("fad/rsssf.py", "escribir la tanda aunque la pata no haya empatado",
     "if pen and gl == gv:",
     "if pen:"),

    ("fad/rsssf.py", "resolver un nombre ambiguo eligiendo cualquiera",
     "    if len(achicado) == 1:\n        return achicado.pop(), \"\"",
     "    if achicado:\n        return sorted(achicado)[0], \"\""),

    ("fad/rsssf.py", "no limpiar la nota partida en dos renglones",
     'limpio = re.sub(r"\\s{2,}[^\\[\\]]*\\]\\s*$", "", limpio)',
     "limpio = limpio"),

    ("fad/parser.py", "no leer la ronda escrita 'instancia'",
     'r"|Primera instancia|Segunda instancia|Tercera instancia|Cuarta instancia"\n    ',
     ""),

    ("fad/parser.py", "no leer la ronda escrita 'ronda'",
     'r"|Primera ronda|Segunda ronda|Tercera ronda|Cuarta ronda"\n    ',
     ""),

    ("fad/parser.py", "no leer la cuarta ni la quinta fase",
     "|Cuarta fase|Quinta fase",
     ""),

    ("fad/validar.py", "no saber que instancia es fase",
     '    "primera instancia": "primera fase",',
     '    "primera instancia": "primera instancia",'),

    ("fad/parser.py", "no conocer la fase final de la Copa",
     '          "Fase final i", "Fase final ii",\n',
     ""),

    ("fad/parser.py", "la fase final de la Copa al reves",
     '"Fase final i", "Fase final ii",',
     '"Fase final ii", "Fase final i",'),

    ("fad/validar.py", "agrupar por el nombre que trae la pagina",
     "        r = _ronda(p.jornada)",
     "        r = p.jornada"),

    ("fad/validar.py", "no despegar el numero de llave",
     'sin_numero = re.sub(r"\\s+\\d+$", "", j)',
     "sin_numero = j"),

    ("fad/validar.py", "no despegar la rama del torneo",
     'sin_rama = re.sub(r"^.+?\\s+-\\s+", "", j)',
     "sin_rama = j"),

    # La reconstruccion de rondas por plantel, por los tres lados que puede
    # fallar: no hacerla, hacerla cuando no junto nada, y ordenar al reves.
    ("fad/validar.py", "no reconstruir las rondas por el plantel",
     "        if 1 < len(porplantel) < len(clubes):",
     "        if False:"),

    ("fad/validar.py", "reconstruir aunque el plantel no junte nada",
     "        if 1 < len(porplantel) < len(clubes):",
     "        if 1 < len(porplantel):"),

    ("fad/validar.py", "el cuadro reconstruido, al reves",
     "            grupos = sorted(armados, key=lambda kv: min(x.fecha for x in kv[1]))",
     "            grupos = sorted(armados, key=lambda kv: min(x.fecha for x in kv[1]), reverse=True)"),

    ("fad/validar.py", "ninguna llave es paralela",
     "        if not any(clubes[a] & clubes[b]",
     "        if False and any(clubes[a] & clubes[b]"),

    ("fad/validar.py", "todas las llaves son paralelas",
     "        if not any(clubes[a] & clubes[b]",
     "        if True or any(clubes[a] & clubes[b]"),

    ("fad/dataset.py", "escribir siempre neutral=false",
     '"neutral": str(neutral if p.neutral is None else p.neutral).lower()',
     '"neutral": "false"'),

    # --- el padron ---
    ("fad/equipos.py", "darle el alias 'Gimnasia' al club equivocado (el de Mendoza)",
     '    Equipo("Gimnasia y Esgrima (LP)", 8,\n'
     '           ("Gimnasia", "Gimnasia y Esgrima La Plata", "Gimnasia (LP)")),\n'
     '    Equipo("Gimnasia y Esgrima (M)", 816,\n'
     '           ("Gimnasia (Mendoza)", "Gimnasia (M)", "Gimnasia y Esgrima de Mendoza",\n'
     '            "Gimnasia y Esgrima (Mendoza)")),',
     '    Equipo("Gimnasia y Esgrima (LP)", 8,\n'
     '           ("Gimnasia y Esgrima La Plata", "Gimnasia (LP)")),\n'
     '    Equipo("Gimnasia y Esgrima (M)", 816,\n'
     '           ("Gimnasia", "Gimnasia (Mendoza)", "Gimnasia (M)", "Gimnasia y Esgrima de Mendoza",\n'
     '            "Gimnasia y Esgrima (Mendoza)")),'),

    # --- el partido que la pagina tiene y no se puede leer ---
    # --- el resaltado contra sus propios digitos ---
    ("fad/parser.py", "acusar tambien cuando el color acompania a los digitos",
     "            if dice != segun_numeros:", "            if dice == segun_numeros:"),

    ("fad/parser.py", "tomar cualquier color por el azul del ganador",
     '_AZUL_DEL_GANADOR = re.compile(r"""bgcolor\\s*=\\s*["\']?#?(?:d0e7ff|doe7ff)\\b""", re.I)',
     '_AZUL_DEL_GANADOR = re.compile(r"""bgcolor""", re.I)'),

    ("fad/parser.py", "acusar a las filas con tanda de penales",
     "            if _TIENE_TANDA.search(celdas[k]):", "            if False:"),

    ("fad/parser.py", "acusar a las filas con nota al pie",
     "        if _TIENE_NOTA.search(bloque):", "        if False:"),

    ("fad/parser.py", "dejar que la hora entre como marcador",
     '_MARCADOR_SOLO = re.compile(r"^\\s*(\\d+)\\s*-\\s*(\\d+)\\s*$")',
     '_MARCADOR_SOLO = re.compile(r"^\\s*(\\d+)\\s*[-:]\\s*(\\d+)\\s*$")'),

    ("fad/parser.py", "acusar aunque haya dos celdas pintadas",
     "            if sum(pintadas) != 1:", "            if sum(pintadas) < 1:"),

    ("fad/parser.py", "acusar de nuevo lo que ya esta arbitrado",
     "                if (local, visita, gl, gv) in ya_arbitrados:",
     "                if False:"),

    ("fad/parser.py", "identificar lo arbitrado por el marcador arreglado",
     "                if (local, visita, gl, gv) in ya_arbitrados:",
     "                if (local, visita, gv, gl) in ya_arbitrados:"),

    ("fad/posiciones.py", "no distinguir la fila mal tipeada del partido al reves",
     "        if tuple(datos[1:3]) == tuple(contada[club][1:3]):",
     "        if False:"),

    ("fad/posiciones.py", "mandar a buscar un partido cuando los goles ya coinciden",
     "        if tuple(datos[1:3]) == tuple(contada[club][1:3]):",
     "        if tuple(datos[1:3]) != tuple(contada[club][1:3]):"),

    # --- el desvio verificado que no era nuestro ---
    ("fad/posiciones.py", "callar el desvio revisado tambien en `contrastar` sin mirar la pagina",
     "        if club not in contada or correcciones.revisado(pagina, club):" + chr(10) +
     "            continue" + chr(10) + "        pj2, gf2, gc2 = contada[club][:3]",
     "        if club not in contada or any(r.club == club for r in correcciones.REVISADOS):" + chr(10) +
     "            continue" + chr(10) + "        pj2, gf2, gc2 = contada[club][:3]"),

    ("fad/posiciones.py", "callar el desvio revisado en todas las paginas",
     "        if club not in contada or correcciones.revisado(pagina, club):" + chr(10) +
     "            continue" + chr(10) + "        pj, suyo = datos[0], tuple(datos[3:6])",
     "        if club not in contada or any(r.club == club for r in correcciones.REVISADOS):" + chr(10) +
     "            continue" + chr(10) + "        pj, suyo = datos[0], tuple(datos[3:6])"),

    ("fad/posiciones.py", "no callar nada aunque este revisado",
     "        if club not in contada or correcciones.revisado(pagina, club):" + chr(10) +
     "            continue" + chr(10) + "        pj, suyo = datos[0], tuple(datos[3:6])",
     "        if club not in contada:" + chr(10) +
     "            continue" + chr(10) + "        pj, suyo = datos[0], tuple(datos[3:6])"),

    ("fad/correcciones.py", "no denunciar la verificacion que caduco",
     "        if r.pagina != pagina:\n            continue",
     "        if True:\n            continue"),

    ("fad/correcciones.py", "dar por huerfano al que si engancha",
     "        elif r.club in desviados:\n            continue",
     "        elif False:\n            continue"),

    ("fad/posiciones.py", "preguntar por los desvios ya filtrados por revisado",
     "            if club not in propios:\n                continue",
     "            if club not in propios or correcciones.revisado(pagina, club):"
     "\n                continue"),

    # --- el resaltado contra la tabla ---
    ("fad/posiciones.py", "publicar la acusacion que la tabla ya contesto",
     "        if all(c in contesta for c in clubes):" + chr(10) + "            continue",
     "        if False:" + chr(10) + "            continue"),

    ("fad/posiciones.py", "callar la acusacion que la tabla acompania",
     "        if all(c in contesta for c in clubes):", "        if any(c in contesta for c in clubes):"),

    ("fad/posiciones.py", "dar por contestado aunque la tabla se desvie",
     "            if tuple(datos[3:6]) == tuple(propios[club][3:6]):" + chr(10) +
     "                contesta.add(club)",
     "            if True:" + chr(10) + "                contesta.add(club)"),

    ("fad/correcciones.py", "no agregar el partido que la pagina no deja leer",
     "        aplicadas += 1" + chr(10) + chr(10) + "    # Los homonimos van DESPUES",
     "        continue" + chr(10) + chr(10) + "    # Los homonimos van DESPUES"),

    ("fad/correcciones.py", "agregar el faltante aunque la pagina ya se lea bien",
     "        if any(p.jornada == fal.jornada and p.local == fal.local",
     "        if False and any(p.jornada == fal.jornada and p.local == fal.local"),

    ("fad/correcciones.py", "escribir la tanda del faltante al reves",
     "                          penales_local=(fal.penales or (None, None))[0]," + chr(10) +
     "                          penales_visita=(fal.penales or (None, None))[1],",
     "                          penales_local=(fal.penales or (None, None))[1]," + chr(10) +
     "                          penales_visita=(fal.penales or (None, None))[0],"),

    ("fad/correcciones.py", "dejarle al faltante la tanda del hermano de la jornada",
     "                          penales_local=(fal.penales or (None, None))[0]," + chr(10) +
     "                          penales_visita=(fal.penales or (None, None))[1],",
     "                          penales_local=(fal.penales or (h.penales_local, 0))[0]," + chr(10) +
     "                          penales_visita=(fal.penales or (0, h.penales_visita))[1],"),

    ("fad/correcciones.py", "inventar el contexto del faltante en vez de heredarlo",
     "        hermanos = [p for p in ps if p.jornada == fal.jornada]",
     "        hermanos = list(ps)"),

    # --- homonimos: el mismo nombre, dos clubes ---
    ("fad/correcciones.py", "no resolver el homonimo en los partidos",
     "            if p.local == h.dice:", "            if False:"),

    ("fad/correcciones.py", "aplicar el homonimo de una pagina en todas",
     "        if h.pagina != pagina:\n            continue\n        for p in ps:",
     "        for p in ps:"),

    ("fad/correcciones.py", "resolver el homonimo de la tabla en cualquier pagina",
     "        if h.pagina == pagina and h.dice == club:",
     "        if h.dice == club:"),

    ("fad/posiciones.py", "leer la tabla sin resolver los homonimos de la pagina",
     "    return correcciones.homonimo(pagina, equipos.canonizar(nombre, articulo))",
     "    return equipos.canonizar(nombre, articulo)"),

    ("fad/posiciones.py", "no denunciar la fila cuyo club no jugo",
     "            if club not in jugaron:", "            if False:"),

    ("fad/posiciones.py", "medir esa fila contra el torneo y no contra su alcance",
     "        jugaron = {p.local for p in ps if not alcance or p.llave == alcance}\n"
     "        jugaron |= {p.visita for p in ps if not alcance or p.llave == alcance}",
     "        jugaron = {p.local for p in ps} | {p.visita for p in ps}"),

    # --- el cuadro de llaves, segundo testigo de una copa ---
    ("build.py", "no cruzar la grilla contra el cuadro de llaves",
     "               for d in posiciones.fuera_del_cuadro(ps, texto, t.pagina)]",
     "               for d in []]"),

    ("fad/posiciones.py", "no nombrar al homonimo que si juega",
     "        hermanos = sorted(_homonimos_de(club) & juegan)",
     "        hermanos = []"),

    ("fad/parser.py", "cerrar el cuadro en el primer }} y no por balance",
     "                if hondo == 0:",
     "                if True:"),

    ("fad/parser.py", "dejarle el cierre de la plantilla al ultimo parametro",
     "                    yield texto[m.start():i - 2]",
     "                    yield texto[m.start():i]"),

    ("fad/parser.py", "partir los parametros del cuadro por cualquier pipe",
     '            if cuerpo[i] == "|" and hondo_l <= 0 and hondo_p <= 1:',
     '            if cuerpo[i] == "|":'),

    ("fad/parser.py", "tomar por club las marcas del cuadro (w/o, penales)",
     '            if not club or _NO_ES_CLUB.match(club) or re.fullmatch(r\"[\\d\\s.:-]*\", club):',
     "            if not club:"),

    # --- los cuatro chequeos del cruce, y el que mira la grilla ---
    ("fad/posiciones.py", "no denunciar el nombre pelado de la grilla",
     "        otros = sorted(_homonimos_de(club) & en_tabla & enlazados)",
     "        otros = []"),

    ("fad/posiciones.py", "denunciar el nombre pelado aunque la pagina lo enlace",
     '        if "(" in club or club in enlazados:',
     '        if "(" in club:'),

    ("fad/posiciones.py", "pedirle al homonimo solo que este enlazado, sin fila de tabla",
     "        otros = sorted(_homonimos_de(club) & en_tabla & enlazados)",
     "        otros = sorted(_homonimos_de(club) & enlazados)"),

    ("fad/posiciones.py", "buscar homonimos solo por el nombre canonico y no por los alias",
     "            if any(_sin_desambiguador(n) == base for n in (e.nombre, *e.alias))} - {club}",
     "            if _sin_desambiguador(e.nombre) == base} - {club}"),

    ("fad/posiciones.py", "descartar la fila que no cierra sin anotarla",
     "            if descartadas is not None:",
     "            if False:"),

    ("fad/posiciones.py", "usar la fila que no cierra consigo misma",
     "        if gf - gc != dif or pg + pe + pp != pj:" + chr(10) +
     "            # La fila no cierra sola, asi que no opina.",
     "        if False:" + chr(10) +
     "            # La fila no cierra sola, asi que no opina."),

    ("fad/posiciones.py", "opinar del PJ aunque se mueva la tabla entera",
     "        if not comunes or len(desviados) * 2 > len(comunes):",
     "        if not comunes:"),

    ("fad/posiciones.py", "no juntar en un aviso a los dos clubes del mismo partido",
     "            por_delta.setdefault(delta, []).append(c)",
     "            por_delta.setdefault(c, []).append(c)"),

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
     "    return {v: next(iter(d.values())) for v, d in vistos.items() if len(d) == 1}",
     "    return {v: next(iter(d.values())) for v, d in vistos.items()}"),

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
     "    if tiene != COLUMNAS:",
     "    if False:"),

    # ---- el paso del bot que decide si hay algo para commitear ----
    # Los tests de tests/test_workflows.py corren el bloque `run:` sacado del YAML,
    # asi que estos mutantes rompen el workflow DE VERDAD, no una copia.
    (".github/workflows/actualizar.yml", "el gate vuelve a mirar el working tree",
     "          git add data/\n          if git diff --cached --quiet -- data/; then",
     "          if git diff --quiet -- data/; then"),

    (".github/workflows/actualizar.yml", "medir el delta sin mirar el indice",
     "delta=$(git diff --cached --numstat -- data/",
     "delta=$(git diff --numstat -- data/"),

    (".github/workflows/actualizar.yml", "el gate contesta que si siempre",
     "if git diff --cached --quiet -- data/; then",
     "if false; then"),
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

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

    ("fad/parser.py", "no cortar en el cierre |} de tabla",
     'bloque = re.sub(r"\\n\\|\\}", "\\n|-", bloque)',
     'bloque = bloque'),

    ("fad/parser.py", "no reconocer 'Interzonal' como etiqueta de seccion",
     '            else:\n                zona = _seccion(cab)',
     '            elif re.match(r"(?i)(zona|grupo)\\b", cab):\n                zona = _seccion(cab)'),

    ("fad/parser.py", "no unificar Interzonal/Interzonales",
     '    if re.match(r"(?i)^interzonal", cab):\n        return "Interzonal"',
     '    pass'),

    ("fad/parser.py", "ignorar el rowspan (asumir 6 celdas siempre)",
     "    return (int(n.group(1)) if n else 1), limpiar(m.group(2))",
     "    return 1, limpiar(m.group(2))"),

    ("fad/parser.py", "no limpiar el rowspan pendiente entre secciones",
     "            pendientes.clear()      # un rowspan no cruza de una seccion a otra",
     "            pass"),

    ("fad/parser.py", "leer los penales de los parentesis del entretiempo",
     '        pen = _marcador(limpiar(campos.get("resultado penalti", "")))',
     '        import re as _r; _m = _r.search(r"\\((\\d+)\\D+(\\d+)\\)", campos.get("resultado", "")); '
     'pen = (int(_m.group(1)), int(_m.group(2))) if _m else None'),

    ("fad/parser.py", "tomar el mes equivocado en la fecha",
     "    return f\"{anio}-{mes:02d}-{int(m.group(1)):02d}\" if mes else \"\"",
     "    return f\"{anio}-{(mes % 12) + 1:02d}-{int(m.group(1)):02d}\" if mes else \"\""),

    ("fad/validar.py", "que el ganador de los penales sea el que perdio la tanda",
     "        return p.local if p.penales_local > p.penales_visita else p.visita",
     "        return p.local if p.penales_local < p.penales_visita else p.visita"),

    ("fad/validar.py", "no chequear que nadie juegue dos veces por fecha",
     "        repiten = [e for e, n in cuenta.items() if n > 1]",
     "        repiten = []"),

    ("fad/validar.py", "aceptar penales en partidos que no empataron",
     "            if p.penales_local is not None and p.goles_local != p.goles_visita]",
     "            if False]"),

    ("fad/validar.py", "no mirar si falta la zona",
     '    sin = [p for p in ps if p.fase == "zonas" and not p.zona]',
     "    sin = []"),

    ("fad/dataset.py", "escribir el CSV sin ordenar",
     "    filas = sorted(filas, key=_orden)",
     "    filas = list(filas)"),

    # el mutante "escribir None en vez de cadena vacia" se saco: resulto
    # EQUIVALENTE. El modulo csv ya escribe None como campo vacio, asi que la
    # rama `"" if ... is None` no cambiaba el archivo. Se simplifico el codigo.
    ("fad/dataset.py", "escribir el CSV sin encabezado",
     "        w.writeheader()",
     "        pass"),

    ("fad/dataset.py", "aceptar campos de mas en silencio",
     'w = csv.DictWriter(f, fieldnames=COLUMNAS, extrasaction="raise")',
     'w = csv.DictWriter(f, fieldnames=COLUMNAS, extrasaction="ignore")'),

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
    else:
        print(f"Los {len(MUTANTES)} mutantes murieron.")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

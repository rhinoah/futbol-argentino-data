"""El paso del bot diario que decide si hay algo para commitear.

Estos tests EJECUTAN el bloque `run:` sacado del YAML, no una copia pegada aca.
Es la unica forma de que sigan probando el workflow y no un fosil suyo: una copia
se desincroniza el dia que alguien toca el YAML, y el test queda verde probando
algo que ya no corre en ningun lado -- que es peor que no tener test, porque
parece que algo se esta mirando.

Lo que se cuida es un modo de falla que este repo ya sufrio dos veces seguidas, y
las dos en SILENCIO, con el job en verde:

  - la primera, el REPORTE quedo ciego: media `git diff --numstat` sobre
    `data/partidos.csv`, un archivo que dejo de existir cuando el dataset se
    partio en uno por anio. Seis commits salieron diciendo "Actualizar dataset
    ( filas)".
  - la segunda, el GATE quedo ciego: preguntaba con `git diff -- data/`, que
    compara el working tree contra el indice y no ve un archivo que todavia no
    esta trackeado. Como `escribir_por_temporada` escribe un archivo por
    temporada, la primera corrida de una temporada nueva contestaba "no cambio
    nada" y ese archivo no se publicaba nunca.
"""
from __future__ import annotations

import os
import re
import shutil
import subprocess
from pathlib import Path

import pytest

WORKFLOW = Path(__file__).resolve().parents[1] / ".github/workflows/actualizar.yml"

def bash_que_ande() -> str | None:
    """Un bash que REALMENTE arranque, no uno que figure en el PATH.

    En Windows `which("bash")` puede devolver el stub de WSL, que existe como
    archivo y explota al ejecutarse si WSL no esta instalado. Se prueba antes de
    confiar: si no contesta, se busca el de Git, y si tampoco, se saltea.
    """
    candidatos = [shutil.which("bash")]
    git = shutil.which("git")
    if git:
        # .../Git/mingw64/bin/git.exe -> .../Git/bin/bash.exe
        raiz = Path(git).resolve().parents[2]
        candidatos += [str(raiz / "bin/bash.exe"), str(raiz / "usr/bin/bash.exe")]
    for c in candidatos:
        if not c or not Path(c).exists():
            continue
        try:
            r = subprocess.run([c, "-c", "echo ok"], capture_output=True, text=True, timeout=30)
        except OSError:
            continue
        if r.returncode == 0 and r.stdout.strip() == "ok":
            return c
    return None


BASH = bash_que_ande()

sin_bash = pytest.mark.skipif(BASH is None,
                              reason="hace falta un bash que ande para correr el bloque del YAML")


def bloque_del_paso(nombre: str) -> str:
    """El `run: |` del paso que se llama `nombre`, tal cual sale del YAML.

    A mano y sin pyyaml, que no es dependencia del proyecto. Es un parseo
    chiquito y si el YAML cambia de forma revienta acá, con nombre y apellido, en
    vez de devolver texto vacio y dejar pasar un test que no probo nada.
    """
    lineas = WORKFLOW.read_text(encoding="utf-8").splitlines()
    for i, l in enumerate(lineas):
        if re.fullmatch(rf"\s*-\s*name:\s*{re.escape(nombre)}\s*", l):
            break
    else:
        raise AssertionError(f"no hay ningun paso llamado {nombre!r} en {WORKFLOW.name}")

    for j in range(i + 1, len(lineas)):
        if re.fullmatch(r"\s*run:\s*\|\s*", lineas[j]):
            break
        if re.fullmatch(r"\s*-\s*name:.*", lineas[j]):
            raise AssertionError(f"el paso {nombre!r} no tiene un `run: |`")
    else:
        raise AssertionError(f"el paso {nombre!r} no tiene un `run: |`")

    sangria = len(lineas[j]) - len(lineas[j].lstrip()) + 2
    cuerpo = []
    for l in lineas[j + 1:]:
        if l.strip() and (len(l) - len(l.lstrip())) < sangria:
            break
        cuerpo.append(l[sangria:] if l.strip() else "")
    texto = "\n".join(cuerpo)
    assert texto.strip(), f"el `run:` de {nombre!r} salio vacio"
    return texto


def repo(tmp_path: Path) -> Path:
    """Un repo de verdad con un archivo por temporada ya commiteado."""
    subprocess.run(["git", "init", "-q", "."], cwd=tmp_path, check=True)
    for k, v in (("user.email", "t@t"), ("user.name", "t")):
        subprocess.run(["git", "config", k, v], cwd=tmp_path, check=True)
    (tmp_path / "data").mkdir()
    (tmp_path / "data/partidos-2026.csv").write_text(
        "date,home_team,away_team\n2026-01-01,A,B\n", encoding="utf-8")
    subprocess.run(["git", "add", "-A", "."], cwd=tmp_path, check=True)
    subprocess.run(["git", "commit", "-qm", "base"], cwd=tmp_path, check=True)
    return tmp_path


def correr_el_gate(carpeta: Path) -> dict[str, str]:
    """Corre el bloque del YAML y devuelve lo que dejo en $GITHUB_OUTPUT."""
    salida = carpeta / "github_output.txt"
    salida.write_text("", encoding="utf-8")
    # El entorno se COPIA y se le agrega la variable, no se reemplaza: en Windows
    # un env pelado se lleva puesto SYSTEMROOT y compania, y el proceso ni arranca
    # -- el sintoma es un error del registro COM+, que no dice nada de esto.
    entorno = {**os.environ, "GITHUB_OUTPUT": str(salida)}
    r = subprocess.run([BASH, "-c", bloque_del_paso("Ver si cambio algo")],
                       cwd=carpeta, env=entorno, capture_output=True, text=True)
    assert r.returncode == 0, f"el bloque fallo:\n{r.stdout}\n{r.stderr}"
    return dict(l.split("=", 1) for l in salida.read_text(encoding="utf-8").splitlines() if "=" in l)


# --------------------------------------------------------------------------
@sin_bash
def test_una_temporada_nueva_no_pasa_desapercibida(tmp_path):
    """LA REGRESION. Un archivo que todavia no esta trackeado es exactamente lo
    que escribe la primera corrida de una temporada nueva, y el gate viejo --
    `git diff` contra el working tree -- no lo veia: contestaba "no cambio nada"
    y el archivo no se publicaba nunca, con el job en verde."""
    d = repo(tmp_path)
    (d / "data/partidos-2027.csv").write_text(
        "date,home_team,away_team\n2027-02-01,A,B\n", encoding="utf-8")

    out = correr_el_gate(d)
    assert out["hay"] == "si"
    assert out["delta"] == "+2 -0 filas en 1 archivo(s)"


@sin_bash
def test_si_no_cambio_nada_no_inventa_un_commit(tmp_path):
    """El testigo del de arriba. Un gate que contesta "si" siempre tambien esta
    roto, solo que ruidoso en vez de callado: commitearia todos los dias sin
    nada que commitear."""
    assert correr_el_gate(repo(tmp_path))["hay"] == "no"


@sin_bash
def test_un_archivo_ya_trackeado_se_sigue_viendo(tmp_path):
    """Que arreglar lo de arriba no rompa lo que ya andaba: el caso comun es una
    temporada en curso, que es un archivo viejo con filas nuevas."""
    d = repo(tmp_path)
    (d / "data/partidos-2026.csv").write_text(
        "date,home_team,away_team\n2026-01-01,A,B\n2026-01-08,C,D\n", encoding="utf-8")

    out = correr_el_gate(d)
    assert out["hay"] == "si"
    assert out["delta"] == "+1 -0 filas en 1 archivo(s)"


@sin_bash
def test_un_archivo_borrado_tambien_cuenta(tmp_path):
    """Y la baja, que es el caso al que `git add data/` podria no llegar. Se
    midio que llega -- por eso no hace falta `-A` --, y esto lo deja fijado."""
    d = repo(tmp_path)
    (d / "data/partidos-2026.csv").unlink()

    out = correr_el_gate(d)
    assert out["hay"] == "si"
    assert out["delta"] == "+0 -2 filas en 1 archivo(s)"


@sin_bash
def test_el_delta_nunca_queda_mudo(tmp_path):
    """El parentesis vacio de las seis corridas. Si por lo que sea el numstat no
    da nada, el mensaje tiene que decirlo en vez de salir "( filas)"."""
    assert "delta=${delta:-sin detalle}" in bloque_del_paso("Ver si cambio algo")

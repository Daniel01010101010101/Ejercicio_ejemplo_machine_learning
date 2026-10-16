"""Pruebas de scripts/entrenar.py con datos pequeños inventados (corren en segundos).

    python -m pytest tests/
"""
import json
import subprocess
import sys
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

RAIZ = Path(__file__).resolve().parent.parent
SCRIPT = RAIZ / "scripts" / "entrenar.py"


def entrenar(*argumentos):
    return subprocess.run([sys.executable, str(SCRIPT), *map(str, argumentos)],
                          capture_output=True, text=True, cwd=RAIZ, timeout=300)


@pytest.fixture(scope="module")
def csv(tmp_path_factory):
    """600 estudiantes inventados: la nota depende de las horas de estudio y de la jornada."""
    azar = np.random.default_rng(7)
    n = 600
    horas = azar.uniform(0, 10, n)
    jornada = azar.choice(["Mañana", "Tarde", "Noche"], n)
    asistencia = azar.uniform(50, 100, n)
    asistencia[azar.random(n) < 0.05] = np.nan  # algunos vacíos
    nota = 1 + 0.3 * horas + np.select([jornada == "Mañana", jornada == "Tarde"], [0.6, 0.3], 0) \
        + 0.01 * np.nan_to_num(asistencia, nan=75) + azar.normal(0, 0.2, n)
    datos = pd.DataFrame({"horas_estudio": horas.round(1), "jornada": jornada, "asistencia": asistencia.round(0),
                          "nota_final": nota.round(2)})
    datos["aprobo"] = np.where(datos["nota_final"] >= datos["nota_final"].median(), "Sí", "No")
    ruta = tmp_path_factory.mktemp("datos") / "notas.csv"
    datos.to_csv(ruta, index=False)
    return ruta


def test_regresion_le_gana_a_la_linea_base(csv, tmp_path):
    r = entrenar("--datos", csv, "--objetivo", "nota_final", "--variables", "horas_estudio, jornada, asistencia",
                 "--modelo", "boosting", "--salida", tmp_path)
    assert r.returncode == 0, r.stderr
    metricas = json.loads((tmp_path / "metricas.json").read_text(encoding="utf-8"))
    claves = [f["clave"] for f in metricas["comparacion"]]
    assert claves == ["linea_base", "lineal", "arbol", "bosque", "boosting"]
    base, publicado = metricas["comparacion"][0], metricas["comparacion"][-1]
    assert publicado.get("publicado") and publicado["mae"] < 0.5 * base["mae"]
    assert (tmp_path / "modelo.js").read_text(encoding="utf-8").startswith("// Generado por el cuaderno")
    assert "| Gradient Boosting |" in r.stdout


def test_clase_estima_probabilidad_y_exactitud(csv, tmp_path):
    r = entrenar("--datos", csv, "--objetivo", "aprobo", "--clase-positiva", "Sí",
                 "--variables", "horas_estudio, jornada", "--excluir", "nota_final", "--salida", tmp_path)
    assert r.returncode == 0, r.stderr
    metricas = json.loads((tmp_path / "metricas.json").read_text(encoding="utf-8"))
    assert metricas["es_clase"] and metricas["clase_positiva"] == "Sí"
    assert all("exactitud" in f for f in metricas["comparacion"])
    assert "Exactitud" in r.stdout


def test_columna_que_no_existe_da_un_error_claro(csv, tmp_path):
    r = entrenar("--datos", csv, "--objetivo", "nota", "--salida", tmp_path)
    assert r.returncode == 1
    assert "No encuentro la columna OBJETIVO = 'nota'" in r.stderr
    assert "Traceback" not in r.stderr


def test_datos_sin_objetivo_pide_el_objetivo(csv):
    r = entrenar("--datos", csv)
    assert r.returncode == 2 and "--objetivo" in r.stderr


def test_publicar_copia_a_web_si_pasa_la_paridad(csv, tmp_path):
    web = tmp_path / "web"
    web.mkdir()
    r = entrenar("--datos", csv, "--objetivo", "nota_final", "--variables", "horas_estudio, jornada",
                 "--salida", tmp_path / "salida", "--publicar", "--web", web)
    assert r.returncode == 0, r.stderr
    assert (web / "modelo.js").exists() and (web / "modelo.json").exists()
    assert "Publicado en" in r.stdout


def test_publicar_exige_ganarle_a_la_linea_base(tmp_path):
    azar = np.random.default_rng(3)
    ruido = pd.DataFrame({"x": azar.uniform(0, 1, 300), "y": azar.normal(0, 1, 300)})
    ruta = tmp_path / "ruido.csv"
    ruido.to_csv(ruta, index=False)
    web = tmp_path / "web"
    web.mkdir()
    r = entrenar("--datos", ruta, "--objetivo", "y", "--variables", "x", "--salida", tmp_path / "salida",
                 "--publicar", "--web", web)
    assert r.returncode == 1 and "No se publicó" in r.stderr
    assert not (web / "modelo.js").exists()

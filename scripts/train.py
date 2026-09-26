#!/usr/bin/env python3
"""Entrena el Predictor Saber 11 y exporta el modelo para la página web.

Hace lo mismo que el cuaderno notebooks/saber11_modelo.ipynb, pero sin
explicaciones ni gráficas, para re-entrenar desde la terminal:

    python scripts/train.py                  # usa el periodo más reciente
    python scripts/train.py --periodo 20224  # fuerza un periodo

Pasos:
 1. Descarga desde la API de datos.gov.co SOLO el periodo elegido
    (filtro $where + páginas de 50 000 filas) y lo guarda en datos/.
 2. Limpia: puntaje a número, quita filas sin puntaje, faltantes -> "Sin información".
 3. Separa train/test ANTES de ajustar cualquier cosa.
 4. Agrupa las categorías con muy pocos casos (aprendido SOLO con train).
 5. Entrena OneHotEncoder + Ridge y lo compara con una línea base y con
    HistGradientBoosting.
 6. Exporta web/modelo.js y web/modelo.json.
 7. Prueba de paridad: Node recalcula las predicciones y deben coincidir con
    scikit-learn (tolerancia 1e-6).

Requisitos: pandas, numpy, scikit-learn, requests (y Node.js para la paridad).
"""

from __future__ import annotations

import argparse
import datetime as dt
import io
import json
import math
import shutil
import subprocess
import sys
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import numpy as np
import pandas as pd
import requests
import sklearn
from sklearn.compose import ColumnTransformer
from sklearn.dummy import DummyRegressor
from sklearn.ensemble import HistGradientBoostingRegressor
from sklearn.linear_model import Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.model_selection import train_test_split
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder

RAIZ = Path(__file__).resolve().parent.parent

# ---------------------------------------------------------------------------
# Configuración
# ---------------------------------------------------------------------------
VERSION = "1.0.0"
DATASET_ID = "kgxf-xxbe"
API = f"https://www.datos.gov.co/resource/{DATASET_ID}"
URL_CONJUNTO = f"https://www.datos.gov.co/d/{DATASET_ID}"

OBJETIVO = "punt_global"
SIN_INFO = "Sin información"
OTRA = "Otra (pocos casos)"

# Variables candidatas del enunciado (todas categóricas, todas llegan como texto).
CANDIDATAS = [
    "fami_estratovivienda",
    "fami_educacionmadre",
    "fami_educacionpadre",
    "fami_tieneinternet",
    "fami_tienecomputador",
    "fami_tieneautomovil",
    "cole_naturaleza",
    "cole_jornada",
    "cole_area_ubicacion",
    "cole_bilingue",
    "cole_depto_ubicacion",
]

# Variables que usa el modelo (9 campos en el formulario). Se quitan dos candidatas,
# según la validación dentro de train que muestra el cuaderno (sección 4):
#  - fami_tieneautomovil: sin ella el MAE de validación cambia en 0,01 puntos; su
#    información ya la traen el estrato, el computador y el internet.
#  - cole_bilingue: la peor calidad (18 % de faltantes, solo 1 % de "S") y un aporte
#    mínimo (0,04 puntos de MAE).
VARIABLES = [
    "fami_estratovivienda",
    "fami_educacionmadre",
    "fami_educacionpadre",
    "fami_tieneinternet",
    "fami_tienecomputador",
    "cole_naturaleza",
    "cole_jornada",
    "cole_area_ubicacion",
    "cole_depto_ubicacion",
]

MOTIVOS_FUERA = {
    "fami_tieneautomovil": "Casi no aporta en validación: su información ya la traen el estrato, el computador y el internet.",
    "cole_bilingue": "La peor calidad de datos (18 % de faltantes) y un aporte mínimo en validación.",
}

# Columnas extra que se descargan solo para verificar y filtrar (no entran al modelo).
COLUMNAS_EXTRA = ["periodo", "estu_consecutivo", "estu_estadoinvestigacion"]

SEMILLA = 42
PROPORCION_PRUEBA = 0.2
MIN_CASOS = 200  # una categoría con menos casos en train se agrupa en OTRA
ALPHA = 1.0

# Nombre, etiqueta corta, grupo y ayuda de cada variable (para el formulario).
INFO_VARIABLES = {
    "fami_estratovivienda": ("Estrato de la vivienda", "Estrato", "hogar",
                             "Aparece en los recibos de servicios públicos."),
    "fami_educacionmadre": ("Nivel educativo de la madre", "Educación de la madre", "hogar",
                            "El nivel más alto que alcanzó."),
    "fami_educacionpadre": ("Nivel educativo del padre", "Educación del padre", "hogar",
                            "El nivel más alto que alcanzó."),
    "fami_tieneinternet": ("¿Hay internet en el hogar?", "Internet en el hogar", "hogar", ""),
    "fami_tienecomputador": ("¿Hay computador en el hogar?", "Computador en el hogar", "hogar", ""),
    "fami_tieneautomovil": ("¿La familia tiene automóvil?", "Automóvil", "hogar", ""),
    "cole_naturaleza": ("Tipo de colegio", "Tipo de colegio", "colegio",
                        "Oficial es público; no oficial es privado."),
    "cole_jornada": ("Jornada del colegio", "Jornada", "colegio", ""),
    "cole_area_ubicacion": ("Zona donde está el colegio", "Zona del colegio", "colegio", ""),
    "cole_bilingue": ("¿El colegio es bilingüe?", "Colegio bilingüe", "colegio", ""),
    "cole_depto_ubicacion": ("Departamento del colegio", "Departamento", "colegio", ""),
}

# Etiquetas legibles y orden lógico de las categorías. Las llaves se comparan
# sin tildes y en mayúsculas (ver clave()), así que toleran variantes como
# "BOGOTÁ"/"BOGOTA". Revisadas contra los valores únicos reales del periodo.
EDUCACION = [
    ("NINGUNO", "Ninguno"),
    ("PRIMARIA INCOMPLETA", "Primaria incompleta"),
    ("PRIMARIA COMPLETA", "Primaria completa"),
    ("SECUNDARIA (BACHILLERATO) INCOMPLETA", "Bachillerato incompleto"),
    ("SECUNDARIA (BACHILLERATO) COMPLETA", "Bachillerato completo"),
    ("TECNICA O TECNOLOGICA INCOMPLETA", "Técnica o tecnológica incompleta"),
    ("TECNICA O TECNOLOGICA COMPLETA", "Técnica o tecnológica completa"),
    ("EDUCACION PROFESIONAL INCOMPLETA", "Universitaria incompleta"),
    ("EDUCACION PROFESIONAL COMPLETA", "Universitaria completa"),
    ("POSTGRADO", "Posgrado"),
    ("NO SABE", "No sabe"),
    ("NO APLICA", "No aplica"),
]
SI_NO = [("SI", "Sí"), ("S", "Sí"), ("NO", "No"), ("N", "No")]
CATEGORIAS = {
    "fami_estratovivienda": [
        ("ESTRATO 1", "Estrato 1"), ("ESTRATO 2", "Estrato 2"), ("ESTRATO 3", "Estrato 3"),
        ("ESTRATO 4", "Estrato 4"), ("ESTRATO 5", "Estrato 5"), ("ESTRATO 6", "Estrato 6"),
        ("SIN ESTRATO", "Sin estrato"),
    ],
    "fami_educacionmadre": EDUCACION,
    "fami_educacionpadre": EDUCACION,
    "fami_tieneinternet": SI_NO,
    "fami_tienecomputador": SI_NO,
    "fami_tieneautomovil": SI_NO,
    "cole_naturaleza": [("OFICIAL", "Oficial (público)"), ("NO OFICIAL", "No oficial (privado)")],
    "cole_jornada": [
        ("MANANA", "Mañana"), ("TARDE", "Tarde"), ("COMPLETA", "Completa"), ("UNICA", "Única"),
        ("NOCHE", "Noche"), ("SABATINA", "Sabatina"),
    ],
    "cole_area_ubicacion": [("URBANO", "Urbana"), ("RURAL", "Rural")],
    "cole_bilingue": SI_NO,
    "cole_depto_ubicacion": [
        ("AMAZONAS", "Amazonas"), ("ANTIOQUIA", "Antioquia"), ("ARAUCA", "Arauca"),
        ("ATLANTICO", "Atlántico"), ("BOGOTA", "Bogotá D. C."), ("BOGOTA D.C.", "Bogotá D. C."),
        ("BOGOTA, D.C.", "Bogotá D. C."), ("BOLIVAR", "Bolívar"), ("BOYACA", "Boyacá"),
        ("CALDAS", "Caldas"), ("CAQUETA", "Caquetá"), ("CASANARE", "Casanare"),
        ("CAUCA", "Cauca"), ("CESAR", "Cesar"), ("CHOCO", "Chocó"), ("CORDOBA", "Córdoba"),
        ("CUNDINAMARCA", "Cundinamarca"), ("GUAINIA", "Guainía"), ("GUAVIARE", "Guaviare"),
        ("HUILA", "Huila"), ("LA GUAJIRA", "La Guajira"), ("GUAJIRA", "La Guajira"),
        ("MAGDALENA", "Magdalena"), ("META", "Meta"), ("NARINO", "Nariño"),
        ("NORTE SANTANDER", "Norte de Santander"), ("NORTE DE SANTANDER", "Norte de Santander"),
        ("PUTUMAYO", "Putumayo"), ("QUINDIO", "Quindío"), ("RISARALDA", "Risaralda"),
        ("SAN ANDRES", "San Andrés y Providencia"),
        ("ARCHIPIELAGO DE SAN ANDRES, PROVIDENCIA Y SANTA CATALINA", "San Andrés y Providencia"),
        ("SANTANDER", "Santander"), ("SUCRE", "Sucre"), ("TOLIMA", "Tolima"),
        ("VALLE", "Valle del Cauca"), ("VALLE DEL CAUCA", "Valle del Cauca"),
        ("VAUPES", "Vaupés"), ("VICHADA", "Vichada"), ("EXTRANJERO", "Extranjero"),
    ],
}
# Variables sin orden natural: sus categorías se ordenan alfabéticamente por etiqueta.
ORDEN_ALFABETICO = {"cole_depto_ubicacion"}


def clave(texto: str) -> str:
    """Normaliza un texto para compararlo: sin tildes, mayúsculas y espacios simples."""
    sin_tildes = unicodedata.normalize("NFKD", str(texto)).encode("ascii", "ignore").decode()
    return " ".join(sin_tildes.upper().split())


# ---------------------------------------------------------------------------
# 1. Descarga desde la API Socrata de datos.gov.co
# ---------------------------------------------------------------------------
def socrata(params: dict, formato: str = "json", intentos: int = 6) -> requests.Response:
    """GET a la API con reintentos (la API a veces responde lento o con 5xx)."""
    url = f"{API}.{formato}"
    for intento in range(1, intentos + 1):
        try:
            respuesta = requests.get(url, params=params, timeout=180)
            respuesta.raise_for_status()
            return respuesta
        except requests.RequestException as error:
            if intento == intentos:
                raise
            espera = 2 ** intento
            print(f"   aviso: {error}. Reintento {intento}/{intentos - 1} en {espera} s")
            time.sleep(espera)
    raise RuntimeError("inalcanzable")


def consultar_periodos() -> pd.DataFrame:
    """Periodos disponibles y número de filas de cada uno (del más reciente al más viejo)."""
    datos = socrata({"$select": "periodo, count(*) AS filas", "$group": "periodo",
                     "$order": "periodo DESC"}).json()
    tabla = pd.DataFrame(datos)
    tabla["filas"] = tabla["filas"].astype(int)
    return tabla


def descargar_periodo(periodo: str, columnas: list[str], carpeta: Path,
                      tam_pagina: int = 50_000, en_paralelo: int = 4) -> pd.DataFrame:
    """Descarga SOLO un periodo, por páginas, y lo guarda en caché como CSV."""
    ruta = carpeta / f"saber11_{periodo}.csv"
    if ruta.exists():
        print(f"   usando la copia local {ruta.name}")
        return pd.read_csv(ruta, dtype=str, keep_default_na=False, na_values=[""])

    filtro = f"periodo = '{periodo}'"
    total = int(socrata({"$select": "count(*) AS filas", "$where": filtro}).json()[0]["filas"])
    print(f"   {total:,} filas en el periodo {periodo}; se descargan en páginas de {tam_pagina:,}".replace(",", "."))

    def pagina(inicio: int) -> pd.DataFrame:
        respuesta = socrata({
            "$select": ",".join(columnas),
            "$where": filtro,
            "$order": ":id",          # orden estable para que las páginas no se crucen
            "$limit": tam_pagina,
            "$offset": inicio,
        }, formato="csv")
        # dtype=str: todo llega como texto. keep_default_na=False evita que pandas
        # convierta textos como "NA" en faltantes; solo la celda vacía es faltante.
        return pd.read_csv(io.StringIO(respuesta.text), dtype=str,
                           keep_default_na=False, na_values=[""])

    # Varias páginas a la vez (el servidor tarda unos segundos en preparar cada una).
    inicios = list(range(0, total, tam_pagina))
    partes = [None] * len(inicios)
    with ThreadPoolExecutor(max_workers=en_paralelo) as grupo:
        tareas = {grupo.submit(pagina, inicio): i for i, inicio in enumerate(inicios)}
        for listas, tarea in enumerate(as_completed(tareas), start=1):
            partes[tareas[tarea]] = tarea.result()
            print(f"   página {listas}/{len(inicios)} lista")
    datos = pd.concat(partes, ignore_index=True)
    if len(datos) != total:
        raise RuntimeError(f"Se esperaban {total} filas y llegaron {len(datos)}")
    carpeta.mkdir(parents=True, exist_ok=True)
    datos.to_csv(ruta, index=False)
    return datos


def quitar_duplicados(datos: pd.DataFrame) -> pd.DataFrame:
    """Deja una sola fila por estudiante (estu_consecutivo identifica cada examen)."""
    copias_exactas = int(datos.duplicated().sum())
    datos = datos.drop_duplicates()
    mismo_estudiante = int(datos["estu_consecutivo"].duplicated().sum())
    datos = datos.drop_duplicates(subset="estu_consecutivo", keep="first")
    print(f"   copias exactas eliminadas: {copias_exactas:,}".replace(",", "."))
    print(f"   filas del mismo estudiante con datos distintos (se deja la primera): {mismo_estudiante:,}".replace(",", "."))
    print(f"   estudiantes únicos: {len(datos):,}".replace(",", "."))
    return datos.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 2. Limpieza (fila por fila: no aprende nada de los datos)
# ---------------------------------------------------------------------------
def limpiar(datos: pd.DataFrame, variables: list[str]) -> pd.DataFrame:
    datos = datos.copy()
    datos[OBJETIVO] = pd.to_numeric(datos[OBJETIVO], errors="coerce")
    datos = datos[datos[OBJETIVO].between(0, 500)]  # también descarta los NaN
    if "estu_estadoinvestigacion" in datos.columns:
        # Solo resultados publicados (quita los que estaban bajo investigación).
        estado = datos["estu_estadoinvestigacion"].fillna("").map(clave)
        if (estado == "PUBLICAR").any():
            datos = datos[estado == "PUBLICAR"]
    for columna in variables:
        texto = datos[columna].fillna("").astype(str).str.strip()
        datos[columna] = texto.replace("", SIN_INFO)
    return datos.reset_index(drop=True)


# ---------------------------------------------------------------------------
# 3. Categorías raras (se aprende con train y se aplica igual a test)
# ---------------------------------------------------------------------------
def aprender_frecuentes(train: pd.DataFrame, variables: list[str], min_casos: int) -> dict:
    frecuentes = {}
    for columna in variables:
        conteo = train[columna].value_counts()
        frecuentes[columna] = set(conteo[conteo >= min_casos].index)
    return frecuentes


def agrupar_raras(datos: pd.DataFrame, frecuentes: dict) -> pd.DataFrame:
    datos = datos.copy()
    for columna, conservar in frecuentes.items():
        datos[columna] = datos[columna].where(datos[columna].isin(conservar), OTRA)
    return datos


# ---------------------------------------------------------------------------
# 4. Modelos y métricas
# ---------------------------------------------------------------------------
def crear_modelo(variables: list[str], alpha: float = ALPHA) -> Pipeline:
    preprocesamiento = ColumnTransformer(
        [("categoricas", OneHotEncoder(handle_unknown="ignore"), variables)])
    return Pipeline([("preprocesamiento", preprocesamiento),
                     ("regresion", Ridge(alpha=alpha))])


def crear_boosting(variables: list[str]) -> Pipeline:
    codificador = ColumnTransformer([("categoricas", OrdinalEncoder(
        handle_unknown="use_encoded_value", unknown_value=-1), variables)])
    boosting = HistGradientBoostingRegressor(
        categorical_features=list(range(len(variables))), random_state=SEMILLA)
    return Pipeline([("preprocesamiento", codificador), ("regresion", boosting)])


def metricas(y_real, y_pred) -> dict:
    return {
        "mae": float(mean_absolute_error(y_real, y_pred)),
        "rmse": float(math.sqrt(mean_squared_error(y_real, y_pred))),
        "r2": float(r2_score(y_real, y_pred)),
    }


# ---------------------------------------------------------------------------
# 5. Exportación a JavaScript
# ---------------------------------------------------------------------------
def etiqueta_categoria(variable: str, valor: str) -> str:
    if valor == SIN_INFO:
        return SIN_INFO
    if valor == OTRA:
        return OTRA
    for llave, etiqueta in CATEGORIAS.get(variable, []):
        if clave(valor) == llave:
            return etiqueta
    print(f"   aviso: sin etiqueta para {variable} = {valor!r}; se usa el texto original")
    return valor.capitalize()


def posicion_categoria(variable: str, valor: str, etiqueta: str) -> tuple:
    """Llave de orden: orden lógico del diccionario; al final 'Sin información' y 'Otra'."""
    if valor == SIN_INFO:
        return (2, 0, "")
    if valor == OTRA:
        return (3, 0, "")
    if variable in ORDEN_ALFABETICO:
        return (0, 0, clave(etiqueta))
    llaves = [llave for llave, _ in CATEGORIAS.get(variable, [])]
    return (0, llaves.index(clave(valor)), "") if clave(valor) in llaves else (1, 0, clave(etiqueta))


def exportar_modelo(modelo: Pipeline, variables: list[str], x_train: pd.DataFrame,
                    y_train: pd.Series, extras: dict) -> dict:
    """Arma el diccionario que usa la página: intercepto + coeficientes por categoría."""
    codificador = modelo.named_steps["preprocesamiento"].named_transformers_["categoricas"]
    ridge = modelo.named_steps["regresion"]
    salida_variables = []
    inicio = 0
    for indice, variable in enumerate(variables):
        categorias = list(codificador.categories_[indice])
        coeficientes = ridge.coef_[inicio:inicio + len(categorias)]
        inicio += len(categorias)
        conteo = x_train[variable].value_counts()
        filas = []
        for valor, coeficiente in zip(categorias, coeficientes):
            etiqueta = etiqueta_categoria(variable, valor)
            fila = {
                "valor": str(valor),
                "etiqueta": etiqueta,
                "coeficiente": float(coeficiente),
                "frecuencia": float(conteo.get(valor, 0) / len(x_train)),
                "n": int(conteo.get(valor, 0)),
                # Una categoría con muy pocos casos sigue en el modelo, pero no se
                # ofrece como respuesta en el formulario.
                "en_formulario": bool(conteo.get(valor, 0) >= MIN_CASOS),
            }
            if valor == OTRA:
                agrupadas = [etiqueta_categoria(variable, r) for r in extras["raras"].get(variable, [])]
                fila["agrupa"] = sorted(set(agrupadas), key=clave)
            filas.append(fila)
        filas.sort(key=lambda f: posicion_categoria(variable, f["valor"], f["etiqueta"]))
        nombre, corta, grupo, ayuda = INFO_VARIABLES[variable]
        salida_variables.append({
            "nombre": variable,
            "etiqueta": nombre,
            "etiqueta_corta": corta,
            "grupo": grupo,
            "ayuda": ayuda,
            "mas_frecuente": str(conteo.idxmax()),
            "categorias": filas,
        })
    if inicio != len(ridge.coef_):
        raise RuntimeError("El número de coeficientes no coincide con las categorías")

    # Identidad útil para la gráfica de contribuciones:
    # intercepto + sum(frecuencia * coeficiente) = promedio de y en train.
    promedio_train = float(np.mean(y_train))
    reconstruido = float(ridge.intercept_) + sum(
        c["frecuencia"] * c["coeficiente"] for v in salida_variables for c in v["categorias"])
    if abs(reconstruido - promedio_train) > 1e-6:
        raise RuntimeError(f"La identidad del promedio falla: {reconstruido} vs {promedio_train}")

    return {
        "version": VERSION,
        "proyecto": "Predictor Saber 11",
        "fuente": {
            "nombre": "Resultados únicos Saber 11 (ICFES)",
            "portal": "datos.gov.co",
            "id": DATASET_ID,
            "url": URL_CONJUNTO,
        },
        "periodo": extras["periodo"],
        "periodo_etiqueta": extras["periodo_etiqueta"],
        "fecha_entrenamiento": extras["fecha"],
        "n_total": extras["n_total"],
        "n_entrenamiento": int(len(x_train)),
        "n_prueba": extras["n_prueba"],
        "semilla": SEMILLA,
        "min_casos": MIN_CASOS,
        "algoritmo": f"Ridge (alpha = {ALPHA:g}) con codificación one-hot",
        "sklearn_version": sklearn.__version__,
        "objetivo": {"nombre": OBJETIVO, "etiqueta": "Puntaje global", "minimo": 0, "maximo": 500},
        "metricas": extras["metricas"],
        "cobertura_mae": extras["cobertura_mae"],
        "promedio_nacional": extras["promedio_nacional"],
        "promedio_entrenamiento": promedio_train,
        "intercepto": float(ridge.intercept_),
        "variables": salida_variables,
        "excluidas": [
            {"nombre": "estu_genero",
             "motivo": "Decisión ética: el modelo no debe cambiar su predicción por el género."},
            {"nombre": "cole_nombre_establecimiento, cole_cod_dane_*, cole_codigo_icfes",
             "motivo": "Nombres y códigos de colegio: identifican instituciones y no describen el contexto."},
        ] + [{"nombre": v, "motivo": MOTIVOS_FUERA.get(v, "No mejora la validación.")}
             for v in CANDIDATAS if v not in variables],
        "casos_prueba": extras["casos_prueba"],
    }


def escribir_modelo(modelo_dict: dict, carpeta_web: Path) -> tuple[Path, Path]:
    carpeta_web.mkdir(parents=True, exist_ok=True)
    texto = json.dumps(modelo_dict, ensure_ascii=False, indent=2)
    ruta_json = carpeta_web / "modelo.json"
    ruta_js = carpeta_web / "modelo.js"
    ruta_json.write_text(texto + "\n", encoding="utf-8")
    ruta_js.write_text(
        "// Generado automáticamente por scripts/train.py o por el cuaderno.\n"
        "// No lo edites a mano: vuelve a entrenar y reemplaza este archivo.\n"
        f"window.MODELO = {texto};\n", encoding="utf-8")
    return ruta_js, ruta_json


def elegir_casos(modelo: Pipeline, x_train: pd.DataFrame, x_test: pd.DataFrame,
                 y_test: pd.Series, variables: list[str], cantidad: int = 5) -> list[dict]:
    """Casos del set de prueba repartidos entre predicciones bajas, medias y altas.

    Solo se eligen estudiantes cuyas respuestas aparecen en el formulario
    (categorías con al menos MIN_CASOS estudiantes en train), para poder cargarlos.
    """
    en_formulario = pd.Series(True, index=x_test.index)
    for v in variables:
        conteo = x_train[v].value_counts()
        en_formulario &= x_test[v].isin(conteo[conteo >= MIN_CASOS].index)
    x_test, y_test = x_test[en_formulario], y_test[en_formulario]
    predicciones = modelo.predict(x_test)
    orden = np.argsort(predicciones, kind="stable")
    cuantiles = np.linspace(0.05, 0.95, cantidad)
    casos = []
    for numero, q in enumerate(cuantiles, start=1):
        i = int(orden[int(round(q * (len(orden) - 1)))])
        fila = x_test.iloc[[i]]
        casos.append({
            "id": numero,
            "entradas": {v: str(fila.iloc[0][v]) for v in variables},
            "puntaje_real": float(y_test.iloc[i]),
            "prediccion_sklearn": float(modelo.predict(fila)[0]),
        })
    return casos


def prueba_paridad(ruta_modelo_js: Path, ruta_casos_extra: Path | None = None) -> bool:
    """Ejecuta scripts/prueba_paridad.js con Node (tolerancia 1e-6)."""
    node = shutil.which("node")
    if node is None:
        print("   aviso: no se encontró Node.js; instala Node y corre "
              "`node scripts/prueba_paridad.js web/modelo.js`")
        return False
    comando = [node, str(RAIZ / "scripts" / "prueba_paridad.js"), str(ruta_modelo_js)]
    if ruta_casos_extra is not None:
        comando.append(str(ruta_casos_extra))
    resultado = subprocess.run(comando, capture_output=True, text=True)
    print(resultado.stdout.rstrip())
    if resultado.returncode != 0:
        print(resultado.stderr.rstrip())
    return resultado.returncode == 0


def etiqueta_periodo(periodo: str) -> str:
    """'20224' -> '2022-2'. El ICFES usa 1 para el primer semestre y 2, 3 o 4 para el segundo."""
    if len(periodo) == 5 and periodo.isdigit():
        return f"{periodo[:4]}-{1 if periodo[4] == '1' else 2}"
    return periodo


# ---------------------------------------------------------------------------
# Programa principal
# ---------------------------------------------------------------------------
def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    parser.add_argument("--periodo", help="código del periodo, p. ej. 20224 (por defecto, el más reciente)")
    parser.add_argument("--datos", default=str(RAIZ / "datos"), help="carpeta para la copia local de los datos")
    parser.add_argument("--salida", default=str(RAIZ / "web"), help="carpeta donde se escriben modelo.js y modelo.json")
    parser.add_argument("--sin-boosting", action="store_true", help="omite la comparación con HistGradientBoosting")
    args = parser.parse_args()
    carpeta_datos = Path(args.datos)

    print("1) Periodo")
    periodo = args.periodo
    if periodo is None:
        periodos = consultar_periodos()
        print(periodos.head(6).to_string(index=False))
        periodo = str(periodos.iloc[0]["periodo"])
    print(f"   periodo elegido: {periodo} ({etiqueta_periodo(periodo)})")

    print("2) Descarga")
    columnas = COLUMNAS_EXTRA + CANDIDATAS + [OBJETIVO]
    crudos = descargar_periodo(periodo, columnas, carpeta_datos)
    crudos = quitar_duplicados(crudos)

    print("3) Limpieza")
    datos = limpiar(crudos, VARIABLES)
    print(f"   {len(crudos):,} filas descargadas -> {len(datos):,} con puntaje válido".replace(",", "."))
    promedio_nacional = float(datos[OBJETIVO].mean())

    print("4) Train/test (antes de ajustar cualquier cosa)")
    x = datos[VARIABLES]
    y = datos[OBJETIVO]
    x_train, x_test, y_train, y_test = train_test_split(
        x, y, test_size=PROPORCION_PRUEBA, random_state=SEMILLA)
    frecuentes = aprender_frecuentes(x_train, VARIABLES, MIN_CASOS)
    raras = {v: sorted(set(x_train[v]) - frecuentes[v]) for v in VARIABLES}
    raras = {v: r for v, r in raras.items() if r}
    x_train = agrupar_raras(x_train, frecuentes)
    x_test = agrupar_raras(x_test, frecuentes)
    print(f"   train: {len(x_train):,}  test: {len(x_test):,}".replace(",", "."))
    print(f"   categorías agrupadas (menos de {MIN_CASOS} casos en train): {raras or 'ninguna'}")

    print("5) Entrenamiento y evaluación en test")
    base = DummyRegressor(strategy="mean").fit(x_train, y_train)
    modelo = crear_modelo(VARIABLES).fit(x_train, y_train)
    pred_modelo = modelo.predict(x_test)
    resultados = {
        "modelo": {"nombre": "Regresión lineal (Ridge)", **metricas(y_test, pred_modelo)},
        "linea_base": {"nombre": "Línea base: siempre el promedio", **metricas(y_test, base.predict(x_test))},
    }
    if not args.sin_boosting:
        boosting = crear_boosting(VARIABLES).fit(x_train, y_train)
        resultados["boosting"] = {"nombre": "HistGradientBoosting (solo comparación)",
                                  **metricas(y_test, boosting.predict(x_test))}
    for fila in resultados.values():
        print(f"   {fila['nombre']:<40} MAE {fila['mae']:6.2f}  RMSE {fila['rmse']:6.2f}  R² {fila['r2']:.3f}")
    mae = resultados["modelo"]["mae"]
    cobertura = float(np.mean(np.abs(y_test.to_numpy() - pred_modelo) <= mae))

    print("6) Exportación")
    extras = {
        "periodo": periodo,
        "periodo_etiqueta": etiqueta_periodo(periodo),
        "fecha": dt.date.today().isoformat(),
        "n_total": int(len(datos)),
        "n_prueba": int(len(x_test)),
        "metricas": resultados,
        "cobertura_mae": cobertura,
        "promedio_nacional": promedio_nacional,
        "raras": raras,
        "casos_prueba": elegir_casos(modelo, x_train, x_test, y_test, VARIABLES),
    }
    modelo_dict = exportar_modelo(modelo, VARIABLES, x_train, y_train, extras)
    ruta_js, ruta_json = escribir_modelo(modelo_dict, Path(args.salida))
    print(f"   {ruta_js}\n   {ruta_json}")

    print("7) Prueba de paridad JavaScript vs scikit-learn")
    # Además de los 5 casos de la página, se verifican 2000 filas de test más.
    muestra = x_test.sample(n=min(2000, len(x_test)), random_state=SEMILLA)
    extra = [{"entradas": {v: str(fila[v]) for v in VARIABLES}, "prediccion_sklearn": float(p)}
             for (_, fila), p in zip(muestra.iterrows(), modelo.predict(muestra))]
    carpeta_datos.mkdir(parents=True, exist_ok=True)
    ruta_extra = carpeta_datos / "paridad_casos.json"
    ruta_extra.write_text(json.dumps(extra, ensure_ascii=False), encoding="utf-8")
    ok = prueba_paridad(ruta_js, ruta_extra)
    print("   PARIDAD OK" if ok else "   PARIDAD FALLÓ o no se pudo ejecutar")
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())

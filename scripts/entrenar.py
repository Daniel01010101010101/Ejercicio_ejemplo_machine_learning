#!/usr/bin/env python3
"""Entrena tu modelo desde la terminal con el mismo código del cuaderno plantilla.

Lee notebooks/plantilla_tu_modelo.ipynb, cambia los valores del formulario por los
que pases aquí y ejecuta sus celdas en orden. Colab y la terminal producen el mismo
modelo.js, y Claude Code puede entrenar, leer las métricas y comparar sin abrir Colab.

Ejemplos:
  python scripts/entrenar.py                      # el ejemplo de diamantes
  python scripts/entrenar.py --datos datos/mis_datos.csv --objetivo nota_final \\
      --variables "horas_estudio, asistencia, jornada" --modelo boosting
  python scripts/entrenar.py ... --publicar       # además copia el modelo a web/

En la carpeta --salida (por defecto mi_modelo/) quedan:
  modelo.js, motor.js, prueba_paridad.js   lo mismo que descarga el cuaderno
  metricas.json                            la tabla de modelos, para leerla con código
  grafica_1.png                            qué pesa más en el modelo
"""
import argparse
import contextlib
import io
import json
import os
import re
import shutil
import subprocess
import sys
import traceback
import warnings
from pathlib import Path

RAIZ = Path(__file__).resolve().parent.parent
CUADERNO = RAIZ / "notebooks" / "plantilla_tu_modelo.ipynb"
MODELOS = ["boosting", "bosque", "arbol", "lineal"]
MEJORA_MINIMA = 0.05  # --publicar exige mejorar el MAE de la línea base al menos 5 %


def argumentos(lista=None):
    p = argparse.ArgumentParser(
        description="Entrena y exporta tu modelo con el cuaderno plantilla, desde la terminal.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="Sin --datos entrena el ejemplo de diamantes del cuaderno.",
    )
    p.add_argument("--datos", help="enlace o ruta de tu CSV")
    p.add_argument("--nombre-datos", help="nombre de la fuente que se muestra en la página")
    p.add_argument("--objetivo", help="columna que quieres predecir (nombre exacto)")
    p.add_argument("--etiqueta-objetivo", help="cómo se llama el objetivo en la página, por ejemplo «Precio»")
    p.add_argument("--unidad", help="unidad del objetivo, por ejemplo USD o puntos")
    p.add_argument("--clase-positiva", help="si predices una clase: la clase cuya probabilidad quieres estimar")
    p.add_argument("--variables", help="columnas para predecir, separadas por comas (vacío = las elige el cuaderno)")
    p.add_argument("--excluir", help="columnas que nunca deben usarse, separadas por comas")
    p.add_argument("--modelo", choices=MODELOS, help="modelo que se publica (por defecto boosting)")
    p.add_argument("--titulo", help="título de la página")
    p.add_argument("--pregunta", help="pregunta que responde el modelo")
    p.add_argument("--autor", help="tu nombre")
    p.add_argument("--usuario-github", help="tu usuario de GitHub")
    p.add_argument("--textos", type=Path,
                   help="JSON opcional con ETIQUETAS, ETIQUETAS_CATEGORIAS, ORDEN_CATEGORIAS y AVISO")
    p.add_argument("--salida", type=Path, default=Path("mi_modelo"), help="carpeta de salida (por defecto mi_modelo/)")
    p.add_argument("--publicar", action="store_true",
                   help="copia modelo.js y modelo.json a web/ si le gana a la línea base y pasa la paridad")
    p.add_argument("--forzar", action="store_true", help="con --publicar: publica aunque mejore menos de 5 %%")
    p.add_argument("--web", type=Path, default=RAIZ / "web", help=argparse.SUPPRESS)  # para las pruebas
    p.add_argument("--detalle", action="store_true", help="muestra todo lo que imprime el cuaderno")
    a = p.parse_args(lista)
    if a.datos and not a.objetivo:
        p.error("con --datos también debes decir --objetivo (la columna que quieres predecir)")
    return a


def parametros(a):
    """Valores del formulario del cuaderno que cambian. Lo que no se pasa queda como en el cuaderno."""
    valores = {}
    if a.datos:
        # Datos nuevos: los textos de ejemplo de diamantes ya no aplican.
        etiqueta = a.etiqueta_objetivo or a.objetivo
        valores.update({
            "URL_DATOS": a.datos, "NOMBRE_DATOS": a.nombre_datos or Path(a.datos).name,
            "OBJETIVO": a.objetivo, "ETIQUETA_OBJETIVO": etiqueta, "UNIDAD": a.unidad or "",
            "VARIABLES": a.variables or "", "TITULO": a.titulo or f"Predictor de {etiqueta.lower()}",
            "PREGUNTA": a.pregunta or f"¿Qué {etiqueta.lower()} tendrá este caso?",
        })
    opcionales = {
        "NOMBRE_DATOS": a.nombre_datos, "OBJETIVO": a.objetivo, "ETIQUETA_OBJETIVO": a.etiqueta_objetivo,
        "UNIDAD": a.unidad, "CLASE_POSITIVA": a.clase_positiva, "VARIABLES": a.variables, "EXCLUIR": a.excluir,
        "MODELO": a.modelo, "TITULO": a.titulo, "PREGUNTA": a.pregunta, "AUTOR": a.autor,
        "USUARIO_GITHUB": a.usuario_github,
    }
    valores.update({k: v for k, v in opcionales.items() if v is not None})
    return valores


def con_parametros(codigo, valores):
    """Reemplaza `NOMBRE = ...  #@param` en la celda del formulario."""
    for nombre, valor in valores.items():
        patron = re.compile(rf"^{nombre} = .*?(\s+#@param.*)$", re.M)
        codigo, n = patron.subn(lambda m: f"{nombre} = {valor!r}{m.group(1)}", codigo)
        if n != 1:
            raise RuntimeError(f"No encontré {nombre} en el formulario del cuaderno; actualiza scripts/entrenar.py.")
    return codigo


def mostrar(objeto):
    """Reemplazo de display() fuera de Jupyter."""
    print(objeto.to_string() if hasattr(objeto, "to_string") else objeto)


def ejecutar_cuaderno(a, valores):
    celdas = [c for c in json.loads(CUADERNO.read_text(encoding="utf-8"))["cells"] if c["cell_type"] == "code"]
    salida = a.salida.resolve()
    salida.mkdir(parents=True, exist_ok=True)
    os.environ.setdefault("MPLBACKEND", "Agg")
    import matplotlib.pyplot as plt

    graficas = []

    def guardar_grafica(*_, **__):
        ruta = salida / f"grafica_{len(graficas) + 1}.png"
        plt.savefig(ruta, dpi=120, bbox_inches="tight")
        plt.close("all")
        graficas.append(ruta)

    plt.show = guardar_grafica
    espacio = {"__name__": "__main__", "display": mostrar}
    marcas = {"formulario": False, "salida": False}
    for numero, celda in enumerate(celdas, start=1):
        codigo = "".join(celda["source"])
        if "#@title 1. Configura tu modelo" in codigo:
            codigo = con_parametros(codigo, valores)
            marcas["formulario"] = True
        if 'CARPETA_SALIDA = Path("mi_modelo")' in codigo:
            codigo = codigo.replace('CARPETA_SALIDA = Path("mi_modelo")', f"CARPETA_SALIDA = Path({str(salida)!r})")
            marcas["salida"] = True
        exec(compile(codigo, f"plantilla_tu_modelo.ipynb, celda de código {numero}", "exec"), espacio)
        if "#@title 2. Opcional" in codigo:
            textos(espacio, a)
    faltan = [k for k, v in marcas.items() if not v]
    if faltan:
        raise RuntimeError(f"El cuaderno cambió ({', '.join(faltan)}); actualiza scripts/entrenar.py.")
    return espacio, graficas


def textos(espacio, a):
    """Textos del formulario: los del JSON de --textos, o vacíos si los datos no son los de ejemplo."""
    if a.textos:
        datos = json.loads(a.textos.read_text(encoding="utf-8"))
        permitidos = {"ETIQUETAS", "ETIQUETAS_CATEGORIAS", "ORDEN_CATEGORIAS", "AVISO", "CURSO"}
        desconocidos = set(datos) - permitidos
        if desconocidos:
            raise ValueError(f"--textos solo acepta {sorted(permitidos)}; sobra {sorted(desconocidos)}.")
        espacio.update(datos)
    elif a.datos:
        espacio.update({"ETIQUETAS": {}, "ETIQUETAS_CATEGORIAS": {}, "ORDEN_CATEGORIAS": {}})


def guardar_metricas(espacio, salida):
    comparacion = espacio["comparacion"]
    resumen = {
        "objetivo": espacio["OBJETIVO"],
        "es_clase": bool(espacio["ES_PROBABILIDAD"]),
        "clase_positiva": espacio["CLASE_POSITIVA"] if espacio["ES_PROBABILIDAD"] else None,
        "variables": list(espacio["VARIABLES"]),
        "excluidas": list(espacio["EXCLUIR"]),
        "n_entrenamiento": int(len(espacio["y_train"])),
        "n_prueba": int(len(espacio["y_test"])),
        "publicado": espacio["MODELO"],
        "mejor": espacio["mejor"]["clave"],
        "comparacion": comparacion,
    }
    (salida / "metricas.json").write_text(json.dumps(resumen, ensure_ascii=False, indent=2), encoding="utf-8")
    return resumen


def tabla(resumen):
    """La comparación como tabla Markdown, lista para pegar en el README."""
    exactitud = resumen["es_clase"]
    filas = ["| Modelo | MAE | R²" + (" | Exactitud" if exactitud else "") + " | |",
             "|---|---:|---:|" + ("---:|" if exactitud else "") + "---|"]
    for f in resumen["comparacion"]:
        nota = "elegido (--modelo)" if f.get("publicado") else ""
        if f["clave"] == resumen["mejor"] and not f.get("publicado"):
            nota = "el mejor en prueba"
        fila = f"| {f['nombre']} | {f['mae']:.2f} | {round(f['r2'], 3) + 0:.3f}"  # + 0 evita «-0.000»
        if exactitud:
            fila += f" | {100 * f['exactitud']:.1f} %"
        filas.append(fila + f" | {nota} |")
    return "\n".join(filas)


def publicar(espacio, salida, resumen, forzar, web):
    """Copia el modelo a web/ solo si le gana a la línea base y pasa la paridad con web/motor.js."""
    publicado = next(f for f in resumen["comparacion"] if f.get("publicado"))
    mejora = 1 - publicado["mae"] / resumen["comparacion"][0]["mae"]
    if mejora < MEJORA_MINIMA and not forzar:
        raise RuntimeError(f"El modelo mejora el MAE de la línea base solo {100 * mejora:.1f} % (mínimo "
                           f"{100 * MEJORA_MINIMA:.0f} %). No se publicó: prueba otras columnas, o usa --forzar.")
    node = shutil.which("node")
    if node:
        # Sin motor.js al lado, la prueba usa web/motor.js: el mismo motor de la página publicada.
        revision = salida / "revision_web"
        revision.mkdir(exist_ok=True)
        shutil.copyfile(salida / "modelo.js", revision / "modelo.js")
        prueba = subprocess.run([node, str(RAIZ / "scripts" / "prueba_paridad.js"), str(revision / "modelo.js")],
                                capture_output=True, text=True)
        print(prueba.stdout.strip().splitlines()[-1] if prueba.stdout.strip() else prueba.stderr)
        if prueba.returncode != 0:
            raise RuntimeError("La prueba de paridad falló con web/motor.js. No se publicó nada en web/.")
    else:
        print("Ojo: no encontré Node.js. La prueba de paridad correrá en GitHub Actions antes de publicar.")
    shutil.copyfile(salida / "modelo.js", web / "modelo.js")
    (web / "modelo.json").write_text(espacio["a_json"](espacio["exportado"]) + "\n", encoding="utf-8")
    print(f"Publicado en {web / 'modelo.js'} y {web / 'modelo.json'}.")


def main(lista=None):
    a = argumentos(lista)
    warnings.filterwarnings("ignore")
    registro = io.StringIO()
    try:
        destino = contextlib.nullcontext() if a.detalle else contextlib.redirect_stdout(registro)
        with destino:
            espacio, graficas = ejecutar_cuaderno(a, parametros(a))
        salida = a.salida.resolve()
        resumen = guardar_metricas(espacio, salida)
        print(tabla(resumen))
        publicado = next(f for f in resumen["comparacion"] if f.get("publicado"))
        base = resumen["comparacion"][0]
        print(f"\nObjetivo: {resumen['objetivo']} · entrenamiento {resumen['n_entrenamiento']} filas · "
              f"prueba {resumen['n_prueba']} filas")
        print(f"Columnas: {', '.join(resumen['variables'])}")
        print(f"Modelo elegido: {publicado['nombre']} · MAE {publicado['mae']:.2f} frente a {base['mae']:.2f} "
              f"de la línea base ({100 * (1 - publicado['mae'] / base['mae']):.0f} % mejor)")
        avisos = [l for l in registro.getvalue().splitlines() if l.startswith("Ojo")]
        for aviso in avisos:
            print(aviso)
        print(f"Archivos en {salida}: modelo.js, metricas.json" + "".join(f", {g.name}" for g in graficas))
        if a.publicar:
            publicar(espacio, salida, resumen, a.forzar, a.web)
    except Exception as error:  # Un mensaje claro en español, sin la pila completa.
        if a.detalle:
            traceback.print_exc()
        print(f"ERROR: {error}", file=sys.stderr)
        ultimas = registro.getvalue().strip().splitlines()[-5:]
        if ultimas and not a.detalle:
            print("Lo último que imprimió el cuaderno:\n  " + "\n  ".join(ultimas), file=sys.stderr)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main())

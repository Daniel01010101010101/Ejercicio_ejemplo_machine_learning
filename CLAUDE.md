# Predictor: un modelo de Machine Learning publicado como página web

Plantilla del curso Machine Learning 1 (Universidad EAN). Un modelo de scikit-learn se exporta
como números a `web/modelo.js` y GitHub Pages publica `web/` como página estática: la página
predice en el navegador, sin servidor.

## Proyecto (en tu copia, cambia esta sección por la de tu proyecto)

- Pregunta: ¿cuánto vale un diamante? (ejemplo de la plantilla)
- Datos: https://raw.githubusercontent.com/mwaskom/seaborn-data/master/diamonds.csv
- Objetivo: `price` · Columnas: `carat, cut, color, clarity` · Excluidas: ninguna
- Entrenar este ejemplo: `python scripts/entrenar.py` (sin argumentos)
- La página publicada de la plantilla original es el Predictor Saber 11 (`scripts/train.py`).
  No la reemplaces desde la plantilla: haz las pruebas en tu copia.

## Comandos

Usa `python3` en macOS y Linux, `python` en Windows.

- Entrenar y comparar los 4 modelos, sin publicar:
  `python scripts/entrenar.py --datos <csv o enlace> --objetivo <columna> --variables "a, b, c" --salida experimentos/<nombre>`
  Imprime la tabla de modelos y deja `metricas.json` en la carpeta de salida.
- Publicar en la página: el mismo comando con `--publicar` (escribe `web/modelo.js` y corre la paridad).
- Prueba de paridad (JavaScript = scikit-learn): `node scripts/prueba_paridad.js web/modelo.js` → debe terminar en «OK».
- Resumen del modelo publicado sin leer los árboles: `node scripts/resumen_modelo.js`
- Pruebas: `python -m pytest tests/ -q`
- Ver la página: `python -m http.server -d web 8000` y abrir http://localhost:8000

## Reglas

- `web/modelo.js` y `web/modelo.json` se generan: nunca se editan a mano (un hook lo bloquea). Para cambiarlos, vuelve a entrenar.
- El entrenamiento vive en `notebooks/plantilla_tu_modelo.ipynb`; `scripts/entrenar.py` solo lo ejecuta. Un cambio de lógica va al cuaderno.
- `web/motor.js` lo usan la página y la prueba de paridad: si cambias su API, cambia los dos.
- Se publica un modelo solo si le gana a la línea base y la paridad pasa.
- Nunca uses variables sensibles (género, etnia, religión, salud, discapacidad, nombres, documentos, direcciones) ni columnas que sean otra forma del objetivo (fuga de datos). Toda columna excluida lleva su motivo.
- Los CSV no se suben al repositorio (`.gitignore`): usa un enlace público o `git add -f` si el archivo es pequeño y no tiene datos personales.
- Git: trabaja en una rama `feature/...`, commits pequeños en español («Agrega...», «Corrige...») y PR hacia `main`. Nunca push directo a `main` ni `--force`.
- Textos de la página y respuestas en español, en frases cortas. Cifras con formato colombiano (12.345,6).
- Antes de decir que algo funciona, muestra la evidencia: la salida de las pruebas o la tabla de métricas.

## Estructura

- `web/` la página: `index.html`, `motor.js`, `modelo.js` (generado), `guia/` y `claude-code/` (guías de clase)
- `scripts/` `entrenar.py` (el cuaderno desde la terminal), `train.py` (Saber 11), `prueba_paridad.js`, `resumen_modelo.js`
- `notebooks/` `plantilla_tu_modelo.ipynb` (Colab) y `saber11_modelo.ipynb`
- `tests/` pruebas de `scripts/entrenar.py`
- `docs/` especificación del proyecto y bitácora de experimentos (`docs/experimentos.md`)
- `.claude/` skills (`/experimento`, `/publicar-modelo`, `/revisar-entrega`), subagentes (`explorador-datos`, `revisor-ml`), hooks y reglas

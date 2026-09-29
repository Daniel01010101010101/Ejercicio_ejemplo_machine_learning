# Predictor Saber 11

Modelo de Machine Learning (**Gradient Boosting**, 100 árboles de decisión) que estima el **puntaje global del Saber 11** (0 a 500) a partir del contexto del hogar y del colegio, publicado como una página web estática. Uno llena un formulario y el modelo predice **en el navegador**: no hay servidor y no se envía ningún dato.

Proyecto de clase del curso **Machine Learning 1**, Universidad EAN (Bogotá).

- **Página publicada:** https://daniel01010101010101.github.io/Ejercicio_ejemplo_machine_learning/ (GitHub Pages; se actualiza sola con cada cambio en `main`)
- **Cuaderno en Colab:** [abrir `notebooks/saber11_modelo.ipynb`](https://colab.research.google.com/github/Daniel01010101010101/Ejercicio_ejemplo_machine_learning/blob/main/notebooks/saber11_modelo.ipynb)
- **Guía de clase «Tu modelo en la web»:** https://daniel01010101010101.github.io/Ejercicio_ejemplo_machine_learning/guia/ ([PDF](https://daniel01010101010101.github.io/Ejercicio_ejemplo_machine_learning/guia/guia_de_clase.pdf)). Cada estudiante copia este repositorio y publica su propio modelo en 60 minutos, sin instalar nada.

> **Uso responsable.** El modelo mide desigualdad de contexto, no capacidad. Nunca debe usarse para juzgar, clasificar o seleccionar a un estudiante.

## Cómo funciona

```
datos.gov.co (API Socrata) ──► cuaderno / train.py ──► web/modelo.js ──► GitHub ──► GitHub Pages
      ICFES, un periodo        limpieza, train/test,     los 100 árboles    dev → main   página
                               4 modelos, métricas       como números                    estática
```

1. Se descarga **un solo periodo** del conjunto [«Resultados únicos Saber 11»](https://www.datos.gov.co/Educaci-n/Resultados-nicos-Saber-11/kgxf-xxbe) (`kgxf-xxbe`), filtrando con `$where` y paginando con `$limit`/`$offset`.
2. Se comparan cuatro `Pipeline` de scikit-learn con el mismo `OneHotEncoder(handle_unknown="ignore")`: regresión lineal (`Ridge`), árbol de decisión, bosque aleatorio y Gradient Boosting (`HistGradientBoostingRegressor`). Se publica el Gradient Boosting, el que menos se equivoca en validación y en prueba.
3. Un árbol es una lista de preguntas de sí o no («¿columna ≤ umbral?») y de hojas con un número. Los 100 árboles se exportan como números a `web/modelo.js`, y `web/motor.js` los recorre en el navegador: *punto de partida + la hoja de cada árbol = estimación*. La página también muestra cuánto aportó cada respuesta y las preguntas que hace el árbol 1.
4. Una **prueba de paridad** en Node carga el mismo `web/motor.js` que usa la página y verifica que JavaScript y scikit-learn den lo mismo (tolerancia 1e-6).

¿Por qué no un `.pkl`? GitHub Pages solo publica archivos estáticos: no ejecuta Python ni ningún código en el servidor. (Netlify tampoco: sus funciones solo corren JavaScript/TypeScript, y Go mediante la API compatible con Lambda.) Exportar el modelo como números lo vuelve portable y auditable.

## Estructura

```
web/
  index.html          la página (HTML, CSS y JS)
  motor.js            recorre los árboles (o suma los coeficientes de un modelo lineal)
  modelo.js           el modelo: window.MODELO = {...}  (generado, no se edita a mano)
  modelo.json         el mismo contenido en JSON
  guia/               guía de clase para estudiantes (página y PDF)
notebooks/
  saber11_modelo.ipynb        cuaderno de clase, ejecutado con los datos reales
  plantilla_tu_modelo.ipynb   plantilla: de un CSV propio a modelo.js
ejemplos/diamantes/
  modelo.js           modelo de ejemplo hecho con la plantilla (plan B en clase)
scripts/
  train.py            lo mismo que el cuaderno, desde la terminal
  prueba_paridad.js   prueba de paridad JavaScript vs scikit-learn
.github/workflows/
  pages.yml           publica web/ en GitHub Pages, después de la prueba de paridad
netlify.toml          alternativa: publicar en Netlify
requirements.txt      dependencias para correr train.py fuera de Colab
```

Los datos crudos se descargan en `datos/`, que está en `.gitignore`.

## Métricas del modelo

Periodo **20224 (Saber 11 2022-2)**. Set de prueba: 106.514 estudiantes que el modelo no vio al entrenar.

| Modelo | MAE | RMSE | R² |
|---|---:|---:|---:|
| Línea base: siempre el promedio | 42,9 | 51,8 | 0,000 |
| Regresión lineal (Ridge) | 35,5 | 43,7 | 0,289 |
| Árbol de decisión (profundidad 8) | 36,5 | 44,9 | 0,249 |
| Bosque aleatorio (50 árboles) | 35,9 | 44,1 | 0,274 |
| **Gradient Boosting (100 árboles, el que se publica)** | **34,7** | **42,8** | **0,316** |

- El Gradient Boosting se equivoca en promedio 34,7 puntos, frente a 42,9 de la línea base (19 % mejor), y explica cerca del 32 % de la variación del puntaje.
- Le gana a la regresión lineal por menos de un punto: con 9 preguntas sobre el contexto, los datos tienen un techo. Un solo árbol se equivoca más que la lineal. El modelo se eligió en una validación dentro de train, con el mismo resultado.
- En el 56 % de los estudiantes de prueba, el puntaje real quedó dentro de la estimación ± MAE.
- Prueba de paridad: JavaScript y scikit-learn coinciden con una diferencia máxima de 0 en 2.005 casos (tolerancia 1e-6).

## Cómo re-entrenar

**Opción A: Google Colab (sin instalar nada).**

1. Abre el [cuaderno en Colab](https://colab.research.google.com/github/Daniel01010101010101/Ejercicio_ejemplo_machine_learning/blob/main/notebooks/saber11_modelo.ipynb) y ejecuta todo (*Entorno de ejecución → Ejecutar todas*). Descarga los datos solo y al final descarga `modelo.js` y `modelo.json`.
2. En GitHub, cambia a la rama `dev`, entra a `web/` y sube los dos archivos (*Add file → Upload files*) para reemplazar los anteriores.
3. Abre la página (o `web/index.html` en tu computador) y confirma que la sección **Verificación** diga «5 de 5 coinciden».
4. Abre un pull request de `dev` a `main` y fusiónalo. GitHub Actions corre la prueba de paridad y, si pasa, publica la nueva versión en GitHub Pages (uno o dos minutos).

**Opción B: terminal.**

```bash
pip install -r requirements.txt
python scripts/train.py                  # periodo más reciente; o --periodo 20224
node scripts/prueba_paridad.js web/modelo.js
git switch dev && git add web/ && git commit -m "Re-entrena el modelo" && git push
```

`train.py` corre la prueba de paridad al final y termina con error si JavaScript y scikit-learn no coinciden.

## Despliegue en GitHub Pages

La página se publica sola con GitHub Actions ([`.github/workflows/pages.yml`](.github/workflows/pages.yml)) cada vez que llega a `main` un cambio en `web/`:

1. Descarga el repositorio.
2. Corre `node scripts/prueba_paridad.js web/modelo.js`. **Si la paridad falla, no se publica nada.**
3. Publica la carpeta `web/` en https://daniel01010101010101.github.io/Ejercicio_ejemplo_machine_learning/.

**Una sola vez:** en el repositorio, *Settings → Pages → Build and deployment → Source:* **GitHub Actions**. El workflow no puede activar Pages por sí mismo.

Para ver cómo va una publicación: pestaña **Actions** del repositorio → «Publicar en GitHub Pages». Para volver a publicar sin cambiar archivos, en esa misma página: **Run workflow**.

### Ramas

Se trabaja en **`dev`** y se fusiona a **`main`** solo cuando todo está verificado: lo que llega a `main` es lo que ven los estudiantes.

### Seguridad y privacidad

`web/index.html` declara una política de seguridad de contenido (`<meta http-equiv="Content-Security-Policy">`) con `connect-src 'none'` y `form-action 'none'`: el navegador **bloquea** cualquier intento de la página de enviar datos (fetch, XHR, WebSocket o beacon). Funciona en GitHub Pages y también al abrir el archivo directamente.

## Alternativa: Netlify

`netlify.toml` deja todo listo por si algún día prefieres Netlify:

1. En [app.netlify.com](https://app.netlify.com): **Add new project → Import an existing project → GitHub** y elige este repositorio.
2. **Branch to deploy:** `main` · **Build command:** vacío · **Publish directory:** `web`.
3. **Deploy.**

El plan gratuito da 300 créditos al mes y cada publicación en producción cuesta 15 (unas 20 al mes); la regla `ignore` de `netlify.toml` omite la publicación cuando no cambia `web/`. Si usas Netlify, desactiva el workflow de GitHub Pages (*Actions → Publicar en GitHub Pages → Disable workflow*) para no publicar en dos lugares.

## Datos

- **Fuente:** ICFES, «Resultados únicos Saber 11», publicado en datos.gov.co, conjunto `kgxf-xxbe` (2010 a 2022).
- **Periodo usado:** `20224` (Saber 11 2022-2, calendario A), el más reciente del conjunto. El portal Data Icfes, donde el ICFES publica años posteriores, no estaba disponible al preparar el proyecto (septiembre de 2026), así que no había una descarga directa que el cuaderno pudiera usar.
- **Duplicados:** el periodo trae 1.065.888 filas, pero solo 532.792 estudiantes distintos (`estu_consecutivo`): cada fila está repetida. Se quitan los duplicados **antes** de separar train y test, para que un mismo estudiante no quede en ambos lados.
- **Limpieza:** se excluyen 226 resultados en estado «VALIDEZ OFICINA JURÍDICA». Quedan 532.566 estudiantes: 426.052 para entrenar y 106.514 para evaluar.
- **Variables del modelo (9 preguntas del formulario):** estrato, educación de la madre, educación del padre, internet, computador, tipo de colegio, jornada, zona y departamento.
- **Variables fuera del modelo:**
  - `estu_genero`: decisión ética; la predicción no debe cambiar por el género.
  - Nombres y códigos de colegio: identifican instituciones y no describen el contexto.
  - `fami_tieneautomovil`: casi no aporta en validación, porque su información ya la traen el estrato, el computador y el internet.
  - `cole_bilingue`: la peor calidad (18 % de faltantes) y un aporte mínimo.

  La justificación completa, con la validación dentro de train, está en el cuaderno.

## Cómo mostrarlo en clase

1. Abre la página (https://daniel01010101010101.github.io/Ejercicio_ejemplo_machine_learning/) y lee con el grupo el aviso de **Uso responsable** y el de privacidad.
2. Cambia una respuesta (por ejemplo, la jornada de «Mañana» a «Sabatina») y mira cómo se mueve el medidor y qué barra cambia en **Qué suma y qué resta**.
3. Pulsa **Cargar un caso real** varias veces: son estudiantes del set de prueba con su puntaje real. Compara real y estimado para ver el tamaño del error individual.
4. En la **Ficha del modelo**, compara los cinco modelos (línea base, lineal, árbol, bosque y Gradient Boosting) y muestra las preguntas que hace el árbol 1 con las respuestas actuales. Cambia el estrato a «Estrato 6» y discute por qué resta: una vez que el modelo conoce el resto del perfil, al estrato le queda poca información propia.
5. En **Verificación**, muestra que el navegador y scikit-learn dan lo mismo. En la consola del navegador (F12) se puede probar `PredictorSaber11.predecir(PredictorSaber11.modelo, {...})` o `PredictorSaber11.explicar({...})`, que devuelve el punto de partida y el aporte de cada respuesta.
6. Abre el cuaderno en Colab y recorre las secciones; las preguntas para discutir están al final.

## Para tu clase: cada estudiante publica su modelo

La misma página sirve para el modelo del proyecto final de cada estudiante: Gradient Boosting, bosque aleatorio, un árbol de decisión o una regresión lineal. Cada estudiante copia este repositorio, entrena su modelo en Colab y reemplaza `web/modelo.js`; la página toma del archivo el título, las preguntas, las unidades y los textos.

1. **Guía de estudiantes:** [`web/guia/`](https://daniel01010101010101.github.io/Ejercicio_ejemplo_machine_learning/guia/) (también en [PDF](https://daniel01010101010101.github.io/Ejercicio_ejemplo_machine_learning/guia/guia_de_clase.pdf)). Tres partes: qué hace el modelo (árboles y Gradient Boosting), cómo leer sus resultados y cómo publicar el modelo propio en 4 pasos.
2. **Cuaderno plantilla:** [abrir `notebooks/plantilla_tu_modelo.ipynb` en Colab](https://colab.research.google.com/github/Daniel01010101010101/Ejercicio_ejemplo_machine_learning/blob/main/notebooks/plantilla_tu_modelo.ipynb). Solo se llena un formulario de Colab: título, autor, CSV, columna a predecir, de 3 a 10 columnas (vacío = el cuaderno las elige) y `MODELO` (`boosting`, `bosque`, `arbol` o `lineal`). Separa entrenamiento y prueba, entrena los cuatro modelos y los compara con la línea base, exporta el elegido, corre la prueba de paridad y descarga `modelo.js`. Las columnas numéricas quedan como números (en la página, una barra para elegir el valor); si el objetivo es sí/no o una clase, estima la probabilidad y reporta la exactitud. Sin cambios, usa un ejemplo de precios de diamantes (Gradient Boosting: MAE 295 USD frente a 3.020 de la línea base).
3. **Plan B:** si Colab falla en clase, [`ejemplos/diamantes/modelo.js`](ejemplos/diamantes/modelo.js) es un modelo listo para subir a `web/`.

**Una sola vez, antes de la clase:** *Settings → General →* marca **Template repository**. Así aparece el botón **Use this template** y cada copia trae la página, los cuadernos y el workflow de publicación. En cada copia, el estudiante activa *Settings → Pages → Source:* **GitHub Actions** (paso 1 de la guía).

## Uso responsable

- El modelo describe **asociaciones promedio**, no causas, y se equivoca mucho a nivel individual.
- Refleja **desigualdad de contexto** (estrato, educación de los padres, tipo de colegio), no la capacidad ni el esfuerzo de nadie.
- **No** debe usarse para juzgar, clasificar, admitir, rechazar ni asignar becas o expectativas a ningún estudiante.

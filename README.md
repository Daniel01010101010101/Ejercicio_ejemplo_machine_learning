# Predictor Saber 11

Modelo de Machine Learning que estima el **puntaje global del Saber 11** (0 a 500) a partir del contexto del hogar y del colegio, publicado como una página web estática. Uno llena un formulario y el modelo predice **en el navegador**: no hay servidor y no se envía ningún dato.

Proyecto de clase del curso **Machine Learning 1**, Universidad EAN (Bogotá).

- **Página publicada:** _pendiente: la URL de Netlify, una vez conectado el repositorio (ver [Despliegue](#despliegue-en-netlify))._
- **Cuaderno en Colab:** [abrir `notebooks/saber11_modelo.ipynb`](https://colab.research.google.com/github/Daniel01010101010101/Ejercicio_ejemplo_machine_learning/blob/main/notebooks/saber11_modelo.ipynb)

> **Uso responsable.** El modelo mide desigualdad de contexto, no capacidad. Nunca debe usarse para juzgar, clasificar o seleccionar a un estudiante.

## Cómo funciona

```
datos.gov.co (API Socrata) ──► cuaderno / train.py ──► web/modelo.js ──► GitHub ──► Netlify
      ICFES, un periodo        limpieza, train/test,     intercepto y      dev → main   página
                               Ridge, métricas           coeficientes                   estática
```

1. Se descarga **un solo periodo** del conjunto [«Resultados únicos Saber 11»](https://www.datos.gov.co/Educaci-n/Resultados-nicos-Saber-11/kgxf-xxbe) (`kgxf-xxbe`), filtrando con `$where` y paginando con `$limit`/`$offset`.
2. Se entrena un `Pipeline` de scikit-learn: `OneHotEncoder(handle_unknown="ignore")` + `Ridge`.
3. Como todas las variables son categóricas, la predicción es **el intercepto más la suma de los coeficientes de las respuestas elegidas**. Esos números se exportan a `web/modelo.js` y la página hace la misma suma en JavaScript.
4. Una **prueba de paridad** en Node verifica que JavaScript y scikit-learn den lo mismo (tolerancia 1e-6).

¿Por qué no un `.pkl`? Netlify publica sitios estáticos y sus funciones no ejecutan Python (solo JavaScript/TypeScript, y Go mediante la API compatible con Lambda). Exportar el modelo como números lo vuelve portable y auditable.

## Estructura

```
web/
  index.html          página completa (HTML, CSS y JS en un solo archivo)
  modelo.js           el modelo: window.MODELO = {...}  (generado, no se edita a mano)
  modelo.json         el mismo contenido en JSON
notebooks/
  saber11_modelo.ipynb  cuaderno de clase, ejecutado con los datos reales
scripts/
  train.py            lo mismo que el cuaderno, desde la terminal
  prueba_paridad.js   prueba de paridad JavaScript vs scikit-learn
netlify.toml          publica la carpeta web/ (sin paso de build)
requirements.txt      dependencias para correr train.py fuera de Colab
```

Los datos crudos se descargan en `datos/`, que está en `.gitignore`.

## Métricas del modelo

Periodo **20224 (Saber 11 2022-2)**. Set de prueba: 106.514 estudiantes que el modelo no vio al entrenar.

| Modelo | MAE | RMSE | R² |
|---|---:|---:|---:|
| **Regresión lineal Ridge (la que se publica)** | **35,5** | **43,7** | **0,289** |
| Línea base: siempre el promedio | 42,9 | 51,8 | 0,000 |
| HistGradientBoosting (solo comparación) | 34,6 | 42,7 | 0,321 |

- El modelo lineal se equivoca en promedio 35,5 puntos, frente a 42,9 de la línea base (17 % mejor), y explica cerca del 29 % de la variación del puntaje.
- En el 56 % de los estudiantes de prueba, el puntaje real quedó dentro de la estimación ± MAE.
- El gradient boosting mejora un poco (MAE 34,6), pero no se puede leer como una suma de coeficientes. Por eso se publica el lineal.
- Prueba de paridad: JavaScript y scikit-learn coinciden con una diferencia máxima de 1,1 × 10⁻¹³ en 2.005 casos (tolerancia 1e-6).

## Cómo re-entrenar

**Opción A: Google Colab (sin instalar nada).**

1. Abre el [cuaderno en Colab](https://colab.research.google.com/github/Daniel01010101010101/Ejercicio_ejemplo_machine_learning/blob/main/notebooks/saber11_modelo.ipynb) y ejecuta todo (*Entorno de ejecución → Ejecutar todas*). Descarga los datos solo y al final descarga `modelo.js` y `modelo.json`.
2. En GitHub, cambia a la rama `dev`, entra a `web/` y sube los dos archivos (*Add file → Upload files*) para reemplazar los anteriores.
3. Abre la página (o `web/index.html` en tu computador) y confirma que la sección **Verificación** diga «5 de 5 coinciden».
4. Abre un pull request de `dev` a `main` y fusiónalo. Netlify publica la nueva versión.

**Opción B: terminal.**

```bash
pip install -r requirements.txt
python scripts/train.py                  # periodo más reciente; o --periodo 20224
node scripts/prueba_paridad.js web/modelo.js
git switch dev && git add web/ && git commit -m "Re-entrena el modelo" && git push
```

`train.py` corre la prueba de paridad al final y termina con error si JavaScript y scikit-learn no coinciden.

## Despliegue en Netlify

Una sola vez:

1. Entra a [app.netlify.com](https://app.netlify.com) con tu cuenta de GitHub.
2. **Add new project → Import an existing project → GitHub.** Autoriza a Netlify y elige el repositorio `Ejercicio_ejemplo_machine_learning`.
3. Configuración de build:
   - **Branch to deploy:** `main`
   - **Base directory:** vacío
   - **Build command:** vacío
   - **Publish directory:** `web` (ya viene en `netlify.toml`)
4. **Deploy.** En uno o dos minutos la página queda en `https://<nombre-al-azar>.netlify.app`. Para cambiar el nombre: *Project configuration → General → Project details → Change project name* (por ejemplo, `saber11-predictor`).

Desde entonces **cada push a `main` publica solo**.

### Ramas y créditos

El plan gratuito de Netlify da **300 créditos al mes** con límite duro, y cada publicación en producción cuesta **15**: alcanzan unas **20 publicaciones al mes**. Por eso:

- Se trabaja en **`dev`** y se fusiona a **`main`** solo cuando todo está verificado (idealmente, varios cambios juntos).
- `netlify.toml` tiene una regla `ignore`: si un push a `main` no cambia nada en `web/` (por ejemplo, solo el cuaderno o este README), Netlify omite la publicación.
- Si no usas vistas previas, en *Project configuration → Build & deploy → Branches and deploy contexts* deja **Branch deploys** en *None* y desactiva los **Deploy Previews**.

### Seguridad y privacidad

`netlify.toml` envía una política de seguridad de contenido con `connect-src 'none'`: el navegador **bloquea** cualquier intento de la página de enviar datos (fetch, XHR o WebSocket). Solo se permiten las fuentes de Google Fonts.

## Plan B: GitHub Pages

Como el sitio es estático, GitHub Pages también sirve gratis:

1. Crea el archivo `.github/workflows/pages.yml` con este contenido:

   ```yaml
   name: Publicar en GitHub Pages
   on:
     push:
       branches: [main]
       paths: ["web/**"]
     workflow_dispatch:
   permissions:
     contents: read
     pages: write
     id-token: write
   concurrency:
     group: pages
     cancel-in-progress: true
   jobs:
     publicar:
       runs-on: ubuntu-latest
       environment:
         name: github-pages
         url: ${{ steps.despliegue.outputs.page_url }}
       steps:
         - uses: actions/checkout@v4
         - uses: actions/configure-pages@v5
         - uses: actions/upload-pages-artifact@v3
           with:
             path: web
         - id: despliegue
           uses: actions/deploy-pages@v4
   ```

2. En el repositorio: *Settings → Pages → Build and deployment → Source: **GitHub Actions***.
3. Haz push a `main`. La página queda en `https://daniel01010101010101.github.io/Ejercicio_ejemplo_machine_learning/`.

(GitHub Pages no permite cabeceras propias, así que allí no aplica la política de seguridad de `netlify.toml`; la página funciona igual.)

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

1. Abre la página y lee con el grupo el aviso de **Uso responsable** y el de privacidad.
2. Cambia una respuesta (por ejemplo, la jornada de «Mañana» a «Sabatina») y mira cómo se mueve el medidor y qué barra cambia en **Qué suma y qué resta**.
3. Pulsa **Cargar un caso real** varias veces: son estudiantes del set de prueba con su puntaje real. Compara real y estimado para ver el tamaño del error individual.
4. En la **Ficha del modelo**, compara el MAE con la línea base y con el gradient boosting, y discute el límite del estrato: su efecto ajustado se invierte.
5. En **Verificación**, muestra que el navegador y scikit-learn dan lo mismo. En la consola del navegador (F12) se puede probar `PredictorSaber11.predecir(PredictorSaber11.modelo, {...})`: el modelo es solo una suma.
6. Abre el cuaderno en Colab y recorre las secciones; las preguntas para discutir están al final.

## Uso responsable

- El modelo describe **asociaciones promedio**, no causas, y se equivoca mucho a nivel individual.
- Refleja **desigualdad de contexto** (estrato, educación de los padres, tipo de colegio), no la capacidad ni el esfuerzo de nadie.
- **No** debe usarse para juzgar, clasificar, admitir, rechazar ni asignar becas o expectativas a ningún estudiante.

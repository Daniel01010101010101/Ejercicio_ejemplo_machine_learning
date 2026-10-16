---
name: guia-ml
description: Criterios del curso para evaluar e interpretar un modelo de Machine Learning (línea base, MAE, R², exactitud, fuga de datos, variables sensibles). Úsala al comparar modelos, explicar métricas o revisar un proyecto.
---
# Cómo se evalúa un modelo en este curso

## Siempre contra la línea base
- Regresión: la línea base responde siempre el promedio de entrenamiento. Clase: la probabilidad promedio.
- Un modelo que mejora el MAE de la línea base en menos de 5 % no vale la pena publicarlo: hay que buscar mejores columnas.

## Cómo explicar las métricas (una frase cada una)
- **MAE**: «en promedio se equivoca X [unidad]». Es la métrica principal del curso.
- **RMSE**: como el MAE, pero castiga más los errores grandes. Si es mucho mayor que el MAE, hay casos con errores enormes.
- **R²**: qué parte de la variación explica el modelo. 0 = igual que la línea base, 1 = perfecto, negativo = peor que la línea base.
- **Exactitud** (solo clases): de cada 100 casos de prueba, cuántos acierta con el umbral de 50 %. Compárala con la exactitud de la línea base.
- Con datos sociales, un R² de 0,3 puede ser honesto y útil; un R² de 0,99 casi siempre es una fuga de datos.

## Fuga de datos (revisa siempre)
- Señales: R² > 0,99, exactitud cercana a 100 % o una columna que pesa muchísimo más que las demás.
- Causas: columnas que son otra forma del objetivo (puntaje por materia cuando se predice el total), que se conocen después del resultado, identificadores o fechas.

## Separación entrenamiento y prueba
- Todo se aprende solo con entrenamiento (categorías raras, medianas, codificación); la prueba solo mide.
- No elijas columnas mirando la prueba una y otra vez: eso la convierte en entrenamiento.

## Uso responsable
- No se usan para predecir: género, etnia, religión, orientación, salud, discapacidad, nombres, documentos ni direcciones exactas.
- Toda columna excluida lleva su motivo en `--excluir` y en el README.
- El modelo describe asociaciones, no causas. Di siempre para qué no debe usarse.

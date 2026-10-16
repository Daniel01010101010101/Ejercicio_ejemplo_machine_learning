---
name: publicar-modelo
description: Publica el modelo elegido en la página. Entrena con --publicar, verifica la paridad, actualiza el README y abre un pull request.
disable-model-invocation: true
argument-hint: "[boosting | bosque | arbol | lineal]"
---
# Publicar el modelo

Estado del repositorio ahora:

!`git status --short --branch`

1. Si la rama actual es `main`, crea una rama `feature/publicar-modelo` (agrega la fecha si ya existe).
2. Toma los datos, el objetivo, las columnas y las exclusiones de la sección «Proyecto» de CLAUDE.md.
   Modelo: $ARGUMENTS. Si está vacío, el de menor MAE (o mayor exactitud) de `docs/experimentos.md`; si no hay bitácora, `boosting`.
3. Corre `python scripts/entrenar.py ... --modelo <modelo> --publicar`.
   Detente y explica el motivo si el modelo no le gana a la línea base o si la prueba de paridad falla.
4. En el README, pon la tabla de métricas que imprimió el script en la sección de métricas (créala si no existe), con la fecha.
5. Commit: «Publica <modelo> entrenado con <columnas>». Sube la rama y abre un PR hacia `main` con la plantilla del repositorio:
   qué cambió, la tabla, la salida de la prueba de paridad y «Cierra #<número>» si hay un issue.
6. Responde con el enlace del PR y la evidencia: la tabla y la línea «OK» de la paridad.

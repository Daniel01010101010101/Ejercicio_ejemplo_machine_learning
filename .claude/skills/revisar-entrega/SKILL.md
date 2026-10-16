---
name: revisar-entrega
description: Revisa si el proyecto cumple la entrega de la línea de profundización (10 % de la nota) y dice qué falta. Solo revisa; no escribe el informe.
disable-model-invocation: true
allowed-tools: Bash(node scripts/prueba_paridad.js *) Bash(node scripts/resumen_modelo.js *) Bash(git remote *) Bash(curl -sI *) Read Grep Glob
---
# Revisar la entrega

Revisa cada punto y responde con una tabla: **Punto · Estado (✅, ⚠️ o ❌) · Evidencia · Qué falta**.
No cambies archivos sin preguntar.

1. **Paridad**: `node scripts/prueba_paridad.js web/modelo.js` termina en «OK» y revisa 5 casos (la página dirá «5 de 5 coinciden»).
2. **Es su modelo**: según `node scripts/resumen_modelo.js`, el `proyecto` no es «Predictor Saber 11» ni el de diamantes, y `autor` tiene su nombre.
3. **Página publicada**: deduce la dirección de `git remote get-url origin` (`https://<usuario>.github.io/<repositorio>/`, en minúsculas) y comprueba con `curl -sI` que responde 200.
4. **Le gana a la línea base**: en la comparación, el modelo publicado tiene menor MAE (o mayor exactitud) que la línea base.
5. **Uso responsable**: hay aviso ético, ninguna variable es sensible y cada columna excluida tiene motivo.
6. **README**: explica la pregunta, los datos con su enlace, la tabla de modelos y el MAE en una frase.
7. **Lo que no puedes revisar**: recuerda que el PDF de máximo 2 páginas (`Apellido_Nombre_ML.pdf`, con los dos enlaces al inicio) se sube a Canvas.

El informe lo escribe el estudiante con sus palabras: señala qué falta, pero no lo redactes.

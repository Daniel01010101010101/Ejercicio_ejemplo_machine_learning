---
name: experimento
description: Entrena y compara los cuatro modelos contra la línea base con las columnas que se indiquen, sin publicar nada, y anota el resultado en docs/experimentos.md.
when_to_use: Cuando el usuario quiera probar otras columnas u otro modelo, o comparar experimentos.
argument-hint: "[columnas separadas por comas]"
allowed-tools: Bash(python scripts/entrenar.py *) Bash(python3 scripts/entrenar.py *) Read Edit Write
---
# Experimento

Columnas que pidió el usuario: $ARGUMENTS

1. Lee los datos y el objetivo en la sección «Proyecto» de CLAUDE.md. Si faltan, pregúntalos; no los inventes.
   Si no hay columnas, usa las de la última fila de `docs/experimentos.md`, o las de CLAUDE.md.
2. Entrena en una carpeta nueva y **sin** `--publicar`:
   `python scripts/entrenar.py --datos <datos> --objetivo <objetivo> --variables "<columnas>" --salida experimentos/<AAAAMMDD-HHMM>`
3. Lee `metricas.json` de esa carpeta. Detente y avisa si el R² pasa de 0,99 (posible fuga de datos) o si una columna es sensible.
4. Agrega una fila al final de `docs/experimentos.md`. Si el archivo no existe, créalo con este encabezado:

   | Fecha | Columnas | Mejor modelo | MAE | R² | Exactitud | MAE línea base | Carpeta | Conclusión |
   |---|---|---|---:|---:|---:|---:|---|---|

   El mejor modelo es el de menor MAE, o el de mayor exactitud si el objetivo es una clase. Cifras con formato colombiano.

5. Responde con la tabla que imprimió el script y una sola frase: ¿mejoró frente al experimento anterior y por qué crees que pasó?

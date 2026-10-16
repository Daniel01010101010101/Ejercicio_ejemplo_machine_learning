#!/usr/bin/env bash
# Hook PreToolUse (Edit|Write): antes de que Claude edite un archivo.
# Bloquea los archivos generados, los datos crudos y los secretos. Con «exit 2» la edición
# no ocurre y Claude recibe el motivo (lo que se escribe en stderr) para buscar otro camino.
# Solo usa bash, grep y sed, así funciona en macOS, Linux y Git Bash de Windows.

entrada=$(cat)
ruta=$(printf '%s' "$entrada" | grep -o '"file_path" *: *"[^"]*"' | head -n 1 | sed 's/^.*: *"//; s/"$//')
ruta=${ruta//\\\\//}   # Windows llega como C:\\proyecto\\web: se normaliza a /
ruta=${ruta//\\//}

case "$ruta" in
  */web/modelo.js | */web/modelo.json)
    echo "Bloqueado: $ruta se genera, no se edita a mano. Vuelve a entrenar con «python scripts/entrenar.py ... --publicar»." >&2
    exit 2 ;;
  */.env | */.env.*)
    echo "Bloqueado: los secretos no se tocan. Usa variables de entorno o los Secrets de GitHub." >&2
    exit 2 ;;
  */datos/*)
    if [ -e "$ruta" ]; then
      echo "Bloqueado: los datos crudos de datos/ no se modifican. Limpia en el código o guarda una copia con otro nombre." >&2
      exit 2
    fi ;;
esac
exit 0

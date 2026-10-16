#!/usr/bin/env bash
# Hook PostToolUse (Edit|Write): después de que Claude edita un archivo, lo revisa al instante.
#   .py               ¿compila? (errores de sintaxis)
#   .json             ¿es JSON válido? (por ejemplo .claude/settings.json)
#   web/motor.js      ¿la prueba de paridad sigue en OK?
# Si algo falla, «exit 2» le muestra el error a Claude para que lo corrija en el mismo turno.

entrada=$(cat)
ruta=$(printf '%s' "$entrada" | grep -o '"file_path" *: *"[^"]*"' | head -n 1 | sed 's/^.*: *"//; s/"$//')
ruta=${ruta//\\\\//}
ruta=${ruta//\\//}
[ -n "$ruta" ] && [ -e "$ruta" ] || exit 0

python=""
for candidato in python3 python; do
  if command -v "$candidato" >/dev/null 2>&1 && "$candidato" -c "import sys" >/dev/null 2>&1; then
    python=$candidato
    break
  fi
done

fallar() {
  echo "Revisión automática de $ruta: $1" >&2
  printf '%s\n' "$2" | tail -n 15 >&2
  exit 2
}

case "$ruta" in
  *.py)
    [ -n "$python" ] || exit 0
    salida=$("$python" -m py_compile "$ruta" 2>&1) || fallar "el archivo no compila." "$salida" ;;
  *.json)
    [ -n "$python" ] || exit 0
    salida=$("$python" -m json.tool "$ruta" 2>&1 >/dev/null) || fallar "no es JSON válido." "$salida" ;;
  */web/motor.js | */scripts/prueba_paridad.js)
    command -v node >/dev/null 2>&1 || exit 0
    cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0
    salida=$(node scripts/prueba_paridad.js web/modelo.js 2>&1) || fallar "la prueba de paridad falló." "$salida" ;;
esac
exit 0

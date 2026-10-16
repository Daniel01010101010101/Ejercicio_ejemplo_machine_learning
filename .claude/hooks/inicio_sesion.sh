#!/usr/bin/env bash
# Hook SessionStart: al abrir (o reanudar) una sesión.
# Lo que este script imprime en stdout entra al contexto de Claude.
#   1. En la nube (claude.ai/code) instala las dependencias de Python, que el VM no trae.
#   2. Le recuerda a Claude en qué rama está y la regla de trabajar en ramas.

cd "${CLAUDE_PROJECT_DIR:-.}" || exit 0

if [ "$CLAUDE_CODE_REMOTE" = "true" ] && [ -f requirements.txt ]; then
  if pip install -q -r requirements.txt pytest >/dev/null 2>&1; then
    echo "Dependencias de Python instaladas (requirements.txt y pytest)."
  else
    echo "No pude instalar requirements.txt. Corre: pip install -r requirements.txt pytest"
  fi
fi

rama=$(git branch --show-current 2>/dev/null)
if [ -n "$rama" ]; then
  echo "Rama actual: $rama."
  if [ "$rama" = "main" ] || [ "$rama" = "master" ]; then
    echo "Estás en $rama: antes de cambiar archivos crea una rama feature/... (regla del proyecto)."
  fi
fi
exit 0

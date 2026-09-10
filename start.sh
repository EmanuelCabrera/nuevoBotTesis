#!/usr/bin/env bash
set -euo pipefail

# Puertos (local / Render)
RASA_PORT="${PORT:-5005}"
ACTIONS_PORT="${ACTIONS_PORT:-5055}"
CORS_VAL="${CORS:-*}"

# Apagado prolijo
trap "echo '→ Apagando...'; kill 0" SIGTERM SIGINT

echo "Iniciando servidor de acciones de Rasa en puerto ${ACTIONS_PORT} ..."
# Quitar --host: no existe en 'rasa run actions' para Rasa 3.6
rasa run actions --port "${ACTIONS_PORT}" --debug &

# Espera corta
sleep 3

# Si tenés un modelo empaquetado fijo
MODEL_PATH="/app/models/model.tar.gz"
RASA_ARGS=( --enable-api --cors "${CORS_VAL}" -i 0.0.0.0 -p "${RASA_PORT}" --debug )
if [ -f "${MODEL_PATH}" ]; then
  RASA_ARGS+=( --model "${MODEL_PATH}" )
fi

echo "Iniciando servidor Rasa en 0.0.0.0:${RASA_PORT} ..."
rasa run "${RASA_ARGS[@]}"

wait -n
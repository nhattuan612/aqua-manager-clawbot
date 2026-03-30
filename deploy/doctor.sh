#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${AQUA_ENV_FILE:-${ROOT_DIR}/.env}"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

AQUA_APP_NAME="${AQUA_APP_NAME:-aqua_manager_clawbot}"
AQUA_PORT="${AQUA_PORT:-6080}"
AQUA_OPENCLAW_HOME="${AQUA_OPENCLAW_HOME:-$HOME/.openclaw}"
AQUA_WORKSPACE_DIR="${AQUA_WORKSPACE_DIR:-${AQUA_OPENCLAW_HOME}/workspace}"
AQUA_OPENCLAW_BIN="${AQUA_OPENCLAW_BIN:-$(command -v openclaw || true)}"
AQUA_PM2_BIN="${AQUA_PM2_BIN:-$(command -v pm2 || true)}"
AQUA_GATEWAY_URL="${AQUA_GATEWAY_URL:-http://127.0.0.1:18789}"

echo "== AQUA Doctor =="
echo "Root: ${ROOT_DIR}"
echo "Env:  ${ENV_FILE}"
echo "Port: ${AQUA_PORT}"
echo "OpenClaw home: ${AQUA_OPENCLAW_HOME}"
echo "Workspace:     ${AQUA_WORKSPACE_DIR}"
echo "Gateway URL:   ${AQUA_GATEWAY_URL}"
echo

check_path() {
  local label="$1" path="$2"
  if [[ -e "${path}" ]]; then
    echo "[ok] ${label}: ${path}"
  else
    echo "[!!] ${label} missing: ${path}"
  fi
}

check_path "app.py" "${ROOT_DIR}/app/app.py"
check_path "index.html" "${ROOT_DIR}/app/templates/index.html"
check_path ".env" "${ENV_FILE}"
check_path "OpenClaw home" "${AQUA_OPENCLAW_HOME}"
check_path "Workspace" "${AQUA_WORKSPACE_DIR}"

if [[ -n "${AQUA_OPENCLAW_BIN}" && -x "${AQUA_OPENCLAW_BIN}" ]]; then
  echo "[ok] openclaw bin: ${AQUA_OPENCLAW_BIN}"
else
  echo "[!!] openclaw bin not found"
fi

if [[ -n "${AQUA_PM2_BIN}" && -x "${AQUA_PM2_BIN}" ]]; then
  echo "[ok] pm2 bin: ${AQUA_PM2_BIN}"
  "${AQUA_PM2_BIN}" describe "${AQUA_APP_NAME}" >/dev/null 2>&1 && echo "[ok] PM2 app exists: ${AQUA_APP_NAME}" || echo "[..] PM2 app not started yet: ${AQUA_APP_NAME}"
else
  echo "[!!] pm2 bin not found"
fi

if command -v curl >/dev/null 2>&1; then
  curl -fsS --max-time 5 "${AQUA_GATEWAY_URL}/" >/dev/null 2>&1 && echo "[ok] gateway reachable: ${AQUA_GATEWAY_URL}" || echo "[..] gateway not reachable from doctor: ${AQUA_GATEWAY_URL}"
  curl -fsS --max-time 5 "http://127.0.0.1:${AQUA_PORT}/login" >/dev/null 2>&1 && echo "[ok] dashboard login reachable on local port ${AQUA_PORT}" || echo "[..] dashboard login not reachable yet on local port ${AQUA_PORT}"
fi

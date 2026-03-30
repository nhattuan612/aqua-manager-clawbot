#!/usr/bin/env bash
set -euo pipefail

# Stable launch wrapper used by PM2/systemd.
# Keep every runtime decision here so upgrades do not need to rewrite the PM2
# definition. This also lets us prefer a production WSGI server while keeping a
# Python fallback for recovery/debug sessions.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${AQUA_ENV_FILE:-${ROOT_DIR}/.env}"

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

AQUA_HOST="${AQUA_HOST:-0.0.0.0}"
AQUA_PORT="${AQUA_PORT:-6080}"

if [[ -x "${ROOT_DIR}/.venv/bin/waitress-serve" ]]; then
  cd "${ROOT_DIR}/app"
  # Waitress is intentionally preferred over Flask's built-in server because
  # this package is meant to be moved between VPS hosts and kept running under
  # PM2 for long periods.
  exec "${ROOT_DIR}/.venv/bin/waitress-serve" --host "${AQUA_HOST}" --port "${AQUA_PORT}" app:app
fi

if [[ -x "${ROOT_DIR}/.venv/bin/python" ]]; then
  # Fallback path for break-glass recovery when dependencies are partially
  # installed. Keeping this path makes upgrades easier to recover remotely.
  exec "${ROOT_DIR}/.venv/bin/python" "${ROOT_DIR}/app/app.py"
fi

exec python3 "${ROOT_DIR}/app/app.py"

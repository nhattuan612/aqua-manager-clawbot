#!/usr/bin/env bash
set -euo pipefail

# Restore a previous AQUA Manager snapshot into the current install directory.
# Keep this script simple and explicit so rollback remains dependable even under
# incident pressure on a remote VPS.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${AQUA_ENV_FILE:-${ROOT_DIR}/.env}"
SNAPSHOT_DIR="${1:-}"

if [[ -z "${SNAPSHOT_DIR}" ]]; then
  echo "Usage: bash deploy/rollback.sh /path/to/snapshot" >&2
  exit 1
fi

if [[ ! -d "${SNAPSHOT_DIR}" ]]; then
  echo "Snapshot not found: ${SNAPSHOT_DIR}" >&2
  exit 1
fi

restore_tree() {
  local name="$1"
  if [[ -d "${SNAPSHOT_DIR}/${name}" ]]; then
    rm -rf "${ROOT_DIR:?}/${name}"
    cp -R "${SNAPSHOT_DIR}/${name}" "${ROOT_DIR}/${name}"
  fi
}

restore_file() {
  local name="$1"
  if [[ -f "${SNAPSHOT_DIR}/${name}" ]]; then
    cp "${SNAPSHOT_DIR}/${name}" "${ROOT_DIR}/${name}"
  fi
}

restore_tree app
restore_tree config
restore_tree deploy
restore_tree docs
restore_tree migrations
restore_file README.md
restore_file VERSION
restore_file requirements.txt

if [[ -f "${SNAPSHOT_DIR}/.env" ]]; then
  cp "${SNAPSHOT_DIR}/.env" "${ENV_FILE}"
fi

python3 -m venv "${ROOT_DIR}/.venv"
"${ROOT_DIR}/.venv/bin/pip" install --upgrade pip >/dev/null
"${ROOT_DIR}/.venv/bin/pip" install -r "${ROOT_DIR}/requirements.txt"

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

PM2_BIN="${AQUA_PM2_BIN:-$(command -v pm2 || true)}"
AQUA_APP_NAME="${AQUA_APP_NAME:-aqua_manager_clawbot}"
AQUA_PORT="${AQUA_PORT:-6080}"
export AQUA_ENV_FILE="${ENV_FILE}"
export AQUA_APP_NAME="${AQUA_APP_NAME}"

if [[ -z "${PM2_BIN}" || ! -x "${PM2_BIN}" ]]; then
  echo "PM2 not found. Set AQUA_PM2_BIN in ${ENV_FILE} or install PM2 first." >&2
  exit 1
fi

"${PM2_BIN}" startOrReload "${ROOT_DIR}/deploy/ecosystem.config.cjs" --update-env

for _ in $(seq 1 45); do
  if curl -fsS --max-time 3 "http://127.0.0.1:${AQUA_PORT}/login" >/dev/null 2>&1; then
    bash "${ROOT_DIR}/deploy/doctor.sh"
    echo "Rollback complete from ${SNAPSHOT_DIR}"
    exit 0
  fi
  sleep 1
done

echo "Rollback restored files, but dashboard did not become ready on port ${AQUA_PORT}" >&2
exit 1

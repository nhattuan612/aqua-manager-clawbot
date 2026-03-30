#!/usr/bin/env bash
set -euo pipefail

# Install or refresh AQUA Manager as a companion app next to OpenClaw.
# The script copies the package to a stable install directory, creates a venv,
# installs Python deps, starts PM2, and runs health checks.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
INSTALL_DIR="${AQUA_INSTALL_DIR:-$HOME/.aqua-manager-clawbot}"
ENV_FILE="${AQUA_ENV_FILE:-${INSTALL_DIR}/.env}"

require_bin() {
  command -v "$1" >/dev/null 2>&1 || {
    echo "Missing required command: $1" >&2
    exit 1
  }
}

generate_secret_key() {
  python3 - <<'PY'
import secrets
print(secrets.token_urlsafe(48))
PY
}

sync_tree() {
  local src="$1" dst="$2"
  if command -v rsync >/dev/null 2>&1; then
    rsync -a \
      --delete \
      --exclude ".git" \
      --exclude ".venv" \
      --exclude ".env" \
      --exclude ".update-snapshots" \
      --exclude ".aqua-manager-snapshots" \
      --exclude "__pycache__" \
      "${src}/" "${dst}/"
    return
  fi

  rm -rf "${dst}/app" "${dst}/config" "${dst}/deploy" "${dst}/docs" "${dst}/migrations"
  mkdir -p "${dst}"
  cp -R "${src}/app" "${src}/config" "${src}/deploy" "${src}/docs" "${src}/migrations" "${dst}/"
  cp "${src}/README.md" "${src}/VERSION" "${src}/requirements.txt" "${dst}/"
}

wait_for_http() {
  local url="$1" label="$2" timeout="${3:-30}" elapsed=0
  while (( elapsed < timeout )); do
    if curl -fsS --max-time 3 "${url}" >/dev/null 2>&1; then
      echo "[ok] ${label}: ${url}"
      return 0
    fi
    sleep 1
    elapsed=$((elapsed + 1))
  done
  echo "[!!] Timed out waiting for ${label}: ${url}" >&2
  return 1
}

first_non_loopback_ip() {
  if command -v hostname >/dev/null 2>&1; then
    hostname -I 2>/dev/null | awk '{for (i = 1; i <= NF; i++) if ($i !~ /^127\\./) { print $i; exit }}'
    return 0
  fi
  return 0
}

require_bin python3
require_bin curl

mkdir -p "${INSTALL_DIR}"

sync_tree "${SOURCE_DIR}" "${INSTALL_DIR}"

if [[ ! -f "${ENV_FILE}" ]]; then
  cp "${INSTALL_DIR}/config/aqua.env.example" "${ENV_FILE}"
  GENERATED_SECRET="$(generate_secret_key)"
  python3 - "${ENV_FILE}" "${GENERATED_SECRET}" <<'PY'
import pathlib
import sys

env_path = pathlib.Path(sys.argv[1])
secret = sys.argv[2]
content = env_path.read_text()
content = content.replace("AQUA_SECRET_KEY=CHANGE_ME_LONG_RANDOM_SECRET", f"AQUA_SECRET_KEY={secret}")
env_path.write_text(content)
PY
  echo "Created ${ENV_FILE} from example. Edit it before exposing the dashboard publicly."
fi

python3 -m venv "${INSTALL_DIR}/.venv"
"${INSTALL_DIR}/.venv/bin/pip" install --upgrade pip >/dev/null
"${INSTALL_DIR}/.venv/bin/pip" install -r "${INSTALL_DIR}/requirements.txt"

set -a
# shellcheck disable=SC1090
source "${ENV_FILE}"
set +a

APP_NAME="${AQUA_APP_NAME:-aqua_manager_clawbot}"
APP_PORT="${AQUA_PORT:-6080}"
PUBLIC_BASE_URL="${AQUA_PUBLIC_BASE_URL:-}"
export AQUA_ENV_FILE="${ENV_FILE}"
export AQUA_APP_NAME="${APP_NAME}"

PM2_BIN="${AQUA_PM2_BIN:-$(command -v pm2 || true)}"
if [[ -z "${PM2_BIN}" || ! -x "${PM2_BIN}" ]]; then
  echo "PM2 not found. Set AQUA_PM2_BIN in ${ENV_FILE} or install PM2 first." >&2
  exit 1
fi

"${PM2_BIN}" startOrReload "${INSTALL_DIR}/deploy/ecosystem.config.cjs" --update-env

# Wait for the local dashboard port before running doctor/smoke tests. This
# avoids false negatives right after first install or after dependency upgrades.
wait_for_http "http://127.0.0.1:${APP_PORT}/login" "dashboard login" 45

"${INSTALL_DIR}/deploy/doctor.sh"
"${INSTALL_DIR}/deploy/smoke-test.sh"

echo
echo "AQUA Manager installed at ${INSTALL_DIR}"
echo "PM2 app: ${APP_NAME}"
echo "Env file: ${ENV_FILE}"
echo
echo "==== Access Information ===="
echo "Local login URL: http://127.0.0.1:${APP_PORT}/login"
SERVER_IP="$(first_non_loopback_ip || true)"
if [[ -n "${SERVER_IP:-}" ]]; then
  echo "Server IP login URL: http://${SERVER_IP}:${APP_PORT}/login"
fi
if [[ -n "${PUBLIC_BASE_URL}" ]]; then
  echo "Public login URL: ${PUBLIC_BASE_URL%/}/login"
else
  echo "Public login URL: set AQUA_PUBLIC_BASE_URL in ${ENV_FILE} if you want a canonical domain-based link."
fi
echo "Login password: read AQUA_ADMIN_PASSWORD from ${ENV_FILE}"
echo
echo "If this is a fresh install, review these values before wide exposure:"
echo "- AQUA_ADMIN_PASSWORD"
echo "- AQUA_SECRET_KEY"
echo "- AQUA_PUBLIC_BASE_URL"
echo "- AQUA_SSH_HOST / AQUA_SSH_USER / AQUA_SSH_PORT"
if grep -q '^AQUA_ADMIN_PASSWORD=123456789$' "${ENV_FILE}"; then
  echo
  echo "[warn] AQUA_ADMIN_PASSWORD is still the default 123456789. Change it before broad public exposure."
fi

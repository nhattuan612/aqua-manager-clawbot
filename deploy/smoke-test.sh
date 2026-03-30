#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
ENV_FILE="${AQUA_ENV_FILE:-${ROOT_DIR}/.env}"
COOKIE_JAR="$(mktemp)"
trap 'rm -f "${COOKIE_JAR}"' EXIT

if [[ -f "${ENV_FILE}" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "${ENV_FILE}"
  set +a
fi

AQUA_PORT="${AQUA_PORT:-6080}"
AQUA_ADMIN_PASSWORD="${AQUA_ADMIN_PASSWORD:-AQUA_2026}"
BASE_URL="http://127.0.0.1:${AQUA_PORT}"

echo "== AQUA Smoke Test =="

curl -fsS -c "${COOKIE_JAR}" --data-urlencode "password=${AQUA_ADMIN_PASSWORD}" -X POST "${BASE_URL}/login" -o /dev/null
for endpoint in / /api/system /api/missions /api/tokens /api/reminders /api/skills /api/git-packages /api/backup-targets /api/logs/openclaw /api/telegram-access /api/openclaw-access; do
  echo "Checking ${endpoint}"
  curl -fsS -b "${COOKIE_JAR}" "${BASE_URL}${endpoint}" -o /dev/null
done

echo "Smoke test passed."

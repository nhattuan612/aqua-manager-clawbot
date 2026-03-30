#!/usr/bin/env bash
set -euo pipefail

# Safe upgrade path:
# 1. snapshot current install
# 2. sync new files
# 3. refresh Python deps
# 4. reload PM2
# 5. wait for readiness
# 6. run doctor + smoke tests

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SOURCE_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
INSTALL_DIR="${AQUA_INSTALL_DIR:-$HOME/.aqua-manager-clawbot}"
ENV_FILE="${AQUA_ENV_FILE:-${INSTALL_DIR}/.env}"
STAMP="$(date +%Y%m%d_%H%M%S)"
SNAPSHOT_DIR="${INSTALL_DIR}/.update-snapshots/${STAMP}"

mkdir -p "${SNAPSHOT_DIR}"

if [[ -d "${INSTALL_DIR}/app" ]]; then
  rsync -a \
    --exclude ".venv" \
    --exclude ".update-snapshots" \
    "${INSTALL_DIR}/" "${SNAPSHOT_DIR}/"
fi

bash "${SOURCE_DIR}/deploy/install.sh"

echo "Update snapshot saved at ${SNAPSHOT_DIR}"
echo "If needed, restore files from that snapshot and restart PM2."

#!/usr/bin/env bash
set -euo pipefail

# Build a clean release tarball that can be copied to another VPS or attached
# to a GitHub/GitLab release.

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "${SCRIPT_DIR}/.." && pwd)"
VERSION="$(tr -d '\n' < "${ROOT_DIR}/VERSION")"
OUTPUT_DIR="${AQUA_RELEASE_DIR:-${ROOT_DIR}/dist}"
ARCHIVE_NAME="aqua-manager-clawbot-${VERSION}.tar.gz"
CHECKSUM_NAME="${ARCHIVE_NAME}.sha256"

mkdir -p "${OUTPUT_DIR}"

export COPYFILE_DISABLE=1

tar \
  --exclude=".git" \
  --exclude=".venv" \
  --exclude=".github" \
  --exclude="dist" \
  --exclude=".DS_Store" \
  --exclude="__pycache__" \
  -czf "${OUTPUT_DIR}/${ARCHIVE_NAME}" \
  -C "$(dirname "${ROOT_DIR}")" \
  "$(basename "${ROOT_DIR}")"

if command -v sha256sum >/dev/null 2>&1; then
  (
    cd "${OUTPUT_DIR}"
    sha256sum "${ARCHIVE_NAME}" > "${CHECKSUM_NAME}"
  )
else
  (
    cd "${OUTPUT_DIR}"
    shasum -a 256 "${ARCHIVE_NAME}" > "${CHECKSUM_NAME}"
  )
fi

echo "Release package created: ${OUTPUT_DIR}/${ARCHIVE_NAME}"
echo "Checksum created: ${OUTPUT_DIR}/${CHECKSUM_NAME}"

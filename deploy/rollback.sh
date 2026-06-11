#!/usr/bin/env bash
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
#
# Roll back to the previously deployed image tag (target < 30s).
# Reads deploy/.last_tag written by deploy.sh.
set -euo pipefail

HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LAST_TAG_FILE="${HERE}/.last_tag"

if [[ ! -f "${LAST_TAG_FILE}" ]]; then
    echo "[rollback] no .last_tag recorded — nothing to roll back to" >&2
    exit 1
fi

PREVIOUS="$(cat "${LAST_TAG_FILE}")"
echo "[rollback] reverting to ${PREVIOUS}"

# Image already present locally from the prior deploy → fast swap, no pull.
IMAGE_REF="${PREVIOUS}" docker compose -f "${HERE}/docker-compose.yml" up -d --no-build

"${HERE}/healthcheck.sh"
echo "[rollback] done — running ${PREVIOUS}"

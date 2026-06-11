#!/usr/bin/env bash
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
#
# Deploy a given image tag on Yahboom (run on the device).
#   ./deploy.sh v1.0.0      # or :latest if omitted
# Records the previously running tag to deploy/.last_tag for rollback.sh.
set -euo pipefail

IMAGE="${IMAGE:-ghcr.io/saibusu/aifinal}"
TAG="${1:-latest}"
HERE="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Save the currently running tag (if any) so rollback can return to it.
CURRENT="$(docker inspect --format '{{ index .Config.Image }}' waste-sorter 2>/dev/null || true)"
if [[ -n "${CURRENT}" ]]; then
    echo "${CURRENT}" > "${HERE}/.last_tag"
    echo "[deploy] previous image recorded: ${CURRENT}"
fi

echo "[deploy] pulling ${IMAGE}:${TAG}"
docker pull "${IMAGE}:${TAG}"

echo "[deploy] starting service"
IMAGE_REF="${IMAGE}:${TAG}" docker compose -f "${HERE}/docker-compose.yml" up -d

"${HERE}/healthcheck.sh"
echo "[deploy] done — Dashboard on http://localhost:8000"

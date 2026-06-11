#!/usr/bin/env bash
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
#
# Poll the Dashboard /health endpoint until it returns 200 (or time out).
set -euo pipefail

URL="${HEALTH_URL:-http://localhost:8000/health}"
RETRIES="${HEALTH_RETRIES:-20}"
SLEEP="${HEALTH_SLEEP:-3}"

for i in $(seq 1 "${RETRIES}"); do
    if curl -fsS "${URL}" >/dev/null 2>&1; then
        echo "[healthcheck] OK (${URL})"
        exit 0
    fi
    echo "[healthcheck] attempt ${i}/${RETRIES} not ready, retrying in ${SLEEP}s..."
    sleep "${SLEEP}"
done

echo "[healthcheck] FAILED: ${URL} not healthy after ${RETRIES} attempts" >&2
exit 1

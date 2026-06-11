#!/usr/bin/env bash
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
#
# Container entrypoint: compile the TensorRT FP16 engine on first run (needs the
# device GPU, so it cannot happen at build time — ADR-003), then launch the app.
set -euo pipefail

MODEL_PATH="${MODEL_PATH:-/app/models/best_v6.engine}"
ONNX_PATH="${ONNX_PATH:-/app/models/best_v6.onnx}"
TRTEXEC="${TRTEXEC:-/usr/src/tensorrt/bin/trtexec}"

if [[ "${MODEL_PATH}" == *.engine && ! -f "${MODEL_PATH}" ]]; then
    if [[ -f "${ONNX_PATH}" ]]; then
        echo "[entrypoint] engine missing — compiling TensorRT FP16 from ${ONNX_PATH}"
        "${TRTEXEC}" --onnx="${ONNX_PATH}" --saveEngine="${MODEL_PATH}" --fp16
    else
        echo "[entrypoint] WARNING: neither ${MODEL_PATH} nor ${ONNX_PATH} found." >&2
        echo "[entrypoint] mount a volume with the model into /app/models." >&2
    fi
fi

echo "[entrypoint] starting waste-sorter app (model=${MODEL_PATH})"
exec python3 -m src.app

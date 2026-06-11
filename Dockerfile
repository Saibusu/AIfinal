# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
#
# arm64 image for Yahboom (Jetson Orin Nano compatible, JetPack 6).
# Base bundles PyTorch + TensorRT + ultralytics + OpenCV(GStreamer) for Jetson,
# so we only add the light app deps. The TensorRT FP16 engine is compiled at
# runtime in the entrypoint (needs the device GPU), NOT during build — per ADR-003.

FROM ultralytics/ultralytics:latest-jetson-jetpack6

WORKDIR /app

# App deps only; ultralytics + opencv ship in the base image.
# Pinned to a major version (capstone §B.2).
RUN pip install --no-cache-dir \
        "paho-mqtt>=2.0,<3" \
        "pyyaml>=6.0,<7" \
        "fastapi>=0.110,<1" \
        "uvicorn[standard]>=0.29,<1"

COPY src/ ./src/
COPY scripts/ ./scripts/
COPY docker-entrypoint.sh ./
RUN chmod +x docker-entrypoint.sh

# Runtime config (override via `docker run -e` / compose). No hardcoded paths.
ENV MODEL_PATH=/app/models/best_v6.engine \
    ONNX_PATH=/app/models/best_v6.onnx \
    DASHBOARD_HOST=0.0.0.0 \
    DASHBOARD_PORT=8000 \
    PYTHONUNBUFFERED=1

EXPOSE 8000

HEALTHCHECK --interval=30s --timeout=5s --start-period=60s --retries=3 \
    CMD python3 -c "import urllib.request,sys; sys.exit(0 if urllib.request.urlopen('http://localhost:8000/health').status==200 else 1)"

ENTRYPOINT ["./docker-entrypoint.sh"]

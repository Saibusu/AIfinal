#!/bin/bash
# Copyright (c) 2026 李軒杰, 黃義鈞 / Datung University — I4210 AI實務專題
# 在 Yahboom Jetson 上一鍵啟動垃圾分類 Demo
#
# 用法：
#   bash run.sh                            # 預設：models/best_v6.engine
#   bash run.sh /path/to/best_v6.engine   # 指定 engine 路徑
#   MQTT_BROKER=192.168.1.x bash run.sh   # 啟用 MQTT

set -e
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
cd "$SCRIPT_DIR"

MODEL_PATH="${1:-models/best_v6.engine}"

if [ ! -f "$MODEL_PATH" ]; then
    echo "[ERROR] engine 不存在：$MODEL_PATH"
    echo "請先在 Jetson 上執行 TensorRT 編譯，或用 CAMERA_SOURCE 覆蓋相機來源。"
    exit 1
fi

echo "[INFO] 安裝 Python 依賴..."
pip install -q -r requirements.txt

echo "[INFO] 啟動系統，model=$MODEL_PATH"
echo "[INFO] Dashboard → http://$(hostname -I | awk '{print $1}'):8000"
MODEL_PATH="$MODEL_PATH" python3 main.py

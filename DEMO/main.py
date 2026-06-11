#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞 / Datung University — I4210 AI實務專題
"""智慧零接觸垃圾分類系統 — 單檔啟動器（Yahboom Jetson Orin Nano）

本檔**只是 bare-metal 一鍵啟動器**：把 repo root 加入 sys.path 後呼叫
`src/app.py` 的 `main()`。所有實際邏輯都在 `src/`（被單元測試 + CI 保證），
**不在此重複實作**，避免「demo 跑的程式 ≠ 測試保證的程式」的漂移風險。

用法：
    bash run.sh                              # CSI 相機 + models/best_v6.engine
    MODEL_PATH=xxx.engine python3 main.py    # 指定 engine
    CAMERA_SOURCE="..." python3 main.py      # 覆蓋相機來源
    MQTT_BROKER=192.168.1.x python3 main.py  # 啟用 MQTT
    瀏覽器開 http://<jetson-ip>:8000
"""
from __future__ import annotations

import pathlib
import sys

# repo root（DEMO/ 的上一層）→ 讓 `import src.*` 可用（bare-metal、非 Docker 路徑）
sys.path.insert(0, str(pathlib.Path(__file__).resolve().parent.parent))

from src.app import main  # noqa: E402  (must follow sys.path setup)

if __name__ == "__main__":
    main()

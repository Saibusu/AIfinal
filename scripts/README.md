# scripts/ — 工具腳本

| 計畫檔案 | 用途 |
|---------|------|
| `parse_tegrastats.py` | 解析 `tegrastats.log` → `utilization.csv`（CPU%/GPU%/power 等）|
| `download_engine.sh` | 下載預編譯 TensorRT engine（避免每次重編）|
| `eval_accuracy.py` | 在 held-out set 評估 mAP，更新 `accuracy_baseline.json` |

規範：腳本須能透過 env var 或 CLI flag 覆蓋輸入路徑（方便 grader 重跑）。
所有 `.py/.sh` 需 Copyright header。

# 智慧零接觸垃圾分類系統 (Smart Touchless Waste Sorting System)

> by 李軒杰 (I4A70) & 黃義鈞 (I4B58) — 大同大學 I4210 AI實務專題

部署於公共區域智慧垃圾桶，透過 Jetson Orin Nano 相容套件（Yahboom）即時辨識垃圾種類，
點亮對應分類 LED 引導使用者正確分類。完整 **Sense → Process → Decide → Act** 閉環。

## 系統概觀

| 階段 | 元件 | 說明 |
|------|------|------|
| Sense | IMX219 攝影機 | CSI-2 即時影像擷取 |
| Process | YOLO26m + TensorRT FP16 | 5 類垃圾分類推論（imgsz=416）|
| Decide | 決策邏輯 | class ID → LED 顏色，信心 < 閾值 → 一般垃圾 |
| Act | GPIO LED ×5 | 點亮對應顏色 LED 5 秒 |

## 5 垃圾分類

| ID | 類別 | GPIO Pin (Yahboom) | LED |
|----|------|-------------------|-----|
| 0  | 寶特瓶 | Pin 11 | 綠 |
| 1  | 鐵鋁罐 | Pin 13 | 黃 |
| 2  | 紙餐盒 | Pin 15 | 藍 |
| 3  | 塑膠袋 | Pin 21 | 白 |
| 4  | 一般垃圾 | Pin 23 | 紅 |

## 快速開始

```bash
# 安裝核心相依 + 開發工具（輕量，純邏輯測試足夠）
pdm install -d

# 執行測試（覆蓋率 gate ≥ 90%）
pdm run pytest

# 需要實際推論 / Dashboard 時，額外安裝對應 extras：
pdm install -G inference   # ultralytics, opencv（YOLO 推論）
pdm install -G dashboard   # fastapi, uvicorn（Web Dashboard）

# Docker（Jetson 上）— 待 ADR-003 實作後填入
# docker pull ghcr.io/saibusu/aifinal:latest
# docker run --runtime nvidia ghcr.io/saibusu/aifinal:latest
```

> 相依分層：核心（paho-mqtt, pyyaml）保持輕量讓 CI 快速；重量級執行期套件
> （torch/opencv/fastapi）放在 optional extras，測試於邊界 mock（見 pyproject.toml）。

## MQTT Topic Map

| Topic | 用途 |
|-------|------|
| `waste/detection` | 分類結果（class_id, confidence, timestamp）|
| `waste/status` | 系統狀態（fps, uptime）|

## 專案文件

完整文件索引見 [docs/README.md](docs/README.md)：架構決策（ADR）、功能規格（SPEC）、領域詞彙（CONTEXT）。

## 開發規範

本專案遵循 ASP (AI-SOP-Protocol) 流程，詳見 [CLAUDE.md](CLAUDE.md)。
所有架構決策需經 ADR 核准（G1），功能需 SPEC 定義（G2），測試先行（G3 TDD）。

# final — AI 行為設定

> ASP v4.3 | 讀取順序：本檔案 → `.ai_profile` → `~/.claude/CLAUDE.md`（user-level 鐵則）
> Profile 邏輯與 ASP skills 詳見 `~/.claude/asp/profiles/` 與 `~/.claude/skills/asp/`

## 專案說明

**智慧零接觸垃圾分類系統 (Smart Touchless Waste Sorting System)**
- 課程：大同大學 I4210 AI實務專題 — 期末專題
- 團隊：李軒杰 (I4A70) + 黃義鈞 (I4B58)
- 硬體：Yahboom 套裝（類 Jetson Orin Nano 第三方套件，GPIO 針腳與原版不同）
- 模型：YOLO26m + TensorRT FP16，Kaggle 訓練（v6，waste_sorter_v6）
- 交期：2026-06-19 23:59（TronClass / iLearn）

**5 垃圾分類與 GPIO（Yahboom）：**
| ID | 類別   | GPIO Pin | LED 顏色 |
|----|--------|----------|---------|
| 0  | 寶特瓶 | Pin 11   | 綠      |
| 1  | 鐵鋁罐 | Pin 13   | 黃      |
| 2  | 紙餐盒 | Pin 15   | 藍      |
| 3  | 塑膠袋 | Pin 21   | 白      |
| 4  | 一般垃圾 | Pin 23 | 紅      |

**與提案差異（詳見 ADR-002）：**
1. 鋁箔包（Tetra Pak）→ 歸入一般垃圾（class 4），不再獨立分類
2. 蜂鳴器取消（actuator 只剩 LED）
3. Yahboom GPIO 針腳與原版 Jetson Orin Nano 不同，統一在 `src/actuator_controller.py` 管理

## 特殊規則（覆蓋 user-level 預設）

- **禁止修改 `docs/proposal/`**：原始提案書唯讀
- **每個 `.md` 檔案 ≤ 300 行**：超出時拆分子文件，確保 Claude 可完整讀取
- **所有 `.py/.sh/.yml` 必須有 Copyright header**（格式：`# Copyright (c) 2026 李軒杰, 黃義鈞 / Datung University — I4210 AI實務專題`）
- **GPIO 針腳統一在 `src/actuator_controller.py`**，不可分散
- **Draft ADR 不得有對應生產代碼**（ASP G1 鐵則）
- **測試覆蓋率 ≥ 90%**，CI 強制執行（`--cov-fail-under=90`）
- **文件語言**：技術文件用中文，程式碼 + CI/CD 用英文

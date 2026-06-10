# Changelog

本檔案記錄所有重大變更，供審查、rollback 與問題追蹤使用。
格式依循 [Keep a Changelog](https://keepachangelog.com/)，版本依 [SemVer](https://semver.org/)。

## [Unreleased]

### Added
- 專案 ASP 初始化（v4.3.0，type=system，level=L3）
- 完整目錄結構（src/tests/deploy/calibration/data/scripts/report/notebooks/.github）
- 核心文件：README.md、CONTEXT.md、docs/README.md（文件索引）
- ADR-001：模型選擇 YOLO26m + TensorRT FP16
- ADR-002：四項實作變動（鋁箔包歸類 / 取消蜂鳴器 / Yahboom GPIO / 資料集來源）
- ADR-003：5-stage CI/CD pipeline 架構
- SPEC-001/002/003：InferenceNode / ActuatorController / DashboardServer
- pyproject.toml（PDM + ruff + pytest + coverage≥90%）
- accuracy_baseline.json（待首次 Jetson 評估填入）
- 訓練 notebook 歸類至 notebooks/train_waste_sorter_v6.ipynb

### Changed
- 與提案差異（詳見 ADR-002）：
  - 垃圾分類由 6 類 → 5 類（鋁箔包併入一般垃圾）
  - 致動器移除蜂鳴器，僅保留 5 色 LED
  - GPIO 針腳改用 Yahboom 套裝編號（BOARD 模式）
  - 資料集由「自建 300–500 張」→ Roboflow 公開資料集（13,104 張）
- 三份 ADR 經人類核准：Draft → Accepted（2026-06-11）

### 決策對應（Traceability）
| 項目 | 文件 | Gate |
|------|------|------|
| 模型選型 | ADR-001 (Accepted) | G1 ✅ |
| 實作變動 | ADR-002 (Accepted) | G1 ✅ |
| CI/CD 架構 | ADR-003 (Accepted) | G1 ✅ |
| 三個核心模組規格 | SPEC-001/002/003 | G2 ✅ |

---

> 版本標記慣例：scaffolding 里程碑 `v0.x`，首個可部署版本 `v1.0.0`。

# 專案文件索引 (Documentation Index)

> 所有專案文件的分類與導覽。新增文件時請同步更新此索引。

## 文件分類

| 目錄 | 用途 | 命名規範 |
|------|------|---------|
| [adr/](adr/) | 架構決策記錄 (Architecture Decision Records) | `ADR-XXX-slug.md` |
| [specs/](specs/) | 功能規格 (Specifications，七欄位) | `SPEC-XXX-slug.md` |
| [changes/](changes/) | 變更記錄（小型、非架構性變動）| `CHANGE-XXX-slug.md` |
| [proposal/](proposal/) | 原始提案書（**唯讀參考**，禁止修改）| PDF |

## ADR — 架構決策記錄

| 編號 | 標題 | 狀態 |
|------|------|------|
| [ADR-001](adr/ADR-001-yolo26m-tensorrt-fp16.md) | 模型選擇：YOLO26m + TensorRT FP16 | Draft |
| [ADR-002](adr/ADR-002-implementation-changes.md) | 實作變動：鋁箔包 / 蜂鳴器 / Yahboom GPIO / 資料集來源 | Draft |
| [ADR-003](adr/ADR-003-cicd-pipeline.md) | CI/CD Pipeline 架構（5-stage）| Draft |

## SPEC — 功能規格

| 編號 | 標題 | 對應源碼 |
|------|------|---------|
| [SPEC-001](specs/SPEC-001-inference-pipeline.md) | 推論管線 (InferenceNode) | `src/inference_node.py` |
| [SPEC-002](specs/SPEC-002-actuator-controller.md) | GPIO 致動器控制器 (ActuatorController) | `src/actuator_controller.py` |
| [SPEC-003](specs/SPEC-003-dashboard-server.md) | Dashboard 伺服器 (DashboardServer) | `src/dashboard_server.py` |

## 進度與規劃

| 文件 | 用途 |
|------|------|
| [ROADMAP.md](ROADMAP.md) | **期末要求完成度追蹤**（對照 CAPSTONE，逐項 checklist + 完成度）|
| [progress/](progress/) | 進度紀錄（訓練狀態、里程碑）|

## 其他核心文件（專案根目錄）

| 文件 | 用途 |
|------|------|
| [../CLAUDE.md](../CLAUDE.md) | AI 行為設定、專案規範、特殊規則 |
| [../CONTEXT.md](../CONTEXT.md) | 領域詞彙與術語定義 |
| [../README.md](../README.md) | 專案說明、快速開始、MQTT topic map |
| [../accuracy_baseline.json](../accuracy_baseline.json) | 模型精度基線（CI accuracy gate 依據）|

## ASP 流程對應

```
ADR (G1) → SPEC (G2) → 測試先行/紅燈 (G3) → 實作/綠燈 (G4) → reality-check (G5) → ship (G6)
```

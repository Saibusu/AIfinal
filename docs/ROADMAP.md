# ROADMAP — 期末專題完成度追蹤

> 對照 `docs/proposal/CAPSTONE_SUBMISSION.pdf` 全部要求。
> 圖例：✅ 完成 ｜ 🟡 部分 ｜ ⬜ 未開始 ｜ ➖ 不適用
> 最後更新：2026-06-11（訓練完成 mAP 0.731）

## 摘要

| 項目 | 狀態 |
|------|------|
| **交期** | 2026-06-19 23:59（TronClass / iLearn）|
| **整體完成度（可評分產出）** | 約 **24%** |
| **ASP Gate** | G1✅ G2✅ G3✅ G4✅（僅 DecisionEngine 一個模組走完）|
| **模型** | ✅ 訓練完成 waste_sorter_v6，mAP@50=0.731（> 目標 0.65）|
| **最大風險** | Docker、5-stage CI、Self-hosted runner、報告、Demo 全未開始；硬體未到位 |

## 評分項目進度總覽（總分 30）

| # | 評分項目 | 配分 | 狀態 | 完成度 |
|---|---------|-----|------|-------|
| A | 課堂簡報（Part A）| 10 | ⬜ | 0% |
| B1 | Repo 結構 & file headers | 2 | 🟡 | 60% |
| B2 | 原始碼合規（one class/file, 型別, ruff）| 3 | 🟡 | 40% |
| B3 | Docker image 在 Jetson 執行 | 2 | ⬜ | 0% |
| B4 | CI/CD 5-stage | 5 | 🟡 | 30% |
| B5 | 測試廣度 & 覆蓋率 ≥90% | 3 | 🟡 | 20%（baseline 已有數據）|
| B6 | 期末報告 PDF（10 章）| 3 | ⬜ | 0% |
| B7 | Demo 影片 | 1 | ⬜ | 0% |
| B8 | Test artifacts zip | 1 | ⬜ | 0% |

---

## B.1 — GitHub Repo（2 pts）

**Repo 生命週期**
- [x] 開發期間維持 public
- [ ] 6/19 提交後轉 private，邀請 instructor + TA（read）

**結構（mirror HW6，rubric 直接評分）**
- [x] `.github/workflows/ci.yml`（🟡 僅 lint+test 骨架）
- [ ] `.github/workflows/deploy.yml`（tag 觸發，選用但建議）
- [x] `src/`（🟡 僅 decision_engine.py）
- [x] `tests/test_*.py` + `tests/integration/`（🟡 僅 1 測試檔）
- [ ] `deploy/`：docker-compose.yml, deploy.sh, healthcheck.sh, rollback.sh
- [x] `calibration/`（➖ FP16 不需 INT8，README 已說明）
- [x] `data/held-out/`（🟡 空，待放 546 張 test set）
- [ ] `scripts/parse_tegrastats.py`
- [ ] `report/`：FINAL_REPORT.pdf, PRESENTATION.pdf, DEMO.mp4/DEMO_LINK.md
- [x] `accuracy_baseline.json`（🟡 數值 null，待 Kaggle）
- [x] `pyproject.toml`
- [ ] `Dockerfile`
- [x] `README.md`
- [x] `LICENSE`（➖ 刻意不加，需校方核准開源）

## B.2 — 原始碼合規（3 pts）

- [x] file header（`.py/.sh/.yml` 皆含 Copyright）— 現有檔案 ✅
- [x] 一檔一主類別（DecisionEngine ✅）
- [x] PDM 管理；ruff + pytest + pytest-cov dev deps
- [x] `[tool.coverage.run]` + `[tool.pytest.ini_options]` 與 `--cov-fail-under=90` 一致
- [ ] **相依釘選到 major 版本**（目前用 `>=`，需確認符合「pinned to a major version」）
- [x] public 方法型別註解 + docstring（DecisionEngine ✅；其餘模組待寫）

## B.3 — Docker Image（2 pts）

- [ ] Dockerfile（arm64；GPU/TensorRT 編譯放 entrypoint，不在 build）
- [ ] 推送 GHCR `ghcr.io/saibusu/aifinal`（:latest + :vX.Y.Z）
- [ ] Jetson `docker run --runtime nvidia` 可跑
- [ ] 設定走 env var / mount（無硬編碼路徑）
- [ ] `deploy/docker-compose.yml`
- [ ] README 附可複製的 `docker pull` / `docker run`

## B.4 — CI/CD 5-stage（5 pts）

DAG：`lint → test ┐ / security-scan ┘ → build → integration-test`
- [x] **lint**（ruff，hosted）✅
- [x] **test**（pytest --cov-fail-under=90，hosted）✅
- [ ] **security-scan**（bandit + pip-audit，hosted）
- [ ] **build**（docker buildx arm64 → GHCR :sha-<commit>）
- [ ] **integration-test**（self-hosted Jetson runner）
- [ ] 觸發條件含 pull_request + push-to-main（目前 ✅ push+PR）
- [ ] Self-hosted Yahboom runner 註冊並顯示 Idle
- [ ] （選用）deploy.yml + 審核 gate；rollback.sh <30s

## B.5 — 測試（3 pts，5 類別，覆蓋率 ≥90%）

- [x] **單元測試：推論邏輯**（DecisionEngine + InferenceNode 已做 ✅）
- [ ] **單元測試：MQTT 訊息**（publish/subscribe, schema, retry）
- [ ] **Accuracy gate**（held-out vs accuracy_baseline.json）
- [ ] **整合測試**（真實 Jetson：camera+推論+LED）
- [x] **Coverage gate**（CI 強制 ≥90%）✅
- [ ] GPIO 於單元測試用 Mock（SPEC-002 已規劃，待實作）

## B.6 — 期末報告 PDF（3 pts，8–12 頁，10 章）

- [ ] §1 問題陳述　- [ ] §2 最終架構（含與提案差異，素材在 ADR-002）
- [ ] §3 實作亮點　- [ ] §4 測試集說明（資料來源，ADR-002 變動四）
- [ ] §5 效能需求與優化歷程（targets→baseline→每步 delta）
- [ ] §6 系統效能結果（accuracy/latency/CPU%/GPU%/power）
- [ ] §7 經驗學習（v6 中斷、YOLOE/TACO 失敗路線可寫）
- [ ] §8 重做會怎麼改　- [ ] §9 個人反思（每人）　- [ ] §10 致謝與引用
- [ ] 用 `tools/md2pdf.sh` 轉 PDF，存 `report/FINAL_REPORT.pdf`

## B.7 — Demo 影片（1 pt）

- [ ] ≤10 分鐘，展示 Sense→Process→Decide→Act 完整迴路
- [ ] 攝影機對準 LED（致動器可見）；FPS / tegrastats 顯示
- [ ] Dashboard UI（FastAPI + MJPEG/WebSocket）即時更新
- [ ] 存 `report/DEMO.mp4`（<50MB）或 `report/DEMO_LINK.md`

## B.8 — Test Artifacts Zip（1 pt，上傳 TronClass）

- [ ] held-out test set（546 張影像+標註）
- [ ] `tegrastats.log` + `utilization.csv`（≥60s 滿載）
- [ ] latency / FPS benchmark CSV
- [ ] 優化歷程 log（每步 FPS/latency/...）
- [ ] 命名 `<team>_test_artifacts.zip`

## Part A — 課堂簡報（10 pts）

- [ ] 15–20 內容頁 + 標題 + 過渡頁（≈21 頁），存 `report/PRESENTATION.pdf`
- [ ] 架構圖、AI 模型選擇、與提案差異、實作亮點、CI/CD、效能結果
- [ ] 兩人均衡發言；Demo ≤10 分鐘
- [ ] 評分：簡報品質(2) 發言(2) 技術深度(2) Demo(3) Q&A(1)

---

## 模組開發狀態（src/ + tests/）

| 模組 | SPEC | 程式碼 | 測試 | Gate |
|------|------|-------|------|------|
| DecisionEngine | SPEC-004 ✅ | ✅ | ✅ 14 tests/100% | G4 ✅ |
| InferenceNode | SPEC-001 ✅ | ✅ | ✅ 15 tests/100% | G4 ✅ |
| ActuatorController | SPEC-002 ✅ | ⬜ | ⬜ | — |
| DashboardServer | SPEC-003 ✅ | ⬜ | ⬜ | — |
| MqttPublisher | ⬜（需 SPEC-005）| ⬜ | ⬜ | — |

---

## 建議執行順序（關鍵路徑）

1. **軟體模組**（可在無硬體下完成，TDD）：InferenceNode → MqttPublisher → ActuatorController(Mock GPIO) → DashboardServer
2. **容器化**：Dockerfile + docker-compose（ADR-003）
3. **CI 補滿**：security-scan + build → 再接 integration-test（需 runner）
4. **硬體相依**（待 Yahboom + Kaggle 模型）：engine 編譯、GPIO 實機、tegrastats、整合測試、accuracy gate
5. **產出文件**：報告 §1–§4（現在就能寫）→ §5–§6（需實測數據）→ 簡報 → Demo 影片

## 外部依賴（阻擋項）

- ✅ Kaggle v6 訓練結果 → mAP@50=0.731，已填 accuracy_baseline（validation；test split 待補）
- ⏳ Yahboom 硬體到位 → GPIO 實測、整合測試、Docker on Jetson、tegrastats、on-device mAP/FPS
- ⏳ Self-hosted runner 註冊 → integration-test job

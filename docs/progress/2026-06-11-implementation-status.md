# 實作進度紀錄 — 2026-06-11（軟體/容器/CI 建置）

> 承接 `2026-06-11-training-status.md`（模型線）。本檔記錄程式碼/維運線。
> 完成度與變更以 `ROADMAP.md` / `CHANGELOG.md` / `git log` 為最終依據；本檔為敘事快照。

## 本日完成（ASP TDD，皆 PC 可驗）

| 交付 | SPEC/ADR | Gate | 測試 |
|------|----------|------|------|
| DecisionEngine | SPEC-004 | G4 ✅ | 14 / 100% |
| InferenceNode | SPEC-001 | G4 ✅ | 15 / 100% |
| MqttPublisher | SPEC-005 | G4 ✅ | 8 / 100% |
| ActuatorController | SPEC-002 | G4 ✅ | 9 / 100% |
| DashboardServer | SPEC-003 | G4 ✅ | 10 / 100% |
| TegrastatsParser | SPEC-006 | G4 ✅ | 11 / 100% |
| PipelineOrchestrator | SPEC-007 | G4 ✅ | 13 / 100% |
| app.py（進入點 glue） | SPEC-007 | — | on-device |

全套件：**80 passed / 2 skipped（整合）/ 100% 覆蓋**；ruff + bandit（medium gate）零高嚴重性。

## 關鍵架構決策：單一進程 orchestrator + Dashboard

- 需求＝「畫面 + 數據」→ 排除 headless（無 UI）與 compose 雙 service（CSI 相機裝置綁定，難跨容器共享）。
- 結論：**一個進程**。uvicorn 主執行緒服務 `DashboardServer`；背景 thread 跑
  `PipelineOrchestrator.run()`，擁有相機、跑 Sense→Process→Decide→Act + MQTT；
  偵測事件經 `loop.call_soon_threadsafe` 推回 event loop 廣播。
- 畫面：MJPEG `/video_feed`；即時數據：WebSocket（事件 + FPS）+ `/health`；
  重負載數據：實機 `tegrastats` → `scripts/parse_tegrastats.py` 轉 CSV（報告 §6 / B.8）。

## 容器化 + CI（ADR-003）

- `Dockerfile`（arm64 jetpack6 base）；TensorRT FP16 engine 在 `docker-entrypoint.sh`
  編譯（需裝置 GPU，非 build 階段）；`.dockerignore`；HEALTHCHECK 打 /health。
- `deploy/`：`docker-compose.yml`（單一 service、runtime nvidia、GPIO/CSI/argus mount）、
  `deploy.sh`、`healthcheck.sh`、`rollback.sh`（讀 .last_tag，目標 <30s）。
- CI 5-stage DAG：`lint → {test, security-scan} → build(buildx arm64 → GHCR) → integration-test(self-hosted jetson)`。
  新增 bandit + pip-audit；`tests/integration/` 煙霧測試（off-device skip）。
- `.gitattributes`：強制 .sh/.py/Dockerfile 用 LF，避免 Windows CRLF 破壞 Linux shebang。

## 狀態：PC 線基本到頂

**可評分產出完成度約 45%**（軟體 6 模組 + orchestrator + 容器 + CI 全寫完）。

### 仍可在 PC 做
- 報告 §1–§4（B6，素材在 ADR-002）
- README 補 `docker pull` / `docker run`（待 CI build 推上 GHCR）
- 相依釘 major 版本（B.2 最後一項）
- 簡報 Part A（內容向）

### 卡 Yahboom 實機（使用者操作，runbook 已備指令）
- Self-hosted runner 註冊 → integration-test 跑通
- `docker run --runtime nvidia` 實跑、GPIO/CSI 整合、tegrastats 數據
- test split accuracy gate、Demo 影片

## ASP Gate

G1 ✅（ADR-001/002/003 **Accepted**）｜G2 ✅（SPEC-001~007）｜G3/G4 ✅（7 單元全紅→綠）。
G5（reality-check）/ G6（實機 smoke）待硬體階段。

---

## 更新（2026-06-12）

完成度 **~45% → ~50%**。本日進展：

- **CI 修綠**：test job 紅燈（`ModuleNotFoundError: fastapi`，自 CI #11）已修
  （fastapi 加入 dev-deps）。run d46fde8：**lint/test/security-scan/build 4/5 實測綠**；
  integration-test queued 待 self-hosted runner。arm64 映像已推 GHCR。
- **模型權重下載歸檔**：`models/best_v6.pt`(42MB) + `best_v6.onnx`(77.9MB, opset12, imgsz416)，
  gitignored；`models/README.md` 模型卡。`accuracy_baseline.json` 修 imgsz 640→416、inference 11.3ms。
  → 解鎖 Yahboom engine 編譯。
- **DEMO/ runtime 重複已收斂** ✅：`DEMO/main.py` 392 行單檔 → ~20 行薄啟動器
  （`from src.app import main`）。收斂時抓到舊 DEMO 已漂移的 bug（設錯 DashboardServer
  欄位 `_frame/_fps` → 影像流/FPS 壞掉）。現在 demo 跑的 = 被測試保證的 src/。
- **B2 依賴釘 major 完成** ✅：pyproject 全部相依 `>=X,<nextmajor`；DEMO/requirements 對齊。

### 仍缺（對照 30 分 rubric）
- ⬜ 報告 PDF（B6, 3分）、簡報（A, 10分）、Demo 影片（B7, 1分）、artifacts zip（B8, 1分）
- ⏳ 實機：runner 註冊、docker run、GPIO/CSI、tegrastats、test split mAP、on-device FPS/power
- ❌ ASP G5 reality-check 未跑、G6 實機 smoke 未過
- ⚠️ 已知待驗：paho-mqtt 2.0 的 `mqtt.Client()` 需 CallbackAPIVersion（啟用 MQTT 時實機驗）

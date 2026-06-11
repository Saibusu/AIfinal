# Changelog

本檔案記錄所有重大變更，供審查、rollback 與問題追蹤使用。
格式依循 [Keep a Changelog](https://keepachangelog.com/)，版本依 [SemVer](https://semver.org/)。

## [Unreleased]

### Changed (consistency + compliance)
- **DEMO/ runtime 收斂為單一真相**：`DEMO/main.py` 由 392 行單檔重複實作 → 改為
  ~20 行薄啟動器（`sys.path` + `from src.app import main`）。bare-metal 一鍵 `bash run.sh`
  行為不變，但現在跑的就是被單元測試 + CI 保證的 `src/` 程式
  - **收斂時抓到重複版已漂移的真實 bug**：舊 DEMO 設 `server._frame/_fps`，但
    `DashboardServer` 實際欄位是 `_frame_source/_fps_source` → 舊 DEMO 的影像流/FPS
    其實是壞的（永遠 503 / 0）。這正是「demo 跑的程式 ≠ 測試保證的程式」的風險實例
  - `DEMO/requirements.txt` 版本對齊 pyproject（`paho-mqtt` 1.6→2.0、全部釘 major）
- **依賴釘 major（§B.2）**：`pyproject.toml` 全部相依由開放 `>=` 改為釘到 major
  （`paho-mqtt>=2.0,<3`、`fastapi>=0.110,<1`、`ultralytics>=8.0,<9` …）。
  pytest/pytest-cov 上界放寬到 `<10`/`<8` 以容納 CI 已解析的 9.x/7.x（無 lockfile，避免強制降版）
  - ⚠️ 已知待驗（on-device）：`src/mqtt_publisher._build_client` 用 `mqtt.Client()` 無參數，
    paho-mqtt 2.0 需 `CallbackAPIVersion` → 啟用 MQTT 時實機需驗證/修正（屬 pragma no-cover 路徑）

### Added (model artifacts)
- **best_v6 權重下載並歸檔**：`models/best_v6.pt`(42MB) + `models/best_v6.onnx`(77.9MB, opset 12, imgsz 416)
  - 兩檔 gitignored（device-bound + 大檔，不入版控）；新增 `models/README.md` 模型卡（mAP/速度/取得方式/engine 編譯）
  - 重跑成功（非中斷）：76 epochs、best @ epoch 56、mAP@50=0.7305687620379155
  - 解鎖 Yahboom 端 TensorRT engine 編譯與整合測試（先前 entrypoint 假設 onnx 存在的依賴已備齊）
- **accuracy_baseline.json 修正**：`imgsz` 640→**416**（與 ONNX 匯出一致）、inference 11.9→**11.3ms**、
  加上 `best_epoch=56` 與 `weights` 路徑；數據（驗證 split）維持 mAP50=0.731

### Fixed (CI)
- **CI test job 紅燈：`ModuleNotFoundError: No module named 'fastapi'`**（自 CI #11 起）
  - 根因：dashboard 單元測試在 collection 時 import `fastapi`（經 `src/dashboard_server.py`），
    但 `fastapi` 只宣告在 `[project.optional-dependencies] dashboard`（extra），
    CI 的 `pdm install -d` 只裝 dev group → 測試環境缺 fastapi
  - 修正：將 `fastapi>=0.110` 加入 dev-dependencies（測試環境必須能 import 受測模組）
  - 驗證：以乾淨 venv 模擬 CI dev-only 安裝，**先重現**同一錯誤、加入 fastapi 後**全綠**（80 passed / 100%）
  - 教訓：本機曾手動 `pip install fastapi` 遮蔽了缺漏宣告 → 本機綠 ≠ CI 綠

### Added (runtime + containerization)
- **PipelineOrchestrator (SPEC-007, TDD)**：`src/pipeline_orchestrator.py`，串起完整迴路
  - frame → InferenceNode(Sense+Process+Decide) → ActuatorController(Act) → MqttPublisher → on_event(Dashboard)
  - rolling FPS、最新 JPEG 幀供 Dashboard；三 sink 各自容錯（單一失敗不終止迴圈）；run() 迴圈以 max_frames/None-frame 終止
  - 五模組全注入 → 13 tests，模組覆蓋率 100%（無相機/GPIO/模型/broker 相依）
- **src/app.py（執行進入點）**：單一進程 = uvicorn 服務 DashboardServer（主執行緒）+ 背景 thread 跑 orchestrator
  - on_event 經 `loop.call_soon_threadsafe` 跨執行緒推播；env 設定 MODEL_PATH/CAMERA_SOURCE/MQTT_BROKER/DASHBOARD_*
  - 屬硬體/事件迴圈 glue，coverage omit（實機驗證）；新增 `InferenceNode.load()`（僅載入模型，由 orchestrator 驅動讀幀）
- **容器化（ADR-003）**：`Dockerfile`（arm64 jetpack6 base）+ `.dockerignore` + `docker-entrypoint.sh`
  - TensorRT FP16 engine 在 entrypoint 編譯（需裝置 GPU，非 build 階段）；HEALTHCHECK 打 /health；deps 釘到 major
  - `deploy/`：docker-compose.yml（單一 service、runtime nvidia、GPIO/CSI/argus mount）、deploy.sh、healthcheck.sh、rollback.sh(<30s)
- **CI 補滿 5-stage（ADR-003）**：`.github/workflows/ci.yml`
  - 新增 **security-scan**（bandit medium gate + pip-audit）、**build**（buildx arm64 → GHCR :latest + :sha，GHA cache，push 才推）、**integration-test**（self-hosted jetson；`tests/integration/` 煙霧測試，hosted 端 skip）
  - DAG：lint ─┬ test ┐／└ security-scan ┘→ build → integration-test
- **TegrastatsParser (SPEC-006, TDD)**：`src/tegrastats_parser.py` + `scripts/parse_tegrastats.py`(CLI)
  - tegrastats.log → utilization.csv + avg/max 摘要（報告 §6 / B.8 artifacts；B.1 結構要求）
  - 相容 POM(JetPack5)/VDD(Orin) 電源命名、`off` 核略過、可選時間戳前綴、雜訊行略過
  - 純文字解析無硬體相依；11 tests，模組覆蓋率 100%；bandit 零發現
- **DashboardServer (SPEC-003, TDD)**：`src/dashboard_server.py`，FastAPI + WebSocket 即時監控
  - `/health`、`/`(HTML)、`/video_feed`(MJPEG multipart)、`/ws`(推播 detection/fps events)
  - `ConnectionManager`：多客戶端 broadcast、斷線客戶端靜默移除；攝影機離線 → /video_feed 503
  - frame_source / fps_source 注入 → 無需實機 CSI 相機即可單元測試（sync TestClient + asyncio.run）
  - 10 tests，模組覆蓋率 100%；**5/5 軟體模組 TDD 全到齊**（G2→G3→G4）
  - 移除未使用的 `pytest-asyncio` dev dep 與 `asyncio_mode` 設定（測試改用 TestClient + asyncio.run，清掉 config warning）
- **ActuatorController (SPEC-002, TDD)**：`src/actuator_controller.py`，Act 階段 GPIO LED 控制
  - Yahboom BOARD 針腳（11/13/15/21/23）、互斥點燈、auto-off timer、無效 class→一般垃圾、env 針腳覆蓋
  - Jetson.GPIO lazy import + 注入 mock；timer_factory 注入避免測試 sleep；9 tests，覆蓋率 100%
  - ✅ Sense→Process→Decide→Act 軟體鏈到齊（InferenceNode→DecisionEngine→ActuatorController + MqttPublisher）
- **MqttPublisher (SPEC-005, TDD)**：`src/mqtt_publisher.py`，發布 detection/status 到 MQTT
  - JSON schema 驗證、publish 重試、topic prefix；paho client 可注入（測試不連 broker）
  - 8 tests，覆蓋率 100%；滿足 CAPSTONE §B.5「MQTT 訊息測試」類別
  - 註：提案原列 MQTT 為選用，CAPSTONE 要求故正式納入
- **InferenceNode (SPEC-001, TDD)**：`src/inference_node.py`，Sense+Process 階段
  - CSI IMX219 GStreamer pipeline builder、YOLO 結果解析、選最高信心 → DecisionEngine、相機重試
  - 重量級 deps（ultralytics/opencv）lazy import；測試以 mock model 注入，無硬體依賴
  - 15 tests，模組覆蓋率 100%；G2→G3→G4 完成

### Added (planning)
- **docs/ROADMAP.md**：對照 CAPSTONE_SUBMISSION.pdf 全部要求的完成度追蹤清單（整體 ~18%）
- **docs/runbook/**：Yahboom 實機操作指令清單（engine 編譯 / GPIO 點燈 / CSI 攝影機 / tegrastats / runner / docker）

### Decided (hardware target 2026-06-11)
- **硬體目標確認 = Yahboom 實機**（arm64）；開發/部署分工：Claude 寫碼+指令，使用者在實機執行驗證（CLAUDE.md）
- **攝影機 = CSI IMX219**：InferenceNode 用 GStreamer nvarguscamerasrc pipeline，env `CAMERA_SOURCE` 可覆蓋（SPEC-001）

### Changed (corrections 2026-06-11)
- **電阻統一 220Ω**：5 顆 LED 全用 220Ω（修正先前藍/白 100Ω；SPEC-002 + ADR-002）
- **模型版本鎖定 v6**：不論 mAP 是否 < v5 的 0.755，一律採 v6（v5 訓練亦不完全），
  移除 v5 fallback（ADR-001 + training-status + memory）

### Added (training result)
- **模型訓練完成** waste_sorter_v6（Kaggle T4，76 epochs）：整體 mAP@50=**0.731**（> 目標 0.65）
- `accuracy_baseline.json` 填入實際數值（validation split；含各類別 + 速度 + accuracy gate 門檻 0.681）
- 已知弱點：塑膠袋 mAP50=0.52 / recall=0.436（防呆：低信心→一般垃圾）

### Fixed (notebook 訓練 bug)
- **Cell 6 best.pt 路徑修正**：原寫死相對路徑 `runs/train/waste_sorter_v6/weights/best.pt`
  導致 Kaggle 上 `FileNotFoundError`（ultralytics 實際 save_dir 不同）。改用
  `model.trainer.best`（+ rglob fallback），訓練完成後可靠定位權重
- **Cell 7 ONNX 匯出**：改用 `model.export()` 回傳路徑，不再用 glob 猜
- 安全提醒：跑用的 notebook8d444b22b9.ipynb 含硬編碼 Roboflow key（已 gitignore 不入版控；建議輪替金鑰）

### Fixed / 影響分析（AI-course 舊專案）
- **notebook 移除 AI-course 死連結**：Cell 3 原 `git clone Saibusu/AI-course` 改為純建立工作目錄；
  確認訓練對 AI-course 程式碼零依賴（資料來自 Roboflow、權重來自 ultralytics、映射在 notebook 內）
- **模型版本事實釐清**（docs/progress/2026-06-11-training-status.md）：
  v6 訓練曾於 epoch 72 中斷（Kernel crash），**best_v6 從未產生**；舊 production 為 v5 (mAP 0.755)；
  目前 Kaggle 重跑中，ADR-001 暫維持 v6 命名，待結果決定（fallback：v5）
- **GPIO 針腳研究確認**（ADR-002）：BOARD 模式 = 物理腳位，Yahboom 與原版一致；
  釐清與舊 wiring.md（6 類）的差異；藍/白 LED 電阻修正為 100Ω（SPEC-002）

### Added
- **SPEC-004 + DecisionEngine（首個生產模組，TDD）**
  - `src/decision_engine.py`：Decide 階段純邏輯（class 對應 + 信心閾值 + 低信心防呆）
  - `tests/test_decision_engine.py`：14 個測試，覆蓋率 100%
  - ASP 流程：G2（SPEC）✅ → G3（紅燈）✅ → G4（綠燈）✅
- **CI 骨架** `.github/workflows/ci.yml`：lint（ruff）+ test（pytest, cov≥90%）on hosted runner（ADR-003 / W12 里程碑）
- `conftest.py`、`src/__init__.py`（package 骨架）
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
- 相依分層：核心 deps 輕量化，重量級執行期套件（ultralytics/opencv/fastapi）移至 optional extras（inference / dashboard）

### 決策對應（Traceability）
| 項目 | 文件 | Gate |
|------|------|------|
| 模型選型 | ADR-001 (Accepted) | G1 ✅ |
| 實作變動 | ADR-002 (Accepted) | G1 ✅ |
| CI/CD 架構 | ADR-003 (Accepted) | G1 ✅ |
| 三個核心模組規格 | SPEC-001/002/003 | G2 ✅ |

---

> 版本標記慣例：scaffolding 里程碑 `v0.x`，首個可部署版本 `v1.0.0`。

# CONTEXT.md — 領域詞彙與術語定義

> 智慧零接觸垃圾分類系統 | 大同大學 I4210 AI實務專題 | 2026

## 垃圾分類術語

| 術語 | 定義 | 備註 |
|------|------|------|
| 寶特瓶 (PET Bottle) | 聚對苯二甲酸乙二酯製成的飲料瓶，class ID 0 | 含牛奶瓶、塑膠杯等 |
| 鐵鋁罐 (Aluminum Can) | 鋁製或鐵製飲料罐、食品罐，class ID 1 | 含鐵鋁罐、氣霧罐 |
| 紙餐盒 (Paper Container) | 紙類包裝、紙杯、紙盒（非淋膜），class ID 2 | 含紙袋、紙板 |
| 塑膠袋 (Plastic Bag) | 塑膠薄膜、購物袋、夾鏈袋，class ID 3 | 含 stretch film |
| 一般垃圾 (General Waste) | 以上四類以外的所有垃圾，class ID 4，預設分類 | 含鋁箔包、陶瓷、家具等 |
| 鋁箔包 (Tetra Pak) | 複合材質飲料盒（紙+鋁箔+塑膠），**歸入一般垃圾** | 提案原為第 5 類，已移除（見 ADR-002） |

## 硬體術語

| 術語 | 定義 |
|------|------|
| Yahboom 套裝 | 第三方 Jetson Orin Nano 相容開發套件，GPIO 針腳編號與 NVIDIA 原版不同 |
| GPIO Pin (Yahboom) | Yahboom 套裝的物理針腳編號，與 Orin Nano DevKit 不同，需查 Yahboom 文件確認 |
| BOARD 模式 | Jetson GPIO 的物理針腳編號模式（Pin 11 = 板上第 11 腳），本專案使用此模式 |
| BCM 模式 | GPIO 晶片內部編號，**不使用** |
| 限流電阻 | 220Ω，串聯 LED 保護 GPIO 腳位（最大額定 40mA，實際 ~12mA/顆） |

## AI/ML 術語

| 術語 | 定義 |
|------|------|
| YOLO26m | Ultralytics YOLO 系列的中型模型（25.9M 參數，~52MB），本專案使用版本 |
| TensorRT FP16 | NVIDIA TensorRT 推論引擎，半精度浮點，比 FP32 快 2-3 倍，mAP 損失 < 1% |
| `.engine` 檔 | TensorRT 編譯後的推論引擎，**依裝置綁定**，不可跨機複製 |
| mAP@50 | 在 IoU 閾值 0.5 下的平均精確度，主要精度指標 |
| 信心閾值 (confidence threshold) | 辨識結果被接受的最低信心分數，低於此值 → 一般垃圾 |
| waste_sorter_v6 | Kaggle 訓練的模型名稱，80 epochs，Tesla T4 GPU |

## 系統架構術語

| 術語 | 定義 |
|------|------|
| Sense→Process→Decide→Act | 課程定義的 Edge AI 閉環架構 |
| InferenceNode | `src/inference_node.py` 的主類別，負責攝影機讀取與 YOLO 推論 |
| ActuatorController | `src/actuator_controller.py` 的主類別，負責 GPIO LED 控制 |
| MqttPublisher | `src/mqtt_publisher.py` 的主類別，負責分類事件發布 |
| DashboardServer | `src/dashboard_server.py` 的主類別，FastAPI + WebSocket |
| MQTT topic | `waste/detection`（分類結果）、`waste/status`（系統狀態） |

## 檔案命名規範

- ADR：`docs/adr/ADR-XXX-slug.md`（3 位數字 + 描述性 slug）
- SPEC：`docs/specs/SPEC-XXX-slug.md`
- 變更記錄：`docs/changes/CHANGE-XXX-slug.md`
- 原始碼：`src/snake_case.py`（一個主類別對應一個檔案）
- 測試：`tests/test_snake_case.py`（與 src 對應）

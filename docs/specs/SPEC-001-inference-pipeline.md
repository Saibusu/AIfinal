# SPEC-001 — 推論管線 (InferenceNode)

| 欄位 | 內容 |
|------|------|
| **Status** | Draft |
| **Date** | 2026-06-11 |
| **ADR 依據** | ADR-001 |
| **對應源碼** | `src/inference_node.py` |

---

## 功能描述 (What)

`InferenceNode` 讀取攝影機即時影像，執行 YOLO26m TensorRT FP16 推論，
輸出分類結果（class ID + confidence）給 `ActuatorController` 與 `MqttPublisher`。

---

## 介面設計 (Interface)

```python
class InferenceNode:
    def __init__(self, model_path: str, camera_id: int = 0,
                 conf_threshold: float = 0.5, imgsz: int = 416) -> None: ...
    def start(self) -> None: ...
    def stop(self) -> None: ...
    def get_latest_result(self) -> dict | None: ...
    # result schema: {"class_id": int, "class_name": str, "confidence": float,
    #                 "bbox": [x1,y1,x2,y2], "timestamp": float}
```

---

## 七欄位 SPEC

| 欄位 | 內容 |
|------|------|
| **Feature** | 即時垃圾分類推論（Sense → Process 階段） |
| **User Story** | 系統持續擷取攝影機畫面，每幀執行 YOLO26m 推論，回傳最高信心分類結果 |
| **Inputs** | CSI/USB 攝影機（OpenCV VideoCapture）；model_path（.engine 或 .onnx）；conf_threshold（預設 0.5） |
| **Outputs** | `detection_result` dict（class_id, class_name, confidence, bbox, timestamp）；若無有效偵測回傳 None |
| **Rules** | 信心分數 < threshold → 回傳 class_id=4（一般垃圾）；同時只處理最高信心偵測；FPS ≥ 15 |
| **Edge Cases** | 攝影機斷線 → 記錄 error + 重試 3 次 + graceful shutdown；無物件 → 回傳 None；多物件 → 取最高信心 |
| **Done When** | 單元測試覆蓋 output schema、conf_threshold 邊界、None 回傳；integration test 在 Jetson 上 FPS ≥ 15 |

---

## 效能需求

| 指標 | 目標 |
|------|------|
| 推論 FPS | ≥ 15 FPS |
| 端到端延遲 | < 200ms（攝影機 → LED 點亮） |
| GPU 使用率 | ≥ 60%（確認使用 TensorRT 加速） |
| 記憶體峰值 | < 4 GB |

---

## 測試計畫

| 測試類型 | 測試項目 |
|---------|---------|
| Unit | `test_output_schema` — 回傳結果包含所有必要欄位 |
| Unit | `test_conf_threshold` — 低於閾值 → class_id=4 |
| Unit | `test_no_detection` — 空畫面 → None |
| Unit | `test_multi_object` — 多目標 → 取最高信心 |
| Integration | `test_fps_on_jetson` — 60 秒連續推論，平均 FPS ≥ 15 |

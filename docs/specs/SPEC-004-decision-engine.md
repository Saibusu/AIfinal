# SPEC-004 — 決策引擎 (DecisionEngine)

| 欄位 | 內容 |
|------|------|
| **Status** | Draft |
| **Date** | 2026-06-11 |
| **ADR 依據** | ADR-002（5 類別、低信心防呆）|
| **對應源碼** | `src/decision_engine.py` |

---

## 功能描述 (What)

`DecisionEngine` 是系統「Decide」階段的純邏輯核心：接收推論結果（class_id + confidence），
套用信心閾值與防呆規則，輸出最終要驅動的致動器指令（class_id + LED 顏色）。

**不依賴攝影機、模型、GPIO** → 可完全單元測試，是 InferenceNode 與 ActuatorController 的共用依賴。

---

## 介面設計 (Interface)

```python
class DecisionEngine:
    def __init__(self, conf_threshold: float = 0.5) -> None: ...
    def decide(self, class_id: int | None, confidence: float) -> Decision: ...
    # Decision: dataclass(class_id: int, class_name: str, led_color: str, is_fallback: bool)
```

---

## 類別 / LED 對應（依 ADR-002）

| class_id | class_name | led_color |
|---------|-----------|-----------|
| 0 | 寶特瓶 | green |
| 1 | 鐵鋁罐 | yellow |
| 2 | 紙餐盒 | blue |
| 3 | 塑膠袋 | white |
| 4 | 一般垃圾 | red |

---

## 七欄位 SPEC

| 欄位 | 內容 |
|------|------|
| **Feature** | 分類決策邏輯（Decide 階段）|
| **User Story** | 系統取得推論結果後，由 DecisionEngine 決定最終分類與對應 LED；信心不足時安全退回一般垃圾 |
| **Inputs** | `class_id: int \| None`（0–4 或 None 代表無偵測）；`confidence: float`（0.0–1.0）；`conf_threshold`（建構時設定，預設 0.5）|
| **Outputs** | `Decision` dataclass：`class_id`, `class_name`, `led_color`, `is_fallback`（是否觸發防呆）|
| **Rules** | (1) confidence < threshold → class_id=4, is_fallback=True；(2) class_id is None → class_id=4, is_fallback=True；(3) 有效且達標 → 原樣回傳, is_fallback=False；(4) led_color 依對應表 |
| **Edge Cases** | class_id 超出 0–4（如 5、-1）→ 視為無效 → class_id=4 防呆；confidence 超出 0.0–1.0 → ValueError；threshold 超出 0.0–1.0 → 建構時 ValueError |
| **Done When** | 單元測試覆蓋全部 5 類別正常路徑 + 低信心防呆 + None + 無效 class_id + 邊界 confidence；`src/decision_engine.py` 覆蓋率 = 100%；ruff 零違規 |

---

## 測試計畫（TDD）

| 測試 | 預期 |
|------|------|
| `test_valid_classes_pass_through` | class 0–4 + 高信心 → 原樣回傳，is_fallback=False |
| `test_led_color_mapping` | 每個 class_id 對應正確 led_color |
| `test_low_confidence_fallback` | confidence < threshold → class 4, is_fallback=True |
| `test_none_class_fallback` | class_id=None → class 4, is_fallback=True |
| `test_invalid_class_id_fallback` | class_id=5 或 -1 → class 4, is_fallback=True |
| `test_confidence_out_of_range_raises` | confidence=1.5 或 -0.1 → ValueError |
| `test_invalid_threshold_raises` | 建構 conf_threshold=1.5 → ValueError |
| `test_boundary_confidence` | confidence == threshold → 視為達標（>=）|

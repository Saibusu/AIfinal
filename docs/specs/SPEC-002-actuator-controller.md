# SPEC-002 — GPIO 致動器控制器 (ActuatorController)

| 欄位 | 內容 |
|------|------|
| **Status** | Draft |
| **Date** | 2026-06-11 |
| **ADR 依據** | ADR-002（Yahboom GPIO 針腳）|
| **對應源碼** | `src/actuator_controller.py` |

---

## 功能描述 (What)

`ActuatorController` 接收分類結果，透過 GPIO 點亮對應 LED（5 秒後自動熄滅），
實現系統的 Act 階段。針腳設定依 Yahboom 套裝文件。

---

## GPIO 針腳對應（Yahboom, BOARD 模式）

```python
GPIO_PINS: dict[int, int] = {
    0: 11,  # 寶特瓶 → 綠 LED
    1: 13,  # 鐵鋁罐 → 黃 LED
    2: 15,  # 紙餐盒 → 藍 LED
    3: 21,  # 塑膠袋 → 白 LED
    4: 23,  # 一般垃圾 → 紅 LED
}
LED_ON_DURATION: float = 5.0  # 秒
```

> 針腳可透過環境變數 `GPIO_PIN_<CLASS_ID>` 覆蓋（方便測試與 Yahboom 調整）

---

## 介面設計 (Interface)

```python
class ActuatorController:
    def __init__(self, gpio_pins: dict[int, int] | None = None,
                 led_duration: float = 5.0) -> None: ...
    def trigger(self, class_id: int) -> None: ...
    def all_off(self) -> None: ...
    def cleanup(self) -> None: ...
```

---

## 七欄位 SPEC

| 欄位 | 內容 |
|------|------|
| **Feature** | GPIO LED 控制（Act 階段） |
| **User Story** | 系統收到分類結果後，點亮對應顏色 LED，5 秒後自動熄滅 |
| **Inputs** | `class_id: int`（0-4）；GPIO 針腳對應表；LED_ON_DURATION |
| **Outputs** | GPIO 數位高電位（LED 亮）→ 5 秒後低電位（LED 滅）；同時只亮一組 LED |
| **Rules** | 互斥邏輯：trigger 前先 all_off；duration 到時自動熄滅；不在 CI 環境中做實際 GPIO 操作 |
| **Edge Cases** | 無效 class_id → 預設 class_id=4（一般垃圾）；GPIO 初始化失敗 → log + graceful degradation；cleanup() 必須在程式結束時呼叫 |
| **Done When** | 單元測試（Mock GPIO）覆蓋 trigger、all_off、互斥邏輯；integration test 確認 LED 實際點亮 |

---

## 測試計畫

| 測試類型 | 測試項目 |
|---------|---------|
| Unit | `test_trigger_calls_gpio` — trigger(2) → GPIO.output(15, HIGH) |
| Unit | `test_mutual_exclusion` — trigger(1) 前會先 all_off |
| Unit | `test_invalid_class_id` — trigger(-1) → 預設 class_id=4 |
| Unit | `test_led_auto_off` — duration 後自動呼叫 all_off |
| Unit | `test_cleanup` — cleanup() 呼叫 GPIO.cleanup() |
| Integration | `test_led_lights_on_jetson` — 實際 LED 點亮確認 |

---

## 限制電流設計

- **5 顆 LED 全部使用 220Ω 限流電阻**（實際接線確認）
- 每顆工作電流：綠/黃/紅 ~6mA（Vf≈2.0V）、藍/白 ~1.4mA（Vf≈3.0V，較暗但可見）
- GPIO 腳位最大額定：40mA；5 顆同時亮總電流 < 30mA → 安全

> 注意：此為軟體 SPEC，電阻為硬體接線參數。實機已採統一 220Ω。

# SPEC-005 — MQTT 發布器 (MqttPublisher)

| 欄位 | 內容 |
|------|------|
| **Status** | Draft |
| **Date** | 2026-06-11 |
| **ADR 依據** | —（CAPSTONE §B.5 要求 MQTT 訊息測試；提案原列 MQTT 為選用，此處正式納入）|
| **對應源碼** | `src/mqtt_publisher.py` |

---

## 功能描述 (What)

`MqttPublisher` 將分類事件與系統狀態發布到 MQTT broker，供 Dashboard 與
（未來）多桶聯網監控訂閱。封裝 paho-mqtt，提供重試與 JSON schema 驗證。

---

## MQTT Topic

| Topic | payload |
|-------|---------|
| `waste/detection` | `{class_id, class_name, confidence, is_fallback, timestamp}` |
| `waste/status` | `{fps, uptime, ...}`（自由欄位）|

---

## 介面設計

```python
class MqttPublisher:
    def __init__(self, broker="localhost", port=1883, topic_prefix="waste",
                 client=None, max_retries=3) -> None: ...
    def connect(self) -> None: ...
    def publish_detection(self, result: dict) -> bool: ...
    def publish_status(self, status: dict) -> bool: ...
    def disconnect(self) -> None: ...
```

---

## 七欄位 SPEC

| 欄位 | 內容 |
|------|------|
| **Feature** | MQTT 事件發布（連接 Act 階段與監控）|
| **User Story** | 系統每次分類後發布 detection 事件到 `waste/detection`，狀態到 `waste/status`，供 Dashboard 即時訂閱 |
| **Inputs** | broker host/port；topic_prefix；detection result dict（來自 InferenceNode）；status dict |
| **Outputs** | publish 到對應 topic（JSON, QoS 1）；回傳 bool 表示是否成功送出 |
| **Rules** | detection payload 必含 class_id/class_name/confidence/timestamp；publish 失敗重試至 max_retries；rc==0 視為成功 |
| **Edge Cases** | 缺必要欄位 → ValueError；broker 未連線 → 重試後回傳 False（不 crash）；client 注入用於測試（不連真 broker）|
| **Done When** | 單元測試（mock client）覆蓋：publish 成功/失敗重試、JSON schema、缺欄位、topic 正確、status 發布；覆蓋率 ≥90% |

---

## 測試計畫（TDD）

| 測試 | 預期 |
|------|------|
| `test_publish_detection_success` | rc=0 → True，publish 到 `waste/detection` |
| `test_publish_detection_payload_schema` | payload JSON 含必要欄位 |
| `test_publish_detection_missing_field_raises` | 缺 class_id → ValueError |
| `test_publish_retries_on_failure` | rc≠0 → 重試 max_retries 次 → False |
| `test_publish_status` | 發布到 `waste/status` |
| `test_topic_prefix_applied` | 自訂 prefix → topic 正確 |
| `test_disconnect` | 呼叫 client.loop_stop + disconnect |

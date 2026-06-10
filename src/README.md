# src/ — 原始碼

所有 Python 原始碼。**一個檔案一個主類別**（類別名稱對應檔名）。

| 計畫檔案 | 主類別 | 對應 SPEC |
|---------|--------|-----------|
| `inference_node.py` | `InferenceNode` | SPEC-001 |
| `actuator_controller.py` | `ActuatorController` | SPEC-002 |
| `dashboard_server.py` | `DashboardServer` | SPEC-003 |
| `mqtt_publisher.py` | `MqttPublisher` | （待定 SPEC）|

規範：型別註解 + docstring（public 方法）；module-level function 僅限真正的工具函式；
每個 `.py` 需 Copyright header（見 [../CLAUDE.md](../CLAUDE.md)）。

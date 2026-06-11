# src/ — 原始碼

所有 Python 原始碼。**一個檔案一個主類別**（類別名稱對應檔名）。

| 檔案 | 主類別 | 對應 SPEC |
|------|--------|-----------|
| `inference_node.py` | `InferenceNode` | SPEC-001 |
| `actuator_controller.py` | `ActuatorController` | SPEC-002 |
| `dashboard_server.py` | `DashboardServer` | SPEC-003 |
| `decision_engine.py` | `DecisionEngine` | SPEC-004 |
| `mqtt_publisher.py` | `MqttPublisher` | SPEC-005 |
| `tegrastats_parser.py` | `TegrastatsParser` | SPEC-006 |
| `pipeline_orchestrator.py` | `PipelineOrchestrator` | SPEC-007 |
| `app.py` | — | 進入點 glue（SPEC-007） |

規範：型別註解 + docstring（public 方法）；每個 `.py` 需 Copyright header（見 [../CLAUDE.md](../CLAUDE.md)）。

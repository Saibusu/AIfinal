# SPEC-003 — Dashboard 伺服器 (DashboardServer)

| 欄位 | 內容 |
|------|------|
| **Status** | Draft |
| **Date** | 2026-06-11 |
| **ADR 依據** | — |
| **對應源碼** | `src/dashboard_server.py` |

---

## 功能描述 (What)

`DashboardServer` 提供 FastAPI + WebSocket 即時 Dashboard，
顯示 MJPEG 影像流、偵測事件、FPS 及系統狀態。

---

## 介面設計

```
GET  /            → HTML dashboard 頁面
GET  /video_feed  → MJPEG 影像流（OpenCV → JPEG frames）
WS   /ws          → WebSocket：推播 detection events + FPS + status
GET  /health      → {"status": "ok", "fps": float, "uptime": float}
```

---

## 七欄位 SPEC

| 欄位 | 內容 |
|------|------|
| **Feature** | 即時監控 Dashboard（FastAPI + MJPEG + WebSocket） |
| **User Story** | 使用者在電腦瀏覽器開啟 `http://<jetson-ip>:8000`，可即時看到攝影機畫面、偵測結果、FPS 計數器 |
| **Inputs** | InferenceNode 的偵測結果（queue）；攝影機 JPEG 幀 |
| **Outputs** | MJPEG stream（/video_feed）；WebSocket JSON events（class_name, confidence, timestamp）；/health JSON |
| **Rules** | WebSocket broadcast 給所有連線的客戶端；/video_feed 目標 ≥ 10 FPS；/health 回傳 200 表示系統正常 |
| **Edge Cases** | 攝影機離線 → /video_feed 回傳 503；WebSocket 客戶端斷線 → 靜默移除；無偵測時 dashboard 仍顯示攝影機畫面 |
| **Done When** | 單元測試覆蓋 /health endpoint、WebSocket event 格式；integration test 在 Jetson 上確認 MJPEG stream 可存取 |

---

## WebSocket Event 格式

```json
{
  "type": "detection",
  "class_id": 0,
  "class_name": "寶特瓶",
  "confidence": 0.87,
  "timestamp": 1749600000.0
}
```

```json
{
  "type": "fps",
  "value": 18.5
}
```

---

## 測試計畫

| 測試類型 | 測試項目 |
|---------|---------|
| Unit | `test_health_endpoint` — GET /health 回傳 200 + 正確 schema |
| Unit | `test_ws_event_format` — WebSocket event 包含必要欄位 |
| Unit | `test_ws_broadcast` — 多客戶端同時收到 event |
| Integration | `test_mjpeg_stream_accessible` — 在 Jetson 上 curl /video_feed 回傳 200 |

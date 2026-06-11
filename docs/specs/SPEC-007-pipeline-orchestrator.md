# SPEC-007 — 管線協調器 (PipelineOrchestrator)

| 欄位 | 內容 |
|------|------|
| **Status** | Draft |
| **Date** | 2026-06-11 |
| **ADR 依據** | ADR-001/002/003（整合 Sense→Process→Decide→Act 為單一可執行 app）|
| **對應源碼** | `src/pipeline_orchestrator.py`、`src/app.py`（進入點 glue）|

---

## 功能描述 (What)

`PipelineOrchestrator` 把五個模組串成完整迴路：每張影像 →
`InferenceNode.infer_frame()`（Sense+Process+Decide）→ `ActuatorController.trigger()`
（Act / GPIO LED）→ `MqttPublisher.publish_detection()`（事件外發）→ `on_event`
回呼（推給 Dashboard 廣播）。同時維護**即時 FPS** 與**最新 JPEG 幀**供 Dashboard
`/video_feed` 與 `/ws` 呈現。

> **執行架構（單一進程）**：`src/app.py` 用 uvicorn 主執行緒服務 `DashboardServer`，
> 另開**背景 thread** 跑本協調器的 `run()` 迴圈（阻塞型推論不卡 async loop）。
> 相機讀取、JPEG 編碼、跨執行緒 broadcast 屬硬體/事件迴圈 glue，置於 `app.py`
> 並標 `pragma: no cover`，於 Yahboom 實機驗證；協調器本身相依全注入、純邏輯可測。

---

## 介面設計

```python
class PipelineOrchestrator:
    def __init__(self, inference_node, actuator, publisher=None,
                 on_event=None, clock=time.monotonic, fps_window=30) -> None: ...
    def process_frame(self, frame, jpeg=None) -> dict | None: ...
    def run(self, frame_reader, jpeg_encoder=None, max_frames=None) -> int: ...
    @property
    def fps(self) -> float: ...
    @property
    def latest_result(self) -> dict | None: ...
    def get_frame(self) -> bytes | None: ...   # 供 Dashboard frame_source
    def get_fps(self) -> float: ...            # 供 Dashboard fps_source
```

`process_frame` 流程：
1. `result = inference_node.infer_frame(frame)`（None = 無偵測）
2. 更新 FPS（rolling window）；若有 `jpeg` 存為最新幀
3. 若 `result` 非 None：依序 `actuator.trigger` → `publisher.publish_detection`
   → `on_event(result)`，**各 sink 以 try 包覆**：單一 sink 失敗不影響其他、不終止迴圈
4. 回傳 `result`

---

## 七欄位 SPEC

| 欄位 | 內容 |
|------|------|
| **Feature** | 將五模組整合為單一可執行迴路，並輸出即時畫面/FPS/事件給 Dashboard |
| **User Story** | 在 Yahboom 啟動容器後，攝影機畫面與偵測事件即時顯示於 `http://<ip>:8000`，對應 LED 同步點亮，MQTT 同步發布 |
| **Inputs** | 注入的 InferenceNode / ActuatorController / MqttPublisher(選用) / on_event 回呼(選用)；frame_reader；可選 jpeg_encoder |
| **Outputs** | 每幀回傳 result dict 或 None；副作用：LED 點燈、MQTT 發布、Dashboard 廣播；維護 fps 與 latest_jpeg |
| **Rules** | 無偵測(None)→不觸發 act/publish/event；有偵測→三個 sink 依序執行且各自容錯；FPS 以最近 N 幀時間窗計算 |
| **Edge Cases** | publisher=None → 略過發布不報錯；任一 sink 擲例外 → 捕捉後續處理續行；無 jpeg → get_frame 回 None；clock 無前進 → fps=0.0 |
| **Done When** | 單元測試（mock 五模組）覆蓋：有/無偵測分支、三 sink 呼叫與容錯、FPS 計算、get_frame/get_fps、run() 迴圈以 max_frames/None-frame 終止；模組覆蓋率 ≥90% |

---

## 測試計畫（TDD）

| 測試 | 預期 |
|------|------|
| `test_process_frame_runs_full_loop` | 有偵測 → actuator.trigger + publisher + on_event 皆被呼叫，回傳 result |
| `test_process_frame_no_detection_skips_sinks` | infer 回 None → 三 sink 都不呼叫 |
| `test_process_frame_without_publisher_ok` | publisher=None → 不報錯，其他 sink 照常 |
| `test_actuator_failure_does_not_stop_publish` | actuator 擲例外 → publisher/on_event 仍被呼叫 |
| `test_publisher_failure_swallowed` | publisher 擲例外 → process_frame 仍回傳 result |
| `test_get_frame_returns_latest_jpeg` | 傳入 jpeg → get_frame 回該 bytes |
| `test_latest_result_tracked` | latest_result 反映最後一次有效偵測 |
| `test_fps_computed_with_clock` | 注入遞增 clock，多幀後 fps>0 且數值合理 |
| `test_fps_zero_when_clock_static` | clock 不前進 → fps=0.0 |
| `test_run_stops_on_none_frame` | frame_reader 回 None → 迴圈結束，回傳處理幀數 |
| `test_run_respects_max_frames` | max_frames=N → 恰處理 N 幀 |
| `test_run_uses_jpeg_encoder` | 提供 encoder → get_frame 回編碼結果 |

#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞 / Datung University — I4210 AI實務專題
"""智慧零接觸垃圾分類系統 — 單檔 Demo（Yahboom Jetson Orin Nano）

用法：
    python3 main.py                          # CSI 相機 + 預設 model
    MODEL_PATH=xxx.engine python3 main.py    # 指定 engine
    CAMERA_SOURCE="..." python3 main.py      # 覆蓋相機來源
    MQTT_BROKER=192.168.1.x python3 main.py  # 啟用 MQTT
    瀏覽器開 http://<jetson-ip>:8000
"""
from __future__ import annotations
import asyncio, json, os, re, threading, time
from collections import deque
from collections.abc import Callable
from dataclasses import dataclass
from typing import Any

# ── Constants ────────────────────────────────────────────────────────────────
GENERAL_WASTE = 4
CLASS_TABLE: dict[int, tuple[str, str]] = {
    0: ("寶特瓶", "green"), 1: ("鐵鋁罐", "yellow"),
    2: ("紙餐盒", "blue"),  3: ("塑膠袋", "white"), 4: ("一般垃圾", "red"),
}
DEFAULT_PINS: dict[int, int] = {0: 11, 1: 13, 2: 15, 3: 21, 4: 23}

# ── Decision ──────────────────────────────────────────────────────────────────
@dataclass(frozen=True)
class Decision:
    class_id: int; class_name: str; led_color: str; is_fallback: bool

class DecisionEngine:
    def __init__(self, conf_threshold: float = 0.5) -> None:
        if not 0.0 <= conf_threshold <= 1.0:
            raise ValueError(f"conf_threshold {conf_threshold} not in [0,1]")
        self._thr = conf_threshold

    def decide(self, class_id: int | None, confidence: float) -> Decision:
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"confidence {confidence} not in [0,1]")
        fallback = class_id is None or class_id not in CLASS_TABLE or confidence < self._thr
        cid = GENERAL_WASTE if fallback else class_id
        name, color = CLASS_TABLE[cid]
        return Decision(cid, name, color, fallback)

# ── Actuator ──────────────────────────────────────────────────────────────────
class ActuatorController:
    def __init__(self, gpio_pins: dict[int, int] | None = None,
                 led_duration: float = 5.0, gpio: Any = None,
                 timer_factory: Callable | None = None) -> None:
        self.pins = gpio_pins or {
            cid: int(os.environ.get(f"GPIO_PIN_{cid}", p))
            for cid, p in DEFAULT_PINS.items()
        }
        self.led_duration = led_duration
        self._gpio = gpio or self._load_gpio()
        self._timer_factory = timer_factory or threading.Timer
        self._timer: Any = None
        self._gpio.setmode(self._gpio.BOARD)
        for pin in self.pins.values():
            self._gpio.setup(pin, self._gpio.OUT)

    @staticmethod
    def _load_gpio() -> Any:
        import Jetson.GPIO as GPIO; return GPIO  # noqa: E702

    def trigger(self, class_id: int) -> None:
        if class_id not in self.pins:
            class_id = GENERAL_WASTE
        self.all_off()
        self._gpio.output(self.pins[class_id], self._gpio.HIGH)
        self._timer = self._timer_factory(self.led_duration, self.all_off)
        self._timer.daemon = True; self._timer.start()

    def all_off(self) -> None:
        for pin in self.pins.values():
            self._gpio.output(pin, self._gpio.LOW)

    def cleanup(self) -> None:
        if self._timer: self._timer.cancel()
        self._gpio.cleanup()

# ── Inference ─────────────────────────────────────────────────────────────────
class InferenceNode:
    def __init__(self, model_path: str, camera_source: str | None = None,
                 conf_threshold: float = 0.5, imgsz: int = 416,
                 model: Any = None, decision_engine: DecisionEngine | None = None) -> None:
        self.model_path = model_path
        self.imgsz = imgsz
        self.camera_source = camera_source or os.environ.get("CAMERA_SOURCE") or self.csi_pipeline()
        self._model = model
        self._engine = decision_engine or DecisionEngine(conf_threshold)
        self._latest: dict | None = None

    @staticmethod
    def csi_pipeline(sensor_id: int = 0, w: int = 1280, h: int = 720, fps: int = 30) -> str:
        return (
            f"nvarguscamerasrc sensor-id={sensor_id} ! "
            f"video/x-raw(memory:NVMM),width={w},height={h},framerate={fps}/1 ! "
            f"nvvidconv ! video/x-raw,format=BGRx ! videoconvert ! "
            f"video/x-raw,format=BGR ! appsink drop=true max-buffers=1"
        )

    def load(self) -> None:
        if self._model is None:
            from ultralytics import YOLO
            self._model = YOLO(self.model_path)

    def infer_frame(self, frame: Any) -> dict | None:
        if self._model is None:
            raise RuntimeError("model not loaded — call load() first")
        results = self._model(frame, imgsz=self.imgsz, verbose=False)
        boxes = results[0].boxes if results else None
        if boxes is None or len(boxes) == 0:
            return None
        best = max(zip(boxes.cls.tolist(), boxes.conf.tolist(), boxes.xyxy.tolist()), key=lambda d: d[1])
        class_id, confidence, bbox = int(best[0]), float(best[1]), [float(v) for v in best[2]]
        d = self._engine.decide(class_id, confidence)
        self._latest = {
            "class_id": d.class_id, "class_name": d.class_name, "led_color": d.led_color,
            "confidence": confidence, "bbox": bbox, "is_fallback": d.is_fallback,
            "timestamp": time.time(),
        }
        return self._latest

    def get_latest_result(self) -> dict | None:
        return self._latest

# ── MQTT ──────────────────────────────────────────────────────────────────────
class MqttPublisher:
    def __init__(self, broker: str = "localhost", port: int = 1883,
                 topic_prefix: str = "waste", client: Any = None,
                 max_retries: int = 3) -> None:
        self.broker, self.port = broker, port
        self.topic_prefix = topic_prefix
        self.max_retries = max_retries
        self._client = client or self._build_client()

    @staticmethod
    def _build_client() -> Any:
        import paho.mqtt.client as mqtt; return mqtt.Client()  # noqa: E702

    def connect(self) -> None:
        self._client.connect(self.broker, self.port); self._client.loop_start()

    def publish_detection(self, result: dict) -> bool:
        missing = [f for f in ("class_id", "class_name", "confidence", "timestamp") if f not in result]
        if missing: raise ValueError(f"missing fields: {missing}")
        return self._publish("detection", {
            "class_id": result["class_id"], "class_name": result["class_name"],
            "confidence": result["confidence"], "is_fallback": result.get("is_fallback", False),
            "timestamp": result["timestamp"],
        })

    def publish_status(self, status: dict) -> bool:
        return self._publish("status", status)

    def _publish(self, suffix: str, payload: dict) -> bool:
        msg = json.dumps(payload, ensure_ascii=False)
        for _ in range(self.max_retries):
            info = self._client.publish(f"{self.topic_prefix}/{suffix}", msg, qos=1)
            if getattr(info, "rc", 1) == 0: return True
        return False

    def disconnect(self) -> None:
        self._client.loop_stop(); self._client.disconnect()

# ── Dashboard ─────────────────────────────────────────────────────────────────
_HTML = """<!DOCTYPE html><html lang="zh-TW"><head><meta charset="utf-8">
<title>智慧垃圾分類 — 即時監控</title></head><body>
<h1>智慧零接觸垃圾分類系統</h1>
<img src="/video_feed" alt="camera" width="640"><pre id="ev"></pre>
<script>
const ws=new WebSocket(`ws://${location.host}/ws`);
ws.onmessage=e=>{const el=document.getElementById("ev");el.textContent=e.data+"\\n"+el.textContent};
</script></body></html>"""

class DashboardServer:
    def __init__(self, frame_source: Callable | None = None,
                 fps_source: Callable | None = None) -> None:
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

        self._frame = frame_source or (lambda: None)
        self._fps   = fps_source   or (lambda: 0.0)
        self._t0    = time.monotonic()
        self._clients: list[Any] = []
        app = FastAPI(title="Waste Sorter")

        @app.get("/", response_class=HTMLResponse)
        async def index() -> str: return _HTML

        @app.get("/health")
        async def health():
            return JSONResponse({"status": "ok", "fps": self._fps(),
                                 "uptime": time.monotonic() - self._t0})

        @app.get("/video_feed")
        async def video_feed():
            first = self._frame()
            if first is None:
                return JSONResponse({"error": "camera offline"}, status_code=503)
            def _stream():
                frame = first
                while frame is not None:
                    yield b"--frame\r\nContent-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                    frame = self._frame()
            return StreamingResponse(_stream(), media_type="multipart/x-mixed-replace; boundary=frame")

        @app.websocket("/ws")
        async def wsep(websocket: WebSocket) -> None:
            await websocket.accept()
            self._clients.append(websocket)
            await websocket.send_text(json.dumps({"type": "fps", "value": self._fps()}))
            try:
                while True: await websocket.receive_text()
            except WebSocketDisconnect:
                if websocket in self._clients: self._clients.remove(websocket)

        self.app = app

    async def broadcast_detection(self, result: dict) -> None:
        msg = json.dumps({"type": "detection", "class_id": result["class_id"],
                          "class_name": result["class_name"], "confidence": result["confidence"],
                          "timestamp": result["timestamp"]}, ensure_ascii=False)
        dead = []
        for ws in list(self._clients):
            try: await ws.send_text(msg)
            except Exception: dead.append(ws)
        for ws in dead:
            if ws in self._clients: self._clients.remove(ws)

# ── Orchestrator ──────────────────────────────────────────────────────────────
class PipelineOrchestrator:
    def __init__(self, inference_node: Any, actuator: Any,
                 publisher: Any = None, on_event: Callable | None = None,
                 clock: Callable = time.monotonic, fps_window: int = 30) -> None:
        self._node, self._actuator = inference_node, actuator
        self._publisher, self._on_event = publisher, on_event
        self._clock = clock
        self._stamps: deque[float] = deque(maxlen=fps_window)
        self._jpeg: bytes | None = None

    def process_frame(self, frame: Any, jpeg: bytes | None = None) -> dict | None:
        result = self._node.infer_frame(frame)
        self._stamps.append(self._clock())
        if jpeg is not None: self._jpeg = jpeg
        if result is None: return None
        self._safe(self._actuator.trigger, result["class_id"])
        if self._publisher: self._safe(self._publisher.publish_detection, result)
        if self._on_event:  self._safe(self._on_event, result)
        return result

    def run(self, reader: Callable, encoder: Callable | None = None,
            max_frames: int | None = None) -> int:
        count = 0
        while max_frames is None or count < max_frames:
            frame = reader()
            if frame is None: break
            self.process_frame(frame, encoder(frame) if encoder else None)
            count += 1
        return count

    @staticmethod
    def _safe(fn: Callable, *args: Any) -> None:
        try: fn(*args)
        except Exception: pass

    def get_fps(self) -> float:
        if len(self._stamps) < 2: return 0.0
        span = self._stamps[-1] - self._stamps[0]
        return round((len(self._stamps) - 1) / span, 2) if span > 0 else 0.0

    def get_frame(self) -> bytes | None: return self._jpeg

# ── TegrastatsParser ──────────────────────────────────────────────────────────
class TegrastatsParser:
    _RAM  = re.compile(r"RAM (\d+)/(\d+)MB")
    _CPU  = re.compile(r"CPU \[([^\]]+)\]")
    _CORE = re.compile(r"(\d+)%@")
    _GPU  = re.compile(r"GR3D_FREQ (\d+)%")
    _PWR  = re.compile(r"(?:POM_5V_IN|VDD_IN) (\d+)/\d+")
    _TS   = re.compile(r"^(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})")

    def parse_line(self, line: str) -> dict | None:
        ram, cpu = self._RAM.search(line), self._CPU.search(line)
        if not ram or not cpu: return None
        cores = [int(p) for p in self._CORE.findall(cpu.group(1))]
        gpu, pwr, ts = self._GPU.search(line), self._PWR.search(line), self._TS.search(line)
        return {
            "timestamp": ts.group(1) if ts else None,
            "cpu_pct": round(sum(cores) / len(cores), 2) if cores else 0.0,
            "gpu_pct": int(gpu.group(1)) if gpu else None,
            "power_mw": int(pwr.group(1)) if pwr else None,
            "ram_used_mb": int(ram.group(1)), "ram_total_mb": int(ram.group(2)),
        }

    def parse_text(self, text: str) -> list[dict]:
        return [r for r in (self.parse_line(l) for l in text.splitlines()) if r]

    def to_csv(self, rows: list[dict]) -> str:
        lines = ["index,timestamp,cpu_pct,gpu_pct,power_mw,ram_used_mb,ram_total_mb"]
        for i, r in enumerate(rows):
            lines.append(f"{i},{r['timestamp'] or ''},{r['cpu_pct']},"
                         f"{r['gpu_pct'] or ''},{r['power_mw'] or ''},"
                         f"{r['ram_used_mb']},{r['ram_total_mb']}")
        return "\n".join(lines) + "\n"

    def summary(self, rows: list[dict]) -> dict:
        if not rows:
            return {"samples": 0, "cpu_avg": 0.0, "cpu_max": 0.0,
                    "gpu_avg": 0.0, "gpu_max": 0, "power_avg_mw": 0.0, "power_max_mw": 0}
        cpu = [r["cpu_pct"] for r in rows]
        gpu = [r["gpu_pct"] for r in rows if r["gpu_pct"] is not None]
        pwr = [r["power_mw"] for r in rows if r["power_mw"] is not None]
        return {
            "samples": len(rows),
            "cpu_avg": round(sum(cpu) / len(cpu), 2), "cpu_max": max(cpu),
            "gpu_avg": round(sum(gpu) / len(gpu), 2) if gpu else 0.0,
            "gpu_max": max(gpu) if gpu else 0,
            "power_avg_mw": round(sum(pwr) / len(pwr), 2) if pwr else 0.0,
            "power_max_mw": max(pwr) if pwr else 0,
        }

# ── Entrypoint ────────────────────────────────────────────────────────────────
def build() -> tuple[DashboardServer, PipelineOrchestrator, threading.Event]:
    node     = InferenceNode(os.environ.get("MODEL_PATH", "models/best_v6.engine"))
    actuator = ActuatorController()
    publisher: MqttPublisher | None = None
    if broker := os.environ.get("MQTT_BROKER"):
        publisher = MqttPublisher(broker=broker)
        publisher.connect()

    server = DashboardServer()
    stop   = threading.Event()
    state: dict[str, Any] = {"loop": None}

    def on_event(result: dict) -> None:
        if loop := state["loop"]:
            loop.call_soon_threadsafe(
                lambda: asyncio.create_task(server.broadcast_detection(result))
            )

    orch = PipelineOrchestrator(node, actuator, publisher=publisher, on_event=on_event)
    server._frame = orch.get_frame
    server._fps   = orch.get_fps

    def _pipeline() -> None:
        node.load()
        import cv2
        cam = cv2.VideoCapture(node.camera_source, cv2.CAP_GSTREAMER)

        def reader():
            if stop.is_set(): return None
            ok, frame = cam.read()
            return frame if ok else None

        def encode(frame: Any) -> bytes | None:
            ok, buf = cv2.imencode(".jpg", frame)
            return buf.tobytes() if ok else None

        orch.run(reader, encode)
        cam.release()

    thread = threading.Thread(target=_pipeline, name="pipeline", daemon=True)

    async def startup() -> None:
        state["loop"] = asyncio.get_running_loop()
        thread.start()

    async def shutdown() -> None:
        stop.set()
        actuator.cleanup()
        if publisher: publisher.disconnect()

    server.app.add_event_handler("startup", startup)
    server.app.add_event_handler("shutdown", shutdown)
    return server, orch, stop


def main() -> None:
    import uvicorn
    server, _, _ = build()
    uvicorn.run(
        server.app,
        host=os.environ.get("DASHBOARD_HOST", "0.0.0.0"),  # nosec B104
        port=int(os.environ.get("DASHBOARD_PORT", "8000")),
    )


if __name__ == "__main__":
    main()

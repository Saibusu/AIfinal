#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Runtime entrypoint: single-process orchestrator + Dashboard (SPEC-007).

Wiring/glue only — verified on Yahboom, excluded from coverage (see pyproject
`[tool.coverage.run] omit`). The testable logic lives in PipelineOrchestrator
and DashboardServer.

Architecture:
    * uvicorn serves DashboardServer on the main thread (live MJPEG + WebSocket
      events + /health) — this is the "畫面 + 數據" surface.
    * a background thread runs PipelineOrchestrator.run(), owning the CSI
      camera and driving Sense→Process→Decide→Act + MQTT.
    * detections are pushed to the dashboard via on_event, hopping back onto the
      uvicorn event loop with loop.call_soon_threadsafe.

Env:
    MODEL_PATH    TensorRT engine / weights (default models/best_v6.engine)
    CAMERA_SOURCE override camera source (else CSI GStreamer pipeline)
    MQTT_BROKER   enable MQTT publishing when set
    DASHBOARD_HOST / DASHBOARD_PORT  bind address (default 0.0.0.0:8000)
"""
from __future__ import annotations

import asyncio
import os
import threading
from typing import Any

from src.actuator_controller import ActuatorController
from src.dashboard_server import DashboardServer
from src.inference_node import InferenceNode
from src.mqtt_publisher import MqttPublisher
from src.pipeline_orchestrator import PipelineOrchestrator


def _build_camera(source: str) -> Any:
    import cv2

    return cv2.VideoCapture(source, cv2.CAP_GSTREAMER)


def _encode_jpeg(frame: Any) -> bytes | None:
    import cv2

    ok, buf = cv2.imencode(".jpg", frame)
    return buf.tobytes() if ok else None


def build() -> tuple[DashboardServer, PipelineOrchestrator, threading.Event]:
    """Construct and wire all modules; return (server, orchestrator, stop_event)."""
    node = InferenceNode(model_path=os.environ.get("MODEL_PATH", "models/best_v6.engine"))
    actuator = ActuatorController()

    publisher = None
    broker = os.environ.get("MQTT_BROKER")
    if broker:
        publisher = MqttPublisher(broker=broker)
        publisher.connect()

    state: dict[str, Any] = {"loop": None, "server": None}

    def on_event(result: dict) -> None:
        loop = state["loop"]
        server = state["server"]
        if loop is None or server is None:
            return
        loop.call_soon_threadsafe(
            lambda: asyncio.create_task(server.broadcast_detection(result))
        )

    orchestrator = PipelineOrchestrator(node, actuator, publisher=publisher, on_event=on_event)
    server = DashboardServer(frame_source=orchestrator.get_frame, fps_source=orchestrator.get_fps)
    state["server"] = server

    stop_event = threading.Event()

    def _pipeline_loop() -> None:
        node.load()  # load model only; orchestrator drives frame reading
        camera = _build_camera(node.camera_source)

        def reader() -> Any:
            if stop_event.is_set():
                return None
            ok, frame = camera.read()
            return frame if ok else None

        orchestrator.run(reader, jpeg_encoder=_encode_jpeg)
        camera.release()

    thread = threading.Thread(target=_pipeline_loop, name="pipeline", daemon=True)

    async def _on_startup() -> None:
        state["loop"] = asyncio.get_running_loop()
        thread.start()

    async def _on_shutdown() -> None:
        stop_event.set()
        actuator.cleanup()
        if publisher is not None:
            publisher.disconnect()

    server.app.add_event_handler("startup", _on_startup)
    server.app.add_event_handler("shutdown", _on_shutdown)
    return server, orchestrator, stop_event


def main() -> None:
    import uvicorn

    server, _orchestrator, _stop = build()
    uvicorn.run(
        server.app,
        # Bind all interfaces inside the container; exposure is via compose ports.
        host=os.environ.get("DASHBOARD_HOST", "0.0.0.0"),  # nosec B104
        port=int(os.environ.get("DASHBOARD_PORT", "8000")),
    )


if __name__ == "__main__":
    main()

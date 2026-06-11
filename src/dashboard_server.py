#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Real-time monitoring dashboard (SPEC-003).

`DashboardServer` exposes a FastAPI app with:

    GET /            → HTML dashboard page
    GET /video_feed  → MJPEG stream (multipart/x-mixed-replace)
    GET /health      → {"status": "ok", "fps": float, "uptime": float}
    WS  /ws          → pushes detection / fps events to all connected clients

The camera frame source and FPS source are injected as callables so the
endpoints can be unit-tested without a real CSI camera (per capstone §B.5).
On Yahboom the frame source wraps the InferenceNode GStreamer pipeline.
"""
from __future__ import annotations

import json
import time
from collections.abc import Callable
from typing import Any

from fastapi import FastAPI, WebSocket, WebSocketDisconnect
from fastapi.responses import HTMLResponse, JSONResponse, StreamingResponse

# Frame source returns the latest JPEG bytes, or None when the camera is offline
# / the stream has ended.
FrameSource = Callable[[], "bytes | None"]
FpsSource = Callable[[], float]

_BOUNDARY = "frame"

_INDEX_HTML = """<!DOCTYPE html>
<html lang="zh-TW">
<head><meta charset="utf-8"><title>智慧垃圾分類 — 即時監控</title></head>
<body>
  <h1>智慧零接觸垃圾分類系統</h1>
  <img src="/video_feed" alt="camera" width="640">
  <pre id="events"></pre>
  <script>
    const ws = new WebSocket(`ws://${location.host}/ws`);
    ws.onmessage = (e) => {
      const el = document.getElementById("events");
      el.textContent = e.data + "\\n" + el.textContent;
    };
  </script>
</body>
</html>
"""


class ConnectionManager:
    """Tracks connected WebSocket clients and broadcasts JSON events.

    Clients that error on send (disconnected) are pruned silently so a single
    dead client never breaks the broadcast to the rest.
    """

    def __init__(self) -> None:
        self.active: list[Any] = []

    async def connect(self, websocket: Any) -> None:
        """Accept the handshake and register the client."""
        await websocket.accept()
        self.active.append(websocket)

    def disconnect(self, websocket: Any) -> None:
        """Remove a client; safe to call for an already-removed client."""
        if websocket in self.active:
            self.active.remove(websocket)

    async def broadcast(self, message: dict) -> None:
        """Send a JSON message to every client, dropping any that fail."""
        text = json.dumps(message, ensure_ascii=False)
        dead: list[Any] = []
        for websocket in list(self.active):
            try:
                await websocket.send_text(text)
            except Exception:  # noqa: BLE001 - client gone; prune silently
                dead.append(websocket)
        for websocket in dead:
            self.disconnect(websocket)


class DashboardServer:
    """FastAPI + WebSocket dashboard exposing the live camera and events."""

    def __init__(self, frame_source: FrameSource | None = None,
                 fps_source: FpsSource | None = None) -> None:
        """Configure the server.

        Args:
            frame_source: callable returning the latest JPEG frame, or None
                when the camera is offline / the stream has ended.
            fps_source: callable returning the current inference FPS.
        """
        self.manager = ConnectionManager()
        self._frame_source: FrameSource = frame_source or (lambda: None)
        self._fps_source: FpsSource = fps_source or (lambda: 0.0)
        self._start = time.monotonic()
        self.app = self._build_app()

    @property
    def uptime(self) -> float:
        """Seconds since the server was constructed."""
        return time.monotonic() - self._start

    async def broadcast_detection(self, result: dict) -> None:
        """Broadcast a detection event to all dashboard clients."""
        await self.manager.broadcast({
            "type": "detection",
            "class_id": result["class_id"],
            "class_name": result["class_name"],
            "confidence": result["confidence"],
            "timestamp": result["timestamp"],
        })

    def _mjpeg_stream(self, first: bytes):
        """Yield multipart MJPEG chunks until the frame source is exhausted."""
        frame: bytes | None = first
        while frame is not None:
            yield (
                b"--" + _BOUNDARY.encode() + b"\r\n"
                b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
            )
            frame = self._frame_source()

    def _build_app(self) -> FastAPI:
        app = FastAPI(title="Waste Sorter Dashboard")

        @app.get("/", response_class=HTMLResponse)
        async def index() -> str:
            return _INDEX_HTML

        @app.get("/health")
        async def health() -> JSONResponse:
            return JSONResponse({
                "status": "ok",
                "fps": self._fps_source(),
                "uptime": self.uptime,
            })

        @app.get("/video_feed")
        async def video_feed() -> StreamingResponse:
            first = self._frame_source()
            if first is None:
                return JSONResponse({"error": "camera offline"}, status_code=503)
            return StreamingResponse(
                self._mjpeg_stream(first),
                media_type=f"multipart/x-mixed-replace; boundary={_BOUNDARY}",
            )

        @app.websocket("/ws")
        async def ws(websocket: WebSocket) -> None:
            await self.manager.connect(websocket)
            # Send current FPS immediately so a fresh client isn't blank.
            await websocket.send_text(
                json.dumps({"type": "fps", "value": self._fps_source()})
            )
            try:
                while True:
                    await websocket.receive_text()
            except WebSocketDisconnect:
                self.manager.disconnect(websocket)

        return app

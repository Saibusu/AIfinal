#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Pipeline orchestrator wiring the full loop (SPEC-007).

Ties the five modules into one runtime loop:
    frame → InferenceNode (Sense+Process+Decide) → ActuatorController (Act)
          → MqttPublisher (event out) → on_event (Dashboard broadcast)

Maintains rolling FPS and the latest JPEG frame for the dashboard. All
collaborators are injected, so the loop is fully unit-testable without a
camera, GPIO, model, or MQTT broker. Hardware/event-loop glue (camera reads,
JPEG encoding, cross-thread broadcast) lives in `src/app.py`.
"""
from __future__ import annotations

import time
from collections import deque
from collections.abc import Callable
from typing import Any


class PipelineOrchestrator:
    """Runs the Sense→Process→Decide→Act loop and exposes live frame/FPS."""

    def __init__(self, inference_node: Any, actuator: Any,
                 publisher: Any | None = None,
                 on_event: Callable[[dict], None] | None = None,
                 clock: Callable[[], float] = time.monotonic,
                 fps_window: int = 30) -> None:
        """Wire the orchestrator.

        Args:
            inference_node: provides `infer_frame(frame) -> dict | None`.
            actuator: provides `trigger(class_id)`.
            publisher: optional `publish_detection(result)`.
            on_event: optional callback fed each detection (dashboard broadcast).
            clock: monotonic seconds source (injected in tests).
            fps_window: number of recent frame timestamps used for the FPS calc.
        """
        self._node = inference_node
        self._actuator = actuator
        self._publisher = publisher
        self._on_event = on_event
        self._clock = clock
        self._stamps: deque[float] = deque(maxlen=fps_window)
        self._latest_jpeg: bytes | None = None
        self._latest_result: dict | None = None

    def process_frame(self, frame: Any, jpeg: bytes | None = None) -> dict | None:
        """Run one frame through the full loop; return the detection or None."""
        result = self._node.infer_frame(frame)
        self._stamps.append(self._clock())
        if jpeg is not None:
            self._latest_jpeg = jpeg
        if result is None:
            return None
        self._latest_result = result
        self._safe(self._actuator.trigger, result["class_id"])
        if self._publisher is not None:
            self._safe(self._publisher.publish_detection, result)
        if self._on_event is not None:
            self._safe(self._on_event, result)
        return result

    def run(self, frame_reader: Callable[[], Any],
            jpeg_encoder: Callable[[Any], bytes] | None = None,
            max_frames: int | None = None) -> int:
        """Loop over frames until the reader returns None or max_frames is hit.

        Returns the number of frames processed.
        """
        count = 0
        while max_frames is None or count < max_frames:
            frame = frame_reader()
            if frame is None:
                break
            jpeg = jpeg_encoder(frame) if jpeg_encoder is not None else None
            self.process_frame(frame, jpeg)
            count += 1
        return count

    @staticmethod
    def _safe(fn: Callable[..., Any], *args: Any) -> None:
        """Call a side-effect sink, swallowing errors so one bad sink/loop
        iteration never crashes the pipeline."""
        # Resilience: a failing sink must never crash the capture loop.
        try:
            fn(*args)
        except Exception:  # noqa: BLE001  # nosec B110
            pass

    @property
    def fps(self) -> float:
        """Rolling frames-per-second over the recent window."""
        if len(self._stamps) < 2:
            return 0.0
        span = self._stamps[-1] - self._stamps[0]
        if span <= 0:
            return 0.0
        return round((len(self._stamps) - 1) / span, 2)

    def get_fps(self) -> float:
        """FPS source for the dashboard."""
        return self.fps

    def get_frame(self) -> bytes | None:
        """Latest JPEG frame source for the dashboard `/video_feed`."""
        return self._latest_jpeg

    @property
    def latest_result(self) -> dict | None:
        """Most recent detection result (None until the first detection)."""
        return self._latest_result

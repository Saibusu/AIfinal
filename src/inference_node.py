#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Sense + Process stage of the pipeline (SPEC-001).

Captures frames from the CSI IMX219 camera (GStreamer) and runs YOLO26m
(TensorRT engine) inference, delegating the final class decision to
DecisionEngine. Heavy deps (ultralytics, opencv) are imported lazily inside
the hardware methods so pure logic stays unit-testable without them.
"""
from __future__ import annotations

import os
import time
from typing import Any

from src.decision_engine import DecisionEngine

# Detection tuple: (class_id, confidence, bbox[x1,y1,x2,y2])
Detection = tuple[int, float, list[float]]


class InferenceNode:
    """Camera → YOLO26m → DecisionEngine, exposing the latest detection result."""

    def __init__(self, model_path: str, camera_source: str | None = None,
                 conf_threshold: float = 0.5, imgsz: int = 416,
                 model: Any | None = None,
                 decision_engine: DecisionEngine | None = None) -> None:
        """Configure the node (does not load the model or open the camera).

        Args:
            model_path: path to the YOLO26m weights / TensorRT engine.
            camera_source: explicit source; if None, falls back to env
                `CAMERA_SOURCE`, then to the default CSI GStreamer pipeline.
            conf_threshold: min confidence to accept a detection.
            imgsz: inference image size.
            model: optional pre-built model (callable) — injected in tests.
            decision_engine: optional DecisionEngine — injected in tests.
        """
        self.model_path = model_path
        self.imgsz = imgsz
        self.camera_source = (
            camera_source
            or os.environ.get("CAMERA_SOURCE")
            or self.build_gstreamer_pipeline()
        )
        self._model = model
        self._engine = decision_engine or DecisionEngine(conf_threshold=conf_threshold)
        self._latest_result: dict | None = None
        self._camera: Any | None = None
        self._running = False

    @staticmethod
    def build_gstreamer_pipeline(sensor_id: int = 0, capture_width: int = 1280,
                                 capture_height: int = 720, framerate: int = 30) -> str:
        """Build the nvarguscamerasrc GStreamer pipeline string for CSI IMX219."""
        return (
            f"nvarguscamerasrc sensor-id={sensor_id} ! "
            f"video/x-raw(memory:NVMM),width={capture_width},height={capture_height},"
            f"framerate={framerate}/1 ! nvvidconv ! video/x-raw,format=BGRx ! "
            f"videoconvert ! video/x-raw,format=BGR ! appsink drop=true max-buffers=1"
        )

    def infer_frame(self, frame: Any) -> dict | None:
        """Run inference on one frame and update the latest result.

        Returns the detection result dict, or None when nothing is detected.

        Raises:
            RuntimeError: if the model has not been loaded (call start() first).
        """
        if self._model is None:
            raise RuntimeError("model not loaded — inject a model or call start() first")
        results = self._model(frame, imgsz=self.imgsz, verbose=False)
        detections = self._parse(results)
        self._latest_result = self._select_and_decide(detections)
        return self._latest_result

    def get_latest_result(self) -> dict | None:
        """Return the most recent detection result (None until first inference)."""
        return self._latest_result

    @staticmethod
    def _parse(results: Any) -> list[Detection]:
        """Extract detections from an ultralytics result list."""
        if not results:
            return []
        boxes = results[0].boxes
        if boxes is None or len(boxes) == 0:
            return []
        cls = boxes.cls.tolist()
        conf = boxes.conf.tolist()
        xyxy = boxes.xyxy.tolist()
        return [(int(c), float(p), [float(v) for v in b]) for c, p, b in zip(cls, conf, xyxy)]

    def _select_and_decide(self, detections: list[Detection]) -> dict | None:
        """Pick the highest-confidence detection and apply DecisionEngine."""
        if not detections:
            return None
        class_id, confidence, bbox = max(detections, key=lambda d: d[1])
        decision = self._engine.decide(class_id, confidence)
        return {
            "class_id": decision.class_id,
            "class_name": decision.class_name,
            "led_color": decision.led_color,
            "confidence": confidence,
            "bbox": bbox,
            "is_fallback": decision.is_fallback,
            "timestamp": time.time(),
        }

    def _read_frame_with_retry(self, camera: Any, retries: int = 3) -> Any | None:
        """Read a frame, retrying on failure (SPEC-001 camera-disconnect edge case)."""
        for _ in range(retries):
            ok, frame = camera.read()
            if ok:
                return frame
        return None

    def stop(self) -> None:
        """Stop the capture loop and release the camera."""
        self._running = False
        if self._camera is not None:
            self._camera.release()
            self._camera = None

    def _load_model(self) -> Any:  # pragma: no cover - needs ultralytics + weights
        from ultralytics import YOLO

        return YOLO(self.model_path)

    def _open_camera(self) -> Any:  # pragma: no cover - needs opencv + CSI hardware
        import cv2

        return cv2.VideoCapture(self.camera_source, cv2.CAP_GSTREAMER)

    def load(self) -> None:  # pragma: no cover - needs ultralytics + weights
        """Load the model without starting the capture loop.

        Used by the app entrypoint when the PipelineOrchestrator (not this
        node's own `start()` loop) drives frame reading.
        """
        if self._model is None:
            self._model = self._load_model()

    def start(self) -> None:  # pragma: no cover - hardware loop, verified on Yahboom
        if self._model is None:
            self._model = self._load_model()
        self._camera = self._open_camera()
        self._running = True
        while self._running:
            frame = self._read_frame_with_retry(self._camera)
            if frame is None:
                self.stop()
                break
            self.infer_frame(frame)

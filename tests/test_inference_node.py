#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Unit tests for InferenceNode (SPEC-001). TDD — written before implementation.

The heavy deps (ultralytics, opencv) are never imported: a fake model is
injected and camera I/O is exercised via mocks.
"""
from types import SimpleNamespace
from unittest.mock import MagicMock

import pytest

from src.inference_node import InferenceNode


class _FakeBoxes:
    """Mimics ultralytics Boxes: .cls/.conf/.xyxy each expose .tolist()."""

    def __init__(self, dets):
        self._cls = SimpleNamespace(tolist=lambda: [d[0] for d in dets])
        self._conf = SimpleNamespace(tolist=lambda: [d[1] for d in dets])
        self._xyxy = SimpleNamespace(tolist=lambda: [d[2] for d in dets])
        self._n = len(dets)

    cls = property(lambda self: self._cls)
    conf = property(lambda self: self._conf)
    xyxy = property(lambda self: self._xyxy)

    def __len__(self):
        return self._n


def _fake_model(dets):
    """Return a callable model that yields one result with the given detections."""
    result = SimpleNamespace(boxes=_FakeBoxes(dets))
    model = MagicMock(return_value=[result])
    return model


def _node(dets, conf_threshold=0.5):
    return InferenceNode(model_path="x.engine", conf_threshold=conf_threshold,
                         model=_fake_model(dets))


def test_gstreamer_pipeline_is_built_for_csi():
    pipe = InferenceNode.build_gstreamer_pipeline(sensor_id=0)
    assert "nvarguscamerasrc" in pipe
    assert "sensor-id=0" in pipe
    assert "appsink" in pipe


def test_camera_source_defaults_to_gstreamer(monkeypatch):
    monkeypatch.delenv("CAMERA_SOURCE", raising=False)
    node = InferenceNode(model_path="x.engine", model=_fake_model([]))
    assert "nvarguscamerasrc" in node.camera_source


def test_camera_source_env_override(monkeypatch):
    monkeypatch.setenv("CAMERA_SOURCE", "/tmp/test.mp4")
    node = InferenceNode(model_path="x.engine", model=_fake_model([]))
    assert node.camera_source == "/tmp/test.mp4"


def test_infer_frame_no_detection_returns_none():
    assert _node([]).infer_frame(frame=object()) is None


def test_infer_frame_empty_results_returns_none():
    node = InferenceNode(model_path="x.engine", model=MagicMock(return_value=[]))
    assert node.infer_frame(frame=object()) is None


def test_infer_frame_handles_none_boxes():
    result = SimpleNamespace(boxes=None)
    node = InferenceNode(model_path="x.engine", model=MagicMock(return_value=[result]))
    assert node.infer_frame(frame=object()) is None


def test_infer_frame_picks_highest_confidence():
    dets = [(0, 0.6, [0, 0, 10, 10]), (1, 0.9, [5, 5, 20, 20])]
    result = _node(dets).infer_frame(frame=object())
    assert result["class_id"] == 1
    assert result["confidence"] == 0.9
    assert result["is_fallback"] is False


def test_infer_frame_low_confidence_falls_back_to_general_waste():
    dets = [(0, 0.3, [0, 0, 10, 10])]
    result = _node(dets, conf_threshold=0.5).infer_frame(frame=object())
    assert result["class_id"] == 4
    assert result["is_fallback"] is True


def test_infer_frame_result_schema():
    result = _node([(2, 0.8, [1, 2, 3, 4])]).infer_frame(frame=object())
    assert set(result) == {
        "class_id", "class_name", "led_color", "confidence", "bbox",
        "is_fallback", "timestamp",
    }
    assert result["bbox"] == [1, 2, 3, 4]
    assert result["class_name"] == "紙餐盒"


def test_get_latest_result_initially_none():
    assert _node([]).get_latest_result() is None


def test_get_latest_result_updates_after_infer():
    node = _node([(1, 0.9, [0, 0, 1, 1])])
    node.infer_frame(frame=object())
    assert node.get_latest_result()["class_id"] == 1


def test_read_frame_with_retry_succeeds_before_limit():
    cam = MagicMock()
    cam.read.side_effect = [(False, None), (False, None), (True, "frame")]
    assert _node([])._read_frame_with_retry(cam, retries=3) == "frame"


def test_read_frame_with_retry_gives_up():
    cam = MagicMock()
    cam.read.return_value = (False, None)
    assert _node([])._read_frame_with_retry(cam, retries=3) is None
    assert cam.read.call_count == 3


def test_stop_releases_camera():
    node = _node([])
    cam = MagicMock()
    node._camera = cam
    node.stop()
    cam.release.assert_called_once()
    assert node._camera is None


def test_infer_frame_without_model_raises():
    node = InferenceNode(model_path="x.engine")  # no model injected, start() not called
    with pytest.raises(RuntimeError):
        node.infer_frame(frame=object())

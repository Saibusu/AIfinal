#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Tests for PipelineOrchestrator (SPEC-007).

All five collaborators are mocked, so the full Sense→Process→Decide→Act loop
is exercised without a camera, GPIO, model, or MQTT broker.
"""
from __future__ import annotations

from unittest.mock import MagicMock

from src.pipeline_orchestrator import PipelineOrchestrator

_RESULT = {
    "class_id": 0,
    "class_name": "寶特瓶",
    "led_color": "green",
    "confidence": 0.91,
    "is_fallback": False,
    "timestamp": 123.0,
}


def _make(infer_return=_RESULT, publisher=None, on_event=None, clock=None):
    node = MagicMock()
    node.infer_frame.return_value = infer_return
    actuator = MagicMock()
    orch = PipelineOrchestrator(
        inference_node=node, actuator=actuator, publisher=publisher,
        on_event=on_event, clock=clock or (lambda: 0.0),
    )
    return orch, node, actuator


def test_process_frame_runs_full_loop() -> None:
    publisher, on_event = MagicMock(), MagicMock()
    orch, node, actuator = _make(publisher=publisher, on_event=on_event)
    result = orch.process_frame("frame")
    assert result == _RESULT
    node.infer_frame.assert_called_once_with("frame")
    actuator.trigger.assert_called_once_with(0)
    publisher.publish_detection.assert_called_once_with(_RESULT)
    on_event.assert_called_once_with(_RESULT)


def test_process_frame_no_detection_skips_sinks() -> None:
    publisher, on_event = MagicMock(), MagicMock()
    orch, node, actuator = _make(infer_return=None, publisher=publisher, on_event=on_event)
    assert orch.process_frame("frame") is None
    actuator.trigger.assert_not_called()
    publisher.publish_detection.assert_not_called()
    on_event.assert_not_called()


def test_process_frame_without_publisher_ok() -> None:
    on_event = MagicMock()
    orch, _node, actuator = _make(publisher=None, on_event=on_event)
    orch.process_frame("frame")
    actuator.trigger.assert_called_once()
    on_event.assert_called_once_with(_RESULT)


def test_actuator_failure_does_not_stop_publish() -> None:
    publisher, on_event = MagicMock(), MagicMock()
    orch, _node, actuator = _make(publisher=publisher, on_event=on_event)
    actuator.trigger.side_effect = RuntimeError("GPIO busy")
    result = orch.process_frame("frame")
    assert result == _RESULT
    publisher.publish_detection.assert_called_once()
    on_event.assert_called_once()


def test_publisher_failure_swallowed() -> None:
    publisher, on_event = MagicMock(), MagicMock()
    publisher.publish_detection.side_effect = RuntimeError("broker down")
    orch, _node, _actuator = _make(publisher=publisher, on_event=on_event)
    assert orch.process_frame("frame") == _RESULT
    on_event.assert_called_once()


def test_get_frame_returns_latest_jpeg() -> None:
    orch, _node, _actuator = _make()
    assert orch.get_frame() is None
    orch.process_frame("frame", jpeg=b"\xff\xd8jpeg\xff\xd9")
    assert orch.get_frame() == b"\xff\xd8jpeg\xff\xd9"


def test_latest_result_tracked() -> None:
    orch, _node, _actuator = _make()
    assert orch.latest_result is None
    orch.process_frame("frame")
    assert orch.latest_result == _RESULT


def test_fps_computed_with_clock() -> None:
    ticks = iter([0.0, 0.1, 0.2, 0.3, 0.4])
    orch, _node, _actuator = _make(clock=lambda: next(ticks))
    for _ in range(5):
        orch.process_frame("frame")
    # 4 intervals of 0.1s over 5 samples → ~10 FPS
    assert 8.0 <= orch.get_fps() <= 12.0


def test_fps_zero_before_two_frames() -> None:
    orch, _node, _actuator = _make()
    assert orch.get_fps() == 0.0          # no frames yet
    orch.process_frame("frame")
    assert orch.get_fps() == 0.0          # only one sample


def test_fps_zero_when_clock_static() -> None:
    orch, _node, _actuator = _make(clock=lambda: 7.0)
    orch.process_frame("frame")
    orch.process_frame("frame")
    assert orch.get_fps() == 0.0


def test_run_stops_on_none_frame() -> None:
    frames = iter(["a", "b", None])
    orch, _node, actuator = _make()
    processed = orch.run(frame_reader=lambda: next(frames))
    assert processed == 2
    assert actuator.trigger.call_count == 2


def test_run_respects_max_frames() -> None:
    orch, _node, _actuator = _make()
    processed = orch.run(frame_reader=lambda: "frame", max_frames=3)
    assert processed == 3


def test_run_uses_jpeg_encoder() -> None:
    frames = iter(["a", None])
    orch, _node, _actuator = _make()
    orch.run(frame_reader=lambda: next(frames), jpeg_encoder=lambda f: b"ENC")
    assert orch.get_frame() == b"ENC"

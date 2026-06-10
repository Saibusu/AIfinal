#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Decision stage of the waste-sorting pipeline (SPEC-004).

Pure logic, no hardware or model dependency: maps an inference result
(class_id + confidence) to the final actuator decision, applying the
confidence threshold and the low-confidence safety fallback to general waste.
"""
from __future__ import annotations

from dataclasses import dataclass

GENERAL_WASTE_ID = 4

# class_id -> (class_name, led_color). Per ADR-002 (5 classes, Yahboom LEDs).
_CLASS_TABLE: dict[int, tuple[str, str]] = {
    0: ("寶特瓶", "green"),
    1: ("鐵鋁罐", "yellow"),
    2: ("紙餐盒", "blue"),
    3: ("塑膠袋", "white"),
    4: ("一般垃圾", "red"),
}


@dataclass(frozen=True)
class Decision:
    """Final decision handed to the actuator layer."""

    class_id: int
    class_name: str
    led_color: str
    is_fallback: bool


class DecisionEngine:
    """Maps inference results to actuator decisions with a safety fallback."""

    def __init__(self, conf_threshold: float = 0.5) -> None:
        """Create the engine.

        Args:
            conf_threshold: minimum confidence (0.0–1.0) to accept a detection.

        Raises:
            ValueError: if conf_threshold is outside [0.0, 1.0].
        """
        if not 0.0 <= conf_threshold <= 1.0:
            raise ValueError(f"conf_threshold must be in [0.0, 1.0], got {conf_threshold}")
        self._conf_threshold = conf_threshold

    def decide(self, class_id: int | None, confidence: float) -> Decision:
        """Decide the final class and LED for a detection.

        Args:
            class_id: detected class id (0–4) or None when nothing was detected.
            confidence: detection confidence in [0.0, 1.0].

        Returns:
            A Decision; falls back to general waste when the detection is
            missing, out of range, or below the confidence threshold.

        Raises:
            ValueError: if confidence is outside [0.0, 1.0].
        """
        if not 0.0 <= confidence <= 1.0:
            raise ValueError(f"confidence must be in [0.0, 1.0], got {confidence}")

        if class_id is None or class_id not in _CLASS_TABLE or confidence < self._conf_threshold:
            return self._build(GENERAL_WASTE_ID, is_fallback=True)
        return self._build(class_id, is_fallback=False)

    def _build(self, class_id: int, is_fallback: bool) -> Decision:
        name, color = _CLASS_TABLE[class_id]
        return Decision(class_id=class_id, class_name=name, led_color=color, is_fallback=is_fallback)

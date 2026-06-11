#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Act stage of the pipeline (SPEC-002).

Drives the 5 classification LEDs via GPIO on the Yahboom kit (Jetson.GPIO,
BOARD pin numbering — see ADR-002). Lights the LED for the decided class for
`led_duration` seconds, then auto-off. Jetson.GPIO is imported lazily so the
logic is unit-testable with an injected mock gpio module.
"""
from __future__ import annotations

import os
import threading
from collections.abc import Callable
from typing import Any

# class_id -> physical BOARD pin (Yahboom, per ADR-002)
DEFAULT_GPIO_PINS: dict[int, int] = {0: 11, 1: 13, 2: 15, 3: 21, 4: 23}
GENERAL_WASTE_ID = 4


class ActuatorController:
    """Controls the per-class LEDs with mutual exclusion and auto-off."""

    def __init__(self, gpio_pins: dict[int, int] | None = None,
                 led_duration: float = 5.0, gpio: Any | None = None,
                 timer_factory: Callable | None = None) -> None:
        """Configure and initialise the GPIO pins.

        Args:
            gpio_pins: class_id → BOARD pin map; defaults to DEFAULT_GPIO_PINS
                with per-pin env override `GPIO_PIN_<class_id>`.
            led_duration: seconds an LED stays on before auto-off.
            gpio: injected GPIO module (Jetson.GPIO) — mocked in tests.
            timer_factory: callable(delay, fn) → timer — injected in tests.
        """
        self.pins = gpio_pins or self._resolve_pins()
        self.led_duration = led_duration
        self._gpio = gpio or self._load_gpio()
        self._timer_factory = timer_factory or threading.Timer
        self._timer: Any | None = None
        self._setup()

    @staticmethod
    def _resolve_pins() -> dict[int, int]:
        """Default pin map, allowing `GPIO_PIN_<class_id>` env overrides."""
        return {
            cid: int(os.environ.get(f"GPIO_PIN_{cid}", default))
            for cid, default in DEFAULT_GPIO_PINS.items()
        }

    @staticmethod
    def _load_gpio() -> Any:  # pragma: no cover - needs Jetson.GPIO on device
        import Jetson.GPIO as GPIO

        return GPIO

    def _setup(self) -> None:
        """Set BOARD mode and configure every LED pin as output."""
        self._gpio.setmode(self._gpio.BOARD)
        for pin in self.pins.values():
            self._gpio.setup(pin, self._gpio.OUT)

    def trigger(self, class_id: int) -> None:
        """Light the LED for `class_id` (falls back to general waste if invalid).

        Enforces mutual exclusion (all off first) and schedules auto-off.
        """
        if class_id not in self.pins:
            class_id = GENERAL_WASTE_ID
        self.all_off()
        self._gpio.output(self.pins[class_id], self._gpio.HIGH)
        self._timer = self._timer_factory(self.led_duration, self.all_off)
        self._timer.daemon = True
        self._timer.start()

    def all_off(self) -> None:
        """Turn every LED off."""
        for pin in self.pins.values():
            self._gpio.output(pin, self._gpio.LOW)

    def cleanup(self) -> None:
        """Cancel any pending auto-off timer and release the GPIO pins."""
        if self._timer is not None:
            self._timer.cancel()
        self._gpio.cleanup()

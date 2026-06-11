#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Unit tests for ActuatorController (SPEC-002). TDD — written before implementation.

Jetson.GPIO is never imported: a mock gpio module is injected, and the
auto-off timer factory is faked so tests never sleep.
"""
from unittest.mock import MagicMock, call

from src.actuator_controller import ActuatorController

DEFAULT_PINS = {0: 11, 1: 13, 2: 15, 3: 21, 4: 23}


def _controller(**kw):
    gpio = MagicMock()
    gpio.HIGH, gpio.LOW, gpio.BOARD, gpio.OUT = 1, 0, "BOARD", "OUT"
    timer_factory = MagicMock()
    return ActuatorController(gpio=gpio, timer_factory=timer_factory, **kw), gpio, timer_factory


def test_default_pins_match_adr002():
    ctrl, _, _ = _controller()
    assert ctrl.pins == DEFAULT_PINS


def test_setup_uses_board_mode_and_configures_all_pins():
    ctrl, gpio, _ = _controller()
    gpio.setmode.assert_called_once_with("BOARD")
    assert gpio.setup.call_count == 5
    for pin in DEFAULT_PINS.values():
        gpio.setup.assert_any_call(pin, "OUT")


def test_trigger_sets_correct_pin_high():
    ctrl, gpio, _ = _controller()
    ctrl.trigger(2)  # 紙餐盒 → Pin 15
    gpio.output.assert_any_call(15, 1)


def test_trigger_mutual_exclusion_turns_all_off_first():
    ctrl, gpio, _ = _controller()
    ctrl.trigger(1)  # Pin 13
    # all_off sets every pin LOW, then the chosen pin HIGH
    gpio.output.assert_any_call(13, 0)  # turned off during all_off
    assert gpio.output.call_args == call(13, 1)  # last call turns it on


def test_trigger_invalid_class_defaults_to_general_waste():
    ctrl, gpio, _ = _controller()
    ctrl.trigger(99)
    gpio.output.assert_any_call(23, 1)  # class 4 → Pin 23


def test_trigger_schedules_auto_off():
    ctrl, _, timer_factory = _controller(led_duration=5.0)
    ctrl.trigger(0)
    timer_factory.assert_called_once_with(5.0, ctrl.all_off)
    timer_factory.return_value.start.assert_called_once()


def test_all_off_sets_every_pin_low():
    ctrl, gpio, _ = _controller()
    gpio.reset_mock()
    ctrl.all_off()
    for pin in DEFAULT_PINS.values():
        gpio.output.assert_any_call(pin, 0)


def test_cleanup_cancels_timer_and_calls_gpio_cleanup():
    ctrl, gpio, timer_factory = _controller()
    ctrl.trigger(0)
    ctrl.cleanup()
    timer_factory.return_value.cancel.assert_called_once()
    gpio.cleanup.assert_called_once()


def test_env_pin_override(monkeypatch):
    monkeypatch.setenv("GPIO_PIN_3", "29")
    ctrl, _, _ = _controller()
    assert ctrl.pins[3] == 29

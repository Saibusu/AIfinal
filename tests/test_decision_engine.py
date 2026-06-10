#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Unit tests for DecisionEngine (SPEC-004). TDD — written before implementation."""
import pytest

from src.decision_engine import Decision, DecisionEngine

GENERAL_WASTE_ID = 4

EXPECTED_LED = {
    0: ("寶特瓶", "green"),
    1: ("鐵鋁罐", "yellow"),
    2: ("紙餐盒", "blue"),
    3: ("塑膠袋", "white"),
    4: ("一般垃圾", "red"),
}


def test_valid_classes_pass_through():
    engine = DecisionEngine(conf_threshold=0.5)
    for class_id in range(5):
        decision = engine.decide(class_id, confidence=0.9)
        assert decision.class_id == class_id
        assert decision.is_fallback is False


def test_led_color_mapping():
    engine = DecisionEngine()
    for class_id, (name, color) in EXPECTED_LED.items():
        decision = engine.decide(class_id, confidence=0.9)
        assert decision.class_name == name
        assert decision.led_color == color


def test_returns_decision_instance():
    engine = DecisionEngine()
    assert isinstance(engine.decide(0, 0.9), Decision)


def test_low_confidence_fallback():
    engine = DecisionEngine(conf_threshold=0.5)
    decision = engine.decide(class_id=0, confidence=0.3)
    assert decision.class_id == GENERAL_WASTE_ID
    assert decision.is_fallback is True
    assert decision.led_color == "red"


def test_none_class_fallback():
    engine = DecisionEngine()
    decision = engine.decide(class_id=None, confidence=0.9)
    assert decision.class_id == GENERAL_WASTE_ID
    assert decision.is_fallback is True


@pytest.mark.parametrize("bad_id", [5, -1, 99])
def test_invalid_class_id_fallback(bad_id):
    engine = DecisionEngine()
    decision = engine.decide(class_id=bad_id, confidence=0.9)
    assert decision.class_id == GENERAL_WASTE_ID
    assert decision.is_fallback is True


@pytest.mark.parametrize("bad_conf", [1.5, -0.1, 2.0])
def test_confidence_out_of_range_raises(bad_conf):
    engine = DecisionEngine()
    with pytest.raises(ValueError):
        engine.decide(class_id=0, confidence=bad_conf)


@pytest.mark.parametrize("bad_threshold", [1.5, -0.1])
def test_invalid_threshold_raises(bad_threshold):
    with pytest.raises(ValueError):
        DecisionEngine(conf_threshold=bad_threshold)


def test_boundary_confidence_is_accepted():
    engine = DecisionEngine(conf_threshold=0.5)
    decision = engine.decide(class_id=2, confidence=0.5)
    assert decision.class_id == 2
    assert decision.is_fallback is False

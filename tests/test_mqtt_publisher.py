#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Unit tests for MqttPublisher (SPEC-005). TDD — written before implementation.

A mock paho client is injected; no real broker is contacted.
"""
import json
from unittest.mock import MagicMock

import pytest

from src.mqtt_publisher import MqttPublisher

DETECTION = {
    "class_id": 0,
    "class_name": "寶特瓶",
    "confidence": 0.87,
    "is_fallback": False,
    "timestamp": 1749600000.0,
}


def _ok_client():
    client = MagicMock()
    client.publish.return_value = MagicMock(rc=0)
    return client


def _fail_client():
    client = MagicMock()
    client.publish.return_value = MagicMock(rc=1)
    return client


def test_publish_detection_success():
    client = _ok_client()
    pub = MqttPublisher(client=client)
    assert pub.publish_detection(DETECTION) is True
    topic = client.publish.call_args[0][0]
    assert topic == "waste/detection"


def test_publish_detection_payload_schema():
    client = _ok_client()
    MqttPublisher(client=client).publish_detection(DETECTION)
    payload = json.loads(client.publish.call_args[0][1])
    assert set(payload) >= {"class_id", "class_name", "confidence", "timestamp"}
    assert payload["class_id"] == 0


def test_publish_detection_missing_field_raises():
    pub = MqttPublisher(client=_ok_client())
    with pytest.raises(ValueError):
        pub.publish_detection({"class_id": 0})  # missing required fields


def test_publish_retries_on_failure():
    client = _fail_client()
    pub = MqttPublisher(client=client, max_retries=3)
    assert pub.publish_detection(DETECTION) is False
    assert client.publish.call_count == 3


def test_publish_status():
    client = _ok_client()
    assert MqttPublisher(client=client).publish_status({"fps": 18.5}) is True
    assert client.publish.call_args[0][0] == "waste/status"


def test_topic_prefix_applied():
    client = _ok_client()
    MqttPublisher(client=client, topic_prefix="bin1").publish_detection(DETECTION)
    assert client.publish.call_args[0][0] == "bin1/detection"


def test_connect_invokes_client():
    client = _ok_client()
    MqttPublisher(client=client, broker="b", port=1883).connect()
    client.connect.assert_called_once()
    client.loop_start.assert_called_once()


def test_disconnect_invokes_client():
    client = _ok_client()
    pub = MqttPublisher(client=client)
    pub.disconnect()
    client.loop_stop.assert_called_once()
    client.disconnect.assert_called_once()

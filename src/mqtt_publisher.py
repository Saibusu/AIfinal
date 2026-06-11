#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""MQTT event publishing (SPEC-005).

Publishes detection events and system status to an MQTT broker for the
dashboard (and future multi-bin monitoring). Wraps paho-mqtt with JSON
schema validation and publish retries. The client is injectable for tests.
"""
from __future__ import annotations

import json
from typing import Any

_REQUIRED_DETECTION_FIELDS = ("class_id", "class_name", "confidence", "timestamp")


class MqttPublisher:
    """Publishes waste-sorting events to MQTT topics with retry."""

    TOPIC_DETECTION = "detection"
    TOPIC_STATUS = "status"

    def __init__(self, broker: str = "localhost", port: int = 1883,
                 topic_prefix: str = "waste", client: Any | None = None,
                 max_retries: int = 3) -> None:
        """Configure the publisher.

        Args:
            broker: MQTT broker host.
            port: MQTT broker port.
            topic_prefix: prefix for topics (e.g. "waste" → "waste/detection").
            client: optional paho client — injected in tests; built lazily otherwise.
            max_retries: publish attempts before giving up.
        """
        self.broker = broker
        self.port = port
        self.topic_prefix = topic_prefix
        self.max_retries = max_retries
        self._client = client or self._build_client()

    @staticmethod
    def _build_client() -> Any:  # pragma: no cover - needs paho broker connection
        import paho.mqtt.client as mqtt

        return mqtt.Client()

    def connect(self) -> None:
        """Connect to the broker and start the network loop."""
        self._client.connect(self.broker, self.port)
        self._client.loop_start()

    def publish_detection(self, result: dict) -> bool:
        """Publish a detection event to `<prefix>/detection`.

        Raises:
            ValueError: if a required field is missing.
        """
        missing = [f for f in _REQUIRED_DETECTION_FIELDS if f not in result]
        if missing:
            raise ValueError(f"detection result missing fields: {missing}")
        payload = {
            "class_id": result["class_id"],
            "class_name": result["class_name"],
            "confidence": result["confidence"],
            "is_fallback": result.get("is_fallback", False),
            "timestamp": result["timestamp"],
        }
        return self._publish(self.TOPIC_DETECTION, payload)

    def publish_status(self, status: dict) -> bool:
        """Publish a system-status event to `<prefix>/status`."""
        return self._publish(self.TOPIC_STATUS, status)

    def _publish(self, topic_suffix: str, payload: dict) -> bool:
        """Publish JSON to a topic, retrying up to max_retries on failure."""
        topic = f"{self.topic_prefix}/{topic_suffix}"
        message = json.dumps(payload, ensure_ascii=False)
        for _ in range(self.max_retries):
            info = self._client.publish(topic, message, qos=1)
            if getattr(info, "rc", 1) == 0:
                return True
        return False

    def disconnect(self) -> None:
        """Stop the network loop and disconnect from the broker."""
        self._client.loop_stop()
        self._client.disconnect()

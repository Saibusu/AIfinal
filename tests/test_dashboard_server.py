#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Tests for DashboardServer (SPEC-003).

Strategy: HTTP endpoints (/health, /, /video_feed, /ws connect) are exercised
with FastAPI's synchronous TestClient. The async ConnectionManager broadcast
logic is exercised with asyncio.run + fake WebSocket stubs, so no live broker,
camera, or pytest-asyncio plugin is required.
"""
from __future__ import annotations

import asyncio

import pytest
from fastapi.testclient import TestClient

from src.dashboard_server import ConnectionManager, DashboardServer


class FakeWebSocket:
    """Minimal async WebSocket stub recording sent text; can simulate disconnect."""

    def __init__(self, fail_on_send: bool = False) -> None:
        self.sent: list[str] = []
        self.accepted = False
        self.fail_on_send = fail_on_send

    async def accept(self) -> None:
        self.accepted = True

    async def send_text(self, text: str) -> None:
        if self.fail_on_send:
            raise RuntimeError("client gone")
        self.sent.append(text)


# --------------------------------------------------------------------------- #
# HTTP endpoints (sync TestClient)
# --------------------------------------------------------------------------- #
@pytest.fixture
def client() -> TestClient:
    server = DashboardServer(frame_source=lambda: None, fps_source=lambda: 18.5)
    return TestClient(server.app)


def test_health_endpoint(client: TestClient) -> None:
    resp = client.get("/health")
    assert resp.status_code == 200
    body = resp.json()
    assert body["status"] == "ok"
    assert body["fps"] == 18.5
    assert isinstance(body["uptime"], float)


def test_root_returns_html(client: TestClient) -> None:
    resp = client.get("/")
    assert resp.status_code == 200
    assert "text/html" in resp.headers["content-type"]


def test_video_feed_offline_returns_503(client: TestClient) -> None:
    # frame_source returns None → camera offline
    resp = client.get("/video_feed")
    assert resp.status_code == 503


def test_video_feed_streams_when_online() -> None:
    frames = iter([b"\xff\xd8jpegbytes\xff\xd9", None])
    server = DashboardServer(frame_source=lambda: next(frames))
    resp = TestClient(server.app).get("/video_feed")
    assert resp.status_code == 200
    assert "multipart/x-mixed-replace" in resp.headers["content-type"]
    assert b"--frame" in resp.content


def test_ws_sends_initial_status() -> None:
    server = DashboardServer(frame_source=lambda: None, fps_source=lambda: 12.0)
    with TestClient(server.app).websocket_connect("/ws") as ws:
        msg = ws.receive_json()
        assert msg["type"] == "fps"
        assert msg["value"] == 12.0


# --------------------------------------------------------------------------- #
# ConnectionManager broadcast logic (asyncio.run + fakes)
# --------------------------------------------------------------------------- #
def test_connect_calls_accept_and_registers() -> None:
    mgr = ConnectionManager()
    ws = FakeWebSocket()
    asyncio.run(mgr.connect(ws))
    assert ws.accepted is True
    assert ws in mgr.active


def test_broadcast_reaches_all_clients() -> None:
    mgr = ConnectionManager()
    a, b = FakeWebSocket(), FakeWebSocket()

    async def scenario() -> None:
        await mgr.connect(a)
        await mgr.connect(b)
        await mgr.broadcast({"type": "fps", "value": 20.0})

    asyncio.run(scenario())
    assert a.sent == b.sent
    assert '"type": "fps"' in a.sent[0]


def test_disconnected_client_removed_silently() -> None:
    mgr = ConnectionManager()
    good, dead = FakeWebSocket(), FakeWebSocket(fail_on_send=True)

    async def scenario() -> None:
        await mgr.connect(good)
        await mgr.connect(dead)
        await mgr.broadcast({"type": "fps", "value": 1.0})

    asyncio.run(scenario())
    assert dead not in mgr.active          # auto-pruned, no exception raised
    assert good in mgr.active
    assert len(good.sent) == 1             # surviving client still received


def test_disconnect_removes_client() -> None:
    mgr = ConnectionManager()
    ws = FakeWebSocket()
    asyncio.run(mgr.connect(ws))
    mgr.disconnect(ws)
    assert ws not in mgr.active
    # idempotent: disconnecting an unknown client must not raise
    mgr.disconnect(ws)


def test_broadcast_detection_event_format() -> None:
    server = DashboardServer(frame_source=lambda: None)
    ws = FakeWebSocket()
    result = {
        "class_id": 0,
        "class_name": "寶特瓶",
        "confidence": 0.87,
        "timestamp": 1749600000.0,
    }

    async def scenario() -> None:
        await server.manager.connect(ws)
        await server.broadcast_detection(result)

    asyncio.run(scenario())
    import json

    event = json.loads(ws.sent[0])
    assert event["type"] == "detection"
    assert event["class_id"] == 0
    assert event["class_name"] == "寶特瓶"
    assert event["confidence"] == 0.87
    assert event["timestamp"] == 1749600000.0

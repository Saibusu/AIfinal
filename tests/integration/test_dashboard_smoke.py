#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""On-device integration smoke test (SPEC-003/007, ADR-003 stage 5).

Runs on the self-hosted Yahboom runner against a live container. Skipped on
hosted CI / PC (no INTEGRATION_URL), so it never affects the unit coverage gate.
"""
from __future__ import annotations

import json
import os
import urllib.request

import pytest

_URL = os.environ.get("INTEGRATION_URL")

pytestmark = pytest.mark.skipif(
    not _URL, reason="INTEGRATION_URL not set — on-device only (Yahboom runner)"
)


def test_health_ok() -> None:
    with urllib.request.urlopen(f"{_URL}/health", timeout=10) as resp:  # noqa: S310
        assert resp.status == 200
        body = json.loads(resp.read())
    assert body["status"] == "ok"
    assert "fps" in body and "uptime" in body


def test_video_feed_reachable() -> None:
    # MJPEG stream: just confirm the endpoint responds (200 live, or 503 if the
    # camera is briefly unavailable — both prove the route is wired).
    req = urllib.request.Request(f"{_URL}/video_feed")  # noqa: S310
    try:
        with urllib.request.urlopen(req, timeout=10) as resp:  # noqa: S310
            assert resp.status == 200
            assert "multipart" in resp.headers.get("Content-Type", "")
    except urllib.error.HTTPError as exc:
        assert exc.code == 503  # camera offline is an accepted wired-but-no-camera state

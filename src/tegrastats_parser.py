#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Parse Yahboom `tegrastats` logs into structured rows / CSV (SPEC-006).

Pure text parsing with no Jetson dependency, so the optimisation-history and
§6 performance numbers can be produced on PC/CI from a `tegrastats.log` the
user captures on-device. Supports both POM (JetPack 5) and VDD (Orin) power
naming and an optional leading timestamp.
"""
from __future__ import annotations

import re

_TIMESTAMP_RE = re.compile(r"^(\d{2}-\d{2}-\d{4} \d{2}:\d{2}:\d{2})")
_RAM_RE = re.compile(r"RAM (\d+)/(\d+)MB")
_CPU_RE = re.compile(r"CPU \[([^\]]+)\]")
_CORE_RE = re.compile(r"(\d+)%@")
_GPU_RE = re.compile(r"GR3D_FREQ (\d+)%")
# Instantaneous input power: "<inst>/<avg>" after POM_5V_IN or VDD_IN.
_POWER_RE = re.compile(r"(?:POM_5V_IN|VDD_IN) (\d+)/\d+")

_CSV_HEADER = "index,timestamp,cpu_pct,gpu_pct,power_mw,ram_used_mb,ram_total_mb"


class TegrastatsParser:
    """Turns tegrastats text into rows, CSV, and an avg/max summary."""

    def parse_line(self, line: str) -> dict | None:
        """Parse one tegrastats line; return None for blank/unrelated lines.

        A line is considered valid only if it carries both RAM and CPU fields
        (the stable backbone of every tegrastats sample).
        """
        ram = _RAM_RE.search(line)
        cpu = _CPU_RE.search(line)
        if ram is None or cpu is None:
            return None

        cores = [int(p) for p in _CORE_RE.findall(cpu.group(1))]
        cpu_pct = round(sum(cores) / len(cores), 2) if cores else 0.0

        gpu = _GPU_RE.search(line)
        power = _POWER_RE.search(line)
        ts = _TIMESTAMP_RE.search(line)

        return {
            "timestamp": ts.group(1) if ts else None,
            "cpu_pct": cpu_pct,
            "gpu_pct": int(gpu.group(1)) if gpu else None,
            "power_mw": int(power.group(1)) if power else None,
            "ram_used_mb": int(ram.group(1)),
            "ram_total_mb": int(ram.group(2)),
        }

    def parse_text(self, text: str) -> list[dict]:
        """Parse multi-line tegrastats text, dropping noise/blank lines."""
        rows = []
        for line in text.splitlines():
            row = self.parse_line(line)
            if row is not None:
                rows.append(row)
        return rows

    def to_csv(self, rows: list[dict]) -> str:
        """Render rows as CSV (with header and a 0-based index column)."""
        lines = [_CSV_HEADER]
        for i, r in enumerate(rows):
            lines.append(
                f"{i},{r['timestamp'] or ''},{r['cpu_pct']},"
                f"{r['gpu_pct'] if r['gpu_pct'] is not None else ''},"
                f"{r['power_mw'] if r['power_mw'] is not None else ''},"
                f"{r['ram_used_mb']},{r['ram_total_mb']}"
            )
        return "\n".join(lines) + "\n"

    def summary(self, rows: list[dict]) -> dict:
        """Compute avg/max for CPU%, GPU%, and power over the rows."""
        if not rows:
            return {
                "samples": 0,
                "cpu_avg": 0.0, "cpu_max": 0.0,
                "gpu_avg": 0.0, "gpu_max": 0,
                "power_avg_mw": 0.0, "power_max_mw": 0,
            }
        cpu = [r["cpu_pct"] for r in rows]
        gpu = [r["gpu_pct"] for r in rows if r["gpu_pct"] is not None]
        power = [r["power_mw"] for r in rows if r["power_mw"] is not None]
        return {
            "samples": len(rows),
            "cpu_avg": round(sum(cpu) / len(cpu), 2),
            "cpu_max": max(cpu),
            "gpu_avg": round(sum(gpu) / len(gpu), 2) if gpu else 0.0,
            "gpu_max": max(gpu) if gpu else 0,
            "power_avg_mw": round(sum(power) / len(power), 2) if power else 0.0,
            "power_max_mw": max(power) if power else 0,
        }

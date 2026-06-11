#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Tests for TegrastatsParser (SPEC-006).

Pure text parsing — no Jetson hardware required. Sample lines mirror real
tegrastats output for both POM (JetPack 5) and VDD (Orin) power naming.
"""
from __future__ import annotations

from src.tegrastats_parser import TegrastatsParser

# Orin / VDD naming, one core offline ("off")
LINE_VDD = (
    "RAM 4190/7765MB (lfb 18x4MB) SWAP 0/3882MB CPU [10%@1479,20%@1479,off,30%@1479] "
    "EMC_FREQ 0% GR3D_FREQ 45% CPU@45C GPU@44C VDD_IN 4924/4800 VDD_SOC 1314/1314"
)
# JetPack 5 / POM naming, with leading timestamp
LINE_POM_TS = (
    "06-11-2026 14:00:01 RAM 2956/7765MB CPU [50%@1479,50%@1479] GR3D_FREQ 99% "
    "POM_5V_IN 3456/3400 POM_5V_GPU 124/120"
)


def test_parse_line_vdd_format() -> None:
    row = TegrastatsParser().parse_line(LINE_VDD)
    assert row is not None
    assert row["cpu_pct"] == 20.0          # (10+20+30)/3, off skipped
    assert row["gpu_pct"] == 45
    assert row["power_mw"] == 4924         # instantaneous, not the /4800 avg
    assert row["ram_used_mb"] == 4190
    assert row["ram_total_mb"] == 7765
    assert row["timestamp"] is None


def test_parse_line_pom_format() -> None:
    row = TegrastatsParser().parse_line(LINE_POM_TS)
    assert row is not None
    assert row["power_mw"] == 3456
    assert row["gpu_pct"] == 99


def test_parse_line_skips_off_cores() -> None:
    row = TegrastatsParser().parse_line(LINE_VDD)
    assert row["cpu_pct"] == 20.0


def test_parse_line_all_off_cores() -> None:
    line = "RAM 100/7765MB CPU [off,off] GR3D_FREQ 0% VDD_IN 1000/1000"
    row = TegrastatsParser().parse_line(line)
    assert row["cpu_pct"] == 0.0


def test_parse_line_with_timestamp() -> None:
    row = TegrastatsParser().parse_line(LINE_POM_TS)
    assert row["timestamp"] == "06-11-2026 14:00:01"


def test_parse_line_noise_returns_none() -> None:
    assert TegrastatsParser().parse_line("") is None
    assert TegrastatsParser().parse_line("   ") is None
    assert TegrastatsParser().parse_line("some unrelated log line") is None


def test_parse_line_missing_power() -> None:
    line = "RAM 100/7765MB CPU [25%@1479] GR3D_FREQ 5%"
    row = TegrastatsParser().parse_line(line)
    assert row["power_mw"] is None
    assert row["cpu_pct"] == 25.0


def test_parse_text_filters_noise() -> None:
    text = "\n".join(["", LINE_VDD, "garbage", LINE_POM_TS, "   "])
    rows = TegrastatsParser().parse_text(text)
    assert len(rows) == 2


def test_to_csv_header_and_rows() -> None:
    parser = TegrastatsParser()
    rows = parser.parse_text("\n".join([LINE_VDD, LINE_POM_TS]))
    csv = parser.to_csv(rows)
    lines = csv.strip().splitlines()
    assert lines[0] == "index,timestamp,cpu_pct,gpu_pct,power_mw,ram_used_mb,ram_total_mb"
    assert len(lines) == 3                 # header + 2 rows
    assert lines[1].startswith("0,")
    assert lines[2].startswith("1,")


def test_summary_avg_max() -> None:
    parser = TegrastatsParser()
    rows = parser.parse_text("\n".join([LINE_VDD, LINE_POM_TS]))
    s = parser.summary(rows)
    assert s["samples"] == 2
    assert s["cpu_avg"] == 35.0            # (20 + 50) / 2
    assert s["cpu_max"] == 50.0
    assert s["gpu_max"] == 99
    assert s["power_max_mw"] == 4924
    assert s["power_avg_mw"] == 4190       # (4924 + 3456) / 2


def test_summary_empty() -> None:
    s = TegrastatsParser().summary([])
    assert s["samples"] == 0
    assert s["cpu_avg"] == 0.0
    assert s["power_max_mw"] == 0

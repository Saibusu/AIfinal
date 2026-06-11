#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""CLI shim: tegrastats.log -> utilization.csv + summary (SPEC-006).

Run on PC/CI after capturing a log on Yahboom (runbook §5):

    sudo tegrastats --interval 1000 --logfile tegrastats.log   # on device
    python scripts/parse_tegrastats.py tegrastats.log -o utilization.csv

Parsing logic lives in `src/tegrastats_parser.py` (unit-tested); this file is
only argument plumbing.
"""
from __future__ import annotations

import argparse
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from src.tegrastats_parser import TegrastatsParser  # noqa: E402


def main(argv: list[str] | None = None) -> int:  # pragma: no cover - CLI plumbing
    ap = argparse.ArgumentParser(description="Parse tegrastats.log to utilization.csv")
    ap.add_argument("logfile", help="path to tegrastats.log")
    ap.add_argument("-o", "--output", default="utilization.csv", help="output CSV path")
    args = ap.parse_args(argv)

    parser = TegrastatsParser()
    rows = parser.parse_text(Path(args.logfile).read_text(encoding="utf-8"))
    Path(args.output).write_text(parser.to_csv(rows), encoding="utf-8")

    s = parser.summary(rows)
    print(f"samples={s['samples']}  "
          f"CPU avg/max={s['cpu_avg']}/{s['cpu_max']}%  "
          f"GPU avg/max={s['gpu_avg']}/{s['gpu_max']}%  "
          f"power avg/max={s['power_avg_mw']}/{s['power_max_mw']}mW")
    print(f"wrote {args.output}")
    return 0


if __name__ == "__main__":  # pragma: no cover
    raise SystemExit(main())

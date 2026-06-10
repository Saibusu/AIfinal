#!/usr/bin/env python3
# Copyright (c) 2026 李軒杰, 黃義鈞
# Datung University — I4210 AI實務專題
"""Pytest root conftest — ensures project root is on sys.path so `import src` works."""
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent))

#!/usr/bin/env python3
"""Run live plot-catalog boundary tests. Requires TARGET_API_URL. Exit 78 if blocked."""
from __future__ import annotations

import os
import sys
import unittest
from pathlib import Path

if not os.getenv("TARGET_API_URL") and not os.getenv("DATA_VIZ_URL"):
    print("blocked: TARGET_API_URL required", file=sys.stderr)
    raise SystemExit(78)

root = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(root / "src"))
loader = unittest.TestLoader()
suite = loader.discover(str(root / "tests"), pattern="test_plot_catalog_live.py")
result = unittest.TextTestRunner(verbosity=2).run(suite)
raise SystemExit(0 if result.wasSuccessful() else 1)

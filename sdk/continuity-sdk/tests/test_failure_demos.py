"""Failure experiment tests."""

from __future__ import annotations

import importlib.util
import sys
from pathlib import Path

SDK_ROOT = Path(__file__).resolve().parents[1]
if str(SDK_ROOT) not in sys.path:
    sys.path.insert(0, str(SDK_ROOT))


def _load_harness(rel_path: str):
    path = SDK_ROOT / rel_path
    spec = importlib.util.spec_from_file_location(path.stem, path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    return mod


def test_missing_crr_failure() -> None:
    mod = _load_harness("experiments/failure/missing_crr/harness.py")
    assert mod.run()["passed"] is True

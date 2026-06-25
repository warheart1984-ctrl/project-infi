"""CRR removal demo — continuity fails without calibration receipts."""

from __future__ import annotations

from typing import Any


def run() -> dict[str, Any]:
    import importlib.util
    import sys
    from pathlib import Path

    path = Path(__file__).resolve().parents[1] / "failure" / "missing_crr" / "harness.py"
    spec = importlib.util.spec_from_file_location("missing_crr", path)
    assert spec and spec.loader
    mod = importlib.util.module_from_spec(spec)
    sys.modules["missing_crr"] = mod
    spec.loader.exec_module(mod)
    result = mod.run()
    return {**result, "question": "Does continuity collapse when CRR-1 is removed from lineage?"}

#!/usr/bin/env python3
"""Gate: fresh Wave 13 calibration report."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_forecast_calibration_engine import (  # noqa: E402
    calibration_stale,
    load_calibration_report,
)
from tools.linguistic_genome_lib import load_json  # noqa: E402


def main() -> int:
    root = _ROOT
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    mode = "observe"
    if reg_path.is_file():
        mode = load_json(reg_path).get("policy_mode", "observe")

    errors: list[str] = []
    warnings: list[str] = []

    if calibration_stale(root):
        msg = "calibration stale or missing (run: make linguistic-calibration-cycle)"
        if mode == "enforce":
            errors.append(msg)
        else:
            warnings.append(msg)
    else:
        report = load_calibration_report(root)
        if report and mode == "enforce":
            miss_rate = float((report.get("metrics") or {}).get("miss_rate", 0))
            if miss_rate > 0.25:
                warnings.append(f"high miss_rate {miss_rate} — review weight_adjustments")

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print(f"linguistic-calibration-gate: FAIL ({len(errors)} error(s))")
        return 1

    reg = load_json(reg_path) if reg_path.is_file() else {}
    last = reg.get("last_calibration_at", "unknown")
    print(f"linguistic-calibration-gate: PASS (last_calibration_at={last})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

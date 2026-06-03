#!/usr/bin/env python3
"""Gate: fresh Wave 12 forecast and enforce-mode preemptive playbook coverage."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_drift_forecast_engine import (  # noqa: E402
    forecast_stale,
    load_forecast_report,
    preemptive_playbook_exists,
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

    if forecast_stale(root):
        msg = "forecast stale or missing (run: make linguistic-predictive-cycle)"
        if mode == "enforce":
            errors.append(msg)
        else:
            warnings.append(msg)
    else:
        report = load_forecast_report(root)
        if report and mode == "enforce":
            for entry in report.get("forecasts") or []:
                if entry.get("predicted_band") == "high":
                    gene = entry.get("gene", "")
                    if gene and not preemptive_playbook_exists(gene, root):
                        errors.append(f"{gene}: missing preemptive playbook (predicted high)")

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print(f"linguistic-predictive-gate: FAIL ({len(errors)} error(s))")
        return 1

    reg = load_json(reg_path) if reg_path.is_file() else {}
    last = reg.get("last_predictive_cycle_at", "unknown")
    print(f"linguistic-predictive-gate: PASS (last_predictive_cycle_at={last})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

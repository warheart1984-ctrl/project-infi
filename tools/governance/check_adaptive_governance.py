#!/usr/bin/env python3
"""Tier 5 adaptive governance gate."""

from __future__ import annotations

import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.adaptive_engine import AdaptiveEngine
from src.governance_organs.genome_engine import GenomeEngine


def main() -> int:
    GenomeEngine.reload(_ROOT)
    reg = GenomeEngine.registry()
    errors: list[str] = []
    pilot = reg.genomes.get("recipe_module_organ")
    if not pilot:
        errors.append("recipe_module_organ genome missing for Tier 5 pilot")
    else:
        gov = pilot.get("governance") or {}
        if not gov.get("operator_lanes"):
            errors.append("recipe_module_organ missing operator_lanes")
        if not gov.get("contextual_gates"):
            errors.append("recipe_module_organ missing contextual_gates")
        for entry in gov.get("invariants") or []:
            if isinstance(entry, dict) and not entry.get("maturity"):
                errors.append("recipe_module_organ invariant missing maturity")

    contract = _ROOT / "docs/contracts/AAIS_ADAPTIVE_GOVERNANCE.md"
    if not contract.is_file():
        errors.append("AAIS_ADAPTIVE_GOVERNANCE.md missing")

    if errors:
        for err in errors:
            print(f"[tier5-gate] FAIL: {err}")
        return 1

    report = AdaptiveEngine(_ROOT).health_check()
    health_path = _ROOT / ".runtime/governance/tier5_health.json"
    if not health_path.is_file():
        print("[tier5-gate] FAIL: tier5_health.json not written")
        return 1

    if not report.get("adaptive_lanes_awakened"):
        errors.append("adaptive lanes not awakened — run Tier5Governance.wake_lanes()")
    if int(report.get("adaptive_lane_count") or 0) < 1:
        errors.append("adaptive_lane_count is zero")

    if errors:
        for err in errors:
            print(f"[tier5-gate] FAIL: {err}")
        return 1

    print(
        f"[tier5-gate] PASS: {report['genome_count']} genomes; "
        f"{report.get('adaptive_lane_count', 0)} adaptive lane(s); health at {health_path}"
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

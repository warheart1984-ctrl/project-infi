#!/usr/bin/env python3
"""Gate: fresh Wave 11 cycle report and enforce-mode playbook coverage."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_governance_cycle_engine import (  # noqa: E402
    LinguisticGovernanceCycleEngine,
    load_cycle_policy,
)
from tools.linguistic_genome_lib import load_json  # noqa: E402


def main() -> int:
    root = _ROOT
    engine = LinguisticGovernanceCycleEngine(root)
    policy = load_cycle_policy(root)
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    mode = "observe"
    if reg_path.is_file():
        mode = load_json(reg_path).get("policy_mode", "observe")

    errors: list[str] = []
    warnings: list[str] = []

    if engine.cycle_stale():
        msg = "no fresh cycle report (run: make linguistic-governance-cycle)"
        if mode == "enforce":
            errors.append(msg)
        else:
            warnings.append(msg)
    else:
        cycle = engine.load_latest_cycle()
        if cycle:
            m = cycle.get("metrics") or {}
            if mode == "enforce" and int(m.get("high_count", 0)) > 0:
                cov = float(m.get("playbook_coverage_pct", 100))
                if cov < 100:
                    errors.append(
                        f"enforce: playbook coverage {cov}% for high-drift genes"
                    )

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print(f"linguistic-governance-cycle-gate: FAIL ({len(errors)} error(s))")
        return 1

    reg = load_json(reg_path) if reg_path.is_file() else {}
    last = reg.get("last_cycle_at", "unknown")
    print(f"linguistic-governance-cycle-gate: PASS (last_cycle_at={last})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

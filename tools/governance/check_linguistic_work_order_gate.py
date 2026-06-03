#!/usr/bin/env python3
"""Gate: top-N urgent work orders must not stay pending beyond SLA."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_governance_attestation_engine import (  # noqa: E402
    load_cadence_policy,
)
from src.governance_organs.linguistic_governance_work_order_engine import (  # noqa: E402
    pending_urgent_stale,
)
from tools.linguistic_genome_lib import load_json  # noqa: E402


def main() -> int:
    root = _ROOT
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    mode = "observe"
    if reg_path.is_file():
        mode = load_json(reg_path).get("policy_mode", "observe")

    policy = load_cadence_policy(root)
    max_days = int(policy.get("max_pending_work_order_days", 14))
    stale = pending_urgent_stale(root, top_n=5, max_pending_days=max_days)

    errors: list[str] = []
    warnings: list[str] = []
    for item in stale:
        msg = (
            f"work order {item['gene']!r} pending {item['age_days']}d "
            f"(max {max_days}d)"
        )
        if mode == "enforce":
            errors.append(msg)
        else:
            warnings.append(msg)

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print(f"linguistic-work-order-gate: FAIL ({len(errors)} error(s))")
        return 1

    print(f"linguistic-work-order-gate: PASS (checked top-5, max_pending_days={max_days})")
    return 0


if __name__ == "__main__":
    sys.exit(main())

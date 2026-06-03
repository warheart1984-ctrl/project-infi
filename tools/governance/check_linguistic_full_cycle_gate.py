#!/usr/bin/env python3
"""Gate: fresh Wave 13–14 full governance cycle report."""

from __future__ import annotations

import sys
from datetime import datetime, timezone
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_governance_attestation_engine import (  # noqa: E402
    load_cadence_policy,
)
from tools.linguistic_genome_lib import load_json  # noqa: E402


def _full_cycle_stale(root: Path, max_days: int) -> bool:
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    if not reg_path.is_file():
        return True
    reg = load_json(reg_path)
    rel = reg.get("last_full_cycle_report")
    if not rel:
        return True
    path = root / rel
    if not path.is_file():
        return True
    data = load_json(path)
    gen = data.get("generated_at", "")
    if not gen:
        return True
    try:
        ts = datetime.fromisoformat(gen.replace("Z", "+00:00"))
    except ValueError:
        return True
    age = (datetime.now(timezone.utc) - ts).total_seconds() / 86400
    return age > max_days


def main() -> int:
    root = _ROOT
    reg_path = root / "governance/meta_linguistic_registry.v1.json"
    mode = "observe"
    if reg_path.is_file():
        mode = load_json(reg_path).get("policy_mode", "observe")

    policy = load_cadence_policy(root)
    max_days = int(policy.get("max_full_cycle_age_days", 7))
    errors: list[str] = []
    warnings: list[str] = []

    if _full_cycle_stale(root, max_days):
        msg = f"full cycle stale or missing (max {max_days}d; run: make linguistic-full-governance-cycle)"
        if mode == "enforce":
            errors.append(msg)
        else:
            warnings.append(msg)

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print(f"linguistic-full-cycle-gate: FAIL ({len(errors)} error(s))")
        return 1

    print("linguistic-full-cycle-gate: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

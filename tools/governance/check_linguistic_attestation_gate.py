#!/usr/bin/env python3
"""Gate: cadence SLA for attestation and full governance cycle."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_drift_forecast_engine import forecast_stale  # noqa: E402
from src.governance_organs.linguistic_forecast_calibration_engine import (  # noqa: E402
    calibration_stale,
)
from src.governance_organs.linguistic_governance_attestation_engine import (  # noqa: E402
    attestation_stale,
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
    from datetime import datetime, timezone

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
    errors: list[str] = []
    warnings: list[str] = []

    checks = [
        ("attestation", attestation_stale(root), "run: make linguistic-governance-attestation"),
        (
            "full_cycle",
            _full_cycle_stale(root, int(policy.get("max_full_cycle_age_days", 7))),
            "run: make linguistic-full-governance-cycle",
        ),
        ("forecast", forecast_stale(root), "refresh forecast via predictive cycle"),
        ("calibration", calibration_stale(root), "run: make linguistic-calibration-cycle"),
    ]

    for label, stale, hint in checks:
        if not stale:
            continue
        msg = f"{label} stale or missing ({hint})"
        if mode == "enforce" and label in ("attestation", "full_cycle"):
            errors.append(msg)
        else:
            warnings.append(msg)

    for w in warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if errors:
        print(f"linguistic-attestation-gate: FAIL ({len(errors)} error(s))")
        return 1

    print("linguistic-attestation-gate: PASS")
    return 0


if __name__ == "__main__":
    sys.exit(main())

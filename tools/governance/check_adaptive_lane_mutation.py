#!/usr/bin/env python3
"""Adaptive lane mutation gate — verifies MP-ALO-001 golden path."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.mutation_engine import MutationEngine

REQUIRED_PATHS = (
    _ROOT / "docs/_future/mutations/MP-ALO-001.md",
    _ROOT / "schemas/deltas/adaptive_lane_organ_MP-ALO-001.json",
    _ROOT / "tests/test_adaptive_lane_organ_mutation_MP_ALO_001.py",
    _ROOT / "docs/proof/platform/ADAPTIVE_LANE_MP-ALO-001_PROOF.md",
)


def main() -> int:
    missing = [path.relative_to(_ROOT) for path in REQUIRED_PATHS if not path.is_file()]
    if missing:
        for item in missing:
            print(f"[adaptive-lane-mutation-gate] FAIL: missing {item}")
        return 1

    engine = MutationEngine(_ROOT)
    result = engine.verify("adaptive_lane_organ", "MP-ALO-001")
    if not result.passed:
        for failure in result.failures:
            print(f"[adaptive-lane-mutation-gate] FAIL: {failure}")
        return 1

    print("[adaptive-lane-mutation-gate] PASS: MP-ALO-001 verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

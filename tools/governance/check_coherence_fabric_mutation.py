#!/usr/bin/env python3
"""Coherence fabric mutation gate — verifies MP-OCCF-001 golden path."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.mutation_engine import MutationEngine

REQUIRED_PATHS = (
    _ROOT / "docs/_future/mutations/MP-OCCF-001.md",
    _ROOT / "schemas/deltas/operator_cognition_coherence_fabric_MP-OCCF-001.json",
    _ROOT / "tests/test_operator_cognition_coherence_fabric_mutation_MP_OCCF_001.py",
    _ROOT
    / "docs/proof/platform/OPERATOR_COGNITION_COHERENCE_FABRIC_MP-OCCF-001_PROOF.md",
)


def main() -> int:
    missing = [path.relative_to(_ROOT) for path in REQUIRED_PATHS if not path.is_file()]
    if missing:
        for item in missing:
            print(f"[coherence-fabric-mutation-gate] FAIL: missing {item}")
        return 1

    engine = MutationEngine(_ROOT)
    result = engine.verify("operator_cognition_coherence_fabric", "MP-OCCF-001")
    if not result.passed:
        for failure in result.failures:
            print(f"[coherence-fabric-mutation-gate] FAIL: {failure}")
        return 1

    proc = subprocess.run(
        [sys.executable, "-m", "pytest", str(REQUIRED_PATHS[2]), "-q"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        detail = (proc.stdout or proc.stderr or "").strip().splitlines()
        suffix = detail[-1] if detail else "mutation tests failed"
        print(f"[coherence-fabric-mutation-gate] FAIL: {suffix}")
        return 1

    print("[coherence-fabric-mutation-gate] PASS: MP-OCCF-001 verify")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

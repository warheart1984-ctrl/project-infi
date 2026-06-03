#!/usr/bin/env python3
"""Release 26.2 Linguistic Operational Closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOFS = (
    _ROOT / "docs/proof/platform/LINGUISTIC_OPERATIONAL_CLOSURE_V1_PROOF.md",
    _ROOT / "docs/proof/platform/LINGUISTIC_GOVERNANCE_DAY_ORGAN_V1_PROOF.md",
)
ALT26_GENES = (
    "linguistic_governance_day_organ",
    "linguistic_work_order_history_organ",
    "linguistic_attestation_history_organ",
)
ENGINE_TESTS = (
    "tests/test_linguistic_governance_day_engine.py",
    "tests/test_linguistic_work_order_history.py",
)


def main() -> int:
    for proof in PROOFS:
        if not proof.is_file():
            print(f"[alt26-closure-gate] FAIL: missing {proof.relative_to(_ROOT)}")
            return 1
    tests = [f"tests/test_{g}.py" for g in ALT26_GENES] + list(ENGINE_TESTS)
    proc = subprocess.run(
        [sys.executable, "-m", "pytest", *tests, "-q"],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        return 1
    schema = _ROOT / "schemas/operator_cognition_coherence_fabric.v1.21.json"
    if not schema.is_file():
        print("[alt26-closure-gate] FAIL: missing coherence v1.21 schema")
        return 1
    print("[alt26-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

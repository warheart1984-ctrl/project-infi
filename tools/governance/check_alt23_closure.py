#!/usr/bin/env python3
"""Release 23.2 Predictive Linguistic Cycle closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOFS = (
    _ROOT / "docs/proof/platform/PREDICTIVE_LINGUISTIC_CYCLE_V1_PROOF.md",
    _ROOT / "docs/proof/platform/LINGUISTIC_DRIFT_FORECAST_ORGAN_V1_PROOF.md",
    _ROOT / "docs/proof/platform/LINGUISTIC_CLOSED_LOOP_FABRIC_ORGAN_V1_PROOF.md",
)
ALT23_GENES = (
    "linguistic_drift_forecast_organ",
    "linguistic_preemptive_remediation_organ",
    "linguistic_predictive_governance_organ",
    "linguistic_predictive_cycle_history_organ",
    "linguistic_governance_cycle_organ",
    "linguistic_governance_cycle_history_organ",
    "linguistic_forecast_consumption_organ",
    "linguistic_cycle_optimization_organ",
    "linguistic_closed_loop_fabric_organ",
)


def main() -> int:
    for proof in PROOFS:
        if not proof.is_file():
            print(f"[alt23-closure-gate] FAIL: missing {proof.relative_to(_ROOT)}")
            return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{g}.py" for g in ALT23_GENES],
            "-q",
        ],
        cwd=_ROOT,
        capture_output=True,
        text=True,
        check=False,
    )
    if proc.returncode != 0:
        print(proc.stdout)
        print(proc.stderr)
        return 1
    print("[alt23-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

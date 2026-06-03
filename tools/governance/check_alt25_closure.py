#!/usr/bin/env python3
"""Release 25.2 Governed Linguistic Lifecycle closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOFS = (
    _ROOT / "docs/proof/platform/GOVERNED_LINGUISTIC_LIFECYCLE_V1_PROOF.md",
    _ROOT / "docs/proof/platform/LINGUISTIC_GOVERNED_LIFECYCLE_FABRIC_ORGAN_V1_PROOF.md",
)
ALT25_GENES = (
    "linguistic_forecast_archive_organ",
    "linguistic_drift_report_organ",
    "linguistic_governance_work_order_organ",
    "linguistic_governance_cadence_organ",
    "linguistic_forecast_calibration_report_organ",
    "linguistic_full_governance_cycle_history_organ",
    "meta_linguistic_registry_organ",
    "linguistic_subsystem_promotion_organ",
    "linguistic_governed_lifecycle_fabric_organ",
)
ENGINE_TESTS = (
    "tests/test_linguistic_forecast_archive.py",
    "tests/test_linguistic_governance_work_order_engine.py",
)


def main() -> int:
    for proof in PROOFS:
        if not proof.is_file():
            print(f"[alt25-closure-gate] FAIL: missing {proof.relative_to(_ROOT)}")
            return 1
    tests = [f"tests/test_{g}.py" for g in ALT25_GENES] + list(ENGINE_TESTS)
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
    print("[alt25-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

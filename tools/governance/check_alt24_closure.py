#!/usr/bin/env python3
"""Release 24.2 Attested Linguistic Closed-Loop closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

PROOFS = (
    _ROOT / "docs/proof/platform/ATTESTED_LINGUISTIC_CLOSED_LOOP_V1_PROOF.md",
)
ALT24_GENES = (
    "linguistic_forecast_calibration_organ",
    "linguistic_governance_queue_organ",
    "linguistic_full_governance_cycle_organ",
    "linguistic_governance_attestation_organ",
)


def main() -> int:
    for proof in PROOFS:
        if not proof.is_file():
            print(f"[alt24-closure-gate] FAIL: missing {proof.relative_to(_ROOT)}")
            return 1

    attestation = _ROOT / "governance/linguistic_governance_attestation.v1.json"
    if not attestation.is_file():
        print("[alt24-closure-gate] FAIL: missing linguistic_governance_attestation.v1.json")
        return 1

    from src.operator_cognition_coherence_fabric import build_coherence_fabric_status

    fabric = build_coherence_fabric_status(root=_ROOT)
    version = fabric.get("operator_cognition_coherence_fabric_version")
    if version not in {
        "operator_cognition_coherence_fabric.v1.19",
        "operator_cognition_coherence_fabric.v1.20",
        "operator_cognition_coherence_fabric.v1.21",
    }:
        print(
            f"[alt24-closure-gate] FAIL: coherence fabric must be v1.19–v1.21 (got {version})"
        )
        return 1
    for key in (
        "linguistic_calibration_layer",
        "linguistic_governance_queue_layer",
        "linguistic_attestation_layer",
    ):
        if len(fabric.get(key) or []) != 3:
            print(f"[alt24-closure-gate] FAIL: expected 3 entries in {key}")
            return 1
    if not fabric.get("linguistic_attested_closed_loop_aligned"):
        print("[alt24-closure-gate] FAIL: linguistic_attested_closed_loop_aligned is false")
        return 1

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{g}.py" for g in ALT24_GENES],
            "tests/test_linguistic_forecast_archive.py",
            "tests/test_linguistic_governance_work_order_engine.py",
            "tests/test_linguistic_governance_attestation_engine.py",
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
    print("[alt24-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

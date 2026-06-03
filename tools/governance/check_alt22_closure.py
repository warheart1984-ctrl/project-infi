#!/usr/bin/env python3
"""Release 22.2 Meta-Linguistic Governance closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOFS = (
    _ROOT / "docs/proof/platform/META_LINGUISTIC_GOVERNANCE_V1_PROOF.md",
    _ROOT / "docs/proof/platform/NAMING_GENOME_ORGAN_V1_PROOF.md",
    _ROOT / "docs/proof/platform/LINGUISTIC_CASCADE_ORGAN_V1_PROOF.md",
)
ALT22_GENES = (
    "naming_protocol_organ",
    "naming_genome_organ",
    "linguistic_mutation_organ",
    "mythic_engineering_translator_organ",
    "linguistic_drift_predictor_organ",
    "linguistic_lineage_viz_organ",
    "linguistic_remediation_organ",
    "linguistic_cascade_organ",
    "meta_linguistic_governance_organ",
)


def main() -> int:
    for proof in PROOFS:
        if not proof.is_file():
            print(f"[alt22-closure-gate] FAIL: missing {proof.relative_to(_ROOT)}")
            return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{g}.py" for g in ALT22_GENES],
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
    print("[alt22-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

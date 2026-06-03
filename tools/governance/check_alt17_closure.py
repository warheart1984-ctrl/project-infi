#!/usr/bin/env python3
"""Alt-17.2 Authority & Protocol Integrity closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
INTEGRITY_PROOF = _ROOT / "docs/proof/platform/AUTHORITY_PROTOCOL_INTEGRITY_V1_PROOF.md"
PROTOCOL_PROOF = _ROOT / "docs/proof/platform/JARVIS_PROTOCOL_ORGAN_V1_PROOF.md"
OUTPUT_PROOF = _ROOT / "docs/proof/platform/OUTPUT_INTEGRITY_ORGAN_V1_PROOF.md"

ALT17_GENES = (
    "jarvis_protocol_organ",
    "reasoning_contract_organ",
    "jarvis_reasoning_lane_organ",
    "conversation_memory_organ",
    "continuity_substrate_organ",
    "jarvis_operator_organ",
    "anti_drift_organ",
    "prompt_assembly_organ",
    "output_integrity_organ",
)


def main() -> int:
    errors: list[str] = []
    for proof in (INTEGRITY_PROOF, PROTOCOL_PROOF, OUTPUT_PROOF):
        if not proof.is_file():
            errors.append(f"missing proof: {proof.relative_to(_ROOT)}")

    if errors:
        for err in errors:
            print(f"[alt17-closure-gate] FAIL: {err}")
        return 1

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT17_GENES],
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
        print("[alt17-closure-gate] FAIL: organ pytest")
        return 1
    print("[alt17-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

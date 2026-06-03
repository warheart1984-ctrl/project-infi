#!/usr/bin/env python3
"""Alt-15.2 Nova lobe and voice closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
NOVA_LOBE_PROOF = _ROOT / "docs/proof/cognitive_runtime/NOVA_LOBE_V1_PROOF.md"
PROJECTION_PROOF = _ROOT / "docs/proof/cognitive_runtime/COHERENCE_PROJECTION_ORGAN_V1_PROOF.md"
SPEAKING_PROOF = _ROOT / "docs/proof/cognitive_runtime/SPEAKING_RUNTIME_ORGAN_V1_PROOF.md"

ALT15_GENES = (
    "reasoning_executive_organ",
    "attention_organ",
    "coherence_projection_organ",
    "deliberation_organ",
    "planning_organ",
    "cortex_arcs_organ",
    "cognitive_execution_organ",
    "speaking_runtime_organ",
    "nova_face_organ",
)


def main() -> int:
    errors: list[str] = []
    for proof in (NOVA_LOBE_PROOF, PROJECTION_PROOF, SPEAKING_PROOF):
        if not proof.is_file():
            errors.append(f"missing proof: {proof.relative_to(_ROOT)}")

    if errors:
        for err in errors:
            print(f"[alt15-closure-gate] FAIL: {err}")
        return 1

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT15_GENES],
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
        print("[alt15-closure-gate] FAIL: organ pytest")
        return 1
    print("[alt15-closure-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

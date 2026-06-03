#!/usr/bin/env python3
"""Alt-16.2 Factory & Kinetic closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
FACTORY_KINETIC_PROOF = _ROOT / "docs/proof/platform/FACTORY_KINETIC_V1_PROOF.md"
AI_FACTORY_PROOF = _ROOT / "docs/proof/ai_factory/AI_FACTORY_ORGAN_V1_PROOF.md"
SLINGSHOT_PROOF = _ROOT / "docs/proof/platform/SLINGSHOT_ORGAN_V1_PROOF.md"

ALT16_GENES = (
    "ai_factory_organ",
    "cogos_runtime_bridge_organ",
    "wolf_rehydration_organ",
    "forge_contractor_organ",
    "forge_eval_organ",
    "evolve_engine_organ",
    "slingshot_organ",
    "operator_workbench_organ",
    "workflow_shell_organ",
)


def main() -> int:
    errors: list[str] = []
    for proof in (FACTORY_KINETIC_PROOF, AI_FACTORY_PROOF, SLINGSHOT_PROOF):
        if not proof.is_file():
            errors.append(f"missing proof: {proof.relative_to(_ROOT)}")

    if errors:
        for err in errors:
            print(f"[alt16-closure-gate] FAIL: {err}")
        return 1

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{gene}.py" for gene in ALT16_GENES],
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
        print("[alt16-closure-gate] FAIL: organ pytest")
        return 1
    print("[alt16-closure-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

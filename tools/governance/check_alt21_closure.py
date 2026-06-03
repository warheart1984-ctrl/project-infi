#!/usr/bin/env python3
"""Release 21.2 Creative Runtime V9/V10 closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOFS = (
    _ROOT / "docs/proof/platform/CREATIVE_RUNTIME_V9_V10_V1_PROOF.md",
    _ROOT / "docs/proof/platform/CREATIVE_CORE_RUNTIME_ORGAN_V1_PROOF.md",
    _ROOT / "docs/proof/platform/V9_RUNTIME_ORGAN_V1_PROOF.md",
)
ALT21_GENES = (
    "creative_core_runtime_organ",
    "v9_core_organ",
    "v9_runtime_organ",
    "v10_core_organ",
    "v10_runtime_organ",
    "v10_action_engine_organ",
    "creative_capability_bridge_organ",
    "creative_operator_handoff_organ",
    "creative_console_interface_organ",
)


def main() -> int:
    for proof in PROOFS:
        if not proof.is_file():
            print(f"[alt21-closure-gate] FAIL: missing {proof.relative_to(_ROOT)}")
            return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{g}.py" for g in ALT21_GENES],
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
    print("[alt21-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Alt-19.2 Operator Product Shell closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOFS = (
    _ROOT / "docs/proof/platform/OPERATOR_PRODUCT_SHELL_V1_PROOF.md",
    _ROOT / "docs/proof/platform/LAUNCHER_ORGAN_V1_PROOF.md",
    _ROOT / "docs/proof/platform/API_GATEWAY_ORGAN_V1_PROOF.md",
)
ALT19_GENES = (
    "launcher_organ",
    "aais_doctor_organ",
    "workflow_runtime_organ",
    "jarvis_console_surface_organ",
    "memory_bank_surface_organ",
    "dashboard_surface_organ",
    "nova_landing_surface_organ",
    "aais_composed_runtime_organ",
    "api_gateway_organ",
)


def main() -> int:
    for proof in PROOFS:
        if not proof.is_file():
            print(f"[alt19-closure-gate] FAIL: missing {proof.relative_to(_ROOT)}")
            return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{g}.py" for g in ALT19_GENES],
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
    print("[alt19-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

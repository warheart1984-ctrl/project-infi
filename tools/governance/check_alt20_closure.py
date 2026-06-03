#!/usr/bin/env python3
"""Release 20.2 Operator Workspace & Extended Interfaces closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOFS = (
    _ROOT / "docs/proof/platform/OPERATOR_WORKSPACE_INTERFACES_V1_PROOF.md",
    _ROOT / "docs/proof/platform/MEMORY_SMITH_ORGAN_V1_PROOF.md",
    _ROOT / "docs/proof/platform/WORKFLOW_INTERFACES_ORGAN_V1_PROOF.md",
)
ALT20_GENES = (
    "memory_smith_organ",
    "operator_workspace_organ",
    "jarvis_runs_organ",
    "state_hygiene_organ",
    "blueprint_posture_organ",
    "workflow_interfaces_organ",
    "platform_console_interfaces_organ",
    "operator_console_interface_organ",
    "nova_workspace_interface_organ",
)


def main() -> int:
    for proof in PROOFS:
        if not proof.is_file():
            print(f"[alt20-closure-gate] FAIL: missing {proof.relative_to(_ROOT)}")
            return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{g}.py" for g in ALT20_GENES],
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
    print("[alt20-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

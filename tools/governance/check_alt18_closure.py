#!/usr/bin/env python3
"""Alt-18.2 Project Infi Law closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOFS = (
    _ROOT / "docs/proof/platform/PROJECT_INFI_LAW_V1_PROOF.md",
    _ROOT / "docs/proof/platform/CHAT_TURN_GOVERNANCE_ORGAN_V1_PROOF.md",
    _ROOT / "docs/proof/platform/GOVERNANCE_LAYER_ORGAN_V1_PROOF.md",
)
ALT18_GENES = (
    "project_infi_state_machine_organ",
    "project_infi_law_organ",
    "run_ledger_binding_organ",
    "chat_turn_governance_organ",
    "aais_ul_substrate_organ",
    "aris_integration_organ",
    "governance_layer_organ",
    "security_protocol_organ",
    "system_guard_organ",
)


def main() -> int:
    for proof in PROOFS:
        if not proof.is_file():
            print(f"[alt18-closure-gate] FAIL: missing {proof.relative_to(_ROOT)}")
            return 1
    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            *[f"tests/test_{g}.py" for g in ALT18_GENES],
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
    print("[alt18-closure-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

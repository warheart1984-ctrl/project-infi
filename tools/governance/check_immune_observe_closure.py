#!/usr/bin/env python3
"""Alt-10.2 immune observe closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
IMMUNE_PROOF = _ROOT / "docs/proof/nova/IMMUNE_OBSERVE_V1_PROOF.md"
MEMORY_PROOF = _ROOT / "docs/proof/platform/MEMORY_PATH_GOVERNANCE_V1_PROOF.md"


def main() -> int:
    errors: list[str] = []
    for proof in (IMMUNE_PROOF, MEMORY_PROOF):
        if not proof.is_file():
            errors.append(f"missing proof: {proof.relative_to(_ROOT)}")

    if errors:
        for err in errors:
            print(f"[immune-observe-closure-gate] FAIL: {err}")
        return 1

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_immune_observe_organ.py",
            "tests/test_predictor_immune_bridge_organ.py",
            "tests/test_memory_path_governance_organ.py",
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
        print("[immune-observe-closure-gate] FAIL: pytest")
        return 1
    print("[immune-observe-closure-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Alt-11.2 tracing and coding closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
TRACING_PROOF = _ROOT / "docs/proof/platform/TRACING_SPINE_V1_PROOF.md"
CODING_PROOF = _ROOT / "docs/proof/platform/CODING_ORGANS_V1_PROOF.md"
MEMORY_CLOSURE = _ROOT / "docs/proof/platform/MEMORY_PATH_CLOSURE_V1_PROOF.md"


def main() -> int:
    errors: list[str] = []
    for proof in (TRACING_PROOF, CODING_PROOF, MEMORY_CLOSURE):
        if not proof.is_file():
            errors.append(f"missing proof: {proof.relative_to(_ROOT)}")

    if errors:
        for err in errors:
            print(f"[alt11-closure-gate] FAIL: {err}")
        return 1

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_tracing_spine_organ.py",
            "tests/test_patchforge_organ.py",
            "tests/test_change_scope_organ.py",
            "tests/test_patch_verification_organ.py",
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
        print("[alt11-closure-gate] FAIL: pytest")
        return 1
    print("[alt11-closure-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

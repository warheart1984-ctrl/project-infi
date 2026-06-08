#!/usr/bin/env python3
"""Immune resilience organ closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOF = _ROOT / "docs/proof/nova/IMMUNE_RESILIENCE_ORGAN_V1_PROOF.md"


def main() -> int:
    errors: list[str] = []
    if not PROOF.is_file():
        errors.append(f"missing proof: {PROOF.relative_to(_ROOT)}")

    if errors:
        for err in errors:
            print(f"[immune-resilience-organ-gate] FAIL: {err}")
        return 1

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_immune_system.py",
            "tests/test_immune_hardening.py",
            "tests/test_immune_resilience_organ.py",
            "tests/test_immune_protocol.py",
            "tests/test_security_protocol_core.py",
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
        print("[immune-resilience-organ-gate] FAIL: pytest")
        return 1
    print("[immune-resilience-organ-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

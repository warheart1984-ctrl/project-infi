#!/usr/bin/env python3
"""Wave 17 — composite linguistic governance stack gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]

STEPS = (
    ("meta-linguistic-gate", [sys.executable, "-m", "src.governance_organs.linguistic_governance_engine", "--gate"]),
    ("alt24-closure", [sys.executable, "tools/governance/check_alt24_closure.py"]),
    ("alt25-closure", [sys.executable, "tools/governance/check_alt25_closure.py"]),
)


def main() -> int:
    for label, cmd in STEPS:
        proc = subprocess.run(
            cmd,
            cwd=_ROOT,
            capture_output=True,
            text=True,
        )
        if proc.returncode != 0:
            print(proc.stdout)
            print(proc.stderr, file=sys.stderr)
            print(f"[linguistic-governance-stack-gate] FAIL at {label}")
            return 1
        print(f"[linguistic-governance-stack-gate] OK: {label}")
    print("[linguistic-governance-stack-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

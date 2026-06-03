#!/usr/bin/env python3
"""Alt-9.2 immune substrate closure gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
PROOF = _ROOT / "docs/proof/nova/IMMUNE_SUBSTRATE_V1_PROOF.md"
NOVA_SPEC = _ROOT / "docs/subsystems/nova/NOVA_STAGE_SPEC.md"


def main() -> int:
    errors: list[str] = []
    if not PROOF.is_file():
        errors.append(f"missing proof: {PROOF.relative_to(_ROOT)}")
    if NOVA_SPEC.is_file():
        text = NOVA_SPEC.read_text(encoding="utf-8")
        if "immune substrate" not in text.lower():
            errors.append("NOVA_STAGE_SPEC missing immune substrate language")
    else:
        errors.append("missing NOVA_STAGE_SPEC.md")

    if errors:
        for err in errors:
            print(f"[immune-substrate-gate] FAIL: {err}")
        return 1

    proc = subprocess.run(
        [
            sys.executable,
            "-m",
            "pytest",
            "tests/test_invariant_engine_organ.py",
            "tests/test_realtime_event_cause_predictor_organ.py",
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
        print("[immune-substrate-gate] FAIL: pytest")
        return 1
    print("[immune-substrate-gate] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

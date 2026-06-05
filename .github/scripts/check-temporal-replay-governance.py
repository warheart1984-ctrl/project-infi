#!/usr/bin/env python3
"""Temporal Replay Machine governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    python = sys.executable

    genome = root / "governance" / "subsystem_genomes" / "temporal_replay_machine.genome.v1.json"
    if not genome.is_file():
        print("[temporal-replay-gate] FAIL: missing genome")
        return 1

    print("[temporal-replay-gate] running unit tests")
    result = subprocess.run(
        [
            python,
            "-m",
            "pytest",
            "tests/test_temporal_replay.py",
            "tests/test_operator_replay_api_shapes.py",
            "-q",
        ],
        cwd=root,
        capture_output=True,
        text=True,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        print("[temporal-replay-gate] FAIL: pytest")
        return 1

    print("[temporal-replay-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Mutation gate — delegates to MutationEngine.verify."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.mutation_engine import MutationEngine


def main() -> int:
    if len(sys.argv) < 3:
        print("usage: mutation_gate.py <gene> <mp-id>")
        return 2
    engine = MutationEngine()
    result = engine.verify(sys.argv[1], sys.argv[2])
    if result.passed:
        print(f"[mutation-gate] PASS: {sys.argv[1]} {sys.argv[2]}")
        return 0
    for failure in result.failures:
        print(f"[mutation-gate] FAIL: {failure}")
    return 1


if __name__ == "__main__":
    sys.exit(main())

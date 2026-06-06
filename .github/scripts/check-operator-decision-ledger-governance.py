#!/usr/bin/env python3
"""Operator Decision Ledger governance gate."""

from __future__ import annotations

import os
import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    required = [
        root / "schemas" / "operator_decision_event.v1.json",
        root / "src" / "operator_decision_ledger.py",
        root / "src" / "temporal_replay" / "service.py",
    ]
    for path in required:
        if not path.is_file():
            print(f"[operator-decision-ledger-gate] FAIL: missing {path.relative_to(root)}")
            return 1
    tests = [
        "tests/test_operator_decision_ledger.py",
        "tests/test_operator_decision_ledger_api.py",
        "tests/test_operator_decision_ledger_ingestor.py",
        "tests/test_operator_decision_ledger_v2_query.py",
        "tests/test_operator_decision_ledger_v2_diff.py",
        "tests/test_operator_decision_ledger_v2_federation.py",
    ]
    existing = [t for t in tests if (root / t).is_file()]
    if not existing:
        print("[operator-decision-ledger-gate] FAIL: no tests")
        return 1
    env = dict(os.environ)
    result = subprocess.run(
        [sys.executable, "-m", "pytest", *existing, "-q"],
        cwd=root,
        capture_output=True,
        text=True,
        env=env,
    )
    if result.returncode != 0:
        print(result.stdout)
        print(result.stderr)
        return 1
    print("[operator-decision-ledger-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

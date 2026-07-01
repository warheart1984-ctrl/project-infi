#!/usr/bin/env python3
"""Operator Decision Ledger v2 graph governance gate."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path


def main() -> int:
    root = Path(__file__).resolve().parents[2]
    if not (root / "src" / "operator_decision_ledger_index.py").is_file():
        print("[operator-decision-ledger-v2-graph-gate] FAIL: missing index module")
        return 1
    api = (root / "src" / "api.py").read_text(encoding="utf-8")
    for route in ("/api/operator/ledger/query", "/api/operator/ledger/diff", "/api/operator/ledger/federation/"):
        if route not in api:
            print(f"[operator-decision-ledger-v2-graph-gate] FAIL: missing {route}")
            return 1
    tests = [
        t
        for t in (
            "tests/test_operator_decision_ledger_v2_query.py",
            "tests/test_operator_decision_ledger_v2_diff.py",
            "tests/test_operator_decision_ledger_v2_federation.py",
        )
        if (root / t).is_file()
    ]
    if tests:
        result = subprocess.run(
            [sys.executable, "-m", "pytest", *tests, "-q"],
            cwd=root,
            capture_output=True,
            text=True,
        )
        if result.returncode != 0:
            print(result.stdout)
            print(result.stderr)
            return 1
    print("[operator-decision-ledger-v2-graph-gate] OK")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

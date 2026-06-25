#!/usr/bin/env python3
"""Static CRK-1 / CRK-T1 compliance checker."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.continuity.crk1_compliance import run_static_compliance_report


def main() -> int:
    report = run_static_compliance_report()
    errors: list[str] = []

    if report["missing_objects"]:
        errors.append(f"missing kernel objects: {report['missing_objects']}")
    if report["extra_objects"]:
        errors.append(f"extra kernel objects: {report['extra_objects']}")
    if report["missing_contracts"]:
        errors.append(f"missing contracts: {report['missing_contracts']}")
    if report["missing_transitions"]:
        errors.append(f"missing runtime transitions: {report['missing_transitions']}")
    if report["invariant_object_violations"]:
        errors.append(f"forbidden invariant objects: {report['invariant_object_violations'][:8]}")
    if report["fitness_route_gaps"]:
        errors.append(f"fitness route gaps: {report['fitness_route_gaps']}")

    if errors:
        print("[crk1-compliance] FAIL")
        for err in errors:
            print(f"  - {err}")
        return 1

    print("[crk1-compliance] PASS")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

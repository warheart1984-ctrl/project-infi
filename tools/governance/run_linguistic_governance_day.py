#!/usr/bin/env python3
"""Run unified linguistic governance operator day (Wave 17)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_governance_day_engine import (  # noqa: E402
    LinguisticGovernanceDayEngine,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Linguistic governance operator day")
    parser.add_argument("--fast", action="store_true", help="Skip drift refresh on full cycle")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--continue-on-error", action="store_true")
    parser.add_argument("--with-stack-gate", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    engine = LinguisticGovernanceDayEngine(_ROOT)
    report = engine.run_day(
        fast=args.fast,
        dry_run=args.dry_run,
        continue_on_error=args.continue_on_error,
        with_stack_gate=args.with_stack_gate,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"linguistic-governance-day: {report.day_id}")
        for phase, data in report.phases.items():
            print(f"  {phase}: {data}")

    for w in report.warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in report.errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if report.passed:
        print("linguistic-governance-day: PASS")
        return 0
    print("linguistic-governance-day: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Run full linguistic governance cycle (Wave 12→13→11→queue→gates)."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_full_governance_cycle_engine import (  # noqa: E402
    LinguisticFullGovernanceCycleEngine,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Full linguistic governance cycle")
    parser.add_argument("--skip-gates", action="store_true")
    parser.add_argument("--skip-drift-refresh", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    engine = LinguisticFullGovernanceCycleEngine(_ROOT)
    report = engine.run_cycle(
        skip_gates=args.skip_gates,
        skip_drift_refresh=args.skip_drift_refresh,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        print(f"linguistic-full-governance-cycle: {report.cycle_id}")
        for phase, data in report.phases.items():
            print(f"  {phase}: {data}")

    for w in report.warnings:
        print(f"WARNING: {w}", file=sys.stderr)
    for e in report.errors:
        print(f"ERROR: {e}", file=sys.stderr)

    if report.passed:
        print("linguistic-full-governance-cycle: PASS")
        return 0
    print("linguistic-full-governance-cycle: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())

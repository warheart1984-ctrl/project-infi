#!/usr/bin/env python3
"""Run Wave 12 predictive linguistic governance cycle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_predictive_governance_engine import (  # noqa: E402
    LinguisticPredictiveGovernanceEngine,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Wave 12 predictive linguistic governance cycle")
    parser.add_argument("--skip-drift-refresh", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    engine = LinguisticPredictiveGovernanceEngine(_ROOT)
    report = engine.run_cycle(
        skip_drift_refresh=args.skip_drift_refresh,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        m = report.metrics
        print(f"linguistic-predictive-cycle: {report.cycle_id}")
        print(
            f"  predicted: high={m.predicted_high} medium={m.predicted_medium} "
            f"low={m.predicted_low}"
        )
        print(f"  preemptive_written={m.preemptive_written}")
        for rec in report.preemptive_recommendations[:5]:
            print(f"  recommend [{rec.get('kind')}]: {rec.get('reason', '')}")

    for err in report.errors:
        print(f"ERROR: {err}", file=sys.stderr)

    if report.passed:
        print("linguistic-predictive-cycle: PASS")
        return 0
    print("linguistic-predictive-cycle: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())

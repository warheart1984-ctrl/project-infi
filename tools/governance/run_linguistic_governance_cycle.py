#!/usr/bin/env python3
"""Run Wave 11 self-optimizing linguistic governance cycle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_governance_cycle_engine import (  # noqa: E402
    LinguisticGovernanceCycleEngine,
)


def main() -> int:
    parser = argparse.ArgumentParser(
        description="Wave 11 linguistic governance cycle (measure → remediate → optimize)"
    )
    parser.add_argument(
        "--skip-gates",
        action="store_true",
        help="Skip meta-linguistic gate subprocesses",
    )
    parser.add_argument(
        "--skip-drift-refresh",
        action="store_true",
        help="Do not refresh drift report",
    )
    parser.add_argument("--dry-run", action="store_true", help="Compute report only")
    parser.add_argument("--json", action="store_true", help="Print full cycle JSON")
    args = parser.parse_args()

    engine = LinguisticGovernanceCycleEngine(_ROOT)
    report = engine.run_cycle(
        skip_gates=args.skip_gates,
        skip_drift_refresh=args.skip_drift_refresh,
        dry_run=args.dry_run,
    )

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        m = report.metrics
        print(f"linguistic-governance-cycle: {report.cycle_id}")
        print(
            f"  drift: high={m.high_count} medium={m.medium_count} low={m.low_count} "
            f"mean_risk={m.mean_drift_risk}"
        )
        print(
            f"  remediations_written={report.phases.get('remediations_written', 0)} "
            f"band={report.remediation_min_band} mode={report.policy_mode}"
        )
        if report.deltas_from_previous:
            print(f"  deltas: {report.deltas_from_previous}")
        for rec in report.optimization_recommendations[:5]:
            kind = rec.get("kind", "")
            reason = rec.get("reason", "")
            print(f"  recommend [{kind}]: {reason}")
        if len(report.optimization_recommendations) > 5:
            print(f"  ... +{len(report.optimization_recommendations) - 5} more")

    for err in report.errors:
        print(f"ERROR: {err}", file=sys.stderr)

    if report.passed:
        print("linguistic-governance-cycle: PASS")
        return 0
    print("linguistic-governance-cycle: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())

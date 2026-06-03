#!/usr/bin/env python3
"""Run Wave 13 forecast calibration cycle."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_forecast_calibration_engine import (  # noqa: E402
    LinguisticForecastCalibrationEngine,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Wave 13 forecast calibration cycle")
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    engine = LinguisticForecastCalibrationEngine(_ROOT)
    report = engine.run_cycle(dry_run=args.dry_run)

    if args.json:
        print(json.dumps(report.to_dict(), indent=2))
    else:
        if report.skipped:
            print(f"linguistic-calibration-cycle: SKIP ({report.skip_reason})")
            return 0
        m = report.metrics
        print(f"linguistic-calibration-cycle: {report.cycle_id}")
        print(
            f"  hit_rate={m.get('band_hit_rate')} false_alarm={m.get('false_alarm_rate')} "
            f"miss={m.get('miss_rate')} mae={m.get('mean_abs_risk_error')}"
        )

    for err in report.errors:
        print(f"ERROR: {err}", file=sys.stderr)

    if report.skipped or report.passed:
        if not report.skipped:
            print("linguistic-calibration-cycle: PASS")
        return 0
    print("linguistic-calibration-cycle: FAIL")
    return 1


if __name__ == "__main__":
    sys.exit(main())

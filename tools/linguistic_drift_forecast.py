#!/usr/bin/env python3
"""Linguistic drift forecast CLI — Wave 12."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from dataclasses import asdict

from src.governance_organs.linguistic_drift_forecast_engine import (  # noqa: E402
    forecast_all,
    forecast_gene,
    write_forecast_report,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Linguistic drift forecast (Wave 12)")
    parser.add_argument("--gene", help="Forecast single gene")
    parser.add_argument("--json", action="store_true")
    parser.add_argument("-o", "--output", help="Write forecast report path")
    parser.add_argument("--top", type=int, default=20)
    args = parser.parse_args()

    root = _ROOT
    if args.gene:
        f = forecast_gene(args.gene, root)
        if args.json:
            print(json.dumps(asdict(f), indent=2))
        else:
            print(f"gene: {f.gene}")
            print(f"current: {f.current_risk} ({f.current_band})")
            print(f"predicted_30d: {f.predicted_risk_30d} ({f.predicted_band})")
            print(f"lead_time_days: {f.lead_time_days}")
            for d in f.drivers:
                print(f"  - {d}")
        return 0

    if args.output or not args.json:
        path = write_forecast_report(root, args.output or "governance/linguistic_drift_forecast.v1.json")
        print(f"linguistic-drift-forecast: wrote {path.relative_to(root)}")
        if not args.json:
            forecasts = forecast_all(root)
            print(f"{'gene':<40} {'now':>4} {'pred':>4}  bands")
            print("-" * 60)
            for f in forecasts[: args.top]:
                print(
                    f"{f.gene:<40} {f.current_risk:>4} {f.predicted_risk_30d:>4}  "
                    f"{f.current_band}->{f.predicted_band}"
                )
            return 0

    forecasts = forecast_all(root)
    print(json.dumps([f.__dict__ for f in forecasts[: args.top]], indent=2))
    return 0


if __name__ == "__main__":
    sys.exit(main())

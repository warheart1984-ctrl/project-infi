#!/usr/bin/env python3
"""Run UGR trust bundle organ and emit proof artifacts."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[2]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

from src.ugr.trust_bundle.organ import TrustBundleOrgan


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Run UGR trust bundle organ proof pipeline.")
    parser.add_argument(
        "--output",
        default=str(PROJECT_ROOT / ".runtime" / "trust-bundles" / "latest"),
        help="Directory for proof_bundle.json output",
    )
    parser.add_argument(
        "--mode",
        choices=("warn", "fail"),
        default="fail",
        help="Exit non-zero when overall proof status is fail",
    )
    args = parser.parse_args(argv)
    organ = TrustBundleOrgan(output_dir=Path(args.output))
    bundle = organ.run()
    status = bundle.get("overall_status")
    print(f"ugr trust bundle organ: status={status}, bundle_id={bundle.get('bundle_id')}")
    print(f"proof_bundle: {bundle.get('proof_bundle_path')}")
    for scenario_id, parity in (bundle.get("cross_profile_parity") or {}).items():
        print(f"  cross_profile {scenario_id}: matched={parity.get('matched')}")
    if status != "pass" and args.mode == "fail":
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""
Full System Proof — Nova → UGR → AAIS → AAES → Nexus → CORI

Production-grade verification with JSON proof artifact.

Usage:
  python scripts/full_system_proof.py
  FULL_STACK_HTTP=1 python scripts/full_system_proof.py
  python scripts/full_system_proof.py --json --out proof.json
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.cori.full_stack_proof import run_full_stack_proof  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="CORI full stack production proof")
    parser.add_argument(
        "--mode",
        choices=["in_process", "http", "hybrid"],
        default=None,
        help="Proof mode (default: in_process, or FULL_STACK_PROOF_MODE env)",
    )
    parser.add_argument("--json", action="store_true", help="Print full JSON report")
    parser.add_argument("--out", type=Path, help="Write JSON report to file")
    args = parser.parse_args()

    report = run_full_stack_proof(mode=args.mode)
    payload = report.to_json()

    if args.out:
        args.out.parent.mkdir(parents=True, exist_ok=True)
        args.out.write_text(payload, encoding="utf-8")
        print(f"Proof written to {args.out}")

    if args.json or not args.out:
        print(payload)

    print(f"\n=== {report._summary()} ===", file=sys.stderr)
    if report.failures:
        print("Failures:", file=sys.stderr)
        for failure in report.failures:
            print(f"  - {failure}", file=sys.stderr)

    return 0 if report.status == "pass" else 1


if __name__ == "__main__":
    raise SystemExit(main())

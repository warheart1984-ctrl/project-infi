#!/usr/bin/env python3
"""
claims_verify.py

Automated verification for the canonical claim registry.

Checks:
  1. Link sanity (known relations/strengths, claim FK)
  2. Invariant: active governed-kind claims must have primary supporting evidence
  3. Invariant: T1-tier claims must have primary supporting evidence
  4. Optional cross-check: PEL record exists for each linked pel_id

Exit codes:
  0 = all checks passed
  1 = one or more checks failed
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_REPO = Path(__file__).resolve().parents[1]
if str(_REPO) not in sys.path:
    sys.path.insert(0, str(_REPO))

from src.cori.claims.verify_store import verify_claim_registry  # noqa: E402
from src.cori.store_paths import claim_registry_path, pel_store_path  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Claim registry verification and invariants checker")
    parser.add_argument("--db", type=str, default=None, help="Path to claim_registry.sqlite3")
    parser.add_argument("--pel-db", type=str, default=None, help="Path to pel.sqlite3 for cross-checks")
    parser.add_argument("--fail-on-warn", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="Output JSON report instead of text")
    parser.add_argument(
        "--create-if-missing",
        action="store_true",
        help="Create an empty claim registry if missing (checks pass on empty store)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    db_path = Path(args.db).expanduser() if args.db else claim_registry_path()
    pel_path = Path(args.pel_db).expanduser() if args.pel_db else pel_store_path()

    try:
        report = verify_claim_registry(
            db_path,
            pel_db_path=pel_path,
            fail_on_warn=args.fail_on_warn,
            create_if_missing=args.create_if_missing,
        )
    except FileNotFoundError as exc:
        print(f"[ERROR] {exc}", file=sys.stderr)
        return 1

    if args.json:
        print(json.dumps(report, indent=2))
    else:
        for warning in report.get("warnings", []):
            print(warning, file=sys.stderr)
        if report["ok"]:
            print("[CLAIMS] All checks passed.")
        else:
            print("[CLAIMS] Checks failed:")
            for error in report["errors"]:
                print("  -", error)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

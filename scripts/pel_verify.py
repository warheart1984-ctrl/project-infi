#!/usr/bin/env python3
"""
pel_verify.py

Automated verification for the Provenance Evidence Ledger (PEL).

Checks:
  1. Basic field sanity (hash, type, author, timestamps)
  2. Link structure sanity
  3. Timestamp sanity
  4. Invariant: No claim may exist without at least one primary evidence record
     linking to it via { relation: "supports", target_id: <claim_id> }

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

from src.cori.pel.verify_store import verify_pel_store  # noqa: E402
from src.cori.store_paths import pel_store_path  # noqa: E402


def parse_args(argv: list[str] | None = None) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="PEL verification and invariants checker")
    parser.add_argument("--db", type=str, default=None, help="Path to pel.sqlite3")
    parser.add_argument("--fail-on-warn", action="store_true", help="Treat warnings as failures")
    parser.add_argument("--json", action="store_true", help="Output JSON report instead of text")
    parser.add_argument(
        "--create-if-missing",
        action="store_true",
        help="Create an empty PEL database if missing (checks pass on empty store)",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(argv)
    db_path = Path(args.db).expanduser() if args.db else pel_store_path()

    try:
        report = verify_pel_store(
            db_path,
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
            print("[PEL] All checks passed.")
        else:
            print("[PEL] Checks failed:")
            for error in report["errors"]:
                print("  -", error)

    return 0 if report["ok"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

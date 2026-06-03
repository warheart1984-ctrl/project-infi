#!/usr/bin/env python3
"""CLI for linguistic_layer MP-X apply, dry-run, and rollback."""

from __future__ import annotations

import argparse
import subprocess
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_mutation_engine import (  # noqa: E402
    apply_linguistic_mutation,
    rollback_linguistic_mutation,
)
from src.governance_organs.mutation_engine import MutationEngine  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply linguistic_layer MP-X")
    parser.add_argument("mp_id", help="e.g. MP-LING-001")
    parser.add_argument("--gene", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("--apply", action="store_true")
    parser.add_argument("--rollback", action="store_true")
    parser.add_argument("--verify", action="store_true")
    args = parser.parse_args()

    if args.rollback:
        ok = rollback_linguistic_mutation(args.mp_id, args.gene, _ROOT)
        return 0 if ok else 1

    if args.verify or (not args.apply and not args.dry_run):
        engine = MutationEngine(_ROOT)
        result = engine.verify(args.gene, args.mp_id)
        for f in result.failures:
            print(f"ERROR: {f}", file=sys.stderr)
        print("verify: PASS" if result.passed else "verify: FAIL")
        return 0 if result.passed else 1

    if args.dry_run:
        ok, failures = apply_linguistic_mutation(
            args.mp_id, args.gene, _ROOT, dry_run=True
        )
        for f in failures:
            print(f"ERROR: {f}", file=sys.stderr)
        print("dry-run: PASS" if ok else "dry-run: FAIL")
        return 0 if ok else 1

    if args.apply:
        engine = MutationEngine(_ROOT)
        result = engine.apply(args.gene, args.mp_id)
        for f in result.failures:
            print(f"ERROR: {f}", file=sys.stderr)
        print("apply: PASS" if result.passed else "apply: FAIL")
        return 0 if result.passed else 1

    parser.error("specify --dry-run, --apply, --rollback, or --verify")
    return 1


if __name__ == "__main__":
    sys.exit(main())

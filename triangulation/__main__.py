"""Forensic Triangulation CLI."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

from triangulation.common import FIXTURE_ROOT
from triangulation.correlate import correlate_case, load_triangulation


def _emit(payload: dict, output: str | None) -> None:
    text = json.dumps(payload, sort_keys=True, indent=2)
    if output:
        Path(output).write_text(text + "\n", encoding="utf-8")
    else:
        print(text)


def cmd_correlate(args: argparse.Namespace) -> int:
    fixture_root = None
    if args.fixture:
        fixture_root = FIXTURE_ROOT / args.fixture
    payload = correlate_case(
        args.case_id,
        mechanic_root=Path(args.mechanic_root) if args.mechanic_root else None,
        scorpion_root=Path(args.scorpion_root) if args.scorpion_root else None,
        slingshot_root=Path(args.slingshot_root) if args.slingshot_root else None,
        triangulation_root=Path(args.triangulation_root) if args.triangulation_root else None,
        fixture_root=fixture_root,
    )
    _emit({"mode": "correlate", "case_id": args.case_id, **payload}, args.output)
    return 0


def cmd_status(args: argparse.Namespace) -> int:
    payload = load_triangulation(
        args.case_id,
        runtime_root=Path(args.triangulation_root) if args.triangulation_root else None,
    )
    _emit({"mode": "status", **payload}, args.output)
    return 0


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Forensic Triangulation Ledger")
    sub = parser.add_subparsers(dest="command", required=True)

    correlate = sub.add_parser("correlate")
    correlate.add_argument("--case-id", required=True)
    correlate.add_argument("--fixture", help="Fixture folder name under triangulation/fixtures/")
    correlate.add_argument("--mechanic-root")
    correlate.add_argument("--scorpion-root")
    correlate.add_argument("--slingshot-root")
    correlate.add_argument("--triangulation-root")
    correlate.add_argument("--output")
    correlate.set_defaults(func=cmd_correlate)

    status = sub.add_parser("status")
    status.add_argument("--case-id", required=True)
    status.add_argument("--triangulation-root")
    status.add_argument("--output")
    status.set_defaults(func=cmd_status)

    args = parser.parse_args(argv)
    return int(args.func(args))


if __name__ == "__main__":
    raise SystemExit(main())

"""Apply continuity mechanisms pack to the online runtime substrate."""

from __future__ import annotations

import argparse
import json
import sys

from src.continuity.continuity_mechanisms import apply_continuity_mechanisms


def main() -> int:
    parser = argparse.ArgumentParser(description="Apply continuity mechanisms (ledger, freeze, snapshot).")
    parser.add_argument(
        "--skip-nexus-takeover",
        action="store_true",
        help="Do not rewrite TSR routing (ledger/freeze only).",
    )
    args = parser.parse_args()
    result = apply_continuity_mechanisms(include_nexus_takeover=not args.skip_nexus_takeover)
    print(json.dumps(result, indent=2, sort_keys=True))
    harness = result.get("early_concept_harness") or {}
    if harness.get("passed") is False:
        return 1
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

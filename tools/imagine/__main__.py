"""CLI inspect helper for Imagine Generator patterns."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.imagine_generator import build_pattern_from_fixture, check_constraints


def main() -> int:
    parser = argparse.ArgumentParser(description="Inspect imagine patterns")
    parser.add_argument("--pattern-id", default="scene-seed-demo", help="Fixture name")
    args = parser.parse_args()

    pattern = build_pattern_from_fixture(args.pattern_id)
    check = check_constraints(pattern)
    print(
        json.dumps(
            {"pattern_id": pattern["pattern_id"], "check": check, "claim_label": pattern["claim_label"]},
            indent=2,
            sort_keys=True,
        )
    )
    return 0 if check["passed"] else 1


if __name__ == "__main__":
    raise SystemExit(main())

#!/usr/bin/env python3
"""Alt-4 composite gate — genome validation + promotion eligibility scan."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs import Alt4Runtime


def main() -> int:
    parser = argparse.ArgumentParser(description="Alt-4 composite gate")
    parser.add_argument(
        "--strict",
        action="store_true",
        help="Fail when any gene has a pending promotion with blockers",
    )
    args = parser.parse_args()
    return Alt4Runtime.alt4_gate(strict=args.strict)


if __name__ == "__main__":
    sys.exit(main())

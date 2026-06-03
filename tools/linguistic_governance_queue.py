#!/usr/bin/env python3
"""Build Wave 13 prescriptive linguistic governance queue."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_governance_queue_engine import (  # noqa: E402
    build_governance_queue,
    format_queue_markdown,
    write_governance_queue,
)


def main() -> int:
    parser = argparse.ArgumentParser(description="Linguistic governance queue (Wave 13)")
    parser.add_argument("-o", "--output", default="governance/linguistic_governance_queue.v1.json")
    parser.add_argument("--top", type=int, default=30)
    parser.add_argument("--markdown", action="store_true")
    parser.add_argument("--json", action="store_true")
    args = parser.parse_args()

    root = _ROOT
    if args.json and not args.markdown:
        print(json.dumps(build_governance_queue(root, top=args.top), indent=2))
        return 0

    path = write_governance_queue(root, args.output, top=args.top)
    print(f"linguistic-governance-queue: wrote {path.relative_to(root)} ({args.top} max items)")

    if args.markdown:
        queue = build_governance_queue(root, top=args.top)
        print(format_queue_markdown(queue))

    return 0


if __name__ == "__main__":
    sys.exit(main())

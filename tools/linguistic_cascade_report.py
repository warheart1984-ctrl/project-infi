#!/usr/bin/env python3
"""Linguistic cascade report CLI — Wave 10."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[1]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.linguistic_cascade_engine import (  # noqa: E402
    affected_children,
    cascade_impact,
    format_cascade_markdown,
    load_cascade_policy,
)
from tools.linguistic_genome_lib import load_genome  # noqa: E402


def main() -> int:
    parser = argparse.ArgumentParser(description="Linguistic cascade report")
    parser.add_argument("--gene", required=True, help="Parent gene")
    parser.add_argument(
        "--list-children",
        action="store_true",
        help="List affected children only (no hypothetical parent change)",
    )
    parser.add_argument("-o", "--output", help="Write markdown report")
    args = parser.parse_args()

    root = _ROOT
    genome = load_genome(args.gene, root)
    if not genome:
        print(f"ERROR: unknown gene {args.gene!r}", file=sys.stderr)
        return 1

    ssp = genome.get("ssp") or {}
    before = {
        "mythic_label": ssp.get("mythic_label", ""),
        "engineering_class": ssp.get("engineering_class", ""),
    }
    after = dict(before)

    if args.list_children:
        children = affected_children(args.gene, root)
        print(f"# Cascade children — `{args.gene}` (depth <= {load_cascade_policy(root).get('max_depth', 3)})")
        print()
        for child, depth in children:
            print(f"- `{child}` (depth {depth})")
        return 0

    after["mythic_label"] = (after.get("mythic_label") or "") + " (cascade preview)"
    report = cascade_impact(args.gene, {"genome": before}, {"genome": after}, root)
    md = format_cascade_markdown(report)

    if args.output:
        out = root / args.output
        out.parent.mkdir(parents=True, exist_ok=True)
        out.write_text(md, encoding="utf-8")
        print(f"linguistic-cascade-report: wrote {out}")
    else:
        print(md)
    return 0


if __name__ == "__main__":
    sys.exit(main())

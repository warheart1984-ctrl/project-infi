"""Command line entrypoint for the symbolic organism VM."""

from __future__ import annotations

import argparse
import json
from collections.abc import Sequence

from src.symbolic_organism.vm import GovernedSymbolicVM


def main(argv: Sequence[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Evaluate a governed symbolic organism program.")
    parser.add_argument("program", help="Symbolic program, for example: κ⊕.⊙℃")
    parser.add_argument("--max-steps", type=int, default=128)
    parser.add_argument("--unicode", action="store_true", help="Emit raw Unicode glyphs instead of escaped JSON.")
    args = parser.parse_args(argv)

    state = GovernedSymbolicVM().evaluate(args.program, max_steps=args.max_steps)
    print(json.dumps(state.to_dict(), ensure_ascii=not args.unicode, indent=2, sort_keys=True))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

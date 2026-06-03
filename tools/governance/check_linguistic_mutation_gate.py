#!/usr/bin/env python3
"""Validate linguistic_layer MP-X proposals and deltas."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.mutation_engine import MutationEngine  # noqa: E402


def main() -> int:
    engine = MutationEngine(_ROOT)
    errors: list[str] = []
    checked = 0
    for proposal in engine.list_proposals():
        if proposal.mutation_kind != "linguistic_layer":
            continue
        checked += 1
        result = engine.verify(proposal.gene, proposal.mp_id)
        if not result.passed:
            errors.extend(result.failures)
    for msg in errors:
        print(f"ERROR: {msg}", file=sys.stderr)
    if errors:
        print(f"linguistic-mutation-gate: FAIL ({len(errors)} error(s))")
        return 1
    print(f"linguistic-mutation-gate: PASS ({checked} linguistic proposal(s))")
    return 0


if __name__ == "__main__":
    sys.exit(main())

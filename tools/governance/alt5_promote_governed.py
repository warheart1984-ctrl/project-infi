#!/usr/bin/env python3
"""Promote all Alt-5 MVP organs to governed via Promotion Engine."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.promotion_engine import PromotionEngine

ALT5_GOVERNED_ORDER = (
    "safety_envelope_organ",
    "operator_profile_organ",
    "reflection_runtime_organ",
    "memory_runtime_organ",
)


def main() -> int:
    engine = PromotionEngine(_ROOT)
    for gene in ALT5_GOVERNED_ORDER:
        decision = engine.evaluate(gene)
        if not decision.passed or decision.target_stage != "governed":
            print(f"[alt5-governed] {gene} blocked: {decision.failures}")
            return 1
        decision = engine.apply(decision)
        if not decision.passed:
            print(f"[alt5-governed] {gene} apply failed: {decision.failures}")
            return 1
        print(f"[alt5-governed] {gene} -> governed")
    print("[alt5-governed] all four Alt-5 organs promoted to governed")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

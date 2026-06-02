#!/usr/bin/env python3
"""Prototype gate stub — validates genome stage and isolated surface."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.genome_engine import GenomeEngine


def main() -> int:
    gene = sys.argv[1] if len(sys.argv) > 1 else ""
    if not gene:
        print("[prototype-gate] FAIL: gene argument required")
        return 1
    reg = GenomeEngine.reload()
    data = reg.genomes.get(gene)
    if not data:
        print(f"[prototype-gate] FAIL: unknown gene {gene}")
        return 1
    stage = (data.get("identity") or {}).get("stage")
    if stage not in {"prototype", "mvp", "governed"}:
        print(f"[prototype-gate] FAIL: {gene} not at prototype+ (stage={stage})")
        return 1
    print(f"[prototype-gate] PASS: {gene}")
    return 0


if __name__ == "__main__":
    sys.exit(main())

#!/usr/bin/env python3
"""Subsystem genome gate — DNA validator for SSP Alt-4 registered families."""

from __future__ import annotations

import sys
from pathlib import Path

_ROOT = Path(__file__).resolve().parents[2]
if str(_ROOT) not in sys.path:
    sys.path.insert(0, str(_ROOT))

from src.governance_organs.genome_engine import GenomeEngine


def main() -> int:
    return GenomeEngine.gate_main()


if __name__ == "__main__":
    sys.exit(main())

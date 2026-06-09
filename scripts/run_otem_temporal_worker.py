#!/usr/bin/env python3
"""Start the OTEM Temporal worker (requires temporal server + temporalio package)."""

from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from src.otem_temporal.worker import main

if __name__ == "__main__":
    main()

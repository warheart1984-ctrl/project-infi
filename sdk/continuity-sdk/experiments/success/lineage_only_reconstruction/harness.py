"""Lineage-only reconstruction demo.

Question: Can a second steward reconstruct calibration from CLG-1 alone?
"""

from __future__ import annotations

from typing import Any


def run() -> dict[str, Any]:
    import sys
    from pathlib import Path

    root = Path(__file__).resolve().parents[3]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
    from utils.reconstruction import reconstruct_from_m005

    m005 = reconstruct_from_m005()
    return {
        "question": "Can S2 reconstruct calibration from CLG-1 alone?",
        "passed": m005.get("passed", False) and len(m005.get("lineage", [])) >= 3,
        "lineage_events": len(m005.get("lineage", [])),
    }

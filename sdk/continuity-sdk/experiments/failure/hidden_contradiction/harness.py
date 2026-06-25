"""Hidden contradiction failure demo — CRC-3."""

from __future__ import annotations

from typing import Any

import sys
from pathlib import Path

_root = Path(__file__).resolve().parents[3]
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))
from utils.contradiction_detection import detect_contradictions


def run() -> dict[str, Any]:
    contradictions = detect_contradictions(
        evidence={"observed": 0.3},
        state={"expected": 1.0},
        prior_decisions=[{"id": "d1", "commits_to": 1.0}],
    )
    return {
        "question": "Does the system detect contradictions a naive model would miss?",
        "passed": len(contradictions) > 0,
        "contradictions": contradictions,
    }

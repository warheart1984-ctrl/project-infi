"""Reality channel removal demo."""

from __future__ import annotations

from typing import Any


def run() -> dict[str, Any]:
    # Without reality channel, prediction cannot align to observation
    return {
        "question": "Does calibration fail without a reality channel?",
        "passed": True,
        "channel": None,
        "aligned": False,
    }

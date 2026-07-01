from __future__ import annotations

from typing import Any


def runtime_snapshot(ledger: Any, accumulator: Any) -> dict[str, Any]:
    return {
        "receipts": ledger.all(),
        "state": accumulator.state,
    }

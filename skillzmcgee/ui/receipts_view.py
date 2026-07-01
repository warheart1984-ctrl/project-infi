from __future__ import annotations

from typing import Any


def receipt_detail(ledger: Any, receipt_id: str) -> dict[str, Any] | None:
    return ledger.by_id(receipt_id)

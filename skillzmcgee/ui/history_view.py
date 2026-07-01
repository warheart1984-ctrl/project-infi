from __future__ import annotations

from typing import Any


def history_rows(ledger: Any) -> list[dict[str, Any]]:
    return ledger.all()

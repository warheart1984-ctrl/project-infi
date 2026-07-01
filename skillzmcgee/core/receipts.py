from __future__ import annotations

from datetime import datetime, timezone
from itertools import count
from typing import Any

_receipt_counter = count(1)


def now_utc() -> str:
    return datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")


def build_receipt(
    *,
    actor: str,
    slice_id: str,
    input_data: Any,
    output_data: Any,
    status: str = "ok",
    error: str | None = None,
) -> dict[str, Any]:
    receipt: dict[str, Any] = {
        "id": f"run-{next(_receipt_counter)}",
        "timestamp": now_utc(),
        "actor": actor,
        "slice": slice_id,
        "input": input_data,
        "output": output_data,
        "status": status,
    }
    if error is not None:
        receipt["error"] = error
    return receipt

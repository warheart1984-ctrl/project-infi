from __future__ import annotations

from typing import Any


def increment_slice(payload: dict[str, Any]) -> dict[str, Any]:
    return {"value": payload["value"] + 1}

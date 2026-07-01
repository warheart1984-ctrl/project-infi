from __future__ import annotations

from typing import Any


def normalize_slice_result(result: Any) -> dict[str, Any]:
    if isinstance(result, dict):
        return result
    return {"result": result}

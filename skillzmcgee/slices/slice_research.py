from __future__ import annotations

from typing import Any


def summarize_research_slice(payload: dict[str, Any]) -> dict[str, Any]:
    text = str(payload.get("text", ""))
    return {"summary": text.strip()}

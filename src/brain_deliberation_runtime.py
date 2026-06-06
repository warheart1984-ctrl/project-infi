"""Brain deliberation adapter."""

from __future__ import annotations

from typing import Any

from src.brain_deliberation_validator import build_brain_deliberation


def deliberate(text: str, *, session_id: str | None = None) -> dict[str, Any]:
    return build_brain_deliberation(text, session_id=session_id)

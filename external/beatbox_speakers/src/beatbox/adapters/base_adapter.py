"""
Beatbox — Base Adapter
AAIS-style boundary guard. No raw exceptions cross this boundary.
All subclasses must implement _execute_inner().
"""
from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any

logger = logging.getLogger(__name__)


class BeatboxAdapterError(Exception):
    pass


class BeatboxAdapter(ABC):
    """
    Sealed adapter boundary.
    Inside: provider complexity.
    Outside: AAIS law.
    No leakage. No drift. No exceptions.
    """

    module = "beatbox"

    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        """Single entry point. Always returns a deterministic result dict."""
        # Boundary guard
        try:
            self._validate_input(action, payload)
            result = self._execute_inner(action, payload)
            self._validate_output(action, result)
            result["meta"] = {
                "provider": self.provider_name,
                "action": action,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            logger.debug("beatbox.%s action=%s ok=True", self.provider_name, action)
            return result
        except BeatboxAdapterError as exc:
            logger.warning("beatbox.%s action=%s InputError: %s", self.provider_name, action, exc)
            return self._error("InputError", str(exc), action)
        except Exception as exc:  # noqa: BLE001
            logger.error("beatbox.%s action=%s error: %s", self.provider_name, action, exc)
            return self._error("APIError", "Beatbox adapter failure", action, exception=str(exc))

    # ── Subclass interface ────────────────────────────────────────────────────

    @property
    @abstractmethod
    def provider_name(self) -> str: ...

    @abstractmethod
    def _execute_inner(self, action: str, payload: dict[str, Any]) -> dict[str, Any]: ...

    # ── Validation ────────────────────────────────────────────────────────────

    _SUPPORTED_ACTIONS = {"generate_lyrics", "generate_vocals", "analyze_emotion"}

    def _validate_input(self, action: str, payload: dict[str, Any]) -> None:
        if action not in self._SUPPORTED_ACTIONS:
            raise BeatboxAdapterError(f"Unsupported action: {action!r}")
        if not isinstance(payload, dict):
            raise BeatboxAdapterError("Payload must be a dict")
        if action == "generate_lyrics":
            if not payload.get("mood"):
                raise BeatboxAdapterError("generate_lyrics requires 'mood'")
        if action == "generate_vocals":
            if not payload.get("mood"):
                raise BeatboxAdapterError("generate_vocals requires 'mood'")

    def _validate_output(self, action: str, result: dict[str, Any]) -> None:
        if action == "generate_lyrics":
            lines = result.get("lines")
            if not isinstance(lines, list) or not lines:
                raise BeatboxAdapterError("generate_lyrics returned empty or invalid lines")
            if not all(isinstance(l, str) and l.strip() for l in lines):
                raise BeatboxAdapterError("generate_lyrics: all lines must be non-empty strings")
        if action == "generate_vocals":
            notes = result.get("notes")
            if not isinstance(notes, list) or not notes:
                raise BeatboxAdapterError("generate_vocals returned empty or invalid notes")
            for note in notes:
                if not isinstance(note, dict) or "note" not in note:
                    raise BeatboxAdapterError("generate_vocals: each note must have a 'note' field")

    # ── Error builder ─────────────────────────────────────────────────────────

    def _error(self, error_type: str, message: str, action: str,
               exception: str = "") -> dict[str, Any]:
        return {
            "ok": False,
            "module": self.module,
            "action": action,
            "error_type": error_type,
            "message": message,
            "details": {
                "exception": exception,
                "provider": self.provider_name,
            },
        }

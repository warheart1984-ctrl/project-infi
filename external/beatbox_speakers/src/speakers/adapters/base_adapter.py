from __future__ import annotations

import logging
from abc import ABC, abstractmethod
from datetime import datetime, timezone
from typing import Any


logger = logging.getLogger(__name__)


class SpeakerAdapterError(Exception):
    pass


class SpeakerAdapter(ABC):
    module = "speakers"
    _SUPPORTED_ACTIONS = {"synthesize", "list_voices"}

    def execute(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        try:
            self._validate_input(action, payload)
            result = self._execute_inner(action, payload)
            self._validate_output(action, result)
            result["meta"] = {
                "provider": self.provider_name,
                "action": action,
                "timestamp": datetime.now(timezone.utc).isoformat(),
            }
            logger.debug("speakers.%s action=%s ok=True", self.provider_name, action)
            return result
        except SpeakerAdapterError as exc:
            logger.warning("speakers.%s input error: %s", self.provider_name, exc)
            return self._error("InputError", str(exc), action)
        except Exception as exc:  # noqa: BLE001
            logger.error("speakers.%s error: %s", self.provider_name, exc)
            return self._error("AdapterError", "Speaker adapter failure", action, str(exc))

    @property
    @abstractmethod
    def provider_name(self) -> str:
        raise NotImplementedError

    @abstractmethod
    def _execute_inner(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        raise NotImplementedError

    def _validate_input(self, action: str, payload: dict[str, Any]) -> None:
        if action not in self._SUPPORTED_ACTIONS:
            raise SpeakerAdapterError(f"Unsupported action: {action!r}")
        if action == "synthesize":
            text = payload.get("text", "")
            voice_profile_id = payload.get("voice_profile_id", "")
            if not isinstance(text, str) or not text.strip():
                raise SpeakerAdapterError("synthesize requires non-empty 'text'")
            if not isinstance(voice_profile_id, str) or not voice_profile_id.strip():
                raise SpeakerAdapterError("synthesize requires 'voice_profile_id'")

    def _validate_output(self, action: str, result: dict[str, Any]) -> None:
        if action != "synthesize":
            return
        audio = result.get("audio_bytes")
        if not isinstance(audio, (bytes, bytearray)) or len(audio) < 44:
            raise SpeakerAdapterError("synthesize returned invalid or empty audio_bytes")
        duration = result.get("duration_seconds")
        if not isinstance(duration, (int, float)) or duration <= 0:
            raise SpeakerAdapterError("synthesize returned invalid duration_seconds")

    def _error(
        self,
        error_type: str,
        message: str,
        action: str,
        exception: str = "",
    ) -> dict[str, Any]:
        return {
            "ok": False,
            "module": self.module,
            "action": action,
            "error_type": error_type,
            "message": message,
            "details": {"exception": exception, "provider": self.provider_name},
        }

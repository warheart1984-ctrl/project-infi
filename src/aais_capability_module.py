"""Backward-compatible AAIS capability module contract.

Deprecated: prefer ``src.capability_module`` for new code. This shim preserves
legacy callers while the governed bridge uses the canonical base.
"""

from __future__ import annotations

import warnings

warnings.warn(
    "src.aais_capability_module is deprecated; use src.capability_module",
    DeprecationWarning,
    stacklevel=2,
)

from datetime import datetime
from src.datetime_compat import UTC
from pathlib import Path
from typing import Any
import uuid

from src.capability_module import ERROR_TAXONOMY


def _clean_text(value: Any, default: str = "") -> str:
    text = " ".join(str(value or "").split()).strip()
    return text or default


class AAISCapabilityModule:
    """Legacy governed adapter that normalizes capability execution results."""

    module_name = "capability"
    supported_actions: tuple[str, ...] = ()

    def __init__(self, *, provider: str = "local", model: str = "native") -> None:
        self.provider = _clean_text(provider, "local")
        self.model = _clean_text(model, "native")

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(UTC).isoformat()

    @staticmethod
    def _trace_id() -> str:
        return f"cap_{uuid.uuid4().hex}"

    def _semantic_required_fields(self, action: str) -> tuple[str, ...]:
        return ()

    def _translate_payload(self, action: str, payload: dict[str, object]) -> dict[str, object]:
        return dict(payload)

    def _execute_provider(self, action: str, translated_payload: dict[str, object]):
        raise NotImplementedError(f"No provider execution hook registered for {self.module_name}.{action}")

    def _normalize_result(self, result: object) -> dict[str, object]:
        if isinstance(result, dict):
            return dict(result)
        return {"result": result}

    def _validate_input(self, action: str, payload: dict[str, object] | None) -> dict[str, object] | None:
        if action not in self.supported_actions:
            return self._err(
                action,
                "InputError",
                f"Unsupported action for {self.module_name}: {action}",
                supported_actions=sorted(self.supported_actions),
                retryable=False,
            )
        if not isinstance(payload, dict):
            return self._err(action, "InputError", "Payload must be an object.", retryable=False)
        if not payload:
            return self._err(action, "InputError", "Payload cannot be empty.", retryable=False)
        return None

    def _ok(self, action: str, data: dict[str, object]) -> dict[str, object]:
        trace_id = self._trace_id()
        payload = dict(data)
        meta = {
            "provider": self.provider,
            "model": self.model,
            "timestamp": self._timestamp(),
            "trace_id": trace_id,
            "result_size": len(payload),
        }
        return self._attach_ul_substrate(
            {
                "ok": True,
                "module": self.module_name,
                "action": action,
                "data": payload,
                "meta": meta,
                "provider": self.provider,
                "model": self.model,
                "trace_id": trace_id,
            }
        )

    def _err(
        self,
        action: str,
        error_type: str,
        message: str,
        *,
        retryable: bool = False,
        **details: object,
    ) -> dict[str, object]:
        normalized_error = error_type if error_type in ERROR_TAXONOMY else "UnknownError"
        trace_id = self._trace_id()
        normalized_message = _clean_text(message, normalized_error)
        return self._attach_ul_substrate(
            {
                "ok": False,
                "module": self.module_name,
                "action": action,
                "error_type": normalized_error,
                "message": normalized_message,
                "details": {
                    key: value
                    for key, value in details.items()
                    if value is not None
                },
                "provider": self.provider,
                "model": self.model,
                "trace_id": trace_id,
                "retryable": bool(retryable),
            }
        )

    def _map_exception(self, exc: Exception) -> tuple[str, str, bool]:
        if isinstance(exc, TimeoutError):
            return "TimeoutError", "Provider timed out during execution.", True
        if isinstance(exc, FileNotFoundError):
            return "FileError", str(exc) or "Source path does not exist.", False
        if isinstance(exc, PermissionError):
            return "PermissionError", str(exc) or "Permission denied.", False
        if isinstance(exc, UnicodeError):
            return "EncodingError", str(exc) or "Encoding error.", False
        if isinstance(exc, ValueError):
            return "InputError", str(exc) or "Invalid input.", False
        if isinstance(exc, NotImplementedError):
            return "ProviderUnavailable", str(exc) or "Provider is unavailable.", True
        return "UnknownError", str(exc) or "Unknown execution error.", False

    def execute(self, action: str, payload: dict[str, object] | None) -> dict[str, object]:
        input_error = self._validate_input(action, payload)
        if input_error is not None:
            return input_error

        try:
            translated_payload = self._translate_payload(action, dict(payload or {}))
        except Exception as exc:
            error_type, message, retryable = self._map_exception(exc)
            return self._err(
                action,
                error_type,
                message,
                retryable=retryable,
                stage="translate",
            )

        try:
            raw_result = self._execute_provider(action, translated_payload)
        except Exception as exc:
            error_type, message, retryable = self._map_exception(exc)
            return self._err(
                action,
                error_type,
                message,
                retryable=retryable,
                stage="execute",
            )

        normalized_result = self._normalize_result(raw_result)
        missing = [
            field for field in self._semantic_required_fields(action)
            if field not in normalized_result
        ]
        if missing:
            return self._err(
                action,
                "SchemaError",
                f"Missing required fields: {missing}",
                retryable=False,
                stage="semantic",
            )
        if not normalized_result:
            return self._err(
                action,
                "SemanticError",
                "Result is empty.",
                retryable=False,
                stage="semantic",
            )

        return self._ok(action, normalized_result)

    def _attach_ul_substrate(self, result: dict[str, object]) -> dict[str, object]:
        from src.aais_ul.runtime import wrap_capability_result

        return wrap_capability_result(dict(result))


class AAISImageModule(AAISCapabilityModule):
    """Legacy image adapter."""

    module_name = "image"
    supported_actions = ("analyze", "generate", "edit")

    def _semantic_required_fields(self, action: str) -> tuple[str, ...]:
        if action == "analyze":
            return ("summary",)
        return ("asset",)


class AAISMusicModule(AAISCapabilityModule):
    """Legacy music adapter."""

    module_name = "music"
    supported_actions = (
        "analyze_track",
        "detect_bpm",
        "classify_mood",
        "generate_loop",
        "transform_style",
    )

    def _semantic_required_fields(self, action: str) -> tuple[str, ...]:
        fields = {
            "analyze_track": ("analysis",),
            "detect_bpm": ("bpm",),
            "classify_mood": ("mood",),
            "generate_loop": ("asset",),
            "transform_style": ("asset",),
        }
        return fields.get(action, ())


class AAISDocumentModule(AAISCapabilityModule):
    """Legacy document adapter."""

    module_name = "document"
    supported_actions = (
        "summarize",
        "extract_fields",
        "classify",
        "rewrite",
        "convert_format",
    )

    def _semantic_required_fields(self, action: str) -> tuple[str, ...]:
        fields = {
            "summarize": ("summary",),
            "extract_fields": ("fields",),
            "classify": ("label",),
            "rewrite": ("content",),
            "convert_format": ("asset",),
        }
        return fields.get(action, ())


class AAISFileCapabilityModule(AAISCapabilityModule):
    """Legacy file-backed adapter that validates ``source_path`` before execution."""

    def _translate_payload(self, action: str, payload: dict[str, object]) -> dict[str, object]:
        translated = dict(payload)
        source_path = _clean_text(translated.get("source_path"))
        if not source_path:
            raise ValueError("source_path is required.")
        path = Path(source_path)
        if not path.exists():
            raise FileNotFoundError(f"Source path does not exist: {path}")
        if not path.is_file():
            raise ValueError(f"Source path is not a file: {path}")
        translated["source_path"] = str(path)
        return translated


# Backward-compatible aliases that mirror the newer naming scheme.
AAISImageCapabilityModule = AAISImageModule
AAISMusicCapabilityModule = AAISMusicModule
AAISDocumentCapabilityModule = AAISDocumentModule


__all__ = [
    "AAISCapabilityModule",
    "AAISDocumentModule",
    "AAISImageModule",
    "AAISMusicModule",
    "AAISFileCapabilityModule",
    "AAISDocumentCapabilityModule",
    "AAISImageCapabilityModule",
    "AAISMusicCapabilityModule",
    "ERROR_TAXONOMY",
]

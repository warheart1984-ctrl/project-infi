"""AAIS capability-module base contract and bounded domain adapters."""

from __future__ import annotations

from datetime import datetime
from src.datetime_compat import UTC
from pathlib import Path
from typing import Any, Callable
import uuid


ERROR_TAXONOMY = {
    "InputError",
    "NetworkError",
    "FileError",
    "PermissionError",
    "TimeoutError",
    "APIError",
    "ProviderUnavailable",
    "EncodingError",
    "SemanticError",
    "SchemaError",
    "UnsupportedFormat",
    "ExecutionError",
    "UnknownError",
}


class AAISCapabilityModule:
    """Governed adapter that normalizes capability execution results."""

    module_name = "capability"
    supported_actions: frozenset[str] = frozenset()
    required_fields_by_action: dict[str, tuple[str, ...]] = {}

    def __init__(
        self,
        *,
        provider_name: str = "local",
        handlers: dict[str, Callable[[dict[str, Any]], Any]] | None = None,
    ):
        self.provider_name = " ".join(str(provider_name or "local").split()).strip() or "local"
        self.handlers = dict(handlers or {})

    @staticmethod
    def _timestamp() -> str:
        return datetime.now(UTC).isoformat()

    def _trace_meta(self, action: str, data: dict[str, Any] | None = None) -> dict[str, Any]:
        result_size = 0
        if isinstance(data, dict):
            result_size = len(data)
        elif isinstance(data, list):
            result_size = len(data)
        return {
            "provider": self.provider_name,
            "timestamp": self._timestamp(),
            "trace_id": f"{self.module_name}_{action}_{uuid.uuid4().hex}",
            "result_size": result_size,
        }

    def _ok(self, action: str, data=None, **meta):
        payload = dict(data or {})
        output = {
            "ok": True,
            "module": self.module_name,
            "action": action,
            "data": payload,
            "meta": self._trace_meta(action, payload),
        }
        output["meta"].update({key: value for key, value in meta.items() if value is not None})
        return self._attach_ul_substrate(output)

    def _err(self, action: str, error_type: str, message: str, **details):
        normalized_error = error_type if error_type in ERROR_TAXONOMY else "UnknownError"
        output = {
            "ok": False,
            "module": self.module_name,
            "action": action,
            "error_type": normalized_error,
            "message": " ".join(str(message or "").split()).strip() or normalized_error,
            "details": {key: value for key, value in details.items() if value is not None},
        }
        output["details"].setdefault("provider", self.provider_name)
        output["details"].setdefault("timestamp", self._timestamp())
        output["details"].setdefault("trace_id", f"{self.module_name}_{action}_{uuid.uuid4().hex}")
        return self._attach_ul_substrate(output)

    @staticmethod
    def _attach_ul_substrate(result: dict[str, Any]) -> dict[str, Any]:
        from src.aais_ul_substrate import wrap_capability_result

        return wrap_capability_result(dict(result))

    def _validate_input(self, action: str, payload: dict[str, Any] | None):
        if action not in self.supported_actions:
            return self._err(
                action,
                "InputError",
                f"Unsupported action for {self.module_name}: {action}",
                supported_actions=sorted(self.supported_actions),
            )
        if not isinstance(payload, dict):
            return self._err(action, "InputError", "Payload must be a dict.")
        return None

    def _semantic_check(self, action: str, result) -> tuple[bool, str | None]:
        if not isinstance(result, dict):
            return False, "Result is not a dict."
        required_fields = list(self.required_fields_by_action.get(action) or ())
        missing = [field for field in required_fields if field not in result]
        if missing:
            return False, f"Missing required fields: {missing}"
        if not result:
            return False, "Result is empty."
        return True, None

    def _translate_payload(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        return dict(payload)

    def _execute_provider_action(self, action: str, translated_payload: dict[str, Any]):
        handler = self.handlers.get(action)
        if handler is None:
            raise NotImplementedError(f"No provider handler registered for {self.module_name}.{action}")
        return handler(dict(translated_payload))

    def _normalize_result(self, action: str, result) -> dict[str, Any]:
        if isinstance(result, dict):
            return dict(result)
        return {"result": result}

    def _map_exception(self, exc: Exception) -> tuple[str, dict[str, Any]]:
        if isinstance(exc, TimeoutError):
            return "TimeoutError", {}
        if isinstance(exc, FileNotFoundError):
            return "FileError", {}
        if isinstance(exc, PermissionError):
            return "PermissionError", {}
        if isinstance(exc, UnicodeError):
            return "EncodingError", {}
        if isinstance(exc, NotImplementedError):
            return "ProviderUnavailable", {}
        if isinstance(exc, ValueError):
            return "InputError", {}
        return "ExecutionError", {"exception_class": exc.__class__.__name__}

    def execute(self, action: str, payload: dict[str, Any] | None) -> dict[str, Any]:
        input_error = self._validate_input(action, payload)
        if input_error:
            return input_error

        try:
            translated_payload = self._translate_payload(action, dict(payload or {}))
        except Exception as exc:
            error_type, details = self._map_exception(exc)
            return self._err(action, error_type, str(exc), stage="translate", **details)

        try:
            raw_result = self._execute_provider_action(action, translated_payload)
        except Exception as exc:
            error_type, details = self._map_exception(exc)
            return self._err(action, error_type, str(exc), stage="execute", **details)

        normalized_result = self._normalize_result(action, raw_result)
        ok, semantic_error = self._semantic_check(action, normalized_result)
        if not ok:
            return self._err(
                action,
                "SemanticError",
                semantic_error or "Result failed semantic validation.",
                stage="semantic_check",
                raw_result_type=type(raw_result).__name__,
            )

        return self._ok(action, normalized_result)


class AAISImageCapabilityModule(AAISCapabilityModule):
    """Bounded image capability adapter."""

    module_name = "image"
    supported_actions = frozenset({"analyze", "generate", "edit"})
    required_fields_by_action = {
        "analyze": ("summary",),
        "generate": ("asset",),
        "edit": ("asset",),
    }


class AAISMusicCapabilityModule(AAISCapabilityModule):
    """Bounded music capability adapter."""

    module_name = "music"
    supported_actions = frozenset(
        {"analyze_track", "detect_bpm", "classify_mood", "generate_loop", "transform_style"}
    )
    required_fields_by_action = {
        "analyze_track": ("analysis",),
        "detect_bpm": ("bpm",),
        "classify_mood": ("mood",),
        "generate_loop": ("asset",),
        "transform_style": ("asset",),
    }


class AAISDocumentCapabilityModule(AAISCapabilityModule):
    """Bounded document capability adapter."""

    module_name = "document"
    supported_actions = frozenset(
        {"summarize", "extract_fields", "classify", "rewrite", "convert_format"}
    )
    required_fields_by_action = {
        "summarize": ("summary",),
        "extract_fields": ("fields",),
        "classify": ("label",),
        "rewrite": ("content",),
        "convert_format": ("asset",),
    }

    def _translate_payload(self, action: str, payload: dict[str, Any]) -> dict[str, Any]:
        translated = dict(payload)
        source = translated.get("source")
        if isinstance(source, str) and source:
            translated["source"] = source
            translated["source_type"] = translated.get("source_type") or (
                "file" if Path(source).suffix else "text"
            )
        return translated

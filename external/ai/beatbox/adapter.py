"""Governed Beatbox adapter seam.

This module prepares a stable slot for future Beatbox-capable providers.
External code should fit this adapter surface instead of wiring directly into
the wider runtime.
"""

from __future__ import annotations

from collections.abc import Mapping
from typing import Any

REQUIRED_INPUT_FIELDS = ("narrative_state", "emotion", "pacing")


def _provider_name(provider: Any) -> str:
    if provider is None:
        return "none"
    return provider.__class__.__name__


def _failure_response(reason: str, *, provider: str = "none", details: Any = None) -> dict[str, Any]:
    metadata: dict[str, Any] = {"provider": provider}
    if details is not None:
        metadata["details"] = details
    return {
        "audio_file": None,
        "output": None,
        "duration": 0.0,
        "metadata": metadata,
        "status": "failed",
        "reason": reason,
    }


class SimpleBeatboxFallback:
    """Low-fidelity fallback used when no primary provider succeeds."""

    def generate(self, input_data: Mapping[str, Any]) -> dict[str, Any]:
        return {
            "audio_file": "basic_tone.wav",
            "output": "basic_tone.wav",
            "duration": 1.0,
            "metadata": {
                "quality": "low",
                "provider": "simple_fallback",
                "input_summary": {
                    "emotion": input_data.get("emotion"),
                    "pacing": input_data.get("pacing"),
                },
            },
            "status": "fallback",
        }


class BeatboxAdapter:
    """Normalized adapter for Beatbox-style audio generators."""

    def __init__(self, primary: Any = None, fallback: Any = None):
        self.primary = primary
        self.fallback = fallback

    def _validate_input(self, input_data: Any) -> dict[str, Any] | None:
        if not isinstance(input_data, Mapping):
            return _failure_response(
                "invalid_input",
                provider="adapter",
                details="input_data must be a mapping",
            )

        missing = [
            field
            for field in REQUIRED_INPUT_FIELDS
            if input_data.get(field) in (None, "", [])
        ]
        if missing:
            return _failure_response(
                "invalid_input",
                provider="adapter",
                details={"missing_fields": missing},
            )

        return None

    def _normalize_result(self, result: Any, *, provider: str) -> dict[str, Any]:
        if not isinstance(result, Mapping):
            return _failure_response(
                "invalid_provider_output",
                provider=provider,
                details="provider result must be a mapping",
            )

        audio_file = result.get("audio_file") or result.get("output")
        metadata = result.get("metadata")
        if not isinstance(metadata, Mapping):
            metadata = {}

        normalized_metadata = dict(metadata)
        normalized_metadata.setdefault("provider", provider)
        if "quality" in result and "quality" not in normalized_metadata:
            normalized_metadata["quality"] = result["quality"]

        status = result.get("status")
        if not isinstance(status, str) or not status.strip():
            status = "ok" if audio_file else "failed"

        return {
            "audio_file": audio_file,
            "output": audio_file,
            "duration": float(result.get("duration") or 0.0),
            "metadata": normalized_metadata,
            "status": status,
            "reason": result.get("reason"),
        }

    def _call_provider(self, provider: Any, input_data: Mapping[str, Any]) -> dict[str, Any]:
        provider_name = _provider_name(provider)
        result = provider.generate(input_data)
        return self._normalize_result(result, provider=provider_name)

    def generate(self, input_data: Any) -> dict[str, Any]:
        validation_error = self._validate_input(input_data)
        if validation_error is not None:
            return validation_error

        assert isinstance(input_data, Mapping)

        try:
            if self.primary:
                primary_result = self._call_provider(self.primary, input_data)
                if primary_result["status"] not in {"failed", "error"}:
                    return primary_result
        except Exception as error:  # pragma: no cover - exercised by fallback test
            primary_result = _failure_response(
                "provider_error",
                provider=_provider_name(self.primary),
                details=str(error),
            )

        try:
            if self.fallback:
                fallback_result = self._call_provider(self.fallback, input_data)
                if fallback_result["status"] not in {"failed", "error"}:
                    return fallback_result
                return fallback_result
        except Exception as error:  # pragma: no cover - defensive only
            return _failure_response(
                "provider_error",
                provider=_provider_name(self.fallback),
                details=str(error),
            )

        if self.primary or self.fallback:
            return primary_result if "primary_result" in locals() else _failure_response(
                "provider_failed",
                provider="adapter",
            )

        return _failure_response("no_provider", provider="adapter")

"""Local AAIS provider adapter for the shared Jarvis protocol."""

from __future__ import annotations

import asyncio
from typing import Any

from src.jarvis_protocol import JarvisMessage, ProviderResponse


class LocalProvider:
    """Protocol-compatible wrapper around the on-laptop AAIS model path."""

    def __init__(self, label: str = "Local Heroine") -> None:
        self.label = label

    async def invoke(
        self,
        messages: list[JarvisMessage | dict[str, Any]],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> ProviderResponse:
        """Run a non-stream local provider turn through the existing AAIS runtime."""
        del tools

        import src.api as api

        normalized_messages = [
            message if isinstance(message, JarvisMessage) else JarvisMessage.from_dict(message)
            for message in messages or []
        ]
        provider_messages = [message.to_provider_message() for message in normalized_messages]
        response_mode = str(kwargs.get("mode") or kwargs.get("response_mode") or "fast")
        max_tokens = int(kwargs.get("max_tokens") or 512)
        temperature = float(kwargs.get("temperature") or 0.7)
        routing_profile = dict(kwargs.get("routing_profile") or {})
        routing_profile.setdefault("provider", "local")
        routing_profile.setdefault("provider_label", self.label)
        routing_profile.setdefault("provider_kind", "local")
        routing_profile.setdefault("execution_backend", "local_model")

        model, _ = await asyncio.to_thread(api.init_ai)
        content = await asyncio.to_thread(
            model.generate_chat,
            provider_messages,
            max_tokens,
            temperature,
            response_mode,
            routing_profile,
        )
        generation_metadata = dict(getattr(model, "last_generation_metadata", {}) or {})

        model_name = (
            routing_profile.get("provider_model")
            or getattr(model, "text_model_name", None)
            or getattr(model, "model_name", None)
            or "local"
        )
        return ProviderResponse(
            content=str(content or "").strip(),
            provider="local",
            model=model_name,
            stop_reason=generation_metadata.get("stop_reason"),
            finish_reason=generation_metadata.get("finish_reason"),
            input_tokens=generation_metadata.get("input_tokens"),
            output_tokens=generation_metadata.get("output_tokens"),
            raw=None,
        )

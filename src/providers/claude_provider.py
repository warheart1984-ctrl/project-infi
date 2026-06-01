"""Claude provider adapter for the Jarvis protocol."""

from __future__ import annotations

import asyncio
import os
from typing import Any

from dotenv import load_dotenv

try:
    import anthropic
except ImportError:  # pragma: no cover - optional dependency
    anthropic = None

from src.jarvis_protocol import JarvisMessage, ProviderResponse, ToolResult


class ClaudeProvider:
    """Anthropic Claude adapter that speaks the shared Jarvis protocol."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str | None = None,
        client: Any | None = None,
    ) -> None:
        load_dotenv()
        self.model = (
            model
            or os.getenv("AAIS_CLAUDE_MODEL")
            or "claude-3-7-sonnet-20250219"
        )
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if client is not None:
            self.client = client
            return

        if anthropic is None:
            raise ImportError(
                "anthropic is required to use ClaudeProvider. "
                "Install it before enabling this provider."
            )

        self.client = anthropic.Anthropic(api_key=self.api_key)

    async def invoke(
        self,
        messages: list[JarvisMessage],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> ProviderResponse:
        """Invoke Claude using the shared Jarvis message contract."""
        default_system = (
            "You are Claude, the first sister of AAIS. "
            "Speak with calm precision and grounded intelligence."
        )
        system_prompt = str(kwargs.get("system") or default_system).strip()
        anthropic_messages: list[dict[str, Any]] = []

        for message in messages:
            normalized = message if isinstance(message, JarvisMessage) else JarvisMessage.from_dict(message)
            if normalized.role == "system":
                system_prompt = f"{system_prompt}\n\n{normalized.content}".strip()
                continue
            anthropic_messages.append(normalized.to_anthropic())

        request_payload = {
            "model": kwargs.get("model") or self.model,
            "messages": anthropic_messages or [{"role": "user", "content": "Hello."}],
            "system": system_prompt,
            "max_tokens": int(kwargs.get("max_tokens") or 4096),
            "temperature": float(kwargs.get("temperature") or 0.7),
        }
        if tools:
            request_payload["tools"] = list(tools)

        response = await asyncio.to_thread(self.client.messages.create, **request_payload)

        text_chunks: list[str] = []
        tool_calls: list[ToolResult] = []

        for block in getattr(response, "content", []) or []:
            block_type = getattr(block, "type", None)
            if block_type == "text":
                text_chunks.append(getattr(block, "text", "") or "")
            elif block_type == "tool_use":
                tool_calls.append(ToolResult.from_claude(block))
        usage = getattr(response, "usage", None)
        stop_reason = str(getattr(response, "stop_reason", None) or "").strip().lower() or None
        finish_reason_map = {
            "end_turn": "stop",
            "max_tokens": "length",
            "stop_sequence": "stop_sequence",
            "tool_use": "tool_calls",
            "pause_turn": "pause_turn",
            "refusal": "refusal",
        }
        finish_reason = finish_reason_map.get(stop_reason, "stop")

        return ProviderResponse(
            content="".join(text_chunks).strip(),
            tool_calls=tool_calls or None,
            provider="claude",
            model=request_payload["model"],
            stop_reason=stop_reason,
            finish_reason=finish_reason,
            input_tokens=int(getattr(usage, "input_tokens", 0) or 0) or None,
            output_tokens=int(getattr(usage, "output_tokens", 0) or 0) or None,
            raw=response,
        )

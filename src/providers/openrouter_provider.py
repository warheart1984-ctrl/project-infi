"""OpenRouter provider adapter for the Jarvis protocol."""

from __future__ import annotations

import asyncio
import json
import os
from typing import Any
from urllib import error, request

from src.jarvis_protocol import JarvisMessage, ProviderResponse
from src.providers.http_chat_provider import extract_text_content, parse_tool_calls


DEFAULT_OPENROUTER_MODEL = "openrouter/free"
DEFAULT_OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"


class OpenRouterProvider:
    """OpenAI-compatible OpenRouter adapter for free or paid routed models."""

    def __init__(
        self,
        api_key: str | None = None,
        *,
        model: str | None = None,
        endpoint: str | None = None,
        app_name: str | None = None,
        site_url: str | None = None,
        client=None,
    ) -> None:
        self.api_key = api_key or os.getenv("OPENROUTER_API_KEY")
        self.model = (
            model
            or os.getenv("AAIS_OPENROUTER_MODEL")
            or DEFAULT_OPENROUTER_MODEL
        )
        self.endpoint = (
            endpoint
            or os.getenv("AAIS_OPENROUTER_BASE_URL")
            or DEFAULT_OPENROUTER_URL
        )
        self.app_name = (
            app_name
            or os.getenv("AAIS_OPENROUTER_APP_NAME")
            or "AAIS Jarvis"
        )
        self.site_url = site_url or os.getenv("AAIS_OPENROUTER_SITE_URL") or ""
        self.client = client or self._post_json

    def _post_json(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(self.endpoint, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=90) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(f"OpenRouter request failed: {exc.code} {message}") from exc
        except error.URLError as exc:
            raise RuntimeError(f"OpenRouter request failed: {exc.reason}") from exc

    async def invoke(
        self,
        messages: list[JarvisMessage | dict[str, Any]],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> ProviderResponse:
        """Invoke OpenRouter through its OpenAI-compatible chat completions API."""
        normalized_messages = [
            message if isinstance(message, JarvisMessage) else JarvisMessage.from_dict(message)
            for message in messages or []
        ]
        provider_messages = [message.to_provider_message() for message in normalized_messages]
        request_payload: dict[str, Any] = {
            "model": kwargs.get("model") or self.model,
            "messages": provider_messages or [{"role": "user", "content": "Hello."}],
            "max_tokens": int(kwargs.get("max_tokens") or 2048),
            "max_completion_tokens": int(kwargs.get("max_tokens") or 2048),
            "temperature": float(kwargs.get("temperature") or 0.7),
        }
        if tools:
            request_payload["tools"] = list(tools)

        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
        }
        if self.site_url:
            headers["HTTP-Referer"] = self.site_url
        if self.app_name:
            headers["X-Title"] = self.app_name

        response = await asyncio.to_thread(self.client, request_payload, headers)
        choice = ((response.get("choices") or [None])[0]) or {}
        message = choice.get("message") or {}
        content = extract_text_content(message.get("content"))
        tool_calls = parse_tool_calls(message, provider_id="openrouter")
        usage = response.get("usage") or {}
        finish_reason = str(choice.get("finish_reason") or "").strip().lower() or None

        model_name = (
            response.get("model")
            or request_payload["model"]
        )
        return ProviderResponse(
            content=content,
            tool_calls=tool_calls,
            provider="openrouter",
            model=model_name,
            stop_reason=finish_reason,
            finish_reason=finish_reason,
            input_tokens=int(usage.get("prompt_tokens") or 0) or None,
            output_tokens=int(usage.get("completion_tokens") or 0) or None,
            raw=response,
        )

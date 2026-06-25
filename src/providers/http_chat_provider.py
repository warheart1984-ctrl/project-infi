"""OpenAI-compatible HTTP chat adapter shared by frontier model providers."""

from __future__ import annotations

import asyncio
import json
import os
from dataclasses import dataclass, field
from typing import Any, Callable, Iterator
from urllib import error, request

from src.jarvis_protocol import JarvisMessage, ProviderResponse, ToolResult


def extract_text_content(content: Any) -> str:
    if isinstance(content, str):
        return content.strip()
    if isinstance(content, list):
        chunks: list[str] = []
        for item in content:
            if isinstance(item, dict):
                if item.get("type") == "text" and item.get("text"):
                    chunks.append(str(item.get("text")))
                elif item.get("content"):
                    chunks.append(str(item.get("content")))
            elif item is not None:
                chunks.append(str(item))
        return "".join(chunks).strip()
    return str(content or "").strip()


def parse_tool_calls(message: dict[str, Any] | None, *, provider_id: str) -> list[ToolResult] | None:
    tool_calls = (message or {}).get("tool_calls") or []
    normalized: list[ToolResult] = []
    for item in tool_calls:
        function_payload = item.get("function") or {}
        arguments = function_payload.get("arguments") or {}
        if isinstance(arguments, str):
            try:
                arguments = json.loads(arguments)
            except json.JSONDecodeError:
                arguments = {"raw": arguments}
        normalized.append(
            ToolResult(
                id=item.get("id"),
                name=function_payload.get("name") or item.get("name"),
                arguments=dict(arguments or {}),
                provider=provider_id,
                kind=str(item.get("type") or "tool_call"),
            )
        )
    return normalized or None


@dataclass(slots=True)
class HttpChatProviderConfig:
    """Runtime configuration for one OpenAI-compatible chat endpoint."""

    provider_id: str
    default_model: str
    endpoint: str
    api_key: str | None = None
    app_name: str | None = None
    site_url: str | None = None
    extra_headers: dict[str, str] = field(default_factory=dict)
    default_extra_body: dict[str, Any] = field(default_factory=dict)
    timeout_sec: int = 90


class HttpChatProvider:
    """Invoke remote chat models through an OpenAI-compatible completions API."""

    def __init__(
        self,
        config: HttpChatProviderConfig,
        *,
        client: Callable[[dict[str, Any], dict[str, str]], dict[str, Any]] | None = None,
    ) -> None:
        self.config = config
        self.provider_id = config.provider_id
        self.model = config.default_model
        self.endpoint = config.endpoint
        self.api_key = config.api_key
        self.client = client or self._post_json

    def _post_json(self, payload: dict[str, Any], headers: dict[str, str]) -> dict[str, Any]:
        body = json.dumps(payload).encode("utf-8")
        req = request.Request(self.endpoint, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self.config.timeout_sec) as response:
                return json.loads(response.read().decode("utf-8"))
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"{self.provider_id} request failed: {exc.code} {message}"
            ) from exc
        except error.URLError as exc:
            raise RuntimeError(f"{self.provider_id} request failed: {exc.reason}") from exc

    def _build_headers(self) -> dict[str, str]:
        headers = {
            "Authorization": f"Bearer {self.api_key or ''}",
            "Content-Type": "application/json",
        }
        if self.config.site_url:
            headers["HTTP-Referer"] = self.config.site_url
        if self.config.app_name:
            headers["X-Title"] = self.config.app_name
        headers.update(self.config.extra_headers)
        return headers

    def _build_request_payload(
        self,
        messages: list[JarvisMessage | dict[str, Any]],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> dict[str, Any]:
        normalized_messages = [
            message if isinstance(message, JarvisMessage) else JarvisMessage.from_dict(message)
            for message in messages or []
        ]
        provider_messages = [message.to_provider_message() for message in normalized_messages]
        max_tokens = int(kwargs.get("max_tokens") or 2048)
        request_payload: dict[str, Any] = {
            "model": kwargs.get("model") or self.model,
            "messages": provider_messages or [{"role": "user", "content": "Hello."}],
            "max_tokens": max_tokens,
            "temperature": float(kwargs.get("temperature") if kwargs.get("temperature") is not None else 0.7),
        }
        if kwargs.get("top_p") is not None:
            request_payload["top_p"] = float(kwargs["top_p"])
        if "max_completion_tokens" not in request_payload:
            request_payload["max_completion_tokens"] = max_tokens
        if tools:
            request_payload["tools"] = list(tools)
        extra_body = dict(self.config.default_extra_body)
        extra_body.update(dict(kwargs.get("extra_body") or {}))
        if extra_body:
            request_payload.update(extra_body)
        return request_payload

    def _parse_completion_response(
        self,
        response: dict[str, Any],
        *,
        request_model: str,
    ) -> ProviderResponse:
        choice = ((response.get("choices") or [None])[0]) or {}
        message = choice.get("message") or {}
        content = extract_text_content(message.get("content"))
        tool_calls = parse_tool_calls(message, provider_id=self.provider_id)
        usage = response.get("usage") or {}
        finish_reason = str(choice.get("finish_reason") or "").strip().lower() or None
        model_name = response.get("model") or request_model

        return ProviderResponse(
            content=content,
            tool_calls=tool_calls,
            provider=self.provider_id,
            model=model_name,
            stop_reason=finish_reason,
            finish_reason=finish_reason,
            input_tokens=int(usage.get("prompt_tokens") or 0) or None,
            output_tokens=int(usage.get("completion_tokens") or 0) or None,
            raw=response,
        )

    def invoke_sync(
        self,
        messages: list[JarvisMessage | dict[str, Any]],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> ProviderResponse:
        """Blocking invoke for sync callers (FastAPI sync routes, LawfulLLM)."""
        request_payload = self._build_request_payload(messages, tools, **kwargs)
        response = self.client(request_payload, self._build_headers())
        return self._parse_completion_response(
            response,
            request_model=str(request_payload["model"]),
        )

    def iter_stream_sync(
        self,
        messages: list[JarvisMessage | dict[str, Any]],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ) -> Iterator[dict[str, Any]]:
        """Blocking SSE iterator for sync streaming handlers."""
        request_payload = self._build_request_payload(messages, tools, **kwargs)
        yield from self._iter_sse_json(request_payload, self._build_headers())

    async def invoke(
        self,
        messages: list[JarvisMessage | dict[str, Any]],
        tools: list[dict] | None = None,
        **kwargs,
    ) -> ProviderResponse:
        request_payload = self._build_request_payload(messages, tools, **kwargs)

        response = await asyncio.to_thread(
            self.client,
            request_payload,
            self._build_headers(),
        )
        return self._parse_completion_response(
            response,
            request_model=str(request_payload["model"]),
        )

    def _iter_sse_json(self, payload: dict[str, Any], headers: dict[str, str]) -> Iterator[dict[str, Any]]:
        stream_payload = {**payload, "stream": True}
        body = json.dumps(stream_payload).encode("utf-8")
        req = request.Request(self.endpoint, data=body, headers=headers, method="POST")
        try:
            with request.urlopen(req, timeout=self.config.timeout_sec) as response:
                for raw_line in response:
                    line = raw_line.decode("utf-8", errors="replace").strip()
                    if not line or not line.startswith("data:"):
                        continue
                    data = line[5:].strip()
                    if data == "[DONE]":
                        return
                    try:
                        yield json.loads(data)
                    except json.JSONDecodeError:
                        continue
        except error.HTTPError as exc:
            message = exc.read().decode("utf-8", errors="replace")
            raise RuntimeError(
                f"{self.provider_id} stream failed: {exc.code} {message}"
            ) from exc
        except error.URLError as exc:
            raise RuntimeError(f"{self.provider_id} stream failed: {exc.reason}") from exc

    async def invoke_stream(
        self,
        messages: list[JarvisMessage | dict[str, Any]],
        tools: list[dict] | None = None,
        **kwargs: Any,
    ):
        request_payload = self._build_request_payload(messages, tools, **kwargs)
        headers = self._build_headers()

        def _collect() -> list[dict[str, Any]]:
            return list(self._iter_sse_json(request_payload, headers))

        chunks = await asyncio.to_thread(_collect)
        for chunk in chunks:
            yield chunk


def env_flag(name: str, *, default: bool = False) -> bool:
    raw = os.getenv(name, "").strip().lower()
    if not raw:
        return default
    return raw in {"1", "true", "yes", "on"}

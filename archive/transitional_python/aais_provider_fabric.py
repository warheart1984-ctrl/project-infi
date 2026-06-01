from __future__ import annotations

from collections.abc import Iterable, Iterator
from dataclasses import dataclass, field
import json
import os
from typing import Any, Protocol

import requests

from .aais_evolving_protocol import (
    JarvisMessage,
    ToolResult,
    build_provider_payload,
)


class ProviderAdapter(Protocol):
    name: str

    def complete(
        self,
        *,
        model: str,
        messages: list[JarvisMessage],
        mode: str,
        temperature: float,
        max_tokens: int,
        metadata: dict[str, Any] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        ...

    def stream(
        self,
        *,
        model: str,
        messages: list[JarvisMessage],
        mode: str,
        temperature: float,
        max_tokens: int,
        metadata: dict[str, Any] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Iterator[str]:
        ...

    def capabilities(self) -> dict[str, Any]:
        ...


@dataclass(slots=True)
class OpenAICompatibleAdapter:
    base_url: str
    api_key: str | None = None
    timeout: int = 180
    name: str = "openai-compatible"

    def _headers(self) -> dict[str, str]:
        headers = {"Content-Type": "application/json", "Accept": "application/json, text/event-stream"}
        if self.api_key:
            headers["Authorization"] = f"Bearer {self.api_key}"
        return headers

    def complete(
        self,
        *,
        model: str,
        messages: list[JarvisMessage],
        mode: str,
        temperature: float,
        max_tokens: int,
        metadata: dict[str, Any] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        payload = build_provider_payload(
            model=model,
            messages=messages,
            stream=False,
            temperature=temperature,
            max_tokens=max_tokens,
            mode=mode,
            metadata=metadata,
            attachments=attachments,
            tools=tools,
        )
        response = requests.post(self.base_url, headers=self._headers(), json=payload, timeout=self.timeout)
        response.raise_for_status()
        data = response.json()
        return self._extract_text(data)

    def stream(
        self,
        *,
        model: str,
        messages: list[JarvisMessage],
        mode: str,
        temperature: float,
        max_tokens: int,
        metadata: dict[str, Any] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> Iterator[str]:
        payload = build_provider_payload(
            model=model,
            messages=messages,
            stream=True,
            temperature=temperature,
            max_tokens=max_tokens,
            mode=mode,
            metadata=metadata,
            attachments=attachments,
            tools=tools,
        )
        with requests.post(
            self.base_url,
            headers=self._headers(),
            json=payload,
            timeout=self.timeout,
            stream=True,
        ) as response:
            response.raise_for_status()
            for raw in response.iter_lines(decode_unicode=True):
                if not raw:
                    continue
                line = raw.strip()
                if line.startswith("data:"):
                    line = line[5:].strip()
                if line == "[DONE]":
                    break
                try:
                    payload = json.loads(line)
                except json.JSONDecodeError:
                    yield line
                    continue
                chunk = self._extract_text(payload)
                if chunk:
                    yield chunk

    def capabilities(self) -> dict[str, Any]:
        return {
            "chat": True,
            "stream": True,
            "tool_calls": True,
            "attachments": True,
            "protocol": "AAIS-JARVIS",
        }

    def _extract_text(self, payload: Any) -> str:
        if isinstance(payload, str):
            return payload
        if isinstance(payload, list):
            for item in payload:
                text = self._extract_text(item)
                if text:
                    return text
            return ""
        if not isinstance(payload, dict):
            return str(payload)

        choices = payload.get("choices")
        if isinstance(choices, list) and choices:
            return self._extract_text(choices[0])

        for key in ("message", "delta", "content", "text", "response", "output_text"):
            value = payload.get(key)
            if isinstance(value, str):
                return value
            if isinstance(value, dict):
                nested = self._extract_text(value)
                if nested:
                    return nested
        return ""


@dataclass(slots=True)
class ClaudeAdapterBridge:
    name: str = "claude"

    def normalize_messages(self, messages: list[JarvisMessage]) -> tuple[str | None, list[dict[str, Any]]]:
        system_parts: list[str] = []
        provider_messages: list[dict[str, Any]] = []
        for message in messages:
            if message.role == "system":
                system_parts.append(message.content)
                continue
            provider_messages.append(message.to_anthropic())
        system = "\n\n".join(part for part in system_parts if part)
        return system or None, provider_messages

    def normalize_tool_result(self, payload: dict[str, Any]) -> ToolResult:
        return ToolResult.from_claude(payload)

    def capabilities(self) -> dict[str, Any]:
        return {
            "chat": True,
            "stream": True,
            "tool_calls": True,
            "attachments": True,
            "protocol": "AAIS-JARVIS",
        }


@dataclass(slots=True)
class MockAdapter:
    name: str = "mock"

    def complete(
        self,
        *,
        model: str,
        messages: list[JarvisMessage],
        mode: str,
        temperature: float,
        max_tokens: int,
        metadata: dict[str, Any] | None = None,
        attachments: list[dict[str, Any]] | None = None,
        tools: list[dict[str, Any]] | None = None,
    ) -> str:
        last_user = next((m.content for m in reversed(messages) if m.role == "user"), "How can I help?")
        return f"[mock:{mode}:{model}] {last_user}"

    def stream(self, **kwargs: Any) -> Iterator[str]:
        yield self.complete(**kwargs)

    def capabilities(self) -> dict[str, Any]:
        return {"chat": True, "stream": True, "protocol": "AAIS-JARVIS"}


@dataclass(slots=True)
class ProviderRegistry:
    providers: dict[str, ProviderAdapter] = field(default_factory=dict)
    default_provider: str = "mock"

    def register(self, name: str, provider: ProviderAdapter) -> None:
        self.providers[name] = provider

    def get(self, name: str | None = None) -> ProviderAdapter:
        selected = name or self.default_provider
        if selected in self.providers:
            return self.providers[selected]
        if self.default_provider in self.providers:
            return self.providers[self.default_provider]
        raise KeyError(f"No provider registered for {selected!r}")


def build_registry_from_env() -> ProviderRegistry:
    registry = ProviderRegistry(default_provider=os.getenv("AAIS_PROVIDER", "mock"))
    registry.register("mock", MockAdapter())
    url = os.getenv("AAIS_API_URL") or os.getenv("FORGE_API_URL") or os.getenv("LLM_API_URL")
    key = os.getenv("AAIS_API_KEY") or os.getenv("FORGE_API_KEY") or os.getenv("LLM_API_KEY")
    if url:
        registry.register("openai-compatible", OpenAICompatibleAdapter(base_url=url, api_key=key))
        if registry.default_provider == "mock":
            registry.default_provider = "openai-compatible"
    return registry

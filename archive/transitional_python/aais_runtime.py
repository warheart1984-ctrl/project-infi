from __future__ import annotations

from collections.abc import Iterator
from dataclasses import dataclass, field
from typing import Any

from .aais_evolving_protocol import JarvisMessage, build_protocol_envelope
from .aais_provider_fabric import ProviderAdapter, ProviderRegistry


@dataclass(slots=True)
class AAISTurnRequest:
    user_message: str
    system_prompt: str
    mode: str = "chat"
    model: str = "default"
    provider: str | None = None
    temperature: float = 0.35
    max_tokens: int = 700
    stream: bool = False
    runtime_context: str | None = None
    workspace_context: str | None = None
    research_context: str | None = None
    memory_context: str | None = None
    tool_context: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class AAISTurnResponse:
    content: str
    protocol_id: str
    protocol_version: str
    provider: str
    model: str
    mode: str
    envelope: dict[str, Any]


class AAISRuntime:
    def __init__(self, registry: ProviderRegistry) -> None:
        self.registry = registry

    def _messages_from_envelope(self, envelope: dict[str, Any]) -> list[JarvisMessage]:
        messages: list[JarvisMessage] = []
        for payload in envelope["messages"]:
            messages.append(
                JarvisMessage(
                    role=str(payload["role"]),
                    content=str(payload["content"]),
                    channel=str(payload.get("channel", "dialogue")),
                    metadata=dict(payload.get("metadata", {}) or {}),
                )
            )
        return messages

    def complete(self, request: AAISTurnRequest) -> AAISTurnResponse:
        provider = self.registry.get(request.provider)
        envelope = build_protocol_envelope(
            system_prompt=request.system_prompt,
            user_message=request.user_message,
            runtime_context=request.runtime_context,
            workspace_context=request.workspace_context,
            research_context=request.research_context,
            memory_context=request.memory_context,
            tool_context=request.tool_context,
            metadata=request.metadata,
        )
        messages = self._messages_from_envelope(envelope)
        content = provider.complete(
            model=request.model,
            messages=messages,
            mode=request.mode,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            metadata=request.metadata,
        )
        protocol = envelope["protocol"]
        return AAISTurnResponse(
            content=content,
            protocol_id=str(protocol["id"]),
            protocol_version=str(protocol["version"]),
            provider=provider.name,
            model=request.model,
            mode=request.mode,
            envelope=envelope,
        )

    def stream(self, request: AAISTurnRequest) -> Iterator[str]:
        provider = self.registry.get(request.provider)
        envelope = build_protocol_envelope(
            system_prompt=request.system_prompt,
            user_message=request.user_message,
            runtime_context=request.runtime_context,
            workspace_context=request.workspace_context,
            research_context=request.research_context,
            memory_context=request.memory_context,
            tool_context=request.tool_context,
            metadata=request.metadata,
        )
        messages = self._messages_from_envelope(envelope)
        yield from provider.stream(
            model=request.model,
            messages=messages,
            mode=request.mode,
            temperature=request.temperature,
            max_tokens=request.max_tokens,
            metadata=request.metadata,
        )

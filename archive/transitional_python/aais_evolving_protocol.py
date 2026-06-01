from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

PROTOCOL_ID = "AAIS-JARVIS"
PROTOCOL_VERSION = "1.0.0"
ROLES = ("system", "user", "assistant", "tool")
CHANNELS = (
    "runtime",
    "workspace",
    "research",
    "memory",
    "tool",
    "dialogue",
)


@dataclass(slots=True)
class JarvisMessage:
    role: str
    content: str
    channel: str = "dialogue"
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_provider(self) -> dict[str, str]:
        return {"role": self.role, "content": self.content}

    def to_openai(self) -> dict[str, str]:
        return self.to_provider()

    def to_anthropic(self) -> dict[str, str]:
        return self.to_provider()

    def as_dict(self) -> dict[str, Any]:
        payload = {
            "role": self.role,
            "content": self.content,
            "channel": self.channel,
        }
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(slots=True)
class ToolCall:
    id: str
    name: str
    arguments: dict[str, Any] = field(default_factory=dict)


@dataclass(slots=True)
class ToolResult:
    id: str
    name: str
    content: str
    arguments: dict[str, Any] = field(default_factory=dict)
    metadata: dict[str, Any] = field(default_factory=dict)

    @classmethod
    def from_claude(cls, payload: dict[str, Any]) -> "ToolResult":
        return cls(
            id=str(payload.get("id", "tool_result")),
            name=str(payload.get("name", "tool")),
            content=str(payload.get("output", payload.get("content", ""))),
            arguments=dict(payload.get("input", {}) or {}),
            metadata={"source": "claude"},
        )

    def to_message(self) -> JarvisMessage:
        return JarvisMessage(
            role="tool",
            content=self.content,
            channel="tool",
            metadata={"tool_name": self.name, "tool_call_id": self.id, **self.metadata},
        )


def protocol_spec() -> dict[str, Any]:
    return {
        "id": PROTOCOL_ID,
        "version": PROTOCOL_VERSION,
        "roles": list(ROLES),
        "channels": list(CHANNELS),
        "description": (
            "AAIS protocol contract for normalized messages, provider payloads, "
            "tool outputs, and orchestration context."
        ),
    }


def collapse_for_provider(messages: list[JarvisMessage | dict[str, Any]]) -> list[dict[str, str]]:
    collapsed: list[dict[str, str]] = []
    for message in messages:
        if isinstance(message, JarvisMessage):
            collapsed.append(message.to_provider())
            continue
        collapsed.append(
            {
                "role": str(message["role"]),
                "content": str(message["content"]),
            }
        )
    return collapsed


def build_provider_payload(
    *,
    model: str,
    messages: list[JarvisMessage | dict[str, Any]],
    stream: bool,
    temperature: float,
    max_tokens: int,
    mode: str,
    metadata: dict[str, Any] | None = None,
    attachments: list[dict[str, Any]] | None = None,
    tools: list[dict[str, Any]] | None = None,
) -> dict[str, Any]:
    envelope_metadata = dict(metadata or {})
    envelope_metadata.setdefault("protocol_id", PROTOCOL_ID)
    envelope_metadata.setdefault("protocol_version", PROTOCOL_VERSION)
    envelope_metadata.setdefault("mode", mode)

    payload: dict[str, Any] = {
        "model": model,
        "messages": collapse_for_provider(messages),
        "stream": stream,
        "temperature": temperature,
        "max_tokens": max_tokens,
        "mode": mode,
        "metadata": envelope_metadata,
    }
    if attachments:
        payload["attachments"] = attachments
    if tools:
        payload["tools"] = tools
    return payload


def build_protocol_envelope(
    *,
    system_prompt: str,
    user_message: str,
    runtime_context: str | None = None,
    workspace_context: str | None = None,
    research_context: str | None = None,
    memory_context: str | None = None,
    tool_context: str | None = None,
    prior_messages: list[JarvisMessage] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    messages: list[JarvisMessage] = []
    messages.append(JarvisMessage(role="system", content=system_prompt, channel="runtime"))
    if runtime_context:
        messages.append(JarvisMessage(role="system", content=runtime_context, channel="runtime"))
    if workspace_context:
        messages.append(JarvisMessage(role="system", content=workspace_context, channel="workspace"))
    if research_context:
        messages.append(JarvisMessage(role="system", content=research_context, channel="research"))
    if memory_context:
        messages.append(JarvisMessage(role="system", content=memory_context, channel="memory"))
    if tool_context:
        messages.append(JarvisMessage(role="system", content=tool_context, channel="tool"))
    if prior_messages:
        messages.extend(prior_messages)
    messages.append(JarvisMessage(role="user", content=user_message, channel="dialogue"))
    return {
        "protocol": protocol_spec(),
        "metadata": dict(metadata or {}),
        "messages": [message.as_dict() for message in messages],
    }

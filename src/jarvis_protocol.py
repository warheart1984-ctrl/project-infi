"""Canonical message and tool protocol for AAIS Jarvis.

Jarvis already had an implied language: roles, context blocks, tool envelopes,
and provider payloads all roughly shared one structure. This module makes that
language explicit so AAIS can reason about one stable protocol across the UI,
runtime, tools, specialists, and model backends.
"""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from dataclasses import dataclass, field
from typing import Any

from src.jarvis_reasoning_protocol import reasoning_protocol_spec
from src.cog_runtime import cognitive_runtime_family_spec, nova_cortex_spec
from src.speaking_runtime import speaking_runtime_spec


PROTOCOL_ID = "jarvis.protocol"
PROTOCOL_VERSION = "0.1"

SUPPORTED_ROLES = ("system", "user", "assistant", "tool")
SUPPORTED_CHANNELS = (
    "instruction",
    "runtime",
    "archive",
    "memory",
    "continuity",
    "workspace",
    "research",
    "corrigibility",
    "browser",
    "specialist",
    "orchestration",
    "dialogue",
    "tool",
)


def _clip_text(value: Any, limit: int = 200) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _normalize_role(role: str | None) -> str:
    cleaned = str(role or "assistant").strip().lower()
    return cleaned if cleaned in SUPPORTED_ROLES else "assistant"


def _normalize_channel(channel: str | None, role: str) -> str:
    cleaned = str(channel or "").strip().lower().replace("-", "_")
    if cleaned in SUPPORTED_CHANNELS:
        return cleaned
    if role == "system":
        return "instruction"
    if role == "tool":
        return "tool"
    return "dialogue"


@dataclass(slots=True)
class ProtocolMessage:
    role: str
    content: str
    channel: str = "dialogue"
    name: str | None = None
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "role": _normalize_role(self.role),
            "content": str(self.content or ""),
            "channel": _normalize_channel(self.channel, self.role),
        }
        if self.name:
            payload["name"] = self.name
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload

    def to_provider_message(self) -> dict[str, str]:
        payload = self.to_dict()
        return _wrap_ul_payload({
            "role": payload["role"],
            "content": payload["content"],
        })


@dataclass(slots=True)
class JarvisMessage(ProtocolMessage):
    """Concrete protocol message object used by provider adapters."""

    @classmethod
    def from_dict(cls, payload: dict[str, Any]) -> "JarvisMessage":
        return cls(
            role=str(payload.get("role") or "assistant"),
            content=str(payload.get("content") or ""),
            channel=str(payload.get("channel") or "dialogue"),
            name=payload.get("name"),
            metadata=dict(payload.get("metadata") or {}),
        )

    def to_anthropic(self) -> dict[str, Any]:
        """Render a message in Anthropic-compatible role/content form."""
        role = _normalize_role(self.role)
        if role == "system":
            role = "user"
        if role == "tool":
            role = "assistant"
        return _wrap_ul_payload({
            "role": role if role in {"user", "assistant"} else "user",
            "content": str(self.content or ""),
        })


@dataclass(slots=True)
class ToolResult:
    """Normalized tool call or tool outcome carried through Jarvis."""

    id: str | None = None
    name: str | None = None
    arguments: dict[str, Any] = field(default_factory=dict)
    output: Any = None
    provider: str | None = None
    kind: str = "tool_call"

    def to_dict(self) -> dict[str, Any]:
        return _wrap_ul_payload({
            "id": self.id,
            "name": self.name,
            "arguments": dict(self.arguments or {}),
            "output": self.output,
            "provider": self.provider,
            "kind": self.kind,
        })

    @classmethod
    def from_claude(cls, block: Any) -> "ToolResult":
        """Normalize one Anthropic tool block into Jarvis protocol form."""
        if isinstance(block, dict):
            block_type = block.get("type")
            block_id = block.get("id")
            block_name = block.get("name")
            block_input = block.get("input")
        else:
            block_type = getattr(block, "type", None)
            block_id = getattr(block, "id", None)
            block_name = getattr(block, "name", None)
            block_input = getattr(block, "input", None)

        return cls(
            id=block_id,
            name=block_name,
            arguments=dict(block_input or {}),
            provider="claude",
            kind="tool_call" if block_type == "tool_use" else str(block_type or "tool_call"),
        )


@dataclass(slots=True)
class ProviderResponse:
    """Normalized provider response returned back to the Jarvis brain."""

    content: str
    tool_calls: list[ToolResult] | None = None
    provider: str | None = None
    model: str | None = None
    stop_reason: str | None = None
    finish_reason: str | None = None
    input_tokens: int | None = None
    output_tokens: int | None = None
    raw: Any = None

    def to_dict(self) -> dict[str, Any]:
        return _wrap_ul_payload({
            "content": self.content,
            "tool_calls": [tool.to_dict() for tool in self.tool_calls or []],
            "provider": self.provider,
            "model": self.model,
            "stop_reason": self.stop_reason,
            "finish_reason": self.finish_reason,
            "input_tokens": self.input_tokens,
            "output_tokens": self.output_tokens,
        })


def protocol_spec() -> dict[str, Any]:
    """Return the stable AAIS Jarvis protocol contract."""
    return _wrap_ul_payload({
        "id": PROTOCOL_ID,
        "version": PROTOCOL_VERSION,
        "summary": (
            "Shared Jarvis message language for dialogue, runtime context, tools, "
            "specialists, and provider routing."
        ),
        "roles": list(SUPPORTED_ROLES),
        "channels": list(SUPPORTED_CHANNELS),
        "tool_envelope": {
            "shape": {"tool": "name", "args": {"...": "..."}},
            "example": {
                "tool": "spatial_reason",
                "args": {
                    "mode": "geo_distance",
                    "space_id": "michigan_route",
                    "from": "Grayling",
                    "to": "TraverseCity",
                },
            },
        },
        "provider_payload": {
            "shape": {
                "model": "model-id",
                "messages": [{"role": "system", "content": "..."}],
                "stream": True,
                "temperature": 0.35,
                "max_tokens": 320,
                "mode": "builder",
            },
            "notes": [
                "Messages follow an OpenAI-style role/content list.",
                "AAIS keeps richer per-message channel metadata in its internal Jarvis protocol envelope.",
            ],
        },
        "reasoning_protocol": reasoning_protocol_spec(),
        "speaking_runtime": speaking_runtime_spec(),
        "nova_cortex": nova_cortex_spec(),
        "cognitive_runtime_family": cognitive_runtime_family_spec(),
    })


def normalize_messages(messages: list[dict[str, Any]] | None) -> list[dict[str, Any]]:
    """Normalize arbitrary message-like dicts into the Jarvis protocol shape."""
    normalized: list[dict[str, Any]] = []
    for message in messages or []:
        if not isinstance(message, dict):
            continue
        role = _normalize_role(message.get("role"))
        content = str(message.get("content") or "").strip()
        if not content:
            continue
        normalized.append(
            ProtocolMessage(
                role=role,
                content=content,
                channel=message.get("channel"),
                name=message.get("name"),
                metadata=message.get("metadata") or {},
            ).to_dict()
        )
    return normalized


def summarize_protocol(
    *,
    session_id: str,
    messages: list[dict[str, Any]] | None,
    response_mode: str | None,
    persona_mode: str | None,
    tool_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a compact summary of the active Jarvis protocol state."""
    normalized = normalize_messages(messages)
    channels: list[str] = []
    for message in normalized:
        channel = message.get("channel")
        if channel and channel not in channels:
            channels.append(channel)

    return _wrap_ul_payload({
        "id": PROTOCOL_ID,
        "version": PROTOCOL_VERSION,
        "session_id": session_id,
        "message_count": len(normalized),
        "channels": channels,
        "roles": sorted({message["role"] for message in normalized}),
        "response_mode": response_mode,
        "persona_mode": persona_mode,
        "tool_active": bool(tool_result),
        "tool_type": (tool_result or {}).get("type"),
    })


def build_turn_envelope(
    *,
    session_id: str,
    messages: list[dict[str, Any]] | None,
    response_mode: str | None,
    persona_mode: str | None,
    current_goal: str | None,
    tool_result: dict[str, Any] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build the full internal Jarvis protocol envelope for one AAIS turn."""
    normalized = normalize_messages(messages)
    provider_messages = [
        {
            "role": message["role"],
            "content": message["content"],
        }
        for message in normalized
    ]
    return _wrap_ul_payload({
        "protocol": {
            "id": PROTOCOL_ID,
            "version": PROTOCOL_VERSION,
        },
        "session": {
            "id": session_id,
            "current_goal": current_goal,
            "response_mode": response_mode,
            "persona_mode": persona_mode,
        },
        "messages": normalized,
        "provider_messages": provider_messages,
        "tool_result": tool_result,
        "metadata": dict(metadata or {}),
    })


def build_provider_payload(
    *,
    model: str,
    messages: list[dict[str, Any]] | None,
    stream: bool,
    temperature: float,
    max_tokens: int,
    mode: str | None = None,
    attachments: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Build a provider-facing payload from the internal Jarvis protocol envelope."""
    normalized = normalize_messages(messages)
    return _wrap_ul_payload({
        "model": model,
        "messages": [
            {
                "role": message["role"],
                "content": message["content"],
            }
            for message in normalized
        ],
        "stream": bool(stream),
        "temperature": temperature,
        "max_tokens": int(max_tokens),
        "mode": mode,
        "attachments": list(attachments or []),
        "metadata": {
            "protocol_id": PROTOCOL_ID,
            "protocol_version": PROTOCOL_VERSION,
            **dict(metadata or {}),
        },
    })


def describe_protocol_use(
    *,
    session_id: str,
    messages: list[dict[str, Any]] | None,
    response_mode: str | None,
    persona_mode: str | None,
    current_goal: str | None,
    tool_result: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Return a concise human-facing description of how Jarvis is using the protocol."""
    summary = summarize_protocol(
        session_id=session_id,
        messages=messages,
        response_mode=response_mode,
        persona_mode=persona_mode,
        tool_result=tool_result,
    )
    return _wrap_ul_payload({
        **summary,
        "summary": (
            f"Jarvis is using {PROTOCOL_ID}/{PROTOCOL_VERSION} with "
            f"{summary['message_count']} normalized messages across "
            f"{', '.join(summary['channels']) or 'dialogue'}."
        ),
        "current_goal": _clip_text(current_goal, limit=160),
    })

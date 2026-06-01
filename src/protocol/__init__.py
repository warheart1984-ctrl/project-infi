"""Protocol package compatibility layer for Jarvis message contracts."""

from src.jarvis_protocol import (
    JarvisMessage,
    ProtocolMessage,
    ProviderResponse,
    ToolResult,
    build_provider_payload,
    build_turn_envelope,
    describe_protocol_use,
    normalize_messages,
    protocol_spec,
    summarize_protocol,
)

__all__ = [
    "JarvisMessage",
    "ProtocolMessage",
    "ProviderResponse",
    "ToolResult",
    "build_provider_payload",
    "build_turn_envelope",
    "describe_protocol_use",
    "normalize_messages",
    "protocol_spec",
    "summarize_protocol",
]

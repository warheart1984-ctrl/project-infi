"""Agent-specific RuntimeSystemLaw (separate from default Velvet chat VS-01)."""

from __future__ import annotations

from dataclasses import dataclass, field

from nova.lawful_llm import RuntimeSystemLaw


@dataclass(frozen=True)
class AgentRuntimeSystemLaw(RuntimeSystemLaw):
    """Expanded capabilities for operator agent planning (not default chat)."""

    allowed_capabilities: frozenset[str] = field(
        default_factory=lambda: frozenset(
            {"observe", "reason", "summarize", "files", "plan", "agent_plan"}
        )
    )


DEFAULT_AGENT_LAW = AgentRuntimeSystemLaw()

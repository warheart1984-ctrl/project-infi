"""
src2/jarvis_modular.py

Jarvis modular context pipeline.

Purpose
-------
This module builds provider-facing messages from explicit context modules instead
of one flattened system blob. It also exposes a protocol/debug view so the final
assembly is inspectable.

Design goals
------------
- Stable, deterministic assembly order
- Mode-specific module stacks
- Easy to extend with workspace / agent runner state
- Provider-facing messages remain separate from raw internal state
- Clean protocol view for /api/jarvis/protocol

Python: 3.10+
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, Iterable, List, Mapping, Optional, Sequence, Tuple


# ============================================================================
# Core dataclasses
# ============================================================================


@dataclass(slots=True)
class ChatMessage:
    role: str
    content: str
    name: Optional[str] = None

    def to_provider_dict(self) -> Dict[str, Any]:
        data: Dict[str, Any] = {
            "role": self.role,
            "content": self.content,
        }
        if self.name:
            data["name"] = self.name
        return data


@dataclass(slots=True)
class ModuleOutput:
    """
    Standardized output from a module.

    section:
        A stable logical grouping, e.g. "runtime_context", "workspace_context",
        "knowledge_context", "mission_context", etc.

    content:
        Arbitrary structured data. The payload formatter decides how to render it.

    priority:
        Lower number = earlier render order within the same pipeline stage.
    """

    name: str
    section: str
    content: Any
    priority: int = 100
    metadata: Dict[str, Any] = field(default_factory=dict)

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "name": self.name,
            "section": self.section,
            "content": self.content,
            "priority": self.priority,
            "metadata": self.metadata,
        }


@dataclass(slots=True)
class ProviderPreview:
    """
    Final provider-facing payload summary. Useful for protocol inspection.
    """

    model: Optional[str]
    provider_messages: List[Dict[str, Any]]
    rendered_sections: List[str]
    module_order: List[str]

    def to_public_dict(self) -> Dict[str, Any]:
        return {
            "model": self.model,
            "provider_messages": self.provider_messages,
            "rendered_sections": self.rendered_sections,
            "module_order": self.module_order,
        }


@dataclass(slots=True)
class AssemblyState:
    """
    Shared immutable-ish state passed to modules.

    You can shape this however you want in api.py before calling the builder.
    """

    session_id: Optional[str] = None
    mode: str = "default"
    model: Optional[str] = None

    # User / conversation state
    user_input: str = ""
    conversation: List[ChatMessage] = field(default_factory=list)

    # Runtime / app state
    runtime_context: Dict[str, Any] = field(default_factory=dict)
    workspace_context: Dict[str, Any] = field(default_factory=dict)
    knowledge_context: Dict[str, Any] = field(default_factory=dict)
    mission_context: Dict[str, Any] = field(default_factory=dict)

    # Tooling / attachments / runner
    tool_results: List[Dict[str, Any]] = field(default_factory=list)
    attachments: List[Dict[str, Any]] = field(default_factory=list)
    runner_state: Dict[str, Any] = field(default_factory=dict)

    # Optional knobs
    flags: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)

    def get(self, key: str, default: Any = None) -> Any:
        return getattr(self, key, default)


@dataclass(slots=True)
class BuildResult:
    """
    Primary output for provider calls and protocol inspection.
    """

    context_modules: List[str]
    modules: List[ModuleOutput]
    provider_messages: List[ChatMessage]
    provider_preview: ProviderPreview

    def to_protocol_dict(self) -> Dict[str, Any]:
        return {
            "context_modules": self.context_modules,
            "modules": [m.to_public_dict() for m in self.modules],
            "provider_messages": [m.to_provider_dict() for m in self.provider_messages],
            "provider_preview": self.provider_preview.to_public_dict(),
        }


# ============================================================================
# Module interface
# ============================================================================


class ContextModule(ABC):
    """
    Base class for every context module.

    Contract:
    - enabled(): decide if the module should run for this state
    - build(): return ModuleOutput or None
    """

    name: str = "context_module"
    stage: str = "context"
    priority: int = 100

    def enabled(self, state: AssemblyState) -> bool:
        return True

    @abstractmethod
    def build(self, state: AssemblyState) -> Optional[ModuleOutput]:
        raise NotImplementedError


# ============================================================================
# Helpers
# ============================================================================


def utc_now_iso() -> str:
    return datetime.now(timezone.utc).isoformat()


def compact_jsonish(value: Any, indent: int = 0) -> str:
    """
    Lightweight deterministic renderer for structured values.
    Keeps this file dependency-free.
    """
    pad = " " * indent

    if value is None:
        return "null"
    if isinstance(value, bool):
        return "true" if value else "false"
    if isinstance(value, (int, float)):
        return str(value)
    if isinstance(value, str):
        return value
    if isinstance(value, Mapping):
        lines: List[str] = []
        for key, item in value.items():
            rendered = compact_jsonish(item, indent + 2)
            if "\n" in rendered:
                lines.append(f"{pad}{key}:")
                lines.append(rendered)
            else:
                lines.append(f"{pad}{key}: {rendered}")
        return "\n".join(lines)
    if isinstance(value, Sequence) and not isinstance(value, (str, bytes, bytearray)):
        lines = []
        for item in value:
            rendered = compact_jsonish(item, indent + 2)
            if "\n" in rendered:
                lines.append(f"{pad}-")
                lines.append(rendered)
            else:
                lines.append(f"{pad}- {rendered}")
        return "\n".join(lines)

    return str(value)


def render_section(title: str, content: Any) -> str:
    rendered = compact_jsonish(content, indent=2).strip()
    if not rendered:
        rendered = "(empty)"
    return f"{title}\n{rendered}"


# ============================================================================
# Concrete modules
# ============================================================================


class ProtocolContextModule(ContextModule):
    name = "ProtocolContextModule"
    stage = "context"
    priority = 10

    def build(self, state: AssemblyState) -> Optional[ModuleOutput]:
        content = {
            "session_id": state.session_id,
            "mode": state.mode,
            "model": state.model,
            "timestamp_utc": utc_now_iso(),
            "flags": state.flags,
            "metadata": state.metadata,
        }
        return ModuleOutput(
            name=self.name,
            section="runtime_context",
            content=content,
            priority=self.priority,
        )


class RuntimeContextModule(ContextModule):
    name = "RuntimeContextModule"
    stage = "context"
    priority = 20

    def enabled(self, state: AssemblyState) -> bool:
        return bool(state.runtime_context)

    def build(self, state: AssemblyState) -> Optional[ModuleOutput]:
        return ModuleOutput(
            name=self.name,
            section="runtime_context",
            content=state.runtime_context,
            priority=self.priority,
        )


class WorkspaceContextModule(ContextModule):
    name = "WorkspaceContextModule"
    stage = "context"
    priority = 30

    def enabled(self, state: AssemblyState) -> bool:
        return bool(state.workspace_context) or bool(state.runner_state)

    def build(self, state: AssemblyState) -> Optional[ModuleOutput]:
        content = dict(state.workspace_context)

        if state.runner_state:
            content.setdefault("runner", {})
            if isinstance(content["runner"], dict):
                content["runner"] = {
                    **content["runner"],
                    **state.runner_state,
                }
            else:
                content["runner"] = state.runner_state

        if not content:
            return None

        return ModuleOutput(
            name=self.name,
            section="workspace_context",
            content=content,
            priority=self.priority,
        )


class MissionContextModule(ContextModule):
    name = "MissionContextModule"
    stage = "context"
    priority = 40

    def enabled(self, state: AssemblyState) -> bool:
        return bool(state.mission_context)

    def build(self, state: AssemblyState) -> Optional[ModuleOutput]:
        return ModuleOutput(
            name=self.name,
            section="mission_context",
            content=state.mission_context,
            priority=self.priority,
        )


class KnowledgeModule(ContextModule):
    name = "KnowledgeModule"
    stage = "context"
    priority = 50

    def enabled(self, state: AssemblyState) -> bool:
        return bool(state.knowledge_context)

    def build(self, state: AssemblyState) -> Optional[ModuleOutput]:
        return ModuleOutput(
            name=self.name,
            section="knowledge_context",
            content=state.knowledge_context,
            priority=self.priority,
        )


class ToolResultsModule(ContextModule):
    name = "ToolResultsModule"
    stage = "context"
    priority = 60

    def enabled(self, state: AssemblyState) -> bool:
        return bool(state.tool_results)

    def build(self, state: AssemblyState) -> Optional[ModuleOutput]:
        return ModuleOutput(
            name=self.name,
            section="tool_results",
            content=state.tool_results,
            priority=self.priority,
            metadata={"count": len(state.tool_results)},
        )


class AttachmentsModule(ContextModule):
    name = "AttachmentsModule"
    stage = "context"
    priority = 70

    def enabled(self, state: AssemblyState) -> bool:
        return bool(state.attachments)

    def build(self, state: AssemblyState) -> Optional[ModuleOutput]:
        return ModuleOutput(
            name=self.name,
            section="attachments",
            content=state.attachments,
            priority=self.priority,
            metadata={"count": len(state.attachments)},
        )


class ProviderPayloadModule(ContextModule):
    """
    Final formatter-only module.

    Important:
    This should not become the new hidden logic blob.
    It only turns already-built modules into provider-facing text blocks.
    """

    name = "ProviderPayloadModule"
    stage = "payload"
    priority = 999

    SECTION_TITLES: Dict[str, str] = {
        "runtime_context": "Runtime context",
        "workspace_context": "Workspace context",
        "mission_context": "Mission context",
        "knowledge_context": "Knowledge context",
        "tool_results": "Tool results",
        "attachments": "Attachments",
    }

    def build(self, state: AssemblyState) -> Optional[ModuleOutput]:
        return ModuleOutput(
            name=self.name,
            section="provider_payload",
            content={"note": "payload_formatter"},
            priority=self.priority,
        )

    def render_context_blocks(self, modules: Sequence[ModuleOutput]) -> List[str]:
        blocks: List[str] = []

        for mod in modules:
            if mod.section == "provider_payload":
                continue

            title = self.SECTION_TITLES.get(mod.section, mod.section.replace("_", " ").title())
            blocks.append(render_section(title, mod.content))

        return blocks


# ============================================================================
# Pipeline registry
# ============================================================================


def default_pipeline() -> List[ContextModule]:
    return [
        ProtocolContextModule(),
        RuntimeContextModule(),
        WorkspaceContextModule(),
        MissionContextModule(),
        KnowledgeModule(),
        ToolResultsModule(),
        AttachmentsModule(),
        ProviderPayloadModule(),
    ]


MODE_PIPELINES: Dict[str, List[ContextModule]] = {
    "default": default_pipeline(),
    "research": [
        ProtocolContextModule(),
        RuntimeContextModule(),
        MissionContextModule(),
        KnowledgeModule(),
        ToolResultsModule(),
        AttachmentsModule(),
        ProviderPayloadModule(),
    ],
    "operator": [
        ProtocolContextModule(),
        RuntimeContextModule(),
        WorkspaceContextModule(),
        ToolResultsModule(),
        AttachmentsModule(),
        ProviderPayloadModule(),
    ],
    "mystic": [
        ProtocolContextModule(),
        RuntimeContextModule(),
        MissionContextModule(),
        KnowledgeModule(),
        ProviderPayloadModule(),
    ],
}


# ============================================================================
# Builder internals
# ============================================================================


def get_pipeline_for_mode(
    mode: str,
    registry: Optional[Mapping[str, Sequence[ContextModule]]] = None,
) -> List[ContextModule]:
    registry = registry or MODE_PIPELINES
    if mode in registry:
        return list(registry[mode])
    return list(registry.get("default", default_pipeline()))


def collect_module_outputs(
    state: AssemblyState,
    pipeline: Sequence[ContextModule],
) -> Tuple[List[str], List[ModuleOutput], Optional[ProviderPayloadModule]]:
    outputs: List[ModuleOutput] = []
    context_module_names: List[str] = []
    payload_module: Optional[ProviderPayloadModule] = None

    for module in pipeline:
        context_module_names.append(module.name)

        if isinstance(module, ProviderPayloadModule):
            payload_module = module

        try:
            if not module.enabled(state):
                continue
            result = module.build(state)
            if result is not None:
                outputs.append(result)
        except Exception as exc:  # pragma: no cover
            outputs.append(
                ModuleOutput(
                    name=f"{module.name}:error",
                    section="runtime_context",
                    content={
                        "module_error": module.name,
                        "error_type": type(exc).__name__,
                        "error_message": str(exc),
                    },
                    priority=5,
                    metadata={"degraded": True},
                )
            )

    outputs.sort(key=lambda item: (item.priority, item.name))
    return context_module_names, outputs, payload_module


def assemble_provider_messages(
    state: AssemblyState,
    modules: Sequence[ModuleOutput],
    payload_module: Optional[ProviderPayloadModule],
) -> Tuple[List[ChatMessage], ProviderPreview]:
    payload_module = payload_module or ProviderPayloadModule()

    context_blocks = payload_module.render_context_blocks(modules)

    provider_messages: List[ChatMessage] = []

    if context_blocks:
        provider_messages.append(
            ChatMessage(
                role="system",
                content="\n\n".join(context_blocks),
            )
        )

    provider_messages.extend(state.conversation)

    if state.user_input.strip():
        provider_messages.append(
            ChatMessage(
                role="user",
                content=state.user_input.strip(),
            )
        )

    preview = ProviderPreview(
        model=state.model,
        provider_messages=[msg.to_provider_dict() for msg in provider_messages],
        rendered_sections=[m.section for m in modules if m.section != "provider_payload"],
        module_order=[m.name for m in modules],
    )
    return provider_messages, preview


# ============================================================================
# Public API
# ============================================================================


def build_provider_turn(
    state: AssemblyState,
    pipeline_registry: Optional[Mapping[str, Sequence[ContextModule]]] = None,
) -> BuildResult:
    pipeline = get_pipeline_for_mode(state.mode, pipeline_registry)
    context_modules, modules, payload_module = collect_module_outputs(state, pipeline)
    provider_messages, preview = assemble_provider_messages(state, modules, payload_module)

    return BuildResult(
        context_modules=context_modules,
        modules=modules,
        provider_messages=provider_messages,
        provider_preview=preview,
    )


def build_protocol_view(
    state: AssemblyState,
    pipeline_registry: Optional[Mapping[str, Sequence[ContextModule]]] = None,
) -> Dict[str, Any]:
    result = build_provider_turn(state, pipeline_registry=pipeline_registry)
    return result.to_protocol_dict()


# ============================================================================
# Optional workspace / agent bridge helpers
# ============================================================================


def make_runner_state(
    *,
    active_task: Optional[Dict[str, Any]] = None,
    artifacts: Optional[List[Dict[str, Any]]] = None,
    steps: Optional[List[Dict[str, Any]]] = None,
    status: Optional[str] = None,
    scratchpad: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    result: Dict[str, Any] = {}
    if active_task is not None:
        result["active_task"] = active_task
    if artifacts is not None:
        result["artifacts"] = artifacts
    if steps is not None:
        result["steps"] = steps
    if status is not None:
        result["status"] = status
    if scratchpad is not None:
        result["scratchpad"] = scratchpad
    return result


def merge_workspace_context(
    base: Optional[Dict[str, Any]],
    runner_state: Optional[Dict[str, Any]],
) -> Dict[str, Any]:
    output: Dict[str, Any] = dict(base or {})
    if runner_state:
        output.setdefault("runner", {})
        if isinstance(output["runner"], dict):
            output["runner"] = {**output["runner"], **runner_state}
        else:
            output["runner"] = dict(runner_state)
    return output


# ============================================================================
# Example integration helpers
# ============================================================================


def from_api_inputs(
    *,
    session_id: Optional[str],
    mode: str,
    model: Optional[str],
    user_input: str,
    conversation: Iterable[Mapping[str, Any]] = (),
    runtime_context: Optional[Dict[str, Any]] = None,
    workspace_context: Optional[Dict[str, Any]] = None,
    knowledge_context: Optional[Dict[str, Any]] = None,
    mission_context: Optional[Dict[str, Any]] = None,
    tool_results: Optional[List[Dict[str, Any]]] = None,
    attachments: Optional[List[Dict[str, Any]]] = None,
    runner_state: Optional[Dict[str, Any]] = None,
    flags: Optional[Dict[str, Any]] = None,
    metadata: Optional[Dict[str, Any]] = None,
) -> AssemblyState:
    msgs: List[ChatMessage] = []
    for item in conversation:
        role = str(item.get("role", "user"))
        content = str(item.get("content", ""))
        name = item.get("name")
        msgs.append(ChatMessage(role=role, content=content, name=name))

    return AssemblyState(
        session_id=session_id,
        mode=mode,
        model=model,
        user_input=user_input,
        conversation=msgs,
        runtime_context=runtime_context or {},
        workspace_context=workspace_context or {},
        knowledge_context=knowledge_context or {},
        mission_context=mission_context or {},
        tool_results=tool_results or [],
        attachments=attachments or [],
        runner_state=runner_state or {},
        flags=flags or {},
        metadata=metadata or {},
    )


# ============================================================================
# Minimal self-test demo
# ============================================================================


if __name__ == "__main__":
    demo_state = from_api_inputs(
        session_id="sess_demo_001",
        mode="operator",
        model="gpt-5.4-thinking",
        user_input="Summarize the current workspace state and next action.",
        conversation=[
            {"role": "user", "content": "Open the research workspace."},
            {"role": "assistant", "content": "Workspace opened."},
        ],
        runtime_context={
            "environment": "dev",
            "provider": "openai",
        },
        workspace_context={
            "workspace_id": "ws_123",
            "workspace_name": "AAIS Lab",
        },
        knowledge_context={
            "memory_hits": [
                {"title": "AAIS architecture notes", "score": 0.92},
            ]
        },
        mission_context={
            "goal": "Keep Jarvis modular and inspectable",
            "constraints": ["no hidden prompt blob", "stable provider assembly"],
        },
        tool_results=[
            {"tool": "search", "status": "ok", "result_count": 3},
        ],
        attachments=[
            {"name": "design.md", "type": "text/markdown"},
        ],
        runner_state=make_runner_state(
            status="idle",
            active_task={"name": "workspace_sync", "phase": "ready"},
            artifacts=[{"id": "art_1", "kind": "note"}],
        ),
    )

    built = build_provider_turn(demo_state)
    print("=== Protocol View ===")
    print(compact_jsonish(built.to_protocol_dict()))

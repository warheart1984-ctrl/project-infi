"""Modular Jarvis message assembly ported from the evolving_ai service pattern.

This layer keeps Jarvis local-first while making context assembly explicit and
pluggable. Each module contributes a slice of provider-facing context without
forcing Jarvis to become a second app shell.
"""

# Mythic: Jarvis Modular
# Engineering: JarvisModularEngine
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
import hashlib
import json
from typing import Any

from src.aais_ul import build_ul_snapshot
from src.angels_and_wards import DEFAULT_DOCTRINE as ANGELS_AND_WARDS
from src.jarvis_reasoning_protocol import build_reasoning_packet, reasoning_protocol_spec
from src.cog_runtime.coherence_projection import (
    build_coherence_projection,
    format_coherence_projection_block,
)
from src.operator_cognition_coherence_fabric import (
    build_governance_coherence_projection,
    format_governance_coherence_block,
    governance_coherence_projection_enabled,
)
from src.cog_runtime import cognitive_runtime_family_spec, nova_cortex_spec
from src.speaking_runtime import speaking_runtime_spec
from src.jarvis_protocol import JarvisMessage, build_provider_payload, normalize_messages
from src.six_wards_guardrails import (
    DEFAULT_DOCTRINE as SIX_WARDS_DOCTRINE,
    GuardrailState as SixWardState,
    JarvisSixWards,
)
from src.writers_3_rules import (
    ALLOWED_GROWTH_ZONES,
    PROTECTED_ZONES,
    WRITERS_3_RULES,
    can_evolve,
)


CHANNEL_LABELS = {
    "instruction": "System instruction",
    "runtime": "Runtime context",
    "governance": "Governance coherence",
    "cognitive": "Nova cognitive state",
    "memory": "Memory context",
    "workspace": "Workspace context",
    "research": "Knowledge context",
    "corrigibility": "Corrigibility context",
    "browser": "Browser context",
    "specialist": "Specialist context",
    "orchestration": "Mission context",
    "tool": "Tool context",
}

CHANNEL_ORDER = {
    "instruction": 0,
    "runtime": 1,
    "governance": 2,
    "cognitive": 3,
    "memory": 4,
    "workspace": 5,
    "research": 6,
    "browser": 7,
    "specialist": 8,
    "orchestration": 9,
    "corrigibility": 10,
    "tool": 11,
    "dialogue": 12,
}


@dataclass(slots=True)
class ContextModule:
    """One modular context block destined for a provider-facing turn."""

    channel: str
    label: str
    content: str
    role: str = "system"
    metadata: dict[str, Any] = field(default_factory=dict)
    source_module: str | None = None

    def to_dict(self) -> dict[str, Any]:
        payload = {
            "channel": self.channel,
            "label": self.label,
            "content": self.content,
            "role": self.role,
        }
        if self.source_module:
            payload["source_module"] = self.source_module
        if self.metadata:
            payload["metadata"] = dict(self.metadata)
        return payload


@dataclass(slots=True)
class ModularContext:
    """Normalized turn inputs passed through the modular pipeline."""

    messages: list[dict[str, Any]]
    tool_result: dict[str, Any] | None = None
    attachments: list[dict[str, Any]] | None = None
    metadata: dict[str, Any] = field(default_factory=dict)


def _clean_text(value: Any) -> str:
    return " ".join(str(value or "").split()).strip()


def _channel_label(channel: str | None) -> str:
    normalized = str(channel or "instruction").strip().lower()
    return CHANNEL_LABELS.get(normalized, normalized.replace("_", " ").title())


def _format_module_content(label: str, content: str, channel: str) -> str:
    cleaned = str(content or "").strip()
    if not cleaned:
        return ""
    if channel == "instruction":
        return cleaned
    lower_cleaned = cleaned.lower()
    lower_label = label.lower()
    if lower_cleaned.startswith(f"{lower_label}:"):
        return cleaned
    return f"{label}:\n{cleaned}"


def _summarize_tool_result(tool_result: dict[str, Any] | None) -> str:
    payload = dict(tool_result or {})
    if not payload:
        return ""

    summary = _clean_text(payload.get("summary"))
    tool_type = _clean_text(payload.get("type"))
    status = _clean_text(payload.get("status"))
    action = payload.get("action") or {}
    action_label = _clean_text(action.get("label") or action.get("id"))

    lines: list[str] = []
    if summary:
        lines.append(summary)
    elif tool_type:
        label = tool_type.replace("_", " ")
        if status:
            lines.append(f"{label.title()} finished with status {status}.")
        else:
            lines.append(f"{label.title()} completed.")

    if action_label:
        lines.append(f"Action: {action_label}")

    result = payload.get("result")
    if isinstance(result, dict):
        for key in ("state_label", "trial", "next_action", "reason"):
            value = _clean_text(result.get(key))
            if value:
                lines.append(f"{key.replace('_', ' ').title()}: {value}")
                break

    return "\n".join(dict.fromkeys(lines))


class BaseContextModule:
    """Interface for one modular Jarvis context contributor."""

    name = "BaseModule"
    order = 50

    def collect(self, context: ModularContext) -> list[ContextModule]:
        return []

    def finalize_payload(
        self,
        payload: dict[str, Any],
        *,
        context: ModularContext,
        modules: list[dict[str, Any]],
        provider_messages: list[JarvisMessage],
    ) -> dict[str, Any]:
        return payload


class ProtocolContextModule(BaseContextModule):
    """Preserve non-research system modules already present in Jarvis protocol messages."""

    name = "ProtocolContextModule"
    order = 10

    def collect(self, context: ModularContext) -> list[ContextModule]:
        modules: list[ContextModule] = []
        for message in context.messages:
            if message.get("role") != "system":
                continue
            channel = str(message.get("channel") or "instruction")
            if channel == "research":
                continue
            content = str(message.get("content") or "").strip()
            if not content:
                continue
            modules.append(
                ContextModule(
                    channel=channel,
                    label=_channel_label(channel),
                    content=content,
                    metadata=dict(message.get("metadata") or {}),
                    source_module=self.name,
                )
            )
        return modules


class KnowledgeModule(BaseContextModule):
    """Extract research/knowledge context as a first-class provider module."""

    name = "KnowledgeModule"
    order = 20

    def collect(self, context: ModularContext) -> list[ContextModule]:
        modules: list[ContextModule] = []
        for message in context.messages:
            if message.get("role") != "system":
                continue
            channel = str(message.get("channel") or "")
            if channel != "research":
                continue
            content = str(message.get("content") or "").strip()
            if not content:
                continue
            modules.append(
                ContextModule(
                    channel="research",
                    label=_channel_label("research"),
                    content=content,
                    metadata=dict(message.get("metadata") or {}),
                    source_module=self.name,
                )
            )
        return modules


class ToolResultsModule(BaseContextModule):
    """Expose the latest direct tool/action output as provider context."""

    name = "ToolResultsModule"
    order = 30

    def collect(self, context: ModularContext) -> list[ContextModule]:
        tool_content = _summarize_tool_result(context.tool_result)
        if not tool_content:
            return []
        return [
            ContextModule(
                channel="tool",
                label=_channel_label("tool"),
                content=tool_content,
                metadata={"tool_type": str((context.tool_result or {}).get("type") or "")},
                source_module=self.name,
            )
        ]


class AttachmentsModule(BaseContextModule):
    """Summarize non-text attachments so providers can use them consistently."""

    name = "AttachmentsModule"
    order = 40

    def collect(self, context: ModularContext) -> list[ContextModule]:
        attachments = list(context.attachments or [])
        if not attachments:
            return []

        lines: list[str] = []
        for item in attachments:
            if not isinstance(item, dict):
                continue
            label = _clean_text(item.get("name") or item.get("label") or item.get("kind"))
            detail = _clean_text(item.get("summary") or item.get("mime_type"))
            if label and detail:
                lines.append(f"- {label}: {detail}")
            elif label:
                lines.append(f"- {label}")

        if not lines:
            return []

        return [
            ContextModule(
                channel="tool",
                label="Attachment context",
                content="\n".join(lines),
                metadata={"source": "attachments"},
                source_module=self.name,
            )
        ]


class ProviderPayloadModule(BaseContextModule):
    """Finalize provider payload metadata from the assembled module graph."""

    name = "ProviderPayloadModule"
    order = 90

    def finalize_payload(
        self,
        payload: dict[str, Any],
        *,
        context: ModularContext,
        modules: list[dict[str, Any]],
        provider_messages: list[JarvisMessage],
    ) -> dict[str, Any]:
        metadata = dict(payload.get("metadata") or {})
        metadata.update(
            {
                "module_count": len([message for message in provider_messages if message.role == "system"]),
                "module_names": [module["source_module"] for module in modules if module.get("source_module")],
                "module_channels": [module["channel"] for module in modules if module.get("channel")],
            }
        )
        payload["metadata"] = metadata
        return payload


class OperatorGovernanceCoherenceModule(BaseContextModule):
    """Project read-only operator governance coherence into provider messages."""

    name = "OperatorGovernanceCoherenceModule"
    order = 14

    def collect(self, context: ModularContext) -> list[ContextModule]:
        if not governance_coherence_projection_enabled():
            return []
        projection = build_governance_coherence_projection()
        content = format_governance_coherence_block(projection)
        if not content.strip():
            return []
        return [
            ContextModule(
                channel="governance",
                label="Governance coherence",
                content=content,
                metadata={
                    "projection_version": projection.get("projection_version"),
                    "read_only": True,
                    "source": "operator_cognition_coherence_fabric",
                    "fabric_genes_aligned": projection.get("fabric_genes_aligned"),
                },
                source_module=self.name,
            )
        ]


class NovaCoherenceProjectionModule(BaseContextModule):
    """Project read-only Nova Cortex state into provider messages before generation."""

    name = "NovaCoherenceProjectionModule"
    order = 15

    def collect(self, context: ModularContext) -> list[ContextModule]:
        projection = build_coherence_projection(context.metadata)
        if not projection:
            return []
        content = format_coherence_projection_block(projection)
        if not content.strip():
            return []
        return [
            ContextModule(
                channel="cognitive",
                label="Nova cognitive state",
                content=content,
                metadata={
                    "projection_version": projection.get("projection_version"),
                    "read_only": True,
                    "source": "coherence_projection",
                },
                source_module=self.name,
            )
        ]


context_modules = [
    ProtocolContextModule(),
    OperatorGovernanceCoherenceModule(),
    NovaCoherenceProjectionModule(),
    KnowledgeModule(),
    ToolResultsModule(),
    AttachmentsModule(),
    ProviderPayloadModule(),
]

DEFAULT_CONTEXT_MODULES = context_modules
SIX_WARDS = JarvisSixWards()
GUARDRAIL_EVALUATION_VERSION = "v1"

MODE_PIPELINES = {
    "default": list(DEFAULT_CONTEXT_MODULES),
    "research": [
        ProtocolContextModule(),
        NovaCoherenceProjectionModule(),
        KnowledgeModule(),
        ToolResultsModule(),
        AttachmentsModule(),
        ProviderPayloadModule(),
    ],
    "operator": [
        ProtocolContextModule(),
        NovaCoherenceProjectionModule(),
        ToolResultsModule(),
        AttachmentsModule(),
        ProviderPayloadModule(),
    ],
    "mystic": [
        ProtocolContextModule(),
        NovaCoherenceProjectionModule(),
        KnowledgeModule(),
        ProviderPayloadModule(),
    ],
}


def _resolve_pipeline_mode(mode: str | None) -> str:
    normalized = " ".join(str(mode or "default").strip().lower().split())
    if normalized in MODE_PIPELINES:
        return normalized
    if normalized in {"builder", "fast", "think", "debug"}:
        return "default"
    return "default"


def _get_pipeline_for_mode(mode: str | None) -> list[BaseContextModule]:
    return list(MODE_PIPELINES.get(_resolve_pipeline_mode(mode), MODE_PIPELINES["default"]))


def _resolve_active_modules(
    mode: str | None,
    modules: list[BaseContextModule] | None,
    metadata: dict[str, Any] | None,
) -> tuple[list[BaseContextModule], dict[str, Any]]:
    normalized_metadata = dict(metadata or {})
    adaptive_zone = normalized_metadata.get("adaptive_zone") or normalized_metadata.get("proposal_zone")
    mode_pipeline = _get_pipeline_for_mode(mode)
    requested_override = modules is not None
    override_allowed = not requested_override
    override_blocked = False

    if requested_override:
        override_allowed = can_evolve(adaptive_zone)
        if override_allowed:
            active_modules = list(modules or [])
        else:
            active_modules = mode_pipeline
            override_blocked = True
    else:
        active_modules = mode_pipeline

    summary = "Jarvis modular pipeline is operating inside the default protected contract."
    status = "nominal"
    if requested_override and override_allowed:
        status = "allow"
        summary = (
            f"Adaptive module override was allowed inside the approved zone '{adaptive_zone}'."
        )
    elif requested_override and override_blocked:
        status = "blocked"
        summary = (
            "Requested modular override was rejected because it falls outside approved growth zones."
        )

    guardrail_state = {
        "status": status,
        "summary": summary,
        "rules": list(WRITERS_3_RULES),
        "protected_zones": sorted(PROTECTED_ZONES),
        "allowed_growth_zones": sorted(ALLOWED_GROWTH_ZONES),
        "adaptive_zone": adaptive_zone,
        "adaptive_zone_allowed": can_evolve(adaptive_zone) if adaptive_zone else None,
        "requested_override": requested_override,
        "override_blocked": override_blocked,
        "preserve_core": True,
        "inspectable": True,
        "requested_pipeline": [module.name for module in list(modules or [])],
        "effective_pipeline": [module.name for module in active_modules],
        "pipeline_mode": _resolve_pipeline_mode(mode),
    }
    return active_modules, guardrail_state


def _normalize_context(
    messages: list[dict[str, Any]] | None,
    *,
    tool_result: dict[str, Any] | None = None,
    attachments: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
) -> ModularContext:
    return ModularContext(
        messages=normalize_messages(messages),
        tool_result=dict(tool_result or {}) or None,
        attachments=list(attachments or []),
        metadata=dict(metadata or {}),
    )


def _coerce_float_metadata(metadata: dict[str, Any], key: str, default: float = 0.0) -> float:
    try:
        return float(metadata.get(key, default))
    except (TypeError, ValueError):
        return default


def _coerce_int_metadata(metadata: dict[str, Any], key: str, default: int = 0) -> int:
    try:
        return int(metadata.get(key, default))
    except (TypeError, ValueError):
        return default


def _build_doctrine_state(
    *,
    mode: str | None,
    metadata: dict[str, Any],
    guardrail_state: dict[str, Any],
    modules: list[dict[str, Any]],
    provider_messages: list[JarvisMessage],
    provider_payload: dict[str, Any],
) -> dict[str, Any]:
    pipeline_mode = _resolve_pipeline_mode(mode)
    adaptive_zone = guardrail_state.get("adaptive_zone")
    requested_override = bool(guardrail_state.get("requested_override"))
    protected_zone_touched = bool(
        requested_override and adaptive_zone in set(guardrail_state.get("protected_zones") or [])
    )
    effective_pipeline = list(guardrail_state.get("effective_pipeline") or [])
    requested_pipeline = list(guardrail_state.get("requested_pipeline") or [])
    provider_metadata = dict(provider_payload.get("metadata") or {})
    module_channels = [
        str(module.get("channel") or "").strip().lower()
        for module in modules
        if str(module.get("channel") or "").strip()
    ]
    unique_channels = {channel for channel in module_channels if channel}

    broken_contract_detected = bool(
        "ProviderPayloadModule" not in effective_pipeline
        or "module_count" not in provider_metadata
    )
    nondeterministic_assembly_detected = len(effective_pipeline) != len(set(effective_pipeline))
    direct_provider_mutation_detected = bool(
        requested_override and adaptive_zone == "provider_assembly_contracts"
    )
    boundary_breach_detected = bool(
        guardrail_state.get("override_blocked")
        or protected_zone_touched
        or direct_provider_mutation_detected
    )
    context_contamination_detected = bool(
        metadata.get("context_contamination_detected")
        or metadata.get("context_contamination")
    )
    stale_context_promoted = bool(
        metadata.get("stale_context_promoted")
        or metadata.get("stale_context_bleed_detected")
    )
    tool_failure_marked_authoritative = bool(metadata.get("tool_failure_marked_authoritative"))
    hidden_subsystem_detected = bool(metadata.get("hidden_subsystem_detected"))
    degraded_reasoning_detected = bool(metadata.get("degraded_reasoning_detected"))
    overload_detected = bool(metadata.get("overload_detected"))

    return {
        "core_identity": {
            "name": "Jarvis",
            "mode": pipeline_mode,
            "provider": provider_metadata.get("provider"),
            "model": provider_payload.get("model"),
        },
        "core_identity_changed": bool(metadata.get("core_identity_changed")),
        "protected_zone_touched": protected_zone_touched,
        "unstable_merge_detected": bool(guardrail_state.get("override_blocked")),
        "broken_contract_detected": broken_contract_detected,
        "module_contract_break_detected": broken_contract_detected,
        "nondeterministic_assembly_detected": nondeterministic_assembly_detected,
        "boundary_breach_detected": boundary_breach_detected,
        "direct_provider_mutation_detected": direct_provider_mutation_detected,
        "provider_bypass_detected": direct_provider_mutation_detected,
        "hidden_subsystem_detected": hidden_subsystem_detected,
        "context_contamination_detected": context_contamination_detected,
        "stale_context_promoted": stale_context_promoted,
        "stale_context_bleed_detected": stale_context_promoted,
        "tool_failure_marked_authoritative": tool_failure_marked_authoritative,
        "trace_available": bool(modules),
        "provider_preview_available": bool(provider_payload.get("messages")),
        "protocol_view_available": bool(provider_messages),
        "repetition_score": _coerce_float_metadata(metadata, "repetition_score", 0.0),
        "recursion_depth": _coerce_int_metadata(metadata, "recursion_depth", 0),
        "degraded_reasoning_detected": degraded_reasoning_detected,
        "overload_detected": overload_detected,
        "mode": pipeline_mode,
        "metadata": {
            "adaptive_zone": adaptive_zone,
            "requested_override": requested_override,
            "requested_pipeline": requested_pipeline,
            "effective_pipeline": effective_pipeline,
            "module_channels": module_channels,
            "unique_channel_count": len(unique_channels),
        },
    }


def _build_doctrine_trace(
    *,
    mode: str | None,
    metadata: dict[str, Any],
    guardrail_state: dict[str, Any],
    modules: list[dict[str, Any]],
    provider_messages: list[JarvisMessage],
    provider_payload: dict[str, Any],
) -> dict[str, Any]:
    doctrine_state = _build_doctrine_state(
        mode=mode,
        metadata=metadata,
        guardrail_state=guardrail_state,
        modules=modules,
        provider_messages=provider_messages,
        provider_payload=provider_payload,
    )
    six_ward_state = SixWardState(
        core_identity=dict(doctrine_state.get("core_identity") or {}),
        core_identity_changed=bool(doctrine_state.get("core_identity_changed")),
        protected_zone_touched=bool(doctrine_state.get("protected_zone_touched")),
        unstable_merge_detected=bool(doctrine_state.get("unstable_merge_detected")),
        broken_contract_detected=bool(doctrine_state.get("broken_contract_detected")),
        nondeterministic_assembly_detected=bool(doctrine_state.get("nondeterministic_assembly_detected")),
        boundary_breach_detected=bool(doctrine_state.get("boundary_breach_detected")),
        direct_provider_mutation_detected=bool(doctrine_state.get("direct_provider_mutation_detected")),
        hidden_subsystem_detected=bool(doctrine_state.get("hidden_subsystem_detected")),
        context_contamination_detected=bool(doctrine_state.get("context_contamination_detected")),
        stale_context_promoted=bool(doctrine_state.get("stale_context_promoted")),
        tool_failure_marked_authoritative=bool(doctrine_state.get("tool_failure_marked_authoritative")),
        trace_available=bool(doctrine_state.get("trace_available")),
        provider_preview_available=bool(doctrine_state.get("provider_preview_available")),
        protocol_view_available=bool(doctrine_state.get("protocol_view_available")),
        repetition_score=float(doctrine_state.get("repetition_score", 0.0)),
        recursion_depth=int(doctrine_state.get("recursion_depth", 0)),
        degraded_reasoning_detected=bool(doctrine_state.get("degraded_reasoning_detected")),
        overload_detected=bool(doctrine_state.get("overload_detected")),
        mode=str(doctrine_state.get("mode") or _resolve_pipeline_mode(mode)),
        metadata=dict(doctrine_state.get("metadata") or {}),
    )
    six_wards = SIX_WARDS.summary(six_ward_state)
    angels_and_wards = ANGELS_AND_WARDS.to_public_dict(doctrine_state)
    return {
        "state": doctrine_state,
        "angels_and_wards": angels_and_wards,
        "six_wards": {
            **six_wards,
            "doctrine": dict(SIX_WARDS_DOCTRINE),
        },
        "preserve_core": bool(angels_and_wards.get("core_safe")) and bool(six_wards.get("passed")),
    }


def _collect_doctrine_tags(doctrine: dict[str, Any], pipeline_mode: str) -> list[str]:
    tags: list[str] = [f"pipeline:{pipeline_mode}", "runtime:readout_only"]
    if doctrine.get("preserve_core"):
        tags.append("core:safe")
    else:
        tags.append("core:at_risk")

    for result in list(doctrine.get("angels_and_wards", {}).get("angels") or []) + list(
        doctrine.get("angels_and_wards", {}).get("wards") or []
    ):
        severity = str(result.get("severity") or "info").strip().lower()
        passed = bool(result.get("passed"))
        if not passed or severity in {"warning", "medium", "high", "critical"}:
            tags.append(f"{result.get('kind', 'node')}:{str(result.get('name') or '').lower()}")

    for result in doctrine.get("six_wards", {}).get("results") or []:
        severity = str(result.get("severity") or "info").strip().lower()
        passed = bool(result.get("passed"))
        if not passed or severity in {"warning", "medium", "high", "critical"}:
            tags.append(f"six_ward:{str(result.get('name') or '').lower()}")

    unique_tags: list[str] = []
    for tag in tags:
        if tag and tag not in unique_tags:
            unique_tags.append(tag)
    return unique_tags


def _build_doctrine_summary(doctrine: dict[str, Any], pipeline_mode: str) -> dict[str, Any]:
    results = list(doctrine.get("six_wards", {}).get("results") or [])
    blocked_results = [
        result
        for result in results
        if (not bool(result.get("passed"))) and str(result.get("severity") or "").lower() in {"critical", "high"}
    ]
    caution_results = [
        result
        for result in results
        if result not in blocked_results
        and (
            (not bool(result.get("passed")))
            or str(result.get("severity") or "").lower() in {"warning", "medium"}
        )
    ]

    if not doctrine.get("preserve_core") or blocked_results:
        status = "blocked"
        summary = "Doctrine found a boundary or stability risk in the current modular assembly."
    elif caution_results:
        status = "caution"
        summary = "Doctrine kept the preview inside guardrails but raised an advisory signal."
    else:
        status = "approved"
        summary = "Doctrine confirms the current modular assembly is coherent and inspectable."

    return {
        "status": status,
        "summary": summary,
        "readout_mode": "explanatory",
        "runtime_effect": "readout_only",
        "influences_runtime": False,
        "preserve_core": bool(doctrine.get("preserve_core")),
        "angels_passed": bool(doctrine.get("angels_and_wards", {}).get("angel_passed")),
        "six_wards_passed": bool(doctrine.get("six_wards", {}).get("passed")),
        "issues": [result.get("message") for result in blocked_results if result.get("message")],
        "advisories": [result.get("message") for result in caution_results if result.get("message")],
        "active_tags": _collect_doctrine_tags(doctrine, pipeline_mode),
    }


def _build_override_result(guardrail_state: dict[str, Any]) -> dict[str, Any]:
    requested_override = bool(guardrail_state.get("requested_override"))
    if not requested_override:
        return {
            "status": "none",
            "summary": "No adaptive override was requested for this preview.",
            "adaptive_zone": guardrail_state.get("adaptive_zone"),
            "requested_pipeline": [],
            "effective_pipeline": list(guardrail_state.get("effective_pipeline") or []),
        }
    if guardrail_state.get("override_blocked"):
        status = "blocked"
        summary = "Jarvis rejected the requested modular override outside approved growth zones."
    else:
        status = "approved"
        summary = "Jarvis allowed the requested modular override inside an approved adaptive zone."
    return {
        "status": status,
        "summary": summary,
        "adaptive_zone": guardrail_state.get("adaptive_zone"),
        "requested_pipeline": list(guardrail_state.get("requested_pipeline") or []),
        "effective_pipeline": list(guardrail_state.get("effective_pipeline") or []),
    }


def _build_escalation_result(
    guardrail_state: dict[str, Any],
    doctrine_summary: dict[str, Any],
) -> dict[str, Any]:
    if guardrail_state.get("status") == "blocked":
        return {
            "status": "runtime_blocked",
            "summary": "Runtime guardrails blocked the requested modular change.",
        }
    if doctrine_summary.get("status") == "blocked":
        return {
            "status": "advisory",
            "summary": "Doctrine escalated this preview for operator review, but runtime behavior remains unchanged.",
        }
    if doctrine_summary.get("status") == "caution":
        return {
            "status": "advisory",
            "summary": "Doctrine raised a caution signal for this preview without changing runtime behavior.",
        }
    return {
        "status": "none",
        "summary": "No escalation is active for this preview.",
    }


def _build_execution_outcome(
    guardrail_state: dict[str, Any],
    override_result: dict[str, Any],
) -> dict[str, Any]:
    if guardrail_state.get("status") == "blocked" or override_result.get("status") == "blocked":
        status = "blocked"
        summary = str(guardrail_state.get("summary") or override_result.get("summary") or "").strip()
    else:
        status = "approved"
        summary = "Canonical runtime evaluation approved the current modular preview."

    return {
        "status": status,
        "summary": summary,
        "runtime_status": str(guardrail_state.get("status") or "nominal"),
        "runtime_allowed": guardrail_state.get("status") != "blocked",
        "runtime_effect": "readout_only",
    }


def _build_canonical_guardrail_evaluation(
    *,
    guardrail_state: dict[str, Any],
    doctrine: dict[str, Any],
    doctrine_summary: dict[str, Any],
    ul_trace: dict[str, Any],
    pipeline_mode: str,
    metadata: dict[str, Any],
) -> dict[str, Any]:
    override_result = _build_override_result(guardrail_state)
    escalation_result = _build_escalation_result(guardrail_state, doctrine_summary)
    execution_outcome = _build_execution_outcome(
        guardrail_state,
        override_result,
    )
    doctrine_posture = dict(doctrine_summary)
    seed = {
        "guardrail_status": guardrail_state.get("status"),
        "pipeline_mode": pipeline_mode,
        "effective_pipeline": list(guardrail_state.get("effective_pipeline") or []),
        "adaptive_zone": guardrail_state.get("adaptive_zone"),
        "doctrine_status": doctrine_posture.get("status"),
        "active_tags": list(doctrine_posture.get("active_tags") or []),
        "ul_sections": list(ul_trace.get("sections") or []),
        "execution_outcome_status": execution_outcome.get("status"),
        "session_id": metadata.get("session_id"),
        "request_id": metadata.get("request_id"),
        "turn_id": metadata.get("turn_id"),
    }
    evaluation_id = "cge_" + hashlib.sha1(
        json.dumps(seed, sort_keys=True).encode("utf-8")
    ).hexdigest()[:16]
    evaluated_at = metadata.get("evaluated_at")
    if not evaluated_at:
        evaluated_at = datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")
    return {
        "id": evaluation_id,
        "evaluation_id": evaluation_id,
        "evaluated_at": evaluated_at,
        "source": "jarvis_modular_runtime",
        "evaluation_source": "jarvis_modular_runtime",
        "evaluation_version": GUARDRAIL_EVALUATION_VERSION,
        "session_id": metadata.get("session_id"),
        "request_id": metadata.get("request_id"),
        "turn_id": metadata.get("turn_id"),
        "state": execution_outcome.get("status"),
        "runtime_state": str(guardrail_state.get("status") or "nominal"),
        "pipeline_mode": pipeline_mode,
        "reason": execution_outcome.get("summary"),
        "readout_mode": "explanatory",
        "runtime_effect": "readout_only",
        "execution_outcome": execution_outcome,
        "final_judgment": execution_outcome,
        "doctrine_posture": doctrine_posture,
        "doctrine_summary": doctrine_posture,
        "active_tags": list(doctrine_posture.get("active_tags") or []),
        "override_result": override_result,
        "escalation_result": escalation_result,
        "doctrine": {
            "preserve_core": bool(doctrine.get("preserve_core")),
            "angels_passed": bool(doctrine.get("angels_and_wards", {}).get("angel_passed")),
            "six_wards_passed": bool(doctrine.get("six_wards", {}).get("passed")),
            "summary": doctrine_posture.get("summary"),
            "status": doctrine_posture.get("status"),
        },
        "ul_trace": {
            "count": int(ul_trace.get("count") or 0),
            "sections": list(ul_trace.get("sections") or []),
        },
    }


def build_context_modules(
    messages: list[dict[str, Any]] | None,
    *,
    mode: str | None = None,
    tool_result: dict[str, Any] | None = None,
    attachments: list[dict[str, Any]] | None = None,
    modules: list[BaseContextModule] | None = None,
    metadata: dict[str, Any] | None = None,
) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Derive ordered context modules from Jarvis protocol messages."""
    context = _normalize_context(
        messages,
        tool_result=tool_result,
        attachments=attachments,
        metadata=metadata,
    )
    active_modules, guardrail_state = _resolve_active_modules(mode, modules, context.metadata)
    collected: list[ContextModule] = []
    for module in sorted(active_modules, key=lambda item: getattr(item, "order", 50)):
        collected.extend(module.collect(context))
    collected.sort(key=lambda item: CHANNEL_ORDER.get(item.channel, 99))
    return [module.to_dict() for module in collected], guardrail_state


def build_provider_messages_from_protocol(
    messages: list[dict[str, Any]] | None,
    *,
    mode: str | None = None,
    tool_result: dict[str, Any] | None = None,
    attachments: list[dict[str, Any]] | None = None,
    modules: list[BaseContextModule] | None = None,
    metadata: dict[str, Any] | None = None,
) -> list[JarvisMessage]:
    """Convert protocol messages into provider-facing messages with explicit modules."""
    context = _normalize_context(
        messages,
        tool_result=tool_result,
        attachments=attachments,
        metadata=metadata,
    )
    context_dicts, _guardrail_state = build_context_modules(
        context.messages,
        mode=mode,
        tool_result=context.tool_result,
        attachments=context.attachments,
        modules=modules,
        metadata=context.metadata,
    )

    provider_messages: list[JarvisMessage] = []
    for module in context_dicts:
        provider_messages.append(
            JarvisMessage(
                role="system",
                content=_format_module_content(
                    str(module.get("label") or "Context"),
                    str(module.get("content") or ""),
                    str(module.get("channel") or "instruction"),
                ),
                channel=str(module.get("channel") or "instruction"),
                metadata=dict(module.get("metadata") or {}),
            )
        )

    for message in context.messages:
        if message.get("role") == "system":
            continue
        provider_messages.append(JarvisMessage.from_dict(message))

    return provider_messages


def build_modular_provider_preview(
    *,
    model: str,
    messages: list[dict[str, Any]] | None,
    stream: bool,
    temperature: float,
    max_tokens: int,
    mode: str | None = None,
    tool_result: dict[str, Any] | None = None,
    attachments: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
    modules: list[BaseContextModule] | None = None,
) -> dict[str, Any]:
    """Build a provider preview with explicit context modules."""
    context = _normalize_context(
        messages,
        tool_result=tool_result,
        attachments=attachments,
        metadata=metadata,
    )
    active_modules, guardrail_state = _resolve_active_modules(mode, modules, context.metadata)
    module_dicts, _guardrail_state = build_context_modules(
        context.messages,
        mode=mode,
        tool_result=context.tool_result,
        attachments=context.attachments,
        modules=active_modules,
        metadata=context.metadata,
    )
    provider_messages = build_provider_messages_from_protocol(
        context.messages,
        mode=mode,
        tool_result=context.tool_result,
        attachments=context.attachments,
        modules=active_modules,
        metadata=context.metadata,
    )
    payload = build_provider_payload(
        model=model,
        messages=[message.to_dict() for message in provider_messages],
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
        mode=mode,
        attachments=context.attachments,
        metadata=dict(context.metadata),
    )

    for module in sorted(active_modules, key=lambda item: getattr(item, "order", 50)):
        payload = module.finalize_payload(
            payload,
            context=context,
            modules=module_dicts,
            provider_messages=provider_messages,
        )

    doctrine = _build_doctrine_trace(
        mode=mode,
        metadata=context.metadata,
        guardrail_state=guardrail_state,
        modules=module_dicts,
        provider_messages=provider_messages,
        provider_payload=payload,
    )
    guardrail_state = {
        **guardrail_state,
        "preserve_core": bool(doctrine.get("preserve_core")),
        "inspectable": bool(
            doctrine.get("state", {}).get("trace_available")
            and doctrine.get("state", {}).get("provider_preview_available")
            and doctrine.get("state", {}).get("protocol_view_available")
        ),
    }
    ul_trace = build_ul_snapshot(
        modules=module_dicts,
        provider_preview=payload,
        guardrail_state=guardrail_state,
    )
    doctrine_summary = _build_doctrine_summary(doctrine, _resolve_pipeline_mode(mode))
    canonical_guardrail_evaluation = _build_canonical_guardrail_evaluation(
        guardrail_state=guardrail_state,
        doctrine=doctrine,
        doctrine_summary=doctrine_summary,
        ul_trace=ul_trace,
        pipeline_mode=_resolve_pipeline_mode(mode),
        metadata=context.metadata,
    )
    reasoning_packet = build_reasoning_packet(
        goal=context.metadata.get("current_goal") or context.metadata.get("goal"),
        mode=str(mode or "default"),
        messages=context.messages,
        model_route=context.metadata.get("model_route"),
        workspace_context=context.metadata.get("workspace_context"),
        action_lifecycle=context.metadata.get("action_lifecycle"),
        guardrail_evaluation=canonical_guardrail_evaluation,
        specialist_profile=context.metadata.get("specialist_profile"),
    )

    preview = {
        "modules": module_dicts,
        "provider_messages": [message.to_dict() for message in provider_messages],
        "provider_payload": payload,
        "context_modules": [module.name for module in active_modules],
        "guardrail_state": guardrail_state,
        "pipeline_mode": _resolve_pipeline_mode(mode),
        "ul_trace": ul_trace,
        "doctrine": doctrine,
        "guardrail_evaluation": canonical_guardrail_evaluation,
        "canonical_guardrail_evaluation": canonical_guardrail_evaluation,
        "execution_outcome": canonical_guardrail_evaluation["execution_outcome"],
        "final_judgment": canonical_guardrail_evaluation["final_judgment"],
        "doctrine_posture": canonical_guardrail_evaluation["doctrine_posture"],
        "doctrine_summary": canonical_guardrail_evaluation["doctrine_summary"],
        "active_doctrine_tags": canonical_guardrail_evaluation["active_tags"],
        "override_result": canonical_guardrail_evaluation["override_result"],
        "escalation_result": canonical_guardrail_evaluation["escalation_result"],
        "reasoning_protocol": reasoning_protocol_spec(),
        "speaking_runtime": speaking_runtime_spec(),
        "nova_cortex": nova_cortex_spec(),
        "cognitive_runtime_family": cognitive_runtime_family_spec(),
        "reasoning_packet": reasoning_packet,
        "reasoning_summary": reasoning_packet["summary"],
    }
    if context.metadata.get("cloud_forge_context"):
        from src.cloud_forge.integration import enrich_preview_with_cloud_forge

        preview = enrich_preview_with_cloud_forge(
            preview,
            dict(context.metadata.get("cloud_forge_context") or {}),
        )
    from src.aais_ul_substrate import wrap_modular_preview

    return wrap_modular_preview(preview)


def build_protocol_view(
    *,
    model: str,
    messages: list[dict[str, Any]] | None,
    stream: bool,
    temperature: float,
    max_tokens: int,
    mode: str | None = None,
    tool_result: dict[str, Any] | None = None,
    attachments: list[dict[str, Any]] | None = None,
    metadata: dict[str, Any] | None = None,
    modules: list[BaseContextModule] | None = None,
) -> dict[str, Any]:
    """Compatibility wrapper matching the richer src2 protocol-view concept."""
    return build_modular_provider_preview(
        model=model,
        messages=messages,
        stream=stream,
        temperature=temperature,
        max_tokens=max_tokens,
        mode=mode,
        tool_result=tool_result,
        attachments=attachments,
        metadata=metadata,
        modules=modules,
    )

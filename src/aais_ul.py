"""AAIS Universal Language adaptation layer.

This module turns raw modular context, provider previews, and guardrail state
into one shared UL payload shape so Jarvis can inspect what entered the system
before provider delivery.
"""

# Mythic: Aais Ul
# Engineering: AaisUlEngine
from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass, field
from typing import Any


SECTION_BY_CHANNEL = {
    "instruction": "identity",
    "runtime": "runtime_context",
    "memory": "knowledge_context",
    "workspace": "workspace_context",
    "research": "knowledge_context",
    "corrigibility": "guardrail_state",
    "browser": "protocol_trace",
    "specialist": "knowledge_context",
    "orchestration": "mission_context",
    "tool": "tool_results",
}


@dataclass(slots=True)
class ULPayload:
    source: str
    kind: str
    section: str
    data: dict[str, Any]
    metadata: dict[str, Any] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "source": self.source,
            "kind": self.kind,
            "section": self.section,
            "data": dict(self.data),
            "metadata": dict(self.metadata),
        }


class ULAdapter(ABC):
    name = "ul_adapter"

    @abstractmethod
    def supports(self, raw: Any) -> bool:
        raise NotImplementedError

    @abstractmethod
    def adapt(self, raw: Any) -> ULPayload:
        raise NotImplementedError


class ULRegistry:
    def __init__(self) -> None:
        self.adapters: list[ULAdapter] = []

    def register(self, adapter: ULAdapter) -> None:
        self.adapters.append(adapter)

    def adapt(self, raw: Any) -> ULPayload:
        for adapter in self.adapters:
            if adapter.supports(raw):
                return adapter.adapt(raw)
        raise ValueError("No UL adapter found for payload.")

    def try_adapt(self, raw: Any) -> ULPayload | None:
        for adapter in self.adapters:
            if adapter.supports(raw):
                return adapter.adapt(raw)
        return None


class RuntimeContextAdapter(ULAdapter):
    name = "runtime_context_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "runtime_context"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="context",
            section="runtime_context",
            data={
                "environment": raw.get("environment"),
                "provider": raw.get("provider"),
                "mode": raw.get("mode"),
            },
            metadata={"raw_type": raw.get("type")},
        )


class WorkspaceRunnerAdapter(ULAdapter):
    name = "workspace_runner_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "workspace_runner"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="workspace",
            section="workspace_context",
            data={
                "status": raw.get("status"),
                "active_task": raw.get("active_task"),
                "artifacts": raw.get("artifacts", []),
                "steps": raw.get("steps", []),
            },
            metadata={"raw_type": raw.get("type")},
        )


class ToolResultAdapter(ULAdapter):
    name = "tool_result_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "tool_result"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="tool_result",
            section="tool_results",
            data={
                "tool": raw.get("tool"),
                "status": raw.get("status"),
                "result": raw.get("result"),
            },
            metadata={"raw_type": raw.get("type")},
        )


class AttachmentAdapter(ULAdapter):
    name = "attachment_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "attachment"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="attachment",
            section="attachments",
            data={
                "name": raw.get("name"),
                "mime_type": raw.get("mime_type"),
                "size": raw.get("size"),
            },
            metadata={"raw_type": raw.get("type")},
        )


class ProtocolModuleAdapter(ULAdapter):
    name = "protocol_module_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and "channel" in raw and "content" in raw

    def adapt(self, raw: Any) -> ULPayload:
        channel = str(raw.get("channel") or "instruction").strip().lower()
        return ULPayload(
            source=str(raw.get("source_module") or self.name),
            kind="module",
            section=SECTION_BY_CHANNEL.get(channel, "protocol_trace"),
            data={
                "channel": channel,
                "label": raw.get("label"),
                "content": raw.get("content"),
                "role": raw.get("role"),
            },
            metadata=dict(raw.get("metadata") or {}),
        )


class ProviderPreviewAdapter(ULAdapter):
    name = "provider_preview_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and "messages" in raw and "model" in raw

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="preview",
            section="provider_payload",
            data={
                "model": raw.get("model"),
                "message_count": len(raw.get("messages") or []),
                "mode": raw.get("mode"),
                "stream": bool(raw.get("stream")),
            },
            metadata=dict(raw.get("metadata") or {}),
        )


class GuardrailStateAdapter(ULAdapter):
    name = "guardrail_state_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "status" in raw
            and "protected_zones" in raw
            and "effective_pipeline" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="guardrail",
            section="guardrail_state",
            data={
                "status": raw.get("status"),
                "summary": raw.get("summary"),
                "pipeline_mode": raw.get("pipeline_mode"),
                "effective_pipeline": list(raw.get("effective_pipeline") or []),
                "requested_pipeline": list(raw.get("requested_pipeline") or []),
                "adaptive_zone": raw.get("adaptive_zone"),
                "override_blocked": bool(raw.get("override_blocked")),
            },
            metadata={
                "protected_zones": list(raw.get("protected_zones") or []),
                "allowed_growth_zones": list(raw.get("allowed_growth_zones") or []),
            },
        )


class CognitiveBridgeAdapter(ULAdapter):
    name = "cognitive_bridge_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("bridge_id") == "aais.cognitive_bridge"
            and "decision" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="bridge",
            section="protocol_trace",
            data={
                "decision": raw.get("decision"),
                "status": raw.get("status"),
                "execution_allowed": bool(raw.get("execution_allowed")),
                "risk": raw.get("risk"),
                "summary": raw.get("summary"),
            },
            metadata={
                "bridge_version": raw.get("version"),
                "reason_codes": list(raw.get("reason_codes") or []),
            },
        )


class GovernedPipelineAdapter(ULAdapter):
    name = "governed_pipeline_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("protocol_id") == "aais.governed_direct_pipeline"
            and "pipeline_id" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="pipeline",
            section="mission_context",
            data={
                "pipeline_id": raw.get("pipeline_id"),
                "active_lane": raw.get("active_lane"),
                "traffic_class": raw.get("traffic_class"),
                "response_mode": raw.get("response_mode"),
                "summary": raw.get("summary"),
            },
            metadata={
                "contract": raw.get("contract"),
                "surface_node": raw.get("surface_node"),
                "runtime_context": raw.get("runtime_context"),
            },
        )


class CapabilityResultAdapter(ULAdapter):
    name = "capability_result_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "module" in raw
            and "action" in raw
            and ("ok" in raw or "error_type" in raw)
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=str(raw.get("module") or self.name),
            kind="capability",
            section="tool_results",
            data={
                "module": raw.get("module"),
                "action": raw.get("action"),
                "ok": bool(raw.get("ok")),
                "error_type": raw.get("error_type"),
                "message": raw.get("message"),
            },
            metadata={
                "trace_id": raw.get("trace_id"),
                "provider": raw.get("provider"),
            },
        )


class ProposalStateAdapter(ULAdapter):
    name = "proposal_state_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("proposal_only") is True
            and "status" in raw
            and "module_id" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=str(raw.get("module_id") or self.name),
            kind="proposal",
            section="proposal_state",
            data={
                "status": raw.get("status"),
                "reason": raw.get("reason"),
                "packet_type": raw.get("packet_type"),
                "execution_authority": raw.get("execution_authority"),
            },
            metadata={
                "bridge_decision": raw.get("bridge_decision"),
                "runtime_context": raw.get("runtime_context"),
            },
        )


class PipelinePacketAdapter(ULAdapter):
    name = "pipeline_packet_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "packet_id" in raw
            and "source" in raw
            and "target" in raw
            and "lane" in raw
            and "intent" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=str(raw.get("source") or self.name),
            kind="pipeline_packet",
            section="protocol_trace",
            data={
                "packet_id": raw.get("packet_id"),
                "source": raw.get("source"),
                "target": raw.get("target"),
                "lane": raw.get("lane"),
                "intent": raw.get("intent"),
                "priority": raw.get("priority"),
            },
            metadata={
                "route": list((raw.get("trace") or {}).get("route") or []),
            },
        )


class ImmuneSnapshotAdapter(ULAdapter):
    name = "immune_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "system_mode" in raw
            and "event_count" in raw
            and "incident_count" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="immune_snapshot",
            section="guardrail_state",
            data={
                "system_mode": raw.get("system_mode"),
                "event_count": raw.get("event_count"),
                "incident_count": raw.get("incident_count"),
                "active_incident_id": raw.get("active_incident_id"),
            },
            metadata={"reason": raw.get("reason")},
        )


class GovernanceSnapshotAdapter(ULAdapter):
    name = "governance_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "roles" in raw
            and "active_break_glass" in raw
            and "request_count" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        break_glass = dict(raw.get("active_break_glass") or {})
        return ULPayload(
            source=self.name,
            kind="governance_snapshot",
            section="guardrail_state",
            data={
                "request_count": raw.get("request_count"),
                "event_count": raw.get("event_count"),
                "break_glass_status": break_glass.get("status"),
                "truth_scope": raw.get("truth_scope"),
            },
            metadata={"role_count": len(list(raw.get("roles") or []))},
        )


class MissionBoardSnapshotAdapter(ULAdapter):
    name = "mission_board_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "mission_count" in raw
            and "cisiv_stage_sequence" in raw
            and "counts" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="mission_board",
            section="mission_context",
            data={
                "mission_count": raw.get("mission_count"),
                "active_mission_id": raw.get("active_mission_id"),
                "summary": raw.get("summary"),
                "counts": dict(raw.get("counts") or {}),
            },
            metadata={"updated_at": raw.get("updated_at")},
        )


class ModuleGovernanceSnapshotAdapter(ULAdapter):
    name = "module_governance_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("id") == "aais.module_governance"

    def adapt(self, raw: Any) -> ULPayload:
        counts = dict(raw.get("module_counts") or {})
        return ULPayload(
            source=self.name,
            kind="module_governance",
            section="guardrail_state",
            data={
                "version": raw.get("version"),
                "module_counts": counts,
                "admitted": counts.get("admitted"),
                "quarantined": counts.get("quarantined"),
            },
            metadata={"cisiv_stage_sequence": list(raw.get("cisiv_stage_sequence") or [])},
        )


class MemoryBoardSnapshotAdapter(ULAdapter):
    name = "memory_board_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        board = raw.get("board") if isinstance(raw, dict) else None
        return (
            isinstance(raw, dict)
            and isinstance(board, dict)
            and board.get("board_id")
            and isinstance(raw.get("slots"), list)
        )

    def adapt(self, raw: Any) -> ULPayload:
        board = dict(raw.get("board") or {})
        return ULPayload(
            source=str(board.get("board_id") or self.name),
            kind="memory_board",
            section="knowledge_context",
            data={
                "board_label": board.get("board_label"),
                "active_slots": raw.get("active_slots"),
                "installed_slots": raw.get("installed_slots"),
                "slot_count": len(list(raw.get("slots") or [])),
            },
            metadata={"board_version": board.get("board_version")},
        )


class OperatorActionResultAdapter(ULAdapter):
    name = "operator_action_result_adapter"

    def supports(self, raw: Any) -> bool:
        action = raw.get("action") if isinstance(raw, dict) else None
        return (
            isinstance(raw, dict)
            and isinstance(action, dict)
            and "status" in raw
            and ("exit_code" in raw or "patch_apply" in raw or "ran_at" in raw)
        )

    def adapt(self, raw: Any) -> ULPayload:
        action = dict(raw.get("action") or {})
        return ULPayload(
            source="jarvis_operator",
            kind="operator_action",
            section="tool_results",
            data={
                "action_id": action.get("id"),
                "label": action.get("label"),
                "status": raw.get("status"),
                "exit_code": raw.get("exit_code"),
            },
            metadata={"summary": raw.get("summary")},
        )


class UGRRuntimeResponseAdapter(ULAdapter):
    name = "ugr_runtime_response_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("runtime_id") == "aais.ugr.unified_runtime"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="ugr_runtime",
            section="runtime_context",
            data={
                "trace_id": raw.get("trace_id"),
                "status": raw.get("status"),
                "summary": raw.get("summary"),
                "lane_count": len(list(raw.get("lane_results") or [])),
            },
            metadata={
                "runtime_version": raw.get("runtime_version"),
            },
        )


class CapabilityBridgeSnapshotAdapter(ULAdapter):
    name = "capability_bridge_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("bridge_id") == "aais.capability_service_bridge"
            and "service_lane" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="capability_bridge",
            section="protocol_trace",
            data={
                "version": raw.get("version"),
                "event_count": raw.get("event_count"),
                "tool_count": len(list(raw.get("registered_tools") or [])),
            },
            metadata={"path": raw.get("path")},
        )


class OperatorConsoleSnapshotAdapter(ULAdapter):
    name = "operator_console_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("console_id") == "aais.operator.ugr_cloud_console"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="operator_console",
            section="runtime_context",
            data={
                "console_version": raw.get("console_version"),
                "status": raw.get("status"),
                "claim_status": raw.get("claim_status"),
                "runtime_effect": raw.get("runtime_effect"),
            },
            metadata={"gate_count": len(list(raw.get("gates") or []))},
        )


class SystemGuardSnapshotAdapter(ULAdapter):
    name = "system_guard_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "accepting_turns" in raw
            and "accepting_actions" in raw
            and "accepting_memory_writes" in raw
            and "status" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="system_guard",
            section="guardrail_state",
            data={
                "status": raw.get("status"),
                "accepting_turns": bool(raw.get("accepting_turns")),
                "accepting_actions": bool(raw.get("accepting_actions")),
                "summary": raw.get("summary"),
            },
            metadata={"last_action": raw.get("last_action")},
        )


class CreativeRuntimeSnapshotAdapter(ULAdapter):
    name = "creative_runtime_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "core" in raw
            and "runtime_version" in raw
            and "mode" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=str(raw.get("core") or self.name),
            kind="creative_runtime",
            section="runtime_context",
            data={
                "core": raw.get("core"),
                "mode": raw.get("mode"),
                "event_count": raw.get("event_count"),
            },
            metadata={"runtime_version": raw.get("runtime_version")},
        )


class WorkspaceContextAdapter(ULAdapter):
    name = "workspace_context_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "query" in raw
            and "prompt_block" in raw
            and isinstance(raw.get("results"), list)
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="workspace_context",
            section="workspace_context",
            data={
                "query": raw.get("query"),
                "summary": raw.get("summary"),
                "project_scope": raw.get("project_scope"),
                "result_count": len(list(raw.get("results") or [])),
                "file_count": len(list(raw.get("files") or [])),
            },
            metadata={"reason": raw.get("reason"), "auto_attached": raw.get("auto_attached")},
        )


class ForgeContextAdapter(ULAdapter):
    name = "forge_context_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "goal" in raw
            and isinstance(raw.get("files"), list)
            and "constraints" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="forge_context",
            section="workspace_context",
            data={
                "goal": raw.get("goal"),
                "file_count": len(list(raw.get("files") or [])),
                "target_scope": raw.get("target_scope"),
                "operation_mode": raw.get("operation_mode"),
            },
            metadata={"change_intent": raw.get("change_intent")},
        )


class StoryForgeCapabilityAdapter(ULAdapter):
    name = "story_forge_capability_adapter"

    def supports(self, raw: Any) -> bool:
        capability = raw.get("capability") if isinstance(raw, dict) else None
        return (
            isinstance(raw, dict)
            and raw.get("artifact_type") == "FinalMovieArtifact"
            and isinstance(capability, dict)
            and capability.get("name") == "story_forge_audio"
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="story_forge_capability",
            section="tool_results",
            data={
                "status": raw.get("status"),
                "movie_path": raw.get("movie_path"),
                "continuity_passed": bool(raw.get("continuity_passed")),
                "issue_count": raw.get("issue_count"),
            },
            metadata={
                "session_id": raw.get("session_id"),
                "story_id": raw.get("story_id"),
            },
        )


class ContinuityWitnessSnapshotAdapter(ULAdapter):
    name = "continuity_witness_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("module_id") == "AAIS-CW-01" and "subsystems" in raw

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="continuity_witness",
            section="protocol_trace",
            data={
                "version": raw.get("version"),
                "subsystem_count": len(dict(raw.get("subsystems") or {})),
            },
            metadata={"updated_at": raw.get("updated_at")},
        )


class ContinuityWitnessObservationAdapter(ULAdapter):
    name = "continuity_witness_observation_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("module_id") == "AAIS-CW-01"
            and "trajectory_status" in raw
            and bool(raw.get("observation_only"))
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="continuity_observation",
            section="protocol_trace",
            data={
                "trajectory_status": raw.get("trajectory_status"),
                "risk_level": raw.get("risk_level"),
                "confidence": raw.get("confidence"),
            },
            metadata={"direction": raw.get("direction")},
        )


class SecurityProtocolSnapshotAdapter(ULAdapter):
    name = "security_protocol_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "decision_counts" in raw
            and isinstance(raw.get("summary"), str)
            and "policy brain" in str(raw.get("summary")).lower()
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="security_protocol",
            section="guardrail_state",
            data={
                "event_count": raw.get("event_count"),
                "decision_counts": dict(raw.get("decision_counts") or {}),
            },
            metadata={"last_event_at": raw.get("last_event_at")},
        )


class DreamspaceSnapshotAdapter(ULAdapter):
    name = "dreamspace_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "auto_enabled" in raw
            and "dream_interval_seconds" in raw
            and "status" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="dreamspace",
            section="runtime_context",
            data={
                "status": raw.get("status"),
                "auto_enabled": bool(raw.get("auto_enabled")),
                "total_dreams": raw.get("total_dreams"),
                "running": raw.get("running"),
            },
            metadata={"last_action": raw.get("last_action")},
        )


class CapabilityExecutionPreviewAdapter(ULAdapter):
    name = "capability_execution_preview_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("path") == "capability_service_bridge"
            and "capability" in raw
            and "action" in raw
            and "flow" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="capability_preview",
            section="proposal_state",
            data={
                "capability": raw.get("capability"),
                "action": raw.get("action"),
                "tool": raw.get("tool"),
                "runtime_context": raw.get("runtime_context"),
            },
            metadata={"endpoint": raw.get("endpoint")},
        )


class PatchPlanAdapter(ULAdapter):
    name = "patch_plan_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("plan_id")
            and raw.get("status") == "proposal_only"
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="patch_plan",
            section="proposal_state",
            data={
                "plan_id": raw.get("plan_id"),
                "status": raw.get("status"),
                "goal": raw.get("goal"),
                "target_count": len(list(raw.get("target_files") or [])),
                "hunk_count": raw.get("hunk_count"),
                "preview_only": bool(raw.get("preview_only")),
            },
            metadata={"review_complete": bool(raw.get("review_complete"))},
        )


class ForgeUlSnapshotAdapter(ULAdapter):
    name = "forge_ul_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        if not isinstance(raw, dict):
            return False
        payloads = raw.get("payloads")
        sections = raw.get("sections")
        count = raw.get("count")
        return (
            isinstance(payloads, list)
            and isinstance(sections, list)
            and isinstance(count, int)
            and count == len(payloads)
            and payloads
            and payloads[0].get("source") == "forge_runtime"
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="forge_ul_snapshot",
            section="protocol_trace",
            data={
                "count": raw.get("count"),
                "sections": list(raw.get("sections") or []),
            },
            metadata={"forge_runtime_payloads": len(list(raw.get("payloads") or []))},
        )


class CloudForgeBundleAdapter(ULAdapter):
    name = "cloud_forge_bundle_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and isinstance(raw.get("rail_decision"), dict)
            and isinstance(raw.get("cognition_plan"), dict)
        )

    def adapt(self, raw: Any) -> ULPayload:
        decision = dict(raw.get("rail_decision") or {})
        plan = dict(raw.get("cognition_plan") or {})
        return ULPayload(
            source=self.name,
            kind="cloud_forge_bundle",
            section="mission_context",
            data={
                "rail": decision.get("rail"),
                "risk": decision.get("risk"),
                "domain_template": plan.get("domain_template"),
                "model_tier": plan.get("model_tier"),
                "step_count": len(list(plan.get("steps") or [])),
            },
            metadata={"contract_version": raw.get("contract_version")},
        )


class CloudForgeReadoutAdapter(ULAdapter):
    name = "cloud_forge_readout_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("runtime_effect") == "readout_only"
            and "rail" in raw
            and "risk" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="cloud_forge_readout",
            section="protocol_trace",
            data={
                "rail": raw.get("rail"),
                "risk": raw.get("risk"),
                "summary": raw.get("summary"),
                "claim_status": raw.get("claim_status"),
                "runtime_effect": raw.get("runtime_effect"),
            },
            metadata={"ledger_record_id": raw.get("ledger_record_id")},
        )


class ContractorResponseAdapter(ULAdapter):
    name = "contractor_response_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("task_id")
            and (raw.get("kind") or raw.get("mode"))
            and ("result" in raw or "error" in raw or "ok" in raw)
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="contractor_response",
            section="tool_results",
            data={
                "task_id": raw.get("task_id"),
                "kind": raw.get("kind") or raw.get("mode"),
                "ok": raw.get("ok"),
                "status": (raw.get("result") or {}).get("status") if isinstance(raw.get("result"), dict) else None,
            },
            metadata={"law_enforcement": bool(raw.get("law_enforcement"))},
        )


class EvolveResponseAdapter(ULAdapter):
    name = "evolve_response_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("job_id")
            and "task" in raw
            and ("result" in raw or "error" in raw or "ok" in raw)
        )

    def adapt(self, raw: Any) -> ULPayload:
        result = raw.get("result") if isinstance(raw.get("result"), dict) else {}
        return ULPayload(
            source=self.name,
            kind="evolve_response",
            section="tool_results",
            data={
                "job_id": raw.get("job_id"),
                "task": raw.get("task"),
                "ok": raw.get("ok"),
                "status": result.get("status"),
                "preset": raw.get("preset"),
            },
            metadata={"law_enforcement": bool(raw.get("law_enforcement"))},
        )


class V10CoreResultAdapter(ULAdapter):
    name = "v10_core_result_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and str(raw.get("version") or "").strip().lower() == "v10"
            and raw.get("status")
            and isinstance(raw.get("quality_report"), dict)
        )

    def adapt(self, raw: Any) -> ULPayload:
        quality = dict(raw.get("quality_report") or {})
        return ULPayload(
            source=self.name,
            kind="v10_core_result",
            section="tool_results",
            data={
                "status": raw.get("status"),
                "location": raw.get("location"),
                "provider": raw.get("provider"),
                "pipeline_count": len(list(raw.get("pipeline") or [])),
                "quality_score": quality.get("quality_score"),
                "readiness": quality.get("readiness"),
            },
            metadata={"model": raw.get("model")},
        )


class V9CoreResultAdapter(ULAdapter):
    name = "v9_core_result_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("status")
            and raw.get("pipeline")
            and raw.get("provider")
            and "output" in raw
            and str(raw.get("version") or "").strip().lower() != "v10"
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="v9_core_result",
            section="tool_results",
            data={
                "status": raw.get("status"),
                "location": raw.get("location"),
                "provider": raw.get("provider"),
                "pipeline_count": len(list(raw.get("pipeline") or [])),
                "character_count": len(list(raw.get("characters") or [])),
            },
            metadata={"model": raw.get("model")},
        )


class MysticReadingAdapter(ULAdapter):
    name = "mystic_reading_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("state")
            and raw.get("dominant_archetype")
            and raw.get("trial")
            and raw.get("next_action")
            and "input_text" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="mystic_reading",
            section="knowledge_context",
            data={
                "state": raw.get("state"),
                "state_label": raw.get("state_label"),
                "dominant_archetype": raw.get("dominant_archetype"),
                "trial": raw.get("trial"),
                "next_action": raw.get("next_action"),
                "signal_count": len(list(raw.get("detected_signals") or [])),
            },
            metadata={"opposing_archetype": raw.get("opposing_archetype")},
        )


class PatchReviewAdapter(ULAdapter):
    name = "patch_review_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("id")
            and isinstance(raw.get("patch_plan"), dict)
            and isinstance(raw.get("current_decision"), dict)
        )

    def adapt(self, raw: Any) -> ULPayload:
        patch_plan = dict(raw.get("patch_plan") or {})
        decision = dict(raw.get("current_decision") or {})
        return ULPayload(
            source=self.name,
            kind="patch_review",
            section="proposal_state",
            data={
                "review_id": raw.get("id"),
                "status": raw.get("status"),
                "goal": raw.get("goal"),
                "decision_state": decision.get("state"),
                "target_count": len(list(patch_plan.get("target_files") or [])),
                "hunk_count": patch_plan.get("hunk_count"),
            },
            metadata={"apply_ready": bool((raw.get("apply_gate") or {}).get("ready"))},
        )


class CreativeCoreRuntimeSnapshotAdapter(ULAdapter):
    name = "creative_core_runtime_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        core = str(raw.get("core") or "").strip().lower()
        return (
            isinstance(raw, dict)
            and core in {"v9", "v10"}
            and "runtime_version" in raw
            and "run_count" in raw
            and "status" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="creative_runtime_snapshot",
            section="runtime_context",
            data={
                "core": raw.get("core"),
                "runtime_version": raw.get("runtime_version"),
                "status": raw.get("status"),
                "run_count": raw.get("run_count"),
                "failure_count": raw.get("failure_count"),
                "event_count": raw.get("event_count"),
            },
            metadata={"mode": raw.get("mode")},
        )


class SpatialReasonResultAdapter(ULAdapter):
    name = "spatial_reason_result_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "from" in raw
            and "to" in raw
            and any(key in raw for key in ("path", "distance", "visibility", "visible", "error"))
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="spatial_reason_result",
            section="tool_results",
            data={
                "from": raw.get("from"),
                "to": raw.get("to"),
                "path_count": len(list(raw.get("path") or [])),
                "distance": raw.get("distance"),
                "visible": raw.get("visible"),
                "error": raw.get("error"),
            },
            metadata={"reason": raw.get("reason")},
        )


class CorrigibilityStateAdapter(ULAdapter):
    name = "corrigibility_state_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "status" in raw
            and "total_corrections" in raw
            and isinstance(raw.get("recent"), list)
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="corrigibility_state",
            section="guardrail_state",
            data={
                "status": raw.get("status"),
                "total_corrections": raw.get("total_corrections"),
                "last_action": raw.get("last_action"),
                "last_severity": raw.get("last_severity"),
                "pending": bool(raw.get("pending")),
            },
            metadata={"last_command": raw.get("last_command")},
        )


class CorrigibilityToolResultAdapter(ULAdapter):
    name = "corrigibility_tool_result_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and raw.get("type") == "corrigibility"

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="corrigibility_tool_result",
            section="guardrail_state",
            data={
                "status": raw.get("status"),
                "direction": raw.get("direction"),
                "severity": raw.get("severity"),
                "rating": raw.get("rating"),
            },
            metadata={"action_id": (raw.get("action") or {}).get("id")},
        )


class OperatorHealthSnapshotAdapter(ULAdapter):
    name = "operator_health_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("module_id") == "AAIS-OHS-01"
            and raw.get("operator_state")
            and raw.get("advisory_only") is True
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="operator_health_snapshot",
            section="guardrail_state",
            data={
                "operator_state": raw.get("operator_state"),
                "recommended_mode": raw.get("recommended_mode"),
                "cognitive_load_score": raw.get("cognitive_load_score"),
                "confidence": raw.get("confidence"),
                "recommended_action_count": len(list(raw.get("recommended_actions") or [])),
            },
            metadata={"status": raw.get("status")},
        )


class V8PolicyStatusAdapter(ULAdapter):
    name = "v8_policy_status_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "posture" in raw
            and "allowed" in raw
            and raw.get("target") == "session"
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="v8_policy_status",
            section="guardrail_state",
            data={
                "status": raw.get("status"),
                "posture": raw.get("posture"),
                "allowed": raw.get("allowed"),
                "violation_count": len(list(raw.get("violations") or [])),
                "guidance_count": len(list(raw.get("guidance") or [])),
            },
            metadata={"summary": raw.get("summary")},
        )


class RunLedgerRecordAdapter(ULAdapter):
    name = "run_ledger_record_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("id")
            and raw.get("session_id")
            and raw.get("status")
            and raw.get("kind")
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="run_ledger_record",
            section="protocol_trace",
            data={
                "run_id": raw.get("id"),
                "session_id": raw.get("session_id"),
                "status": raw.get("status"),
                "kind": raw.get("kind"),
                "cisiv_stage": raw.get("cisiv_stage"),
                "step_count": len(list(raw.get("steps") or [])),
            },
            metadata={"title": raw.get("title")},
        )


class OperatorReadoutAdapter(ULAdapter):
    name = "operator_readout_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("runtime_effect") == "readout_only"
            and "status" in raw
            and (
                "traces_path" in raw
                or "dashboard" in raw
                or "trace_count" in raw
            )
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="operator_readout",
            section="protocol_trace",
            data={
                "status": raw.get("status"),
                "summary": raw.get("summary"),
                "trace_count": raw.get("trace_count"),
                "returned": raw.get("returned"),
                "live_checks": raw.get("live_checks"),
            },
            metadata={"runtime_effect": raw.get("runtime_effect")},
        )


class MemorySmithSnapshotAdapter(ULAdapter):
    name = "memory_smith_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and "review_count" in raw
            and "durable_count" in raw
            and "project_summary" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="memory_smith_snapshot",
            section="knowledge_context",
            data={
                "review_count": raw.get("review_count"),
                "durable_count": raw.get("durable_count"),
                "expired_count": raw.get("expired_count"),
            },
            metadata={"summary": (raw.get("project_summary") or {}).get("summary")},
        )


class KnowledgeAuthoritySnapshotAdapter(ULAdapter):
    name = "knowledge_authority_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and isinstance(raw.get("authority_order"), list)
            and isinstance(raw.get("preferences"), dict)
            and "current_contract" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="knowledge_authority_snapshot",
            section="knowledge_context",
            data={
                "mode": (raw.get("summary") or {}).get("mode"),
                "active_conflict_count": (raw.get("summary") or {}).get("active_conflict_count"),
                "memory_count": len(list(raw.get("memory") or [])),
                "document_count": len(list(raw.get("documents") or [])),
            },
            metadata={"preset": (raw.get("preferences") or {}).get("preset")},
        )


class RealtimePredictorSnapshotAdapter(ULAdapter):
    name = "realtime_predictor_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("module_id") == "aais.realtime_event_cause_predictor"
            and raw.get("cause_class")
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="realtime_predictor_snapshot",
            section="protocol_trace",
            data={
                "cause_class": raw.get("cause_class"),
                "recommended_state": raw.get("recommended_state"),
                "data_sufficiency": raw.get("data_sufficiency"),
                "confidence": raw.get("confidence"),
            },
            metadata={"status": raw.get("status")},
        )


class InvariantValidationAdapter(ULAdapter):
    name = "invariant_validation_adapter"

    def supports(self, raw: Any) -> bool:
        module_id = str(raw.get("module_id") or "")
        return isinstance(raw, dict) and module_id.startswith("aais.invariant_engine") and "allows" in raw

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="invariant_validation",
            section="guardrail_state",
            data={
                "status": raw.get("status"),
                "allows": raw.get("allows"),
                "failed_invariant_count": len(list(raw.get("failed_invariants") or [])),
            },
            metadata={"module_id": raw.get("module_id")},
        )


class ReasoningExchangeResultAdapter(ULAdapter):
    name = "reasoning_exchange_result_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("protocol_id") == "aais.reasoning_exchange"
            and raw.get("status")
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="reasoning_exchange_result",
            section="protocol_trace",
            data={
                "status": raw.get("status"),
                "reason": raw.get("reason"),
                "confidence_adjustment": raw.get("confidence_adjustment"),
            },
            metadata={"protocol_version": raw.get("protocol_version")},
        )


class GovernedEventChainAdapter(ULAdapter):
    name = "governed_event_chain_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("module_id") == "aais.governed_event_chain"
            and raw.get("decision")
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="governed_event_chain",
            section="guardrail_state",
            data={
                "status": raw.get("status"),
                "decision": raw.get("decision"),
                "runtime_context": raw.get("runtime_context"),
            },
            metadata={"advisory_only": raw.get("advisory_only")},
        )


class DetachmentGuardSnapshotAdapter(ULAdapter):
    name = "detachment_guard_snapshot_adapter"

    def supports(self, raw: Any) -> bool:
        return (
            isinstance(raw, dict)
            and raw.get("component_id") == "jarvis.detachment_guard"
            and "temporary_deny_count" in raw
        )

    def adapt(self, raw: Any) -> ULPayload:
        return ULPayload(
            source=self.name,
            kind="detachment_guard_snapshot",
            section="guardrail_state",
            data={
                "temporary_deny_count": raw.get("temporary_deny_count"),
                "attempt_history_sources": raw.get("attempt_history_sources"),
            },
            metadata={"version": raw.get("version")},
        )


class GenericIngressAdapter(ULAdapter):
    """Fallback adapter — wraps any dict that no other adapter claimed."""

    name = "generic_ingress_adapter"

    def supports(self, raw: Any) -> bool:
        return isinstance(raw, dict) and bool(raw)

    def adapt(self, raw: Any) -> ULPayload:
        keys = sorted(str(key) for key in raw.keys())
        return ULPayload(
            source=self.name,
            kind="ingress",
            section="protocol_trace",
            data={"keys": keys[:24], "size": len(raw)},
            metadata={"adapted_as": "generic_ingress"},
        )


def build_default_registry() -> ULRegistry:
    registry = ULRegistry()
    registry.register(RuntimeContextAdapter())
    registry.register(WorkspaceRunnerAdapter())
    registry.register(ToolResultAdapter())
    registry.register(AttachmentAdapter())
    registry.register(ProtocolModuleAdapter())
    registry.register(ProviderPreviewAdapter())
    registry.register(GuardrailStateAdapter())
    registry.register(CognitiveBridgeAdapter())
    registry.register(GovernedPipelineAdapter())
    registry.register(CapabilityResultAdapter())
    registry.register(ProposalStateAdapter())
    registry.register(PipelinePacketAdapter())
    registry.register(ImmuneSnapshotAdapter())
    registry.register(GovernanceSnapshotAdapter())
    registry.register(MissionBoardSnapshotAdapter())
    registry.register(ModuleGovernanceSnapshotAdapter())
    registry.register(MemoryBoardSnapshotAdapter())
    registry.register(OperatorActionResultAdapter())
    registry.register(UGRRuntimeResponseAdapter())
    registry.register(CapabilityBridgeSnapshotAdapter())
    registry.register(OperatorConsoleSnapshotAdapter())
    registry.register(SystemGuardSnapshotAdapter())
    registry.register(CreativeRuntimeSnapshotAdapter())
    registry.register(WorkspaceContextAdapter())
    registry.register(ForgeContextAdapter())
    registry.register(StoryForgeCapabilityAdapter())
    registry.register(ContinuityWitnessSnapshotAdapter())
    registry.register(ContinuityWitnessObservationAdapter())
    registry.register(SecurityProtocolSnapshotAdapter())
    registry.register(DreamspaceSnapshotAdapter())
    registry.register(CapabilityExecutionPreviewAdapter())
    registry.register(PatchPlanAdapter())
    registry.register(ForgeUlSnapshotAdapter())
    registry.register(CloudForgeBundleAdapter())
    registry.register(CloudForgeReadoutAdapter())
    registry.register(ContractorResponseAdapter())
    registry.register(EvolveResponseAdapter())
    registry.register(V10CoreResultAdapter())
    registry.register(V9CoreResultAdapter())
    registry.register(MysticReadingAdapter())
    registry.register(PatchReviewAdapter())
    registry.register(CreativeCoreRuntimeSnapshotAdapter())
    registry.register(SpatialReasonResultAdapter())
    registry.register(CorrigibilityStateAdapter())
    registry.register(CorrigibilityToolResultAdapter())
    registry.register(OperatorHealthSnapshotAdapter())
    registry.register(V8PolicyStatusAdapter())
    registry.register(RunLedgerRecordAdapter())
    registry.register(OperatorReadoutAdapter())
    registry.register(MemorySmithSnapshotAdapter())
    registry.register(KnowledgeAuthoritySnapshotAdapter())
    registry.register(RealtimePredictorSnapshotAdapter())
    registry.register(InvariantValidationAdapter())
    registry.register(ReasoningExchangeResultAdapter())
    registry.register(GovernedEventChainAdapter())
    registry.register(DetachmentGuardSnapshotAdapter())
    registry.register(GenericIngressAdapter())
    return registry


DEFAULT_REGISTRY = build_default_registry()


def _collect_adapted_payloads(
    raw_items: list[Any],
    *,
    registry: ULRegistry,
) -> list[dict[str, Any]]:
    payloads: list[dict[str, Any]] = []
    for raw in raw_items:
        if raw is None:
            continue
        payload = registry.try_adapt(raw)
        if payload:
            payloads.append(payload.to_dict())
    return payloads


def build_ul_snapshot(
    *,
    modules: list[dict[str, Any]] | None = None,
    provider_preview: dict[str, Any] | None = None,
    guardrail_state: dict[str, Any] | None = None,
    bridge_results: list[dict[str, Any]] | None = None,
    pipeline: dict[str, Any] | None = None,
    pipeline_packets: list[dict[str, Any]] | None = None,
    capability_results: list[dict[str, Any]] | None = None,
    proposals: list[dict[str, Any]] | None = None,
    ingress: list[dict[str, Any]] | None = None,
    registry: ULRegistry | None = None,
) -> dict[str, Any]:
    """Adapt runtime context into inspectable UL payloads."""
    active_registry = registry or DEFAULT_REGISTRY
    payloads: list[dict[str, Any]] = []

    payloads.extend(_collect_adapted_payloads(list(modules or []), registry=active_registry))

    for optional in (provider_preview, guardrail_state, pipeline):
        if optional:
            payload = active_registry.try_adapt(optional)
            if payload:
                payloads.append(payload.to_dict())

    payloads.extend(_collect_adapted_payloads(list(bridge_results or []), registry=active_registry))
    payloads.extend(_collect_adapted_payloads(list(pipeline_packets or []), registry=active_registry))
    payloads.extend(_collect_adapted_payloads(list(capability_results or []), registry=active_registry))
    payloads.extend(_collect_adapted_payloads(list(proposals or []), registry=active_registry))
    payloads.extend(_collect_adapted_payloads(list(ingress or []), registry=active_registry))

    sections: list[str] = []
    for payload in payloads:
        section = payload.get("section")
        if section and section not in sections:
            sections.append(section)

    return {
        "count": len(payloads),
        "sections": sections,
        "payloads": payloads,
    }


def adapt_ingress(raw: Any, *, registry: ULRegistry | None = None, required: bool = True) -> dict[str, Any]:
    """Adapt one raw ingress value into a UL payload dict."""
    active_registry = registry or DEFAULT_REGISTRY
    payload = active_registry.try_adapt(raw)
    if payload is None:
        if required:
            raise ValueError("No UL adapter found for ingress payload.")
        return {}
    return payload.to_dict()

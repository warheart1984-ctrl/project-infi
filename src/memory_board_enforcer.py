"""Strict gateway for live Jarvis memory operations.

This module does not implement memory doctrine. It exists to ensure that live
runtime operations route through the governed memory board, respect phase and
module admission checks, and emit bounded audit metadata.
"""

from __future__ import annotations

def _wrap_ul_payload(payload: dict) -> dict:
    from src.aais_ul_substrate import attach_ul_substrate

    return attach_ul_substrate(dict(payload))
from typing import Any
import uuid

from src.immune_system import ImmuneSystemController, immune_system
from src.module_governance import ModuleGovernanceController, module_governance
from src.phase_gate import (
    ComponentNotRegisteredError,
    GovernedComponent,
    Phase,
    PhaseGateError,
    assert_executable,
    get_component,
    register_component,
)
from src.seam_log import record_seam_event


MEMORY_BOARD_ENFORCER_COMPONENT_ID = "jarvis.memory_board_enforcer"
MEMORY_BOARD_ENFORCER_ALLOWED_CONTEXTS = [
    "live_runtime",
    "operator_runtime",
    "dreamspace_runtime",
    "test_harness",
]
READ_ONLY_ACTIONS = {
    "get_memory",
    "get_memory_board_snapshot",
    "list_memories",
}
MUTATING_ACTIONS = {
    "add_memory",
    "add_override",
    "archive_memory",
    "compact_state",
    "delete_memory",
    "install_memory_module",
    "merge_memories",
    "record_board_event",
    "swap_memory_module",
    "update_memory",
}


class MemoryBoardEnforcerError(PermissionError):
    """Raised when the gateway blocks a memory operation."""


class MemoryBoardBypassError(MemoryBoardEnforcerError):
    """Raised when code attempts to mutate live memory outside the gateway."""


def _clean_text(value: Any, *, limit: int = 280) -> str:
    normalized = " ".join(str(value or "").split()).strip()
    if len(normalized) <= limit:
        return normalized
    return normalized[: limit - 3].rstrip() + "..."


def _normalize_runtime_context(value: Any) -> str:
    cleaned = _clean_text(value, limit=80).lower().replace("-", "_").replace(" ", "_")
    return cleaned or "operator_runtime"


def build_memory_board_enforcer_module_spec(
    module_id: str = MEMORY_BOARD_ENFORCER_COMPONENT_ID,
) -> dict[str, Any]:
    """Return a compliant module-governance spec for the gateway itself."""
    return _wrap_ul_payload({
        "module_id": module_id,
        "label": "Memory Board Enforcer",
        "lane": "memory_governance",
        "declared_scope": [
            "memory_bank",
            "memory_board",
            "conversation_memory",
            "prompt_assembly",
            "knowledge_authority",
            "memory_smith",
            "api",
            "jarvis_operator",
        ],
        "declared_surfaces": [
            "memory_bank",
            "memory_board",
            "operator_runtime",
            "live_runtime",
        ],
        "capabilities": [
            "governed_memory_gateway",
            "phase_gate_enforcement",
            "module_governance_enforcement",
            "bypass_detection",
            "audit_trace",
        ],
        "cisiv": {
            "concept": {
                "status": "passed",
                "summary": "Act as the single live gateway for memory operations without duplicating doctrine logic.",
            },
            "identity": {
                "status": "passed",
                "summary": "Enforce memory boundaries while leaving decision law inside jarvis_memory_board.",
            },
            "structure": {
                "status": "passed",
                "summary": "Route memory reads and mutations through the board-governed store with explicit audit trails.",
            },
            "implementation": {
                "status": "implemented",
                "summary": "The gateway applies phase and module admission checks before forwarding to the live memory store.",
            },
            "verification": {
                "status": "verified",
                "summary": "Gateway coverage proves routed operations succeed and bypass attempts fail closed.",
                "evidence": [
                    "pytest tests/test_memory_board_enforcer.py -q",
                    "pytest tests/test_api.py -k memory",
                ],
            },
        },
        "compliance": {
            "stores_persistent_user_metadata": False,
            "creates_user_identity_profiles": False,
            "retains_behavioral_history": False,
            "infers_user_labels": False,
            "builds_personality_models": False,
            "builds_behavior_models": False,
            "stores_live_signals": False,
            "reconstructs_signals": False,
            "requires_identity_history": False,
            "adaptive_logic_scope": "system",
            "alters_nova_tone": False,
            "alters_nova_role": False,
            "alters_nova_constancy": False,
            "bypasses_jarvis_authority": False,
            "bypasses_routing": False,
            "logs_user_identity": False,
            "logs_behavior_patterns": False,
            "logs_biometric_traces": False,
            "hidden_logging": False,
            "exfiltrates_data": False,
        },
    })


class MemoryBoardEnforcer:
    """Strict gateway around the live Jarvis memory board/store."""

    def __init__(
        self,
        memory_store: Any,
        *,
        component_id: str = MEMORY_BOARD_ENFORCER_COMPONENT_ID,
        immune_controller: ImmuneSystemController | None = None,
        module_governance_controller: ModuleGovernanceController | None = None,
        actor_id: str = "memory_board_enforcer",
    ):
        self.memory_store = memory_store
        self.component_id = _clean_text(component_id, limit=120).lower().replace(" ", "_")
        self.immune_controller = immune_controller or immune_system
        self.module_governance_controller = module_governance_controller or module_governance
        self.actor_id = _clean_text(actor_id, limit=80) or "memory_board_enforcer"
        self._authority_token = uuid.uuid4().hex
        self._last_audit: dict[str, Any] | None = None
        if hasattr(self.memory_store, "configure_governance_enforcer"):
            self.memory_store.configure_governance_enforcer(
                self._authority_token,
                component_id=self.component_id,
                reporter=self._handle_bypass_report,
            )
        self._ensure_phase_component()
        self._ensure_module_record()

    def last_audit(self) -> dict[str, Any] | None:
        """Return the latest gateway audit payload."""
        return dict(self._last_audit) if isinstance(self._last_audit, dict) else None

    def _handle_bypass_report(self, payload: dict[str, Any]) -> None:
        """Escalate one detected bypass attempt into governance and immune traces."""
        self._ensure_module_record()
        reason = _clean_text(
            payload.get("detail")
            or f"Live memory operation `{payload.get('action')}` attempted outside the memory board enforcer.",
            limit=220,
        )
        details = {
            "action": str(payload.get("action") or "").strip().lower() or "unknown",
            "component_id": self.component_id,
            "reported_by": "memory_store",
        }
        if payload.get("memory_id"):
            details["memory_id"] = str(payload.get("memory_id") or "").strip()
        signal_result = self.module_governance_controller.report_runtime_signal(
            self.component_id,
            signal_type="unauthorized_memory_creation",
            reason=reason,
            details=details,
            actor_id=self.actor_id,
            actor_role="system",
        )
        self._last_audit = {
            "decision": "BLOCK",
            "operation": details["action"],
            "runtime_context": _normalize_runtime_context(payload.get("runtime_context")),
            "reason": reason,
            "phase_gate": self._phase_gate_payload("ALLOW", runtime_context=payload.get("runtime_context")),
            "module_governance": {
                "decision": "BLOCK",
                "module_id": self.component_id,
                "status": str((signal_result.get("module") or {}).get("status") or "").strip().lower() or "unknown",
                "reason": reason,
            },
            "bypass_detected": True,
            "immune_update": dict(signal_result.get("immune_update") or {}),
        }

    def _ensure_phase_component(self) -> dict[str, Any]:
        try:
            component = get_component(self.component_id)
        except ComponentNotRegisteredError:
            register_component(
                GovernedComponent(
                    component_id=self.component_id,
                    name="Memory Board Enforcer",
                    component_type="memory_gateway",
                    phase=Phase.ACTIVE,
                    allowed_contexts=list(MEMORY_BOARD_ENFORCER_ALLOWED_CONTEXTS),
                    notes="Live gateway for Jarvis memory operations.",
                    validation_metadata={"admitted_by": "memory_board_enforcer"},
                )
            )
            component = get_component(self.component_id)
        return _wrap_ul_payload({
            "component_id": component.component_id,
            "phase": component.phase.value,
            "allowed_contexts": list(component.allowed_contexts),
        })

    def _ensure_module_record(self) -> dict[str, Any]:
        record = self.module_governance_controller.get_module(self.component_id)
        if record is not None:
            return dict(record)
        admitted = self.module_governance_controller.admit_module(
            build_memory_board_enforcer_module_spec(self.component_id),
            actor_id=self.actor_id,
            actor_role="system",
        )
        return dict(admitted.get("module") or {})

    def _phase_gate_payload(self, decision: str, *, runtime_context: Any, reason: str | None = None) -> dict[str, Any]:
        component = self._ensure_phase_component()
        return _wrap_ul_payload({
            "decision": "ALLOW" if str(decision).upper() == "ALLOW" else "BLOCK",
            "component": component,
            "runtime_context": _normalize_runtime_context(runtime_context),
            "reason": _clean_text(reason) or None,
        })

    def _seam_runtime_dir(self) -> Any:
        return getattr(self.module_governance_controller, "runtime_dir", None)

    def _authorize(
        self,
        operation: str,
        *,
        runtime_context: str,
        mutation: bool,
        target: str | None = None,
    ) -> dict[str, Any]:
        normalized_operation = _clean_text(operation, limit=80).lower().replace(" ", "_")
        normalized_context = _normalize_runtime_context(runtime_context)

        phase_payload = self._phase_gate_payload("ALLOW", runtime_context=normalized_context)
        try:
            assert_executable(self.component_id, normalized_context)
        except PhaseGateError as exc:
            phase_payload = self._phase_gate_payload("BLOCK", runtime_context=normalized_context, reason=str(exc))

        module_record = self._ensure_module_record()
        module_status = str(module_record.get("status") or "").strip().lower() or "unknown"
        allowed_statuses = {"admitted"}
        module_decision = "ALLOW" if module_status in allowed_statuses else "BLOCK"
        module_reason = None
        if module_decision == "BLOCK":
            module_reason = (
                "Memory mutations are blocked because the gateway is not admitted."
                if mutation
                else "Memory reads are blocked because the gateway is not admitted."
            )

        decision = "ALLOW" if phase_payload["decision"] == "ALLOW" and module_decision == "ALLOW" else "BLOCK"
        audit = {
            "decision": decision,
            "operation": normalized_operation,
            "target": _clean_text(target, limit=120) or None,
            "runtime_context": normalized_context,
            "phase_gate": phase_payload,
            "module_governance": {
                "decision": module_decision,
                "module_id": self.component_id,
                "status": module_status,
                "reason": module_reason,
            },
            "bypass_detected": False,
        }
        self._last_audit = audit
        if decision == "BLOCK":
            blocked_reason = phase_payload.get("reason") or module_reason or "Memory operation blocked by governance."
            record_seam_event(
                classification="boundary_violation",
                source=self.actor_id,
                boundary="memory_board_gateway",
                severity="high",
                decision="BLOCK",
                component_id=self.component_id,
                runtime_context=normalized_context,
                event_type="memory_operation_blocked",
                reason=blocked_reason,
                details={
                    "operation": normalized_operation,
                    "target": audit["target"],
                    "phase_gate": dict(phase_payload),
                    "module_governance": dict(audit["module_governance"]),
                },
                runtime_dir=self._seam_runtime_dir(),
            )
            raise MemoryBoardEnforcerError(blocked_reason)
        return audit

    def list_memories(self, *, runtime_context: str = "operator_runtime", **kwargs: Any):
        self._authorize("list_memories", runtime_context=runtime_context, mutation=False)
        return self.memory_store.list_memories(
            **kwargs,
            _enforcer_authority=self._authority_token,
        )

    def get_memory(self, memory_id: str, *, runtime_context: str = "operator_runtime"):
        self._authorize(
            "get_memory",
            runtime_context=runtime_context,
            mutation=False,
            target=memory_id,
        )
        return self.memory_store.get_memory(
            memory_id,
            _enforcer_authority=self._authority_token,
        )

    def get_memory_board_snapshot(self, *, runtime_context: str = "operator_runtime", **kwargs: Any):
        self._authorize("get_memory_board_snapshot", runtime_context=runtime_context, mutation=False)
        return self.memory_store.get_memory_board_snapshot(
            **kwargs,
            _enforcer_authority=self._authority_token,
        )

    def build_summary(
        self,
        *,
        truth_scope: str = "live",
        runtime_context: str = "operator_runtime",
    ):
        self._authorize("build_summary", runtime_context=runtime_context, mutation=False)
        return self.memory_store.build_summary(
            truth_scope=truth_scope,
            _enforcer_authority=self._authority_token,
        )

    def get_relevant_memories(
        self,
        query: str,
        limit: int = 4,
        *,
        runtime_context: str = "operator_runtime",
    ):
        self._authorize("get_relevant_memories", runtime_context=runtime_context, mutation=False)
        return self.memory_store.get_relevant_memories(
            query,
            limit=limit,
            _enforcer_authority=self._authority_token,
        )

    def render_memory_summary(
        self,
        query: str | None = None,
        limit: int = 5,
        *,
        runtime_context: str = "operator_runtime",
    ):
        self._authorize("render_memory_summary", runtime_context=runtime_context, mutation=False)
        return self.memory_store.render_memory_summary(
            query=query,
            limit=limit,
            _enforcer_authority=self._authority_token,
        )

    def suggest_merge_candidates(
        self,
        limit: int = 6,
        *,
        runtime_context: str = "operator_runtime",
    ):
        self._authorize("suggest_merge_candidates", runtime_context=runtime_context, mutation=False)
        return self.memory_store.suggest_merge_candidates(
            limit=limit,
            _enforcer_authority=self._authority_token,
        )

    def detect_conflicts(
        self,
        limit: int = 6,
        *,
        runtime_context: str = "operator_runtime",
    ):
        self._authorize("detect_conflicts", runtime_context=runtime_context, mutation=False)
        return self.memory_store.detect_conflicts(
            limit=limit,
            _enforcer_authority=self._authority_token,
        )

    def list_why_gaps(
        self,
        limit: int = 6,
        *,
        runtime_context: str = "operator_runtime",
    ):
        self._authorize("list_why_gaps", runtime_context=runtime_context, mutation=False)
        return self.memory_store.list_why_gaps(
            limit=limit,
            _enforcer_authority=self._authority_token,
        )

    def list_archived_memories(
        self,
        limit: int = 6,
        *,
        truth_scope: str = "live",
        runtime_context: str = "operator_runtime",
    ):
        self._authorize("list_archived_memories", runtime_context=runtime_context, mutation=False)
        return self.memory_store.list_archived_memories(
            limit=limit,
            truth_scope=truth_scope,
            _enforcer_authority=self._authority_token,
        )

    def build_governance_snapshot(
        self,
        limit: int = 6,
        *,
        runtime_context: str = "operator_runtime",
    ):
        self._authorize("build_governance_snapshot", runtime_context=runtime_context, mutation=False)
        return self.memory_store.build_governance_snapshot(
            limit=limit,
            _enforcer_authority=self._authority_token,
        )

    def add_memory(self, *args: Any, runtime_context: str = "operator_runtime", **kwargs: Any):
        self._authorize("add_memory", runtime_context=runtime_context, mutation=True)
        return self.memory_store.add_memory(*args, _enforcer_authority=self._authority_token, **kwargs)

    def add_override(self, *args: Any, runtime_context: str = "operator_runtime", **kwargs: Any):
        self._authorize("add_override", runtime_context=runtime_context, mutation=True)
        return self.memory_store.add_override(*args, _enforcer_authority=self._authority_token, **kwargs)

    def delete_memory(self, memory_id: str, *, runtime_context: str = "operator_runtime"):
        self._authorize(
            "delete_memory",
            runtime_context=runtime_context,
            mutation=True,
            target=memory_id,
        )
        return self.memory_store.delete_memory(memory_id, _enforcer_authority=self._authority_token)

    def update_memory(self, memory_id: str, *, runtime_context: str = "operator_runtime", **kwargs: Any):
        self._authorize(
            "update_memory",
            runtime_context=runtime_context,
            mutation=True,
            target=memory_id,
        )
        return self.memory_store.update_memory(
            memory_id,
            _enforcer_authority=self._authority_token,
            **kwargs,
        )

    def archive_memory(self, memory_id: str, *, runtime_context: str = "operator_runtime", **kwargs: Any):
        self._authorize(
            "archive_memory",
            runtime_context=runtime_context,
            mutation=True,
            target=memory_id,
        )
        return self.memory_store.archive_memory(
            memory_id,
            _enforcer_authority=self._authority_token,
            **kwargs,
        )

    def merge_memories(self, *, runtime_context: str = "operator_runtime", **kwargs: Any):
        self._authorize(
            "merge_memories",
            runtime_context=runtime_context,
            mutation=True,
            target=str(kwargs.get("target_id") or "").strip() or None,
        )
        return self.memory_store.merge_memories(
            _enforcer_authority=self._authority_token,
            **kwargs,
        )

    def install_memory_module(
        self,
        slot_id: str,
        module: dict[str, Any] | Any,
        *,
        runtime_context: str = "operator_runtime",
    ):
        self._authorize(
            "install_memory_module",
            runtime_context=runtime_context,
            mutation=True,
            target=slot_id,
        )
        return self.memory_store.install_memory_module(
            slot_id,
            module,
            _enforcer_authority=self._authority_token,
        )

    def swap_memory_module(
        self,
        slot_id: str,
        module: dict[str, Any] | Any,
        *,
        migration_records: list[dict[str, Any]] | None = None,
        runtime_context: str = "operator_runtime",
    ):
        self._authorize(
            "swap_memory_module",
            runtime_context=runtime_context,
            mutation=True,
            target=slot_id,
        )
        return self.memory_store.swap_memory_module(
            slot_id,
            module,
            migration_records=migration_records,
            _enforcer_authority=self._authority_token,
        )

    def compact_state(self, *, runtime_context: str = "operator_runtime"):
        self._authorize("compact_state", runtime_context=runtime_context, mutation=True)
        return self.memory_store.compact_state(_enforcer_authority=self._authority_token)

    def record_board_event(
        self,
        *,
        action: str,
        slot_id: str | None,
        memory: dict[str, Any] | None = None,
        decision: str = "allow",
        source: str | None = None,
        detail: str | None = None,
        meta: dict[str, Any] | None = None,
        runtime_context: str = "operator_runtime",
    ) -> dict[str, Any]:
        self._authorize(
            "record_board_event",
            runtime_context=runtime_context,
            mutation=True,
            target=slot_id,
        )
        return self.memory_store.record_board_event(
            action=action,
            slot_id=slot_id,
            memory=memory,
            decision=decision,
            source=source,
            detail=detail,
            meta=meta,
            _enforcer_authority=self._authority_token,
        )

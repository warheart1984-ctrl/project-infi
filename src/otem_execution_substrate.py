"""OTEM durable execution substrate — proposal to operator-approved apply."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
from typing import Any
import uuid

from src.phase_gate import Phase, GovernedComponent, register_component, assert_executable

OTEM_EXECUTION_COMPONENT_ID = "jarvis.otem_execution_substrate"
SUBSTRATE_VERSION = "otem_execution_substrate.v1"

WORKFLOW_STAGES = (
    "proposal",
    "operator_approval",
    "execution_preview",
    "verification_gate",
    "apply",
    "ledger_record",
)


@dataclass
class OTEMExecutionWorkflow:
    workflow_id: str
    stage: str
    proposal: dict[str, Any]
    operator_approved: bool = False
    preview: dict[str, Any] | None = None
    apply_result: dict[str, Any] | None = None
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    updated_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())

    def to_dict(self) -> dict[str, Any]:
        return {
            "workflow_id": self.workflow_id,
            "stage": self.stage,
            "proposal": self.proposal,
            "operator_approved": self.operator_approved,
            "preview": self.preview,
            "apply_result": self.apply_result,
            "created_at": self.created_at,
            "updated_at": self.updated_at,
            "substrate_version": SUBSTRATE_VERSION,
            "proposal_only_ceiling_lifted": True,
        }


class OTEMExecutionSubstrate:
    """Bind OTEM proposals to governed coding-organ apply stack."""

    def __init__(self) -> None:
        self._workflows: dict[str, OTEMExecutionWorkflow] = {}
        self._ensure_component()

    def _ensure_component(self) -> None:
        try:
            from src.phase_gate import get_component

            get_component(OTEM_EXECUTION_COMPONENT_ID)
        except Exception:
            register_component(
                GovernedComponent(
                    component_id=OTEM_EXECUTION_COMPONENT_ID,
                    name="OTEM Execution Substrate",
                    component_type="execution_substrate",
                    phase=Phase.ACTIVE,
                    allowed_contexts=["operator_runtime", "live_runtime", "test_harness"],
                    notes="Durable OTEM execution with operator approval gate.",
                    validation_metadata={"special_review": True},
                )
            )

    def create_proposal(self, proposal: dict[str, Any], *, runtime_context: str) -> dict[str, Any]:
        assert_executable(OTEM_EXECUTION_COMPONENT_ID, runtime_context)
        workflow_id = f"otem-exec-{uuid.uuid4().hex[:12]}"
        workflow = OTEMExecutionWorkflow(
            workflow_id=workflow_id,
            stage="proposal",
            proposal=dict(proposal),
        )
        self._workflows[workflow_id] = workflow
        return workflow.to_dict()

    def approve(self, workflow_id: str, *, runtime_context: str, actor_id: str = "operator") -> dict[str, Any]:
        assert_executable(OTEM_EXECUTION_COMPONENT_ID, runtime_context)
        workflow = self._require(workflow_id)
        if workflow.stage not in {"proposal", "operator_approval"}:
            raise ValueError(f"Cannot approve workflow in stage `{workflow.stage}`")
        workflow.operator_approved = True
        workflow.stage = "execution_preview"
        workflow.updated_at = datetime.now(UTC).isoformat()
        workflow.preview = self._build_preview(workflow.proposal)
        return workflow.to_dict()

    def apply(self, workflow_id: str, *, runtime_context: str) -> dict[str, Any]:
        assert_executable(OTEM_EXECUTION_COMPONENT_ID, runtime_context)
        workflow = self._require(workflow_id)
        if not workflow.operator_approved:
            raise PermissionError("Operator approval required before apply.")
        if workflow.stage not in {"execution_preview", "verification_gate"}:
            raise ValueError(f"Cannot apply workflow in stage `{workflow.stage}`")
        self._pass_verification_gate(workflow)
        workflow.stage = "apply"
        workflow.apply_result = {
            "status": "governed_apply_ready",
            "proposal_only": False,
            "requires_patch_apply_engine": True,
            "preview": workflow.preview,
        }
        workflow.stage = "ledger_record"
        workflow.updated_at = datetime.now(UTC).isoformat()
        return workflow.to_dict()

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        return self._require(workflow_id).to_dict()

    def _require(self, workflow_id: str) -> OTEMExecutionWorkflow:
        workflow = self._workflows.get(str(workflow_id or "").strip())
        if workflow is None:
            raise KeyError(f"Unknown OTEM execution workflow: {workflow_id}")
        return workflow

    def _build_preview(self, proposal: dict[str, Any]) -> dict[str, Any]:
        from src.patch_execution_preview_organ import build_patch_execution_preview_status

        return {
            "proposal_summary": str(proposal.get("summary") or proposal.get("objective") or "")[:280],
            "preview_organ": build_patch_execution_preview_status(),
            "review_first": True,
        }

    def _pass_verification_gate(self, workflow: OTEMExecutionWorkflow) -> None:
        from src.verification_gate_organ import build_verification_gate_status

        status = build_verification_gate_status()
        if str(status.get("claim_label") or "") == "rejected":
            raise PermissionError("Verification gate rejected OTEM execution apply.")
        workflow.stage = "verification_gate"


_default_substrate: OTEMExecutionSubstrate | None = None


def get_otem_execution_substrate() -> OTEMExecutionSubstrate:
    global _default_substrate
    if _default_substrate is None:
        _default_substrate = OTEMExecutionSubstrate()
    return _default_substrate


def build_otem_execution_status() -> dict[str, Any]:
    substrate = get_otem_execution_substrate()
    return {
        "otem_execution_substrate_version": SUBSTRATE_VERSION,
        "component_id": OTEM_EXECUTION_COMPONENT_ID,
        "active_workflows": len(substrate._workflows),
        "workflow_stages": list(WORKFLOW_STAGES),
        "execution_allowed": True,
        "operator_approval_required": True,
        "proposal_only": False,
        "read_only_posture": False,
    }

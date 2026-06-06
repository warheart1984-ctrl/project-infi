"""OTEM durable execution substrate — proposal to operator-approved apply."""

# Mythic: Otem Execution Substrate
# Engineering: OtemExecutionSubstrateEngine
from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime
from src.datetime_compat import UTC
from pathlib import Path
from typing import Any
import json
import os
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


def _default_runtime_dir() -> Path:
    configured = os.getenv("AAIS_RUNTIME_DIR")
    if configured:
        return Path(configured).expanduser()
    return Path(__file__).resolve().parents[1] / ".runtime"


class OTEMExecutionSubstrate:
    """Bind OTEM proposals to governed coding-organ apply stack."""

    def __init__(self, *, runtime_dir: Path | None = None) -> None:
        self._runtime_dir = runtime_dir or _default_runtime_dir()
        self._persist_path = self._runtime_dir / "otem" / "workflows.jsonl"
        self._workflows: dict[str, OTEMExecutionWorkflow] = {}
        self._ensure_component()
        self._load_persisted()

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
        self._persist_workflow(workflow)
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
        self._persist_workflow(workflow)
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

        # --- MVP plumbing: actually wire to live contractors when reachable ---
        # This makes OTEM approval -> execution end-to-end real instead of pure simulation.
        # Uses the same clients the organs/status use. Robust: falls back visibly if contractors down.
        execution_results = []
        contractors_reachable = {}
        try:
            from src.forge_client import forge_client
            from src.evolve_client import evolve_client

            # Probe reachability (lightweight, same as health)
            try:
                forge_client.health()
                contractors_reachable["forge"] = True
            except Exception:
                contractors_reachable["forge"] = False

            try:
                evolve_client.health()
                contractors_reachable["evolve"] = True
            except Exception:
                contractors_reachable["evolve"] = False

            plan = workflow.proposal.get("plan") or []
            for step in plan:
                step_type = str(step.get("type") or step.get("kind") or step.get("action") or "").lower()
                step_label = step.get("label") or step.get("id") or "step"
                config = step.get("config") or step.get("context") or {}

                if "forge" in step_type or "patch" in step_type or "code" in step_type:
                    if contractors_reachable.get("forge"):
                        try:
                            kind = config.get("kind") or "generate_diff"
                            ctx = config.get("context") or config
                            result = forge_client.request(kind=kind, context=dict(ctx), task_id=f"otem-{workflow_id}")
                            execution_results.append({
                                "step_id": step.get("id"),
                                "label": step_label,
                                "via": "live_forge",
                                "kind": kind,
                                "result_summary": result.get("summary") or str(result)[:200],
                                "raw": result,
                            })
                        except Exception as e:
                            execution_results.append({
                                "step_id": step.get("id"),
                                "label": step_label,
                                "via": "live_forge",
                                "error": str(e)[:200],
                            })
                    else:
                        execution_results.append({
                            "step_id": step.get("id"),
                            "label": step_label,
                            "via": "simulation",
                            "note": "Forge contractor not reachable (start with scripts/start_contractors.py)",
                        })

                elif "evolve" in step_type or "mutation" in step_type or "search" in step_type:
                    if contractors_reachable.get("evolve"):
                        try:
                            task = config.get("task") or workflow.proposal.get("objective") or "evolve from otem plan"
                            result = evolve_client.evolve(
                                task=task,
                                config=dict(config.get("config") or {}),
                                evaluation=dict(config.get("evaluation") or {}),
                                constraints=dict(config.get("constraints") or {}),
                                job_id=f"otem-{workflow_id}",
                            )
                            execution_results.append({
                                "step_id": step.get("id"),
                                "label": step_label,
                                "via": "live_evolve",
                                "result_summary": result.get("summary") or str(result)[:200],
                                "raw": result,
                            })
                        except Exception as e:
                            execution_results.append({
                                "step_id": step.get("id"),
                                "label": step_label,
                                "via": "live_evolve",
                                "error": str(e)[:200],
                            })
                    else:
                        execution_results.append({
                            "step_id": step.get("id"),
                            "label": step_label,
                            "via": "simulation",
                            "note": "Evolve contractor not reachable (start with scripts/start_contractors.py)",
                        })
                else:
                    execution_results.append({
                        "step_id": step.get("id"),
                        "label": step_label,
                        "via": "simulation",
                        "note": "no matching contractor for step type",
                    })

        except Exception as e:
            execution_results.append({"via": "error", "error": f"contractor wiring failed: {str(e)[:200]}"})

        workflow.apply_result = {
            "status": "governed_apply_complete",
            "proposal_only": False,
            "requires_patch_apply_engine": True,
            "preview": workflow.preview,
            "contractors_reachable": contractors_reachable,
            "execution_results": execution_results,
            "message": "OTEM plan steps routed to live contractors where available; results captured for observability.",
        }
        # --- end MVP execution wiring ---

        workflow.stage = "ledger_record"
        workflow.updated_at = datetime.now(UTC).isoformat()
        self._persist_workflow(workflow)
        return workflow.to_dict()

    def _persist_workflow(self, workflow: OTEMExecutionWorkflow) -> None:
        self._persist_path.parent.mkdir(parents=True, exist_ok=True)
        with self._persist_path.open("a", encoding="utf-8") as handle:
            handle.write(json.dumps(workflow.to_dict(), sort_keys=True) + "\n")

    def _load_persisted(self) -> None:
        if not self._persist_path.is_file():
            return
        latest: dict[str, dict[str, Any]] = {}
        with self._persist_path.open(encoding="utf-8") as handle:
            for line in handle:
                line = line.strip()
                if not line:
                    continue
                try:
                    row = json.loads(line)
                except json.JSONDecodeError:
                    continue
                workflow_id = str(row.get("workflow_id") or "").strip()
                if workflow_id:
                    latest[workflow_id] = row
        for workflow_id, row in latest.items():
            self._workflows[workflow_id] = OTEMExecutionWorkflow(
                workflow_id=workflow_id,
                stage=str(row.get("stage") or "proposal"),
                proposal=dict(row.get("proposal") or {}),
                operator_approved=bool(row.get("operator_approved")),
                preview=dict(row.get("preview") or {}) if row.get("preview") else None,
                apply_result=dict(row.get("apply_result") or {}) if row.get("apply_result") else None,
                created_at=str(row.get("created_at") or datetime.now(UTC).isoformat()),
                updated_at=str(row.get("updated_at") or datetime.now(UTC).isoformat()),
            )

    def get_workflow(self, workflow_id: str) -> dict[str, Any]:
        return self._require(workflow_id).to_dict()

    def _require(self, workflow_id: str) -> OTEMExecutionWorkflow:
        workflow = self._workflows.get(str(workflow_id or "").strip())
        if workflow is None:
            raise KeyError(f"Unknown OTEM execution workflow: {workflow_id}")
        return workflow

    def _build_preview(self, proposal: dict[str, Any]) -> dict[str, Any]:
        from src.patch_execution_preview_organ import build_patch_execution_preview_status

        preview = {
            "proposal_summary": str(proposal.get("summary") or proposal.get("objective") or "")[:280],
            "preview_organ": build_patch_execution_preview_status(),
            "review_first": True,
        }
        # MVP plumbing: enrich preview with realistic "what live contractors would do" dry-run info
        # when they are reachable (via start_contractors.py). This gives the operator a concrete
        # pre-approval view instead of pure theory.
        preview["contractor_preview"] = self._preview_contractor_usage(proposal)
        return preview

    def _preview_contractor_usage(self, proposal: dict[str, Any]) -> dict[str, Any]:
        """Dry-run preview of which contractors the plan would hit (no actual execution)."""
        reachable = {}
        try:
            forge_client.health()
            reachable["forge"] = True
        except Exception:
            reachable["forge"] = False
        try:
            evolve_client.health()
            reachable["evolve"] = True
        except Exception:
            reachable["evolve"] = False

        plan = proposal.get("plan") or []
        steps = []
        for step in plan:
            step_type = str(step.get("type") or step.get("kind") or step.get("action") or "").lower()
            step_label = step.get("label") or step.get("id") or "step"
            if "forge" in step_type or "patch" in step_type or "code" in step_type:
                steps.append({
                    "step_id": step.get("id"),
                    "label": step_label,
                    "would_use": "live_forge" if reachable.get("forge") else "simulation (forge not reachable)",
                })
            elif "evolve" in step_type or "mutation" in step_type or "search" in step_type:
                steps.append({
                    "step_id": step.get("id"),
                    "label": step_label,
                    "would_use": "live_evolve" if reachable.get("evolve") else "simulation (evolve not reachable)",
                })
            else:
                steps.append({
                    "step_id": step.get("id"),
                    "label": step_label,
                    "would_use": "simulation (no matching contractor)",
                })
        return {
            "contractors_reachable": reachable,
            "plan_steps": steps,
            "note": "This is a dry-run preview. Real execution happens on approve+apply if contractors are up.",
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
        "mvp_note": "apply() now routes plan steps to live Forge/Evolve contractors (when reachable via start_contractors.py) and records real execution_results for observability.",
    }

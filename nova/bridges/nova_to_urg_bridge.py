"""Bridge Lawful Nova LAW_EVAL mission intents into URG mission payloads."""

from __future__ import annotations

from typing import Any
from uuid import uuid4

from nova.bridges import identity_bridge, panel_store, reference_bridge


def _law_eval_id(evaluation: dict[str, Any]) -> str:
    proof = str(evaluation.get("invariant_proof_id") or "").strip()
    if proof:
        return proof
    candidate = dict(evaluation.get("candidate_intent") or {})
    return str(candidate.get("id") or f"law-eval-{uuid4().hex[:12]}")


def build_law_context() -> dict[str, Any]:
    """Assemble LawContext fields from identity + reference bridges."""
    identity = identity_bridge.get_current_identity()
    binding = reference_bridge.current_reference_binding()
    return {
        "actor_id": str(identity.identity.get("instance_id") or identity.identity.get("subject_id") or "nova-local"),
        "steward_id": str(identity.identity.get("steward_id") or identity.identity.get("operator_id") or "operator"),
        "epoch": identity.epoch,
        "t5_ref_signal_hash": binding.ref_hash,
        "t5_metrics": dict(binding.metrics),
        "identity": dict(identity.identity),
        "drift_scores": dict(identity.drift_scores),
    }


class NovaToURGBridge:
    """Package a admitted LAW_EVAL mission intent for URG /api/ugr/mission/run."""

    def __init__(self, *, panels: panel_store.PanelStore | None = None) -> None:
        self._panels = panels or panel_store.PanelStore()

    def mission_from_law_eval(
        self,
        *,
        evaluation: dict[str, Any],
        operator_id: str,
        aais_instance_id: str,
        prompt: str,
        tenant_id: str = "tenant:acme",
        law_context: dict[str, Any] | None = None,
    ) -> dict[str, Any]:
        ctx = dict(law_context or build_law_context())
        law_eval_id = _law_eval_id(evaluation)
        candidate = dict(evaluation.get("candidate_intent") or {})
        payload = dict(candidate.get("payload") or {})
        steps = list(payload.get("steps") or [])
        if not steps:
            steps = [
                {
                    "step_id": "governed-spine",
                    "objective": prompt.strip() or "Governed constitutional spine mission",
                    "organ_id": "organ-local-tiny",
                }
            ]

        mission = {
            "operator_id": operator_id,
            "tenant_id": tenant_id,
            "aais_instance_id": aais_instance_id,
            "region_id": str(payload.get("region_id") or "tenant-us"),
            "intent": str(payload.get("intent") or "governed_constitutional_spine"),
            "objective": str(payload.get("objective") or prompt.strip() or "Governed mission"),
            "execution_mode": str(payload.get("execution_mode") or "DRY_RUN"),
            "constraints": dict(
                payload.get("constraints")
                or {
                    "max_total_cost_units": 25,
                    "risk_ceiling": "medium",
                    "required_region": "tenant-us",
                }
            ),
            "context": {
                "forbid_express": True,
                "law_eval_id": law_eval_id,
                "intent_type": "mission",
                "governed": True,
                "law_context": ctx,
                "t5_ref_signal_hash": ctx.get("t5_ref_signal_hash"),
                "panels": self._panel_metadata(),
            },
            "steps": steps,
            "halt_on_failure": bool(payload.get("halt_on_failure", True)),
        }
        self._panels.append_steward_event(
            kind="nova_to_urg_mission",
            payload={
                "law_eval_id": law_eval_id,
                "mission_intent": mission["intent"],
                "step_count": len(steps),
            },
        )
        return mission

    def _panel_metadata(self) -> dict[str, Any]:
        return {
            "reflexive_count": len(self._panels.list_reflexive_events()),
            "steward_count": len(self._panels.list_steward_events()),
            "perception_count": len(self._panels.list_perception_snapshots()),
        }

    def is_mission_intent(self, evaluation: dict[str, Any]) -> bool:
        candidate = dict(evaluation.get("candidate_intent") or {})
        payload = dict(candidate.get("payload") or {})
        if str(payload.get("intent_type") or "").strip().lower() == "mission":
            return True
        if str(candidate.get("kind") or "").strip().upper() == "MISSION":
            return True
        return bool(payload.get("governed_mission"))

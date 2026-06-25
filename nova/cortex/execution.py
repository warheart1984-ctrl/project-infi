from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nova.cortex.router import CortexRouter
from nova.crk.panels.perception_health_panel import PerceptionHealthPanel
from nova.law_kernel.bootstrap import make_law_kernel_stack
from nova.law_kernel.models import Intent, LawContext, new_intent


@dataclass
class CortexExecutionResult:
    law_result: dict[str, Any]
    substrate_result: Any | None
    perception_snapshot: dict[str, Any] | None


class CortexExecutor:
    """Lawful cortex execution path with perception health hooks (T4-PER-1)."""

    def __init__(
        self,
        *,
        router: CortexRouter | None = None,
        perception_panel: PerceptionHealthPanel | None = None,
    ) -> None:
        lawful_router = make_law_kernel_stack()
        self.router = router or CortexRouter(lawful_router)
        self.perception_panel = perception_panel or PerceptionHealthPanel()

    def execute(
        self,
        intent: Intent,
        *,
        actor_id: str,
        domain: str,
        epoch: str,
        lineage_contract_id: str,
        lineage_event_id: str = "",
    ) -> CortexExecutionResult:
        law_result = self.router.route(
            intent,
            actor_id=actor_id,
            domain=domain,
            epoch=epoch,
            lineage_contract_id=lineage_contract_id,
            lineage_event_id=lineage_event_id,
        )
        substrate_result = None
        if law_result.get("admitted"):
            substrate_result = self.router.router.substrate_executor.last_result
            if substrate_result is None:
                substrate_result = law_result

        context = LawContext(
            actor_id=actor_id,
            domain=domain,
            epoch=epoch,
            lineage_contract_id=lineage_contract_id,
            t5_ref_signal_hash=str(
                law_result.get("evaluation", {}).get("t5_ref_signal_hash", "")
            ),
            lineage_event_id=lineage_event_id,
        )
        perception_snapshot = None
        if law_result.get("admitted") and self._has_perceptual_io(intent):
            snap = self.perception_panel.record_snapshot(intent, context, substrate_result)
            perception_snapshot = snap.stable_dict()

        return CortexExecutionResult(
            law_result=law_result,
            substrate_result=substrate_result,
            perception_snapshot=perception_snapshot,
        )

    def handle(
        self,
        *,
        kind: str,
        payload: dict[str, Any],
        actor_id: str,
        domain: str,
        epoch: str,
        lineage_contract_id: str,
        lineage_event_id: str | None = None,
    ) -> CortexExecutionResult:
        intent = new_intent(kind=kind, payload=payload, origin=actor_id)
        return self.execute(
            intent,
            actor_id=actor_id,
            domain=domain,
            epoch=epoch,
            lineage_contract_id=lineage_contract_id,
            lineage_event_id=lineage_event_id or "",
        )

    @staticmethod
    def _has_perceptual_io(intent: Intent) -> bool:
        if intent.payload.get("capability"):
            return True
        if intent.payload.get("tool_name"):
            return True
        return intent.kind in {"ACT", "ASK"}

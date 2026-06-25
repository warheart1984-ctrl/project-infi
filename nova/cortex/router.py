from __future__ import annotations

from typing import Any

from nova.crk.panels.perception_health_panel import PerceptionHealthPanel
from nova.crk.panels.reflexive_evaluation_panel import ReflexiveEvaluationPanel
from nova.law_kernel.models import Intent, LawContext, new_intent
from nova.law_kernel.router import LawfulIntentRouter


class CortexRouter:
    """Routes all cortex intents through LawfulIntentRouter (CTX-1)."""

    def __init__(
        self,
        router: LawfulIntentRouter,
        *,
        reflexive_panel: ReflexiveEvaluationPanel | None = None,
    ) -> None:
        self.router = router
        self.reflexive_panel = reflexive_panel or ReflexiveEvaluationPanel()

    def route(
        self,
        intent: Intent,
        *,
        actor_id: str,
        domain: str,
        epoch: str,
        lineage_contract_id: str,
        lineage_event_id: str = "",
    ) -> dict[str, Any]:
        result = self.router.route(
            intent,
            actor_id=actor_id,
            domain=domain,
            epoch=epoch,
            lineage_contract_id=lineage_contract_id,
            lineage_event_id=lineage_event_id,
        )
        if result.get("admitted") and str(intent.payload.get("pit_mode", "")).upper() == "PIT-2":
            evaluation = result.get("evaluation", {})
            transformed = evaluation.get("transformed_intent")
            if transformed:
                transformed_intent = Intent(
                    id=transformed["id"],
                    kind=transformed["kind"],
                    payload=transformed["payload"],
                    origin=transformed["origin"],
                )
            else:
                transformed_intent = intent
            context = LawContext(
                actor_id=actor_id,
                domain=domain,
                epoch=epoch,
                lineage_contract_id=lineage_contract_id,
                t5_ref_signal_hash=evaluation.get("t5_ref_signal_hash", ""),
                lineage_event_id=lineage_event_id,
            )
            self.reflexive_panel.evaluate(transformed_intent, context)
        return result

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
    ) -> dict[str, Any]:
        intent = new_intent(kind=kind, payload=payload, origin=actor_id)
        return self.route(
            intent,
            actor_id=actor_id,
            domain=domain,
            epoch=epoch,
            lineage_contract_id=lineage_contract_id,
            lineage_event_id=lineage_event_id or "",
        )

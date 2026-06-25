from __future__ import annotations

from copy import deepcopy
from dataclasses import dataclass
import hashlib
import json
from typing import Any

from nova.law_kernel.bootstrap import make_law_kernel_stack
from nova.law_kernel.models import Intent, LawContext
from nova.law_kernel.router import LawfulIntentRouter


@dataclass(frozen=True)
class ContinuitySnapshot:
    id: str
    state_hash: str
    lineage_anchor: str


class ContinuityReplayEngine:
    def __init__(self, router: LawfulIntentRouter) -> None:
        self.router = router

    def snapshot(self) -> ContinuitySnapshot:
        state = {
            "laws": [law.to_dict() for law in self.router.ledger.all()],
        }
        blob = json.dumps(state, sort_keys=True).encode("utf-8")
        digest = hashlib.sha256(blob).hexdigest()
        return ContinuitySnapshot(
            id=f"snapshot:{digest[:8]}",
            state_hash=digest,
            lineage_anchor="continuity:root",
        )

    def replay(self, intent: Intent, ctx: LawContext) -> list[dict[str, Any]]:
        fresh = make_law_kernel_stack()
        fresh.route(
            intent,
            actor_id=ctx.actor_id,
            domain=ctx.domain,
            epoch=ctx.epoch,
            lineage_contract_id=ctx.lineage_contract_id,
            lineage_event_id=ctx.lineage_event_id,
        )
        return deepcopy(fresh.lineage_emitter.client.events)


class ContinuityDriftDetector:
    @staticmethod
    def _normalize(events: list[dict[str, Any]]) -> list[dict[str, Any]]:
        normalized: list[dict[str, Any]] = []
        for event in events:
            payload = event.get("payload", {})
            normalized.append(
                {
                    "kind": event.get("kind"),
                    "decision": payload.get("decision"),
                    "context": payload.get("context"),
                    "reasons": payload.get("reasons"),
                }
            )
        return normalized

    def compare_runs(
        self,
        events_a: list[dict[str, Any]],
        events_b: list[dict[str, Any]],
    ) -> bool:
        return self._normalize(events_a) == self._normalize(events_b)

    def detect_drift(
        self,
        events_a: list[dict[str, Any]],
        events_b: list[dict[str, Any]],
    ) -> bool:
        return not self.compare_runs(events_a, events_b)

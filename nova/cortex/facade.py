from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nova.law_kernel.bootstrap import make_law_kernel_stack
from nova.law_kernel.models import new_intent
from nova.law_kernel.router import LawfulIntentRouter


@dataclass
class NovaCortexFacade:
    """Single lawful entrypoint: Intent → LawKernel → Substrate."""

    router: LawfulIntentRouter

    @classmethod
    def from_kernel(cls) -> NovaCortexFacade:
        return cls(router=make_law_kernel_stack())

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
        return self.router.route(
            intent,
            actor_id=actor_id,
            domain=domain,
            epoch=epoch,
            lineage_contract_id=lineage_contract_id,
            lineage_event_id=lineage_event_id or "",
        )

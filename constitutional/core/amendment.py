from __future__ import annotations

from typing import Dict, Literal

from pydantic import BaseModel

from constitutional.core.models import StateObject, Transition
from constitutional.core.runtime import ConstitutionalStateRuntime

AmendmentChangeType = Literal["addition", "modification", "removal"]


class AmendmentContext(BaseModel):
    article: str
    change_type: AmendmentChangeType
    justification: str
    trigger_receipt_id: str


class AmendmentEngine:
    """Maps Article XVI amendment stages onto the universal constitutional state graph."""

    def __init__(self, csr: ConstitutionalStateRuntime) -> None:
        self.csr = csr

    def _make_transition(
        self,
        state: StateObject,
        to_state: str,
        receipt_id: str,
        runtime: str,
        legal_basis: str,
        accountable_party: str,
    ) -> Transition:
        return Transition(
            state_object_id=state.state_id,
            from_state=state.current_state,
            to_state=to_state,
            receipt_id=receipt_id,
            runtime=runtime,
            legal_basis=legal_basis,
            accountable_party=accountable_party,
        )

    def run_amendment_lifecycle(
        self,
        amendment_state: StateObject,
        ctx: AmendmentContext,
        receipt_ids: Dict[str, str],
        accountable_party: str,
    ) -> StateObject:
        """
        receipt_ids keys: proposal, evaluation, ratification, implementation, observation, closure
        (observation receipt id optional when closing directly from Observed)
        """
        self.csr.register_state(amendment_state)

        steps = [
            ("Evaluated", "proposal", f"proposal:{ctx.article}"),
            ("Approved", "evaluation", f"evaluation:{ctx.article}"),
            ("Executed", "ratification", f"ratification:{ctx.article}"),
            ("Observed", "implementation", f"implementation:{ctx.article}"),
            ("Closed", "closure", f"closure:{ctx.article}"),
        ]
        for to_state, receipt_key, legal_basis in steps:
            state = self.csr.get_state(amendment_state.state_id)
            t = self._make_transition(
                state,
                to_state,
                receipt_ids[receipt_key],
                "constitutional_amendment",
                legal_basis,
                accountable_party,
            )
            self.csr.apply_transition(t)

        return self.csr.get_state(amendment_state.state_id)

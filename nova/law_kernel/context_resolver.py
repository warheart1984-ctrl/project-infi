"""LawContextResolver — builds complete LawContext for every intent."""

from __future__ import annotations

from nova.law_kernel import t5_binding
from nova.law_kernel.models import Intent, LawContext, LineageContract
from nova.law_kernel.t5_binding import InvariantViolation


class LawContextResolver:
    def __init__(self, *, lineage_contracts: dict[str, LineageContract]) -> None:
        self.lineage_contracts = dict(lineage_contracts)

    def resolve(
        self,
        intent: Intent,
        *,
        actor_id: str,
        domain: str,
        epoch: str,
        lineage_contract_id: str,
        lineage_event_id: str = "",
    ) -> LawContext:
        ref = t5_binding.T5ReferenceSignal.current()
        contract = self.lineage_contracts.get(lineage_contract_id)
        if contract is None:
            raise InvariantViolation(
                "LINEAGE_CONTRACT_UNKNOWN",
                details={"contract_id": lineage_contract_id, "intent_id": intent.id},
            )
        if contract.current_ref_signal_hash != ref.hash:
            raise InvariantViolation(
                "REF_SIGNAL_MISMATCH",
                details={
                    "expected": contract.current_ref_signal_hash,
                    "got": ref.hash,
                    "contract_id": lineage_contract_id,
                },
            )
        return LawContext(
            actor_id=actor_id,
            domain=domain,
            epoch=epoch,
            lineage_contract_id=lineage_contract_id,
            t5_ref_signal_hash=ref.hash,
            lineage_event_id=lineage_event_id,
        )

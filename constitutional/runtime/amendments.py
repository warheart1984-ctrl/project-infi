"""Article XVI — Constitutional Amendment Process."""

from __future__ import annotations

from datetime import UTC, datetime

from pydantic import BaseModel, Field

from constitutional.runtime.runtime import ConstitutionalStateRuntime

from constitutional.runtime.receipts_v2 import (
    AMENDMENT_TRANSITIONS,
    AmendmentClosureReceiptV2,
    AmendmentEvaluationReceiptV2,
    AmendmentImplementationReceiptV2,
    AmendmentObservationReceiptV2,
    AmendmentPayloadV2,
    AmendmentProposalReceiptV2,
    AmendmentRatificationReceiptV2,
    AmendmentReceiptV2,
    AmendmentStage,
    BaseReceiptV2,
    is_amendment_trigger_receipt,
    is_receipt_v2_complete,
    validate_amendment_transition,
    validate_immutable_amendment,
    stable_json_hash,
)

AmendmentReceiptUnion = (
    AmendmentProposalReceiptV2
    | AmendmentEvaluationReceiptV2
    | AmendmentRatificationReceiptV2
    | AmendmentImplementationReceiptV2
    | AmendmentObservationReceiptV2
    | AmendmentClosureReceiptV2
)

STAGE_RECEIPT_TYPES: dict[AmendmentStage, type[AmendmentReceiptV2]] = {
    "proposed": AmendmentProposalReceiptV2,
    "evaluated": AmendmentEvaluationReceiptV2,
    "ratified": AmendmentRatificationReceiptV2,
    "implemented": AmendmentImplementationReceiptV2,
    "observed": AmendmentObservationReceiptV2,
    "closed": AmendmentClosureReceiptV2,
}


class AmendmentState(BaseModel):
    amendment_id: str
    article: str
    current_stage: AmendmentStage = "proposed"
    trigger_receipt_id: str
    version: int = 0
    receipt_ids: list[str] = Field(default_factory=list)

    def apply_receipt(self, receipt: AmendmentReceiptV2) -> None:
        if not is_receipt_v2_complete(receipt):
            raise ValueError(f"incomplete amendment receipt: {receipt.receipt_id}")
        stage = receipt.amendment.amendment_stage
        if self.version == 0 and stage != "proposed":
            raise ValueError("amendment must begin with proposed stage")
        if self.version > 0:
            validate_amendment_transition(self.current_stage, stage)
        validate_immutable_amendment(receipt.amendment)
        expected_type = STAGE_RECEIPT_TYPES[stage]
        if not isinstance(receipt, expected_type):
            raise TypeError(f"expected {expected_type.__name__} for stage {stage}")
        self.current_stage = stage
        self.version += 1
        self.receipt_ids.append(receipt.receipt_id)


class AmendmentReplayResult(BaseModel):
    amendment_id: str
    final_stage: AmendmentStage
    diverged: bool
    canonical_stage: AmendmentStage
    replay_hash: str


def begin_amendment(
    trigger_receipt: BaseReceiptV2,
    proposal: AmendmentProposalReceiptV2,
) -> AmendmentState:
    if not is_amendment_trigger_receipt(trigger_receipt):
        raise ValueError(f"receipt {trigger_receipt.receipt_id} is not a lawful amendment trigger")
    if proposal.amendment.trigger_receipt_id != trigger_receipt.receipt_id:
        raise ValueError("proposal must reference trigger_receipt_id")
    state = AmendmentState(
        amendment_id=proposal.receipt_id,
        article=proposal.amendment.article,
        trigger_receipt_id=trigger_receipt.receipt_id,
    )
    state.apply_receipt(proposal)
    return state


def process_amendment_receipts(
    trigger_receipt: BaseReceiptV2,
    receipts: list[AmendmentReceiptV2],
    *,
    csr: ConstitutionalStateRuntime | None = None,
    opened_at: datetime | None = None,
) -> AmendmentState:
    if not receipts:
        raise ValueError("amendment requires at least a proposal receipt")
    state = begin_amendment(trigger_receipt, receipts[0])  # type: ignore[arg-type]
    for receipt in receipts[1:]:
        state.apply_receipt(receipt)
    if csr is not None and state.current_stage == "closed":
        run_fitness_after_amendment(csr, opened_at=opened_at)
    return state


def run_fitness_after_amendment(
    csr: ConstitutionalStateRuntime,
    *,
    opened_at: datetime | None = None,
) -> None:
    """S-1.2 — mandatory fitness assessment after constitutional amendment."""
    from operator_kernel.heartbeat import run_fitness_audit

    now = opened_at or datetime.now(UTC).replace(microsecond=0)
    run_fitness_audit(now, csr)


def replay_amendment(
    trigger_receipt: BaseReceiptV2,
    receipts: list[AmendmentReceiptV2],
    canonical: AmendmentState,
) -> AmendmentReplayResult:
    replayed = process_amendment_receipts(trigger_receipt, receipts)
    diverged = (
        replayed.current_stage != canonical.current_stage
        or replayed.version != canonical.version
        or replayed.receipt_ids != canonical.receipt_ids
    )
    material = {
        "replayed": stable_json_hash(replayed.model_dump()),
        "canonical": stable_json_hash(canonical.model_dump()),
    }
    return AmendmentReplayResult(
        amendment_id=canonical.amendment_id,
        final_stage=replayed.current_stage,
        diverged=diverged,
        canonical_stage=canonical.current_stage,
        replay_hash=stable_json_hash(material),
    )

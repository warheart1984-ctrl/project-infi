"""Kernel Challenge Loop (KCL) — KΩ consequence exposure for the constitution itself."""

from __future__ import annotations

from dataclasses import dataclass, field
from datetime import UTC, datetime
from typing import Any, Literal

from pydantic import BaseModel, Field, model_validator

from src.crk1.errors import ConstitutionalError
from src.crk1.kernel_continuity_ledger import KernelContinuityLedger

ChallengeHypothesis = Literal["too_weak", "too_strong", "mis_scoped", "obsolete"]
ChallengeAction = Literal["refine", "narrow", "broaden", "deprecate", "split", "review"]
KCRStatus = Literal["Accepted", "Rejected", "Pending"]
ProposedChangeKind = Literal["Amendment", "Retirement", "Addition"]
ValidationResult = Literal["Sufficient", "Insufficient"]


def _now_iso() -> str:
    return datetime.now(UTC).replace(microsecond=0).isoformat().replace("+00:00", "Z")


class CFEvent(BaseModel):
    """Continuity failure event referenced by a Kernel Challenge."""

    id: str
    description: str
    silent_failure: bool = False


class ProposedChange(BaseModel):
    kind: ProposedChangeKind
    target: str
    diff: str


class ValidationProcess(BaseModel):
    steps: list[str] = Field(default_factory=list)
    result: ValidationResult = "Insufficient"


class KernelChallengeReceiptPayload(BaseModel):
    challenge_id: str
    kernel_version_before: str
    kernel_version_after: str | None = None
    status: KCRStatus = "Pending"
    reason: str
    cf_events: list[CFEvent] = Field(default_factory=list)
    receipts_implicated: list[str] = Field(default_factory=list)
    invariants_challenged: list[str] = Field(default_factory=list)
    proposed_changes: list[ProposedChange] = Field(default_factory=list)
    validation_process: ValidationProcess = Field(default_factory=ValidationProcess)


class KernelChallengeReceiptLinks(BaseModel):
    cf_event_ids: list[str] = Field(default_factory=list)
    receipt_ids: list[str] = Field(default_factory=list)
    old_kernel_id: str = ""
    new_kernel_id: str = ""


class KernelChallengeReceipt(BaseModel):
    """
    Kernel Challenge Receipt (KCR) — formal wire object per KΩ.4.

    Legacy accessors (`target_invariant`, `proposed_action`, etc.) support existing harnesses.
    """

    id: str
    type: Literal["KernelChallengeReceipt"] = "KernelChallengeReceipt"
    created_at: str = Field(default_factory=_now_iso)
    created_by: str = "G-ENGINE"
    epoch: int = 1
    payload: KernelChallengeReceiptPayload
    links: KernelChallengeReceiptLinks = Field(default_factory=KernelChallengeReceiptLinks)

    @model_validator(mode="after")
    def _sync_links(self) -> "KernelChallengeReceipt":
        self.links.cf_event_ids = [event.id for event in self.payload.cf_events]
        if self.payload.receipts_implicated:
            self.links.receipt_ids = list(self.payload.receipts_implicated)
        return self

    @property
    def challenge_id(self) -> str:
        return self.payload.challenge_id

    @property
    def target_invariant(self) -> str:
        if self.payload.invariants_challenged:
            return self.payload.invariants_challenged[0]
        return ""

    @property
    def evidence_grr_ids(self) -> list[str]:
        return list(self.payload.receipts_implicated)

    @property
    def hypothesis(self) -> ChallengeHypothesis:
        if not self.payload.proposed_changes:
            return "too_weak"
        kind = self.payload.proposed_changes[0].kind
        if kind == "Retirement":
            return "obsolete"
        return "too_weak"

    @property
    def proposed_action(self) -> ChallengeAction:
        if not self.payload.proposed_changes:
            return "review"
        kind = self.payload.proposed_changes[0].kind
        mapping: dict[ProposedChangeKind, ChallengeAction] = {
            "Amendment": "refine",
            "Retirement": "deprecate",
            "Addition": "broaden",
        }
        return mapping[kind]

    @property
    def failure_rate(self) -> float:
        return 0.0

    @property
    def timestamp(self) -> str:
        return self.created_at

    def to_dict(self) -> dict[str, Any]:
        return self.model_dump(mode="json")


class InvariantPerformanceRecord(BaseModel):
    """Accumulated reality feedback for one invariant K_i."""

    invariant_id: str
    predictions_made: int = 0
    continuity_preserved: int = 0
    continuity_failed: int = 0
    contexts_helpful: list[str] = Field(default_factory=list)
    contexts_harmful: list[str] = Field(default_factory=list)
    linked_grr_ids: list[str] = Field(default_factory=list)

    @property
    def failure_rate(self) -> float:
        total = self.continuity_preserved + self.continuity_failed
        if total == 0:
            return 0.0
        return self.continuity_failed / total

    def record_outcome(
        self,
        *,
        preserved: bool,
        context: str,
        grr_id: str | None = None,
    ) -> None:
        self.predictions_made += 1
        if preserved:
            self.continuity_preserved += 1
            if context and context not in self.contexts_helpful:
                self.contexts_helpful.append(context)
        else:
            self.continuity_failed += 1
            if context and context not in self.contexts_harmful:
                self.contexts_harmful.append(context)
        if grr_id and grr_id not in self.linked_grr_ids:
            self.linked_grr_ids.append(grr_id)


@dataclass
class KernelChallengeLoop:
    """
    KΩ.1 — canonical Kernel Challenge path.

    Accumulates InvariantPerformanceRecord entries and emits KCR when failure
    patterns cross thresholds or when explicit challenges are submitted.
    """

    failure_rate_threshold: float = 0.4
    min_samples: int = 3
    kernel_epoch: int = 1
    records: dict[str, InvariantPerformanceRecord] = field(default_factory=dict)
    challenges: list[KernelChallengeReceipt] = field(default_factory=list)
    ledger: KernelContinuityLedger = field(default_factory=KernelContinuityLedger)
    _challenge_seq: int = 0
    _kcr_seq: int = 0

    def _next_challenge_id(self) -> str:
        self._challenge_seq += 1
        return f"KC-{self._challenge_seq:04d}"

    def _next_kcr_id(self) -> str:
        self._kcr_seq += 1
        return f"KCR-{self._kcr_seq:04d}"

    def _kernel_version(self, epoch: int | None = None) -> str:
        ep = epoch if epoch is not None else self.kernel_epoch
        return f"K0-K15@epoch-{ep}"

    def _kernel_id(self, epoch: int | None = None) -> str:
        ep = epoch if epoch is not None else self.kernel_epoch
        return f"KERNEL-{ep}"

    def assert_admissible(
        self,
        *,
        cf_events: list[CFEvent],
        receipts_implicated: list[str],
    ) -> None:
        """KΩ.2 — evidence threshold for Kernel Challenge admissibility."""
        if not cf_events:
            raise ConstitutionalError("KΩ.2: Kernel Challenge requires at least one CF-event")
        if not receipts_implicated:
            raise ConstitutionalError(
                "KΩ.2: Kernel Challenge requires at least one implicated governance receipt"
            )

    def submit_challenge(
        self,
        *,
        invariants_challenged: list[str],
        cf_events: list[CFEvent],
        receipts_implicated: list[str],
        reason: str,
        proposed_changes: list[ProposedChange] | None = None,
        validation_steps: list[str] | None = None,
        created_by: str = "G-ENGINE",
    ) -> KernelChallengeReceipt:
        """KΩ.1 — explicit governed challenge submission."""
        self.assert_admissible(cf_events=cf_events, receipts_implicated=receipts_implicated)
        challenge_id = self._next_challenge_id()
        kcr_id = self._next_kcr_id()

        for event in cf_events:
            self.ledger.record_cf_event(
                cf_event_id=event.id,
                epoch=self.kernel_epoch,
                description=event.description,
                receipt_ids=receipts_implicated,
            )

        payload = KernelChallengeReceiptPayload(
            challenge_id=challenge_id,
            kernel_version_before=self._kernel_version(),
            status="Pending",
            reason=reason,
            cf_events=cf_events,
            receipts_implicated=receipts_implicated,
            invariants_challenged=invariants_challenged,
            proposed_changes=proposed_changes or [],
            validation_process=ValidationProcess(
                steps=validation_steps
                or ["Evidence review", "Simulation / replay", "Cross-domain check"],
                result="Insufficient",
            ),
        )
        receipt = KernelChallengeReceipt(
            id=kcr_id,
            created_by=created_by,
            epoch=self.kernel_epoch,
            payload=payload,
            links=KernelChallengeReceiptLinks(
                old_kernel_id=self._kernel_id(),
            ),
        )
        self.challenges.append(receipt)
        self.ledger.record_challenge(
            kcr_id=kcr_id,
            epoch=self.kernel_epoch,
            challenge_id=challenge_id,
        )
        return receipt

    def performance(self, invariant_id: str) -> InvariantPerformanceRecord:
        if invariant_id not in self.records:
            self.records[invariant_id] = InvariantPerformanceRecord(invariant_id=invariant_id)
        return self.records[invariant_id]

    def observe_grr(
        self,
        *,
        decisive_invariants: list[str],
        grr_id: str,
        continuity_preserved: bool,
        context: str = "",
        cf_event: CFEvent | None = None,
    ) -> list[KernelChallengeReceipt]:
        emitted: list[KernelChallengeReceipt] = []
        for invariant_id in decisive_invariants:
            record = self.performance(invariant_id)
            record.record_outcome(
                preserved=continuity_preserved,
                context=context,
                grr_id=grr_id,
            )
            challenge = self._maybe_emit_challenge(record, grr_id=grr_id, cf_event=cf_event)
            if challenge is not None:
                emitted.append(challenge)
        return emitted

    def _maybe_emit_challenge(
        self,
        record: InvariantPerformanceRecord,
        *,
        grr_id: str,
        cf_event: CFEvent | None = None,
    ) -> KernelChallengeReceipt | None:
        total = record.continuity_preserved + record.continuity_failed
        if total < self.min_samples:
            return None
        if record.failure_rate < self.failure_rate_threshold:
            return None

        existing = [
            challenge
            for challenge in self.challenges
            if record.invariant_id in challenge.payload.invariants_challenged
        ]
        if existing:
            return None

        event = cf_event or CFEvent(
            id=f"CF-AUTO-{record.invariant_id}",
            description=(
                f"Repeated continuity failure under compliant governance "
                f"for {record.invariant_id} (failure_rate={record.failure_rate:.2f})"
            ),
        )
        proposed_action: ChallengeAction = "refine"
        if record.failure_rate > 0.75:
            proposed_action = "deprecate"
        elif len(record.contexts_harmful) > len(record.contexts_helpful):
            proposed_action = "narrow"

        kind: ProposedChangeKind = "Amendment"
        if proposed_action == "deprecate":
            kind = "Retirement"
        elif proposed_action == "broaden":
            kind = "Addition"

        return self.submit_challenge(
            invariants_challenged=[record.invariant_id],
            cf_events=[event],
            receipts_implicated=list(record.linked_grr_ids or [grr_id]),
            reason=f"Continuity failure despite full compliance for {record.invariant_id}.",
            proposed_changes=[
                ProposedChange(
                    kind=kind,
                    target=record.invariant_id,
                    diff=f"Auto-proposed {proposed_action} after sustained failure.",
                )
            ],
        )

    def accept_challenge(self, kcr_id: str) -> KernelChallengeReceipt:
        """KΩ.4 — governed kernel mutation on accepted challenge."""
        receipt = next((item for item in self.challenges if item.id == kcr_id), None)
        if receipt is None:
            raise KeyError(f"Unknown KCR: {kcr_id}")

        new_epoch = self.kernel_epoch + 1
        receipt.payload.status = "Accepted"
        receipt.payload.kernel_version_after = self._kernel_version(new_epoch)
        receipt.payload.validation_process.result = "Sufficient"
        receipt.links.new_kernel_id = self._kernel_id(new_epoch)

        self.ledger.record_epoch_transition(
            old_kernel_id=receipt.links.old_kernel_id,
            new_kernel_id=receipt.links.new_kernel_id,
            epoch=new_epoch,
            kcr_id=kcr_id,
        )
        self.kernel_epoch = new_epoch
        return receipt

    def docket(self) -> list[KernelChallengeReceipt]:
        return list(self.challenges)

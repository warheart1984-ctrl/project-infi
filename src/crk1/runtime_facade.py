"""CRK-1 runtime facade — Decision → Outcome → Evidence loop with constitutional guards."""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, TYPE_CHECKING

from src.continuity.constitutional_runtime import ConstitutionalRuntime
from src.continuity.decision_ledger import DecisionRecord, DecisionStatus
from src.continuity.evidence_ledger import EvidenceRecord, EvidenceType
from src.continuity.identity_object import IdentityObject
from src.continuity.outcome_ledger import OutcomeRecord

from src.crk1.errors import ConstitutionalError
from src.crk1 import runtime_assertions as assertions
from src.crk1.semantic_layer import (
    CRK1Interpretation,
    CRK1Prediction,
    CRK1PredictionOutcome,
    CRK1Reconstruction,
    SemanticLayer,
)

if TYPE_CHECKING:
    from src.crk1.consequence_lattice import ConsequenceExposure


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class CRK1Decision:
    id: str
    identity_id: str
    evidence_refs: list[str] = field(default_factory=list)
    payload: dict | None = None
    reviews: list[dict] = field(default_factory=list)

    @property
    def input_evidence_ids(self) -> list[str]:
        return self.evidence_refs


@dataclass
class CRK1Outcome:
    id: str
    decision_id: str
    replayable: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "_crk1_frozen", True)

    def __setattr__(self, name: str, value: object) -> None:
        if (
            name == "replayable"
            and value is False
            and getattr(self, "_crk1_frozen", False)
        ):
            raise ConstitutionalError("K1: outcome replayability is immutable")
        object.__setattr__(self, name, value)


@dataclass
class CRK1Evidence:
    id: str
    outcome_id: str
    source_identity_id: str
    admissible_for_decision: bool = True

    def __post_init__(self) -> None:
        object.__setattr__(self, "_crk1_frozen", True)

    def __setattr__(self, name: str, value: object) -> None:
        if (
            name == "admissible_for_decision"
            and value is False
            and getattr(self, "_crk1_frozen", False)
        ):
            raise ConstitutionalError("K1: evidence admissibility is immutable")
        object.__setattr__(self, name, value)


class CRK1Runtime:
    """Wraps ConstitutionalRuntime with CRK-1 consequence-transmission invariants."""

    def __init__(self, kernel: ConstitutionalRuntime) -> None:
        self._kernel = kernel
        self._identities: dict[str, IdentityObject] = {
            kernel.ledgers.identity.id: kernel.ledgers.identity,
        }
        self._identity_parents: dict[str, str | None] = {
            kernel.ledgers.identity.id: None,
        }
        self._outcome_replayable: dict[str, bool] = {}
        self._replay_evidence: dict[str, CRK1Evidence] = {}
        self._evidence_by_id: dict[str, CRK1Evidence] = {}
        self._outcome_by_decision: dict[str, str] = {}
        self._decisions: dict[str, CRK1Decision] = {}
        self._amendments: list[dict] = []
        self._last_consequence_exposure: ConsequenceExposure | None = None
        self._disable_outcome_creation: bool = False
        self._semantic = SemanticLayer(self)
        self._semantic_monitor: Any = None

    def attach_semantic_monitor(self, monitor: Any) -> None:
        """Link SE monitor for interpretive history replay (K11)."""
        self._semantic_monitor = monitor

    @property
    def kernel(self) -> ConstitutionalRuntime:
        return self._kernel

    def create_identity(
        self,
        name: str,
        *,
        parent_identity_id: str | None = None,
    ) -> IdentityObject:
        identity_id = f"ID-{name}-{uuid.uuid4().hex[:8]}"
        parent = parent_identity_id
        if parent is not None and parent not in self._identities:
            raise ConstitutionalError(f"Unknown parent identity: {parent}")
        identity = IdentityObject(
            id=identity_id,
            mission=f"Derived identity {name}",
            values=self._kernel.ledgers.identity.values,
            invariants=self._kernel.ledgers.identity.invariants,
            authority_model=dict(self._kernel.ledgers.identity.authority_model),
        )
        self._identities[identity_id] = identity
        self._identity_parents[identity_id] = parent
        return identity

    def create_decision(
        self,
        *,
        identity: str,
        evidence: list[str],
        payload: dict | None = None,
    ) -> CRK1Decision:
        if identity not in self._identities:
            raise ConstitutionalError(f"Unknown identity: {identity}")
        if not evidence:
            raise ConstitutionalError("K2: decision requires evidence")
        decision_id = f"DEC-{uuid.uuid4().hex[:10]}"
        decision = CRK1Decision(
            id=decision_id,
            identity_id=identity,
            evidence_refs=list(evidence),
            payload=payload,
        )
        self._decisions[decision_id] = decision
        return decision

    def propose_decision(
        self,
        *,
        identity: str,
        evidence: list[str],
        payload: dict | None = None,
    ) -> CRK1Decision:
        """ProposeDecision(Identity, Evidence) → Decision (K0/K2)."""
        decision = self.create_decision(identity=identity, evidence=evidence, payload=payload)
        return self.save_decision(decision)

    def load_decision(self, decision_id: str) -> CRK1Decision:
        decision = self._decisions.get(decision_id)
        if decision is None:
            record = self._kernel.decisions.get(decision_id)
            if record is None:
                raise ConstitutionalError(f"Unknown decision: {decision_id}")
            decision = CRK1Decision(
                id=record.id,
                identity_id=record.identity_id,
                evidence_refs=list(record.evidence_refs),
            )
            self._decisions[decision_id] = decision
        return decision

    def attach_review(self, decision_id: str, review: dict) -> None:
        decision = self.load_decision(decision_id)
        decision.reviews.append(dict(review))

    def execute_decision(self, decision_id: str) -> CRK1Outcome:
        if self._disable_outcome_creation:
            raise ConstitutionalError("K0: execution must produce outcome")

        decision = self.load_decision(decision_id)
        record = self._kernel.decisions.get(decision_id)
        if record is None:
            self.save_decision(decision)
        elif record.status == DecisionStatus.PROPOSED:
            self._kernel.approve_decision(decision_id)
        outcome_record = self._kernel.execute_decision(
            decision_id,
            expected={"continuity": True},
            observed={"continuity": True},
            lessons=["crk1-governance-execute"],
        )
        self._outcome_replayable[outcome_record.id] = True
        self._outcome_by_decision[decision_id] = outcome_record.id
        outcome = CRK1Outcome(id=outcome_record.id, decision_id=decision_id, replayable=True)
        assertions.assert_execution_produces_outcome(outcome)
        return outcome

    def get_lineage(self, identity_id: str) -> list[str]:
        if identity_id not in self._identities:
            raise ConstitutionalError(f"Unknown identity: {identity_id}")
        chain = [identity_id]
        parent = self._identity_parents.get(identity_id)
        while parent:
            chain.append(parent)
            parent = self._identity_parents.get(parent)
        return chain

    def get_all_identities(self) -> list[IdentityObject]:
        return list(self._identities.values())

    def get_all_outcomes(self) -> list[CRK1Outcome]:
        outcomes: list[CRK1Outcome] = []
        for record in self._kernel.outcomes.list_outcomes():
            replayable = self._outcome_replayable.get(record.id, True)
            outcomes.append(
                CRK1Outcome(
                    id=record.id,
                    decision_id=record.decision_id,
                    replayable=replayable,
                )
            )
        return outcomes

    def get_all_evidence(self) -> list[CRK1Evidence]:
        items = list(self._replay_evidence.values())
        store = self._kernel.ledgers.evidence_store
        if store is not None:
            for entry in store.ledger_entries():
                if any(item.id == entry.evidence_id for item in items):
                    continue
                items.append(
                    CRK1Evidence(
                        id=entry.evidence_id,
                        outcome_id="",
                        source_identity_id=self._kernel.ledgers.identity.id,
                    )
                )
        return items

    def load_evidence(self, evidence_id: str) -> CRK1Evidence:
        evidence = self._evidence_by_id.get(evidence_id)
        if evidence is None:
            raise ConstitutionalError(f"Unknown evidence: {evidence_id}")
        return evidence

    def apply_amendment(self, changes: dict) -> None:
        self._amendments.append(dict(changes))

    def save_decision(self, decision: CRK1Decision) -> CRK1Decision:
        assertions.assert_decision_has_identity(decision)
        assertions.assert_decision_has_evidence(decision)
        if decision.identity_id not in self._identities:
            raise ConstitutionalError(f"K2: unknown identity {decision.identity_id}")
        draft = DecisionRecord(
            id=decision.id,
            actor_id="ROLE-STEWARD-01",
            identity_id=decision.identity_id,
            intent="CRK-1 saved decision",
            type="operational",
            evidence_refs=list(decision.evidence_refs),
            risk_profile={"level": "low"},
            governance_basis={"process": "crk1"},
            resource_plan={},
            status=DecisionStatus.PROPOSED,
            epoch=self._kernel.ledgers.epoch,
            created_at=_now_iso(),
            updated_at=_now_iso(),
        )
        self._kernel.propose_decision(draft)
        return decision

    def propose_and_execute(
        self,
        *,
        identity: str,
        evidence: list[str],
    ) -> CRK1Decision:
        if identity not in self._identities:
            raise ConstitutionalError(f"Unknown identity: {identity}")
        if not evidence:
            raise ConstitutionalError("K2: decision requires evidence")
        decision = self.create_decision(identity=identity, evidence=evidence)
        draft = DecisionRecord(
            id=decision.id,
            actor_id="ROLE-STEWARD-01",
            identity_id=identity,
            intent="CRK-1 propose-and-execute",
            type="operational",
            evidence_refs=list(evidence),
            risk_profile={"level": "low"},
            governance_basis={"process": "crk1"},
            resource_plan={},
            status=DecisionStatus.PROPOSED,
            epoch=self._kernel.ledgers.epoch,
            created_at=_now_iso(),
            updated_at=_now_iso(),
        )
        self._kernel.propose_decision(draft)
        self._kernel.approve_decision(decision.id)
        outcome = self._kernel.execute_decision(
            decision.id,
            expected={"continuity": True},
            observed={"continuity": True},
            lessons=["crk1-execute"],
        )
        self._outcome_replayable[outcome.id] = True
        self._outcome_by_decision[decision.id] = outcome.id
        return decision

    def get_outcomes(self, decision_id: str) -> list[CRK1Outcome]:
        outcome_id = self._outcome_by_decision.get(decision_id)
        if outcome_id is None:
            record = self._kernel.outcomes.get_by_decision(decision_id)
            if record is None:
                return []
            outcome_id = record.id
            self._outcome_by_decision[decision_id] = outcome_id
        replayable = self._outcome_replayable.get(outcome_id, True)
        return [CRK1Outcome(id=outcome_id, decision_id=decision_id, replayable=replayable)]

    def delete_outcome(self, outcome_id: str) -> None:
        assertions.assert_no_outcome_deletion()

    def replay_outcome(self, outcome_id: str) -> CRK1Evidence:
        replayable = self._outcome_replayable.get(outcome_id, True)
        assertions.assert_outcome_replayable(
            CRK1Outcome(id=outcome_id, decision_id="", replayable=replayable)
        )
        record: OutcomeRecord | None = self._kernel.outcomes.get(outcome_id)
        if record is None:
            raise ConstitutionalError(f"Unknown outcome: {outcome_id}")
        decision = self._kernel.decisions.get(record.decision_id)
        identity_id = decision.identity_id if decision else self._kernel.ledgers.identity.id
        evidence_id = f"EV-REPLAY-{outcome_id}"
        store = self._kernel.ledgers.evidence_store
        if store is not None:
            store.upsert_evidence_record(
                EvidenceRecord(
                    evidence_id=evidence_id,
                    evidence_hash=f"{evidence_id}-hash",
                    evidence_type=EvidenceType.DERIVATION,
                    source_lineage=f"outcome:{outcome_id}",
                    source_epoch=record.epoch,
                    validation_method="crk1-replay",
                    confidence=0.99,
                    canonical_hash=f"{evidence_id}-hash",
                )
            )
        evidence = CRK1Evidence(
            id=evidence_id,
            outcome_id=outcome_id,
            source_identity_id=identity_id,
        )
        self._replay_evidence[outcome_id] = evidence
        self._evidence_by_id[evidence_id] = evidence
        assertions.assert_replay_produces_evidence(evidence)
        return evidence

    def mark_evidence_non_admissible(self, evidence_id: str) -> None:
        assertions.assert_no_evidence_quarantine()

    def mark_evidence_irrelevant_for_identity(self, evidence_id: str, identity_id: str) -> None:
        assertions.assert_no_evidence_irrelevance_mark()

    def get_admissible_evidence(self, identity_id: str) -> list[CRK1Evidence]:
        if identity_id not in self._identities:
            raise ConstitutionalError(f"Unknown identity: {identity_id}")

        lineage = set(self.get_lineage(identity_id))
        visible: dict[str, CRK1Evidence] = {}

        for evidence in self._evidence_by_id.values():
            if evidence.source_identity_id in lineage:
                visible[evidence.id] = evidence

        store = self._kernel.ledgers.evidence_store
        if store is not None:
            for entry in store.ledger_entries():
                if entry.evidence_id in visible:
                    continue
                visible[entry.evidence_id] = CRK1Evidence(
                    id=entry.evidence_id,
                    outcome_id="",
                    source_identity_id=self._kernel.ledgers.identity.id,
                )

        return sorted(visible.values(), key=lambda item: item.id)

    # ------------------------------------------------------------
    # Semantic layer (K7–K12) — delegated to SemanticLayer
    # ------------------------------------------------------------

    def create_evidence(
        self,
        *,
        source_identity_id: str | None = None,
        outcome_id: str = "",
    ) -> CRK1Evidence:
        return self._semantic.create_evidence(
            source_identity_id=source_identity_id,
            outcome_id=outcome_id,
        )

    def create_interpretation(self, **kwargs: Any) -> CRK1Interpretation:
        return self._semantic.create_interpretation(**kwargs)

    def load_interpretation(self, frame_id: str) -> CRK1Interpretation:
        return self._semantic.load_interpretation(frame_id)

    def get_all_interpretations(self) -> list[CRK1Interpretation]:
        return self._semantic.get_all_interpretations()

    def get_dominant_interpretation(self) -> CRK1Interpretation:
        return self._semantic.get_dominant_interpretation()

    def get_interpretations(self, evidence_id: str) -> list[CRK1Interpretation]:
        return self._semantic.get_interpretations(evidence_id)

    def interpret(self, frame_id: str, evidence_id: str) -> str:
        return self._semantic.interpret(frame_id, evidence_id)

    def reconstruct(self, frame_id: str, evidence_id: str) -> str:
        return self._semantic.reconstruct(frame_id, evidence_id)

    def generate_prediction(self, frame_id: str, evidence_id: str) -> CRK1Prediction:
        return self._semantic.generate_prediction(frame_id, evidence_id)

    def realize_outcome_from_prediction(self, prediction_id: str) -> CRK1Outcome:
        return self._semantic.realize_outcome_from_prediction(prediction_id)

    def update_interpretation(self, frame_id: str, evidence_id: str) -> None:
        return self._semantic.update_interpretation(frame_id, evidence_id)

    def apply_semantic_drift(self) -> None:
        return self._semantic.apply_semantic_drift()

    def get_interpretive_history(self) -> list[dict[str, float]]:
        if self._semantic_monitor is not None:
            return list(self._semantic_monitor.history)
        return self._semantic.get_interpretive_history()

    def get_all_predictions(self) -> list[CRK1Prediction]:
        return self._semantic.get_all_predictions()

    def list_interpreted_evidence(self) -> list[CRK1Evidence]:
        return self._semantic.list_interpreted_evidence()

    def get_predictions_for_evidence(self, evidence_id: str) -> list[CRK1Prediction]:
        return self._semantic.get_predictions_for_evidence(evidence_id)

    def get_outcome_for_prediction(self, prediction_id: str) -> CRK1PredictionOutcome:
        return self._semantic.get_outcome_for_prediction(prediction_id)

    def get_reconstructions_for_evidence(self, evidence_id: str) -> list[CRK1Reconstruction]:
        return self._semantic.get_reconstructions_for_evidence(evidence_id)

"""CRK-T5 reference integrity evaluator — identity alignment metrics."""

from __future__ import annotations

from src.continuity.identity_object import DEFAULT_IDENTITY, IdentityObject
from src.continuity.decision_ledger import DecisionLedgerStore, DecisionRecord, bootstrap_decision_ledger
from src.continuity.outcome_ledger import OutcomeLedgerStore, OutcomeRecord, bootstrap_outcome_ledger
from src.kernel.identity_history import IdentityHistory, IdentityIntegrityEvaluator, _clamp, _tokenize


class DecisionIdentityEvaluator:
    def __init__(
        self,
        decisions: DecisionLedgerStore,
        *,
        identity: IdentityObject = DEFAULT_IDENTITY,
    ) -> None:
        self.decisions = decisions
        self.identity = identity

    @classmethod
    def current(cls) -> DecisionIdentityEvaluator:
        store = DecisionLedgerStore.in_memory()
        bootstrap_decision_ledger(store, epoch=17)
        return cls(store)

    def _alignment_score(self, decision: DecisionRecord) -> float:
        intent_tokens = _tokenize(decision.intent)
        mission_tokens = _tokenize(self.identity.mission)
        value_tokens: set[str] = set()
        for value in self.identity.values:
            value_tokens |= _tokenize(value)

        mission_overlap = len(intent_tokens & mission_tokens) / max(len(mission_tokens), 1)
        value_overlap = len(intent_tokens & value_tokens) / max(len(value_tokens), 1)
        alignment = max(mission_overlap, value_overlap)

        for invariant in self.identity.invariants:
            token = invariant.split()[0].lower() if invariant else ""
            if token and token in decision.intent.lower() and "without" in invariant.lower():
                alignment = 0.0
                break

        roles = self.identity.authority_model.get(decision.actor_id) or {}
        allowed = set(roles.get("approve") or [])
        if decision.type not in allowed and "*" not in allowed:
            alignment *= 0.5

        return _clamp(alignment)

    def identity_divergence_score(self) -> float:
        rows = self.decisions.list_decisions()
        if not rows:
            return 0.0
        divergences = [1.0 - self._alignment_score(row) for row in rows]
        return _clamp(sum(divergences) / len(divergences))


class OutcomeIdentityEvaluator:
    def __init__(
        self,
        outcomes: OutcomeLedgerStore,
        decisions: DecisionLedgerStore,
        *,
        identity: IdentityObject = DEFAULT_IDENTITY,
    ) -> None:
        self.outcomes = outcomes
        self.decisions = decisions
        self.identity = identity

    @classmethod
    def current(cls) -> OutcomeIdentityEvaluator:
        decisions = DecisionLedgerStore.in_memory()
        outcomes = OutcomeLedgerStore()
        bootstrap_decision_ledger(decisions, epoch=17)
        bootstrap_outcome_ledger(outcomes, epoch=17)
        return cls(outcomes, decisions)

    def _outcome_divergence(self, outcome: OutcomeRecord) -> float:
        variance = outcome.variance or {}
        classification = str(variance.get("classification") or "").lower()
        severity = {
            "acceptable": 0.05,
            "minor": 0.2,
            "moderate": 0.45,
            "severe": 0.75,
            "critical": 0.95,
        }.get(classification, 0.3)

        text = " ".join(
            [
                str(outcome.expected.get("description") or ""),
                str(outcome.observed.get("description") or ""),
                " ".join(outcome.lessons),
            ]
        ).lower()
        harm_markers = ("harm", "violation", "breach", "erosion", "unlawful")
        if any(marker in text for marker in harm_markers):
            severity = max(severity, 0.6)

        return _clamp(severity)

    def identity_divergence_score(self) -> float:
        rows = self.outcomes.list_outcomes()
        if not rows:
            return 0.0
        divergences = [self._outcome_divergence(row) for row in rows]
        return _clamp(sum(divergences) / len(divergences))


class ReferenceEvaluator:
    """Composite CRK-T5 reference integrity metrics."""

    def __init__(
        self,
        identity_history: IdentityHistory | None = None,
        decisions: DecisionLedgerStore | None = None,
        outcomes: OutcomeLedgerStore | None = None,
    ) -> None:
        decision_store = decisions or DecisionLedgerStore()
        if decisions is None:
            bootstrap_decision_ledger(decision_store, epoch=17)
        outcome_store = outcomes or OutcomeLedgerStore()
        if outcomes is None:
            bootstrap_outcome_ledger(outcome_store, epoch=17)
        history = identity_history or IdentityHistory.current()
        self.identity = IdentityIntegrityEvaluator(history, decisions=decision_store)
        active = history.active_identity
        self.decisions = DecisionIdentityEvaluator(decision_store, identity=active)
        self.outcomes = OutcomeIdentityEvaluator(outcome_store, decision_store, identity=active)

    def compute_metrics(self) -> dict[str, float]:
        metrics = {
            "mission": self.identity.mission_drift_score(),
            "values": self.identity.value_drift_score(),
            "invariants": self.identity.invariant_erosion_score(),
            "authority": self.identity.authority_drift_score(),
            "decision": self.decisions.identity_divergence_score(),
            "outcome": self.outcomes.identity_divergence_score(),
            "epoch": self.identity.cross_epoch_inconsistency_score(),
        }
        metrics["reference_integrity"] = _clamp(
            1.0
            - (
                0.2 * metrics["mission"]
                + 0.15 * metrics["values"]
                + 0.2 * metrics["invariants"]
                + 0.1 * metrics["authority"]
                + 0.15 * metrics["decision"]
                + 0.1 * metrics["outcome"]
                + 0.1 * metrics["epoch"]
            )
        )
        return {key: round(value, 6) for key, value in metrics.items()}

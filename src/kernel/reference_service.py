"""Shared CRK-T5 reference evaluator context for API and cockpit."""

from __future__ import annotations

from src.continuity.decision_ledger import DecisionLedgerStore, bootstrap_decision_ledger
from src.continuity.outcome_ledger import OutcomeLedgerStore, bootstrap_outcome_ledger
from src.kernel.identity_history import IdentityHistory
from src.kernel.reference_evaluator import ReferenceEvaluator

_DECISIONS: DecisionLedgerStore | None = None
_OUTCOMES: OutcomeLedgerStore | None = None


def get_reference_stores() -> tuple[DecisionLedgerStore, OutcomeLedgerStore]:
    global _DECISIONS, _OUTCOMES
    if _DECISIONS is None:
        _DECISIONS = DecisionLedgerStore()
        _OUTCOMES = OutcomeLedgerStore()
        bootstrap_decision_ledger(_DECISIONS, epoch=17)
        bootstrap_outcome_ledger(_OUTCOMES, epoch=17)
    return _DECISIONS, _OUTCOMES


def get_reference_evaluator() -> ReferenceEvaluator:
    decisions, outcomes = get_reference_stores()
    return ReferenceEvaluator(
        identity_history=IdentityHistory.current(),
        decisions=decisions,
        outcomes=outcomes,
    )


def reset_reference_service() -> None:
    global _DECISIONS, _OUTCOMES
    _DECISIONS = None
    _OUTCOMES = None

"""CRK-T5 identity history and drift metrics over IdentityObject snapshots."""

from __future__ import annotations

import json
import re
from dataclasses import dataclass
from typing import TYPE_CHECKING

from src.continuity.identity_object import DEFAULT_IDENTITY, IdentityObject

if TYPE_CHECKING:
    from src.continuity.decision_ledger import DecisionLedgerStore


def _clamp(value: float, low: float = 0.0, high: float = 1.0) -> float:
    return max(low, min(high, value))


def _tokenize(text: str) -> set[str]:
    return {token for token in re.findall(r"[a-z0-9]+", text.lower()) if len(token) > 2}


@dataclass(frozen=True, slots=True)
class IdentitySnapshot:
    epoch: int
    identity: IdentityObject


class IdentityHistory:
    """Replayable identity timeline — baseline + epoch snapshots."""

    def __init__(self, snapshots: list[IdentitySnapshot]) -> None:
        if not snapshots:
            raise ValueError("IdentityHistory requires at least one snapshot")
        self.snapshots = sorted(snapshots, key=lambda item: item.epoch)

    @property
    def baseline(self) -> IdentityObject:
        return self.snapshots[0].identity

    @property
    def active_identity(self) -> IdentityObject:
        return self.snapshots[-1].identity

    @classmethod
    def current(cls) -> IdentityHistory:
        from src.constitutional_cockpit_routes import _ensure_ledgers
        from src.kernel.identity_history_ledger import shared_identity_ledger

        law_store, _, _, _, _, _ = _ensure_ledgers()
        epoch = int(law_store.get_current_epoch())
        ledger = shared_identity_ledger()
        snapshots: list[IdentitySnapshot] = [IdentitySnapshot(epoch=0, identity=DEFAULT_IDENTITY)]
        for row in ledger.list():
            snapshots.append(
                IdentitySnapshot(
                    epoch=row.epoch,
                    identity=IdentityObject.from_dict(row.identity),
                )
            )
        if len(snapshots) == 1:
            return cls.from_identity(DEFAULT_IDENTITY, epoch=epoch)
        return cls(snapshots)

    @classmethod
    def from_identity(
        cls,
        identity: IdentityObject,
        *,
        epoch: int = 0,
        prior_snapshots: list[IdentitySnapshot] | None = None,
    ) -> IdentityHistory:
        rows = list(prior_snapshots or [IdentitySnapshot(epoch=0, identity=identity)])
        if not rows or rows[-1].identity.to_dict() != identity.to_dict():
            rows.append(IdentitySnapshot(epoch=epoch, identity=identity))
        return cls(rows)

    def mission_drift_score(self) -> float:
        baseline_tokens = _tokenize(self.baseline.mission)
        current_tokens = _tokenize(self.active_identity.mission)
        if not baseline_tokens and not current_tokens:
            return 0.0
        union = baseline_tokens | current_tokens
        if not union:
            return 0.0
        overlap = len(baseline_tokens & current_tokens)
        return _clamp(1.0 - overlap / len(union))

    def value_drift_score(self) -> float:
        baseline = set(self.baseline.values)
        current = set(self.active_identity.values)
        union = baseline | current
        if not union:
            return 0.0
        return _clamp(len(baseline ^ current) / len(union))

    def invariant_erosion_score(self, decisions: DecisionLedgerStore | None = None) -> float:
        baseline = set(self.baseline.invariants)
        current = set(self.active_identity.invariants)
        removed = baseline - current
        snapshot_score = _clamp(len(removed) / len(baseline)) if baseline else 0.0
        if decisions is None:
            return snapshot_score
        rows = decisions.list_decisions()
        if not rows:
            return snapshot_score
        exceptions = 0
        for row in rows:
            basis = row.governance_basis or {}
            if basis.get("invariant_override") or basis.get("invariant_exception"):
                exceptions += 1
            elif "invariant-exception" in row.tags:
                exceptions += 1
        return _clamp(max(snapshot_score, exceptions / len(rows)))

    def authority_drift_score(self) -> float:
        baseline_json = json.dumps(self.baseline.authority_model, sort_keys=True)
        current_json = json.dumps(self.active_identity.authority_model, sort_keys=True)
        if baseline_json == current_json:
            return 0.0
        baseline_keys = set(self.baseline.authority_model)
        current_keys = set(self.active_identity.authority_model)
        key_drift = len(baseline_keys ^ current_keys) / max(len(baseline_keys | current_keys), 1)
        approve_drift = 0.0
        for actor in baseline_keys & current_keys:
            baseline_approve = set(self.baseline.authority_model[actor].get("approve") or [])
            current_approve = set(self.active_identity.authority_model[actor].get("approve") or [])
            union = baseline_approve | current_approve
            if union:
                approve_drift = max(approve_drift, len(baseline_approve ^ current_approve) / len(union))
        return _clamp(0.5 * key_drift + 0.5 * approve_drift)

    def cross_epoch_inconsistency_score(self) -> float:
        if len(self.snapshots) < 2:
            return 0.0
        mission_sets = [frozenset(_tokenize(item.identity.mission)) for item in self.snapshots]
        values = {tuple(item.identity.values) for item in self.snapshots}
        mission_conflict = 0.0
        if len(set(mission_sets)) > 1:
            overlap_all = set.intersection(*mission_sets) if mission_sets else set()
            union_all = set.union(*mission_sets) if mission_sets else set()
            mission_conflict = 1.0 - (len(overlap_all) / len(union_all) if union_all else 1.0)
        value_conflict = 0.0 if len(values) == 1 else 0.5
        return _clamp(max(mission_conflict, value_conflict))


class IdentityIntegrityEvaluator:
    """CRK-T5 facade over identity history with decision-level invariant erosion."""

    def __init__(
        self,
        history: IdentityHistory,
        *,
        decisions: DecisionLedgerStore | None = None,
    ) -> None:
        self.history = history
        self.decisions = decisions

    def mission_drift_score(self) -> float:
        return self.history.mission_drift_score()

    def value_drift_score(self) -> float:
        return self.history.value_drift_score()

    def invariant_erosion_score(self) -> float:
        return self.history.invariant_erosion_score(self.decisions)

    def authority_drift_score(self) -> float:
        return self.history.authority_drift_score()

    def cross_epoch_inconsistency_score(self) -> float:
        return self.history.cross_epoch_inconsistency_score()

"""
CRK-1 Minimal Runtime — smallest working invariant-enforcing skeleton.

Conceptual reference implementation for K0–K2 (transmission) and K7–K12 (semantic).
For production continuity, use `CRK1Runtime` in `runtime_facade.py`.
"""

from __future__ import annotations

import uuid
from dataclasses import dataclass, field

from src.crk1.errors import ConstitutionalError


@dataclass
class Identity:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))


@dataclass
class Decision:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    identity_id: str = ""
    evidence_ids: list[str] = field(default_factory=list)


@dataclass
class Outcome:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    decision_id: str = ""
    status: str = "realized"
    replayable: bool = True


@dataclass
class Evidence:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    outcome_id: str = ""
    admissible: bool = True


@dataclass
class Interpretation:
    id: str = field(default_factory=lambda: str(uuid.uuid4()))
    name: str = ""
    prediction_binding: bool = True
    weight: float = 0.5
    adversarial: bool = False


class CRK1MinimalRuntime:
    """
    Minimal, invariant-enforcing CRK-1 runtime (conceptual skeleton).

    Enforces the Decision→Outcome→Evidence loop, plural/adversarial interpretations,
    and a non-zero SE(S) metric.
    """

    def __init__(self) -> None:
        self.identities: dict[str, Identity] = {}
        self.decisions: dict[str, Decision] = {}
        self.outcomes: dict[str, Outcome] = {}
        self.evidence: dict[str, Evidence] = {}
        self.interpretations: list[Interpretation] = []
        self._bootstrap_semantic_defaults()

    def _bootstrap_semantic_defaults(self) -> None:
        """Seed plural + adversarial frames (K7, K10) so the runtime is usable."""
        self.interpretations = [
            Interpretation(
                name="dominant-frame",
                prediction_binding=True,
                weight=0.55,
                adversarial=False,
            ),
            Interpretation(
                name="adversarial-frame",
                prediction_binding=True,
                weight=0.45,
                adversarial=True,
            ),
        ]

    # K0–K2: Transmission
    def execute_decision(self, decision: Decision) -> Outcome:
        if not decision.identity_id:
            raise ConstitutionalError("K2 violation: decision requires identity")
        if not decision.evidence_ids:
            raise ConstitutionalError("K2 violation: decision requires input evidence")
        self.decisions[decision.id] = decision
        outcome = Outcome(decision_id=decision.id)
        self.outcomes[outcome.id] = outcome
        evidence = Evidence(outcome_id=outcome.id, admissible=True)
        self.evidence[evidence.id] = evidence
        decision.evidence_ids.append(evidence.id)
        return outcome

    def replay_outcome(self, outcome: Outcome) -> Evidence:
        if not outcome.replayable:
            raise ConstitutionalError("K1 violation: outcome is not replayable")
        stored = self.outcomes.get(outcome.id)
        if stored is None:
            raise ConstitutionalError(f"Unknown outcome: {outcome.id}")
        replay = Evidence(outcome_id=outcome.id, admissible=True)
        self.evidence[replay.id] = replay
        return replay

    # K7–K10: basic semantic layer
    def register_interpretation(self, frame: Interpretation) -> None:
        if frame.prediction_binding is not True:
            raise ConstitutionalError("K8 violation: interpretation must be prediction-bound")
        self.interpretations.append(frame)
        if len(self.interpretations) < 2:
            raise ConstitutionalError("K7 violation: interpretive pluralism requires >= 2 frames")
        if not any(item.adversarial for item in self.interpretations):
            raise ConstitutionalError("K10 violation: adversarial frame required")
        dominant = max(self.interpretations, key=lambda item: item.weight)
        if dominant.weight >= 1.0:
            raise ConstitutionalError("K9 violation: interpretive monoculture")

    def measure_SE(self) -> float:
        """Minimal SE: plural substrate + adversarial fraction (K12)."""
        if not self.interpretations:
            return 0.0
        plural = 1.0 if len(self.interpretations) >= 2 else 0.0
        adversarial = len([frame for frame in self.interpretations if frame.adversarial]) / len(
            self.interpretations
        )
        return plural + adversarial

    def check_semantic_invariants(self) -> float:
        exposure = self.measure_SE()
        if exposure <= 0:
            raise ConstitutionalError("K12 violation: semantic exposure must be > 0")
        return exposure

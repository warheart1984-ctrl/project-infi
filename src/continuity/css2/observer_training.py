"""Continuity observer training protocol — five phases for recalibration literacy."""

from __future__ import annotations

from datetime import UTC, datetime
from typing import Literal

from pydantic import BaseModel, Field

from src.continuity.css2.governance import RecalibrationGovernanceEngine
from src.continuity.css2.models import (
    RecalibrationProposalContext,
    RecalibrationTrigger,
    ThresholdChange,
)
from src.continuity.css2.spec import OBSERVER_TRAINING_PHASES


TrainingPhaseId = Literal[
    "phase_1_concept_free",
    "phase_2_vocabulary",
    "phase_3_f5_independence",
    "phase_4_meta_observation",
    "phase_5_governance_drills",
]


class TrainingCase(BaseModel):
    case_id: str
    raw_narrative: str
    domain_language_narrative: str | None = None
    expected_failure_markers: list[str] = Field(default_factory=list)
    expected_recalibration_point: int | None = None


class PhaseScore(BaseModel):
    phase: TrainingPhaseId
    detection_rate: float = 0.0
    explanation_quality: float = 0.0
    vocabulary_independent: bool | None = None
    notes: list[str] = Field(default_factory=list)


class ObserverTrainingSession(BaseModel):
    session_id: str
    trainee_id: str
    started_at: datetime = Field(default_factory=lambda: datetime.now(UTC).replace(microsecond=0))
    phase_scores: list[PhaseScore] = Field(default_factory=list)
    completed: bool = False


class ObserverTrainingProtocol:
    """
    Train observers to notice when their own interpretation needs recalibration.

    Phase 1 — concept-free observation
    Phase 2 — vocabulary introduction
    Phase 3 — F5 vocabulary-independence test
    Phase 4 — meta-observation drills
    Phase 5 — recalibration governance exercises (Five-Team war room)
    """

    def __init__(self) -> None:
        self._cases: list[TrainingCase] = []
        self._sessions: dict[str, ObserverTrainingSession] = {}

    def register_case(self, case: TrainingCase) -> None:
        self._cases.append(case)

    def start_session(self, session_id: str, trainee_id: str) -> ObserverTrainingSession:
        session = ObserverTrainingSession(session_id=session_id, trainee_id=trainee_id)
        self._sessions[session_id] = session
        return session

    def score_phase_1(
        self,
        session_id: str,
        *,
        markers_found: list[str],
        thresholds_marked_off: int,
    ) -> PhaseScore:
        """Concept-free observation — no JPSS/CSS vocabulary."""
        expected = sum(len(case.expected_failure_markers) for case in self._cases) or 1
        detection_rate = min(1.0, len(markers_found) / expected)
        score = PhaseScore(
            phase="phase_1_concept_free",
            detection_rate=detection_rate,
            explanation_quality=0.5 if thresholds_marked_off > 0 else 0.2,
            notes=["Raw cases only — trainee uses own words for drift and threshold mismatch."],
        )
        self._append_score(session_id, score)
        return score

    def score_phase_2(
        self,
        session_id: str,
        *,
        detection_rate: float,
        explanation_quality: float,
    ) -> PhaseScore:
        score = PhaseScore(
            phase="phase_2_vocabulary",
            detection_rate=detection_rate,
            explanation_quality=explanation_quality,
            notes=["Calibration, recalibration, drift, invariants, stewardship vocabulary introduced."],
        )
        self._append_score(session_id, score)
        return score

    def score_phase_3_f5(
        self,
        session_id: str,
        *,
        phase_2_detection: float,
        domain_detection: float,
    ) -> PhaseScore:
        """F5 vocabulary-independence — performance should not collapse without jargon."""
        collapse = domain_detection < phase_2_detection * 0.6
        score = PhaseScore(
            phase="phase_3_f5_independence",
            detection_rate=domain_detection,
            explanation_quality=domain_detection,
            vocabulary_independent=not collapse,
            notes=[
                "Domain language only — JPSS/CSS terms stripped.",
                "Collapse detected." if collapse else "Performance stable without jargon.",
            ],
        )
        self._append_score(session_id, score)
        return score

    def score_phase_4_meta(
        self,
        session_id: str,
        *,
        revision_point_accuracy: float,
        signal_identification: float,
    ) -> PhaseScore:
        score = PhaseScore(
            phase="phase_4_meta_observation",
            detection_rate=revision_point_accuracy,
            explanation_quality=signal_identification,
            notes=["When should interpretation have been revised? What signal broke the model?"],
        )
        self._append_score(session_id, score)
        return score

    def run_phase_5_governance_drill(
        self,
        session_id: str,
        *,
        trainee_id: str,
        proposed_changes: list[ThresholdChange],
        triggers: list[RecalibrationTrigger],
        governance: RecalibrationGovernanceEngine | None = None,
    ) -> PhaseScore:
        """Trainees propose recalibrations; Five-Team adversarial review applies."""
        engine = governance or RecalibrationGovernanceEngine()
        ctx = RecalibrationProposalContext(
            proposed_changes=proposed_changes,
            triggers=triggers,
            proposer_id=trainee_id,
        )
        event = engine.evaluate_proposal(ctx)
        withdrew = event.decision == "rejected"
        defended = event.decision in {"approved", "escalated"}
        revised = event.decision == "deferred"
        quality = 0.9 if defended else (0.6 if revised else 0.3)
        score = PhaseScore(
            phase="phase_5_governance_drills",
            detection_rate=1.0 if event.adversarial_review_passed or withdrew else 0.5,
            explanation_quality=quality,
            notes=[
                f"Trainee outcome: {event.decision}.",
                "Red/Blue/Black/White/Gold war-room applied.",
                "Withdraw" if withdrew else ("Revise" if revised else "Defend"),
            ],
        )
        self._append_score(session_id, score)
        return score

    def complete_session(self, session_id: str) -> ObserverTrainingSession:
        session = self._sessions[session_id]
        session.completed = True
        return session

    @staticmethod
    def phase_catalog() -> tuple[tuple[str, str], ...]:
        return OBSERVER_TRAINING_PHASES

    def _append_score(self, session_id: str, score: PhaseScore) -> None:
        self._sessions[session_id].phase_scores.append(score)

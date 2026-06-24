"""CRK-1 semantic layer — K7–K12 interpretive pluralism and exposure."""

from __future__ import annotations

import hashlib
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import TYPE_CHECKING

from src.continuity.evidence_ledger import EvidenceRecord, EvidenceType

from src.crk1.errors import ConstitutionalError

if TYPE_CHECKING:
    from src.crk1.runtime_facade import CRK1Evidence, CRK1Outcome, CRK1Runtime

WEIGHT_MAX = 0.99
WEIGHT_EPSILON = 1e-6


def _now_iso() -> str:
    return datetime.now(timezone.utc).replace(microsecond=0).isoformat().replace("+00:00", "Z")


@dataclass
class CRK1Interpretation:
    id: str
    name: str
    version: str
    assumptions: list[str]
    prediction_binding: bool
    weight: float
    adversarial: bool
    created_at: str
    credibility: float = 0.5
    lineage: list[str] = field(default_factory=list)

    def to_schema_dict(self) -> dict:
        payload = {
            "id": self.id,
            "name": self.name,
            "version": self.version,
            "assumptions": list(self.assumptions),
            "prediction_binding": self.prediction_binding,
            "weight": self.weight,
            "adversarial": self.adversarial,
            "created_at": self.created_at,
        }
        if self.lineage:
            payload["lineage"] = list(self.lineage)
        return payload


@dataclass
class CRK1Prediction:
    id: str
    frame_id: str
    evidence_id: str
    claim: str
    created_at: str
    outcome_id: str | None = None
    expected_outcome: str = "outcome-pending"

    @property
    def interpretation_id(self) -> str:
        return self.frame_id


@dataclass
class CRK1Reconstruction:
    id: str
    interpretation_id: str
    evidence_id: str
    reconstructed_view: str
    divergence_from_dominant: float


@dataclass
class CRK1PredictionOutcome:
    id: str
    status: str


class SemanticLayer:
    """K7–K10 interpretive frames, predictions, and reconstruction."""

    def __init__(self, runtime: CRK1Runtime) -> None:
        self._runtime = runtime
        self._frames: dict[str, CRK1Interpretation] = {}
        self._predictions: dict[str, CRK1Prediction] = {}
        self._evidence_frame_ids: dict[str, list[str]] = {}
        self._prediction_outcomes: dict[str, str] = {}
        self._reconstructions: dict[str, list[CRK1Reconstruction]] = {}
        self._interpretive_history: list[dict[str, float]] = []
        self._bootstrapped = False

    def _bootstrap(self) -> None:
        if self._bootstrapped:
            return
        self._bootstrapped = True
        dominant = self._register_interpretation(
            name="dominant-frame",
            assumptions=["consequence-visible"],
            adversarial=False,
            weight=0.55,
            normalize=False,
            lineage=[],
        )
        self._register_interpretation(
            name="adversarial-frame",
            assumptions=["challenge-dominant-reading"],
            adversarial=True,
            weight=0.45,
            normalize=False,
            lineage=[dominant.id],
        )
        self._normalize_weights()

    def _register_interpretation(
        self,
        *,
        name: str,
        assumptions: list[str] | None = None,
        adversarial: bool = False,
        weight: float | None = None,
        version: str = "1.0",
        normalize: bool = True,
        lineage: list[str] | None = None,
    ) -> CRK1Interpretation:
        frame_id = str(uuid.uuid4())
        frame = CRK1Interpretation(
            id=frame_id,
            name=name,
            version=version,
            assumptions=list(assumptions or []),
            prediction_binding=True,
            weight=weight if weight is not None else 0.0,
            adversarial=adversarial,
            created_at=_now_iso(),
            lineage=list(lineage or []),
        )
        if frame.prediction_binding is not True:
            raise ConstitutionalError("K8 violation: interpretation must be prediction-bound")
        self._frames[frame_id] = frame
        if weight is None:
            even = 1.0 / max(len(self._frames), 1)
            for item in self._frames.values():
                if item.weight <= 0:
                    item.weight = even
        if normalize:
            self._normalize_weights()
        return frame

    def get_interpretive_history(self) -> list[dict[str, float]]:
        """Recorded interpretive exposure snapshots for K11 replay."""
        return list(self._interpretive_history)

    def record_interpretive_snapshot(self, record: dict[str, float]) -> None:
        self._interpretive_history.append(dict(record))

    def list_interpreted_evidence(self) -> list[CRK1Evidence]:
        """Evidence objects admitted to the interpretive layer (K7 substrate view)."""
        from src.crk1.runtime_facade import CRK1Evidence

        self._bootstrap()
        admitted: list[CRK1Evidence] = []
        for evidence_id, frame_ids in self._evidence_frame_ids.items():
            if len(frame_ids) < 2:
                continue
            evidence = self._runtime._evidence_by_id.get(evidence_id)
            if evidence is not None:
                admitted.append(evidence)
        return sorted(admitted, key=lambda item: item.id)

    def _normalize_weights(self, *, enforce_k9: bool = True) -> None:
        frames = list(self._frames.values())
        if not frames:
            return
        total = sum(frame.weight for frame in frames)
        if total <= 0:
            even = 1.0 / len(frames)
            for frame in frames:
                frame.weight = even
            total = 1.0
        for frame in frames:
            frame.weight = frame.weight / total
        dominant = max(frames, key=lambda item: item.weight)
        if dominant.weight >= 1.0 - WEIGHT_EPSILON:
            dominant.weight = WEIGHT_MAX
            remainder = 1.0 - WEIGHT_MAX
            others = [item for item in frames if item.id != dominant.id]
            if others:
                share = remainder / len(others)
                for item in others:
                    item.weight = share
        if enforce_k9:
            self._assert_k9()

    def _assert_k9(self) -> None:
        frames = list(self._frames.values())
        if len(frames) < 2:
            raise ConstitutionalError("K9 violation: interpretive monoculture")
        total = sum(frame.weight for frame in frames)
        if abs(total - 1.0) > WEIGHT_EPSILON:
            raise ConstitutionalError("K9 violation: interpretive weights must sum to 1")
        dominant = max(frames, key=lambda item: item.weight)
        if dominant.weight >= 1.0 - WEIGHT_EPSILON:
            raise ConstitutionalError("K9 violation: dominant frame weight too high")
        if not any(frame.weight > 0 and frame.id != dominant.id for frame in frames):
            raise ConstitutionalError("K9 violation: no alternative frame with positive weight")

    def _assert_k7(self, evidence_id: str) -> None:
        bindings = self._evidence_frame_ids.get(evidence_id, [])
        if len(bindings) < 2:
            raise ConstitutionalError("K7 violation: evidence requires plural interpretations")

    def _view_hash(self, frame_id: str, evidence_id: str, *, adversarial: bool) -> str:
        prefix = "reconstruct" if adversarial else "interpret"
        body = f"{prefix}:{frame_id}:{evidence_id}"
        return hashlib.sha256(body.encode()).hexdigest()[:16]

    def create_interpretation(
        self,
        *,
        name: str,
        assumptions: list[str] | None = None,
        adversarial: bool = False,
        weight: float | None = None,
        version: str = "1.0",
        lineage: list[str] | None = None,
    ) -> CRK1Interpretation:
        self._bootstrap()
        return self._register_interpretation(
            name=name,
            assumptions=assumptions,
            adversarial=adversarial,
            weight=weight,
            version=version,
            lineage=lineage,
        )

    def load_interpretation(self, frame_id: str) -> CRK1Interpretation:
        self._bootstrap()
        frame = self._frames.get(frame_id)
        if frame is None:
            raise ConstitutionalError(f"Unknown interpretation frame: {frame_id}")
        return frame

    def get_all_interpretations(self) -> list[CRK1Interpretation]:
        self._bootstrap()
        return sorted(self._frames.values(), key=lambda item: item.id)

    def get_dominant_interpretation(self) -> CRK1Interpretation:
        frames = self.get_all_interpretations()
        return max(frames, key=lambda item: item.weight)

    def create_evidence(
        self,
        *,
        source_identity_id: str | None = None,
        outcome_id: str = "",
    ) -> CRK1Evidence:
        self._bootstrap()
        identity_id = source_identity_id or self._runtime.kernel.ledgers.identity.id
        evidence_id = str(uuid.uuid4())
        store = self._runtime.kernel.ledgers.evidence_store
        if store is not None:
            store.upsert_evidence_record(
                EvidenceRecord(
                    evidence_id=evidence_id,
                    evidence_hash=f"{evidence_id}-hash",
                    evidence_type=EvidenceType.IMPORT,
                    source_lineage="crk1-semantic",
                    source_epoch=self._runtime.kernel.ledgers.epoch,
                    validation_method="crk1-semantic",
                    confidence=0.9,
                    canonical_hash=f"{evidence_id}-hash",
                )
            )
        from src.crk1.runtime_facade import CRK1Evidence

        evidence = CRK1Evidence(
            id=evidence_id,
            outcome_id=outcome_id,
            source_identity_id=identity_id,
        )
        self._runtime._evidence_by_id[evidence_id] = evidence
        self._evidence_frame_ids[evidence_id] = [frame.id for frame in self.get_all_interpretations()]
        self._assert_k7(evidence_id)
        return evidence

    def get_interpretations(self, evidence_id: str) -> list[CRK1Interpretation]:
        self._bootstrap()
        if evidence_id not in self._runtime._evidence_by_id:
            raise ConstitutionalError(f"Unknown evidence: {evidence_id}")
        frame_ids = self._evidence_frame_ids.get(evidence_id, [])
        frames = [self._frames[fid] for fid in frame_ids if fid in self._frames]
        if len(frames) < 2:
            raise ConstitutionalError("K7 violation: evidence requires plural interpretations")
        return frames

    def interpret(self, frame_id: str, evidence_id: str) -> str:
        frame = self.load_interpretation(frame_id)
        if evidence_id not in self._runtime._evidence_by_id:
            raise ConstitutionalError(f"Unknown evidence: {evidence_id}")
        return self._view_hash(frame.id, evidence_id, adversarial=frame.adversarial)

    def reconstruct(self, frame_id: str, evidence_id: str) -> str:
        frame = self.load_interpretation(frame_id)
        if not frame.adversarial:
            raise ConstitutionalError("K10 violation: reconstruction requires adversarial frame")
        return self._view_hash(frame.id, evidence_id, adversarial=True)

    def generate_prediction(self, frame_id: str, evidence_id: str) -> CRK1Prediction:
        frame = self.load_interpretation(frame_id)
        if evidence_id not in self._runtime._evidence_by_id:
            raise ConstitutionalError(f"Unknown evidence: {evidence_id}")
        if frame.prediction_binding is not True:
            raise ConstitutionalError("K8 violation: frame must be prediction-bound")
        prediction_id = str(uuid.uuid4())
        prediction = CRK1Prediction(
            id=prediction_id,
            frame_id=frame_id,
            evidence_id=evidence_id,
            claim=f"predicted-consequence-for-{evidence_id}",
            created_at=_now_iso(),
            expected_outcome=f"expected-outcome-for-{evidence_id}",
        )
        self._predictions[prediction_id] = prediction
        return prediction

    def get_all_predictions(self) -> list[CRK1Prediction]:
        self._bootstrap()
        return sorted(self._predictions.values(), key=lambda item: item.created_at)

    def get_predictions_for_frame(self, frame_id: str) -> list[CRK1Prediction]:
        self._bootstrap()
        return [item for item in self._predictions.values() if item.frame_id == frame_id]

    def get_predictions_for_evidence(self, evidence_id: str) -> list[CRK1Prediction]:
        self._bootstrap()
        if evidence_id not in self._runtime._evidence_by_id:
            raise ConstitutionalError(f"Unknown evidence: {evidence_id}")
        return [item for item in self._predictions.values() if item.evidence_id == evidence_id]

    def get_outcome_for_prediction(self, prediction_id: str) -> CRK1PredictionOutcome:
        prediction = self._predictions.get(prediction_id)
        if prediction is None:
            raise ConstitutionalError(f"Unknown prediction: {prediction_id}")
        outcome_id = self._prediction_outcomes.get(prediction_id) or prediction.outcome_id
        if outcome_id:
            return CRK1PredictionOutcome(id=outcome_id, status="realized")
        return CRK1PredictionOutcome(id="", status="pending")

    def _divergence(self, dominant_view: str, adversarial_view: str) -> float:
        if dominant_view == adversarial_view:
            return 0.0
        return 1.0

    def _ensure_reconstructions(self, evidence_id: str) -> list[CRK1Reconstruction]:
        if evidence_id in self._reconstructions:
            return self._reconstructions[evidence_id]
        if evidence_id not in self._runtime._evidence_by_id:
            raise ConstitutionalError(f"Unknown evidence: {evidence_id}")
        dominant = self.get_dominant_interpretation()
        dom_view = self.interpret(dominant.id, evidence_id)
        recs: list[CRK1Reconstruction] = []
        for frame in self.get_all_interpretations():
            if not frame.adversarial:
                continue
            view = self.reconstruct(frame.id, evidence_id)
            recs.append(
                CRK1Reconstruction(
                    id=str(uuid.uuid4()),
                    interpretation_id=frame.id,
                    evidence_id=evidence_id,
                    reconstructed_view=view,
                    divergence_from_dominant=self._divergence(dom_view, view),
                )
            )
        self._reconstructions[evidence_id] = recs
        return recs

    def get_reconstructions_for_evidence(self, evidence_id: str) -> list[CRK1Reconstruction]:
        self._bootstrap()
        return list(self._ensure_reconstructions(evidence_id))

    def realize_outcome_from_prediction(self, prediction_id: str) -> CRK1Outcome:
        prediction = self._predictions.get(prediction_id)
        if prediction is None:
            raise ConstitutionalError(f"Unknown prediction: {prediction_id}")
        identity_id = self._runtime.kernel.ledgers.identity.id
        decision = self._runtime.propose_and_execute(
            identity=identity_id,
            evidence=[prediction.evidence_id],
        )
        outcomes = self._runtime.get_outcomes(decision.id)
        if not outcomes:
            raise ConstitutionalError("K8 violation: prediction realization must produce outcome")
        outcome = outcomes[0]
        prediction.outcome_id = outcome.id
        self._prediction_outcomes[prediction_id] = outcome.id
        return outcome

    def update_interpretation(self, frame_id: str, evidence_id: str) -> None:
        frame = self.load_interpretation(frame_id)
        if evidence_id not in self._runtime._evidence_by_id:
            raise ConstitutionalError(f"Unknown evidence: {evidence_id}")
        frame.credibility = min(1.0, frame.credibility + 0.1)

    def apply_semantic_drift(self) -> None:
        """K11-admissible drift: shift weight from dominant to challengers without breaking K9."""
        frames = self.get_all_interpretations()
        if len(frames) < 2:
            return
        dominant = max(frames, key=lambda item: item.weight)
        shift = min(0.02, dominant.weight * 0.05)
        if shift <= 0:
            return
        dominant.weight -= shift
        others = [item for item in frames if item.id != dominant.id]
        share = shift / len(others)
        for item in others:
            item.weight += share
        self._normalize_weights()

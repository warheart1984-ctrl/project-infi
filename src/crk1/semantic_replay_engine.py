"""CRK-1 Semantic Replay Engine — reconstruct interpretive state from raw evidence."""

from __future__ import annotations

from typing import TYPE_CHECKING, Any

if TYPE_CHECKING:
    from src.crk1.runtime_facade import CRK1Runtime


class SemanticReplayEngine:
    """
    Reconstructs interpretive state from raw Evidence + Semantic Ledger.
    Founder-independent: requires only Evidence, InterpretationObjects,
    PredictionObjects, and ReconstructionObjects.
    """

    def __init__(self, runtime: CRK1Runtime) -> None:
        self.runtime = runtime

    def replay_evidence_views(self, evidence_id: str) -> dict[str, Any]:
        """
        Returns interpretive views for every frame bound to evidence.
        """
        evidence = self.runtime.load_evidence(evidence_id)
        frames = self.runtime.get_interpretations(evidence.id)

        views = []
        for frame in frames:
            view = self.runtime.interpret(frame.id, evidence.id)
            views.append(
                {
                    "frame_id": frame.id,
                    "frame_name": frame.name,
                    "adversarial": frame.adversarial,
                    "weight": frame.weight,
                    "view": view,
                }
            )

        return {
            "evidence_id": evidence.id,
            "interpretations": views,
        }

    def replay_predictions(self, evidence_id: str) -> list[dict[str, Any]]:
        """Reconstruct predictions for evidence and their realized outcomes."""
        preds = self.runtime.get_predictions_for_evidence(evidence_id)
        result: list[dict[str, Any]] = []

        for prediction in preds:
            outcome = self.runtime.get_outcome_for_prediction(prediction.id)
            result.append(
                {
                    "prediction_id": prediction.id,
                    "interpretation_id": prediction.interpretation_id,
                    "evidence_id": prediction.evidence_id,
                    "claim": prediction.claim,
                    "expected_outcome": prediction.expected_outcome,
                    "realized_outcome": outcome.status if outcome else None,
                }
            )

        return result

    def replay_reconstructions(self, evidence_id: str) -> list[dict[str, Any]]:
        """Return adversarial reconstructions for evidence (K10)."""
        recs = self.runtime.get_reconstructions_for_evidence(evidence_id)
        return [
            {
                "reconstruction_id": item.id,
                "interpretation_id": item.interpretation_id,
                "evidence_id": item.evidence_id,
                "reconstructed_view": item.reconstructed_view,
                "divergence_from_dominant": item.divergence_from_dominant,
            }
            for item in recs
        ]

    def replay_semantic_state(self, evidence_id: str) -> dict[str, Any]:
        """Full semantic snapshot: views, predictions, reconstructions."""
        return {
            "views": self.replay_evidence_views(evidence_id),
            "predictions": self.replay_predictions(evidence_id),
            "reconstructions": self.replay_reconstructions(evidence_id),
        }

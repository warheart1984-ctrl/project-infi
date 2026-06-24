"""CRK-1 Semantic Ledger — canonical interpretive continuity record (K7–K12)."""

from __future__ import annotations

import hashlib
import json
from typing import Any, Literal

from pydantic import BaseModel, Field

from src.crk1.errors import ConstitutionalError
from src.crk1.semantic_objects import (
    InterpretationObject,
    PredictionObject,
    ReconstructionObject,
)

SEMANTIC_LEDGER_VERSION = "1.0"
SEMANTIC_LEDGER_TYPE = "Semantic Continuity Record"

SEMANTIC_INVARIANTS = (
    "K7: Interpretive Pluralism",
    "K8: Prediction Binding",
    "K9: Anti‑Monoculture",
    "K10: Adversarial Reconstruction",
    "K11: Interpretive Drift Envelope",
    "K12: Semantic Exposure Metric",
)

REPLAY_ANCHORS = (
    "All InterpretationObjects must be replayable.",
    "All PredictionObjects must be falsifiable.",
    "All ReconstructionObjects must be reproducible.",
)


class SemanticLedgerEntry(BaseModel):
    """Single append-only semantic ledger row."""

    entry_type: Literal["InterpretationObject", "PredictionObject", "ReconstructionObject"]
    payload: InterpretationObject | PredictionObject | ReconstructionObject

    def to_dict(self) -> dict[str, Any]:
        return {
            "type": self.entry_type,
            **self.payload.model_dump(mode="json"),
        }


class CRK1SemanticLedger(BaseModel):
    """Append-only semantic memory of CRK-1."""

    version: str = SEMANTIC_LEDGER_VERSION
    ledger_type: str = SEMANTIC_LEDGER_TYPE
    entries: list[SemanticLedgerEntry] = Field(default_factory=list)
    signature: str = ""

    def append_interpretation(self, obj: InterpretationObject) -> None:
        self.entries.append(SemanticLedgerEntry(entry_type="InterpretationObject", payload=obj))

    def append_prediction(self, obj: PredictionObject) -> None:
        self.entries.append(SemanticLedgerEntry(entry_type="PredictionObject", payload=obj))

    def append_reconstruction(self, obj: ReconstructionObject) -> None:
        self.entries.append(SemanticLedgerEntry(entry_type="ReconstructionObject", payload=obj))

    def sync_from_runtime(self, runtime: Any) -> int:
        """Materialize current interpretive substrate into ledger entries."""
        from src.crk1.semantic_objects import OutcomeDescriptor

        added = 0
        seen_interp: set[str] = set()
        seen_pred: set[str] = set()
        seen_rec: set[str] = set()

        for frame in runtime.get_all_interpretations():
            if frame.id in seen_interp:
                continue
            self.append_interpretation(InterpretationObject.from_crk1_interpretation(frame))
            seen_interp.add(frame.id)
            added += 1

        for prediction in runtime.get_all_predictions():
            if prediction.id in seen_pred:
                continue
            self.append_prediction(
                PredictionObject.from_crk1_prediction(
                    prediction,
                    expected_outcome=OutcomeDescriptor(
                        summary=prediction.expected_outcome or prediction.claim,
                        measurable=True,
                    ),
                )
            )
            seen_pred.add(prediction.id)
            added += 1

        for evidence in runtime.list_interpreted_evidence():
            try:
                reconstructions = runtime.get_reconstructions_for_evidence(evidence.id)
            except ConstitutionalError:
                continue
            for rec in reconstructions:
                if rec.id in seen_rec:
                    continue
                self.append_reconstruction(ReconstructionObject.from_crk1_reconstruction(rec))
                seen_rec.add(rec.id)
                added += 1

        return added

    def finalize_signature(self, *, secret: str = "SEMANTIC") -> str:
        body = json.dumps(
            [entry.to_dict() for entry in self.entries],
            sort_keys=True,
            separators=(",", ":"),
        )
        digest = hashlib.sha256(f"{secret}:{body}".encode("utf-8")).hexdigest()
        self.signature = digest
        return digest

    def to_canonical_text(self) -> str:
        sig = self.signature or self.finalize_signature()
        lines = [
            "CRK‑1 Semantic Ledger",
            f"Version: {self.version}",
            f"Ledger Type: {self.ledger_type}",
            "",
            "Entries:",
        ]
        for entry in self.entries:
            payload = entry.payload.model_dump(mode="json")
            lines.append(f"  - type: {entry.entry_type}")
            for key, value in payload.items():
                if isinstance(value, list):
                    rendered = ", ".join(str(item) for item in value)
                    lines.append(f"    {key}: [{rendered}]")
                elif isinstance(value, dict):
                    lines.append(f"    {key}: {value}")
                else:
                    lines.append(f"    {key}: {value}")
            lines.append("")
        lines.append("Semantic Invariants:")
        for invariant in SEMANTIC_INVARIANTS:
            lines.append(f"  - {invariant}")
        lines.append("")
        lines.append("Replay Anchors:")
        for anchor in REPLAY_ANCHORS:
            lines.append(f"  - {anchor}")
        lines.append("")
        lines.append("Signature:")
        lines.append(f"  {sig}")
        return "\n".join(lines)


def bootstrap_semantic_ledger(runtime: Any) -> CRK1SemanticLedger:
    """Build a signed semantic ledger from a live runtime."""
    ledger = CRK1SemanticLedger()
    ledger.sync_from_runtime(runtime)
    ledger.finalize_signature()
    return ledger

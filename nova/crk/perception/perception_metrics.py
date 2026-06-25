from __future__ import annotations

from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Literal

PerceptionHealthStatus = Literal["healthy", "drifting", "degraded"]


@dataclass(frozen=True)
class PerceptionSnapshot:
    intent_id: str
    epoch_id: str
    inputs: dict[str, Any]
    outputs: dict[str, Any]
    confidence: float
    anomaly_score: float
    recorded_at: str = field(
        default_factory=lambda: datetime.now(timezone.utc)
        .replace(microsecond=0)
        .isoformat()
        .replace("+00:00", "Z")
    )

    def stable_dict(self) -> dict[str, Any]:
        return {
            "intent_id": self.intent_id,
            "epoch_id": self.epoch_id,
            "inputs": self.inputs,
            "outputs": self.outputs,
            "confidence": round(self.confidence, 6),
            "anomaly_score": round(self.anomaly_score, 6),
        }


def health_from_anomaly(anomaly_score: float) -> PerceptionHealthStatus:
    if anomaly_score >= 0.75:
        return "degraded"
    if anomaly_score >= 0.4:
        return "drifting"
    return "healthy"

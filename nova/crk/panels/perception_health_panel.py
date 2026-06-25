from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nova.crk.perception.perception_metrics import (
    PerceptionSnapshot,
    health_from_anomaly,
)
from nova.law_kernel.models import Intent, LawContext

_snapshots: list[PerceptionSnapshot] = []
_hydrated = False


def _ensure_hydrated() -> None:
    global _hydrated
    if _hydrated or _snapshots:
        return
    try:
        from nova.bridges.panel_store import get_panel_store

        for row in get_panel_store().list_perception_snapshots():
            _snapshots.append(
                PerceptionSnapshot(
                    intent_id=str(row.get("intent_id") or ""),
                    epoch_id=str(row.get("epoch_id") or ""),
                    inputs=dict(row.get("inputs") or {}),
                    outputs=dict(row.get("outputs") or {}),
                    confidence=float(row.get("confidence") or 0.0),
                    anomaly_score=float(row.get("anomaly_score") or 0.0),
                )
            )
    except Exception:
        pass
    _hydrated = True


def _persist_snapshot(snapshot: PerceptionSnapshot) -> None:
    try:
        from nova.bridges.panel_store import get_panel_store

        get_panel_store().append_perception_snapshot(snapshot.stable_dict())
    except Exception:
        pass


@dataclass
class PerceptionHealthSummary:
    epoch_id: str
    snapshot_count: int = 0
    latest_health: str = "healthy"
    max_anomaly: float = 0.0
    anomaly_trend: list[float] = field(default_factory=list)

    def to_dict(self) -> dict[str, Any]:
        return {
            "epoch_id": self.epoch_id,
            "snapshot_count": self.snapshot_count,
            "latest_health": self.latest_health,
            "max_anomaly": round(self.max_anomaly, 6),
            "anomaly_trend": [round(value, 6) for value in self.anomaly_trend],
        }


class PerceptionHealthPanel:
    """CRK-T4: tracks perceptual IO health per epoch."""

    def record_snapshot(
        self,
        intent: Intent,
        context: LawContext,
        result: Any,
    ) -> PerceptionSnapshot:
        inputs = {
            "kind": intent.kind,
            "capability": intent.payload.get("capability"),
            "domain": context.domain,
        }
        outputs = result if isinstance(result, dict) else {"result": str(result)}
        confidence = float(intent.payload.get("perception_confidence", 0.85))
        anomaly_score = float(intent.payload.get("anomaly_score", 0.0))
        if intent.payload.get("force_anomaly") is not None:
            anomaly_score = float(intent.payload["force_anomaly"])

        snapshot = PerceptionSnapshot(
            intent_id=intent.id,
            epoch_id=context.epoch,
            inputs=inputs,
            outputs=outputs,
            confidence=confidence,
            anomaly_score=anomaly_score,
        )
        _snapshots.append(snapshot)
        _persist_snapshot(snapshot)
        return snapshot

    def evaluate_epoch(self, epoch_id: str) -> PerceptionHealthSummary:
        _ensure_hydrated()
        epoch_snaps = [snap for snap in _snapshots if snap.epoch_id == epoch_id]
        trend = [snap.anomaly_score for snap in epoch_snaps]
        max_anomaly = max(trend) if trend else 0.0
        latest_health = health_from_anomaly(max_anomaly)
        return PerceptionHealthSummary(
            epoch_id=epoch_id,
            snapshot_count=len(epoch_snaps),
            latest_health=latest_health,
            max_anomaly=max_anomaly,
            anomaly_trend=trend,
        )

    def list_snapshots(self, *, epoch_id: str | None = None) -> list[PerceptionSnapshot]:
        _ensure_hydrated()
        if epoch_id is None:
            return list(_snapshots)
        return [snap for snap in _snapshots if snap.epoch_id == epoch_id]


def clear_perception_snapshots() -> None:
    global _hydrated
    _snapshots.clear()
    _hydrated = False
    try:
        from nova.bridges.panel_store import get_panel_store

        get_panel_store().clear_perception()
    except Exception:
        pass

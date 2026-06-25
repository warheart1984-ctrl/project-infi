from __future__ import annotations

from dataclasses import dataclass, field
from typing import Any

from nova.governance.steward_models import RatifiedAmendment


@dataclass
class IdentitySnapshot:
    actor_id: str
    epoch_id: str
    identity_hash: str
    amendments: list[dict[str, Any]] = field(default_factory=list)
    source: str = "nova"
    mission: str = ""
    values: list[str] = field(default_factory=list)
    drift_scores: dict[str, float] = field(default_factory=dict)

    def to_dict(self) -> dict[str, Any]:
        return {
            "actor_id": self.actor_id,
            "epoch_id": self.epoch_id,
            "identity_hash": self.identity_hash,
            "amendments": list(self.amendments),
            "source": self.source,
            "mission": self.mission,
            "values": list(self.values),
            "drift_scores": dict(self.drift_scores),
        }


class IdentityHistoryStore:
    def __init__(self) -> None:
        self._snapshots: dict[str, IdentitySnapshot] = {}

    def ensure_snapshot(self, *, actor_id: str, epoch_id: str, identity_hash: str) -> IdentitySnapshot:
        key = f"{actor_id}:{epoch_id}"
        if key not in self._snapshots:
            self._snapshots[key] = IdentitySnapshot(
                actor_id=actor_id,
                epoch_id=epoch_id,
                identity_hash=identity_hash,
            )
        return self._snapshots[key]

    def append_amendment(self, snapshot_key: str, amendment: dict[str, Any]) -> None:
        snapshot = self._snapshots.setdefault(
            snapshot_key,
            IdentitySnapshot(actor_id="unknown", epoch_id="unknown", identity_hash="unknown"),
        )
        snapshot.amendments.append(amendment)

    def list_snapshots(self) -> list[IdentitySnapshot]:
        return list(self._snapshots.values())

    def list_local_snapshots(self) -> list[IdentitySnapshot]:
        return list(self._snapshots.values())


_store = IdentityHistoryStore()


def get_identity_history() -> IdentityHistoryStore:
    return _store


def list_hud_identity_snapshots() -> list[IdentitySnapshot]:
    """Merge src kernel identity (identity_bridge) with Nova steward amendments."""
    merged: dict[str, IdentitySnapshot] = {}

    try:
        from nova.bridges import identity_bridge

        current = identity_bridge.get_current_identity()
        identity = current.identity
        epoch_id = f"EPOCH:{current.epoch}:T0"
        actor_id = str(identity.get("actor_id") or identity.get("subject") or "operator")
        key = f"{actor_id}:{epoch_id}"
        merged[key] = IdentitySnapshot(
            actor_id=actor_id,
            epoch_id=epoch_id,
            identity_hash=str(identity.get("identity_hash") or ""),
            source="src.kernel",
            mission=str(identity.get("mission") or ""),
            values=[str(v) for v in identity.get("values") or []],
            drift_scores=dict(current.drift_scores),
        )
        for event in identity_bridge.get_identity_history():
            event_epoch_id = f"EPOCH:{event.epoch}:T0"
            event_identity = event.identity
            event_actor = str(event_identity.get("actor_id") or actor_id)
            event_key = f"{event_actor}:{event_epoch_id}"
            if event_key in merged:
                continue
            merged[event_key] = IdentitySnapshot(
                actor_id=event_actor,
                epoch_id=event_epoch_id,
                identity_hash=str(event_identity.get("identity_hash") or ""),
                source="src.kernel",
                mission=str(event_identity.get("mission") or ""),
                values=[str(v) for v in event_identity.get("values") or []],
            )
    except Exception:
        pass

    for local in _store.list_local_snapshots():
        key = f"{local.actor_id}:{local.epoch_id}"
        if key in merged:
            merged[key].amendments.extend(local.amendments)
            if local.identity_hash and local.identity_hash != "unknown":
                merged[key] = IdentitySnapshot(
                    actor_id=merged[key].actor_id,
                    epoch_id=merged[key].epoch_id,
                    identity_hash=local.identity_hash,
                    amendments=merged[key].amendments + list(local.amendments),
                    source=merged[key].source,
                    mission=merged[key].mission,
                    values=list(merged[key].values),
                    drift_scores=dict(merged[key].drift_scores),
                )
        else:
            merged[key] = local

    return list(merged.values())


def append_ratified_amendment(amendment: RatifiedAmendment) -> None:
    actor_id = str(amendment.payload.get("actor_id", "operator"))
    epoch_id = str(amendment.payload.get("epoch_id", "EPOCH:0:T0"))
    identity_hash = str(amendment.payload.get("identity_hash", amendment.t5_ref_signal_hash))
    key = f"{actor_id}:{epoch_id}"
    _store.ensure_snapshot(actor_id=actor_id, epoch_id=epoch_id, identity_hash=identity_hash)
    _store.append_amendment(key, amendment.to_dict())


def clear_identity_history() -> None:
    _store._snapshots.clear()

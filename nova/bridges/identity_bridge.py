"""Identity history — src.kernel.identity_history → steward HUD."""

from __future__ import annotations

from typing import Iterable

from src.kernel.identity_history import IdentityHistory

from nova.bridges.identity_types import IdentityEvent, IdentitySnapshot


def get_identity_history(subject_id: str = "") -> Iterable[IdentityEvent]:
    del subject_id  # src store is process-global; subject scoping is future work
    history = IdentityHistory.current()
    for snap in history.snapshots:
        yield IdentityEvent(
            epoch=snap.epoch,
            identity=snap.identity.to_dict(),
        )


def get_current_identity(subject_id: str = "") -> IdentitySnapshot:
    del subject_id
    history = IdentityHistory.current()
    active = history.active_identity
    return IdentitySnapshot(
        epoch=history.snapshots[-1].epoch,
        identity=active.to_dict(),
        drift_scores={
            "mission_drift": history.mission_drift_score(),
            "value_drift": history.value_drift_score(),
        },
    )

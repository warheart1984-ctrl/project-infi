"""Epochs, RIL export/replay, drift — nova continuity ↔ src substrate."""

from __future__ import annotations

from typing import Iterable

from src.continuity.law_ledger import LawLedgerStore

from nova.continuity.replay import replay_ril
from nova.continuity.ril_bridge import RILEpochBundle, ReplayedSummary, export_epoch_lineage
from nova.continuity.types import EpochSummary, RILExport


def list_epochs() -> Iterable[EpochSummary]:
    store = LawLedgerStore()
    current = store.get_current_epoch()
    laws = store.all_laws()
    for number in range(0, current + 1):
        yield EpochSummary(
            epoch_id=f"EPOCH:{number}:T0",
            epoch_number=number,
            law_count=len(laws),
            metadata={"source": "src.continuity.law_ledger"},
        )


def export_ril(epoch_id: str) -> RILExport:
    bundle = export_epoch_lineage(epoch_id)
    return RILExport(epoch_id=epoch_id, bundle=bundle.to_dict())


def replay_epoch_through_law_kernel(epoch_id: str) -> ReplayedSummary:
    """
    Deep replay: pull RIL from src/nova bundle, re-materialize panel state,
    rebuild cockpit summary through the law-kernel-aware replay path.
    """
    ril = export_ril(epoch_id)
    return replay_ril(ril)


def replay_bundle(bundle: RILEpochBundle) -> ReplayedSummary:
    """Replay an already-exported epoch bundle."""
    return replay_ril(RILExport(epoch_id=bundle.epoch_id, bundle=bundle.to_dict()))

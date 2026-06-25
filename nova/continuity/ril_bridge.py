from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from nova.crk.cockpit.summary_builder import build_cockpit_summary
from nova.crk.lineage.reflexive_events import list_reflexive_events
from nova.crk.panels.perception_health_panel import PerceptionHealthPanel
from nova.governance.steward_ledger import list_steward_events


@dataclass(frozen=True)
class RILEpochBundle:
    epoch_id: str
    cockpit_summary: dict[str, Any]
    reflexive_events: list[dict[str, Any]]
    steward_events: list[dict[str, Any]]
    perception_snapshots: list[dict[str, Any]]

    def to_dict(self) -> dict[str, Any]:
        return {
            "epoch_id": self.epoch_id,
            "cockpit_summary": self.cockpit_summary,
            "reflexive_events": self.reflexive_events,
            "steward_events": self.steward_events,
            "perception_snapshots": self.perception_snapshots,
        }


@dataclass(frozen=True)
class ReplayedSummary:
    epoch_id: str
    cockpit_summary: dict[str, Any]

    def to_dict(self) -> dict[str, Any]:
        return {"epoch_id": self.epoch_id, "cockpit_summary": self.cockpit_summary}


def export_epoch_lineage(epoch_id: str) -> RILEpochBundle:
    panel = PerceptionHealthPanel()
    return RILEpochBundle(
        epoch_id=epoch_id,
        cockpit_summary=build_cockpit_summary(epoch_id=epoch_id),
        reflexive_events=[
            event for event in list_reflexive_events() if event.get("epoch_id") == epoch_id
        ],
        steward_events=list_steward_events(),
        perception_snapshots=[
            snap.stable_dict() for snap in panel.list_snapshots(epoch_id=epoch_id)
        ],
    )


def replay_epoch(bundle: RILEpochBundle) -> ReplayedSummary:
    from nova.continuity.replay import replay_ril
    from nova.continuity.types import RILExport

    return replay_ril(RILExport(epoch_id=bundle.epoch_id, bundle=bundle.to_dict()))

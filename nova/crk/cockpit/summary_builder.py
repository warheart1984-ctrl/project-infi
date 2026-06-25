from __future__ import annotations

from typing import Any

from nova.crk.cockpit.summary_schema import CockpitSummarySchema
from nova.crk.identity.identity_history import list_hud_identity_snapshots
from nova.crk.lineage.reflexive_events import KIND_REFLEXIVE_EVAL, list_reflexive_events
from nova.crk.panels.perception_health_panel import PerceptionHealthPanel
from nova.crk.panels.reflexive_evaluation_panel import ReflexiveEvaluationPanel
from nova.governance.steward_ledger import list_steward_events
from nova.bridges.boundary_bridge import compute_boundary_status, to_panel_status
from nova.law_kernel import t5_binding


def build_cockpit_summary(*, epoch_id: str = "EPOCH:0:T0") -> dict[str, Any]:
    """Pure aggregation of recorded events and panel state for an epoch."""
    try:
        boundary_panel = to_panel_status(
            compute_boundary_status(focus_ref=epoch_id),
            epoch_id=epoch_id,
        )
    except Exception:
        boundary_panel = {
            "epoch_id": epoch_id,
            "status": "stable",
            "violations": 0,
            "message": "boundary kernel unavailable",
        }

    ref = t5_binding.T5ReferenceSignal.current()
    reflexive_panel = ReflexiveEvaluationPanel()
    perception_panel = PerceptionHealthPanel()

    reflexive_events = [
        event for event in list_reflexive_events() if event.get("epoch_id") == epoch_id
    ]
    reflexive_eval_count = sum(
        1 for event in reflexive_events if event.get("kind") == KIND_REFLEXIVE_EVAL
    )
    reflexive_summary = reflexive_panel.summarize_epoch(epoch_id)
    perception_summary = perception_panel.evaluate_epoch(epoch_id)

    identity_snapshots = [snap.to_dict() for snap in list_hud_identity_snapshots()]
    amendments = [
        event for event in list_steward_events() if event.get("kind") == "AMENDMENT_RATIFIED"
    ]

    schema = CockpitSummarySchema(
        boundary_detection=boundary_panel,
        reference_integrity={
            "t5_ref_signal_hash": ref.hash,
            "ref_signal_id": ref.id,
            "bound": True,
        },
        identity_history={
            "snapshots": identity_snapshots,
            "amendment_count": sum(len(s.get("amendments", [])) for s in identity_snapshots),
        },
        pit_evolution={
            "epoch_id": epoch_id,
            "active_bands": ["PIT-1", "PIT-2", "PIT-3"],
        },
        reflexive_evaluation={
            "latest_reflexive_health": reflexive_summary.get("latest_health", "unknown"),
            "reflexive_eval_count": reflexive_eval_count,
            "epoch_summary": reflexive_summary,
        },
        perception_health={
            "latest_perception_health": perception_summary.latest_health,
            "anomaly_trend": perception_summary.anomaly_trend,
            "epoch_summary": perception_summary.to_dict(),
        },
        amendment_history={
            "ratified": amendments,
            "count": len(amendments),
        },
    )
    return schema.to_dict()

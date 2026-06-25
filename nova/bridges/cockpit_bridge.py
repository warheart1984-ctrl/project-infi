"""Constitutional cockpit v1 → cockpit v2 / HUD normalization."""

from __future__ import annotations

from typing import Any

from nova.crk.cockpit.summary_schema import CockpitSummarySchema


class CockpitSummaryV2:
    """Normalized cockpit v2 view built from legacy src summary or nova panels."""

    def __init__(self, payload: dict[str, Any]) -> None:
        self._payload = dict(payload)

    @classmethod
    def from_legacy(cls, legacy: dict[str, Any]) -> CockpitSummaryV2:
        epoch_id = f"EPOCH:{legacy.get('epoch', 0)}:T0"
        boundary = legacy.get("boundary_detection") or {}
        reference = legacy.get("reference_integrity") or {}
        identity = {
            "snapshots": [],
            "amendment_count": 0,
            "source": "src.constitutional_cockpit",
        }
        schema = CockpitSummarySchema(
            boundary_detection={
                "epoch_id": epoch_id,
                "status": _legacy_boundary_status(boundary),
                "violations": _legacy_boundary_violations(boundary),
                "kernel": boundary,
            },
            reference_integrity={
                "t5_ref_signal_hash": str(reference.get("reference_integrity", "")),
                "metrics": reference,
                "bound": True,
            },
            identity_history=identity,
            pit_evolution={
                "epoch_id": epoch_id,
                "active_bands": ["PIT-1", "PIT-2", "PIT-3"],
                "sovereign_laws": legacy.get("sovereign_laws") or [],
            },
            reflexive_evaluation={
                "latest_reflexive_health": "unknown",
                "reflexive_eval_count": 0,
                "epoch_summary": {},
            },
            perception_health={
                "latest_perception_health": "healthy",
                "anomaly_trend": [],
                "epoch_summary": {},
            },
            amendment_history={
                "ratified": legacy.get("amendments") or [],
                "count": len(legacy.get("amendments") or []),
            },
        )
        return cls(schema.to_dict())

    def to_dict(self) -> dict[str, Any]:
        return dict(self._payload)


def _legacy_boundary_status(boundary: dict[str, Any]) -> str:
    insufficiency = float(boundary.get("insufficiency") or 0.0)
    if insufficiency >= 0.65 or boundary.get("amendment_triggered"):
        return "violation"
    if insufficiency >= 0.40 or boundary.get("amendment_proposed"):
        return "warning"
    return "stable"


def _legacy_boundary_violations(boundary: dict[str, Any]) -> int:
    signals = boundary.get("signals") or []
    return sum(1 for value in signals if float(value) >= 0.65)


def fetch_legacy_cockpit_summary() -> CockpitSummaryV2:
    """
    Call the src constitutional cockpit and normalize into v2 schema.
    Transitional: lets you keep v1 alive while moving operators to v2/HUD.
    """
    from src.constitutional_cockpit_routes import build_cockpit_summary

    legacy = build_cockpit_summary()
    return CockpitSummaryV2.from_legacy(legacy)

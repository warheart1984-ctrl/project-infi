"""CRK-T2 boundary status — src.kernel boundary loop → cockpit v2."""

from __future__ import annotations

from typing import Literal, TypedDict

from src.kernel.amendment_controller import DEFAULT_THETA_HIGH, DEFAULT_THETA_LOW
from src.kernel.boundary_service import get_boundary_loop
from src.kernel.telemetry import Telemetry

from nova.crk.types import BoundaryStatus


class BoundarySummary(TypedDict):
    status: Literal["stable", "warning", "violation"]
    violations: int
    details: str
    kernel: dict


def _classify_snapshot(snapshot: dict) -> tuple[Literal["stable", "warning", "violation"], int]:
    insufficiency = float(snapshot.get("insufficiency") or 0.0)
    signals = snapshot.get("signals") or []
    violation_count = sum(1 for value in signals if float(value) >= DEFAULT_THETA_HIGH)
    if insufficiency >= DEFAULT_THETA_HIGH or bool(snapshot.get("amendment_triggered")):
        return "violation", max(violation_count, 1)
    if insufficiency >= DEFAULT_THETA_LOW or bool(snapshot.get("amendment_proposed")):
        return "warning", violation_count
    return "stable", violation_count


def compute_boundary_status(focus_ref: str = "") -> BoundarySummary:
    """
    Ask src.kernel for CRK-T2 boundary status for the focused object
    (agent, substrate, environment, etc.).
    """
    loop = get_boundary_loop()
    loop.monitor.telemetry = Telemetry.current()
    snapshot = loop.snapshot()
    status, violations = _classify_snapshot(snapshot)
    details = f"insufficiency={snapshot.get('insufficiency', 0.0):.4f}"
    if focus_ref:
        details = f"focus={focus_ref}; {details}"
    return BoundarySummary(
        status=status,
        violations=violations,
        details=details,
        kernel=snapshot,
    )


def to_panel_status(summary: BoundarySummary, *, epoch_id: str = "") -> dict:
    """Map src boundary summary into cockpit v2 / HUD panel shape."""
    panel = BoundaryStatus(
        status=summary["status"],
        violations=summary["violations"],
        message=summary["details"],
        kernel=summary.get("kernel"),
    ).to_dict()
    if epoch_id:
        panel["epoch_id"] = epoch_id
    return panel

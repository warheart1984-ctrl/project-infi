"""Compositor UI bridge — ui.* capabilities through USLGate."""

from __future__ import annotations

from src.usl.types import CapabilityRequest, DeltaSummary, GuestContext, ResourceInfo


def build_ui_present_request(
    guest: GuestContext,
    surface_id: str,
    *,
    width: int = 800,
    height: int = 600,
    ceiling_id: str = "ui.basic",
) -> CapabilityRequest:
    return CapabilityRequest(
        capability_id="ui.present",
        ceiling_id=ceiling_id,
        resource=ResourceInfo(
            kind="surface",
            locator=surface_id,
            extra={"width": width, "height": height},
        ),
        guest=guest,
        pre_state_hash="ui:hidden",
        post_state_hash=f"ui:visible:{surface_id}",
        delta_hash=f"ui:delta:{surface_id}",
        delta_summary=DeltaSummary(),
    )

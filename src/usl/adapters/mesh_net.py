"""Mesh network adapter — net.* capabilities through USLGate."""

from __future__ import annotations

from src.usl.types import CapabilityRequest, DeltaSummary, GuestContext, ResourceInfo


def build_net_connect_request(
    guest: GuestContext,
    host: str,
    port: int,
    *,
    ceiling_id: str = "net.basic",
) -> CapabilityRequest:
    return CapabilityRequest(
        capability_id="net.connect",
        ceiling_id=ceiling_id,
        resource=ResourceInfo(
            kind="socket",
            locator=f"{host}:{port}",
            extra={"host": host, "port": port},
        ),
        guest=guest,
        pre_state_hash="net:closed",
        post_state_hash=f"net:open:{host}:{port}",
        delta_hash=f"net:delta:{host}:{port}",
        delta_summary=DeltaSummary(bytes_out=0, bytes_in=0),
    )

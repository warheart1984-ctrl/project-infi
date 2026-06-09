"""Capability checks for mesh peer requests."""

from __future__ import annotations

from src.mesh.known_peers import KnownPeersStore
from src.mesh.runtime import mesh_base

CAP_REASONING_EVALUATE = "reasoning_evaluate"
CAP_FALSITY_SYNC = "falsity_sync"
CAP_INVARIANT_PROPAGATE = "invariant_propagate"


def check_evaluate_capability(peer_id: str | None, base_dir=None) -> tuple[bool, str | None]:
    if not peer_id:
        return True, None
    store = KnownPeersStore(base_dir or mesh_base())
    if not store.get(peer_id):
        return False, "unknown_peer"
    if not store.peer_has_capability(peer_id, CAP_REASONING_EVALUATE):
        return False, "capability_denied:reasoning_evaluate"
    return True, None


def check_gossip_capability(peer_id: str | None, base_dir=None) -> tuple[bool, str | None]:
    if not peer_id:
        return True, None
    store = KnownPeersStore(base_dir or mesh_base())
    if not store.get(peer_id):
        return False, "unknown_peer"
    if not store.peer_has_capability(peer_id, CAP_FALSITY_SYNC):
        return False, "capability_denied:falsity_sync"
    return True, None

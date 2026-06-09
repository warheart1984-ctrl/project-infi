"""Capability negotiation between mesh nodes."""

from __future__ import annotations

DEFAULT_CAPABILITIES = frozenset(
    {
        "reasoning_evaluate",
        "falsity_sync",
        "invariant_propagate",
        "handshake",
        "gossip",
    }
)


def normalize_capabilities(caps: list[str] | None) -> set[str]:
    if not caps:
        return set()
    return {c.strip() for c in caps if c and c.strip()}


def negotiate(local: list[str], remote: list[str]) -> dict:
    local_set = normalize_capabilities(local) & DEFAULT_CAPABILITIES
    remote_set = normalize_capabilities(remote) & DEFAULT_CAPABILITIES
    shared = sorted(local_set & remote_set)
    local_only = sorted(local_set - remote_set)
    remote_only = sorted(remote_set - local_set)
    return {
        "shared": shared,
        "intersection": shared,
        "local_only": local_only,
        "remote_only": remote_only,
        "compatible": bool(shared) and "handshake" in shared,
    }


def capability_advertisement(config: dict) -> list[str]:
    return sorted(normalize_capabilities(config.get("capabilities")) & DEFAULT_CAPABILITIES)

"""Derive USL capabilities from syscall effects."""

from __future__ import annotations

from src.usl.lift.types import (
    AAISCapabilitySet,
    AAISEffectSurface,
    AuthorityGrant,
    ResourceCapability,
)

_BUCKET_TO_CAP: dict[str, tuple[str, str]] = {
    "fs": ("fs.read", "fs"),
    "net": ("net.connect", "net"),
    "timer": ("time.read", "time"),
    "proc": ("proc.exit", "proc"),
    "mem": ("mem.map", "mem"),
    "device_io": ("ipc.invoke", "ipc"),
}

_BUCKET_TO_AUTHORITY: dict[str, tuple[str, str]] = {
    "fs": ("auth.fs", "write"),
    "net": ("auth.net", "write"),
    "timer": ("auth.time", "read"),
    "proc": ("auth.proc", "execute"),
    "mem": ("auth.mem", "write"),
    "device_io": ("auth.device", "admin"),
}


def lift_capabilities_from_effects(effects: AAISEffectSurface) -> AAISCapabilitySet:
    """Map effect buckets to usl_capability_id resources and authorities."""
    seen: set[str] = set()
    resources: list[ResourceCapability] = []
    authorities: list[AuthorityGrant] = []

    for fx in effects.syscalls:
        bucket = fx.bucket
        if bucket == "unknown" or bucket in seen:
            continue
        seen.add(bucket)
        cap_id, cap_class = _BUCKET_TO_CAP.get(bucket, ("ipc.invoke", "ipc"))
        auth_id, level = _BUCKET_TO_AUTHORITY.get(bucket, ("auth.unknown", "read"))
        resources.append(
            ResourceCapability(
                usl_capability_id=cap_id,
                class_=cap_class,  # type: ignore[arg-type]
                scope="guest",
            )
        )
        authorities.append(
            AuthorityGrant(
                authority_id=auth_id,
                level=level,  # type: ignore[arg-type]
            )
        )

    ceiling = "daily-driver" if resources else "containment"
    return AAISCapabilitySet(resources=resources, authorities=authorities, ceiling_id=ceiling)

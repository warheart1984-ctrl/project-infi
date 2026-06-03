"""UGR Proof-of-Subsystem discovery — governed spec validation and hash-anchored receipts."""

from src.ugr.discovery.subsystem_discovery import (
    SubsystemDiscoveryService,
    build_subsystem_discovery_service,
    discovery_enabled,
    shadow_only_default,
)
from src.ugr.discovery.subsystem_spec import SubsystemSpec, stable_json, subsystem_id_from_spec

__all__ = [
    "SubsystemDiscoveryService",
    "SubsystemSpec",
    "build_subsystem_discovery_service",
    "discovery_enabled",
    "shadow_only_default",
    "stable_json",
    "subsystem_id_from_spec",
]

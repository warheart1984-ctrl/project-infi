"""UGR Proof-of-Discovery — contribution and subsystem discovery."""

from src.ugr.discovery.contribution_discovery import (
    ContributionDiscoveryService,
    build_contribution_discovery_service,
)
from src.ugr.discovery.subsystem_discovery import (
    SubsystemDiscoveryService,
    build_subsystem_discovery_service,
    discovery_enabled,
)

__all__ = [
    "ContributionDiscoveryService",
    "SubsystemDiscoveryService",
    "build_contribution_discovery_service",
    "build_subsystem_discovery_service",
    "discovery_enabled",
]

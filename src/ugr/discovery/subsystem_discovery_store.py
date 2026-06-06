"""Backward-compatible subsystem discovery store — delegates to ContributionDiscoveryStore."""

from __future__ import annotations

from src.ugr.discovery.contribution_store import ContributionDiscoveryStore


class SubsystemDiscoveryStore(ContributionDiscoveryStore):
    def get_by_subsystem_id(self, subsystem_id: str) -> dict[str, Any] | None:
        return self.get_by_contribution_id(subsystem_id)

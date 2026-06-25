"""Tiered artifact index for stewardship substrate runtimes."""

from __future__ import annotations

from dataclasses import dataclass

from constitutional.significance.reference_lattice import (
    SIGNIFICANCE_TIER_LABELS,
    SYNTHETIC_ARTIFACTS,
    get_reference_lattice,
)


@dataclass(frozen=True)
class StewardshipArtifact:
    id: str
    title: str
    significance_tier: int
    tier_label: str


class ArtifactIndex:
    """Index of constitutional artifacts with significance tiers."""

    def __init__(self, lattice: dict[str, int] | None = None) -> None:
        self._lattice = lattice or get_reference_lattice()

    def all_artifacts(self) -> list[StewardshipArtifact]:
        items: list[StewardshipArtifact] = []
        for artifact_id, meta in SYNTHETIC_ARTIFACTS.items():
            tier = self._lattice.get(artifact_id, 4)
            items.append(
                StewardshipArtifact(
                    id=artifact_id,
                    title=meta.get("title", artifact_id),
                    significance_tier=tier,
                    tier_label=SIGNIFICANCE_TIER_LABELS.get(tier, f"Tier {tier}"),
                )
            )
        return items

    def tier_0_and_1(self) -> list[StewardshipArtifact]:
        return [artifact for artifact in self.all_artifacts() if artifact.significance_tier <= 1]

    def get(self, artifact_id: str) -> StewardshipArtifact | None:
        for artifact in self.all_artifacts():
            if artifact.id == artifact_id:
                return artifact
        return None


def default_artifact_index() -> ArtifactIndex:
    return ArtifactIndex()

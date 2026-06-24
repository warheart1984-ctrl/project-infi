"""Reality Contact Layer (RCL) — K13–K15 invariants and Reality Diversity Index."""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from typing import Any

from src.crk1.errors import ConstitutionalError


class ControlLevel(str, Enum):
    NONE = "none"
    PARTIAL = "partial"
    HIGH = "high"


@dataclass
class RealityDomain:
    """One external reality surface D_i."""

    domain_id: str
    label: str
    control_level: ControlLevel = ControlLevel.NONE
    contact_frequency: float = 1.0
    consequence_intensity: float = 1.0
    independent_incentives: bool = True
    independent_failure_modes: bool = True
    independent_power_structures: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "domain_id": self.domain_id,
            "label": self.label,
            "control_level": self.control_level.value,
            "contact_frequency": self.contact_frequency,
            "consequence_intensity": self.consequence_intensity,
            "independent_incentives": self.independent_incentives,
            "independent_failure_modes": self.independent_failure_modes,
            "independent_power_structures": self.independent_power_structures,
        }


@dataclass
class RealitySurfaceRegistry:
    """Registry of reality domains the system must remain exposed to."""

    domains: list[RealityDomain] = field(default_factory=list)
    min_uncontrolled_domains: int = 2
    min_consequence_intensity: float = 0.25
    min_independent_channels: int = 2

    def add(self, domain: RealityDomain) -> None:
        self.domains.append(domain)

    def uncontrolled_domains(self) -> list[RealityDomain]:
        return [d for d in self.domains if d.control_level == ControlLevel.NONE]

    def meaningful_domains(self) -> list[RealityDomain]:
        return [
            d
            for d in self.domains
            if d.consequence_intensity >= self.min_consequence_intensity
            and d.contact_frequency > 0.0
        ]

    def independent_channels(self) -> list[RealityDomain]:
        return [
            d
            for d in self.domains
            if d.independent_incentives
            and d.independent_failure_modes
            and d.independent_power_structures
            and d.consequence_intensity >= self.min_consequence_intensity
        ]

    def to_dict(self) -> dict[str, Any]:
        return {
            "domains": [d.to_dict() for d in self.domains],
            "min_uncontrolled_domains": self.min_uncontrolled_domains,
            "min_consequence_intensity": self.min_consequence_intensity,
            "min_independent_channels": self.min_independent_channels,
        }


def compute_reality_diversity_index(registry: RealitySurfaceRegistry) -> float:
    """
    RDI — diversity of consequential reality encounters.

    Combines domain count, control spread, and intensity variance.
    """
    domains = registry.meaningful_domains()
    if not domains:
        return 0.0

    control_spread = len({d.control_level for d in domains}) / 3.0
    intensities = [d.consequence_intensity for d in domains]
    mean_intensity = sum(intensities) / len(intensities)
    variance = sum((value - mean_intensity) ** 2 for value in intensities) / len(intensities)
    intensity_diversity = min(1.0, variance * 4.0)

    domain_factor = min(1.0, len(domains) / max(1, registry.min_independent_channels + 1))
    return round((0.4 * domain_factor) + (0.3 * control_spread) + (0.3 * intensity_diversity), 4)


def check_k13_reality_surface_preservation(registry: RealitySurfaceRegistry) -> None:
    """K13: meaningful exposure to external domains the system does not control."""
    uncontrolled = registry.uncontrolled_domains()
    meaningful_uncontrolled = [
        d for d in uncontrolled if d.consequence_intensity >= registry.min_consequence_intensity
    ]
    if len(meaningful_uncontrolled) < registry.min_uncontrolled_domains:
        raise ConstitutionalError(
            f"K13 violation: uncontrolled reality surfaces below threshold "
            f"({len(meaningful_uncontrolled)} < {registry.min_uncontrolled_domains})"
        )

    symbolic_only = [
        d
        for d in registry.domains
        if d.control_level == ControlLevel.NONE and d.consequence_intensity < registry.min_consequence_intensity
    ]
    if symbolic_only and not meaningful_uncontrolled:
        raise ConstitutionalError(
            "K13 violation: external domains decayed to symbolic-only consequence intensity"
        )


def check_k14_anti_domestication(
    rdi_before: float,
    rdi_after: float,
    *,
    tolerance: float = 1e-9,
) -> None:
    """K14: governance must not systematically reduce reality encounter diversity."""
    if rdi_after + tolerance < rdi_before:
        raise ConstitutionalError(
            f"K14 violation: Reality Diversity Index decreased ({rdi_before:.4f} -> {rdi_after:.4f})"
        )


def check_k15_reality_diversity_requirement(registry: RealitySurfaceRegistry) -> None:
    """K15: maintain multiple independent consequence-generating environments."""
    channels = registry.independent_channels()
    if len(channels) < registry.min_independent_channels:
        raise ConstitutionalError(
            f"K15 violation: independent consequence channels below minimum "
            f"({len(channels)} < {registry.min_independent_channels})"
        )


def assert_reality_contact_layer(registry: RealitySurfaceRegistry) -> dict[str, float]:
    """Run K13–K15 checks; return RDI snapshot."""
    rdi = compute_reality_diversity_index(registry)
    check_k13_reality_surface_preservation(registry)
    check_k15_reality_diversity_requirement(registry)
    return {"rdi": rdi, "domain_count": float(len(registry.domains))}

"""Reality Access Index (RAI) — composite reality reachability metric."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.crk1.reality_contact_layer import RealitySurfaceRegistry, compute_reality_diversity_index


@dataclass(frozen=True)
class RAIWeights:
    """Kernel-defined weights for RAI components."""

    rdi: float = 0.35
    ce: float = 0.25
    se: float = 0.25
    r_ext: float = 0.15

    def normalized(self) -> "RAIWeights":
        total = self.rdi + self.ce + self.se + self.r_ext
        if total <= 0:
            return RAIWeights(0.25, 0.25, 0.25, 0.25)
        return RAIWeights(
            rdi=self.rdi / total,
            ce=self.ce / total,
            se=self.se / total,
            r_ext=self.r_ext / total,
        )


def compute_reality_access_index(
    *,
    rdi: float,
    ce: float,
    se: float,
    registry: RealitySurfaceRegistry | None = None,
    external_domain_count: int | None = None,
    weights: RAIWeights | None = None,
) -> float:
    """
    RAI = w1·RDI + w2·CE + w3·SE + w4·R_ext

    R_ext is normalized external domain count (0–1) from registry when provided.
    """
    w = (weights or RAIWeights()).normalized()
    if external_domain_count is None:
        if registry is None:
            r_ext_norm = 0.0
        else:
            ext = registry.uncontrolled_domains()
            n_min = max(1, registry.min_uncontrolled_domains)
            r_ext_norm = min(1.0, len(ext) / n_min)
    else:
        r_ext_norm = min(1.0, float(external_domain_count))

    rdi_clamped = max(0.0, min(1.0, rdi))
    ce_clamped = max(0.0, min(1.0, ce))
    se_clamped = max(0.0, min(1.0, se))

    return round(
        w.rdi * rdi_clamped + w.ce * ce_clamped + w.se * se_clamped + w.r_ext * r_ext_norm,
        4,
    )


def compute_rai_from_registry(
    registry: RealitySurfaceRegistry,
    *,
    ce: float,
    se: float,
    weights: RAIWeights | None = None,
) -> dict[str, float]:
    rdi = compute_reality_diversity_index(registry)
    rai = compute_reality_access_index(
        rdi=rdi,
        ce=ce,
        se=se,
        registry=registry,
        weights=weights,
    )
    return {"rdi": rdi, "ce": ce, "se": se, "rai": rai}


def rai_drift_negative(rai_series: list[float], *, window: int = 3) -> bool:
    """RAI drift trigger — sustained negative dRAI/dt."""
    if len(rai_series) < window + 1:
        return False
    for index in range(len(rai_series) - window):
        if all(rai_series[index + offset + 1] < rai_series[index + offset] for offset in range(window)):
            return True
    return False

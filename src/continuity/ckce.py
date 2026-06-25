"""CKCE-1 cross-kernel coherence engine."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

from src.continuity.wave_math import WaveSignature


@dataclass(frozen=True, slots=True)
class CKCEThresholds:
    c_min: float = 0.80
    tau: float = 0.80
    phi_max: float = 0.10
    r_max: float = 0.10


@dataclass(frozen=True, slots=True)
class CrossKernelCoherence:
    C_comp: float
    C_identity: float
    C_pair: float
    delta_phi: float
    delta_R: float
    continuity_ok: bool
    violations: tuple[str, ...] = ()

    def to_dict(self) -> dict[str, Any]:
        return {
            "C_comp": self.C_comp,
            "C_identity": self.C_identity,
            "C_pair": self.C_pair,
            "delta_phi": self.delta_phi,
            "delta_R": self.delta_R,
            "continuity_ok": self.continuity_ok,
            "violations": list(self.violations),
        }


def evaluate_cross_kernel_coherence(
    computational: WaveSignature,
    identity: WaveSignature,
    *,
    thresholds: CKCEThresholds | None = None,
) -> CrossKernelCoherence:
    """Enforce the Identity-Computation Coupling Theorem over two wave signatures."""

    active = thresholds or CKCEThresholds()
    c_comp = round(float(computational.coherence), 10)
    c_identity = round(float(identity.coherence), 10)
    c_pair = round(c_comp * c_identity, 10)
    delta_phi = round(abs(float(computational.phase) - float(identity.phase)), 10)
    delta_r = round(abs(float(computational.resonance) - float(identity.resonance)), 10)

    violations: list[str] = []
    if c_comp < active.c_min:
        violations.append("ckce.computational_coherence_below_min")
    if c_identity < active.c_min:
        violations.append("ckce.identity_coherence_below_min")
    if c_pair < active.tau:
        violations.append("ckce.pair_coherence_below_tau")
    if delta_phi > active.phi_max:
        violations.append("ckce.phase_drift_exceeds_max")
    if delta_r > active.r_max:
        violations.append("ckce.resonance_delta_exceeds_max")

    return CrossKernelCoherence(
        C_comp=c_comp,
        C_identity=c_identity,
        C_pair=c_pair,
        delta_phi=delta_phi,
        delta_R=delta_r,
        continuity_ok=not violations,
        violations=tuple(violations),
    )

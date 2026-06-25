"""CE-1 specification — unified continuity engine axes, thresholds, and phases."""

from __future__ import annotations

from typing import Literal

CE1_REFERENCE = "Continuity Engine CE-1"
CE1_VERSION = "1.0"

# Three axes
TRANSMISSION_AXIS = "propagation"
REALITY_AXIS = "convergence"
CONTINUITY_AXIS = "accumulation"

AXIS_DEFINITIONS: dict[str, str] = {
    TRANSMISSION_AXIS: "Can ideas spread between minds? (vitality)",
    REALITY_AXIS: "Do independent minds rediscover similar structures? (reality-tracking)",
    CONTINUITY_AXIS: "Do insights build on each other across generations? (compounding)",
}

# Thresholds (CE-1)
PT3_MIN_PROPAGATION = 3
CT2_MIN_CONVERGENCE = 2
CT2_MIN_DOMAINS = 2
MAT3_MIN_ACCUMULATION = 3

# CE-Forecast-1 weights
CE_FORECAST_ALPHA = 0.2  # propagation
CE_FORECAST_BETA = 0.3  # convergence
CE_FORECAST_GAMMA = 0.4  # accumulation
CE_FORECAST_DELTA = 0.3  # chain length
CE_FORECAST_STEWARDSHIP_THRESHOLD = 0.75

ContinuityPhase = Literal[
    "propagation",
    "convergence",
    "accumulation",
    "steward_emergence",
    "stewardability",
]

COMPOUNDING_CURVE_PHASES: tuple[tuple[ContinuityPhase, str], ...] = (
    ("propagation", "Phase 1 — ideas spread between minds."),
    ("convergence", "Phase 2 — independent rediscovery of structures."),
    ("accumulation", "Phase 3 — insights compound across generations."),
    ("steward_emergence", "Phase 4 — governance of framework evolution."),
    ("stewardability", "Phase 5 — stewards without founders."),
)

# Continuity kernel invariants (K1–K3)
KERNEL_K1_IDENTITY_COHERENCE = (
    "K1 — Identity Coherence: extensions remain recognizably part of the lineage."
)
KERNEL_K2_GENERATIVE_GRAMMAR = (
    "K2 — Generative Grammar: ideas carry structure that enables extension."
)
KERNEL_K3_INTEGRABILITY = (
    "K3 — Integrability: new insights strengthen the lineage, not fragment it."
)

CONTINUITY_KERNEL_INVARIANTS: tuple[str, ...] = (
    KERNEL_K1_IDENTITY_COHERENCE,
    KERNEL_K2_GENERATIVE_GRAMMAR,
    KERNEL_K3_INTEGRABILITY,
)

COMPOUNDING_DOMINANCE_NOTE = (
    "Continuity becomes self-sustaining when A(t) grows faster than P(t) + C(t)."
)

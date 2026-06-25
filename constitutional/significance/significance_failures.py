"""Significance and decision-environment failure taxonomy (Q-F, Q-EC)."""

from enum import Enum

QF_SURFACE_COUNT = 6
QEC_SURFACE_COUNT = 5


class SignificanceFailureClass(str, Enum):
    UNRANKED_CORE = "Q-F1 UnrankedCore"
    MISRANKED_CORE = "Q-F2 MisrankedCore"
    TIER_BLOAT = "Q-F3 TierBloat"
    PRIORITY_INVERSION = "Q-F4 PriorityInversion"
    SIGNIFICANCE_AMNESIA = "Q-F5 SignificanceAmnesia"
    SIGNIFICANCE_DRIFT = "Q-F6 SignificanceDrift"


class DecisionEnvironmentFailure(str, Enum):
    CONTEXT_LOSS = "Q-EC1 ContextLoss"
    CONTEXT_MISALIGNMENT = "Q-EC2 ContextMisalignment"
    CONTEXT_DRIFT = "Q-EC3 ContextDrift"
    CONTEXT_FOSSILIZATION = "Q-EC4 ContextFossilization"
    CONTEXT_BLINDNESS = "Q-EC5 ContextBlindness"


def qf_surface_code(qf: SignificanceFailureClass) -> str:
    return qf.value.split()[0]

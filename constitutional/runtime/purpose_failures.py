"""Purpose-failure taxonomy — Periodic Table of Purpose Failure (P-F1 … P-F10)."""

from enum import Enum


class PurposeFailureClass(str, Enum):
    PURPOSE_DRIFT = "P-F1 PurposeDrift"
    INVARIANT_DILUTION = "P-F2 InvariantDilution"
    MISSION_AMNESIA = "P-F3 MissionAmnesia"
    TELOS_INVERSION = "P-F4 TelosInversion"
    CULTURAL_DISCONTINUITY = "P-F5 CulturalDiscontinuity"
    PURPOSE_FRAGMENTATION = "P-F6 PurposeFragmentation"
    PURPOSE_AMBIGUITY = "P-F7 PurposeAmbiguity"
    PURPOSE_CAPTURE = "P-F8 PurposeCapture"
    PURPOSE_DEGENERATION = "P-F9 PurposeDegeneration"
    PURPOSE_CORRUPTION = "P-F10 PurposeCorruption"


ALL_PURPOSE_FAILURES: frozenset[PurposeFailureClass] = frozenset(PurposeFailureClass)

PF_SURFACE_COUNT = 10

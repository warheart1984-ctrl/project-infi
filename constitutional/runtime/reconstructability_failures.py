# constitutional_substrate/reconstructability_failures.py
"""Universal taxonomy — Periodic Table of Reconstructability Failure (R-F1 … R-F10)."""

from enum import Enum


class ReconstructabilityFailureClass(str, Enum):
    EVIDENCE_LOSS = "R-F1 EvidenceLoss"
    STATE_LOSS = "R-F2 StateLoss"
    LINEAGE_BREAK = "R-F3 LineageBreak"
    AUTHORITY_OPACITY = "R-F4 AuthorityOpacity"
    ACCOUNTABILITY_EROSION = "R-F5 AccountabilityErosion"
    REMEDIATION_AMNESIA = "R-F6 RemediationAmnesia"
    LEARNING_AMNESIA = "R-F7 LearningAmnesia"
    STEWARD_DISCONTINUITY = "R-F8 StewardDiscontinuity"
    SEMANTIC_DRIFT = "R-F9 SemanticDrift"
    BOUNDARY_CONFUSION = "R-F10 BoundaryConfusion"


ALL_RECONSTRUCTABILITY_FAILURES: frozenset[ReconstructabilityFailureClass] = frozenset(
    ReconstructabilityFailureClass
)

"""Runtime registry — which R-F* threats each runtime exists to resist."""

from __future__ import annotations

from typing import ClassVar

from constitutional.runtime.burnout_runtime import BurnoutRuntime
from constitutional.runtime.personal_continuity_runtime import PersonalContinuityRuntime
from constitutional.hiddenness.hiddenness_failures import HiddennessFailureClass
from constitutional.runtime.purpose_failures import PurposeFailureClass
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass

RF = ReconstructabilityFailureClass


class TruthRuntime:
    """Resists evidence loss and semantic drift."""

    resists: ClassVar[list[ReconstructabilityFailureClass]] = [
        RF.EVIDENCE_LOSS,
        RF.SEMANTIC_DRIFT,
    ]


class SovereigntyRuntime:
    resists: ClassVar[list[ReconstructabilityFailureClass]] = [
        RF.AUTHORITY_OPACITY,
        RF.ACCOUNTABILITY_EROSION,
        RF.STEWARD_DISCONTINUITY,
    ]


class InstitutionalRuntime:
    resists: ClassVar[list[ReconstructabilityFailureClass]] = [
        RF.LINEAGE_BREAK,
        RF.BOUNDARY_CONFUSION,
    ]


class ContinuityRuntime:
    resists: ClassVar[list[ReconstructabilityFailureClass]] = [
        RF.STATE_LOSS,
        RF.LINEAGE_BREAK,
        RF.LEARNING_AMNESIA,
    ]


RUNTIME_CHARTER: dict[str, list[ReconstructabilityFailureClass]] = {
    "TruthRuntime": TruthRuntime.resists,
    "SovereigntyRuntime": SovereigntyRuntime.resists,
    "InstitutionalRuntime": InstitutionalRuntime.resists,
    "ContinuityRuntime": ContinuityRuntime.resists,
    "PersonalContinuityRuntime": PersonalContinuityRuntime.resists,
    "BurnoutRuntime": BurnoutRuntime.resists,
    "PersonalConstitutionalStateRuntime": [
        RF.STEWARD_DISCONTINUITY,
        RF.EVIDENCE_LOSS,
        RF.LINEAGE_BREAK,
    ],
    "OperatorRuntime": [
        RF.EVIDENCE_LOSS,
        RF.LINEAGE_BREAK,
        RF.REMEDIATION_AMNESIA,
    ],
    "ReconstructabilityFitnessRuntime": list(ReconstructabilityFailureClass),
    "MissionFidelityRuntime": list(PurposeFailureClass),
    "MissionFidelityInteractiveRuntime": list(PurposeFailureClass),
    "HiddennessRuntime": list(HiddennessFailureClass),
    "HiddennessRuntimeV2": list(HiddennessFailureClass),
}


def charter_for(runtime_name: str) -> list[ReconstructabilityFailureClass]:
    return list(RUNTIME_CHARTER.get(runtime_name, []))

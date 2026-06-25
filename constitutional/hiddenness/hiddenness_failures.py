"""Hiddenness-failure taxonomy — Periodic Table of Hiddenness Failure (H-F1 … H-F10)."""

from enum import Enum


class HiddennessFailureClass(str, Enum):
    HIDDEN_ASSUMPTION = "H-F1 HiddenAssumption"
    HIDDEN_INVARIANT = "H-F2 HiddenInvariant"
    HIDDEN_RATIONALE = "H-F3 HiddenRationale"
    HIDDEN_PURPOSE_FRAGMENT = "H-F4 HiddenPurposeFragment"
    HIDDEN_AUTHORITY = "H-F5 HiddenAuthority"
    HIDDEN_DEPENDENCY = "H-F6 HiddenDependency"
    HIDDEN_CONTEXT = "H-F7 HiddenContext"
    HIDDEN_CONSTRAINT = "H-F8 HiddenConstraint"
    HIDDEN_MEANING = "H-F9 HiddenMeaning"
    HIDDEN_STEWARD_KNOWLEDGE = "H-F10 HiddenStewardKnowledge"


ALL_HIDDENNESS_FAILURES: frozenset[HiddennessFailureClass] = frozenset(HiddennessFailureClass)

HF_SURFACE_COUNT = 10


def hf_surface_code(hf: HiddennessFailureClass) -> str:
    """Short H-F surface code for receipts (e.g. ``H-F1``)."""
    return hf.value.split()[0]

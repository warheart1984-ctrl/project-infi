"""Hiddenness as universal precursor — the substrate beneath R-F, S-F, and P-F symptoms."""

from __future__ import annotations

from constitutional.core.articles import (
    ARTICLE_P_REFERENCE,
    ARTICLE_R_REFERENCE,
    ARTICLE_S_REFERENCE,
    HIDDENNESS_CONSTITUTIONAL_ROLE,
    HIDDENNESS_PRESSURE_QUESTION,
)
from constitutional.hiddenness.hiddenness_failures import HiddennessFailureClass as HF
from constitutional.runtime.purpose_failures import PurposeFailureClass as PF
from constitutional.runtime.reconstructability_failures import ReconstructabilityFailureClass as RF

__all__ = [
    "COLD_START_AS_HIDDENNESS_DETECTOR",
    "HF_TO_PF",
    "HF_TO_RF",
    "HF_TO_SURVIVABILITY_SYMPTOMS",
    "HIDDENNESS_CONSTITUTIONAL_ROLE",
    "HIDDENNESS_PRESSURE_QUESTION",
    "HIDDENNESS_PRECurses_PURPOSE",
    "HIDDENNESS_PRECurses_RECONSTRUCTABILITY",
    "HIDDENNESS_PRECurses_SURVIVABILITY",
    "downstream_pf_threats",
    "downstream_rf_threats",
]

HIDDENNESS_PRECurses_RECONSTRUCTABILITY = ARTICLE_R_REFERENCE
HIDDENNESS_PRECurses_SURVIVABILITY = ARTICLE_S_REFERENCE
HIDDENNESS_PRECurses_PURPOSE = ARTICLE_P_REFERENCE

# H-F → R-F: hidden substrate that makes reconstructability failures possible.
HF_TO_RF: dict[HF, list[RF]] = {
    HF.HIDDEN_ASSUMPTION: [RF.REMEDIATION_AMNESIA, RF.LEARNING_AMNESIA, RF.STEWARD_DISCONTINUITY],
    HF.HIDDEN_INVARIANT: [RF.SEMANTIC_DRIFT, RF.BOUNDARY_CONFUSION],
    HF.HIDDEN_RATIONALE: [RF.REMEDIATION_AMNESIA, RF.LEARNING_AMNESIA],
    HF.HIDDEN_PURPOSE_FRAGMENT: [RF.SEMANTIC_DRIFT],
    HF.HIDDEN_AUTHORITY: [RF.AUTHORITY_OPACITY, RF.ACCOUNTABILITY_EROSION],
    HF.HIDDEN_DEPENDENCY: [RF.STEWARD_DISCONTINUITY, RF.EVIDENCE_LOSS],
    HF.HIDDEN_CONTEXT: [RF.SEMANTIC_DRIFT, RF.LEARNING_AMNESIA],
    HF.HIDDEN_CONSTRAINT: [RF.BOUNDARY_CONFUSION],
    HF.HIDDEN_MEANING: [RF.SEMANTIC_DRIFT],
    HF.HIDDEN_STEWARD_KNOWLEDGE: [RF.STEWARD_DISCONTINUITY, RF.EVIDENCE_LOSS],
}

# H-F → P-F: hidden substrate that makes purpose failures possible.
HF_TO_PF: dict[HF, list[PF]] = {
    HF.HIDDEN_ASSUMPTION: [PF.PURPOSE_DRIFT, PF.PURPOSE_AMBIGUITY],
    HF.HIDDEN_INVARIANT: [PF.INVARIANT_DILUTION],
    HF.HIDDEN_RATIONALE: [PF.INVARIANT_DILUTION, PF.PURPOSE_DEGENERATION],
    HF.HIDDEN_PURPOSE_FRAGMENT: [PF.MISSION_AMNESIA, PF.PURPOSE_FRAGMENTATION],
    HF.HIDDEN_AUTHORITY: [PF.PURPOSE_CAPTURE, PF.PURPOSE_FRAGMENTATION],
    HF.HIDDEN_DEPENDENCY: [PF.CULTURAL_DISCONTINUITY, PF.PURPOSE_CAPTURE],
    HF.HIDDEN_CONTEXT: [PF.CULTURAL_DISCONTINUITY, PF.MISSION_AMNESIA],
    HF.HIDDEN_CONSTRAINT: [PF.PURPOSE_AMBIGUITY, PF.PURPOSE_FRAGMENTATION],
    HF.HIDDEN_MEANING: [PF.PURPOSE_AMBIGUITY, PF.TELOS_INVERSION],
    HF.HIDDEN_STEWARD_KNOWLEDGE: [PF.CULTURAL_DISCONTINUITY, PF.MISSION_AMNESIA],
}

# Survivability expresses hiddenness through R-F surfaces plus founder/steward metrics.
HF_TO_SURVIVABILITY_SYMPTOMS: dict[HF, list[str]] = {
    HF.HIDDEN_ASSUMPTION: ["founder_dependency", "implicit_assumptions_required"],
    HF.HIDDEN_AUTHORITY: ["authority_chain_incomplete", "founder_exclusive_authority"],
    HF.HIDDEN_DEPENDENCY: ["founder_dependency", "steward_independence_low"],
    HF.HIDDEN_STEWARD_KNOWLEDGE: ["cold_start_failure", "knowledge_not_externalized"],
    HF.HIDDEN_CONTEXT: ["cultural_discontinuity", "mission_amnesia"],
    HF.HIDDEN_PURPOSE_FRAGMENT: ["purpose_continuity_breach", "mission_amnesia"],
}

# Cold-Start Steward Test is the first hiddenness detector (Section 6 formalizes it).
COLD_START_AS_HIDDENNESS_DETECTOR: dict[str, HF] = {
    "unanswered_steward_question": HF.HIDDEN_ASSUMPTION,
    "founder_only_explanation": HF.HIDDEN_DEPENDENCY,
    "missing_rationale": HF.HIDDEN_RATIONALE,
    "unclear_invariant": HF.HIDDEN_INVARIANT,
    "missing_lineage_link": HF.HIDDEN_DEPENDENCY,
    "missing_purpose_fragment": HF.HIDDEN_PURPOSE_FRAGMENT,
    "implicit_authority": HF.HIDDEN_AUTHORITY,
    "missing_context": HF.HIDDEN_CONTEXT,
}


def downstream_rf_threats(hf_surfaces: list[HF]) -> list[RF]:
    seen: set[RF] = set()
    ordered: list[RF] = []
    for hf in hf_surfaces:
        for rf in HF_TO_RF.get(hf, []):
            if rf not in seen:
                seen.add(rf)
                ordered.append(rf)
    return ordered


def downstream_pf_threats(hf_surfaces: list[HF]) -> list[PF]:
    seen: set[PF] = set()
    ordered: list[PF] = []
    for hf in hf_surfaces:
        for pf in HF_TO_PF.get(hf, []):
            if pf not in seen:
                seen.add(pf)
                ordered.append(pf)
    return ordered

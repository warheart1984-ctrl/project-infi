"""SSDE-1 — Successor Surpassment Detection Engine."""

from __future__ import annotations

from typing import Literal

from pydantic import BaseModel, Field

from src.continuity.css.fap import FounderInsight, SuccessorInsight
from src.continuity.css.spec import SSDE1_FORMULA
from src.cos1.continuity_engine.ce_json_schema import ContinuityEngineEventLog

SSDE1_REFERENCE = "Successor Surpassment Detection Engine SSDE-1"

SurpassmentSignature = Literal["A3", "A4", "NONE"]


class SSDE1Assessment(BaseModel):
    reference: str = SSDE1_REFERENCE
    formula: str = SSDE1_FORMULA
    surpassment_detected: bool = False
    qualifying_events: list[str] = Field(default_factory=list)
    explanatory_gain: float = 0.0
    integration_exceeds_founder: bool = False
    blockers: list[str] = Field(default_factory=list)


def assess_ssde1_from_ce_log(
    ce_log: ContinuityEngineEventLog,
    founder: FounderInsight,
) -> SSDE1Assessment:
    """Detect surpassment from A3/A4 accumulation events in the CE log."""
    qualifying: list[str] = []
    max_gain = 0.0
    max_integration = 0.0

    for event in ce_log.accumulation_events():
        sig = event.accumulation.signature
        if sig not in ("A3", "A4"):
            continue
        if not event.insight.lineage_compatible:
            continue
        if event.insight.novelty_level == "ECHO":
            continue

        primitive_count = len(event.insight.structural_alignment)
        gain = 0.5 + 0.1 * primitive_count
        if sig == "A4":
            gain += 0.3
        if event.accumulation.returns_stronger:
            gain += 0.2

        integration = gain + 0.1 * primitive_count
        max_gain = max(max_gain, gain)
        max_integration = max(max_integration, integration)
        qualifying.append(event.event_id)

    blockers: list[str] = []
    has_a3_a4 = bool(qualifying)
    e_gain = max_gain > 0
    exceeds_founder = max_integration > founder.integration_score

    if not has_a3_a4:
        blockers.append("No A3 or A4 accumulation event from successor.")
    if not e_gain:
        blockers.append("No explanatory gain detected (E_gain > 0).")
    if not exceeds_founder:
        blockers.append("Integration does not exceed founder model (I > F).")

    met = has_a3_a4 and e_gain and exceeds_founder

    return SSDE1Assessment(
        surpassment_detected=met,
        qualifying_events=qualifying,
        explanatory_gain=max_gain,
        integration_exceeds_founder=exceeds_founder,
        blockers=blockers if not met else [],
    )


def assess_ssde1(
    successor: SuccessorInsight,
    founder: FounderInsight,
) -> SSDE1Assessment:
    """Direct surpassment assessment from successor/founder insight pair."""
    has_a3_a4 = successor.accumulation_signature in ("A3", "A4")
    e_gain = successor.explanatory_gain > 0
    exceeds = successor.integration_score > founder.integration_score
    survives = successor.survives_critique

    blockers: list[str] = []
    if not has_a3_a4:
        blockers.append("Successor insight is not A3 or A4.")
    if not e_gain:
        blockers.append("Explanatory gain must be positive.")
    if not exceeds:
        blockers.append("Successor integration must exceed founder.")
    if not survives:
        blockers.append("Insight must survive critique.")

    met = has_a3_a4 and e_gain and exceeds and survives

    return SSDE1Assessment(
        surpassment_detected=met,
        qualifying_events=[successor.id] if met else [],
        explanatory_gain=successor.explanatory_gain,
        integration_exceeds_founder=exceeds,
        blockers=blockers if not met else [],
    )

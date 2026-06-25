"""JPSS convergence experiment — independent rediscovery without exposure."""

from __future__ import annotations

import re
from typing import Literal

from pydantic import BaseModel, Field

InsightClassification = Literal["CONVERGENCE", "NOISE"]

_CONVERGENCE_HINTS = re.compile(
    r"\b(drift|threshold|calibrat|slow change|silent|lose their way|judgment|preserv|continuity)\b",
    re.IGNORECASE,
)


class ConvergenceParticipant(BaseModel):
    id: str
    domain: str
    prior_jpss_exposure: bool = False


class RawConvergenceResponse(BaseModel):
    participant_id: str
    text: str


class ClassifiedConvergenceInsight(BaseModel):
    participant_id: str
    domain: str
    classification: InsightClassification
    lineage_compatible: bool = False
    grammar_tags: list[str] = Field(default_factory=list)


class ConvergenceSummary(BaseModel):
    convergence_count: int
    convergence_domains: list[str]
    noise_count: int


def _extract_grammar_tags(text: str) -> list[str]:
    lowered = text.lower()
    tags: list[str] = []
    if "drift" in lowered:
        tags.append("drift")
    if "threshold" in lowered:
        tags.append("threshold")
    if "calibrat" in lowered:
        tags.append("calibration")
    if "judgment" in lowered or "judgement" in lowered:
        tags.append("judgment")
    if "preserv" in lowered:
        tags.append("preservation")
    if "continuity" in lowered or "lose their way" in lowered:
        tags.append("continuity")
    if "silent" in lowered or "slow change" in lowered:
        tags.append("silent_change")
    return tags


def classify_convergence_insight(
    response: RawConvergenceResponse,
    participant: ConvergenceParticipant,
) -> ClassifiedConvergenceInsight:
    """Classify a domain-neutral response (CDP-1 placeholder — rule-based proxy)."""
    lineage_compatible = bool(_CONVERGENCE_HINTS.search(response.text))
    grammar_tags = _extract_grammar_tags(response.text)
    if not participant.prior_jpss_exposure and lineage_compatible:
        classification: InsightClassification = "CONVERGENCE"
    else:
        classification = "NOISE"

    return ClassifiedConvergenceInsight(
        participant_id=participant.id,
        domain=participant.domain,
        classification=classification,
        lineage_compatible=lineage_compatible,
        grammar_tags=grammar_tags,
    )


def summarize_convergence(insights: list[ClassifiedConvergenceInsight]) -> ConvergenceSummary:
    convergence = [i for i in insights if i.classification == "CONVERGENCE"]
    domains = sorted({i.domain for i in convergence})
    return ConvergenceSummary(
        convergence_count=len(convergence),
        convergence_domains=domains,
        noise_count=len(insights) - len(convergence),
    )


def classified_to_dual_origin_insights(
    classified: list[ClassifiedConvergenceInsight],
    *,
    id_prefix: str = "conv",
) -> list:
    """Map convergence experiment rows to DualOriginInsight inputs."""
    from constitutional.jpss.dual_origin_validation import DualOriginInsight

    rows: list[DualOriginInsight] = []
    for index, item in enumerate(classified):
        if item.classification != "CONVERGENCE":
            continue
        rows.append(
            DualOriginInsight(
                id=f"{id_prefix}-{index}",
                source_id=item.participant_id,
                domain=item.domain,
                exposed_to_jpss=False,
                lineage_compatible=item.lineage_compatible,
                grammar_tags=item.grammar_tags,
            )
        )
    return rows

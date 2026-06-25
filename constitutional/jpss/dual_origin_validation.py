"""DOV-T1 — dual-origin validation for JPSS propagation and convergence."""

from __future__ import annotations

from pydantic import BaseModel, Field

from constitutional.jpss.dov_t1_spec import (
    DOV_T1_C1_MIN_CONVERGENCE,
    DOV_T1_C2_MIN_CONVERGENCE_DOMAINS,
    DOV_T1_K1_MIN_SHARED_GRAMMAR_TOKENS,
    DOV_T1_P1_MIN_PROPAGATION,
    DOV_T1_P2_MIN_BIDIRECTIONAL,
    JPSS_CONCEPTUAL_GRAMMAR,
)


class DualOriginInsight(BaseModel):
    """Recorded insight for propagation or convergence analysis."""

    id: str
    source_id: str
    domain: str
    exposed_to_jpss: bool
    lineage_compatible: bool
    bidirectional: bool = False
    grammar_tags: list[str] = Field(default_factory=list)
    incompatible_fork: bool = False


class DOVT1Result(BaseModel):
    reached: bool
    reasons: list[str] = Field(default_factory=list)
    propagation_count: int = 0
    bidirectional_count: int = 0
    convergence_count: int = 0
    convergence_domain_count: int = 0
    shared_grammar_tokens: list[str] = Field(default_factory=list)


def _grammar_tokens(insights: list[DualOriginInsight]) -> set[str]:
    tokens: set[str] = set()
    for insight in insights:
        for tag in insight.grammar_tags:
            normalized = tag.strip().lower().replace(" ", "_")
            if normalized:
                tokens.add(normalized)
    return tokens


def evaluate_dov_t1(insights: list[DualOriginInsight]) -> DOVT1Result:
    """Return whether P1+P2+C1+C2+K1+K2 hold for the insight set."""
    reasons: list[str] = []

    propagation = [
        i for i in insights if i.exposed_to_jpss and i.lineage_compatible and not i.incompatible_fork
    ]
    convergence = [
        i
        for i in insights
        if not i.exposed_to_jpss and i.lineage_compatible and not i.incompatible_fork
    ]
    bidirectional = [i for i in propagation if i.bidirectional]
    convergence_domains = {i.domain for i in convergence}

    if len(propagation) < DOV_T1_P1_MIN_PROPAGATION:
        reasons.append(
            f"P1: insufficient propagation insights (need ≥ {DOV_T1_P1_MIN_PROPAGATION}, got {len(propagation)})."
        )
    if len(bidirectional) < DOV_T1_P2_MIN_BIDIRECTIONAL:
        reasons.append("P2: no bidirectional propagation event.")

    if len(convergence) < DOV_T1_C1_MIN_CONVERGENCE:
        reasons.append(
            f"C1: insufficient convergence insights (need ≥ {DOV_T1_C1_MIN_CONVERGENCE}, got {len(convergence)})."
        )
    if len(convergence_domains) < DOV_T1_C2_MIN_CONVERGENCE_DOMAINS:
        reasons.append(
            f"C2: convergence not observed across ≥ {DOV_T1_C2_MIN_CONVERGENCE_DOMAINS} domains "
            f"(got {len(convergence_domains)})."
        )

    propagation_grammar = _grammar_tokens(propagation) & JPSS_CONCEPTUAL_GRAMMAR
    convergence_grammar = _grammar_tokens(convergence) & JPSS_CONCEPTUAL_GRAMMAR
    shared_grammar = sorted(propagation_grammar & convergence_grammar)
    if len(shared_grammar) < DOV_T1_K1_MIN_SHARED_GRAMMAR_TOKENS:
        reasons.append(
            "K1: propagation and convergence do not share enough JPSS conceptual grammar "
            f"(need ≥ {DOV_T1_K1_MIN_SHARED_GRAMMAR_TOKENS} shared tokens)."
        )

    incompatible = [i for i in insights if i.incompatible_fork]
    if incompatible:
        reasons.append(
            f"K2: {len(incompatible)} incompatible fork(s) — identity-breaking divergence detected."
        )

    return DOVT1Result(
        reached=not reasons,
        reasons=reasons,
        propagation_count=len(propagation),
        bidirectional_count=len(bidirectional),
        convergence_count=len(convergence),
        convergence_domain_count=len(convergence_domains),
        shared_grammar_tokens=shared_grammar,
    )

"""UGR-MIT-1 — Meaning Invariance Theory fitness functional Mu(X)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Any

UGR_MIT_1_CANONICAL_TEXT = """UGR-MIT-1 — Meaning Invariance Theory
Class: Constitutional Invariant
Purpose: Ensure constitutional objects retain stable, operator-convergent meaning across epochs.

Mu(X) = w_purp*M_purp + w_cons*M_cons + w_stab*M_stab + w_intent*M_intent
Objects below Theta_MIT cannot influence governance meaningfully.
"""

MIT_1_CAPABILITY_ID = "UGR-MIT-1"
DEFAULT_THETA_MIT = 0.75

LAW_CANONICAL_MEANING: dict[str, str] = {
    "SIT-1": "Structure claims must be recoverable independent of representation or operator.",
    "GIT-1": "Generative laws must remain recoverable as structure families across operators.",
    "PIT-1": "Only laws whose generative fitness remains above threshold are admissible.",
}

LAW_INTENT_NOTES: dict[str, str] = {
    "SIT-1": "Origin: UGR/SIT-1.md — anchors structural equivalence for all downstream laws.",
    "GIT-1": "Origin: UGR/GIT-1.md — binds generative law recovery to SIT-1.",
    "PIT-1": "Origin: UGR/PIT-1.md — sovereign selection kernel over law fitness F(G).",
}


@dataclass
class MeaningComponents:
    M_purp: float
    M_cons: float
    M_stab: float
    M_intent: float

    def to_dict(self) -> dict[str, float]:
        return {
            "M_purp": round(self.M_purp, 6),
            "M_cons": round(self.M_cons, 6),
            "M_stab": round(self.M_stab, 6),
            "M_intent": round(self.M_intent, 6),
        }


@dataclass
class MeaningConfig:
    w_purp: float = 0.25
    w_cons: float = 0.25
    w_stab: float = 0.25
    w_intent: float = 0.25
    theta_mit: float = DEFAULT_THETA_MIT


@dataclass
class MeaningStrip:
    object_type: str
    object_id: str
    mu: float
    purpose: str
    canonical_meaning: str
    intent_note: str
    components: MeaningComponents
    ready: bool = True

    def to_dict(self) -> dict[str, Any]:
        return {
            "object_type": self.object_type,
            "object_id": self.object_id,
            "mu": round(self.mu, 6),
            "purpose": self.purpose,
            "canonical_meaning": self.canonical_meaning,
            "intent_note": self.intent_note,
            "components": self.components.to_dict(),
            "ready": self.ready,
        }


def clamp01(value: float) -> float:
    return max(0.0, min(1.0, value))


def compute_mu(components: MeaningComponents, cfg: MeaningConfig | None = None) -> float:
    config = cfg or MeaningConfig()
    mu = (
        config.w_purp * components.M_purp
        + config.w_cons * components.M_cons
        + config.w_stab * components.M_stab
        + config.w_intent * components.M_intent
    )
    return clamp01(mu)


def meaning_components_for_law(law_record: dict[str, Any]) -> MeaningComponents:
    law_id = str(law_record.get("law_id") or "")
    status = str(law_record.get("status") or "proposed")
    fitness = law_record.get("fitness") or {}
    history = fitness.get("history") or []
    domains = law_record.get("domains") or []

    admitted = status == "admitted"
    experimental = status == "experimental"
    history_depth = len(history)

    m_purp = 0.92 if law_id in LAW_CANONICAL_MEANING else 0.75
    m_cons = clamp01(0.7 + 0.05 * history_depth + (0.15 if admitted else 0.05))
    m_stab = clamp01(0.65 + 0.08 * history_depth + (0.2 if admitted else 0.1 if experimental else 0.0))
    m_intent = clamp01(0.72 + 0.04 * len(domains) + (0.16 if law_id in LAW_INTENT_NOTES else 0.0))

    return MeaningComponents(
        M_purp=m_purp,
        M_cons=m_cons,
        M_stab=m_stab,
        M_intent=m_intent,
    )


def build_law_meaning_strip(
    law_record: dict[str, Any],
    *,
    cfg: MeaningConfig | None = None,
) -> MeaningStrip:
    law_id = str(law_record.get("law_id") or "")
    components = meaning_components_for_law(law_record)
    mu = compute_mu(components, cfg)
    config = cfg or MeaningConfig()

    from src.continuity.comprehension_fitness import LAW_PURPOSE_TEXT

    purpose = LAW_PURPOSE_TEXT.get(law_id, f"Constitutional purpose of {law_id}.")
    canonical = LAW_CANONICAL_MEANING.get(law_id, purpose)
    intent = LAW_INTENT_NOTES.get(law_id, f"See Meaning Ledger entry for {law_id}.")

    return MeaningStrip(
        object_type="law",
        object_id=law_id,
        mu=mu,
        purpose=purpose,
        canonical_meaning=canonical,
        intent_note=intent,
        components=components,
        ready=mu >= config.theta_mit,
    )

"""Reference salience maps for Salience Judgment Test v1."""

from __future__ import annotations

from pydantic import BaseModel, Field

SALIENCE_JUDGMENT_PASS_SCORE = 0.67

SYNTHETIC_SALIENCE_SCENARIOS: dict[str, dict[str, str]] = {
    "scenario_override": {
        "title": "Emergency steward override proposed",
        "prompt": "What signals and risks should dominate attention?",
    },
    "scenario_context": {
        "title": "Seasonal context ledger update",
        "prompt": "Which cues are signal vs noise for constitutional interpretation?",
    },
}


class ReferenceSalienceMap(BaseModel):
    primary_signals: list[str] = Field(default_factory=list)
    secondary_signals: list[str] = Field(default_factory=list)
    ignored_signals: list[str] = Field(default_factory=list)
    false_signals: list[str] = Field(default_factory=list)
    risk_order: list[str] = Field(default_factory=list)


class StewardSalienceAnswer(BaseModel):
    scenario_id: str
    primary_signals: list[str] = Field(default_factory=list)
    secondary_signals: list[str] = Field(default_factory=list)
    ignored_signals: list[str] = Field(default_factory=list)
    risk_order: list[str] = Field(default_factory=list)
    steward_id: str = "steward"


_DEFAULT_REFERENCE_MAPS: dict[str, ReferenceSalienceMap] = {
    "scenario_override": ReferenceSalienceMap(
        primary_signals=[
            "latent authority concentration",
            "anti-corruption invariant",
            "emergency bypass scope",
        ],
        secondary_signals=["operational urgency", "incident severity"],
        ignored_signals=["convenience", "founder preference"],
        false_signals=["routine maintenance"],
        risk_order=[
            "constitutional capture",
            "hidden authority",
            "operational outage",
        ],
    ),
    "scenario_context": ReferenceSalienceMap(
        primary_signals=["interpretation frame", "invariant linkage", "continuity impact"],
        secondary_signals=["seasonal environmental shift"],
        ignored_signals=["cosmetic ritual change"],
        false_signals=["tier elevation without evidence"],
        risk_order=["context-to-doctrine drift", "lost interpretive continuity"],
    ),
}


def get_reference_salience_maps() -> dict[str, ReferenceSalienceMap]:
    return dict(_DEFAULT_REFERENCE_MAPS)

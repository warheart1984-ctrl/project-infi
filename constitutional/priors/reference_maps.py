"""Reference prior maps for Prior Judgment Test v1 — novelty under prior shift."""

from __future__ import annotations

from pydantic import BaseModel, Field

PRIOR_JUDGMENT_PASS_SCORE = 0.67

SYNTHETIC_PRIOR_SCENARIOS: dict[str, dict[str, str]] = {
    "scenario_prior_shift": {
        "title": "Environmental shift invalidates assumed stability",
        "prompt": "Which expectations transfer, invert, or require revision?",
    },
    "scenario_novel_failure": {
        "title": "Novel incident resembles historically feared failure",
        "prompt": "Which priors should dominate attention and which were wrongly dismissed?",
    },
}


class ReferencePriorMap(BaseModel):
    expected_signals: list[str] = Field(default_factory=list)
    expected_risks: list[str] = Field(default_factory=list)
    assumed_stabilities: list[str] = Field(default_factory=list)
    assumed_volatilities: list[str] = Field(default_factory=list)
    feared_failures: list[str] = Field(default_factory=list)
    ignored_possibilities: list[str] = Field(default_factory=list)
    false_expectations: list[str] = Field(default_factory=list)


class StewardPriorAnswer(BaseModel):
    scenario_id: str
    expected_signals: list[str] = Field(default_factory=list)
    expected_risks: list[str] = Field(default_factory=list)
    assumed_stabilities: list[str] = Field(default_factory=list)
    assumed_volatilities: list[str] = Field(default_factory=list)
    feared_failures: list[str] = Field(default_factory=list)
    ignored_possibilities: list[str] = Field(default_factory=list)
    steward_id: str = "steward"


_DEFAULT_REFERENCE_MAPS: dict[str, ReferencePriorMap] = {
    "scenario_prior_shift": ReferencePriorMap(
        expected_signals=[
            "latent authority concentration",
            "emergency bypass scope",
        ],
        expected_risks=["constitutional capture", "hidden authority"],
        assumed_stabilities=["tier 0 invariants", "anti-corruption invariant"],
        assumed_volatilities=["emergency bypass scope", "operational urgency"],
        feared_failures=["unchecked bypass", "founder override ritual"],
        ignored_possibilities=["cosmetic ritual change"],
        false_expectations=["routine maintenance window"],
    ),
    "scenario_novel_failure": ReferencePriorMap(
        expected_signals=["interpretation frame shift", "failure lineage match"],
        expected_risks=["context-to-doctrine drift", "lost interpretive continuity"],
        assumed_stabilities=["significance lattice anchors"],
        assumed_volatilities=["seasonal environmental shift"],
        feared_failures=["salience collapse", "prior blindness"],
        ignored_possibilities=["founder preference"],
        false_expectations=["one-off cosmetic outage"],
    ),
}


def get_reference_prior_maps() -> dict[str, ReferencePriorMap]:
    return dict(_DEFAULT_REFERENCE_MAPS)

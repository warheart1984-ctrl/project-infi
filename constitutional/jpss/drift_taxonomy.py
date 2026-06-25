"""JPSS Drift Taxonomy — full failure map of judgment (sub-type catalog)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Literal

from pydantic import BaseModel, Field

from constitutional.jpss.models import JPSSDriftClass, JPSSDriftFinding, JPSSDriftReport
from constitutional.jpss.spec import JPSS_DRIFT_CLASSES

JPSSDriftSubtype = Literal[
    "E-D1",
    "E-D2",
    "E-D3",
    "P-D1",
    "P-D2",
    "P-D3",
    "S-D1",
    "S-D2",
    "S-D3",
    "S-D4",
    "C-D1",
    "C-D2",
    "C-D3",
    "C-D4",
    "D-D1",
    "D-D2",
    "D-D3",
    "O-D1",
    "O-D2",
    "O-D3",
    "R-D1",
    "R-D2",
    "R-D3",
    "PR-D1",
    "PR-D2",
    "PR-D3",
    "PR-D4",
    "PR-D5",
]

JPSS_DRIFT_SUBTYPES: tuple[JPSSDriftSubtype, ...] = (
    "E-D1",
    "E-D2",
    "E-D3",
    "P-D1",
    "P-D2",
    "P-D3",
    "S-D1",
    "S-D2",
    "S-D3",
    "S-D4",
    "C-D1",
    "C-D2",
    "C-D3",
    "C-D4",
    "D-D1",
    "D-D2",
    "D-D3",
    "O-D1",
    "O-D2",
    "O-D3",
    "R-D1",
    "R-D2",
    "R-D3",
    "PR-D1",
    "PR-D2",
    "PR-D3",
    "PR-D4",
    "PR-D5",
)

SUBTYPE_TO_DRIFT_CLASS: dict[JPSSDriftSubtype, JPSSDriftClass | Literal["prior_drift"]] = {
    "E-D1": "environmental_drift",
    "E-D2": "environmental_drift",
    "E-D3": "environmental_drift",
    "P-D1": "perceptual_drift",
    "P-D2": "perceptual_drift",
    "P-D3": "perceptual_drift",
    "S-D1": "salience_drift",
    "S-D2": "salience_drift",
    "S-D3": "salience_drift",
    "S-D4": "salience_drift",
    "C-D1": "calibration_drift",
    "C-D2": "calibration_drift",
    "C-D3": "calibration_drift",
    "C-D4": "calibration_drift",
    "D-D1": "decision_drift",
    "D-D2": "decision_drift",
    "D-D3": "decision_drift",
    "O-D1": "outcome_drift",
    "O-D2": "outcome_drift",
    "O-D3": "outcome_drift",
    "R-D1": "reflection_drift",
    "R-D2": "reflection_drift",
    "R-D3": "reflection_drift",
    "PR-D1": "prior_drift",
    "PR-D2": "prior_drift",
    "PR-D3": "prior_drift",
    "PR-D4": "prior_drift",
    "PR-D5": "prior_drift",
}

JPSS_DRIFT_SUBTYPE_DESCRIPTIONS: dict[JPSSDriftSubtype, str] = {
    "E-D1": "Context Misclassification — treating high-risk as low-risk or vice versa.",
    "E-D2": "Constraint Blindness — ignoring hard constraints that shaped past decisions.",
    "E-D3": "Incentive Misalignment — misreading incentives that drove prior behavior.",
    "P-D1": "Channel Narrowing — fewer information channels considered than historically.",
    "P-D2": "Channel Flooding — overwhelming perception with noise, reducing effective signal intake.",
    "P-D3": "Source Reweighting — unjustified changes in trust toward specific sources.",
    "S-D1": "Salience Inversion — critical signals treated as noise; minor signals treated as primary.",
    "S-D2": "Salience Collapse — everything feels equally important; no clear prioritization.",
    "S-D3": "Salience Overfitting — copying historical salience without regard to changed environment.",
    "S-D4": "Salience Blindness — missing signals consistently salient in successful past judgments.",
    "C-D1": "Threshold Inflation — requiring more evidence than historically necessary, causing paralysis.",
    "C-D2": "Threshold Erosion — lowering thresholds without justification, causing reckless action.",
    "C-D3": "Risk Tolerance Flip — risk-seeking where historically risk-averse, or vice versa.",
    "C-D4": "Evidence Reweighting — changing which evidence counts without explicit rationale.",
    "D-D1": "Option Narrowing — considering fewer options than historically.",
    "D-D2": "Option Inflation — many options generated but failing to converge.",
    "D-D3": "Invariant Bypass — decisions that skip or misapply core invariants.",
    "O-D1": "Outcome Misattribution — blaming or crediting wrong causes for results.",
    "O-D2": "Outcome Sanitization — under-recording negative outcomes or failures.",
    "O-D3": "Outcome Overreaction — over-correcting from single events without sufficient evidence.",
    "R-D1": "Reflection Suppression — skipping postmortems, reviews, or honest retrospectives.",
    "R-D2": "Reflection Ritualization — reviews as ceremony without genuine learning.",
    "R-D3": "Reflection Capture — political or reputational pressures distort reflective conclusions.",
    "PR-D1": "Prior Drift (Unanchored Expectations) — new expectations without grounding in environment or evidence.",
    "PR-D2": "Prior Inversion — stable elements treated as volatile, or vice versa.",
    "PR-D3": "Prior Collapse — everything feels equally likely; no structured expectation.",
    "PR-D4": "Prior Overfitting — treating historical priors as universally valid across new environments.",
    "PR-D5": "Prior Blindness — failing to carry forward historically critical expectations.",
}

JPSS_DRIFT_TAXONOMY_SECTIONS: dict[str, tuple[JPSSDriftSubtype, ...]] = {
    "environmental_drift": ("E-D1", "E-D2", "E-D3"),
    "perceptual_drift": ("P-D1", "P-D2", "P-D3"),
    "salience_drift": ("S-D1", "S-D2", "S-D3", "S-D4"),
    "calibration_drift": ("C-D1", "C-D2", "C-D3", "C-D4"),
    "decision_drift": ("D-D1", "D-D2", "D-D3"),
    "outcome_drift": ("O-D1", "O-D2", "O-D3"),
    "reflection_drift": ("R-D1", "R-D2", "R-D3"),
    "prior_drift": ("PR-D1", "PR-D2", "PR-D3", "PR-D4", "PR-D5"),
}


@dataclass(frozen=True)
class DriftSubtypeEntry:
    code: JPSSDriftSubtype
    drift_class: str
    name: str
    description: str


def list_drift_taxonomy() -> list[DriftSubtypeEntry]:
    entries: list[DriftSubtypeEntry] = []
    for code in JPSS_DRIFT_SUBTYPES:
        description = JPSS_DRIFT_SUBTYPE_DESCRIPTIONS[code]
        name = description.split(" — ", 1)[0]
        entries.append(
            DriftSubtypeEntry(
                code=code,
                drift_class=SUBTYPE_TO_DRIFT_CLASS[code],
                name=name,
                description=description,
            )
        )
    return entries


class JPSSDriftSubtypeFinding(BaseModel):
    subtype: JPSSDriftSubtype
    drift_class: str
    detected: bool = False
    description: str = ""
    remediation_hint: str = ""


class JPSSDriftTaxonomyReport(BaseModel):
    decision_id: str | None = None
    layer_findings: list[JPSSDriftFinding] = Field(default_factory=list)
    subtype_findings: list[JPSSDriftSubtypeFinding] = Field(default_factory=list)

    @property
    def active_subtypes(self) -> list[JPSSDriftSubtypeFinding]:
        return [finding for finding in self.subtype_findings if finding.detected]


def _remediation_for_subtype(subtype: JPSSDriftSubtype) -> str:
    hints: dict[JPSSDriftSubtype, str] = {
        "E-D1": "Re-anchor environment classification against preserved environment register.",
        "E-D2": "Surface active constraints from historical decision environment snapshots.",
        "E-D3": "Reconstruct incentive map from environment register and outcome history.",
        "P-D1": "Expand intake channels; compare current vs historical perception register.",
        "P-D2": "Filter noise; restore salience-weighted channel prioritization.",
        "P-D3": "Document source trust rationale in perception register metadata.",
        "S-D1": "Reconcile primary/secondary signal lists against historical salience ledger.",
        "S-D2": "Explicitly rank signals; avoid undifferentiated attention allocation.",
        "S-D3": "Re-evaluate salience against current environment, not only historical patterns.",
        "S-D4": "Cross-check ignored signals against historically successful judgments.",
        "C-D1": "Review evidence thresholds in calibration register; justify inflation.",
        "C-D2": "Restore minimum evidence requirements with documented rationale.",
        "C-D3": "Reconcile risk tolerance with calibration history and failure register.",
        "C-D4": "Make evidence-weight changes explicit in calibration register notes.",
        "D-D1": "Widen option set; check for salience or calibration compression.",
        "D-D2": "Apply convergence criteria; reduce option proliferation.",
        "D-D3": "Re-apply constitutional invariants before decision registration.",
        "O-D1": "Trace causal chain in outcome register with linked decision rationale.",
        "O-D2": "Record negative outcomes in outcome and failure registers.",
        "O-D3": "Require multiple outcome samples before calibration update.",
        "R-D1": "Require reflection register entry for every recorded outcome.",
        "R-D2": "Tie reflection lessons to measurable calibration updates.",
        "R-D3": "Separate political narrative from reflection register content.",
        "PR-D1": "Ground priors in environment and perception registers.",
        "PR-D2": "Reconcile stability/volatility assumptions in prior ledger.",
        "PR-D3": "Structure expectations explicitly in prior ledger.",
        "PR-D4": "Validate priors against current environment before reuse.",
        "PR-D5": "Carry forward critical expectations from historical prior ledger.",
    }
    return hints.get(subtype, "Review preserved registers and re-run reconstruction pipeline.")


def classify_drift_subtypes(layer_report: JPSSDriftReport) -> list[JPSSDriftSubtypeFinding]:
    """Map layer-level drift findings to taxonomy sub-types (heuristic catalog)."""
    findings: list[JPSSDriftSubtypeFinding] = []
    active_classes = {finding.drift_class for finding in layer_report.findings if finding.detected}

    for subtype in JPSS_DRIFT_SUBTYPES:
        drift_class = SUBTYPE_TO_DRIFT_CLASS[subtype]
        detected = drift_class in active_classes
        if drift_class == "prior_drift" and "perceptual_drift" in active_classes:
            detected = detected or subtype in ("PR-D1", "PR-D5")
        if drift_class == "reflection_drift" and "outcome_drift" in active_classes:
            detected = detected or subtype == "R-D1"

        findings.append(
            JPSSDriftSubtypeFinding(
                subtype=subtype,
                drift_class=drift_class,
                detected=detected,
                description=JPSS_DRIFT_SUBTYPE_DESCRIPTIONS[subtype] if detected else "",
                remediation_hint=_remediation_for_subtype(subtype) if detected else "",
            )
        )
    return findings


def build_drift_taxonomy_report(layer_report: JPSSDriftReport) -> JPSSDriftTaxonomyReport:
    return JPSSDriftTaxonomyReport(
        decision_id=layer_report.decision_id,
        layer_findings=layer_report.findings,
        subtype_findings=classify_drift_subtypes(layer_report),
    )


def format_drift_taxonomy() -> str:
    lines = ["=== JPSS Drift Taxonomy (full) ===", ""]
    for drift_class in (*JPSS_DRIFT_CLASSES, "prior_drift"):
        if drift_class not in JPSS_DRIFT_TAXONOMY_SECTIONS:
            continue
        title = drift_class.replace("_", " ").title()
        lines.append(f"{title}")
        for subtype in JPSS_DRIFT_TAXONOMY_SECTIONS[drift_class]:
            lines.append(f"  {subtype}: {JPSS_DRIFT_SUBTYPE_DESCRIPTIONS[subtype]}")
        lines.append("")
    return "\n".join(lines).strip()

"""Constitutional articles — survivability (S), reconstructability (R), and purpose (P) doctrines."""

from __future__ import annotations

from typing import Any, TypedDict


class ConstitutionalArticle(TypedDict):
    id: str
    name: str
    invariant: str
    summary: str
    non_derogable: bool
    obligations: list[str]


RECONSTRUCTABILITY_INVARIANT = "CRITICAL_SYSTEMS_MUST_REMAIN_RECONSTRUCTABLE"
ARTICLE_R_REFERENCE = "Article R — Reconstructability Doctrine"
ARTICLE_S_INVARIANT = "CRITICAL_SYSTEMS_MUST_REMAIN_SURVIVABLE"
ARTICLE_S_ID = "S-000"
ARTICLE_S_REFERENCE = "Article S — Survivability Doctrine"
ARTICLE_S2_ID = "S-002"
ARTICLE_S2_REFERENCE = "Article S-2 — Succession Protocol Integration"

ARTICLE_R: ConstitutionalArticle = {
    "id": "R-000",
    "name": "Reconstructability Doctrine",
    "invariant": RECONSTRUCTABILITY_INVARIANT,
    "summary": "An independent steward must reconstruct and operate the system from constitution and ledger alone.",
    "non_derogable": True,
    "obligations": [
        "Periodic Reconstructability Fitness Assessments",
        "Evidence and Lineage Preservation",
        "Decision Replay Falsification",
        "Semantic Stability Maintenance",
        "Impact Boundary Clarity",
    ],
}

ARTICLE_S: ConstitutionalArticle = {
    "id": ARTICLE_S_ID,
    "name": "Survivability Doctrine",
    "invariant": ARTICLE_S_INVARIANT,
    "summary": "A governed system must remain survivable across changes in time, context, and stewardship.",
    "non_derogable": True,
    "obligations": [
        "Periodic Reconstructability Fitness Assessments",
        "Periodic Cold-Start Steward Tests",
        "Succession Readiness Maintenance",
        "Founder Dependency Reduction",
        "Survivability Threshold Enforcement",
    ],
}

ARTICLE_S2: ConstitutionalArticle = {
    "id": ARTICLE_S2_ID,
    "name": "Succession Protocol Integration",
    "invariant": ARTICLE_S_INVARIANT,
    "summary": (
        "Succession is a constitutional inevitability when survivability requires it, "
        "not a founder-driven event."
    ),
    "non_derogable": True,
    "obligations": [
        "Succession Readiness Assessment",
        "Mandatory Succession Trigger on Sustained Founder Dependency",
        "Succession Proof (C6-SP2) Recording",
        "Knowledge Externalization Before Transfer",
        "Authority Chain Transfer Receipting",
    ],
}

# Article S constitutional thresholds (v0) — S-1.1 governed invariant
SURVIVABILITY_CONSTITUTIONAL_MIN = 0.60
STEWARD_INDEPENDENCE_CONSTITUTIONAL_MIN = 0.60
FOUNDER_DEPENDENCY_CONSTITUTIONAL_MAX = 0.40

SURVIVABILITY_GREEN_MIN = 0.70
STEWARD_INDEPENDENCE_GREEN_MIN = 0.70
FOUNDER_DEPENDENCY_GREEN_MAX = 0.30

# Red zone = constitutional breach → mandatory amendment + governance block
SURVIVABILITY_BLOCK_THRESHOLD = SURVIVABILITY_CONSTITUTIONAL_MIN
STEWARD_INDEPENDENCE_BLOCK_THRESHOLD = STEWARD_INDEPENDENCE_CONSTITUTIONAL_MIN
SURVIVABILITY_WARN_THRESHOLD = SURVIVABILITY_GREEN_MIN
STEWARD_INDEPENDENCE_WARN_THRESHOLD = STEWARD_INDEPENDENCE_GREEN_MIN
FOUNDER_DEPENDENCY_BLOCK_THRESHOLD = FOUNDER_DEPENDENCY_CONSTITUTIONAL_MAX
FOUNDER_DEPENDENCY_WARN_THRESHOLD = FOUNDER_DEPENDENCY_GREEN_MAX
MISSION_MIN_SURVIVABILITY = 0.50
MISSION_MAX_FOUNDER_DEPENDENCY = 0.60
SUCCESSION_MIN_STEWARD_INDEPENDENCE = 0.70
SUCCESSION_MIN_SURVIVABILITY = 0.70
SUCCESSION_MAX_FOUNDER_DEPENDENCY = 0.30
SUCCESSION_MIN_FITNESS = 0.70

# Article S-2 mandatory succession (founder dependency sustained above threshold)
FOUNDER_DEPENDENCY_MANDATORY_SUCCESSION_THRESHOLD = 0.40
MANDATORY_SUCCESSION_CYCLES = 3

# Survivability remediation amendment (UGR-AMENDMENT-S-SURVIVABILITY-v0)
SURVIVABILITY_AMENDMENT_SCORE_THRESHOLD = 0.60
STEWARD_INDEPENDENCE_AMENDMENT_THRESHOLD = 0.60
FOUNDER_DEPENDENCY_AMENDMENT_THRESHOLD = 0.40
RED_ZONE_RF_THREAT_COUNT = 4
SURVIVABILITY_AMENDMENT_COMPLETE_SURVIVABILITY = 0.70
SURVIVABILITY_AMENDMENT_COMPLETE_STEWARD = 0.70
SURVIVABILITY_AMENDMENT_COMPLETE_FOUNDER_MAX = 0.30
SURVIVABILITY_AMENDMENT_COMPLETE_FITNESS = 0.70

SURVIVABILITY_AMENDMENT_TEMPLATE_ID = "UGR-AMENDMENT-S-SURVIVABILITY-v0"

PURPOSE_CONTINUITY_INVARIANT = "CRITICAL_SYSTEMS_MUST_PRESERVE_FOUNDING_PURPOSE"
ARTICLE_P_ID = "P-000"
ARTICLE_P_REFERENCE = "Article P — Purpose Continuity Doctrine"

# Article P constitutional thresholds (v0)
PURPOSE_CONTINUITY_INDEX_THRESHOLD = 0.70
MISSION_LEGIBILITY_MIN_SCORE = 1.0
INVARIANT_INTERPRETATION_MIN_SCORE = 0.70
INVARIANT_INTERPRETATION_SUCCESS_SCORE = 0.80
PURPOSE_CONTINUITY_AMENDMENT_TEMPLATE_ID = "UGR-AMENDMENT-P-PURPOSE-CONTINUITY-v0"
RED_ZONE_PF_THREAT_COUNT = 3
SUCCESSION_MIN_PURPOSE_CONTINUITY_INDEX = PURPOSE_CONTINUITY_INDEX_THRESHOLD
SUCCESSION_MIN_MISSION_LEGIBILITY = MISSION_LEGIBILITY_MIN_SCORE
SUCCESSION_MIN_INVARIANT_INTERPRETATION = INVARIANT_INTERPRETATION_SUCCESS_SCORE

ARTICLE_P: ConstitutionalArticle = {
    "id": ARTICLE_P_ID,
    "name": "Purpose Continuity Doctrine",
    "invariant": PURPOSE_CONTINUITY_INVARIANT,
    "summary": "A governed system must preserve the meaning it was created to protect across time and stewardship.",
    "non_derogable": True,
    "obligations": [
        "Periodic Mission Fidelity Assessments",
        "Mission Legibility Maintenance",
        "Invariant Interpretation Receipts",
        "Purpose Drift Detection and Correction",
        "Cultural Context Preservation",
    ],
}

HIDDENNESS_INVARIANT = "NOTHING_REQUIRED_FOR_CONTINUITY_MAY_REMAIN_IMPLICIT"
HIDDENNESS_CONSTITUTIONAL_ROLE = "meta_runtime"
HIDDENNESS_PRESSURE_QUESTION = "What required knowledge still exists outside the system?"
ARTICLE_H_ID = "H-000"
ARTICLE_H_REFERENCE = "Article H — Hiddenness Doctrine"

# Article H constitutional thresholds (v1)
HIDDENNESS_INDEX_THRESHOLD = 0.70
HIDDENNESS_AMENDMENT_COMPLETE_INDEX = 0.80
SUCCESSION_MIN_HIDDENNESS_INDEX = HIDDENNESS_AMENDMENT_COMPLETE_INDEX
RED_ZONE_HF_THREAT_COUNT = 3
HIDDENNESS_AMENDMENT_TEMPLATE_ID = "UGR-AMENDMENT-H-HIDDENNESS-v0"
HIDDENNESS_RECEIPT_INVARIANT = "NOTHING_REQUIRED_FOR_CONTINUITY_MAY_REMAIN_HIDDEN"

# Article Q — judgment continuity stack (significance, environment, salience, priors)
SIGNIFICANCE_CONTINUITY_INVARIANT = "CRITICAL_SYSTEMS_MUST_PRESERVE_SIGNIFICANCE_CONTINUITY"
ARTICLE_Q3_ID = "Q-003"
ARTICLE_Q3_REFERENCE = "Article Q-3 — Significance Continuity"

DECISION_ENVIRONMENT_INVARIANT = "CRITICAL_SYSTEMS_MUST_PRESERVE_DECISION_ENVIRONMENT"
ARTICLE_Q5_ID = "Q-005"
ARTICLE_Q5_REFERENCE = "Article Q-5 — Decision Environment Continuity"

SALIENCE_CONTINUITY_INVARIANT = "CRITICAL_SYSTEMS_MUST_PRESERVE_SALIENCE_CONTINUITY"
ARTICLE_Q6_ID = "Q-006"
ARTICLE_Q6_REFERENCE = "Article Q-6 — Salience Continuity Doctrine"

PRIOR_CONTINUITY_INVARIANT = "CRITICAL_SYSTEMS_MUST_PRESERVE_STEWARDSHIP_PRIORS"
ARTICLE_Q7_ID = "Q-007"
ARTICLE_Q7_REFERENCE = "Article Q-7 — Stewardship Prior Continuity"

SUCCESSION_MIN_SALIENCE_INDEX = 0.80
SUCCESSION_MIN_PRIOR_DRIFT_INDEX = 0.80
SALIENCE_AMENDMENT_TEMPLATE_ID = "UGR-AMENDMENT-Q-SALIENCE-v0"

ARTICLE_Q6: ConstitutionalArticle = {
    "id": ARTICLE_Q6_ID,
    "name": "Salience Continuity Doctrine",
    "invariant": SALIENCE_CONTINUITY_INVARIANT,
    "summary": (
        "A governed system must preserve the salience patterns that guided past stewardship, "
        "including which signals were weighted, which risks were foregrounded, and which cues were ignored."
    ),
    "non_derogable": True,
    "obligations": [
        "Salience Ledger maintenance for constitutional judgments",
        "Salience Continuity Runtime assessments",
        "Salience Judgment Test for steward perceptual competence",
        "Perceptual Drift detection and remediation",
        "Mandatory amendment on salience continuity failure",
    ],
}

ARTICLE_Q7: ConstitutionalArticle = {
    "id": ARTICLE_Q7_ID,
    "name": "Stewardship Prior Continuity",
    "invariant": PRIOR_CONTINUITY_INVARIANT,
    "summary": (
        "A governed system must preserve the implicit expectations (priors) that shaped "
        "salience, calibration, and judgment across stewardship generations."
    ),
    "non_derogable": True,
    "obligations": [
        "Stewardship Prior Ledger maintenance",
        "Prior Drift detection",
        "Prior Judgment Test for steward epistemic competence",
        "Prior-aware succession gating",
        "Prior continuity dashboard visibility",
    ],
}

ARTICLE_Q5: ConstitutionalArticle = {
    "id": ARTICLE_Q5_ID,
    "name": "Decision Environment Continuity",
    "invariant": DECISION_ENVIRONMENT_INVARIANT,
    "summary": (
        "A governed system must preserve the decision environment — constraints, incentives, "
        "uncertainties, and contextual factors — that shaped past judgments."
    ),
    "non_derogable": True,
    "obligations": [
        "Stewardship context ledger and ECK-1 environment register",
        "Decision Environment Runtime assessments",
        "Environment continuity succession gating",
        "Environment panel on constitutional dashboard",
    ],
}

ARTICLE_H: ConstitutionalArticle = {
    "id": ARTICLE_H_ID,
    "name": "Hiddenness Doctrine",
    "invariant": HIDDENNESS_INVARIANT,
    "summary": (
        "Hiddenness is constitutional pressure — the adversarial search for knowledge "
        "required for continuity that remains outside the system. It is the meta-runtime "
        "precursor beneath reconstructability (R-F), survivability (S), and purpose (P-F) failures."
    ),
    "non_derogable": True,
    "obligations": [
        "Operate Hiddenness as meta-runtime pressure exposing what all surfaces lack",
        "Treat Cold-Start Steward Test as the first hiddenness detector",
        "Continuous adversarial search against implicit knowledge",
        "Implicit Assumption Externalization",
        "Invariant and Rationale Receipting",
        "Purpose Fragment Documentation",
        "Authority Chain Explicitness",
        "Cultural Context Preservation",
        "Mandatory Amendment on Hiddenness Failure",
    ],
}


SIGNIFICANCE_INVARIANT = "CRITICAL_ARTIFACTS_MUST_REMAIN_RANKED_AND_JUSTIFIED"
SIGNIFICANCE_STABILITY_INVARIANT = "SIGNIFICANCE_TIERS_MUST_NOT_DRIFT_WITHOUT_JUSTIFICATION"
ARTICLE_Q_ID = "Q-000"
ARTICLE_Q2_ID = "Q-002"
ARTICLE_Q_REFERENCE = "Article Q — Significance Doctrine"
ARTICLE_Q2_REFERENCE = "Article Q-2 — Significance Stability Doctrine"

# Article Q constitutional thresholds (v0)
SIGNIFICANCE_HEALTH_THRESHOLD = 0.70
SIGNIFICANCE_STABILITY_THRESHOLD = 0.80
SUCCESSION_MIN_SIGNIFICANCE_HEALTH = 0.70
SUCCESSION_MIN_SIGNIFICANCE_STABILITY = 0.80
SUCCESSION_MIN_SIGNIFICANCE_CONTINUITY = 0.85
SUCCESSION_MIN_DECISION_ENVIRONMENT = 0.80
SIGNIFICANCE_CORE_CAPACITY = 12
RED_ZONE_QF_THREAT_COUNT = 3
SIGNIFICANCE_AMENDMENT_TEMPLATE_ID = "UGR-AMENDMENT-Q-SIGNIFICANCE-v0"
SIGNIFICANCE_STABILITY_AMENDMENT_TEMPLATE_ID = "UGR-AMENDMENT-Q2-SIGNIFICANCE-STABILITY-v0"

# ECK-1 succession thresholds (normative spec v1.0)
ECK1_MIN_PRIOR_DRIFT_INDEX = 0.80
ECK1_MIN_SALIENCE_INDEX = 0.80
ECK1_MIN_PERCEPTUAL_DRIFT_INDEX = 0.80
ECK1_MIN_ENVIRONMENT_HEALTH = 0.80
ECK1_MIN_CALIBRATION_INDEX = 0.80
ECK1_MIN_SIGNIFICANCE_CONTINUITY = 0.85
ECK1_MIN_FAILURE_CONTINUITY = 0.80

# JPSS-1 / JPSS-I / JPSS-C / Legitimacy / ECK-2 thresholds
JPSS_CONTINUITY_INVARIANT = "JUDGMENT_CYCLES_MUST_REMAIN_RECONSTRUCTABLE"
JPSS_IDENTITY_INVARIANT = "IDENTITY_ANCHORS_MUST_REMAIN_STABLE"
STEWARDSHIP_LEGITIMACY_INVARIANT = "INVARIANT_ALTERATION_REQUIRES_DEMONSTRATED_RECONSTRUCTION"
ARTICLE_JPSS_ID = "JPSS-1"
ARTICLE_JPSS_REFERENCE = "JPSS-1 — Judgment Preservation & Stewardship Science"
ARTICLE_JPSS_I_ID = "JPSS-I"
ARTICLE_JPSS_I_REFERENCE = "JPSS-I — Integrated Judgment Preservation & Stewardship Science"
ARTICLE_JPSS_C_ID = "JPSS-C"
ARTICLE_JPSS_C_REFERENCE = "JPSS-C — Constitutional Judgment Preservation Science"
ARTICLE_LEGITIMACY_ID = "LEGITIMACY-1"
ARTICLE_LEGITIMACY_REFERENCE = "Stewardship Legitimacy Protocol v1.0"
ECK2_MIN_DRIFT_SYMMETRY_INDEX = 0.80
ECK2_MIN_INVARIANT_DRIFT_INDEX = 0.80
MIN_LEGITIMACY_INDEX = 0.80
MIN_PLURALITY_FOR_INVARIANT_ALTERATION = 2
JPSS_II_MIN_TRANSFERABILITY_INDEX = 0.80
ECK2_REFERENCE = "ECK-2 — Unified Epistemic Kernel (formation + reconstruction)"

ARTICLE_JPSS: ConstitutionalArticle = {
    "id": ARTICLE_JPSS_ID,
    "name": "Judgment Preservation & Stewardship Science",
    "invariant": JPSS_CONTINUITY_INVARIANT,
    "summary": (
        "A governed system must preserve the full eight-stage judgment cycle "
        "so future stewards can reconstruct how decisions were formed."
    ),
    "non_derogable": True,
    "obligations": [
        "Preserve environment, perception, salience, and calibration registers",
        "Record decisions, outcomes, reflection, and failure history",
        "Detect drift across all eight JPSS layers",
        "Enable bidirectional formation and reconstruction pipelines (ECK-2)",
        "Require dual-pipeline competence for succession",
    ],
}

ARTICLE_JPSS_I: ConstitutionalArticle = {
    "id": ARTICLE_JPSS_I_ID,
    "name": "Integrated Judgment Preservation & Stewardship Science",
    "invariant": JPSS_IDENTITY_INVARIANT,
    "summary": (
        "A governed system must unify adaptive judgment, invariant identity, "
        "and stewardship balance so plasticity and purpose remain jointly preserved."
    ),
    "non_derogable": True,
    "obligations": [
        "Maintain purpose, values, commitments, identity, and sacred constraint registers",
        "Detect invariant drift across all five identity surfaces",
        "Require stewardship balancing competence for succession",
        "Prevent adaptive updates from violating invariant anchors",
        "Prevent invariant rigidity from blocking necessary adaptation",
    ],
}

ARTICLE_JPSS_C: ConstitutionalArticle = {
    "id": ARTICLE_JPSS_C_ID,
    "name": "Constitutional Judgment Preservation Science",
    "invariant": STEWARDSHIP_LEGITIMACY_INVARIANT,
    "summary": (
        "A governed system must govern the boundary between adaptive and invariant "
        "judgment through explicit classification, reconstruction evidence, and consequence simulation."
    ),
    "non_derogable": True,
    "obligations": [
        "Classify changes as adaptive, invariant, boundary consultation, or legitimacy review",
        "Require reconstruction evidence before invariant alteration",
        "Require consequence simulation before invariant touch",
        "Record constitutional reasoning for boundary decisions",
    ],
}

ARTICLE_LEGITIMACY: ConstitutionalArticle = {
    "id": ARTICLE_LEGITIMACY_ID,
    "name": "Stewardship Legitimacy Protocol",
    "invariant": STEWARDSHIP_LEGITIMACY_INVARIANT,
    "summary": (
        "A continuity system must determine who is qualified to alter continuity through "
        "demonstrated, reconstructable stewardship competence — not title, vote, or founder preference."
    ),
    "non_derogable": True,
    "obligations": [
        "Require public reconstructable stewardship exams (JPSS, JPSS-I, JPSS-C)",
        "Ground authority in reconstruction demonstrations before invariant alteration",
        "Maintain certified steward register with receipt-backed reasoning",
        "Enforce plurality — no unilateral invariant alteration",
        "Detect legitimacy drift on certification standards",
    ],
}

ARTICLE_Q: ConstitutionalArticle = {
    "id": ARTICLE_Q_ID,
    "name": "Significance Doctrine",
    "invariant": SIGNIFICANCE_INVARIANT,
    "summary": "A governed system must preserve a justified lattice of what matters most.",
    "non_derogable": True,
    "obligations": [
        "Rank all constitutional artifacts by significance tier",
        "Require rationale for Tier 0 and Tier 1 assignments",
        "Detect unranked and mis-ranked core artifacts",
        "Prevent tier bloat in sacred and structural tiers",
        "Detect priority inversion against core constraints",
    ],
}

ARTICLE_Q2: ConstitutionalArticle = {
    "id": ARTICLE_Q2_ID,
    "name": "Significance Stability Doctrine",
    "invariant": SIGNIFICANCE_STABILITY_INVARIANT,
    "summary": (
        "A governed system must preserve not only the ordering of importance, "
        "but also the rationale behind that ordering — detecting significance drift."
    ),
    "non_derogable": True,
    "obligations": [
        "Track historical tier assignments and rationales",
        "Detect changes in tier assignments",
        "Require justification for any tier change",
        "Block unjustified reclassification",
        "Require constitutional amendment for Tier 0/1 changes",
    ],
}


def article_as_dict(article: ConstitutionalArticle) -> dict[str, Any]:
    return dict(article)

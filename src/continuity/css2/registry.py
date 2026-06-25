"""Seed Threshold registry from CSS-1 / CE-1 / RA-COS-1 constants."""

from __future__ import annotations

from src.continuity.css.spec import ADM_HIGH_THRESHOLD
from src.continuity.css2.threshold import RecalibrationRule, Threshold
from src.continuity.ra.spec import (
    DEFAULT_RECONSTRUCTION_COST_THRESHOLD,
    PSD_REEVALUATION_THRESHOLD,
    PSD_REJECTION_THRESHOLD,
    VAS1_MIN_CRITERIA_PASSED,
)
from src.cos1.continuity_engine.spec import (
    CT2_MIN_CONVERGENCE,
    CT2_MIN_DOMAINS,
    MAT3_MIN_ACCUMULATION,
    PT3_MIN_PROPAGATION,
)


def default_recalibration_rule() -> RecalibrationRule:
    return RecalibrationRule(
        id="rr-default",
        name="CRK-1 default recalibration rule",
        who_may_propose=["steward"],
        who_may_approve=["steward"],
        requires_evidence=True,
        requires_adversarial_review=True,
        non_derogable_invariants=["K4", "reality_precedence"],
        intent="Stewards govern recalibration legitimacy; they do not recalibrate ad hoc.",
        created_by="CRK-1",
    )


def seed_css1_thresholds() -> list[Threshold]:
    """Materialize CE-1 / CSS-1 / RA-COS-1 decision boundaries as Threshold objects."""
    creator = "CSS-1-seed"
    return [
        Threshold(
            id="th-ce-pt3",
            name="PT-3 propagation minimum",
            domain="CE-1",
            metric="propagation_count",
            comparator=">=",
            value=PT3_MIN_PROPAGATION,
            unit="count",
            intent="Propagation threshold — ideas must spread across minds.",
            owner="CE-1",
            created_by=creator,
            last_updated_by=creator,
        ),
        Threshold(
            id="th-ce-ct2-count",
            name="CT-2 convergence count",
            domain="CE-1",
            metric="convergence_count",
            comparator=">=",
            value=CT2_MIN_CONVERGENCE,
            unit="count",
            intent="Convergence threshold — independent rediscovery.",
            owner="CE-1",
            created_by=creator,
            last_updated_by=creator,
        ),
        Threshold(
            id="th-ce-ct2-domains",
            name="CT-2 domain diversity",
            domain="CE-1",
            metric="convergence_domains",
            comparator=">=",
            value=CT2_MIN_DOMAINS,
            unit="count",
            intent="Convergence must span multiple domains.",
            owner="CE-1",
            created_by=creator,
            last_updated_by=creator,
        ),
        Threshold(
            id="th-ce-mat3",
            name="MAT-3 accumulation minimum",
            domain="CE-1",
            metric="accumulation_count",
            comparator=">=",
            value=MAT3_MIN_ACCUMULATION,
            unit="count",
            intent="Accumulation threshold — compounding across generations.",
            owner="CE-1",
            created_by=creator,
            last_updated_by=creator,
        ),
        Threshold(
            id="th-adm-high",
            name="ADM-1 high drift",
            domain="ADM-1",
            metric="accumulation_drift_score",
            comparator=">=",
            value=ADM_HIGH_THRESHOLD,
            unit="score",
            intent="Pathological accumulation — continuity collapse risk.",
            owner="ADM-1",
            created_by=creator,
            last_updated_by=creator,
        ),
        Threshold(
            id="th-vas-min",
            name="VAS-1 minimum criteria",
            domain="VAS-1",
            metric="criteria_passed",
            comparator=">=",
            value=VAS1_MIN_CRITERIA_PASSED,
            unit="count",
            intent="Reality validation after surpassment — at least 3/5 criteria.",
            owner="RA-COS-1",
            created_by=creator,
            last_updated_by=creator,
        ),
        Threshold(
            id="th-psd-reeval",
            name="PSDD-1 re-evaluation",
            domain="PSDD-1",
            metric="psd_score",
            comparator=">=",
            value=PSD_REEVALUATION_THRESHOLD,
            unit="score",
            intent="Post-surpassment drift — trigger re-evaluation.",
            owner="RA-COS-1",
            created_by=creator,
            last_updated_by=creator,
        ),
        Threshold(
            id="th-psd-reject",
            name="PSDD-1 rejection",
            domain="PSDD-1",
            metric="psd_score",
            comparator=">=",
            value=PSD_REJECTION_THRESHOLD,
            unit="score",
            intent="Post-surpassment drift — reject / correct.",
            owner="RA-COS-1",
            created_by=creator,
            last_updated_by=creator,
        ),
        Threshold(
            id="th-k4-recon",
            name="K4 reconstruction cost",
            domain="K4",
            metric="reconstruction_cost",
            comparator="<=",
            value=DEFAULT_RECONSTRUCTION_COST_THRESHOLD,
            unit="cost",
            intent="Reconstructability protection — non-derogable.",
            owner="K4",
            created_by=creator,
            last_updated_by=creator,
        ),
    ]

"""Constitutional article registry — Article R and Article S."""

from __future__ import annotations

from constitutional import (
    ARTICLE_R,
    ARTICLE_S,
    ARTICLE_S2,
    ARTICLE_S_ID,
    ARTICLE_S_INVARIANT,
    constitutional_registry,
)
from constitutional.core.articles import ARTICLE_R_REFERENCE, ARTICLE_S_REFERENCE


def test_article_s_registered() -> None:
    article = constitutional_registry.get_article(ARTICLE_S_ID)
    assert article is not None
    assert article["name"] == "Survivability Doctrine"
    assert article["invariant"] == ARTICLE_S_INVARIANT
    assert article["non_derogable"] is True
    assert "Founder Dependency Reduction" in article["obligations"]


def test_article_r_registered() -> None:
    article = constitutional_registry.get_article(ARTICLE_R["id"])
    assert article is not None
    assert article["invariant"] == ARTICLE_R["invariant"]


def test_registry_lookup_by_invariant() -> None:
    by_s = constitutional_registry.get_by_invariant(ARTICLE_S_INVARIANT)
    assert by_s is not None
    assert by_s["id"] == ARTICLE_S_ID

    by_r = constitutional_registry.get_by_invariant(ARTICLE_R["invariant"])
    assert by_r is not None
    assert by_r["id"] == ARTICLE_R["id"]


def test_article_s2_registered() -> None:
    article = constitutional_registry.get_article("S-002")
    assert article is not None
    assert article["name"] == "Succession Protocol Integration"


def test_article_p_registered() -> None:
    from constitutional.core.articles import ARTICLE_P_ID, PURPOSE_CONTINUITY_INVARIANT

    article = constitutional_registry.get_article(ARTICLE_P_ID)
    assert article is not None
    assert article["invariant"] == PURPOSE_CONTINUITY_INVARIANT


def test_article_h_registered() -> None:
    from constitutional.core.articles import (
        ARTICLE_H_ID,
        HIDDENNESS_CONSTITUTIONAL_ROLE,
        HIDDENNESS_INVARIANT,
        HIDDENNESS_PRESSURE_QUESTION,
    )

    article = constitutional_registry.get_article(ARTICLE_H_ID)
    assert article is not None
    assert article["invariant"] == HIDDENNESS_INVARIANT
    assert article["non_derogable"] is True
    assert HIDDENNESS_CONSTITUTIONAL_ROLE == "meta_runtime"
    assert "outside the system" in HIDDENNESS_PRESSURE_QUESTION
    assert "meta-runtime" in article["summary"]
    assert "meta-runtime pressure" in article["obligations"][0]


def test_hiddenness_amendment_template_registered() -> None:
    from constitutional.hiddenness.hiddenness_amendment import (
        HIDDENNESS_AMENDMENT_TEMPLATE,
        HIDDENNESS_AMENDMENT_TEMPLATE_ID,
    )

    assert HIDDENNESS_AMENDMENT_TEMPLATE_ID == "UGR-AMENDMENT-H-HIDDENNESS-v0"
    assert HIDDENNESS_AMENDMENT_TEMPLATE["template_id"] == HIDDENNESS_AMENDMENT_TEMPLATE_ID
    assert "HIDDENNESS REMEDIATION AMENDMENT" in HIDDENNESS_AMENDMENT_TEMPLATE["amendment_type"]


def test_article_references() -> None:
    assert "Survivability" in ARTICLE_S_REFERENCE
    assert "Reconstructability" in ARTICLE_R_REFERENCE


def test_article_q6_salience_registered() -> None:
    from constitutional.core.articles import ARTICLE_Q6_ID, ARTICLE_Q6_REFERENCE

    article = constitutional_registry.get_article(ARTICLE_Q6_ID)
    assert article is not None
    assert "Salience" in article["name"]
    assert ARTICLE_Q6_REFERENCE in article.get("summary", "") or "Salience" in article["name"]


def test_article_q7_prior_registered() -> None:
    from constitutional.core.articles import ARTICLE_Q7_ID, ARTICLE_Q7_REFERENCE

    article = constitutional_registry.get_article(ARTICLE_Q7_ID)
    assert article is not None
    assert "Prior" in article["name"]
    assert ARTICLE_Q7_REFERENCE in article.get("summary", "") or "Prior" in article["name"]


def test_article_q5_environment_registered() -> None:
    from constitutional.core.articles import ARTICLE_Q5_ID, DECISION_ENVIRONMENT_INVARIANT

    article = constitutional_registry.get_article(ARTICLE_Q5_ID)
    assert article is not None
    assert article["invariant"] == DECISION_ENVIRONMENT_INVARIANT
    assert "Environment" in article["name"]


def test_article_q_and_q2_registered() -> None:
    from constitutional.core.articles import (
        ARTICLE_Q2_ID,
        ARTICLE_Q2_REFERENCE,
        ARTICLE_Q_ID,
        ARTICLE_Q_REFERENCE,
        ECK1_MIN_CALIBRATION_INDEX,
        SIGNIFICANCE_INVARIANT,
        SIGNIFICANCE_STABILITY_INVARIANT,
    )

    q = constitutional_registry.get_article(ARTICLE_Q_ID)
    assert q is not None
    assert q["invariant"] == SIGNIFICANCE_INVARIANT
    assert q["non_derogable"] is True
    assert "Significance" in ARTICLE_Q_REFERENCE

    q2 = constitutional_registry.get_article(ARTICLE_Q2_ID)
    assert q2 is not None
    assert q2["invariant"] == SIGNIFICANCE_STABILITY_INVARIANT
    assert "Stability" in ARTICLE_Q2_REFERENCE
    assert ECK1_MIN_CALIBRATION_INDEX == 0.80

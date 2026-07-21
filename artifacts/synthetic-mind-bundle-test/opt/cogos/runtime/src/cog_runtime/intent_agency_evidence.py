"""Agency evidence metrics — session reset fixtures and survival scoring."""

from __future__ import annotations

from typing import Any

CLAIM_POSTURES = frozenset({"asserted", "proven", "rejected"})


def active_commitment_texts(intent: dict[str, Any] | None) -> list[str]:
    payload = dict(intent or {})
    texts: list[str] = []
    for item in payload.get("active_commitments") or []:
        if not isinstance(item, dict):
            continue
        if item.get("status") not in {"active", "in_tension", "deferred"}:
            continue
        text = str(item.get("commitment") or "").strip()
        if text:
            texts.append(text)
    return texts


def score_commitment_survival(
    prior_intent: dict[str, Any] | None,
    next_intent: dict[str, Any] | None,
) -> dict[str, Any]:
    """Fraction of prior active commitments still present after a boundary."""
    prior_texts = active_commitment_texts(prior_intent)
    next_texts = set(active_commitment_texts(next_intent))
    if not prior_texts:
        return {"rate": 1.0, "survived": [], "lost": [], "passed": True}
    survived = [text for text in prior_texts if text in next_texts]
    lost = [text for text in prior_texts if text not in next_texts]
    rate = round(len(survived) / len(prior_texts), 3)
    return {
        "rate": rate,
        "survived": survived,
        "lost": lost,
        "passed": rate >= 1.0,
    }


def score_story_change_commitment_hold(
    *,
    prior_narrative: dict[str, Any] | None,
    next_narrative: dict[str, Any] | None,
    prior_intent: dict[str, Any] | None,
    next_intent: dict[str, Any] | None,
) -> dict[str, Any]:
    """Commitments survive even when active_story changes."""
    prior_story = str((prior_narrative or {}).get("active_story") or "")
    next_story = str((next_narrative or {}).get("active_story") or "")
    survival = score_commitment_survival(prior_intent, next_intent)
    story_changed = bool(prior_story and next_story and prior_story != next_story)
    passed = survival["passed"] and (not story_changed or bool(survival["survived"]))
    return {
        **survival,
        "story_changed": story_changed,
        "passed": passed,
    }


def score_unified_closure_present(intent: dict[str, Any] | None) -> dict[str, Any]:
    closure = dict((intent or {}).get("unified_closure") or {})
    unified = bool(closure.get("unified"))
    layers = list(closure.get("layers") or [])
    layer_names = {str(item.get("layer") or "") for item in layers if isinstance(item, dict)}
    return {
        "unified": unified,
        "layer_count": len(layers),
        "has_intent_layer": "intent" in layer_names,
        "has_arc_layer": "arc" in layer_names,
        "passed": unified and "intent" in layer_names,
    }


def score_claim_posture_coverage(intent: dict[str, Any] | None) -> dict[str, Any]:
    commitments = list((intent or {}).get("active_commitments") or [])
    if not commitments:
        return {"coverage": 1.0, "missing": 0, "passed": True}
    missing = 0
    for item in commitments:
        if not isinstance(item, dict):
            missing += 1
            continue
        posture = str(item.get("claim_posture") or "")
        if posture not in CLAIM_POSTURES:
            missing += 1
    coverage = round((len(commitments) - missing) / len(commitments), 3)
    return {
        "coverage": coverage,
        "missing": missing,
        "continuity_claim_posture": (intent or {}).get("continuity_claim_posture"),
        "passed": missing == 0,
    }


def run_agency_evidence_fixture(
    *,
    prior_intent: dict[str, Any],
    next_intent: dict[str, Any],
    prior_narrative: dict[str, Any] | None = None,
    next_narrative: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Single-call fixture evaluation for CI and proof bundles."""
    survival = score_story_change_commitment_hold(
        prior_narrative=prior_narrative,
        next_narrative=next_narrative,
        prior_intent=prior_intent,
        next_intent=next_intent,
    )
    closure = score_unified_closure_present(next_intent)
    posture = score_claim_posture_coverage(next_intent)
    passed = survival["passed"] and posture["passed"]
    return {
        "commitment_survival": survival,
        "unified_closure": closure,
        "claim_posture": posture,
        "passed": passed,
    }

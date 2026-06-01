"""Turn-boundary agency preservation — intent/narrative drift detection."""

from __future__ import annotations

from typing import Any

from src.cog_runtime.formal.agency_preservation import check_agency_preservation
from src.cog_runtime.formal.intent_narrative_reconcile import reconcile_intent_narrative

INTENT_DRIFT_EPSILON = 0.35


class AgencyViolation(Exception):
    """Raised when intent or narrative drift exceeds constitutional bounds."""

    def __init__(self, message: str, *, delta: float | None = None, issues: list[str] | None = None):
        super().__init__(message)
        self.delta = delta
        self.issues = list(issues or [])

    def to_dict(self) -> dict[str, Any]:
        return {
            "error": str(self),
            "delta": self.delta,
            "issues": list(self.issues),
            "theorem": "turn_agency_preservation",
        }


def _intent_fingerprint(intent: dict[str, Any] | None) -> set[str]:
    payload = dict(intent or {})
    tokens: set[str] = set()
    for key in ("agency_note", "continuity_claim_posture"):
        value = str(payload.get(key) or "").strip().lower()
        if value:
            tokens.update(value.split())
    for item in payload.get("active_commitments") or []:
        if isinstance(item, dict):
            text = str(item.get("commitment") or item.get("text") or "").strip().lower()
            if text:
                tokens.add(text[:80])
    for item in payload.get("long_horizon_goals") or []:
        if isinstance(item, dict):
            text = str(item.get("goal") or "").strip().lower()
            if text:
                tokens.add(text[:80])
        elif item:
            tokens.add(str(item).strip().lower()[:80])
    return tokens


def measure_intent_shift(before: dict[str, Any] | None, after: dict[str, Any] | None) -> float:
    """Return normalized Jaccard distance between intent fingerprints (0 = identical)."""
    left = _intent_fingerprint(before)
    right = _intent_fingerprint(after)
    if not left and not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    intersection = left & right
    similarity = len(intersection) / len(union)
    return round(1.0 - similarity, 3)


def _narrative_fingerprint(narrative: dict[str, Any] | None) -> set[str]:
    payload = dict(narrative or {})
    tokens: set[str] = set()
    for key in ("active_story", "becoming", "working_on", "current_chapter"):
        value = str(payload.get(key) or "").strip().lower()
        if value:
            tokens.update(part for part in value.split() if len(part) > 2)
    return tokens


def measure_narrative_shift(before: dict[str, Any] | None, after: dict[str, Any] | None) -> float:
    left = _narrative_fingerprint(before)
    right = _narrative_fingerprint(after)
    if not left and not right:
        return 0.0
    union = left | right
    if not union:
        return 0.0
    return round(1.0 - (len(left & right) / len(union)), 3)


def capture_turn_boundary(metadata: dict[str, Any] | None) -> dict[str, Any]:
    meta = dict(metadata or {})
    intent = dict(meta.get("nova_intent") or {})
    narrative = dict(meta.get("nova_narrative") or {})
    artifacts = dict(meta.get("cognitive_runtime_artifacts") or {})
    if not intent and isinstance(artifacts.get("intent_artifact"), dict):
        intent = dict(artifacts["intent_artifact"])
    if not narrative and isinstance(artifacts.get("narrative_artifact"), dict):
        narrative = dict(artifacts["narrative_artifact"])
    return {
        "intent": intent,
        "narrative": narrative,
        "focus": dict(artifacts.get("focus_artifact") or {}),
    }


def reconcile_turn_agency(
    before: dict[str, Any] | None,
    after: dict[str, Any] | None,
    *,
    epsilon: float = INTENT_DRIFT_EPSILON,
) -> dict[str, Any]:
    """Compare turn boundaries; raise AgencyViolation on usurpation or excessive drift."""
    prior_intent = dict((before or {}).get("intent") or {})
    current_intent = dict((after or {}).get("intent") or {})
    prior_narrative = dict((before or {}).get("narrative") or {})
    current_narrative = dict((after or {}).get("narrative") or {})

    intent_delta = measure_intent_shift(prior_intent, current_intent)
    narrative_delta = measure_narrative_shift(prior_narrative, current_narrative)
    issues: list[str] = []

    if prior_intent and intent_delta > epsilon:
        issues.append(f"intent_drift:{intent_delta}>{epsilon}")
    if prior_narrative and narrative_delta > epsilon:
        issues.append(f"narrative_drift:{narrative_delta}>{epsilon}")

    reconciliation = reconcile_intent_narrative(
        current_intent or None,
        current_narrative or None,
        prior_intent=prior_intent or None,
    )
    if not reconciliation.get("valid"):
        issues.extend(list(reconciliation.get("issues") or []))

    agency = check_agency_preservation(prior_intent or None, current_intent or None, current_narrative or None)
    if not agency.get("valid"):
        issues.extend(list(agency.get("issues") or []))

    if issues:
        if any("usurpation" in issue or "dangling_promise" in issue for issue in issues):
            raise AgencyViolation(
                "Intent or narrative drift beyond threshold",
                delta=max(intent_delta, narrative_delta),
                issues=issues,
            )
        if (prior_intent and intent_delta > epsilon) or (prior_narrative and narrative_delta > epsilon):
            raise AgencyViolation(
                "Intent or narrative drift beyond threshold",
                delta=max(intent_delta, narrative_delta),
                issues=issues,
            )

    return {
        "valid": True,
        "intent_delta": intent_delta,
        "narrative_delta": narrative_delta,
        "epsilon": epsilon,
        "reconciliation": reconciliation,
        "agency_preservation": agency,
        "rule_id": "turn_agency.v1",
    }

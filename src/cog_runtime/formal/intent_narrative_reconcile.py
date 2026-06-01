"""Turn-boundary reconciliation between Intent commitments and Narrative promises."""

from __future__ import annotations

from typing import Any

from src.cog_runtime.formal.agency_preservation import check_agency_preservation


RESOLVED_COMMITMENT_STATUSES = frozenset({"resolved", "superseded"})
OPEN_PROMISE_STATUSES = frozenset({"open", "active", "pending"})


def reconcile_intent_narrative(
    intent: dict[str, Any] | None,
    narrative: dict[str, Any] | None,
    *,
    prior_intent: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """
    At turn boundary:
    - resolve closed commitments
    - update narrative promises
    - check tension ↔ commitment ↔ narrative inconsistencies
    """
    intent_payload = dict(intent or {})
    narrative_payload = dict(narrative or {})
    prior = dict(prior_intent or {})
    issues: list[str] = []

    commitments = list(intent_payload.get("active_commitments") or [])
    closed_this_turn: list[dict[str, Any]] = []
    still_active: list[dict[str, Any]] = []
    for item in commitments:
        if not isinstance(item, dict):
            continue
        status = str(item.get("status") or "active").lower()
        if status in RESOLVED_COMMITMENT_STATUSES:
            closed_this_turn.append(item)
        else:
            still_active.append(item)

    promises = list(narrative_payload.get("promises") or [])
    open_promises = [
        p for p in promises if isinstance(p, dict) and str(p.get("status") or "open").lower() in OPEN_PROMISE_STATUSES
    ]
    resolved_promises = [
        p
        for p in promises
        if isinstance(p, dict) and str(p.get("status") or "").lower() in {"fulfilled", "broken", "withdrawn"}
    ]

    commitment_ids = {str(c.get("id") or c.get("commitment_id") or "") for c in still_active if c.get("id") or c.get("commitment_id")}
    promise_commitment_refs = {
        str(p.get("commitment_id") or p.get("source_commitment") or "")
        for p in open_promises
        if p.get("commitment_id") or p.get("source_commitment")
    }
    dangling_promises = sorted(ref for ref in promise_commitment_refs if ref and ref not in commitment_ids)
    if dangling_promises:
        issues.append(f"dangling_promise_refs:{','.join(dangling_promises[:4])}")

    prior_story = str(prior.get("active_story") or "")
    current_story = str(narrative_payload.get("active_story") or "")
    story_changed = bool(prior_story and current_story and prior_story != current_story)
    if story_changed and still_active:
        for c in still_active:
            if str(c.get("narrative_bound") or "").lower() == "story_specific":
                issues.append(f"story_change_with_bound_commitment:{c.get('id', 'unknown')}")

    tensions = list(intent_payload.get("current_tensions") or [])
    protected = set(str(v) for v in (intent_payload.get("protected_values") or []))
    if "identity_consistency" in protected and story_changed and not still_active:
        issues.append("identity_tension:story_changed_without_active_commitments")

    agency = check_agency_preservation(prior, intent_payload, narrative_payload)
    if not agency.get("valid"):
        issues.extend(list(agency.get("issues") or []))

    reconciliation = {
        "closed_commitments": closed_this_turn,
        "active_commitment_count": len(still_active),
        "open_promise_count": len(open_promises),
        "resolved_promise_count": len(resolved_promises),
        "story_changed": story_changed,
        "tension_count": len(tensions),
        "dangling_promise_refs": dangling_promises,
        "agency_preservation": {
            "valid": bool(agency.get("valid")),
            "issues": list(agency.get("issues") or []),
        },
    }

    return {
        "valid": not issues,
        "issues": issues,
        "reconciliation": reconciliation,
        "rule_id": "intent_narrative_reconcile.v1",
    }

"""Pattern Ledger promotion stub (COLLECTIVE_PATTERN_LEDGER — no auto-fame)."""

from __future__ import annotations

from typing import Any

PROMOTION_STATUSES = frozenset(
    {
        "pending_review",
        "accepted",
        "rejected",
        "discarded",
    }
)


def submit_rail_promotion_candidate(
    ledger_record: dict[str, Any],
    *,
    classification: str = "pending_review",
) -> dict[str, Any]:
    """
    Stage a rail decision for Collective Pattern Ledger review.

    Phase 2 stub: never auto-promotes to Hall of Fame; returns pending_review.
    """
    decision = dict(ledger_record.get("rail_decision") or {})
    plan = dict(ledger_record.get("cognition_plan") or {})
    rail = str(decision.get("rail") or "UNKNOWN")
    domain = plan.get("domain_template") or (plan.get("template") or {}).get("template_id")

    normalized_class = str(classification or "pending_review").strip().lower()
    if normalized_class not in PROMOTION_STATUSES:
        normalized_class = "pending_review"

    if rail == "SAFE" and normalized_class == "success":
        normalized_class = "pending_review"

    return {
        "promotion_id": f"promo-{ledger_record.get('record_id', 'unknown')}",
        "source_class": "routing_subsystem",
        "event_type": "rail_decision",
        "classification": normalized_class,
        "claim_status": "asserted",
        "domain": domain,
        "rail": rail,
        "verification_gate": "COLLECTIVE_PATTERN_LEDGER",
        "auto_publish": False,
        "hall_of_fame_eligible": False,
        "hall_of_shame_required": rail == "SAFE" and decision.get("risk") == "HIGH",
        "summary": (
            f"Rail {rail} candidate for domain={domain or 'n/a'}; "
            "requires operator verification before guidance promotion."
        ),
        "evidence_ref": ledger_record.get("record_id"),
    }

"""Human–AI Co-Collaboration Charter operator surfaces (Art IV / Art V).

Shared helpers for civilizational-tier operator APIs (ISD, NFD, etc.).
"""

from __future__ import annotations

from typing import Any

CHARTER_DOC = "HUMAN_AI_CO_COLLABORATION_CHARTER.md"


def _ambiguity_from_drift(drift_events: list[dict[str, Any]]) -> list[dict[str, Any]]:
    signals: list[dict[str, Any]] = []
    for event in drift_events:
        severity = str(event.get("severity") or "")
        summary = str(event.get("summary") or "")
        lowered = summary.lower()
        if severity in {"attention", "critical"} or "insufficient" in lowered or "unclear" in lowered:
            signals.append(
                {
                    "drift_id": event.get("drift_id"),
                    "severity": severity,
                    "source": event.get("source"),
                    "summary": summary[:200],
                    "escalate": True,
                }
            )
    return signals


def build_epistemic_perimeter(
    *,
    domain: str,
    declared_scopes: list[str],
    drift_events: list[dict[str, Any]],
    upstream_evidence_count: int,
) -> dict[str, Any]:
    """Charter Art IV — declare knowledge scope and surface ambiguity for operator escalation."""
    ambiguities = _ambiguity_from_drift(drift_events)
    return {
        "charter_ref": CHARTER_DOC,
        "charter_article": "IV",
        "perimeter_owner": "human_operator",
        "ai_cannot_expand_scope": True,
        "declared_knowledge_scope": {
            "domain": domain,
            "scopes": list(declared_scopes),
            "upstream_evidence_count": upstream_evidence_count,
        },
        "ambiguity_signals": ambiguities,
        "escalation_required": bool(ambiguities),
        "escalation_guidance": (
            "Surface ambiguity to the operator immediately; do not infer external substrate "
            "or federation facts beyond declared scopes."
        ),
        "claim_label": "asserted",
    }


def build_collaboration_options(
    *,
    domain: str,
    candidates: list[dict[str, Any]],
    stakes: str = "high",
    collaboration_mode: str = "strict",
) -> dict[str, Any]:
    """Charter Art V — multiple adoption paths when civilizational stakes are high."""
    options: list[dict[str, Any]] = []
    for index, candidate in enumerate(candidates[:8]):
        options.append(
            {
                "option_id": candidate.get("candidate_id"),
                "label": chr(65 + index),
                "summary": str(candidate.get("summary") or "")[:200],
                "stability_score": candidate.get("stability_score"),
                "recommended": index == 0,
            }
        )

    if len(options) == 1:
        options.append(
            {
                "option_id": "defer_operator_review",
                "label": "B",
                "summary": "Defer adoption pending additional operator evidence",
                "stability_score": None,
                "recommended": False,
            }
        )
    elif not options:
        options.extend(
            [
                {
                    "option_id": "gather_evidence",
                    "label": "A",
                    "summary": "Gather upstream evidence before proposing adoption paths",
                    "stability_score": None,
                    "recommended": True,
                },
                {
                    "option_id": "defer_operator_review",
                    "label": "B",
                    "summary": "Defer adoption pending additional operator evidence",
                    "stability_score": None,
                    "recommended": False,
                },
            ]
        )

    return {
        "charter_ref": CHARTER_DOC,
        "charter_article": "V",
        "domain": domain,
        "stakes": stakes,
        "collaboration_mode": collaboration_mode,
        "single_path_blocked": stakes == "high" and len(candidates) <= 1,
        "options": options,
        "reversible": True,
        "undo_guidance": (
            "Reject candidate or rollback adopted overlay via operator registry; "
            "adoption requires explicit operator_approved + Jarvis authorization."
        ),
        "claim_label": "asserted",
    }


def attach_charter_surfaces(
    payload: dict[str, Any],
    *,
    domain: str,
    declared_scopes: list[str],
    drift_events: list[dict[str, Any]],
    upstream_evidence_count: int,
    candidates: list[dict[str, Any]],
    stakes: str = "high",
) -> dict[str, Any]:
    """Merge Art IV + Art V blocks into an operator observe/snapshot payload."""
    enriched = dict(payload)
    enriched["charter_surfaces"] = {
        "epistemic_perimeter": build_epistemic_perimeter(
            domain=domain,
            declared_scopes=declared_scopes,
            drift_events=drift_events,
            upstream_evidence_count=upstream_evidence_count,
        ),
        "collaboration_options": build_collaboration_options(
            domain=domain,
            candidates=candidates,
            stakes=stakes,
        ),
    }
    return enriched

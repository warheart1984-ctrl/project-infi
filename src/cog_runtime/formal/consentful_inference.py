"""Consentful inference enforcement — MA-13 axiom for deliberation defaults (INV-7)."""

from __future__ import annotations

from typing import Any

BINDING_POSTURES = frozenset({"proven", "operator", "binding"})
PROVISIONAL_POSTURES = frozenset({"asserted", "provisional", "inferred"})


def evaluate_consentful_inference(
    decision: dict[str, Any] | None,
    *,
    intent_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Ensure deliberation commits do not silently upgrade provisional inference to binding authority."""
    payload = dict(decision or {})
    chosen = str(payload.get("chosen_option") or "").strip()
    commit_source = str(payload.get("commit_source") or "deterministic")
    ctx = dict(intent_context or {})

    commitments = list(ctx.get("intent_commitments") or ctx.get("active_commitments") or [])
    provisional_refs: list[str] = []
    binding_refs: list[str] = []
    for item in commitments:
        if not isinstance(item, dict):
            continue
        text = str(item.get("commitment") or item.get("text") or "").strip()
        posture = str(item.get("claim_posture") or "asserted").lower()
        if not text:
            continue
        if posture in BINDING_POSTURES:
            binding_refs.append(text)
        else:
            provisional_refs.append(text)

    silent_upgrade = False
    violations: list[str] = []
    lowered = chosen.lower()
    for text in provisional_refs:
        if text.lower() in lowered and text not in binding_refs:
            silent_upgrade = True
            violations.append(f"provisional_commitment_in_chosen_option:{text[:80]}")

    consent_required = bool(provisional_refs) and commit_source == "llm"
    consent_recorded = bool(payload.get("operator_consent") or payload.get("consentful_inference", {}).get("consent_recorded"))
    if consent_required and not consent_recorded and silent_upgrade:
        violations.append("llm_commit_without_recorded_consent")

    passed = not violations
    return {
        "passed": passed,
        "violations": violations,
        "consent_required": consent_required,
        "consent_recorded": consent_recorded,
        "provisional_commitments": provisional_refs,
        "binding_commitments": binding_refs,
        "commit_source": commit_source,
        "claim_label": "proven" if passed else "asserted",
    }


def attach_consentful_inference(
    decision: dict[str, Any],
    *,
    intent_context: dict[str, Any] | None = None,
) -> dict[str, Any]:
    """Attach consentful inference evaluation to a deliberation decision object."""
    evaluation = evaluate_consentful_inference(decision, intent_context=intent_context)
    decision["consentful_inference"] = {
        "doctrine_axiom": "consentful_inference",
        "passed": evaluation["passed"],
        "violations": list(evaluation["violations"]),
        "consent_required": evaluation["consent_required"],
        "consent_recorded": evaluation["consent_recorded"],
        "claim_label": evaluation["claim_label"],
    }
    return decision

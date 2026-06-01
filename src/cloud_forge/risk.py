"""Risk and novelty estimation for Cloud Forge rails (v1 rule table)."""

from __future__ import annotations

from src.cloud_forge.types import (
    HIGH_RISK_SIGNALS,
    SIDE_EFFECT_TOOL_INTENTS,
    LawEnvelope,
    RiskLevel,
    TaskSignature,
)

_DOCS_PATTERN_PREFIXES = ("docs_", "explanation", "read_only")


def estimate_risk(task: TaskSignature, law_envelope: LawEnvelope) -> RiskLevel:
    """Classify task risk per cloud-forge-rail-contract.md § Risk signals."""
    if law_envelope.required_proof:
        return RiskLevel.HIGH

    scope = (task.mutation_scope or "none").strip().lower()
    if scope == "constitutional":
        return RiskLevel.HIGH

    signals = {s.strip().lower() for s in law_envelope.signals}
    if signals & HIGH_RISK_SIGNALS:
        return RiskLevel.HIGH

    context = (task.context_text or "").lower()
    if any(token in context for token in ("password=", "api_key", "secret=", "ssn")):
        return RiskLevel.HIGH

    if scope == "write":
        pattern = (task.pattern_class or "").lower()
        intents = {t.strip().lower() for t in task.tool_intents}
        if "prod" in pattern or "deploy" in pattern or "deploy" in intents:
            return RiskLevel.HIGH
        return RiskLevel.MEDIUM

    intents = {t.strip().lower() for t in task.tool_intents}
    if intents & SIDE_EFFECT_TOOL_INTENTS and "read_only" not in signals:
        return RiskLevel.MEDIUM

    pattern = (task.pattern_class or "").lower()
    if scope in {"none", "read"} and (
        pattern.startswith(_DOCS_PATTERN_PREFIXES)
        or "docs" in pattern
        or "explanation" in pattern
    ):
        return RiskLevel.LOW

    if scope == "read":
        return RiskLevel.LOW

    return RiskLevel.MEDIUM


def estimate_novelty(
    task: TaskSignature,
    pattern_records: list[dict] | None = None,
) -> RiskLevel:
    """LOW when verified pattern hash + domain repeat in rail ledger (Phase 2)."""
    if not task.normalized_prompt_hash or not task.domain:
        return RiskLevel.MEDIUM

    hits = 0
    for row in pattern_records or []:
        snapshot = row.get("task_snapshot") or row.get("task") or {}
        if str(snapshot.get("normalized_prompt_hash") or "") != task.normalized_prompt_hash:
            continue
        plan = row.get("cognition_plan") or {}
        row_domain = (
            snapshot.get("domain")
            or plan.get("domain_template")
            or (plan.get("template") or {}).get("template_id")
        )
        if str(row_domain or "") != str(task.domain):
            continue
        decision = row.get("rail_decision") or {}
        if decision.get("rail") in {"EXPRESS", "NORMAL"}:
            hits += 1

    if hits >= 2:
        return RiskLevel.LOW
    return RiskLevel.MEDIUM

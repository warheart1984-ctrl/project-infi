"""Pattern-based standing resolution for proof-of-discovery documents."""

from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any

from src.ugr.discovery.standing import (
    Standing,
    label_from_standing,
    standing_from_label,
)

DEFAULT_POLICY_PATH = (
    Path(__file__).resolve().parents[3] / "deploy" / "ugr" / "discovery-proof-promotion.json"
)
POLICY_ENV = "UGR_DISCOVERY_PROOF_PROMOTION_POLICY_PATH"


def _repo_root() -> Path:
    return Path(__file__).resolve().parents[3]


def policy_path() -> Path:
    override = os.getenv(POLICY_ENV, "").strip()
    if override:
        return Path(override)
    return DEFAULT_POLICY_PATH


def load_promotion_policy(path: Path | None = None) -> dict[str, Any]:
    target = path or policy_path()
    if not target.is_absolute():
        target = _repo_root() / target
    return json.loads(target.read_text(encoding="utf-8"))


def _normalize_text(*parts: str) -> str:
    return " ".join(p.strip() for p in parts if p and p.strip()).lower()


def _matches_regex(pattern: str, haystack: str) -> bool:
    try:
        return bool(re.search(pattern, haystack))
    except re.error:
        return False


def _has_denied_flag(document: dict[str, Any], policy: dict[str, Any]) -> bool:
    deny_flags = policy.get("deny_if_flags") or []
    for flag in deny_flags:
        if document.get(flag):
            return True
    return False


def _matches_deny_patterns(haystack: str, policy: dict[str, Any]) -> str | None:
    for rule in policy.get("deny_patterns") or []:
        regex = str(rule.get("regex") or "").strip()
        if regex and _matches_regex(regex, haystack):
            return str(rule.get("id") or "deny")
    return None


def _rule_matches(document: dict[str, Any], haystack: str, rule: dict[str, Any]) -> bool:
    flags = rule.get("flags") or []
    if flags:
        return all(document.get(flag) for flag in flags)
    regex = str(rule.get("regex") or "").strip()
    return bool(regex and _matches_regex(regex, haystack))


def _matches_hypothetical_patterns(haystack: str, policy: dict[str, Any]) -> str | None:
    for rule in policy.get("hypothetical_patterns") or []:
        regex = str(rule.get("regex") or "").strip()
        if regex and _matches_regex(regex, haystack):
            return str(rule.get("id") or "hypothetical")
    return None


def _matches_asserted_patterns(
    document: dict[str, Any], haystack: str, policy: dict[str, Any]
) -> str | None:
    contribution_type = str(document.get("contribution_type") or "").strip().lower()
    for rule in policy.get("asserted_patterns") or []:
        types = rule.get("contribution_types") or []
        if types and contribution_type in {str(t).lower() for t in types}:
            return str(rule.get("id") or "module_workflow_default")
        regex = str(rule.get("regex") or "").strip()
        if regex and _matches_regex(regex, haystack):
            return str(rule.get("id") or "asserted")
    return None


def _matches_proven_group(haystack: str, group: dict[str, Any]) -> bool:
    for pattern in group.get("patterns") or []:
        regex = str(pattern.get("regex") or "").strip()
        if regex and _matches_regex(regex, haystack):
            return True
    return False


def _matches_proven_groups(document: dict[str, Any], haystack: str, policy: dict[str, Any]) -> str | None:
    groups = policy.get("proven_groups") or []
    if not groups:
        return None
    matched: list[str] = []
    for group in groups:
        if _matches_proven_group(haystack, group):
            matched.append(str(group.get("id") or "group"))
    if len(matched) == len(groups):
        return "+".join(matched)
    return None


def _verification_context(document: dict[str, Any], verification_context: dict[str, Any] | None) -> dict[str, Any]:
    ctx = dict(verification_context or {})
    verification = dict(document.get("verification") or {})
    for key, value in verification.items():
        ctx.setdefault(key, value)
    if document.get("receipt_verified") is not None:
        ctx.setdefault("receipt_verified", document.get("receipt_verified"))
    artifacts = document.get("verification_artifacts") or verification.get("artifacts") or []
    if artifacts:
        ctx.setdefault("verification_artifacts", artifacts)
    return ctx


def _has_proven_verification(
    document: dict[str, Any],
    policy: dict[str, Any],
    verification_context: dict[str, Any] | None,
) -> tuple[bool, str | None]:
    cfg = dict(policy.get("proven_verification") or {})
    ctx = _verification_context(document, verification_context)

    if cfg.get("require_receipt_verified", True) and not ctx.get("receipt_verified"):
        return False, None

    signals = cfg.get("signals_any_of") or []
    matched: list[str] = []
    if "ci_structural_test" in signals and ctx.get("ci_structural_test"):
        matched.append("ci_structural_test")
    if "subsystem_genome_gate" in signals and ctx.get("subsystem_genome_gate"):
        matched.append("subsystem_genome_gate")
    if "workflow_otem_gate" in signals and ctx.get("workflow_otem_gate"):
        matched.append("workflow_otem_gate")
    artifacts = ctx.get("verification_artifacts") or []
    if "verification_artifacts" in signals and artifacts:
        matched.append("verification_artifacts")

    if matched:
        return True, "+".join(matched)
    return False, None


def resolve_standing(
    document: dict[str, Any],
    *,
    policy: dict[str, Any] | None = None,
    verification_context: dict[str, Any] | None = None,
    auto_promote: bool | None = None,
) -> tuple[int, str, str | None]:
    """Return (standing, claim_label, matched_rule_id)."""
    pol = policy or load_promotion_policy()
    promote = pol.get("auto_promote_enabled", True) if auto_promote is None else auto_promote

    haystack = _normalize_text(
        str(document.get("title") or ""),
        str(document.get("slug") or ""),
        str(document.get("source_path") or ""),
    )

    if _has_denied_flag(document, pol):
        return int(Standing.DENIED), label_from_standing(Standing.DENIED), "deny:duplicate_of"

    denied = _matches_deny_patterns(haystack, pol)
    if denied:
        return int(Standing.DENIED), label_from_standing(Standing.DENIED), f"deny:{denied}"

    if promote:
        verified, verify_rule = _has_proven_verification(document, pol, verification_context)
        if verified:
            return int(Standing.PROVEN), label_from_standing(Standing.PROVEN), f"verify:{verify_rule}"

    hypothetical = _matches_hypothetical_patterns(haystack, pol)
    if hypothetical:
        return (
            int(Standing.HYPOTHETICAL),
            label_from_standing(Standing.HYPOTHETICAL),
            f"hypothetical:{hypothetical}",
        )

    asserted = _matches_asserted_patterns(document, haystack, pol)
    if asserted:
        return int(Standing.ASSERTED), label_from_standing(Standing.ASSERTED), f"asserted:{asserted}"

    if promote:
        grouped = _matches_proven_groups(document, haystack, pol)
        if grouped:
            return int(Standing.ASSERTED), label_from_standing(Standing.ASSERTED), f"hint:{grouped}"

    default_standing = int(pol.get("default_standing") or Standing.ASSERTED)
    return default_standing, label_from_standing(Standing(default_standing)), None


def resolve_claim_label(
    document: dict[str, Any],
    *,
    policy: dict[str, Any] | None = None,
    verification_context: dict[str, Any] | None = None,
    auto_promote: bool | None = None,
) -> tuple[str, str | None]:
    """Return (claim_label, matched_rule_id). Back-compat wrapper over resolve_standing."""
    standing, label, rule_id = resolve_standing(
        document,
        policy=policy,
        verification_context=verification_context,
        auto_promote=auto_promote,
    )
    _ = standing
    return label, rule_id


def _current_standing(document: dict[str, Any]) -> Standing:
    if "standing" in document:
        try:
            return Standing(int(document["standing"]))
        except (TypeError, ValueError):
            pass
    return standing_from_label(str(document.get("claim_label") or "asserted"))


def should_transition_standing(
    document: dict[str, Any],
    *,
    policy: dict[str, Any] | None = None,
    verification_context: dict[str, Any] | None = None,
    auto_promote: bool | None = None,
) -> tuple[bool, int, str, str | None]:
    """True when standing should change; returns (changed, target_standing, target_label, rule_id)."""
    current = _current_standing(document)
    target_standing, target_label, rule_id = resolve_standing(
        document,
        policy=policy,
        verification_context=verification_context,
        auto_promote=auto_promote,
    )
    target = Standing(target_standing)
    if current == target:
        return False, target_standing, target_label, rule_id
    return True, target_standing, target_label, rule_id


def should_upgrade_claim_label(
    document: dict[str, Any],
    *,
    policy: dict[str, Any] | None = None,
    verification_context: dict[str, Any] | None = None,
    auto_promote: bool | None = None,
) -> tuple[bool, str, str | None]:
    """True when standing increases."""
    current = _current_standing(document)
    changed, target_standing, target_label, rule_id = should_transition_standing(
        document,
        policy=policy,
        verification_context=verification_context,
        auto_promote=auto_promote,
    )
    if not changed or target_standing <= int(current):
        return False, label_from_standing(current), rule_id
    return True, target_label, rule_id


def should_downgrade_claim_label(
    document: dict[str, Any],
    *,
    policy: dict[str, Any] | None = None,
    verification_context: dict[str, Any] | None = None,
    auto_promote: bool | None = None,
) -> tuple[bool, str, str | None]:
    """True when standing decreases."""
    current = _current_standing(document)
    changed, target_standing, target_label, rule_id = should_transition_standing(
        document,
        policy=policy,
        verification_context=verification_context,
        auto_promote=auto_promote,
    )
    if not changed or target_standing >= int(current):
        return False, label_from_standing(current), rule_id
    return True, target_label, rule_id


def should_exclude_from_library(
    document: dict[str, Any],
    *,
    policy: dict[str, Any] | None = None,
    verification_context: dict[str, Any] | None = None,
    auto_promote: bool | None = None,
) -> tuple[bool, str | None]:
    """True when document should be withdrawn from discovery store (standing 0)."""
    standing, _, rule_id = resolve_standing(
        document,
        policy=policy,
        verification_context=verification_context,
        auto_promote=auto_promote,
    )
    return standing == int(Standing.DENIED), rule_id


def rejection_source_for_rule(rule_id: str | None) -> str | None:
    """Map proof-promotion deny rules to canonical rejection_source values."""
    rid = str(rule_id or "").strip()
    if rid.startswith("deny:"):
        return "discovery_denial"
    return None

"""Org policy DSL compiler (v13) — restricted rule subset."""

from __future__ import annotations

import hashlib
import json
import re
from typing import Any, Callable

ALLOWED_ATTRS = frozenset(
    {
        "job.type",
        "job.kind",
        "job.cost_estimate",
        "job.proof_status",
        "job_type",
        "job_kind",
        "job_proof_status",
        "principal.role",
        "principal_role",
        "org.plan",
        "org.plan_id",
        "org_plan_id",
        "listing.approval_status",
        "listing.deprecated",
        "listing_approval_status",
        "listing_deprecated",
    }
)

RulePredicate = Callable[[dict[str, Any]], tuple[bool, str]]


def _compile_hash(source: str) -> str:
    return hashlib.sha256(source.encode()).hexdigest()[:16]


def parse_rule_line(line: str) -> dict[str, str] | None:
    line = line.strip()
    if not line or line.startswith("#"):
        return None
    m = re.match(
        r"^(allow|deny|require)\s+(\S+)\s+(when|if)\s+(.+)$",
        line,
        re.IGNORECASE,
    )
    if not m:
        return None
    return {
        "effect": m.group(1).lower(),
        "target": m.group(2),
        "condition": m.group(4).strip(),
    }


def _eval_condition(condition: str, ctx: dict[str, Any]) -> bool:
    """Safe whitelist evaluation for simple comparisons."""
    cond = condition.strip()
    listing = ctx.get("listing") or {}
    env: dict[str, Any] = {
        "job_type": ctx.get("job_type") or ctx.get("job", {}).get("type"),
        "job_kind": ctx.get("job_kind") or ctx.get("job", {}).get("kind"),
        "job_proof_status": ctx.get("job_proof_status") or ctx.get("job", {}).get("proof_status"),
        "org_plan_id": ctx.get("org_plan_id") or ctx.get("org", {}).get("plan_id"),
        "principal_role": ctx.get("principal_role") or ctx.get("principal", {}).get("role"),
        "listing_visibility": listing.get("visibility"),
        "listing_curated": listing.get("curated"),
        "listing_approval_status": listing.get("approval_status"),
        "listing_deprecated": listing.get("approval_status") == "deprecated",
        "marketplace_install": ctx.get("marketplace_install", False),
    }
    for attr in sorted(ALLOWED_ATTRS, key=len, reverse=True):
        parts = attr.split(".")
        obj: Any = ctx
        for p in parts:
            obj = obj.get(p, {}) if isinstance(obj, dict) else None
        env[attr.replace(".", "_")] = obj
    if re.search(r"__|import|exec|eval|open|[;]", cond):
        return False
    try:
        return bool(eval(cond, {"__builtins__": {}}, env))  # noqa: S307
    except Exception:
        return False


def compile_rules(*, org_id: str, source: str) -> tuple[list[RulePredicate], str, list[dict[str, Any]]]:
    predicates: list[RulePredicate] = []
    records: list[dict[str, Any]] = []
    lines = source.strip().splitlines()
    for i, line in enumerate(lines):
        parsed = parse_rule_line(line)
        if not parsed:
            continue
        effect = parsed["effect"]
        condition = parsed["condition"]

        def make_pred(eff: str = effect, cond: str = condition) -> RulePredicate:
            def _pred(ctx: dict[str, Any]) -> tuple[bool, str]:
                if not _eval_condition(cond, ctx):
                    return True, "no_match"
                if eff == "deny":
                    return False, f"policy deny: {cond}"
                if eff == "require":
                    req = cond
                    if "proof_status" in req and ctx.get("job", {}).get("proof_status") != "proven":
                        return False, "proof required by org policy"
                return True, "ok"

            return _pred

        predicates.append(make_pred())
        records.append(
            {
                "rule_id": f"{org_id}:rule:{i}",
                "org_id": org_id,
                "source": line,
                "compiled_hash": _compile_hash(line),
                "enabled": True,
            }
        )
    compiled_hash = _compile_hash(source)
    return predicates, compiled_hash, records


def evaluate_compiled_rules(
    predicates: list[RulePredicate],
    *,
    ctx: dict[str, Any],
) -> tuple[bool, str]:
    for pred in predicates:
        ok, reason = pred(ctx)
        if not ok:
            return False, reason
    return True, "ok"


def build_admission_context(
    *,
    org: dict[str, Any],
    job_request: dict[str, Any],
    principal_role: str = "operator",
) -> dict[str, Any]:
    jtype = job_request.get("job_type") or str(job_request.get("kind", "")).split(".")[-1]
    return {
        "org": org,
        "org_plan": org.get("plan_id"),
        "org_plan_id": org.get("plan_id"),
        "principal": {"role": principal_role},
        "principal_role": principal_role,
        "job": {
            "type": jtype,
            "kind": job_request.get("kind"),
            "cost_estimate": job_request.get("cost_estimate", 0),
            "proof_status": job_request.get("proof_status", "asserted"),
        },
        "job_type": jtype,
        "job_kind": job_request.get("kind"),
        "job_cost_estimate": job_request.get("cost_estimate", 0),
        "job_proof_status": job_request.get("proof_status", "asserted"),
        "listing": job_request.get("listing") or {},
        "marketplace_install": bool(job_request.get("marketplace_install")),
    }
